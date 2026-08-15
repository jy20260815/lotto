import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "lotto.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS draws (
    round INTEGER PRIMARY KEY,
    draw_date TEXT NOT NULL,
    num1 INTEGER NOT NULL,
    num2 INTEGER NOT NULL,
    num3 INTEGER NOT NULL,
    num4 INTEGER NOT NULL,
    num5 INTEGER NOT NULL,
    num6 INTEGER NOT NULL,
    bonus INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS number_stats (
    number INTEGER PRIMARY KEY,
    appear_count INTEGER NOT NULL,
    total_draws INTEGER NOT NULL,
    ratio REAL NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS number_stats_recent (
    number INTEGER PRIMARY KEY,
    appear_count INTEGER NOT NULL,
    total_draws INTEGER NOT NULL,
    ratio REAL NOT NULL,
    window_size INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
