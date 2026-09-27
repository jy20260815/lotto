"""규칙별 백테스트: 과거 각 회차 직전까지의 데이터만으로 번호를 생성해 그 회차
결과와 맞춰본다. 모든 조합의 당첨 확률은 같으므로, 규칙들이 무작위 선택이나
이론 기댓값과 비슷하게 나오는 것이 정상이다."""

import random
from math import comb

from .check import rank_of
from .db import get_connection
from .generate import VALID_RULES, generate_combinations, snapshot_from_draws

RANDOM_RULE = "random"
TOTAL_COMBINATIONS = comb(45, 6)
RANK_PROBABILITY = {
    1: 1 / TOTAL_COMBINATIONS,
    2: comb(6, 5) * 1 / TOTAL_COMBINATIONS,
    3: comb(6, 5) * (45 - 6 - 1) / TOTAL_COMBINATIONS,
    4: comb(6, 4) * comb(39, 2) / TOTAL_COMBINATIONS,
    5: comb(6, 3) * comb(39, 3) / TOTAL_COMBINATIONS,
}
EXPECTED_MATCHES = 6 * 6 / 45  # 티켓 한 장의 평균 일치 개수


def _load_draws() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM draws ORDER BY round").fetchall()
    finally:
        conn.close()
    return [
        {"round": row["round"], "numbers": [row[f"num{i}"] for i in range(1, 7)], "bonus": row["bonus"]}
        for row in rows
    ]


def _empty_tally() -> dict:
    return {"tickets": 0, "matches": 0, "ranks": {r: 0 for r in range(1, 6)}}


def run_backtest(rounds: int = 100, tickets: int = 5, seed: int | None = None) -> dict:
    draws = _load_draws()
    if len(draws) < 2:
        raise RuntimeError("백테스트에 필요한 회차 데이터가 부족합니다.")
    rounds = min(rounds, len(draws) - 1)
    rng = random.Random(seed)
    rules = (*VALID_RULES, RANDOM_RULE)
    tally = {rule: _empty_tally() for rule in rules}

    all_numbers = [d["numbers"] for d in draws]
    for idx in range(len(draws) - rounds, len(draws)):
        target = draws[idx]
        winning = set(target["numbers"])
        snapshot = snapshot_from_draws(all_numbers[:idx])
        for rule in rules:
            if rule == RANDOM_RULE:
                combos = [sorted(rng.sample(range(1, 46), 6)) for _ in range(tickets)]
            else:
                combos = [c["numbers"] for c in generate_combinations(rule, tickets, snapshot, rng=rng)]
            t = tally[rule]
            for numbers in combos:
                t["tickets"] += 1
                t["matches"] += len(winning & set(numbers))
                rank = rank_of(numbers, winning, target["bonus"])
                if rank:
                    t["ranks"][rank] += 1

    results = []
    for rule in rules:
        t = tally[rule]
        results.append(
            {
                "rule": rule,
                "tickets": t["tickets"],
                "avg_matches": t["matches"] / t["tickets"],
                "ranks": t["ranks"],
                "wins": sum(t["ranks"].values()),
            }
        )

    total_tickets = rounds * tickets
    return {
        "rounds": rounds,
        "tickets_per_round": tickets,
        "from_round": draws[-rounds]["round"],
        "to_round": draws[-1]["round"],
        "results": results,
        "expected": {
            "avg_matches": EXPECTED_MATCHES,
            "ranks": {r: p * total_tickets for r, p in RANK_PROBABILITY.items()},
            "wins": sum(RANK_PROBABILITY.values()) * total_tickets,
        },
    }
