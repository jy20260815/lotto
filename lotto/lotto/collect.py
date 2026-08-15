import time

from .db import get_connection
from .fetch import fetch_batch, fetch_latest_round, new_session

REQUEST_DELAY_SECONDS = 0.3


def _existing_rounds(conn) -> set[int]:
    rows = conn.execute("SELECT round FROM draws").fetchall()
    return {row["round"] for row in rows}


def _insert_draw(conn, item: dict) -> None:
    raw_date = item["ltRflYmd"]
    draw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
    conn.execute(
        """
        INSERT OR IGNORE INTO draws
            (round, draw_date, num1, num2, num3, num4, num5, num6, bonus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["ltEpsd"],
            draw_date,
            item["tm1WnNo"],
            item["tm2WnNo"],
            item["tm3WnNo"],
            item["tm4WnNo"],
            item["tm5WnNo"],
            item["tm6WnNo"],
            item["bnsWnNo"],
        ),
    )


def collect_all() -> int:
    """Collect every round from 1 up to the latest, walking backwards in
    batches of 10 via the site's paging API. Rounds already present in
    the DB are kept but not re-inserted. Returns newly inserted count."""
    conn = get_connection()
    inserted = 0
    try:
        existing = _existing_rounds(conn)
        session = new_session()
        latest = fetch_latest_round(session)

        if len(existing) >= latest and all(r in existing for r in range(1, latest + 1)):
            return 0

        cursor = latest
        first_batch = True
        while cursor >= 1:
            if first_batch:
                batch = fetch_batch(session, "center", latest)
                first_batch = False
            else:
                batch = fetch_batch(session, "older", cursor)

            if not batch:
                break

            for item in batch:
                round_no = item["ltEpsd"]
                if round_no not in existing:
                    _insert_draw(conn, item)
                    existing.add(round_no)
                    inserted += 1

            conn.commit()
            cursor = min(item["ltEpsd"] for item in batch)
            time.sleep(REQUEST_DELAY_SECONDS)
    finally:
        conn.close()
    return inserted
