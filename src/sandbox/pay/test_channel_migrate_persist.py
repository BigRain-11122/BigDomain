"""Acceptance suite for the pay channel-status matrix cross-restart
DELTA-persistence example window (tech.md claim line R1921).

Asserts the pre-registered criteria AC-CHM8..AC-CHM12 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: PayOrders.channel_status_matrix(window=None) - R1921 claim of
the R1918 seed, scoped by the dedup ruling written into the claim line:
the R1904 suite (test_channel_persist.py, AC-CW8..CW14) already
established the carrier faces (pre-close==reopen byte-identity, new
post-restart order recompute, two-instance sequential reads). This
suite registers only the delta faces the seed adds on top:

(1) AC-CHM8 control anchor + NEW historical-month fixture window:
    anchor world (real product paths) + direct-DB historical fixture
    rows (honest fixture note, R1730 family); pre-close snapshots of
    four reads; close -> reopen -> all four byte-identical (the
    restart carrier is the control anchor for THIS world; anchor
    failure invalidates every later reading, AC-EX0 law).
(2) AC-CHM10 post-restart refund migration per-cell follow: a real
    product-path granted order placed on the reopened instance, then
    close_refund (the only legal refund edge, granted -> closed) -
    exactly two cells migrate in the window read, every other dense
    cell byte-equal, the historical window never penetrated.
(3) AC-CHM11 out-of-domain observation row x window x dense
    orthogonality across restart (R1776 AC-CHM3 tamper posture):
    PRAGMA ignore_check_constraints direct rows in two months; dense
    ten cells stay untouched, appended rows ride after the dense
    cells in (channel,status) ascending order and are counted in the
    total; each window read sees only its own month's appended row.
(4) AC-CHM12 third instance sequential byte-identity + pure-read law
    + hygiene (suite-only round, zero product changes).

Usage: python test_channel_migrate_persist.py
"""

import hashlib
import inspect
import json
import os
import re
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                     # noqa: E402 (fixture reuse)
import orders as O                         # noqa: E402 (face under test)
import adapters as A                       # noqa: E402 (channel adapters)

RESULTS = []
EXPECTED = 5
CHANNELS = ("standard", "virtual")        # ascending, mirrors the face
STATUSES = ("created", "pending", "paid", "granted", "closed")
CONFIG_PATH = os.path.join(BASE, "config.json")
ORDERS_PATH = os.path.join(BASE, "orders.py")
DENSE_ORDER = [(c, s) for c in CHANNELS for s in STATUSES]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def cell(env, channel, status):
    for row in env["channel_status_matrix"]:
        if row["channel"] == channel and row["status"] == status:
            return row["count"]
    return None


def dumps(env):
    return json.dumps(env, sort_keys=True)


def month_shift(ym, delta):
    """'YYYY-MM' arithmetic by whole months (fixture-only helper)."""
    total = int(ym[:4]) * 12 + (int(ym[5:7]) - 1) + delta
    return "%04d-%02d" % (total // 12, total % 12 + 1)


def inject_hist(pay, order_id, channel, status, month):
    """Direct-DB fixture row (record-time stamp injected by hand; the
    product never backdates - honest fixture note, R1730 family)."""
    conn = sqlite3.connect(pay.db_path)
    try:
        conn.execute(
            "INSERT INTO pay_orders (order_id, channel, census_avatar_id,"
            " product_id, amount_cent, demand_text, status, ts_utc)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (order_id, channel, "CMP-FIX", "pack_compute_19_9", 1990,
             None, status, month + "-15T00:00:00Z"))
        conn.commit()
    finally:
        conn.close()


def inject_out_of_domain(db_path, order_id, month):
    """R1776 AC-CHM3 tamper posture: both columns are schema-constrained
    in live use, so the out-of-domain pair can only enter through
    PRAGMA ignore_check_constraints (direct-DB simulation, noted)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA ignore_check_constraints = ON")
        conn.execute(
            "INSERT INTO pay_orders (order_id, channel, census_avatar_id,"
            " product_id, amount_cent, demand_text, status, ts_utc)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (order_id, "legacy", "CMP-TAMPER", "pack_compute_19_9", 1990,
             None, "reversed", month + "-15T00:00:00Z"))
        conn.commit()
    finally:
        conn.close()


def happy_on(pay, chans, product_id, avatar, nonce):
    """create -> place -> valid callback -> granted on a caller-passed
    instance (the R1904 carrier reuses caller-owned adapters; a fresh
    adapter set is built here for the reopened instance)."""
    resp = pay.create_order(product_id, avatar)
    oid = resp["order_id"]
    pay.place_order(oid)
    amount = pay.order_detail(oid)["amount_cent"]
    cb = chans[resp["channel"]].make_callback(oid, amount, nonce)
    pay.handle_callback(cb)
    return oid


def reopen(cfg, db_path, events, led):
    return O.PayOrders(cfg, db_path, events, led)


def main():
    with open(CONFIG_PATH, "rb") as fh:
        cfg_sha_before = hashlib.sha256(fh.read()).hexdigest()
    with open(ORDERS_PATH, "rb") as fh:
        orders_sha_before = hashlib.sha256(fh.read()).hexdigest()

    # ---- shared world ----------------------------------------------
    w = TP.build()
    try:
        pay = w["pay"]
        pay_db = os.path.join(w["tmp"], "pay.db")
        cfg = w["cfg"]

        # anchor world: real product paths, current month W
        happy_on(pay, w["chans"], "pack_compute_19_9", "CMP-A", "n-a")
        happy_on(pay, w["chans"], "report_data_b", "CMP-B", "n-b")
        oid_c = pay.create_order("report_data_b", "CMP-C")["order_id"]
        pay.place_order(oid_c)

        first_ts = TP.db_query(
            pay_db, "SELECT ts_utc FROM pay_orders"
            " ORDER BY ts_utc, order_id LIMIT 1")[0][0]
        w_month = str(first_ts)[:7]
        h_month = month_shift(w_month, -1)
        fut_month = month_shift(w_month, 12)

        # historical-month fixture rows (direct-DB, noted)
        inject_hist(pay, "cmp-hist-v", "virtual", "granted", h_month)
        inject_hist(pay, "cmp-hist-s1", "standard", "closed", h_month)
        inject_hist(pay, "cmp-hist-s2", "standard", "pending", h_month)

        s_def = pay.channel_status_matrix()
        s_w = pay.channel_status_matrix(window=w_month)
        s_h = pay.channel_status_matrix(window=h_month)
        s_fut = pay.channel_status_matrix(window=fut_month)

        # ---- AC-CHM8: control anchor + historical window across ----
        pay.close()
        pay2 = reopen(cfg, pay_db, w["events"], w["led"])
        r_def = pay2.channel_status_matrix()
        r_w = pay2.channel_status_matrix(window=w_month)
        r_h = pay2.channel_status_matrix(window=h_month)
        r_fut = pay2.channel_status_matrix(window=fut_month)
        dense_ok = (
            len(s_def["channel_status_matrix"]) == 10
            and [(x["channel"], x["status"])
                 for x in s_def["channel_status_matrix"]] == DENSE_ORDER)
        anchor_ok = (
            dumps(r_def) == dumps(s_def)
            and dumps(r_w) == dumps(s_w)
            and dumps(r_h) == dumps(s_h)
            and dumps(r_fut) == dumps(s_fut)
            and dense_ok
            and s_w["total"] == 3 and s_def["total"] == 6
            and s_h["total"] == 3 and s_fut["total"] == 0
            and set(s_w) == set(s_def) | {"window"}
            and s_w["window"] == w_month)
        record("AC-CHM8", anchor_ok,
               "w=%s h=%s fut=%s def==reopen=%s w==reopen=%s h==reopen=%s"
               " fut==reopen=%s totals def=%d w=%d h=%d fut=%d dense=%s"
               % (w_month, h_month, fut_month,
                  dumps(r_def) == dumps(s_def),
                  dumps(r_w) == dumps(s_w),
                  dumps(r_h) == dumps(s_h),
                  dumps(r_fut) == dumps(s_fut),
                  s_def["total"], s_w["total"], s_h["total"],
                  s_fut["total"], dense_ok))

        # ---- AC-CHM9: post-restart new order recompute --------------
        pay2.create_order("pack_compute_19_9", "CMP-D")
        row_d = TP.db_query(
            pay_db, "SELECT channel, status FROM pay_orders"
            " WHERE census_avatar_id = 'CMP-D'")[0]
        r_w2 = pay2.channel_status_matrix(window=w_month)
        r_h2 = pay2.channel_status_matrix(window=h_month)
        want_w2 = json.loads(dumps(s_w))
        for row in want_w2["channel_status_matrix"]:
            if (row["channel"], row["status"]) == (row_d[0], row_d[1]):
                row["count"] += 1
        want_w2["total"] += 1
        ok9 = (
            dumps(r_w2) == json.dumps(want_w2, sort_keys=True)
            and dumps(r_h2) == dumps(s_h)
            and cell(r_w2, row_d[0], row_d[1])
            == cell(s_w, row_d[0], row_d[1]) + 1
            and pay2.channel_status_matrix()["total"] == s_def["total"] + 1)
        record("AC-CHM9", ok9,
               "new-cell=(%s,%s) recompute=%s hist-frozen=%s def-total=%d"
               % (row_d[0], row_d[1],
                  dumps(r_w2) == json.dumps(want_w2, sort_keys=True),
                  dumps(r_h2) == dumps(s_h),
                  pay2.channel_status_matrix()["total"]))

        # ---- AC-CHM10: post-restart refund migration per-cell -------
        chans2 = A.from_config(cfg)
        oid_e = happy_on(pay2, chans2, "report_data_b", "CMP-E", "n-e")
        row_e = TP.db_query(
            pay_db, "SELECT channel, status FROM pay_orders"
            " WHERE order_id = ?", (oid_e,))[0]
        pre_refund = pay2.channel_status_matrix(window=w_month)
        pay2.close_refund(oid_e)
        post_refund = pay2.channel_status_matrix(window=w_month)
        want_post = json.loads(dumps(pre_refund))
        for row in want_post["channel_status_matrix"]:
            if (row["channel"], row["status"]) == (row_e[0], "granted"):
                row["count"] -= 1
            if (row["channel"], row["status"]) == (row_e[0], "closed"):
                row["count"] += 1
        migration_ok = (
            dumps(post_refund) == json.dumps(want_post, sort_keys=True)
            and cell(post_refund, row_e[0], "granted")
            == cell(pre_refund, row_e[0], "granted") - 1
            and cell(post_refund, row_e[0], "closed")
            == cell(pre_refund, row_e[0], "closed") + 1
            and pay2.channel_status_matrix(window=h_month)["total"]
            == s_h["total"]
            and pay2.channel_status_matrix()["total"]
            == s_def["total"] + 2)
        record("AC-CHM10", migration_ok,
               "refund-edge=(%s granted->closed) two-cell-diff=%s"
               " hist-total=%d def-total=%d"
               % (row_e[0],
                  dumps(post_refund) == json.dumps(want_post,
                                                   sort_keys=True),
                  pay2.channel_status_matrix(window=h_month)["total"],
                  pay2.channel_status_matrix()["total"]))

        # ---- AC-CHM11: out-of-domain x window x dense across -------
        pre_tamper_w = pay2.channel_status_matrix(window=w_month)
        pre_tamper_def = pay2.channel_status_matrix()
        inject_out_of_domain(pay_db, "cmp-tamper-w", w_month)
        inject_out_of_domain(pay_db, "cmp-tamper-h", h_month)
        tam_def = pay2.channel_status_matrix()
        tam_w = pay2.channel_status_matrix(window=w_month)
        tam_h = pay2.channel_status_matrix(window=h_month)
        tam_fut = pay2.channel_status_matrix(window=fut_month)
        want_tam_w = json.loads(dumps(pre_tamper_w))
        want_tam_w["channel_status_matrix"].append(
            {"channel": "legacy", "status": "reversed", "count": 1})
        want_tam_w["total"] += 1
        want_tam_def = json.loads(dumps(pre_tamper_def))
        want_tam_def["channel_status_matrix"].append(
            {"channel": "legacy", "status": "reversed", "count": 2})
        want_tam_def["total"] += 2
        dense_prefix = [(x["channel"], x["status"])
                        for x in tam_def["channel_status_matrix"][:10]]
        dense_cells_stable = (
            json.dumps(tam_def["channel_status_matrix"][:10],
                       sort_keys=True)
            == json.dumps(pre_tamper_def["channel_status_matrix"],
                          sort_keys=True))
        ok11 = (
            dumps(tam_def) == json.dumps(want_tam_def, sort_keys=True)
            and dumps(tam_w) == json.dumps(want_tam_w, sort_keys=True)
            and tam_h["total"] == s_h["total"] + 1
            and cell(tam_h, "legacy", "reversed") == 1
            and dumps(tam_fut) == dumps(s_fut)
            and dense_prefix == DENSE_ORDER
            and dense_cells_stable
            and len(tam_def["channel_status_matrix"]) == 11
            and len(tam_w["channel_status_matrix"]) == 11
            and len(tam_h["channel_status_matrix"]) == 11
            and len(tam_fut["channel_status_matrix"]) == 10)
        record("AC-CHM11", ok11,
               "appended-default=%s appended-w=%s h-appended=%d"
               " fut-empty=%s dense-stable=%s totals def=%d w=%d h=%d"
               % (dumps(tam_def) == json.dumps(want_tam_def,
                                               sort_keys=True),
                  dumps(tam_w) == json.dumps(want_tam_w, sort_keys=True),
                  cell(tam_h, "legacy", "reversed"),
                  dumps(tam_fut) == dumps(s_fut),
                  dense_cells_stable,
                  tam_def["total"], tam_w["total"], tam_h["total"]))

        # ---- AC-CHM12: third instance + pure-read + hygiene --------
        f_def = pay2.channel_status_matrix()
        f_w = pay2.channel_status_matrix(window=w_month)
        f_h = pay2.channel_status_matrix(window=h_month)
        f_fut = pay2.channel_status_matrix(window=fut_month)
        counts_before = tuple(
            TP.db_query(pay_db, "SELECT COUNT(*) FROM %s" % t)[0][0]
            for t in ("pay_orders", "pay_receipts", "pay_grants"))
        pay2.close()
        pay3 = reopen(cfg, pay_db, w["events"], w["led"])
        t_def = pay3.channel_status_matrix()
        t_w = pay3.channel_status_matrix(window=w_month)
        t_h = pay3.channel_status_matrix(window=h_month)
        t_fut = pay3.channel_status_matrix(window=fut_month)
        counts_after = tuple(
            TP.db_query(pay_db, "SELECT COUNT(*) FROM %s" % t)[0][0]
            for t in ("pay_orders", "pay_receipts", "pay_grants"))
        pay3.close()

        method_src = inspect.getsource(O.PayOrders.channel_status_matrix)
        body = method_src.split('"""', 2)[-1]
        write_hits = re.findall(r"INSERT|UPDATE|DELETE", body)
        with open(ORDERS_PATH, "rb") as fh:
            orders_sha_after = hashlib.sha256(fh.read()).hexdigest()
        with open(CONFIG_PATH, "rb") as fh:
            cfg_sha_after = hashlib.sha256(fh.read()).hexdigest()
        suite_src = open(__file__, "rb").read()
        ascii_ok = all(b < 128 for b in suite_src)
        import_lines = [l for l in suite_src.decode("ascii").splitlines()
                        if l.startswith("import ")
                        or l.startswith("from ")]
        net_hits = [l for l in import_lines
                   if re.search(r"urllib|requests|socket|http", l)]
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "rb") as fh:
            reg_src = fh.read().decode("utf-8")
        reg_ok = ('("pay-channel-migrate-persist"' in reg_src
                  and 'test_channel_migrate_persist.py"), 5)' in reg_src)
        prior_ok = len(RESULTS) == EXPECTED - 1
        ok12 = (
            dumps(t_def) == dumps(f_def)
            and dumps(t_w) == dumps(f_w)
            and dumps(t_h) == dumps(f_h)
            and dumps(t_fut) == dumps(f_fut)
            and counts_before == counts_after
            and not write_hits
            and orders_sha_after == orders_sha_before
            and cfg_sha_after == cfg_sha_before
            and ascii_ok and not net_hits and reg_ok and prior_ok)
        record("AC-CHM12", ok12,
               "third-instance-identity=%s counts=%s write-hits=%d"
               " orders-sha-same=%s cfg-sha-same=%s ascii=%s"
               " net-imports=%d reg=%s prior=%d"
               % (dumps(t_def) == dumps(f_def)
                  and dumps(t_w) == dumps(f_w)
                  and dumps(t_h) == dumps(f_h)
                  and dumps(t_fut) == dumps(f_fut),
                  counts_before == counts_after, len(write_hits),
                  orders_sha_after == orders_sha_before,
                  cfg_sha_after == cfg_sha_before, ascii_ok,
                  len(net_hits), reg_ok, len(RESULTS)))
    finally:
        # teardown of the shared world (instances already closed or
        # never opened on failure paths; rmtree is idempotent)
        try:
            w["pay"].close()
        except Exception:
            pass
        try:
            w["led"].close()
        except Exception:
            pass
        import shutil
        shutil.rmtree(w["tmp"], ignore_errors=True)

    ok = all(flag for _, flag in RESULTS) and len(RESULTS) == EXPECTED
    passed = sum(1 for _, flag in RESULTS if flag)
    print("SUITE %s %d/%d" % ("PASS" if ok else "FAIL", passed, EXPECTED),
          flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
