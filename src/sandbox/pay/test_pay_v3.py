"""Acceptance suite for the WeChat Pay V3 callback face (BigDomain
P-47-4b follow-up, tech-queue item). Asserts the pre-registered
criteria AC-V31..AC-V39 (src/os/backlog.md R555 row, registered before
this file existed; honesty law). Prints PASS/FAIL with evidence; exits
non-zero on any FAIL.

The V3 face is opt-in per channel ("callback_style": "v3"); the shipped
config.json keeps the flat legacy contract, so the AC-Y1..Y14 baseline
suite (test_pay.py) is untouched and re-run separately as regression.

Usage: python test_pay_v3.py
"""

import copy
import datetime
import hashlib
import hmac
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import orders as O                                    # noqa: E402
import adapters as A                                  # noqa: E402
import v3 as V3M                                      # noqa: E402
from ledger import Ledger                             # noqa: E402 (ledger product)
import store as lobby_store                           # noqa: E402 (lobby product)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_reject(fn, needle):
    try:
        fn()
    except O.PayError as exc:
        return (exc.code == "E_CALLBACK_REJECTED"
                and needle in (exc.detail or "")), "%s (detail=%s)" % (
            exc.code, exc.detail or "-")
    return False, "no-error-raised"


def db_query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def build():
    """Fresh world with the standard channel switched to the V3
    callback contract (in-test config only; shipped config untouched)."""
    tmp = tempfile.mkdtemp(prefix="pay-v3-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        cfg = json.load(h)
    cfg["channels"]["standard"]["callback_style"] = "v3"
    cfg["channels"]["standard"]["v3_serials"] = ["PLAT-CERT-SERIAL-1"]
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as h:
        json.dump(cfg, h, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as h:
        led_cfg = json.load(h)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-PAY-V3-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    return {"tmp": tmp, "cfg": cfg, "events": events, "ledger": led, "pay": pay}


def fresh_placed_v3_order(world, product_id="share_observation",
                          avatar="v3-avatar-1"):
    """create + place one order on the V3 (standard) channel. Distinct
    avatars per call: order ids are content-addressed per
    (avatar, product, bucket), so a same-avatar re-buy of the same
    product replays onto the same id instead of a fresh order."""
    made = world["pay"].create_order(product_id, avatar)
    world["pay"].place_order(made["order_id"])
    return made["order_id"]


def main():
    world = build()
    pay, led, events = world["pay"], world["ledger"], world["events"]
    adapter = pay._adapters["standard"]
    assert isinstance(adapter, V3M.V3Channel), "standard channel not V3"

    order_id = fresh_placed_v3_order(world)
    nonce1 = "v3nonce-0001"
    good = adapter.make_v3_callback(order_id, 100000, nonce1)

    # AC-V34 first (also proves the 4012365342 verification string)
    body, ts, hnonce = good["v3"]["body"], good["v3"]["headers"][
        "Wechatpay-Timestamp"], good["v3"]["headers"]["Wechatpay-Nonce"]
    manual = hmac.new(adapter.key.encode("utf-8"),
                      ("%s\n%s\n%s\n" % (ts, hnonce, body)).encode("utf-8"),
                      hashlib.sha256).hexdigest()
    record("AC-V34a", manual == good["sig"] and manual == good["v3"][
        "headers"]["Wechatpay-Signature"],
        "sig == HMAC-SHA256(key, ts\\nnonce\\nbody\\n) canonical string")
    bad_sig = copy.deepcopy(good)
    bad_sig["sig"] = ("0" * 64) if good["sig"][0] != "0" else ("1" * 64)
    bad_sig["v3"]["headers"]["Wechatpay-Signature"] = bad_sig["sig"]
    ok, ev = expect_reject(
        lambda: pay.handle_callback(bad_sig), "signature mismatch")
    record("AC-V34b", ok, "tampered signature rejected: " + ev)

    # AC-V31: four-header contract
    miss = copy.deepcopy(good)
    del miss["v3"]["headers"]["Wechatpay-Signature"]
    ok, ev = expect_reject(
        lambda: pay.handle_callback(miss), "missing header: Wechatpay-Signature")
    rows = db_query(os.path.join(world["tmp"], "pay.db"),
                    "SELECT COUNT(*) FROM pay_receipts WHERE sig_ok=0"
                    " AND nonce=?", (nonce1,))
    record("AC-V31", ok and rows[0][0] >= 1,
           "missing header rejected + bad receipt row: " + ev)

    # AC-V32: serial gate
    unk = copy.deepcopy(good)
    unk["v3"]["headers"]["Wechatpay-Serial"] = "NOT-A-KNOWN-SERIAL"
    ok, ev = expect_reject(lambda: pay.handle_callback(unk), "unknown serial")
    record("AC-V32a", ok, "unknown serial rejected: " + ev)
    pk = adapter.make_v3_callback(order_id, 100000, "v3nonce-pubkey",
                                  serial="PUB_KEY_ID_1234567890")
    pay.handle_callback(pk)  # pub-key-id format passes the serial gate
    rows = db_query(os.path.join(world["tmp"], "pay.db"),
                    "SELECT status FROM pay_orders WHERE order_id=?", (order_id,))
    record("AC-V32b", rows[0][0] == "granted",
           "PUB_KEY_ID_<digits> serial accepted, order granted: %s" % rows[0][0])

    # fresh order for the remaining stateful cases
    order_id = fresh_placed_v3_order(world, "report_data_b", "v3-avatar-2")
    good = adapter.make_v3_callback(order_id, 199900, "v3nonce-1000")

    # AC-V33: parameterized timestamp window (stale = now-400s > 300s)
    stale_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp()
                   - 400)
    stale = adapter.make_v3_callback(order_id, 199900, "v3nonce-stale",
                                     ts_unix=stale_ts)
    ok, ev = expect_reject(lambda: pay.handle_callback(stale), "ts outside")
    record("AC-V33", ok, "stale Wechatpay-Timestamp rejected: " + ev)

    # AC-V35: envelope decode + uniform/body cross-check. A hostile or
    # buggy gateway signs whatever body it pushes, so the corrupt-
    # ciphertext case must carry a VALID signature over the corrupt body
    # (re-signed in-test with the channel test key).
    msg = json.loads(good["v3"]["body"])
    msg["resource"]["ciphertext"] = "!!" + msg["resource"]["ciphertext"]
    bad_body = json.dumps(msg, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
    corrupt = copy.deepcopy(good)
    corrupt["v3"]["body"] = bad_body
    corrupt_sig = hmac.new(adapter.key.encode("utf-8"),
                          ("%s\n%s\n%s\n" % (
                              good["v3"]["headers"]["Wechatpay-Timestamp"],
                              good["v3"]["headers"]["Wechatpay-Nonce"],
                              bad_body))
                          .encode("utf-8"), hashlib.sha256).hexdigest()
    corrupt["v3"]["headers"]["Wechatpay-Signature"] = corrupt_sig
    corrupt["sig"] = corrupt_sig
    ok, ev = expect_reject(lambda: pay.handle_callback(corrupt),
                           "malformed resource")
    record("AC-V35a", ok, "valid-sig corrupt ciphertext rejected: " + ev)
    inject = adapter.make_v3_callback(order_id, 199900, "v3nonce-inject")
    inject["amount_cent"] = 1  # uniform field no longer matches signed body
    ok, ev = expect_reject(lambda: pay.handle_callback(inject),
                           "uniform/body mismatch")
    record("AC-V35b", ok, "translation-injection rejected: " + ev)

    # AC-V36: trade_state gate + zero idempotency pollution
    refund = adapter.make_v3_callback(order_id, 199900, "v3nonce-refund",
                                      trade_state="REFUND",
                                      event_type="TRANSACTION.REFUND")
    ok, ev = expect_reject(lambda: pay.handle_callback(refund),
                           "trade_state=REFUND not SUCCESS")
    record("AC-V36a", ok, "signed but non-SUCCESS rejected: " + ev)
    succ = adapter.make_v3_callback(order_id, 199900, "v3nonce-succ")
    res = pay.handle_callback(succ)
    record("AC-V36b", res["status"] == "granted",
           "later SUCCESS callback on same order still pays: %s" % res["status"])

    # AC-V37: ack semantics per 4012791902
    a_ok, a_fail = V3M.ack_ok(), V3M.ack_fail("signature mismatch")
    record("AC-V37", a_ok == {"http_status": 200, "body": None}
           and a_fail["http_status"] == 400
           and a_fail["body"] == {"code": "FAIL",
                                  "message": "signature mismatch"},
           "ok=200 no body / fail=400 {code:FAIL,message}")

    # AC-V38: end-to-end constitutional order + idempotent redelivery
    redel = pay.handle_callback(succ)
    grants = db_query(os.path.join(world["tmp"], "pay.db"),
                      "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                      (order_id,))
    evs = db_query(os.path.join(world["tmp"], "events.db"),
                   "SELECT COUNT(*) FROM events WHERE type='pay.success'"
                   " AND payload_json LIKE ?",
                   ("%" + order_id + "%",))
    record("AC-V38a", redel["idempotent"] is True and grants[0][0] == 1
           and evs[0][0] == 1,
           "redelivery idempotent, 1 grant, 1 pay.success event (15-retry"
           " gradient re-entry)")
    order_id = fresh_placed_v3_order(world, "report_data_b", "v3-avatar-3")
    t_now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    base = adapter.make_v3_callback(order_id, 199900, "v3nonce-replay",
                                    ts_unix=t_now)
    pay.handle_callback(base)
    replay = adapter.make_v3_callback(order_id, 199900, "v3nonce-replay",
                                      ts_unix=t_now + 1)  # distinct receipt,
    ok, ev = expect_reject(lambda: pay.handle_callback(replay),  # same nonce
                           "nonce replay")
    record("AC-V38b", ok, "nonce replay (bad 4) rejected: " + ev)

    # AC-V39: honesty marks + ASCII + no network
    src = open(os.path.join(BASE, "v3.py"), "rb").read()
    ascii_ok = all(b < 128 for b in src)
    text = src.decode("ascii")
    marks = ("RSA-SHA256" in text and "stand-in" in text
             and "AEAD_AES_256_GCM" in text and "PUB_KEY_ID" in text
             and ".env" in text)
    no_net = not any(w in text for w in ("import socket", "urllib",
                                        "requests", "http.client"))
    record("AC-V39", ascii_ok and marks and no_net,
           "STANDIN marks present, pure ASCII, zero network imports")

    world["pay"].close()
    world["ledger"].close()
    world["events"].close()
    bad = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d/%d" % ("PASS" if not bad else "FAIL",
                               len(RESULTS) - len(bad), len(RESULTS)),
          flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
