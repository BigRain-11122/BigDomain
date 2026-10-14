"""Acceptance suite: pay sweep_expired timeout-close read-face family
cross-restart persistence window (BigDomain R1965, R1957 seed).

Pins the pre-registered criteria AC-SWP1..AC-SWP7 (claim row in
state/queue/tech.md, pre-registered before any suite code): the
timeout-close sweep is a durability seam - closed-by-timeout orders,
the drained-window idempotency, the closed-rebuy bucket law and the
grant read faces must all survive a close -> reopen on the same
databases byte-identically; a live sweep after the restart closes
only in-window rows while every pre-restart row stays frozen
(append-only prefix law); the read battery is pure and double-run
stable across two restarts; the suite is ascii, offline and ships
zero product changes.

Clock discipline (frozen-clock sweep reference): rows are written
on the real record clock via the public API; only the sweep reference
is explicit - FAR (2030) sweeps everything recorded before it, PAST
(2020) is the empty-window probe that must write nothing.

Usage: python test_pay_sweep_persist.py
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import orders as O                                    # noqa: E402
import adapters as A                                  # noqa: E402
from ledger import Ledger                             # noqa: E402 (ledger product)
import store as lobby_store                           # noqa: E402 (lobby product)

RESULTS = []
PROD = "share_observation"
AV_A = "AV-SWP-A"
AV_B = "AV-SWP-B"
AV_C = "AV-SWP-C"
AV_D = "AV-SWP-D"
AV_F = "AV-SWP-F"
FAR = "2030-01-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def scalar(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


def fetch_rows(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return [list(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def counts(pay_db):
    return {
        "orders": scalar(pay_db, "SELECT COUNT(*) FROM pay_orders"),
        "receipts": scalar(pay_db, "SELECT COUNT(*) FROM pay_receipts"),
        "grants": scalar(pay_db, "SELECT COUNT(*) FROM pay_grants"),
    }


def frozen_rows(pay_db):
    return {
        "orders": fetch_rows(pay_db, "SELECT * FROM pay_orders ORDER BY rowid"),
        "receipts": fetch_rows(pay_db, "SELECT * FROM pay_receipts"
                               " ORDER BY rowid"),
        "grants": fetch_rows(pay_db, "SELECT * FROM pay_grants ORDER BY rowid"),
    }


def read_battery(pay, oids, avatars):
    """Every read face, json-serialized: the byte-identity lens."""
    out = []
    for oid in oids:
        out.append(("detail:" + oid,
                    json.dumps(pay.order_detail(oid), sort_keys=True)))
    for av in avatars:
        out.append(("grants:" + av,
                    json.dumps(pay.grants_for(av), sort_keys=True)))
    return out


def battery_same(a, b):
    return (len(a) == len(b)
            and all(x[0] == y[0] and x[1] == y[1] for x, y in zip(a, b)))


def status_of(pay, oid):
    return pay.order_detail(oid)["status"]


def grant(pay, chans, avatar, nonce):
    resp = pay.create_order(PROD, avatar)
    oid = resp["order_id"]
    pay.place_order(oid)
    amount = pay.order_detail(oid)["amount_cent"]
    cb = chans[resp["channel"]].make_callback(oid, amount, nonce)
    pay.handle_callback(cb)
    return oid


def build_world():
    """Four-avatar order spectrum on the public API only: A walks the
    full grant chain (never sweepable), B stays created, C and D are
    placed (pending) - C/D ride both legal timeout-close edges."""
    tmp = tempfile.mkdtemp(prefix="pay-swp-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as handle:
        json.dump(cfg, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as handle:
        led_cfg = json.load(handle)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-SWP-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    chans = A.from_config(cfg)
    oid_a = grant(pay, chans, AV_A, "n-swp-1")
    oid_b = pay.create_order(PROD, AV_B)["order_id"]
    oid_c = pay.create_order(PROD, AV_C)["order_id"]
    pay.place_order(oid_c)
    oid_d = pay.create_order(PROD, AV_D)["order_id"]
    pay.place_order(oid_d)
    return {"tmp": tmp, "cfg": cfg, "cfg_path": cfg_path, "led_cfg": led_cfg,
            "events": events, "led": led, "pay": pay, "chans": chans,
            "oid_a": oid_a, "oid_b": oid_b, "oid_c": oid_c, "oid_d": oid_d,
            "pay_db": os.path.join(tmp, "pay.db"),
            "ledger_db": os.path.join(tmp, "ledger.db")}


def reopen(world):
    events = lobby_store.EventStore(
        os.path.join(world["tmp"], "events.db"))
    led = Ledger(world["ledger_db"], world["led_cfg"])
    pay = O.PayOrders(world["cfg"], world["pay_db"], events, led)
    return events, led, pay


def close_all(events, led, pay):
    pay.close()
    led.close()
    events.close()


def main():
    frozen = {}
    for rel in ("config.json", "orders.py", "adapters.py"):
        with open(os.path.join(BASE, rel), "rb") as handle:
            frozen[rel] = handle.read()

    world = build_world()
    try:
        oids4 = [world["oid_a"], world["oid_b"], world["oid_c"],
                 world["oid_d"]]
        avatars4 = [AV_A, AV_B, AV_C, AV_D]

        # AC-SWP1: anchor world + pre-restart sweep spectrum ----------
        c_before = counts(world["pay_db"])
        n_past = world["pay"].sweep_expired(now=PAST)
        c_past = counts(world["pay_db"])
        n_full = world["pay"].sweep_expired(now=FAR)
        n_drain = world["pay"].sweep_expired(now=FAR)
        st = {o: status_of(world["pay"], o) for o in oids4}
        ga = world["pay"].grants_for(AV_A)
        gb = world["pay"].grants_for(AV_B)["items"]
        gc = world["pay"].grants_for(AV_C)["items"]
        gd = world["pay"].grants_for(AV_D)["items"]
        ok1 = (n_past == 0 and c_past == c_before and n_full == 3
               and n_drain == 0
               and st[world["oid_a"]] == "granted"
               and st[world["oid_b"]] == "closed"
               and st[world["oid_c"]] == "closed"
               and st[world["oid_d"]] == "closed"
               and len(ga["items"]) == 1
               and ga["items"][0]["order_id"] == world["oid_a"]
               and not ga["items"][0]["refunded"]
               and gb == [] and gc == [] and gd == []
               and c_before == {"orders": 4, "receipts": 1, "grants": 1})
        record("AC-SWP1", ok1,
               "empty-window=%d full=%d drain=%d spectrum ok=%s"
               " grants A=%d B/C/D=%d/%d/%d counts=%s"
               % (n_past, n_full, n_drain,
                  st[world["oid_a"]] == "granted"
                  and st[world["oid_b"]] == "closed"
                  and st[world["oid_c"]] == "closed"
                  and st[world["oid_d"]] == "closed",
                  len(ga["items"]), len(gb), len(gc), len(gd), c_before))

        # post-sweep anchor: the state that must survive the restart
        anchor_battery = read_battery(world["pay"], oids4, avatars4)
        anchor_rows = frozen_rows(world["pay_db"])

        # AC-SWP2: close every writer, reopen, read faces identical ---
        close_all(world["events"], world["led"], world["pay"])
        ev2, led2, pay2 = reopen(world)
        battery2 = read_battery(pay2, oids4, avatars4)
        n3 = pay2.sweep_expired(now=FAR)
        ok2 = battery_same(battery2, anchor_battery) and n3 == 0
        record("AC-SWP2", ok2,
               "byte-identity=%s drained-persists=%d"
               % (battery_same(battery2, anchor_battery), n3))

        # AC-SWP3: post-restart closed-rebuy under a new bucket -------
        resp = pay2.create_order(PROD, AV_D)
        oid_d2 = resp["order_id"]
        created_ok = (oid_d2 != world["oid_d"]
                      and resp["idempotent"] is False
                      and resp["status"] == "created")
        pay2.place_order(oid_d2)
        amount2 = pay2.order_detail(oid_d2)["amount_cent"]
        cb2 = world["chans"][resp["channel"]].make_callback(
            oid_d2, amount2, "n-swp-2")
        pay2.handle_callback(cb2)
        gd2 = pay2.grants_for(AV_D)
        d1_detail = json.dumps(pay2.order_detail(world["oid_d"]),
                               sort_keys=True)
        d1_anchor = [x[1] for x in anchor_battery
                     if x[0] == "detail:" + world["oid_d"]][0]
        ok3 = (created_ok and status_of(pay2, oid_d2) == "granted"
               and len(gd2["items"]) == 1
               and gd2["items"][0]["order_id"] == oid_d2
               and not gd2["items"][0]["refunded"]
               and d1_detail == d1_anchor)
        record("AC-SWP3", ok3,
               "new-bucket id=%s created=%s granted=%s grants-D=%d"
               " old-closed-frozen=%s"
               % (oid_d2, created_ok, status_of(pay2, oid_d2) == "granted",
                  len(gd2["items"]), d1_detail == d1_anchor))

        # AC-SWP4: live sweep after restart bites only in-window rows --
        oid_f = pay2.create_order(PROD, AV_F)["order_id"]
        n_f = pay2.sweep_expired(now=FAR)
        n_f2 = pay2.sweep_expired(now=FAR)
        st2 = {o: status_of(pay2, o)
               for o in [world["oid_a"], world["oid_b"], world["oid_c"],
                         world["oid_d"], oid_d2, oid_f]}
        gf = pay2.grants_for(AV_F)["items"]
        ga2 = pay2.grants_for(AV_A)["items"]
        ok4 = (n_f == 1 and n_f2 == 0 and st2[oid_f] == "closed"
               and st2[world["oid_a"]] == "granted"
               and st2[world["oid_b"]] == "closed"
               and st2[world["oid_c"]] == "closed"
               and st2[world["oid_d"]] == "closed"
               and st2[oid_d2] == "granted"
               and gf == [] and len(ga2) == 1)
        record("AC-SWP4", ok4,
               "sweep=%d/%d F=%s others-stable=%s grants A=%d F=%d"
               % (n_f, n_f2, st2[oid_f],
                  st2[world["oid_a"]] == "granted"
                  and st2[world["oid_b"]] == "closed"
                  and st2[world["oid_c"]] == "closed"
                  and st2[world["oid_d"]] == "closed"
                  and st2[oid_d2] == "granted",
                  len(ga2), len(gf)))

        # mid-state battery: the end state the second restart must hold
        oids6 = oids4 + [oid_d2, oid_f]
        avatars5 = avatars4 + [AV_F]
        mid_battery = read_battery(pay2, oids6, avatars5)

        # AC-SWP5: frozen-prefix law after both continuations ----------
        post_rows = frozen_rows(world["pay_db"])
        pref = {
            "orders": post_rows["orders"][:len(anchor_rows["orders"])],
            "receipts": post_rows["receipts"][:len(anchor_rows["receipts"])],
            "grants": post_rows["grants"][:len(anchor_rows["grants"])],
        }
        ok5 = (pref["orders"] == anchor_rows["orders"]
               and pref["receipts"] == anchor_rows["receipts"]
               and pref["grants"] == anchor_rows["grants"]
               and len(post_rows["orders"]) == 6
               and len(post_rows["receipts"]) == 2
               and len(post_rows["grants"]) == 2)
        record("AC-SWP5", ok5,
               "prefix-frozen=%s rows orders=%d/%d receipts=%d/%d"
               " grants=%d/%d"
               % (pref["orders"] == anchor_rows["orders"]
                  and pref["receipts"] == anchor_rows["receipts"]
                  and pref["grants"] == anchor_rows["grants"],
                  len(anchor_rows["orders"]), len(post_rows["orders"]),
                  len(anchor_rows["receipts"]), len(post_rows["receipts"]),
                  len(anchor_rows["grants"]), len(post_rows["grants"])))

        # AC-SWP6: second restart + pure-read + determinism ------------
        c_mid = counts(world["pay_db"])
        close_all(ev2, led2, pay2)
        ev3, led3, pay3 = reopen(world)
        battery3 = read_battery(pay3, oids6, avatars5)
        battery3b = read_battery(pay3, oids6, avatars5)
        c_after_reads = counts(world["pay_db"])
        n_past3 = pay3.sweep_expired(now=PAST)
        c_after_probe = counts(world["pay_db"])
        ok6 = (battery_same(battery3, mid_battery)
               and battery_same(battery3, battery3b)
               and c_after_reads == c_mid and n_past3 == 0
               and c_after_probe == c_mid)
        record("AC-SWP6", ok6,
               "second-restart-identity=%s double-run=%s counts-stable=%s"
               " empty-probe=%d"
               % (battery_same(battery3, mid_battery),
                  battery_same(battery3, battery3b),
                  c_after_reads == c_mid and c_after_probe == c_mid,
                  n_past3))
        close_all(ev3, led3, pay3)
    finally:
        shutil.rmtree(world["tmp"], ignore_errors=True)

    # AC-SWP7: hygiene -----------------------------------------------
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_src = handle.read()
    own_ascii = all(ord(ch) < 128 for ch in own_src)
    net_hits = [ln.strip() for ln in own_src.splitlines()
                if ln.strip().startswith(("import ", "from "))
                and any(w in ln for w in
                        ("urllib", "requests", "socket", "http"))]
    thawed = [rel for rel, blob in frozen.items()
              if open(os.path.join(BASE, rel), "rb").read() != blob]
    record("AC-SWP7", own_ascii and not net_hits and not thawed
           and len(RESULTS) == 6,
           "ascii=%s net-imports=%s thawed=%s results-so-far=%d"
           % (own_ascii, net_hits, thawed, len(RESULTS)))

    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay sweep persist acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
