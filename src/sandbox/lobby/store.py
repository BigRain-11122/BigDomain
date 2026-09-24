"""Public event store: SQLite WAL single writer + content-addressed evt_id.

Row = group six-field core superset (ts_utc/type/actor/repo/zone/summary)
plus evt_id (content-addressed, UNIQUE). repo is fixed to domain/BigDomain.
Daily jsonl export = the compatibility layer (readable by later P-47-2
ledger tooling; same storage discipline, one DB in this repo, tables split
per P-47-2 schema decision).
"""

import hashlib
import json
import os
import sqlite3
import threading

REPO = "domain/BigDomain"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    evt_id TEXT PRIMARY KEY,
    ts_utc TEXT NOT NULL,
    type   TEXT NOT NULL,
    actor  TEXT NOT NULL,
    repo   TEXT NOT NULL,
    zone   TEXT NOT NULL,
    summary TEXT NOT NULL,
    payload_json TEXT
);
"""

_COLUMNS = "evt_id, ts_utc, type, actor, repo, zone, summary, payload_json"


def compute_evt_id(ts_utc, evt_type, actor, repo, zone, summary, payload_json):
    canonical = "|".join((ts_utc, evt_type, actor, repo, zone, summary, payload_json or ""))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class EventStore:
    """Single-writer store: one connection guarded by one lock; every write
    opens with BEGIN IMMEDIATE (SQLite WAL discipline)."""

    def __init__(self, db_path):
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(_SCHEMA)

    def append(self, ts_utc, evt_type, actor, zone, summary, payload=None, evt_id=None):
        """Insert one public event; returns evt_id. Replaying the exact same
        event raises sqlite3.IntegrityError (content-addressed dedup)."""
        payload_json = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True) if payload is not None else None
        )
        if evt_id is None:
            evt_id = compute_evt_id(ts_utc, evt_type, actor, REPO, zone, summary, payload_json)
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO events (" + _COLUMNS + ") VALUES (?,?,?,?,?,?,?,?)",
                    (evt_id, ts_utc, evt_type, actor, REPO, zone, summary, payload_json),
                )
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return evt_id

    def count(self, where="", args=()):
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM events " + where, args).fetchone()
        return int(row[0])

    def export_day(self, day, out_dir):
        """Export one UTC day to jsonl (compatibility layer). Returns (path, n)."""
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "events-" + day + ".jsonl")
        with self._lock:
            rows = self._conn.execute(
                "SELECT " + _COLUMNS + " FROM events WHERE substr(ts_utc, 1, 10) = ? ORDER BY ts_utc",
                (day,),
            ).fetchall()
        written = 0
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                obj = {
                    "evt_id": row[0],
                    "ts_utc": row[1],
                    "type": row[2],
                    "actor": row[3],
                    "repo": row[4],
                    "zone": row[5],
                    "summary": row[6],
                }
                if row[7]:
                    obj["payload"] = json.loads(row[7])
                handle.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
                written += 1
        return path, written

    def close(self):
        with self._lock:
            self._conn.close()
