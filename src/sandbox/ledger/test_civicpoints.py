"""Acceptance suite for the citizen civic-behavior points face
(BigDomain R1752; canon = explore-queue civic-points line: civic
points inside the counts-vs-tokens isolation law, public-welfare
compliance judged first, points-redeem-entitlements on the
props-domain adjacency verdict). Asserts the pre-registered
criteria AC-CV1..CV7 from the R1752 explore-queue row (criteria
were registered before this code existed; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_civicpoints.py
"""

import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import civicpoints as CV              # noqa: E402 (R1752 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: civic points are a"
              " public-welfare engagement feature, not investment"
              " advice, not currency, and not redeemable for money")

BANNED_VERBS = ("trade", "sell", "buy", "auction", "swap", "gift")
BACKFLOW_APIS = ("cash_out", "convert_points", "to_tokens",
                "transfer_points", "transfer")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_cv_error(fn, *codes):
    try:
        fn()
    except CV.CivicError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="civicpoints-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    led_path = os.path.join(tmp, "ledger.db")
    cv_path = os.path.join(tmp, "civic.db")

    led = L.Ledger(led_path, cfg)
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    conn = sqlite3.connect(led_path)
    cvconn = sqlite3.connect(cv_path)

    # -- AC-CV1 behavior registry face ---------------------------------------
    r1 = cv.register_behavior("city-poll", "Community Poll", 5, 2, False)
    ok_dup, code_dup = expect_cv_error(
        lambda: cv.register_behavior("city-poll", "Again", 5, 2, False),
        CV.E_CV_DUP_BEHAVIOR)
    bad1 = []
    raised1 = True
    for label, fn in (
            ("empty id", lambda: cv.register_behavior(
                "  ", "t", 5, 2, False)),
            ("empty title", lambda: cv.register_behavior(
                "k1", "  ", 5, 2, False)),
            ("bool points", lambda: cv.register_behavior(
                "k2", "t", True, 2, False)),
            ("zero points", lambda: cv.register_behavior(
                "k3", "t", 0, 2, False)),
            ("bool daily limit", lambda: cv.register_behavior(
                "k4", "t", 5, True, False)),
            ("zero daily limit", lambda: cv.register_behavior(
                "k5", "t", 5, 0, False)),
            ("non-bool ai flag", lambda: cv.register_behavior(
                "k6", "t", 5, 2, "yes"))):
        ok_one, got = expect_cv_error(fn, CV.E_CV_BAD_ARGS)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    row1 = cvconn.execute(
        "SELECT title, points_per_event, daily_limit, ai_label FROM"
        " civic_behaviors WHERE behavior_id = 'city-poll'").fetchone()
    n_reg1 = _count(cvconn, "civic_behaviors")
    ok1 = (r1["behavior_id"] == "city-poll"
           and r1["points_per_event"] == 5
           and r1["daily_limit"] == 2
           and r1["ai_label"] == 0
           and r1["disclaimer"] == DISCLAIMER
           and ok_dup and code_dup == CV.E_CV_DUP_BEHAVIOR
           and raised1 and n_reg1 == 1
           and row1 == ("Community Poll", 5, 2, 0))
    record("AC-CV1", ok1, "register writes one registry row %s; dup"
          " refused %s; all %d bad args rejected (%s); ai_label"
          " persists on row %s"
          % (row1, code_dup, len(bad1), "; ".join(bad1),
             int(row1[3])))

    # -- AC-CV2 earn face: idempotency + daily cap + strict day --------------
    e1 = cv.earn_civic("usr:alice", "city-poll", "2026-10-10", "evt-1")
    ok_replay, code_replay = expect_cv_error(
        lambda: cv.earn_civic("usr:alice", "city-poll", "2026-10-10",
                              "evt-1"),
        CV.E_CV_DUP_EARN)
    n_after_replay = _count(cvconn, "civic_earns")
    e2 = cv.earn_civic("usr:alice", "city-poll", "2026-10-10", "evt-2")
    ok_cap, code_cap = expect_cv_error(
        lambda: cv.earn_civic("usr:alice", "city-poll", "2026-10-10",
                              "evt-3"),
        CV.E_CV_DAY_LIMIT)
    n_after_cap = _count(cvconn, "civic_earns")
    e3 = cv.earn_civic("usr:alice", "city-poll", "2026-10-11", "evt-3")
    cv.register_behavior("litter-pick", "Litter Pick", 3, 1, True)
    e4 = cv.earn_civic("usr:alice", "litter-pick", "2026-10-10", "lp-1")
    pts_rows = cvconn.execute(
        "SELECT behavior_id, points FROM civic_earns ORDER BY"
        " earn_id").fetchall()
    bad2 = []
    raised2 = True
    for label, fn in (
            ("slash day", lambda: cv.earn_civic(
                "usr:alice", "city-poll", "2026/10/10", "d1")),
            ("compact day", lambda: cv.earn_civic(
                "usr:alice", "city-poll", "20261010", "d2")),
            ("bad month", lambda: cv.earn_civic(
                "usr:alice", "city-poll", "2026-13-01", "d3")),
            ("impossible date", lambda: cv.earn_civic(
                "usr:alice", "city-poll", "2026-02-31", "d4")),
            ("unit day", lambda: cv.earn_civic(
                "usr:alice", "city-poll", "2026-10-1", "d5")),
            ("int day", lambda: cv.earn_civic(
                "usr:alice", "city-poll", 20261010, "d6")),
            ("empty ref", lambda: cv.earn_civic(
                "usr:alice", "city-poll", "2026-10-10", "  ")),
            ("non-usr account", lambda: cv.earn_civic(
                "res:abc", "city-poll", "2026-10-10", "d7")),
            ("unknown behavior", lambda: cv.earn_civic(
                "usr:alice", "ghost-behavior", "2026-10-10", "d8"))):
        codes = ((CV.E_CV_UNKNOWN_BEHAVIOR,)
                 if label == "unknown behavior"
                 else (CV.E_CV_BAD_ARGS,))
        ok_one, got = expect_cv_error(fn, *codes)
        if ok_one:
            bad2.append("%s=%s" % (label, got))
        else:
            bad2.append("%s NOT-RAISED(%s)" % (label, got))
            raised2 = False
    n_final2 = _count(cvconn, "civic_earns")
    ok2 = (e1["points_earned"] == 5 and e1["balance"] == 5
           and ok_replay and code_replay == CV.E_CV_DUP_EARN
           and n_after_replay == 1
           and e2["balance"] == 10
           and ok_cap and code_cap == CV.E_CV_DAY_LIMIT
           and n_after_cap == 2
           and e3["balance"] == 15
           and e4["points_earned"] == 3 and e4["balance"] == 18
           and e4["ai_label"] == 1
           and pts_rows == [("city-poll", 5), ("city-poll", 5),
                            ("city-poll", 5), ("litter-pick", 3)]
           and raised2 and n_final2 == 4)
    record("AC-CV2", ok2, "earn rows carry the registered immutable"
          " point copy %s; replay refused %s (rows %d==%d); daily"
          " cap 2 enforced on day 1 (%s, rows %d) and reset on day"
          " 2 (balance %d); per-behavior value 3 lands (%d); all %d"
          " fault paths rejected (%s); rows final %d"
          % (pts_rows, code_replay, n_after_replay, 1, code_cap,
             n_after_cap, e3["balance"], e4["points_earned"],
             len(bad2), "; ".join(bad2), n_final2))

    # -- AC-CV3 reward registry face -------------------------------------------
    r3a = cv.register_reward("civic-badge", "Civic Badge", 8,
                             "cosmetic", 1, True)
    r3b = cv.register_reward("ride-vouchers", "Ride Vouchers", 4,
                             "count", 2, False)
    ok_dup_r, code_dup_r = expect_cv_error(
        lambda: cv.register_reward("civic-badge", "Again", 8,
                                   "cosmetic", 1, True),
        CV.E_CV_DUP_REWARD)
    bad3 = []
    raised3 = True
    for label, fn in (
            ("empty id", lambda: cv.register_reward(
                "  ", "t", 8, "cosmetic", 1, False)),
            ("empty title", lambda: cv.register_reward(
                "r1", "  ", 8, "cosmetic", 1, False)),
            ("bool cost", lambda: cv.register_reward(
                "r2", "t", True, "cosmetic", 1, False)),
            ("zero cost", lambda: cv.register_reward(
                "r3", "t", 0, "cosmetic", 1, False)),
            ("bad kind", lambda: cv.register_reward(
                "r4", "t", 8, "prop", 1, False)),
            ("cosmetic multi grant", lambda: cv.register_reward(
                "r5", "t", 8, "cosmetic", 2, False)),
            ("count zero grant", lambda: cv.register_reward(
                "r6", "t", 8, "count", 0, False)),
            ("non-bool ai flag", lambda: cv.register_reward(
                "r7", "t", 8, "cosmetic", 1, "yes"))):
        ok_one, got = expect_cv_error(fn, CV.E_CV_BAD_ARGS)
        if ok_one:
            bad3.append("%s=%s" % (label, got))
        else:
            bad3.append("%s NOT-RAISED(%s)" % (label, got))
            raised3 = False
    n_reg3 = _count(cvconn, "civic_rewards")
    ok3 = (r3a["reward_id"] == "civic-badge" and r3a["ai_label"] == 1
           and r3b["kind"] == "count" and r3b["grant_count"] == 2
           and r3a["disclaimer"] == DISCLAIMER
           and ok_dup_r and code_dup_r == CV.E_CV_DUP_REWARD
           and raised3 and n_reg3 == 2)
    record("AC-CV3", ok3, "reward registry: cosmetic %s ai=%d and"
          " count %s x%d registered; dup refused %s; all %d bad args"
          " rejected (%s); rows %d"
          % (r3a["reward_id"], r3a["ai_label"], r3b["reward_id"],
             r3b["grant_count"], code_dup_r, len(bad3),
             "; ".join(bad3), n_reg3))

    # -- AC-CV4 redemption face: fail-closed gate order ----------------------
    n_red0 = _count(cvconn, "civic_redeems")
    n_gr0 = _count(cvconn, "civic_grants")
    ok_unk_r, code_unk_r = expect_cv_error(
        lambda: cv.redeem_reward("usr:alice", "ghost-reward"),
        CV.E_CV_UNKNOWN_REWARD)
    cv.earn_civic("usr:bob", "city-poll", "2026-10-10", "b-1")
    n_bob_red0 = cvconn.execute(
        "SELECT COUNT(*) FROM civic_redeems WHERE"
        " account_id = 'usr:bob'").fetchone()[0]
    n_bob_gr0 = cvconn.execute(
        "SELECT COUNT(*) FROM civic_grants WHERE"
        " account_id = 'usr:bob'").fetchone()[0]
    ok_insuf, code_insuf = expect_cv_error(
        lambda: cv.redeem_reward("usr:bob", "civic-badge"),
        CV.E_CV_INSUFFICIENT)
    n_bob_red1 = cvconn.execute(
        "SELECT COUNT(*) FROM civic_redeems WHERE"
        " account_id = 'usr:bob'").fetchone()[0]
    n_bob_gr1 = cvconn.execute(
        "SELECT COUNT(*) FROM civic_grants WHERE"
        " account_id = 'usr:bob'").fetchone()[0]
    d1 = cv.redeem_reward("usr:alice", "civic-badge")
    ok_dup_g, code_dup_g = expect_cv_error(
        lambda: cv.redeem_reward("usr:alice", "civic-badge"),
        CV.E_CV_DUP_GRANT)
    d2a = cv.redeem_reward("usr:alice", "ride-vouchers")
    d2b = cv.redeem_reward("usr:alice", "ride-vouchers")
    alice_grants = cvconn.execute(
        "SELECT reward_id, kind, count_credits FROM civic_grants"
        " WHERE account_id = 'usr:alice' ORDER BY"
        " grant_id").fetchall()
    n_red1 = _count(cvconn, "civic_redeems")
    n_gr1 = _count(cvconn, "civic_grants")
    ok4 = (ok_unk_r and code_unk_r == CV.E_CV_UNKNOWN_REWARD
           and ok_insuf and code_insuf == CV.E_CV_INSUFFICIENT
           and n_bob_red1 == n_bob_red0 and n_bob_gr1 == n_bob_gr0
           and d1["balance"] == 10 and d1["granted"] == 1
           and ok_dup_g and code_dup_g == CV.E_CV_DUP_GRANT
           and d2a["balance"] == 6 and d2b["balance"] == 2
           and d2a["granted"] == 2 and d2b["granted"] == 2
           and alice_grants == [("civic-badge", "cosmetic", 1),
                                ("ride-vouchers", "count", 2),
                                ("ride-vouchers", "count", 2)]
           and n_red1 - n_red0 == 3 and n_gr1 - n_gr0 == 3)
    record("AC-CV4", ok4, "gate order verified: unknown reward %s;"
          " insufficient balance %s with zero bob rows"
          " (redeems %d==%d, grants %d==%d); cosmetic redeemed once"
          " (balance %d, granted %d), re-redeem refused %s; count"
          " kind stacks (%d then %d, credits %s); exactly 3 redeem"
          " + 3 grant rows written (%d/%d -> %d/%d)"
          % (code_unk_r, code_insuf, n_bob_red1, n_bob_red0,
             n_bob_gr1, n_bob_gr0, d1["balance"], d1["granted"],
             code_dup_g, d2a["balance"], d2b["balance"],
             [g[2] for g in alice_grants], n_red0, n_gr0, n_red1,
             n_gr1))

    # -- AC-CV5 counts-vs-tokens isolation law --------------------------------
    init_params = list(inspect.signature(
        CV.CivicPointsFace.__init__).parameters)
    n_tx0 = _count(conn, "ledger_tx")
    bal_alice0 = conn.execute(
        "SELECT balance FROM ledger_accounts WHERE"
        " account_id = 'usr:alice'").fetchone()
    cv.register_behavior("park-clean", "Park Clean", 2, 1, False)
    cv.earn_civic("usr:bob", "park-clean", "2026-10-10", "pc-1")
    cv.register_reward("seed-pack", "Seed Pack", 2, "count", 1, False)
    cv.redeem_reward("usr:bob", "seed-pack")
    cv.points_view("usr:alice")
    cv.behavior_board()
    cv.reward_board()
    n_tx1 = _count(conn, "ledger_tx")
    bal_alice1 = conn.execute(
        "SELECT balance FROM ledger_accounts WHERE"
        " account_id = 'usr:alice'").fetchone()
    with open(os.path.join(BASE, "civicpoints.py"), "rb") as h:
        cv_src = h.read().decode("ascii")
    no_ledger_import = ("import ledger" not in cv_src
                        and "Ledger(" not in cv_src)
    banned_hits = [w for w in BANNED_VERBS if w in cv_src]
    backflow_apis = [m for m in BACKFLOW_APIS if hasattr(cv, m)]
    money_entrance = ("token_price" in cv_src or "money" in cv_src)
    ok5 = ("ledger" not in init_params
           and n_tx0 == n_tx1
           and bal_alice0 == bal_alice1
           and no_ledger_import and not banned_hits
           and not backflow_apis and not money_entrance)
    record("AC-CV5", ok5, "constructor takes NO ledger reference"
          " (params %s); full op cycle leaves ledger_tx constant"
          " (%d==%d) and ledger balances untouched (%s); no ledger"
          " import in source; zero circulation verbs (%s); zero"
          " backflow APIs (%s); no money/token entrance (%s)"
          % (init_params, n_tx0, n_tx1, bal_alice0 == bal_alice1,
             banned_hits, backflow_apis, money_entrance))

    # -- AC-CV6 AIGC labeling + resident disclaimer ---------------------------
    ok_nd, code_nd = expect_cv_error(
        lambda: CV.CivicPointsFace("  ", os.path.join(
            tmp, "civic-nodisclaimer.db")),
        CV.E_CV_NO_DISCLAIMER)
    ok_ndb, code_ndb = expect_cv_error(
        lambda: CV.CivicPointsFace(DISCLAIMER, "  "),
        CV.E_CV_BAD_ARGS)
    label_rejected = []
    for table, values in (
            ("civic_behaviors", ('x', 't', 1, 1, 2, 't')),
            ("civic_rewards", ('x', 't', 1, 'count', 1, 2, 't'))):
        try:
            cvconn.execute(
                "INSERT INTO %s VALUES (%s)"
                % (table, ",".join("?" * len(values))), values)
            cvconn.commit()
        except sqlite3.IntegrityError:
            cvconn.rollback()
            label_rejected.append(True)
        else:
            label_rejected.append(False)
    view6 = cv.points_view("usr:alice")
    board6b = cv.behavior_board()
    board6r = cv.reward_board()
    envelopes = (r1, e4, r3a, d1, view6, board6b, board6r)
    all_disclaimer = all(e.get("disclaimer") == DISCLAIMER
                         for e in envelopes)
    ai_rows = cvconn.execute(
        "SELECT ai_label FROM civic_behaviors WHERE"
        " behavior_id = 'litter-pick'").fetchone()
    ok6 = (ok_nd and code_nd == CV.E_CV_NO_DISCLAIMER
           and ok_ndb and code_ndb == CV.E_CV_BAD_ARGS
           and all(label_rejected)
           and view6["disclaimer"] == DISCLAIMER
           and board6r["rewards"][0]["ai_label"] == 1
           and int(ai_rows[0]) == 1
           and all_disclaimer)
    record("AC-CV6", ok6, "empty disclaimer refused %s; empty"
          " db path refused %s; ai_label persists (litter-pick row"
          " =%d, badge row shown %d); direct SQL ai_label=2 refused"
          " by CHECK on both registry tables (%s); all %d envelopes"
          " carry the resident disclaimer"
          % (code_nd, code_ndb, int(ai_rows[0]),
             board6r["rewards"][0]["ai_label"], label_rejected,
             len(envelopes)))

    # -- AC-CV7 read faces + hard laws ----------------------------------------
    view7 = cv.points_view("usr:alice")
    eq7 = (view7["earned_total"] - view7["redeemed_total"]
           == view7["balance"])
    counts0 = (_count(cvconn, "civic_behaviors"),
               _count(cvconn, "civic_earns"),
               _count(cvconn, "civic_rewards"),
               _count(cvconn, "civic_redeems"),
               _count(cvconn, "civic_grants"))
    cv.points_view("usr:alice")
    cv.behavior_board()
    cv.reward_board()
    counts1 = (_count(cvconn, "civic_behaviors"),
               _count(cvconn, "civic_earns"),
               _count(cvconn, "civic_rewards"),
               _count(cvconn, "civic_redeems"),
               _count(cvconn, "civic_grants"))
    non_ascii = sum(1 for ch in cv_src if ord(ch) > 127)
    net_imports = [ln for ln in cv_src.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    update_hits = [w for w in ("UPDATE civic_behaviors",
                               "UPDATE civic_earns",
                               "UPDATE civic_rewards",
                               "UPDATE civic_redeems",
                               "UPDATE civic_grants")
                   if w in cv_src]
    ok7 = (eq7 and counts0 == counts1 and non_ascii == 0
           and not net_imports and not update_hits
           and "random" not in cv_src
           and view7["balance"] == 2
           and len(view7["grants"]) == 3)
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = ok7 and cfg_after == cfg_bytes
    record("AC-CV7", ok7, "points_view derived balance holds"
          " (earned %d - redeemed %d == balance %d); grants listed"
          " %d; all reads pure (row counts %s unchanged); module"
          " pure ASCII (%d non-ascii); zero network imports (%d);"
          " zero UPDATE surface (%s); zero RNG; shipped"
          " config.json byte-stable"
          % (view7["earned_total"], view7["redeemed_total"],
             view7["balance"], len(view7["grants"]), counts0,
             non_ascii, len(net_imports), update_hits))

    conn.close()
    cvconn.close()
    cv.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
