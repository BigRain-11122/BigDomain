"""Acceptance suite for the apidev key_view windowed panel read
restart-persistence example window (BigDomain R1907; canon = the
tech-queue "apidev key_view windowed read cross-restart
persistence" row, the R1902 seed, claimed from the tech-lane FIFO
oldest claimable row). Asserts the pre-registered criteria
AC-KVW8..AC-KVW14 from the R1907 claim note (criteria were
registered in state/queue/tech.md before this code ran; honesty
law; the AC-KVW8+ prefix was verified unowned by a whole-repo
scan on claim -- AC-KVW1..7 belong to the R1868 window face).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Covered semantics: the derived purity of the single-key 18-field
panel across an instance restart -- the three-piece stack
(Ledger -> MeteredFace -> DevKeyFace) closes fully in reverse
dependency order and reopens on the same db path and config
bytes; the October explicit-window panel (window echo + ancestry
quota counter + exact-key reject/usage tallies + lifecycle
status) must replay byte-identical from the fresh instance while
the clock stands still (zero in-memory drift, full-envelope
comparable because the two minute-ring fields are frozen too);
two November calls on roll-b -- the very key whose October panel
is pinned -- recalculate the default read via the real product
path (zero cache) while the October windowed read stays
byte-frozen under the banded projection (claim ruling 3: the
panel carries two clock-following minute fields, orthogonal to
the month window per the R1863 AC-ANW5 ruling, so cross-clock
comparisons strip them -- the R1902 dev_board banded-projection
precedent; the full-envelope diff after the clock move is
exactly those two fields); api_calls rows are record-time
immutable so the old window never permeates; a third instance
replays the post-injection state byte-identically (two-instance
sequential reads).

The metered face is the real product injected by reference (no
copy); the two November calls spend real credits from the same
pack the October calls spent. This test source stays pure ASCII
per the encoding discipline.

Usage: python test_apidev_keyviewpersist.py
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
ACCT = "usr:kvp"

# the R1824/R1868 18-key panel pin list (reused verbatim: this
# suite adds zero keys to the envelope)
VIEW_KEYS = sorted([
    "api_key", "dev_account", "key_name", "metered_client",
    "window_cap", "enabled_kinds", "ai_label", "minute_cap",
    "status", "rotated_from_key_id", "window", "quota_used",
    "quota_remaining", "minute_window", "minute_used",
    "reject_tally", "usage_kind_tally", "disclaimer"])

# the two clock-following fields (minute ring orthogonal to the
# month window; R1863 AC-ANW5 / R1902 banded-projection ruling)
MINUTE_FIELDS = ("minute_window", "minute_used")


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


def snap(view):
    return json.dumps(view, sort_keys=True)


def project(view):
    """Banded projection: the envelope minus the two
    clock-following minute fields (the AC-KVW12 comparison
    caliber; R1868 AC-KVW4 / R1902 dev_board precedent)."""
    return json.dumps(
        {k: v for k, v in view.items() if k not in MINUTE_FIELDS},
        sort_keys=True)


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


def expect_ad_error(fn, code):
    try:
        fn()
    except D.ApiDevError as exc:
        return exc.code == code, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-kvp-ac-")
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

        # -- AC-KVW8 October anchor world + pre-close snapshots --
        led.mint_to_pool("pool:reserve", 5000, "MINT-KVP",
                         "settlement")
        led.ensure_account(ACCT, census_avatar_id="kvp")
        led.adjust([("pool:reserve", "debit", 100),
                    (ACCT, "credit", 100)],
                   "manual:fund-kvp", "suite funding kvp")

        kp = dk.issue_key(ACCT, "roll-p", 3, ["backtest"], True)
        dk.buy_credits(kp["api_key"], 10, 1, "PACK-KVP-P")
        _make_calls(dk, clock, kp["api_key"], "KVP-P", 2,
                    "backtest")
        kb = dk.rotate_key(kp["api_key"], "roll-b")
        _make_calls(dk, clock, kb["api_key"], "KVP-B", 1,
                    "backtest")
        ok_rej, code_rej = expect_ad_error(
            lambda: dk.call(kb["api_key"], "backtest",
                            "KVP-B-02", "engine:KVP-B-02"),
            D.E_AD_QUOTA)
        assert ok_rej, "quota reject anchor failed: %s" % code_rej

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys"
                " WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_p = key_id_of(kp["api_key"])
        id_b = key_id_of(kb["api_key"])

        # month-abstraction law (R1813): W derives from a real
        # call row's record-time window column, never hardcoded
        W = conn.execute(
            "SELECT window FROM api_calls WHERE key_id = ?"
            " ORDER BY called_utc, call_ref LIMIT 1",
            (id_p,)).fetchone()[0]

        s_oct_b = snap(dk.key_view(kb["api_key"], window=W))
        s_def_b = snap(dk.key_view(kb["api_key"]))
        s_oct_p = snap(dk.key_view(kp["api_key"], window=W))
        s_nov = snap(dk.key_view(kb["api_key"], window=NEW_WIN))
        s_fut = snap(dk.key_view(kb["api_key"], window=FUT_WIN))

        v_oct_b = json.loads(s_oct_b)
        v_oct_p = json.loads(s_oct_p)
        v_nov = json.loads(s_nov)
        v_fut = json.loads(s_fut)
        # manual SQL crosses: ancestry quota, exact-key tallies
        anc_sql = conn.execute(
            "SELECT COUNT(*) FROM api_calls WHERE window = ?"
            " AND key_id IN (?, ?)", (W, id_p, id_b)).fetchone()[0]
        rej_sql = dict(rjconn.execute(
            "SELECT reason, COUNT(*) FROM reject_events"
            " WHERE key_id = ? AND window = ? GROUP BY reason",
            (id_b, W)).fetchall())
        kind_sql = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM api_calls"
            " WHERE key_id = ? AND window = ? GROUP BY kind",
            (id_b, W)).fetchall())
        kind_sql_p = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM api_calls"
            " WHERE key_id = ? AND window = ? GROUP BY kind",
            (id_p, W)).fetchall())
        kvw8 = (
            W == "2026-10"
            and sorted(v_oct_b.keys()) == VIEW_KEYS
            and len(VIEW_KEYS) == 18
            and s_def_b == s_oct_b
            and v_oct_b["window"] == W
            and v_oct_b["quota_used"] == 3
            and v_oct_b["quota_used"] == anc_sql
            and v_oct_b["quota_remaining"] == 0
            and v_oct_b["window_cap"] == 3
            and v_oct_b["status"] == "active"
            and v_oct_b["rotated_from_key_id"] == id_p
            and v_oct_b["reject_tally"] == {D.E_AD_QUOTA: 1}
            and v_oct_b["reject_tally"] == rej_sql
            and v_oct_b["usage_kind_tally"] == {"backtest": 1}
            and v_oct_b["usage_kind_tally"] == kind_sql
            and v_oct_p["status"] == "rotated_out"
            and v_oct_p["rotated_from_key_id"] is None
            and v_oct_p["quota_used"] == 2
            and v_oct_p["quota_remaining"] == 1
            and v_oct_p["reject_tally"] == {}
            and v_oct_p["usage_kind_tally"] == {"backtest": 2}
            and v_oct_p["usage_kind_tally"] == kind_sql_p
            and v_nov["quota_used"] == 0
            and v_nov["quota_remaining"] == 3
            and v_nov["reject_tally"] == {}
            and v_nov["usage_kind_tally"] == {}
            and v_nov["window"] == NEW_WIN
            and v_fut["quota_used"] == 0
            and v_fut["reject_tally"] == {}
            and v_fut["window"] == FUT_WIN
        )
        record("AC-KVW8", kvw8,
               "October anchor world: rotate chain roll-p 2 calls"
               " -> roll-b 1 call -> 4th E_AD_QUOTA reject; W=%s"
               " SQL-derived; 18-key pin=%s; default==explicit"
               " byte-identical=%s; roll-b quota 3==ancestry SQL"
               " %d remaining=0, reject_tally %s==SQL %s,"
               " kind %s==SQL %s (exact-key attribution); roll-p"
               " dead-key panel status=%s quota 2/1 rotated_from"
               " None tallies %s/%s; nov/fut honest zero panels"
               % (W, sorted(v_oct_b.keys()) == VIEW_KEYS,
                  s_def_b == s_oct_b, anc_sql,
                  v_oct_b["reject_tally"], rej_sql,
                  v_oct_b["usage_kind_tally"], kind_sql,
                  v_oct_p["status"], v_oct_p["reject_tally"],
                  v_oct_p["usage_kind_tally"]))

        # -- AC-KVW9 restart replay: explicit October panel ------
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        replay = snap(dk2.key_view(kb["api_key"], window=W))
        replay2 = snap(dk2.key_view(kb["api_key"], window=W))
        kvw9 = (replay == s_oct_b and replay2 == s_oct_b)
        record("AC-KVW9", kvw9,
               "full stack close (reverse order) -> reopen same"
               " db/config: October explicit-window 18-key panel"
               " byte-identical to the pre-close snapshot=%s"
               " (clock unmoved, so the two minute-ring fields"
               " are full-envelope comparable, zero projection),"
               " second same-param read self-identical=%s"
               % (replay == s_oct_b, replay2 == s_oct_b))

        # -- AC-KVW10 default / roll-p / nov / fut replay ---------
        r_def = snap(dk2.key_view(kb["api_key"]))
        r_oct_p = snap(dk2.key_view(kp["api_key"], window=W))
        r_nov = snap(dk2.key_view(kb["api_key"], window=NEW_WIN))
        r_fut = snap(dk2.key_view(kb["api_key"], window=FUT_WIN))
        kvw10 = (r_def == s_def_b and r_oct_p == s_oct_p
                 and r_nov == s_nov and r_fut == s_fut)
        record("AC-KVW10", kvw10,
               "default read replayed byte-identical=%s (clock"
               " still in October, default month == explicit"
               " October), roll-p dead-key panel=%s, nov zero"
               " panel=%s, fut zero panel=%s -- the derived panel"
               " carries zero in-memory state across the restart"
               % (r_def == s_def_b, r_oct_p == s_oct_p,
                  r_nov == s_nov, r_fut == s_fut))

        # -- AC-KVW11 November calls -> default recompute ---------
        clock.advance(23 * 86400)
        _make_calls(dk2, clock, kb["api_key"], "KVP-N", 2,
                    "backtest")
        nov_b = _count(
            conn, "api_calls",
            " WHERE window = ? AND key_id = ?", (NEW_WIN, id_b))
        nov_default = json.loads(snap(dk2.key_view(kb["api_key"])))
        nov_explicit = json.loads(
            snap(dk2.key_view(kb["api_key"], window=NEW_WIN)))
        kvw11 = (
            nov_b == 2
            and nov_default["window"] == NEW_WIN
            and nov_default["quota_used"] == 2
            and nov_default["quota_remaining"] == 1
            and nov_default["usage_kind_tally"] == {"backtest": 2}
            and nov_default["reject_tally"] == {}
            and snap(nov_default) != s_def_b
            and snap(nov_explicit) == snap(nov_default)
        )
        record("AC-KVW11", kvw11,
               "frozen clock +23d -> 2 November calls on roll-b"
               " (the very key whose October panel is pinned) via"
               " the real product path (record-time window=%s"
               " SQL count==%d): default read followed the clock"
               " into November and recalculated (quota 2,"
               " kind %s, byte-differs from the pre-close"
               " default snapshot=%s = zero cache), November"
               " explicit read == default byte-identical=%s"
               % (NEW_WIN, nov_b,
                  nov_default["usage_kind_tally"],
                  snap(nov_default) != s_def_b,
                  snap(nov_explicit) == snap(nov_default)))

        # -- AC-KVW12 old-window zero permeation (banded proj) ----
        post_oct = dk2.key_view(kb["api_key"], window=W)
        pre_oct = json.loads(s_oct_b)
        diff_keys = sorted(
            k for k in VIEW_KEYS if post_oct[k] != pre_oct[k])
        chain_marks = ",".join("?" for _ in (id_p, id_b))
        chain_oct = _count(
            conn, "api_calls",
            " WHERE window = ? AND key_id IN (" + chain_marks + ")",
            (W, id_p, id_b))
        chain_all = _count(
            conn, "api_calls",
            " WHERE key_id IN (" + chain_marks + ")",
            (id_p, id_b))
        kvw12 = (
            project(post_oct) == project(pre_oct)
            and diff_keys == sorted(MINUTE_FIELDS)
            and post_oct["minute_window"] == clock.minute_utc()
            and post_oct["minute_used"] == 2
            and chain_oct == 3 and chain_all == 5
        )
        record("AC-KVW12", kvw12,
               "after the November injection on the same pinned"
               " key: October explicit-window read stays"
               " byte-frozen under the banded projection (strip"
               " the two minute fields)=%s, the full-envelope"
               " diff is exactly %s (minute ring follows the"
               " clock, orthogonal to the month window; ancestors"
               " sit in the October minute and never leak,"
               " minute_used 3->%d at %s), telescoping chain"
               " all-time %d == oct %d + nov %d, api_calls rows"
               " record-time immutable"
               % (project(post_oct) == project(pre_oct),
                  diff_keys, post_oct["minute_used"],
                  post_oct["minute_window"], chain_all,
                  chain_oct, nov_b))

        # -- AC-KVW13 third instance sequential reads -------------
        f2_a = snap(dk2.key_view(kb["api_key"], window=W))
        f2_b = snap(dk2.key_view(kb["api_key"]))
        f2_c = snap(dk2.key_view(kb["api_key"], window=NEW_WIN))
        f2_d = snap(dk2.key_view(kp["api_key"], window=W))
        conn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = snap(dk3.key_view(kb["api_key"], window=W))
        f3_b = snap(dk3.key_view(kb["api_key"]))
        f3_c = snap(dk3.key_view(kb["api_key"], window=NEW_WIN))
        f3_d = snap(dk3.key_view(kp["api_key"], window=W))
        kvw13 = (f3_a == f2_a and f3_b == f2_b
                 and f3_c == f2_c and f3_d == f2_d
                 and project(json.loads(f3_a)) == project(pre_oct))
        record("AC-KVW13", kvw13,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s), and the October"
               " explicit-window read still equals the ORIGINAL"
               " pre-close snapshot under the banded projection=%s"
               " (windowed panel read survives restart x new-data"
               " unscratched)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d,
                  project(json.loads(f3_a)) == project(pre_oct)))

        # -- AC-KVW14 pure-read law + hygiene ----------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        rj_before = _count(rjconn, "reject_events")
        for w in (W, NEW_WIN, FUT_WIN, None):
            dk3.key_view(kb["api_key"], window=w)
        for w in (W, None):
            dk3.key_view(kp["api_key"], window=w)
        gate_ok, gate_code = expect_ad_error(
            lambda: dk3.key_view("no-such-key", window="2026-13"),
            D.E_AD_UNKNOWN_KEY)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        rj_after = _count(rjconn, "reject_events")

        source = product_pre.decode("ascii")
        idx = source.find("def key_view")
        seg_end = source.find("    def ", idx + 20)
        view_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 code-strip precedent)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', view_seg)
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
        net_pat = re.compile(
            r'^\s*(import|from)\s+(socket|http|urllib|requests)'
            r'\b', re.M)
        net_free = not net_pat.search(me_bytes.decode("ascii"))
        registry_path = os.path.join(
            os.path.dirname(BASE), "reconcile_all.py")
        with open(registry_path, "rb") as handle:
            registry_src = handle.read().decode("ascii")
        wired = ("ledger-apidev-keyviewpersist"
                 in registry_src)
        kvw14 = (
            calls_after == calls_before
            and keys_after == keys_before
            and ev_after == ev_before
            and rj_after == rj_before
            and gate_ok
            and len(write_kw) == 0
            and product_post == product_pre
            and product_pre_sha == product_post_sha
            and cfg_bytes_end == cfg_bytes
            and me_ascii and net_free and wired
        )
        record("AC-KVW14", kvw14,
               "pure read: 11-form read battery across both keys"
               " (plus the unknown-key gate probe=%s) moves zero"
               " rows (api_calls %d==%d, api_dev_keys %d==%d,"
               " key_events %d==%d, reject_events %d==%d),"
               " key_view segment zero write keywords=%d,"
               " apidev.py sha256 stable=%s, config.json"
               " byte-stable=%s, suite source pure ASCII=%s,"
               " zero network imports=%s, runner row wired=%s"
               % (gate_ok, calls_after, calls_before,
                  keys_after, keys_before, ev_after, ev_before,
                  rj_after, rj_before, len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  net_free, wired))

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
    print("SUITE apidev-keyviewpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
