"""Acceptance suite for the payment-state notification face sandbox.

Asserts the pre-registered criteria AC-PN1..AC-PN7 (state/queue/tech.md
R1706 claim line, registered before this code; honesty law). Each
criterion prints PASS/FAIL with evidence; non-zero exit on any FAIL.

Usage: python test_pay_notify.py
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse, not copy)
import notify as N                      # noqa: E402

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_raise(fn, *code_fragments):
    """Run fn; return (ok, evidence) when it raises ValueError carrying
    every code fragment in its message (zero-row fail-closed family;
    TemplateNotApproved is a ValueError subclass)."""
    try:
        fn()
    except ValueError as exc:
        msg = str(exc)
        missing = [c for c in code_fragments if c not in msg]
        return not missing, msg
    return False, "no-error-raised"


def notify_cfg(base_cfg, cap=None, approved=True, reason_map=None,
               templates=None, disclaimer=None):
    """Deep-copied shipped pay config with a notify node (tests own
    their config copy; the shipped file stays byte-stable)."""
    cfg = json.loads(json.dumps(base_cfg))
    if disclaimer is not None:
        cfg["compliance"]["disclaimer"] = disclaimer
    tpls = templates if templates is not None else {
        "tpl_ok": {"approved": approved, "copy": "order state notice"},
    }
    node = {"daily_send_cap": 3000000 if cap is None else cap,
            "templates": tpls}
    if reason_map:
        node["reason_templates"] = reason_map
    cfg["notify"] = node
    return cfg


def row_count(face):
    return len(face.log_rows())


def raw_set_status(pay_db, order_id, status):
    """Fixture manipulation: legal-edge status move straight on pay.db
    (trigger T1 validates granted->closed / created->closed)."""
    conn = sqlite3.connect(pay_db)
    try:
        conn.execute("UPDATE pay_orders SET status=? WHERE order_id=?",
                      (status, order_id))
        conn.commit()
    finally:
        conn.close()


def main():
    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")
    # fixture: six orders across the state space (same avatar reaches
    # a second granted order through a second product - order ids are
    # content-addressed per avatar+product+bucket, one active per pair)
    oid_ok1, _ = TP.happy(world, "pack_compute_19_9", "AV-1", nonce="pn-1")
    oid_ok2, _ = TP.happy(world, "birthright_entry", "AV-1", nonce="pn-2")
    oid_ok3, _ = TP.happy(world, "pack_compute_19_9", "AV-2", nonce="pn-3")
    oid_refund, _ = TP.happy(world, "pack_compute_19_9", "AV-3", nonce="pn-4")
    raw_set_status(pay_db, oid_refund, "closed")          # granted->closed = refund
    oid_timeout = world["pay"].create_order(
        "pack_compute_19_9", "AV-4")["order_id"]          # created
    raw_set_status(pay_db, oid_timeout, "closed")         # created->closed = timeout
    oid_pending = world["pay"].create_order(
        "pack_compute_19_9", "AV-5")["order_id"]
    world["pay"].place_order(oid_pending)                 # pending

    # ---- AC-PN1: honest default + fail-closed construction ----------
    fdef = N.PayNotifyFace(TP.load_pay_config(),
                           os.path.join(world["tmp"], "ndef.db"),
                           pay_db=pay_db)
    approved0 = [t for t, r in fdef.templates.items() if r["approved"]]
    raises0 = expect_raise(
        lambda: fdef.notify_payment_success(oid_ok1),
        N.E_TEMPLATE_NOT_APPROVED)
    fdef.close()
    ok1 = (not approved0) and raises0[0]

    cfg_nodisc = notify_cfg(TP.load_pay_config())
    cfg_nodisc["compliance"]["disclaimer"] = ""
    ok1a = expect_raise(
        lambda: N.PayNotifyFace(cfg_nodisc,
                                os.path.join(world["tmp"], "n1.db"),
                                pay_db=pay_db),
        N.E_PN_NO_DISCLAIMER)[0]
    cfg_banned = notify_cfg(TP.load_pay_config(),
                            templates={"tpl_b": {
                                "approved": True,
                                # first banned word straight from the
                                # shipped config (data stays in json;
                                # this source stays ASCII)
                                "copy": "x %s y"
                                        % TP.load_pay_config()["copy_ban_words"][0],
                            }})
    ok1b = expect_raise(
        lambda: N.PayNotifyFace(cfg_banned,
                                os.path.join(world["tmp"], "n2.db"),
                                pay_db=pay_db),
        N.E_PN_BAD_CONFIG)[0]
    cfg_badcap = notify_cfg(TP.load_pay_config(), cap=0)
    ok1c = expect_raise(
        lambda: N.PayNotifyFace(cfg_badcap,
                                os.path.join(world["tmp"], "n3.db"),
                                pay_db=pay_db),
        N.E_PN_BAD_CONFIG)[0]
    ok1d = expect_raise(
        lambda: N.PayNotifyFace(notify_cfg(TP.load_pay_config()),
                                os.path.join(world["tmp"], "n4.db"),
                                pay_db=os.path.join(world["tmp"],
                                                    "missing.db")),
        N.E_PN_NO_PAY_DB)[0]
    record("AC-PN1", ok1 and ok1a and ok1b and ok1c and ok1d,
           "shipped default constructs with approved=%s, send raises "
           "%s (%s); empty-disclaimer/banned-copy/bad-cap/missing-paydb "
           "all refuse construction"
           % (approved0, N.E_TEMPLATE_NOT_APPROVED, raises0[1]))

    # ---- AC-PN2: W15 authorization budget --------------------------
    f2 = N.PayNotifyFace(notify_cfg(TP.load_pay_config()),
                         os.path.join(world["tmp"], "nbudget.db"),
                         pay_db=pay_db)
    f2.grant_authorization("AV-1", "tpl_ok", "once")      # AV-1: 1 unit
    f2.grant_authorization("AV-2", "tpl_ok", "longterm")  # AV-2: unlimited
    r_first = f2.notify_payment_success(oid_ok1)           # AV-1 consumes the unit
    r_second = f2.notify_payment_success(oid_ok2)          # AV-1 budget burnt
    r_third = f2.notify_payment_success(oid_ok3)          # AV-2 longterm pass
    okg1 = expect_raise(
        lambda: f2.grant_authorization("AV-1", "tpl_ok", "monthly"),
        N.E_PN_BAD_GRANT_TYPE)[0]
    okg2 = expect_raise(
        lambda: f2.grant_authorization("AV-1", "tpl_missing", "once"),
        N.E_PN_UNKNOWN_TEMPLATE)[0]
    ok2 = (r_first["status"] == "sent"
           and r_second["status"] == "skipped_no_budget"
           and r_third["status"] == "sent" and okg1 and okg2)
    f2.close()
    record("AC-PN2", ok2,
           "once grant: first=%s second=%s (unit consumed), longterm "
           "avatar=%s; bad type/unknown template refuse"
           % (r_first["status"], r_second["status"], r_third["status"]))

    # ---- AC-PN3: dual event faces + idempotency + state gates ------
    f3 = N.PayNotifyFace(notify_cfg(TP.load_pay_config()),
                         os.path.join(world["tmp"], "nevent.db"),
                         pay_db=pay_db)
    f3.grant_authorization("AV-1", "tpl_ok", "longterm")
    f3.grant_authorization("AV-3", "tpl_ok", "longterm")
    s1 = f3.notify_payment_success(oid_ok1)
    s1b = f3.notify_payment_success(oid_ok1)               # idempotent replay
    rows_after_replay = row_count(f3)
    s2 = f3.notify_refund(oid_refund)
    s2b = f3.notify_refund(oid_refund)
    o3a = expect_raise(lambda: f3.notify_refund(oid_timeout),
                       N.E_PN_BAD_STATE)                   # timeout close: no grant
    o3b = expect_raise(lambda: f3.notify_payment_success(oid_pending),
                       N.E_PN_BAD_STATE)                   # pending, not granted
    o3c = expect_raise(lambda: f3.notify_refund(oid_ok1),
                       N.E_PN_BAD_STATE)                   # granted, not closed
    o3d = expect_raise(lambda: f3.notify_payment_success(oid_refund),
                       N.E_PN_BAD_STATE)                   # closed, not granted
    o3e = expect_raise(
        lambda: f3.notify_payment_success("no-such-order"),
        N.E_PN_UNKNOWN_ORDER)
    rows_final = row_count(f3)
    ok3 = (s1["status"] == "sent" and s1b["status"] == "already_logged"
           and s2["status"] == "sent" and s2b["status"] == "already_logged"
           and rows_after_replay == 1 and rows_final == 2
           and all(x[0] for x in (o3a, o3b, o3c, o3d, o3e)))
    f3.close()
    record("AC-PN3", ok3,
           "success=%s replay=%s refund=%s replay=%s rows %d->%d; "
           "timeout-close/pending/granted-not-closed/closed-not-granted/"
           "unknown all raise zero-row"
           % (s1["status"], s1b["status"], s2["status"], s2b["status"],
              rows_after_replay, rows_final))

    # ---- AC-PN4: daily send cap ------------------------------------
    f4 = N.PayNotifyFace(notify_cfg(TP.load_pay_config(), cap=1),
                         os.path.join(world["tmp"], "ncap.db"),
                         pay_db=pay_db)
    f4.grant_authorization("AV-2", "tpl_ok", "longterm")
    f4.grant_authorization("AV-3", "tpl_ok", "longterm")
    c1 = f4.notify_payment_success(oid_ok3)                # AV-2 takes cap slot 1
    c2 = f4.notify_refund(oid_refund)                      # AV-3 hits the cap
    n_sent = sum(1 for r in f4.log_rows() if r[4] == "sent")
    n_cap = sum(1 for r in f4.log_rows() if r[4] == "skipped_daily_cap")
    ok4 = (c1["status"] == "sent" and c2["status"] == "skipped_daily_cap"
           and n_sent == 1 and n_cap == 1)
    f4.close()
    record("AC-PN4", ok4,
           "cap=1: first=%s second=%s (sent=%d cap-skips=%d)"
           % (c1["status"], c2["status"], n_sent, n_cap))

    # ---- AC-PN5: gate order first + compliance faces ---------------
    f5 = N.PayNotifyFace(TP.load_pay_config(),
                         os.path.join(world["tmp"], "ngate.db"),
                         pay_db=pay_db)                     # approved=0 default
    gate_ok = True
    for _ in range(3):
        gate_ok = gate_ok and expect_raise(
            lambda: f5.notify_payment_success(oid_ok1),
            N.E_TEMPLATE_NOT_APPROVED)[0]
    gate_rows = row_count(f5)
    f5.close()
    f5b = N.PayNotifyFace(notify_cfg(
        TP.load_pay_config(),
        reason_map={"payment_success": "tpl_missing", "refund": "tpl_ok"}),
        os.path.join(world["tmp"], "ngate2.db"), pay_db=pay_db)
    ok5b = expect_raise(lambda: f5b.notify_payment_success(oid_ok1),
                        N.E_PN_UNKNOWN_TEMPLATE)[0]
    f5b.close()
    f5c = N.PayNotifyFace(notify_cfg(TP.load_pay_config()),
                          os.path.join(world["tmp"], "ngate3.db"),
                          pay_db=pay_db)
    f5c.grant_authorization("AV-1", "tpl_ok", "longterm")
    env = f5c.notify_payment_success(oid_ok1)
    ok5c = (env.get("ai_service") == 1
            and str(env.get("disclaimer", "")).strip()
            and env["status"] == "sent")
    f5c.close()
    record("AC-PN5", gate_ok and gate_rows == 0 and ok5b and ok5c,
           "unapproved template raises on 3 calls rows=%d (template gate "
           "before idempotency); bogus reason template raises; envelope "
           "ai_service=%s disclaimer=%s"
           % (gate_rows, env.get("ai_service") if ok5c else "-",
              "present" if ok5c else "-"))

    # ---- AC-PN6: zero-silent-loss + banner persistence -------------
    db6 = os.path.join(world["tmp"], "nqueue.db")
    f6 = N.PayNotifyFace(notify_cfg(TP.load_pay_config(), cap=1),
                         db6, pay_db=pay_db)
    f6.grant_authorization("AV-1", "tpl_ok", "once")
    f6.grant_authorization("AV-3", "tpl_ok", "longterm")
    q1 = f6.notify_payment_success(oid_ok1)                 # sent (cap slot 1)
    q2 = f6.notify_refund(oid_refund)                       # cap skip -> banner
    all_rows = f6.log_rows()
    banner = f6.banner_queue()
    cover_ok1 = f6.event_coverage(oid_ok1)
    cover_ref = f6.event_coverage(oid_refund)
    f6.close()
    f6b = N.PayNotifyFace(notify_cfg(TP.load_pay_config(), cap=1),
                          db6, pay_db=pay_db)               # reopen same db
    banner_after = f6b.banner_queue()
    ok6 = (len(all_rows) == 2 and len(banner) == 1 and len(banner_after) == 1
           and q1["status"] == "sent" and q2["status"] == "skipped_daily_cap"
           and cover_ok1 == {"payment_success"} and cover_ref == {"refund"})
    f6b.close()
    record("AC-PN6", ok6,
           "attempts=2 rows=%d banner=%d survives reopen=%d; coverage "
           "ok1=%s refund=%s"
           % (len(all_rows), len(banner), len(banner_after),
              sorted(cover_ok1), sorted(cover_ref)))

    # ---- AC-PN7: hygiene self-scan ----------------------------------
    src_path = os.path.join(BASE, "notify.py")
    with open(src_path, "rb") as handle:
        raw = handle.read()
    ok_ascii = all(b < 128 for b in raw)
    import_lines = [ln.strip() for ln in raw.decode("ascii", "replace")
                    .splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in
                       ("urllib", "requests", "socket", "http"))]
    ok_update = b"UPDATE " not in raw
    record("AC-PN7", ok_ascii and not net_hits and ok_update,
           "ascii=%s net-imports=%s update-free=%s (imports: %s)"
           % (ok_ascii, net_hits or "none", ok_update,
              "; ".join(import_lines) or "none"))

    TP.tear(world)
    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay-notify acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
