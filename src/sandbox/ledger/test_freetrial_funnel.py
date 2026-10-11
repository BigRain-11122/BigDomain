"""Acceptance suite for the free-trial conversion-funnel
board (BigDomain R1788; canon = the explore-queue "free-trial
conversion funnel" row: plan-level grant/conversion/rate
aggregates as a pure derived read; seed = freetrial.py R1768).
Asserts the pre-registered criteria AC-CF1..AC-CF7 from the
R1788 explore-queue row (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

The fixture is the real product stack injected by reference
(no copy): MeteredFace over the real Ledger, DevKeyFace over
that, FreeTrialFace over that. The funnel board is a pure
derived read over immutable rows; the suite proves the four
own tables and the token domain stayed untouched.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_freetrial_funnel.py
"""

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
import freetrial as T                   # noqa: E402 (R1768/R1788 face)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")

ROW_KEYS = {"plan_id", "plan_key", "title", "ai_label",
            "granted", "converted", "active_trials",
            "conversion_rate"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _table(conn, sql, args=()):
    return conn.execute(sql, args).fetchall()


def main():
    tmp = tempfile.mkdtemp(prefix="freetrial-funnel-")
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
    tx0 = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]

    # -- AC-CF1 contract, dense board, empty world, ordering ------
    empty = ft.conversion_funnel_board()
    ok1_empty = (empty["conversion_funnel_board"] == []
                 and empty["disclaimer"] == DISCLAIMER)
    # in-register developers (the funnel itself needs no caller
    # identity, but the world below does).
    dk.issue_key("usr:alice", "alice-key", 100,
                 ("backtest", "visualize"), False)
    dk.issue_key("usr:carol", "carol-key", 100, ("backtest",), True)
    # register plans in REVERSE key order to prove the board
    # walks plan_key ascending (zero insertion-order keys).
    pg = ft.register_trial_plan("gamma-ungranted",
                                "Gamma Registered No Grants",
                                5, False)
    pb = ft.register_trial_plan("beta-pro", "Beta Pro Trial",
                                2, True)
    pa = ft.register_trial_plan("alpha-starter",
                               "Alpha Starter Tier", 3, False)
    # funnel world:
    #   alpha: alice grant + 1 call; carol grant + convert
    #   beta : alice grant + cap calls + convert (full funnel)
    #   gamma: registered, zero grants
    ft.grant_trial("usr:alice", pa["plan_id"])
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a1", "eng-a1")
    ft.grant_trial("usr:carol", pa["plan_id"])
    ft.convert_upgrade("usr:carol", pa["plan_id"], "paid")
    ft.grant_trial("usr:alice", pb["plan_id"])
    ft.trial_call("usr:alice", pb["plan_id"], "backtest",
                  "b1", "eng-b1")
    ft.trial_call("usr:alice", pb["plan_id"], "visualize",
                  "b2", "eng-b2")
    ft.convert_upgrade("usr:alice", pb["plan_id"], "paid-pro")

    board = ft.conversion_funnel_board()
    rows = board["conversion_funnel_board"]
    ok1 = (ok1_empty
           and set(board.keys()) ==
           {"conversion_funnel_board", "disclaimer"}
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and len(rows) == 3
           and [r["plan_key"] for r in rows] ==
           ["alpha-starter", "beta-pro", "gamma-ungranted"])
    record("AC-CF1", ok1,
           "empty world [] honest (%s); envelope keys exact;"
           " row keys exact x%d; dense 3-row board;"
           " plan_key ascending despite reverse registration"
           " (gamma, beta, alpha) = %s"
           % (ok1_empty, len(rows),
              [r["plan_key"] for r in rows]))

    # -- AC-CF2 aggregation cross-validation ----------------------
    g_manual = {r[0]: r[1] for r in _table(
        ftconn, "SELECT plan_id, COUNT(*) FROM trial_grants"
        " GROUP BY plan_id")}
    c_manual = {r[0]: r[1] for r in _table(
        ftconn, "SELECT plan_id, COUNT(*) FROM"
        " trial_conversions GROUP BY plan_id")}
    ok2 = True
    trace2 = []
    for r in rows:
        pid = r["plan_id"]
        gm = g_manual.get(pid, 0)
        cm = c_manual.get(pid, 0)
        rate_m = (round(cm / gm, 4) if gm > 0 else 0.0)
        hit = (r["granted"] == gm and r["converted"] == cm
               and r["conversion_rate"] == rate_m)
        ok2 = ok2 and hit
        trace2.append("%s g=%d/%d c=%d/%d rate=%s/%s%s"
                      % (r["plan_key"], r["granted"], gm,
                         r["converted"], cm, r["conversion_rate"],
                         rate_m, "" if hit else " MISS"))
    record("AC-CF2", ok2,
           "every cell == manual SQL GROUP BY + rate"
           " arithmetic: %s" % "; ".join(trace2))

    # -- AC-CF3 derived semantics ---------------------------------
    by_key = {r["plan_key"]: r for r in rows}
    ok3 = (all(r["active_trials"] ==
               r["granted"] - r["converted"] for r in rows)
           and all(r["active_trials"] >= 0 for r in rows)
           and by_key["beta-pro"]["active_trials"] == 0
           and by_key["gamma-ungranted"]["granted"] == 0
           and by_key["gamma-ungranted"]["converted"] == 0
           and by_key["gamma-ungranted"]
           ["conversion_rate"] == 0.0
           and by_key["alpha-starter"]["active_trials"] == 1)
    record("AC-CF3", ok3,
           "active==granted-converted >=0 all rows; full-"
           "conversion plan (beta) active=0; zero-grant plan"
           " (gamma) 0/0 rate=0.0 funnel-top empty honest;"
           " partial plan (alpha) active=1")

    # -- AC-CF4 determinism + liveness -----------------------------
    b1 = json.dumps(ft.conversion_funnel_board(),
                    sort_keys=True)
    b2 = json.dumps(ft.conversion_funnel_board(),
                    sort_keys=True)
    ok4_det = b1 == b2
    # liveness: a fresh grant and conversion move the board on
    # re-read (zero cached counters).
    dk.issue_key("usr:dave", "dave-key", 100, ("backtest",),
                 False)
    ft.grant_trial("usr:dave", pg["plan_id"])
    after_grant = ft.conversion_funnel_board()[
        "conversion_funnel_board"]
    rg = [r for r in after_grant
          if r["plan_key"] == "gamma-ungranted"][0]
    ok4_g = (rg["granted"] == 1 and rg["converted"] == 0
             and rg["active_trials"] == 1
             and rg["conversion_rate"] == 0.0)
    ft.convert_upgrade("usr:dave", pg["plan_id"], "paid")
    after_conv = ft.conversion_funnel_board()[
        "conversion_funnel_board"]
    rc = [r for r in after_conv
          if r["plan_key"] == "gamma-ungranted"][0]
    ok4_c = (rc["granted"] == 1 and rc["converted"] == 1
             and rc["active_trials"] == 0
             and rc["conversion_rate"] == 1.0)
    record("AC-CF4", ok4_det and ok4_g and ok4_c,
           "double-call json.dumps byte-identical=%s; grant"
           " liveness 0->1 (rate 0.0 zero-conversion guard)=%s;"
           " conversion liveness converted 0->1 rate=1.0"
           " active=0=%s" % (ok4_det, ok4_g, ok4_c))

    # -- AC-CF5 pure-read law --------------------------------------
    counts0 = tuple(
        ftconn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
        for t in ("trial_plans", "trial_grants",
                  "trial_calls", "trial_conversions"))
    for _ in range(3):
        ft.conversion_funnel_board()
    ft.plan_view(pa["plan_id"])
    counts1 = tuple(
        ftconn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
        for t in ("trial_plans", "trial_grants",
                  "trial_calls", "trial_conversions"))
    method_src = inspect.getsource(
        T.FreeTrialFace.conversion_funnel_board)
    ok5 = (counts0 == counts1
           and "INSERT" not in method_src
           and "UPDATE" not in method_src
           and "DELETE" not in method_src
           and conn.execute(
               "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
           == tx0)
    record("AC-CF5", ok5,
           "four-table counts flat %s; method source carries"
           " zero data-changing statements (inspect); ledger_tx"
           " flat at %d (zero token movement structural)"
           % (counts0, tx0))

    # -- AC-CF6 AIGC label + resident disclaimer -------------------
    decl = {"alpha-starter": 0, "beta-pro": 1,
            "gamma-ungranted": 0}
    ok6 = (all(r["ai_label"] ==
               decl[r["plan_key"]]
               for r in ft.conversion_funnel_board()[
                   "conversion_funnel_board"])
           and ft.conversion_funnel_board()["disclaimer"]
           == DISCLAIMER)
    record("AC-CF6", ok6,
           "every row ai_label == registry declaration (0/1"
           " both states exercised); resident disclaimer"
           " rides the envelope")

    # -- AC-CF7 hygiene + wiring -----------------------------------
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
           and 'ledger-freetrial-funnel' in runner_src
           and len(RESULTS) + 1 == EXPECTED)
    record("AC-CF7", ok7,
           "module pure ASCII (%d non-ascii); true import lines"
           " carry zero network libs (%d); zero mutation surface"
           " for own tables; zero dice; config.json byte-stable;"
           " reconcile_all SUITES row 'ledger-freetrial-funnel'"
           " registered; criteria drift self-check %d/%d"
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
