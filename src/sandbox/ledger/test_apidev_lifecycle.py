"""Acceptance suite for the apidev key lifecycle face (BigDomain
R1711; canon = tech-queue key revocation/rotation row, the R1700
three-rings successor). Asserts the pre-registered criteria
AC-KR1..AC-KR8 from the R1711 tech-queue claim note (criteria
were registered before this code ran; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Covered semantics: revoke = immutable 'revoke' event, every write
face fails closed E_AD_REVOKED before the billing ring (zero
charge, zero rows); rotate = successor key inheriting the
contract, the billing binding (same metered client: balance
carries over with zero token movement) and the window usage of
its full ancestor chain (rotation never resets the monthly
quota); lifecycle events live in a separate sqlite file so the
ledger schema (R1676 baseline fingerprints) stays untouched.

The metered face is the real product injected by reference (no
copy); this suite reaches the billing ring only through the
apidev public API. This test source stays pure ASCII per the
encoding discipline.

Usage: python test_apidev_lifecycle.py
"""

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
import apidev as D                      # noqa: E402 (R1700 + R1711)

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


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _tables(conn, pattern):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE ? AND name NOT LIKE 'sqlite_%'",
        (pattern,)).fetchall()
    return set(r[0] for r in rows)


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-lc-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-LC-A", "settlement")
    for who, amount, tag in (("ada", 400, "a"), ("lin", 400, "l")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)
    ledger_api_tables_start = _tables(conn, "api%")

    source = open(os.path.join(BASE, "apidev.py"), "r",
                  encoding="ascii").read()

    # -- AC-KR1 separate lifecycle store, zero ledger touch --------
    led_api_expected = {"api_dev_keys", "api_calls"}
    kr1_tables = (ledger_api_tables_start == led_api_expected
                  and os.path.exists(lc_path))
    lconn_probe = sqlite3.connect(lc_path)
    lc_tables = _tables(lconn_probe, "%")
    lconn_probe.close()
    code_only = re.sub(r'"""[\s\S]*?"""', '""', source)
    code_only = "\n".join(re.sub(r"#.*$", "", line)
                          for line in code_only.splitlines())
    has_update = re.search(r"\bUPDATE\b", code_only) is not None
    kr1 = (kr1_tables and lc_tables == {"key_events"}
           and not has_update)
    record("AC-KR1", kr1,
           "lifecycle store = separate file api_lifecycle.db"
           " tables=%s, ledger api%% tables=%s (R1676 fingerprints"
           " untouched), zero UPDATE in code=%s"
           % (sorted(lc_tables), sorted(ledger_api_tables_start),
              not has_update))

    # -- AC-KR2 revocation fails closed ------------------------------
    rk = dk.issue_key("usr:ada", "legacy-key", 5, ["backtest"], False)
    dk.buy_credits(rk["api_key"], 5, 1, "PACK-R-1")
    dk.call(rk["api_key"], "backtest", "CALL-R-1", "eng-r1")
    rec_r = metered.reconcile_client(rk["metered_client"])
    remaining_before = rec_r["remaining_credits"]
    calls_before = _count(conn, "api_calls")
    bal_ada_before = bal("ada")
    rev = dk.revoke_key(rk["api_key"])
    ok_call, code_call = expect_ad_error(
        lambda: dk.call(rk["api_key"], "backtest", "CALL-R-2", "e"),
        D.E_AD_REVOKED)
    ok_buy, code_buy = expect_ad_error(
        lambda: dk.buy_credits(rk["api_key"], 5, 1, "PACK-R-2"),
        D.E_AD_REVOKED)
    rec_r2 = metered.reconcile_client(rk["metered_client"])
    ok_twice, _ = expect_ad_error(
        lambda: dk.revoke_key(rk["api_key"]), D.E_AD_ALREADY)
    lcconn = sqlite3.connect(lc_path)
    # key_id lookup: api_key column -> key_id via module table
    rkey_id = conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (rk["api_key"],)).fetchone()[0]
    ev_count_r = lcconn.execute(
        "SELECT COUNT(*) FROM key_events WHERE key_id = ?",
        (rkey_id,)).fetchone()[0]
    lcconn.close()
    view_r = dk.key_view(rk["api_key"])
    log_r = dk.usage_log(rk["api_key"])
    board_r = dk.dev_board("usr:ada")
    kr2 = (rev["status"] == "revoked" and ok_call and ok_buy
           and ok_twice and ev_count_r == 1
           and _count(conn, "api_calls") == calls_before
           and rec_r2["remaining_credits"] == remaining_before
           and rec_r2["consumed_calls"] == rec_r["consumed_calls"]
           and bal("ada") == bal_ada_before
           and view_r["status"] == "revoked"
           and len(log_r["calls"]) == 1
           and any(k["key_name"] == "legacy-key"
                   and k["status"] == "revoked"
                   for k in board_r["keys"]))
    record("AC-KR2", kr2,
           "revoke: status=%s, call/buy rejected %s/%s before billing"
           " (calls %d==%d, credits %d==%d, balance flat), double"
           " revoke E_AD_ALREADY, events=%d, read faces open"
           " (view=%s, log=%d call, board shows revoked)"
           % (rev["status"], code_call, code_buy,
              _count(conn, "api_calls"), calls_before,
              rec_r2["remaining_credits"], remaining_before,
              ev_count_r, view_r["status"], len(log_r["calls"])))

    # -- AC-KR3 rotation semantics -----------------------------------
    ak = dk.issue_key("usr:ada", "prod-key", 5, ["backtest"], True)
    dk.buy_credits(ak["api_key"], 10, 1, "PACK-A-1")
    dk.call(ak["api_key"], "backtest", "CALL-A-1", "eng-a1")
    dk.call(ak["api_key"], "backtest", "CALL-A-2", "eng-a2")
    rot = dk.rotate_key(ak["api_key"], "prod-key-v2")
    akey_id = conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (ak["api_key"],)).fetchone()[0]
    bkey_id = conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (rot["api_key"],)).fetchone()[0]
    lcconn = sqlite3.connect(lc_path)
    ev_out = lcconn.execute(
        "SELECT pair_key_id FROM key_events"
        " WHERE key_id = ? AND event = 'rotate_out'",
        (akey_id,)).fetchone()
    ev_in = lcconn.execute(
        "SELECT pair_key_id FROM key_events"
        " WHERE key_id = ? AND event = 'rotate_in'",
        (bkey_id,)).fetchone()
    lcconn.close()
    ok_a_call, _ = expect_ad_error(
        lambda: dk.call(ak["api_key"], "backtest", "CALL-A-3", "e"),
        D.E_AD_REVOKED)
    ok_a_buy, _ = expect_ad_error(
        lambda: dk.buy_credits(ak["api_key"], 5, 1, "PACK-A-2"),
        D.E_AD_REVOKED)
    view_a = dk.key_view(ak["api_key"])
    view_b = dk.key_view(rot["api_key"])
    kr3 = (rot["api_key"] != ak["api_key"]
           and rot["metered_client"] == ak["metered_client"]
           and rot["window_cap"] == 5
           and rot["enabled_kinds"] == ["backtest"]
           and rot["ai_label"] == 1
           and rot["rotated_from"] == "prod-key"
           and ev_out is not None and ev_out[0] == bkey_id
           and ev_in is not None and ev_in[0] == akey_id
           and ok_a_call and ok_a_buy
           and view_a["status"] == "rotated_out"
           and view_b["status"] == "active"
           and view_b["rotated_from_key_id"] == akey_id)
    record("AC-KR3", kr3,
           "rotate: successor new key, same metered client %s,"
           " cap/kinds/ai carried %s/%s/%s, event pair out->%s"
           " in->%s, old write faces %s, view_a=%s view_b=%s"
           " from_key=%s"
           % (rot["metered_client"] == ak["metered_client"],
              rot["window_cap"], rot["enabled_kinds"],
              rot["ai_label"], ev_out and ev_out[0],
              ev_in and ev_in[0], ok_a_call and ok_a_buy,
              view_a["status"], view_b["status"],
              view_b["rotated_from_key_id"]))

    # -- AC-KR4 rotation gate order and bad args ---------------------
    kk = dk.issue_key("usr:lin", "starter", 5, ["backtest"], False)
    kk2 = dk.issue_key("usr:lin", "backup", 5, ["backtest"], False)
    metered_clients_before = _count(conn, "metered_clients")
    bad_args = [
        (lambda: dk.rotate_key(kk["api_key"], ""), D.E_AD_BAD_ARGS),
        (lambda: dk.rotate_key(kk["api_key"], "starter"),
         D.E_AD_DUP_KEY),
        (lambda: dk.rotate_key(kk["api_key"], "backup"),
         D.E_AD_DUP_KEY),
        (lambda: dk.rotate_key("sk-nonexistent", "x"),
         D.E_AD_UNKNOWN_KEY),
        (lambda: dk.revoke_key("sk-nonexistent"),
         D.E_AD_UNKNOWN_KEY),
        (lambda: dk.rotate_key(rk["api_key"], "x2"),   # revoked
         D.E_AD_ALREADY),
        (lambda: dk.rotate_key(ak["api_key"], "x3"),   # rotated out
         D.E_AD_ALREADY),
    ]
    codes_got = []
    for fn, want in bad_args:
        ok_one, code_one = expect_ad_error(fn, want)
        codes_got.append(ok_one)
    metered_clients_after = _count(conn, "metered_clients")
    kr4 = (all(codes_got)
           and metered_clients_after == metered_clients_before)
    record("AC-KR4", kr4,
           "gate order: empty name/dup-name/unknown/revoked-source"
           " batch all rejected %s, metered_clients %d==%d (zero"
           " metered touch)"
           % (codes_got, metered_clients_before,
              metered_clients_after))

    # -- AC-KR5 anti-evasion window inheritance ----------------------
    view_b2 = dk.key_view(rot["api_key"])
    vb_used = view_b2["quota_used"]
    dk.call(rot["api_key"], "backtest", "CALL-B-1", "eng-b1")
    dk.call(rot["api_key"], "backtest", "CALL-B-2", "eng-b2")
    dk.call(rot["api_key"], "backtest", "CALL-B-3", "eng-b3")
    view_b3 = dk.key_view(rot["api_key"])
    rec_b = metered.reconcile_client(rot["metered_client"])
    remaining_b = rec_b["remaining_credits"]
    calls_b = _count(conn, "api_calls")
    ok_b_cap, code_b_cap = expect_ad_error(
        lambda: dk.call(rot["api_key"], "backtest", "CALL-B-4", "e"),
        D.E_AD_QUOTA)
    rec_b2 = metered.reconcile_client(rot["metered_client"])
    rot2 = dk.rotate_key(rot["api_key"], "prod-key-v3")
    view_c = dk.key_view(rot2["api_key"])
    ok_c_cap, code_c_cap = expect_ad_error(
        lambda: dk.call(rot2["api_key"], "backtest", "CALL-C-1", "e"),
        D.E_AD_QUOTA)
    kr5 = (vb_used == 2 and view_b3["quota_used"] == 5
           and view_b3["quota_remaining"] == 0
           and ok_b_cap
           and rec_b2["remaining_credits"] == remaining_b
           and _count(conn, "api_calls") == calls_b
           and view_c["quota_used"] == 5
           and view_c["rotated_from_key_id"] == bkey_id
           and ok_c_cap
           and metered.reconcile_client(rot2["metered_client"])
           ["remaining_credits"] == remaining_b)
    record("AC-KR5", kr5,
           "window inheritance: successor starts at quota_used=%d"
           " (2 ancestor rows), grows to %d, cap E_AD_QUOTA at 5"
           " with zero charge (credits %d==%d, calls %d==%d),"
           " second hop C inherits %d rows (A2+B3) and is capped"
           " at once %s"
           % (vb_used, view_b3["quota_used"],
              rec_b2["remaining_credits"], remaining_b,
              _count(conn, "api_calls"), calls_b,
              view_c["quota_used"], ok_c_cap))

    # -- AC-KR6 no revival path --------------------------------------
    ok_rel_rev, _ = expect_ad_error(
        lambda: dk.issue_key("usr:ada", "legacy-key", 5,
                             ["backtest"], False), D.E_AD_DUP_KEY)
    ok_rel_rot, _ = expect_ad_error(
        lambda: dk.issue_key("usr:ada", "prod-key", 5,
                             ["backtest"], True), D.E_AD_DUP_KEY)
    no_reinstate = (not hasattr(dk, "reinstate_key")
                    and not hasattr(dk, "restore_key"))
    kr6 = (ok_rel_rev and ok_rel_rot and no_reinstate)
    record("AC-KR6", kr6,
           "no revival: re-issue over revoked/rotated names still"
           " E_AD_DUP_KEY %s/%s, reinstate/restore APIs absent=%s,"
           " terminal events immutable (AC-KR2 double-revoke zero"
           " new rows)"
           % (ok_rel_rev, ok_rel_rot, no_reinstate))

    # -- AC-KR7 balance carry-over ------------------------------------
    a2 = dk.issue_key("usr:ada", "billing-key", 30, ["backtest"],
                      False)
    dk.buy_credits(a2["api_key"], 10, 1, "PACK-BILL-1")
    b2 = dk.rotate_key(a2["api_key"], "billing-key-v2")
    dk.buy_credits(b2["api_key"], 5, 1, "PACK-BILL-2")
    rec_bal = metered.reconcile_client(a2["metered_client"])
    bal_ada_mid = bal("ada")
    ok_a2_buy, _ = expect_ad_error(
        lambda: dk.buy_credits(a2["api_key"], 5, 1, "PACK-BILL-3"),
        D.E_AD_REVOKED)
    rec_bal2 = metered.reconcile_client(a2["metered_client"])
    kr7 = (b2["metered_client"] == a2["metered_client"]
           and rec_bal["packs"] == 2
           and rec_bal["purchased_calls"] == 15
           and rec_bal["consumed_calls"] == 0
           and rec_bal["remaining_credits"] == 15
           and ok_a2_buy
           and rec_bal2["packs"] == 2
           and bal("ada") == bal_ada_mid)
    record("AC-KR7", kr7,
           "balance carry-over: same metered client, packs=%d"
           " purchased=%d consumed=%d remaining=%d after rotation,"
           " old-key buy rejected %s (packs still %d, funding"
           " balance flat)"
           % (rec_bal["packs"], rec_bal["purchased_calls"],
              rec_bal["consumed_calls"], rec_bal["remaining_credits"],
              ok_a2_buy, rec_bal2["packs"]))

    # -- AC-KR8 hygiene face ------------------------------------------
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes_end = handle.read()
    imports_net = [line for line in source.splitlines()
                   if re.match(r"\s*(?:import|from)\s", line)
                   and re.search(r"urllib|requests|socket|http",
                                 line)]
    is_ascii = all(ord(ch) < 128 for ch in source)
    has_rng = re.search(r"\brandom\b", source) is not None
    ledger_api_tables_end = _tables(conn, "api%")
    try:
        dk.close()
        dk._conn.execute("SELECT 1")
        both_closed = False
    except sqlite3.ProgrammingError:
        try:
            dk._lconn.execute("SELECT 1")
            both_closed = False
        except sqlite3.ProgrammingError:
            both_closed = True
    kr8 = (cfg_bytes_end == cfg_bytes
           and is_ascii and not has_update and not has_rng
           and len(imports_net) == 0
           and ledger_api_tables_end == ledger_api_tables_start
           and both_closed)
    record("AC-KR8", kr8,
           "hygiene: config.json byte-stable=%s, source"
           " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
           " net-imports=%d, ledger api%% tables unchanged=%s,"
           " close() shuts both connections=%s"
           % (cfg_bytes_end == cfg_bytes, is_ascii, not has_update,
              not has_rng, len(imports_net),
              ledger_api_tables_end == ledger_api_tables_start,
              both_closed))

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-lifecycle: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
