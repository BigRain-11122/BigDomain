"""Acceptance suite for the pay notify banner_queue read-cap window.

Asserts the pre-registered criteria AC-PN8..AC-PN15 (state/queue/tech.md
R1871 claim line, registered before this code; honesty law). Each
criterion prints PASS/FAIL with evidence; non-zero exit on any FAIL.

Usage: python test_pay_notify_bannerlimit.py
"""

import inspect
import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import test_pay_notify as TN             # noqa: E402 (scaffold reuse)
import notify as N                       # noqa: E402

RESULTS = []
EXPECTED = 8


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_raise(fn, *code_fragments):
    try:
        fn()
    except ValueError as exc:
        msg = str(exc)
        missing = [c for c in code_fragments if c not in msg]
        return not missing, msg
    return False, "no-error-raised"


def table_count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]


def main():
    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")
    oids = []
    for i in range(6):
        oid, _ = TP.happy(world, "pack_compute_19_9", "AV-%d" % (i + 1),
                          nonce="nbl-%d" % i)
        oids.append(oid)
    oid_refund, _ = TP.happy(world, "birthright_entry", "AV-9",
                             nonce="nbl-ref")
    TN.raw_set_status(pay_db, oid_refund, "closed")

    db = os.path.join(world["tmp"], "nbl.db")
    cfg = TN.notify_cfg(TP.load_pay_config(), cap=1000)
    f = N.PayNotifyFace(cfg, db, pay_db=pay_db)      # no grants -> all skip
    for i in range(5):
        f.notify_payment_success(oids[i],
                                 now="2026-10-12T10:00:%02dZ" % i)
    f.notify_refund(oid_refund, now="2026-10-12T10:00:05Z")   # tie row A
    f.notify_payment_success(oids[5],
                             now="2026-10-12T10:00:05Z")      # tie row B
    full = f.banner_queue()
    full_again = f.banner_queue(limit=0)
    conn = sqlite3.connect(db)

    # ---- AC-PN8: default = raw-list byte-identical ---------------
    ok8 = (isinstance(full, list) and len(full) == 7
           and json.dumps(full) == json.dumps(full_again)
           and json.dumps(full) == json.dumps(f.banner_queue())
           and len(full[0]) == 6)
    record("AC-PN8", ok8,
           "default raw list rows=%d double-read-identical=%s fields=%d"
           % (len(full), json.dumps(full) == json.dumps(full_again),
              len(full[0])))

    # ---- AC-PN9: bad limit forms fail closed ----------------------
    bads = []
    for bad in (-1, True, "2", 2.5, None):
        raised, msg = expect_raise(lambda b=bad: f.banner_queue(limit=b),
                                   N.E_PN_BAD_LIMIT)
        bads.append(raised)
    pre = table_count(conn, "pay_notify_log")
    for bad in (-1, True, "2", 2.5, None):
        try:
            f.banner_queue(limit=bad)
        except ValueError:
            pass
    post = table_count(conn, "pay_notify_log")
    record("AC-PN9", all(bads) and pre == post,
           "bad forms raised=%d/5 log-rows %d==%d zero side effects"
           % (sum(bads), pre, post))

    # ---- AC-PN10: limit > total returns everything ----------------
    env10 = f.banner_queue(limit=50)
    ok10 = (isinstance(env10, dict)
            and set(env10) == {"rows", "limit", "total", "returned",
                              "truncated"}
            and env10["rows"] == full and env10["limit"] == 50
            and env10["total"] == 7 and env10["returned"] == 7
            and env10["truncated"] is False)
    record("AC-PN10", ok10,
           "envelope keys=%s total=%s returned=%s truncated=%s rows==full=%s"
           % (sorted(env10) if isinstance(env10, dict) else "-",
              env10.get("total") if isinstance(env10, dict) else "-",
              env10.get("returned") if isinstance(env10, dict) else "-",
              env10.get("truncated") if isinstance(env10, dict) else "-",
              env10.get("rows") == full if isinstance(env10, dict) else "-"))

    # ---- AC-PN11: truncated tail window + mirror SQL --------------
    env11 = f.banner_queue(limit=3)
    mirror = list(conn.execute(
        "SELECT send_id, census_avatar_id, order_id, reason, status,"
        " ts_utc FROM pay_notify_log WHERE status LIKE 'skipped_%'"
        " ORDER BY ts_utc DESC, rowid DESC LIMIT 3"))[::-1]
    ok11 = (env11["returned"] == 3 and env11["truncated"] is True
            and env11["total"] == 7 and env11["rows"] == full[4:]
            and env11["rows"] == mirror
            and len(env11["rows"][0]) == 6)
    record("AC-PN11", ok11,
           "returned=%s truncated=%s total=%s tail==full[4:] %s "
           "mirror-SQL %s fields=%d"
           % (env11["returned"], env11["truncated"], env11["total"],
              env11["rows"] == full[4:], env11["rows"] == mirror,
              len(env11["rows"][0])))

    # ---- AC-PN12: boundary states ---------------------------------
    env12a = f.banner_queue(limit=7)
    db0 = os.path.join(world["tmp"], "nbl-empty.db")
    f0 = N.PayNotifyFace(cfg, db0, pay_db=pay_db)
    env12b = f0.banner_queue(limit=3)
    env12c = f.banner_queue(limit=1)
    ok12 = (env12a["truncated"] is False and env12a["returned"] == 7
            and env12b == {"rows": [], "limit": 3, "total": 0,
                           "returned": 0, "truncated": False}
            and env12c["returned"] == 1 and env12c["rows"] == full[-1:]
            and env12c["truncated"] is True)
    f0.close()
    record("AC-PN12", ok12,
           "limit==total truncated=%s empty-world envelope=%s "
           "limit=1 tail==last=%s"
           % (env12a["truncated"],
              env12b if isinstance(env12b, dict) else "-",
              env12c["rows"] == full[-1:]))

    # ---- AC-PN13: same-second tie order + determinism -------------
    tie_a, tie_b = full[5], full[6]
    env13 = f.banner_queue(limit=2)
    ok13 = (tie_a[3] == "refund" and tie_b[3] == "payment_success"
            and tie_a[5] == tie_b[5] == "2026-10-12T10:00:05Z"
            and env13["rows"] == [tie_a, tie_b]
            and json.dumps(env13, sort_keys=True)
            == json.dumps(f.banner_queue(limit=2), sort_keys=True))
    record("AC-PN13", ok13,
           "tie pair same-ts=%s full order=(%s,%s) capped-tail "
           "match=%s double-call-identical=%s"
           % (tie_a[5] == tie_b[5], tie_a[3], tie_b[3],
              env13["rows"] == [tie_a, tie_b],
              json.dumps(env13, sort_keys=True)
              == json.dumps(f.banner_queue(limit=2), sort_keys=True)))

    # ---- AC-PN14: pure-read law ------------------------------------
    src = inspect.getsource(N.PayNotifyFace.banner_queue)
    kw_hits = [kw for kw in ("INSERT", "UPDATE ", "DELETE")
               if kw in src]
    pre14 = (table_count(conn, "pay_notify_log"),
             table_count(conn, "pay_notify_grants"),
             table_count(conn, "pay_notify_revokes"))
    f.banner_queue()
    f.banner_queue(limit=4)
    post14 = (table_count(conn, "pay_notify_log"),
              table_count(conn, "pay_notify_grants"),
              table_count(conn, "pay_notify_revokes"))
    record("AC-PN14", not kw_hits and pre14 == post14,
           "write-stmt hits=%s table-counts %s==%s (log/grants/revokes)"
           % (kw_hits or "none", pre14, post14))

    # ---- AC-PN15: hygiene + delivery self-check --------------------
    with open(os.path.join(BASE, "notify.py"), "rb") as handle:
        raw = handle.read()
    ok_ascii = all(b < 128 for b in raw)
    import_lines = [ln.strip() for ln in raw.decode("ascii", "replace")
                    .splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in
                       ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "test_pay_notify_bannerlimit.py"),
              "rb") as handle:
        suite_raw = handle.read()
    ok_suite_ascii = all(b < 128 for b in suite_raw)
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        cfg_stable = len(handle.read()) > 0   # read-only touch, no write
    record("AC-PN15",
           ok_ascii and not net_hits and ok_suite_ascii and cfg_stable
           and len(RESULTS) + 1 == EXPECTED,
           "ascii=%s net-imports=%s suite-ascii=%s shipped-cfg "
           "read-only=%s criteria-so-far=%d/%d"
           % (ok_ascii, net_hits or "none", ok_suite_ascii, cfg_stable,
              len(RESULTS), EXPECTED))

    f.close()
    conn.close()
    TP.tear(world)
    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay-notify-bannerlimit acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails or len(RESULTS) != EXPECTED:
        if fails:
            print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
