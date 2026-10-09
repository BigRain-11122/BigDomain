"""Acceptance suite for the apidev minute-window rate ring
(BigDomain R1712; canon = tech-queue "apidev short-window rate
face" row, the R1700/R1711 successor). Asserts the pre-registered
criteria AC-RT1..AC-RT7 from the R1712 tech-queue claim note
(criteria were registered before this code ran; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Covered semantics: per-key per-UTC-minute call cap (minute_cap,
0 = ring dark, legacy five-argument issue_key form unchanged);
the rate gate sits between the kind gate and the monthly quota
gate and fires before the billing ring (zero charge, zero rows);
minute and monthly readings stay separate in every envelope;
like the monthly ring (R1711), the minute count runs over the
full rotate_in ancestry (rotation never resets the minute ring);
rotation inherits minute_cap with the contract; the rate gate
precedes the duplicate pre-check.

Deterministic clock: module-level _now_utc/_minute_utc are
monkeypatched onto a frozen clock holder (R1678 frozen-clock
precedent), restored in finally. The metered face is the real
product injected by reference (no copy); this suite reaches the
billing ring only through the apidev public API. This source
stays pure ASCII per the encoding discipline.

Usage: python test_apidev_rate.py
"""

import datetime
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
import apidev as D                      # noqa: E402 (R1700/R1711/R1712)

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


class _FrozenClock(object):
    """Deterministic UTC clock holder: _now_utc/_minute_utc are
    patched onto the apidev module so minute windows roll only
    when the suite advances the clock explicitly."""

    def __init__(self):
        self.dt = datetime.datetime(2026, 10, 10, 5, 0, 0)

    def now_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def minute_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M")

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-rate-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-RT-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada", "suite funding ada")
    conn = sqlite3.connect(db_path)
    clock = _FrozenClock()
    real_now, real_minute = D._now_utc, D._minute_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc

        # -- AC-RT1 contract face + default-dark ring ---------------
        # legacy five-argument positional form must keep working
        legacy = dk.issue_key("usr:ada", "legacy", 5, ["backtest"],
                              False)
        dk.buy_credits(legacy["api_key"], 10, 1, "PACK-RT-L0")
        v_legacy = dk.key_view(legacy["api_key"])
        l1 = dk.call(legacy["api_key"], "backtest", "RT-L-1", "e1")
        l2 = dk.call(legacy["api_key"], "backtest", "RT-L-2", "e2")
        l3 = dk.call(legacy["api_key"], "backtest", "RT-L-3", "e3")
        keys_before = _count(conn, "api_dev_keys")
        clients_before = _count(conn, "metered_clients")
        bad_codes = []
        for bad in (-1, True, "2"):
            ok_one, code_one = expect_ad_error(
                lambda b=bad: dk.issue_key("usr:ada", "bad-" + str(b),
                                           5, ["backtest"], False,
                                           minute_cap=b),
                D.E_AD_BAD_ARGS)
            bad_codes.append(ok_one)
        mc = dk.issue_key("usr:ada", "mc-key", 5, ["backtest"], False,
                          minute_cap=2)
        rt1 = (v_legacy["minute_cap"] == 0
               and l1["minute_used"] == 1 and l2["minute_used"] == 2
               and l3["minute_used"] == 3
               and all(r["minute_cap"] == 0
                       for r in (l1, l2, l3))
               and all(bad_codes)
               and _count(conn, "api_dev_keys") == keys_before + 1
               and _count(conn, "metered_clients") == clients_before + 1
               and mc["minute_cap"] == 2)
        record("AC-RT1", rt1,
               "legacy 5-arg form ok (view minute_cap=%d, 3 calls in"
               " one minute all pass, ring dark), bad minute_cap"
               " batch rejected %s, rows +1 (issued mc-key),"
               " metered_clients +1 only" %
               (v_legacy["minute_cap"], bad_codes))

        # -- AC-RT2 rate enforcement, fail-closed, rollover ---------
        dk.buy_credits(mc["api_key"], 10, 1, "PACK-RT-MC0")
        m0 = clock.minute_utc()
        c1 = dk.call(mc["api_key"], "backtest", "RT-M-1", "e")
        c2 = dk.call(mc["api_key"], "backtest", "RT-M-2", "e")
        rec_before = metered.reconcile_client(mc["metered_client"])
        remaining_before = rec_before["remaining_credits"]
        calls_before = _count(conn, "api_calls")
        ok_rate, code_rate = expect_ad_error(
            lambda: dk.call(mc["api_key"], "backtest", "RT-M-3", "e"),
            D.E_AD_RATE)
        rec_after = metered.reconcile_client(mc["metered_client"])
        calls_after_reject = _count(conn, "api_calls")
        clock.advance(61)
        m1 = clock.minute_utc()
        c3 = dk.call(mc["api_key"], "backtest", "RT-M-3", "e")
        rt2 = (c1["minute_used"] == 1 and c2["minute_used"] == 2
               and ok_rate and code_rate == D.E_AD_RATE
               and rec_after["remaining_credits"]
               == remaining_before
               and calls_after_reject == calls_before
               and m1 != m0
               and c3["minute_window"] == m1
               and c3["minute_used"] == 1
               and c3["quota_used"] == 3
               and _count(conn, "api_calls")
               == calls_after_reject + 1)
        record("AC-RT2", rt2,
               "minute_cap=2: calls 1/2 pass (minute_used %d/%d), 3rd"
               " in minute rejected %s before billing (credits %d==%d,"
               " call rows %d==%d at reject, +%d after the rolled pass),"
               " minute rolls %s->%s, 3rd passes (minute_used=%d)"
               " while monthly quota_used=%d"
               % (c1["minute_used"], c2["minute_used"], code_rate,
                  rec_after["remaining_credits"], remaining_before,
                  calls_after_reject, calls_before,
                  _count(conn, "api_calls") - calls_after_reject,
                  m0, m1, c3["minute_used"], c3["quota_used"]))

        # -- AC-RT3 monthly vs minute separation ---------------------
        dual = dk.issue_key("usr:ada", "dual-cap", 3, ["backtest"],
                            False, minute_cap=2)
        dk.buy_credits(dual["api_key"], 10, 1, "PACK-RT-D0")
        d1 = dk.call(dual["api_key"], "backtest", "RT-D-1", "e")
        d2 = dk.call(dual["api_key"], "backtest", "RT-D-2", "e")
        ok_d_rate, code_d_rate = expect_ad_error(
            lambda: dk.call(dual["api_key"], "backtest", "RT-D-3",
                            "e"),
            D.E_AD_RATE)
        clock.advance(61)
        d3 = dk.call(dual["api_key"], "backtest", "RT-D-3", "e")
        ok_d_quota, code_d_quota = expect_ad_error(
            lambda: dk.call(dual["api_key"], "backtest", "RT-D-4",
                            "e"),
            D.E_AD_QUOTA)
        v_dual = dk.key_view(dual["api_key"])
        rt3 = (d1["quota_used"] == 1 and d2["quota_used"] == 2
               and ok_d_rate and code_d_rate == D.E_AD_RATE
               and d3["quota_used"] == 3
               and ok_d_quota and code_d_quota == D.E_AD_QUOTA
               and v_dual["minute_used"] == 1
               and v_dual["quota_used"] == 3
               and v_dual["quota_remaining"] == 0)
        record("AC-RT3", rt3,
               "window_cap=3 + minute_cap=2: 3rd in minute=%s (monthly"
               " used=2<3, minute is the blocker), after roll 3rd"
               " passes (quota_used=%d), 4th=%s (monthly cap hit,"
               " minute_used=%d<2 not the blocker) - two rings never"
               " mask each other"
               % (code_d_rate, d3["quota_used"], code_d_quota,
                  v_dual["minute_used"]))

        # -- AC-RT4 ancestry anti-evasion on the minute ring ---------
        rot_src = dk.issue_key("usr:ada", "rot-src", 10, ["backtest"],
                               False, minute_cap=2)
        dk.buy_credits(rot_src["api_key"], 10, 1, "PACK-RT-R0")
        r1 = dk.call(rot_src["api_key"], "backtest", "RT-R-1", "e")
        r2 = dk.call(rot_src["api_key"], "backtest", "RT-R-2", "e")
        expect_ad_error(
            lambda: dk.call(rot_src["api_key"], "backtest", "RT-R-3",
                            "e"),
            D.E_AD_RATE)
        rot = dk.rotate_key(rot_src["api_key"], "rot-src-v2")
        v_rot = dk.key_view(rot["api_key"])
        rec_rot_before = metered.reconcile_client(
            rot["metered_client"])["remaining_credits"]
        ok_rot_rate, code_rot_rate = expect_ad_error(
            lambda: dk.call(rot["api_key"], "backtest", "RT-R-3", "e"),
            D.E_AD_RATE)
        rec_rot_after = metered.reconcile_client(
            rot["metered_client"])["remaining_credits"]
        clock.advance(61)
        r3 = dk.call(rot["api_key"], "backtest", "RT-R-3", "e")
        rt4 = (rot["minute_cap"] == 2
               and v_rot["minute_used"] == 2
               and ok_rot_rate and code_rot_rate == D.E_AD_RATE
               and rec_rot_after == rec_rot_before
               and r3["minute_used"] == 1
               and r3["quota_used"] == 3)
        record("AC-RT4", rt4,
               "rotate inside a capped minute: successor inherits"
               " minute_cap=%d and starts at minute_used=%d (ancestor"
               " rows counted), immediate call rejected %s with zero"
               " charge (credits %d==%d), after roll successor passes"
               " (minute_used=%d, monthly quota_used=%d = 2 ancestor"
               " + 1 own)"
               % (rot["minute_cap"], v_rot["minute_used"],
                  code_rot_rate, rec_rot_after, rec_rot_before,
                  r3["minute_used"], r3["quota_used"]))

        # -- AC-RT5 rotation contract carry + read faces --------------
        v_old = dk.key_view(rot_src["api_key"])
        v_new = dk.key_view(rot["api_key"])
        board = dk.dev_board("usr:ada")
        board_rows_have_min = all(
            ("minute_window" in k and "minute_used" in k
             and "minute_cap" in k) for k in board["keys"])
        succ_row = [k for k in board["keys"]
                    if k["key_name"] == "rot-src-v2"][0]
        log_new = dk.usage_log(rot["api_key"])
        log_keys = (set(log_new["calls"][0].keys())
                    if log_new["calls"] else set())
        rt5 = (rot["minute_cap"] == 2
               and v_new["minute_cap"] == 2
               and "minute_window" in v_new
               and "minute_used" in v_new
               and v_old["status"] == "rotated_out"
               and "minute_window" in v_old
               and board_rows_have_min
               and succ_row["minute_cap"] == 2
               and len(log_new["calls"]) == 1
               and log_keys == {"call_ref", "kind", "engine_ref",
                                "window", "called_utc"})
        record("AC-RT5", rt5,
               "rotate return carries minute_cap=%d; successor view"
               " minute fields present (cap=%d), old key readable"
               " status=%s with minute fields, dev_board rows all"
               " carry minute fields (rot-src-v2 cap=%d),"
               " usage_log row shape unchanged (%s)"
               % (rot["minute_cap"], v_new["minute_cap"],
                  v_old["status"], succ_row["minute_cap"],
                  sorted(log_keys)))

        # -- AC-RT6 gate order: rate before duplicate pre-check -------
        gate = dk.issue_key("usr:ada", "gate-key", 10, ["backtest"],
                            False, minute_cap=1)
        dk.buy_credits(gate["api_key"], 5, 1, "PACK-RT-G0")
        g1 = dk.call(gate["api_key"], "backtest", "RT-G-1", "e")
        calls_g_before = _count(conn, "api_calls")
        ok_g_rate, code_g_rate = expect_ad_error(
            lambda: dk.call(gate["api_key"], "backtest", "RT-G-1",
                             "e"),
            D.E_AD_RATE)
        clock.advance(61)
        ok_g_dup, code_g_dup = expect_ad_error(
            lambda: dk.call(gate["api_key"], "backtest", "RT-G-1",
                            "e"),
            D.E_AD_DUP)
        rt6 = (g1["minute_used"] == 1
               and ok_g_rate and code_g_rate == D.E_AD_RATE
               and ok_g_dup and code_g_dup == D.E_AD_DUP
               and _count(conn, "api_calls") == calls_g_before)
        record("AC-RT6", rt6,
               "replay with minute exhausted -> %s (rate gate precedes"
               " the dup pre-check), same replay after minute roll ->"
               " %s (dup semantics intact), call rows %d==%d (zero"
               " rows on both rejects)"
               % (code_g_rate, code_g_dup,
                  _count(conn, "api_calls"), calls_g_before))

        # -- AC-RT7 hygiene face ---------------------------------------
        source = open(os.path.join(BASE, "apidev.py"), "r",
                      encoding="ascii").read()
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        code_only = re.sub(r'"""[\s\S]*?"""', '""', source)
        code_only = "\n".join(re.sub(r"#.*$", "", line)
                             for line in code_only.splitlines())
        has_update = re.search(r"\bUPDATE\b", code_only) is not None
        imports_net = [line for line in source.splitlines()
                       if re.match(r"\s*(?:import|from)\s", line)
                       and re.search(r"urllib|requests|socket|http",
                                     line)]
        is_ascii = all(ord(ch) < 128 for ch in source)
        has_rng = re.search(r"\brandom\b", source) is not None
        rate_code = D.E_AD_RATE in source
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
        rt7 = (cfg_bytes_end == cfg_bytes
               and is_ascii and not has_update and not has_rng
               and len(imports_net) == 0 and rate_code and both_closed)
        record("AC-RT7", rt7,
               "hygiene: config.json byte-stable=%s, source"
               " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
               " net-imports=%d, E_AD_RATE exported=%s,"
               " close() shuts both connections=%s"
               % (cfg_bytes_end == cfg_bytes, is_ascii, not has_update,
                  not has_rng, len(imports_net), rate_code,
                  both_closed))
    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-rate: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
