"""Batch + degradation face for the UGC msgSecCheck gate (P2 tech item).

Implements the pre-registered criteria AC-SB1..AC-SB7 from
state/queue/tech.md (R1681 claim row, registered BEFORE this code;
honesty law: criteria table first, implementation second).

Two faces, both honest about the sandbox stand-in:
  1. batch face: one call gates N texts through the SAME gate product
     (lobby SecGate - referenced, not copied). Batch semantics add a
     wall-clock budget per chunk; verdicts are per-text and identical
     to per-text gate calls (AC-SB2). A p95 profile face measures the
     wordlist-mock batch overhead floor across sizes (AC-SB3); the
     production msgSecCheck p95 belongs to the bootstrap wiring window
     (CEO physical items; no fabricated platform thresholds here).
  2. degradation face: when the batch budget is breached mid-chunk or
     the gate fails at runtime, the UNGATED texts never pass and never
     vanish - they land in a persistent degraded banner queue (this
     module's OWN sqlite file, R1254 reminder.py single-writer
     precedent; zero ugc.db schema touch). Rows ARE the queue (R1254
     semantics): banner_queue() reads them, drain() re-gates them
     idempotently once the gate recovers (fail-closed: a gate hit on
     drain stays rejected forever).

Encoding discipline: this script stays ASCII; config lives in
config.json (the sec_batch section is optional - module defaults run
with zero shipped config changes).

Run (readiness self-check):
    python sec_batch.py
    python sec_batch.py --config config.json --db data/sec_degraded.db
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
for _p in (_LOBBY, BASE):
    # BASE ahead of the lobby dir; sec_gate comes from the lobby
    # product (referenced, not copied) - same import pattern as
    # pipeline.py in this package
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import ContentRejectedError, GateOfflineError, SecGate  # noqa: E402

# queue row vocabulary (ASCII)
R_BUDGET = "budget_breach"
R_GATE_ERR = "gate_error"
ST_QUEUED = "queued"
ST_DRAINED_PASS = "drained_pass"
ST_DRAINED_REJ = "drained_rejected"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sec_degraded_queue (
  qid        TEXT PRIMARY KEY,
  source     TEXT NOT NULL,
  actor      TEXT NOT NULL,
  content    TEXT NOT NULL,
  reason     TEXT NOT NULL CHECK (reason IN ('budget_breach','gate_error')),
  status     TEXT NOT NULL CHECK (status IN
             ('queued','drained_pass','drained_rejected')),
  ts_utc     TEXT NOT NULL,
  ts_drained TEXT
);
"""


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _qid(source, actor, content):
    """Idempotency key over (source, actor, content): the same content
    degrades onto one row no matter how many times it is re-landed."""
    canonical = "|".join(("secq", str(source), str(actor), str(content)))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _pct(sorted_ms, p):
    """Linear-interpolation percentile over an already-sorted list."""
    if not sorted_ms:
        return 0.0
    if len(sorted_ms) == 1:
        return sorted_ms[0]
    rank = (len(sorted_ms) - 1) * float(p)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_ms) - 1)
    frac = rank - lo
    return sorted_ms[lo] + (sorted_ms[hi] - sorted_ms[lo]) * frac


class SecBatchFace(object):
    """Batch gate wrapper + single writer of sec_degraded.db."""

    def __init__(self, gate, db_path, config=None, clock=None):
        cfg = (config or {}).get("sec_batch", {}) or {}
        self.gate = gate
        self.budget_s = float(cfg.get("budget_ms", 200.0)) / 1000.0
        if self.budget_s < 0:
            raise ValueError("budget_ms must be >= 0")
        self.max_batch = int(cfg.get("max_batch", 200))
        if self.max_batch <= 0:
            raise ValueError("max_batch must be positive")
        self.clock = clock or time.monotonic
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.isolation_level = None
        # executescript would auto-commit the open transaction, so the
        # DDL rides one explicit BEGIN IMMEDIATE (reminder.py precedent)
        self._exec("BEGIN IMMEDIATE")
        for stmt in SCHEMA.split(";"):
            if stmt.strip():
                self.conn.execute(stmt)
        self._exec("COMMIT")

    # ---------------- low-level helpers ----------------

    def _exec(self, sql, args=()):
        return self.conn.execute(sql, args)

    def _one(self, sql, args=()):
        row = self._exec(sql, args).fetchone()
        return row[0] if row else None

    def close(self):
        self.conn.close()

    # ---------------- queue landing (idempotent) ----------------

    def _enqueue(self, source, actor, content, reason, ts):
        """Land one degraded row. Deduped by qid: an existing row is
        never duplicated and never overwritten (terminal verdicts are
        history). Returns (qid, landing_status)."""
        qid = _qid(source, actor, content)
        self._exec("BEGIN IMMEDIATE")
        try:
            existing = self._one(
                "SELECT status FROM sec_degraded_queue WHERE qid=?", (qid,))
            if existing is not None:
                self._exec("COMMIT")
                return qid, str(existing)
            self._exec(
                "INSERT INTO sec_degraded_queue"
                " (qid, source, actor, content, reason, status, ts_utc)"
                " VALUES (?,?,?,?,?,?,?)",
                (qid, str(source), str(actor), str(content), reason,
                 ST_QUEUED, ts))
            self._exec("COMMIT")
        except Exception:
            self._exec("ROLLBACK")
            raise
        return qid, ST_QUEUED

    # ---------------- batch gate face ----------------

    def check_batch(self, texts, source="batch", actor="", ts=None):
        """Gate N texts under a per-chunk wall-clock budget.

        Verdicts are per-text ("pass", 0, "", text) / ("rejected",
        gate_no, word, text). When the budget is breached mid-chunk the
        REMAINING texts land queued (reason budget_breach) with NO
        verdict - fail-closed: ungated content never passes. A runtime
        gate failure degrades the failing text plus the rest of its
        chunk (reason gate_error).
        """
        ts = ts or _utc_now_iso()
        verdicts, degraded = [], []
        chunk = [str(t) for t in texts]
        for start in range(0, len(chunk), self.max_batch):
            piece = chunk[start:start + self.max_batch]
            t0 = self.clock()
            breach = False
            for i, text in enumerate(piece):
                try:
                    self.gate.check_text(text)
                    verdicts.append(("pass", 0, "", text))
                except ContentRejectedError as exc:
                    verdicts.append(("rejected", exc.gate, exc.word, text))
                except GateOfflineError:
                    # runtime gate failure: this text stays ungated ->
                    # degraded, never passed (fail-closed)
                    for rest in piece[i:]:
                        qid, landed = self._enqueue(
                            source, actor, rest, R_GATE_ERR, ts)
                        degraded.append((qid, landed))
                    breach = True
                    break
                if (self.clock() - t0) > self.budget_s and i + 1 < len(piece):
                    # budget exhausted with texts remaining -> they are
                    # degraded, not silently gated nor silently passed
                    for rest in piece[i + 1:]:
                        qid, landed = self._enqueue(
                            source, actor, rest, R_BUDGET, ts)
                        degraded.append((qid, landed))
                    breach = True
                    break
            if breach:
                continue  # next chunk gets a fresh budget window
        return {"verdicts": verdicts, "degraded": degraded}

    # ---------------- drain (idempotent recovery) ----------------

    def drain(self, ts=None):
        """Re-gate every queued row. Clean rows flip to drained_pass,
        gate hits flip to drained_rejected (fail-closed forever). A row
        whose gate call still fails stays queued for the next window -
        drain never drops and never fabricates a verdict."""
        ts = ts or _utc_now_iso()
        rows = self._exec(
            "SELECT qid, source, actor, content FROM sec_degraded_queue"
            " WHERE status=? ORDER BY ts_utc", (ST_QUEUED,)).fetchall()
        passed = rejected = failed = 0
        for qid, source, actor, content in rows:
            try:
                self.gate.check_text(content)
                status = ST_DRAINED_PASS
                passed += 1
            except ContentRejectedError:
                status = ST_DRAINED_REJ
                rejected += 1
            except GateOfflineError:
                failed += 1  # stays queued; honest, no fake verdict
                continue
            self._exec("BEGIN IMMEDIATE")
            try:
                self._exec(
                    "UPDATE sec_degraded_queue SET status=?, ts_drained=?"
                    " WHERE qid=? AND status=?",
                    (status, ts, qid, ST_QUEUED))
                self._exec("COMMIT")
            except Exception:
                self._exec("ROLLBACK")
                raise
        return {"drained": passed + rejected, "passed": passed,
                "rejected": rejected, "still_queued": failed}

    # ---------------- read faces ----------------

    def banner_queue(self):
        """Degraded in-app banner queue = all queued rows (rows ARE the
        queue; R1254 semantics)."""
        return self._exec(
            "SELECT qid, source, actor, content, reason, status, ts_utc"
            " FROM sec_degraded_queue WHERE status=? ORDER BY ts_utc",
            (ST_QUEUED,)).fetchall()

    def rows_by_status(self, status):
        """Read face for the recovery loop (R1681 wiring, AC-PW5):
        queue rows at one status. Terminal rows are history - callers
        treat them read-only; the single writer stays inside this
        class."""
        if status not in (ST_QUEUED, ST_DRAINED_PASS, ST_DRAINED_REJ):
            raise ValueError("unknown queue status: %s" % status)
        return self._exec(
            "SELECT qid, source, actor, content, reason, status, ts_utc,"
            " ts_drained FROM sec_degraded_queue WHERE status = ?"
            " ORDER BY ts_utc", (status,)).fetchall()

    def queue_counts(self):
        rows = self._exec(
            "SELECT status, COUNT(*) FROM sec_degraded_queue"
            " GROUP BY status").fetchall()
        return {str(s): int(c) for s, c in rows}

    # ---------------- p95 profile face (AC-SB3) ----------------

    def p95_profile(self, texts, sizes, repeats):
        """Measure real wall-clock batch cost across sizes. Honest
        stand-in note: this profiles the wordlist mock (the sandbox
        overhead floor); production msgSecCheck p95 lands with real
        wiring (bootstrap window, CEO physical items)."""
        pool = [str(t) for t in texts]
        profile = []
        for n in sizes:
            if n > len(pool):
                raise ValueError("profile pool smaller than size %d" % n)
            runs_ms = []
            for _ in range(int(repeats)):
                t0 = self.clock()
                out = self.check_batch(pool[:n])
                dt_ms = (self.clock() - t0) * 1000.0
                if len(out["verdicts"]) != n or out["degraded"]:
                    raise ValueError(
                        "profile run degraded (budget too tight): %d/%d"
                        % (len(out["verdicts"]), n))
                runs_ms.append(dt_ms)
            runs_ms.sort()
            profile.append({
                "n": int(n), "runs": int(repeats),
                "p50_ms": round(_pct(runs_ms, 0.50), 3),
                "p95_ms": round(_pct(runs_ms, 0.95), 3),
                "max_ms": round(runs_ms[-1], 3),
            })
        return profile


def main():
    parser = argparse.ArgumentParser(
        description="UGC sec-gate batch + degradation face readiness check")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(
        BASE, "data", "sec_degraded.db"))
    args = parser.parse_args()
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
        gate = SecGate.from_config(cfg)  # raises GateOfflineError family
    except (OSError, json.JSONDecodeError) as exc:
        print("config unreadable: %s" % exc, file=sys.stderr)
        return 2
    except GateOfflineError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    face = SecBatchFace(gate, args.db, config=cfg)
    face.close()
    print("READY budget_ms=%.0f max_batch=%d db=%s"
          % (face.budget_s * 1000.0, face.max_batch, args.db))
    return 0


if __name__ == "__main__":
    sys.exit(main())
