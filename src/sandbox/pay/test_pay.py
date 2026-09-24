"""Acceptance suite for the pay order domain sandbox (BigDomain P-47-4b).

Asserts the pre-registered criteria AC-Y1..AC-Y14 from
docs/spec/payment-integration-spec.md section 1. Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage: python test_pay.py
"""

import datetime
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import orders as O                                    # noqa: E402
import adapters as A                                  # noqa: E402
import reconcile as RC                                # noqa: E402
from ledger import Ledger, LedgerError                # noqa: E402 (ledger product)
from sec_gate import GateOfflineError                 # noqa: E402 (lobby product)
import store as lobby_store                           # noqa: E402 (lobby product)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_code(fn, *codes):
    """Run fn; return (ok, evidence) for a PayError/LedgerError/GateOffline
    whose code is in codes."""
    try:
        fn()
    except (O.PayError, LedgerError) as exc:
        return exc.code in codes, "%s (detail=%s)" % (exc.code, exc.detail or "-")
    except GateOfflineError as exc:
        return ("E_GATE_OFFLINE" in codes), "E_GATE_OFFLINE: %s" % exc
    return False, "no-error-raised"


def raw_sql(db_path, sql, args=()):
    """Execute raw SQL; return None on success or the error string."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql, args)
        conn.commit()
        return None
    except sqlite3.Error as exc:
        return str(exc)
    finally:
        conn.close()


def db_query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def run_cli(script, args_list):
    proc = subprocess.run([sys.executable, os.path.join(BASE, script)] + args_list,
                          capture_output=True, text=True, encoding="utf-8",
                          timeout=180, cwd=BASE)
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def load_pay_config():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        return json.load(handle)


def build(mint=True, cfg_mutator=None):
    """One fresh world: tmp dirs + pay config file + lobby event store +
    ledger (optionally funded) + PayOrders instance."""
    tmp = tempfile.mkdtemp(prefix="pay-ac-")
    cfg = load_pay_config()
    if cfg_mutator:
        cfg = cfg_mutator(json.loads(json.dumps(cfg)))
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as handle:
        json.dump(cfg, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as handle:
        led_cfg = json.load(handle)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    if mint:
        led.mint_to_pool("pool:share", 1000000, "SETTLE-PAY-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    return {"tmp": tmp, "cfg": cfg, "cfg_path": cfg_path, "events": events,
            "led": led, "pay": pay, "chans": A.from_config(cfg)}


def tear(world):
    world["pay"].close()
    world["led"].close()
    shutil.rmtree(world["tmp"], ignore_errors=True)


def happy(world, product_id, avatar, demand=None, nonce="n-1"):
    """create -> place -> valid callback -> granted. Returns (order_id, cb)."""
    resp = world["pay"].create_order(product_id, avatar, demand_text=demand)
    oid = resp["order_id"]
    world["pay"].place_order(oid)
    amount = world["pay"].order_detail(oid)["amount_cent"]
    cb = world["chans"][resp["channel"]].make_callback(oid, amount, nonce)
    world["pay"].handle_callback(cb)
    return oid, cb


def fresh_granted():
    """Tamper base world: one granted order + one order still created."""
    world = build()
    happy(world, "pack_compute_19_9", "AV-200", nonce="n-t")
    world["pay"].create_order("pack_compute_19_9", "AV-201")  # stays created
    return world


def main():
    # -- shared world for the single-world criteria ------------------------
    w = build()
    try:
        pay, chans = w["pay"], w["chans"]
        pay_db = os.path.join(w["tmp"], "pay.db")
        led_db = os.path.join(w["tmp"], "ledger.db")
        ev_db = os.path.join(w["tmp"], "events.db")

        # AC-Y13 first (cheap): avatar binding + grants query face
        ok_nobind, ev_nobind = expect_code(
            lambda: pay.create_order("pack_compute_19_9", ""), O.E_NO_BINDING)
        count = db_query(pay_db, "SELECT COUNT(*) FROM pay_orders")[0][0]
        oid_birth, _ = happy(w, "birthright_entry", "AV-900", nonce="n-b")
        grants = pay.grants_for("AV-900")
        record("AC-Y13", ok_nobind and count == 0 and grants["items"]
               and grants["items"][0]["entitlement"] == "birthright",
               "unbound create rejected=%s rows=%d birthright grant=%s"
               % (ok_nobind, count,
                  grants["items"][0]["entitlement"] if grants["items"] else "none"))

        # AC-Y1: state machine edges + amount lock (library-trigger law)
        r1 = pay.create_order("pack_compute_19_9", "AV-101")
        oid1 = r1["order_id"]
        pay.place_order(oid1)                      # pending
        errs = {}
        errs["skip"] = raw_sql(pay_db,
                               "UPDATE pay_orders SET status='granted' WHERE order_id=?",
                               (oid1,))
        errs["revert"] = raw_sql(pay_db,
                                 "UPDATE pay_orders SET status='created' WHERE order_id=?",
                                 (oid1,))
        errs["amount"] = raw_sql(pay_db,
                                 "UPDATE pay_orders SET amount_cent=1 WHERE order_id=?",
                                 (oid1,))
        oid_c, _ = happy(w, "pack_compute_19_9", "AV-102", nonce="n-c")  # legal walk
        errs["terminal"] = raw_sql(pay_db,
                                   "UPDATE pay_orders SET status='pending' WHERE order_id=?",
                                   (oid_c,))
        closed_n = pay.sweep_expired(now="2030-01-01T00:00:00Z")  # oid1 pending->closed
        errs["absorbing"] = raw_sql(pay_db,
                                    "UPDATE pay_orders SET status='pending' WHERE order_id=?",
                                    (oid1,))
        record("AC-Y1",
               all(v and "E_BAD_TRANSITION" in v for k, v in errs.items() if k != "amount")
               and errs["amount"] and "E_AMOUNT_LOCKED" in errs["amount"]
               and closed_n >= 1,
               "skip=%s revert=%s terminal=%s closed-absorbing=%s amount=%s"
               % (errs["skip"] and "REJ" or "NO", errs["revert"] and "REJ" or "NO",
                  errs["terminal"] and "REJ" or "NO", errs["absorbing"] and "REJ" or "NO",
                  errs["amount"]))

        # AC-Y2: server-side pricing law
        ok_taint, ev_taint = expect_code(
            lambda: pay.create_order("pack_compute_19_9", "AV-103",
                                     client_amount_cent=1990), O.E_PRICE_TAINTED)
        ok_unknown, ev_unknown = expect_code(
            lambda: pay.create_order("no_such_product", "AV-103"), O.E_PRODUCT_UNKNOWN)
        server_price = pay.order_detail(oid1)["amount_cent"]
        want_price = w["cfg"]["products"]["pack_compute_19_9"]["price_cent"]
        record("AC-Y2", ok_taint and ok_unknown and server_price == want_price,
               "tainted=%s unknown=%s server_price=%d==price_table"
               % (ev_taint, ev_unknown, server_price))

        # AC-Y3: content-addressed order id + bucket idempotence
        a1 = pay.create_order("report_data_b", "AV-104")
        a2 = pay.create_order("report_data_b", "AV-104")
        n_orders = db_query(pay_db, "SELECT COUNT(*) FROM pay_orders WHERE"
                            " census_avatar_id='AV-104' AND product_id='report_data_b'"
                            )[0][0]
        pay.sweep_expired(now="2030-01-01T00:00:00Z")   # closes the active bucket
        a3 = pay.create_order("report_data_b", "AV-104")
        record("AC-Y3", a1["order_id"] == a2["order_id"] and n_orders == 1
               and a2["idempotent"] and a3["order_id"] != a1["order_id"],
               "replay same id=%s rows=%d; closed re-buy new bucket=%s"
               % (a1["order_id"] == a2["order_id"], n_orders,
                  a3["order_id"] != a1["order_id"]))

        # AC-Y4: four bads + price injection = reject, zero state migration
        r4 = pay.create_order("pack_compute_19_9", "AV-105")
        oid4 = r4["order_id"]
        pay.place_order(oid4)
        amount4 = pay.order_detail(oid4)["amount_cent"]
        virt = chans["virtual"]
        bad_sig = virt.make_callback(oid4, amount4, "n-bad1")
        bad_sig["sig"] = "deadbeef"
        ok1, ev1 = expect_code(lambda: pay.handle_callback(bad_sig), O.E_CALLBACK_REJECTED)
        bad_signer = virt.make_callback(oid4, amount4, "n-bad2", signer="rogue-gateway")
        ok2, ev2 = expect_code(lambda: pay.handle_callback(bad_signer),
                               O.E_CALLBACK_REJECTED)
        stale = (datetime.datetime.now(datetime.timezone.utc)
                 - datetime.timedelta(seconds=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        bad_ts = virt.make_callback(oid4, amount4, "n-bad3", ts_utc=stale)
        ok3, ev3 = expect_code(lambda: pay.handle_callback(bad_ts), O.E_CALLBACK_REJECTED)
        bad_nonce = virt.make_callback(oid4, amount4, "n-bad1")  # nonce burned by bad #1
        ok4, ev4 = expect_code(lambda: pay.handle_callback(bad_nonce),
                               O.E_CALLBACK_REJECTED)
        bad_price = virt.make_callback(oid4, amount4 + 7, "n-bad5")
        ok5, ev5 = expect_code(lambda: pay.handle_callback(bad_price), O.E_AMOUNT_MISMATCH)
        st = pay.order_detail(oid4)["status"]
        grants_n = db_query(pay_db, "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                            (oid4,))[0][0]
        pay.handle_callback(virt.make_callback(oid4, amount4, "n-good4"))
        record("AC-Y4", ok1 and ok2 and ok3 and ok4 and ok5
               and st == "pending" and grants_n == 0
               and pay.order_detail(oid4)["status"] == "granted",
               "bad_sig=%s bad_signer=%s bad_ts=%s nonce_replay=%s price=%s;"
               " status stayed %s, grants=%d, good cb then granted=%s"
               % (ev1.split(" (")[0], ev2.split(" (")[0], ev3.split(" (")[0],
                  ev4.split(" (")[0], ev5.split(" (")[0], st, grants_n,
                  pay.order_detail(oid4)["status"] == "granted"))

        # AC-Y5: idempotent redelivery, single effect everywhere
        oid5, cb5 = happy(w, "share_observation", "AV-106", nonce="n-y5")
        again = pay.handle_callback(cb5)
        conv_n = db_query(led_db, "SELECT COUNT(*) FROM ledger_tx WHERE ref=?"
                          " AND ref_type='order'", (oid5,))[0][0]
        ev_n = db_query(ev_db, "SELECT COUNT(*) FROM events WHERE type='pay.success'"
                        " AND actor='AV-106'")[0][0]
        grant_n = db_query(pay_db, "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                           (oid5,))[0][0]
        cb5b = chans["standard"].make_callback(oid5, 100000, "n-y5-other")
        ok_dup, ev_dup = expect_code(lambda: pay.handle_callback(cb5b), O.E_BAD_STATE)
        record("AC-Y5", again.get("idempotent") and conv_n == 1 and ev_n == 1
               and grant_n == 1 and ok_dup,
               "redelivery idempotent=%s conversion=%d event=%d grant=%d;"
               " second distinct valid receipt rejected=%s"
               % (again.get("idempotent"), conv_n, ev_n, grant_n, ev_dup))

        # AC-Y7: fiat/token domain isolation (cross-piece with the ledger)
        rows = db_query(led_db, "SELECT t.type, t.action, e.account_id, e.amount"
                        " FROM ledger_tx t JOIN ledger_entries e ON e.tx_id=t.tx_id"
                        " WHERE t.ref=? AND t.ref_type='order' AND e.direction='credit'",
                        (oid5,))
        fiat_cols = []
        for table in ("ledger_accounts", "gate_events", "ledger_tx", "ledger_entries"):
            fiat_cols += ["%s.%s" % (table, r[1]) for r in
                          db_query(led_db, "PRAGMA table_info(%s)" % table)
                          if r[1].lower() in RC._FIAT_COLUMNS]
        inject = raw_sql(led_db, "INSERT INTO ledger_tx (tx_id, type, action, ref,"
                         " ref_type, source_ai, memo, closed, ts_utc, amount_cent)"
                         " VALUES ('x1','share','pay_conversion','r','order',0,NULL,1,"
                         "'2026-09-24T00:00:00Z',1990)")
        record("AC-Y7",
               rows and rows[0][0] == "share" and rows[0][2] == "usr:AV-106"
               and rows[0][3] == 30000 and not fiat_cols
               and bool(inject) and "amount_cent" in inject,
               "conversion share credits usr:AV-106 +%d tokens; fiat columns=%s;"
               " fiat-field injection into ledger rejected: %s"
               % (rows[0][3] if rows else -1, fiat_cols or "none", inject))

        # AC-Y8: demand-text content gate (lobby product, same origin);
        # wordlist strings load from the config data file (encoding law)
        gate_words = w["cfg"]["gate"]
        ok_g1, ev_g1 = expect_code(lambda: pay.create_order(
            "pack_compute_19_9", "AV-107", demand_text=gate_words["forbidden_words"][0]),
            O.E_CONTENT_REJECTED)
        ok_g2, ev_g2 = expect_code(lambda: pay.create_order(
            "pack_compute_19_9", "AV-107", demand_text=gate_words["advisory_ban_words"][0]),
            O.E_CONTENT_REJECTED)
        ok_g3 = pay.create_order("pack_compute_19_9", "AV-107",
                                 demand_text="verify the backtest display"
                                 )["status"] == "created"
        n107 = db_query(pay_db, "SELECT COUNT(*) FROM pay_orders WHERE"
                        " census_avatar_id='AV-107'")[0][0]
        record("AC-Y8", ok_g1 and ok_g2 and ok_g3 and n107 == 1,
               "gate1=%s gate2=%s clean=%s rows_after_rejections=%d"
               % (ev_g1.split(" (")[0], ev_g2.split(" (")[0], ok_g3, n107))

        # AC-Y9 + AC-Y10: fixed ai_service marker + resident disclaimer
        r9 = pay.create_order("pack_compute_19_9", "AV-108", client_ai_service=0)
        oid9 = r9["order_id"]
        p9 = pay.place_order(oid9)
        d9 = pay.order_detail(oid9)
        cb9 = chans["virtual"].make_callback(oid9, d9["amount_cent"], "n-y9")
        ack9 = pay.handle_callback(cb9)
        want_disc = w["cfg"]["compliance"]["disclaimer"]
        record("AC-Y9",
               r9["ai_service"] == 1 and p9["ai_service"] == 1
               and d9["ai_service"] == 1 and ack9["ai_service"] == 1,
               "client hint ai_service=0 ignored; four faces all carry ai_service=1")
        record("AC-Y10",
               r9["disclaimer"] == want_disc and p9["disclaimer"] == want_disc
               and d9["disclaimer"] == want_disc and ack9["disclaimer"] == want_disc
               and r9["persistent"] is True,
               "confirm/detail/receipt faces all carry the resident disclaimer")

        # AC-Y14: pay.success public stream dialect
        ev = db_query(ev_db, "SELECT evt_id, ts_utc, type, actor, repo, zone, summary"
                      " FROM events WHERE type='pay.success' AND actor='AV-106'")
        evt_fields_ok = (bool(ev) and all(ev[0][i] for i in range(7))
                         and ev[0][4] == "domain/BigDomain" and ev[0][5] == "pay")
        dup_err = None
        try:
            g_utc = db_query(pay_db, "SELECT granted_utc FROM pay_grants WHERE"
                             " order_id=?", (oid5,))[0][0]
            w["events"].append(g_utc, "pay.success", "AV-106", "pay", ev[0][6],
                               {"order_id": oid5, "product_id": "share_observation",
                                "channel": "standard", "share_tokens": 30000})
        except sqlite3.IntegrityError as exc:
            dup_err = str(exc)
        record("AC-Y14", evt_fields_ok and bool(dup_err) and "UNIQUE" in dup_err,
               "six fields + evt_id=%s repo/zone ok; duplicate evt_id rejected=%s"
               % (ev[0][0][:12] + "..." if ev else "none", bool(dup_err)))

        # AC-Y12 (clean): reconcile six checks green on this world
        code, out, err = run_cli("reconcile.py", [pay_db, w["cfg_path"], led_db])
        record("AC-Y12-clean", code == 0 and "PASS" in out,
               "reconcile exit=%d line1=%s"
               % (code, out.splitlines()[0] if out else err))
    finally:
        tear(w)

    # AC-Y12 (tamper): four injection families, fresh world per case -----
    tamps = {}
    names = ("amount", "grant", "receipt", "phantom")
    for name in names:
        ww = fresh_granted()
        try:
            pdb = os.path.join(ww["tmp"], "pay.db")
            ldb = os.path.join(ww["tmp"], "ledger.db")
            if name == "amount":
                raw_sql(pdb, "DROP TRIGGER trg_order_amount_lock")
                raw_sql(pdb, "UPDATE pay_orders SET amount_cent = amount_cent + 7")
            elif name == "grant":
                raw_sql(pdb, "INSERT INTO pay_grants (grant_id, order_id,"
                        " census_avatar_id, entitlement, granted_utc) VALUES ('g-fake',"
                        " (SELECT order_id FROM pay_orders WHERE status <> 'granted'"
                        " LIMIT 1), 'AV-999', 'fake', '2026-09-24T00:00:00Z')")
            elif name == "receipt":
                raw_sql(pdb, "DELETE FROM pay_receipts WHERE sig_ok = 1")
            else:  # phantom conversion entry via the ledger dock itself
                ww["led"].share_from_pool("pool:share", "usr:ghost", 55,
                                          "ORDBOGUS", "order", "pay_conversion")
            code, out, err = run_cli("reconcile.py", [pdb, ww["cfg_path"], ldb])
            tamps[name] = (code == 2 and name in out.replace("_match", "")
                           .replace("conversion", "phantom"))
            if not tamps[name]:
                print("  tamper %s: rc=%d out=%r err=%r" % (name, code, out, err))
        finally:
            tear(ww)
    record("AC-Y12-tamper", all(tamps.get(n) for n in names),
           "amount=%s grant=%s receipt=%s phantom=%s (all exit 2, named check fails)"
           % (tamps.get("amount"), tamps.get("grant"),
              tamps.get("receipt"), tamps.get("phantom")))

    # AC-Y6: grant atomicity + retry heal (conversion pool unfunded) -------
    w6 = build(mint=False)
    try:
        pay6 = w6["pay"]
        r6 = pay6.create_order("share_observation", "AV-300")
        oid6 = r6["order_id"]
        pay6.place_order(oid6)
        amount6 = pay6.order_detail(oid6)["amount_cent"]
        cb6 = w6["chans"]["standard"].make_callback(oid6, amount6, "n-y6")
        ok_fail, ev_fail = expect_code(lambda: pay6.handle_callback(cb6),
                                       "E_NEGATIVE_BALANCE")
        pdb6 = os.path.join(w6["tmp"], "pay.db")
        st6 = db_query(pdb6, "SELECT status FROM pay_orders WHERE order_id=?",
                       (oid6,))[0][0]
        g6 = db_query(pdb6, "SELECT COUNT(*) FROM pay_grants")[0][0]
        c6 = db_query(os.path.join(w6["tmp"], "ledger.db"),
                      "SELECT COUNT(*) FROM ledger_tx WHERE ref_type='order'")[0][0]
        w6["led"].mint_to_pool("pool:share", 100000, "SETTLE-HEAL", "settlement")
        heal = pay6.handle_callback(cb6)  # idempotent replay = the grant retry entry
        record("AC-Y6", ok_fail and st6 == "paid" and g6 == 0 and c6 == 0
               and heal.get("idempotent") and heal.get("status") == "granted",
               "mid-grant ledger failure (%s) rolled back whole grant:"
               " status=%s grants=%d conversions=%d; retry healed to granted=%s"
               % (ev_fail.split(" (")[0], st6, g6, c6, heal.get("status")))
    finally:
        tear(w6)

    # AC-Y11: banned product copy = config refused, product never listed;
    # the banned word loads from the config data file (encoding law) ------
    banned_word = load_pay_config()["copy_ban_words"][0]

    def add_banned(cfg):
        cfg["products"]["rogue_pack"] = {
            "channel": "virtual", "price_cent": 1990, "share_tokens": 0,
            "entitlement": "rogue", "copy": banned_word + " pack"}
        return cfg

    bad_dir = tempfile.mkdtemp(prefix="pay-ban-")
    ok11, ev11 = expect_code(lambda: O.PayOrders(
        add_banned(load_pay_config()), os.path.join(bad_dir, "pay.db"), None, None),
        "E_GATE_OFFLINE")
    listed = not os.path.exists(os.path.join(bad_dir, "pay.db"))
    shutil.rmtree(bad_dir, ignore_errors=True)
    record("AC-Y11", ok11 and "AC-Y11" in ev11 and listed,
           "banned copy refuses construction (%s); nothing listed on disk=%s"
           % (ev11, listed))

    # CLI readiness: rc0 on good config, rc2 on unwired-gate config --------
    tmp_cli = tempfile.mkdtemp(prefix="pay-cli-")
    code0, out0, err0 = run_cli("orders.py",
                                ["--config", os.path.join(BASE, "config.json"),
                                 "--db", os.path.join(tmp_cli, "pay.db"),
                                 "--events-db", os.path.join(tmp_cli, "events.db"),
                                 "--ledger-db", os.path.join(tmp_cli, "ledger.db")])
    bad_cfg = {"products": {"x": {"channel": "virtual", "price_cent": 1,
                                 "share_tokens": 0, "entitlement": "x", "copy": "x"}}}
    bad_path = os.path.join(tmp_cli, "bad-config.json")
    with open(bad_path, "w", encoding="utf-8") as handle:
        json.dump(bad_cfg, handle)
    code2, out2, err2 = run_cli("orders.py",
                                ["--config", bad_path,
                                 "--db", os.path.join(tmp_cli, "p2.db"),
                                 "--events-db", os.path.join(tmp_cli, "e2.db"),
                                 "--ledger-db", os.path.join(tmp_cli, "l2.db")])
    record("CLI", code0 == 0 and "ready" in out0 and code2 == 2
           and "E_GATE_OFFLINE" in err2,
           "readiness rc=%d (%s); unwired-gate rc=%d (%s)"
           % (code0, out0.splitlines()[0] if out0 else "-", code2,
              err2.splitlines()[0] if err2 else "-"))
    shutil.rmtree(tmp_cli, ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay acceptance: %d/%d passed" % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
