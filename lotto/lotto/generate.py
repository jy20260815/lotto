import random
from typing import Literal

from .db import get_connection
from .stats import DEFAULT_RECENT_WINDOW

HIGH_POOL_SIZE = 15
LOW_POOL_SIZE = 15
POPULARITY_SAMPLE_SIZE = 300
LUCKY_NUMBERS = {3, 7, 8}

SlotRule = Literal["independent", "fixed", "all_high", "all_low", "biased", "unpopular"]


def _load_pools(conn, table: str = "number_stats"):
    rows = conn.execute(f"SELECT number, ratio FROM {table} ORDER BY ratio DESC").fetchall()
    if len(rows) < HIGH_POOL_SIZE + LOW_POOL_SIZE:
        raise RuntimeError(f"{table}가 비어있거나 부족합니다. 먼저 데이터 수집을 실행하세요.")
    high_pool = rows[:HIGH_POOL_SIZE]
    low_pool = rows[-LOW_POOL_SIZE:]
    return high_pool, low_pool


def _rank_lookup(conn, table: str) -> dict[int, int]:
    rows = conn.execute(f"SELECT number FROM {table} ORDER BY ratio DESC").fetchall()
    return {row["number"]: idx + 1 for idx, row in enumerate(rows)}


def _ratio_lookup(conn, table: str = "number_stats") -> dict[int, float]:
    rows = conn.execute(f"SELECT number, ratio FROM {table}").fetchall()
    return {row["number"]: row["ratio"] for row in rows}


def _previous_draw_numbers(conn) -> set[int]:
    row = conn.execute(
        "SELECT num1, num2, num3, num4, num5, num6 FROM draws ORDER BY round DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return set()
    return {row[f"num{i}"] for i in range(1, 7)}


def _pick(pool, count, exclude):
    candidates = [row for row in pool if row["number"] not in exclude]
    chosen = random.sample(candidates, count)
    exclude.update(row["number"] for row in chosen)
    return chosen


def _compose_3_2_1(high_pool, low_pool, exclude, swing_mode, labels):
    """고확률 3(고정) + 변동 슬롯 2 + 저확률 1(고정) 구성.
    swing_mode="independent": 슬롯마다 독립적으로 50% 확률로 고/저 선택.
    swing_mode="fixed": 변동 슬롯을 고확률 1 + 저확률 1로 고정."""
    picks: list[dict] = []

    for row in _pick(high_pool, 3, exclude):
        picks.append({"number": row["number"], "ratio": row["ratio"], "source": labels["high_fixed"]})

    if swing_mode == "independent":
        for _ in range(2):
            pool, label = (
                (high_pool, labels["high_swing"]) if random.random() < 0.5 else (low_pool, labels["low_swing"])
            )
            row = _pick(pool, 1, exclude)[0]
            picks.append({"number": row["number"], "ratio": row["ratio"], "source": label})
    else:
        for pool, label in ((high_pool, labels["high_swing"]), (low_pool, labels["low_swing"])):
            row = _pick(pool, 1, exclude)[0]
            picks.append({"number": row["number"], "ratio": row["ratio"], "source": label})

    for row in _pick(low_pool, 1, exclude):
        picks.append({"number": row["number"], "ratio": row["ratio"], "source": labels["low_fixed"]})

    return picks


def _popularity_score(numbers: list[int], prev_draw: set[int]) -> tuple[int, list[str]]:
    """점수가 높을수록 '사람들이 흔히 고르는' 인기 조합에 가깝다는 뜻이다.
    unpopular 모드는 무작위 표본 중 이 점수가 가장 낮은(=사람들이 덜 고를 법한)
    조합을 채택한다. 규칙 근거는 docs/plan_bias_unpopular.md 2-2 표 참고."""
    score = 0
    traits: list[str] = []
    nums = sorted(numbers)

    low_range_count = sum(1 for n in nums if n <= 31)
    score += low_range_count
    if low_range_count <= 2:
        traits.append("32~45 범위 번호 다수 포함 (생일 편향 회피)")

    consecutive_pairs = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
    score -= consecutive_pairs * 3
    if consecutive_pairs > 0:
        traits.append(f"연속 번호 {consecutive_pairs}쌍 포함")

    diffs = [b - a for a, b in zip(nums, nums[1:])]
    has_arithmetic_run = any(diffs[i] == diffs[i + 1] == diffs[i + 2] for i in range(len(diffs) - 2))
    if has_arithmetic_run:
        score -= 3
        traits.append("등차수열 포함")

    all_multiples_of_5 = all(n % 5 == 0 for n in nums)
    same_last_digit = len({n % 10 for n in nums}) == 1
    if all_multiples_of_5 or same_last_digit:
        score -= 2
        traits.append("배수/끝자리 패턴 포함")

    score += sum(1 for n in nums if n in LUCKY_NUMBERS)

    total = sum(nums)
    if 100 <= total <= 170:
        score += 2
    else:
        score -= 2
        traits.append(f"번호 합계 {total} (평균권 100~170 밖이라 사람들이 덜 고름)")

    overlap = len(set(nums) & prev_draw)
    if overlap > 0:
        score -= overlap * 2
        traits.append(f"직전 회차 번호와 {overlap}개 중복")

    if not traits:
        traits.append("뚜렷한 회피 패턴은 없지만 무작위 표본 중 인기 점수가 상대적으로 낮음")

    return score, traits


def _generate_unpopular_combination(ratio_lookup: dict[int, float], prev_draw: set[int]) -> dict:
    best: tuple[int, list[int], list[str]] | None = None
    for _ in range(POPULARITY_SAMPLE_SIZE):
        candidate = sorted(random.sample(range(1, 46), 6))
        score, traits = _popularity_score(candidate, prev_draw)
        if best is None or score < best[0]:
            best = (score, candidate, traits)

    _, numbers, traits = best
    detail = [
        {"number": n, "ratio": ratio_lookup.get(n, 0.0), "source": "저인기 조합 구성 번호"} for n in numbers
    ]
    return {"slot_rule": "unpopular", "numbers": numbers, "traits": traits, "detail": detail}


def generate_combination(slot_rule: SlotRule = "independent") -> dict:
    """당첨번호 6개 조합을 만든다.
    - "independent"/"fixed": 전체 누적 출현빈도 상위 15(고확률)·하위 15(저확률) 풀에서
      3(고정 고확률) + 2(변동 슬롯) + 1(고정 저확률) 구성. 변동 슬롯 규칙은 슬롯모드 참고.
    - "all_high"/"all_low": 6개 전부 고확률 또는 저확률 풀에서 선택.
    - "biased": 위와 같은 3:2:1 구성이지만 전체 누적 대신 최근 window회차 출현빈도
      기준 풀을 사용 ("혹시 편향이 있다면" 가정의 실험 모드, 근거는 약함).
    - "unpopular": 당첨 확률은 다른 조합과 동일하다. 대신 사람들이 실제로 덜 고르는
      특징(32~45 비중, 연속/등차수열, 극단적 합계 등)을 일부러 포함시켜, 당첨 시
      상금을 나눠 가질 인원을 줄이는 것이 목적.
    """
    conn = get_connection()
    try:
        if slot_rule == "unpopular":
            ratio_lookup = _ratio_lookup(conn)
            prev_draw = _previous_draw_numbers(conn)
            return _generate_unpopular_combination(ratio_lookup, prev_draw)

        if slot_rule == "biased":
            high_pool, low_pool = _load_pools(conn, table="number_stats_recent")
            alltime_rank = _rank_lookup(conn, "number_stats")
            recent_rank = _rank_lookup(conn, "number_stats_recent")
        else:
            high_pool, low_pool = _load_pools(conn, table="number_stats")
            alltime_rank = recent_rank = None
    finally:
        conn.close()

    exclude: set[int] = set()

    if slot_rule == "all_high":
        picks = [
            {"number": r["number"], "ratio": r["ratio"], "source": "고확률(전체 6개)"}
            for r in _pick(high_pool, 6, exclude)
        ]
    elif slot_rule == "all_low":
        picks = [
            {"number": r["number"], "ratio": r["ratio"], "source": "저확률(전체 6개)"}
            for r in _pick(low_pool, 6, exclude)
        ]
    elif slot_rule == "biased":
        picks = _compose_3_2_1(
            high_pool,
            low_pool,
            exclude,
            "independent",
            {
                "high_fixed": f"최근 {DEFAULT_RECENT_WINDOW}회 고빈도(고정 3개 중 하나)",
                "low_fixed": f"최근 {DEFAULT_RECENT_WINDOW}회 저빈도(고정 1개)",
                "high_swing": f"최근 {DEFAULT_RECENT_WINDOW}회 고빈도(변동 슬롯)",
                "low_swing": f"최근 {DEFAULT_RECENT_WINDOW}회 저빈도(변동 슬롯)",
            },
        )
        for p in picks:
            delta = alltime_rank[p["number"]] - recent_rank[p["number"]]
            if delta > 0:
                p["source"] += f" · 전체 누적 순위보다 {delta}계단 상승"
            elif delta < 0:
                p["source"] += f" · 전체 누적 순위보다 {-delta}계단 하락"
    elif slot_rule == "fixed":
        picks = _compose_3_2_1(
            high_pool,
            low_pool,
            exclude,
            "fixed",
            {
                "high_fixed": "고확률(고정 3개 중 하나)",
                "low_fixed": "저확률(고정 1개)",
                "high_swing": "고확률(변동 슬롯, 규칙상 고정 배정)",
                "low_swing": "저확률(변동 슬롯, 규칙상 고정 배정)",
            },
        )
    else:  # independent
        picks = _compose_3_2_1(
            high_pool,
            low_pool,
            exclude,
            "independent",
            {
                "high_fixed": "고확률(고정 3개 중 하나)",
                "low_fixed": "저확률(고정 1개)",
                "high_swing": "고확률(변동 슬롯, 50% 확률로 당첨)",
                "low_swing": "저확률(변동 슬롯, 50% 확률로 당첨)",
            },
        )

    picks.sort(key=lambda p: p["number"])
    return {"slot_rule": slot_rule, "numbers": [p["number"] for p in picks], "detail": picks}


def generate_combinations(slot_rule: SlotRule = "independent", count: int = 5) -> list[dict]:
    """서로 다른 조합 count개를 생성한다 (중복 조합은 걸러내고 다시 뽑음)."""
    results: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    max_attempts = count * 20
    attempts = 0
    while len(results) < count and attempts < max_attempts:
        attempts += 1
        result = generate_combination(slot_rule)
        key = tuple(result["numbers"])
        if key in seen:
            continue
        seen.add(key)
        results.append(result)
    return results


def explain(result: dict) -> str:
    ratio_label = f"최근 {DEFAULT_RECENT_WINDOW}회 출현비율" if result["slot_rule"] == "biased" else "역대 출현비율"
    numbers = ", ".join(str(n) for n in result["numbers"])
    lines = [f"[{result['slot_rule']}] 생성된 번호: {numbers}"]
    for p in result["detail"]:
        lines.append(f"  {p['number']:>2} - {p['source']} ({ratio_label} {p['ratio'] * 100:.1f}%)")
    if "traits" in result:
        lines.append("  특징: " + "; ".join(result["traits"]))
    return "\n".join(lines)
