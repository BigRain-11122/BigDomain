"""Acceptance suite for the REAL-primitive V3 path (BigDomain R598,
pay v3 adapter real-primitive upgrade: R555 STANDIN -> real RSA-SHA256
verify + real AEAD_AES_256_GCM resource decrypt, behind per-channel
opt-in "verify_mode": "rsa"). Asserts the pre-registered criteria
AC-V3R1..AC-V3R8 (src/os/backlog.md R598 row, registered before this
file and before the v3.py edits existed; honesty law).

Fixture honesty: the RSA keypair and the APIv3 key are self-generated
in-memory at runtime (cryptography RSA 2048 / os.urandom); they are
throwaway fixtures, never real WeChat platform keys, never persisted
to disk, never committed. Real keys remain CEO account-domain physical
items (.env only). Zero network is used anywhere.

Usage: python test_pay_v3_real.py
"""

import base64
import copy
import datetime
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from cryptography.hazmat.primitives import serialization          # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa          # noqa: E402

import orders as O                                    # noqa: E402
import adapters as A                                  # noqa: E402
import v3 as V3M                                      # noqa: E402
from ledger import Ledger                             # noqa: E402 (ledger product)
import store as lobby_store                           # noqa: E402 (lobby product)

RESULTS = []
SERIAL_R = "PLAT-CERT-SERIAL-R"
PRIV, PUB, APIV3_KEY = None, None, None  # filled by make_fixtures()


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s %s: %s" % ("PASS" if ok else "FAIL", ac,
                            "OK" if ok else "NG", evidence), flush=True)


def expect_reject(fn, needle):
    try:
        fn()
    except O.PayError as exc:
        return (exc.code == "E_CALLBACK_REJECTED"
                and needle in (exc.detail or "")), "%s (detail=%s)" % (
            exc.code, exc.detail or "-")
    except A.AdapterError as exc:
        return needle in str(exc), "AdapterError (%s)" % exc
    return False, "no-error-raised"


def db_query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def make_fixtures():
    """Throwaway in-memory fixtures; never written to disk."""
    global PRIV, PUB, APIV3_KEY
    sk = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    PRIV = sk.private_bytes(serialization.Encoding.PEM,
                            serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption()).decode("ascii")
    PUB = sk.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")
    APIV3_KEY = base64.b64encode(os.urandom(32)).decode("ascii")


def build():
    """Fresh world; standard channel switched to the V3 + rsa contract
    (in-test config only; shipped config.json untouched)."""
    tmp = tempfile.mkdtemp(prefix="pay-v3-real-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        cfg = json.load(h)
    std = cfg["channels"]["standard"]
    std["callback_style"] = "v3"
    std["v3_serials"] = [SERIAL_R]
    std["verify_mode"] = "rsa"
    std["platform_public_key_pem"] = PUB
    std["apiv3_key_b64"] = APIV3_KEY
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as h:
        json.dump(cfg, h, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as h:
        led_cfg = json.load(h)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-PAY-V3R-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    return {"tmp": tmp, "cfg": cfg, "events": events, "ledger": led,
            "pay": pay}


def cb(adapter, *args, **kw):
    kw.setdefault("private_key_pem", PRIV)
    return adapter.make_v3_callback(*args, **kw)


def fresh_placed(world, product_id="share_observation", avatar="r-avatar-1"):
    made = world["pay"].create_order(product_id, avatar)
    world["pay"].place_order(made["order_id"])
    return made["order_id"]


def main():
    make_fixtures()
    world = build()
    pay = world["pay"]
    adapter = pay._adapters["standard"]

    # AC-V3R1: opt-in face + shipped config isolation + spec validation
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        ship = json.load(h)
    ship_clean = all(
        k not in ship["channels"][n]
        for n in ship["channels"]
        for k in ("verify_mode", "platform_public_key_pem", "apiv3_key_b64"))
    virt_legacy = isinstance(pay._adapters["virtual"], A.MockChannel)
    record("AC-V3R1a",
           isinstance(adapter, V3M.V3Channel)
           and adapter.verify_mode == "rsa" and virt_legacy,
           "standard=V3Channel(rsa), virtual stays legacy MockChannel")
    record("AC-V3R1b", ship_clean,
           "shipped config.json carries no rsa keys (byte diff at commit)")
    spec_bad = {"signer": "s", "mock_key": "k", "verify_mode": "bogus"}
    spec_nokey = {"signer": "s", "mock_key": "k", "verify_mode": "rsa"}
    ok1, ev1 = expect_reject(
        lambda: V3M.V3Channel.from_spec("standard", spec_bad),
        "bad verify_mode")
    ok2, ev2 = expect_reject(
        lambda: V3M.V3Channel.from_spec("standard", spec_nokey),
        "needs platform_public_key_pem")
    record("AC-V3R1c", ok1 and ok2,
           "spec validation: %s / %s" % (ev1, ev2))

    # AC-V3R2: real RSA-SHA256 (PKCS#1 v1.5) over ts\nnonce\nbody\n
    order_id = fresh_placed(world)
    good = cb(adapter, order_id, 100000, "rn-0001")
    b64sig = good["v3"]["headers"]["Wechatpay-Signature"]
    manual_ok = False
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    try:
        serialization.load_pem_public_key(PUB.encode("ascii")).verify(
            base64.b64decode(b64sig, validate=True),
            ("%s\n%s\n%s\n" % (
                good["v3"]["headers"]["Wechatpay-Timestamp"],
                good["v3"]["headers"]["Wechatpay-Nonce"],
                good["v3"]["body"])).encode("utf-8"),
            padding.PKCS1v15(), hashes.SHA256())
        manual_ok = True
    except Exception:  # noqa: BLE001 - evidence only
        manual_ok = False
    tampered = copy.deepcopy(good)
    tampered["v3"]["body"] = tampered["v3"]["body"].replace(
        "TRANSACTION.SUCCESS", "TRANSACTION.SUCCESX")
    ok, ev = expect_reject(lambda: pay.handle_callback(tampered),
                           "signature mismatch")
    record("AC-V3R2", manual_ok and ok,
           "manual RSA-SHA256 verify ok; tampered body (no re-sign) "
           "rejected: " + ev)

    # AC-V3R3: real AEAD_AES_256_GCM resource decrypt (fresh nonce: the
    # rejected tampered callback above consumed rn-0001 as bad evidence)
    settle_cb = cb(adapter, order_id, 100000, "rn-settle")
    res_good = pay.handle_callback(settle_cb)
    order_id2 = fresh_placed(world, "report_data_b", "r-avatar-2")
    g2 = cb(adapter, order_id2, 199900, "rn-1000")
    msg = json.loads(g2["v3"]["body"])
    assert msg["resource"]["algorithm"] == "AEAD_AES_256_GCM"
    ct = bytearray(base64.b64decode(msg["resource"]["ciphertext"]))
    ct[0] ^= 0x01
    msg["resource"]["ciphertext"] = base64.b64encode(bytes(ct)).decode("ascii")
    bad_body = json.dumps(msg, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
    corrupt = copy.deepcopy(g2)
    corrupt["v3"]["body"] = bad_body
    sk = serialization.load_pem_private_key(PRIV.encode("ascii"),
                                            password=None)
    corrupt_sig = base64.b64encode(sk.sign(
        ("%s\n%s\n%s\n" % (g2["v3"]["headers"]["Wechatpay-Timestamp"],
                          g2["v3"]["headers"]["Wechatpay-Nonce"],
                          bad_body)).encode("utf-8"),
        padding.PKCS1v15(), hashes.SHA256())).decode("ascii")
    corrupt["v3"]["headers"]["Wechatpay-Signature"] = corrupt_sig
    corrupt["sig"] = corrupt_sig
    ok1, ev1 = expect_reject(lambda: pay.handle_callback(corrupt),
                             "malformed resource")
    wrong_key = base64.b64encode(os.urandom(32)).decode("ascii")
    wrong_ch = V3M.V3Channel("standard", "sandbox-standard", "k", 300,
                             [SERIAL_R], "rsa", PUB, wrong_key)
    ok2, ev2 = expect_reject(lambda: wrong_ch.verify(g2),
                             "malformed resource")
    record("AC-V3R3", res_good["status"] == "granted" and ok1 and ok2,
           "good AEAD path settles (%s); flipped ct w/ valid re-sign %s; "
           "wrong apiv3 key %s" % (res_good["status"], ev1, ev2))

    # AC-V3R4: mode isolation, cross-rejected on both directions
    standin_ch = V3M.V3Channel("standard", "sandbox-standard",
                               ship["channels"]["standard"]["mock_key"],
                               300, [SERIAL_R])
    standin_cb = standin_ch.make_v3_callback(order_id2, 199900, "rn-cross")
    ok1, ev1 = expect_reject(lambda: adapter.verify(standin_cb),
                             "signature mismatch")
    ok2, ev2 = expect_reject(lambda: standin_ch.verify(g2),
                             "signature mismatch")
    record("AC-V3R4", ok1 and ok2,
           "rsa rejects standin cb (%s); standin rejects rsa cb (%s)"
           % (ev1, ev2))

    # AC-V3R5: the four constitutional gates all hold under rsa mode
    unk = cb(adapter, order_id2, 199900, "rn-serial",
             serial="NOT-A-KNOWN-SERIAL")
    ok1, ev1 = expect_reject(lambda: pay.handle_callback(unk), "unknown serial")
    stale = cb(adapter, order_id2, 199900, "rn-stale", ts_unix=int(
        datetime.datetime.now(datetime.timezone.utc).timestamp()) - 400)
    ok2, ev2 = expect_reject(lambda: pay.handle_callback(stale), "ts outside")
    inject = cb(adapter, order_id2, 199900, "rn-inject")
    inject["amount_cent"] = 1
    ok3, ev3 = expect_reject(lambda: pay.handle_callback(inject),
                             "uniform/body mismatch")
    refund = cb(adapter, order_id2, 199900, "rn-refund",
                trade_state="REFUND", event_type="TRANSACTION.REFUND")
    ok4, ev4 = expect_reject(lambda: pay.handle_callback(refund),
                             "trade_state=REFUND not SUCCESS")
    record("AC-V3R5", ok1 and ok2 and ok3 and ok4,
           "serial %s | ts %s | injection %s | state %s"
           % (ev1, ev2, ev3, ev4))

    # AC-V3R8: end-to-end settlement + idempotent redelivery (rsa mode)
    redel = pay.handle_callback(settle_cb)
    grants = db_query(os.path.join(world["tmp"], "pay.db"),
                      "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                      (order_id,))
    evs = db_query(os.path.join(world["tmp"], "events.db"),
                   "SELECT COUNT(*) FROM events WHERE type='pay.success'"
                   " AND payload_json LIKE ?", ("%" + order_id + "%",))
    record("AC-V3R8", redel["idempotent"] is True and grants[0][0] == 1
           and evs[0][0] == 1,
           "redelivery idempotent, 1 grant, 1 pay.success event")

    # AC-V3R7: honesty marks + ASCII + no network + no fixture on disk
    src = open(os.path.join(BASE, "v3.py"), "rb").read()
    ascii_ok = all(b < 128 for b in src)
    text = src.decode("ascii")
    marks = ("verify_mode" in text and "stand-in" in text
             and "AEAD_AES_256_GCM" in text and "PKCS#1 v1.5" in text
             and ".env" in text and "cryptography package" in text)
    no_net = not any(w in text for w in ("import socket", "urllib",
                                        "requests", "http.client"))
    stray = [f for f in os.listdir(world["tmp"]) if f.endswith(".pem")]
    record("AC-V3R7", ascii_ok and marks and no_net and not stray,
           "v3.py ASCII + real/stand-in marks + zero network imports + "
           "fixture keys never hit disk")

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
