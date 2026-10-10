"""Acceptance suite for the city public dataset subscription face
(BigDomain explore queue, claimed round R1764; canon = the
"city public dataset subscription" line: periodic subscription
windows with delivery, seeded by the reports one-time-purchase
face R627). Asserts the pre-registered criteria AC-DSB1..AC-DSB7
from the R1764 explore-queue row (criteria were registered before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

No SecGate is injected here: the face is platform-side (dataset
registration + subscription purchase contain zero resident free
text - festival/ads/showroom precedent), asserted structurally in
AC-DSB5/AC-DSB7. This test source stays pure ASCII per the
encoding discipline.

Usage: python test_datasub.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
for _d in (BASE,):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import datasub as S                   # noqa: E402 (R1764 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: city public dataset"
              " subscription delivers aggregate operational"
              " statistics, not investment advice")

# the exact descriptor key set a delivery bundle may carry
BUNDLE_KEYS = {"dataset_key", "title", "period", "period_window",
               "disclaimer_first", "disclaimer_last", "dataset_digest",
               "ai_label", "disclaimer", "pricing_note"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except S.DataSubError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="datasub-ac-")
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        cfg_sha_before = hashlib.sha256(handle.read()).hexdigest()
    with open(cfg_path, "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))

    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    ds = S.DatasetSubscriptionFace(led, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    ds_conn = sqlite3.connect(ds.db_path)

    led.mint_to_pool("pool:reserve", 5000, "SETTLE-DSB-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.ensure_account("usr:poor", census_avatar_id="poor")
    for who, amount, tag in (("ada", 500, "ada"), ("bob", 1500, "bob"),
                             ("carol", 300, "carol")):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)

    def bal(who):
        return led.balance("usr:" + who)["balance"]

    def tx_count(kind):
        return conn.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type = ?",
            (kind,)).fetchone()[0]

    # -- AC-DSB1 registration face ----------------------------------------
    r1 = ds.register_dataset("city-mobility", "City Mobility Index",
                             "monthly", 99, "digest-mob-1", False)
    n0 = _count(ds_conn, "dataset_registry")
    again = ds.register_dataset("city-mobility", "City Mobility Index",
                                "monthly", 99, "digest-mob-1", False)
    ok_conflict, code_conflict = expect_error(
        lambda: ds.register_dataset("city-mobility", "Renamed",
                                    "monthly", 99, "digest-mob-1", False),
        S.E_DSB_DUP)
    n1 = _count(ds_conn, "dataset_registry")
    r2 = ds.register_dataset("city-quarterly", "City Economy Quarterly",
                             "quarterly", 999, "digest-q-1", True)
    bad1 = []
    for fn in (
            lambda: ds.register_dataset("", "t", "monthly", 5, "d", False),
            lambda: ds.register_dataset(" ", "t", "monthly", 5, "d", False),
            lambda: ds.register_dataset("k1", "", "monthly", 5, "d", False),
            lambda: ds.register_dataset("k2", "t", "weekly", 5, "d", False),
            lambda: ds.register_dataset("k3", "t", "monthly", 0, "d", False),
            lambda: ds.register_dataset("k4", "t", "monthly", True, "d",
                                        False),
            lambda: ds.register_dataset("k5", "t", "monthly", "5", "d",
                                        False),
            lambda: ds.register_dataset("k6", "t", "monthly", 5, "", False),
            lambda: ds.register_dataset("k7", "t", "monthly", 5, "d",
                                        "yes")):
        ok_x, _code_x = expect_error(fn, S.E_DSB_BAD_ARGS)
        bad1.append(ok_x)
    n2 = _count(ds_conn, "dataset_registry")
    ok_unk, _ = expect_error(lambda: ds.dataset_view("no-such-set"),
                             S.E_DSB_UNKNOWN_DATASET)
    ok_unkr, _ = expect_error(
        lambda: ds.reconcile_dataset("no-such-set"),
        S.E_DSB_UNKNOWN_DATASET)
    record("AC-DSB1",
           r1["idempotent"] is False and r1["ai_label"] == 0
           and again["idempotent"] is True and n1 == n0
           and ok_conflict and code_conflict == S.E_DSB_DUP
           and r2["ai_label"] == 1 and n2 == n0 + 1
           and all(bad1) and ok_unk and ok_unkr,
           "register rows %d->%d idem=%s conflict=%s ai=%d/%d"
           " badargs=%d/9 unknown=%s/%s"
           % (n0, n2, again["idempotent"], ok_conflict, r1["ai_label"],
              r2["ai_label"], sum(bad1), ok_unk, ok_unkr))

    # -- AC-DSB2 window format gate ----------------------------------------
    ok_m01 = ds.subscribe("usr:ada", "city-mobility", "2026-01",
                          "ref-w-01")
    ok_m12 = ds.subscribe("usr:ada", "city-mobility", "2026-12",
                          "ref-w-12")
    bad_monthly = []
    for w in ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
              "202610", "abcd", "", 2026, True, "2026-10\n", "2026-10 "):
        ok_w, code_w = expect_error(
            lambda x=w: ds.subscribe("usr:bob", "city-mobility", x,
                                     "ref-bad-" + str(len(bad_monthly))),
            S.E_DSB_BAD_WINDOW)
        bad_monthly.append(ok_w and code_w == S.E_DSB_BAD_WINDOW)
    nq0 = _count(ds_conn, "dataset_subscriptions")
    ok_q1 = ds.subscribe("usr:bob", "city-quarterly", "2026-Q1",
                         "ref-q-1")
    bad_quarterly = []
    for w in ("2026-Q0", "2026-Q5", "2026-q1", "2026-Q", "2026Q1",
              "2026-Q1\n"):
        ok_w, code_w = expect_error(
            lambda x=w: ds.subscribe("usr:bob", "city-quarterly", x,
                                     "ref-badq-" + str(len(bad_quarterly))),
            S.E_DSB_BAD_WINDOW)
        bad_quarterly.append(ok_w and code_w == S.E_DSB_BAD_WINDOW)
    ok_cross1, code_cross1 = expect_error(
        lambda: ds.subscribe("usr:bob", "city-quarterly", "2026-10",
                            "ref-cross-1"),
        S.E_DSB_BAD_WINDOW)
    ok_cross2, code_cross2 = expect_error(
        lambda: ds.subscribe("usr:bob", "city-mobility", "2026-Q1",
                            "ref-cross-2"),
        S.E_DSB_BAD_WINDOW)
    nq1 = _count(ds_conn, "dataset_subscriptions")
    record("AC-DSB2",
           ok_m01["spend_tx"] and ok_m12["spend_tx"] and ok_q1["spend_tx"]
           and all(bad_monthly) and all(bad_quarterly)
           and ok_cross1 and code_cross1 == S.E_DSB_BAD_WINDOW
           and ok_cross2 and code_cross2 == S.E_DSB_BAD_WINDOW
           and nq1 == nq0 + 1,
           "edges 01/12/Q1 ok; monthly-bad %d/12 quarterly-bad %d/6"
           " cross-period %s/%s; rows %d==%d+1"
           % (sum(bad_monthly), sum(bad_quarterly), ok_cross1,
              ok_cross2, nq1, nq0))

    # -- AC-DSB3 subscription idempotency + exactly one spend --------------
    b0 = bal("carol")
    spend0 = tx_count("spend")
    s1 = ds.subscribe("usr:carol", "city-mobility", "2026-10",
                       "ref-carol-1010")
    b1 = bal("carol")
    spend1 = tx_count("spend")
    srow = ds_conn.execute(
        "SELECT price_cent, bound_spend_tx FROM"
        " dataset_subscriptions WHERE purchase_ref = ?",
        ("ref-carol-1010",)).fetchone()
    ok_dupwin, _ = expect_error(
        lambda: ds.subscribe("usr:carol", "city-mobility", "2026-10",
                             "ref-carol-1010b"),
        S.E_DSB_DUP)
    b2 = bal("carol")
    ok_dupref, _ = expect_error(
        lambda: ds.subscribe("usr:carol", "city-mobility", "2026-11",
                             "ref-carol-1010"),
        S.E_DSB_DUP)
    b3 = bal("carol")
    s2 = ds.subscribe("usr:carol", "city-mobility", "2026-11",
                      "ref-carol-1011")
    b4 = bal("carol")
    spend2 = tx_count("spend")
    ok_unkds, _ = expect_error(
        lambda: ds.subscribe("usr:carol", "no-such-set", "2026-10",
                             "ref-carol-unk"),
        S.E_DSB_UNKNOWN_DATASET)
    ns0 = _count(ds_conn, "dataset_subscriptions")
    ok_ledger_reject = False
    try:
        ds.subscribe("usr:poor", "city-mobility", "2026-10",
                     "ref-poor-1010")
    except L.LedgerError as exc:
        ok_ledger_reject = (exc.code == L.E_NEGATIVE_BALANCE)
    except S.DataSubError:
        ok_ledger_reject = False
    ns1 = _count(ds_conn, "dataset_subscriptions")
    record("AC-DSB3",
           b0 - b1 == 99 and b1 - b2 == 0 and b2 - b3 == 0
           and spend1 - spend0 == 1 and b3 - b4 == 99
           and spend2 - spend1 == 1
           and srow[0] == 99 and srow[1] == s1["spend_tx"]
           and s2["spend_tx"] != s1["spend_tx"]
           and ok_dupwin and ok_dupref and ok_unkds
           and ok_ledger_reject and ns1 == ns0,
           "carol -99 spend 1; dup-window=%s dup-ref=%s zero charge"
           " (b %d==%d==%d); other window -99 tx distinct;"
           " unknown=%s ledger-reject=%s rows %d==%d"
           % (ok_dupwin, ok_dupref, b1, b2, b3, ok_unkds,
              ok_ledger_reject, ns0, ns1))

    # -- AC-DSB4 delivery gate + voucher rows -------------------------------
    tx_b = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    d0 = _count(ds_conn, "dataset_deliveries")
    ok_nosub, code_nosub = expect_error(
        lambda: ds.deliver("usr:ada", "city-mobility", "2026-10",
                           "dlv-ada-1010"),
        S.E_DSB_NOT_SUBSCRIBED)
    d1 = _count(ds_conn, "dataset_deliveries")
    bundle = ds.deliver("usr:carol", "city-mobility", "2026-10",
                        "dlv-carol-1010")
    d2 = _count(ds_conn, "dataset_deliveries")
    again_bundle = ds.deliver("usr:carol", "city-mobility", "2026-10",
                             "dlv-carol-1010b")
    d3 = _count(ds_conn, "dataset_deliveries")
    ok_dupdlv, _ = expect_error(
        lambda: ds.deliver("usr:carol", "city-mobility", "2026-10",
                           "dlv-carol-1010"),
        S.E_DSB_DUP)
    d4 = _count(ds_conn, "dataset_deliveries")
    ok_badwin, _ = expect_error(
        lambda: ds.deliver("usr:carol", "city-mobility", "2026-Q1",
                           "dlv-carol-q"),
        S.E_DSB_BAD_WINDOW)
    tx_a = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    record("AC-DSB4",
           ok_nosub and code_nosub == S.E_DSB_NOT_SUBSCRIBED
           and d1 == d0 and d2 == d0 + 1 and d3 == d0 + 2 and ok_dupdlv
           and d4 == d3 and ok_badwin and tx_a == tx_b
           and bundle["period_window"] == "2026-10"
           and again_bundle["period_window"] == "2026-10",
           "not-subscribed=%s rows %d->%d(redeliver %d, dup-unchanged %d)"
           " dup-ref=%s bad-window=%s ledger_tx %d==%d"
           " (zero token movement)"
           % (ok_nosub, d0, d2, d3, d4, ok_dupdlv, ok_badwin, tx_b,
              tx_a))

    # -- AC-DSB5 de-identification + non-advisory residency ---------------
    keys_ok = set(bundle.keys()) == BUNDLE_KEYS
    with open(os.path.join(BASE, "datasub.py"), "rb") as handle:
        mod_src = handle.read().decode("ascii")
    own_tables = ("dataset_registry", "dataset_subscriptions",
                  "dataset_deliveries")
    from_lines = [ln for ln in mod_src.splitlines()
                  if "FROM " in ln.upper()]
    foreign_reads = [ln.strip() for ln in from_lines
                     if not any(t in ln for t in own_tables)]
    notice_ok = (bundle["disclaimer_first"] == S.NON_ADVISORY
                 and bundle["disclaimer_last"] == S.NON_ADVISORY)
    record("AC-DSB5",
           keys_ok and not foreign_reads and notice_ok,
           "bundle key-set exact=%s foreign-SELECT lines=%d"
           " notice-first/last=%s"
           % (keys_ok, len(foreign_reads), notice_ok))

    # -- AC-DSB6 AIGC label + resident disclaimer --------------------------
    ok_nodisc, _ = expect_error(
        lambda: S.DatasetSubscriptionFace(led, "  "),
        S.E_DSB_NO_DISCLAIMER)
    view = ds.dataset_view("city-mobility")
    sview = ds.subscription_view("usr:carol")
    recon = ds.reconcile_dataset("city-mobility")
    env_ok = all(x.get("disclaimer") == DISCLAIMER
                 for x in (view, sview, recon, r1, bundle))
    ai_ok = (view["ai_label"] == 0
             and ds.dataset_view("city-quarterly")["ai_label"] == 1
             and r2["ai_label"] == 1 and bundle["ai_label"] == 0)
    ok_ai2 = False
    try:
        ds_conn.execute(
            "INSERT INTO dataset_registry (dataset_key, title, period,"
            " price_cent, dataset_digest, ai_label, registered_utc)"
            " VALUES (?,?,?,?,?,?,?)",
            ("hack-row", "t", "monthly", 5, "d", 2, "z"))
    except sqlite3.IntegrityError:
        ok_ai2 = True
    finally:
        ds_conn.rollback()   # release the implicit write txn
    record("AC-DSB6",
           ok_nodisc and env_ok and ai_ok and ok_ai2,
           "empty-disclaimer=%s envelopes=%s ai view 0/1=%s"
           " ai_label=2 db-check=%s"
           % (ok_nodisc, env_ok, ai_ok, ok_ai2))

    # -- AC-DSB7 reconcile read face + hard laws ----------------------------
    clean = ds.reconcile_dataset("city-mobility")
    ds_conn.execute(
        "INSERT INTO dataset_deliveries (delivery_ref, account,"
        " dataset_key, period_window, delivered_utc)"
        " VALUES (?,?,?,?,?)",
        ("hack-orphan", "usr:ghost", "city-mobility", "2026-10", "z"))
    ds_conn.commit()   # cross-connection visibility (WAL committed)
    tampered = ds.reconcile_dataset("city-mobility")
    ds_conn.execute(
        "DELETE FROM dataset_deliveries WHERE delivery_ref = ?",
        ("hack-orphan",))
    ds_conn.commit()   # test hygiene only; module itself is append-only
    post = ds.reconcile_dataset("city-mobility")
    with open(os.path.join(BASE, "datasub.py"), "rb") as handle:
        src_bytes = handle.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    src_text = src_bytes.decode("ascii")
    upd_lines = [ln for ln in src_text.splitlines()
                 if ".execute(" in ln
                 and ("UPDATE" in ln.upper() or "DELETE" in ln.upper())]
    import_lines = [ln for ln in src_text.splitlines()
                    if ln.startswith("import ")
                    or ln.startswith("from ")]
    net_ok = not any(re.search(r"\b(urllib|requests|socket|http)\b", ln)
                     for ln in import_lines)
    rng_ok = ("import random" not in src_text
              and "random." not in src_text)
    with open(cfg_path, "rb") as handle:
        cfg_sha_after = hashlib.sha256(handle.read()).hexdigest()
    ledger_tables_after = set(
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"))
    indep_ok = (os.path.exists(ds.db_path)
                and not any(name.startswith("dataset_")
                           for name in ledger_tables_after))
    record("AC-DSB7",
           clean["balanced"] and clean["subscriptions"] == 4
           and not clean["orphan_deliveries"]
           and (not tampered["balanced"])
           and tampered["orphan_deliveries"] == ["hack-orphan"]
           and post["balanced"] and post["deliveries"] == 2
           and ascii_ok and not upd_lines and net_ok and rng_ok
           and cfg_sha_after == cfg_sha_before and indep_ok
           and clean["billed_total_cent"] == 4 * 99,
           "clean balanced=%s subs=%d billed=%d; orphan-injection"
           " flip=%s named; post-rollback balanced=%s; ascii=%s"
           " upd/del-execute-lines=%d net=%s rng=%s config-stable=%s"
           " independent-db=%s"
           % (clean["balanced"], clean["subscriptions"],
              clean["billed_total_cent"], not tampered["balanced"],
              post["balanced"], ascii_ok, len(upd_lines), net_ok, rng_ok,
              cfg_sha_after == cfg_sha_before, indep_ok))

    ds.close()
    ds_conn.close()
    conn.close()
    print("", flush=True)
    fails = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fails == 0 else "FAIL",
                              len(RESULTS) - fails, len(RESULTS)),
          flush=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
