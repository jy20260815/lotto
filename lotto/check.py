from .db import get_connection

RANK_LABELS = {1: "1등", 2: "2등", 3: "3등", 4: "4등", 5: "5등"}


def rank_of(numbers: list[int], winning: set[int], bonus: int) -> int | None:
    """로또 6/45 등수. 6개 일치 1등, 5개+보너스 2등, 5개 3등, 4개 4등, 3개 5등."""
    matched = len(set(numbers) & winning)
    if matched == 6:
        return 1
    if matched == 5:
        return 2 if bonus in numbers else 3
    if matched == 4:
        return 4
    if matched == 3:
        return 5
    return None


def _row_to_draw(row) -> dict:
    return {
        "round": row["round"],
        "draw_date": row["draw_date"],
        "numbers": [row[f"num{i}"] for i in range(1, 7)],
        "bonus": row["bonus"],
    }


def get_draw(round_no: int | None = None) -> dict | None:
    """round_no가 없으면 최신 회차를 돌려준다."""
    conn = get_connection()
    try:
        if round_no is None:
            row = conn.execute("SELECT * FROM draws ORDER BY round DESC LIMIT 1").fetchone()
        else:
            row = conn.execute("SELECT * FROM draws WHERE round = ?", (round_no,)).fetchone()
    finally:
        conn.close()
    return _row_to_draw(row) if row else None


def recent_draws(limit: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM draws ORDER BY round DESC LIMIT ?", (limit,)).fetchall()
    finally:
        conn.close()
    return [_row_to_draw(row) for row in rows]


def check_tickets(tickets: list[list[int]], draw: dict) -> list[dict]:
    winning = set(draw["numbers"])
    results = []
    for numbers in tickets:
        rank = rank_of(numbers, winning, draw["bonus"])
        results.append(
            {
                "numbers": sorted(numbers),
                "matched": sorted(set(numbers) & winning),
                "bonus_matched": draw["bonus"] in numbers,
                "rank": rank,
                "rank_label": RANK_LABELS.get(rank, "낙첨"),
            }
        )
    return results


def all_draws() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM draws ORDER BY round").fetchall()
    finally:
        conn.close()
    return [_row_to_draw(row) for row in rows]


def ticket_history(tickets: list[list[int]], best_round_limit: int = 3) -> dict:
    """조합마다 '역대 모든 회차에 이 번호를 샀다면' 등수별 당첨 횟수와 최고 일치 기록."""
    draws = all_draws()
    if not draws:
        return {"total_draws": 0, "latest": None, "results": []}
    latest = draws[-1]
    results = []
    for numbers in tickets:
        picked = set(numbers)
        ranks = {r: 0 for r in RANK_LABELS}
        best = 0
        best_rounds: list[int] = []
        for draw in draws:
            winning = set(draw["numbers"])
            matched = len(picked & winning)
            rank = rank_of(numbers, winning, draw["bonus"])
            if rank:
                ranks[rank] += 1
            if matched > best:
                best, best_rounds = matched, [draw["round"]]
            elif matched == best:
                best_rounds.append(draw["round"])
        results.append(
            {
                "numbers": sorted(numbers),
                "ranks": ranks,
                "best_match": best,
                "best_match_count": len(best_rounds),
                # 최고 일치 회차 중 최근 것부터 몇 개만
                "best_rounds": sorted(best_rounds, reverse=True)[:best_round_limit],
                "latest_overlap": len(picked & set(latest["numbers"])),
            }
        )
    return {"total_draws": len(draws), "latest": latest, "results": results}
