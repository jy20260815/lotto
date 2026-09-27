"""구매 시뮬레이션: 최근 각 회차에 무작위(자동) 번호를 N장씩 샀다면 등수별로 몇 장이 당첨됐을지.

적은 장수는 실제로 번호를 뽑아 맞춰보고, 많은 장수(수백만~천만 장)는 한 장씩 뽑는 대신
"무작위 N장의 등수별 장수"를 다항분포에서 바로 뽑는다. 무작위 번호 한 장의 등수 확률은
당첨번호와 무관하게 고정이므로 두 방법은 통계적으로 같은 결과를 준다.
"""

import random

from .backtest import RANK_PROBABILITY
from .check import rank_of, recent_draws

AMOUNTS = (5, 10, 50, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000)
DIRECT_SIMULATION_LIMIT = 1_000
TICKET_PRICE = 1_000


def _direct_counts(amount: int, draw: dict, rng: random.Random) -> dict[int, int]:
    winning = set(draw["numbers"])
    counts = {r: 0 for r in RANK_PROBABILITY}
    for _ in range(amount):
        rank = rank_of(rng.sample(range(1, 46), 6), winning, draw["bonus"])
        if rank:
            counts[rank] += 1
    return counts


def _multinomial_counts(amount: int, rng: random.Random) -> dict[int, int]:
    """다항분포를 이항분포의 연쇄로 뽑는다: 1등부터 차례로, 남은 장수 중 해당 등수 장수를 뽑음."""
    counts = {}
    remaining = amount
    remaining_prob = 1.0
    for rank, p in RANK_PROBABILITY.items():
        k = rng.binomialvariate(remaining, min(1.0, p / remaining_prob)) if remaining else 0
        counts[rank] = k
        remaining -= k
        remaining_prob -= p
    return counts


def simulate_purchases(rounds: int = 10, seed: int | None = None) -> dict:
    draws = list(reversed(recent_draws(rounds)))
    if not draws:
        raise RuntimeError("수집된 회차가 없습니다. 먼저 데이터 수집을 실행하세요.")
    rng = random.Random(seed)

    results = []
    for amount in AMOUNTS:
        per_round = []
        totals = {r: 0 for r in RANK_PROBABILITY}
        for draw in draws:
            if amount <= DIRECT_SIMULATION_LIMIT:
                counts = _direct_counts(amount, draw, rng)
            else:
                counts = _multinomial_counts(amount, rng)
            per_round.append({"round": draw["round"], "ranks": counts})
            for r, k in counts.items():
                totals[r] += k
        tickets = amount * len(draws)
        results.append(
            {
                "amount": amount,
                "method": "direct" if amount <= DIRECT_SIMULATION_LIMIT else "multinomial",
                "cost_per_round": amount * TICKET_PRICE,
                "total_cost": tickets * TICKET_PRICE,
                "per_round": per_round,
                "totals": totals,
                "expected": {r: p * tickets for r, p in RANK_PROBABILITY.items()},
                # 한 회차에서 1등이 한 장이라도 나올 확률
                "first_prize_chance": 1 - (1 - RANK_PROBABILITY[1]) ** amount,
            }
        )

    return {"draws": draws, "ticket_price": TICKET_PRICE, "results": results}
