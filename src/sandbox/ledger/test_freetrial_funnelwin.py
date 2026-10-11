"""Acceptance suite for the free-trial conversion-funnel
board window parameterization (BigDomain R1793 tech-queue
row; seed = freetrial.py conversion_funnel_board R1788).
Asserts the pre-registered criteria AC-CFW1..AC-CFW7 from
the R1793 tech.md claim line (criteria were registered
before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL.

Family law = the R1730/R1732/R1735/R1784 window-parameteri
zation line: default None keeps the full-window behavior
byte-stable; an explicit YYYY-MM month window filters
granted by granted_utc and converted by converted_utc
(record-time columns); active_trials in a windowed read is
the end-of-window snapshot (grants month<=W minus
conversions month<=W, structurally non-negative because the
conversion gate forces month(grant) <= month(conversion));
the in-window net flow is deliberately NOT surfaced under
the active_trials field name; the rate stays the
window-filtered ratio under the zero-grant guard; a
malformed window fails closed before any read.

History rows are injected straight into the trial tables by
this fixture (test-side direct writes, the R1730 family
precedent, noted here): the product gates are bypassed on
purpose so two synthetic past months can be pinned
deterministically. Injected rows respect the temporal order
the product gate enforces (a conversion row only exists
with its grant month at or before it).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_funnelwin.py
"""

import datetime
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

ROW_KEYS = {"plan_id", "plan_key", "title", "ai_label",
            "granted", "converted", "active_trials",
            "conversion_rate"}

BAD_FORMS = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
             "202610", "abcd", "", 2026, True, 2.5,
             "2026-10\n", "2026-10 ", "2026-10\r"]


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

    tmp = tempfile.mkdtemp(prefix="freetrial-funnelwin-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)

    import sqlite3
    conn = sqlite3.connect(db_path)
    ftconn = sqlite3.connect(ft.db_path)

    def _counts():
        return tuple(
            ftconn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("trial_plans", "trial_grants",
                      "trial_calls", "trial_conversions"))

    def _manual(pid, w):
        g = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants WHERE plan_id = ?"
            " AND substr(granted_utc, 1, 7) = ?",
            (pid, w)).fetchone()[0]
        c = ftconn.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " plan_id = ? AND substr(converted_utc, 1, 7) = ?",
            (pid, w)).fetchone()[0]
        return int(g), int(c)

    def _manual_active(pid, w):
        gc = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants WHERE plan_id = ?"
            " AND substr(granted_utc, 1, 7) <= ?",
            (pid, w)).fetchone()[0]
        cc = ftconn.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " plan_id = ? AND substr(converted_utc, 1, 7) <= ?",
            (pid, w)).fetchone()[0]
        return int(gc) - int(cc)

    # -- real-API world (all rows stamped in the current month) --
    dk.issue_key("usr:alice", "alice-key", 100,
                 ("backtest", "visualize"), False)
    pa = ft.register_trial_plan("alpha-starter",
                                "Alpha Starter Tier", 3, False)
    ft.grant_trial("usr:alice", pa["plan_id"])
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a1", "eng-a1")
    pz = ft.register_trial_plan("zulu-zero",
                                "Zulu Registered No Grants",
                                5, True)

    # -- AC-CFW1 contract, default zero drift, additive window --
    full1 = ft.conversion_funnel_board()
    full2 = ft.conversion_funnel_board()
    ok1_keys = (set(full1.keys()) ==
                {"conversion_funnel_board", "disclaimer"}
                and full1["disclaimer"] == DISCLAIMER)
    ok1_det = (json.dumps(full1, sort_keys=True)
               == json.dumps(full2, sort_keys=True))
    rows_full = full1["conversion_funnel_board"]
    ok1_rows = (len(rows_full) == 2
                and all(set(r.keys()) == ROW_KEYS
                       for r in rows_full)
                and [r["plan_key"] for r in rows_full] ==
                ["alpha-starter", "zulu-zero"])
    ok1_manual = True
    for r in rows_full:
        g = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants WHERE plan_id = ?",
            (r["plan_id"],)).fetchone()[0]
        c = ftconn.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " plan_id = ?", (r["plan_id"],)).fetchone()[0]
        ok1_manual = ok1_manual and (
            r["granted"] == int(g) and r["converted"] == int(c)
            and r["active_trials"] == int(g) - int(c))
    win_read = ft.conversion_funnel_board(cur_m)
    ok1_add = (set(win_read.keys()) ==
               {"conversion_funnel_board", "window", "disclaimer"}
               and win_read["window"] == cur_m)
    # current-month window equals the full board for this world
    # (every row so far lives in the current month).
    ok1_cur = (win_read["conversion_funnel_board"]
               == rows_full)
    record("AC-CFW1", ok1_keys and ok1_det and ok1_rows
           and ok1_manual and ok1_add and ok1_cur,
           "default envelope keys exact=%s; double-call"
           " byte-identical=%s; rows manual-SQL equal=%s;"
           " explicit window adds key window=%s additive;"
           " cur-month window == full board for the"
           " all-current-month world=%s"
           % (ok1_keys, ok1_det, ok1_manual, ok1_add, ok1_cur))

    # -- AC-CFW2 malformed window fail-closed ----------------------
    before = _counts()
    rejects = 0
    for bad in BAD_FORMS:
        try:
            ft.conversion_funnel_board(bad)
        except T.TrialError as exc:
            if exc.code == T.E_FT_BAD_ARGS:
                rejects += 1
    after = _counts()
    ok2 = (rejects == len(BAD_FORMS) and before == after)
    record("AC-CFW2", ok2,
           "%d/%d malformed forms rejected E_FT_BAD_ARGS"
           " (11 base + 3 trailing R1748 forms); default"
           " sentinel is None only (empty string rejected);"
           " four-table counts flat %s -> %s"
           % (rejects, len(BAD_FORMS), before, after))

    # -- history injection (test-side direct writes, noted) -------
    px = ft.register_trial_plan("xmonth-cross",
                                "Cross Month Conversion", 4, False)
    pi = ft.register_trial_plan("inmonth-full",
                                "In Month Full Funnel", 4, True)
    ftconn.execute(
        "INSERT INTO trial_grants (plan_id, dev_account,"
        " granted_utc) VALUES (?,?,?)",
        (px["plan_id"], "usr:fx", _stamp(m1, 5)))
    ftconn.execute(
        "INSERT INTO trial_conversions (plan_id, dev_account,"
        " tier_key, converted_utc) VALUES (?,?,?,?)",
        (px["plan_id"], "usr:fx", "paid-x", _stamp(m2, 7)))
    ftconn.execute(
        "INSERT INTO trial_grants (plan_id, dev_account,"
        " granted_utc) VALUES (?,?,?)",
        (pi["plan_id"], "usr:fi", _stamp(m2, 9)))
    ftconn.execute(
        "INSERT INTO trial_conversions (plan_id, dev_account,"
        " tier_key, converted_utc) VALUES (?,?,?,?)",
        (pi["plan_id"], "usr:fi", "paid-i", _stamp(m2, 21)))
    ftconn.commit()

    # -- AC-CFW3 record-time window filter semantics ---------------
    r_m2 = {r["plan_key"]: r for r in
            ft.conversion_funnel_board(m2)
            ["conversion_funnel_board"]}
    ok3_dense = len(r_m2) == 4      # registry-driven axis, dense
    ok3_hist = True
    trace3 = []
    for key, pid in (("xmonth-cross", px["plan_id"]),
                     ("inmonth-full", pi["plan_id"]),
                     ("alpha-starter", pa["plan_id"]),
                     ("zulu-zero", pz["plan_id"])):
        g, c = _manual(pid, m2)
        ok3_hist = ok3_hist and (
            r_m2[key]["granted"] == g
            and r_m2[key]["converted"] == c)
        trace3.append("%s g=%d c=%d" % (key, g, c))
    ok3_no_leak = (r_m2["alpha-starter"]["granted"] == 0
                   and r_m2["alpha-starter"]["converted"] == 0)
    r_cur = {r["plan_key"]: r for r in
             ft.conversion_funnel_board(cur_m)
             ["conversion_funnel_board"]}
    ok3_cur_leak = (r_cur["xmonth-cross"]["granted"] == 0
                    and r_cur["xmonth-cross"]["converted"] == 0
                    and r_cur["alpha-starter"]["granted"] == 1)
    r_m1 = {r["plan_key"]: r for r in
            ft.conversion_funnel_board(m1)
            ["conversion_funnel_board"]}
    ok3_m1 = (r_m1["xmonth-cross"]["granted"] == 1
              and r_m1["xmonth-cross"]["converted"] == 0
              and r_m1["inmonth-full"]["granted"] == 0)
    r_fut = ft.conversion_funnel_board(fut)
    ok3_fut = (all(r["granted"] == 0
                   and r["converted"] == 0
                   for r in r_fut["conversion_funnel_board"])
               and len(r_fut["conversion_funnel_board"]) == 4
               and r_fut["window"] == fut)
    full_now = ft.conversion_funnel_board()
    ok3_full_contains = (
        {r["plan_key"] for r in
         full_now["conversion_funnel_board"]}
        == {"alpha-starter", "zulu-zero",
            "xmonth-cross", "inmonth-full"})
    record("AC-CFW3", ok3_dense and ok3_hist and ok3_no_leak
           and ok3_cur_leak and ok3_m1 and ok3_fut
           and ok3_full_contains,
           "windowed cells == manual SQL per record-time"
           " column [%s]; history window carries zero"
           " current-month rows=%s; current-month window"
           " carries zero history rows=%s; older month read"
           " exact=%s; future window honest zeros dense=%s;"
           " default full-window still shows every plan=%s"
           % ("; ".join(trace3), ok3_no_leak, ok3_cur_leak,
              ok3_m1, ok3_fut, ok3_full_contains))

    # -- AC-CFW4 active_trials end-of-window snapshot --------------
    ok4_cross = (r_m2["xmonth-cross"]["granted"] == 0
                 and r_m2["xmonth-cross"]["converted"] == 1
                 and r_m2["xmonth-cross"]["active_trials"] == 0)
    ok4_m1_snap = (r_m1["xmonth-cross"]["active_trials"] == 1)
    ok4_manual = all(
        r["active_trials"] == _manual_active(r["plan_id"], m2)
        for r in ft.conversion_funnel_board(m2)
        ["conversion_funnel_board"])
    ok4_nonneg = all(
        r["active_trials"] >= 0
        for w in (m1, m2, cur_m, fut)
        for r in ft.conversion_funnel_board(w)
        ["conversion_funnel_board"])
    record("AC-CFW4", ok4_cross and ok4_m1_snap
           and ok4_manual and ok4_nonneg,
           "cross-month case (grant %s + conversion %s):"
           " window %s granted_w=0 converted_w=1"
           " active=0 (net-flow -1 never surfaced under the"
           " field name)=%s; older-month snapshot active=1=%s;"
           " every windowed active == manual cumulative"
           " SQL=%s; active >= 0 across all windows=%s"
           % (m1, m2, m2, ok4_cross, ok4_m1_snap,
              ok4_manual, ok4_nonneg))

    # -- AC-CFW5 conversion_rate window path ------------------------
    ok5_cross = (r_m2["xmonth-cross"]["conversion_rate"] == 0.0)
    ok5_full = (r_m2["inmonth-full"]["conversion_rate"] == 1.0)
    ok5_manual = all(
        r["conversion_rate"] == (round(r["converted"]
                                        / r["granted"], 4)
                                  if r["granted"] > 0 else 0.0)
        for r in ft.conversion_funnel_board(m2)
        ["conversion_funnel_board"])
    record("AC-CFW5", ok5_cross and ok5_full and ok5_manual,
           "zero-grant guard in window (granted_w=0,"
           " converted_w=1 -> rate 0.0)=%s; in-month full"
           " funnel rate 1.0=%s; every windowed rate =="
           " windowed ratio arithmetic=%s"
           % (ok5_cross, ok5_full, ok5_manual))

    # -- AC-CFW6 pure-read law + liveness + determinism -------------
    counts0 = _counts()
    for w in (None, m1, m2, cur_m, fut):
        ft.conversion_funnel_board(w)
    counts1 = _counts()
    method_src = inspect.getsource(
        T.FreeTrialFace.conversion_funnel_board)
    ok6_pure = (counts0 == counts1
                and "INSERT" not in method_src
                and "UPDATE" not in method_src
                and "DELETE" not in method_src)
    w1 = json.dumps(ft.conversion_funnel_board(m2),
                    sort_keys=True)
    w2 = json.dumps(ft.conversion_funnel_board(m2),
                    sort_keys=True)
    ok6_det = w1 == w2
    # liveness: a fresh current-month grant moves the
    # current-month window on re-read; the history window
    # stays unchanged (zero cached state).
    dk.issue_key("usr:carol", "carol-key", 100, ("backtest",),
                 True)
    ft.grant_trial("usr:carol", pz["plan_id"])
    cur_after = {r["plan_key"]: r for r in
                 ft.conversion_funnel_board(cur_m)
                 ["conversion_funnel_board"]}
    hist_after = {r["plan_key"]: r for r in
                  ft.conversion_funnel_board(m2)
                  ["conversion_funnel_board"]}
    ok6_live = (cur_after["zulu-zero"]["granted"] == 1
                and hist_after["zulu-zero"]["granted"] == 0)
    record("AC-CFW6", ok6_pure and ok6_det and ok6_live,
           "four-table counts flat %s; method source carries"
           " zero data-changing statements (inspect)=%s;"
           " windowed double-call byte-identical=%s; fresh"
           " grant moves cur-month window 0->1 while history"
           " window stays 0=%s"
           % (counts0 == counts1, ok6_pure, ok6_det, ok6_live))

    # -- AC-CFW7 hygiene + wiring -----------------------------------
    with open(os.path.join(BASE, "freetrial.py"),
              encoding="utf-8") as handle:
        src = handle.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [ln for ln in src.splitlines()
                    if (ln.startswith("import ")
                        or ln.startswith("from "))]
    net_imports = [ln for ln in import_lines
                   if any(w in ln for w in
                          ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(
            os.path.dirname(BASE), "reconcile_all.py"),
            encoding="utf-8") as handle:
        runner_src = handle.read()
    ok7 = (non_ascii == 0 and not net_imports
           and "UPDATE trial_" not in src
           and "random" not in src
           and cfg_after == cfg_bytes
           and 'ledger-freetrial-funnelwin' in runner_src
           and len(RESULTS) + 1 == EXPECTED)
    record("AC-CFW7", ok7,
           "module pure ASCII (%d non-ascii); true import lines"
           " carry zero network libs (%d); zero mutation"
           " surface for own tables; zero dice; config.json"
           " byte-stable; reconcile_all SUITES row"
           " 'ledger-freetrial-funnelwin' registered; criteria"
           " drift self-check %d/%d"
           % (non_ascii, len(net_imports), len(RESULTS),
              EXPECTED))

    conn.close()
    ftconn.close()
    ft.close()
    dk.close()
    metered.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
