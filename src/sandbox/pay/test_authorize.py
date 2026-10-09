"""Acceptance suite for the W15 authorization report face (R1718
successor, closes the grant_authorization zero-caller gap).

Asserts the pre-registered criteria AC-AZ1..AC-AZ7 (state/queue/
tech.md R1719 claim line, registered 2026-10-10 BEFORE this code;
honesty law). Bearer decision: pay-domain AuthorizeFace wrapping a
caller-built PayNotifyFace (lobby forwarding rejected - ephemeral
lobby actors cannot key budget the pay send path ever consumes).

Usage: python test_authorize.py
"""

import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import test_pay_notify as TN             # noqa: E402 (notify_cfg helper)
import test_pay_notify_wiring as TW      # noqa: E402 (build_wired pattern)
import notify as N                       # noqa: E402 (face, never re-built)
import authorize as AZ                   # noqa: E402 (subject)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_value_error(fn, code):
    try:
        fn()
    except ValueError as exc:
        return code in str(exc), str(exc).split(":", 1)[0]
    except Exception as exc:  # wrong family = FAIL
        return False, "wrong-family:%s" % type(exc).__name__
    return False, "no-error-raised"


def grant_rows(db_path):
    """Test-side read-only count of the authorization budget rows."""
    ro = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        return int(ro.execute(
            "SELECT COUNT(*) FROM pay_notify_grants").fetchone()[0])
    finally:
        ro.close()


def main():
    world = TW.build_wired()
    face = world["face"]
    az = AZ.AuthorizeFace(face)
    ndb = os.path.join(world["tmp"], "nwiring.db")

    # ---- AC-AZ1: bearer face contract ----------------------------
    src = open(os.path.join(BASE, "authorize.py"), "rb").read()
    no_db = b"sqlite3" not in src
    wraps = az.notify is face
    r1 = az.authorize("AV-AZ1", "tpl_ok", "once")
    keys_ok = (r1["status"] == "granted" and len(r1["grant_id"]) == 16
               and r1["template_id"] == "tpl_ok"
               and r1["grant_type"] == "once"
               and r1["budget"] == {"once": 1, "longterm": 0,
                                    "consumed": 0})
    bf = face.budget_face("AV-AZ1", "tpl_ok")
    bf_ok = bf == {"once": 1, "longterm": 0, "consumed": 0}
    rows1 = grant_rows(ndb)
    record("AC-AZ1", no_db and wraps and keys_ok and bf_ok and rows1 == 1,
           "no-direct-db=%s wraps=%s receipt=%s budget_face=%s rows=%d"
           % (no_db, wraps, keys_ok, bf_ok, rows1))

    # ---- AC-AZ2: identity gate -----------------------------------
    o2a, m2a = expect_value_error(
        lambda: az.authorize("", "tpl_ok", "once"), AZ.E_AZ_BAD_ARGS)
    o2b, m2b = expect_value_error(
        lambda: az.authorize(None, "tpl_ok", "once"), AZ.E_AZ_BAD_ARGS)
    o2c, m2c = expect_value_error(
        lambda: az.authorize("   ", "tpl_ok", "once"), AZ.E_AZ_BAD_ARGS)
    rows2 = grant_rows(ndb)
    record("AC-AZ2", o2a and o2b and o2c and rows2 == 1,
           "empty=%s(%s) none=%s(%s) blank=%s(%s) rows=%d (expect 1)"
           % (o2a, m2a, o2b, m2b, o2c, m2c, rows2))

    # ---- AC-AZ3: template review gate (fail-closed) ---------------
    o3a, m3a = expect_value_error(
        lambda: az.authorize("AV-AZ3", "tpl_missing", "once"),
        N.E_PN_UNKNOWN_TEMPLATE)
    rows3a = grant_rows(ndb)
    cfg_unapproved = TN.notify_cfg(TP.load_pay_config(), approved=False)
    ndb2 = os.path.join(world["tmp"], "az-unapproved.db")
    face2 = N.PayNotifyFace(cfg_unapproved, ndb2)
    az2 = AZ.AuthorizeFace(face2)
    o3b, m3b = expect_value_error(
        lambda: az2.authorize("AV-AZ3", "tpl_ok", "once"),
        N.E_TEMPLATE_NOT_APPROVED)
    rows3b = grant_rows(ndb2)
    face2.close()
    record("AC-AZ3", o3a and rows3a == 1 and o3b and rows3b == 0,
           "unknown=%s(%s) rows-after=%d; unapproved=%s(%s) rows=%d"
           % (o3a, m3a, rows3a, o3b, m3b, rows3b))

    # ---- AC-AZ4: two grant types + longterm suppression -------------
    az.authorize("AV-B", "tpl_ok", "once")
    rb2 = az.authorize("AV-B", "tpl_ok", "once")  # fresh gesture: accumulates
    acc_ok = rb2["budget"]["once"] == 2
    az.authorize("AV-C", "tpl_ok", "longterm")
    before = grant_rows(ndb)
    rc2 = az.authorize("AV-C", "tpl_ok", "longterm")  # popup suppressed
    after = grant_rows(ndb)
    supp_ok = (rc2["status"] == "already_longterm"
               and rc2["grant_id"] is None
               and rc2["budget"]["longterm"] == 1 and after == before)
    record("AC-AZ4", acc_ok and supp_ok,
           "once-reaccept=%s (budget.once=%d); longterm-suppress=%s"
           " rows=%d->%d" % (acc_ok, rb2["budget"]["once"], supp_ok,
                             before, after))

    # ---- AC-AZ5: request_id idempotent replay ----------------------
    rd1 = az.authorize("AV-D", "tpl_ok", "once", request_id="rid-1")
    pre = grant_rows(ndb)
    rd1b = az.authorize("AV-D", "tpl_ok", "once", request_id="rid-1")
    mid = grant_rows(ndb)
    rd2 = az.authorize("AV-D", "tpl_ok", "once", request_id="rid-2")
    post = grant_rows(ndb)
    replay_ok = (rd1b["status"] == "already_granted"
                 and rd1b["grant_id"] == rd1["grant_id"]
                 and mid == pre)
    fresh_ok = (rd2["status"] == "granted"
                and rd2["grant_id"] != rd1["grant_id"]
                and post == mid + 1)
    record("AC-AZ5", replay_ok and fresh_ok,
           "replay=%s (gid-same=%s rows=%d->%d); fresh-rid=%s rows=%d"
           % (replay_ok,
              rd1b["grant_id"] == rd1["grant_id"], pre, mid,
              fresh_ok, post))

    # ---- AC-AZ6: W15 flow end-to-end (wired orders path) ------------
    # fresh world so budget arithmetic is isolated; the R1718 wiring
    # consumes the authorization budget on real granted orders. Per
    # avatar the second order uses a second product (order ids are
    # per avatar+product buckets keyed on closed count, so a second
    # order of the SAME product would idempotently replay the first).
    w6 = TW.build_wired()
    az6 = AZ.AuthorizeFace(w6["face"])
    az6.authorize("AV-LT", "tpl_ok", "longterm")
    az6.authorize("AV-ONCE", "tpl_ok", "once")
    o1, _, e1 = TW.flow(w6, "pack_compute_19_9", "AV-LT", "az6-lt-1")
    o2, _, e2 = TW.flow(w6, "birthright_entry", "AV-LT", "az6-lt-2")
    o3, _, e3 = TW.flow(w6, "pack_compute_19_9", "AV-ONCE", "az6-on-1")
    o4, _, e4 = TW.flow(w6, "birthright_entry", "AV-ONCE", "az6-on-2")
    o5, _, e5 = TW.flow(w6, "pack_compute_19_9", "AV-NONE", "az6-no-1")
    lt_ok = (e1["notify"] == {"reason": "payment_success", "status": "sent"}
             and e2["notify"]["status"] == "sent")
    once_ok = (e3["notify"]["status"] == "sent"
               and e4["notify"]["status"] == "skipped_no_budget")
    none_ok = (e5["notify"]["status"] == "skipped_no_budget"
               and len(w6["face"].banner_queue()) == 2)
    granted_all = all(w6["pay"].order_detail(o)["status"] == "granted"
                      for o in (o1, o2, o3, o4, o5))
    record("AC-AZ6", lt_ok and once_ok and none_ok and granted_all,
           "lt=%s once=%s none=%s granted=%s banner=%d"
           % (lt_ok, once_ok, none_ok, granted_all,
              len(w6["face"].banner_queue())))
    TW.drop(w6)

    # ---- AC-AZ7: hygiene -------------------------------------------
    raw = src
    ok_ascii = all(b < 128 for b in raw)
    import_lines = [ln.strip() for ln in
                    open(os.path.join(BASE, "authorize.py"),
                         encoding="ascii").read().splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in
                       ("urllib", "requests", "socket", "http"))]
    nsrc = open(os.path.join(BASE, "notify.py"), encoding="ascii").read()
    additive = "def budget_face" in nsrc
    record("AC-AZ7", ok_ascii and not net_hits and additive,
           "ascii=%s net-imports=%s budget_face-additive=%s (imports: %s)"
           % (ok_ascii, net_hits or "none", additive,
              "; ".join(import_lines) or "none"))

    TW.drop(world)
    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay-authorize acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
