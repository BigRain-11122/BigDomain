"""Acceptance suite: pay reconcile control-plane revokes coverage
(BigDomain R1746, R1740 successor).

Pins the pre-registered criteria AC-RVC1..AC-RVC7 (claim row in
state/queue/tech.md, pre-registered before any code): the pay
reconcile grew checks 7 revoke_ref (dangling revoke references) and
8 revoke_dead (dead-account discipline), with a three-state notify-db
resolution (explicit argument > sibling auto-discovery > six-check
mode) and a fail-closed refusal when an explicitly named db is
missing.

Usage: python test_pay_revoke_recon.py
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
import adapters as A                                   # noqa: E402
import notify as N                                     # noqa: E402
from ledger import Ledger                              # noqa: E402 (ledger product)
import store as lobby_store                            # noqa: E402 (lobby product)

RESULTS = []
TPL = "tpl_pay_success_pending_ceo"


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


def build_world(notify=True):
    """One fresh world: granted plain-grant order (share_tokens=0, no
    conversion entry needed) plus, optionally, the notify pair (grant
    then same-second revoke = dead account, R1740 ruling 2). Public
    API only; shipped config copied, never written."""
    tmp = tempfile.mkdtemp(prefix="pay-rvc-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        cfg = json.load(h)
    cfg_path = os.path.join(tmp, "pay-config.json")
    with open(cfg_path, "w", encoding="utf-8") as h:
        json.dump(cfg, h, ensure_ascii=False, indent=2)
    with open(os.path.join(os.path.dirname(BASE), "ledger", "config.json"),
              encoding="utf-8") as h:
        led_cfg = json.load(h)
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-RVC-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    chans = A.from_config(cfg)
    resp = pay.create_order("pack_compute_19_9", "AV-RVC-1")
    oid = resp["order_id"]
    pay.place_order(oid)
    amount = pay.order_detail(oid)["amount_cent"]
    cb = chans[resp["channel"]].make_callback(oid, amount, "n-rvc-1")
    pay.handle_callback(cb)
    pay.close()
    notify_db = None
    if notify:
        # sibling of pay.db by the face's canonical name: exercises the
        # auto-discovery resolution in AC-RVC6
        notify_db = os.path.join(tmp, "pay_notify.db")
        face = N.PayNotifyFace(cfg, notify_db,
                               pay_db=os.path.join(tmp, "pay.db"))
        face.grant_authorization("AV-RVC-1", TPL, "once")
        face.revoke_authorization("AV-RVC-1", TPL)
        face.close()
    led.close()
    return {"tmp": tmp, "cfg_path": cfg_path, "notify_db": notify_db,
            "pay_db": os.path.join(tmp, "pay.db"),
            "ledger_db": os.path.join(tmp, "ledger.db")}


def tear(world):
    shutil.rmtree(world["tmp"], ignore_errors=True)


def main():
    frozen = {}
    for rel in ("config.json", "notify.py", "orders.py"):
        with open(os.path.join(BASE, rel), "rb") as h:
            frozen[rel] = h.read()

    # AC-RVC1: clean eight-check mode (explicit notify db) ----------
    w1 = build_world(notify=True)
    try:
        code, out = run_reconcile([w1["pay_db"], w1["cfg_path"],
                                   w1["ledger_db"], w1["notify_db"]])
        record("AC-RVC1", code == 0 and "checks=8/8" in out
               and "[ok] revoke_ref" in out and "[ok] revoke_dead" in out
               and "(explicit)" in out,
               "clean exit=%d head=%s" % (
                   code, out.splitlines()[0] if out else "-"))
        base_args = [w1["pay_db"], w1["cfg_path"], w1["ledger_db"]]

        # AC-RVC2: dangling revoke posture (surgical FAIL naming) ---
        dangling_db = os.path.join(w1["tmp"], "notify-dangling.db")
        shutil.copyfile(w1["notify_db"], dangling_db)
        raw_exec(dangling_db, [
            "INSERT INTO pay_notify_revokes (revoke_id, census_avatar_id,"
            " template_id, ts_utc) VALUES ('rv-rvc-dangling',"
            " 'AV-RVC-NOGRANT', '%s', '2026-10-10T00:00:00Z')" % TPL])
        code2, out2 = run_reconcile(base_args + [dangling_db])
        record("AC-RVC2", code2 == 2 and "[FAIL] revoke_ref" in out2
               and "rv-rvc-dangling" in out2
               and "[ok] revoke_dead" in out2,
               "dangling exit=%d revoke_ref FAIL named, revoke_dead still"
               " ok" % code2)

        # AC-RVC3: dead-account sent posture (surgical FAIL naming) --
        dead_db = os.path.join(w1["tmp"], "notify-dead.db")
        shutil.copyfile(w1["notify_db"], dead_db)
        raw_exec(dead_db, [
            "INSERT INTO pay_notify_log (send_id, census_avatar_id,"
            " order_id, template_id, reason, status, ts_utc) VALUES ("
            "'sn-rvc-dead', 'AV-RVC-1', 'ORD-RVC', '%s',"
            " 'payment_success', 'sent', '2999-01-01T00:00:00Z')" % TPL])
        code3, out3 = run_reconcile(base_args + [dead_db])
        record("AC-RVC3", code3 == 2 and "[FAIL] revoke_dead" in out3
               and "sn-rvc-dead" in out3 and "[ok] revoke_ref" in out3,
               "dead-account exit=%d revoke_dead FAIL named, revoke_ref"
               " still ok" % code3)

        # AC-RVC5: explicitly named missing db = fail-closed ---------
        missing = os.path.join(w1["tmp"], "no-such-notify.db")
        code5, out5 = run_reconcile(base_args + [missing])
        record("AC-RVC5", code5 == 2 and "notify db not found" in out5
               and "[FAIL] revoke_ref" in out5
               and "[FAIL] revoke_dead" in out5,
               "explicit-missing exit=%d both revoke checks FAIL, no"
               " silent six-check downgrade" % code5)

        # AC-RVC6: sibling auto-discovery (three args, no explicit) ---
        code6, out6 = run_reconcile(base_args)
        record("AC-RVC6", code6 == 0 and "checks=8/8" in out6
               and "(auto)" in out6,
               "auto-discovery exit=%d sibling pay_notify.db bound" % code6)
    finally:
        tear(w1)

    # AC-RVC4: six-check mode (no notify db anywhere) ----------------
    w4 = build_world(notify=False)
    try:
        code4, out4 = run_reconcile([w4["pay_db"], w4["cfg_path"],
                                     w4["ledger_db"]])
        record("AC-RVC4", code4 == 0 and "checks=6/6" in out4
               and "[skip]" in out4 and "[mode]" not in out4,
               "six-check mode exit=%d skip line present, 6/6 preserved"
               % code4)
    finally:
        tear(w4)

    # AC-RVC7: hygiene -----------------------------------------------
    with open(os.path.join(BASE, "reconcile.py"), encoding="utf-8") as h:
        rec_src = h.read()
    with open(os.path.abspath(__file__), encoding="utf-8") as h:
        own_src = h.read()
    own_ascii = all(ord(ch) < 128 for ch in own_src)
    net_hits = [ln.strip() for ln in own_src.splitlines()
                if ln.strip().startswith(("import ", "from "))
                and any(w in ln for w in
                        ("urllib", "requests", "socket", "http"))]
    write_hits = [k for k in ("INSERT INTO", "UPDATE ", "DELETE FROM",
                              "DROP ") if k in rec_src]
    thawed = [rel for rel, blob in frozen.items()
              if open(os.path.join(BASE, rel), "rb").read() != blob]
    record("AC-RVC7", own_ascii and not net_hits and not write_hits
           and not thawed,
           "ascii=%s net-imports=%s reconcile-write-kw=%s thawed=%s"
           % (own_ascii, net_hits, write_hits, thawed))

    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay revoke-reconcile acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
