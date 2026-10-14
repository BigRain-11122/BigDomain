"""Acceptance suite: pay reconcile control-plane cross-restart
determinism window (BigDomain R1963, R1956 seed).

Pins the pre-registered criteria AC-PRC1..AC-PRC7 (claim row in
state/queue/tech.md, pre-registered before any suite code): the pay
reconcile scanner re-derives its whole verdict from the three on-disk
databases, so closing every writer face and reopening fresh instances
on the same databases must reproduce the CLI scan byte-for-byte;
tamper probes (dangling revoke / dead-account sent) fail with the
same naming before and after the restart; a post-restart grant
recomputes the scan (zero cache) while pre-restart rows stay frozen;
a second restart keeps the guarantee; the scanner is pure-read.

Usage: python test_pay_reconcile_persist.py
"""

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
import notify as N                                    # noqa: E402
import reconcile as RC                                # noqa: E402
from ledger import Ledger                             # noqa: E402 (ledger product)
import store as lobby_store                           # noqa: E402 (lobby product)

RESULTS = []
PROD = "share_observation"
TPL = "tpl_pay_success_pending_ceo"
AV_DEAD = "AV-PRC-DEAD"
AV_LIVE = "AV-PRC-LIVE"
AV_REGRAFT = "AV-PRC-REGRAFT"
T1 = "2026-10-15T08:00:01Z"
T2 = "2026-10-15T08:00:02Z"
T3 = "2026-10-15T08:00:03Z"
T4 = "2026-10-15T08:00:04Z"
PROBE_TS = "2999-01-01T00:00:00Z"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def run_reconcile(args_list):
    proc = subprocess.run(
        [sys.executable, os.path.join(BASE, "reconcile.py")] + args_list,
        capture_output=True, text=True, encoding="utf-8", timeout=180,
        cwd=BASE)
    return proc.returncode, (proc.stdout or "").strip()


def raw_exec(db_path, statements):
    conn = sqlite3.connect(db_path)
    try:
        for sql in statements:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


def fetch_rows(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return [list(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def scalar(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


def load_cfg_with_template():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    # harness fix (R1963 takeover): the notify face reads the registry
    # from config["notify"]["templates"] (notify.py L178); a top-level
    # injection silently falls back to the shipped unapproved
    # placeholders - criteria semantics unchanged.
    cfg.setdefault("notify", {})["templates"] = {
        TPL: {"approved": True,
              "copy": "payment success notice template - sandbox approved copy"}}
    return cfg


def build_world():
    """One fresh three-db world: three granted token-product orders
    (each carries a conversion share entry) plus the notify tri-pair
    spectrum - dead account (grant, revoke, degraded send), live
    account (longterm, sent), re-granted account (AC-VR4: dead then
    live again, legal post-cutoff send). All ts values are injected
    (frozen-clock discipline), public API only."""
    tmp = tempfile.mkdtemp(prefix="pay-prc-")
    cfg = load_cfg_with_template()
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as handle:
        json.dump(cfg, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as handle:
        led_cfg = json.load(handle)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-PRC-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    chans = A.from_config(cfg)

    def grant(avatar, nonce):
        resp = pay.create_order(PROD, avatar)
        oid = resp["order_id"]
        pay.place_order(oid)
        amount = pay.order_detail(oid)["amount_cent"]
        cb = chans[resp["channel"]].make_callback(oid, amount, nonce)
        pay.handle_callback(cb)
        return oid

    oid_dead = grant(AV_DEAD, "n-prc-1")
    oid_live = grant(AV_LIVE, "n-prc-2")
    oid_regraft = grant(AV_REGRAFT, "n-prc-3")
    notify = N.PayNotifyFace(cfg, os.path.join(tmp, "pay_notify.db"),
                             pay_db=os.path.join(tmp, "pay.db"))
    notify.grant_authorization(AV_DEAD, TPL, "once", now=T1)
    notify.revoke_authorization(AV_DEAD, TPL, now=T2)
    notify.notify_payment_success(oid_dead, now=T3)
    notify.grant_authorization(AV_LIVE, TPL, "longterm", now=T1)
    notify.notify_payment_success(oid_live, now=T2)
    notify.grant_authorization(AV_REGRAFT, TPL, "once", now=T1)
    notify.revoke_authorization(AV_REGRAFT, TPL, now=T2)
    notify.grant_authorization(AV_REGRAFT, TPL, "once", now=T3)
    notify.notify_payment_success(oid_regraft, now=T4)
    return {"tmp": tmp, "cfg": cfg, "cfg_path": cfg_path, "led_cfg": led_cfg,
            "events": events, "led": led, "pay": pay, "notify": notify,
            "chans": chans, "oids": [oid_dead, oid_live, oid_regraft],
            "pay_db": os.path.join(tmp, "pay.db"),
            "ledger_db": os.path.join(tmp, "ledger.db"),
            "notify_db": os.path.join(tmp, "pay_notify.db")}


def reopen(world):
    events = lobby_store.EventStore(
        os.path.join(world["tmp"], "events.db"))
    led = Ledger(world["ledger_db"], world["led_cfg"])
    pay = O.PayOrders(world["cfg"], world["pay_db"], events, led)
    notify = N.PayNotifyFace(world["cfg"], world["notify_db"],
                             pay_db=world["pay_db"])
    return events, led, pay, notify


def close_all(events, led, pay, notify):
    notify.close()
    pay.close()
    led.close()
    events.close()


def make_dangling_probe(src, dst):
    shutil.copyfile(src, dst)
    raw_exec(dst, [
        "INSERT INTO pay_notify_revokes (revoke_id, census_avatar_id,"
        " template_id, ts_utc) VALUES ('rv-prc-dangling',"
        " 'AV-PRC-NOGRANT', '%s', '%s')" % (TPL, PROBE_TS)])


def make_dead_probe(src, dst):
    shutil.copyfile(src, dst)
    raw_exec(dst, [
        "INSERT INTO pay_notify_log (send_id, census_avatar_id,"
        " order_id, template_id, reason, status, ts_utc) VALUES ("
        "'sn-prc-dead', '%s', 'ORD-PRC-X', '%s',"
        " 'payment_success', 'sent', '%s')" % (AV_DEAD, TPL, PROBE_TS)])


def notify_counts(notify_db):
    return {
        "grants": scalar(notify_db, "SELECT COUNT(*) FROM pay_notify_grants"),
        "revokes": scalar(notify_db, "SELECT COUNT(*) FROM pay_notify_revokes"),
        "sent": scalar(notify_db, "SELECT COUNT(*) FROM pay_notify_log"
                       " WHERE status='sent'"),
        "skipped": scalar(notify_db, "SELECT COUNT(*) FROM pay_notify_log"
                          " WHERE status='skipped_no_budget'"),
    }


def frozen_anchor(world):
    """Raw row dumps taken with the writer faces open (pre-restart)."""
    pay_db, led_db, ndb = (world["pay_db"], world["ledger_db"],
                           world["notify_db"])
    return {
        "orders": fetch_rows(pay_db, "SELECT * FROM pay_orders ORDER BY rowid"),
        "receipts": fetch_rows(pay_db, "SELECT * FROM pay_receipts ORDER BY rowid"),
        "grants": fetch_rows(pay_db, "SELECT * FROM pay_grants ORDER BY rowid"),
        "conv_refs": fetch_rows(led_db, "SELECT ref FROM ledger_tx WHERE"
                                " ref_type='order' AND type='share' ORDER BY ref"),
        "n_grants": fetch_rows(ndb, "SELECT * FROM pay_notify_grants ORDER BY rowid"),
        "n_revokes": fetch_rows(ndb, "SELECT * FROM pay_notify_revokes ORDER BY rowid"),
        "n_log": fetch_rows(ndb, "SELECT * FROM pay_notify_log ORDER BY rowid"),
    }


def prefix_frozen(anchor, world):
    """After post-restart continuation: pre-restart rows must stay
    byte-identical (append-only) and the notify tables (not touched
    by the continuation) fully identical. R1964 takeover fix
    (evidence-dialect lens, criteria semantics unchanged): the
    conversion share refs are content-addressed hex hashes read
    ORDER BY ref (string sort), so the continuation's new ref may
    sort BEFORE an anchor ref - the frozen lens is the anchor subset
    (all anchor refs present, unchanged, order-stable under the same
    sort; the new ref is a pure addition), not a sorted-list prefix.
    rowid-ordered pay tables keep the prefix lens (new rows are tail
    rows, rowid is append-only)."""
    pay_db, led_db, ndb = (world["pay_db"], world["ledger_db"],
                           world["notify_db"])
    anchor_ref_set = set(r[0] for r in anchor["conv_refs"])
    conv_all = fetch_rows(led_db, "SELECT ref FROM ledger_tx WHERE"
                         " ref_type='order' AND type='share' ORDER BY ref")
    conv_kept = [r for r in conv_all if r[0] in anchor_ref_set]
    checks = [
        fetch_rows(pay_db, "SELECT * FROM pay_orders ORDER BY rowid")[:len(
            anchor["orders"])] == anchor["orders"],
        fetch_rows(pay_db, "SELECT * FROM pay_receipts ORDER BY rowid")[:len(
            anchor["receipts"])] == anchor["receipts"],
        fetch_rows(pay_db, "SELECT * FROM pay_grants ORDER BY rowid")[:len(
            anchor["grants"])] == anchor["grants"],
        conv_kept == anchor["conv_refs"],
        fetch_rows(ndb, "SELECT * FROM pay_notify_grants ORDER BY rowid"
                  ) == anchor["n_grants"],
        fetch_rows(ndb, "SELECT * FROM pay_notify_revokes ORDER BY rowid"
                  ) == anchor["n_revokes"],
        fetch_rows(ndb, "SELECT * FROM pay_notify_log ORDER BY rowid"
                  ) == anchor["n_log"],
    ]
    return all(checks), checks


def main():
    frozen = {}
    for rel in ("config.json", "notify.py", "orders.py", "reconcile.py"):
        with open(os.path.join(BASE, rel), "rb") as handle:
            frozen[rel] = handle.read()

    world = build_world()
    try:
        base_args = [world["pay_db"], world["cfg_path"],
                     world["ledger_db"], world["notify_db"]]

        # AC-PRC1: anchor world + pre-restart scan snapshot ---------
        rc1, out_pre = run_reconcile(base_args)
        nc = notify_counts(world["notify_db"])
        anchor = frozen_anchor(world)
        ok1 = (rc1 == 0 and "checks=8/8" in out_pre
               and "(explicit)" in out_pre
               and '"granted": 3' in out_pre
               and "(3 checked)" in out_pre
               and "pairs checked" in out_pre and "(2 pairs checked)" in out_pre
               and nc == {"grants": 4, "revokes": 2, "sent": 2, "skipped": 1}
               and scalar(world["ledger_db"], "SELECT COUNT(*) FROM"
                          " ledger_tx WHERE ref_type='order' AND"
                          " type='share'") == 3
               and len(anchor["orders"]) == 3 and len(anchor["receipts"]) == 3
               and len(anchor["grants"]) == 3)
        record("AC-PRC1", ok1,
               "anchor exit=%d checks8/8=%s explicit=%s notify=%s conv=%d"
               % (rc1, "checks=8/8" in out_pre, "(explicit)" in out_pre,
                  nc, 3))

        # AC-PRC3 phase 1: tamper probes before the restart ----------
        probe_dangling = os.path.join(world["tmp"], "notify-probe-dangling.db")
        probe_dead = os.path.join(world["tmp"], "notify-probe-dead.db")
        make_dangling_probe(world["notify_db"], probe_dangling)
        rcd1, outd1 = run_reconcile(base_args[:3] + [probe_dangling])
        make_dead_probe(world["notify_db"], probe_dead)
        rcs1, outs1 = run_reconcile(base_args[:3] + [probe_dead])

        # AC-PRC2: close every writer face, reopen, rescan ----------
        close_all(world["events"], world["led"], world["pay"],
                  world["notify"])
        ev2, led2, pay2, notify2 = reopen(world)
        rc2, out_post = run_reconcile(base_args)
        ok2 = rc2 == 0 and out_post == out_pre
        record("AC-PRC2", ok2,
               "cross-restart byte-identity=%s exit=%d"
               % (out_post == out_pre, rc2))

        # AC-PRC3 phase 2: same probes, same paths, after restart ----
        make_dangling_probe(world["notify_db"], probe_dangling)
        rcd2, outd2 = run_reconcile(base_args[:3] + [probe_dangling])
        make_dead_probe(world["notify_db"], probe_dead)
        rcs2, outs2 = run_reconcile(base_args[:3] + [probe_dead])
        ok3 = (rcd1 == 2 and rcd2 == 2 and outd1 == outd2
               and "[FAIL] revoke_ref" in outd1
               and "rv-prc-dangling" in outd1
               and "[ok] revoke_dead" in outd1
               and rcs1 == 2 and rcs2 == 2 and outs1 == outs2
               and "[FAIL] revoke_dead" in outs1
               and "sn-prc-dead" in outs1
               and "[ok] revoke_ref" in outs1)
        record("AC-PRC3", ok3,
               "dangling exit=%d/%d identical=%s dead exit=%d/%d"
               " identical=%s"
               % (rcd1, rcd2, outd1 == outd2, rcs1, rcs2, outs1 == outs2))

        # AC-PRC4: post-restart live grant recomputes the scan -------
        resp4 = pay2.create_order(PROD, "AV-PRC-NEW")
        oid4 = resp4["order_id"]
        pay2.place_order(oid4)
        amount4 = pay2.order_detail(oid4)["amount_cent"]
        cb4 = world["chans"][resp4["channel"]].make_callback(
            oid4, amount4, "n-prc-4")
        pay2.handle_callback(cb4)
        rc4, out_new = run_reconcile(base_args)
        pref_ok, pref_checks = prefix_frozen(anchor, world)
        ok4 = (rc4 == 0 and "checks=8/8" in out_new and out_new != out_pre
               and '"granted": 4' in out_new
               and "(4 checked)" in out_new
               and '"granted": 3' in out_pre
               and pref_ok)
        record("AC-PRC4", ok4,
               "recompute exit=%d changed=%s granted-4=%s conv-4=%s"
               " frozen-prefix=%s"
               % (rc4, out_new != out_pre, '"granted": 4' in out_new,
                  "(4 checked)" in out_new, pref_ok))

        # AC-PRC5: pure-read law + CLI double run --------------------
        table_sqls = [
            (world["pay_db"], "SELECT COUNT(*) FROM pay_orders"),
            (world["pay_db"], "SELECT COUNT(*) FROM pay_receipts"),
            (world["pay_db"], "SELECT COUNT(*) FROM pay_grants"),
            (world["ledger_db"], "SELECT COUNT(*) FROM ledger_tx"),
            (world["ledger_db"], "SELECT COUNT(*) FROM ledger_entries"),
            (world["notify_db"], "SELECT COUNT(*) FROM pay_notify_grants"),
            (world["notify_db"], "SELECT COUNT(*) FROM pay_notify_log"),
        ]
        before = [scalar(db, sql) for db, sql in table_sqls]
        verdicts = []
        for _ in range(3):
            vok, _results, _np, _nm = RC.run_checks(
                world["pay_db"], world["cfg"], world["ledger_db"],
                world["notify_db"])
            verdicts.append(vok)
        rc5b, out_post2 = run_reconcile(base_args)
        after = [scalar(db, sql) for db, sql in table_sqls]
        ok5 = (all(verdicts) and before == after and rc5b == 0
               and out_post2 == out_new)
        record("AC-PRC5", ok5,
               "in-process verdicts=%s counts-stable=%s cli-double=%s"
               % (all(verdicts), before == after, out_post2 == out_new))

        # AC-PRC6: second restart keeps the guarantee ----------------
        close_all(ev2, led2, pay2, notify2)
        ev3, led3, pay3, notify3 = reopen(world)
        rc6, out_3 = run_reconcile(base_args)
        ok6 = rc6 == 0 and out_3 == out_new
        record("AC-PRC6", ok6,
               "second-restart byte-identity=%s exit=%d"
               % (out_3 == out_new, rc6))
        close_all(ev3, led3, pay3, notify3)
    finally:
        shutil.rmtree(world["tmp"], ignore_errors=True)

    # AC-PRC7: hygiene -----------------------------------------------
    with open(os.path.join(BASE, "reconcile.py"), encoding="utf-8") as handle:
        rec_src = handle.read()
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_src = handle.read()
    own_ascii = all(ord(ch) < 128 for ch in own_src)
    net_hits = [ln.strip() for ln in own_src.splitlines()
                if ln.strip().startswith(("import ", "from "))
                and any(w in ln for w in
                        ("urllib", "requests", "socket", "http"))]
    write_hits = [k for k in ("INSERT INTO", "UPDATE ", "DELETE FROM",
                              "DROP ") if k in rec_src]
    thawed = [rel for rel, blob in frozen.items()
              if open(os.path.join(BASE, rel), "rb").read() != blob]
    record("AC-PRC7", own_ascii and not net_hits and not write_hits
           and not thawed,
           "ascii=%s net-imports=%s reconcile-write-kw=%s thawed=%s"
           % (own_ascii, net_hits, write_hits, thawed))

    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay reconcile persist acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
