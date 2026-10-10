"""Acceptance suite for the developer free-trial tier face
(BigDomain R1768; canon = explore-queue "developer free-trial
quota" line: the zero-fee trial window + the upgrade-conversion
gate; seeds = the apidev quota ring read as a variant and the
member tier-grant structure). Asserts the pre-registered
criteria AC-FT1..AC-FT7 from the R1768 explore-queue row
(criteria were registered before this code existed; honesty
law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

The developer-key face is the real product injected by
reference (no copy): MeteredFace over the real Ledger, then
DevKeyFace over that - the registry gate is exercised against
the live dev_board public read face. The trial face itself
holds no ledger reference at all (zero-fee structural
self-evidence); the suite proves the token domain stayed
untouched by watching ledger_tx stay flat.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_freetrial.py
"""

import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700 registry face)
import freetrial as T                   # noqa: E402 (R1768 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except T.TrialError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def run_battery(cases):
    """Every case must raise its expected code; returns
    (all-raised, trace list)."""
    ok_all = True
    trace = []
    for label, fn, code in cases:
        hit, got = expect_error(fn, code)
        if hit:
            trace.append("%s->%s" % (label, got))
        else:
            trace.append("%s MISS(%s)" % (label, got))
            ok_all = False
    return ok_all, trace


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _tx_count(conn):
    return conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="freetrial-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)

    # in-register developers: alice + carol hold keys; bob holds
    # none (off-register). No account funding anywhere: the free
    # tier must work with zero token traffic.
    dk.issue_key("usr:alice", "alice-key", 100,
                 ("backtest", "visualize"), False)
    dk.issue_key("usr:carol", "carol-key", 100, ("backtest",), True)

    conn = sqlite3.connect(db_path)
    ftconn = sqlite3.connect(ft.db_path)
    tx0 = _tx_count(conn)

    # -- AC-FT1 plan registry face ------------------------------------------
    p1 = ft.register_trial_plan("free-starter", "Free Starter Tier",
                                3, False)
    n_plans_0 = _count(ftconn, "trial_plans")
    ok_dup, got_dup = expect_error(
        lambda: ft.register_trial_plan("free-starter", "Again", 3,
                                        False),
        T.E_FT_DUP_PLAN)
    n_plans_1 = _count(ftconn, "trial_plans")
    p2 = ft.register_trial_plan("free-pro", "Free Pro Trial",
                                2, True)
    bad1, trace1 = run_battery((
        ("empty key", lambda: ft.register_trial_plan(
            " ", "t", 3, False), T.E_FT_BAD_PLAN),
        ("none key", lambda: ft.register_trial_plan(
            None, "t", 3, False), T.E_FT_BAD_PLAN),
        ("empty title", lambda: ft.register_trial_plan(
            "k", "  ", 3, False), T.E_FT_BAD_PLAN),
        ("bool cap", lambda: ft.register_trial_plan(
            "k", "t", True, False), T.E_FT_BAD_PLAN),
        ("zero cap", lambda: ft.register_trial_plan(
            "k", "t", 0, False), T.E_FT_BAD_PLAN),
        ("neg cap", lambda: ft.register_trial_plan(
            "k", "t", -2, False), T.E_FT_BAD_PLAN),
        ("str cap", lambda: ft.register_trial_plan(
            "k", "t", "3", False), T.E_FT_BAD_PLAN),
        ("non-bool ai flag", lambda: ft.register_trial_plan(
            "k", "t", 3, "yes"), T.E_FT_BAD_PLAN),
        ("unknown plan read", lambda: ft.plan_view(999),
         T.E_FT_UNKNOWN_PLAN),
        ("bool plan id read", lambda: ft.plan_view(True),
         T.E_FT_BAD_ARGS),
    ))
    n_plans_2 = _count(ftconn, "trial_plans")
    ok1 = (isinstance(p1["plan_id"], int)
           and p1["ai_label"] == 0 and p2["ai_label"] == 1
           and ok_dup and got_dup == T.E_FT_DUP_PLAN
           and n_plans_0 == 1 and n_plans_1 == 1
           and bad1 and n_plans_2 == 2
           and p1["disclaimer"] == DISCLAIMER)
    record("AC-FT1", ok1,
           "plan registry: two rows (ai_label %d/%d persisted),"
           " replay rejected %s, %d bad-arg cases all rejected"
           " (%s), zero rows on rejects (%d->%d->%d), envelope"
           " carries disclaimer"
           % (p1["ai_label"], p2["ai_label"], got_dup, len(trace1),
              "; ".join(trace1), n_plans_0, n_plans_1, n_plans_2))

    p1_id, p2_id = p1["plan_id"], p2["plan_id"]

    # -- AC-FT2 registry gate + grant idempotency -----------------------------
    g1 = ft.grant_trial("usr:alice", p1_id)
    n_gr_0 = _count(ftconn, "trial_grants")
    ok_dup_g, got_dup_g = expect_error(
        lambda: ft.grant_trial("usr:alice", p1_id), T.E_FT_DUP_GRANT)
    n_gr_1 = _count(ftconn, "trial_grants")
    ok_notdev, got_notdev = expect_error(
        lambda: ft.grant_trial("usr:bob", p1_id), T.E_FT_NOT_DEV)
    n_gr_2 = _count(ftconn, "trial_grants")
    bad2, trace2 = run_battery((
        ("pool account grant", lambda: ft.grant_trial(
            "pool:reserve", p1_id), T.E_FT_BAD_ACCOUNT),
        ("unknown plan grant", lambda: ft.grant_trial(
            "usr:alice", 999), T.E_FT_UNKNOWN_PLAN),
        ("bool plan grant", lambda: ft.grant_trial(
            "usr:alice", True), T.E_FT_BAD_ARGS),
    ))
    g2 = ft.grant_trial("usr:alice", p2_id)
    n_gr_3 = _count(ftconn, "trial_grants")
    ok2 = (n_gr_0 == 1 and ok_dup_g and n_gr_1 == 1
           and ok_notdev and got_notdev == T.E_FT_NOT_DEV
           and n_gr_2 == 1 and bad2 and n_gr_3 == 2
           and g1["trial_cap"] == 3 and g2["plan_key"] == "free-pro"
           and g1["disclaimer"] == DISCLAIMER
           and _tx_count(conn) == tx0)
    record("AC-FT2", ok2,
           "registry gate + grant idempotency: in-register dev"
           " granted on both plans (%d rows), replay rejected %s,"
           " off-register bob rejected %s before any row (dev_board"
           " referenced), %d bad-arg cases rejected (%s), ledger_tx"
           " flat at %d (zero fee, zero token)"
           % (n_gr_3, got_dup_g, got_notdev, len(trace2),
              "; ".join(trace2), _tx_count(conn)))

    # -- AC-FT3 zero-fee trial window + quota ring variant --------------------
    ok_notrial, got_notrial = expect_error(
        lambda: ft.trial_call("usr:carol", p1_id, "backtest",
                              "ref-c1", "engine-alpha"),
        T.E_FT_NO_TRIAL)
    n_call_0 = _count(ftconn, "trial_calls")
    c1 = ft.trial_call("usr:alice", p1_id, "backtest",
                       "ref-a1", "engine-alpha")
    c2 = ft.trial_call("usr:alice", p1_id, "visualize",
                       "ref-a2", "engine-alpha")
    c3 = ft.trial_call("usr:alice", p1_id, "backtest",
                       "ref-a3", "engine-beta")
    n_call_1 = _count(ftconn, "trial_calls")
    ok_dup_c, got_dup_c = expect_error(
        lambda: ft.trial_call("usr:alice", p1_id, "backtest",
                              "ref-a1", "engine-alpha"),
        T.E_FT_DUP)
    n_call_2 = _count(ftconn, "trial_calls")
    quota_hit, quota_detail = False, ""
    try:
        ft.trial_call("usr:alice", p1_id, "backtest",
                      "ref-a4", "engine-alpha")
    except T.TrialError as exc:
        quota_hit = exc.code == T.E_FT_QUOTA
        quota_detail = str(exc.detail)
    n_call_3 = _count(ftconn, "trial_calls")
    ok_notdev_c, _ = expect_error(
        lambda: ft.trial_call("usr:bob", p1_id, "backtest",
                              "ref-b1", "engine-alpha"),
        T.E_FT_NOT_DEV)
    bad3, trace3 = run_battery((
        ("pool account call", lambda: ft.trial_call(
            "pool:reserve", p1_id, "backtest", "r", "e"),
         T.E_FT_BAD_ACCOUNT),
        ("empty kind", lambda: ft.trial_call(
            "usr:carol", p1_id, "  ", "r", "e"), T.E_FT_BAD_ARGS),
        ("empty call ref", lambda: ft.trial_call(
            "usr:carol", p1_id, "backtest", " ", "e"),
         T.E_FT_BAD_ARGS),
        ("empty engine ref", lambda: ft.trial_call(
            "usr:carol", p1_id, "backtest", "r", ""),
         T.E_FT_BAD_ARGS),
        ("unknown plan call", lambda: ft.trial_call(
            "usr:alice", 999, "backtest", "r", "e"),
         T.E_FT_UNKNOWN_PLAN),
        ("bool plan call", lambda: ft.trial_call(
            "usr:alice", True, "backtest", "r", "e"),
         T.E_FT_BAD_ARGS),
    ))
    calls_sql = ftconn.execute(
        "SELECT sql FROM sqlite_master WHERE name ="
        " 'trial_calls'").fetchone()[0]
    ok3 = (ok_notrial and got_notrial == T.E_FT_NO_TRIAL
           and n_call_0 == 0
           and c1["calls_used"] == 1 and c3["calls_used"] == 3
           and c3["engine_ref"] == "engine-beta"
           and n_call_1 == 3 and ok_dup_c and n_call_2 == 3
           and quota_hit and "upgrade" in quota_detail
           and n_call_3 == 3 and ok_notdev_c and bad3
           and _tx_count(conn) == tx0
           and "window" not in calls_sql)
    record("AC-FT3", ok3,
           "zero-fee trial window + quota ring variant: no-grant"
           " carol refused %s fail-closed; 3 in-cap calls pass"
           " (calls_used 1..3, engine_ref stored as-is); replay"
           " rejected %s; call cap+1 refused %s with upgrade hint"
           " (%s); off-register refused; %d bad-arg cases"
           " rejected (%s); rows 0->3->3->3; trial_calls schema"
           " carries no window column (lifetime window never"
           " resets - the apidev monthly-ring variant); ledger_tx"
           " flat at %d"
           % (got_notrial, got_dup_c, T.E_FT_QUOTA, quota_detail,
              len(trace3), "; ".join(trace3), _tx_count(conn)))

    # -- AC-FT4 upgrade-conversion gate ---------------------------------------
    ok_notrial_cv, got_notrial_cv = expect_error(
        lambda: ft.convert_upgrade("usr:carol", p1_id,
                                   "paid-tier-pro"),
        T.E_FT_NO_TRIAL)
    ok_notdev_cv, _ = expect_error(
        lambda: ft.convert_upgrade("usr:bob", p1_id, "paid-tier"),
        T.E_FT_NOT_DEV)
    bad4, trace4 = run_battery((
        ("empty tier key", lambda: ft.convert_upgrade(
            "usr:alice", p1_id, "  "), T.E_FT_BAD_ARGS),
        ("pool account convert", lambda: ft.convert_upgrade(
            "pool:reserve", p1_id, "paid"), T.E_FT_BAD_ACCOUNT),
        ("unknown plan convert", lambda: ft.convert_upgrade(
            "usr:alice", 999, "paid"), T.E_FT_UNKNOWN_PLAN),
    ))
    conv1 = ft.convert_upgrade("usr:alice", p1_id, "paid-tier-pro")
    n_cv_0 = _count(ftconn, "trial_conversions")
    ok_dup_cv, got_dup_cv = expect_error(
        lambda: ft.convert_upgrade("usr:alice", p1_id,
                                   "paid-tier-pro"),
        T.E_FT_DUP_CONVERT)
    n_cv_1 = _count(ftconn, "trial_conversions")
    ok_closed, got_closed = expect_error(
        lambda: ft.trial_call("usr:alice", p1_id, "backtest",
                              "ref-a5", "engine-alpha"),
        T.E_FT_CONVERTED)
    n_call_4 = _count(ftconn, "trial_calls")
    c_p2 = ft.trial_call("usr:alice", p2_id, "backtest",
                         "ref-p2-1", "engine-alpha")
    n_call_5 = _count(ftconn, "trial_calls")
    ok4 = (ok_notrial_cv and got_notrial_cv == T.E_FT_NO_TRIAL
           and ok_notdev_cv and bad4
           and conv1["tier_key"] == "paid-tier-pro"
           and n_cv_0 == 1 and ok_dup_cv and n_cv_1 == 1
           and ok_closed and got_closed == T.E_FT_CONVERTED
           and n_call_4 == 3
           and c_p2["calls_used"] == 1 and n_call_5 == 4
           and _tx_count(conn) == tx0)
    record("AC-FT4", ok4,
           "upgrade-conversion gate: no-trial convert refused %s,"
           " off-register refused, %d bad-arg cases rejected"
           " (%s); conversion row written (tier %s, one per"
           " (dev,plan) - member tier-grant structure reference);"
           " replay refused %s; converted dev's free call closed"
           " %s fail-closed (rows %d); plan independence proven"
           " (p2 call passes, rows %d->%d); zero token movement"
           " (ledger_tx flat at %d)"
           % (got_notrial_cv, len(trace4), "; ".join(trace4),
              conv1["tier_key"], got_dup_cv, got_closed,
              n_call_4, n_call_4, n_call_5, _tx_count(conn)))

    # -- AC-FT5 AIGC label + standing disclaimer ------------------------------
    ok_nodisc, got_nodisc = expect_error(
        lambda: T.FreeTrialFace(dk, " "), T.E_FT_NO_DISCLAIMER)
    ok_nodev, got_nodev = expect_error(
        lambda: T.FreeTrialFace(None, DISCLAIMER), T.E_FT_BAD_ARGS)
    check_probe = False
    try:
        ftconn.execute(
            "INSERT INTO trial_plans (plan_key, title, trial_cap,"
            " ai_label, registered_utc) VALUES ('x','x',1,2,'x')")
        ftconn.commit()
    except sqlite3.IntegrityError:
        check_probe = True
        ftconn.rollback()
    envelopes = [p1, p2, g1, g2, c1, c3, conv1,
                 ft.trial_view("usr:alice", p1_id),
                 ft.plan_view(p1_id), ft.plan_board(),
                 ft.trials_board(p1_id),
                 ft.conversions_board(p1_id)]
    discl_ok = all(e.get("disclaimer") == DISCLAIMER
                   for e in envelopes)
    view_p1, view_p2 = ft.plan_view(p1_id), ft.plan_view(p2_id)
    ok5 = (ok_nodisc and got_nodisc == T.E_FT_NO_DISCLAIMER
           and ok_nodev and check_probe and discl_ok
           and view_p1["ai_label"] == 0
           and view_p2["ai_label"] == 1)
    record("AC-FT5", ok5,
           "AIGC + disclaimer: empty disclaimer refuses"
           " construction %s, missing devkeys face refuses %s;"
           " direct ai_label=2 insert rejected by DB CHECK;"
           " %d envelopes all carry the standing disclaimer;"
           " registry labels persist (%d/%d on views)"
           % (got_nodisc, got_nodev, len(envelopes),
              view_p1["ai_label"], view_p2["ai_label"]))

    # -- AC-FT6 read faces are pure reads ---------------------------------------
    counts6_0 = (_count(ftconn, "trial_plans"),
                 _count(ftconn, "trial_grants"),
                 _count(ftconn, "trial_calls"),
                 _count(ftconn, "trial_conversions"))
    tv_alice = ft.trial_view("usr:alice", p1_id)
    tv_carol = ft.trial_view("usr:carol", p1_id)
    tv_alice_p2 = ft.trial_view("usr:alice", p2_id)
    pv1, pv2 = ft.plan_view(p1_id), ft.plan_view(p2_id)
    board = ft.plan_board()
    tb1, cb1 = ft.trials_board(p1_id), ft.conversions_board(p1_id)
    counts6_1 = (_count(ftconn, "trial_plans"),
                 _count(ftconn, "trial_grants"),
                 _count(ftconn, "trial_calls"),
                 _count(ftconn, "trial_conversions"))
    bad6, trace6 = run_battery((
        ("unknown plan trial_view", lambda: ft.trial_view(
            "usr:alice", 999), T.E_FT_UNKNOWN_PLAN),
        ("unknown plan trials_board", lambda: ft.trials_board(999),
         T.E_FT_UNKNOWN_PLAN),
        ("unknown plan conversions_board",
         lambda: ft.conversions_board(999),
         T.E_FT_UNKNOWN_PLAN),
    ))
    write_words = ("INSERT INTO", "UPDATE ", "DELETE FROM")
    inspect_ok = True
    for name in ("trial_view", "plan_view", "plan_board",
                 "trials_board", "conversions_board"):
        body = inspect.getsource(getattr(T.FreeTrialFace, name))
        if any(w in body for w in write_words):
            inspect_ok = False
    ok6 = (tv_alice["granted"] and tv_alice["calls_used"] == 3
           and tv_alice["calls_remaining"] == 0
           and tv_alice["converted"]
           and tv_alice["tier_key"] == "paid-tier-pro"
           and not tv_carol["granted"] and not tv_carol["converted"]
           and tv_carol["calls_used"] == 0
           and tv_alice_p2["calls_used"] == 1
           and tv_alice_p2["calls_remaining"] == 1
           and not tv_alice_p2["converted"]
           and pv1["grant_count"] == 1 and pv1["call_count"] == 3
           and pv1["conversion_count"] == 1
           and pv2["grant_count"] == 1 and pv2["call_count"] == 1
           and pv2["conversion_count"] == 0
           and len(board["plans"]) == 2
           and board["plans"][0]["plan_key"] == "free-starter"
           and board["plans"][1]["ai_label"] == 1
           and len(tb1["grants"]) == 1
           and tb1["grants"][0]["dev_account"] == "usr:alice"
           and len(cb1["conversions"]) == 1
           and cb1["conversions"][0]["tier_key"] == "paid-tier-pro"
           and counts6_0 == counts6_1 and bad6 and inspect_ok)
    record("AC-FT6", ok6,
           "read faces: trial_view derives grant/calls/remaining/"
           "conversion from COUNT faces (alice p1 used %d"
           " remaining %d converted->%s; carol honest no-grant"
           " state; alice p2 used %d remaining %d); plan_view"
           " counts %s/%s; board order + labels true; audit rows"
           " alice; counts unchanged %s->%s; unknown-plan reads"
           " refused (%d cases); zero write statements in all"
           " five read methods (inspect probe)"
           % (tv_alice["calls_used"], tv_alice["calls_remaining"],
              tv_alice["tier_key"], tv_alice_p2["calls_used"],
              tv_alice_p2["calls_remaining"],
              (pv1["grant_count"], pv1["call_count"],
               pv1["conversion_count"]), (pv2["grant_count"],
                                          pv2["call_count"],
                                          pv2["conversion_count"]),
              counts6_0, counts6_1, len(trace6)))

    # -- AC-FT7 hard laws -------------------------------------------------------
    counts7_0 = (_count(ftconn, "trial_plans"),
                 _count(ftconn, "trial_grants"),
                 _count(ftconn, "trial_calls"),
                 _count(ftconn, "trial_conversions"))
    bad7, trace7 = run_battery((
        ("grant pool account", lambda: ft.grant_trial(
            "pool:reserve", p1_id), T.E_FT_BAD_ACCOUNT),
        ("call pool account", lambda: ft.trial_call(
            "pool:reserve", p1_id, "backtest", "r", "e"),
         T.E_FT_BAD_ACCOUNT),
        ("convert pool account", lambda: ft.convert_upgrade(
            "pool:reserve", p1_id, "paid"), T.E_FT_BAD_ACCOUNT),
        ("grant zero plan", lambda: ft.grant_trial(
            "usr:carol", 0), T.E_FT_BAD_ARGS),
        ("call str plan", lambda: ft.trial_call(
            "usr:carol", "1", "backtest", "r", "e"),
         T.E_FT_BAD_ARGS),
        ("convert bool plan", lambda: ft.convert_upgrade(
            "usr:carol", True, "paid"), T.E_FT_BAD_ARGS),
        ("grant unknown plan", lambda: ft.grant_trial(
            "usr:carol", 999), T.E_FT_UNKNOWN_PLAN),
        ("call unknown plan", lambda: ft.trial_call(
            "usr:carol", 999, "backtest", "r", "e"),
         T.E_FT_UNKNOWN_PLAN),
        ("convert unknown plan", lambda: ft.convert_upgrade(
            "usr:carol", 999, "paid"), T.E_FT_UNKNOWN_PLAN),
        ("grant off-register", lambda: ft.grant_trial(
            "usr:bob", p1_id), T.E_FT_NOT_DEV),
        ("call off-register", lambda: ft.trial_call(
            "usr:bob", p1_id, "backtest", "r", "e"),
         T.E_FT_NOT_DEV),
        ("convert off-register", lambda: ft.convert_upgrade(
            "usr:bob", p1_id, "paid"), T.E_FT_NOT_DEV),
        ("trial_view pool account", lambda: ft.trial_view(
            "pool:reserve", p1_id), T.E_FT_BAD_ACCOUNT),
    ))
    counts7_1 = (_count(ftconn, "trial_plans"),
                 _count(ftconn, "trial_grants"),
                 _count(ftconn, "trial_calls"),
                 _count(ftconn, "trial_conversions"))
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
    ledger_imports = [ln for ln in import_lines
                      if "ledger" in ln]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    ok7 = (bad7 and counts7_0 == counts7_1
           and _tx_count(conn) == tx0
           and non_ascii == 0 and not net_imports
           and not ledger_imports
           and "UPDATE trial_" not in src
           and "random" not in src
           and cfg_after == cfg_bytes)
    record("AC-FT7", ok7,
           "hard laws: %d bad-arg cases all rejected (%s); zero"
           " side effects (rows %s unchanged, ledger_tx flat at"
           " %d - zero fee structural); module pure ASCII (%d"
           " non-ascii); true import lines carry zero network"
           " libs and zero ledger imports (%d/%d); zero"
           " mutation surface (quota = COUNT faces); zero dice"
           " (no random in source); config.json byte-stable"
           % (len(trace7), "; ".join(trace7), counts7_0,
              _tx_count(conn), non_ascii, len(net_imports),
              len(ledger_imports)))

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
