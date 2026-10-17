"""SQLite storage: services + persisted logs.  DB file: ~/.devlauncher/devlauncher.db

sqlite3 ships with Python, nothing to install. An old services.json is imported
automatically the first time and renamed to services.json.migrated.
"""
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from app.models import Service

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Data directory
CONFIG_DIR = PROJECT_DIR / "data"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database
DB_FILE = CONFIG_DIR / "devlauncher.db"

# Legacy JSON file
LEGACY_JSON = CONFIG_DIR / "services.json"

MAX_LOG_ROWS = 5000  # per service

SCHEMA = """
CREATE TABLE IF NOT EXISTS services (
    id          TEXT PRIMARY KEY,
    position    INTEGER NOT NULL,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'command',
    command     TEXT NOT NULL DEFAULT '',
    working_dir TEXT NOT NULL DEFAULT '',
    venv        TEXT NOT NULL DEFAULT '',
    env         TEXT NOT NULL DEFAULT '{}',
    target      TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT 'Custom',
    port        INTEGER NOT NULL DEFAULT 0,
    auto_start  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT NOT NULL,
    ts         REAL NOT NULL,
    text       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service_id, id);
"""

UPSERT = """
INSERT INTO services (id, position, name, kind, command, working_dir, venv, env,
                      target, category, port, auto_start)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    position=excluded.position, name=excluded.name, kind=excluded.kind,
    command=excluded.command, working_dir=excluded.working_dir, venv=excluded.venv,
    env=excluded.env, target=excluded.target, category=excluded.category,
    port=excluded.port, auto_start=excluded.auto_start
"""


def _connect() -> sqlite3.Connection:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def _row(position: int, s: Service) -> tuple:
    return (s.id, position, s.name, s.kind, s.command, s.working_dir, s.venv,
            json.dumps(s.env), s.target, s.category, int(s.port), int(s.auto_start))


def _to_service(r: tuple) -> Service:
    try:
        env = json.loads(r[7])
    except (json.JSONDecodeError, TypeError):
        env = {}
    return Service(id=r[0], name=r[2], kind=r[3], command=r[4], working_dir=r[5], venv=r[6],
                   env=env, target=r[8], category=r[9], port=r[10], auto_start=bool(r[11]))


def _migrate_legacy(conn: sqlite3.Connection) -> None:
    if not LEGACY_JSON.exists():
        return
    if conn.execute("SELECT COUNT(*) FROM services").fetchone()[0]:
        return
    try:
        data = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
        services = [Service.from_dict(item) for item in data]
    except (json.JSONDecodeError, OSError, TypeError):
        return
    with conn:
        conn.executemany(UPSERT, [_row(i, s) for i, s in enumerate(services)])
    try:
        LEGACY_JSON.rename(LEGACY_JSON.with_suffix(".json.migrated"))
    except OSError:
        pass


# ---- services ----------------------------------------------------------
def load_services() -> list:
    try:
        with closing(_connect()) as conn:
            _migrate_legacy(conn)
            rows = conn.execute(
                "SELECT id, position, name, kind, command, working_dir, venv, env, "
                "target, category, port, auto_start FROM services ORDER BY position"
            ).fetchall()
        return [_to_service(r) for r in rows]
    except sqlite3.Error:
        return []


def save_services(services: list) -> None:
    ids = [s.id for s in services]
    with closing(_connect()) as conn, conn:
        if ids:
            marks = ",".join("?" * len(ids))
            conn.execute(f"DELETE FROM services WHERE id NOT IN ({marks})", ids)
        else:
            conn.execute("DELETE FROM services")
        conn.executemany(UPSERT, [_row(i, s) for i, s in enumerate(services)])
        conn.execute("DELETE FROM logs WHERE service_id NOT IN (SELECT id FROM services)")


# ---- logs (best effort: never crash the app over a log) -----------------
def append_logs(rows: list) -> None:
    """rows: [(service_id, text), ...]"""
    if not rows:
        return
    now = time.time()
    try:
        with closing(_connect()) as conn, conn:
            conn.executemany(
                "INSERT INTO logs (service_id, ts, text) VALUES (?, ?, ?)",
                [(sid, now, text) for sid, text in rows],
            )
            for sid in {sid for sid, _ in rows}:
                conn.execute(
                    "DELETE FROM logs WHERE service_id=? AND id <= "
                    "(SELECT id FROM logs WHERE service_id=? ORDER BY id DESC LIMIT 1 OFFSET ?)",
                    (sid, sid, MAX_LOG_ROWS),
                )
    except sqlite3.Error:
        pass


def load_all_logs() -> dict:
    """-> {service_id: [chunk, chunk, ...]} oldest first."""
    logs: dict = {}
    try:
        with closing(_connect()) as conn:
            for sid, text in conn.execute("SELECT service_id, text FROM logs ORDER BY id"):
                logs.setdefault(sid, []).append(text)
    except sqlite3.Error:
        pass
    return logs


def clear_logs(service_id: str) -> None:
    try:
        with closing(_connect()) as conn, conn:
            conn.execute("DELETE FROM logs WHERE service_id=?", (service_id,))
    except sqlite3.Error:
        pass