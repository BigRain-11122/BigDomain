"""Acceptance suite for the refund conversion-share clawback (R1721
successor, R1723). Asserts the pre-registered criteria AC-RC1..AC-RC8
(state/queue/tech.md R1723 claim line, registered BEFORE this code;
honesty law).

Design ruling under test: no overdraft ever (AC-L2 floor is
constitutional, the claw is capped at min(forward, current balance));
the forward tx is the amount authority (zero caller amounts); the
reverse books as ref='refund:'+order_id / ref_type='order' /
type='adjust' with a provenance memo; the UNIQUE(ref, ref_type) pair
is the natural idempotency key. Wiring law: caller-built caller-owned
face (conversion_clawback=None default = shipped behavior
byte-stable), post-commit attempts never break a completed refund
close (R1681->R1701->R1718 degraded-pipeline precedent).

Usage: python test_clawback_wiring.py
"""

import json
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import orders as O                       # noqa: E402 (wiring subject)
import ledger as LED                     # noqa: E402 (face subject)

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


def mutate_tokens(cfg, tokens):
    """Test-owned config copy: the shipped price face keeps
    share_tokens=0 ([needs-CEO] real prices); this mutator is the
    only place a conversion amount enters a test world."""
    cfg["products"]["pack_compute_19_9"]["share_tokens"] = int(tokens)
    return cfg


def build_claw(tokens=100):
    """Fresh world with a funded pool and a share_tokens product."""
    world = TP.build(mint=True,
                     cfg_mutator=lambda c: mutate_tokens(c, tokens))
    return world


def build_wired(tokens=100, face="LEDGER"):
    """Fresh world re-opened with a wired conversion_clawback face
    (R1718 build_wired precedent: the un-wired PayOrders closes
    FIRST, then the wired one opens on the same pay.db - sequential
    single-writer). face='LEDGER' wires the real ledger (the product
    face); any other object is a caller-built stub."""
    world = build_claw(tokens)
    pay_db = os.path.join(world["tmp"], "pay.db")
    world["pay"].close()
    claw = world["led"] if face == "LEDGER" else face
    world["pay"] = O.PayOrders(world["cfg"], pay_db, world["events"],
                               world["led"], conversion_clawback=claw)
    world["pay_db"] = pay_db
    return world


def drop(world):
    world["pay"].close()
    world["led"].close()
    shutil.rmtree(world["tmp"], ignore_errors=True)


class BrokenClawFace(object):
    """Caller-built failure-injection stub (never the product)."""

    def __init__(self, exc):
        self._exc = exc

    def clawback_conversion(self, order_id):
        raise self._exc


def simulate_race(led, oid):
    """Deterministic race-window probe: a 'concurrent' booker lands a
    reverse tx BETWEEN the face's pre-check and its own write, so the
    pre-check misses and the INSERT collides on UNIQUE(ref, ref_type).
    The face must answer already_clawed - never a raise. The injected
    racing book carries a forced distinct ts so the collision is the
    ref-pair (E_REF_DUPLICATE), not a same-tx_id echo (E_TX_DUPLICATE)."""
    orig = led._write_tx
    fired = [False]

    def racer(tx_type, action, ref, ref_type, source_ai, entries,
              memo=None, ts_utc=None):
        if ref.startswith("refund:") and not fired[0]:
            fired[0] = True
            orig(tx_type, action, ref, ref_type, source_ai, entries,
                 memo, ts_utc="2000-01-01T00:00:00Z")
        return orig(tx_type, action, ref, ref_type, source_ai, entries,
                    memo, ts_utc)

    led._write_tx = racer
    try:
        return led.clawback_conversion(oid)
    finally:
        led._write_tx = orig


def tx_count(db_path):
    return TP.db_query(db_path, "SELECT COUNT(*) FROM ledger_tx")[0][0]


def main():
    # AC-RC1: face contract + missing-forward fail-closed --------------
    w1 = build_claw(100)
    try:
        ok_blank, ev_blank = expect_ledger_error(
            lambda: w1["led"].clawback_conversion(""), LED.E_BAD_TYPE)
        ok_unknown, ev_unknown = expect_ledger_error(
            lambda: w1["led"].clawback_conversion("NOPE-1"),
            LED.E_NO_FORWARD_ENTRY)
        n_before = tx_count(os.path.join(w1["tmp"], "ledger.db"))
        n_after = tx_count(os.path.join(w1["tmp"], "ledger.db"))
    finally:
        drop(w1)
    w1z = build_claw(0)                    # zero-token product world
    try:
        with open(LEDGER_CFG, encoding="utf-8") as handle:
            led_cfg = json.load(handle)
        oid0, _ = TP.happy(w1z, "pack_compute_19_9", "AV-RC1Z",
                           nonce="n-rc1z")
        ok_z, ev_z = expect_ledger_error(
            lambda: w1z["led"].clawback_conversion(oid0),
            LED.E_NO_FORWARD_ENTRY)
        fwd0 = TP.db_query(os.path.join(w1z["tmp"], "ledger.db"),
                           "SELECT COUNT(*) FROM ledger_tx WHERE ref=?"
                           " AND ref_type='order'", (oid0,))[0][0]
        # schema-object parity: the claw path never touches the schema
        probe = os.path.join(w1z["tmp"], "probe.db")
        LED.Ledger(probe, led_cfg).close()
        obj_claw = TP.db_query(os.path.join(w1z["tmp"], "ledger.db"),
                               "SELECT COUNT(*) FROM sqlite_master WHERE"
                               " name NOT LIKE 'sqlite_%'")[0][0]
        obj_fresh = TP.db_query(probe,
                                "SELECT COUNT(*) FROM sqlite_master WHERE"
                                " name NOT LIKE 'sqlite_%'")[0][0]
        record("AC-RC1", ok_blank and ok_unknown and n_before == n_after
               and ok_z and fwd0 == 0 and obj_claw == obj_fresh,
               "blank=%s unknown=%s zero-writes=%s (%d==%d)"
               " zero-token-product=%s fwd-rows=%d schema-objects"
               " %d==%d" % (ok_blank, ok_unknown, n_before == n_after,
                            n_before, n_after, ok_z, fwd0,
                            obj_claw, obj_fresh))
    finally:
        drop(w1z)

    # AC-RC2: forward-authority read + full claw (unspent world) ------
    w2 = build_claw(100)
    try:
        oid2, _ = TP.happy(w2, "pack_compute_19_9", "AV-RC2", nonce="n-rc2")
        led_db2 = os.path.join(w2["tmp"], "ledger.db")
        out2 = w2["led"].clawback_conversion(oid2)
        rev2 = TP.db_query(led_db2,
                           "SELECT t.type, t.action, t.ref, t.ref_type,"
                           " t.source_ai, t.memo FROM ledger_tx t WHERE"
                           " t.ref=? AND t.ref_type='order'",
                           ("refund:" + oid2,))[0]
        entries2 = TP.db_query(led_db2,
                              "SELECT account_id, direction, amount FROM"
                              " ledger_entries WHERE tx_id=? ORDER BY"
                              " direction", (out2["tx_id"],))
        bal2 = w2["led"].balance("usr:AV-RC2")["balance"]
        ok2 = (out2["status"] == "clawed" and out2["clawed"] == 100
               and out2["forward_amount"] == 100
               and out2["unclawed_consumed"] == 0
               and out2["balance_before"] == 100
               and out2["balance_after"] == 0 and not out2["idempotent"]
               and out2["ref"] == "refund:" + oid2
               and rev2[0] == "adjust" and rev2[1] == "pay_conversion_refund"
               and rev2[3] == "order" and rev2[4] == 0
               and oid2 in str(rev2[5])
               and entries2 == [("pool:share", "credit", 100),
                                ("usr:AV-RC2", "debit", 100)]
               and bal2 == 0)
        record("AC-RC2", ok2,
               "status=%s clawed=%s fwd=%s bal %d->%d tx=%s pool-entry"
               "=%s" % (out2["status"], out2["clawed"],
                        out2["forward_amount"], out2["balance_before"],
                        out2["balance_after"], out2["tx_id"],
                        entries2[0]))
    finally:
        drop(w2)

    # AC-RC3: overdraft cap + pool net-zero (spent world) -------------
    w3 = build_claw(100)
    try:
        oid3, _ = TP.happy(w3, "pack_compute_19_9", "AV-RC3", nonce="n-rc3")
        w3["led"].spend("usr:AV-RC3", 60, "SPEND-RC3-1", "order")
        out3 = w3["led"].clawback_conversion(oid3)
        led_db3 = os.path.join(w3["tmp"], "ledger.db")
        conv_bal = w3["led"].balance("pool:share")["balance"]
        reserve_bal = w3["led"].balance("pool:reserve")["balance"]
        usr_bal = w3["led"].balance("usr:AV-RC3")["balance"]
        pool_delta = (conv_bal + reserve_bal) - 1000000
        ok3 = (out3["status"] == "clawed" and out3["clawed"] == 40
               and out3["unclawed_consumed"] == 60
               and out3["balance_before"] == 40
               and out3["balance_after"] == 0 and usr_bal == 0
               and conv_bal == 999940 and reserve_bal == 60
               and pool_delta == 0)
        record("AC-RC3", ok3,
               "claw=min(100,bal40)=%d consumed=%d usr=%d conv=%d"
               " reserve=%d pool-delta=%d"
               % (out3["clawed"], out3["unclawed_consumed"], usr_bal,
                  conv_bal, reserve_bal, pool_delta))
    finally:
        drop(w3)

    # AC-RC4: idempotence + nothing-to-claw + race window -------------
    w4 = build_claw(100)
    try:
        oid4, _ = TP.happy(w4, "pack_compute_19_9", "AV-RC4", nonce="n-rc4")
        led_db4 = os.path.join(w4["tmp"], "ledger.db")
        first4 = w4["led"].clawback_conversion(oid4)
        n4 = tx_count(led_db4)
        again4 = w4["led"].clawback_conversion(oid4)
        n4b = tx_count(led_db4)
        ok_idem = (again4["status"] == "already_clawed"
                   and again4["idempotent"] and n4b == n4
                   and again4["tx_id"] == first4["tx_id"]
                   and again4["clawed"] == first4["clawed"])
        # fully-consumed world: nothing_to_claw, zero reverse rows
        oid4b, _ = TP.happy(w4, "pack_compute_19_9", "AV-RC4B",
                            nonce="n-rc4b")
        w4["led"].spend("usr:AV-RC4B", 100, "SPEND-RC4-2", "order")
        out4b = w4["led"].clawback_conversion(oid4b)
        rev4b = TP.db_query(led_db4,
                            "SELECT COUNT(*) FROM ledger_tx WHERE ref=?",
                            ("refund:" + oid4b,))[0][0]
        ok_zero = (out4b["status"] == "nothing_to_claw"
                   and out4b["clawed"] == 0
                   and out4b["unclawed_consumed"] == 100 and rev4b == 0)
        # race window: concurrent booker between pre-check and write
        oid4c, _ = TP.happy(w4, "pack_compute_19_9", "AV-RC4C",
                            nonce="n-rc4c")
        race4 = simulate_race(w4["led"], oid4c)
        race_rev = TP.db_query(led_db4,
                               "SELECT COUNT(*) FROM ledger_tx WHERE"
                               " ref=?", ("refund:" + oid4c,))[0][0]
        ok_race = (race4["status"] == "already_clawed"
                   and race4["idempotent"] and race_rev == 1
                   and race4["clawed"] == 100)
        record("AC-RC4", ok_idem and ok_zero and ok_race,
               "idem=%s nothing=%s race=%s (txs %d==%d, race-rows=%d)"
               % (ok_idem, ok_zero, ok_race, n4, n4b, race_rev))
    finally:
        drop(w4)

    # AC-RC5: double-entry discipline + reconcile audit ----------------
    w5 = build_claw(100)
    try:
        oid5, _ = TP.happy(w5, "pack_compute_19_9", "AV-RC5", nonce="n-rc5")
        w5["led"].spend("usr:AV-RC5", 60, "SPEND-RC5-1", "order")
        w5["led"].clawback_conversion(oid5)
        led_db5 = os.path.join(w5["tmp"], "ledger.db")
        sum_bal = TP.db_query(led_db5,
                              "SELECT COALESCE(SUM(balance),0) FROM"
                              " ledger_accounts")[0][0]
        proc = subprocess.run([sys.executable,
                               os.path.join(os.path.dirname(BASE),
                                            "ledger", "reconcile.py"),
                               led_db5, LEDGER_CFG],
                              capture_output=True, text=True,
                              encoding="utf-8", timeout=180,
                              cwd=os.path.dirname(LEDGER_CFG))
        text = proc.stdout or ""
        n_pass = sum(1 for ln in text.splitlines()
                     if ln.strip().endswith("PASS"))
        n_fail = sum(1 for ln in text.splitlines()
                     if ln.strip().endswith("FAIL"))
        audit_named = ("refund:" + oid5) in text and "adjust:" in text
        ok5 = (proc.returncode == 0 and n_pass == 8 and n_fail == 0
               and sum_bal == 0 and audit_named)
        record("AC-RC5", ok5,
               "reconcile exit=%d %d PASS/%d FAIL zero-sum=%d"
               " audit-line-named=%s" % (proc.returncode, n_pass,
                                         n_fail, sum_bal, audit_named))
    finally:
        drop(w5)

    # AC-RC6: pay wiring contract --------------------------------------
    w6 = build_claw(100)                   # not wired (shipped default)
    try:
        oid6, _ = TP.happy(w6, "pack_compute_19_9", "AV-RC6",
                           nonce="n-rc6")
        env6 = w6["pay"].close_refund(oid6)
        ok_notwired = ("clawback" not in env6
                       and env6["status"] == "closed")
    finally:
        drop(w6)
    w7 = build_wired(100)                  # wired, full claw
    try:
        oid7, _ = TP.happy(w7, "pack_compute_19_9", "AV-RC7",
                           nonce="n-rc7")
        env7 = w7["pay"].close_refund(oid7)
        rev7 = TP.db_query(os.path.join(w7["tmp"], "ledger.db"),
                           "SELECT COUNT(*) FROM ledger_tx WHERE ref=?",
                           ("refund:" + oid7,))[0][0]
        ok_wired = (env7["status"] == "closed"
                    and env7["clawback"]["status"] == "clawed"
                    and env7["clawback"]["clawed"] == 100 and rev7 == 1
                    and w7["led"].balance("usr:AV-RC7")["balance"] == 0)
    finally:
        drop(w7)
    w8 = build_wired(0)                    # wired, zero-token product
    try:
        oid8, _ = TP.happy(w8, "pack_compute_19_9", "AV-RC8",
                           nonce="n-rc8")
        env8 = w8["pay"].close_refund(oid8)
        ok_zerotok = (env8["status"] == "closed"
                      and env8["clawback"]["status"] == "no_forward_entry")
    finally:
        drop(w8)
    w9 = build_wired(100, face=BrokenClawFace(RuntimeError("boom")))
    try:
        oid9, _ = TP.happy(w9, "pack_compute_19_9", "AV-RC9",
                           nonce="n-rc9")
        env9 = w9["pay"].close_refund(oid9)
        rev9 = TP.db_query(os.path.join(w9["tmp"], "ledger.db"),
                           "SELECT COUNT(*) FROM ledger_tx WHERE ref=?",
                           ("refund:" + oid9,))[0][0]
        ok_broken = (env9["status"] == "closed"
                     and env9["clawback"]["status"] == "off:RuntimeError"
                     and rev9 == 0)
    finally:
        drop(w9)
    w10 = build_wired(100, face=BrokenClawFace(
        LED.LedgerError(LED.E_UNKNOWN_ACCOUNT, "stub")))
    try:
        oid10, _ = TP.happy(w10, "pack_compute_19_9", "AV-RC10",
                            nonce="n-rc10")
        env10 = w10["pay"].close_refund(oid10)
        ok_ledgerr = (env10["status"] == "closed"
                      and env10["clawback"]["status"]
                      == "off:E_UNKNOWN_ACCOUNT")
    finally:
        drop(w10)
    record("AC-RC6", ok_notwired and ok_wired and ok_zerotok and ok_broken
           and ok_ledgerr,
           "not-wired=%s wired=%s zero-tok=%s broken=%s ledgerr=%s"
           % (ok_notwired, ok_wired, ok_zerotok, ok_broken, ok_ledgerr))

    # AC-RC7: heal / operator face -------------------------------------
    w11 = build_claw(100)                  # not wired: crash-window path
    try:
        oid11, _ = TP.happy(w11, "pack_compute_19_9", "AV-RC11",
                            nonce="n-rc11")
        env11 = w11["pay"].close_refund(oid11)      # no clawback attempt
        heal11 = w11["pay"].clawback_conversion_share(oid11)
        heal11b = w11["pay"].clawback_conversion_share(oid11)
        ok_heal = ("clawback" not in env11
                   and heal11["status"] == "clawed"
                   and heal11["clawed"] == 100
                   and w11["led"].balance("usr:AV-RC11")["balance"] == 0
                   and heal11b["status"] == "already_clawed"
                   and heal11b["idempotent"])
        # non-closed order refuses
        oid11b, _ = TP.happy(w11, "pack_compute_19_9", "AV-RC11B",
                             nonce="n-rc11b")        # stays granted
        ok_granted, ev_granted = expect_pay_error(
            lambda: w11["pay"].clawback_conversion_share(oid11b),
            O.E_BAD_STATE)
        # timeout close (no grant row) refuses honestly
        resp11c = w11["pay"].create_order("pack_compute_19_9", "AV-RC11C")
        w11["pay"].place_order(resp11c["order_id"])
        w11["pay"].sweep_expired(now="2030-01-01T00:00:00Z")
        ok_timeout, ev_timeout = expect_pay_error(
            lambda: w11["pay"].clawback_conversion_share(resp11c["order_id"]),
            O.E_BAD_STATE)
        ok_unknown, ev_unknown = expect_pay_error(
            lambda: w11["pay"].clawback_conversion_share("NOPE-RC7"),
            O.E_UNKNOWN_ORDER)
        # zero-token heal: honest no_forward_entry read, zero writes
        oid11d, _ = TP.happy(w11, "birthright_entry", "AV-RC11D",
                             nonce="n-rc11d")        # share_tokens=0
        w11["pay"].close_refund(oid11d)
        heal11d = w11["pay"].clawback_conversion_share(oid11d)
        ok_zeroheal = heal11d["status"] == "no_forward_entry"
        record("AC-RC7", ok_heal and ok_granted and ok_timeout
               and ok_unknown and ok_zeroheal,
               "heal=%s granted-refuse=%s timeout-refuse=%s"
               " unknown=%s zero-token-heal=%s"
               % (ok_heal, ok_granted, ok_timeout, ok_unknown,
                  ok_zeroheal))
    finally:
        drop(w11)

    # AC-RC8: hygiene + delivery ---------------------------------------
    with open(os.path.join(os.path.dirname(BASE), "ledger", "ledger.py"),
              "rb") as handle:
        led_src = handle.read()
    with open(os.path.join(BASE, "orders.py"), "rb") as handle:
        ord_src = handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        own_src = handle.read()
    ok_ascii = all(_is_ascii(src) for src in (led_src, ord_src, own_src))

    def method_block(source, marker):
        text = source.decode("ascii")
        start = text.index(marker)
        end = text.index("\n    def ", start)
        return text[start:end]

    led_block = method_block(led_src, "def clawback_conversion")
    ord_block = method_block(ord_src, "def clawback_conversion_share")
    ord_wiring = ord_src.decode("ascii")
    seg_start = ord_wiring.index("claw_out = None")
    seg_end = ord_wiring.index('out = {"order_id": order_id, "status":'
                               ' "closed"}', seg_start)
    wiring_seg = ord_wiring[seg_start:seg_end]
    ok_noupd = ("UPDATE" not in led_block
                and "UPDATE" not in ord_block
                and "UPDATE" not in wiring_seg)
    own_text = own_src.decode("ascii")
    bad_imports = [line for line in own_text.splitlines()
                   if line.strip().startswith(("import ", "from "))
                   and any(net in line for net in
                           ("urllib", "requests", "socket", "http"))]
    ok_imports = not bad_imports
    shipped = TP.load_pay_config()
    ok_cfg = (shipped["products"]["pack_compute_19_9"]["share_tokens"] == 0
              and os.path.isfile(LEDGER_CFG))
    record("AC-RC8", ok_ascii and ok_noupd and ok_imports and ok_cfg,
           "ascii=%s no-UPDATE=%s net-imports=%d shipped-cfg-untouched=%s"
           % (ok_ascii, ok_noupd, len(bad_imports), ok_cfg))

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not fails else "FAIL",
                              len(RESULTS) - len(fails), len(RESULTS)),
          flush=True)
    return 1 if fails else 0


def _is_ascii(raw):
    try:
        raw.decode("ascii")
        return True
    except UnicodeDecodeError:
        return False


if __name__ == "__main__":
    sys.exit(main())
