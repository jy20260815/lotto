from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analysis import summarize
from .backtest import run_backtest
from .check import check_tickets, get_draw, recent_draws
from .simulate import simulate_purchases
from .generate import (
    MAX_SUM,
    MIN_SUM,
    VALID_RULES,
    Constraints,
    GenerationError,
    generate_combination,
    generate_combinations,
    load_snapshot,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="로또 번호 생성기")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

CATEGORY_LABELS = {
    "independent": "독립 50:50 방식",
    "fixed": "고정 1:1 방식",
    "all_high": "고확률만",
    "all_low": "저확률만",
    "biased": "편향 가정 (최근 100회 가중)",
    "unpopular": "비인기 조합",
}


def _parse_numbers(raw: str, field: str) -> set[int]:
    if not raw.strip():
        return set()
    try:
        return {int(part) for part in raw.split(",") if part.strip()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{field}는 쉼표로 구분한 숫자여야 합니다") from exc


def _load_snapshot_or_503():
    try:
        return load_snapshot()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/generate")
def api_generate(
    rule: str = "independent",
    count: int = 5,
    include: str = "",
    exclude: str = "",
    odd: int | None = None,
    sum_min: int = MIN_SUM,
    sum_max: int = MAX_SUM,
) -> dict:
    if rule not in VALID_RULES:
        raise HTTPException(status_code=400, detail=f"rule은 {', '.join(VALID_RULES)} 중 하나여야 합니다")
    if not (1 <= count <= 20):
        raise HTTPException(status_code=400, detail="count는 1~20 사이여야 합니다")
    constraints = Constraints(
        include=_parse_numbers(include, "include"),
        exclude=_parse_numbers(exclude, "exclude"),
        odd_count=odd,
        sum_min=sum_min,
        sum_max=sum_max,
    )
    snapshot = _load_snapshot_or_503()
    try:
        constraints.validate()
        combinations = generate_combinations(rule, count, snapshot, constraints)
    except GenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"slot_rule": rule, "combinations": combinations}


@app.get("/api/weekly")
def api_weekly() -> dict:
    """카테고리(6종)마다 조합을 하나씩 뽑아 '이번주 로또번호'로 제시한다."""
    snapshot = _load_snapshot_or_503()
    picks = []
    for rule in VALID_RULES:
        result = generate_combination(rule, snapshot)
        result["label"] = CATEGORY_LABELS[rule]
        picks.append(result)
    return {"picks": picks}


@app.get("/api/draws")
def api_draws(limit: int = 10) -> dict:
    if not (1 <= limit <= 100):
        raise HTTPException(status_code=400, detail="limit은 1~100 사이여야 합니다")
    return {"draws": recent_draws(limit)}


@app.get("/api/draws/latest")
def api_latest_draw() -> dict:
    draw = get_draw()
    if draw is None:
        raise HTTPException(status_code=503, detail="수집된 회차가 없습니다. 먼저 데이터 수집을 실행하세요.")
    return draw


@app.get("/api/draws/{round_no}")
def api_draw(round_no: int) -> dict:
    draw = get_draw(round_no)
    if draw is None:
        raise HTTPException(status_code=404, detail=f"{round_no}회 결과가 없습니다")
    return draw


class CheckRequest(BaseModel):
    tickets: list[list[int]]
    round: int | None = None


@app.post("/api/check")
def api_check(req: CheckRequest) -> dict:
    if not (1 <= len(req.tickets) <= 50):
        raise HTTPException(status_code=400, detail="확인할 조합은 1~50개여야 합니다")
    for numbers in req.tickets:
        if len(numbers) != 6 or len(set(numbers)) != 6 or not all(1 <= n <= 45 for n in numbers):
            raise HTTPException(status_code=400, detail="각 조합은 1~45 사이의 서로 다른 번호 6개여야 합니다")
    draw = get_draw(req.round)
    if draw is None:
        detail = f"{req.round}회 결과가 없습니다" if req.round else "수집된 회차가 없습니다"
        raise HTTPException(status_code=404, detail=detail)
    return {"draw": draw, "results": check_tickets(req.tickets, draw)}


@app.get("/api/stats")
def api_stats(window: int = 0) -> dict:
    """window=0이면 전체 회차, 양수면 최근 window회차 기준."""
    if window < 0:
        raise HTTPException(status_code=400, detail="window는 0 이상이어야 합니다")
    try:
        return summarize(window or None)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/backtest")
def api_backtest(rounds: int = 100, tickets: int = 5, seed: int | None = None) -> dict:
    if not (10 <= rounds <= 300):
        raise HTTPException(status_code=400, detail="rounds는 10~300 사이여야 합니다")
    if not (1 <= tickets <= 10):
        raise HTTPException(status_code=400, detail="tickets는 1~10 사이여야 합니다")
    try:
        return run_backtest(rounds, tickets, seed)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/simulate")
def api_simulate(rounds: int = 5, seed: int | None = None) -> dict:
    """최근 rounds회차마다 무작위 번호를 5장~1000만 장씩 샀을 때 등수별 당첨 장수."""
    if not (1 <= rounds <= 10):
        raise HTTPException(status_code=400, detail="rounds는 1~10 사이여야 합니다")
    try:
        return simulate_purchases(rounds, seed)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
