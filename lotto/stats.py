from datetime import datetime, timezone

from .db import get_connection

_FREQUENCY_QUERY = """
SELECT number, COUNT(*) AS appear_count
FROM (
    SELECT num1 AS number FROM draws
    UNION ALL SELECT num2 FROM draws
    UNION ALL SELECT num3 FROM draws
    UNION ALL SELECT num4 FROM draws
    UNION ALL SELECT num5 FROM draws
    UNION ALL SELECT num6 FROM draws
)
GROUP BY number
"""

DEFAULT_RECENT_WINDOW = 100

_RECENT_FREQUENCY_QUERY = """
SELECT number, COUNT(*) AS appear_count
FROM (
    SELECT num1 AS number, round FROM draws
    UNION ALL SELECT num2, round FROM draws
    UNION ALL SELECT num3, round FROM draws
    UNION ALL SELECT num4, round FROM draws
    UNION ALL SELECT num5, round FROM draws
    UNION ALL SELECT num6, round FROM draws
)
WHERE round > (SELECT MAX(round) FROM draws) - ?
GROUP BY number
"""


def compute_number_stats() -> None:
    """Recompute 1~45 appearance counts/ratios from the draws table and
    upsert them into number_stats."""
    conn = get_connection()
    try:
        total_draws = conn.execute("SELECT COUNT(*) AS n FROM draws").fetchone()["n"]
        if total_draws == 0:
            return

        counts = {row["number"]: row["appear_count"] for row in conn.execute(_FREQUENCY_QUERY)}
        updated_at = datetime.now(timezone.utc).isoformat()

        rows = [
            (number, counts.get(number, 0), total_draws, counts.get(number, 0) / total_draws, updated_at)
            for number in range(1, 46)
        ]
        conn.executemany(
            """
            INSERT INTO number_stats (number, appear_count, total_draws, ratio, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(number) DO UPDATE SET
                appear_count = excluded.appear_count,
                total_draws = excluded.total_draws,
                ratio = excluded.ratio,
                updated_at = excluded.updated_at
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def compute_recent_number_stats(window: int = DEFAULT_RECENT_WINDOW) -> None:
    """최근 window회차만 대상으로 출현 빈도/비율을 계산해 number_stats_recent에
    upsert한다 (편향 가정 모드용, docs/plan_bias_unpopular.md 1-2 참고)."""
    conn = get_connection()
    try:
        total_draws = conn.execute("SELECT COUNT(*) AS n FROM draws").fetchone()["n"]
        if total_draws == 0:
            return

        actual_window = min(window, total_draws)
        counts = {
            row["number"]: row["appear_count"]
            for row in conn.execute(_RECENT_FREQUENCY_QUERY, (actual_window,))
        }
        updated_at = datetime.now(timezone.utc).isoformat()

        rows = [
            (
                number,
                counts.get(number, 0),
                actual_window,
                counts.get(number, 0) / actual_window,
                actual_window,
                updated_at,
            )
            for number in range(1, 46)
        ]
        conn.executemany(
            """
            INSERT INTO number_stats_recent (number, appear_count, total_draws, ratio, window_size, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(number) DO UPDATE SET
                appear_count = excluded.appear_count,
                total_draws = excluded.total_draws,
                ratio = excluded.ratio,
                window_size = excluded.window_size,
                updated_at = excluded.updated_at
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()
