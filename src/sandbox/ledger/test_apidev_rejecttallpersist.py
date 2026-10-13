"""Acceptance suite for the apidev reject_tally windowed read
restart-persistence example window (BigDomain R1908; canon = the
tech-queue "apidev reject_tally windowed read cross-restart
persistence" row, the R1903 seed, claimed from the tech-lane FIFO
oldest claimable row). Asserts the pre-registered criteria
AC-RJW8..AC-RJW14 from the R1908 claim note (criteria were
registered in state/queue/tech.md before this code ran; honesty
law). Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Covered semantics: the derived purity of the reject_tally
diagnostic aggregation face across an instance restart -- the
three-piece stack (Ledger -> MeteredFace -> DevKeyFace) closes
fully in reverse dependency order and reopens on the same db path
and config bytes; the October windowed envelope (window echo +
by_reason GROUP BY aggregate + total over the immutable
key-attributed reject rows) must replay byte-identical from the
fresh instance (zero in-memory drift in the derived face); one
November disabled-kind reject on chain-b -- the very key whose
October windowed read is pinned, fired through the real product
call chain (recorded before the billing ring, zero call rows) --
recalculates the default current-month read (which follows the
clock into November) while the October windowed read stays
byte-frozen (reject_events rows are record-time immutable; the
row lands on the very key the October read pins -- a row-level
same-key hijack face, the R1897 strong-injection family); a third
instance replays the post-injection state byte-identically
(two-instance sequential reads).

Comparison-surface ruling (the claim ruling 3): the reject_tally
envelope carries zero clock-following fields (no minute ring, no
billing block), so explicit-window reads use the FULL envelope
byte-for-byte comparison even across the +23d clock move; the
default read's window echo follows the clock by design, so its
post-move re-domaining is itself the zero-cache recompute
evidence.

World ruling (the claim ruling 2): the quota gate counts the full
rotation ancestry (anti-evasion), so a cap-3 chain with two
ancestor calls gives the pinned key a deterministic dual-reject
October family (E_AD_KIND via a disabled-kind call + E_AD_QUOTA
via the ancestry-inclusive quota gate), both fired through the
real product call chain with zero call rows (rejects fire before
the billing ring and the local append).

This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_rejecttallpersist.py
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
ACCT = "usr:rjp"

# exact envelope contract (the R1730 pin, reused verbatim: this
# suite adds zero keys to reject_tally)
ENV_KEYS = sorted(["api_key", "key_name", "window", "by_reason",
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


def _expect_reject(fn, code):
    try:
        fn()
    except D.ApiDevError as exc:
        return exc.code == code
    return False


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-rtp-ac-")
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

        # -- AC-RJW8 October anchor world + pre-close snapshots --
        led.mint_to_pool("pool:reserve", 5000, "MINT-RTP",
                         "settlement")
        led.ensure_account(ACCT, census_avatar_id="rtp")
        led.adjust([("pool:reserve", "debit", 300),
                    (ACCT, "credit", 300)],
                   "manual:fund-rtp", "suite funding rtp")

        # cap-3 chain: two ancestor calls, rotate, one own call,
        # then the ancestry-inclusive quota gate fires
        ka = dk.issue_key(ACCT, "chain-a", 3,
                          ["backtest", "visualize"], True)
        dk.buy_credits(ka["api_key"], 40, 1, "PACK-RTP-A")
        dk.call(ka["api_key"], "backtest", "RTP-A-01",
                "engine:RTP-A-01")
        clock.advance(3)
        dk.call(ka["api_key"], "backtest", "RTP-A-02",
                "engine:RTP-A-02")
        clock.advance(3)
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        # disabled-kind reject: recorded, zero call rows
        kind_reject = _expect_reject(
            lambda: dk.call(kb["api_key"], "narrate", "RTP-B-X1",
                            "engine:RTP-B-X1"), D.E_AD_KIND)
        clock.advance(3)
        dk.call(kb["api_key"], "backtest", "RTP-B-01",
                "engine:RTP-B-01")
        clock.advance(3)
        # ancestry 2 + own 1 == cap 3 -> quota reject, zero rows
        quota_reject = _expect_reject(
            lambda: dk.call(kb["api_key"], "backtest", "RTP-B-02",
                            "engine:RTP-B-02"), D.E_AD_QUOTA)
        # lone clean key: live key with zero rejects
        ke = dk.issue_key(ACCT, "lone-e", 50, ["backtest"], True)
        dk.buy_credits(ke["api_key"], 20, 1, "PACK-RTP-E")
        dk.call(ke["api_key"], "backtest", "RTP-E-01",
                "engine:RTP-E-01")
        clock.advance(3)

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_a = key_id_of(ka["api_key"])
        id_b = key_id_of(kb["api_key"])
        id_e = key_id_of(ke["api_key"])
        oct_b_rejects = _count(
            rjconn, "reject_events",
            " WHERE key_id = ? AND window = '2026-10'", (id_b,))
        oct_all_rejects = _count(
            rjconn, "reject_events",
            " WHERE window = '2026-10'")
        calls_b = _count(conn, "api_calls",
                         " WHERE key_id = ?", (id_b,))
        calls_all = _count(conn, "api_calls")
        # month-abstraction law (R1813): W derives from the pinned
        # key's first reject row's record-time window column
        W = rjconn.execute(
            "SELECT window FROM reject_events WHERE key_id = ?"
            " ORDER BY reject_id LIMIT 1", (id_b,)).fetchone()[0]
        sql_by_reason = {
            r[0]: int(r[1]) for r in rjconn.execute(
                "SELECT reason, COUNT(*) FROM reject_events"
                " WHERE key_id = ? AND window = ?"
                " GROUP BY reason ORDER BY reason",
                (id_b, W)).fetchall()}

        s_oct = snap(dk.reject_tally(kb["api_key"], W))
        s_default = snap(dk.reject_tally(kb["api_key"]))
        s_nov = snap(dk.reject_tally(kb["api_key"], NEW_WIN))
        s_fut = snap(dk.reject_tally(kb["api_key"], FUT_WIN))
        s_lone = snap(dk.reject_tally(ke["api_key"]))

        oc = json.loads(s_oct)
        on = json.loads(s_nov)
        of_ = json.loads(s_fut)
        ol = json.loads(s_lone)
        rjw8 = (
            kind_reject and quota_reject
            and W == "2026-10" and oct_b_rejects == 2
            and oct_all_rejects == 2 and calls_b == 1
            and calls_all == 4
            and sorted(oc.keys()) == ENV_KEYS
            and len(ENV_KEYS) == 6
            and oc["window"] == W
            and oc["api_key"] == kb["api_key"]
            and oc["key_name"] == "chain-b"
            and oc["disclaimer"] == DISCLAIMER
            and oc["by_reason"] == {"E_AD_KIND": 1,
                                    "E_AD_QUOTA": 1}
            and oc["by_reason"] == sql_by_reason
            and oc["total"] == 2
            and s_default == s_oct
            and on["window"] == NEW_WIN
            and on["by_reason"] == {} and on["total"] == 0
            and of_["window"] == FUT_WIN
            and of_["by_reason"] == {} and of_["total"] == 0
            and sorted(ol.keys()) == ENV_KEYS
            and ol["by_reason"] == {} and ol["total"] == 0
        )
        record("AC-RJW8", rjw8,
               "October anchor world: cap-3 rotate chain (chain-a"
               " 2 calls -> chain-b) with the ancestry-inclusive"
               " quota gate gives chain-b a dual-reject family"
               " {E_AD_KIND: 1, E_AD_QUOTA: 1} total 2 (SQL"
               " count==%d whole-db==%d, manual GROUP BY cross"
               " ==%s, kind reject fired=%s quota reject fired=%s"
               " both zero call rows: chain-b call rows==%d"
               " whole-db==%d), W=%s SQL-derived from chain-b's"
               " first reject row; envelope 6-key pin, default"
               " ==explicit October byte-identical=%s, nov/fut"
               " honest empty ({}), lone-e live-key honest empty"
               " face=%s"
               % (oct_b_rejects, oct_all_rejects,
                  oc["by_reason"] == sql_by_reason, kind_reject,
                  quota_reject, calls_b, calls_all, W,
                  s_default == s_oct, ol["by_reason"] == {}))

        # -- AC-RJW9 restart replay: October windowed envelope ---
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        rjconn = sqlite3.connect(rj_path)

        replay = snap(dk2.reject_tally(kb["api_key"], W))
        replay2 = snap(dk2.reject_tally(kb["api_key"], W))
        rjw9 = (replay == s_oct and replay2 == s_oct)
        record("AC-RJW9", rjw9,
               "full stack close (reverse order) -> reopen same"
               " db/config: October windowed reject_tally envelope"
               " byte-identical to the pre-close snapshot=%s,"
               " second same-param read self-identical=%s"
               % (replay == s_oct, replay2 == s_oct))

        # -- AC-RJW10 default / nov / fut replay ----------------------
        r_default = snap(dk2.reject_tally(kb["api_key"]))
        r_nov = snap(dk2.reject_tally(kb["api_key"], NEW_WIN))
        r_fut = snap(dk2.reject_tally(kb["api_key"], FUT_WIN))
        rjw10 = (r_default == s_default and r_nov == s_nov
                 and r_fut == s_fut)
        record("AC-RJW10", rjw10,
               "default current-month read (clock still October,"
               " default month == explicit October) replayed"
               " byte-identical=%s, nov honest-empty=%s, fut"
               " honest-empty=%s -- the derived aggregate face"
               " carries zero in-memory state across the restart"
               % (r_default == s_default, r_nov == s_nov,
                  r_fut == s_fut))

        # -- AC-RJW11 November reject on the pinned key -> recalc --
        clock.advance(23 * 86400)
        nov_reject = _expect_reject(
            lambda: dk2.call(kb["api_key"], "narrate",
                             "RJW-N-X1", "engine:RJW-N-X1"),
            D.E_AD_KIND)
        nov_b = _count(
            rjconn, "reject_events",
            " WHERE key_id = ? AND window = '2026-11'", (id_b,))
        calls_all_nov = _count(conn, "api_calls")
        r_default_nov = json.loads(
            snap(dk2.reject_tally(kb["api_key"])))
        r_nov_win = json.loads(
            snap(dk2.reject_tally(kb["api_key"], NEW_WIN)))
        rjw11 = (
            nov_reject and nov_b == 1 and calls_all_nov == 4
            and snap(r_default_nov) != s_default
            and r_default_nov["window"] == NEW_WIN
            and r_default_nov["by_reason"] == {"E_AD_KIND": 1}
            and r_default_nov["total"] == 1
            and snap(r_nov_win) == snap(r_default_nov)
        )
        record("AC-RJW11", rjw11,
               "frozen clock +23d -> one November disabled-kind"
               " reject on chain-b (the very key whose October"
               " windowed read is pinned) via the real product"
               " call chain (record-time window=2026-11 SQL"
               " count==%d, api_calls rows unchanged %d =="
               " October's 4: rejects fire before the billing ring"
               " and the local append): default read followed the"
               " clock into November and recalculated (window=%s"
               " by_reason=%s total=%s, byte-differs from the"
               " pre-close default snapshot=%s = zero cache),"
               " November explicit window read == default=%s"
               % (nov_b, calls_all_nov, r_default_nov["window"],
                  r_default_nov["by_reason"],
                  r_default_nov["total"],
                  snap(r_default_nov) != s_default,
                  snap(r_nov_win) == snap(r_default_nov)))

        # -- AC-RJW12 old-window zero permeation ----------------------
        p_oct_post = snap(dk2.reject_tally(kb["api_key"], W))
        b_alltime = _count(rjconn, "reject_events",
                           " WHERE key_id = ?", (id_b,))
        b_oct = _count(rjconn, "reject_events",
                       " WHERE key_id = ? AND window = '2026-10'",
                       (id_b,))
        b_nov = _count(rjconn, "reject_events",
                       " WHERE key_id = ? AND window = '2026-11'",
                       (id_b,))
        all_rows = _count(rjconn, "reject_events")
        all_oct = _count(rjconn, "reject_events",
                         " WHERE window = '2026-10'")
        all_nov = _count(rjconn, "reject_events",
                         " WHERE window = '2026-11'")
        rjw12 = (p_oct_post == s_oct
                 and b_alltime == 3 and b_oct == 2 and b_nov == 1
                 and b_oct + b_nov == b_alltime
                 and all_rows == 3 and all_oct == 2
                 and all_nov == 1
                 and all_oct + all_nov == all_rows)
        record("AC-RJW12", rjw12,
               "after the November injection on the same pinned"
               " key: October windowed read stays FULL-envelope"
               " byte-frozen=%s (reject_events rows are"
               " record-time immutable and the reject_tally"
               " envelope carries zero clock-following fields, so"
               " no projection is needed), telescoping chain-b"
               " all-time %d == oct %d + nov %d, whole-db %d =="
               " %d + %d immutable rows never lost"
               % (p_oct_post == s_oct, b_alltime, b_oct, b_nov,
                  all_rows, all_oct, all_nov))

        # -- AC-RJW13 two-instance sequential reads --------------------
        f2_a = snap(dk2.reject_tally(kb["api_key"], W))
        f2_b = snap(dk2.reject_tally(kb["api_key"]))
        f2_c = snap(dk2.reject_tally(kb["api_key"], NEW_WIN))
        f2_d = snap(dk2.reject_tally(kb["api_key"], FUT_WIN))
        conn.close()
        rjconn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = snap(dk3.reject_tally(kb["api_key"], W))
        f3_b = snap(dk3.reject_tally(kb["api_key"]))
        f3_c = snap(dk3.reject_tally(kb["api_key"], NEW_WIN))
        f3_d = snap(dk3.reject_tally(kb["api_key"], FUT_WIN))
        rjw13 = (f3_a == f2_a and f3_b == f2_b
                 and f3_c == f2_c and f3_d == f2_d
                 and f3_a == s_oct)
        record("AC-RJW13", rjw13,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s), and the October"
               " windowed read still equals the ORIGINAL pre-close"
               " snapshot=%s (windowed read survives restart x"
               " new-data unscratched, full envelope)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d, f3_a == s_oct))

        # -- AC-RJW14 pure-read law + hygiene -------------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        rj_before = _count(rjconn, "reject_events")
        for w in (None, W, NEW_WIN, FUT_WIN):
            dk3.reject_tally(kb["api_key"], w)
        dk3.reject_tally(kb["api_key"], W)
        dk3.reject_tally(ke["api_key"])
        dk3.reject_tally(ke["api_key"], W)
        dk3.reject_tally(ke["api_key"], NEW_WIN)
        unknown_gate = _expect_reject(
            lambda: dk3.reject_tally("usr:bogus", W),
            D.E_AD_UNKNOWN_KEY)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        rj_after = _count(rjconn, "reject_events")

        source = product_pre.decode("ascii")
        idx = source.find("def reject_tally")
        seg_end = source.find("    def ", idx + 20)
        rt_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 code-strip precedent)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', rt_seg)
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
        runner_path = os.path.join(
            os.path.dirname(BASE), "reconcile_all.py")
        with open(runner_path, encoding="utf-8") as handle:
            runner_src = handle.read()
        row_wired = ("ledger-apidev-rejecttallpersist"
                     in runner_src)
        rjw14 = (calls_after == calls_before
                 and keys_after == keys_before
                 and ev_after == ev_before
                 and rj_after == rj_before
                 and unknown_gate
                 and len(write_kw) == 0
                 and product_post == product_pre
                 and product_pre_sha == product_post_sha
                 and cfg_bytes_end == cfg_bytes
                 and me_ascii and len(imports_net) == 0
                 and len(mine_net) == 0 and row_wired)
        record("AC-RJW14", rjw14,
               "pure read: 9-form read battery across both keys"
               " plus the unknown-key gate probe (fired=%s) moves"
               " zero rows (api_calls %d==%d, api_dev_keys %d==%d,"
               " key_events %d==%d, reject_events %d==%d),"
               " reject_tally segment zero write keywords=%d,"
               " apidev.py sha256 stable=%s, config.json"
               " byte-stable=%s, sources pure-ASCII=%s, network"
               " imports 0/0=%s, runner row wired=%s"
               % (unknown_gate, calls_after, calls_before,
                  keys_after, keys_before, ev_after, ev_before,
                  rj_after, rj_before, len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0,
                  row_wired))

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
    print("SUITE apidev-rejecttallpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
