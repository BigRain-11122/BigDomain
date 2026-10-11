"""Acceptance suite for the free-trial calls-by-engine pure
read face (BigDomain R1831 tech-queue row; seed = the
freetrial.py calls_by_kind R1829 face). Asserts the
pre-registered criteria AC-CBE1..AC-CBE8 from the R1831
tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Family law = the R1730/R1732/R1735/R1784/R1793 window
parameterization line: default None keeps the full-window
behavior byte-stable; an explicit YYYY-MM month window
filters rows by their called_utc record-time stamp first,
then aggregates engine stamps over the surviving rows (a
row-filter window, orthogonal to the calls_by_month cell
window). A malformed window fails closed before any read.

engine_ref is a free TEXT domain (trial_calls.engine_ref),
the engine attribution stamp (the apidev ring-3 convention:
a live call always carries a non-empty stamp): one injected
history row carries an engine stamp outside the live-call
gate's stamp set on purpose - the face must surface it, not
hide it (AC-CBE5, the R1776 AC-CHM3 law).

History rows are injected straight into the trial_calls
table by this fixture (test-side direct writes, the R1730
family precedent, noted here): the product call gate is
bypassed on purpose so two synthetic past months can be
pinned deterministically. Injected rows respect the table's
own uniqueness constraint (distinct call_ref values).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_callengine.py
"""

import datetime
import hashlib
import inspect
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700 registry)
import freetrial as T                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 8

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")

BAD_FORMS = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
             "202610", "abcd", "", 2026, True, 2.5,
             "2026-10\n", "2026-10 ", "2026-10\r"]

GHOST_ENGINE = "ghost-engine-probe"  # outside live-gate stamps

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _month_now():
    return datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m")


def _prev_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)


def _next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return "%04d-%02d" % (y, m)


def _stamp(ym, day):
    return "%s-%02dT12:00:00Z" % (ym, day)


def main():
    cur_m = _month_now()
    m2 = _prev_month(cur_m)          # the recent history month
    m1 = _prev_month(m2)             # the older history month
    fut = _next_month(cur_m)         # the future month

    tmp = tempfile.mkdtemp(prefix="freetrial-callengine-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)

    import sqlite3
    ftconn = sqlite3.connect(ft.db_path)

    def _counts():
        return tuple(
            ftconn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("trial_plans", "trial_grants",
                      "trial_calls", "trial_conversions"))

    # -- zero-call world first (honest empty state) ---------------
    zero = ft.calls_by_engine()
    ok_zero = (zero["calls_by_engine"] == {}
               and zero["total"] == 0
               and set(zero.keys()) ==
               {"calls_by_engine", "total", "disclaimer"}
               and zero["disclaimer"] == DISCLAIMER)

    # -- real flow: in-register dev, plans, grants, live calls ----
    dk.issue_key("usr:alice", "alice-key", 100,
                 ("backtest", "visualize"), False)
    dk.issue_key("usr:bob", "bob-key", 100, ("backtest",), True)
    pa = ft.register_trial_plan("alpha-starter",
                                "Alpha Starter Tier", 50, False)
    pb = ft.register_trial_plan("beta-pro", "Beta Pro Trial",
                                50, True)
    ft.grant_trial("usr:alice", pa["plan_id"])
    ft.grant_trial("usr:bob", pb["plan_id"])
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a1", "eng-x")
    ft.trial_call("usr:alice", pa["plan_id"], "visualize",
                  "a2", "eng-x")
    ft.trial_call("usr:bob", pb["plan_id"], "backtest",
                  "b1", "eng-y")
    live_cur = 3                                   # real calls

    # -- history fixture rows (direct writes, noted in header) ----
    # one row carries the out-of-domain ghost engine stamp on
    # purpose (the live gate always stamps eng-*, only direct
    # injection can produce anything else)
    hist_rows = [
        (pa["plan_id"], "usr:hist-a", "backtest", "h1",
         "eng-x", _stamp(m1, 2)),
        (pa["plan_id"], "usr:hist-a", "visualize", "h2",
         "eng-z", _stamp(m1, 5)),
        (pb["plan_id"], "usr:hist-b", "backtest", "h3",
         "eng-x", _stamp(m2, 3)),
        (pb["plan_id"], "usr:hist-b", "backtest", "h4",
         "eng-y", _stamp(m2, 8)),
        (pb["plan_id"], "usr:hist-b", "visualize", "h5",
         "eng-z", _stamp(m2, 9)),
        (pb["plan_id"], "usr:hist-b", "backtest", "h6",
         GHOST_ENGINE, _stamp(m2, 11)),
    ]
    for pid, who, kind, ref, eng, ts in hist_rows:
        ftconn.execute(
            "INSERT INTO trial_calls (plan_id, dev_account,"
            " kind, call_ref, engine_ref, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (pid, who, kind, ref, eng, ts))
    ftconn.commit()

    counts_before = _counts()

    # full-window expectations:
    #   eng-x = 2(live) + 1(m1) + 1(m2) = 4
    #   eng-y = 1(live) + 1(m2) = 2
    #   eng-z = 1(m1) + 1(m2) = 2
    #   ghost-engine-probe = 1 (m2 fixture)
    want_full = {"eng-x": 4, "eng-y": 2,
                 "eng-z": 2, GHOST_ENGINE: 1}
    want_total = 9

    # -- AC-CBE1 contract, ascending keys, invariants -------------
    env = ft.calls_by_engine()
    by = env["calls_by_engine"]
    keys_sorted = sorted(by.keys())
    ok1 = (ok_zero
           and set(env.keys()) ==
           {"calls_by_engine", "total", "disclaimer"}
           and keys_sorted == ["eng-x", "eng-y", "eng-z",
                              GHOST_ENGINE]
           and list(by.keys()) == keys_sorted
           and by == want_full
           and env["total"] == want_total
           and sum(by.values()) == want_total
           and env["disclaimer"] == DISCLAIMER)
    wenv = ft.calls_by_engine(cur_m)
    ok1 = (ok1
           and set(wenv.keys()) ==
           {"calls_by_engine", "total", "disclaimer", "window"}
           and wenv["window"] == cur_m)
    with open(os.path.join(BASE, "config.json"), "rb") as h2:
        ok1 = ok1 and (h2.read() == cfg_bytes)
    record("AC-CBE1", ok1,
           "zero-call world honest empty (%s); envelope keys"
           " exact; engine keys ascending %s; cells %s; total"
           " %s == sum == COUNT; window key additive on"
           " explicit read; config bytes stable"
           % (ok_zero, list(by.keys()), by, env["total"]))

    # -- AC-CBE2 malformed windows fail closed -------------------
    ok2 = True
    trace2 = []
    for form in BAD_FORMS:
        try:
            ft.calls_by_engine(form)
            ok2 = False
            trace2.append("accepted:%r" % (form,))
        except T.TrialError as exc:
            if exc.code != T.E_FT_BAD_ARGS:
                ok2 = False
                trace2.append("wrongcode:%r" % (form,))
    ok2 = ok2 and (_counts() == counts_before)
    try:
        ft.calls_by_engine(None)      # sole default sentinel
    except T.TrialError:
        ok2 = False
        trace2.append("None-rejected")
    record("AC-CBE2", ok2,
           "%d bad forms rejected E_FT_BAD_ARGS; four-table"
           " counts unchanged %s; None default accepted %s"
           % (len(BAD_FORMS), counts_before, trace2))

    # -- AC-CBE3 window filtering semantics ----------------------
    e_m1 = ft.calls_by_engine(m1)
    e_m2 = ft.calls_by_engine(m2)
    e_fut = ft.calls_by_engine(fut)
    ok3 = (e_m1["calls_by_engine"] == {"eng-x": 1, "eng-z": 1}
           and e_m1["total"] == 2
           and e_m2["calls_by_engine"] ==
           {"eng-x": 1, "eng-y": 1, "eng-z": 1,
            GHOST_ENGINE: 1}
           and e_m2["total"] == 4
           and e_fut["calls_by_engine"] == {}
           and e_fut["total"] == 0
           and e_m1["window"] == m1)
    default_read = ft.calls_by_engine()
    ok3 = (ok3
           and default_read["calls_by_engine"] == want_full
           and set(e_m1["calls_by_engine"].keys()) ==
           {"eng-x", "eng-z"})
    record("AC-CBE3", ok3,
           "month %s engine profile %s; month %s engine profile"
           " %s; future %s honest empty; default read carries"
           " all observed engines; zero cross-month leakage"
           % (m1, e_m1["calls_by_engine"], m2,
              e_m2["calls_by_engine"], fut))

    # -- AC-CBE4 manual SQL cross-validation ---------------------
    sql_rows = ftconn.execute(
        "SELECT engine_ref, COUNT(*) FROM trial_calls"
        " GROUP BY engine_ref"
        " ORDER BY engine_ref").fetchall()
    sql_map = {str(r[0]): int(r[1]) for r in sql_rows}
    sql_order = [str(r[0]) for r in sql_rows]
    sql_total = ftconn.execute(
        "SELECT COUNT(*) FROM trial_calls").fetchone()[0]
    ok4 = (sql_map == by
           and sql_order == list(by.keys())
           and sql_total == env["total"]
           and sum(by.values()) == env["total"])
    wsql = ftconn.execute(
        "SELECT COUNT(*) FROM trial_calls WHERE"
        " substr(called_utc, 1, 7) = ?",
        (m2,)).fetchone()[0]
    wsql_eng = ftconn.execute(
        "SELECT engine_ref, COUNT(*) FROM trial_calls WHERE"
        " substr(called_utc, 1, 7) = ?"
        " GROUP BY engine_ref ORDER BY engine_ref",
        (m2,)).fetchall()
    ok4 = (ok4
           and wsql == e_m2["total"]
           and {str(r[0]): int(r[1]) for r in wsql_eng} ==
           e_m2["calls_by_engine"])
    record("AC-CBE4", ok4,
           "per-engine counts == manual SQL GROUP BY; total %s =="
           " COUNT(*) == sum(cells); key order == SQL ORDER BY"
           " ascending %s; windowed total == manual SQL %s;"
           " windowed engine map == windowed SQL"
           % (env["total"], sql_order, wsql))

    # -- AC-CBE5 free-domain non-hiding law -----------------------
    keys_now = list(by.keys())
    ok5 = (GHOST_ENGINE in by
           and by[GHOST_ENGINE] == 1
           and keys_now.index(GHOST_ENGINE) == 3
           and keys_now.index("eng-x") == 0
           and keys_now.index("eng-y") == 1
           and keys_now.index("eng-z") == 2
           and (by["eng-x"] + by["eng-y"] + by["eng-z"]) ==
           want_total - 1
           and env["total"] == want_total
           and GHOST_ENGINE in e_m2["calls_by_engine"]
           and e_m2["calls_by_engine"][GHOST_ENGINE] == 1
           and GHOST_ENGINE not in e_m1["calls_by_engine"])
    record("AC-CBE5", ok5,
           "out-of-domain engine %r surfaced in full read (cell"
           " %s, ascending slot %d of %s) and counted toward"
           " total %s (live-gate engines sum %s); surfaced in"
           " its month window; absent from months without it -"
           " the face never hides observed data"
           % (GHOST_ENGINE, by[GHOST_ENGINE],
              keys_now.index(GHOST_ENGINE) + 1, keys_now,
              env["total"],
              by["eng-x"] + by["eng-y"] + by["eng-z"]))

    # -- AC-CBE6 pure-read law ------------------------------------
    src = inspect.getsource(T.FreeTrialFace.calls_by_engine)
    banned = ("INSERT INTO", "REPLACE INTO",
              "UPDATE ", "DELETE FROM")
    ok6 = not any(b in src for b in banned)
    ok6 = ok6 and (_counts() == counts_before)
    a1_ = json.dumps(ft.calls_by_engine(), sort_keys=True)
    a2_ = json.dumps(ft.calls_by_engine(), sort_keys=True)
    b1_ = json.dumps(ft.calls_by_engine())
    b2_ = json.dumps(ft.calls_by_engine())
    ok6 = ok6 and (a1_ == a2_) and (b1_ == b2_)
    wa = json.dumps(ft.calls_by_engine(m2), sort_keys=True)
    wb = json.dumps(ft.calls_by_engine(m2), sort_keys=True)
    ok6 = ok6 and (wa == wb)
    record("AC-CBE6", ok6,
           "method source free of data-changing statements;"
           " four-table counts unchanged %s; double-call dumps"
           " byte-identical (sorted and insertion order);"
           " windowed double-call identical" % (counts_before,))

    # -- AC-CBE7 live zero-cache derivation ----------------------
    mid_counts = _counts()
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a3", "eng-x")
    after = ft.calls_by_engine()
    ok7 = (after["calls_by_engine"]["eng-x"] ==
           by["eng-x"] + 1
           and after["total"] == env["total"] + 1
           and after["calls_by_engine"][GHOST_ENGINE] == 1
           and after["calls_by_engine"]["eng-y"] == 2
           and after["calls_by_engine"]["eng-z"] == 2)
    w_after = ft.calls_by_engine(cur_m)
    ok7 = (ok7
           and w_after["calls_by_engine"]["eng-x"] == 3
           and w_after["total"] == live_cur + 1)
    ok7 = ok7 and (ft.calls_by_engine(m1)["calls_by_engine"] ==
                   {"eng-x": 1, "eng-z": 1})
    ok7 = ok7 and (_counts() != mid_counts)
    record("AC-CBE7", ok7,
           "new live call: eng-x cell %s -> %s; total %s ->"
           " %s; ghost/eng-y/eng-z cells unchanged; windowed"
           " read follows (cur window eng-x -> %s); history"
           " month engine profile unchanged"
           % (by["eng-x"],
              after["calls_by_engine"]["eng-x"],
              env["total"], after["total"],
              w_after["calls_by_engine"]["eng-x"]))

    # -- AC-CBE8 hygiene and registration ------------------------
    with open(os.path.join(BASE, "freetrial.py"), "rb") as h3:
        src_bytes = h3.read()
    ok8 = all(b < 128 for b in src_bytes)
    imports = [ln.strip() for ln in
               src_bytes.decode("ascii").splitlines()
               if ln.strip().startswith("import ")]
    ok8 = ok8 and not any(
        lib in ln for ln in imports for lib in NET_LIBS)
    reg_path = os.path.join(os.path.dirname(BASE),
                            "reconcile_all.py")
    with open(reg_path, "r", encoding="utf-8") as h4:
        reg_text = h4.read()
    ok8 = (ok8
           and "ledger-freetrial-callengine" in reg_text
           and "test_freetrial_callengine.py" in reg_text)
    ok8 = ok8 and (len(RESULTS) + 1 == EXPECTED)
    record("AC-CBE8", ok8,
           "freetrial.py pure ASCII; import lines network-free"
           " (%d imports); SUITES registration row present;"
           " criteria drift self-check %d+1==%d"
           % (len(imports), len(RESULTS), EXPECTED))

    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d exit=%d"
          % ("PASS" if fail == 0 else "FAIL",
             len(RESULTS) - fail, len(RESULTS),
             0 if fail == 0 else 1), flush=True)
    ft.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
