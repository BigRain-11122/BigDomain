"""Acceptance suite for the pay channel-status matrix monthly
window read face (tech.md claim line R1784).

Asserts the pre-registered criteria AC-CW1..AC-CW7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: PayOrders.channel_status_matrix(window=None) - R1784
window-parameterized variant of the R1776 dense coverage matrix read
face (family = the R1730/R1732 window-parameterized read faces):
default None keeps the full-window behavior with zero drift; an
explicit 'YYYY-MM' restricts counts to orders whose creation month
(ts_utc record-time stamp, never rewritten by later status
transitions) matches. Read-time filter, zero caching, zero rows
written.

Usage: python test_channel_window.py
"""

import datetime
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
import orders as O                        # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
STATUSES = ("created", "pending", "paid", "granted", "closed")
CHANNELS = ("standard", "virtual")        # ascending, mirrors the face

CONFIG_PATH = os.path.join(BASE, "config.json")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def cell(env, channel, status):
    for row in env["channel_status_matrix"]:
        if row["channel"] == channel and row["status"] == status:
            return row["count"]
    return None


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
            (order_id, channel, "CW-FIX", "pack_compute_19_9", 1990,
             None, status, month + "-15T00:00:00Z"))
        conn.commit()
    finally:
        conn.close()


def main():
    with open(CONFIG_PATH, "rb") as fh:
        cfg_sha_before = hashlib.sha256(fh.read()).hexdigest()

    # ---- AC-CW1: contract, default-face zero drift --------------------
    w = TP.build()
    env_def = w["pay"].channel_status_matrix()
    env_none = w["pay"].channel_status_matrix(window=None)
    env_hist = w["pay"].channel_status_matrix(window="2026-01")
    rows_def = env_def["channel_status_matrix"]
    want_order = [(c, s) for c in CHANNELS for s in STATUSES]
    got_order = [(r["channel"], r["status"]) for r in rows_def]
    ok1 = (
        set(env_def) == {"channel_status_matrix", "total", "ai_service",
                        "disclaimer", "persistent"}
        and "window" not in env_def
        and json.dumps(env_def, sort_keys=True)
        == json.dumps(env_none, sort_keys=True)
        and set(env_hist) == set(env_def) | {"window"}
        and env_hist["window"] == "2026-01"
        and len(rows_def) == 10 and got_order == want_order
        and all(r["count"] == 0 for r in rows_def)
        and env_def["total"] == 0
        and all(r["count"] == 0 for r in env_hist["channel_status_matrix"])
        and env_hist["total"] == 0)
    record("AC-CW1", ok1,
           "def-keys=%s def==None=%s explicit-keys=%s dense=%d"
           " order-ok=%s zero-state=%s"
           % ("window" not in env_def,
              json.dumps(env_def, sort_keys=True)
              == json.dumps(env_none, sort_keys=True),
              set(env_hist) == set(env_def) | {"window"},
              len(rows_def), got_order == want_order,
              env_def["total"] == 0 and env_hist["total"] == 0))
    TP.tear(w)

    # ---- AC-CW2: bad window forms fail closed -------------------------
    w = TP.build()
    oid = w["pay"].create_order("pack_compute_19_9", "CW-B1")["order_id"]
    count_before = TP.db_query(
        w["pay"].db_path, "SELECT COUNT(*) FROM pay_orders")[0][0]
    bads = ["2026-13", "2026-00", "2026-1", "2026/10", "2026", "202610",
            "abcd", "", 2026, True, 2.5, "2026-10\n", "2026-10 ",
            "2026-10\r"]
    rejected = 0
    for bad in bads:
        try:
            w["pay"].channel_status_matrix(window=bad)
        except O.PayError as exc:
            if exc.code == O.E_BAD_STATE:
                rejected += 1
    count_after = TP.db_query(
        w["pay"].db_path, "SELECT COUNT(*) FROM pay_orders")[0][0]
    ok2 = rejected == len(bads) and count_before == count_after
    record("AC-CW2", ok2,
           "rejected=%d/%d count-stable=%s (%d==%d)"
           % (rejected, len(bads), count_before == count_after,
              count_before, count_after))
    TP.tear(w)

    # ---- AC-CW3: historical window read, separation, future empty -----
    w = TP.build()
    oid_v, _ = TP.happy(w, "pack_compute_19_9", "CW-H1", nonce="n-h1")
    oid_s, _ = TP.happy(w, "report_data_b", "CW-H2", nonce="n-h2")
    ts_cur = TP.db_query(
        w["pay"].db_path,
        "SELECT ts_utc FROM pay_orders WHERE order_id = ?", (oid_v,))[0][0]
    cur_month = str(ts_cur)[:7]
    hist_month = month_shift(cur_month, -1)
    future_month = month_shift(cur_month, 12)
    inject_hist(w["pay"], "hist-v1", "virtual", "granted", hist_month)
    inject_hist(w["pay"], "hist-s1", "standard", "pending", hist_month)
    inject_hist(w["pay"], "hist-s2", "standard", "closed", hist_month)
    env_h = w["pay"].channel_status_matrix(window=hist_month)
    env_c = w["pay"].channel_status_matrix(window=cur_month)
    env_f = w["pay"].channel_status_matrix(window=future_month)
    env_full = w["pay"].channel_status_matrix()
    manual_h = dict(((str(c), str(s)), int(n)) for c, s, n in TP.db_query(
        w["pay"].db_path,
        "SELECT channel, status, COUNT(*) FROM pay_orders"
        " WHERE substr(ts_utc,1,7) = ? GROUP BY channel, status",
        (hist_month,)))
    hist_cross = all(
        cell(env_h, c, s) == manual_h.get((c, s), 0)
        for c in CHANNELS for s in STATUSES)
    total_full = TP.db_query(
        w["pay"].db_path, "SELECT COUNT(*) FROM pay_orders")[0][0]
    separation = (
        cell(env_h, "virtual", "granted") == 1
        and cell(env_h, "standard", "pending") == 1
        and cell(env_h, "standard", "closed") == 1
        and env_h["total"] == 3
        and cell(env_c, "virtual", "granted") == 1
        and cell(env_c, "standard", "granted") == 1
        and cell(env_c, "standard", "pending") == 0
        and env_c["total"] == 2
        and env_full["total"] == total_full == 5)
    future_empty = (env_f["total"] == 0
                    and all(r["count"] == 0 for r in env_f[
                        "channel_status_matrix"]))
    ok3 = (env_h["window"] == hist_month and hist_cross and separation
           and future_empty)
    record("AC-CW3", ok3,
           "cur=%s hist=%s future=%s hist-cross=%s hist-total=%d"
           " cur-total=%d full=%d(%d) future-empty=%s"
           % (cur_month, hist_month, future_month, hist_cross,
              env_h["total"], env_c["total"], env_full["total"],
              total_full, future_empty))
    TP.tear(w)

    # ---- AC-CW4: out-of-domain pair honest inside the window ----------
    w = TP.build()
    oid_v, _ = TP.happy(w, "pack_compute_19_9", "CW-T1", nonce="n-t1")
    ts_cur = TP.db_query(
        w["pay"].db_path,
        "SELECT ts_utc FROM pay_orders WHERE order_id = ?", (oid_v,))[0][0]
    cur_month = str(ts_cur)[:7]
    hist_month = month_shift(cur_month, -1)
    conn = sqlite3.connect(w["pay"].db_path)
    # direct-DB tamper posture (R1776 AC-CHM3): CHECK bypass via pragma;
    # the T1 edge trigger only fires on a status change, so a raw row
    # with an out-of-domain pair reaches the table; production cannot.
    conn.execute("PRAGMA ignore_check_constraints=ON")
    conn.execute(
        "INSERT INTO pay_orders (order_id, channel, census_avatar_id,"
        " product_id, amount_cent, demand_text, status, ts_utc)"
        " VALUES ('tamper-w','legacy','CW-X','pack_compute_19_9',1990,"
        "NULL,'reversed',?)", (hist_month + "-15T00:00:00Z",))
    conn.commit()
    conn.close()
    env_h = w["pay"].channel_status_matrix(window=hist_month)
    env_c = w["pay"].channel_status_matrix(window=cur_month)
    rows_h = env_h["channel_status_matrix"]
    dense, extra = rows_h[:10], rows_h[10:]
    ok4 = (len(rows_h) == 11 and len(dense) == 10 and len(extra) == 1
           and extra[0] == {"channel": "legacy", "status": "reversed",
                            "count": 1}
           and env_h["total"] == 1
           and len(env_c["channel_status_matrix"]) == 10
           and env_c["total"] == 1
           and cell(env_c, "virtual", "granted") == 1)
    record("AC-CW4", ok4,
           "hist-rows=%d extra=%s hist-total=%d cur-rows=%d"
           " cur-total=%d"
           % (len(rows_h), extra, env_h["total"],
              len(env_c["channel_status_matrix"]), env_c["total"]))
    TP.tear(w)

    # ---- AC-CW5: pure-read law ----------------------------------------
    w = TP.build()
    oid = w["pay"].create_order("pack_compute_19_9", "CW-R1")["order_id"]
    src = inspect.getsource(O.PayOrders.channel_status_matrix)
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
    before = {t: TP.db_query(w["pay"].db_path,
                             "SELECT COUNT(*) FROM %s" % t)[0][0]
              for t in ("pay_orders", "pay_receipts", "pay_grants")}
    ts_cur = TP.db_query(
        w["pay"].db_path,
        "SELECT ts_utc FROM pay_orders WHERE order_id = ?", (oid,))[0][0]
    cur_month = str(ts_cur)[:7]
    first_d = w["pay"].channel_status_matrix()
    second_d = w["pay"].channel_status_matrix()
    first_w = w["pay"].channel_status_matrix(window=cur_month)
    second_w = w["pay"].channel_status_matrix(window=cur_month)
    after = {t: TP.db_query(w["pay"].db_path,
                            "SELECT COUNT(*) FROM %s" % t)[0][0]
             for t in ("pay_orders", "pay_receipts", "pay_grants")}
    same = (json.dumps(first_d, sort_keys=True)
            == json.dumps(second_d, sort_keys=True)
            and json.dumps(first_w, sort_keys=True)
            == json.dumps(second_w, sort_keys=True))
    ok5 = (not dml) and before == after and same
    record("AC-CW5", ok5,
           "dml-hits=%d counts-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))
    TP.tear(w)

    # ---- AC-CW6: live derivation, zero caching ------------------------
    w = TP.build()
    oid = w["pay"].create_order("pack_compute_19_9", "CW-L1")["order_id"]
    ts_cur = TP.db_query(
        w["pay"].db_path,
        "SELECT ts_utc FROM pay_orders WHERE order_id = ?", (oid,))[0][0]
    cur_month = str(ts_cur)[:7]
    hist_month = month_shift(cur_month, -1)   # always distinct from live
    inject_hist(w["pay"], "hist-c6", "virtual", "granted", hist_month)
    env_h0 = w["pay"].channel_status_matrix(window=hist_month)
    env_c1 = w["pay"].channel_status_matrix(window=cur_month)
    env_h1 = w["pay"].channel_status_matrix(window=hist_month)
    w["pay"].place_order(oid)
    env_c2 = w["pay"].channel_status_matrix(window=cur_month)
    env_h2 = w["pay"].channel_status_matrix(window=hist_month)
    amount = w["pay"].order_detail(oid)["amount_cent"]
    cb = w["chans"]["virtual"].make_callback(oid, amount, "n-c6")
    w["pay"].handle_callback(cb)
    env_c3 = w["pay"].channel_status_matrix(window=cur_month)
    env_h3 = w["pay"].channel_status_matrix(window=hist_month)
    steps = (
        cell(env_c1, "virtual", "created") == 1
        and cell(env_c2, "virtual", "created") == 0
        and cell(env_c2, "virtual", "pending") == 1
        and cell(env_c3, "virtual", "pending") == 0
        and cell(env_c3, "virtual", "granted") == 1
        and env_c1["total"] == 1 and env_c2["total"] == 1
        and env_c3["total"] == 1)
    hist_frozen = (json.dumps(env_h0, sort_keys=True)
                   == json.dumps(env_h1, sort_keys=True)
                   == json.dumps(env_h2, sort_keys=True)
                   == json.dumps(env_h3, sort_keys=True)
                   and cell(env_h3, "virtual", "granted") == 1
                   and env_h3["total"] == 1)
    record("AC-CW6", steps and hist_frozen,
           "cur created %s->%s->pending %s->%s->granted %s totals=%s"
           " hist-frozen=%s"
           % (cell(env_c1, "virtual", "created"),
              cell(env_c2, "virtual", "created"),
              cell(env_c2, "virtual", "pending"),
              cell(env_c3, "virtual", "pending"),
              cell(env_c3, "virtual", "granted"),
              (env_c1["total"], env_c2["total"], env_c3["total"]),
              hist_frozen))
    TP.tear(w)

    # ---- AC-CW7: hygiene + delivery wiring ---------------------------
    subjects = [os.path.join(BASE, "orders.py"), os.path.abspath(__file__)]
    ascii_ok = True
    net_hits = []
    for path in subjects:
        with open(path, "rb") as fh:
            data = fh.read()
        if any(b > 127 for b in data):
            ascii_ok = False
        text = data.decode("ascii", "replace")
        for line in text.splitlines():
            stripped = line.strip()
            if (stripped.startswith("import ")
                    or stripped.startswith("from ")) and (
                    re.search(r"\b(urllib|requests|socket|http)\b",
                              stripped)):
                net_hits.append(stripped)
    with open(CONFIG_PATH, "rb") as fh:
        cfg_sha_after = hashlib.sha256(fh.read()).hexdigest()
    sig = str(inspect.signature(O.PayOrders.channel_status_matrix))
    signature_ok = sig == "(self, window=None)"
    additive = all(hasattr(O.PayOrders, m) for m in (
        "channel_status_matrix", "create_order", "place_order",
        "handle_callback", "order_detail", "grants_for", "close_refund"))
    all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(all_path, encoding="utf-8") as fh:
        all_text = fh.read()
    wired = ('("pay-channel-window",' in all_text
             and "test_channel_window.py" in all_text)
    prior = len(RESULTS)                  # six criteria before this one
    ok7 = (ascii_ok and not net_hits and cfg_sha_before == cfg_sha_after
           and signature_ok and additive and wired
           and prior == EXPECTED - 1)
    record("AC-CW7", ok7,
           "ascii=%s network-imports=%d config-sha-stable=%s"
           " signature=%s additive=%s wired=%s prior=%d"
           % (ascii_ok, len(net_hits), cfg_sha_before == cfg_sha_after,
              sig, additive, wired, prior))

    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
