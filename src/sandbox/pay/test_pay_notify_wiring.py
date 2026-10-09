"""Acceptance suite for the orders.py notify wiring (R1706 successor).

Asserts the pre-registered criteria AC-NW1..AC-NW7 (state/queue/tech.md
R1718 claim line, registered 2026-10-10 BEFORE this code; honesty law).
Wiring law: the notify face is caller-built and caller-owned (orders.py
holds a reference only, notify=None default = shipped behavior
byte-stable); post-commit notify attempts never break a completed
payment (R1681->R1701 degraded-pipeline precedent); outcomes land in
the response envelope as evidence.

Usage: python test_pay_notify_wiring.py
"""

import os
import shutil
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import test_pay_notify as TN             # noqa: E402 (notify_cfg/raw helpers)
import notify as N                       # noqa: E402 (face, never re-built here)
import orders as O                       # noqa: E402 (wiring subject)

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


def flow(world, product_id, avatar, nonce):
    """create -> place -> valid callback. Returns (order_id, cb,
    callback envelope) - TP.happy discards the envelope, this wiring
    suite asserts on it."""
    resp = world["pay"].create_order(product_id, avatar)
    oid = resp["order_id"]
    world["pay"].place_order(oid)
    amount = world["pay"].order_detail(oid)["amount_cent"]
    cb = world["chans"][resp["channel"]].make_callback(oid, amount, nonce)
    env = world["pay"].handle_callback(cb)
    return oid, cb, env


def build_wired(cfg=None, face=None):
    """Fresh TP.build world re-opened with a wired notify face.
    Sequential single-writer: the un-wired PayOrders closes FIRST,
    then the wired one opens on the same pay.db. The face is built by
    this caller (tests own their config copy - the shipped config.json
    stays byte-stable); orders.py never builds or closes the face."""
    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")
    world["pay"].close()
    if face is None:
        if cfg is None:
            cfg = TN.notify_cfg(TP.load_pay_config())
        face = N.PayNotifyFace(cfg, os.path.join(world["tmp"],
                                                 "nwiring.db"),
                               pay_db=pay_db)
    world["pay"] = O.PayOrders(world["cfg"], pay_db, world["events"],
                               world["led"], notify=face)
    world["face"] = face
    world["pay_db"] = pay_db
    return world


def drop(world):
    """Tear that also closes the caller-owned face."""
    world["pay"].close()
    world["face"].close()
    world["led"].close()
    shutil.rmtree(world["tmp"], ignore_errors=True)


class BrokenFace(object):
    """AC-NW4 scenario 4: an unexpected notify error must never break
    the payment flow; the envelope carries the honest off:<ExcName>."""

    def notify_payment_success(self, order_id):
        raise RuntimeError("channel down")

    def notify_refund(self, order_id):
        raise RuntimeError("channel down")

    def close(self):
        pass  # face contract: caller-owned close is a no-op here


def main():
    # ---- AC-NW1: constructor contract ---------------------------------
    w0 = TP.build(mint=True)
    oid0, _, env0 = flow(w0, "pack_compute_19_9", "NW-0", "nw-0")
    key_absent = "notify" not in env0
    granted0 = w0["pay"].order_detail(oid0)["status"] == "granted"
    TP.tear(w0)

    w1 = build_wired()
    ok_ref = w1["pay"].notify is w1["face"]
    # close ownership: PayOrders.close() must NOT close the face
    w1["pay"].close()
    face_alive = True
    try:
        w1["face"].banner_queue()  # readable => still open, caller-owned
    except Exception:
        face_alive = False
    w1["face"].close()
    w1["led"].close()
    shutil.rmtree(w1["tmp"], ignore_errors=True)
    record("AC-NW1", key_absent and granted0 and ok_ref and face_alive,
           "shipped default: notify key absent=%s granted=%s; wired "
           "reference held=%s; face alive after pay.close()=%s"
           % (key_absent, granted0, ok_ref, face_alive))

    # ---- AC-NW2: _grant completion auto-notify ------------------------
    w2 = build_wired()
    w2["face"].grant_authorization("NW-2", "tpl_ok", "longterm")
    # share_observation carries share_tokens=30000: the conversion
    # bridge books (pack/birthright ship share_tokens=0 - conv_n would
    # honestly be 0 there, not a wiring defect)
    oid2, _, env2 = flow(w2, "share_observation", "NW-2", "nw-2")
    notif = env2.get("notify") or {}
    rows2 = [r for r in w2["face"].log_rows() if r[2] == oid2]
    led_db = os.path.join(w2["tmp"], "ledger.db")
    ev_db = os.path.join(w2["tmp"], "events.db")
    conv_n = TP.db_query(led_db, "SELECT COUNT(*) FROM ledger_tx WHERE ref=?"
                         " AND ref_type='order'", (oid2,))[0][0]
    ev_n = TP.db_query(ev_db, "SELECT COUNT(*) FROM events"
                        " WHERE type='pay.success' AND actor='NW-2'")[0][0]
    grant_n = TP.db_query(w2["pay_db"],
                          "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                          (oid2,))[0][0]
    ok2 = (notif.get("reason") == "payment_success"
           and notif.get("status") == "sent" and len(rows2) == 1
           and env2["status"] == "granted" and grant_n == 1
           and conv_n == 1 and ev_n == 1)
    drop(w2)
    record("AC-NW2", ok2,
           "notify=%s rows_for_order=%d status=%s grant=%d conversion=%d "
           "event=%d (payment complete, notice is post-commit evidence)"
           % (notif, len(rows2), env2.get("status"), grant_n, conv_n, ev_n))

    # ---- AC-NW3: refund close point (close_refund face) ---------------
    w3 = build_wired()
    w3["face"].grant_authorization("NW-3", "tpl_ok", "longterm")
    oid3, _, env3 = flow(w3, "pack_compute_19_9", "NW-3", "nw-3")
    closed = w3["pay"].close_refund(oid3)
    notif3 = closed.get("notify") or {}
    rows3 = [r for r in w3["face"].log_rows() if r[2] == oid3]
    # fail-closed face states (zero writes on every refusal)
    oid3_created = w3["pay"].create_order("pack_compute_19_9",
                                          "NW-3b")["order_id"]  # stays created
    oid3_timeout = w3["pay"].create_order("pack_compute_19_9",
                                          "NW-3c")["order_id"]
    TN.raw_set_status(w3["pay_db"], oid3_timeout, "closed")  # timeout close
    e_unk = expect_pay_error(lambda: w3["pay"].close_refund("no-such"),
                             O.E_UNKNOWN_ORDER)
    e_created = expect_pay_error(lambda: w3["pay"].close_refund(oid3_created),
                                 O.E_BAD_STATE)
    e_timeout = expect_pay_error(lambda: w3["pay"].close_refund(oid3_timeout),
                                 O.E_BAD_STATE)  # no grant row: no face pass
    e_again = expect_pay_error(lambda: w3["pay"].close_refund(oid3),
                               O.E_BAD_STATE)  # closed is absorbing
    ok3 = (closed["status"] == "closed"
           and notif3.get("reason") == "refund"
           and notif3.get("status") == "sent" and len(rows3) == 2
           and e_unk[0] and e_created[0] and e_timeout[0] and e_again[0]
           and w3["pay"].order_detail(oid3)["status"] == "closed")
    drop(w3)
    record("AC-NW3", ok3,
           "close_refund: status=%s notify=%s rows=%d (success+refund); "
           "unknown=%s created=%s timeout-close=%s re-close=%s"
           % (closed.get("status"), notif3, len(rows3), e_unk[0],
              e_created[0], e_timeout[0], e_again[0]))

    # ---- AC-NW4: degradation trio never breaks the payment ------------
    # (a) honest pending state: shipped default templates approved=0
    w4a = build_wired(cfg=TP.load_pay_config())
    oid4a, _, env4a = flow(w4a, "pack_compute_19_9", "NW-4a", "nw-4a")
    notif4a = env4a.get("notify") or {}
    rows4a = len(w4a["face"].log_rows())
    oka = (notif4a.get("status") == "template_not_approved"
           and rows4a == 0
           and w4a["pay"].order_detail(oid4a)["status"] == "granted")
    drop(w4a)
    # (b) daily-cap breach: payment stands, skipped row lands (banner)
    w4b = build_wired(cfg=TN.notify_cfg(TP.load_pay_config(), cap=1))
    w4b["face"].grant_authorization("NW-4b1", "tpl_ok", "longterm")
    w4b["face"].grant_authorization("NW-4b2", "tpl_ok", "longterm")
    _, _, env4b1 = flow(w4b, "pack_compute_19_9", "NW-4b1", "nw-4b1")
    oid4b2, _, env4b2 = flow(w4b, "pack_compute_19_9", "NW-4b2", "nw-4b2")
    notif4b2 = env4b2.get("notify") or {}
    banner4b = len(w4b["face"].banner_queue())
    okb = (env4b1.get("notify", {}).get("status") == "sent"
           and notif4b2.get("status") == "skipped_daily_cap"
           and banner4b == 1
           and w4b["pay"].order_detail(oid4b2)["status"] == "granted")
    drop(w4b)
    # (c) broken face: unexpected error -> off:<ExcName>, zero breakage
    w4c = build_wired(face=BrokenFace())
    oid4c, _, env4c = flow(w4c, "pack_compute_19_9", "NW-4c", "nw-4c")
    notif4c = env4c.get("notify") or {}
    okc = (notif4c.get("status") == "off:RuntimeError"
           and w4c["pay"].order_detail(oid4c)["status"] == "granted"
           and TP.db_query(w4c["pay_db"],
                           "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                           (oid4c,))[0][0] == 1)
    drop(w4c)
    record("AC-NW4", oka and okb and okc,
           "pending-state=%s rows=%d; cap-breach=%s banner=%d; "
           "broken-face=%s grant stands"
           % (notif4a.get("status"), rows4a, notif4b2.get("status"),
              banner4b, notif4c.get("status")))

    # ---- AC-NW5: refund notice e2e + redelivery zero re-notify --------
    w5 = build_wired()
    w5["face"].grant_authorization("NW-5", "tpl_ok", "longterm")
    oid5a, _, _ = flow(w5, "pack_compute_19_9", "NW-5", "nw-5a")
    closed5 = w5["pay"].close_refund(oid5a)
    notif5 = closed5.get("notify") or {}
    rows5_after_refund = len(w5["face"].log_rows())   # success + refund
    oid5b, cb5b, _ = flow(w5, "birthright_entry", "NW-5", "nw-5b")
    rows5_second = len(w5["face"].log_rows())         # + second success
    replay5 = w5["pay"].handle_callback(cb5b)          # granted redelivery
    rows5_final = len(w5["face"].log_rows())
    ok5 = (notif5.get("reason") == "refund" and notif5.get("status") == "sent"
           and rows5_after_refund == 2 and rows5_second == 3
           and replay5.get("idempotent")
           and "notify" not in replay5 and rows5_final == 3)
    drop(w5)
    record("AC-NW5", ok5,
           "refund notify=%s rows 1->%d; second grant ->%d; redelivery "
           "idempotent=%s notify-key absent=%s rows unchanged=%d==%d"
           % (notif5.get("status"), rows5_after_refund, rows5_second,
              replay5.get("idempotent"), "notify" not in replay5,
              rows5_second, rows5_final))

    # ---- AC-NW6: crash-window heal carries the notify ------------------
    w6 = build_wired()
    w6["face"].grant_authorization("NW-6", "tpl_ok", "longterm")
    resp6 = w6["pay"].create_order("pack_compute_19_9", "NW-6")
    oid6 = resp6["order_id"]
    w6["pay"].place_order(oid6)
    amount6 = w6["pay"].order_detail(oid6)["amount_cent"]
    cb6 = w6["chans"][resp6["channel"]].make_callback(oid6, amount6, "nw-6")
    # fixture: crash between the receipt+paid commit and the grant
    # commit - raw receipt row (sig_ok=1) + legal pending->paid edge
    rid6 = O.compute_receipt_id(cb6)
    conn = sqlite3.connect(w6["pay_db"])
    conn.execute(
        "INSERT INTO pay_receipts (receipt_id, order_id, signer, nonce,"
        " amount_cent, sig_ok, verified_utc) VALUES (?,?,?,?,?,1,?)",
        (rid6, oid6, cb6["signer"], cb6["nonce"], cb6["amount_cent"],
         "2026-01-01T00:00:00Z"))
    conn.commit()
    conn.close()
    TN.raw_set_status(w6["pay_db"], oid6, "paid")
    heal6 = w6["pay"].handle_callback(cb6)
    notif6 = heal6.get("notify") or {}
    rows6 = [r for r in w6["face"].log_rows() if r[2] == oid6]
    grant6 = TP.db_query(w6["pay_db"],
                         "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                         (oid6,))[0][0]
    ok6 = (heal6.get("idempotent") and heal6.get("status") == "granted"
           and notif6.get("reason") == "payment_success"
           and notif6.get("status") == "sent" and len(rows6) == 1
           and grant6 == 1)
    drop(w6)
    record("AC-NW6", ok6,
           "heal: status=%s idempotent=%s notify=%s rows=%d grant=%d"
           % (heal6.get("status"), heal6.get("idempotent"), notif6,
              len(rows6), grant6))

    # ---- AC-NW7: hygiene self-scan ------------------------------------
    src_path = os.path.join(BASE, "orders.py")
    with open(src_path, "rb") as handle:
        raw = handle.read()
    ok_ascii = all(b < 128 for b in raw)
    import_lines = [ln.strip() for ln in raw.decode("ascii", "replace")
                    .splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in
                       ("urllib", "requests", "socket", "http"))]
    ok7 = ok_ascii and not net_hits
    record("AC-NW7", ok7,
           "orders.py ascii=%s net-imports=%s (imports: %s)"
           % (ok_ascii, net_hits or "none", "; ".join(import_lines) or "none"))

    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay-notify-wiring acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
