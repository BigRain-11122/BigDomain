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
from datetime import datetime, timezone

REPO = "domain/BigDomain"


def utc_now_iso():
    """Canonical UTC timestamp for frames and event rows."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

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
CREATE TABLE IF NOT EXISTS census_cache (
    cid TEXT PRIMARY KEY,
    fields_json TEXT NOT NULL
);
"""

_COLUMNS = "evt_id, ts_utc, type, actor, repo, zone, summary, payload_json"


def compute_evt_id(ts_utc, evt_type, actor, repo, zone, summary, payload_json):
    canonical = "|".join((ts_utc, evt_type, actor, repo, zone, summary, payload_json or ""))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class EventStore:
    """Single-writer store: one connection guarded by one lock; every write
    opens with BEGIN IMMEDIATE (SQLite WAL discipline)."""

    def __init__(self, db_path, disclaimer=None):
        self.db_path = db_path
        # R1773 room-level message read face: the standing non-advisory
        # disclaimer carried by the read-face envelope. Legacy callers
        # construct without it (backward compatible); the read face
        # itself refuses fail-closed until a non-empty one is wired.
        # An EXPLICITLY provided empty/whitespace/non-str value is a
        # bad argument and rejected at construction.
        if disclaimer is not None and (
            not isinstance(disclaimer, str) or not disclaimer.strip()
        ):
            raise ValueError("E_STORE_NO_DISCLAIMER")
        self.disclaimer = disclaimer
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)

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

    def import_census(self, rows):
        """Replace the census cache from a git read-only import (whole-table
        refresh: the source jsonl is the truth, the cache is a query index
        per server-city section 2). Rows keep every source field; the public
        face filters by the whitelist at response time. Returns row count."""
        pairs = []
        for row in rows:
            cid = str(row.get("id", "")).strip()
            if cid:
                pairs.append((cid, json.dumps(row, ensure_ascii=False, sort_keys=True)))
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute("DELETE FROM census_cache")
                self._conn.executemany(
                    "INSERT OR REPLACE INTO census_cache (cid, fields_json) VALUES (?,?)",
                    pairs,
                )
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return len(pairs)

    def census_lookup(self, cid):
        """Return the full imported census row for cid, or None."""
        with self._lock:
            row = self._conn.execute(
                "SELECT fields_json FROM census_cache WHERE cid = ?", (cid,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def room_message_board(self):
        """R1773 room-level message read face: pure-read derivation over
        the public event stream. Per room (zone) chat message count and
        distinct active-actor count, aggregated read-only over
        type='chat.broadcast' rows (the server chat path lands broadcasts
        with zone=room). The events table stays append-only: this face
        holds no mutation statements and no cache counters - every call
        re-derives from the events table. Zone-ascending deterministic
        order, zero RNG. Envelope carries the standing non-advisory
        disclaimer (the lobby compliance face lives at the protocol
        layer, sys.risk_warning at connect; this read face keeps the
        same standing-discipline)."""
        if not self.disclaimer or not self.disclaimer.strip():
            raise ValueError("E_STORE_NO_DISCLAIMER")
        with self._lock:
            rows = self._conn.execute(
                "SELECT zone, COUNT(*), COUNT(DISTINCT actor) FROM events"
                " WHERE type = 'chat.broadcast' GROUP BY zone ORDER BY zone"
            ).fetchall()
        board = [
            {"room": room, "messages": int(n), "actors": int(k)}
            for room, n, k in rows
        ]
        return {"room_message_board": board, "disclaimer": self.disclaimer}

    def close(self):
        with self._lock:
            self._conn.close()
