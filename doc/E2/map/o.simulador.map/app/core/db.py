from __future__ import annotations
import sqlite3
import os

DB_PATH = os.getenv("OSIM_DB_PATH", "osim.db")

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn

def _ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scenarios(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        owner_id TEXT,
        data TEXT NOT NULL
    );
    """)
    conn.commit()
