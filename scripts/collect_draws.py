import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lotto.db import init_db
from lotto.collect import collect_all
from lotto.stats import compute_number_stats, compute_recent_number_stats


def main() -> None:
    init_db()

    print("당첨번호 수집 중...")
    inserted = collect_all()
    print(f"신규 회차 {inserted}건 저장 완료")

    print("출현 빈도 통계 계산 중...")
    compute_number_stats()
    compute_recent_number_stats()
    print("완료")


if __name__ == "__main__":
    main()
