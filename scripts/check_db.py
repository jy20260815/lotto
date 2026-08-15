import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lotto.db import get_connection


def main() -> None:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS n FROM draws").fetchone()["n"]
        if total == 0:
            print("draws 테이블이 비어 있습니다. python scripts/collect_draws.py를 먼저 실행하세요.")
            return

        span = conn.execute("SELECT MIN(round) AS lo, MAX(round) AS hi FROM draws").fetchone()
        latest = conn.execute("SELECT * FROM draws ORDER BY round DESC LIMIT 1").fetchone()
        stats_sum_row = conn.execute("SELECT SUM(appear_count) AS s FROM number_stats").fetchone()
        stats_sum = stats_sum_row["s"]
        expected = total * 6

        print(f"총 회차 수: {total}건 ({span['lo']}회 ~ {span['hi']}회)")
        print(
            f"최신 회차: {latest['round']}회 ({latest['draw_date']}) - "
            f"{latest['num1']}, {latest['num2']}, {latest['num3']}, "
            f"{latest['num4']}, {latest['num5']}, {latest['num6']} + 보너스 {latest['bonus']}"
        )
        ok = stats_sum == expected
        print(
            f"number_stats 정합성: SUM(appear_count)={stats_sum} (기대값 {expected}) "
            f"-> {'정상' if ok else '불일치! python scripts/collect_draws.py를 다시 실행하세요'}"
        )

        top5 = conn.execute(
            "SELECT number, appear_count, ratio FROM number_stats ORDER BY ratio DESC LIMIT 5"
        ).fetchall()
        bottom5 = conn.execute(
            "SELECT number, appear_count, ratio FROM number_stats ORDER BY ratio ASC LIMIT 5"
        ).fetchall()

        print("\n출현빈도 상위 5개:")
        for r in top5:
            print(f"  {r['number']:>2} - {r['appear_count']}회 ({r['ratio'] * 100:.1f}%)")

        print("출현빈도 하위 5개:")
        for r in bottom5:
            print(f"  {r['number']:>2} - {r['appear_count']}회 ({r['ratio'] * 100:.1f}%)")

        recent_row = conn.execute(
            "SELECT SUM(appear_count) AS s, MAX(window_size) AS w FROM number_stats_recent"
        ).fetchone()
        if recent_row["s"] is None:
            print("\nnumber_stats_recent가 비어 있습니다. python scripts/collect_draws.py를 다시 실행하세요.")
        else:
            window = recent_row["w"]
            recent_expected = window * 6
            recent_ok = recent_row["s"] == recent_expected
            print(
                f"\nnumber_stats_recent 정합성 (window={window}): SUM(appear_count)={recent_row['s']} "
                f"(기대값 {recent_expected}) -> {'정상' if recent_ok else '불일치! 다시 수집을 실행하세요'}"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
