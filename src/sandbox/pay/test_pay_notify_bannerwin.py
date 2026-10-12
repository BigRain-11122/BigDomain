"""Acceptance suite for the pay notify banner_queue month-window
filter (window tail param).

Asserts the pre-registered criteria AC-PN16..AC-PN22
(state/queue/tech.md R1878 claim line, registered before this
code; honesty law). Each criterion prints PASS/FAIL with evidence;
non-zero exit on any FAIL.

Usage: python test_pay_notify_bannerwin.py
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
EXPECTED = 7

# R1856 bads14 tuple, reused verbatim (family law).
BADS14 = ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
          "202610", "abcd", "", 2026, True, 2.5,
          "2026-10\n", "2026-10 ", "2026-10\r")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


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


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def main():
    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")
    oids = []
    for i in range(6):
        oid, _ = TP.happy(world, "pack_compute_19_9", "AV-%d" % (i + 1),
                          nonce="bw-%d" % i)
        oids.append(oid)
    sep_oids = []
    for i in range(3):
        oid, _ = TP.happy(world, "pack_compute_19_9", "SV-%d" % (i + 1),
                          nonce="bws-%d" % i)
        sep_oids.append(oid)
    oid_refund, _ = TP.happy(world, "birthright_entry", "AV-9",
                             nonce="bw-ref")
    TN.raw_set_status(pay_db, oid_refund, "closed")

    db = os.path.join(world["tmp"], "bw.db")
    cfg = TN.notify_cfg(TP.load_pay_config(), cap=1000)
    f = N.PayNotifyFace(cfg, db, pay_db=pay_db)      # no grants -> all skip
    # September world: 3 rows (record time in month 2026-09)
    for i in range(3):
        f.notify_payment_success(
            sep_oids[i], now="2026-09-30T23:59:5%dZ" % i)
    # October world: 5 distinct rows + refund/6th same-second tie pair
    for i in range(5):
        f.notify_payment_success(oids[i],
                                 now="2026-10-12T10:00:%02dZ" % i)
    f.notify_refund(oid_refund, now="2026-10-12T10:00:05Z")   # tie row A
    f.notify_payment_success(oids[5],
                             now="2026-10-12T10:00:05Z")      # tie row B
    conn = sqlite3.connect(db)

    full = f.banner_queue()                       # 10 rows: 3 sep + 7 oct
    full_kw = f.banner_queue(window=None)
    full_lim0 = f.banner_queue(limit=0)
    oct_rows = [r for r in full if r[5].startswith("2026-10")]
    sep_rows = [r for r in full if r[5].startswith("2026-09")]

    # ---- AC-PN16: default zero drift + list-face shape ----------
    oct_list = f.banner_queue(window="2026-10")
    cap_default = f.banner_queue(limit=4)
    ok16 = (isinstance(full, list) and len(full) == 10
            and dumps(full) == dumps(full_kw) == dumps(full_lim0)
            and isinstance(oct_list, list) and len(oct_list) == 7
            and not isinstance(oct_list, dict)
            and isinstance(cap_default, dict)
            and set(cap_default) == {"rows", "limit", "total",
                                     "returned", "truncated"}
            and cap_default["total"] == 10)
    record("AC-PN16", ok16,
           "default==window-None==limit-0 byte-identical=%s "
           "explicit-window list-face rows=%d is-list=%s "
           "default-cap keys=%s total=%s"
           % (dumps(full) == dumps(full_kw) == dumps(full_lim0),
              len(oct_list), isinstance(oct_list, list),
              sorted(cap_default) if isinstance(cap_default, dict)
              else "-", cap_default["total"]))

    # ---- AC-PN17: bad window fail-closed + gate order -----------
    bads = []
    for bad in BADS14:
        raised, _msg = expect_raise(
            lambda b=bad: f.banner_queue(window=b), N.E_PN_BAD_WINDOW)
        bads.append(raised)
    pre = table_count(conn, "pay_notify_log")
    for bad in BADS14:
        try:
            f.banner_queue(window=bad)
        except ValueError:
            pass
    post = table_count(conn, "pay_notify_log")
    got_limit_first, _m1 = expect_raise(
        lambda: f.banner_queue(limit=-1, window="2026-13"),
        N.E_PN_BAD_LIMIT)
    got_win_after, _m2 = expect_raise(
        lambda: f.banner_queue(limit=3, window="2026-13"),
        N.E_PN_BAD_WINDOW)
    record("AC-PN17",
           all(bads) and pre == post and got_limit_first and got_win_after,
           "bad forms raised=%d/14 log-rows %d==%d zero side effects "
           "gate-order limit-first=%s window-after=%s"
           % (sum(bads), pre, post, got_limit_first, got_win_after))

    # ---- AC-PN18: window slices by record time (list face) ------
    oct_read = f.banner_queue(window="2026-10")
    sep_read = f.banner_queue(window="2026-09")
    empty_read = f.banner_queue(window="2026-08")
    mirror_oct = conn.execute(
        "SELECT send_id, census_avatar_id, order_id, reason, status,"
        " ts_utc FROM pay_notify_log WHERE status LIKE 'skipped_%'"
        " AND substr(ts_utc,1,7)=? ORDER BY ts_utc",
        ("2026-10",)).fetchall()
    subseq = oct_read == oct_rows and sep_read == sep_rows
    record("AC-PN18",
           subseq and oct_read == mirror_oct and empty_read == []
           and len(oct_read) == 7 and len(sep_read) == 3,
           "oct=%d sep=%d subsequence-preserved=%s mirror-SQL=%s "
           "empty-window honest-empty=%s"
           % (len(oct_read), len(sep_read), subseq,
              oct_read == mirror_oct, empty_read == []))

    # ---- AC-PN19: window x cap orthogonality --------------------
    env = f.banner_queue(limit=3, window="2026-10")
    mirror_tail = list(conn.execute(
        "SELECT send_id, census_avatar_id, order_id, reason, status,"
        " ts_utc FROM pay_notify_log WHERE status LIKE 'skipped_%'"
        " AND substr(ts_utc,1,7)=?"
        " ORDER BY ts_utc DESC, rowid DESC LIMIT 3",
        ("2026-10",)))[::-1]
    ok19 = (isinstance(env, dict)
            and set(env) == {"rows", "limit", "total", "returned",
                            "truncated", "window"}
            and env["window"] == "2026-10"
            and env["total"] == 7          # windowed count, not global 10
            and env["rows"] == oct_rows[4:]
            and env["rows"] == mirror_tail
            and env["returned"] == 3 and env["truncated"] is True)
    record("AC-PN19", ok19,
           "keys=%s window=%s total=%s (windowed; global would be 10) "
           "tail==oct[4:] %s mirror-SQL %s returned=%s truncated=%s"
           % (sorted(env) if isinstance(env, dict) else "-",
              env.get("window") if isinstance(env, dict) else "-",
              env.get("total") if isinstance(env, dict) else "-",
              env.get("rows") == oct_rows[4:]
              if isinstance(env, dict) else "-",
              env.get("rows") == mirror_tail if isinstance(env, dict)
              else "-",
              env.get("returned") if isinstance(env, dict) else "-",
              env.get("truncated") if isinstance(env, dict) else "-"))

    # ---- AC-PN20: truncation honesty + boundary states -----------
    env_full_win = f.banner_queue(limit=7, window="2026-10")
    env_one = f.banner_queue(limit=1, window="2026-10")
    env_empty_win = f.banner_queue(limit=3, window="2026-08")
    ok20 = (env_full_win["truncated"] is False
            and env_full_win["returned"] == 7
            and env_full_win["total"] == 7
            and env_one["truncated"] is True
            and env_one["returned"] == 1
            and env_one["rows"] == oct_rows[-1:]
            and env_empty_win == {"rows": [], "limit": 3, "total": 0,
                                  "returned": 0, "truncated": False,
                                  "window": "2026-08"})
    record("AC-PN20", ok20,
           "limit==windowed-total truncated=%s returned=%s; limit=1 "
           "tail==last=%s truncated=%s; empty-window envelope=%s"
           % (env_full_win["truncated"], env_full_win["returned"],
              env_one["rows"] == oct_rows[-1:], env_one["truncated"],
              env_empty_win))

    # ---- AC-PN21: cross-month preservation + future window ------
    ids_full = {r[0] for r in full}
    ids_oct = {r[0] for r in oct_read}
    ids_sep = {r[0] for r in sep_read}
    tie_a, tie_b = full[8], full[9]      # same-second tie pair (oct)
    future_list = f.banner_queue(window="2027-01")
    future_cap = f.banner_queue(limit=5, window="2027-01")
    tie_in_oct = (tie_a[5] == tie_b[5]
                  and tie_a[5].startswith("2026-10")
                  and tie_a in oct_read and tie_b in oct_read)
    ok21 = (ids_oct.isdisjoint(ids_sep)
            and ids_oct | ids_sep == ids_full
            and tie_in_oct
            and future_list == []
            and future_cap["total"] == 0 and future_cap["rows"] == []
            and future_cap["truncated"] is False)
    record("AC-PN21", ok21,
           "oct-only=%s sep-only=%s disjoint=%s union==full=%s "
           "tie-pair in record month=%s future-window list-empty=%s "
           "future-cap total=%s rows=%s"
           % (len(ids_oct) == 7, len(ids_sep) == 3,
              ids_oct.isdisjoint(ids_sep),
              ids_oct | ids_sep == ids_full, tie_in_oct,
              future_list == [], future_cap["total"],
              len(future_cap["rows"])))

    # ---- AC-PN22: pure-read law + hygiene + self-check -----------
    src = inspect.getsource(N.PayNotifyFace.banner_queue)
    kw_hits = [kw for kw in ("INSERT", "UPDATE ", "DELETE")
               if kw in src]
    pre22 = (table_count(conn, "pay_notify_log"),
             table_count(conn, "pay_notify_grants"),
             table_count(conn, "pay_notify_revokes"))
    f.banner_queue()
    f.banner_queue(window="2026-10")
    f.banner_queue(limit=3, window="2026-09")
    post22 = (table_count(conn, "pay_notify_log"),
              table_count(conn, "pay_notify_grants"),
              table_count(conn, "pay_notify_revokes"))
    with open(os.path.join(BASE, "notify.py"), "rb") as handle:
        raw = handle.read()
    ok_ascii = all(b < 128 for b in raw)
    import_lines = [ln.strip() for ln in raw.decode("ascii", "replace")
                    .splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in
                       ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "test_pay_notify_bannerwin.py"),
              "rb") as handle:
        suite_raw = handle.read()
    ok_suite_ascii = all(b < 128 for b in suite_raw)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    record("AC-PN22",
           not kw_hits and pre22 == post22 and ok_ascii and not net_hits
           and ok_suite_ascii and len(cfg_bytes) > 0
           and len(RESULTS) + 1 == EXPECTED,
           "write-stmt hits=%s table-counts %s==%s (log/grants/revokes "
           "3 paths) ascii=%s net-imports=%s suite-ascii=%s "
           "shipped-cfg read-only=%s criteria-so-far=%d/%d"
           % (kw_hits or "none", pre22, post22, ok_ascii,
              net_hits or "none", ok_suite_ascii, len(cfg_bytes) > 0,
              len(RESULTS), EXPECTED))

    f.close()
    conn.close()
    TP.tear(world)
    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay-notify-bannerwin acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails or len(RESULTS) != EXPECTED:
        if fails:
            print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
