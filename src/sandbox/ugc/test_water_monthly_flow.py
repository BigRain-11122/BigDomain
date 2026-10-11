"""Acceptance suite: water journal monthly_flow read face (R1802).

Asserts the pre-registered criteria AC-MF1..AC-MF7 from the R1802
claim line in state/queue/tech.md (seed: water_journal.py R1801
kind_tally - per-kind window counts exist, "how much net water
changed per month" had no aggregation face). This source is pure
ASCII; Chinese copy lives in config.json (data file).

Usage: python test_water_monthly_flow.py
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


def rows_only(env):
    return [tuple(sorted(r)) for r in env["monthly_flow"]]


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-mf-")
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
    env_pass = {"pool_water_delta": {"review.suspended": -1,
                                      "review.verdicted.pass": 1},
                "total_delta": -1, "disclaimer": disc, "persistent": True}
    try:
        # ---- AC-MF1: default contract + honest empty ---------------
        t0 = face.monthly_flow()
        keys_ok = set(t0) == {"monthly_flow", "total", "net_delta",
                              "ai_generated", "disclaimer", "persistent"}
        empty_ok = (t0["monthly_flow"] == [] and t0["total"] == 0
                    and t0["net_delta"] == 0)
        comp_ok = (t0["ai_generated"] == 0 and t0["disclaimer"] == disc
                   and t0["persistent"] is True)
        t0b = face.monthly_flow()
        double_ok = (json.dumps(t0, sort_keys=True)
                     == json.dumps(t0b, sort_keys=True)
                     and json.dumps(t0) == json.dumps(t0b))
        face.record("submit", env_susp)
        face.record("ingest", env_zero)
        face.record("batch", env_zero)
        face.record("drain", env_zero)
        face.record("verdict", env_zero)
        t1 = face.monthly_flow()
        row_keys_ok = rows_only(t1) == [("month", "total_delta", "windows")]
        agg_ok = (t1["monthly_flow"]
                  == [{"month": cur_month, "windows": 5, "total_delta": 1}]
                  and t1["total"] == 5 and t1["net_delta"] == 1)
        wenv = face.monthly_flow(cur_month)
        window_key_ok = (set(wenv) == {"monthly_flow", "total",
                                       "net_delta", "ai_generated",
                                       "disclaimer", "persistent",
                                       "window"}
                         and wenv["window"] == cur_month
                         and wenv["monthly_flow"] == t1["monthly_flow"])
        record("AC-MF1",
               keys_ok and empty_ok and comp_ok and double_ok
               and row_keys_ok and agg_ok and window_key_ok,
               "envelope-keys=%s honest-empty=%s compliance=%s "
               "double-call=%s row-keys-exact=%s aggregate=%s "
               "explicit-window-key=%s"
               % (keys_ok, empty_ok, comp_ok, double_ok, row_keys_ok,
                  agg_ok, window_key_ok))

        # ---- AC-MF2: 14 bad window shapes fail closed --------------
        bad_forms = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
                     "202610", "abcd", "", 2026, True, 2.5,
                     "2026-10\n", "2026-10 ", "2026-10\r"]
        n_before = row_count(journal_db)
        reject_hits = []
        for bad in bad_forms:
            try:
                face.monthly_flow(bad)
                reject_hits.append("none")
            except ValueError as exc:
                reject_hits.append(WJ.E_WJ_BAD_WINDOW
                                   if WJ.E_WJ_BAD_WINDOW in str(exc)
                                   else "other-ValueError")
        all_rejected = (reject_hits == [WJ.E_WJ_BAD_WINDOW] * 14)
        no_side = row_count(journal_db) == n_before
        record("AC-MF2", all_rejected and no_side,
               "rejected=%d/14 codes=%s rows-stable=%s"
               % (reject_hits.count(WJ.E_WJ_BAD_WINDOW),
                  ",".join(sorted(set(reject_hits))), no_side))

        # ---- AC-MF3: month-window filter semantics -----------------
        insert_fixture_row(journal_db, "submit", {}, 0,
                           "2026-08-14T08:00:00.000000Z")
        insert_fixture_row(journal_db, "submit", {}, 0,
                           "2026-08-20T09:30:00.000000Z")
        insert_fixture_row(journal_db, "verdict",
                           {"review.verdicted.pass": 1}, -1,
                           "2026-09-01T10:00:00.000000Z")
        aug = face.monthly_flow("2026-08")
        sep = face.monthly_flow("2026-09")
        aug_ok = (aug["window"] == "2026-08"
                  and aug["monthly_flow"] == [{"month": "2026-08",
                                               "windows": 2,
                                               "total_delta": 0}]
                  and aug["total"] == 2 and aug["net_delta"] == 0)
        sep_ok = (sep["window"] == "2026-09"
                  and sep["monthly_flow"] == [{"month": "2026-09",
                                               "windows": 1,
                                               "total_delta": -1}]
                  and sep["total"] == 1 and sep["net_delta"] == -1)
        default_read = face.monthly_flow()
        months = [r["month"] for r in default_read["monthly_flow"]]
        includes_hist = (months == ["2026-08", "2026-09", cur_month]
                         and default_read["total"] == 8
                         and default_read["net_delta"] == 0)
        cur_read = face.monthly_flow(cur_month)
        no_perm = (cur_read["monthly_flow"]
                   == [{"month": cur_month, "windows": 5, "total_delta": 1}]
                   and cur_read["total"] == 5)
        future = face.monthly_flow("2026-12")
        future_ok = (future["monthly_flow"] == [] and future["total"] == 0
                     and future["net_delta"] == 0)
        record("AC-MF3",
               aug_ok and sep_ok and includes_hist and no_perm and future_ok,
               "aug=%s sep=%s default-includes-history=%s "
               "no-current-permeation=%s future-empty=%s"
               % (aug_ok, sep_ok, includes_hist, no_perm, future_ok))

        # ---- AC-MF4: manual SQL cross + negative net honesty -------
        conn = sqlite3.connect(journal_db)
        manual_rows = conn.execute(
            "SELECT substr(ts_utc, 1, 7), COUNT(*), SUM(total_delta)"
            " FROM water_windows GROUP BY substr(ts_utc, 1, 7)"
            " ORDER BY substr(ts_utc, 1, 7)").fetchall()
        manual_cur = conn.execute(
            "SELECT substr(ts_utc, 1, 7), COUNT(*), SUM(total_delta)"
            " FROM water_windows WHERE substr(ts_utc, 1, 7) = ?"
            " GROUP BY substr(ts_utc, 1, 7)", (cur_month,)).fetchall()
        total_all = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sum_all = conn.execute(
            "SELECT SUM(total_delta) FROM water_windows").fetchone()[0]
        conn.close()
        cross_ok = (default_read["monthly_flow"]
                    == [{"month": m, "windows": int(n),
                         "total_delta": int(s)}
                        for m, n, s in manual_rows]
                    and default_read["total"] == total_all
                    and default_read["net_delta"] == sum_all
                    and cur_read["monthly_flow"]
                    == [{"month": m, "windows": int(n),
                         "total_delta": int(s)}
                        for m, n, s in manual_cur]
                    and cur_read["total"] == sum(n for _m, n, _s in
                                                manual_cur))
        # explicit negative month: the verdict -1 lands verbatim
        neg_ok = (face.monthly_flow("2026-09")["monthly_flow"][0]
                  ["total_delta"] == -1
                  and sep["net_delta"] == -1)
        record("AC-MF4", cross_ok and neg_ok,
               "manual-cross-default+window=%s negative-month-visible=%s"
               % (cross_ok, neg_ok))

        # ---- AC-MF5: pure-read law ---------------------------------
        method_src = inspect.getsource(WJ.WaterJournalFace.monthly_flow)
        src_clean = ("INSERT" not in method_src
                     and "UPDATE" not in method_src
                     and "DELETE" not in method_src)
        n_a = row_count(journal_db)
        r1 = face.monthly_flow()
        r2 = face.monthly_flow()
        n_b = row_count(journal_db)
        same_calls = (json.dumps(r1, sort_keys=True)
                      == json.dumps(r2, sort_keys=True)
                      and json.dumps(r1) == json.dumps(r2))
        record("AC-MF5", src_clean and n_a == n_b and same_calls,
               "read-method-clean=%s rows-stable=%s double-call-identical=%s"
               % (src_clean, n_a == n_b, same_calls))

        # ---- AC-MF6: liveness + restart persistence ----------------
        before = face.monthly_flow()
        face.record("verdict", env_pass)
        after = face.monthly_flow()
        cur_before = [r for r in before["monthly_flow"]
                      if r["month"] == cur_month][0]
        cur_after = [r for r in after["monthly_flow"]
                     if r["month"] == cur_month][0]
        live_ok = (cur_after["windows"] == cur_before["windows"] + 1
                   and cur_after["total_delta"]
                   == cur_before["total_delta"] - 1
                   and after["net_delta"] == before["net_delta"] - 1
                   and after["total"] == before["total"] + 1)
        snapshot = face.monthly_flow()
        snap_sep = face.monthly_flow("2026-09")
        face.close()
        face = WJ.WaterJournalFace(journal_db, disc)
        persist_ok = (face.monthly_flow() == snapshot
                      and face.monthly_flow("2026-09") == snap_sep)
        face.record("drain", env_zero)
        resumed = face.monthly_flow()
        resume_ok = (resumed["total"] == snapshot["total"] + 1
                     and [r for r in resumed["monthly_flow"]
                          if r["month"] == cur_month][0]["windows"]
                     == cur_after["windows"] + 1)
        record("AC-MF6", live_ok and persist_ok and resume_ok,
               "liveness-plus-one-and-net=%s restart-identical=%s "
               "resume-plus-one=%s"
               % (live_ok, persist_ok, resume_ok))

        # ---- AC-MF7: hygiene + delivery ----------------------------
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
        reg_ok = ('"ugc-water-monthlyflow"' in reg_src
                  and "test_water_monthly_flow.py" in reg_src)
        record("AC-MF7",
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
