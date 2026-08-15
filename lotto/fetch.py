import re
import time
from typing import Optional

import requests

RESULT_PAGE_URL = "https://www.dhlottery.co.kr/lt645/result"
API_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": RESULT_PAGE_URL,
}
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1.0


def new_session() -> requests.Session:
    """A session cookie from the result page is required before the
    batch API accepts requests."""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get(RESULT_PAGE_URL, timeout=10)
    return session


def fetch_latest_round(session: requests.Session) -> int:
    resp = session.get(RESULT_PAGE_URL, timeout=10)
    resp.raise_for_status()
    match = re.search(r'id="opt_val"\s+value="(\d+)"', resp.text)
    if not match:
        raise RuntimeError("최신 회차 번호를 찾을 수 없습니다 (페이지 구조 변경 가능성)")
    return int(match.group(1))


def fetch_batch(session: requests.Session, direction: str, epsd: int) -> list[dict]:
    """direction="center": 10 rounds ending at epsd (inclusive).
    direction="older": up to 10 rounds strictly below epsd."""
    params = {"srchDir": direction}
    if direction == "center":
        params["srchLtEpsd"] = str(epsd)
    else:
        params["srchCursorLtEpsd"] = str(epsd)

    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.get(API_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("list") or []
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
    raise RuntimeError(f"배치 조회 실패 (dir={direction}, epsd={epsd})") from last_error
