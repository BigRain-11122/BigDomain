"""Acceptance suite for the trading-hall value-added effects face
(BigDomain R629; canon = BLUEPRINT sec-4 C3 hall value-added line,
effects residual). Asserts the pre-registered criteria AC-LE1..
AC-LE7 from the R629 backlog row (criteria were registered before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Usage: python test_effects.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L   # noqa: E402  (P-47-2b core)
import effects as F  # noqa: E402  (R629 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_f_error(fn, *codes):
    try:
        fn()
    except F.EffectsError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="effects-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    fx = F.EffectsFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-LE-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 100), ("usr:bob", "credit", 100)],
               "manual:fund-b", "suite funding bob")
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-LE1 idempotent purchase: one spend per ref, replay free --
    b0 = bal("usr:alice")
    p1 = fx.purchase("usr:alice", "dynamic_emoji", 50, "order:le1")
    b1 = bal("usr:alice")
    p2 = fx.purchase("usr:alice", "dynamic_emoji", 50, "order:le1")
    b2 = bal("usr:alice")
    ok1 = (b1 == b0 - 50 and b2 == b1 and p2["idempotent"]
           and p1["credit_id"] == p2["credit_id"] and not p1["idempotent"]
           and bool(p1["spend_tx"]) and p1["spend_tx"] == p2["spend_tx"]
           and p1["kind"] == "dynamic_emoji")
    record("AC-LE1", ok1, "fresh ref charged once (%d->%d->%d); replay of"
          " order:le1 returned the same credit #%d with spend tx %s and no"
          " second charge" % (b0, b1, b2, p2["credit_id"],
                              p1["spend_tx"][:10]))

    # -- AC-LE2 purchase provenance: all four kinds bind a real spend --
    kinds = (("limit_up_effect", "order:le2a"),
             ("flood_effect", "order:le2b"),
             ("message_pin", "order:le2c"))
    for kind, ref in kinds:
        fx.purchase("usr:alice", kind, 10, ref)
    b3 = bal("usr:alice")
    conn = sqlite3.connect(db_path)
    creds = conn.execute(
        "SELECT credit_id, kind, bound_spend_tx FROM effect_credits"
        " WHERE account_id = 'usr:alice' ORDER BY credit_id").fetchall()
    prov = []
    ok2 = (len(creds) == 4 and b3 == b0 - 50 - 30)
    for credit_id, kind, tx in creds:
        head = conn.execute(
            "SELECT type FROM ledger_tx WHERE tx_id = ?", (tx,)).fetchone()
        leg = conn.execute(
            "SELECT direction FROM ledger_entries WHERE tx_id = ?"
            " AND account_id = 'usr:alice'", (tx,)).fetchone()
        good = (head is not None and head[0] == "spend" and leg is not None
                and leg[0] == "debit")
        prov.append("%s->%s" % (kind, head[0] if head else "MISSING"))
        ok2 = ok2 and good
    conn.close()
    record("AC-LE2", ok2, "four credits, four kinds, every row bound to a"
          " real spend (type=spend, debit leg): %s; total charge 80 of 300"
          " (%d left)" % ("; ".join(prov), b3))

    # -- AC-LE3 consumption gate: no credit -> reject, zero rows -------
    b_bob = bal("usr:bob")
    ok_gate, code_gate = expect_f_error(
        lambda: fx.use("usr:bob", "limit_up_effect", "msg:b-1",
                       "use:le3"),
        F.E_EFF_NO_CREDIT)
    conn = sqlite3.connect(db_path)
    n_events = conn.execute(
        "SELECT COUNT(*) FROM effect_events").fetchone()[0]
    conn.close()
    ok3 = (ok_gate and code_gate == F.E_EFF_NO_CREDIT
           and n_events == 0 and bal("usr:bob") == b_bob)
    record("AC-LE3", ok3, "bob with zero credits: effect use rejected %s"
          " leaving zero effect rows and zero charge (%d==%d)" %
          (code_gate, b_bob, bal("usr:bob")))

    # -- AC-LE4 kind law: registry gates both ways, no cross-kind serve -
    b_alice4 = bal("usr:alice")
    ok_p_bad, code_p_bad = expect_f_error(
        lambda: fx.purchase("usr:alice", "magic_spark", 10, "order:le4x"),
        F.E_EFF_BAD_KIND)
    ok_u_bad, code_u_bad = expect_f_error(
        lambda: fx.use("usr:alice", "magic_spark", "msg:m-0",
                       "use:le4y"),
        F.E_EFF_BAD_KIND)
    pb = fx.purchase("usr:bob", "flood_effect", 10, "order:le4b")
    b_bob4 = bal("usr:bob")
    ok_cross, code_cross = expect_f_error(
        lambda: fx.use("usr:bob", "limit_up_effect", "msg:b-2",
                       "use:le4c"),
        F.E_EFF_NO_CREDIT)
    bob_credits = fx.credits_view("usr:bob")["credits"]
    flood = [c for c in bob_credits if c["kind"] == "flood_effect"]
    conn = sqlite3.connect(db_path)
    bob_events = conn.execute(
        "SELECT COUNT(*) FROM effect_events WHERE account_id ="
        " 'usr:bob'").fetchone()[0]
    conn.close()
    ok4 = (ok_p_bad and ok_u_bad and ok_cross
           and code_p_bad == F.E_EFF_BAD_KIND
           and code_u_bad == F.E_EFF_BAD_KIND
           and code_cross == F.E_EFF_NO_CREDIT
           and bal("usr:alice") == b_alice4
           and b_bob4 == b_bob - 10 and len(flood) == 1
           and not flood[0]["consumed"] and bob_events == 0
           and pb["kind"] == "flood_effect")
    record("AC-LE4", ok4, "unknown kind rejected on purchase and use (%s,"
          " %s) with zero charge; bob's flood credit cannot serve a"
          " limit_up use (%s) - credit stayed unconsumed, zero effect"
          " rows, alice balance untouched" %
          (code_p_bad, code_u_bad, code_cross))

    # -- AC-LE5 use idempotency: replay returns the same effect row -----
    u1 = fx.use("usr:alice", "dynamic_emoji", "msg:m-1", "use:le5")
    u2 = fx.use("usr:alice", "dynamic_emoji", "msg:m-1", "use:le5")
    dyn = [c for c in fx.credits_view("usr:alice")["credits"]
           if c["kind"] == "dynamic_emoji"]
    consumed_dyn = [c for c in dyn if c["consumed"]]
    ok_dup, code_dup = expect_f_error(
        lambda: fx.use("usr:bob", "dynamic_emoji", "msg:m-1", "use:le5"),
        F.E_EFF_DUP_USE)
    ok5 = (not u1["idempotent"] and u2["idempotent"]
           and u1["effect_id"] == u2["effect_id"]
           and u1["used_credit"] == p1["credit_id"]
           and len(consumed_dyn) == 1
           and consumed_dyn[0]["credit_id"] == p1["credit_id"]
           and ok_dup and code_dup == F.E_EFF_DUP_USE)
    record("AC-LE5", ok5, "first use consumed credit #%d for effect #%d;"
          " replay of use:le5 returned the same effect #%d idempotent"
          " with no second consumption (%d of %d dynamic credits"
          " consumed); cross-account replay of the same use_ref rejected"
          " %s with zero new rows" %
          (u1["used_credit"], u1["effect_id"], u2["effect_id"],
           len(consumed_dyn), len(dyn), code_dup))

    # -- AC-LE6 one credit = one effect, single UPDATE surface ----------
    ok_again, code_again = expect_f_error(
        lambda: fx.use("usr:alice", "dynamic_emoji", "msg:m-2",
                       "use:le6"),
        F.E_EFF_NO_CREDIT)
    eff_rows = fx.effects_view("usr:alice")["effects"]
    conn = sqlite3.connect(db_path)
    ev_immutable = conn.execute(
        "SELECT used_credit FROM effect_events WHERE effect_id = ?",
        (u1["effect_id"],)).fetchone()
    conn.close()
    with open(os.path.join(BASE, "effects.py"), encoding="utf-8") as h:
        src = h.read()
    single_update = ("UPDATE effect_credits SET consumed_utc" in src
                     and "UPDATE effect_events" not in src
                     and "UPDATE effect_credits SET account_id" not in src
                     and "UPDATE effect_credits SET kind" not in src)
    ok6 = (ok_again and code_again == F.E_EFF_NO_CREDIT
           and len(eff_rows) == 1
           and ev_immutable is not None
           and int(ev_immutable[0]) == p1["credit_id"]
           and consumed_dyn[0]["used_effect"] == u1["effect_id"]
           and single_update)
    record("AC-LE6", ok6, "second dynamic use rejected %s after the credit"
          " was consumed (one credit = one effect); consumed credit #%d"
          " binds effect #%d and the effect row binds the credit back"
          " (provenance both directions); consumption marking is the"
          " module's single UPDATE surface, effect rows immutable, no"
          " ownership-column rewrite" %
          (code_again, p1["credit_id"], u1["effect_id"]))

    # -- AC-LE7 bad args: zero side effects + pure-ASCII source scan -----
    b7 = bal("usr:alice")
    credits7 = len(fx.credits_view("usr:alice")["credits"])
    effects7 = len(fx.effects_view("usr:alice")["effects"])
    bad = []
    raised_all = True
    for label, fn, code in (
            ("bad account use", lambda: fx.use("svc:x", "flood_effect",
                                              "msg:z", "use:le7a"),
             F.E_EFF_BAD_ACCOUNT),
            ("empty message ref", lambda: fx.use("usr:alice",
                                                "flood_effect", "  ",
                                                "use:le7b"),
             F.E_EFF_BAD_MESSAGE),
            ("empty use ref", lambda: fx.use("usr:alice", "flood_effect",
                                            "msg:z", "  "),
             F.E_EFF_BAD_REF),
            ("zero price", lambda: fx.purchase("usr:alice",
                                               "message_pin", 0,
                                               "order:le7c"),
             F.E_EFF_BAD_AMOUNT),
            ("empty purchase ref", lambda: fx.purchase("usr:alice",
                                                       "message_pin", 10,
                                                       "  "),
             F.E_EFF_BAD_REF),
            ("bad account purchase", lambda: fx.purchase(
                "svc:x", "message_pin", 10, "order:le7d"),
             F.E_EFF_BAD_ACCOUNT)):
        ok_one, got = expect_f_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    ok7 = (b7 == bal("usr:alice")
           and credits7 == len(fx.credits_view("usr:alice")["credits"])
           and effects7 == len(fx.effects_view("usr:alice")["effects"])
           and raised_all and non_ascii == 0)
    record("AC-LE7", ok7, "all bad args rejected (%s); zero side effects"
          " (balance %d==%d, credits %d, effects %d); module pure ASCII"
          " (%d non-ascii)" % ("; ".join(bad), b7, bal("usr:alice"),
                               credits7, effects7, non_ascii))

    fx.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
