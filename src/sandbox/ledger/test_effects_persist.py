"""Cross-restart persistence window for the trading-hall
value-added effects face (BigDomain R1947; the effects seat of the
R1886 persist family - the R1942-seeded row, criteria
AC-EFP1..AC-EFP7 pre-registered in the R1947 tech.md claim row
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Two-piece restart world on the real product path (the face rides
the same ledger.db with its own connection): anchor world (three
funded accounts, ada buys one credit of each of the four kinds
binding four real spend txs, bob buys a cross-kind probe round,
ada fires two effects, carol stays a zero-row face; purchase-ref
replay absorbed idempotently in-world) -> close both pieces
(fx.close + led.close) -> reopen the same db/config ->
byte-identical read battery replay (credits/effects views for all
three accounts + four balances) -> nine restart-surviving gate
probes -> post-restart real-path continuation where ada's
pre-restart flood and pin credits keep serving new uses and carol
runs a fresh purchase->use chain binding a fresh spend tx ->
frozen rows + idempotent replay gates -> pure-read law -> third
instance stability. The read faces carry persisted clock strings
(purchased/consumed/used utc) and time-derived hex spend tx ids,
so the evidence digests mask both families (banded projection,
R1902 law) while the in-run battery keeps full dumps.

Usage: python test_effects_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L   # noqa: E402  (P-47-2b core)
import effects as F  # noqa: E402  (R629 hall value-added face)

RESULTS = []

_UTC_RE = re.compile(
    r'"([a-z_]*utc[a-z_]*)": "(?:\d{4}-\d{2}[^"]*)"')
_TX_RE = re.compile(r'"spend_tx": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except F.EffectsError as exc:
        return exc.code in codes, exc.code
    except Exception as exc:                     # noqa: BLE001
        return False, type(exc).__name__ + ":" + str(exc)
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    text = _TX_RE.sub('"spend_tx": "<tx>"', text)
    return _UTC_RE.sub(lambda m: '"%s": "<ts>"' % m.group(1), text)


def evidence_digest(bat):
    parts = []
    for key in sorted(bat):
        val = bat[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    out = {
        "credits": int(conn.execute(
            "SELECT COUNT(*) FROM effect_credits").fetchone()[0]),
        "effects": int(conn.execute(
            "SELECT COUNT(*) FROM effect_events").fetchone()[0]),
        "spend_tx": int(conn.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
        ).fetchone()[0]),
        "ledger_tx": int(conn.execute(
            "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]),
    }
    conn.close()
    return out


def read_battery(fx, led):
    return {
        "cv_ada": dump(fx.credits_view("usr:ada")),
        "cv_bob": dump(fx.credits_view("usr:bob")),
        "cv_carol": dump(fx.credits_view("usr:carol")),
        "ev_ada": dump(fx.effects_view("usr:ada")),
        "ev_bob": dump(fx.effects_view("usr:bob")),
        "ev_carol": dump(fx.effects_view("usr:carol")),
        "bal_ada": led.balance("usr:ada")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_reserve": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def full_rows(db_path, table, order_col):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT * FROM %s ORDER BY %s" % (table, order_col)).fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def make_probes(fx):
    return (
        ("bad-acc-buy", lambda: fx.purchase(
            "svc:x", "flood_effect", 10, "order:efp-x1"),
         F.E_EFF_BAD_ACCOUNT),
        ("bad-kind-buy", lambda: fx.purchase(
            "usr:ada", "magic_spark", 10, "order:efp-x2"),
         F.E_EFF_BAD_KIND),
        ("bad-kind-use", lambda: fx.use(
            "usr:ada", "magic_spark", "msg:hall-x", "use:efp-x3"),
         F.E_EFF_BAD_KIND),
        ("zero-price", lambda: fx.purchase(
            "usr:ada", "message_pin", 0, "order:efp-x4"),
         F.E_EFF_BAD_AMOUNT),
        ("empty-buy-ref", lambda: fx.purchase(
            "usr:ada", "message_pin", 10, "   "),
         F.E_EFF_BAD_REF),
        ("empty-msg-ref", lambda: fx.use(
            "usr:ada", "flood_effect", "   ", "use:efp-x6"),
         F.E_EFF_BAD_MESSAGE),
        ("empty-use-ref", lambda: fx.use(
            "usr:ada", "flood_effect", "msg:hall-x", "   "),
         F.E_EFF_BAD_REF),
        ("bob-no-credit", lambda: fx.use(
            "usr:bob", "dynamic_emoji", "msg:hall-x", "use:efp-x8"),
         F.E_EFF_NO_CREDIT),
        ("bob-cross-kind", lambda: fx.use(
            "usr:bob", "limit_up_effect", "msg:hall-x", "use:efp-x9"),
         F.E_EFF_NO_CREDIT),
    )


def run_probes(probe_specs):
    lines = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_error(fn, code)
        lines.append("%s=%s" % (label, got) if ok_one else
                     "%s NOT-RAISED(%s)" % (label, got))
    return lines, all("NOT-RAISED" not in p for p in lines)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="effects-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    mod_sha_before = dict(
        (name, sha16(io_read(os.path.join(BASE, name + ".py"))))
        for name in ("effects", "ledger"))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path ----
    led = L.Ledger(db_path, cfg)
    fx = F.EffectsFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-EFP", "settlement")
    for who in ("ada", "bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    for who, amount in (("ada", 300), ("bob", 100), ("carol", 200)):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:efp-fund-" + who,
                   "persist window funding " + who)

    p1 = fx.purchase("usr:ada", "dynamic_emoji", 50, "order:efp-a1")
    p2 = fx.purchase("usr:ada", "limit_up_effect", 10, "order:efp-a2")
    p3 = fx.purchase("usr:ada", "flood_effect", 10, "order:efp-a3")
    p4 = fx.purchase("usr:ada", "message_pin", 10, "order:efp-a4")
    p5 = fx.purchase("usr:bob", "flood_effect", 10, "order:efp-b1")
    p1b = fx.purchase("usr:ada", "dynamic_emoji", 50, "order:efp-a1")
    u1 = fx.use("usr:ada", "dynamic_emoji", "msg:hall-1", "use:efp-u1")
    u2 = fx.use("usr:ada", "limit_up_effect", "msg:hall-2", "use:efp-u2")

    # -- AC-EFP1 control anchor: world pinned + gate probes ----
    bat1 = read_battery(fx, led)
    cnt1 = table_counts(db_path)
    snap_credits = full_rows(db_path, "effect_credits", "credit_id")
    snap_effects = full_rows(db_path, "effect_events", "effect_id")
    ok_world = (
        p1["credit_id"] == 1 and p2["credit_id"] == 2
        and p3["credit_id"] == 3 and p4["credit_id"] == 4
        and p5["credit_id"] == 5
        and not p1["idempotent"] and p1b["idempotent"]
        and p1b["credit_id"] == p1["credit_id"]
        and p1b["spend_tx"] == p1["spend_tx"]
        and u1["effect_id"] == 1 and u1["used_credit"] == 1
        and not u1["idempotent"]
        and u2["effect_id"] == 2 and u2["used_credit"] == 2
        and cnt1["credits"] == 5 and cnt1["effects"] == 2
        and cnt1["spend_tx"] == 5
        and bat1["bal_ada"] == 220 and bat1["bal_bob"] == 90
        and bat1["bal_carol"] == 200 and bat1["bal_reserve"] == 490
        and '"consumed": true' in bat1["cv_ada"]
        and '"consumed": false' in bat1["cv_ada"]
        and '"consumed": false' in bat1["cv_bob"]
        and '"credits": []' in bat1["cv_carol"]
        and '"effects": []' in bat1["ev_carol"])
    probe_specs1 = make_probes(fx)
    probes1, ok_probes1 = run_probes(probe_specs1)
    ok_drift1 = (table_counts(db_path) == cnt1
                 and read_battery(fx, led) == bat1)
    ok1 = ok_world and ok_probes1 and ok_drift1
    record("AC-EFP1", ok1, "anchor world pinned (ada buys all four"
          " kinds 50/10/10/10 = credits #1..#4 each bound to a real"
          " spend tx; bob buys flood@10 = credit #5 for the"
          " cross-kind probe; purchase-ref replay of order:efp-a1"
          " absorbed idempotently onto credit #%d with zero second"
          " charge; ada fires dynamic + limit-up effects #1/#2"
          " consuming credits #1/#2; carol stays a zero-row pure"
          " face; credits=5 effects=2 spend-tx=5; balances"
          " 220/90/200, pool:reserve 490 = consumption flows back"
          " in); nine gate probes rejected (%s); counts and"
          " battery frozen across the probe batch; digest=%s"
          % (p1b["credit_id"], "; ".join(probes1),
             evidence_digest(bat1)))

    # -- AC-EFP2 cross-restart byte-identical replay -------------
    fx.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    fx2 = F.EffectsFace(led2)
    bat2 = read_battery(fx2, led2)
    diffs2 = battery_diffs(bat1, bat2)
    ok2 = not diffs2
    record("AC-EFP2", ok2, "two-piece close (fx.close + led.close)"
          " -> Ledger same db/cfg + EffectsFace fresh: read battery"
          " byte-identical to the pre-close snapshot (credits and"
          " effects views for all three accounts with persisted"
          " spend-tx provenance and consumption state + four"
          " balances), diffs=%s; the effects read faces rebuild"
          " over the same effect_credits/effect_events rows with"
          " zero in-memory drift; digest=%s"
          % (diffs2 or "none", evidence_digest(bat2)))

    # -- AC-EFP3 gates survive the restart, zero drift ----------
    probe_specs2 = make_probes(fx2)
    probes2, ok_probes2 = run_probes(probe_specs2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(fx2, led2) == bat2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-EFP3", ok3, "restart-surviving gates: nine probes"
          " all rejected with identical codes on instance 2 (%s);"
          " the kind registry gate rides the CHECK constraint, the"
          " no-credit gates ride the persisted unconsumed-credit"
          " rows, the arg gates ride the module law - every gate"
          " survives the restart; counts and battery frozen across"
          " the probe batch (credits=%d effects=%d unchanged, zero"
          " movement)" % (
              "; ".join(probes2), cnt1["credits"], cnt1["effects"]))

    # -- AC-EFP4 post-restart real-path continuation --------------
    u3 = fx2.use("usr:ada", "message_pin", "msg:hall-3", "use:efp-u3")
    u4 = fx2.use("usr:ada", "flood_effect", "msg:hall-4", "use:efp-u4")
    p6 = fx2.purchase("usr:carol", "dynamic_emoji", 5, "order:efp-c1")
    u5 = fx2.use("usr:carol", "dynamic_emoji", "msg:hall-5",
                 "use:efp-c2")
    bat4 = read_battery(fx2, led2)
    cnt4 = table_counts(db_path)
    conn = sqlite3.connect(db_path)
    tx_head = conn.execute(
        "SELECT type FROM ledger_tx WHERE tx_id = ?",
        (p6["spend_tx"],)).fetchone()
    carol_leg = conn.execute(
        "SELECT COUNT(*) FROM ledger_entries e JOIN ledger_tx t"
        " ON t.tx_id = e.tx_id WHERE t.tx_id = ? AND"
        " e.direction = 'debit' AND e.account_id = 'usr:carol'",
        (p6["spend_tx"],)).fetchone()
    conn.close()
    ok4 = (
        u3["effect_id"] == 3 and u3["used_credit"] == 4
        and not u3["idempotent"]
        and u4["effect_id"] == 4 and u4["used_credit"] == 3
        and not u4["idempotent"]
        and p6["credit_id"] == 6 and not p6["idempotent"]
        and u5["effect_id"] == 5 and u5["used_credit"] == 6
        and not u5["idempotent"]
        and tx_head is not None and tx_head[0] == "spend"
        and int(carol_leg[0]) == 1
        and cnt4["credits"] == 6 and cnt4["effects"] == 5
        and cnt4["spend_tx"] == 6
        and bat4["bal_ada"] == 220 and bat4["bal_bob"] == 90
        and bat4["bal_carol"] == 195 and bat4["bal_reserve"] == 495
        and '"consumed": false' in bat4["cv_bob"]
        and '"consumed": true' in bat4["cv_carol"])
    record("AC-EFP4", ok4, "post-restart continuation: ada's"
          " pre-restart message_pin credit #4 keeps serving the"
          " new use (effect #3) and her pre-restart flood credit"
          " #3 keeps serving the new use (effect #4) - the"
          " persisted credit pool survives the restart as live"
          " ammunition; carol runs a fresh purchase->use chain:"
          " dynamic_emoji@5 buys credit #6 bound to a fresh spend"
          " tx (SQL cross: type=spend with the usr:carol debit"
          " leg) and fires effect #5; credits 5->6, effects 2->5,"
          " spend-tx 5->6; balances ada 220 / bob 90 / carol"
          " 200->195, pool:reserve 490->495; bob's flood credit"
          " still unconsumed, carol's credit consumed; digest=%s"
          % evidence_digest(bat4))

    # -- AC-EFP5 frozen rows + replay gates across the restart --
    # Three-lane freeze law (R1947 first-run erratum, R1883
    # family): rows untouched by the continuation freeze full-
    # field; credits #3/#4 are consumed BY DESIGN by the AC-EFP4
    # continuation (consumption marking is the module's single
    # UPDATE surface), so their identity columns (0..6, incl.
    # purchased_utc and the bound spend tx) freeze and their
    # consumption transition is asserted instead.
    rows_c = full_rows(db_path, "effect_credits", "credit_id")
    rows_e = full_rows(db_path, "effect_events", "effect_id")
    frozen_touched = (rows_c[0] == snap_credits[0]
                      and rows_c[1] == snap_credits[1]
                      and rows_c[4] == snap_credits[4])
    identity_frozen = all(rows_c[i][:7] == snap_credits[i][:7]
                          for i in (2, 3))
    transition = (rows_c[2][7] is not None and rows_c[2][8] == 4
                 and rows_c[3][7] is not None and rows_c[3][8] == 3)
    frozen_e = rows_e[:len(snap_effects)] == snap_effects
    pr = fx2.purchase("usr:ada", "dynamic_emoji", 50, "order:efp-a1")
    ur = fx2.use("usr:ada", "dynamic_emoji", "msg:hall-1",
                 "use:efp-u1")
    ok_dup, code_dup = expect_error(
        lambda: fx2.use("usr:bob", "dynamic_emoji", "msg:hall-1",
                        "use:efp-u1"),
        F.E_EFF_DUP_USE)
    ok_empty, code_empty = expect_error(
        lambda: fx2.use("usr:ada", "dynamic_emoji", "msg:hall-9",
                        "use:efp-u9"),
        F.E_EFF_NO_CREDIT)
    bat5 = read_battery(fx2, led2)
    ok5 = (frozen_touched and identity_frozen and transition
           and frozen_e
           and pr["idempotent"] and pr["credit_id"] == 1
           and pr["spend_tx"] == p1["spend_tx"]
           and ur["idempotent"] and ur["effect_id"] == 1
           and ur["used_credit"] == 1
           and ok_dup and code_dup == F.E_EFF_DUP_USE
           and ok_empty and code_empty == F.E_EFF_NO_CREDIT
           and table_counts(db_path) == cnt4 and bat5 == bat4)
    record("AC-EFP5", ok5, "frozen faces, three lanes: the"
          " continuation-untouched credit rows (#1/#2 consumed"
          " pre-close with their consumed_utc marking and"
          " used_effect bindings, #5 bob's idle round) keep"
          " every one of the nine columns byte-identical to the"
          " pre-close snapshot; credits #3/#4 - consumed BY DESIGN"
          " by the continuation (consumption marking is the"
          " module's single UPDATE surface) - keep their identity"
          " columns frozen (account/kind/ref/price/bound spend tx/"
          " purchased_utc) while the transition lands as asserted"
          " (credit #3 consumed by effect #4, credit #4 consumed"
          " by effect #3, both consumed_utc set); every"
          " pre-existing effect row (all seven columns) stays"
          " byte-identical (immutable rows, zero UPDATE); replay"
          " gates across the restart: purchase-ref replay returns"
          " the original credit #%d idempotently with the original"
          " spend tx and zero second charge, use-ref replay"
          " returns the original effect #%d idempotently with"
          " zero second consumption, cross-account replay of"
          " use:efp-u1 by bob rejected %s, exhausted-kind reuse"
          " rejected %s; counts and battery frozen across all"
          " four replay probes"
          % (pr["credit_id"], ur["effect_id"], code_dup,
             code_empty))

    # -- AC-EFP6 pure-read law ------------------------------------
    bat_a = read_battery(fx2, led2)
    bat_b = read_battery(fx2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(db_path) == cnt4)
    record("AC-EFP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - credits/effects views for all three"
          " accounts plus four balances byte-identical between the"
          " two reads and table counts constant (read faces have"
          " zero side effects)")

    # -- AC-EFP7 third instance stability + hygiene ---------------
    fx2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    fx3 = F.EffectsFace(led3)
    bat3 = read_battery(fx3, led3)
    diffs3 = battery_diffs(bat5, bat3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in
                         ("urllib", "requests", "socket", "http"))]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    ok7 = (not diffs3
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok
           and non_ascii == 0 and not net_imports
           and tmp_outside)
    record("AC-EFP7", ok7, "third instance: two-piece close ->"
          " reopen same db once more - battery byte-identical to"
          " the instance-2 terminal state (diffs=%s, views and"
          " balances stable across a second restart); shipped"
          " files untouched (config + effects/ledger sha16"
          " stable); suite source pure ASCII (%d non-ascii), zero"
          " network imports (%d hits), world tmp outside repo"
          " (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if tmp_outside else "NO"))

    fx3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
