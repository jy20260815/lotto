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
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT = 15
LATEST_ROUND_RETRIES = 5
LATEST_ROUND_RETRY_DELAY_SECONDS = 60


def _get_with_retry(session: requests.Session, url: str, **kwargs) -> requests.Response:
    """추첨 직후처럼 접속이 몰리는 시간대의 일시적 지연/오류를 버티기 위한 재시도 래퍼."""
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
    raise RuntimeError(f"페이지 요청 실패 ({url})") from last_error


def new_session() -> requests.Session:
    """A session cookie from the result page is required before the
    batch API accepts requests."""
    session = requests.Session()
    session.headers.update(HEADERS)
    _get_with_retry(session, RESULT_PAGE_URL)
    return session


def fetch_latest_round(session: requests.Session) -> int:
    """점검/대기열 안내 페이지가 200으로 내려오는 경우가 있어, 회차 번호가 없으면
    잠시 기다렸다가 다시 시도한다."""
    for attempt in range(LATEST_ROUND_RETRIES + 1):
        resp = _get_with_retry(session, RESULT_PAGE_URL)
        match = re.search(r'id="opt_val"\s+value="(\d+)"', resp.text)
        if match:
            return int(match.group(1))
        if attempt < LATEST_ROUND_RETRIES:
            time.sleep(LATEST_ROUND_RETRY_DELAY_SECONDS)
    raise RuntimeError("최신 회차 번호를 찾을 수 없습니다 (페이지 구조 변경 가능성)")


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
            resp = session.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("list") or []
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
    raise RuntimeError(f"배치 조회 실패 (dir={direction}, epsd={epsd})") from last_error
