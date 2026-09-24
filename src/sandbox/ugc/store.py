"""UGC pipeline store: SQLite tables, state-machine triggers, exports.

BigDomain P-47-3b (docs/spec/ugc-pipeline-spec.md section 2). One DB per
repo, tables split: the lobby event table and the token ledger live in
the same SQLite file (WAL, single writer), so the diverting reader and
the UGC intake share one database.

DB-layer law (same discipline as the ledger schema.sql):
  - items enter the state machine at 'pooled' only (INSERT trigger)
  - state moves follow the legal graph; terminal states are immutable
    (UPDATE trigger, AC-U9)
  - adopting a needs-CEO item without a CEO receipt aborts (UPDATE
    trigger, AC-U9); the needs_ceo flag freezes after the drafted stage
  - gate receipts open only for adopted items (INSERT trigger, AC-U10)

This module also hosts the shared error family so pipeline.py and
review.py raise one exception type without an import cycle.
Encoding discipline: this script stays ASCII; Chinese wordlists, labels
and copy live in config.json.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

REPO = "domain/BigDomain"

# error codes (ASCII; shared family for pipeline + review)
E_DUPLICATE = "E_DUPLICATE"                    # AC-U6 content replay
E_BAD_SOURCE = "E_BAD_SOURCE"
E_SOURCE_BLOCKED = "E_SOURCE_BLOCKED"          # live_danmaku reserved (AC-UP3)
E_ENTRANCE_REQUIRED = "E_ENTRANCE_REQUIRED"    # AC-U1 (C0 paid entrance)
E_RATE_LIMIT = "E_RATE_LIMIT"                  # AC-U1 (lobby AC-S9 params)
E_BAD_FRAME = "E_BAD_FRAME"
E_NOT_FOUND = "E_NOT_FOUND"
E_BAD_STATE = "E_BAD_STATE"
E_BAD_DECISION = "E_BAD_DECISION"
E_BAD_VERDICT = "E_BAD_VERDICT"                # AC-U3
E_REVIEW_DONE = "E_REVIEW_DONE"                # AC-U3 (no double verdict)
E_CONTENT_REJECTED = "E_CONTENT_REJECTED"     # gate family (sec_gate alias)
E_BAD_TRANSITION = "E_BAD_TRANSITION"          # trigger: state legality
E_ITEM_MUST_ENTER_POOLED = "E_ITEM_MUST_ENTER_POOLED"
E_CEO_RECEIPT_REQUIRED = "E_CEO_RECEIPT_REQUIRED"
E_NEEDS_CEO_IMMUTABLE = "E_NEEDS_CEO_IMMUTABLE"
E_RECEIPT_REQUIRES_ADOPTED = "E_RECEIPT_REQUIRES_ADOPTED"

_TRIGGER_CODES = (E_BAD_TRANSITION, E_ITEM_MUST_ENTER_POOLED,
                  E_CEO_RECEIPT_REQUIRED, E_NEEDS_CEO_IMMUTABLE,
                  E_RECEIPT_REQUIRES_ADOPTED)


class PipelineError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


def utc_now_iso():
    """Canonical UTC timestamp (same dialect as the lobby store)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def parse_iso(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS ugc_events (      -- original intake rows
  evt_id   TEXT PRIMARY KEY,                 -- content-addressed (AC-U6)
  ts_utc   TEXT NOT NULL, type TEXT NOT NULL,
  actor    TEXT NOT NULL,                    -- census avatar id (AC-L11 same origin)
  repo     TEXT NOT NULL,
  zone     TEXT NOT NULL,                    -- source enum
  summary  TEXT NOT NULL,                     -- normalized content
  payload_json TEXT
);
CREATE TABLE IF NOT EXISTS ugc_items (       -- state machine body (1:1 = evt_id)
  item_id  TEXT PRIMARY KEY, line TEXT NOT NULL,
  state    TEXT NOT NULL CHECK (state IN ('pooled','drafted','final_review',
              'needs_ceo_review','adopted','rejected','chronicled')),
  gate_status TEXT NOT NULL CHECK (gate_status IN ('pass','review','risky')),
  producer TEXT NOT NULL DEFAULT 'rule_template'
              CHECK (producer IN ('rule_template','local_llm','human')),
  ai_generated INTEGER NOT NULL DEFAULT 0,   -- =1 iff producer='local_llm'
  needs_ceo INTEGER NOT NULL DEFAULT 0,
  duplicate_of TEXT, decision TEXT, ts_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_queue (    -- gray-zone human review (AC-U3)
  evt_id TEXT PRIMARY KEY,
  verdict TEXT CHECK (verdict IN ('pass','risky')),   -- NULL = suspended
  reviewer TEXT, ts_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gate_receipts (   -- receipts = ledger share ref face
  evt_id TEXT PRIMARY KEY, gate TEXT NOT NULL, ts_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ugc_ingest_log (  -- mechanical: diverting-reader idempotence
  origin_evt_id TEXT PRIMARY KEY, status TEXT NOT NULL, ts_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ugc_entrance (    -- mechanical: mock entrance (prod = P-47-4)
  actor TEXT PRIMARY KEY, granted_utc TEXT NOT NULL, ttl_seconds INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ugc_drafts (       -- mechanical: rule-template draft body
  item_id TEXT PRIMARY KEY, draft_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ceo_receipts (     -- mechanical: approval trace (AC-U9 trigger dep)
  item_id TEXT PRIMARY KEY, decision TEXT NOT NULL, ts_utc TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS ugc_item_enter_pooled
BEFORE INSERT ON ugc_items
WHEN NEW.state <> 'pooled'
BEGIN SELECT RAISE(ABORT, 'E_ITEM_MUST_ENTER_POOLED'); END;
CREATE TRIGGER IF NOT EXISTS ugc_state_legality
BEFORE UPDATE ON ugc_items
WHEN NEW.state IS NOT OLD.state AND NOT (
     (OLD.state = 'pooled' AND NEW.state = 'drafted')
  OR (OLD.state = 'drafted' AND NEW.state = 'final_review')
  OR (OLD.state = 'final_review' AND NEW.state IN ('adopted','rejected','needs_ceo_review'))
  OR (OLD.state = 'needs_ceo_review' AND NEW.state IN ('adopted','rejected'))
  OR (OLD.state = 'rejected' AND NEW.state = 'chronicled'))
BEGIN SELECT RAISE(ABORT, 'E_BAD_TRANSITION'); END;
CREATE TRIGGER IF NOT EXISTS ugc_ceo_receipt_gate
BEFORE UPDATE ON ugc_items
WHEN NEW.state = 'adopted' AND OLD.needs_ceo = 1 AND NOT EXISTS
     (SELECT 1 FROM ceo_receipts WHERE item_id = OLD.item_id AND decision = 'approved')
BEGIN SELECT RAISE(ABORT, 'E_CEO_RECEIPT_REQUIRED'); END;
CREATE TRIGGER IF NOT EXISTS ugc_needs_ceo_freeze
BEFORE UPDATE ON ugc_items
WHEN NEW.needs_ceo IS NOT OLD.needs_ceo
     AND OLD.state NOT IN ('pooled','drafted','final_review')
BEGIN SELECT RAISE(ABORT, 'E_NEEDS_CEO_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS ugc_receipt_discipline
BEFORE INSERT ON gate_receipts
WHEN NOT EXISTS (SELECT 1 FROM ugc_items WHERE item_id = NEW.evt_id AND state = 'adopted')
BEGIN SELECT RAISE(ABORT, 'E_RECEIPT_REQUIRES_ADOPTED'); END;
"""


class UGCStore:
    """Single-writer store: one connection guarded by one lock; every
    multi-statement write opens with BEGIN IMMEDIATE (SQLite WAL)."""

    def __init__(self, db_path):
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- raw faces (locked) -------------------------------------------------

    def read(self, sql, args=()):
        with self._lock:
            return self._conn.execute(sql, args).fetchall()

    def read_one(self, sql, args=()):
        with self._lock:
            return self._conn.execute(sql, args).fetchone()

    def write(self, sql, args=()):
        with self._lock:
            try:
                self._conn.execute(sql, args)
            except sqlite3.IntegrityError as exc:
                raise self._map_integrity(exc)

    def write_tx(self, statements):
        """[(sql, args), ...] inside one BEGIN IMMEDIATE transaction."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                for sql, args in statements:
                    self._conn.execute(sql, args)
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                self._conn.execute("ROLLBACK")
                raise self._map_integrity(exc) from None
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise

    @staticmethod
    def _map_integrity(exc):
        msg = str(exc)
        for code in _TRIGGER_CODES:
            if code in msg:
                return PipelineError(code, msg)
        if "ugc_events.evt_id" in msg or "review_queue.evt_id" in msg:
            return PipelineError(E_DUPLICATE, msg)
        return exc

    # -- events -------------------------------------------------------------

    def insert_event(self, evt_id, ts, actor, source, content, payload):
        self.write(
            "INSERT INTO ugc_events (evt_id, ts_utc, type, actor, repo, zone, summary,"
            " payload_json) VALUES (?,?,?,?,?,?,?,?)",
            (evt_id, ts, "ugc.submit", actor, REPO, source, content,
             json.dumps(payload, ensure_ascii=False, sort_keys=True)))
        return evt_id

    def event_row(self, evt_id):
        return self.read_one("SELECT * FROM ugc_events WHERE evt_id = ?", (evt_id,))

    def content_seen(self, content, exclude_evt_id):
        row = self.read_one(
            "SELECT evt_id FROM ugc_events WHERE summary = ? AND evt_id <> ?"
            " ORDER BY ts_utc LIMIT 1", (content, exclude_evt_id))
        return row["evt_id"] if row else None

    def count_recent(self, actor, cutoff_ts):
        row = self.read_one(
            "SELECT COUNT(*) FROM ugc_events WHERE actor = ? AND ts_utc >= ?",
            (actor, cutoff_ts))
        return int(row[0])

    def events_count(self):
        return int(self.read_one("SELECT COUNT(*) FROM ugc_events")[0])

    # -- lobby diverting reader (one DB, tables split) -----------------------

    def lobby_intake_rows(self):
        have = self.read_one(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'events'")
        if not have:
            return []
        return self.read(
            "SELECT evt_id, type, actor, payload_json FROM events"
            " WHERE type IN ('idea.submit','avatar.intake')"
            " AND evt_id NOT IN (SELECT origin_evt_id FROM ugc_ingest_log)"
            " ORDER BY ts_utc")

    def mark_ingest(self, origin_evt_id, status, ts):
        self.write("INSERT OR REPLACE INTO ugc_ingest_log (origin_evt_id, status, ts_utc)"
                   " VALUES (?,?,?)", (origin_evt_id, status, ts))

    # -- entrance (sandbox mock; production = P-47-4 payment receipt) --------

    def entrance_grant(self, actor, ttl, ts=None):
        self.write("INSERT OR REPLACE INTO ugc_entrance (actor, granted_utc, ttl_seconds)"
                   " VALUES (?,?,?)", (actor, ts or utc_now_iso(), int(ttl)))

    def entrance_valid(self, actor):
        row = self.read_one(
            "SELECT granted_utc, ttl_seconds FROM ugc_entrance WHERE actor = ?", (actor,))
        if not row:
            return False
        granted = parse_iso(row["granted_utc"])
        now = datetime.now(timezone.utc)
        return (now - granted).total_seconds() <= int(row["ttl_seconds"])

    # -- items + state machine ----------------------------------------------

    def insert_item(self, item_id, line, duplicate_of, ts,
                    gate_status="pass", needs_ceo=0):
        self.write(
            "INSERT INTO ugc_items (item_id, line, state, gate_status, producer,"
            " ai_generated, needs_ceo, duplicate_of, decision, ts_utc)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (item_id, line, "pooled", gate_status, "rule_template", 0, needs_ceo,
             duplicate_of, None, ts))

    def item_row(self, item_id):
        return self.read_one("SELECT * FROM ugc_items WHERE item_id = ?", (item_id,))

    def items_in_states(self, states, line=None):
        sql = ("SELECT i.*, e.summary AS content, e.actor AS author, e.zone AS source"
               " FROM ugc_items i JOIN ugc_events e ON e.evt_id = i.item_id"
               " WHERE i.state IN (%s)" % ",".join("?" * len(states)))
        args = list(states)
        if line is not None:
            sql += " AND i.line = ?"
            args.append(line)
        sql += " ORDER BY i.ts_utc"
        return self.read(sql, args)

    def items_count(self, where="1=1", args=()):
        return int(self.read_one("SELECT COUNT(*) FROM ugc_items WHERE " + where, args)[0])

    def set_state(self, item_id, new_state, decision=None, needs_ceo=None):
        sets, args = ["state = ?"], [new_state]
        if decision is not None:
            sets.append("decision = ?")
            args.append(decision)
        if needs_ceo is not None:
            sets.append("needs_ceo = ?")
            args.append(int(needs_ceo))
        args.append(item_id)
        self.write("UPDATE ugc_items SET " + ", ".join(sets) + " WHERE item_id = ?", args)

    def to_needs_ceo(self, item_id):
        """Landfall marking follows the legal graph (drafted ->
        final_review -> needs_ceo_review) inside one transaction, so no
        item is ever visible at final_review with needs_ceo still unset
        (no force-adopt window between the two moves, AC-U9)."""
        self.write_tx([
            ("UPDATE ugc_items SET state = 'final_review' WHERE item_id = ?",
             (item_id,)),
            ("UPDATE ugc_items SET state = 'needs_ceo_review', needs_ceo = 1"
             " WHERE item_id = ?", (item_id,)),
        ])

    def adopt_with_receipt(self, item_id, ts=None):
        """Adoption + receipt in one transaction; the receipt trigger is the
        AC-U10 discipline at the DB layer (adopted items only)."""
        ts = ts or utc_now_iso()
        self.write_tx([
            ("UPDATE ugc_items SET state = 'adopted', decision = 'adopted'"
             " WHERE item_id = ?", (item_id,)),
            ("INSERT INTO gate_receipts (evt_id, gate, ts_utc) VALUES (?,?,?)",
             (item_id, "pass", ts)),
        ])

    # -- review queue -------------------------------------------------------

    def review_open(self, evt_id, ts):
        self.write("INSERT INTO review_queue (evt_id, verdict, reviewer, ts_utc)"
                   " VALUES (?,NULL,NULL,?)", (evt_id, ts))

    def review_row(self, evt_id):
        return self.read_one("SELECT * FROM review_queue WHERE evt_id = ?", (evt_id,))

    def review_set_verdict(self, evt_id, verdict, reviewer, ts):
        self.write("UPDATE review_queue SET verdict = ?, reviewer = ?, ts_utc = ?"
                   " WHERE evt_id = ?", (verdict, reviewer, ts, evt_id))

    # -- drafts + ceo receipts ----------------------------------------------

    def save_draft(self, item_id, draft):
        self.write("INSERT OR REPLACE INTO ugc_drafts (item_id, draft_json) VALUES (?,?)",
                   (item_id, json.dumps(draft, ensure_ascii=False, sort_keys=True)))

    def draft_row(self, item_id):
        row = self.read_one("SELECT draft_json FROM ugc_drafts WHERE item_id = ?", (item_id,))
        return json.loads(row["draft_json"]) if row else None

    def ceo_receipt_upsert(self, item_id, decision, ts=None):
        self.write("INSERT OR REPLACE INTO ceo_receipts (item_id, decision, ts_utc)"
                   " VALUES (?,?,?)", (item_id, decision, ts or utc_now_iso()))

    def ceo_receipt(self, item_id):
        return self.read_one("SELECT * FROM ceo_receipts WHERE item_id = ?", (item_id,))

    # -- receipts (ledger share ref face) -----------------------------------

    def gate_receipt(self, evt_id):
        return self.read_one("SELECT * FROM gate_receipts WHERE evt_id = ?", (evt_id,))

    def gate_receipts_count(self):
        return int(self.read_one("SELECT COUNT(*) FROM gate_receipts")[0])
