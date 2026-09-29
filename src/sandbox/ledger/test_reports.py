"""Acceptance suite for the city data report paid-download face
(BigDomain R627; canon = BLUEPRINT sec-4 B-side price row B6 at
L76, explore-lane top open row claim).
Asserts the pre-registered criteria AC-CT1..AC-CT7 from the R627
backlog row (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Usage: python test_reports.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L        # noqa: E402  (P-47-2b core)
import reports as R       # noqa: E402  (R627 report download face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_rpt_error(fn, *codes):
    try:
        fn()
    except R.ReportError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_ledger_error(fn, *codes):
    try:
        fn()
    except L.LedgerError as exc:
        return getattr(exc, "code", "") in codes, getattr(exc, "code", "")
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="reports-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    rpt = R.ReportsFace(led)

    led.mint_to_pool("pool:reserve", 400000, "SETTLE-CT-A", "settlement")
    for who, av, amt in (("usr:alice", "alice", 50000),
                         ("usr:bob", "bob", 200000),
                         ("usr:carol", "carol", 50000)):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", amt), (who, "credit", amt)],
                   "manual:fund-%s" % av, "suite funding %s" % av)
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    with open(os.path.join(BASE, "reports.py"), encoding="utf-8") as h:
        src = h.read()

    # -- AC-CT1 reference law: three own tables, one token touch, -------
    # -- structural de-identification, resident disclaimer --------------
    pub1 = rpt.publish_report("rpt:q-2026Q3", "quarterly",
                              "one-person AI company ecosystem report"
                              " 2026Q3", "2026-Q3", "ecosystem", 9900,
                              "sha256:digest-q3")
    pub_idem = rpt.publish_report("rpt:q-2026Q3", "quarterly",
                                  "one-person AI company ecosystem report"
                                  " 2026Q3", "2026-Q3", "ecosystem", 9900,
                                  "sha256:digest-q3")
    ok_dup_pub, code_dp = expect_rpt_error(
        lambda: rpt.publish_report("rpt:q-2026Q3", "quarterly",
                                   "one-person AI company ecosystem report"
                                   " 2026Q3", "2026-Q3", "ecosystem", 19900,
                                   "sha256:digest-q3"),
        R.E_RPT_DUP)
    ok_badkind, code_bk = expect_rpt_error(
        lambda: rpt.publish_report("rpt:x", "forecast", "t", "p", "i",
                                   9900, "d"),
        R.E_RPT_BAD_ARGS)
    ok_badprice, code_bp = expect_rpt_error(
        lambda: rpt.publish_report("rpt:x", "custom", "t", "p", "i", 0, "d"),
        R.E_RPT_BAD_ARGS)
    pub2 = rpt.publish_report("rpt:custom-quant-01", "custom",
                              "custom industry insight: quant tooling",
                              "2026-H2", "quant-tools", 99900,
                              "sha256:digest-custom")
    conn = sqlite3.connect(db_path)
    my_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE 'report%' ORDER BY name").fetchall()]
    pur_cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(report_purchases)").fetchall()]
    conn.close()
    from_targets = [seg.strip().split()[0] for seg in
                    src.split("FROM ")[1:]]
    ok1 = (pub1["idempotent"] is False and pub_idem["idempotent"] is True
           and pub2["idempotent"] is False
           and ok_dup_pub and code_dp == R.E_RPT_DUP
           and ok_badkind and code_bk == R.E_RPT_BAD_ARGS
           and ok_badprice and code_bp == R.E_RPT_BAD_ARGS
           and my_tables == ["report_catalog", "report_downloads",
                             "report_purchases"]
           and pur_cols == ["purchase_id", "buyer", "report_id",
                            "purchase_ref", "price_cent", "bound_spend_tx",
                            "voucher_id", "purchased_utc"]
           and src.count("self.led.spend") == 1
           and all(t.startswith("report_") for t in from_targets)
           and "not investment advice" in src)
    record("AC-CT1", ok1, "own tables = %s; purchase row binds voucher +"
          " spend tx (%s); module has exactly one token touch point"
          " (self.led.spend x%d, inside purchase); source SELECTs"
          " touch only report tables (%d FROM targets, all report_*);"
          " conflicting re-publish %s; bad kind %s; bad price %s;"
          " non-advisory note resident"
          % (my_tables, pur_cols, src.count("self.led.spend"),
             len(from_targets), code_dp, code_bk, code_bp))

    # -- AC-CT2 purchase: idempotent gates, one spend, one voucher ------
    b0 = bal("usr:alice")
    p1 = rpt.purchase("usr:alice", "rpt:q-2026Q3", "order:ct2a")
    b1 = bal("usr:alice")
    ok_dup_ref, code_dr = expect_rpt_error(
        lambda: rpt.purchase("usr:alice", "rpt:q-2026Q3", "order:ct2a"),
        R.E_RPT_DUP)
    b2 = bal("usr:alice")
    ok_dup_copy, code_dc = expect_rpt_error(
        lambda: rpt.purchase("usr:alice", "rpt:q-2026Q3", "order:ct2b"),
        R.E_RPT_DUP)
    b3 = bal("usr:alice")
    p2 = rpt.purchase("usr:bob", "rpt:custom-quant-01", "order:ct2c")
    b_bob = bal("usr:bob")
    ok_insuf, code_in = expect_ledger_error(
        lambda: rpt.purchase("usr:carol", "rpt:custom-quant-01",
                             "order:ct2big"),
        L.E_NEGATIVE_BALANCE)
    b_carol = bal("usr:carol")
    conn = sqlite3.connect(db_path)
    carol_rows = conn.execute(
        "SELECT COUNT(*) FROM report_purchases WHERE buyer ="
        " 'usr:carol'").fetchone()[0]
    conn.close()
    ok2 = (b0 - b1 == 9900 and p1["price_cent"] == 9900
           and p1["spend_tx"] and p1["voucher_id"].startswith("vch-")
           and ok_dup_ref and code_dr == R.E_RPT_DUP and b2 == b1
           and ok_dup_copy and code_dc == R.E_RPT_DUP and b3 == b1
           and b_bob == 200000 - 99900
           and p2["price_cent"] == 99900
           and ok_insuf and code_in == L.E_NEGATIVE_BALANCE
           and b_carol == 50000 and carol_rows == 0)
    record("AC-CT2", ok2, "alice copy 9900 = one spend (delta %d, tx"
          " bound, voucher %s...); ref replay %s zero charge (bal flat"
          " %d); second copy attempt %s zero charge (bal flat %d); bob"
          " custom 99900 spent; carol insufficient %s zero side"
          " effects (bal flat %d, %d purchase rows)"
          % (b0 - b1, p1["voucher_id"][:8], code_dr, b2, code_dc, b3,
             code_in, b_carol, carol_rows))

    # -- AC-CT3 download voucher: descriptor delivery, immutable rows --
    b_pre_dl = bal("usr:alice")
    d1 = rpt.download("usr:alice", p1["voucher_id"], "dl:a1")
    ok_dup_dl, code_dd = expect_rpt_error(
        lambda: rpt.download("usr:alice", p1["voucher_id"], "dl:a1"),
        R.E_RPT_DUP)
    d2 = rpt.download("usr:alice", p1["voucher_id"], "dl:a2")
    b_post_dl = bal("usr:alice")
    dlog = rpt.download_log("rpt:q-2026Q3")
    ok3 = (d1["dataset_digest"] == "sha256:digest-q3"
           and d2["dataset_digest"] == d1["dataset_digest"]
           and d1["disclaimer_first"] == R.NON_ADVISORY
           and d1["disclaimer_last"] == R.NON_ADVISORY
           and ok_dup_dl and code_dd == R.E_RPT_DUP
           and len(dlog["downloads"]) == 2
           and dlog["downloads"][0]["voucher_id"] == p1["voucher_id"]
           and b_post_dl == b_pre_dl)
    record("AC-CT3", ok3, "voucher downloads deliver descriptor +"
          " digest (%s); duplicate download_ref %s zero double-row"
          " (log rows = %d, both on voucher %s...); repeated"
          " downloads legal with distinct refs; downloads move zero"
          " tokens (bal flat %d)"
          % (d1["dataset_digest"], code_dd, len(dlog["downloads"]),
             p1["voucher_id"][:8], b_post_dl - b_pre_dl))

    # -- AC-CT4 permission gate + bad args, all zero side effects -------
    b_pre_gate = bal("usr:alice")
    ok_unpub, code_up = expect_rpt_error(
        lambda: rpt.purchase("usr:alice", "rpt:ghost", "order:ct4a"),
        R.E_RPT_UNPUBLISHED)
    ok_unk_vch, code_uv = expect_rpt_error(
        lambda: rpt.download("usr:alice", "vch-nonexistent", "dl:g1"),
        R.E_RPT_UNKNOWN_VOUCHER)
    ok_not_owner, code_no = expect_rpt_error(
        lambda: rpt.download("usr:bob", p1["voucher_id"], "dl:g2"),
        R.E_RPT_NOT_OWNER)
    ok_bad_buyer, code_bb = expect_rpt_error(
        lambda: rpt.purchase("corp:ghost", "rpt:q-2026Q3", "order:ct4b"),
        R.E_RPT_BAD_ARGS)
    ok_empty_ref, code_er = expect_rpt_error(
        lambda: rpt.purchase("usr:alice", "rpt:q-2026Q3", "  "),
        R.E_RPT_BAD_ARGS)
    ok_empty_vch, code_ev = expect_rpt_error(
        lambda: rpt.download("usr:alice", "", "dl:g3"),
        R.E_RPT_BAD_ARGS)
    ok_unpub_desc, code_ud = expect_rpt_error(
        lambda: rpt.report_descriptor("rpt:ghost"),
        R.E_RPT_UNPUBLISHED)
    ok_unpub_rec, code_ur = expect_rpt_error(
        lambda: rpt.reconcile_report("rpt:ghost"),
        R.E_RPT_UNPUBLISHED)
    conn = sqlite3.connect(db_path)
    dl_count = conn.execute(
        "SELECT COUNT(*) FROM report_downloads").fetchone()[0]
    conn.close()
    ok4 = (ok_unpub and code_up == R.E_RPT_UNPUBLISHED
           and ok_unk_vch and code_uv == R.E_RPT_UNKNOWN_VOUCHER
           and ok_not_owner and code_no == R.E_RPT_NOT_OWNER
           and ok_bad_buyer and code_bb == R.E_RPT_BAD_ARGS
           and ok_empty_ref and code_er == R.E_RPT_BAD_ARGS
           and ok_empty_vch and code_ev == R.E_RPT_BAD_ARGS
           and ok_unpub_desc and code_ud == R.E_RPT_UNPUBLISHED
           and ok_unpub_rec and code_ur == R.E_RPT_UNPUBLISHED
           and bal("usr:alice") == b_pre_gate and dl_count == 2)
    record("AC-CT4", ok4, "unknown report %s; unknown voucher %s;"
          " cross-buyer voucher %s; corp: buyer %s; empty purchase"
          " ref %s; empty voucher %s; descriptor/reconcile of ghost"
          " %s/%s; download rows flat at %d and balances flat (all"
          " rejects zero side effects)"
          % (code_up, code_uv, code_no, code_bb, code_er, code_ev,
             code_ud, code_ur, dl_count))

    # -- AC-CT5 reconciliation read face + tamper detection --------------
    b_pre_read = bal("usr:alice")
    rec = rpt.reconcile_report("rpt:q-2026Q3")
    rec_bob = rpt.reconcile_report("rpt:custom-quant-01")
    b_post_read = bal("usr:alice")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO report_downloads (download_ref, voucher_id, buyer,"
        " report_id, downloaded_utc) VALUES ('evil-orphan', 'vch-evil',"
        " 'usr:mallory', 'rpt:q-2026Q3', '2026-09-29T00:00:00Z')")
    conn.commit()
    conn.close()
    tampered = rpt.reconcile_report("rpt:q-2026Q3")
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM report_downloads WHERE download_ref ="
                 " 'evil-orphan'")
    conn.commit()
    conn.close()
    restored = rpt.reconcile_report("rpt:q-2026Q3")
    descriptor_keys = set(d1.keys())
    expected_keys = {"report_id", "kind", "title", "disclaimer_first",
                     "disclaimer_last", "period_tag", "industry_tag",
                     "dataset_digest", "pricing_note"}
    ok5 = (rec["purchases"] == 1 and rec["vouchers"] == 1
           and rec["downloads"] == 2 and rec["balanced"] is True
           and rec["orphan_downloads"] == []
           and len(rec["spend_txs"]) == 1
           and rec["billed_total_cent"] == 9900
           and rec_bob["purchases"] == 1 and rec_bob["vouchers"] == 1
           and rec_bob["billed_total_cent"] == 99900
           and b_post_read == b_pre_read
           and tampered["balanced"] is False
           and tampered["orphan_downloads"] == ["evil-orphan"]
           and restored["balanced"] is True
           and descriptor_keys == expected_keys)
    record("AC-CT5", ok5, "quarterly: purchases %d == vouchers %d,"
          " downloads %d all on valid vouchers, billed %d with %d"
          " spend tx, balanced=True; custom: billed %d; descriptor"
          " key set == exactly the aggregate descriptor set (%d keys,"
          " zero raw-data keys); orphan download injection ->"
          " balanced=%s orphans=%s, restored -> %s; unknown report"
          " %s; reads move zero tokens (bal flat)"
          % (rec["purchases"], rec["vouchers"], rec["downloads"],
             rec["billed_total_cent"], len(rec["spend_txs"]),
             rec_bob["billed_total_cent"], len(descriptor_keys),
             tampered["balanced"], tampered["orphan_downloads"],
             restored["balanced"], code_ur))

    # -- AC-CT6 isolation law: no voucher-to-token verb, immutable rows --
    spent_alice = 50000 - bal("usr:alice")
    spent_bob = 200000 - bal("usr:bob")
    spent_carol = 50000 - bal("usr:carol")
    fees = p1["price_cent"] + p2["price_cent"]
    pool_left = led.balance("pool:reserve")["balance"]
    banned_hits = [w for w in ("refund", "withdraw", "convert", "transfer")
                   if w in src]
    immutable_ok = ("UPDATE report_" not in src
                    and "DELETE FROM" not in src)
    ok6 = (spent_alice == 9900 and spent_bob == 99900
           and spent_carol == 0 and fees == 109800
           and pool_left == 400000 - 300000 + fees
           and not banned_hits and immutable_ok)
    record("AC-CT6", ok6, "spends alice %d (quarterly) + bob %d"
          " (custom) + carol %d (zero - insufficient gate); billed %d"
          " recirculated to pool:reserve (%d conservation); zero"
          " banned verbs in source %s; zero UPDATE/DELETE on"
          " catalog/purchase/download rows (immutable, published"
          " catalog cannot be re-priced - re-publish rejects %s)"
          % (spent_alice, spent_bob, spent_carol, fees, pool_left,
             banned_hits, code_dp))

    # -- AC-CT7 hard laws: ASCII, config bytes, prices caller-supplied --
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    non_ascii = sum(1 for byte in
                     open(os.path.join(BASE, "reports.py"), "rb").read()
                     if byte > 127)
    ok7 = (cfg_after == cfg_bytes and non_ascii == 0
           and "needs-CEO" in src
           and cfg == json.loads(cfg_bytes.decode("utf-8")))
    record("AC-CT7", ok7, "config.json byte-identical before/after"
          " (zero new keys; 99/999-CNY anchors arrive as"
          " caller-supplied publish arguments; production price"
          " points = [needs-CEO] P1 approval-only; pure local zero"
          " network); reports.py pure ASCII (%d non-ascii bytes)"
          % non_ascii)

    led.close()
    rpt.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
