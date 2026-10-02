"""Wiring acceptance suite for the MinorGuardFace three call-site
integration (BigDomain R939, first cut of the R937 scope-amendment
follow-up row cc76e8c; criteria AC-W1..AC-W4 were pre-registered in
the R939 backlog row before this code existed - honesty law. AC-W5
regression = the four in-register suites re-run from the R939 qa
evidence log, not from here).

WIRING_POINTS registry (minors.py):
  [0] member activate   -> check_time  (read-only window gate; the
       money gate stays single-source at the pay entry, no re-record)
  [1] pay create_order  -> check_spend (server-table amount, before
       any billing row exists)
  [2] liveroom open     -> check_live  (sec.31 minors hard ban)

Resident-id namespace: guard residents ARE census avatar ids; every
resident must be registered (adult or minor) so the guard can make
a scope call - an unknown resident refuses (fail-closed). Wired
faces with missing caller-supplied gate inputs refuse likewise.

Usage: python test_wiring.py
"""

import datetime
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_PAY = os.path.normpath(os.path.join(BASE, "..", "pay"))
_MEMBER = os.path.normpath(os.path.join(BASE, "..", "member"))
_LIVEROOM = os.path.normpath(os.path.join(BASE, "..", "liveroom"))
for _p in (_MEMBER, _PAY, _LEDGER, _LOBBY, _LIVEROOM, BASE):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import minors as MG                                # noqa: E402 (this package)
import ledger as L                                 # noqa: E402 (ledger product)
import sec_gate as SG                              # noqa: E402 (lobby product)
import store as lobby_store                        # noqa: E402 (lobby product)
import orders as pay_orders                        # noqa: E402 (pay product)
import adapters as A                               # noqa: E402 (pay product)
import member as M                                 # noqa: E402 (member product)
import liveroom as LR                              # noqa: E402 (R608 face)

RESULTS = []

_ERRS = (MG.GuardError, LR.LiveRoomError, pay_orders.PayError, M.MemberError)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_codes(fn, *codes):
    try:
        fn()
    except _ERRS as exc:
        code = getattr(exc, "code", None)
        return code in codes, "%s (detail=%s)" % (code, exc)
    return False, "no-error-raised"


def count_rows(db_path, table, where="1=1", args=()):
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute(
            "SELECT COUNT(*) FROM %s WHERE %s" % (table, where),
            args).fetchone()[0])
    finally:
        conn.close()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_guard(kid_window=(600, 900), kid_single=100000, kid_daily=100000):
    """One guard: adult amy, windowed minor kid, limitless minor nolimit.
    Limit VALUES are test-supplied (the [needs-CEO] face never gets a
    platform-invented default - minors.py law)."""
    g = MG.MinorGuardFace()
    g.register_resident("amy", False)
    g.register_resident("kid", True, "g1")
    g.register_resident("nolimit", True, "g1")
    g.set_guardian_limits("g1", "kid", allowed_windows=[kid_window],
                          single_cent=kid_single, daily_cent=kid_daily)
    return g


# -- liveroom world ---------------------------------------------------------


def build_liveroom(guard):
    tmp = tempfile.mkdtemp(prefix="wire-liveroom-")
    cfg = load_json(os.path.join(_LEDGER, "config.json"))
    led = L.Ledger(os.path.join(tmp, "ledger.db"), cfg)
    gate = SG.SecGate(cfg["gate"]["forbidden_words"],
                      cfg["gate"]["advisory_ban_words"])
    face = LR.LiveRoomFace(led, gate, cfg["token"]["disclaimer"],
                           cfg["token"]["ai_label_text"],
                           minor_guard=guard)
    legacy = LR.LiveRoomFace(L.Ledger(os.path.join(tmp, "legacy.db"), cfg),
                             gate, cfg["token"]["disclaimer"],
                             cfg["token"]["ai_label_text"])
    return {"tmp": tmp, "led": led, "face": face, "legacy": legacy,
            "db": os.path.join(tmp, "ledger.db"),
            "legacy_db": os.path.join(tmp, "legacy.db")}


def ac_w1_w2_liveroom():
    w = build_liveroom(build_guard())
    face, db = w["face"], w["db"]
    try:
        ok, ev = expect_codes(
            lambda: face.open_session("s1", "r1", True, "rc-1"),
            LR.E_LIVE_BAD_ARGS)
        record("AC-W2", ok,
               "liveroom guard wired, opener id missing -> %s" % ev)

        ok, ev = expect_codes(
            lambda: face.open_session("s1", "r1", True, "rc-1",
                                      opener_resident_id="kid"),
            "E_MG_LIVE_BAN")
        zero = count_rows(db, "live_sessions") == 0
        record("AC-W1", ok and zero,
               "minor opener refused (%s); live_sessions rows=%d"
               % (ev, count_rows(db, "live_sessions")))

        res = face.open_session("s1", "r1", True, "rc-1",
                                opener_resident_id="amy")
        record("AC-W1", res.get("attended") is True
               and count_rows(db, "live_sessions") == 1,
               "adult opener opens; rows=%d"
               % count_rows(db, "live_sessions"))

        res = w["legacy"].open_session("s9", "r1", True, "rc-1")
        record("AC-W1", res.get("session_id") == "s9"
               and count_rows(w["legacy_db"], "live_sessions") == 1,
               "legacy face (no guard) opens without opener id (unchanged)")
    finally:
        w["face"].close()
        w["legacy"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


# -- pay world --------------------------------------------------------------


def build_pay(guard):
    tmp = tempfile.mkdtemp(prefix="wire-pay-")
    cfg = load_json(os.path.join(_PAY, "config.json"))
    led_cfg = load_json(os.path.join(_LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = L.Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-WIRE-1", "settlement")
    pay = pay_orders.PayOrders(cfg, os.path.join(tmp, "pay.db"), events,
                               led, minor_guard=guard)
    legacy = pay_orders.PayOrders(cfg, os.path.join(tmp, "legacy-pay.db"),
                                  lobby_store.EventStore(
                                      os.path.join(tmp, "legacy-events.db")),
                                  L.Ledger(os.path.join(tmp, "legacy-ledger.db"),
                                           led_cfg))
    product = sorted(cfg["products"])[0]
    price = int(cfg["products"][product]["price_cent"])
    return {"tmp": tmp, "cfg": cfg, "led": led, "pay": pay, "legacy": legacy,
            "product": product, "price": price,
            "db": os.path.join(tmp, "pay.db"),
            "legacy_db": os.path.join(tmp, "legacy-pay.db")}


def ac_w2_w3_pay():
    g = build_guard()
    w = build_pay(g)
    pay, db, product, price = w["pay"], w["db"], w["product"], w["price"]
    try:
        ok, ev = expect_codes(
            lambda: pay.create_order(product, "kid"),
            pay_orders.E_BAD_STATE)
        record("AC-W2", ok,
               "pay guard wired, minor_date missing -> %s" % ev)

        ok, ev = expect_codes(
            lambda: pay.create_order(product, "nolimit", minor_date="2026-10-02"),
            "E_MG_NO_LIMIT")
        record("AC-W3", ok and count_rows(db, "pay_orders") == 0,
               "minor without limits refused (%s); zero orders" % ev)

        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=price - 1, daily_cent=price)
        ok, ev = expect_codes(
            lambda: pay.create_order(product, "kid", minor_date="2026-10-02"),
            "E_MG_SPEND_SINGLE")
        record("AC-W3", ok and count_rows(db, "pay_orders") == 0,
               "minor over single limit refused (%s); zero orders" % ev)

        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=price, daily_cent=price)
        res = pay.create_order(product, "kid", minor_date="2026-10-02")
        again = pay.create_order(product, "kid", minor_date="2026-10-02")
        record("AC-W3", res.get("status") == "created"
               and again.get("idempotent") is True
               and count_rows(db, "pay_orders") == 1,
               "minor within limits creates 1 order (replay idempotent)")

        res = pay.create_order(product, "amy", minor_date="2026-10-02")
        record("AC-W3", res.get("status") == "created"
               and count_rows(db, "pay_orders") == 2,
               "adult pass-through creates; orders=%d"
               % count_rows(db, "pay_orders"))

        ok, ev = expect_codes(
            lambda: pay.create_order(product, "stranger",
                                     minor_date="2026-10-02"),
            "E_MG_UNKNOWN")
        record("AC-W3", ok and count_rows(db, "pay_orders") == 2,
               "unregistered resident refused (%s); orders stay 2" % ev)

        res = w["legacy"].create_order(product, "amy")
        record("AC-W3", res.get("status") == "created",
               "legacy pay (no guard) creates without minor_date (unchanged)")
    finally:
        pay.close()
        w["legacy"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


# -- member world -----------------------------------------------------------


def build_member(guard):
    tmp = tempfile.mkdtemp(prefix="wire-member-")
    mcfg = load_json(os.path.join(_MEMBER, "config.json"))
    pcfg = load_json(os.path.join(_PAY, "config.json"))
    led_cfg = load_json(os.path.join(_LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = L.Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-WIRE-2", "settlement")
    pay = pay_orders.PayOrders(pcfg, os.path.join(tmp, "pay.db"), events, led)
    store = M.MemberStore(mcfg, os.path.join(tmp, "member.db"), pay,
                          minor_guard=guard)
    legacy = M.MemberStore(mcfg, os.path.join(tmp, "legacy-member.db"), pay)
    product = sorted(pcfg["products"])[0]
    return {"tmp": tmp, "led": led, "pay": pay, "store": store,
            "legacy": legacy, "chans": A.from_config(pcfg),
            "product": product,
            "db": os.path.join(tmp, "member.db"),
            "legacy_db": os.path.join(tmp, "legacy-member.db")}


def grant_for(w, avatar, nonce):
    resp = w["pay"].create_order(w["product"], avatar)
    oid = resp["order_id"]
    w["pay"].place_order(oid)
    amount = w["pay"].order_detail(oid)["amount_cent"]
    cb = w["chans"][resp["channel"]].make_callback(oid, amount, nonce)
    w["pay"].handle_callback(cb)
    items = w["pay"].grants_for(avatar)["items"]
    return items[-1]["grant_id"]


def ac_w2_w4_member():
    w = build_member(build_guard())
    store, db = w["store"], w["db"]
    try:
        g_kid = grant_for(w, "kid", "NONCE-KID-1")
        g_amy = grant_for(w, "amy", "NONCE-AMY-1")

        ok, ev = expect_codes(
            lambda: store.activate(g_kid, "kid"),
            M.E_BAD_STATE)
        record("AC-W2", ok, "member guard wired, minor_now_min missing -> %s"
               % ev)

        ok, ev = expect_codes(
            lambda: store.activate(g_kid, "kid", minor_now_min=100),
            M.E_BAD_STATE)
        record("AC-W2", ok, "member guard wired, minor_date missing -> %s"
               % ev)

        ok, ev = expect_codes(
            lambda: store.activate(g_kid, "kid", minor_now_min=100,
                                   minor_date="2026-10-02"),
            "E_MG_TIME")
        record("AC-W4", ok and count_rows(db, "member_periods",
                                         "census_avatar_id = ?",
                                         ("kid",)) == 0,
               "minor outside window refused (%s); zero periods" % ev)

        res = store.activate(g_kid, "kid", minor_now_min=700,
                             minor_date="2026-10-02")
        record("AC-W4", res.get("census_avatar_id") == "kid",
               "minor inside window activates a real grant")

        res = store.activate(g_amy, "amy", minor_now_min=100,
                             minor_date="2026-10-02")
        record("AC-W4", res.get("census_avatar_id") == "amy",
               "adult pass-through activates (guard wired)")

        res = w["legacy"].activate(g_amy, "amy")
        record("AC-W4", res.get("census_avatar_id") == "amy",
               "legacy store (no guard) activates without gate inputs"
               " (unchanged)")
    finally:
        store.close()
        w["legacy"].close()
        w["pay"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


def ac_w7_pay_grant_commit():
    """AC-W7 (pre-registered R939b, executed R940): the pay grant
    commit face books the minors day ledger exactly once per order,
    idempotent on ref, zero-record on refusal, adults untouched.

    Order ids are content-addressed by (avatar, product, bucket), so
    the two concurrent kid orders use two distinct products."""
    g = build_guard()
    w = build_pay(g)
    pay, db = w["pay"], w["db"]
    chans = A.from_config(w["cfg"])
    prods = sorted(w["cfg"]["products"])
    p1 = w["cfg"]["products"][prods[0]]["price_cent"]
    p2 = w["cfg"]["products"][prods[1]]["price_cent"]
    grant_day = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d")
    try:
        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=max(p1, p2),
                              daily_cent=p1 + p2)

        # (a) granted order books exactly one day-ledger entry (ref=oid)
        res = pay.create_order(prods[0], "kid", minor_date=grant_day)
        oid = res["order_id"]
        pay.place_order(oid)
        cb = chans[res["channel"]].make_callback(
            oid, p1, "NONCE-W7-A")
        out = pay.handle_callback(cb)
        day = g.day_readout("kid", grant_day)
        grant_rows = count_rows(db, "pay_grants", "order_id = ?", (oid,))
        record("AC-W7", out.get("status") == "granted"
               and day["spent_cent"] == p1
               and day["events"] == [oid] and grant_rows == 1,
               "granted minor order books day ledger once: spent=%d "
               "events=%s grant_rows=%d"
               % (day["spent_cent"], day["events"], grant_rows))

        # (b) ref replay (crash-window retry entry) double-records zero
        again = g.record_spend("kid", p1, grant_day, oid)
        day = g.day_readout("kid", grant_day)
        record("AC-W7", again.get("idempotent") is True
               and day["spent_cent"] == p1 and day["events"] == [oid],
               "same-ref record_spend replay is a no-op (zero double-"
               "record): spent=%d events=%s" % (day["spent_cent"],
                                                day["events"]))

        # (c) refusal at grant time records zero and rolls the grant
        res2 = pay.create_order(prods[1], "kid", minor_date=grant_day)
        oid2 = res2["order_id"]
        pay.place_order(oid2)
        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=max(p1, p2), daily_cent=p1)
        cb2 = chans[res2["channel"]].make_callback(
            oid2, p2, "NONCE-W7-C")
        ok, ev = expect_codes(lambda: pay.handle_callback(cb2), "E_MG_SPEND_DAILY")
        day = g.day_readout("kid", grant_day)
        st2 = pay.order_detail(oid2)["status"]
        record("AC-W7", ok and oid2 not in day["events"]
               and day["spent_cent"] == p1
               and count_rows(db, "pay_grants", "order_id = ?", (oid2,)) == 0
               and st2 == "paid",
               "grant-time limit refusal (%s) records zero, rolls back: "
               "spent=%d events=%s status=%s grant_rows2=%d"
               % (ev, day["spent_cent"], day["events"], st2,
                  count_rows(db, "pay_grants", "order_id = ?", (oid2,))))

        # guardian restores budget -> identical callback retries, grant
        # heals and books the one entry (paid->granted heal path)
        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=max(p1, p2),
                              daily_cent=p1 + p2)
        out2 = pay.handle_callback(cb2)
        day = g.day_readout("kid", grant_day)
        record("AC-W7", out2.get("status") == "granted" and out2.get("idempotent") is True
               and day["events"] == [oid, oid2]
               and day["spent_cent"] == p1 + p2,
               "retry heals the refused grant and books its one entry: "
               "spent=%d events=%s" % (day["spent_cent"], day["events"]))

        # (d) adult grant books nothing on the minors day ledger
        res3 = pay.create_order(prods[0], "amy", minor_date=grant_day)
        oid3 = res3["order_id"]
        pay.place_order(oid3)
        cb3 = chans[res3["channel"]].make_callback(
            oid3, p1, "NONCE-W7-D")
        out3 = pay.handle_callback(cb3)
        amy_day = g.day_readout("amy", grant_day)
        record("AC-W7", out3.get("status") == "granted"
               and amy_day["spent_cent"] == 0 and amy_day["events"] == [],
               "adult grant pass-through books no day-ledger entry "
               "(minors-only face)")
    finally:
        pay.close()
        w["legacy"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


def main():
    print("=== MinorGuard three-call-site wiring suite (R939) ===",
          flush=True)
    ac_w1_w2_liveroom()
    ac_w2_w3_pay()
    ac_w2_w4_member()
    ac_w7_pay_grant_commit()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE PASS %d/%d" % (len(RESULTS) - len(failed), len(RESULTS)),
          flush=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
