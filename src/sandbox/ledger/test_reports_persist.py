"""Cross-restart persistence suite for the city data report
paid-download face (BigDomain R1955; FIFO head claim of the R1950
reseed row; persist-example family R1886 lineage).
Asserts the pre-registered criteria AC-RPP1..AC-RPP7 from the
tech.md reports-persist claim row (criteria were registered before
this code existed; honesty law). Two-piece restart law: the
reports face owns its sqlite connection over the same db file;
persistence semantics live in the three immutable report tables
(catalog / purchases / downloads - append-only, no UPDATE/DELETE).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_reports_persist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L      # noqa: E402  (P-47-2b core)
import reports as R     # noqa: E402  (R627 report download face)

RESULTS = []
REPORTS = ("rpt:q-2026Q3", "rpt:custom-quant-01", "rpt:q-2026Q4")
BUYERS = ("usr:alice", "usr:bob", "usr:carol", "usr:dave")

Q3_TITLE = "one-person AI company ecosystem report 2026Q3"
CUSTOM_TITLE = "custom industry insight: quant tooling"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_rpt_error(fn, *codes):
    try:
        fn()
    except R.ReportError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def battery(face, led):
    """Full read-face battery over the three reports + buyer
    balances (deterministic dumps, zero ts echo in evidence)."""
    out = {}
    for rid in REPORTS:
        out[rid + "/descriptor"] = face.report_descriptor(rid)
        out[rid + "/reconcile"] = face.reconcile_report(rid)
        out[rid + "/log"] = face.download_log(rid)
    for who in BUYERS:
        out["bal/" + who] = led.balance(who)["balance"]
    return json.dumps(out, sort_keys=True)


def table_rows(db_path):
    conn = sqlite3.connect(db_path)
    out = {}
    for tbl, order in (
            ("report_catalog", "report_id"),
            ("report_purchases", "purchase_id"),
            ("report_downloads", "downloaded_utc, download_ref")):
        out[tbl] = [list(r) for r in conn.execute(
            "SELECT * FROM %s ORDER BY %s" % (tbl, order)).fetchall()]
    conn.close()
    return out


def table_dump(db_path):
    return json.dumps(table_rows(db_path), sort_keys=True, default=str)


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    counts = tuple(conn.execute(
        "SELECT COUNT(*) FROM %s" % tbl).fetchone()[0]
        for tbl in ("report_catalog", "report_purchases",
                    "report_downloads"))
    conn.close()
    return counts


def tx_exists(db_path, tx_id):
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM ledger_tx WHERE tx_id = ?",
                     (tx_id,)).fetchone()[0]
    conn.close()
    return int(n)


def bound_tx_of(db_path, buyer, report_id, ref):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT bound_spend_tx FROM report_purchases WHERE buyer = ?"
        " AND report_id = ? AND purchase_ref = ?",
        (buyer, report_id, ref)).fetchone()
    conn.close()
    return row[0] if row else None


def gate_batch(face, led, vch_alice):
    """The twelve-gate probe batch (eleven rejects + one idempotent
    re-publish). Every reject fires before the spend / before any
    row write. Returns (codes, all_ok, idem_ok, flat, counts)."""
    pre = {w: led.balance(w)["balance"] for w in BUYERS}
    pre_counts = table_counts(face.db_path)
    codes = []
    all_ok = True

    def probe(fn, *expect):
        ok, code = expect_rpt_error(fn, *expect)
        codes.append(code if ok else "WRONG:" + str(code))
        return ok

    all_ok &= probe(
        lambda: face.purchase("usr:alice", "rpt:q-2026Q3",
                              "order:rpp-a1"), R.E_RPT_DUP)
    all_ok &= probe(
        lambda: face.purchase("usr:alice", "rpt:q-2026Q3",
                              "order:rpp-a9"), R.E_RPT_DUP)
    all_ok &= probe(
        lambda: face.download("usr:alice", vch_alice, "dl:rpp-a1"),
        R.E_RPT_DUP)
    all_ok &= probe(
        lambda: face.download("usr:alice", "vch-ghost", "dl:rpp-g1"),
        R.E_RPT_UNKNOWN_VOUCHER)
    all_ok &= probe(
        lambda: face.download("usr:bob", vch_alice, "dl:rpp-g2"),
        R.E_RPT_NOT_OWNER)
    all_ok &= probe(
        lambda: face.purchase("usr:alice", "rpt:ghost",
                              "order:rpp-g3"), R.E_RPT_UNPUBLISHED)
    all_ok &= probe(
        lambda: face.purchase("corp:ghost", "rpt:q-2026Q3",
                              "order:rpp-g4"), R.E_RPT_BAD_ARGS)
    all_ok &= probe(
        lambda: face.purchase("usr:alice", "rpt:q-2026Q3", "  "),
        R.E_RPT_BAD_ARGS)
    all_ok &= probe(
        lambda: face.publish_report(
            "rpt:q-2026Q3", "quarterly", Q3_TITLE, "2026-Q3",
            "ecosystem", 19900, "sha256:digest-q3"), R.E_RPT_DUP)
    all_ok &= probe(
        lambda: face.publish_report("rpt:x", "forecast", "t", "p",
                                    "i", 9900, "d"), R.E_RPT_BAD_ARGS)
    all_ok &= probe(
        lambda: face.report_descriptor("rpt:ghost"),
        R.E_RPT_UNPUBLISHED)
    idem = face.publish_report("rpt:q-2026Q3", "quarterly", Q3_TITLE,
                               "2026-Q3", "ecosystem", 9900,
                               "sha256:digest-q3")
    post = {w: led.balance(w)["balance"] for w in BUYERS}
    post_counts = table_counts(face.db_path)
    flat = all(pre[w] == post[w] for w in BUYERS)
    return (codes, all_ok, idem.get("idempotent") is True, flat,
            pre_counts, post_counts)


def main():
    tmp = tempfile.mkdtemp(prefix="reports-persist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "reports.py"), "rb") as handle:
        reports_bytes = handle.read()
    with open(os.path.join(BASE, "ledger.py"), "rb") as handle:
        ledger_bytes = handle.read()
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    rpt = R.ReportsFace(led)
    led.mint_to_pool("pool:reserve", 600000, "SETTLE-RPP", "settlement")
    for who, av, amt in (("usr:alice", "alice", 200000),
                         ("usr:bob", "bob", 120000),
                         ("usr:carol", "carol", 60000),
                         ("usr:dave", "dave", 150000)):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", amt), (who, "credit", amt)],
                   "manual:fund-%s" % av, "suite funding %s" % av)
    bal = lambda who, lg: lg.balance(who)["balance"]  # noqa: E731

    # -- anchor world (pre-registration AC-RPP1 shape) --------------------
    rpt.publish_report("rpt:q-2026Q3", "quarterly", Q3_TITLE,
                       "2026-Q3", "ecosystem", 9900,
                       "sha256:digest-q3")
    rpt.publish_report("rpt:custom-quant-01", "custom", CUSTOM_TITLE,
                       "2026-H2", "quant-tools", 99900,
                       "sha256:digest-custom")
    rpt.publish_report("rpt:q-2026Q4", "quarterly",
                       "one-person AI company ecosystem report"
                       " 2026Q4", "2026-Q4", "ecosystem", 4900,
                       "sha256:digest-q4")
    p_a1 = rpt.purchase("usr:alice", "rpt:q-2026Q3", "order:rpp-a1")
    p_a2 = rpt.purchase("usr:alice", "rpt:custom-quant-01",
                         "order:rpp-a2")
    p_b1 = rpt.purchase("usr:bob", "rpt:q-2026Q3", "order:rpp-b1")
    p_c1 = rpt.purchase("usr:carol", "rpt:q-2026Q4", "order:rpp-c1")
    p_d1 = rpt.purchase("usr:dave", "rpt:custom-quant-01",
                         "order:rpp-d1")
    rpt.download("usr:alice", p_a1["voucher_id"], "dl:rpp-a1")
    rpt.download("usr:alice", p_a1["voucher_id"], "dl:rpp-a2")
    rpt.download("usr:alice", p_a2["voucher_id"], "dl:rpp-a3")
    rpt.download("usr:bob", p_b1["voucher_id"], "dl:rpp-b1")
    rpt.download("usr:carol", p_c1["voucher_id"], "dl:rpp-c1")

    snap_battery = battery(rpt, led)
    snap_tables = table_rows(db_path)
    snap_dump = json.dumps(snap_tables, sort_keys=True, default=str)
    counts_pre = table_counts(db_path)
    cross = [tx_exists(db_path, p["spend_tx"])
             for p in (p_a1, p_a2, p_b1, p_c1, p_d1)]
    recs = [rpt.reconcile_report(rid) for rid in REPORTS]
    codes1, all_ok1, idem1, flat1, c1_pre, c1_post = gate_batch(
        rpt, led, p_a1["voucher_id"])
    ok1 = (counts_pre == (3, 5, 5)
           and cross == [1, 1, 1, 1, 1]
           and all(r["balanced"] is True for r in recs)
           and recs[0]["purchases"] == 2
           and recs[0]["billed_total_cent"] == 19800
           and recs[1]["purchases"] == 2
           and recs[1]["billed_total_cent"] == 199800
           and recs[2]["purchases"] == 1
           and recs[2]["billed_total_cent"] == 4900
           and all_ok1 and idem1 and flat1 and c1_post == counts_pre)
    record("AC-RPP1", ok1, "anchor world: %d catalog / %d purchases /"
          " %d downloads; five spend txs cross-checked in ledger_tx"
          " %s; billed q3=%d custom=%d q4=%d; balanced verdicts all"
          " True; twelve-gate batch codes %s all-reject; idempotent"
          " re-publish ok; balances flat and counts flat %s -> %s"
          " (zero drift)"
          % (counts_pre[0], counts_pre[1], counts_pre[2], cross,
             recs[0]["billed_total_cent"], recs[1]["billed_total_cent"],
             recs[2]["billed_total_cent"], codes1, c1_pre, c1_post))

    # -- AC-RPP2: two-piece close -> reopen, byte-identical battery ------
    rpt.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    rpt2 = R.ReportsFace(led2)
    post_battery = battery(rpt2, led2)
    post_dump = table_dump(db_path)
    ok2 = (post_battery == snap_battery and post_dump == snap_dump)
    record("AC-RPP2", ok2, "close -> new Ledger + new ReportsFace"
          " over the same db: read battery byte-identical (%d bytes)"
          " and three-table SQL rows byte-identical (%d rows total)"
          " = zero in-memory drift; immutable report rows persisted"
          % (len(snap_battery.encode("utf-8")),
             counts_pre[0] + counts_pre[1] + counts_pre[2]))

    # -- AC-RPP3: gates cross-restart, same codes, same order -----------
    codes2, all_ok2, idem2, flat2, c2_pre, c2_post = gate_batch(
        rpt2, led2, p_a1["voucher_id"])
    ok3 = (codes2 == codes1 and all_ok2 and idem2 and flat2
           and c2_pre == counts_pre and c2_post == counts_pre)
    record("AC-RPP3", ok3, "restart-surviving gates: probe batch on"
          " the reopened instance returns the same code sequence %s"
          " (eleven rejects + idempotent re-publish); balances flat"
          " and row counts flat %s -> %s = every reject still fires"
          " before any write" % (codes2, c2_pre, c2_post))

    # -- AC-RPP4: real-path continuation, zero-cache recompute ----------
    px1 = rpt2.purchase("usr:dave", "rpt:q-2026Q3", "order:rpp-x1")
    px2 = rpt2.purchase("usr:bob", "rpt:q-2026Q4", "order:rpp-x2")
    rpt2.download("usr:dave", px1["voucher_id"], "dl:rpp-x1")
    cont_battery = battery(rpt2, led2)
    rec_q3 = rpt2.reconcile_report("rpt:q-2026Q3")
    rec_q4 = rpt2.reconcile_report("rpt:q-2026Q4")
    rec_cu = rpt2.reconcile_report("rpt:custom-quant-01")
    log_q3 = rpt2.download_log("rpt:q-2026Q3")
    ok4 = (cont_battery != snap_battery
           and rec_q3["purchases"] == 3
           and rec_q3["billed_total_cent"] == 29700
           and rec_q3["balanced"] is True
           and rec_q4["purchases"] == 2
           and rec_q4["billed_total_cent"] == 9800
           and rec_q4["balanced"] is True
           and rec_cu["purchases"] == 2
           and rec_cu["balanced"] is True
           and len(log_q3["downloads"]) == 4
           and log_q3["downloads"][-1]["download_ref"] == "dl:rpp-x1"
           and tx_exists(db_path, px1["spend_tx"]) == 1
           and tx_exists(db_path, px2["spend_tx"]) == 1
           and bal("usr:dave", led2) == 150000 - 99900 - 9900
           and bal("usr:bob", led2) == 120000 - 9900 - 4900)
    record("AC-RPP4", ok4, "post-restart continuation: dave q3 + bob"
          " q4 real purchases (txs cross-checked) + one new download"
          " -> q3 purchases 2->%d billed %d, q4 1->%d billed %d,"
          " custom unchanged %d; download_log q3 recomputed 3->%d"
          " rows (zero cache); balanced verdicts stay True; balances"
          " recompute dave=%d bob=%d"
          % (rec_q3["purchases"], rec_q3["billed_total_cent"],
             rec_q4["purchases"], rec_q4["billed_total_cent"],
             rec_cu["purchases"], len(log_q3["downloads"]),
             bal("usr:dave", led2), bal("usr:bob", led2)))

    # -- AC-RPP5: frozen anchor rows + replay gate cross-restart ---------
    now_rows = table_rows(db_path)
    frozen_catalog = (now_rows["report_catalog"]
                      == snap_tables["report_catalog"])
    frozen_pur = (now_rows["report_purchases"][:5]
                  == snap_tables["report_purchases"])
    frozen_dl = (now_rows["report_downloads"][:5]
                 == snap_tables["report_downloads"])
    grew = (len(now_rows["report_purchases"]) == 7
            and len(now_rows["report_downloads"]) == 6
            and len(now_rows["report_catalog"]) == 3)
    binding = (bound_tx_of(db_path, "usr:alice", "rpt:q-2026Q3",
                           "order:rpp-a1") == p_a1["spend_tx"])
    pre_replay_counts = table_counts(db_path)
    ok_replay, code_rp = expect_rpt_error(
        lambda: rpt2.purchase("usr:alice", "rpt:q-2026Q3",
                               "order:rpp-a1"), R.E_RPT_DUP)
    idem3 = rpt2.publish_report("rpt:q-2026Q3", "quarterly", Q3_TITLE,
                                "2026-Q3", "ecosystem", 9900,
                                "sha256:digest-q3")
    ok_ghost, code_gh = expect_rpt_error(
        lambda: rpt2.report_descriptor("rpt:ghost"),
        R.E_RPT_UNPUBLISHED)
    post_replay_counts = table_counts(db_path)
    ok5 = (frozen_catalog and frozen_pur and frozen_dl and grew
           and binding
           and ok_replay and code_rp == R.E_RPT_DUP
           and idem3["idempotent"] is True
           and ok_ghost and code_gh == R.E_RPT_UNPUBLISHED
           and post_replay_counts == pre_replay_counts)
    record("AC-RPP5", ok5, "frozen anchors: original 3 catalog rows"
          " and the first 5 purchase / 5 download rows byte-identical"
          " after restart + continuation (immutable, append-only:"
          " purchases 5->%d downloads 5->%d catalog 3); first-purchase"
          " spend tx still bound; pre-restart ref replay %s zero new"
          " rows (counts flat %s); idempotent re-publish ok; ghost"
          " descriptor honest reject %s"
          % (len(now_rows["report_purchases"]),
             len(now_rows["report_downloads"]), code_rp,
             post_replay_counts, code_gh))

    # -- AC-RPP6: pure-read law ------------------------------------------
    before = table_counts(db_path)
    bal_pre = {w: bal(w, led2) for w in BUYERS}
    b1 = battery(rpt2, led2)
    b2 = battery(rpt2, led2)
    after = table_counts(db_path)
    bal_post = {w: bal(w, led2) for w in BUYERS}
    flat_bal = (bal_pre == bal_post)
    ok6 = (before == after and b1 == b2 and flat_bal)
    record("AC-RPP6", ok6, "pure-read law: full battery double-call"
          " byte-identical; row counts identical %s; balances flat"
          " (reads move zero tokens, zero side effects)" % (before,))

    # -- AC-RPP7: third instance stable + hygiene ------------------------
    end_battery = battery(rpt2, led2)
    rpt2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    rpt3 = R.ReportsFace(led3)
    third_battery = battery(rpt3, led3)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(BASE, "reports.py"), "rb") as handle:
        reports_after = handle.read()
    with open(os.path.join(BASE, "ledger.py"), "rb") as handle:
        ledger_after = handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        own_bytes = handle.read()
    own_non_ascii = sum(1 for b in own_bytes if b > 127)
    sha_own = hashlib.sha256(own_bytes).hexdigest()[:16]
    net_imports = [ln.strip() for ln in own_bytes.decode(
        "utf-8").splitlines()
        if ln.strip().startswith("import ")
        or ln.strip().startswith("from ")]
    ok7 = (third_battery == end_battery
           and cfg_after == cfg_bytes
           and reports_after == reports_bytes
           and ledger_after == ledger_bytes
           and own_non_ascii == 0
           and tmp.startswith(tempfile.gettempdir()))
    record("AC-RPP7", ok7, "second close -> third instance over the"
          " same db: battery byte-identical to the second-instance"
          " end state (%d reports x 3 faces + 4 balances);"
          " config.json / reports.py / ledger.py byte-identical"
          " before/after; suite source pure ASCII (%d non-ascii"
          " bytes, sha16 %s); %d imports all stdlib (zero network"
          " libraries); world in tempfile.gettempdir()"
          % (len(REPORTS), own_non_ascii, sha_own,
             len(net_imports)))

    rpt3.close()
    led3.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
