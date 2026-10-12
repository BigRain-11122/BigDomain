"""Acceptance suite for the pay channel-status matrix cross-restart
persistence example window (tech.md claim line R1904).

Asserts the pre-registered criteria AC-CW8..AC-CW14 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: PayOrders.channel_status_matrix(window=None) - R1904
cross-restart derived-purity example window for the R1776/R1784
dense coverage matrix read face (family = the R1889..R1903 persist
example windows). The face closes, a new instance reopens against
the same db and config (event store and ledger are caller-owned
dependencies that survive, R1900 same-type carrier): (1) the
October window read envelope (window echo + dense ten cells) is
byte-identical to the pre-close snapshot, (2) the default
full-window board recovers, (3) new November orders placed on the
reopened instance re-derive the default read (zero caching) while
the old window stays frozen (pay_orders rows are record-time
immutable), (4) a third instance reads pairwise byte-identical.
Suite-only round: zero product changes.

Usage: python test_channel_persist.py
"""

import hashlib
import inspect
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                     # noqa: E402 (fixture reuse)
import orders as O                        # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
CHANNELS = ("standard", "virtual")        # ascending, mirrors the face
STATUSES = ("created", "pending", "paid", "granted", "closed")
CONFIG_PATH = os.path.join(BASE, "config.json")
ORDERS_PATH = os.path.join(BASE, "orders.py")


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


def three_counts(db):
    return tuple(TP.db_query(db, "SELECT COUNT(*) FROM %s" % t)[0][0]
                 for t in ("pay_orders", "pay_receipts", "pay_grants"))


def main():
    with open(CONFIG_PATH, "rb") as fh:
        cfg_sha_before = hashlib.sha256(fh.read()).hexdigest()
    with open(ORDERS_PATH, "rb") as fh:
        orders_sha_before = hashlib.sha256(fh.read()).hexdigest()

    print("Criteria: AC-CW8..AC-CW14 (pre-registered in tech.md"
          " BEFORE code; honesty law)", flush=True)

    w = TP.build()
    try:
        pay, cfg = w["pay"], w["cfg"]
        pay_db = os.path.join(w["tmp"], "pay.db")

        # ---- AC-CW8: October world + pre-close quartet snapshot ----
        oid_v1, _ = TP.happy(w, "pack_compute_19_9", "CW-P1",
                             nonce="n-cp1")
        oid_v2 = pay.create_order("pack_compute_19_9", "CW-P2")["order_id"]
        oid_s1, _ = TP.happy(w, "report_data_b", "CW-P3", nonce="n-cp3")
        oid_s2 = pay.create_order("report_data_b", "CW-P4")["order_id"]
        pay.place_order(oid_s2)
        oid_s3, _ = TP.happy(w, "report_data_b", "CW-P5", nonce="n-cp5")
        pay.close_refund(oid_s3)
        W = str(TP.db_query(
            pay_db, "SELECT ts_utc FROM pay_orders"
            " ORDER BY ts_utc, order_id LIMIT 1")[0][0])[:7]
        FUT = month_shift(W, 12)
        s_oct = pay.channel_status_matrix(window=W)
        s_def = pay.channel_status_matrix()
        s_fut = pay.channel_status_matrix(window=FUT)
        manual = dict(((str(c), str(st)), int(n))
                      for c, st, n in TP.db_query(
                          pay_db,
                          "SELECT channel, status, COUNT(*) FROM pay_orders"
                          " WHERE substr(ts_utc,1,7) = ?"
                          " GROUP BY channel, status", (W,)))
        cross = all(cell(s_oct, c, st) == manual.get((c, st), 0)
                    for c in CHANNELS for st in STATUSES)
        ok8 = (
            set(s_oct) == {"channel_status_matrix", "total", "ai_service",
                          "disclaimer", "persistent", "window"}
            and s_oct["window"] == W
            and set(s_def) == {"channel_status_matrix", "total",
                              "ai_service", "disclaimer", "persistent"}
            and len(s_oct["channel_status_matrix"]) == 10
            and cell(s_oct, "virtual", "granted") == 1
            and cell(s_oct, "virtual", "created") == 1
            and cell(s_oct, "standard", "granted") == 1
            and cell(s_oct, "standard", "pending") == 1
            and cell(s_oct, "standard", "closed") == 1
            and s_oct["total"] == 5 and s_def["total"] == 5
            and dumps(s_def) != dumps(s_oct)
            and set(s_fut) == set(s_oct) and s_fut["window"] == FUT
            and s_fut["total"] == 0
            and all(r["count"] == 0
                    for r in s_fut["channel_status_matrix"])
            and cross)
        record("AC-CW8", ok8,
               "W=%s fut=%s dense=%d cells=(v-granted=%d v-created=%d"
               " s-granted=%d s-pending=%d s-closed=%d) oct-total=%d"
               " def-total=%d cross=%s future-empty=%s"
               % (W, FUT, len(s_oct["channel_status_matrix"]),
                  cell(s_oct, "virtual", "granted"),
                  cell(s_oct, "virtual", "created"),
                  cell(s_oct, "standard", "granted"),
                  cell(s_oct, "standard", "pending"),
                  cell(s_oct, "standard", "closed"),
                  s_oct["total"], s_def["total"], cross,
                  s_fut["total"] == 0))
        snap_oct, snap_def, snap_fut = dumps(s_oct), dumps(s_def), dumps(s_fut)

        # ---- AC-CW9: cross-restart October window read restore ----
        pay.close()
        pay2 = O.PayOrders(cfg, pay_db, w["events"], w["led"])
        r_oct = pay2.channel_status_matrix(window=W)
        r_oct_b = pay2.channel_status_matrix(window=W)
        ok9 = (dumps(r_oct) == snap_oct
               and dumps(r_oct_b) == dumps(r_oct))
        record("AC-CW9", ok9,
               "oct-win-restore=%s self-reread=%s"
               % (dumps(r_oct) == snap_oct,
                  dumps(r_oct_b) == dumps(r_oct)))

        # ---- AC-CW10: default + future window reads restore ------
        r_def = pay2.channel_status_matrix()
        r_fut = pay2.channel_status_matrix(window=FUT)
        ok10 = (dumps(r_def) == snap_def
                and dumps(r_fut) == snap_fut
                and "window" not in r_def
                and r_fut["window"] == FUT and r_fut["total"] == 0
                and len(r_def["channel_status_matrix"]) == 10
                and len(r_fut["channel_status_matrix"]) == 10)
        record("AC-CW10", ok10,
               "def-restore=%s fut-restore=%s def-keys=%d fut-keys=%d"
               % (dumps(r_def) == snap_def, dumps(r_fut) == snap_fut,
                  len(r_def), len(r_fut)))

        # ---- AC-CW11: November orders -> recalc, zero caching -----
        NOV = month_shift(W, 1)
        real_now = O.now_utc
        frozen_nov = NOV + "-07T10:00:00Z"
        O.now_utc = lambda: frozen_nov          # noqa: E731 (fixture)
        try:
            pay2.create_order("pack_compute_19_9", "CW-P6")
            pay2.create_order("report_data_b", "CW-P7")
        finally:
            O.now_utc = real_now
        restore_probe = O.now_utc() != frozen_nov
        nov_rows = TP.db_query(
            pay_db, "SELECT COUNT(*) FROM pay_orders"
            " WHERE substr(ts_utc,1,7) = ?", (NOV,))[0][0]
        r_def2 = pay2.channel_status_matrix()
        r_nov = pay2.channel_status_matrix(window=NOV)
        ok11 = (nov_rows == 2
                and r_def2["total"] == 7
                and dumps(r_def2) != snap_def
                and r_nov["window"] == NOV
                and cell(r_nov, "virtual", "created") == 1
                and cell(r_nov, "standard", "created") == 1
                and r_nov["total"] == 2
                and restore_probe)
        record("AC-CW11", ok11,
               "nov-rows=%d def-total=%d nov-total=%d recalc=%s"
               " restore-probe=%s"
               % (nov_rows, r_def2["total"], r_nov["total"],
                  dumps(r_def2) != snap_def, restore_probe))

        # ---- AC-CW12: old window frozen + immutable rows ----------
        r_oct2 = pay2.channel_status_matrix(window=W)
        oct_rows = TP.db_query(
            pay_db, "SELECT COUNT(*) FROM pay_orders"
            " WHERE substr(ts_utc,1,7) = ?", (W,))[0][0]
        all_rows = TP.db_query(
            pay_db, "SELECT COUNT(*) FROM pay_orders")[0][0]
        ok12 = (dumps(r_oct2) == snap_oct
                and oct_rows == 5 and nov_rows == 2
                and oct_rows + nov_rows == all_rows)
        record("AC-CW12", ok12,
               "oct-frozen=%s oct-count=%d nov-count=%d all=%d"
               % (dumps(r_oct2) == snap_oct, oct_rows, nov_rows, all_rows))

        # ---- AC-CW13: third instance pairwise byte-identical ------
        q2 = [dumps(x) for x in (
            pay2.channel_status_matrix(window=W),
            pay2.channel_status_matrix(),
            pay2.channel_status_matrix(window=NOV),
            pay2.channel_status_matrix(window=FUT))]
        pay2.close()
        pay3 = O.PayOrders(cfg, pay_db, w["events"], w["led"])
        q3 = [dumps(x) for x in (
            pay3.channel_status_matrix(window=W),
            pay3.channel_status_matrix(),
            pay3.channel_status_matrix(window=NOV),
            pay3.channel_status_matrix(window=FUT))]
        ok13 = (q2 == q3 and q3[0] == snap_oct)
        record("AC-CW13", ok13,
               "pairwise=%s oct-still-original=%s"
               % (q2 == q3, q3[0] == snap_oct))

        # ---- AC-CW14: pure-read law + hygiene + wiring ------------
        before = three_counts(pay_db)
        battery = [
            pay3.channel_status_matrix(),
            pay3.channel_status_matrix(window=W),
            pay3.channel_status_matrix(window=NOV),
            pay3.channel_status_matrix(window=FUT),
            pay3.channel_status_matrix(window=W),
            pay3.channel_status_matrix(),
        ]
        battery_identical = (
            dumps(battery[0]) == dumps(battery[5])
            and dumps(battery[1]) == dumps(battery[4]))
        after = three_counts(pay_db)
        src = inspect.getsource(O.PayOrders.channel_status_matrix)
        dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
        with open(CONFIG_PATH, "rb") as fh:
            cfg_sha_after = hashlib.sha256(fh.read()).hexdigest()
        with open(ORDERS_PATH, "rb") as fh:
            orders_sha_after = hashlib.sha256(fh.read()).hexdigest()
        ascii_ok = True
        net_hits = []
        with open(os.path.abspath(__file__), "rb") as fh:
            data = fh.read()
        if any(b > 127 for b in data):
            ascii_ok = False
        for line in data.decode("ascii", "replace").splitlines():
            stripped = line.strip()
            if ((stripped.startswith("import ")
                 or stripped.startswith("from "))
                    and re.search(r"\b(urllib|requests|socket|http)\b",
                                  stripped)):
                net_hits.append(stripped)
        all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
        with open(all_path, encoding="utf-8") as fh:
            all_text = fh.read()
        wired = ('("pay-channel-persist",' in all_text
                 and "test_channel_persist.py" in all_text)
        prior = len(RESULTS)
        ok14 = (before == after and not dml
                and cfg_sha_before == cfg_sha_after
                and orders_sha_before == orders_sha_after
                and ascii_ok and not net_hits and wired
                and battery_identical and prior == EXPECTED - 1)
        record("AC-CW14", ok14,
               "counts-stable=%s(%s) dml-hits=%d cfg-sha-stable=%s"
               " orders-sha-stable=%s ascii=%s network-imports=%d"
               " wired=%s prior=%d"
               % (before == after, before, len(dml),
                  cfg_sha_before == cfg_sha_after,
                  orders_sha_before == orders_sha_after,
                  ascii_ok, len(net_hits), wired, prior))
    finally:
        try:
            pay3.close()
        except NameError:
            pass
        TP.tear(w)

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
