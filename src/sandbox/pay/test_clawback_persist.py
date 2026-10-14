"""Cross-restart persistence acceptance suite for the refund
conversion-share clawback wiring read faces (R1957; FIFO queue head
from the R1952 reseed line, persist-suite family cadence R1886+).
Criteria AC-CKP1..AC-CKP7 were pre-registered in the
state/queue/tech.md R1957 claim line BEFORE this code (honesty law).

Restart semantics under test: close(Ledger + PayOrders) -> same-db
reopen. The claw idempotence key is the ledger-side UNIQUE(ref,
ref_type) pair plus the pay-side order state, so the whole read-face
family (balance reads, claw envelopes, already_clawed replays,
fail-closed gate codes, wired close_refund envelopes, heal
envelopes) must survive the restart byte-identical with zero new
rows (pure-read law). Envelopes are ts-free by design, so dumps
comparisons are naturally deterministic. The lobby event store
stays live across the reopen - it is not part of the clawback read
family (sequential single-writer precedent R1718 build_wired).

Usage: python test_clawback_persist.py
"""

import hashlib
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import orders as O                       # noqa: E402 (restart subject)
import ledger as LED                     # noqa: E402 (restart subject)

LEDGER_CFG = os.path.join(os.path.dirname(BASE), "ledger", "config.json")
RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_pay_error(fn, code):
    try:
        fn()
    except O.PayError as exc:
        return exc.code == code, str(exc)
    return False, "no-error-raised"


def expect_ledger_error(fn, code):
    try:
        fn()
    except LED.LedgerError as exc:
        return exc.code == code, str(exc)
    return False, "no-error-raised"


def _share100(cfg):
    """Test-owned config copy: the shipped price face keeps
    share_tokens=0 ([needs-CEO] real prices); this mutator is the
    only place a conversion amount enters a test world
    (test_clawback_wiring mutate_tokens precedent)."""
    cfg["products"]["pack_compute_19_9"]["share_tokens"] = 100
    return cfg


def face(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def bal_face(led, account):
    return face(led.balance(account))


def tx_count(db_path):
    return TP.db_query(db_path, "SELECT COUNT(*) FROM ledger_tx")[0][0]


def rev_freeze(db_path, oid):
    """Full reverse-tx freeze evidence for refund:<oid>: the tx row
    tuple plus its entries, deterministically ordered."""
    rows = TP.db_query(db_path,
                       "SELECT tx_id, type, action, ref, ref_type,"
                       " source_ai, memo FROM ledger_tx WHERE ref=?"
                       " ORDER BY tx_id", ("refund:" + oid,))
    out = []
    for row in rows:
        entries = TP.db_query(db_path,
                              "SELECT account_id, direction, amount FROM"
                              " ledger_entries WHERE tx_id=? ORDER BY"
                              " direction, account_id", (row[0],))
        out.append([list(row), [list(e) for e in entries]])
    return face(out)


def gate_batch(led, pay, unknown_led, unknown_pay, granted_oid,
               timeout_oid, zt_oid):
    """The fail-closed gate battery of the claw family, in a fixed
    order; returns the outcome-code sequence (exception codes for
    refusals, envelope status for the honest zero-token read)."""
    out = []
    ok_blank, ev_blank = expect_ledger_error(
        lambda: led.clawback_conversion(""), LED.E_BAD_TYPE)
    out.append("E_BAD_TYPE" if ok_blank else "BAD:" + ev_blank[:30])
    ok_unk, ev_unk = expect_ledger_error(
        lambda: led.clawback_conversion(unknown_led), LED.E_NO_FORWARD_ENTRY)
    out.append("E_NO_FORWARD_ENTRY" if ok_unk else "BAD:" + ev_unk[:30])
    ok_upay, ev_upay = expect_pay_error(
        lambda: pay.clawback_conversion_share(unknown_pay),
        O.E_UNKNOWN_ORDER)
    out.append("E_UNKNOWN_ORDER" if ok_upay else "BAD:" + ev_upay[:30])
    ok_grant, ev_grant = expect_pay_error(
        lambda: pay.clawback_conversion_share(granted_oid), O.E_BAD_STATE)
    out.append("E_BAD_STATE" if ok_grant else "BAD:" + ev_grant[:30])
    ok_tmo, ev_tmo = expect_pay_error(
        lambda: pay.clawback_conversion_share(timeout_oid), O.E_BAD_STATE)
    out.append("E_BAD_STATE" if ok_tmo else "BAD:" + ev_tmo[:30])
    out.append(pay.clawback_conversion_share(zt_oid)["status"])
    return out


def battery(led, pay, accounts, replay_oids):
    """Pure-read battery: balance faces + ledger claw replays + heal
    replays, all dumped for byte-identity comparison."""
    out = {"bal": {}, "claw": {}, "heal": {}}
    for account in accounts:
        out["bal"][account] = bal_face(led, account)
    for oid in replay_oids:
        out["claw"][oid] = face(led.clawback_conversion(oid))
        out["heal"][oid] = face(pay.clawback_conversion_share(oid))
    return face(out)


def _sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    led_path = os.path.join(os.path.dirname(BASE), "ledger", "ledger.py")
    ord_path = os.path.join(BASE, "orders.py")
    wiring_path = os.path.join(BASE, "test_clawback_wiring.py")
    ship_cfg_path = os.path.join(BASE, "config.json")
    pre_sha = {p: _sha(p) for p in (led_path, ord_path, wiring_path,
                                    ship_cfg_path)}
    with open(LEDGER_CFG, encoding="utf-8") as handle:
        led_cfg = json.load(handle)

    # AC-CKP1: anchor world + pre-registered read faces --------------
    world = TP.build(mint=True, cfg_mutator=_share100)
    led_db = os.path.join(world["tmp"], "ledger.db")
    pay_db = os.path.join(world["tmp"], "pay.db")
    led, pay = world["led"], world["pay"]
    oid_a, _ = TP.happy(world, "pack_compute_19_9", "AV-CKPA",
                        nonce="n-ckpa")
    env_close_a = pay.close_refund(oid_a)            # un-wired build
    claw_a = pay.clawback_conversion_share(oid_a)    # heal face claws
    heal_replay_pre = pay.clawback_conversion_share(oid_a)
    replay_a = led.clawback_conversion(oid_a)
    oid_b, _ = TP.happy(world, "pack_compute_19_9", "AV-CKPB",
                        nonce="n-ckpb")
    led.spend("usr:AV-CKPB", 60, "SPEND-CKPB", "order")
    pay.close_refund(oid_b)                 # refund-close, then claw
    claw_b = led.clawback_conversion(oid_b)
    oid_c, _ = TP.happy(world, "pack_compute_19_9", "AV-CKPC",
                        nonce="n-ckpc")
    led.spend("usr:AV-CKPC", 100, "SPEND-CKPC", "order")
    pay.close_refund(oid_c)
    claw_c = led.clawback_conversion(oid_c)
    oid_d, _ = TP.happy(world, "birthright_entry", "AV-CKPD",
                        nonce="n-ckpd")
    pay.close_refund(oid_d)
    claw_d = pay.clawback_conversion_share(oid_d)
    oid_g, _ = TP.happy(world, "pack_compute_19_9", "AV-CKPG",
                        nonce="n-ckpg")               # stays granted
    resp_h = pay.create_order("pack_compute_19_9", "AV-CKPH")
    pay.place_order(resp_h["order_id"])
    pay.sweep_expired(now="2030-01-01T00:00:00Z")
    oid_h = resp_h["order_id"]
    pre_codes = gate_batch(led, pay, "NOPE-CKP-LED", "NOPE-CKP-PAY",
                           oid_g, oid_h, oid_d)
    accounts = ["usr:AV-CKPA", "usr:AV-CKPB", "usr:AV-CKPC",
                "usr:AV-CKPG", "pool:share", "pool:reserve"]
    snap_bal = {a: bal_face(led, a) for a in accounts}
    n_tx = tx_count(led_db)
    n_acct = TP.db_query(led_db,
                         "SELECT COUNT(*) FROM ledger_accounts")[0][0]
    freeze_a = rev_freeze(led_db, oid_a)
    freeze_b = rev_freeze(led_db, oid_b)
    freeze_c = rev_freeze(led_db, oid_c)
    want_codes = ["E_BAD_TYPE", "E_NO_FORWARD_ENTRY", "E_UNKNOWN_ORDER",
                 "E_BAD_STATE", "E_BAD_STATE", "no_forward_entry"]
    ok1 = (env_close_a.get("status") == "closed"
           and "clawback" not in env_close_a
           and claw_a["status"] == "clawed" and claw_a["clawed"] == 100
           and claw_a["idempotent"] is False
           and heal_replay_pre["status"] == "already_clawed"
           and heal_replay_pre["idempotent"] is True
           and replay_a["status"] == "already_clawed"
           and replay_a["idempotent"] is True
           and claw_b["status"] == "clawed" and claw_b["clawed"] == 40
           and claw_b["unclawed_consumed"] == 60
           and claw_b["balance_before"] == 40
           and claw_b["balance_after"] == 0
           and claw_c["status"] == "nothing_to_claw"
           and claw_c["clawed"] == 0
           and claw_c["unclawed_consumed"] == 100
           and claw_d["status"] == "no_forward_entry"
           and led.balance("usr:AV-CKPA")["balance"] == 0
           and led.balance("usr:AV-CKPB")["balance"] == 0
           and led.balance("usr:AV-CKPC")["balance"] == 0
           and led.balance("usr:AV-CKPG")["balance"] == 100
           and led.balance("pool:share")["balance"] == 999740
           and led.balance("pool:reserve")["balance"] == 160
           and pre_codes == want_codes and freeze_c == "[]")
    record("AC-CKP1", ok1,
           "clawA=%s clawB=%s/%d clawC=%s clawD=%s pool=%d reserve=%d"
           " codes=%s" % (claw_a["status"], claw_b["status"],
                         claw_b["clawed"], claw_c["status"],
                         claw_d["status"],
                         led.balance("pool:share")["balance"],
                         led.balance("pool:reserve")["balance"],
                         ",".join(pre_codes)))

    # AC-CKP2: cross-restart byte-identical read faces ----------------
    led.close()
    pay.close()
    led2 = LED.Ledger(led_db, led_cfg)
    pay2 = O.PayOrders(world["cfg"], pay_db, world["events"], led2)
    post_bal = {a: bal_face(led2, a) for a in accounts}
    replay_a2 = led2.clawback_conversion(oid_a)
    heal_replay_post = pay2.clawback_conversion_share(oid_a)
    n_tx2 = tx_count(led_db)
    n_acct2 = TP.db_query(led_db,
                          "SELECT COUNT(*) FROM ledger_accounts")[0][0]
    ok2 = (post_bal == snap_bal
           and face(replay_a2) == face(replay_a)
           and face(heal_replay_post) == face(heal_replay_pre)
           and n_tx2 == n_tx and n_acct2 == n_acct)
    record("AC-CKP2", ok2,
           "bal-identical=%s replay-identical=%s heal-identical=%s"
           " txs %d==%d accounts %d==%d"
           % (post_bal == snap_bal, face(replay_a2) == face(replay_a),
              face(heal_replay_post) == face(heal_replay_pre),
              n_tx, n_tx2, n_acct, n_acct2))

    # AC-CKP3: fail-closed gates cross-restart, same codes/order ------
    post_codes = gate_batch(led2, pay2, "NOPE-CKP-LED", "NOPE-CKP-PAY",
                            oid_g, oid_h, oid_d)
    ok3 = post_codes == pre_codes and post_codes == want_codes
    record("AC-CKP3", ok3,
           "pre==post=%s sequence=%s"
           % (post_codes == pre_codes, ",".join(post_codes)))

    # AC-CKP4: real-path continuation, zero-cache recompute -----------
    world["led"] = led2
    world["pay"] = pay2
    oid_e, _ = TP.happy(world, "pack_compute_19_9", "AV-CKPE",
                        nonce="n-ckpe")
    led2.spend("usr:AV-CKPE", 20, "SPEND-CKPE", "order")
    claw_e = led2.clawback_conversion(oid_e)
    cont_bal = {a: bal_face(led2, a) for a in accounts}
    moved = cont_bal != snap_bal
    pay2.close()
    pay3 = O.PayOrders(world["cfg"], pay_db, world["events"], led2,
                       conversion_clawback=led2)
    world["pay"] = pay3
    oid_f, _ = TP.happy(world, "pack_compute_19_9", "AV-CKPF",
                        nonce="n-ckpf")
    env_f = pay3.close_refund(oid_f)
    rev_f = TP.db_query(led_db, "SELECT COUNT(*) FROM ledger_tx WHERE"
                        " ref=?", ("refund:" + oid_f,))[0][0]
    ok4 = (claw_e["status"] == "clawed" and claw_e["clawed"] == 80
           and claw_e["unclawed_consumed"] == 20
           and claw_e["balance_after"] == 0 and moved
           and led2.balance("pool:share")["balance"] == 999720
           and led2.balance("pool:reserve")["balance"] == 180
           and led2.balance("usr:AV-CKPE")["balance"] == 0
           and env_f["status"] == "closed"
           and env_f["clawback"]["status"] == "clawed"
           and env_f["clawback"]["clawed"] == 100 and rev_f == 1
           and led2.balance("usr:AV-CKPF")["balance"] == 0)
    record("AC-CKP4", ok4,
           "clawE=%d/%d wired-F=%s rev-rows=%d pool=%d reserve=%d"
           % (claw_e["clawed"], claw_e["unclawed_consumed"],
              env_f["clawback"]["status"], rev_f,
              led2.balance("pool:share")["balance"],
              led2.balance("pool:reserve")["balance"]))

    # AC-CKP5: frozen anchors, append-only, zero replay rows -----------
    freeze_a2 = rev_freeze(led_db, oid_a)
    freeze_b2 = rev_freeze(led_db, oid_b)
    replay_c2 = led2.clawback_conversion(oid_c)
    n_pre_replay = tx_count(led_db)
    led2.clawback_conversion(oid_a)
    pay3.clawback_conversion_share(oid_a)
    n_post_replay = tx_count(led_db)
    ok5 = (freeze_a2 == freeze_a and freeze_b2 == freeze_b
           and face(replay_c2) == face(claw_c)
           and rev_freeze(led_db, oid_c) == "[]"
           and n_pre_replay == n_post_replay)
    record("AC-CKP5", ok5,
           "freezeA=%s freezeB=%s nothing-replay=%s rows %d==%d"
           % (freeze_a2 == freeze_a, freeze_b2 == freeze_b,
              face(replay_c2) == face(claw_c), n_pre_replay,
              n_post_replay))

    # AC-CKP6: pure-read law (battery is side-effect free) ------------
    term_accounts = accounts + ["usr:AV-CKPE", "usr:AV-CKPF"]
    b1 = battery(led2, pay3, term_accounts, [oid_a, oid_b])
    n_mid = tx_count(led_db)
    n_acct_mid = TP.db_query(led_db,
                             "SELECT COUNT(*) FROM"
                             " ledger_accounts")[0][0]
    b2 = battery(led2, pay3, term_accounts, [oid_a, oid_b])
    n_end = tx_count(led_db)
    n_acct_end = TP.db_query(led_db,
                             "SELECT COUNT(*) FROM"
                             " ledger_accounts")[0][0]
    ok6 = (b1 == b2 and n_mid == n_end and n_acct_mid == n_acct_end
           and n_mid == n_post_replay)
    record("AC-CKP6", ok6,
           "battery-identical=%s txs %d==%d accounts %d==%d"
           % (b1 == b2, n_mid, n_end, n_acct_mid, n_acct_end))

    # AC-CKP7: third instance stable + hygiene ------------------------
    term_bal = {a: bal_face(led2, a) for a in term_accounts}
    term_tx = tx_count(led_db)
    led2.close()
    pay3.close()
    led3 = LED.Ledger(led_db, led_cfg)
    pay4 = O.PayOrders(world["cfg"], pay_db, world["events"], led3,
                       conversion_clawback=led3)
    third_bal = {a: bal_face(led3, a) for a in term_accounts}
    replay_a3 = led3.clawback_conversion(oid_a)
    heal_replay_third = pay4.clawback_conversion_share(oid_a)
    third_tx = tx_count(led_db)
    ok_third = (third_bal == term_bal and third_tx == term_tx
                and face(replay_a3) == face(replay_a)
                and face(heal_replay_third) == face(heal_replay_pre))
    post_sha = {p: _sha(p) for p in (led_path, ord_path, wiring_path,
                                     ship_cfg_path)}
    with open(os.path.abspath(__file__), "rb") as handle:
        own_src = handle.read()
    try:
        own_src.decode("ascii")
        ok_ascii = True
    except UnicodeDecodeError:
        ok_ascii = False
    bad_imports = [ln for ln in own_src.decode("ascii").splitlines()
                   if ln.strip().startswith(("import ", "from "))
                   and any(net in ln for net in
                           ("urllib", "requests", "socket", "http"))]
    shipped = TP.load_pay_config()
    ok_ship = (shipped["products"]["pack_compute_19_9"]["share_tokens"]
               == 0)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
    ok_outside = not os.path.abspath(world["tmp"]).startswith(repo_root)
    ok7 = (ok_third and post_sha == pre_sha and ok_ascii
           and not bad_imports and ok_ship and ok_outside)
    record("AC-CKP7", ok7,
           "third=%s sha-stable=%s ascii=%s net-imports=%d"
           " shipped-cfg-untouched=%s tmp-outside=%s"
           % (ok_third, post_sha == pre_sha, ok_ascii, len(bad_imports),
              ok_ship, ok_outside))

    led3.close()
    pay4.close()
    shutil.rmtree(world["tmp"], ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not fails else "FAIL",
                              len(RESULTS) - len(fails), len(RESULTS)),
          flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
