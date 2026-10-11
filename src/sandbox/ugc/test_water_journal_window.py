"""Acceptance suite: water journal journal_board month-window read
(R1803).

Asserts the pre-registered criteria AC-JB1..AC-JB7 from the R1803
claim line in state/queue/tech.md (seed: water_journal.py R1802
monthly_flow - journal_board is the full time-ordered row list with
no window filter). This source is pure ASCII; Chinese copy lives in
config.json (data file).

Usage: python test_water_journal_window.py
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


def manual_rows(db_path, where="", args=()):
    """Independent re-derivation of the board rows straight from the
    sqlite file (read-only connection; the face is never imported
    here - standalone re-derivation law)."""
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        rows = []
        for window_id, kind, delta, total_delta, ts_utc in conn.execute(
                "SELECT window_id, kind, delta, total_delta, ts_utc "
                "FROM water_windows %s ORDER BY ts_utc, window_id" % where,
                args):
            rows.append({"window_id": window_id, "kind": kind,
                         "delta": json.loads(delta),
                         "total_delta": total_delta, "ts_utc": ts_utc})
        return rows
    finally:
        conn.close()


def month_of(ts):
    return ts[:7]


def board_subsequence(full_rows, w):
    return [r for r in full_rows if month_of(r["ts_utc"]) == w]


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-jw-")
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
        # ---- AC-JB1: default contract + explicit window key -------
        t0 = face.journal_board()
        keys_ok = set(t0) == {"journal_board", "total", "ai_generated",
                              "disclaimer", "persistent"}
        zero_ok = (t0["journal_board"] == [] and t0["total"] == 0
                   == len(t0["journal_board"]))
        comp_ok = (t0["ai_generated"] == 0 and t0["disclaimer"] == disc
                   and t0["persistent"] is True)
        face.record("submit", env_susp)
        face.record("ingest", env_zero)
        face.record("batch", env_zero)
        face.record("drain", env_zero)
        face.record("verdict", env_zero)
        t1 = face.journal_board()
        default_ok = (
            set(t1) == {"journal_board", "total", "ai_generated",
                        "disclaimer", "persistent"}
            and t1["total"] == 5 == len(t1["journal_board"])
            and t1["journal_board"] == manual_rows(journal_db)
            and json.dumps(t1) == json.dumps(face.journal_board()))
        wenv = face.journal_board(cur_month)
        window_key_ok = (
            set(wenv) == {"journal_board", "total", "ai_generated",
                          "disclaimer", "persistent", "window"}
            and wenv["window"] == cur_month
            and wenv["total"] == len(wenv["journal_board"]) == 5)
        record("AC-JB1",
               keys_ok and zero_ok and comp_ok and default_ok and window_key_ok,
               "envelope-keys=%s honest-zero=%s compliance=%s "
               "default-board==manual=%s double-call=%s "
               "explicit-window-key-additive=%s"
               % (keys_ok, zero_ok, comp_ok,
                  t1["journal_board"] == manual_rows(journal_db),
                  json.dumps(t1) == json.dumps(face.journal_board()),
                  window_key_ok))

        # ---- AC-JB2: 14 bad window shapes fail closed --------------
        bad_forms = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
                     "202610", "abcd", "", 2026, True, 2.5,
                     "2026-10\n", "2026-10 ", "2026-10\r"]
        n_before = row_count(journal_db)
        reject_hits = []
        for bad in bad_forms:
            try:
                face.journal_board(bad)
                reject_hits.append("none")
            except ValueError as exc:
                reject_hits.append(WJ.E_WJ_BAD_WINDOW
                                   if WJ.E_WJ_BAD_WINDOW in str(exc)
                                   else "other-ValueError")
        all_rejected = (reject_hits == [WJ.E_WJ_BAD_WINDOW] * 14)
        no_side = row_count(journal_db) == n_before
        record("AC-JB2", all_rejected and no_side,
               "rejected=%d/14 codes=%s rows-stable=%s"
               % (reject_hits.count(WJ.E_WJ_BAD_WINDOW),
                  ",".join(sorted(set(reject_hits))), no_side))

        # ---- AC-JB3: month-window filter semantics -----------------
        insert_fixture_row(journal_db, "submit", {}, 0,
                           "2026-08-14T08:00:00.000000Z")
        insert_fixture_row(journal_db, "verdict",
                           {"review.verdicted.risky": 1}, -1,
                           "2026-09-01T10:00:00.000000Z")
        aug = face.journal_board("2026-08")
        sep = face.journal_board("2026-09")
        aug_ok = (aug["window"] == "2026-08"
                  and [r["window_id"] for r in aug["journal_board"]]
                  == [r["window_id"] for r in manual_rows(
                      journal_db, "WHERE substr(ts_utc, 1, 7) = ?",
                      ("2026-08",))]
                  and aug["total"] == 1)
        sep_ok = (sep["window"] == "2026-09"
                  and sep["journal_board"][0]["total_delta"] == -1
                  and sep["total"] == 1)
        default_read = face.journal_board()
        includes_hist = (default_read["total"] == 7
                         and {month_of(r["ts_utc"])
                              for r in default_read["journal_board"]}
                         == {"2026-08", "2026-09", cur_month})
        cur_read = face.journal_board(cur_month)
        no_perm = (cur_read["total"] == 5
                   and all(month_of(r["ts_utc"]) == cur_month
                           for r in cur_read["journal_board"]))
        future = face.journal_board("2026-12")
        future_ok = (future["journal_board"] == [] and future["total"] == 0
                     and future["window"] == "2026-12")
        record("AC-JB3",
               aug_ok and sep_ok and includes_hist and no_perm and future_ok,
               "aug=%s sep=%s default-includes-history=%s "
               "no-current-permeation=%s future-empty=%s"
               % (aug_ok, sep_ok, includes_hist, no_perm, future_ok))

        # ---- AC-JB4: manual SQL cross + order preservation ---------
        full_rows = face.journal_board()["journal_board"]
        wrows = face.journal_board(cur_month)["journal_board"]
        manual_w = manual_rows(journal_db,
                               "WHERE substr(ts_utc, 1, 7) = ?",
                               (cur_month,))
        cross_ok = (wrows == manual_w
                    and [r["window_id"] for r in wrows]
                    == [r["window_id"] for r in manual_w])
        subseq_ok = ([r["window_id"] for r in wrows]
                     == [r["window_id"]
                         for r in board_subsequence(full_rows, cur_month)])
        aug_rows = face.journal_board("2026-08")["journal_board"]
        subseq_aug_ok = ([r["window_id"] for r in aug_rows]
                         == [r["window_id"]
                             for r in board_subsequence(full_rows,
                                                        "2026-08")])
        record("AC-JB4", cross_ok and subseq_ok and subseq_aug_ok,
               "window==manual-sql=%s full-board-subsequence=%s "
               "history-subsequence=%s"
               % (cross_ok, subseq_ok, subseq_aug_ok))

        # ---- AC-JB5: pure-read law ---------------------------------
        method_src = inspect.getsource(WJ.WaterJournalFace.journal_board)
        src_clean = ("INSERT" not in method_src
                     and "UPDATE" not in method_src
                     and "DELETE" not in method_src)
        n_a = row_count(journal_db)
        r1 = face.journal_board()
        r1w = face.journal_board(cur_month)
        r2 = face.journal_board()
        r2w = face.journal_board(cur_month)
        n_b = row_count(journal_db)
        same_calls = (json.dumps(r1, sort_keys=True)
                      == json.dumps(r2, sort_keys=True)
                      and json.dumps(r1) == json.dumps(r2)
                      and json.dumps(r1w) == json.dumps(r2w))
        record("AC-JB5", src_clean and n_a == n_b and same_calls,
               "read-method-clean=%s rows-stable=%s double-call-identical=%s"
               % (src_clean, n_a == n_b, same_calls))

        # ---- AC-JB6: liveness + restart persistence ----------------
        cur_before = face.journal_board(cur_month)
        face.record("drain", env_zero)
        cur_after = face.journal_board(cur_month)
        live_ok = (cur_after["total"] == cur_before["total"] + 1
                   and [r["window_id"]
                        for r in cur_after["journal_board"]]
                   == [r["window_id"]
                       for r in cur_before["journal_board"]]
                   + [cur_after["journal_board"][-1]["window_id"]])
        snap_full = face.journal_board()
        snap_aug = face.journal_board("2026-08")
        snap_cur = face.journal_board(cur_month)
        face.close()
        face = WJ.WaterJournalFace(journal_db, disc)
        persist_ok = (face.journal_board() == snap_full
                      and face.journal_board("2026-08") == snap_aug)
        face.record("submit", env_susp)
        resume_ok = (face.journal_board()["total"] == snap_full["total"] + 1
                     and face.journal_board(cur_month)["total"]
                     == snap_cur["total"] + 1)
        record("AC-JB6", live_ok and persist_ok and resume_ok,
               "liveness-plus-one=%s restart-identical=%s resume-plus-one=%s"
               % (live_ok, persist_ok, resume_ok))

        # ---- AC-JB7: hygiene + delivery ----------------------------
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
        # sqlite_sequence is the AUTOINCREMENT bookkeeping table sqlite
        # itself keeps (present since R1800); the schema-constant law is
        # "no new tables beyond the R1800 shape".
        schema_ok = set(tables) == {"water_windows", "sqlite_sequence"}
        frozen_ok = all(sha256_file(os.path.join(BASE, rel)) == sha
                        for rel, sha in frozen.items())
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ('"ugc-water-journalwin"' in reg_src
                  and "test_water_journal_window.py" in reg_src)
        record("AC-JB7",
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
