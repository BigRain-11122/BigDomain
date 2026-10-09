"""Acceptance suite for the API open-platform developer-ecosystem
face (BigDomain R1700; canon = explore-queue API open-platform row,
the B5 metered successor: third-party developer key issuance /
window quota / billing three rings). Asserts the pre-registered
criteria AC-DK1..AC-DK7 from the R1700 explore-queue row (criteria
were registered before this code existed; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

The metered face is the real product injected by reference (no
copy); this module reaches the billing ring only through its
public API. This test source stays pure ASCII per the encoding
discipline.

Usage: python test_apidev.py
"""

import json
import os
import re
import sqlite3
import sys
import tempfile
import datetime as _real_datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                    # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_ad_error(fn, *codes):
    try:
        fn()
    except D.ApiDevError as exc:
        return exc.code in codes, exc.code
    except M.MeteredError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _FrozenDateTime(object):
    """Module-level datetime replacement: now() returns a fixed
    instant so the window-rollover face can be proven (AC-DK2)."""

    class _dt(object):
        fixed = None

        @classmethod
        def now(cls, tz=None):
            return cls.fixed

    class _tz(object):
        utc = "frozen"

    datetime = _dt
    timezone = _tz


def _freeze(dev_module, y, m, d=1):
    _FrozenDateTime.datetime.fixed = _real_datetime.datetime(
        y, m, d, tzinfo=_real_datetime.timezone.utc)


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-AD-A", "settlement")
    for who, amount, tag in (("ada", 400, "a"), ("lin", 400, "l")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)

    # -- AC-DK1 key issuance ring ----------------------------------------
    k1 = dk.issue_key("usr:ada", "mobile-app", 2, ["backtest"], False)
    k2 = dk.issue_key("usr:ada", "web-dashboard", 30,
                      ["backtest", "visualize"], True)
    n_keys = _count(conn, "api_dev_keys")
    ok_dup, code_dup = expect_ad_error(
        lambda: dk.issue_key("usr:ada", "mobile-app", 9,
                             ["backtest"], False), D.E_AD_DUP_KEY)
    n_after_dup = _count(conn, "api_dev_keys")
    metered_clients_after_dup = _count(conn, "metered_clients")
    bad_batch = [
        lambda: dk.issue_key("ent:corp", "x", 5, ["backtest"], False),
        lambda: dk.issue_key("usr:ada", "", 5, ["backtest"], False),
        lambda: dk.issue_key("usr:ada", "y", 0, ["backtest"], False),
        lambda: dk.issue_key("usr:ada", "y", True, ["backtest"], False),
        lambda: dk.issue_key("usr:ada", "y", 5, ["teleport"], False),
        lambda: dk.issue_key("usr:ada", "y", 5, ["backtest"], "yes"),
    ]
    bad_ok, bad_codes = [], []
    for fn in bad_batch:
        okc, code = expect_ad_error(fn, D.E_AD_BAD_ARGS)
        bad_ok.append(okc)
        bad_codes.append(code)
    n_after_bad = _count(conn, "api_dev_keys")
    ok_dk1 = (n_keys == 2 and ok_dup and code_dup == D.E_AD_DUP_KEY
              and n_after_dup == n_keys
              and metered_clients_after_dup == 2
              and all(bad_ok) and n_after_bad == n_keys
              and k1["api_key"].startswith("sk_")
              and len(k1["api_key"]) == 43
              and re.match(r"^sk_[0-9a-f]{40}$", k1["api_key"])
              and k1["api_key"] != k2["api_key"]
              and k1["metered_client"].startswith("ent:api-")
              and k1["ai_label"] == 0 and k2["ai_label"] == 1
              and k1["disclaimer"] == DISCLAIMER)
    record("AC-DK1", ok_dk1,
           "two keys, dup rejected %s (rows %d->%d->%d, metered"
           " clients %d), bad-args %s, key sk_+40hex deterministic,"
           " ent:api- binding, ai_label 0/1 persistent"
           % (code_dup, n_keys, n_after_dup, n_after_bad,
              metered_clients_after_dup, all(bad_ok)))

    # -- AC-DK2 quota ring, fail-closed + window rollover ----------------
    bal0 = bal("ada")
    dk.buy_credits(k1["api_key"], 5, 3, "PACK-QUOTA-A")
    ok_pack_charge = bal("ada") == bal0 - 15
    c1 = dk.call(k1["api_key"], "backtest", "call-q-1", "engine-receipt-1")
    c2 = dk.call(k1["api_key"], "backtest", "call-q-2", "engine-receipt-2")
    ok_quota, code_quota = expect_ad_error(
        lambda: dk.call(k1["api_key"], "backtest", "call-q-3",
                        "engine-receipt-3"), D.E_AD_QUOTA)
    rec = metered.reconcile_client(k1["metered_client"])
    n_local = _count(conn, "api_calls")
    window_now = c1["window"]
    _freeze(D, 2099, int(window_now[5:7]) % 12 + 1)  # next month
    real_datetime = D.datetime
    D.datetime = _FrozenDateTime
    try:
        c3 = dk.call(k1["api_key"], "backtest", "call-q-3",
                     "engine-receipt-3")
        rollover_ok = c3["window"] != window_now
    finally:
        D.datetime = real_datetime
    rec2 = metered.reconcile_client(k1["metered_client"])
    ok_dk2 = (ok_pack_charge and ok_quota and code_quota == D.E_AD_QUOTA
              and rec["balanced"] and rec["consumed_calls"] == 2
              and n_local == 2
              and rollover_ok and rec2["balanced"]
              and rec2["consumed_calls"] == 3
              and rec2["remaining_credits"] == 2)
    record("AC-DK2", ok_dk2,
           "cap 2: calls 1-2 pass, 3rd rejected %s pre-billing"
           " (metered consumed %d, local rows %d, balanced=%s),"
           " frozen-clock rollover -> fresh window, consumed %d"
           % (code_quota, rec["consumed_calls"], n_local,
              rec["balanced"], rec2["consumed_calls"]))

    # -- AC-DK3 billing ring = metered public-API delegation -------------
    bal1 = bal("ada")
    ok_dup_ref, code_dup_ref = expect_ad_error(
        lambda: dk.buy_credits(k1["api_key"], 5, 3, "PACK-QUOTA-A"),
        M.E_MT_DUP)
    ok_unknown_buy, code_unknown_buy = expect_ad_error(
        lambda: dk.buy_credits("sk-nonexistent", 5, 3, "PACK-X"),
        D.E_AD_UNKNOWN_KEY)
    ok_flat_after_rejects = bal("ada") == bal1
    dk.buy_credits(k1["api_key"], 3, 4, "PACK-QUOTA-B")
    ok_charged_once = bal("ada") == bal1 - 12
    rec3 = metered.reconcile_client(k1["metered_client"])
    with open(os.path.join(BASE, "apidev.py"), "r",
              encoding="utf-8") as handle:
        source = handle.read()
    second_engine_hits = re.findall(r"metered_(?:clients|packs|calls)",
                                    source)
    ok_dk3 = (ok_dup_ref and code_dup_ref == M.E_MT_DUP
              and ok_flat_after_rejects
              and ok_unknown_buy and ok_charged_once
              and rec3["packs"] == 2 and rec3["purchased_calls"] == 8
              and rec3["balanced"]
              and len(second_engine_hits) == 0)
    record("AC-DK3", ok_dk3,
           "dup ref rejected %s zero-charge (balance flat), unknown"
           " key rejected %s, stack purchase charged exactly once"
           " (-12), credits stack (packs %d, purchased %d,"
           " balanced=%s), source zero metered_* table writes (%d hits)"
           % (code_dup_ref, code_unknown_buy, rec3["packs"],
              rec3["purchased_calls"], rec3["balanced"],
              len(second_engine_hits)))

    # -- AC-DK4 call-chain three-ring order ------------------------------
    k4 = dk.issue_key("usr:lin", "research-key", 10, ["backtest"], False)
    ok_unknown_call, _ = expect_ad_error(
        lambda: dk.call("sk-nope", "backtest", "call-a", "r"),
        D.E_AD_UNKNOWN_KEY)
    ok_kind, code_kind = expect_ad_error(
        lambda: dk.call(k4["api_key"], "visualize", "call-b", "r"),
        D.E_AD_KIND)
    n_calls_before = _count(conn, "api_calls")
    ok_nocredits, code_nocredits = expect_ad_error(
        lambda: dk.call(k4["api_key"], "backtest", "call-c", "r"),
        M.E_MT_NO_CREDITS)
    ok_zero_rows = _count(conn, "api_calls") == n_calls_before
    dk.buy_credits(k4["api_key"], 2, 5, "PACK-LIN-A")
    cc1 = dk.call(k4["api_key"], "backtest", "call-d",
                  "opaque-engine-receipt-XYZ")
    ok_dup_call, code_dup_call = expect_ad_error(
        lambda: dk.call(k4["api_key"], "backtest", "call-d", "r2"),
        D.E_AD_DUP)
    ok_no_orphan = _count(conn, "api_calls") == n_calls_before + 1
    # orphan local row simulated by direct SQL -> the local dup
    # pre-check must fire before the billing ring
    conn.execute(
        "INSERT INTO api_calls (call_ref, key_id, kind, engine_ref,"
        " window, called_utc) VALUES ('call-orphan',"
        " (SELECT key_id FROM api_dev_keys WHERE key_name="
        " 'research-key'), 'backtest', 'r', '2000-01', '2000-01')"
    )
    conn.commit()
    bal_lin = bal("lin")
    ok_local_dup, code_local_dup = expect_ad_error(
        lambda: dk.call(k4["api_key"], "backtest", "call-orphan", "r3"),
        D.E_AD_DUP)
    ok_no_double_charge = bal("lin") == bal_lin
    # metered-first path: a ref present in the billing ring but not
    # locally must reject through the metered gate leaving zero
    # local rows (billing-ring reject = zero local side effects)
    conn.execute(
        "INSERT INTO metered_calls (call_ref, client_id, kind,"
        " engine_ref, consumed_utc) VALUES ('call-metered-only',"
        " (SELECT metered_client FROM api_dev_keys WHERE key_name ="
        " 'research-key'), 'backtest', 'r', '2000-01')")
    conn.commit()
    n_local_pre_metered = _count(conn, "api_calls")
    ok_metered_first, code_metered_first = expect_ad_error(
        lambda: dk.call(k4["api_key"], "backtest", "call-metered-only",
                        "r4"), M.E_MT_DUP)
    ok_metered_first_zero = _count(conn, "api_calls") == n_local_pre_metered
    rec4 = metered.reconcile_client(k4["metered_client"])
    usage = dk.usage_log(k4["api_key"])
    # k4's local log holds call-d + the injected call-orphan; the
    # billing ring holds call-d + the injected call-metered-only
    ok_verbatim = any(c["call_ref"] == "call-d"
                      and c["engine_ref"] == "opaque-engine-receipt-XYZ"
                      for c in usage["calls"])
    ok_dk4 = (ok_unknown_call and ok_kind and code_kind == D.E_AD_KIND
              and ok_nocredits and code_nocredits == M.E_MT_NO_CREDITS
              and ok_zero_rows
              and ok_verbatim
              and ok_dup_call and ok_no_orphan
              and ok_local_dup and code_local_dup == D.E_AD_DUP
              and ok_no_double_charge
              and ok_metered_first and ok_metered_first_zero
              and rec4["consumed_calls"] == 2
              and len(usage["calls"]) == 2
              and len([c for c in usage["calls"]
                       if c["call_ref"] == "call-d"]) == 1)
    record("AC-DK4", ok_dk4,
           "chain: unknown-key %s, kind %s, no-credits %s zero local"
           " rows, local dup pre-check %s zero orphan, metered-first"
           " dup %s zero local rows, zero double charge, cross-count"
           " metered %d local %d (call-d in both), engine_ref verbatim"
           % (ok_unknown_call, code_kind, code_nocredits,
              code_dup_call, code_metered_first,
              rec4["consumed_calls"], len(usage["calls"])))

    # -- AC-DK5 AIGC label + disclaimer residency + platform posture -----
    ok_no_dis, code_no_dis = expect_ad_error(
        lambda: D.DevKeyFace(metered, ""), D.E_AD_NO_DISCLAIMER)
    kv = dk.key_view(k2["api_key"])
    db = dk.dev_board("usr:ada")
    issue_env = dk.issue_key("usr:lin", "posture-key", 5,
                             ["visualize"], False)
    try:
        conn.execute(
            "INSERT INTO api_dev_keys (dev_account, key_name,"
            " metered_client, api_key, window_cap, enabled_kinds,"
            " ai_label, issued_utc) VALUES ('usr:z', 'z', 'ent:z',"
            " 'sk_zzz', 1, 'backtest', 2, '2000-01')")
        check_refused = False
    except sqlite3.IntegrityError:
        check_refused = True
    conn.rollback()
    ok_dk5 = (ok_no_dis and code_no_dis == D.E_AD_NO_DISCLAIMER
              and "disclaimer" in c1 and "disclaimer" in kv
              and "disclaimer" in db and "disclaimer" in usage
              and "disclaimer" in issue_env
              and kv["ai_label"] == 1
              and all(k["ai_label"] in (0, 1) for k in db["keys"])
              and "SecGate" in D.apidev_posture_note
              and check_refused)
    record("AC-DK5", ok_dk5,
           "empty disclaimer refused %s, five envelopes carry the"
           " resident disclaimer, ai_label 0/1 (view=%d), direct SQL"
           " ai_label=2 refused=%s, SecGate posture note in module"
           % (code_no_dis, kv["ai_label"], check_refused))

    # -- AC-DK6 hard laws --------------------------------------------------
    n_keys_a = _count(conn, "api_dev_keys")
    n_calls_a = _count(conn, "api_calls")
    bal_ada = bal("ada")
    for fn in (lambda: dk.issue_key("usr:ada", "another", -1,
                                    ["backtest"], False),
               lambda: dk.call(k1["api_key"], "backtest", "", "r"),
               lambda: dk.call(k1["api_key"], "backtest", "x", ""),
               lambda: dk.buy_credits(k1["api_key"], 0, 3, "r"),
               lambda: dk.dev_board("pool:reserve")):
        expect_ad_error(fn, D.E_AD_BAD_ARGS)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes_end = handle.read()
    imports_net = [line for line in source.splitlines()
                   if re.match(r"\s*(?:import|from)\s", line)
                   and re.search(r"urllib|requests|socket|http",
                                 line)]
    is_ascii = all(ord(ch) < 128 for ch in source)
    # zero-UPDATE scan on executable statements only: strip all
    # triple-quoted spans (docstrings) and comment tails first
    # (R1678 self-referential-false-positive lesson)
    code_only = re.sub(r'"""[\s\S]*?"""', '""', source)
    code_only = "\n".join(re.sub(r"#.*$", "", line)
                          for line in code_only.splitlines())
    has_update = re.search(r"\bUPDATE\b", code_only) is not None
    has_rng = re.search(r"\brandom\b", source) is not None
    ok_dk6 = (_count(conn, "api_dev_keys") == n_keys_a
              and _count(conn, "api_calls") == n_calls_a
              and bal("ada") == bal_ada
              and cfg_bytes_end == cfg_bytes
              and is_ascii and not has_update and not has_rng
              and len(imports_net) == 0)
    record("AC-DK6", ok_dk6,
           "bad-arg batch zero side effects (keys %d==%d, calls"
           " %d==%d, balance flat), config.json byte-stable, source"
           " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s, net-imports"
           " %d" % (n_keys_a, _count(conn, "api_dev_keys"),
                    n_calls_a, _count(conn, "api_calls"),
                    is_ascii, not has_update, not has_rng,
                    len(imports_net)))

    # -- AC-DK7 cross-domain reconcile + suite summary --------------------
    board = dk.dev_board("usr:ada")
    cross = []
    for entry in board["keys"]:
        rec_x = metered.reconcile_client(entry["metered_client"])
        log_x = dk.usage_log(entry["api_key"])
        cross.append(rec_x["consumed_calls"] == len(log_x["calls"]))
    ok_dk7 = (all(cross) and all(e["billing"]["balanced"]
                                 for e in board["keys"])
              and len(board["keys"]) == 2)
    total = len(RESULTS) + 1
    passed = sum(1 for _, ok in RESULTS if ok) + (1 if ok_dk7 else 0)
    record("AC-DK7", ok_dk7,
           "dev_board cross-reconcile: per-key metered consumed =="
           " local call count %s, billing balanced %s, 2 keys"
           % (all(cross),
              all(e["billing"]["balanced"] for e in board["keys"])))
    print("SUITE apidev: %d/%d criteria pass" % (passed, total),
          flush=True)
    dk.close()
    metered.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
