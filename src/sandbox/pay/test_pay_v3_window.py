"""Boundary-value suite for the V3 callback timestamp window (BigDomain
tech-queue item, R1678; seed = the R598 real-primitive suite on record).
Asserts the pre-registered criteria AC-V3W1..AC-V3W6
(state/queue/tech.md R1678 row, registered before this file existed;
honesty law).

The window check in v3.V3Channel.verify is `delta > self.ts_window`
with delta = abs(now - ts). AC-V33 proved a 400s-stale ts rejects
under the 300s window, but the boundary itself was never pinned - and
an unfrozen construction cannot pin it: a callback built at
now()-window is already delta==window+runtime by the time verify runs.

This suite freezes the verifier clock (a shim over the v3 module's
datetime attribute; everything else stays real) and pins:

  - inclusive boundary: delta == window exactly -> ACCEPTED, past and
    future edges, through the full constitutional-order chain
    (pending -> paid -> granted)
  - one-past: delta == window + 1 -> rejected "ts outside", both edges
  - the boundary follows the per-channel ts_window_seconds parameter
    (a 10s world and the default 300s world on the same ts values)
  - a burned nonce is not exempted by window freshness: same-nonce
    different-ts in-window replay (different receipt_id, valid fresh
    signature) hits the AC-Y4 bad-4 nonce gate
  - the same inclusive boundary under verify_mode "rsa" (real
    RSA-SHA256; throwaway fixture keys self-generated in-memory at
    runtime per the R598 law: never real platform keys, never
    persisted, zero network)

Usage: python test_pay_v3_window.py
"""

import base64
import datetime as real_dt
import json
import os
import sqlite3
import sys
import tempfile
import types as _types

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
FROZEN = 1800000000  # fixed epoch; the verifier clock is frozen anyway
RSA_BITS = 2048


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


def expect_adapter_reject(fn, needle):
    try:
        fn()
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
    """Throwaway in-memory RSA keypair + APIv3 key (R598 law: never
    real platform keys, never written to disk, zero network)."""
    sk = rsa.generate_private_key(public_exponent=65537, key_size=RSA_BITS)
    return {
        "priv": sk.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode("ascii"),
        "pub": sk.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("ascii"),
        "apiv3": base64.b64encode(os.urandom(32)).decode("ascii")}


def freeze_v3_clock(frozen_ts):
    """Deterministic verifier clock for the boundary math: v3.verify
    computes delta = abs(now - ts) against
    datetime.datetime.now(timezone.utc); freezing now() pins
    |now - ts| to exact integers. Subclass keeps every other datetime
    behavior inherited; the caller restores in finally."""
    class _FrozenDT(real_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return real_dt.datetime.fromtimestamp(
                frozen_ts, real_dt.timezone.utc)
    return _types.SimpleNamespace(datetime=_FrozenDT,
                                  timezone=real_dt.timezone)


def build(window_seconds=None, tag="pay-v3w"):
    """Fresh world; the standard channel switched to the V3 callback
    contract in-test (shipped config.json untouched). window_seconds
    overrides the channel parameter (AC-V3W3)."""
    tmp = tempfile.mkdtemp(prefix="%s-%s-" % (tag, window_seconds or 300))
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        cfg = json.load(h)
    cfg["channels"]["standard"]["callback_style"] = "v3"
    cfg["channels"]["standard"]["v3_serials"] = ["PLAT-CERT-SERIAL-W1"]
    if window_seconds is not None:
        cfg["channels"]["standard"]["ts_window_seconds"] = int(window_seconds)
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as h:
        json.dump(cfg, h, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as h:
        led_cfg = json.load(h)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000,
                     "SETTLE-PAY-V3W-%s" % (window_seconds or 300),
                     "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    return {"tmp": tmp, "cfg": cfg, "events": events, "ledger": led,
            "pay": pay}


def fresh_placed_v3_order(world, product_id, avatar):
    made = world["pay"].create_order(product_id, avatar)
    world["pay"].place_order(made["order_id"])
    return made["order_id"]


def v3cb(world, adapter, order_id, nonce, ts_unix=None):
    """Valid fresh callback for the order (amount always taken from the
    authoritative order row, never hardcoded)."""
    amount = world["pay"].order_detail(order_id)["amount_cent"]
    return adapter.make_v3_callback(order_id, amount, nonce, ts_unix=ts_unix)


def main():
    fixtures = make_fixtures()
    w300 = build(None, "pay-v3w300")
    w10 = build(10, "pay-v3w10")
    pay300, pay10 = w300["pay"], w10["pay"]
    adapter300 = pay300._adapters["standard"]
    adapter10 = pay10._adapters["standard"]
    assert isinstance(adapter300, V3M.V3Channel), "w300 not V3"
    assert isinstance(adapter10, V3M.V3Channel), "w10 not V3"

    try:
        V3M.datetime = freeze_v3_clock(FROZEN)

        # AC-V3W2 first: one-past rejects on both edges (the absorber
        # order stays pending; rejections never move state)
        rej = fresh_placed_v3_order(w300, "share_observation", "v3w-rej")
        ok_p, ev_p = expect_reject(
            lambda: pay300.handle_callback(
                v3cb(w300, adapter300, rej, "v3w-n-rej-p", FROZEN - 301)),
            "ts outside")
        ok_f, ev_f = expect_reject(
            lambda: pay300.handle_callback(
                v3cb(w300, adapter300, rej, "v3w-n-rej-f", FROZEN + 301)),
            "ts outside")
        record("AC-V3W2", ok_p and ok_f,
               "one-past (delta==W+1) rejected both edges: %s / %s"
               % (ev_p, ev_f))

        # AC-V3W1: exact boundary accepted on both edges, full chain
        a_past = fresh_placed_v3_order(w300, "share_observation",
                                       "v3w-acc-p")
        r_past = pay300.handle_callback(
            v3cb(w300, adapter300, a_past, "v3w-n-acc-p", FROZEN - 300))
        a_fut = fresh_placed_v3_order(w300, "report_data_b", "v3w-acc-f")
        r_fut = pay300.handle_callback(
            v3cb(w300, adapter300, a_fut, "v3w-n-acc-f", FROZEN + 300))
        record("AC-V3W1", r_past["status"] == "granted"
               and r_fut["status"] == "granted",
               "exact boundary (delta==W) accepted both edges, full"
               " chain: %s / %s" % (r_past["status"], r_fut["status"]))

        # AC-V3W3: the boundary follows the channel parameter
        a10 = fresh_placed_v3_order(w10, "share_observation", "v3w10-acc")
        r10 = pay10.handle_callback(
            v3cb(w10, adapter10, a10, "v3w-n-10-acc", FROZEN - 10))
        rej10 = fresh_placed_v3_order(w10, "share_observation", "v3w10-rej")
        ok10, ev10 = expect_reject(
            lambda: pay10.handle_callback(
                v3cb(w10, adapter10, rej10, "v3w-n-10-rej", FROZEN - 11)),
            "ts outside")
        a11 = fresh_placed_v3_order(w300, "share_observation", "v3w-acc-11")
        r11 = pay300.handle_callback(
            v3cb(w300, adapter300, a11, "v3w-n-acc-11", FROZEN - 11))
        record("AC-V3W3", r10["status"] == "granted" and ok10
               and r11["status"] == "granted",
               "boundary is parameterized: 10s world accepts -10s (%s),"
               " rejects -11s (%s); 300s world accepts the same -11s (%s)"
               % (r10["status"], ev10, r11["status"]))

        # AC-V3W4: burned nonce is not exempted by window freshness
        rp = fresh_placed_v3_order(w300, "share_observation", "v3w-replay")
        first = pay300.handle_callback(
            v3cb(w300, adapter300, rp, "v3w-nonce-rp", FROZEN - 200))
        ok_rp, ev_rp = expect_reject(
            lambda: pay300.handle_callback(
                v3cb(w300, adapter300, rp, "v3w-nonce-rp", FROZEN)),
            "nonce replay")
        rows = db_query(os.path.join(w300["tmp"], "pay.db"),
                        "SELECT COUNT(*) FROM pay_receipts WHERE sig_ok=0"
                        " AND nonce=?", ("v3w-nonce-rp",))
        record("AC-V3W4", first["status"] == "granted" and ok_rp
               and rows[0][0] >= 1,
               "same-nonce in-window replay (fresh ts, valid new"
               " signature, distinct receipt) rejected at the nonce"
               " gate; bad receipt row in store: %s (rows=%d)"
               % (ev_rp, rows[0][0]))

        # AC-V3W5: same inclusive boundary under the real primitive
        rsa_ch = V3M.V3Channel(
            "standard", "v3w-signer-r", "unused-in-rsa-mode",
            ts_window_seconds=300, serials=["PLAT-CERT-SERIAL-WR"],
            verify_mode="rsa", platform_public_key_pem=fixtures["pub"],
            apiv3_key=fixtures["apiv3"])
        cb_edge = rsa_ch.make_v3_callback(
            "v3w-rsa-order", 100, "v3w-n-rsa-e", ts_unix=FROZEN - 300,
            private_key_pem=fixtures["priv"])
        edge_ok = rsa_ch.verify(cb_edge) is None
        cb_past = rsa_ch.make_v3_callback(
            "v3w-rsa-order", 100, "v3w-n-rsa-p", ts_unix=FROZEN - 301,
            private_key_pem=fixtures["priv"])
        ok_rsa, ev_rsa = expect_adapter_reject(
            lambda: rsa_ch.verify(cb_past), "ts outside")
        record("AC-V3W5", edge_ok and ok_rsa,
               "rsa mode same boundary: delta==W verifies (None),"
               " delta==W+1 rejects: %s" % ev_rsa)
    finally:
        V3M.datetime = real_dt  # restore the real clock, no bleed

    # AC-V3W6: honesty face - restored clock (real-clock grant still
    # works), pure ASCII, zero network, shipped config untouched
    a_real = fresh_placed_v3_order(w300, "share_observation", "v3w-acc-real")
    r_real = pay300.handle_callback(
        v3cb(w300, adapter300, a_real, "v3w-n-real"))
    restored = V3M.datetime is real_dt and r_real["status"] == "granted"
    with open(os.path.join(BASE, "test_pay_v3_window.py"),
              "rb") as h:
        src = h.read()
    ascii_ok = all(b < 128 for b in src)
    text = src.decode("ascii")
    # zero-network face: scan the ACTUAL import statements (a whole-file
    # substring scan is self-referential here - the check line itself
    # would name the forbidden words)
    import_lines = [ln.strip() for ln in text.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    no_net = not any(w in ln for ln in import_lines
                     for w in ("socket", "urllib", "requests",
                               "http.client", "httpx", "aiohttp"))
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        shipped = json.load(h)
    cfg_untouched = "callback_style" not in json.dumps(
        shipped["channels"]["standard"])
    record("AC-V3W6", restored and ascii_ok and no_net and cfg_untouched,
           "clock restored (real-clock grant OK), suite pure ASCII,"
           " zero network, shipped config untouched")

    pay300.close()
    pay10.close()
    w300["ledger"].close()
    w10["ledger"].close()
    w300["events"].close()
    w10["events"].close()
    bad = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d/%d" % ("PASS" if not bad else "FAIL",
                               len(RESULTS) - len(bad), len(RESULTS)),
          flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
