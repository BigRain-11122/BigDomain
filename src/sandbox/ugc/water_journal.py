"""Completed-window water journal (R1800, seed: R1799 five-window wiring).

The five water-delta windows (ingest_lobby R1794, submit_batch R1796,
drain_recover R1797, submit R1798, review_verdict R1799) share one
single _last_water slot: only the most recent completed window stays
visible and history is lost on restart. This module is the append-only
observability ledger - one row per completed window (kind + delta
envelope + ts), stored in an independent sqlite file next to ugc.db
(single writer: the pipeline builds one journal per instance; R1681
sec_degraded / R1254 reminder precedent; zero ugc.db schema touch).
journal_board() is the pure read face: time ascending, compliance
three-piece resident, ai_generated=0 (server authority).

Append-only law: rows land via INSERT only; the ledger never rewrites
history. total_delta carries any sign (a verdict pass window lands
total_delta=-1, AC-VW1), so the table has no sign constraint on it.

Encoding discipline: this source stays ASCII; Chinese copy lives in
config.json (data file).
"""

import json
import re
import sqlite3
from datetime import datetime, timezone

KINDS = ("ingest", "batch", "drain", "submit", "verdict")

SCHEMA = """
CREATE TABLE IF NOT EXISTS water_windows (
    window_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL
        CHECK (kind IN ('ingest','batch','drain','submit','verdict')),
    delta TEXT NOT NULL,
    total_delta INTEGER NOT NULL,
    ts_utc TEXT NOT NULL
);
"""

E_WJ_NO_DISCLAIMER = "E_WJ_NO_DISCLAIMER"
E_WJ_BAD_KIND = "E_WJ_BAD_KIND"
E_WJ_BAD_ENVELOPE = "E_WJ_BAD_ENVELOPE"
E_WJ_BAD_WINDOW = "E_WJ_BAD_WINDOW"
E_WJ_BAD_LIMIT = "E_WJ_BAD_LIMIT"

# R1748 family law: strict \Z anchor (a bare $ would admit a
# trailing newline and silently read an empty account).
_WINDOW_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])\Z")


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


class WaterJournalFace:
    """Single-writer face over the independent journal sqlite file."""

    def __init__(self, db_path, disclaimer=None):
        if not isinstance(disclaimer, str) or not disclaimer.strip():
            raise ValueError(
                "water journal: disclaimer missing (%s)" % E_WJ_NO_DISCLAIMER)
        self.db_path = db_path
        self.disclaimer = disclaimer
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def record(self, kind, envelope):
        """Archive one completed window (AC-WJ2): kind must be one of
        the five window kinds; envelope is the store pool_water_delta
        envelope the window already derived (single derivation source
        stays the store face - this ledger only archives it). Returns
        the landing receipt {window_id, kind, ts_utc}."""
        if kind not in KINDS:
            raise ValueError(
                "water journal: unknown window kind (%s)" % E_WJ_BAD_KIND)
        if (not isinstance(envelope, dict)
                or not isinstance(envelope.get("pool_water_delta"), dict)
                or isinstance(envelope.get("total_delta"), bool)
                or not isinstance(envelope.get("total_delta"), int)):
            raise ValueError(
                "water journal: bad delta envelope (%s)" % E_WJ_BAD_ENVELOPE)
        ts = _utc_now_iso()
        cur = self._conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc) "
            "VALUES (?, ?, ?, ?)",
            (kind, json.dumps(envelope["pool_water_delta"], sort_keys=True),
             int(envelope["total_delta"]), ts))
        self._conn.commit()
        return {"window_id": cur.lastrowid, "kind": kind, "ts_utc": ts}

    def journal_board(self, window=None, limit=0):
        """Pure read face (AC-WJ3, AC-JB1..AC-JB7, AC-JL1..AC-JL7):
        every archived completed-window row, time ascending with the
        window_id tie-break (append order kept within one second -
        deterministic, zero RNG). window=None keeps the whole-board
        behavior; an explicit YYYY-M filters on the record-time ts_utc
        month (the same single-column key the kind_tally /
        monthly_flow faces read) and malformed windows fail closed
        E_WJ_BAD_WINDOW. The in-window row order is the full-board
        order restricted to that window: one ORDER BY clause, zero
        re-sorting. limit=0 keeps the full-list behavior; limit>0
        returns the ascending tail window of N rows (mirror-SQL law:
        ORDER BY ts_utc DESC, window_id DESC LIMIT N, then reversed
        back to board order) and adds exactly the three keys
        {limit, returned, truncated} - the envelope total reports
        the full filtered count so a truncated board never lies
        about its size. The limit gate runs before the window gate
        (both-bad determinism: E_WJ_BAD_LIMIT fires first). The
        compliance three-piece stays resident: ai_generated=0
        (server authority), the standing non-advisory disclaimer
        and the persistent flag."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ValueError(
                "water journal: limit must be a non-negative int (%s)"
                % E_WJ_BAD_LIMIT)
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise ValueError(
                    "water journal: window must be YYYY-MM (%s)"
                    % E_WJ_BAD_WINDOW)
        where = ""
        args = []
        if w is not None:
            where = " WHERE substr(ts_utc, 1, 7) = ?"
            args.append(w)
        total = self._conn.execute(
            "SELECT COUNT(*) FROM water_windows" + where, args).fetchone()[0]
        if limit > 0:
            cur = self._conn.execute(
                "SELECT window_id, kind, delta, total_delta, ts_utc"
                " FROM water_windows" + where
                + " ORDER BY ts_utc DESC, window_id DESC LIMIT ?",
                args + [limit])
            fetched = list(cur)
            fetched.reverse()
        else:
            cur = self._conn.execute(
                "SELECT window_id, kind, delta, total_delta, ts_utc"
                " FROM water_windows" + where
                + " ORDER BY ts_utc, window_id", args)
            fetched = list(cur)
        rows = []
        for window_id, kind, delta, total_delta, ts_utc in fetched:
            rows.append({
                "window_id": window_id, "kind": kind,
                "delta": json.loads(delta),
                "total_delta": total_delta, "ts_utc": ts_utc})
        env = {"journal_board": rows, "total": total,
               "ai_generated": 0, "disclaimer": self.disclaimer,
               "persistent": True}
        if limit > 0:
            env["limit"] = limit
            env["returned"] = len(rows)
            env["truncated"] = len(rows) < total
        if w is not None:
            env["window"] = w
        return env

    def kind_tally(self, window=None):
        """Pure dense per-kind aggregation over the append-only ledger
        (AC-KT1..AC-KT6). window=None keeps the all-history behavior;
        an explicit YYYY-MM filters on the record-time ts_utc month
        (single column, same key the journal_board rows carry).
        Malformed windows fail closed E_WJ_BAD_WINDOW before any
        read. The five window kinds are a closed set, so zero-count
        cells stay explicit (dense grid); observed kinds outside the
        domain (production-unreachable through the CHECK guard; a
        raw-row simulation may still land them) are appended after
        the dense cells in ascending order and counted in total -
        the face never hides data. Keys render ascending,
        deterministic, zero RNG; total == sum of all cells."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise ValueError(
                    "water journal: window must be YYYY-MM (%s)"
                    % E_WJ_BAD_WINDOW)
        if w is None:
            grouped = self._conn.execute(
                "SELECT kind, COUNT(*) FROM water_windows GROUP BY kind")
        else:
            grouped = self._conn.execute(
                "SELECT kind, COUNT(*) FROM water_windows"
                " WHERE substr(ts_utc, 1, 7) = ? GROUP BY kind", (w,))
        observed = {}
        for kind, n in grouped:
            observed[kind] = int(n)
        by_kind = {}
        for kind in sorted(KINDS):
            by_kind[kind] = observed.pop(kind, 0)
        for kind in sorted(observed):
            by_kind[kind] = observed[kind]
        env = {"kind_tally": by_kind,
               "total": sum(by_kind.values()),
               "ai_generated": 0, "disclaimer": self.disclaimer,
               "persistent": True}
        if w is not None:
            env["window"] = w
        return env

    def monthly_flow(self, window=None):
        """Pure by-month net-flow aggregation over the append-only
        ledger (AC-MF1..AC-MF7). window=None keeps the whole-board
        behavior (every observed month, ascending); an explicit
        YYYY-MM filters on the record-time ts_utc month and returns
        just that month's row. Months are an unbounded domain (any
        YYYY-MM), so a dense grid is not constructible - a month
        with no archived window reads as an honest empty row list.
        Malformed windows fail closed E_WJ_BAD_WINDOW before any
        read. Each month row keys exactly {month, windows,
        total_delta}: windows = the month's completed-window count,
        total_delta = the month's signed sum (a verdict pass window
        lands -1, AC-VW1). Envelope invariants: total == sum of row
        windows, net_delta == sum of row total_delta (the whole-
        board net in one read - the point of this face). Month keys
        render ascending, deterministic, zero RNG."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise ValueError(
                    "water journal: window must be YYYY-MM (%s)"
                    % E_WJ_BAD_WINDOW)
        if w is None:
            grouped = self._conn.execute(
                "SELECT substr(ts_utc, 1, 7), COUNT(*), SUM(total_delta)"
                " FROM water_windows"
                " GROUP BY substr(ts_utc, 1, 7)"
                " ORDER BY substr(ts_utc, 1, 7)")
        else:
            grouped = self._conn.execute(
                "SELECT substr(ts_utc, 1, 7), COUNT(*), SUM(total_delta)"
                " FROM water_windows"
                " WHERE substr(ts_utc, 1, 7) = ?"
                " GROUP BY substr(ts_utc, 1, 7)"
                " ORDER BY substr(ts_utc, 1, 7)", (w,))
        rows = []
        for month, n, s in grouped:
            rows.append({"month": month, "windows": int(n),
                         "total_delta": int(s)})
        env = {"monthly_flow": rows,
               "total": sum(r["windows"] for r in rows),
               "net_delta": sum(r["total_delta"] for r in rows),
               "ai_generated": 0, "disclaimer": self.disclaimer,
               "persistent": True}
        if w is not None:
            env["window"] = w
        return env

    def close(self):
        self._conn.close()
