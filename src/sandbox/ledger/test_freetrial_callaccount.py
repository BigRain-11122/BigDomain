"""Acceptance suite for the free-trial calls-by-account pure
read face (BigDomain R1837 tech-queue row; seed = the
freetrial.py calls_by_engine R1831 face). Asserts the
pre-registered criteria AC-CBA1..AC-CBA8 from the R1837
tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Family law = the R1730/R1732/R1735/R1784/R1793 window
parameterization line: default None keeps the full-window
behavior byte-stable; an explicit YYYY-MM month window
filters rows by their called_utc record-time stamp first,
then aggregates account stamps over the surviving rows (a
row-filter window, orthogonal to the calls_by_month cell
window). A malformed window fails closed before any read.

dev_account is the developer account stamp (trial_calls.
dev_account TEXT; the live call gate always stamps an
in-register "usr:"-shaped account - grant first, then
call): one injected history row carries a non-"usr:"
shaped ghost account stamp on purpose - the face must
surface it, not hide it (AC-CBA5, the R1776 AC-CHM3 law).
The history accounts themselves (usr:hist-a, usr:hist-b)
are also direct-injection stamps no live gate produced.

History rows are injected straight into the trial_calls
table by this fixture (test-side direct writes, the R1730
family precedent, noted here): the product call gate is
bypassed on purpose so two synthetic past months can be
pinned deterministically. Injected rows respect the table's
own uniqueness constraint (distinct call_ref values).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_callaccount.py
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

GHOST_ACCOUNT = "ghost-account-probe"  # non-"usr:"-shaped stamp

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

    tmp = tempfile.mkdtemp(prefix="freetrial-callaccount-")
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
    zero = ft.calls_by_account()
    ok_zero = (zero["calls_by_account"] == {}
               and zero["total"] == 0
               and set(zero.keys()) ==
               {"calls_by_account", "total", "disclaimer"}
               and zero["disclaimer"] == DISCLAIMER)

    # -- real flow: in-register devs, plans, grants, live calls ---
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
    # one row carries the non-"usr:"-shaped ghost account stamp
    # on purpose (the live gate always stamps in-register
    # usr:-shaped accounts, only direct injection can produce
    # anything else)
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
        (pb["plan_id"], GHOST_ACCOUNT, "backtest", "h6",
         "eng-x", _stamp(m2, 11)),
    ]
    for pid, who, kind, ref, eng, ts in hist_rows:
        ftconn.execute(
            "INSERT INTO trial_calls (plan_id, dev_account,"
            " kind, call_ref, engine_ref, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (pid, who, kind, ref, eng, ts))
    ftconn.commit()

    counts_before = _counts()

    # full-window expectations (ascending TEXT order):
    #   ghost-account-probe = 1 (m2 fixture)
    #   usr:alice = 2 (live)
    #   usr:bob = 1 (live)
    #   usr:hist-a = 2 (m1)
    #   usr:hist-b = 3 (m2)
    want_full = {GHOST_ACCOUNT: 1, "usr:alice": 2,
                 "usr:bob": 1, "usr:hist-a": 2,
                 "usr:hist-b": 3}
    want_total = 9

    # -- AC-CBA1 contract, ascending keys, invariants -------------
    env = ft.calls_by_account()
    by = env["calls_by_account"]
    keys_sorted = sorted(by.keys())
    ok1 = (ok_zero
           and set(env.keys()) ==
           {"calls_by_account", "total", "disclaimer"}
           and keys_sorted == [GHOST_ACCOUNT, "usr:alice",
                               "usr:bob", "usr:hist-a",
                               "usr:hist-b"]
           and list(by.keys()) == keys_sorted
           and by == want_full
           and env["total"] == want_total
           and sum(by.values()) == want_total
           and env["disclaimer"] == DISCLAIMER)
    wenv = ft.calls_by_account(cur_m)
    ok1 = (ok1
           and set(wenv.keys()) ==
           {"calls_by_account", "total", "disclaimer", "window"}
           and wenv["window"] == cur_m)
    with open(os.path.join(BASE, "config.json"), "rb") as h2:
        ok1 = ok1 and (h2.read() == cfg_bytes)
    record("AC-CBA1", ok1,
           "zero-call world honest empty (%s); envelope keys"
           " exact; account keys ascending %s; cells %s; total"
           " %s == sum == COUNT; window key additive on"
           " explicit read; config bytes stable"
           % (ok_zero, list(by.keys()), by, env["total"]))

    # -- AC-CBA2 malformed windows fail closed -------------------
    ok2 = True
    trace2 = []
    for form in BAD_FORMS:
        try:
            ft.calls_by_account(form)
            ok2 = False
            trace2.append("accepted:%r" % (form,))
        except T.TrialError as exc:
            if exc.code != T.E_FT_BAD_ARGS:
                ok2 = False
                trace2.append("wrongcode:%r" % (form,))
    ok2 = ok2 and (_counts() == counts_before)
    try:
        ft.calls_by_account(None)     # sole default sentinel
    except T.TrialError:
        ok2 = False
        trace2.append("None-rejected")
    record("AC-CBA2", ok2,
           "%d bad forms rejected E_FT_BAD_ARGS; four-table"
           " counts unchanged %s; None default accepted %s"
           % (len(BAD_FORMS), counts_before, trace2))

    # -- AC-CBA3 window filtering semantics ----------------------
    e_m1 = ft.calls_by_account(m1)
    e_m2 = ft.calls_by_account(m2)
    e_fut = ft.calls_by_account(fut)
    ok3 = (e_m1["calls_by_account"] == {"usr:hist-a": 2}
           and e_m1["total"] == 2
           and e_m2["calls_by_account"] ==
           {GHOST_ACCOUNT: 1, "usr:hist-b": 3}
           and e_m2["total"] == 4
           and e_fut["calls_by_account"] == {}
           and e_fut["total"] == 0
           and e_m1["window"] == m1)
    default_read = ft.calls_by_account()
    ok3 = (ok3
           and default_read["calls_by_account"] == want_full
           and set(e_m1["calls_by_account"].keys()) ==
           {"usr:hist-a"})
    record("AC-CBA3", ok3,
           "month %s account profile %s; month %s account"
           " profile %s; future %s honest empty; default read"
           " carries all observed accounts; zero cross-month"
           " leakage"
           % (m1, e_m1["calls_by_account"], m2,
              e_m2["calls_by_account"], fut))

    # -- AC-CBA4 manual SQL cross-validation ---------------------
    sql_rows = ftconn.execute(
        "SELECT dev_account, COUNT(*) FROM trial_calls"
        " GROUP BY dev_account"
        " ORDER BY dev_account").fetchall()
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
    wsql_acc = ftconn.execute(
        "SELECT dev_account, COUNT(*) FROM trial_calls WHERE"
        " substr(called_utc, 1, 7) = ?"
        " GROUP BY dev_account ORDER BY dev_account",
        (m2,)).fetchall()
    ok4 = (ok4
           and wsql == e_m2["total"]
           and {str(r[0]): int(r[1]) for r in wsql_acc} ==
           e_m2["calls_by_account"])
    record("AC-CBA4", ok4,
           "per-account counts == manual SQL GROUP BY; total"
           " %s == COUNT(*) == sum(cells); key order == SQL"
           " ORDER BY ascending %s; windowed total == manual"
           " SQL %s; windowed account map == windowed SQL"
           % (env["total"], sql_order, wsql))

    # -- AC-CBA5 free-domain non-hiding law -----------------------
    keys_now = list(by.keys())
    usr_sum = sum(v for k, v in by.items()
                  if k.startswith("usr:"))
    ok5 = (GHOST_ACCOUNT in by
           and by[GHOST_ACCOUNT] == 1
           and keys_now.index(GHOST_ACCOUNT) == 0
           and keys_now.index("usr:alice") == 1
           and keys_now.index("usr:bob") == 2
           and keys_now.index("usr:hist-a") == 3
           and keys_now.index("usr:hist-b") == 4
           and usr_sum == want_total - 1
           and env["total"] == want_total
           and GHOST_ACCOUNT in e_m2["calls_by_account"]
           and e_m2["calls_by_account"][GHOST_ACCOUNT] == 1
           and GHOST_ACCOUNT not in e_m1["calls_by_account"])
    record("AC-CBA5", ok5,
           "out-of-domain account %r surfaced in full read"
           " (cell %s, ascending slot %d of %s) and counted"
           " toward total %s (usr-shaped stamps sum %s);"
           " surfaced in its month window; absent from months"
           " without it - the face never hides observed data"
           % (GHOST_ACCOUNT, by[GHOST_ACCOUNT],
              keys_now.index(GHOST_ACCOUNT) + 1, keys_now,
              env["total"], usr_sum))

    # -- AC-CBA6 pure-read law ------------------------------------
    src = inspect.getsource(T.FreeTrialFace.calls_by_account)
    banned = ("INSERT INTO", "REPLACE INTO",
              "UPDATE ", "DELETE FROM")
    ok6 = not any(b in src for b in banned)
    ok6 = ok6 and (_counts() == counts_before)
    a1_ = json.dumps(ft.calls_by_account(), sort_keys=True)
    a2_ = json.dumps(ft.calls_by_account(), sort_keys=True)
    b1_ = json.dumps(ft.calls_by_account())
    b2_ = json.dumps(ft.calls_by_account())
    ok6 = ok6 and (a1_ == a2_) and (b1_ == b2_)
    wa = json.dumps(ft.calls_by_account(m2), sort_keys=True)
    wb = json.dumps(ft.calls_by_account(m2), sort_keys=True)
    ok6 = ok6 and (wa == wb)
    record("AC-CBA6", ok6,
           "method source free of data-changing statements;"
           " four-table counts unchanged %s; double-call dumps"
           " byte-identical (sorted and insertion order);"
           " windowed double-call identical" % (counts_before,))

    # -- AC-CBA7 live zero-cache derivation ----------------------
    mid_counts = _counts()
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a3", "eng-x")
    after = ft.calls_by_account()
    ok7 = (after["calls_by_account"]["usr:alice"] ==
           by["usr:alice"] + 1
           and after["total"] == env["total"] + 1
           and after["calls_by_account"][GHOST_ACCOUNT] == 1
           and after["calls_by_account"]["usr:bob"] == 1
           and after["calls_by_account"]["usr:hist-a"] == 2
           and after["calls_by_account"]["usr:hist-b"] == 3)
    w_after = ft.calls_by_account(cur_m)
    ok7 = (ok7
           and w_after["calls_by_account"]["usr:alice"] == 3
           and w_after["total"] == live_cur + 1)
    ok7 = ok7 and (ft.calls_by_account(m1)["calls_by_account"] ==
                   {"usr:hist-a": 2})
    ok7 = ok7 and (_counts() != mid_counts)
    record("AC-CBA7", ok7,
           "new live call: usr:alice cell %s -> %s; total %s ->"
           " %s; ghost/usr:bob/usr:hist-a/usr:hist-b cells"
           " unchanged; windowed read follows (cur window"
           " usr:alice -> %s); history month account profile"
           " unchanged"
           % (by["usr:alice"],
              after["calls_by_account"]["usr:alice"],
              env["total"], after["total"],
              w_after["calls_by_account"]["usr:alice"]))

    # -- AC-CBA8 hygiene and registration ------------------------
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
           and "ledger-freetrial-callaccount" in reg_text
           and "test_freetrial_callaccount.py" in reg_text)
    ok8 = ok8 and (len(RESULTS) + 1 == EXPECTED)
    record("AC-CBA8", ok8,
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
