"""Acceptance suite: water journal journal_board read-cap parameter
(R1804).

Asserts the pre-registered criteria AC-JL1..AC-JL7 from the R1804
claim line in state/queue/tech.md (seed: water_journal.py R1803
journal_board window param - the full time-ordered row list has no
read cap, a large ledger read-face amplification; R1729 usage_log
read-cap family). This source is pure ASCII; Chinese copy lives in
config.json (data file).

Usage: python test_water_journal_limit.py
"""

import hashlib
import inspect
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import water_journal as WJ  # noqa: E402

EXPECTED = 7
RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def row_count(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
    finally:
        conn.close()


def insert_fixture_row(db_path, kind, delta, total_delta, ts_utc):
    """Test-fixture direct row landing for historical months
    (R1730 family precedent: the product record path stamps ts at
    record time, so a historical month can only arrive via fixture)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc)"
            " VALUES (?, ?, ?, ?)",
            (kind, json.dumps(delta, sort_keys=True), total_delta, ts_utc))
        conn.commit()
    finally:
        conn.close()


def query_rows(db_path, where, args, order, limit=None):
    """Independent re-derivation straight from the sqlite file
    (read-only connection; the face is never imported here -
    standalone re-derivation law)."""
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        sql = ("SELECT window_id, kind, delta, total_delta, ts_utc "
               "FROM water_windows " + where + " " + order)
        if limit is not None:
            sql += " LIMIT ?"
            args = list(args) + [limit]
        rows = []
        for window_id, kind, delta, total_delta, ts_utc in conn.execute(
                sql, args):
            rows.append({"window_id": window_id, "kind": kind,
                         "delta": json.loads(delta),
                         "total_delta": total_delta, "ts_utc": ts_utc})
        return rows
    finally:
        conn.close()


def manual_full(db_path):
    return query_rows(db_path, "", (), "ORDER BY ts_utc, window_id")


def mirror_tail(db_path, where, args, limit):
    """Mirror-SQL law (R1729 AC-UL4): DESC/DESC LIMIT N then reversed
    back to ascending board order."""
    rows = query_rows(db_path, where, args,
                      "ORDER BY ts_utc DESC, window_id DESC", limit)
    rows.reverse()
    return rows


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-jl-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    disc = cfg["compliance"]["disclaimer"]
    frozen = {rel: sha256_file(os.path.join(BASE, rel))
              for rel in ("config.json", "store.py", "sec_batch.py",
                          "pipeline.py")}
    journal_db = os.path.join(tmp, "water_journal.db")
    face = WJ.WaterJournalFace(journal_db, disc)
    cur_month = datetime.now(timezone.utc).strftime("%Y-%m")
    env_zero = {"pool_water_delta": {}, "total_delta": 0,
                "disclaimer": disc, "persistent": True}
    env_susp = {"pool_water_delta": {"review.suspended": 1},
                "total_delta": 1, "disclaimer": disc, "persistent": True}
    try:
        # ten-row current-month world, alternating kinds and envelopes
        for i in range(10):
            face.record(WJ.KINDS[i % 5], env_susp if i % 3 == 0 else env_zero)

        # ---- AC-JL1: default contract + limit>0 three new keys -----
        t0 = face.journal_board()
        keys_ok = (set(t0) == {"journal_board", "total", "ai_generated",
                               "disclaimer", "persistent"}
                   and t0["total"] == 10 == len(t0["journal_board"]))
        default_ok = (t0["journal_board"] == manual_full(journal_db)
                      and json.dumps(t0)
                      == json.dumps(face.journal_board())
                      and json.dumps(t0, sort_keys=True)
                      == json.dumps(face.journal_board(), sort_keys=True))
        capped = face.journal_board(limit=3)
        capped_ok = (set(capped) == {"journal_board", "total",
                                     "ai_generated", "disclaimer",
                                     "persistent", "limit", "returned",
                                     "truncated"}
                     and capped["total"] == 10
                     and capped["returned"] == 3 == len(
                         capped["journal_board"])
                     and capped["truncated"] is True
                     and capped["limit"] == 3)
        comp_ok = (capped["ai_generated"] == 0
                   and capped["disclaimer"] == disc
                   and capped["persistent"] is True)
        record("AC-JL1", keys_ok and default_ok and capped_ok and comp_ok,
               "default-keys=%s default==manual+double-call=%s "
               "limit3-keys/total10/returned3/truncated=%s "
               "compliance=%s"
               % (keys_ok, default_ok, capped_ok, comp_ok))

        # ---- AC-JL2: bad limit shapes + both-bad gate order --------
        bad_limits = [-1, True, "2", 2.5]
        n_before = row_count(journal_db)
        reject_hits = []
        for bad in bad_limits:
            try:
                face.journal_board(limit=bad)
                reject_hits.append("none")
            except ValueError as exc:
                reject_hits.append(WJ.E_WJ_BAD_LIMIT
                                   if WJ.E_WJ_BAD_LIMIT in str(exc)
                                   else "other-ValueError")
        all_rejected = (reject_hits == [WJ.E_WJ_BAD_LIMIT] * 4)
        both_bad = False
        try:
            face.journal_board(window="2026-13", limit=-1)
        except ValueError as exc:
            both_bad = WJ.E_WJ_BAD_LIMIT in str(exc)
        single_bad_win = False
        try:
            face.journal_board(window="2026-13")
        except ValueError as exc:
            single_bad_win = WJ.E_WJ_BAD_WINDOW in str(exc)
        no_side = row_count(journal_db) == n_before
        record("AC-JL2",
               all_rejected and both_bad and single_bad_win and no_side,
               "rejected=%d/4 codes=%s both-bad=limit-first=%s "
               "window-only-still-E_WJ_BAD_WINDOW=%s rows-stable=%s"
               % (reject_hits.count(WJ.E_WJ_BAD_LIMIT),
                  ",".join(sorted(set(reject_hits))), both_bad,
                  single_bad_win, no_side))

        # ---- AC-JL3: tail-window truncation semantics ---------------
        full_rows = face.journal_board()["journal_board"]
        capped_rows = face.journal_board(limit=3)["journal_board"]
        tail_ok = capped_rows == full_rows[-3:]
        mirror_ok = capped_rows == mirror_tail(journal_db, "", (), 3)
        field_ok = all(set(r) == {"window_id", "kind", "delta",
                                  "total_delta", "ts_utc"}
                       for r in capped_rows)
        record("AC-JL3", tail_ok and mirror_ok and field_ok,
               "rows==default-tail3=%s mirror-sql=%s field-keys=%s"
               % (tail_ok, mirror_ok, field_ok))

        # ---- AC-JL4: boundary states --------------------------------
        exact = face.journal_board(limit=10)
        exact_ok = (exact["returned"] == 10 and exact["total"] == 10
                    and exact["truncated"] is False
                    and exact["journal_board"] == full_rows)
        over = face.journal_board(limit=50)
        over_ok = (over["returned"] == 10 and over["truncated"] is False
                   and over["journal_board"] == full_rows)
        one = face.journal_board(limit=1)
        one_ok = (one["returned"] == 1
                  and one["journal_board"] == full_rows[-1:])
        empty_db = os.path.join(tmp, "empty_journal.db")
        empty_face = WJ.WaterJournalFace(empty_db, disc)
        try:
            zero_world = empty_face.journal_board(limit=3)
            zero_ok = (zero_world["journal_board"] == []
                       and zero_world["total"] == 0
                       and zero_world["returned"] == 0
                       and zero_world["truncated"] is False
                       and set(zero_world) == {
                           "journal_board", "total", "ai_generated",
                           "disclaimer", "persistent", "limit",
                           "returned", "truncated"})
        finally:
            empty_face.close()
        record("AC-JL4", exact_ok and over_ok and one_ok and zero_ok,
               "limit==total-full=%s over-total-full=%s limit1-tail=%s "
               "zero-world-honest=%s"
               % (exact_ok, over_ok, one_ok, zero_ok))

        # ---- AC-JL5: window x limit orthogonality -------------------
        insert_fixture_row(journal_db, "submit", {}, 0,
                           "2026-08-14T08:00:00.000000Z")
        insert_fixture_row(journal_db, "verdict",
                           {"review.verdicted.risky": 1}, -1,
                           "2026-08-20T09:00:00.000000Z")
        full12 = face.journal_board()["journal_board"]
        full_ok = len(full12) == 12
        winlim = face.journal_board(window=cur_month, limit=3)
        win_cur = query_rows(journal_db, "WHERE substr(ts_utc, 1, 7) = ?",
                             (cur_month,), "ORDER BY ts_utc, window_id")
        winlim_ok = (winlim["window"] == cur_month
                     and winlim["total"] == 10 == len(win_cur)
                     and winlim["returned"] == 3
                     and winlim["truncated"] is True
                     and winlim["journal_board"] == win_cur[-3:]
                     and winlim["journal_board"] == mirror_tail(
                         journal_db, "WHERE substr(ts_utc, 1, 7) = ?",
                         (cur_month,), 3))
        coexist_ok = set(winlim) == {
            "journal_board", "total", "ai_generated", "disclaimer",
            "persistent", "window", "limit", "returned", "truncated"}
        overwin = face.journal_board(window=cur_month, limit=50)
        overwin_ok = (overwin["returned"] == 10
                      and overwin["truncated"] is False
                      and overwin["journal_board"] == win_cur)
        auglim = face.journal_board(window="2026-08", limit=1)
        aug_ok = (auglim["total"] == 2 and auglim["returned"] == 1
                  and auglim["journal_board"][-1]["total_delta"] == -1)
        record("AC-JL5", full_ok and winlim_ok and coexist_ok
               and overwin_ok and aug_ok,
               "full12=%s window-cap-ok=%s keys-coexist=%s "
               "over-window-full=%s history-window=%s"
               % (full_ok, winlim_ok, coexist_ok, overwin_ok, aug_ok))

        # ---- AC-JL6: pure-read law + liveness ------------------------
        method_src = inspect.getsource(WJ.WaterJournalFace.journal_board)
        src_clean = ("INSERT" not in method_src
                     and "UPDATE" not in method_src
                     and "DELETE" not in method_src)
        n_a = row_count(journal_db)
        r1 = face.journal_board()
        r1c = face.journal_board(limit=3)
        r1w = face.journal_board(window=cur_month, limit=2)
        r2 = face.journal_board()
        r2c = face.journal_board(limit=3)
        r2w = face.journal_board(window=cur_month, limit=2)
        n_b = row_count(journal_db)
        same_calls = (json.dumps(r1, sort_keys=True)
                      == json.dumps(r2, sort_keys=True)
                      and json.dumps(r1) == json.dumps(r2)
                      and json.dumps(r1c) == json.dumps(r2c)
                      and json.dumps(r1w, sort_keys=True)
                      == json.dumps(r2w, sort_keys=True))
        before_total = r2["total"]
        face.record("drain", env_zero)
        after_default = face.journal_board()
        after_capped = face.journal_board(limit=3)
        live_ok = (after_default["total"] == before_total + 1
                   and after_capped["total"] == before_total + 1
                   and after_capped["journal_board"]
                   == after_default["journal_board"][-3:])
        record("AC-JL6", src_clean and n_a == n_b and same_calls and live_ok,
               "read-method-clean=%s rows-stable=%s "
               "double-call-identical=%s liveness-plus-one=%s"
               % (src_clean, n_a == n_b, same_calls, live_ok))

        # ---- AC-JL7: hygiene + delivery ------------------------------
        ascii_ok = True
        for rel in ("water_journal.py", os.path.basename(__file__)):
            with open(os.path.join(BASE, rel), "rb") as handle:
                ascii_ok = ascii_ok and max(handle.read()) < 128
        net_ok = True
        for rel in ("water_journal.py", os.path.basename(__file__)):
            with open(os.path.join(BASE, rel), encoding="utf-8") as handle:
                for line in handle:
                    s = line.strip()
                    if s.startswith("import ") or s.startswith("from "):
                        if any(w in s for w in ("urllib", "requests",
                                                "socket", "http")):
                            net_ok = False
        with open(os.path.join(BASE, "water_journal.py"),
                  encoding="utf-8") as handle:
            wj_src = handle.read()
        source_law_ok = ("UPDATE" not in wj_src
                         and "DELETE" not in wj_src)
        tables = [r[0] for r in sqlite3.connect(journal_db).execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        schema_ok = set(tables) == {"water_windows", "sqlite_sequence"}
        frozen_ok = all(sha256_file(os.path.join(BASE, rel)) == sha
                        for rel, sha in frozen.items())
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ('"ugc-water-journalcap"' in reg_src
                  and "test_water_journal_limit.py" in reg_src)
        record("AC-JL7",
               ascii_ok and net_ok and source_law_ok and schema_ok
               and frozen_ok and reg_ok,
               "pure-ascii=%s import-lines-clean=%s append-only-source=%s "
               "schema-constant=%s frozen-bytes=%s registry-wired=%s"
               % (ascii_ok, net_ok, source_law_ok, schema_ok, frozen_ok,
                  reg_ok))
    finally:
        face.close()

    ok_all = len(RESULTS) == EXPECTED and all(ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                             sum(1 for _a, ok in RESULTS if ok), EXPECTED),
          flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
