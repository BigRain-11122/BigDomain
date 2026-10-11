"""Acceptance suite for the free-trial calls-by-month pure
read face (BigDomain R1828 tech-queue row; seed = the
freetrial.py trial_calls table). Asserts the pre-registered
criteria AC-CBM1..AC-CBM7 from the R1828 tech.md claim line
(criteria were registered before this code existed; honesty
law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Family law = the R1730/R1732/R1735/R1784/R1793 window
parameterization line: default None keeps the full-window
behavior byte-stable; an explicit YYYY-MM month window keeps
only that month's cell; a malformed window fails closed
before any read. The month key derives from the called_utc
record-time column (single event family, single column).

History rows are injected straight into the trial_calls
table by this fixture (test-side direct writes, the R1730
family precedent, noted here): the product call gate is
bypassed on purpose so two synthetic past months can be
pinned deterministically. Injected rows respect the table's
own uniqueness constraint (distinct call_ref values).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_callmonth.py
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
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")

BAD_FORMS = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
             "202610", "abcd", "", 2026, True, 2.5,
             "2026-10\n", "2026-10 ", "2026-10\r"]

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

    tmp = tempfile.mkdtemp(prefix="freetrial-callmonth-")
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
    zero = ft.calls_by_month()
    ok_zero = (zero["calls_by_month"] == {}
               and zero["total"] == 0
               and set(zero.keys()) ==
               {"calls_by_month", "total", "disclaimer"}
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
                  "a1", "eng-a1")
    ft.trial_call("usr:alice", pa["plan_id"], "visualize",
                  "a2", "eng-a2")
    ft.trial_call("usr:bob", pb["plan_id"], "backtest",
                  "b1", "eng-b1")
    live_cur = 3                                   # real calls

    # -- history fixture rows (direct writes, noted in header) ----
    hist_rows = [
        (pa["plan_id"], "usr:hist-a", "backtest", "h1",
         "eng-h1", _stamp(m1, 2)),
        (pa["plan_id"], "usr:hist-a", "visualize", "h2",
         "eng-h2", _stamp(m1, 5)),
        (pb["plan_id"], "usr:hist-b", "backtest", "h3",
         "eng-h3", _stamp(m2, 3)),
        (pb["plan_id"], "usr:hist-b", "backtest", "h4",
         "eng-h4", _stamp(m2, 8)),
        (pb["plan_id"], "usr:hist-b", "visualize", "h5",
         "eng-h5", _stamp(m2, 9)),
    ]
    for pid, who, kind, ref, eng, ts in hist_rows:
        ftconn.execute(
            "INSERT INTO trial_calls (plan_id, dev_account,"
            " kind, call_ref, engine_ref, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (pid, who, kind, ref, eng, ts))
    ftconn.commit()

    counts_before = _counts()

    # -- AC-CBM1 contract, ascending keys, invariants -------------
    env = ft.calls_by_month()
    by = env["calls_by_month"]
    keys_sorted = sorted(by.keys())
    ok1 = (ok_zero
           and set(env.keys()) ==
           {"calls_by_month", "total", "disclaimer"}
           and keys_sorted == [m1, m2, cur_m]
           and list(by.keys()) == keys_sorted
           and by == {m1: 2, m2: 3, cur_m: live_cur}
           and env["total"] == 5 + live_cur
           and env["disclaimer"] == DISCLAIMER)
    wenv = ft.calls_by_month(cur_m)
    ok1 = (ok1
           and set(wenv.keys()) ==
           {"calls_by_month", "total", "disclaimer", "window"}
           and wenv["window"] == cur_m)
    with open(os.path.join(BASE, "config.json"), "rb") as h2:
        ok1 = ok1 and (h2.read() == cfg_bytes)
    record("AC-CBM1", ok1,
           "zero-call world honest empty (%s); envelope keys"
           " exact; month keys ascending %s; cells %s; total"
           " %s; window key additive on explicit read; config"
           " bytes stable"
           % (ok_zero, list(by.keys()), by, env["total"]))

    # -- AC-CBM2 malformed windows fail closed -------------------
    ok2 = True
    trace2 = []
    for form in BAD_FORMS:
        try:
            ft.calls_by_month(form)
            ok2 = False
            trace2.append("accepted:%r" % (form,))
        except T.TrialError as exc:
            if exc.code != T.E_FT_BAD_ARGS:
                ok2 = False
                trace2.append("wrongcode:%r" % (form,))
    ok2 = ok2 and (_counts() == counts_before)
    try:
        ft.calls_by_month(None)          # sole default sentinel
    except T.TrialError:
        ok2 = False
        trace2.append("None-rejected")
    record("AC-CBM2", ok2,
           "%d bad forms rejected E_FT_BAD_ARGS; four-table"
           " counts unchanged %s; None default accepted"
           % (len(BAD_FORMS), counts_before))

    # -- AC-CBM3 window filtering semantics ----------------------
    e_m1 = ft.calls_by_month(m1)
    e_m2 = ft.calls_by_month(m2)
    e_fut = ft.calls_by_month(fut)
    ok3 = (e_m1["calls_by_month"] == {m1: 2}
           and e_m1["total"] == 2
           and e_m2["calls_by_month"] == {m2: 3}
           and e_fut["calls_by_month"] == {}
           and e_fut["total"] == 0
           and set(e_m1["calls_by_month"].keys()) == {m1})
    default_read = ft.calls_by_month()
    ok3 = (ok3
           and set(default_read["calls_by_month"].keys()) ==
           {m1, m2, cur_m})
    record("AC-CBM3", ok3,
           "history month %s cell == {2}; month %s cell == {3};"
           " future %s honest empty; default read carries all"
           " three months; zero cross-month leakage"
           % (m1, m2, fut))

    # -- AC-CBM4 manual SQL cross-validation ---------------------
    sql_rows = ftconn.execute(
        "SELECT substr(called_utc, 1, 7), COUNT(*) FROM"
        " trial_calls GROUP BY substr(called_utc, 1, 7)"
        " ORDER BY substr(called_utc, 1, 7)").fetchall()
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
    ok4 = ok4 and (wsql == e_m2["total"])
    record("AC-CBM4", ok4,
           "per-cell counts == manual SQL GROUP BY; total %s =="
           " COUNT(*) == sum(cells); key order == SQL ORDER BY"
           " ascending; windowed total == manual SQL %s"
           % (env["total"], wsql))

    # -- AC-CBM5 pure-read law ------------------------------------
    src = inspect.getsource(T.FreeTrialFace.calls_by_month)
    banned = ("INSERT INTO", "REPLACE INTO",
              "UPDATE ", "DELETE FROM")
    ok5 = not any(b in src for b in banned)
    ok5 = ok5 and (_counts() == counts_before)
    a1 = json.dumps(ft.calls_by_month(), sort_keys=True)
    a2 = json.dumps(ft.calls_by_month(), sort_keys=True)
    b1 = json.dumps(ft.calls_by_month())
    b2 = json.dumps(ft.calls_by_month())
    ok5 = ok5 and (a1 == a2) and (b1 == b2)
    wa = json.dumps(ft.calls_by_month(m2), sort_keys=True)
    wb = json.dumps(ft.calls_by_month(m2), sort_keys=True)
    ok5 = ok5 and (wa == wb)
    record("AC-CBM5", ok5,
           "method source free of data-changing statements;"
           " four-table counts unchanged %s; double-call dumps"
           " byte-identical (sorted and insertion order);"
           " windowed double-call identical" % (counts_before,))

    # -- AC-CBM6 live zero-cache derivation ----------------------
    mid_counts = _counts()
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a3", "eng-a3")
    after = ft.calls_by_month()
    ok6 = (after["calls_by_month"][cur_m] ==
           by[cur_m] + 1
           and after["total"] == env["total"] + 1)
    w_after = ft.calls_by_month(cur_m)
    ok6 = (ok6
           and w_after["calls_by_month"][cur_m] ==
           by[cur_m] + 1)
    ok6 = ok6 and (ft.calls_by_month(m1)["calls_by_month"][m1] == 2)
    record("AC-CBM6", ok6,
           "new live call: current-month cell %s -> %s; total"
           " %s -> %s; windowed read follows; history month"
           " cell unchanged"
           % (by[cur_m], after["calls_by_month"][cur_m],
              env["total"], after["total"]))

    # -- AC-CBM7 hygiene and registration ------------------------
    with open(os.path.join(BASE, "freetrial.py"), "rb") as h3:
        src_bytes = h3.read()
    ok7 = all(b < 128 for b in src_bytes)
    imports = [ln.strip() for ln in
               src_bytes.decode("ascii").splitlines()
               if ln.strip().startswith("import ")]
    ok7 = ok7 and not any(
        lib in ln for ln in imports for lib in NET_LIBS)
    reg_path = os.path.join(os.path.dirname(BASE),
                            "reconcile_all.py")
    with open(reg_path, "r", encoding="utf-8") as h4:
        reg_text = h4.read()
    ok7 = ok7 and ("ledger-freetrial-callmonth" in reg_text
                   and "test_freetrial_callmonth.py" in reg_text)
    ok7 = ok7 and (len(RESULTS) + 1 == EXPECTED)
    record("AC-CBM7", ok7,
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
