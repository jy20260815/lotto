import random
from dataclasses import dataclass, field
from typing import Literal

from .db import get_connection
from .stats import DEFAULT_RECENT_WINDOW

HIGH_POOL_SIZE = 15
LOW_POOL_SIZE = 15
POPULARITY_SAMPLE_SIZE = 300
LUCKY_NUMBERS = {3, 7, 8}
CONSTRAINT_MAX_ATTEMPTS = 500
MIN_SUM = sum(range(1, 7))
MAX_SUM = sum(range(40, 46))

SlotRule = Literal["independent", "fixed", "all_high", "all_low", "biased", "unpopular"]
VALID_RULES: tuple[str, ...] = ("independent", "fixed", "all_high", "all_low", "biased", "unpopular")


class GenerationError(ValueError):
    """사용자가 준 조건(고정수·제외수·홀짝·합계)으로는 조합을 만들 수 없을 때."""


@dataclass
class Snapshot:
    """번호 생성에 필요한 통계를 메모리에 올려둔 것. 백테스트는 과거 특정 회차
    직전까지의 draws만으로 이 스냅샷을 만들어, 미래 데이터를 보지 않고 생성한다."""

    alltime: list[dict]  # [{"number", "ratio"}] 출현비율 내림차순
    recent: list[dict]  # 최근 window회 기준, 같은 형식
    prev_draw: set[int]

    @property
    def alltime_ratio(self) -> dict[int, float]:
        return {row["number"]: row["ratio"] for row in self.alltime}


@dataclass
class Constraints:
    include: set[int] = field(default_factory=set)
    exclude: set[int] = field(default_factory=set)
    odd_count: int | None = None
    sum_min: int = MIN_SUM
    sum_max: int = MAX_SUM

    def validate(self) -> None:
        for n in self.include | self.exclude:
            if not 1 <= n <= 45:
                raise GenerationError("번호는 1~45 사이여야 합니다")
        if self.include & self.exclude:
            overlap = ", ".join(str(n) for n in sorted(self.include & self.exclude))
            raise GenerationError(f"고정수와 제외수에 같은 번호가 있습니다: {overlap}")
        if len(self.include) > 5:
            raise GenerationError("고정수는 최대 5개까지 지정할 수 있습니다")
        if 45 - len(self.exclude) < 6:
            raise GenerationError("제외수가 너무 많아 6개를 고를 수 없습니다")
        if self.sum_min > self.sum_max:
            raise GenerationError("합계 최솟값이 최댓값보다 큽니다")
        if self.odd_count is not None:
            if not 0 <= self.odd_count <= 6:
                raise GenerationError("홀수 개수는 0~6 사이여야 합니다")
            fixed_odd = sum(1 for n in self.include if n % 2)
            fixed_even = len(self.include) - fixed_odd
            if fixed_odd > self.odd_count or fixed_even > 6 - self.odd_count:
                raise GenerationError("고정수의 홀짝 구성이 지정한 홀짝 비율과 맞지 않습니다")

    def accepts(self, numbers: list[int]) -> bool:
        if self.odd_count is not None and sum(1 for n in numbers if n % 2) != self.odd_count:
            return False
        return self.sum_min <= sum(numbers) <= self.sum_max

    @property
    def is_empty(self) -> bool:
        return (
            not self.include
            and not self.exclude
            and self.odd_count is None
            and self.sum_min <= MIN_SUM
            and self.sum_max >= MAX_SUM
        )


def _ranked(counts: dict[int, int], total: int) -> list[dict]:
    rows = [{"number": n, "ratio": counts.get(n, 0) / total} for n in range(1, 46)]
    rows.sort(key=lambda r: (-r["ratio"], r["number"]))
    return rows


def snapshot_from_draws(draws: list[list[int]], window: int = DEFAULT_RECENT_WINDOW) -> Snapshot:
    """draws는 회차 오름차순으로 정렬된 당첨번호 6개 리스트들."""
    if not draws:
        raise RuntimeError("draws가 비어있습니다. 먼저 데이터 수집을 실행하세요.")
    alltime_counts: dict[int, int] = {}
    for nums in draws:
        for n in nums:
            alltime_counts[n] = alltime_counts.get(n, 0) + 1
    recent_draws = draws[-window:]
    recent_counts: dict[int, int] = {}
    for nums in recent_draws:
        for n in nums:
            recent_counts[n] = recent_counts.get(n, 0) + 1
    return Snapshot(
        alltime=_ranked(alltime_counts, len(draws)),
        recent=_ranked(recent_counts, len(recent_draws)),
        prev_draw=set(draws[-1]),
    )


def load_draw_numbers(conn) -> list[list[int]]:
    rows = conn.execute("SELECT num1, num2, num3, num4, num5, num6 FROM draws ORDER BY round").fetchall()
    return [[row[f"num{i}"] for i in range(1, 7)] for row in rows]


def load_snapshot() -> Snapshot:
    conn = get_connection()
    try:
        return snapshot_from_draws(load_draw_numbers(conn))
    finally:
        conn.close()


def _pools(ranked: list[dict]) -> tuple[list[dict], list[dict]]:
    return ranked[:HIGH_POOL_SIZE], ranked[-LOW_POOL_SIZE:]


def _pick(pool, count, exclude, rng):
    candidates = [row for row in pool if row["number"] not in exclude]
    if len(candidates) < count:
        raise GenerationError("제외수 때문에 이 규칙의 번호 풀이 부족합니다. 제외수를 줄이거나 다른 규칙을 골라보세요.")
    chosen = rng.sample(candidates, count)
    exclude.update(row["number"] for row in chosen)
    return chosen


def _compose_3_2_1(high_pool, low_pool, exclude, swing_mode, labels, rng):
    """고확률 3(고정) + 변동 슬롯 2 + 저확률 1(고정) 구성.
    swing_mode="independent": 슬롯마다 독립적으로 50% 확률로 고/저 선택.
    swing_mode="fixed": 변동 슬롯을 고확률 1 + 저확률 1로 고정."""
    picks: list[dict] = []

    for row in _pick(high_pool, 3, exclude, rng):
        picks.append({"number": row["number"], "ratio": row["ratio"], "source": labels["high_fixed"]})

    if swing_mode == "independent":
        for _ in range(2):
            pool, label = (
                (high_pool, labels["high_swing"]) if rng.random() < 0.5 else (low_pool, labels["low_swing"])
            )
            row = _pick(pool, 1, exclude, rng)[0]
            picks.append({"number": row["number"], "ratio": row["ratio"], "source": label})
    else:
        for pool, label in ((high_pool, labels["high_swing"]), (low_pool, labels["low_swing"])):
            row = _pick(pool, 1, exclude, rng)[0]
            picks.append({"number": row["number"], "ratio": row["ratio"], "source": label})

    for row in _pick(low_pool, 1, exclude, rng):
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


def _generate_unpopular_combination(snapshot: Snapshot, constraints: Constraints, rng) -> dict:
    fixed = sorted(constraints.include)
    allowed = [n for n in range(1, 46) if n not in constraints.exclude and n not in constraints.include]
    best: tuple[int, list[int], list[str]] | None = None
    valid_samples = 0
    for _ in range(POPULARITY_SAMPLE_SIZE * 20):
        candidate = sorted(fixed + rng.sample(allowed, 6 - len(fixed)))
        if not constraints.accepts(candidate):
            continue
        score, traits = _popularity_score(candidate, snapshot.prev_draw)
        if best is None or score < best[0]:
            best = (score, candidate, traits)
        valid_samples += 1
        if valid_samples >= POPULARITY_SAMPLE_SIZE:
            break

    if best is None:
        raise GenerationError("조건을 만족하는 조합을 찾지 못했습니다. 홀짝·합계 조건을 완화해보세요.")

    _, numbers, traits = best
    ratio_lookup = snapshot.alltime_ratio
    detail = [
        {
            "number": n,
            "ratio": ratio_lookup.get(n, 0.0),
            "source": "고정수(직접 지정)" if n in constraints.include else "저인기 조합 구성 번호",
        }
        for n in numbers
    ]
    return {"slot_rule": "unpopular", "numbers": numbers, "traits": traits, "detail": detail}


def _rule_picks(slot_rule: str, snapshot: Snapshot, exclude: set[int], rng) -> list[dict]:
    if slot_rule == "biased":
        high_pool, low_pool = _pools(snapshot.recent)
    else:
        high_pool, low_pool = _pools(snapshot.alltime)

    if slot_rule == "all_high":
        return [
            {"number": r["number"], "ratio": r["ratio"], "source": "고확률(전체 6개)"}
            for r in _pick(high_pool, 6, exclude, rng)
        ]
    if slot_rule == "all_low":
        return [
            {"number": r["number"], "ratio": r["ratio"], "source": "저확률(전체 6개)"}
            for r in _pick(low_pool, 6, exclude, rng)
        ]
    if slot_rule == "biased":
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
            rng,
        )
        alltime_rank = {row["number"]: idx + 1 for idx, row in enumerate(snapshot.alltime)}
        recent_rank = {row["number"]: idx + 1 for idx, row in enumerate(snapshot.recent)}
        for p in picks:
            delta = alltime_rank[p["number"]] - recent_rank[p["number"]]
            if delta > 0:
                p["source"] += f" · 전체 누적 순위보다 {delta}계단 상승"
            elif delta < 0:
                p["source"] += f" · 전체 누적 순위보다 {-delta}계단 하락"
        return picks
    if slot_rule == "fixed":
        return _compose_3_2_1(
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
            rng,
        )
    return _compose_3_2_1(  # independent
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
        rng,
    )


def generate_combination(
    slot_rule: SlotRule = "independent",
    snapshot: Snapshot | None = None,
    constraints: Constraints | None = None,
    rng: random.Random | None = None,
) -> dict:
    """당첨번호 6개 조합을 만든다.
    - "independent"/"fixed": 전체 누적 출현빈도 상위 15(고확률)·하위 15(저확률) 풀에서
      3(고정 고확률) + 2(변동 슬롯) + 1(고정 저확률) 구성. 변동 슬롯 규칙은 슬롯모드 참고.
    - "all_high"/"all_low": 6개 전부 고확률 또는 저확률 풀에서 선택.
    - "biased": 위와 같은 3:2:1 구성이지만 전체 누적 대신 최근 window회차 출현빈도
      기준 풀을 사용 ("혹시 편향이 있다면" 가정의 실험 모드, 근거는 약함).
    - "unpopular": 당첨 확률은 다른 조합과 동일하다. 대신 사람들이 실제로 덜 고르는
      특징(32~45 비중, 연속/등차수열, 극단적 합계 등)을 일부러 포함시켜, 당첨 시
      상금을 나눠 가질 인원을 줄이는 것이 목적.

    constraints가 있으면 제외수는 풀에서 빼고, 고정수는 규칙이 뽑은 번호 중 일부를
    무작위로 대체하며, 홀짝·합계 조건은 만족할 때까지 다시 뽑는다.
    """
    snapshot = snapshot or load_snapshot()
    constraints = constraints or Constraints()
    rng = rng or random

    if slot_rule == "unpopular":
        return _generate_unpopular_combination(snapshot, constraints, rng)

    ratio_lookup = snapshot.alltime_ratio
    for _ in range(CONSTRAINT_MAX_ATTEMPTS):
        picks = _rule_picks(slot_rule, snapshot, set(constraints.exclude | constraints.include), rng)
        if constraints.include:
            keep = rng.sample(picks, 6 - len(constraints.include))
            picks = keep + [
                {"number": n, "ratio": ratio_lookup.get(n, 0.0), "source": "고정수(직접 지정)"}
                for n in constraints.include
            ]
        numbers = sorted(p["number"] for p in picks)
        if constraints.accepts(numbers):
            picks.sort(key=lambda p: p["number"])
            return {"slot_rule": slot_rule, "numbers": numbers, "detail": picks}

    raise GenerationError("조건을 만족하는 조합을 찾지 못했습니다. 홀짝·합계 조건을 완화하거나 다른 규칙을 골라보세요.")


def generate_combinations(
    slot_rule: SlotRule = "independent",
    count: int = 5,
    snapshot: Snapshot | None = None,
    constraints: Constraints | None = None,
    rng: random.Random | None = None,
) -> list[dict]:
    """서로 다른 조합 count개를 생성한다 (중복 조합은 걸러내고 다시 뽑음)."""
    snapshot = snapshot or load_snapshot()
    results: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    max_attempts = count * 20
    attempts = 0
    while len(results) < count and attempts < max_attempts:
        attempts += 1
        result = generate_combination(slot_rule, snapshot, constraints, rng)
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
