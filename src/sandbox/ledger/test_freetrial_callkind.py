"""Acceptance suite for the free-trial calls-by-kind pure
read face (BigDomain R1829 tech-queue row; seed = the
freetrial.py calls_by_month R1828 face). Asserts the
pre-registered criteria AC-CBK1..AC-CBK8 from the R1829
tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Family law = the R1730/R1732/R1735/R1784/R1793 window
parameterization line: default None keeps the full-window
behavior byte-stable; an explicit YYYY-MM month window
filters rows by their called_utc record-time stamp first,
then aggregates kinds over the surviving rows (a row-filter
window, orthogonal to the calls_by_month cell window). A
malformed window fails closed before any read.

kind is a free TEXT domain (trial_calls.kind, no CHECK
constraint): one injected history row carries a kind outside
the registered usage tally domain on purpose - the face must
surface it, not hide it (AC-CBK5, the R1776 AC-CHM3 law).

History rows are injected straight into the trial_calls
table by this fixture (test-side direct writes, the R1730
family precedent, noted here): the product call gate is
bypassed on purpose so two synthetic past months can be
pinned deterministically. Injected rows respect the table's
own uniqueness constraint (distinct call_ref values).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_callkind.py
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

GHOST_KIND = "ghost-probe"      # outside the tally domain (AC-CBK5)

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

    tmp = tempfile.mkdtemp(prefix="freetrial-callkind-")
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
    zero = ft.calls_by_kind()
    ok_zero = (zero["calls_by_kind"] == {}
               and zero["total"] == 0
               and set(zero.keys()) ==
               {"calls_by_kind", "total", "disclaimer"}
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
    # one row carries the out-of-domain ghost kind on purpose
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
        (pb["plan_id"], "usr:hist-b", GHOST_KIND, "h6",
         "eng-h6", _stamp(m2, 11)),
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
    #   backtest = 1(m1) + 2(m2) + 2(live) = 5
    #   ghost-probe = 1 (m2 fixture)
    #   visualize = 1(m1) + 1(m2) + 1(live) = 3
    want_full = {"backtest": 5, GHOST_KIND: 1, "visualize": 3}
    want_total = 9

    # -- AC-CBK1 contract, ascending keys, invariants -------------
    env = ft.calls_by_kind()
    by = env["calls_by_kind"]
    keys_sorted = sorted(by.keys())
    ok1 = (ok_zero
           and set(env.keys()) ==
           {"calls_by_kind", "total", "disclaimer"}
           and keys_sorted == ["backtest", GHOST_KIND,
                               "visualize"]
           and list(by.keys()) == keys_sorted
           and by == want_full
           and env["total"] == want_total
           and sum(by.values()) == want_total
           and env["disclaimer"] == DISCLAIMER)
    wenv = ft.calls_by_kind(cur_m)
    ok1 = (ok1
           and set(wenv.keys()) ==
           {"calls_by_kind", "total", "disclaimer", "window"}
           and wenv["window"] == cur_m)
    with open(os.path.join(BASE, "config.json"), "rb") as h2:
        ok1 = ok1 and (h2.read() == cfg_bytes)
    record("AC-CBK1", ok1,
           "zero-call world honest empty (%s); envelope keys"
           " exact; kind keys ascending %s; cells %s; total %s"
           " == sum == COUNT; window key additive on explicit"
           " read; config bytes stable"
           % (ok_zero, list(by.keys()), by, env["total"]))

    # -- AC-CBK2 malformed windows fail closed -------------------
    ok2 = True
    trace2 = []
    for form in BAD_FORMS:
        try:
            ft.calls_by_kind(form)
            ok2 = False
            trace2.append("accepted:%r" % (form,))
        except T.TrialError as exc:
            if exc.code != T.E_FT_BAD_ARGS:
                ok2 = False
                trace2.append("wrongcode:%r" % (form,))
    ok2 = ok2 and (_counts() == counts_before)
    try:
        ft.calls_by_kind(None)          # sole default sentinel
    except T.TrialError:
        ok2 = False
        trace2.append("None-rejected")
    record("AC-CBK2", ok2,
           "%d bad forms rejected E_FT_BAD_ARGS; four-table"
           " counts unchanged %s; None default accepted %s"
           % (len(BAD_FORMS), counts_before, trace2))

    # -- AC-CBK3 window filtering semantics ----------------------
    e_m1 = ft.calls_by_kind(m1)
    e_m2 = ft.calls_by_kind(m2)
    e_fut = ft.calls_by_kind(fut)
    ok3 = (e_m1["calls_by_kind"] == {"backtest": 1,
                                     "visualize": 1}
           and e_m1["total"] == 2
           and e_m2["calls_by_kind"] ==
           {"backtest": 2, GHOST_KIND: 1, "visualize": 1}
           and e_m2["total"] == 4
           and e_fut["calls_by_kind"] == {}
           and e_fut["total"] == 0
           and e_m1["window"] == m1)
    default_read = ft.calls_by_kind()
    ok3 = (ok3
           and default_read["calls_by_kind"] == want_full
           and set(e_m1["calls_by_kind"].keys()) ==
           {"backtest", "visualize"})
    record("AC-CBK3", ok3,
           "month %s kind profile %s; month %s kind profile"
           " %s; future %s honest empty; default read carries"
           " all observed kinds; zero cross-month leakage"
           % (m1, e_m1["calls_by_kind"], m2,
              e_m2["calls_by_kind"], fut))

    # -- AC-CBK4 manual SQL cross-validation ---------------------
    sql_rows = ftconn.execute(
        "SELECT kind, COUNT(*) FROM trial_calls"
        " GROUP BY kind ORDER BY kind").fetchall()
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
    wsql_kinds = ftconn.execute(
        "SELECT kind, COUNT(*) FROM trial_calls WHERE"
        " substr(called_utc, 1, 7) = ?"
        " GROUP BY kind ORDER BY kind",
        (m2,)).fetchall()
    ok4 = (ok4
           and wsql == e_m2["total"]
           and {str(r[0]): int(r[1]) for r in wsql_kinds} ==
           e_m2["calls_by_kind"])
    record("AC-CBK4", ok4,
           "per-kind counts == manual SQL GROUP BY; total %s =="
           " COUNT(*) == sum(cells); key order == SQL ORDER BY"
           " ascending %s; windowed total == manual SQL %s;"
           " windowed kind map == windowed SQL"
           % (env["total"], sql_order, wsql))

    # -- AC-CBK5 free-domain non-hiding law -----------------------
    keys_now = list(by.keys())
    ok5 = (GHOST_KIND in by
           and by[GHOST_KIND] == 1
           and keys_now.index(GHOST_KIND) == 1
           and keys_now.index("backtest") == 0
           and keys_now.index("visualize") == 2
           and (by["backtest"] + by["visualize"]) == want_total - 1
           and env["total"] == want_total
           and GHOST_KIND in e_m2["calls_by_kind"]
           and e_m2["calls_by_kind"][GHOST_KIND] == 1
           and GHOST_KIND not in e_m1["calls_by_kind"])
    record("AC-CBK5", ok5,
           "out-of-domain kind %r surfaced in full read (cell"
           " %s, ascending slot %d of %s) and counted toward"
           " total %s (tally-domain kinds sum %s); surfaced in"
           " its month window; absent from months without it -"
           " the face never hides observed data"
           % (GHOST_KIND, by[GHOST_KIND],
              keys_now.index(GHOST_KIND) + 1, keys_now,
              env["total"],
              by["backtest"] + by["visualize"]))

    # -- AC-CBK6 pure-read law ------------------------------------
    src = inspect.getsource(T.FreeTrialFace.calls_by_kind)
    banned = ("INSERT INTO", "REPLACE INTO",
              "UPDATE ", "DELETE FROM")
    ok6 = not any(b in src for b in banned)
    ok6 = ok6 and (_counts() == counts_before)
    a1_ = json.dumps(ft.calls_by_kind(), sort_keys=True)
    a2_ = json.dumps(ft.calls_by_kind(), sort_keys=True)
    b1_ = json.dumps(ft.calls_by_kind())
    b2_ = json.dumps(ft.calls_by_kind())
    ok6 = ok6 and (a1_ == a2_) and (b1_ == b2_)
    wa = json.dumps(ft.calls_by_kind(m2), sort_keys=True)
    wb = json.dumps(ft.calls_by_kind(m2), sort_keys=True)
    ok6 = ok6 and (wa == wb)
    record("AC-CBK6", ok6,
           "method source free of data-changing statements;"
           " four-table counts unchanged %s; double-call dumps"
           " byte-identical (sorted and insertion order);"
           " windowed double-call identical" % (counts_before,))

    # -- AC-CBK7 live zero-cache derivation ----------------------
    mid_counts = _counts()
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a3", "eng-a3")
    after = ft.calls_by_kind()
    ok7 = (after["calls_by_kind"]["backtest"] ==
           by["backtest"] + 1
           and after["total"] == env["total"] + 1
           and after["calls_by_kind"][GHOST_KIND] == 1
           and after["calls_by_kind"]["visualize"] == 3)
    w_after = ft.calls_by_kind(cur_m)
    ok7 = (ok7
           and w_after["calls_by_kind"]["backtest"] == 3
           and w_after["total"] == live_cur + 1)
    ok7 = ok7 and (ft.calls_by_kind(m1)["calls_by_kind"] ==
                   {"backtest": 1, "visualize": 1})
    ok7 = ok7 and (_counts() != mid_counts)
    record("AC-CBK7", ok7,
           "new live call: backtest cell %s -> %s; total %s ->"
           " %s; ghost and visualize cells unchanged; windowed"
           " read follows (cur window backtest -> %s); history"
           " month kind profile unchanged"
           % (by["backtest"],
              after["calls_by_kind"]["backtest"],
              env["total"], after["total"],
              w_after["calls_by_kind"]["backtest"]))

    # -- AC-CBK8 hygiene and registration ------------------------
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
           and "ledger-freetrial-callkind" in reg_text
           and "test_freetrial_callkind.py" in reg_text)
    ok8 = ok8 and (len(RESULTS) + 1 == EXPECTED)
    record("AC-CBK8", ok8,
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
