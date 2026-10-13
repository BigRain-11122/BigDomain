"""Acceptance suite for the apidev usage_kind_tally windowed
read restart-persistence example window (BigDomain R1911; canon
= the tech-queue "apidev usage_kind_tally windowed read
cross-restart persistence" row, the R1906 seed, claimed from the
tech-lane FIFO oldest claimable row; gated rows L5/L48/L51/L93
skipped per the R1908-R1910 rulings). Asserts the pre-registered
criteria AC-UKP1..AC-UKP7 from the R1911 claim note (criteria
were registered in state/queue/tech.md before this code ran;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Covered semantics: the derived purity of the by-kind windowed
count face across an instance restart -- the three-piece stack
(Ledger -> MeteredFace -> DevKeyFace) closes fully in reverse
dependency order and reopens on the same db path and config
bytes; the October by-kind envelope (six keys: api_key,
key_name, window, by_kind, total, disclaimer over the immutable
api_calls rows) must replay byte-identical from the fresh
instance (zero in-memory drift in the derived face); two
November calls on chain-b -- the very key whose October by-kind
profile is pinned -- recalculate the default read via the real
product path (zero cache; the default window echo follows the
clock, so the recompute face is the byte-difference evidence)
while the October explicit-window read stays byte-frozen
(api_calls rows are record-time immutable); a third instance
replays the post-injection state byte-identically.

Cross-key rulings: chain-a keeps its own two pre-rotation rows
(exact-key attribution, R1728/R1735 law -- the rotated successor
tally counts only its own rows) and its read face stays open
across the restart although the key is rotated_out; lone-e is
the clean-key cross face. Comparison-surface ruling: the
explicit-window envelope carries zero clock-following fields,
so FULL envelope byte-for-byte comparison is structurally
reachable; the default read follows the clock (window echo =
_window_utc) and is compared same-clock byte-identical, then
its post-clock-move byte-difference IS the zero-cache evidence.

The metered face is the real product injected by reference (no
copy); the November calls spend real credits from the same pack
the October calls spent (the suite funds each client once).
This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_usagekindpersist.py
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
FUT_WIN = "2026-12"
ACCT = "usr:ukp"

SIX_KEYS = sorted(["api_key", "key_name", "window", "by_kind",
                   "total", "disclaimer"])


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
    tmp = tempfile.mkdtemp(prefix="apidev-ukp-ac-")
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

        # -- AC-UKP1 October anchor world + pre-close snapshots --
        led.mint_to_pool("pool:reserve", 5000, "MINT-UKP",
                         "settlement")
        led.ensure_account(ACCT, census_avatar_id="ukp")
        led.adjust([("pool:reserve", "debit", 300),
                    (ACCT, "credit", 300)],
                   "manual:fund-ukp", "suite funding ukp")

        ka = dk.issue_key(ACCT, "chain-a", 50,
                          ["backtest", "visualize"], True)
        dk.buy_credits(ka["api_key"], 40, 1, "PACK-UKP-A")
        _make_calls(dk, clock, ka["api_key"], "UKP-A", 2,
                    "backtest")
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        _make_calls(dk, clock, kb["api_key"], "UKP-B", 4,
                    "visualize")
        _make_calls(dk, clock, kb["api_key"], "UKP-B", 2,
                    "backtest", start=5)
        ke = dk.issue_key(ACCT, "lone-e", 50, ["backtest"], True)
        dk.buy_credits(ke["api_key"], 20, 1, "PACK-UKP-E")
        _make_calls(dk, clock, ke["api_key"], "UKP-E", 1,
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

        s_oct = snap(dk.usage_kind_tally(kb["api_key"], W))
        s_default = snap(dk.usage_kind_tally(kb["api_key"]))
        s_oct_a = snap(dk.usage_kind_tally(ka["api_key"], W))
        s_oct_e = snap(dk.usage_kind_tally(ke["api_key"], W))

        oc = json.loads(s_oct)
        od = json.loads(s_default)
        oa = json.loads(s_oct_a)
        oe = json.loads(s_oct_e)
        # manual SQL cross: by_kind == GROUP BY kind COUNT over
        # chain-b's October rows (the R1735 cross face)
        sql_tally = {}
        for kind, cnt in conn.execute(
                "SELECT kind, COUNT(*) FROM api_calls"
                " WHERE key_id = ? AND window = ?"
                " GROUP BY kind", (id_b, W)).fetchall():
            sql_tally[kind] = cnt
        ukp1 = (
            oct_b == 6 and oct_all == 9 and W == "2026-10"
            and sorted(oc.keys()) == SIX_KEYS
            and len(SIX_KEYS) == 6
            and oc["api_key"] == kb["api_key"]
            and oc["key_name"] == "chain-b"
            and oc["window"] == W
            and oc["disclaimer"] == DISCLAIMER
            and oc["by_kind"] == {"backtest": 2, "visualize": 4}
            and oc["total"] == 6
            and oc["total"] == sum(oc["by_kind"].values())
            and oc["by_kind"] == sql_tally
            and od == oc
            and oa["by_kind"] == {"backtest": 2}
            and oa["total"] == 2
            and oe["by_kind"] == {"backtest": 1}
            and oe["total"] == 1
            and sorted(oa.keys()) == SIX_KEYS
            and sorted(oe.keys()) == SIX_KEYS
        )
        record("AC-UKP1", ukp1,
               "October anchor: chain-b 6 real call rows (4"
               " visualize + 2 backtest) window=2026-10 (SQL"
               " count==%d), whole-db oct rows==%d, W=%s from"
               " chain-b's first call row (month-abstraction"
               " law); six-key envelope pinned {api_key,"
               " key_name=chain-b, window, by_kind"
               " {backtest:2, visualize:4}, total=6,"
               " disclaimer}, by_kind == manual SQL GROUP BY"
               " cross=%s, total==sum(by_kind)=%s; default"
               " (None) read byte-identical to the explicit"
               " October read (frozen clock in October)=%s;"
               " chain-a (rotated_out, exact-key attribution)"
               " {backtest:%d}=%s, lone-e {backtest:%d}=%s --"
               " zero rotation-ancestry leak into the"
               " successor tally"
               % (oct_b, oct_all, W, oc["by_kind"] == sql_tally,
                  oc["total"] == sum(oc["by_kind"].values()),
                  od == oc, oa["total"], oa["by_kind"],
                  oe["total"], oe["by_kind"]))

        # -- AC-UKP2 restart replay: explicit October envelope --
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        replay = snap(dk2.usage_kind_tally(kb["api_key"], W))
        replay2 = snap(dk2.usage_kind_tally(kb["api_key"], W))
        ukp2 = (replay == s_oct and replay2 == s_oct)
        record("AC-UKP2", ukp2,
               "full stack close (reverse dependency order) ->"
               " reopen same db/config: October by-kind envelope"
               " byte-identical to the pre-close snapshot=%s,"
               " second same-param read self-identical=%s"
               % (replay == s_oct, replay2 == s_oct))

        # -- AC-UKP3 default + cross-key replay, same clock -----
        r_default = snap(dk2.usage_kind_tally(kb["api_key"]))
        r_oct_a = snap(dk2.usage_kind_tally(ka["api_key"], W))
        r_oct_e = snap(dk2.usage_kind_tally(ke["api_key"], W))
        ukp3 = (r_default == s_default
                and r_oct_a == s_oct_a
                and r_oct_e == s_oct_e)
        record("AC-UKP3", ukp3,
               "default (None, window echo follows the frozen"
               " October clock) replayed byte-identical=%s;"
               " chain-a (rotated_out key, read face open across"
               " restart)=%s; lone-e clean key=%s -- the"
               " derived by-kind face carries zero in-memory"
               " state across the restart"
               % (r_default == s_default, r_oct_a == s_oct_a,
                  r_oct_e == s_oct_e))

        # -- AC-UKP4 November calls on the pinned key -> recalc --
        clock.advance(23 * 86400)
        _make_calls(dk2, clock, kb["api_key"], "UKP-N", 1,
                    "backtest")
        _make_calls(dk2, clock, kb["api_key"], "UKP-N", 1,
                    "visualize", start=2)
        nov_b = _count(
            conn, "api_calls",
            " WHERE window = '2026-11' AND key_id = ?", (id_b,))
        r_default_nov = json.loads(
            snap(dk2.usage_kind_tally(kb["api_key"])))
        r_nov = json.loads(
            snap(dk2.usage_kind_tally(kb["api_key"], NEW_WIN)))
        ukp4 = (
            nov_b == 2
            and snap(r_default_nov) != s_default
            and r_default_nov["window"] == NEW_WIN
            and r_default_nov["by_kind"]
            == {"backtest": 1, "visualize": 1}
            and r_default_nov["total"] == 2
            and snap(r_nov) == snap(r_default_nov)
        )
        record("AC-UKP4", ukp4,
               "frozen clock +23d -> 2 November calls on"
               " chain-b (the very key the October profile"
               " pins) via the real product path (record-time"
               " window=2026-11 SQL count==%d): default read"
               " RECALCULATED (window echo %s, by_kind"
               " {backtest:1, visualize:1}, total 2, and"
               " byte-differs from the pre-close default"
               " snapshot=%s = zero cache), explicit November"
               " window read byte-identical to the default"
               " November read=%s (explicit==default under a"
               " clock inside the month)"
               % (nov_b, r_default_nov["window"],
                  snap(r_default_nov) != s_default,
                  snap(r_nov) == snap(r_default_nov)))

        # -- AC-UKP5 old-window zero permeation + telescoping ---
        p_oct_post = snap(dk2.usage_kind_tally(kb["api_key"], W))
        p_oct_e_post = snap(dk2.usage_kind_tally(ke["api_key"], W))
        p_fut = json.loads(
            snap(dk2.usage_kind_tally(kb["api_key"], FUT_WIN)))
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
        ukp5 = (p_oct_post == s_oct
                and p_oct_e_post == s_oct_e
                and p_fut["window"] == FUT_WIN
                and p_fut["by_kind"] == {}
                and p_fut["total"] == 0
                and b_alltime == 8 and b_oct == 6 and b_nov == 2
                and b_oct + b_nov == b_alltime
                and all_rows == 11 and all_oct == 9
                and all_nov == 2
                and all_oct + all_nov == all_rows)
        record("AC-UKP5", ukp5,
               "after the November injection on the same pinned"
               " key: October explicit-window read stays"
               " FULL-envelope byte-frozen=%s (api_calls rows"
               " are record-time immutable and the explicit"
               " window envelope carries zero clock-following"
               " fields), lone-e October read zero-permeated=%s,"
               " future window %s honest empty read"
               " {by_kind:{}, total:0}=%s; telescoping chain-b"
               " all-time %d == oct %d + nov %d, whole-db %d =="
               " %d + %d immutable rows never lost"
               % (p_oct_post == s_oct, p_oct_e_post == s_oct_e,
                  FUT_WIN, p_fut["by_kind"] == {},
                  b_alltime, b_oct, b_nov, all_rows, all_oct,
                  all_nov))

        # -- AC-UKP6 two-instance sequential reads --------------------
        f2_oct = snap(dk2.usage_kind_tally(kb["api_key"], W))
        f2_def = snap(dk2.usage_kind_tally(kb["api_key"]))
        f2_nov = snap(dk2.usage_kind_tally(kb["api_key"], NEW_WIN))
        f2_e = snap(dk2.usage_kind_tally(ke["api_key"], W))
        conn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_oct = snap(dk3.usage_kind_tally(kb["api_key"], W))
        f3_def = snap(dk3.usage_kind_tally(kb["api_key"]))
        f3_nov = snap(dk3.usage_kind_tally(kb["api_key"], NEW_WIN))
        f3_e = snap(dk3.usage_kind_tally(ke["api_key"], W))
        ukp6 = (f3_oct == f2_oct and f3_def == f2_def
                and f3_nov == f2_nov and f3_e == f2_e
                and f3_oct == s_oct)
        record("AC-UKP6", ukp6,
               "third instance on the same db: all four"
               " post-injection reads (oct explicit / default"
               " November / nov explicit / lone-e oct)"
               " byte-identical to the second instance"
               " (%s/%s/%s/%s), and the October explicit read"
               " still equals the ORIGINAL pre-close"
               " snapshot=%s (windowed read survives restart x"
               " new-data unscratched, full envelope)"
               % (f3_oct == f2_oct, f3_def == f2_def,
                  f3_nov == f2_nov, f3_e == f2_e,
                  f3_oct == s_oct))

        # -- AC-UKP7 pure-read law + hygiene -------------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        rj_before = _count(rjconn, "reject_events")
        for w in (None, W, NEW_WIN, FUT_WIN):
            dk3.usage_kind_tally(kb["api_key"], w)
        for w in (None, W):
            dk3.usage_kind_tally(ke["api_key"], w)
            dk3.usage_kind_tally(ka["api_key"], w)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        rj_after = _count(rjconn, "reject_events")

        source = product_pre.decode("ascii")
        write_kw_total = 0
        for defname in ("usage_kind_tally", "_usage_kind_tally"):
            idx = source.find("def " + defname)
            seg_end = source.find("    def ", idx + 20)
            seg = source[idx:seg_end]
            # strip docstrings and comments before the
            # write-keyword scan (the R1888 AC-LG7 code-strip
            # precedent: the naive scan hits the segment's own
            # hygiene sentences)
            code_seg = re.sub(r'"""[\s\S]*?"""', '""', seg)
            code_seg = "\n".join(re.sub(r"#.*$", "", line)
                                 for line in code_seg.splitlines())
            write_kw_total += len(re.findall(
                r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE)\b",
                code_seg))
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
        ukp7 = (calls_after == calls_before
                and keys_after == keys_before
                and ev_after == ev_before
                and rj_after == rj_before
                and write_kw_total == 0
                and product_post == product_pre
                and product_pre_sha == product_post_sha
                and cfg_bytes_end == cfg_bytes
                and me_ascii and len(imports_net) == 0
                and len(mine_net) == 0)
        record("AC-UKP7", ukp7,
               "pure read: 8-form read battery on the third face"
               " across all three keys (incl. the rotated_out"
               " chain-a) moves zero rows (api_calls %d==%d,"
               " api_dev_keys %d==%d, key_events %d==%d,"
               " reject_events %d==%d), usage_kind_tally +"
               " _usage_kind_tally segments zero write"
               " keywords=%d, apidev.py sha256 stable=%s,"
               " config.json byte-stable=%s, sources pure-ASCII"
               "=%s, network imports 0/0=%s"
               % (calls_after, calls_before, keys_after,
                  keys_before, ev_after, ev_before,
                  rj_after, rj_before, write_kw_total,
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
    print("SUITE apidev-usagekindpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
