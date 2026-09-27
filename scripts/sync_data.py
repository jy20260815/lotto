"""GitHub Actions가 수집·커밋한 최신 data/lotto.db를 로컬로 받아온다.

수집은 GitHub Actions 한 곳에서만 하고 로컬은 git pull로 따라가기만 하므로,
같은 바이너리 DB를 양쪽에서 따로 수정해 충돌이 나는 일이 없다.
안전을 위해 main 브랜치이고 추적 중인 파일에 커밋 안 된 변경이 없을 때만
fast-forward pull을 하며, 그 외에는 건너뛰고 로그만 남긴다.

작업 스케줄러 등록: scripts/register_sync_task.ps1
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "sync_data.log"
BRANCH = "main"

sys.path.insert(0, str(ROOT))

from lotto.db import get_connection  # noqa: E402


def log(message: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def git(*args: str) -> subprocess.CompletedProcess:
    git_exe = shutil.which("git")
    if git_exe is None:
        raise RuntimeError("git 실행 파일을 찾을 수 없습니다")
    return subprocess.run(
        [git_exe, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def latest_label() -> str:
    conn = get_connection()
    try:
        row = conn.execute("SELECT round, draw_date FROM draws ORDER BY round DESC LIMIT 1").fetchone()
    finally:
        conn.close()
    return f"{row['round']}회 ({row['draw_date']})" if row else "데이터 없음"


def main() -> int:
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch != BRANCH:
        log(f"건너뜀: 현재 브랜치가 {branch}입니다 ({BRANCH}에서만 자동 갱신)")
        return 0

    dirty = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
    if dirty:
        log("건너뜀: 커밋되지 않은 변경이 있습니다\n" + dirty)
        return 0

    before = latest_label()
    result = git("pull", "--ff-only", "origin", BRANCH)
    if result.returncode != 0:
        log(f"실패: git pull\n{result.stderr.strip()}")
        return 1

    after = latest_label()
    if before == after:
        log(f"변경 없음: {after}")
    else:
        log(f"갱신 완료: {before} -> {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
