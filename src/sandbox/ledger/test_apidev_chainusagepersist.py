"""Acceptance suite for the apidev chain_usage capped-windowed
read restart-persistence example window (BigDomain R1897; canon =
the tech-queue "apidev chain_usage cap-window read cross-restart
persistence" row, the R1893 seed, claimed from the tech-lane FIFO
oldest claimable row). Asserts the pre-registered criteria
AC-LU15..AC-LU21 from the R1897 claim note (criteria were
registered in state/queue/tech.md before this code ran; honesty
law). Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Covered semantics: the derived purity of the chain_usage read
face across an instance restart -- the three-piece stack (Ledger
-> MeteredFace -> DevKeyFace) closes fully and reopens on the
same db path and config; the October capped-windowed usage
envelope (window echo + overflow block) must replay
byte-identical from the fresh instance (zero in-memory drift in
the derived face); two November calls on the live chain-tail key
C via the real product path must recalculate the default capped
read (zero cache) while the October windowed reads stay
byte-frozen (api_calls rows are record-time immutable; the
injection lands on the very key whose October capped read is
pinned -- a stronger hijack face than the R1896 isolated-key
injection, per the claim ruling); a third instance replays the
post-injection state byte-identically (two-instance sequential
reads).

The metered face is the real product injected by reference (no
copy); the two November calls spend real credits from the same
pack the October calls spent (the suite funds the account once).
This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_chainusagepersist.py
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

# exact envelope contracts (the R1833/R1893 pin lists, reused
# verbatim: this suite adds zero keys to any read face)
CHAIN_USAGE_KEYS = sorted([
    "api_key", "dev_account", "key_name", "key_id", "window",
    "by_member", "chain_total", "effective_upto_queried",
    "chain_size", "queried_index", "disclaimer"])
CAPPED_KEYS = sorted(CHAIN_USAGE_KEYS
                     + ["limit", "total", "returned", "truncated"])


class _FrozenClock(object):
    """Deterministic UTC clock holder: _now_utc/_minute_utc/
    _window_utc are patched onto the apidev module so every call
    stamp and month window moves only when the suite advances
    the clock."""

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
        clock.advance(7)


def _own_map(env):
    return {m["key_id"]: m["own_calls"] for m in env["by_member"]}


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-cup-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")

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

        # -- AC-LU15 October anchor world + pre-close snapshots ---
        led.mint_to_pool("pool:reserve", 5000, "MINT-CU",
                         "settlement")
        led.ensure_account("usr:cup", census_avatar_id="cup")
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:cup", "credit", 300)],
                   "manual:fund-cup-cu", "suite funding cup")

        ka = dk.issue_key("usr:cup", "chain-a", 50,
                          ["backtest", "visualize"], True)
        dk.buy_credits(ka["api_key"], 40, 1, "PACK-CU-A")
        _make_calls(dk, clock, ka["api_key"], "CU-A", 3, "backtest")
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        _make_calls(dk, clock, kb["api_key"], "CU-B", 2, "visualize")
        kc = dk.rotate_key(kb["api_key"], "chain-c")
        _make_calls(dk, clock, kc["api_key"], "CU-C", 2, "backtest")

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_a = key_id_of(ka["api_key"])
        id_b = key_id_of(kb["api_key"])
        id_c = key_id_of(kc["api_key"])
        marks3 = ",".join("?" for _ in (id_a, id_b, id_c))
        oct_rows = _count(
            conn, "api_calls",
            " WHERE window = '2026-10' AND key_id IN (" + marks3
            + ")", (id_a, id_b, id_c))
        # month-abstraction law (R1813): W derives from a real
        # call row's record-time window column, never hardcoded
        W = conn.execute(
            "SELECT window FROM api_calls WHERE key_id = ?"
            " ORDER BY called_utc, call_ref LIMIT 1",
            (id_a,)).fetchone()[0]

        s_oct_capwin = snap(dk.chain_usage(kc["api_key"], W, 2))
        s_oct_win = snap(dk.chain_usage(kc["api_key"], W))
        s_default = snap(dk.chain_usage(kc["api_key"]))
        s_def_cap = snap(dk.chain_usage(kc["api_key"], None, 2))

        oc = json.loads(s_oct_capwin)
        view_c = dk.key_view(kc["api_key"])
        lu15_shape = (
            oct_rows == 7 and W == "2026-10"
            and sorted(oc.keys()) == CAPPED_KEYS
            and len(CAPPED_KEYS) == 15
            and sorted(json.loads(s_oct_win).keys())
            == CHAIN_USAGE_KEYS
            and len(CHAIN_USAGE_KEYS) == 11)
        lu15_block = (
            oc["window"] == W and oc["api_key"] == kc["api_key"]
            and oc["key_id"] == id_c and oc["key_name"] == "chain-c"
            and oc["disclaimer"] == DISCLAIMER
            and oc["limit"] == 2 and oc["total"] == 3
            and oc["returned"] == 2 and oc["truncated"] is True
            and oc["chain_size"] == 2
            and [m["key_id"] for m in oc["by_member"]]
            == [id_b, id_c]
            and _own_map(oc) == {id_b: 2, id_c: 2}
            and oc["chain_total"] == 7
            and oc["effective_upto_queried"] == 7
            and oc["queried_index"] == 2)
        od = json.loads(s_default)
        lu15_align = (
            od["window"] == "2026-10"
            and _own_map(od) == {id_a: 3, id_b: 2, id_c: 2}
            and od["chain_total"] == 7
            and od["effective_upto_queried"] == 7
            and od["chain_size"] == 3 and od["queried_index"] == 2
            and od["effective_upto_queried"]
            == view_c["quota_used"] == 7
            and s_default == s_oct_win)
        lu15 = lu15_shape and lu15_block and lu15_align
        record("AC-LU15", lu15,
               "October anchor: 7 real call rows window=2026-10"
               " over the 3-key chain (SQL count==%d), W=%s from"
               " the first call row's window column, four"
               " snapshots anchored (capped-win 15 keys block"
               " l/t/r/tr=%s/%s/%s/%s tail [B,C] own=%s"
               " chain_total=%d effective=%d==key_view"
               " quota_used=%d; win-bare/default 11 keys"
               " byte-equal=%s; default-cap 15 keys)"
               % (oct_rows, W, oc["limit"], oc["total"],
                  oc["returned"], oc["truncated"],
                  _own_map(oc), oc["chain_total"],
                  od["effective_upto_queried"],
                  view_c["quota_used"], s_default == s_oct_win))

        # -- AC-LU16 restart replay: capped-windowed envelope ------
        conn.close()
        lcconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)

        replay = snap(dk2.chain_usage(kc["api_key"], W, 2))
        replay2 = snap(dk2.chain_usage(kc["api_key"], W, 2))
        lu16 = (replay == s_oct_capwin
                and replay2 == s_oct_capwin)
        record("AC-LU16", lu16,
               "full stack close -> reopen same db/config: October"
               " capped-windowed envelope byte-identical to the"
               " pre-close snapshot=%s, second same-param read"
               " self-identical=%s"
               % (replay == s_oct_capwin,
                  replay2 == s_oct_capwin))

        # -- AC-LU17 default / bare-window / default-cap replay -----
        r_default = snap(dk2.chain_usage(kc["api_key"]))
        r_oct_win = snap(dk2.chain_usage(kc["api_key"], W))
        r_def_cap = snap(dk2.chain_usage(kc["api_key"], None, 2))
        rd = json.loads(r_default)
        lu17 = (r_default == s_default
                and r_oct_win == s_oct_win
                and r_def_cap == s_def_cap
                and rd["chain_size"] == 3
                and [m["key_id"] for m in rd["by_member"]]
                == [id_a, id_b, id_c]
                and [m["key_name"] for m in rd["by_member"]]
                == ["chain-a", "chain-b", "chain-c"]
                and rd["queried_index"] == 2
                and rd["window"] == "2026-10")
        record("AC-LU17", lu17,
               "default read replayed byte-identical=%s (window"
               " echo=2026-10, chain [A,B,C] ids/names facts"
               " stable across restart), bare-window=%s,"
               " default-cap=%s (derived face zero in-memory"
               " drift)"
               % (r_default == s_default,
                  r_oct_win == s_oct_win,
                  r_def_cap == s_def_cap))

        # -- AC-LU18 November real calls -> recalc face --------------
        clock.advance(23 * 86400)
        _make_calls(dk2, clock, kc["api_key"], "CU-N", 2,
                    "backtest")
        nov_rows = _count(
            conn, "api_calls",
            " WHERE window = '2026-11' AND key_id IN (" + marks3
            + ")", (id_a, id_b, id_c))
        r_lx = json.loads(
            snap(dk2.chain_usage(kc["api_key"], None, 2)))
        r_nov_capwin = json.loads(
            snap(dk2.chain_usage(kc["api_key"], NEW_WIN, 2)))
        view_nov = dk2.key_view(kc["api_key"])
        lu18 = (nov_rows == 2
                and snap(r_lx) != s_def_cap
                and r_lx["window"] == NEW_WIN
                and _own_map(r_lx) == {id_b: 0, id_c: 2}
                and r_lx["total"] == 3 and r_lx["returned"] == 2
                and r_lx["truncated"] is True
                and r_lx["chain_total"] == 2
                and r_lx["effective_upto_queried"] == 2
                and r_nov_capwin["window"] == NEW_WIN
                and _own_map(r_nov_capwin) == {id_b: 0, id_c: 2}
                and r_nov_capwin["chain_total"] == 2
                and r_lx["effective_upto_queried"]
                == view_nov["quota_used"] == 2
                and view_nov["window"] == NEW_WIN)
        record("AC-LU18", lu18,
               "frozen clock +23d -> 2 November calls on the live"
               " chain-tail key C via the real product path"
               " (record-time window=2026-11 SQL count==%d):"
               " default capped read recalculated (window echo"
               " %s, own=%s, byte-differs from the pre-close"
               " default-cap snapshot=%s = zero cache), November"
               " windowed capped read carries the new rows=%s,"
               " three-way alignment effective==key_view"
               " quota_used==%d in the new window"
               % (nov_rows, r_lx["window"], _own_map(r_lx),
                  snap(r_lx) != s_def_cap,
                  _own_map(r_nov_capwin) == {id_b: 0, id_c: 2},
                  view_nov["quota_used"]))

        # -- AC-LU19 old-window zero penetration ---------------------
        p_oct_capwin = snap(dk2.chain_usage(kc["api_key"], W, 2))
        p_oct_win = snap(dk2.chain_usage(kc["api_key"], W))
        total_rows = _count(conn, "api_calls")
        oct_total = json.loads(
            snap(dk2.chain_usage(kc["api_key"], W)))["chain_total"]
        nov_total = json.loads(
            snap(dk2.chain_usage(kc["api_key"],
                                 NEW_WIN)))["chain_total"]
        lu19 = (p_oct_capwin == s_oct_capwin
                and p_oct_win == s_oct_win
                and total_rows == 9 and oct_total == 7
                and nov_total == 2
                and oct_total + nov_total == total_rows)
        record("AC-LU19", lu19,
               "after the November injection on the same key:"
               " October capped-windowed read still byte-identical"
               " to the pre-close snapshot=%s, bare-window=%s"
               " (record-time window column immutable), api_calls"
               " total %d == 7+2 immutable rows never lost,"
               " telescoping oct %d + nov %d == all-time %d"
               % (p_oct_capwin == s_oct_capwin,
                  p_oct_win == s_oct_win, total_rows,
                  oct_total, nov_total, total_rows))

        # -- AC-LU20 two-instance sequential reads --------------------
        f2_a = snap(dk2.chain_usage(kc["api_key"], W, 2))
        f2_b = snap(dk2.chain_usage(kc["api_key"]))
        f2_c = snap(dk2.chain_usage(kc["api_key"], NEW_WIN, 2))
        f2_d = snap(dk2.chain_usage(kc["api_key"], None, 2))
        conn.close()
        lcconn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = snap(dk3.chain_usage(kc["api_key"], W, 2))
        f3_b = snap(dk3.chain_usage(kc["api_key"]))
        f3_c = snap(dk3.chain_usage(kc["api_key"], NEW_WIN, 2))
        f3_d = snap(dk3.chain_usage(kc["api_key"], None, 2))
        lu20 = (f3_a == f2_a and f3_b == f2_b
                and f3_c == f2_c and f3_d == f2_d
                and f3_a == s_oct_capwin)
        record("AC-LU20", lu20,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s) and the October"
               " capped-windowed read still equals the original"
               " pre-close snapshot=%s (windowed read survives"
               " restart x new-data unscratched)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d, f3_a == s_oct_capwin))

        # -- AC-LU21 pure-read law + hygiene -------------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        for w, lmt in ((None, 0), (W, 2), (NEW_WIN, 1),
                       (None, 1), (W, 0), (None, 2),
                       (W, 1), (NEW_WIN, 2)):
            dk3.chain_usage(kc["api_key"], w, lmt)
        dk3.chain_usage(ka["api_key"])
        dk3.chain_usage(kb["api_key"], W, 1)
        dk3.chain_usage(kc["api_key"], NEW_WIN)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")

        source = product_pre.decode("ascii")
        idx = source.find("def chain_usage")
        seg_end = source.find("    def ", idx + 20)
        usage_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 / R1896 AC-LG29 code-strip
        # precedent: the naive scan hits the segment's own
        # "zero UPDATE" hygiene sentences)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', usage_seg)
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
        lu21 = (calls_after == calls_before
                and keys_after == keys_before
                and ev_after == ev_before
                and len(write_kw) == 0
                and product_post == product_pre
                and product_pre_sha == product_post_sha
                and cfg_bytes_end == cfg_bytes
                and me_ascii and len(imports_net) == 0
                and len(mine_net) == 0)
        record("AC-LU21", lu21,
               "pure read: 12 read calls on the third face move"
               " zero rows (api_calls %d==%d, api_dev_keys"
               " %d==%d, key_events %d==%d), chain_usage"
               " segment zero write keywords=%d, apidev.py"
               " sha256 stable=%s, config.json byte-stable=%s,"
               " sources pure-ASCII=%s, network imports 0/0=%s"
               % (calls_after, calls_before, keys_after,
                  keys_before, ev_after, ev_before,
                  len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0))

        conn.close()
        lcconn.close()
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
    print("SUITE apidev-chainusagepersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
