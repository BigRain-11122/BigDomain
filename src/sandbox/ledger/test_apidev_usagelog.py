"""Acceptance suite for the apidev usage-log read cap
(BigDomain R1729; canon = tech-queue "apidev usage_log read-cap
face" row). Asserts the pre-registered criteria AC-UL1..AC-UL7
from the R1729 tech-queue claim note (criteria were registered
before this code ran; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Covered semantics: usage_log(api_key, limit=0) keeps the
full-log behavior byte-stable on the default call (envelope key
set exactly api_key/calls/disclaimer, row order and row set
identical); limit>0 bounds the response to the most recent
limit rows and adds an overflow block (limit/total/returned/
truncated) to the envelope; the truncated window is the exact
tail of the ascending (called_utc, call_ref) order (mirror
SQL: DESC/DESC LIMIT then reverse; call_ref is the primary key
so the pair is a total order and the mirror is exact); the key
gate fires before the argument gate (an unknown key rejects
E_AD_UNKNOWN_KEY even with a bad limit); a bad limit (-1, bool,
non-int string, float) rejects E_AD_BAD_ARGS with zero rows
read; capped reads stay read-only (zero api_calls rows
written) and dead keys (revoked, rotated-out) keep the capped
read face open with identical semantics.

Deterministic clock: module-level _now_utc/_minute_utc/
_window_utc are monkeypatched onto a frozen clock holder
(R1678 frozen-clock precedent), restored in finally; the
clock advances a few seconds per call so called_utc is strictly
increasing and the (called_utc, call_ref) order is exercised on
both keys. The metered face is the real product injected by
reference (no copy); this suite reaches the billing ring only
through the apidev public API. This source stays pure ASCII per
the encoding discipline.

Usage: python test_apidev_usagelog.py
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
import apidev as D                      # noqa: E402 (R1700..R1729)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 10, 6, 30, 0)


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


def _call_count(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM api_calls").fetchone()[0]


def _manual_refs(conn, key_id):
    rows = conn.execute(
        "SELECT call_ref FROM api_calls WHERE key_id = ?"
        " ORDER BY called_utc, call_ref", (key_id,)).fetchall()
    return [r[0] for r in rows]


class _FrozenClock(object):
    """Deterministic UTC clock holder: _now_utc/_minute_utc/
    _window_utc are patched onto the apidev module so the window
    and minute keys roll only when the suite moves the clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def minute_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M")

    def window_utc(self):
        return self.dt.strftime("%Y-%m")

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def _make_calls(dk, clock, api_key, prefix, n, start=1):
    refs = ["%s-%02d" % (prefix, i) for i in range(start, start + n)]
    for ref in refs:
        dk.call(api_key, "backtest", ref, "engine:%s" % ref)
        clock.advance(7)
    return refs


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-usagelog-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-UL-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada-ul", "suite funding ada")
    conn = sqlite3.connect(db_path)
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # -- AC-UL1 contract + default zero-drift ---------------------
        k10 = dk.issue_key("usr:ada", "ul-full", 20, ["backtest"],
                           False)
        dk.buy_credits(k10["api_key"], 12, 1, "PACK-UL-A")
        refs_10 = _make_calls(dk, clock, k10["api_key"], "UL-A", 10)
        full = dk.usage_log(k10["api_key"])
        k10_id = conn.execute(
            "SELECT key_id FROM api_dev_keys"
            " WHERE dev_account = ? AND key_name = ?",
            ("usr:ada", "ul-full")).fetchone()[0]
        manual = _manual_refs(conn, k10_id)
        env_keys = set(full.keys())
        row_keys = set(full["calls"][0].keys())
        ok_unknown_plain, code_unknown_plain = expect_ad_error(
            lambda: dk.usage_log("sk-nonexistent"),
            D.E_AD_UNKNOWN_KEY)
        ok_unknown_badlimit, code_unknown_badlimit = expect_ad_error(
            lambda: dk.usage_log("sk-nonexistent", -1),
            D.E_AD_UNKNOWN_KEY)
        ul1 = (env_keys == {"api_key", "calls", "disclaimer"}
               and len(full["calls"]) == 10
               and [c["call_ref"] for c in full["calls"]] == refs_10
               and [c["call_ref"] for c in full["calls"]] == manual
               and row_keys == {"call_ref", "kind", "engine_ref",
                                "window", "called_utc"}
               and all(c["window"] == "2026-10"
                       for c in full["calls"])
               and ok_unknown_plain
               and code_unknown_plain == D.E_AD_UNKNOWN_KEY
               and ok_unknown_badlimit
               and code_unknown_badlimit == D.E_AD_UNKNOWN_KEY)
        record("AC-UL1", ul1,
               "default envelope keys=%s (3-key set), 10 rows in"
               " ascending order=%s (manual SQL cross-check %s),"
               " row fields=%s, window=%s, unknown key -> %s"
               " (plain) and %s with bad limit (key gate first)"
               % (sorted(env_keys),
                  [c["call_ref"] for c in full["calls"]] == refs_10,
                  [c["call_ref"] for c in full["calls"]] == manual,
                  sorted(row_keys),
                  full["calls"][0]["window"],
                  code_unknown_plain, code_unknown_badlimit))

        # -- AC-UL2 bad-args fail-closed ------------------------------
        calls_before = _call_count(conn)
        codes = []
        oks = []
        for bad in (-1, True, "2", 2.5):
            ok_bad, code_bad = expect_ad_error(
                lambda b=bad: dk.usage_log(k10["api_key"], b),
                D.E_AD_BAD_ARGS)
            oks.append(ok_bad)
            codes.append(code_bad)
        calls_after = _call_count(conn)
        ul2 = (all(oks) and codes == [D.E_AD_BAD_ARGS] * 4
               and calls_after == calls_before)
        record("AC-UL2", ul2,
               "bad limits -1/True/'2'/2.5 -> %s (api_calls"
               " %d==%d, zero rows read)"
               % (codes, calls_after, calls_before))

        # -- AC-UL3 under-cap full return ----------------------------
        under = dk.usage_log(k10["api_key"], 50)
        ul3 = (set(under.keys()) == {"api_key", "calls", "disclaimer",
                                     "limit", "total", "returned",
                                     "truncated"}
               and under["limit"] == 50 and under["total"] == 10
               and under["returned"] == 10
               and under["truncated"] is False
               and under["calls"] == full["calls"])
        record("AC-UL3", ul3,
               "limit=50 over total=10: envelope keys=%s, limit=%d"
               " total=%d returned=%d truncated=%s, rows identical"
               " to default read=%s"
               % (sorted(under.keys()), under["limit"],
                  under["total"], under["returned"],
                  under["truncated"], under["calls"] == full["calls"]))

        # -- AC-UL4 truncation = exact tail window --------------------
        t3 = dk.usage_log(k10["api_key"], 3)
        t3_row_keys = set(t3["calls"][0].keys())
        ul4 = (t3["limit"] == 3 and t3["total"] == 10
               and t3["returned"] == 3
               and t3["truncated"] is True
               and t3["calls"] == full["calls"][-3:]
               and [c["call_ref"] for c in t3["calls"]]
               == refs_10[-3:]
               and t3_row_keys == {"call_ref", "kind", "engine_ref",
                                   "window", "called_utc"})
        record("AC-UL4", ul4,
               "limit=3 over 10 rows: returned=%d truncated=%s"
               " total=%d, rows=%s == default tail %s, row fields"
               "=%s"
               % (t3["returned"], t3["truncated"], t3["total"],
                  [c["call_ref"] for c in t3["calls"]],
                  [c["call_ref"] for c in full["calls"][-3:]],
                  sorted(t3_row_keys)))

        # -- AC-UL5 boundary states -----------------------------------
        exact = dk.usage_log(k10["api_key"], 10)
        k0 = dk.issue_key("usr:ada", "ul-empty", 5, ["backtest"],
                          False)
        empty = dk.usage_log(k0["api_key"], 3)
        one = dk.usage_log(k10["api_key"], 1)
        ul5 = (exact["limit"] == 10 and exact["total"] == 10
               and exact["returned"] == 10
               and exact["truncated"] is False
               and exact["calls"] == full["calls"]
               and empty["calls"] == [] and empty["total"] == 0
               and empty["returned"] == 0
               and empty["truncated"] is False
               and one["returned"] == 1 and one["truncated"] is True
               and one["calls"] == full["calls"][-1:])
        record("AC-UL5", ul5,
               "limit==total (10/10): truncated=%s full set=%s;"
               " empty key limit=3: calls=%s total=%d truncated=%s;"
               " limit=1: returned=%d truncated=%s tail=%s"
               % (exact["truncated"],
                  len(exact["calls"]) == 10,
                  empty["calls"], empty["total"],
                  empty["truncated"], one["returned"],
                  one["truncated"],
                  [c["call_ref"] for c in one["calls"]]))

        # -- AC-UL6 read-only law + dead-key faces -------------------
        reads_before = _call_count(conn)
        dk.usage_log(k10["api_key"], 3)
        dk.usage_log(k0["api_key"], 2)
        dk.usage_log(k10["api_key"], 1)
        reads_after = _call_count(conn)
        krev = dk.issue_key("usr:ada", "ul-rev", 20, ["backtest"],
                            False)
        dk.buy_credits(krev["api_key"], 8, 1, "PACK-UL-R")
        refs_5 = _make_calls(dk, clock, krev["api_key"], "UL-R", 5)
        dk.revoke_key(krev["api_key"])
        rev_full = dk.usage_log(krev["api_key"])
        rev_cap = dk.usage_log(krev["api_key"], 2)
        krot = dk.issue_key("usr:ada", "ul-rot", 20, ["backtest"],
                            False)
        dk.buy_credits(krot["api_key"], 6, 1, "PACK-UL-T")
        _make_calls(dk, clock, krot["api_key"], "UL-T", 4)
        dk.rotate_key(krot["api_key"], "ul-rot-v2")
        rot_cap = dk.usage_log(krot["api_key"], 2)
        rot_full = dk.usage_log(krot["api_key"])
        ul6 = (reads_after == reads_before
               and rev_full["calls"] and len(rev_full["calls"]) == 5
               and rev_cap["total"] == 5 and rev_cap["returned"] == 2
               and rev_cap["truncated"] is True
               and rev_cap["calls"] == rev_full["calls"][-2:]
               and [c["call_ref"] for c in rev_cap["calls"]]
               == refs_5[-2:]
               and rot_cap["total"] == 4 and rot_cap["returned"] == 2
               and rot_cap["truncated"] is True
               and rot_cap["calls"] == rot_full["calls"][-2:])
        record("AC-UL6", ul6,
               "capped reads leave api_calls %d==%d; revoked key"
               " capped read open (total=%d returned=%d truncated=%s"
               " tail=%s), rotated-out key capped read open"
               " (total=%d returned=%d tail=%s)"
               % (reads_after, reads_before, rev_cap["total"],
                  rev_cap["returned"], rev_cap["truncated"],
                  [c["call_ref"] for c in rev_cap["calls"]],
                  rot_cap["total"], rot_cap["returned"],
                  [c["call_ref"] for c in rot_cap["calls"]]))

        # -- AC-UL7 hygiene + delivery carriers ----------------------
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
        cap_face = re.search(r"def usage_log\(self, api_key,"
                             r" limit=0\)", source) is not None
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "r",
                  encoding="utf-8") as handle:
            runner_src = handle.read()
        registered = re.search(
            r'\("ledger-apidev-usagelog",\s*'
            r'os\.path\.join\("ledger",\s*'
            r'"test_apidev_usagelog\.py"\),\s*7\)',
            runner_src) is not None
        dk.close()
        closed = []
        for handle_conn in (dk._conn, dk._lconn, dk._rconn):
            try:
                handle_conn.execute("SELECT 1")
                closed.append(False)
            except sqlite3.ProgrammingError:
                closed.append(True)
        ul7 = (cfg_bytes_end == cfg_bytes
               and is_ascii and not has_update and not has_rng
               and len(imports_net) == 0 and cap_face
               and registered
               and len(RESULTS) == 6
               and all(ok for _, ok in RESULTS)
               and closed == [True, True, True])
        record("AC-UL7", ul7,
               "hygiene: config.json byte-stable=%s, source"
               " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
               " net-imports=%d, capped face exported=%s,"
               " reconcile_all SUITES row registered=%s, close()"
               " shuts all three connections=%s; suite self-"
               "carrier: %d prior criteria all green=%s"
               % (cfg_bytes_end == cfg_bytes, is_ascii,
                  not has_update, not has_rng, len(imports_net),
                  cap_face, registered, closed == [True, True, True],
                  len(RESULTS), all(ok for _, ok in RESULTS)))
    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-usagelog: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
