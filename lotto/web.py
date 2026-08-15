from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .generate import generate_combination, generate_combinations
from .templates import INDEX_HTML

app = FastAPI(title="로또 번호 생성기")

VALID_RULES = ("independent", "fixed", "all_high", "all_low", "biased", "unpopular")

CATEGORY_LABELS = {
    "independent": "독립 50:50 방식",
    "fixed": "고정 1:1 방식",
    "all_high": "고확률만",
    "all_low": "저확률만",
    "biased": "편향 가정 (최근 100회 가중)",
    "unpopular": "비인기 조합",
}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/api/generate")
def api_generate(rule: str = "independent", count: int = 5) -> dict:
    if rule not in VALID_RULES:
        raise HTTPException(status_code=400, detail=f"rule은 {', '.join(VALID_RULES)} 중 하나여야 합니다")
    if not (1 <= count <= 20):
        raise HTTPException(status_code=400, detail="count는 1~20 사이여야 합니다")
    try:
        combinations = generate_combinations(rule, count)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"slot_rule": rule, "combinations": combinations}


@app.get("/api/weekly")
def api_weekly() -> dict:
    """카테고리(6종)마다 조합을 하나씩 뽑아 '이번주 로또번호'로 제시한다."""
    try:
        picks = []
        for rule in VALID_RULES:
            result = generate_combination(rule)
            result["label"] = CATEGORY_LABELS[rule]
            picks.append(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"picks": picks}
