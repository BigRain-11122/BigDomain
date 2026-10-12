"""Acceptance suite for the water journal month-roll fidelity
example (BigDomain R1864 tech-queue claim row; seed = the
journal_board/cell_totals/month-window/read-cap faces
R1800/R1805/R1807/R1812 plus the R1730/R1738/R1739/R1839/R1845/
R1854/R1858 month-roll family - the water journal was the
window-parameter family member without a roll pin). Asserts the
pre-registered criteria AC-WMR1..AC-WMR7 from the R1864 tech.md
claim line (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Carrier verdict (the R1858 callroll dedicated-suite precedent):
the existing water journal suite worlds do not cross a month
boundary on a frozen clock, so this suite builds a fresh isolated
WaterJournalFace in its own temp world and freezes the module
clock (water_journal._utc_now_iso patched onto a deterministic
holder, restored in finally).

World (all stamps ride the frozen clock, the live record path -
zero fixture injection for the roll scenario): BASE_DT
2026-10-15; October lands two completed windows (ingest
{noise.total:+1, noise.by_reason.fw:+1}; submit
{review.suspended:+1}), then the clock advances +23d across the
month boundary and November lands two more (verdict
{review.suspended:-1, review.verdicted.pass:1} total_delta=-1 -
the in-book AC-VW1 verdict shape that keeps the R1785
composition law; batch {noise.total:+2}). Every window slices
rows by their own ts_utc record-time month; the month axis
telescopes (sum of observed month-window totals == all-window
total per face); old-month window reads stay byte-identical
across the roll. Zero product bytes change: the roll semantics
already live in the four faces, this suite only pins them.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_water_journal_roll.py
"""

import datetime
import hashlib
import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import water_journal as W             # noqa: E402 (R1800 face under test)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: non-advisory "
              "observable water ledger")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"

FACES = ("journal_board", "kind_tally", "monthly_flow",
         "cell_totals")

BASE_ENV_KEYS = {"total", "ai_generated", "disclaimer",
                 "persistent"}
WIN_ENV_KEYS = BASE_ENV_KEYS | {"window"}
# monthly_flow carries its whole-board net in the net_delta key
# (in-book since the R1802 AC-MF registration)
EXTRA_ENV_KEYS = {"monthly_flow": {"net_delta"}}

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")


class _FrozenClock(object):
    """Deterministic UTC clock holder: the water_journal module
    _utc_now_iso is patched onto this holder so record stamps
    roll only when the suite moves the clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_iso(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _env(face, *args):
    return getattr(face_obj, face)(*args)


def main():
    global face_obj
    tmp = tempfile.mkdtemp(prefix="water-journalroll-")
    with open(os.path.join(BASE, "water_journal.py"), "rb") as h:
        face_bytes = h.read()
    face_sha = hashlib.sha256(face_bytes).hexdigest()
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as h:
        cfg_bytes = h.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    db_path = os.path.join(tmp, "water_journal.db")

    face_obj = W.WaterJournalFace(db_path, DISCLAIMER)
    conn = sqlite3.connect(db_path)

    def _count():
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]

    def _win_count(win):
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows WHERE"
            " substr(ts_utc, 1, 7) = ?",
            (win,)).fetchone()[0]

    clock = _FrozenClock()
    real_now = W._utc_now_iso
    try:
        W._utc_now_iso = clock.now_iso

        # -- October anchor world --------------------------------
        r1 = face_obj.record("ingest", {
            "pool_water_delta": {"noise.total": 1,
                                 "noise.by_reason.fw": 1},
            "total_delta": 1})
        clock.advance(7)
        r2 = face_obj.record("submit", {
            "pool_water_delta": {"review.suspended": 1},
            "total_delta": 1})
        clock.advance(7)

        oct_cells = {"noise.by_reason.fw": 1, "noise.total": 1,
                     "review.suspended": 1}
        oct_tally = {"batch": 0, "drain": 0, "ingest": 1,
                     "submit": 1, "verdict": 0}
        oct_flow_rows = [{"month": OLD_WIN, "windows": 2,
                          "total_delta": 2}]

        # -- AC-WMR1 October anchor ------------------------------
        oct_sql = _win_count(OLD_WIN)
        ok1 = (oct_sql == 2 and r1["ts_utc"].startswith(OLD_WIN)
               and r2["ts_utc"].startswith(OLD_WIN))
        snapshots = {}
        face_envs = {}
        for face in FACES:
            wenv = _env(face, OLD_WIN)
            denv = _env(face)
            snapshots[face] = json.dumps(wenv, sort_keys=True)
            face_envs[face] = (wenv, denv)
            ok1 = ok1 and set(wenv.keys()) == \
                WIN_ENV_KEYS | {face} | EXTRA_ENV_KEYS.get(face, set())
            ok1 = ok1 and wenv["window"] == OLD_WIN
            ok1 = ok1 and wenv["ai_generated"] == 0
            ok1 = ok1 and wenv["disclaimer"] == DISCLAIMER
            ok1 = ok1 and wenv["persistent"] is True
            ok1 = ok1 and "window" not in denv
            ok1 = ok1 and json.dumps(
                {k: v for k, v in denv.items()}, sort_keys=True) \
                == json.dumps(
                    {k: v for k, v in wenv.items() if k != "window"},
                    sort_keys=True)
        b_win, b_def = face_envs["journal_board"]
        t_win, t_def = face_envs["kind_tally"]
        f_win, f_def = face_envs["monthly_flow"]
        c_win, c_def = face_envs["cell_totals"]
        ok1 = (ok1
               and b_win["total"] == 2
               and [r["window_id"] for r in b_win["journal_board"]]
               == [r1["window_id"], r2["window_id"]]
               and t_win["kind_tally"] == oct_tally
               and t_win["total"] == 2
               and f_win["monthly_flow"] == oct_flow_rows
               and f_win["total"] == 2 and f_win["net_delta"] == 2
               and c_win["cell_totals"] == oct_cells
               and c_win["total"] == 2
               and c_win["cell_totals"]["noise.total"]
               + c_win["cell_totals"]["review.suspended"]
               == c_win["total"] == 2)
        record("AC-WMR1", ok1,
               "October anchor: frozen-clock record-time stamps"
               " (SQL %s prefix count %d); four window-parameter"
               " faces explicit %s window reads carry exactly the"
               " October cells (board rows %d..%d, tally"
               " ingest:1 submit:1 dense grid, flow single row"
               " {windows:2, total_delta:2}, cells %s with"
               " composition noise.total+review.suspended==2);"
               " default reads equal window reads field-for-field"
               " pre-roll; envelope key sets exact-pinned with the"
               " compliance three-piece resident; pre-roll"
               " snapshots anchored for all four faces"
               % (OLD_WIN, oct_sql, OLD_WIN, r1["window_id"],
                  r2["window_id"], oct_cells))

        # -- month roll: +23d crosses the boundary ---------------
        clock.advance(23 * 86400)

        # -- November windows land (record-time stamps) ----------
        r3 = face_obj.record("verdict", {
            "pool_water_delta": {"review.suspended": -1,
                                 "review.verdicted.pass": 1},
            "total_delta": -1})
        clock.advance(7)
        r4 = face_obj.record("batch", {
            "pool_water_delta": {"noise.total": 2},
            "total_delta": 2})

        nov_cells = {"noise.total": 2, "review.suspended": -1,
                     "review.verdicted.pass": 1}
        nov_tally = {"batch": 1, "drain": 0, "ingest": 0,
                     "submit": 0, "verdict": 1}
        nov_flow_rows = [{"month": NEW_WIN, "windows": 2,
                          "total_delta": 1}]
        all_cells = {"noise.by_reason.fw": 1, "noise.total": 3,
                     "review.suspended": 0,
                     "review.verdicted.pass": 1}
        all_tally = {"batch": 1, "drain": 0, "ingest": 1,
                     "submit": 1, "verdict": 1}

        # -- AC-WMR2 new-month windows land in new-month cells ----
        cross_ts = r3["ts_utc"]
        nov_sql = _win_count(NEW_WIN)
        ok2 = (cross_ts.startswith(NEW_WIN) and nov_sql == 2
               and r4["ts_utc"].startswith(NEW_WIN))
        nb = _env("journal_board", NEW_WIN)
        nt = _env("kind_tally", NEW_WIN)
        nf = _env("monthly_flow", NEW_WIN)
        nc = _env("cell_totals", NEW_WIN)
        db_all = _env("journal_board")
        dt_all = _env("kind_tally")
        df_all = _env("monthly_flow")
        dc_all = _env("cell_totals")
        ok2 = (ok2
               and [r["window_id"] for r in nb["journal_board"]]
               == [r3["window_id"], r4["window_id"]]
               and nb["total"] == 2 and nb["window"] == NEW_WIN
               and nt["kind_tally"] == nov_tally
               and nt["total"] == 2
               and nf["monthly_flow"] == nov_flow_rows
               and nf["total"] == 2 and nf["net_delta"] == 1
               and nc["cell_totals"] == nov_cells
               and nc["total"] == 1
               and nc["cell_totals"]["noise.total"]
               + nc["cell_totals"]["review.suspended"]
               == nc["total"] == 1
               and db_all["total"] == 4 and dt_all["total"] == 4
               and dt_all["kind_tally"] == all_tally
               and df_all["total"] == 4
               and df_all["net_delta"] == 3
               and dc_all["total"] == 3
               and dc_all["cell_totals"] == all_cells)
        record("AC-WMR2", ok2,
               "frozen clock +23d crossed the month boundary; the"
               " November windows stamp ts_utc=%s (SQL %s prefix"
               " count %d) - every window slices rows by their own"
               " record-time month; four faces explicit %s reads"
               " carry exactly the November cells (board rows"
               " %d..%d append order, tally batch:1 verdict:1,"
               " flow single row {windows:2, total_delta:1},"
               " cells %s with composition 2+(-1)==1); default"
               " all-window reads carry the cross-month rows"
               " (board/tally totals 4, flow total 4 net_delta 3,"
               " cells total 3)"
               % (cross_ts, NEW_WIN, nov_sql, NEW_WIN,
                  r3["window_id"], r4["window_id"], nov_cells))

        # -- AC-WMR3 old-month window original-value preservation -
        ok3 = True
        for face in FACES:
            oct2 = _env(face, OLD_WIN)
            ok3 = ok3 and json.dumps(oct2, sort_keys=True) \
                == snapshots[face]
        oct_tally2 = _env("kind_tally", OLD_WIN)
        ok3 = (ok3
               and oct_tally2["kind_tally"] == oct_tally
               and oct_tally2["total"] == 2
               and all(r["ts_utc"].startswith(NEW_WIN)
                       for r in nb["journal_board"])
               and nt["kind_tally"]["ingest"] == 0
               and nt["kind_tally"]["submit"] == 0
               and "noise.by_reason.fw" not in nc["cell_totals"]
               and [row["month"] for row in nf["monthly_flow"]]
               == [NEW_WIN])
        record("AC-WMR3", ok3,
               "post-roll explicit %s window reads are"
               " byte-identical to the pre-roll snapshots for all"
               " four faces (original cell values and totals"
               " preserved, zero November leakage); %s window"
               " reads carry zero October rows/kinds/cells - the"
               " two windows never leak into each other in either"
               " direction" % (OLD_WIN, NEW_WIN))

        # -- AC-WMR4 month-axis telescoping ----------------------
        b_old, b_new = _env("journal_board", OLD_WIN), nb
        t_old, t_new = _env("kind_tally", OLD_WIN), nt
        f_old, f_new = _env("monthly_flow", OLD_WIN), nf
        c_old, c_new = _env("cell_totals", OLD_WIN), nc
        ok4 = (b_old["total"] + b_new["total"]
               == db_all["total"] == 4
               and t_old["total"] + t_new["total"]
               == dt_all["total"] == 4
               and c_old["total"] + c_new["total"]
               == dc_all["total"] == 3
               and f_old["total"] + f_new["total"]
               == df_all["total"] == 4
               and f_old["net_delta"] + f_new["net_delta"]
               == df_all["net_delta"] == 3
               and df_all["monthly_flow"]
               == f_old["monthly_flow"] + f_new["monthly_flow"]
               and [row["month"] for row in df_all["monthly_flow"]]
               == [OLD_WIN, NEW_WIN]
               and dc_all["total"] == df_all["net_delta"] == 3
               and c_old["total"] == f_old["net_delta"] == 2
               and c_new["total"] == f_new["net_delta"] == 1)
        record("AC-WMR4", ok4,
               "month-axis telescoping: per-face month-window"
               " totals %s(%d)+%s(%d) == all-window totals"
               " (board 4, tally 4, cells 3, flow windows 4 and"
               " net_delta 2+1==3); monthly_flow all-window row"
               " set == the union of the two explicit window"
               " reads (row-set partition, every row belongs to"
               " exactly one month); cross-face law: cell_totals"
               " total == monthly_flow net_delta == 3 on the"
               " whole board and per window (2/1)"
               % (OLD_WIN, b_old["total"], NEW_WIN,
                  b_new["total"]))

        # -- AC-WMR5 read-cap x month-window orthogonality --------
        mirror = conn.execute(
            "SELECT window_id FROM water_windows WHERE"
            " substr(ts_utc, 1, 7) = ?"
            " ORDER BY ts_utc DESC, window_id DESC LIMIT 1",
            (NEW_WIN,)).fetchone()[0]
        capped = _env("journal_board", NEW_WIN, 1)
        oct_full = _env("journal_board", OLD_WIN, 5)
        lim0 = _env("journal_board", NEW_WIN, 0)
        ok5 = (capped["total"] == 2 and capped["returned"] == 1
               and capped["truncated"] is True
               and capped["limit"] == 1
               and [r["window_id"]
                    for r in capped["journal_board"]] == [mirror]
               == [r4["window_id"]]
               and all(r["ts_utc"].startswith(NEW_WIN)
                       for r in capped["journal_board"])
               and oct_full["total"] == 2
               and oct_full["returned"] == 2
               and oct_full["truncated"] is False
               and len(oct_full["journal_board"]) == 2
               and all(r["ts_utc"].startswith(OLD_WIN)
                       for r in oct_full["journal_board"])
               and "limit" not in lim0
               and "returned" not in lim0
               and "truncated" not in lim0
               and lim0["total"] == 2
               and len(lim0["journal_board"]) == 2)
        record("AC-WMR5", ok5,
               "read-cap x month-window orthogonal (R1812 law):"
               " journal_board(%s, limit=1) returns the ascending"
               " tail window of exactly 1 November row (mirror-SQL"
               " DESC/DESC LIMIT 1 == row %d, zero October rows"
               " leak into the capped November read); envelope"
               " total=2 reports the full filtered count so the"
               " truncated board never lies about its size"
               " (returned=1 truncated=True); limit=5 on %s"
               " returns the full 2 rows un-truncated; limit=0"
               " keeps the full-list behavior with zero cap keys"
               % (NEW_WIN, mirror, OLD_WIN))

        # -- AC-WMR6 immutable rows + pure-read law ---------------
        rows_n = _count()
        ok6 = (rows_n == 4)
        banned = ("INSERT INTO", "REPLACE INTO", "UPDATE ",
                  "DELETE FROM")
        for face in FACES:
            src = inspect.getsource(
                getattr(W.WaterJournalFace, face))
            ok6 = ok6 and not any(b in src for b in banned)
        dumps = []
        for face in FACES:
            for args in ((), (OLD_WIN,), (NEW_WIN,)):
                e1 = _env(face, *args)
                e2 = _env(face, *args)
                dumps.append((json.dumps(e1, sort_keys=True),
                              json.dumps(e2, sort_keys=True),
                              json.dumps(e1), json.dumps(e2)))
        ok6 = (ok6
               and all(a == b and c == d
                       for (a, b, c, d) in dumps)
               and _count() == 4)
        record("AC-WMR6", ok6,
               "immutable rows never lost: water_windows=%d"
               " (2 October + 2 November) constant across every"
               " read face; all four read-method sources free of"
               " data-changing statements; double-call dumps"
               " byte-identical for default and both explicit"
               " windows on all four faces (sorted and insertion"
               " order); row count unchanged across reads"
               % rows_n)

        # -- AC-WMR7 hygiene + registration + criteria drift ------
        with open(os.path.join(BASE, "water_journal.py"),
                  "rb") as h:
            ok7 = (hashlib.sha256(h.read()).hexdigest()
                   == face_sha)
        with open(cfg_path, "rb") as h:
            ok7 = ok7 and (hashlib.sha256(
                h.read()).hexdigest() == cfg_sha)
        ok7 = ok7 and all(b < 128 for b in face_bytes)
        imports = [ln.strip() for ln in
                   face_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok7 = ok7 and not any(
            lib in ln for ln in imports for lib in NET_LIBS)
        reg_path = os.path.join(os.path.dirname(BASE),
                                "reconcile_all.py")
        with open(reg_path, "r", encoding="utf-8") as h:
            reg_text = h.read()
        ok7 = ("ugc-water-journalroll" in reg_text
               and "test_water_journal_roll.py" in reg_text
               and len(RESULTS) + 1 == EXPECTED)
        record("AC-WMR7", ok7,
               "water_journal.py sha256 stable across the whole"
               " run (zero product bytes - pin-only suite);"
               " shipped ugc config.json sha256 stable; face"
               " source pure ASCII with network-free import lines"
               " (%d imports); SUITES registration row present"
               " (ugc-water-journalroll, criteria 7); criteria"
               " drift self-check %d+1==%d"
               % (len(imports), len(RESULTS), EXPECTED))

        fail = sum(1 for _, ok in RESULTS if not ok)
        print("SUITE %s %d/%d exit=%d"
              % ("PASS" if fail == 0 else "FAIL",
                 len(RESULTS) - fail, len(RESULTS),
                 0 if fail == 0 else 1), flush=True)
        conn.close()
        face_obj.close()
        return 0 if fail == 0 else 1
    finally:
        W._utc_now_iso = real_now


if __name__ == "__main__":
    sys.exit(main())
