"""통계 탭에 쓰는 요약 지표. number_stats 테이블과 달리 요청마다 draws에서 바로
계산하므로, 전체/최근 N회 등 원하는 구간을 자유롭게 볼 수 있다."""

from .db import get_connection

RANGE_BANDS = ((1, 10), (11, 20), (21, 30), (31, 40), (41, 45))
SUM_BUCKET_WIDTH = 20
SUM_BUCKET_START = 21
SUM_BUCKET_END = 255


def _load_rows(conn):
    return conn.execute("SELECT * FROM draws ORDER BY round").fetchall()


def summarize(window: int | None = None) -> dict:
    """window가 None이면 전체 회차, 아니면 최근 window회차 기준 요약."""
    conn = get_connection()
    try:
        rows = _load_rows(conn)
    finally:
        conn.close()
    if not rows:
        raise RuntimeError("draws가 비어있습니다. 먼저 데이터 수집을 실행하세요.")

    latest_round = rows[-1]["round"]
    scoped = rows[-window:] if window else rows
    draws = [[row[f"num{i}"] for i in range(1, 7)] for row in scoped]
    total = len(draws)

    counts = {n: 0 for n in range(1, 46)}
    last_seen: dict[int, int] = {}
    for row in rows:  # 미출현 기간은 구간과 무관하게 전체 회차에서 계산
        for i in range(1, 7):
            last_seen[row[f"num{i}"]] = row["round"]
    for nums in draws:
        for n in nums:
            counts[n] += 1

    numbers = [
        {
            "number": n,
            "count": counts[n],
            "ratio": counts[n] / total,
            "last_round": last_seen.get(n),
            "gap": latest_round - last_seen[n] if n in last_seen else None,
        }
        for n in range(1, 46)
    ]

    odd_even = [0] * 7
    for nums in draws:
        odd_even[sum(1 for n in nums if n % 2)] += 1

    ranges = []
    for lo, hi in RANGE_BANDS:
        size = hi - lo + 1
        appear = sum(counts[n] for n in range(lo, hi + 1))
        ranges.append(
            {
                "label": f"{lo}~{hi}",
                "count": appear,
                "share": appear / (total * 6),
                "expected_share": size / 45,
            }
        )

    sums = []
    start = SUM_BUCKET_START
    while start <= SUM_BUCKET_END:
        end = min(start + SUM_BUCKET_WIDTH - 1, SUM_BUCKET_END)
        sums.append({"label": f"{start}~{end}", "from": start, "to": end, "count": 0})
        start = end + 1
    for nums in draws:
        s = sum(nums)
        sums[(s - SUM_BUCKET_START) // SUM_BUCKET_WIDTH]["count"] += 1

    return {
        "window": window,
        "total_draws": total,
        "first_round": scoped[0]["round"],
        "latest_round": latest_round,
        "expected_ratio": 6 / 45,
        "numbers": numbers,
        "odd_even": [{"odd": k, "even": 6 - k, "count": c} for k, c in enumerate(odd_even)],
        "ranges": ranges,
        "sums": sums,
    }
