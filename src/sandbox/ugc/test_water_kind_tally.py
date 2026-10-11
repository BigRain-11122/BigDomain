"""Acceptance suite: water journal kind_tally read face (R1801).

Asserts the pre-registered criteria AC-KT1..AC-KT7 from the R1801
claim line in state/queue/tech.md (seed: water_journal.py R1800 -
journal_board is the full time-ordered row list; "which window kind
happened how many times" had no aggregation face). This source is
pure ASCII; Chinese copy lives in config.json (data file).

Usage: python test_water_kind_tally.py
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


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-kt-")
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
    dense_keys = sorted(WJ.KINDS)
    try:
        # ---- AC-KT1: default contract + dense honest zero ---------
        t0 = face.kind_tally()
        keys_ok = set(t0) == {"kind_tally", "total", "ai_generated",
                              "disclaimer", "persistent"}
        dense_ok = (list(t0["kind_tally"].keys()) == dense_keys
                    and all(t0["kind_tally"][k] == 0 for k in dense_keys))
        total_ok = t0["total"] == 0 == sum(t0["kind_tally"].values())
        comp_ok = (t0["ai_generated"] == 0 and t0["disclaimer"] == disc
                   and t0["persistent"] is True)
        t0b = face.kind_tally()
        double_ok = (json.dumps(t0, sort_keys=True)
                     == json.dumps(t0b, sort_keys=True)
                     and json.dumps(t0) == json.dumps(t0b))
        face.record("submit", env_susp)
        face.record("ingest", env_zero)
        face.record("batch", env_zero)
        face.record("drain", env_zero)
        face.record("verdict", env_zero)
        t1 = face.kind_tally()
        all_ok = (t1["kind_tally"] == {"batch": 1, "drain": 1, "ingest": 1,
                                       "submit": 1, "verdict": 1}
                  and t1["total"] == 5)
        wenv = face.kind_tally(cur_month)
        window_key_ok = (set(wenv) == {"kind_tally", "total", "ai_generated",
                                       "disclaimer", "persistent", "window"}
                         and wenv["window"] == cur_month)
        record("AC-KT1",
               keys_ok and dense_ok and total_ok and comp_ok and double_ok
               and all_ok and window_key_ok,
               "envelope-keys=%s dense-ascending=%s zero-total=%s "
               "compliance=%s double-call=%s all-window=%s "
               "explicit-window-key=%s"
               % (keys_ok, dense_ok, total_ok, comp_ok, double_ok, all_ok,
                  window_key_ok))

        # ---- AC-KT2: 14 bad window shapes fail closed --------------
        bad_forms = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
                     "202610", "abcd", "", 2026, True, 2.5,
                     "2026-10\n", "2026-10 ", "2026-10\r"]
        n_before = row_count(journal_db)
        reject_hits = []
        for bad in bad_forms:
            try:
                face.kind_tally(bad)
                reject_hits.append("none")
            except ValueError as exc:
                reject_hits.append(WJ.E_WJ_BAD_WINDOW
                                   if WJ.E_WJ_BAD_WINDOW in str(exc)
                                   else "other-ValueError")
        all_rejected = (reject_hits == [WJ.E_WJ_BAD_WINDOW] * 14)
        no_side = row_count(journal_db) == n_before
        record("AC-KT2", all_rejected and no_side,
               "rejected=%d/14 codes=%s rows-stable=%s"
               % (reject_hits.count(WJ.E_WJ_BAD_WINDOW),
                  ",".join(sorted(set(reject_hits))), no_side))

        # ---- AC-KT3: month-window filter semantics -----------------
        insert_fixture_row(journal_db, "submit", {}, 0,
                           "2026-08-14T08:00:00.000000Z")
        insert_fixture_row(journal_db, "submit", {}, 0,
                           "2026-08-20T09:30:00.000000Z")
        insert_fixture_row(journal_db, "verdict",
                           {"review.verdicted.risky": 1}, -1,
                           "2026-09-01T10:00:00.000000Z")
        aug = face.kind_tally("2026-08")
        sep = face.kind_tally("2026-09")
        aug_ok = (aug["window"] == "2026-08"
                  and aug["kind_tally"] == {"batch": 0, "drain": 0,
                                            "ingest": 0, "submit": 2,
                                            "verdict": 0}
                  and aug["total"] == 2)
        sep_ok = (sep["kind_tally"] == {"batch": 0, "drain": 0, "ingest": 0,
                                        "submit": 0, "verdict": 1}
                  and sep["total"] == 1)
        default_read = face.kind_tally()
        includes_hist = (default_read["kind_tally"]["submit"] == 3
                         and default_read["kind_tally"]["verdict"] == 2
                         and default_read["total"] == 8)
        cur_read = face.kind_tally(cur_month)
        no_perm = (cur_read["kind_tally"]["submit"] == 1
                   and cur_read["kind_tally"]["verdict"] == 1
                   and cur_read["total"] == 5)
        future = face.kind_tally("2026-12")
        future_ok = (future["kind_tally"] == {k: 0 for k in dense_keys}
                     and future["total"] == 0)
        record("AC-KT3",
               aug_ok and sep_ok and includes_hist and no_perm and future_ok,
               "aug=%s sep=%s default-includes-history=%s "
               "no-current-permeation=%s future-empty=%s"
               % (aug_ok, sep_ok, includes_hist, no_perm, future_ok))

        # ---- AC-KT4: manual SQL cross + out-of-domain honesty ------
        conn = sqlite3.connect(journal_db)
        manual = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM water_windows GROUP BY kind"
        ).fetchall())
        manual_cur = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM water_windows"
            " WHERE substr(ts_utc, 1, 7) = ? GROUP BY kind",
            (cur_month,)).fetchall())
        total_all = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.execute("PRAGMA ignore_check_constraints = ON")
        conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc)"
            " VALUES ('legacy-ghost', '{}', 0, '2026-08-25T11:00:00.000000Z')")
        conn.commit()
        conn.execute("PRAGMA ignore_check_constraints = OFF")
        conn.close()
        cross_ok = (default_read["kind_tally"]
                    == {k: manual.get(k, 0) for k in dense_keys}
                    and default_read["total"] == total_all
                    and cur_read["kind_tally"]
                    == {k: manual_cur.get(k, 0) for k in dense_keys}
                    and cur_read["total"] == sum(manual_cur.values()))
        ghost = face.kind_tally()
        ghost_aug = face.kind_tally("2026-08")
        ghost_keys = list(ghost["kind_tally"].keys())
        ghost_ok = (ghost_keys == dense_keys + ["legacy-ghost"]
                    and ghost["kind_tally"]["legacy-ghost"] == 1
                    and ghost["total"] == 9
                    and list(ghost_aug["kind_tally"].keys())
                    == dense_keys + ["legacy-ghost"]
                    and ghost_aug["kind_tally"]["legacy-ghost"] == 1
                    and ghost_aug["kind_tally"]["submit"] == 2
                    and ghost_aug["total"] == 3)
        ghost_cur = face.kind_tally(cur_month)
        ghost_iso = "legacy-ghost" not in ghost_cur["kind_tally"]
        record("AC-KT4", cross_ok and ghost_ok and ghost_iso,
               "manual-cross=%s ghost-visible=%s ghost-aug-window=%s "
               "window-isolation=%s"
               % (cross_ok, ghost_ok, ghost_ok, ghost_iso))

        # ---- AC-KT5: pure-read law ---------------------------------
        method_src = inspect.getsource(WJ.WaterJournalFace.kind_tally)
        src_clean = ("INSERT" not in method_src
                     and "UPDATE" not in method_src
                     and "DELETE" not in method_src)
        n_a = row_count(journal_db)
        r1 = face.kind_tally()
        r2 = face.kind_tally()
        n_b = row_count(journal_db)
        same_calls = (json.dumps(r1, sort_keys=True)
                      == json.dumps(r2, sort_keys=True)
                      and json.dumps(r1) == json.dumps(r2))
        record("AC-KT5", src_clean and n_a == n_b and same_calls,
               "read-method-clean=%s rows-stable=%s double-call-identical=%s"
               % (src_clean, n_a == n_b, same_calls))

        # ---- AC-KT6: liveness + restart persistence ----------------
        before = face.kind_tally()
        face.record("submit", env_susp)
        after = face.kind_tally()
        live_ok = (after["kind_tally"]["submit"]
                   == before["kind_tally"]["submit"] + 1
                   and after["total"] == before["total"] + 1)
        snapshot = face.kind_tally()
        snap_aug = face.kind_tally("2026-08")
        face.close()
        face = WJ.WaterJournalFace(journal_db, disc)
        persist_ok = (face.kind_tally() == snapshot
                     and face.kind_tally("2026-08") == snap_aug)
        face.record("drain", env_zero)
        resume_ok = (face.kind_tally()["kind_tally"]["drain"]
                     == snapshot["kind_tally"]["drain"] + 1)
        record("AC-KT6", live_ok and persist_ok and resume_ok,
               "liveness-plus-one=%s restart-identical=%s resume-plus-one=%s"
               % (live_ok, persist_ok, resume_ok))

        # ---- AC-KT7: hygiene + delivery ----------------------------
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
        reg_ok = ('"ugc-water-kindtally"' in reg_src
                  and "test_water_kind_tally.py" in reg_src)
        record("AC-KT7",
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
