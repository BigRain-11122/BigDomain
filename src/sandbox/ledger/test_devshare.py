"""Acceptance suite for the developer revenue-share gradient
settlement face (BigDomain explore queue, claimed round R1759).
Asserts the pre-registered criteria AC-DS1..AC-DS7 from the
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Usage: python test_devshare.py
"""

import hashlib
import inspect
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700 face)
import incentive as IN                  # noqa: E402 (R600 gradient)
import devshare as DS                   # noqa: E402 (R1759 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: revenue-share settlement"
              " is a platform accounting face, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except Exception as exc:                     # noqa: BLE001
        code = getattr(exc, "code", type(exc).__name__)
        return code in codes, code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="devshare-ac-")
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, encoding="utf-8") as handle:
        cfg = json.load(handle)
    with open(cfg_path, "rb") as handle:
        cfg_sha_before = hashlib.sha256(handle.read()).hexdigest()

    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    inc = IN.IncentiveFace(led)          # UGC-params face (AC-DS4 cross)
    conn = sqlite3.connect(db_path)

    def tables():
        return set(r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall())

    def share_count():
        return conn.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type='share'"
        ).fetchone()[0]

    def bal(who):
        return led.balance("usr:" + who)["balance"]

    led.mint_to_pool("pool:share", 4000, "MINT-DS-SHARE", "settlement")
    led.mint_to_pool("pool:reserve", 5000, "MINT-DS-RES", "settlement")
    for who in ("ada", "lin", "ghost"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    for who, tag in (("ada", "a"), ("lin", "l")):
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:ds-fund-" + tag, "suite funding " + who)

    k1 = dk.issue_key("usr:ada", "alpha", 50, ["backtest"], True)
    k2 = dk.issue_key("usr:lin", "beta", 50, ["visualize"], True)
    dk.buy_credits(k1["api_key"], 40, 5, "PACK-DS-A")
    dk.buy_credits(k2["api_key"], 20, 5, "PACK-DS-B")
    for i in range(12):
        dk.call(k1["api_key"], "backtest",
                "ds-call-a-%d" % i, "eng-a-%d" % i)
    for i in range(5):
        dk.call(k2["api_key"], "visualize",
                "ds-call-b-%d" % i, "eng-b-%d" % i)

    tables_before_inc_window = tables()       # post-IncentiveFace build
    ds = DS.DevShareFace(led, dk, DISCLAIMER)
    tables_after_ds = tables()
    # captured BEFORE any settlement (the read face reads the shared
    # incentive_windows table, so the empty-world reading must be
    # taken before the first settle)
    empty_read = ds.devshare_windows()

    # ---------- AC-DS1: constructor fail-closed ----------
    ok_none_led, c1 = expect_error(
        lambda: DS.DevShareFace(None, dk, DISCLAIMER), DS.E_DS_BAD_ARGS)
    ok_none_dk, c2 = expect_error(
        lambda: DS.DevShareFace(led, None, DISCLAIMER), DS.E_DS_BAD_ARGS)
    ok_no_board, c3 = expect_error(
        lambda: DS.DevShareFace(led, object(), DISCLAIMER),
        DS.E_DS_BAD_ARGS)
    ok_no_disc, c4 = expect_error(
        lambda: DS.DevShareFace(led, dk, "   "), DS.E_DS_NO_DISCLAIMER)
    ok_params = (ds.params["bands"] == DS.DEVSHARE_PARAMS["bands"]
                 and DS.DEVSHARE_PARAMS["bands"]
                 != IN.SANDBOX_PARAMS["bands"]
                 and ds.params["collar"] == DS.DEVSHARE_PARAMS["collar"])
    ok_table_stable = tables_before_inc_window == tables_after_ds
    record("AC-DS1", ok_none_led and ok_none_dk and ok_no_board
           and ok_no_disc and ok_params and ok_table_stable,
           "rejects=%s/%s/%s/%s default-params-distinct=%s"
           " table-set-stable=%s" % (c1, c2, c3, c4, ok_params,
                                     ok_table_stable))

    # ---------- AC-DS2: developer-registry gate ----------
    shares_0 = share_count()
    bal_ada_0, bal_ghost_0 = bal("ada"), bal("ghost")
    ok_gate_ghost, cg = expect_error(
        lambda: ds.settle_window("w-gate", [("usr:ghost", 5)]),
        DS.E_DS_NOT_DEV)
    ok_gate_nonusr, cn = expect_error(
        lambda: ds.settle_window("w-gate2", [("ent:corp", 5)]),
        D.E_AD_BAD_ARGS)
    ok_zero_move = (share_count() == shares_0
                    and bal("ada") == bal_ada_0
                    and bal("ghost") == bal_ghost_0)
    record("AC-DS2", ok_gate_ghost and ok_gate_nonusr and ok_zero_move,
           "ghost=%s non-usr=%s zero-movement=%s (codes %s/%s)"
           % (ok_gate_ghost, ok_gate_nonusr, ok_zero_move, cg, cn))

    # ---------- AC-DS3: structure reuse + one share tx ----------
    ok_ref_same = DS._GRADIENT_REF is IN.payout_for
    ok_grad = (DS._GRADIENT_REF(12, ds.params) == 34
               and DS._GRADIENT_REF(5, ds.params) == 15)
    r1 = ds.settle_window("w1", [("usr:ada", 12), ("usr:lin", 5)])
    ok_paid = (r1["paid"] == [("usr:ada", 34), ("usr:lin", 15)])
    ok_env = (set(r1.keys()) == {"window_id", "paid", "disclaimer"}
              and r1["disclaimer"] == DISCLAIMER
              and r1["window_id"] == "w1")
    ok_tx = (share_count() == shares_0 + 2
             and bal("ada") == bal_ada_0 + 34)
    # collar enforcement flows through the composed face (custom params)
    ds_cap = DS.DevShareFace(led, dk, DISCLAIMER,
                             params={"bands": [(3, 5)], "collar": 7,
                                     "budget": 10})
    r_cap = ds_cap.settle_window("w-cap", [("usr:ada", 10)])
    ok_cap = r_cap["paid"] == [("usr:ada", 7)]
    record("AC-DS3", ok_ref_same and ok_grad and ok_paid and ok_env
           and ok_tx and ok_cap,
           "gradient-ref-shared=%s readings=34/15 paid=%s share-tx"
           " +%d collar-flow=%s" % (ok_ref_same, r1["paid"],
                                    share_count() - shares_0, ok_cap))

    # ---------- AC-DS4: window idempotence + namespace ----------
    bal_ada_1 = bal("ada")               # post w1 + w-cap settlements
    shares_1 = share_count()
    ok_dup, cd = expect_error(
        lambda: ds.settle_window("w1", [("usr:ada", 12),
                                        ("usr:lin", 5)]),
        IN.E_INC_WINDOW_DUP)
    ok_dup_zero = (share_count() == shares_1 and bal("ada") == bal_ada_1)
    # cross-face: a UGC incentive window with the same caller id
    # settles independently (namespace isolation)
    inc.settle_window("w1", [("usr:ada", 3)])      # UGC params: 3*10=30
    ok_cross = bal("ada") == bal_ada_1 + 30
    windows_snap = ds.devshare_windows()
    # prefix filter proof: exactly the two devshare windows are
    # visible with their devshare totals - the raw UGC "w1" row
    # (total 30) stays filtered out by the devshare prefix
    snap_totals = dict((w["window_id"], w["total_paid"])
                       for w in windows_snap["windows"])
    ok_prefix = (len(windows_snap["windows"]) == 2
                 and snap_totals == {"w1": 49, "w-cap": 7})
    record("AC-DS4", ok_dup and ok_dup_zero and ok_cross
           and ok_prefix,
           "re-settle=%s zero-move=%s cross-face-same-id-ok=%s"
           " prefix-filter=%s snap=%s (code %s)" % (
               ok_dup, ok_dup_zero, ok_cross, ok_prefix,
               snap_totals, cd))

    # ---------- AC-DS5: usage-attribution intake ----------
    r2 = ds.settle_from_usage("w2", ["usr:lin", "usr:ada"])
    ok_usage = (r2["paid"] == [("usr:lin", 15), ("usr:ada", 34)])
    ok_no_usage, cu = expect_error(
        lambda: ds.settle_from_usage("w3", ["usr:ghost"]),
        DS.E_DS_NO_USAGE)
    shares_2 = share_count()
    r3 = ds.settle_from_usage("w3", ["usr:ghost", "usr:ada"])
    ok_mixed = (r3["paid"] == [("usr:ada", 34)]
                and share_count() == shares_2 + 1)
    ok_bad_list, cl = expect_error(
        lambda: ds.settle_from_usage("w9", []),
        DS.E_DS_BAD_ARGS)
    ok_bad_type, ct = expect_error(
        lambda: ds.settle_from_usage("w9", "usr:ada"),
        DS.E_DS_BAD_ARGS)
    board = dk.dev_board("usr:ada")
    units_ada = sum(int(k["quota_used"]) for k in board["keys"])
    record("AC-DS5", ok_usage and ok_no_usage and ok_mixed
           and ok_bad_list and ok_bad_type and units_ada == 12,
           "derived-units(ada)=%d paid-order=%s no-usage=%s mixed=%s"
           " bad-args=%s/%s (codes %s/%s/%s)" % (
               units_ada, r2["paid"], ok_no_usage, ok_mixed,
               ok_bad_list, ok_bad_type, cu, cl, ct))

    # ---------- AC-DS6: read face, pure-read law ----------
    ok_empty_env = (empty_read == {"windows": [], "disclaimer":
                                   DISCLAIMER})
    hist = ds.devshare_windows()
    ok_hist_env = set(hist.keys()) == {"windows", "disclaimer"}
    # order-independent content check (settled_utc has second
    # resolution; ties resolve by window_id - both deterministic,
    # but the content equality is the honest assertion)
    hist_totals = dict((w["window_id"], w["total_paid"])
                       for w in hist["windows"])
    ok_hist = (hist_totals == {"w1": 49, "w-cap": 7, "w2": 49,
                               "w3": 34})
    ok_row_keys = all(set(w.keys()) == {"window_id", "total_paid",
                                        "settled_utc"}
                      for w in hist["windows"])
    src = inspect.getsource(DS.DevShareFace.devshare_windows)
    ok_src = not re.search(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b"
                           r"|\bDROP\b", src)
    ok_ro = False
    try:
        ds._dock.execute("CREATE TABLE zz_probe(x)")
    except sqlite3.OperationalError:
        ok_ro = True
    record("AC-DS6", ok_empty_env and ok_hist_env and ok_hist
           and ok_row_keys and ok_src and ok_ro,
           "empty=%s totals=%s row-keys=%s source-select-only=%s"
           " dock-read-only=%s" % (ok_empty_env, hist_totals,
                                   ok_row_keys, ok_src, ok_ro))

    # ---------- AC-DS7: hard laws + delivery wiring ----------
    module_src = open(os.path.join(BASE, "devshare.py"),
                      encoding="ascii").read()
    ok_ascii = True
    with open(os.path.join(BASE, "devshare.py"), "rb") as handle:
        try:
            handle.read().decode("ascii")
        except UnicodeDecodeError:
            ok_ascii = False
    import_lines = [ln.strip() for ln in module_src.splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    ok_no_net = not any(re.search(r"\b(urllib|requests|socket|http)\b",
                                  ln) for ln in import_lines)
    ok_no_random = not any(re.search(r"\brandom\b", ln)
                          for ln in import_lines)
    exec_lines = [ln for ln in module_src.splitlines()
                  if ".execute(" in ln or "executescript(" in ln]
    ok_no_update = not any(re.search(r"\bUPDATE\b|\bDELETE\b"
                                     r"|\bDROP\b|\bINSERT\b", ln)
                           for ln in exec_lines)
    runner_src = open(os.path.join(os.path.dirname(BASE),
                                   "reconcile_all.py"),
                      encoding="utf-8").read()
    ok_wired = bool(re.search(
        r'\("ledger-devshare",\s*\n?\s*os\.path\.join\("ledger",'
        r'\s*\n?\s*"test_devshare\.py"\),\s*7\)', runner_src))
    with open(cfg_path, "rb") as handle:
        cfg_sha_after = hashlib.sha256(handle.read()).hexdigest()
    ok_cfg = cfg_sha_before == cfg_sha_after
    record("AC-DS7", ok_ascii and ok_no_net and ok_no_random
           and ok_no_update and ok_wired and ok_cfg,
           "ascii=%s net-imports=0 random=0 sql-writes=0"
           " suite-wired=%s config-sha-stable=%s" % (
               ok_ascii, ok_wired, ok_cfg))

    ds.close()
    ds_cap.close()
    inc.close()
    conn.close()

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d criteria" % (
        "PASS" if not failed else "FAIL", len(RESULTS) - len(failed),
        len(RESULTS)), flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
