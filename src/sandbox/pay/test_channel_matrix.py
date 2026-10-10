"""Acceptance suite for the pay channel-status coverage matrix read
face (tech.md claim line R1776).

Asserts the pre-registered criteria AC-CHM1..AC-CHM7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: PayOrders.channel_status_matrix() - pure-read derived
per-channel x per-status dense coverage matrix (reconciliation-read
consumption candidate; the reconcile control plane stays the
independent enforcement face): every legal (channel, status) cell is
always present with zero counts explicit, deterministic cell order,
_face compliance envelope, out-of-domain observed pairs appended
instead of hidden, zero writes.

Usage: python test_channel_matrix.py
"""

import inspect
import json
import os
import re
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                     # noqa: E402 (build/tear/happy reuse)
import orders as O                        # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
STATUSES = ("created", "pending", "paid", "granted", "closed")
CHANNELS = ("standard", "virtual")        # ascending, mirrors the face


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def cell(env, channel, status):
    for row in env["channel_status_matrix"]:
        if row["channel"] == channel and row["status"] == status:
            return row["count"]
    return None


def main():
    # ---- AC-CHM1: contract, empty dense matrix ------------------------
    w = TP.build()
    env1 = w["pay"].channel_status_matrix()
    rows = env1["channel_status_matrix"]
    want_order = [(c, s) for c in CHANNELS for s in STATUSES]
    got_order = [(r["channel"], r["status"]) for r in rows]
    env_keys = set(env1) == {"channel_status_matrix", "total",
                             "ai_service", "disclaimer", "persistent"}
    row_keys = all(set(r) == {"channel", "status", "count"} for r in rows)
    ok1 = (env_keys and row_keys and len(rows) == 10
           and got_order == want_order
           and all(r["count"] == 0 for r in rows)
           and env1["total"] == 0 and env1["ai_service"] == 1
           and isinstance(env1["disclaimer"], str) and env1["disclaimer"]
           and env1["persistent"] is True)
    record("AC-CHM1", ok1,
           "rows=%d order-ok=%s all-zero=%s total=%d ai_service=%s"
           " env-keys=%s row-keys=%s"
           % (len(rows), got_order == want_order,
              all(r["count"] == 0 for r in rows), env1["total"],
              env1["ai_service"], env_keys, row_keys))
    TP.tear(w)

    # ---- AC-CHM2: mixed world, manual-SQL cross-validation ------------
    w = TP.build()
    oid_v1, _ = TP.happy(w, "pack_compute_19_9", "CHM-V1", nonce="n-v1")
    oid_v2, _ = TP.happy(w, "birthright_entry", "CHM-V2", nonce="n-v2")
    w["pay"].close_refund(oid_v2)                      # virtual -> closed
    oid_v3 = w["pay"].create_order("pack_compute_19_9", "CHM-V3")["order_id"]
    w["pay"].place_order(oid_v3)                        # virtual -> pending
    w["pay"].create_order("birthright_entry", "CHM-V4")  # virtual created
    TP.happy(w, "share_observation", "CHM-S1", nonce="n-s1")  # std granted
    oid_s2 = w["pay"].create_order("report_data_b", "CHM-S2")["order_id"]
    w["pay"].place_order(oid_s2)                        # std -> pending
    oid_s3, _ = TP.happy(w, "report_data_b", "CHM-S3", nonce="n-s3")
    w["pay"].close_refund(oid_s3)                       # std -> closed
    env2 = w["pay"].channel_status_matrix()
    manual = dict(((str(c), str(s)), int(n)) for c, s, n in TP.db_query(
        w["pay"].db_path, "SELECT channel, status, COUNT(*) FROM pay_orders"
        " GROUP BY channel, status"))
    cross = all(cell(env2, c, s) == manual.get((c, s), 0)
                for c in CHANNELS for s in STATUSES)
    nonzero = sum(1 for c in CHANNELS for s in STATUSES
                  if cell(env2, c, s) > 0)
    total_cross = env2["total"] == TP.db_query(
        w["pay"].db_path, "SELECT COUNT(*) FROM pay_orders")[0][0]
    spot = (cell(env2, "virtual", "granted") == 1
            and cell(env2, "virtual", "paid") == 0
            and cell(env2, "standard", "created") == 0
            and cell(env2, "standard", "closed") == 1)
    ok2 = cross and total_cross and nonzero >= 6 and spot and env2["total"] == 7
    record("AC-CHM2", ok2,
           "cell-cross=%s total-cross=%s(%d) nonzero=%d spot=%s"
           % (cross, total_cross, env2["total"], nonzero, spot))
    TP.tear(w)

    # ---- AC-CHM3: out-of-domain observed pairs are appended -----------
    w = TP.build()
    TP.happy(w, "pack_compute_19_9", "CHM-T1", nonce="n-t1")
    conn = sqlite3.connect(w["pay"].db_path)
    # direct-DB tamper posture: CHECK bypass via pragma (the T1 edge
    # trigger only fires on UPDATE OF status, so a raw INSERT with an
    # out-of-domain pair reaches the table; production code cannot)
    conn.execute("PRAGMA ignore_check_constraints=ON")
    conn.execute(
        "INSERT INTO pay_orders (order_id, channel, census_avatar_id,"
        " product_id, amount_cent, demand_text, status, ts_utc)"
        " VALUES ('tamper-x','legacy','CHM-X','pack_compute_19_9',1990,"
        "NULL,'reversed','2026-10-11T00:00:00Z')")
    conn.commit()
    conn.close()
    env3 = w["pay"].channel_status_matrix()
    rows3 = env3["channel_status_matrix"]
    dense, extra = rows3[:10], rows3[10:]
    manual_extra = TP.db_query(
        w["pay"].db_path, "SELECT COUNT(*) FROM pay_orders"
        " WHERE channel='legacy' AND status='reversed'")[0][0]
    ok3 = (len(rows3) == 11 and len(dense) == 10 and len(extra) == 1
           and extra[0] == {"channel": "legacy", "status": "reversed",
                            "count": 1}
           and cell(env3, "virtual", "granted") == 1
           and env3["total"] == 2 and manual_extra == 1)
    record("AC-CHM3", ok3,
           "rows=%d dense=%d extra=%s total=%d manual-extra=%d"
           % (len(rows3), len(dense), extra, env3["total"], manual_extra))
    TP.tear(w)

    # ---- AC-CHM4: pure-read law ----------------------------------------
    w = TP.build()
    oid = w["pay"].create_order("pack_compute_19_9", "CHM-R1")["order_id"]
    src = inspect.getsource(O.PayOrders.channel_status_matrix)
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
    before = {t: TP.db_query(w["pay"].db_path,
                             "SELECT COUNT(*) FROM %s" % t)[0][0]
              for t in ("pay_orders", "pay_receipts", "pay_grants")}
    first = w["pay"].channel_status_matrix()
    second = w["pay"].channel_status_matrix()
    after = {t: TP.db_query(w["pay"].db_path,
                            "SELECT COUNT(*) FROM %s" % t)[0][0]
             for t in ("pay_orders", "pay_receipts", "pay_grants")}
    same = (json.dumps(first, sort_keys=True)
            == json.dumps(second, sort_keys=True))
    ok4 = (not dml) and before == after and same
    record("AC-CHM4", ok4,
           "dml-hits=%d counts-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))
    TP.tear(w)

    # ---- AC-CHM5: live derivation, zero caching ------------------------
    w = TP.build()
    env_a = w["pay"].channel_status_matrix()
    oid = w["pay"].create_order("pack_compute_19_9", "CHM-L1")["order_id"]
    env_b = w["pay"].channel_status_matrix()
    w["pay"].place_order(oid)
    env_c = w["pay"].channel_status_matrix()
    amount = w["pay"].order_detail(oid)["amount_cent"]
    cb = w["chans"]["virtual"].make_callback(oid, amount, "n-l1")
    w["pay"].handle_callback(cb)
    env_d = w["pay"].channel_status_matrix()
    steps = (
        cell(env_b, "virtual", "created") == cell(env_a, "virtual", "created") + 1
        and cell(env_c, "virtual", "created") == cell(env_b, "virtual", "created") - 1
        and cell(env_c, "virtual", "pending") == cell(env_b, "virtual", "pending") + 1
        and cell(env_d, "virtual", "pending") == cell(env_c, "virtual", "pending") - 1
        and cell(env_d, "virtual", "granted") == cell(env_c, "virtual", "granted") + 1
        and env_a["total"] == 0 and env_b["total"] == 1
        and env_c["total"] == 1 and env_d["total"] == 1)
    record("AC-CHM5", steps,
           "created %s->%s pending %s->%s->%s granted %s->%s totals=%s"
           % (cell(env_a, "virtual", "created"),
              cell(env_b, "virtual", "created"),
              cell(env_b, "virtual", "pending"),
              cell(env_c, "virtual", "pending"),
              cell(env_d, "virtual", "pending"),
              cell(env_c, "virtual", "granted"),
              cell(env_d, "virtual", "granted"),
              (env_a["total"], env_b["total"], env_c["total"],
               env_d["total"])))
    TP.tear(w)

    # ---- AC-CHM6: hygiene ----------------------------------------------
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
    additive = all(hasattr(O.PayOrders, m) for m in (
        "channel_status_matrix", "create_order", "place_order",
        "handle_callback", "order_detail", "grant_row", "grants_for"))
    with open(os.path.join(BASE, "reconcile.py"), encoding="utf-8") as fh:
        recon_text = fh.read()
    independence = "channel_status_matrix" not in recon_text
    ok6 = ascii_ok and not net_hits and additive and independence
    record("AC-CHM6", ok6,
           "ascii=%s subjects=%d network-imports=%d additive=%s"
           " control-plane-independent=%s"
           % (ascii_ok, len(subjects), len(net_hits), additive,
              independence))

    # ---- AC-CHM7: delivery wiring --------------------------------------
    all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(all_path, encoding="utf-8") as fh:
        all_text = fh.read()
    wired = ('("pay-channel-matrix",' in all_text
             and "test_channel_matrix.py" in all_text)
    prior = len(RESULTS)                      # six criteria before this one
    ok7 = wired and prior == EXPECTED - 1
    record("AC-CHM7", ok7,
           "suites-registry-line=%s prior-criteria=%d expected=%d"
           % (wired, prior, EXPECTED))

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
