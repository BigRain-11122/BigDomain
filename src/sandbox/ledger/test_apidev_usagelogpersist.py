"""Acceptance suite for the apidev usage_log capped-windowed
read restart-persistence example window (BigDomain R1903; canon =
the tech-queue "apidev usage_log cap-window read cross-restart
persistence" row, the R1897 seed, claimed from the tech-lane FIFO
oldest claimable row). Asserts the pre-registered criteria
AC-UW9..AC-UW15 from the R1903 claim note (criteria were
registered in state/queue/tech.md before this code ran; honesty
law). Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Covered semantics: the derived purity of the usage_log read face
across an instance restart -- the three-piece stack (Ledger ->
MeteredFace -> DevKeyFace) closes fully in reverse dependency
order and reopens on the same db path and config bytes; the
October windowed capped envelope (window echo + overflow block
over the immutable five-key call rows) must replay
byte-identical from the fresh instance (zero in-memory drift in
the derived face); two November calls on chain-b -- the very key
whose October capped-windowed read is pinned in its tail slice
-- recalculate the default capped and default bare reads via the
real product path (zero cache) while the October windowed reads
stay byte-frozen (api_calls rows are record-time immutable; the
injection lands on the very key the October capped read pins --
a row-level same-key hijack face, stronger than the R1896
isolated-key injection per the R1897 claim ruling); a third
instance replays the post-injection state byte-identically
(two-instance sequential reads).

Comparison-surface ruling (the claim ruling 3): usage_log rows
are record-time immutable and the envelope carries zero
clock-following fields (no minute ring, no lifetime billing
block, and W is an explicit read parameter), so the FULL
envelope byte-for-byte comparison is structurally reachable even
across the +23d clock move -- a stronger face than the R1902
dev_board window-scoped banded projection; this suite uses full
envelope comparisons throughout.

The metered face is the real product injected by reference (no
copy); the two November calls spend real credits from the same
pack the October calls spent (the suite funds each client once).
This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_usagelogpersist.py
"""

import datetime
import hashlib
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
import apidev as D                      # noqa: E402 (R1700+ face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
NEW_WIN = "2026-11"
ACCT = "usr:ulp"

# exact envelope contracts (the R1729/R1732 pin lists, reused
# verbatim: this suite adds zero keys to usage_log)
BARE_KEYS = sorted(["api_key", "calls", "disclaimer"])
WIN_KEYS = sorted(BARE_KEYS + ["window"])
CAP_KEYS = sorted(BARE_KEYS + ["limit", "total", "returned",
                               "truncated"])
CAPWIN_KEYS = sorted(CAP_KEYS + ["window"])
ROW_KEYS = sorted(["call_ref", "kind", "engine_ref", "window",
                   "called_utc"])


class _FrozenClock(object):
    """Deterministic UTC clock holder patched onto the apidev
    module (the R1845 recipe): the window and minute keys roll
    only when the suite moves the clock, so double-run stdout is
    byte-identical (zero real-time leakage)."""

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


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def snap(env):
    return json.dumps(env, sort_keys=True)


def _count(conn, table, extra="", args=()):
    return conn.execute(
        "SELECT COUNT(*) FROM " + table + extra,
        tuple(args)).fetchone()[0]


def _open_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    return led, metered, dk


def _close_stack(dk, metered, led):
    dk.close()
    metered.close()
    led.close()


def _make_calls(dk, clock, api_key, prefix, n, kind, start=1):
    for i in range(start, start + n):
        ref = "%s-%02d" % (prefix, i)
        dk.call(api_key, kind, ref, "engine:%s" % ref)
        clock.advance(3)


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-ulp-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")
    rj_path = os.path.join(tmp, "api_rejects.db")

    product_path = os.path.join(BASE, "apidev.py")
    with open(product_path, "rb") as handle:
        product_pre = handle.read()
    product_pre_sha = hashlib.sha256(product_pre).hexdigest()

    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    D._now_utc = clock.now_utc
    D._minute_utc = clock.minute_utc
    D._window_utc = clock.window_utc

    try:
        led, metered, dk = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)

        # -- AC-UW9 October anchor world + pre-close snapshots ---
        led.mint_to_pool("pool:reserve", 5000, "MINT-ULP",
                         "settlement")
        led.ensure_account(ACCT, census_avatar_id="ulp")
        led.adjust([("pool:reserve", "debit", 300),
                    (ACCT, "credit", 300)],
                   "manual:fund-ulp", "suite funding ulp")

        ka = dk.issue_key(ACCT, "chain-a", 50,
                          ["backtest", "visualize"], True)
        dk.buy_credits(ka["api_key"], 40, 1, "PACK-ULP-A")
        _make_calls(dk, clock, ka["api_key"], "ULP-A", 2,
                    "backtest")
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        _make_calls(dk, clock, kb["api_key"], "ULP-B", 4,
                    "visualize")
        ke = dk.issue_key(ACCT, "lone-e", 50, ["backtest"], True)
        dk.buy_credits(ke["api_key"], 20, 1, "PACK-ULP-E")
        _make_calls(dk, clock, ke["api_key"], "ULP-E", 1,
                    "backtest")
        clock.advance(3)

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_a = key_id_of(ka["api_key"])
        id_b = key_id_of(kb["api_key"])
        id_e = key_id_of(ke["api_key"])
        marks3 = ",".join("?" for _ in (id_a, id_b, id_e))
        oct_b = _count(
            conn, "api_calls",
            " WHERE window = '2026-10' AND key_id = ?", (id_b,))
        oct_all = _count(
            conn, "api_calls",
            " WHERE window = '2026-10' AND key_id IN (" + marks3
            + ")", (id_a, id_b, id_e))
        # month-abstraction law (R1813): W derives from a real
        # call row's record-time window column, never hardcoded
        W = conn.execute(
            "SELECT window FROM api_calls WHERE key_id = ?"
            " ORDER BY called_utc, call_ref LIMIT 1",
            (id_b,)).fetchone()[0]

        s_oct_capwin = snap(dk.usage_log(kb["api_key"], 2, W))
        s_oct_bare = snap(dk.usage_log(kb["api_key"], 0, W))
        s_default = snap(dk.usage_log(kb["api_key"]))
        s_def_cap = snap(dk.usage_log(kb["api_key"], 2))

        oc = json.loads(s_oct_capwin)
        ob = json.loads(s_oct_bare)
        od = json.loads(s_default)
        odc = json.loads(s_def_cap)
        rows_keys_ok = all(sorted(r.keys()) == ROW_KEYS
                           for r in od["calls"])
        # manual SQL cross: the default bare row list == the
        # ascending (called_utc, call_ref) SELECT, and the capped
        # tail slice == that list's last two rows
        sql_rows = conn.execute(
            "SELECT call_ref, kind, engine_ref, window, called_utc"
            " FROM api_calls WHERE key_id = ?"
            " ORDER BY called_utc, call_ref",
            (id_b,)).fetchall()
        sql_list = [{"call_ref": r[0], "kind": r[1],
                     "engine_ref": r[2], "window": r[3],
                     "called_utc": r[4]} for r in sql_rows]
        tail_slice = [r["call_ref"] for r in oc["calls"]]
        uw9 = (
            oct_b == 4 and oct_all == 7 and W == "2026-10"
            and sorted(oc.keys()) == CAPWIN_KEYS
            and len(CAPWIN_KEYS) == 8
            and sorted(ob.keys()) == WIN_KEYS
            and len(WIN_KEYS) == 4
            and sorted(od.keys()) == BARE_KEYS
            and len(BARE_KEYS) == 3
            and sorted(odc.keys()) == CAP_KEYS
            and len(CAP_KEYS) == 7
            and rows_keys_ok and len(ROW_KEYS) == 5
            and oc["api_key"] == kb["api_key"]
            and oc["window"] == W
            and oc["disclaimer"] == DISCLAIMER
            and oc["limit"] == 2 and oc["total"] == 4
            and oc["returned"] == 2 and oc["truncated"] is True
            and tail_slice == ["ULP-B-03", "ULP-B-04"]
            and oc["calls"] == od["calls"][-2:]
            and len(ob["calls"]) == 4 and len(od["calls"]) == 4
            and od["calls"] == sql_list
            and ob["calls"] == od["calls"]
            and odc["limit"] == 2 and odc["total"] == 4
            and odc["returned"] == 2 and odc["truncated"] is True
            and odc["calls"] == od["calls"][-2:]
        )
        record("AC-UW9", uw9,
               "October anchor: chain-b 4 real call rows"
               " window=2026-10 (SQL count==%d), whole-db oct"
               " rows==%d, W=%s from chain-b's first call row;"
               " four snapshots anchored (capwin 8 keys overflow"
               " l/t/r/tr=%s/%s/%s/%s tail=%s == ascending tail"
               " slice; windowed-bare 4 keys %d rows; default 3"
               " keys; default-cap 7 keys tail same), row pin 5"
               " keys=%s, default rows == manual SQL ascending"
               " cross=%s"
               % (oct_b, oct_all, W, oc["limit"], oc["total"],
                  oc["returned"], oc["truncated"], tail_slice,
                  len(ob["calls"]), rows_keys_ok,
                  od["calls"] == sql_list))

        # -- AC-UW10 restart replay: capped-windowed envelope ---
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        replay = snap(dk2.usage_log(kb["api_key"], 2, W))
        replay2 = snap(dk2.usage_log(kb["api_key"], 2, W))
        uw10 = (replay == s_oct_capwin
                and replay2 == s_oct_capwin)
        record("AC-UW10", uw10,
               "full stack close (reverse order) -> reopen same"
               " db/config: October windowed capped envelope"
               " byte-identical to the pre-close snapshot=%s,"
               " second same-param read self-identical=%s"
               % (replay == s_oct_capwin,
                  replay2 == s_oct_capwin))

        # -- AC-UW11 default / bare-window / default-cap replay --
        r_default = snap(dk2.usage_log(kb["api_key"]))
        r_oct_bare = snap(dk2.usage_log(kb["api_key"], 0, W))
        r_def_cap = snap(dk2.usage_log(kb["api_key"], 2))
        uw11 = (r_default == s_default
                and r_oct_bare == s_oct_bare
                and r_def_cap == s_def_cap)
        record("AC-UW11", uw11,
               "default bare read replayed byte-identical=%s (3"
               " keys, 4 rows), oct bare-window=%s (4 keys),"
               " default-cap=%s (7 keys) -- the derived row face"
               " carries zero in-memory state across the restart"
               % (r_default == s_default,
                  r_oct_bare == s_oct_bare,
                  r_def_cap == s_def_cap))

        # -- AC-UW12 November calls on the pinned key -> recalc --
        clock.advance(23 * 86400)
        _make_calls(dk2, clock, kb["api_key"], "ULP-N", 2,
                    "backtest")
        nov_b = _count(
            conn, "api_calls",
            " WHERE window = '2026-11' AND key_id = ?", (id_b,))
        r_def_cap_nov = json.loads(
            snap(dk2.usage_log(kb["api_key"], 2)))
        r_default_nov = json.loads(
            snap(dk2.usage_log(kb["api_key"])))
        r_nov_capwin = json.loads(
            snap(dk2.usage_log(kb["api_key"], 2, NEW_WIN)))
        uw12 = (
            nov_b == 2
            and snap(r_def_cap_nov) != s_def_cap
            and r_def_cap_nov["total"] == 6
            and r_def_cap_nov["returned"] == 2
            and r_def_cap_nov["truncated"] is True
            and [r["call_ref"] for r in r_def_cap_nov["calls"]]
            == ["ULP-N-01", "ULP-N-02"]
            and len(r_default_nov["calls"]) == 6
            and snap(r_default_nov) != s_default
            and r_nov_capwin["window"] == NEW_WIN
            and r_nov_capwin["limit"] == 2
            and r_nov_capwin["total"] == 2
            and r_nov_capwin["returned"] == 2
            and r_nov_capwin["truncated"] is False
            and [r["call_ref"] for r in r_nov_capwin["calls"]]
            == ["ULP-N-01", "ULP-N-02"]
            and all(r["window"] == NEW_WIN
                    for r in r_nov_capwin["calls"])
        )
        record("AC-UW12", uw12,
               "frozen clock +23d -> 2 November calls on chain-b"
               " (the very key the October capped read pins) via"
               " the real product path (record-time window=2026-11"
               " SQL count==%d): default capped read recalculated"
               " (total 4->%s, tail=%s, byte-differs from the"
               " pre-close default-cap snapshot=%s = zero cache),"
               " default bare read grew 4->%s rows, November"
               " windowed capped read carries the new rows"
               " exactly-full {limit=2,total=2,returned=2,"
               " truncated=%s}"
               % (nov_b, r_def_cap_nov["total"],
                  [r["call_ref"] for r in r_def_cap_nov["calls"]],
                  snap(r_def_cap_nov) != s_def_cap,
                  len(r_default_nov["calls"]),
                  r_nov_capwin["truncated"]))

        # -- AC-UW13 old-window zero permeation ----------------------
        p_oct_capwin_post = snap(dk2.usage_log(kb["api_key"], 2, W))
        p_oct_bare_post = snap(dk2.usage_log(kb["api_key"], 0, W))
        b_alltime = _count(conn, "api_calls",
                           " WHERE key_id = ?", (id_b,))
        b_oct = _count(conn, "api_calls",
                       " WHERE key_id = ? AND window = '2026-10'",
                       (id_b,))
        b_nov = _count(conn, "api_calls",
                       " WHERE key_id = ? AND window = '2026-11'",
                       (id_b,))
        all_rows = _count(conn, "api_calls")
        all_oct = _count(conn, "api_calls",
                         " WHERE window = '2026-10'")
        all_nov = _count(conn, "api_calls",
                         " WHERE window = '2026-11'")
        uw13 = (p_oct_capwin_post == s_oct_capwin
                and p_oct_bare_post == s_oct_bare
                and b_alltime == 6 and b_oct == 4 and b_nov == 2
                and b_oct + b_nov == b_alltime
                and all_rows == 9 and all_oct == 7
                and all_nov == 2
                and all_oct + all_nov == all_rows)
        record("AC-UW13", uw13,
               "after the November injection on the same pinned"
               " key: October windowed reads stay FULL-envelope"
               " byte-frozen (capped=%s, bare=%s; api_calls rows"
               " are record-time immutable and the usage_log"
               " envelope carries zero clock-following fields, so"
               " no projection is needed -- the claim ruling-3"
               " stronger face), telescoping chain-b all-time %d"
               " == oct %d + nov %d, whole-db %d == %d + %d"
               " immutable rows never lost"
               % (p_oct_capwin_post == s_oct_capwin,
                  p_oct_bare_post == s_oct_bare,
                  b_alltime, b_oct, b_nov,
                  all_rows, all_oct, all_nov))

        # -- AC-UW14 two-instance sequential reads --------------------
        f2_a = snap(dk2.usage_log(kb["api_key"], 2, W))
        f2_b = snap(dk2.usage_log(kb["api_key"], 0, W))
        f2_c = snap(dk2.usage_log(kb["api_key"], 2, NEW_WIN))
        f2_d = snap(dk2.usage_log(kb["api_key"], 2))
        conn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = snap(dk3.usage_log(kb["api_key"], 2, W))
        f3_b = snap(dk3.usage_log(kb["api_key"], 0, W))
        f3_c = snap(dk3.usage_log(kb["api_key"], 2, NEW_WIN))
        f3_d = snap(dk3.usage_log(kb["api_key"], 2))
        uw14 = (f3_a == f2_a and f3_b == f2_b
                and f3_c == f2_c and f3_d == f2_d
                and f3_a == s_oct_capwin)
        record("AC-UW14", uw14,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s), and the October"
               " capped-windowed read still equals the ORIGINAL"
               " pre-close snapshot=%s (windowed read survives"
               " restart x new-data unscratched, full envelope)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d, f3_a == s_oct_capwin))

        # -- AC-UW15 pure-read law + hygiene -------------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        rj_before = _count(rjconn, "reject_events")
        for lmt, w in ((0, None), (2, W), (1, NEW_WIN),
                       (2, None), (0, W), (1, W), (2, NEW_WIN),
                       (0, NEW_WIN)):
            dk3.usage_log(kb["api_key"], lmt, w)
        for lmt, w in ((0, None), (1, None), (0, W)):
            dk3.usage_log(ke["api_key"], lmt, w)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        rj_after = _count(rjconn, "reject_events")

        source = product_pre.decode("ascii")
        idx = source.find("def usage_log")
        seg_end = source.find("    def ", idx + 20)
        log_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 code-strip precedent: the naive
        # scan hits the segment's own hygiene sentences)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', log_seg)
        code_seg = "\n".join(re.sub(r"#.*$", "", line)
                            for line in code_seg.splitlines())
        write_kw = re.findall(
            r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE)\b",
            code_seg)
        with open(product_path, "rb") as handle:
            product_post = handle.read()
        product_post_sha = hashlib.sha256(product_post).hexdigest()
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        with open(os.path.abspath(__file__), "rb") as handle:
            me_bytes = handle.read()
        me_ascii = all(b < 128 for b in me_bytes)
        imports_net = [
            line for line in source.splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and re.search(r"urllib|requests|socket|http", line)]
        mine_net = [
            line for line in
            me_bytes.decode("ascii").splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and re.search(r"urllib|requests|socket|http", line)]
        uw15 = (calls_after == calls_before
                and keys_after == keys_before
                and ev_after == ev_before
                and rj_after == rj_before
                and len(write_kw) == 0
                and product_post == product_pre
                and product_pre_sha == product_post_sha
                and cfg_bytes_end == cfg_bytes
                and me_ascii and len(imports_net) == 0
                and len(mine_net) == 0)
        record("AC-UW15", uw15,
               "pure read: 11-form read battery on the third face"
               " across both keys moves zero rows (api_calls"
               " %d==%d, api_dev_keys %d==%d, key_events %d==%d,"
               " reject_events %d==%d), usage_log segment zero"
               " write keywords=%d, apidev.py sha256 stable=%s,"
               " config.json byte-stable=%s, sources pure-ASCII"
               "=%s, network imports 0/0=%s"
               % (calls_after, calls_before, keys_after,
                  keys_before, ev_after, ev_before,
                  rj_after, rj_before, len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0))

        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk3, metered3, led3)

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    restored = (D._now_utc is real_now
                and D._minute_utc is real_minute
                and D._window_utc is real_window)
    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-usagelogpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
