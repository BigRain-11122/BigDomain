"""Acceptance suite: water journal cumulative per-cell net-flow
aggregation read face (R1805).

Asserts the pre-registered criteria AC-CT1..AC-CT7 from the R1805
claim line in state/queue/tech.md (seed: water_journal.py R1804
journal_board read-cap - the five windows land per-cell deltas in
the ledger but "which water cell moved how much, cumulatively"
had no read face). This source is pure ASCII; Chinese copy lives
in config.json (data file).

Usage: python test_water_cell_totals.py
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
    """Independent re-derivation straight from the sqlite file
    (read-only connection; the face is never imported here -
    standalone re-derivation law)."""
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        return list(conn.execute(
            "SELECT delta, total_delta FROM water_windows " + where, args))
    finally:
        conn.close()


def manual_cells(db_path, where="", args=()):
    cells = {}
    total = 0
    for delta, total_delta in manual_rows(db_path, where, args):
        for key, value in json.loads(delta).items():
            cells[key] = cells.get(key, 0) + int(value)
        total += int(total_delta)
    return cells, total


def manual_sum(db_path, where="", args=()):
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        return int(conn.execute(
            "SELECT SUM(total_delta) FROM water_windows " + where,
            args).fetchone()[0] or 0)
    finally:
        conn.close()


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-ct-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    disc = cfg["compliance"]["disclaimer"]
    frozen = {rel: sha256_file(os.path.join(BASE, rel))
              for rel in ("config.json", "store.py", "sec_batch.py",
                          "pipeline.py")}
    journal_db = os.path.join(tmp, "water_journal.db")
    face = WJ.WaterJournalFace(journal_db, disc)
    face2 = None
    cur_month = datetime.now(timezone.utc).strftime("%Y-%m")
    env_zero = {"pool_water_delta": {}, "total_delta": 0,
                "disclaimer": disc, "persistent": True}
    env_susp = {"pool_water_delta": {"review.suspended": 1},
                "total_delta": 1, "disclaimer": disc, "persistent": True}
    env_noise = {"pool_water_delta": {"noise.total": 1,
                                      "noise.by_reason.emoji_only": 1},
                 "total_delta": 1, "disclaimer": disc, "persistent": True}
    env_pass = {"pool_water_delta": {"review.suspended": -1,
                                     "review.verdicted.pass": 1},
                "total_delta": -1, "disclaimer": disc, "persistent": True}
    env_risky = {"pool_water_delta": {"review.suspended": -1,
                                      "review.verdicted.risky": 1},
                 "total_delta": -1, "disclaimer": disc, "persistent": True}
    try:
        # six current-month rows: two clean windows + the four
        # water-moving window shapes (gray / noise / verdict pass /
        # verdict risky - AC-VW1 total_delta=-1 family)
        for i, env in enumerate((env_zero, env_zero, env_susp, env_noise,
                                 env_pass, env_risky)):
            face.record(WJ.KINDS[i % 5], env)

        # ---- AC-CT1: default contract + zero-world ------------------
        t0 = face.cell_totals()
        keys_ok = set(t0) == {"cell_totals", "total", "ai_generated",
                              "disclaimer", "persistent"}
        order_ok = (list(t0["cell_totals"].keys())
                    == sorted(t0["cell_totals"].keys()))
        cells_ok = t0["cell_totals"] == {
            "noise.by_reason.emoji_only": 1, "noise.total": 1,
            "review.suspended": -1, "review.verdicted.pass": 1,
            "review.verdicted.risky": 1}
        total_ok = t0["total"] == 0 == manual_sum(journal_db)
        call_ok = (json.dumps(t0) == json.dumps(face.cell_totals())
                   and json.dumps(t0, sort_keys=True)
                   == json.dumps(face.cell_totals(), sort_keys=True))
        comp_ok = (t0["ai_generated"] == 0 and t0["disclaimer"] == disc
                   and t0["persistent"] is True)
        empty_db = os.path.join(tmp, "empty_journal.db")
        empty_face = WJ.WaterJournalFace(empty_db, disc)
        try:
            zero_world = empty_face.cell_totals()
            zero_ok = (zero_world["cell_totals"] == {}
                       and zero_world["total"] == 0
                       and set(zero_world) == {"cell_totals", "total",
                                               "ai_generated",
                                               "disclaimer",
                                               "persistent"})
        finally:
            empty_face.close()
        record("AC-CT1",
               keys_ok and order_ok and cells_ok and total_ok
               and call_ok and comp_ok and zero_ok,
               "keys=%s ascending=%s cells=%s total0==sql-sum=%s "
               "double-call=%s compliance=%s zero-world=%s"
               % (keys_ok, order_ok, cells_ok, total_ok, call_ok,
                  comp_ok, zero_ok))

        # ---- AC-CT2: 14 bad window shapes fail closed ---------------
        bad_windows = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
                       "202610", "abcd", "", 2026, True, 2.5,
                       "2026-10\n", "2026-10 ", "2026-10\r"]
        n_before = row_count(journal_db)
        codes = []
        for bad in bad_windows:
            try:
                face.cell_totals(window=bad)
                codes.append("none")
            except ValueError as exc:
                codes.append(WJ.E_WJ_BAD_WINDOW
                             if WJ.E_WJ_BAD_WINDOW in str(exc)
                             else "other-ValueError")
        all_rej = codes == [WJ.E_WJ_BAD_WINDOW] * 14
        no_side = row_count(journal_db) == n_before
        record("AC-CT2", all_rej and no_side,
               "rejected=%d/14 code=%s rows-stable=%s"
               % (codes.count(WJ.E_WJ_BAD_WINDOW),
                  ",".join(sorted(set(codes))), no_side))

        # ---- AC-CT3: window filter semantics -------------------------
        insert_fixture_row(journal_db, "submit", {"noise.total": 2}, 2,
                           "2026-08-14T08:00:00.000000Z")
        insert_fixture_row(journal_db, "verdict",
                           {"review.suspended": -1,
                            "review.verdicted.pass": 1}, -1,
                           "2026-08-20T09:00:00.000000Z")
        aug = face.cell_totals(window="2026-08")
        aug_ok = (set(aug) == {"cell_totals", "total", "ai_generated",
                               "disclaimer", "persistent", "window"}
                  and aug["window"] == "2026-08"
                  and aug["cell_totals"] == {"noise.total": 2,
                                            "review.suspended": -1,
                                            "review.verdicted.pass": 1}
                  and aug["total"] == 1)
        full = face.cell_totals()
        full_ok = (full["cell_totals"]["noise.total"] == 3
                   and full["cell_totals"]["review.suspended"] == -2
                   and full["cell_totals"]["review.verdicted.pass"] == 2
                   and full["total"] == 1)
        curwin = face.cell_totals(window=cur_month)
        curwin_ok = (curwin["cell_totals"] == {
            "noise.by_reason.emoji_only": 1, "noise.total": 1,
            "review.suspended": -1, "review.verdicted.pass": 1,
            "review.verdicted.risky": 1}
            and curwin["total"] == 0)
        future = face.cell_totals(window="2027-01")
        future_ok = (future["cell_totals"] == {} and future["total"] == 0
                     and future["window"] == "2027-01")
        record("AC-CT3", aug_ok and full_ok and curwin_ok and future_ok,
               "history-window=%s default-includes-history=%s "
               "current-window-no-penetration=%s future-empty=%s"
               % (aug_ok, full_ok, curwin_ok, future_ok))

        # ---- AC-CT4: manual cross + composition + monthly_flow --------
        m_cells, m_total = manual_cells(journal_db)
        cells_eq = full["cell_totals"] == m_cells
        total_eq = full["total"] == m_total == manual_sum(journal_db)
        aug_m_cells, aug_m_total = manual_cells(
            journal_db, "WHERE substr(ts_utc, 1, 7) = ?", ("2026-08",))
        aug_eq = (aug["cell_totals"] == aug_m_cells
                  and aug["total"] == aug_m_total
                  and aug["total"] == manual_sum(
                      journal_db, "WHERE substr(ts_utc, 1, 7) = ?",
                      ("2026-08",)))
        comp_default = (full["total"]
                        == full["cell_totals"]["noise.total"]
                        + full["cell_totals"]["review.suspended"])
        comp_aug = (aug["total"] == aug["cell_totals"]["noise.total"]
                    + aug["cell_totals"]["review.suspended"])
        mf = face.monthly_flow()
        mf_aug = face.monthly_flow(window="2026-08")
        cross_ok = (full["total"] == mf["net_delta"]
                    and aug["total"] == mf_aug["net_delta"]
                    and curwin["total"]
                    == face.monthly_flow(window=cur_month)["net_delta"])
        record("AC-CT4",
               cells_eq and total_eq and aug_eq and comp_default
               and comp_aug and cross_ok,
               "cells==manual=%s total==sql-sum=%s window==manual=%s "
               "composition(default)=%s composition(2026-08)=%s "
               "monthly_flow-net-delta-x3=%s"
               % (cells_eq, total_eq, aug_eq, comp_default, comp_aug,
                  cross_ok))

        # ---- AC-CT5: pure-read law ------------------------------------
        method_src = inspect.getsource(WJ.WaterJournalFace.cell_totals)
        src_clean = ("INSERT" not in method_src
                     and "UPDATE" not in method_src
                     and "DELETE" not in method_src)
        n_a = row_count(journal_db)
        r1 = face.cell_totals()
        r1w = face.cell_totals(window="2026-08")
        r2 = face.cell_totals()
        r2w = face.cell_totals(window="2026-08")
        n_b = row_count(journal_db)
        same_calls = (json.dumps(r1) == json.dumps(r2)
                      and json.dumps(r1, sort_keys=True)
                      == json.dumps(r2, sort_keys=True)
                      and json.dumps(r1w) == json.dumps(r2w))
        record("AC-CT5", src_clean and n_a == n_b and same_calls,
               "read-method-clean=%s rows-stable=%s "
               "double-call-identical=%s"
               % (src_clean, n_a == n_b, same_calls))

        # ---- AC-CT6: liveness + restart continuity -------------------
        noise_before = face.cell_totals()["cell_totals"]["noise.total"]
        total_before = face.cell_totals()["total"]
        face.record("drain", env_noise)
        live = face.cell_totals()
        live_ok = (live["cell_totals"]["noise.total"] == noise_before + 1
                   and live["cell_totals"]["noise.by_reason.emoji_only"]
                   == 2
                   and live["total"] == total_before + 1)
        snap = face.cell_totals()
        face.close()
        face2 = WJ.WaterJournalFace(journal_db, disc)
        reopen = face2.cell_totals()
        reopen_ok = (json.dumps(reopen) == json.dumps(snap)
                     and json.dumps(reopen, sort_keys=True)
                     == json.dumps(snap, sort_keys=True))
        face2.record("submit", env_susp)
        after = face2.cell_totals()
        resume_ok = (after["cell_totals"]["review.suspended"]
                     == snap["cell_totals"]["review.suspended"] + 1
                     and after["total"] == snap["total"] + 1
                     and list(after["cell_totals"].keys())
                     == sorted(after["cell_totals"].keys()))
        record("AC-CT6", live_ok and reopen_ok and resume_ok,
               "liveness-plus-one=%s reopen-identical=%s "
               "resume-record-follows=%s"
               % (live_ok, reopen_ok, resume_ok))

        # ---- AC-CT7: hygiene + delivery -------------------------------
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
        tables = [r[0] for r in sqlite3.connect(
            face2.db_path).execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        schema_ok = set(tables) == {"water_windows", "sqlite_sequence"}
        frozen_ok = all(sha256_file(os.path.join(BASE, rel)) == sha
                        for rel, sha in frozen.items())
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ('"ugc-water-celltotals"' in reg_src
                  and "test_water_cell_totals.py" in reg_src)
        record("AC-CT7",
               ascii_ok and net_ok and source_law_ok and schema_ok
               and frozen_ok and reg_ok,
               "pure-ascii=%s import-lines-clean=%s append-only-source=%s "
               "schema-constant=%s frozen-bytes=%s registry-wired=%s"
               % (ascii_ok, net_ok, source_law_ok, schema_ok, frozen_ok,
                  reg_ok))
    finally:
        if face2 is not None:
            face2.close()

    ok_all = len(RESULTS) == EXPECTED and all(ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                             sum(1 for _a, ok in RESULTS if ok), EXPECTED),
          flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
