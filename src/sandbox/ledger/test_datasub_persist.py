"""Cross-restart persistence window for the city public dataset
subscription face (BigDomain R1935; the datasub seat of the
R1886 persist-family lineage - the R1931-seeded row, criteria
pre-registered in the R1935 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay -> restart-surviving gate probes (zero drift) ->
post-restart real-path continuation -> frozen faces + zero
cross-dataset permeation -> pure-read law -> third instance
stability. subscription_view rows carry subscribed_utc (a
persisted value, not a clock echo), so full-dump byte-identity
holds without clock freezing; the evidence digests mask the
ts and spend-tx fields (banded projection, R1902 law) so the
suite stdout stays deterministic across double runs.

Usage: python test_datasub_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import datasub as S          # noqa: E402  (R1764 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: city public dataset"
              " subscription delivers aggregate operational"
              " statistics, not investment advice")

_TS_RE = re.compile(r'"subscribed_utc": "[^"]*"')
_TX_RE = re.compile(r'"spend_tx": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except S.DataSubError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    out = _TS_RE.sub('"subscribed_utc": "<ts>"', text)
    return _TX_RE.sub('"spend_tx": "<tx>"', out)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path, ds_path):
    out = {}
    conn = sqlite3.connect(db_path)
    for tbl in ("ledger_tx", "ledger_entries"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    dconn = sqlite3.connect(ds_path)
    for tbl in ("dataset_registry", "dataset_subscriptions",
                "dataset_deliveries"):
        out[tbl] = int(dconn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    dconn.close()
    return out


def read_faces(ds, led):
    return {
        "bundle_mob": dump(ds.dataset_bundle("city-mobility", "2026-10")),
        "view_mob": dump(ds.dataset_view("city-mobility")),
        "view_q": dump(ds.dataset_view("city-quarterly")),
        "sview_ada": dump(ds.subscription_view("usr:ada")),
        "sview_bob": dump(ds.subscription_view("usr:bob")),
        "sview_carol": dump(ds.subscription_view("usr:carol")),
        "sview_dave": dump(ds.subscription_view("usr:dave")),
        "recon_mob": dump(ds.reconcile_dataset("city-mobility")),
        "recon_q": dump(ds.reconcile_dataset("city-quarterly")),
        "bal_ada": led.balance("usr:ada")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def face_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="datasub-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    dsmod_sha_before = sha16(io_read(os.path.join(BASE, "datasub.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    ds = S.DatasetSubscriptionFace(led, DISCLAIMER)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-DSP-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.ensure_account("usr:dave", census_avatar_id="dave")
    led.adjust([("pool:reserve", "debit", 2000),
                ("usr:ada", "credit", 2000)],
               "manual:dsp-fund-ada", "persist window funding ada")
    led.adjust([("pool:reserve", "debit", 3000),
                ("usr:bob", "credit", 3000)],
               "manual:dsp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 1000),
                ("usr:carol", "credit", 1000)],
               "manual:dsp-fund-carol", "persist window funding carol")

    # ---- AC-DSP1: anchor world, real paths, pre-close snapshot ------
    ds.register_dataset("city-mobility", "City Mobility Index",
                        "monthly", 99, "digest-mob-1", False)
    ds.register_dataset("city-quarterly", "City Economy Quarterly",
                        "quarterly", 999, "digest-q-1", True)
    s_ada_01 = ds.subscribe("usr:ada", "city-mobility", "2026-01",
                            "dsp-ada-0101")
    s_ada_12 = ds.subscribe("usr:ada", "city-mobility", "2026-12",
                            "dsp-ada-1212")
    s_carol = ds.subscribe("usr:carol", "city-mobility", "2026-10",
                           "dsp-carol-1010")
    s_bob = ds.subscribe("usr:bob", "city-quarterly", "2026-Q1",
                         "dsp-bob-q1")
    ds.deliver("usr:carol", "city-mobility", "2026-10", "dsp-dlv-carol-1")
    ds.deliver("usr:carol", "city-mobility", "2026-10", "dsp-dlv-carol-2")
    dlv_ada = ds.deliver("usr:ada", "city-mobility", "2026-01",
                         "dsp-dlv-ada-01")
    ok_dupwin_pre, code_dupwin_pre = expect_error(
        lambda: ds.subscribe("usr:ada", "city-mobility", "2026-01",
                            "dsp-dupwin-fresh"), S.E_DSB_DUP)
    ok_dupref_pre, code_dupref_pre = expect_error(
        lambda: ds.subscribe("usr:carol", "city-mobility", "2026-11",
                            "dsp-ada-0101"), S.E_DSB_DUP)
    ok_nosub_pre, code_nosub_pre = expect_error(
        lambda: ds.deliver("usr:ada", "city-mobility", "2026-11",
                           "dsp-dlv-ada-11"), S.E_DSB_NOT_SUBSCRIBED)
    snap = read_faces(ds, led)
    cnt1 = table_counts(db_path, ds.db_path)
    view_mob = json.loads(snap["view_mob"])
    view_q = json.loads(snap["view_q"])
    recon_mob = json.loads(snap["recon_mob"])
    recon_q = json.loads(snap["recon_q"])
    sview_ada = json.loads(snap["sview_ada"])
    sview_carol = json.loads(snap["sview_carol"])
    sview_dave = json.loads(snap["sview_dave"])
    ok1 = (s_ada_01["price_cent"] == 99 and s_bob["price_cent"] == 999
           and all(r["spend_tx"] for r in (s_ada_01, s_ada_12, s_carol,
                                           s_bob))
           and dlv_ada["period_window"] == "2026-01"
           and view_mob["subscriber_count"] == 3
           and view_mob["delivery_count"] == 3
           and view_mob["ai_label"] == 0
           and view_q["subscriber_count"] == 1
           and view_q["delivery_count"] == 0
           and view_q["ai_label"] == 1
           and recon_mob == {"dataset_key": "city-mobility",
                             "subscriptions": 3, "deliveries": 3,
                             "orphan_deliveries": [],
                             "missing_spend_tx": [], "balanced": True,
                             "billed_total_cent": 297,
                             "disclaimer": DISCLAIMER}
           and recon_q["subscriptions"] == 1 and recon_q["deliveries"] == 0
           and recon_q["balanced"] is True
           and recon_q["billed_total_cent"] == 999
           and len(sview_ada["subscriptions"]) == 2
           and sview_ada["subscriptions"][0]["deliveries"] == 1
           and sview_ada["subscriptions"][1]["deliveries"] == 0
           and len(sview_carol["subscriptions"]) == 1
           and sview_carol["subscriptions"][0]["deliveries"] == 2
           and sview_dave["subscriptions"] == []
           and snap["bal_ada"] == 1802 and snap["bal_bob"] == 2001
           and snap["bal_carol"] == 901 and snap["bal_pool"] == 15296
           and ok_dupwin_pre and code_dupwin_pre == S.E_DSB_DUP
           and ok_dupref_pre and code_dupref_pre == S.E_DSB_DUP
           and ok_nosub_pre and code_nosub_pre == S.E_DSB_NOT_SUBSCRIBED
           and cnt1["dataset_registry"] == 2
           and cnt1["dataset_subscriptions"] == 4
           and cnt1["dataset_deliveries"] == 3
           and cnt1["spend_tx"] == 4)
    record("AC-DSP1", ok1,
           "anchor world: 2 datasets, 4 subs (ada two-window x99,"
           " carol x99, bob x999), 3 deliveries (carol redownload x2,"
           " ada x1); views mobility 3/3 ai=0, quarterly 1/0 ai=1;"
           " reconcile balanced 297/999; balances ada=%d bob=%d"
           " carol=%d pool=%d; pre-close gates dup-window=%s"
           " dup-ref=%s not-subscribed=%s; five-table counts %s"
           % (snap["bal_ada"], snap["bal_bob"], snap["bal_carol"],
              snap["bal_pool"], code_dupwin_pre, code_dupref_pre,
              code_nosub_pre,
              {k: cnt1[k] for k in ("dataset_registry",
                                    "dataset_subscriptions",
                                    "dataset_deliveries", "spend_tx")})
           + "; snapshot digest(sha16,ts/tx-masked) " +
           evidence_digest(snap))

    # ---- AC-DSP2: close -> reopen -> byte-identical replay -----------
    ds.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    ds2 = S.DatasetSubscriptionFace(led2, DISCLAIMER)
    snap2 = read_faces(ds2, led2)
    diffs2 = face_diffs(snap, snap2)
    ok2 = not diffs2
    record("AC-DSP2", ok2,
           "instance2 same db/config replays all 13 snapshot values"
           " (nine read faces + four balances) byte-identical"
           " (diff keys=%s, digest %s)"
           % (diffs2 if diffs2 else "none",
              evidence_digest(snap2)))

    # ---- AC-DSP3: gate laws survive the restart, zero drift ----------
    cnt3_before = table_counts(db_path, ds2.db_path)
    bal3_before = (led2.balance("usr:ada")["balance"],
                   led2.balance("usr:bob")["balance"],
                   led2.balance("usr:carol")["balance"],
                   led2.balance("usr:dave")["balance"])
    ok_dupwin, code_dupwin = expect_error(
        lambda: ds2.subscribe("usr:ada", "city-mobility", "2026-01",
                              "dsp2-dupwin"), S.E_DSB_DUP)
    ok_dupref, code_dupref = expect_error(
        lambda: ds2.subscribe("usr:carol", "city-mobility", "2026-11",
                              "dsp-ada-0101"), S.E_DSB_DUP)
    ok_dupdlv, code_dupdlv = expect_error(
        lambda: ds2.deliver("usr:carol", "city-mobility", "2026-10",
                           "dsp-dlv-carol-1"), S.E_DSB_DUP)
    ok_nosub, code_nosub = expect_error(
        lambda: ds2.deliver("usr:ada", "city-mobility", "2026-11",
                            "dsp2-dlv-ada-11"),
        S.E_DSB_NOT_SUBSCRIBED)
    ok_badwin, code_badwin = expect_error(
        lambda: ds2.subscribe("usr:bob", "city-mobility", "2026-Q2",
                              "dsp2-badwin"), S.E_DSB_BAD_WINDOW)
    ok_conflict, code_conflict = expect_error(
        lambda: ds2.register_dataset("city-mobility", "Renamed",
                                     "monthly", 99, "digest-mob-1",
                                     False), S.E_DSB_DUP)
    idem = ds2.register_dataset("city-mobility", "City Mobility Index",
                                "monthly", 99, "digest-mob-1", False)
    cnt3_after = table_counts(db_path, ds2.db_path)
    bal3_after = (led2.balance("usr:ada")["balance"],
                  led2.balance("usr:bob")["balance"],
                  led2.balance("usr:carol")["balance"],
                  led2.balance("usr:dave")["balance"])
    ok3 = (ok_dupwin and code_dupwin == S.E_DSB_DUP
           and ok_dupref and code_dupref == S.E_DSB_DUP
           and ok_dupdlv and code_dupdlv == S.E_DSB_DUP
           and ok_nosub and code_nosub == S.E_DSB_NOT_SUBSCRIBED
           and ok_badwin and code_badwin == S.E_DSB_BAD_WINDOW
           and ok_conflict and code_conflict == S.E_DSB_DUP
           and idem["idempotent"] is True
           and cnt3_before == cnt3_after and bal3_before == bal3_after)
    record("AC-DSP3", ok3,
           "post-restart gates: dup-window=%s dup-ref=%s dup-delivery=%s"
           " not-subscribed=%s bad-window=%s register-conflict=%s"
           " register-idem=%s; counts constant %s; four balances"
           " zero-moved (%s==%s)"
           % (code_dupwin, code_dupref, code_dupdlv, code_nosub,
              code_badwin, code_conflict, idem["idempotent"],
              {k: cnt3_after[k] for k in ("dataset_subscriptions",
                                          "dataset_deliveries",
                                          "spend_tx")},
              bal3_before, bal3_after))

    # ---- AC-DSP4: post-restart continuation + bound-tx cross-check ---
    b4 = ds2.subscribe("usr:bob", "city-quarterly", "2026-Q2",
                       "dsp2-bob-q2")
    a4 = ds2.subscribe("usr:ada", "city-quarterly", "2026-Q1",
                       "dsp2-ada-q1")
    ds2.deliver("usr:carol", "city-mobility", "2026-10",
                "dsp2-dlv-carol-3")
    dconn = sqlite3.connect(ds2.db_path)
    bound = {}
    for ref in ("dsp2-bob-q2", "dsp2-ada-q1"):
        bound[ref] = dconn.execute(
            "SELECT bound_spend_tx FROM dataset_subscriptions"
            " WHERE purchase_ref = ?", (ref,)).fetchone()[0]
    dconn.close()
    conn = sqlite3.connect(db_path)
    tx_checks = []
    for ref, account in (("dsp2-bob-q2", "usr:bob"),
                        ("dsp2-ada-q1", "usr:ada")):
        head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                            (bound[ref],)).fetchone()
        leg = conn.execute(
            "SELECT direction FROM ledger_entries WHERE tx_id = ?"
            " AND account_id = ?", (bound[ref], account)).fetchone()
        tx_checks.append(head is not None and head[0] == "spend"
                         and leg is not None and leg[0] == "debit")
    conn.close()
    view_q4 = ds2.dataset_view("city-quarterly")
    view_mob4 = ds2.dataset_view("city-mobility")
    sview_carol4 = ds2.subscription_view("usr:carol")
    recon_q4 = ds2.reconcile_dataset("city-quarterly")
    bal_ada4 = led2.balance("usr:ada")["balance"]
    bal_bob4 = led2.balance("usr:bob")["balance"]
    bal_pool4 = led2.balance("pool:reserve")["balance"]
    ok4 = (b4["price_cent"] == 999 and a4["price_cent"] == 999
           and b4["spend_tx"] and a4["spend_tx"]
           and all(tx_checks)
           and view_q4["subscriber_count"] == 3
           and view_q4["delivery_count"] == 0
           and view_mob4["subscriber_count"] == 3
           and view_mob4["delivery_count"] == 4
           and sview_carol4["subscriptions"][0]["deliveries"] == 3
           and recon_q4["subscriptions"] == 3
           and recon_q4["deliveries"] == 0
           and recon_q4["balanced"] is True
           and recon_q4["billed_total_cent"] == 2997
           and bal_ada4 == 803 and bal_bob4 == 1002
           and bal_pool4 == 17294)
    record("AC-DSP4", ok4,
           "post-restart continuation: bob Q2 -999 -> %d, ada Q1 -999"
           " -> %d, carol redelivery row (zero token); both new subs"
           " bound to real spend tx (type=spend, debit entry)=%s;"
           " derived recompute zero-cache: quarterly subs 1->3"
           " deliveries 0, mobility deliveries 3->4, carol window"
           " deliveries 2->3, reconcile quarterly balanced billed"
           " 2997; pool=%d" % (bal_bob4, bal_ada4,
                                all(tx_checks), bal_pool4))

    # ---- AC-DSP5: frozen faces + zero cross-dataset permeation -------
    bundle_now = ds2.dataset_bundle("city-mobility", "2026-10")
    sview_dave_now = ds2.subscription_view("usr:dave")
    recon_mob5 = ds2.reconcile_dataset("city-mobility")
    ok5 = (dump(bundle_now) == snap["bundle_mob"]
           and dump(sview_dave_now) == snap["sview_dave"]
           and recon_mob5["subscriptions"] == 3
           and recon_mob5["deliveries"] == 4
           and recon_mob5["billed_total_cent"] == 297
           and recon_mob5["balanced"] is True
           and recon_q4["deliveries"] == 0
           and recon_q4["subscriptions"] == 3)
    record("AC-DSP5", ok5,
           "frozen faces: descriptor bundle byte==anchor; untouched"
           " dave subscription_view byte==anchor (zero subs);"
           " reconcile mobility counts == anchor+1 delivery only"
           " (subs 3, billed 297 - quarterly spends do not permeate);"
           " reconcile quarterly carries zero mobility rows"
           " (deliveries 0, subs 3) - cross-dataset isolation both"
           " ways")

    # ---- AC-DSP6: pure-read law + double-restart stability -----------
    snap_post = read_faces(ds2, led2)
    cnt6_before = table_counts(db_path, ds2.db_path)
    read_faces(ds2, led2)
    read_faces(ds2, led2)
    cnt6_after = table_counts(db_path, ds2.db_path)
    ds2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    ds3 = S.DatasetSubscriptionFace(led3, DISCLAIMER)
    snap3 = read_faces(ds3, led3)
    diffs6 = face_diffs(snap_post, snap3)
    ok6 = (cnt6_before == cnt6_after and not diffs6)
    record("AC-DSP6", ok6,
           "read battery leaves all five table counts constant %s;"
           " third instance replays the post-continuation state"
           " byte-identical (diff keys=%s, digest %s)"
           % ({k: cnt6_after[k] for k in ("ledger_tx", "ledger_entries",
                                          "dataset_subscriptions",
                                          "dataset_deliveries")},
              diffs6 if diffs6 else "none",
              evidence_digest(snap3)))

    # ---- AC-DSP7: hygiene ---------------------------------------------
    cfg_sha_after = sha16(io_read(cfg_path))
    dsmod_sha_after = sha16(io_read(os.path.join(BASE, "datasub.py")))
    ledmod_sha_after = sha16(io_read(os.path.join(BASE, "ledger.py")))
    reg_src = io_read(os.path.join(os.path.dirname(BASE),
                                   "reconcile_all.py"))
    reg_ok = ('"ledger-datasub-persist"' in reg_src
              and '"test_datasub_persist.py"), 7)' in reg_src)
    own_src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in own_src if ord(ch) > 127)
    import_lines = [ln for ln in own_src.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    network = [ln for ln in import_lines
               if any(w in ln for w in ("urllib", "requests", "socket",
                                        "http"))]
    ok7 = (cfg_sha_before == cfg_sha_after
           and dsmod_sha_before == dsmod_sha_after
           and ledmod_sha_before == ledmod_sha_after
           and reg_ok and non_ascii == 0 and not network
           and tmp.startswith(tempfile.gettempdir()))
    record("AC-DSP7", ok7,
           "shipped config sha16 stable %s; datasub.py/ledger.py"
           " sha16 stable (%s/%s); SUITES registration row=%s;"
           " own source pure-ascii=%d network-imports=%d; world tmp"
           " outside repo=%s"
           % (cfg_sha_after, dsmod_sha_before == dsmod_sha_after,
              ledmod_sha_before == ledmod_sha_after, reg_ok,
              non_ascii, len(network),
              tmp.startswith(tempfile.gettempdir())))

    ds3.close()
    led3.close()
    print("", flush=True)
    fails = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fails == 0 else "FAIL",
                              len(RESULTS) - fails, len(RESULTS)),
          flush=True)
    sys.exit(0 if fails == 0 else 2)


if __name__ == "__main__":
    main()
