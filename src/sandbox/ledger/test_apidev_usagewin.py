"""Acceptance suite for the apidev usage-log window-filtered
read face (BigDomain R1732; canon = tech-queue "apidev usage_log
window-filtered read" row, seed = usage_log read cap R1729).
Asserts the pre-registered criteria AC-UW1..AC-UW8 from the
R1732 and R1739 tech-queue claim notes (criteria were registered
before this code ran; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Covered semantics: usage_log(api_key, limit=0, window=None)
keeps the all-months default behavior byte-stable (envelope
key set exactly api_key/calls/disclaimer, row order and row
set identical to the manual SQL cross-check); an explicit
"YYYY-MM" window filters the read to that month at read time
over the immutable rows (a historical month stays readable
forever, a future month is an honest empty read); the window
filter applies before COUNT/LIMIT so the overflow block total
is the in-window row count (not the all-months count); the
explicit-window envelope adds an additive "window" key
(mirroring the overflow block additivity, default face stays
key-drift-free); the key gate fires before the window gate
(call-chain key-gate-first law) and the limit gate before the
window gate (deterministic parameter gate order, probed with a
double-bad call); 11 bad window shapes reject E_AD_BAD_ARGS
fail-closed with zero rows read (empty string is a bad shape,
only None is the default sentinel); window-filtered reads
stay read-only (zero api_calls rows written) and dead keys
(revoked, rotated-out) keep the window-filtered read face open
with identical semantics.

Month rollover (AC-UW8, the R1739 symmetric case closing the
window-family gap to the R1730 rejectwin / R1738 usagekind
rollover precedents): the quota ring rolls with _window_utc so
a capped-out October key accepts calls again after the frozen
clock crosses the month boundary; the all-months default read
then carries both months with the new rows record-time stamped
into the new window; old-month explicit reads keep their exact
row sets (the cap-rejected call left zero rows); immutable rows
are never lost; and the window-x-cap orthogonal read after the
roll counts its overflow total inside the new-month window.

Historical rows enter through a direct fixture INSERT (the
product record path stamps the window column at record time
from the live clock, so a past month cannot be produced
through the public API; the fixture injects what a real past
month would have stamped -- same honest note as the R1730
rejectwin suite).

Deterministic clock: module-level _now_utc/_minute_utc/
_window_utc are monkeypatched onto a frozen clock holder
(R1678 frozen-clock precedent), restored in finally. The
metered face is the real product injected by reference (no
copy); this suite reaches the billing ring only through the
apidev public API. This source stays pure ASCII per the
encoding discipline.

Usage: python test_apidev_usagewin.py
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
import apidev as D                      # noqa: E402 (R1700..R1732)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 10, 7, 30, 0)

CUR_WIN = "2026-10"
HIST_WIN = "2026-09"
FUT_WIN = "2026-11"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_ad_error(fn, *codes):
    try:
        fn()
    except D.ApiDevError as exc:
        return exc.code in codes, exc.code, exc.detail
    except M.MeteredError as exc:
        return exc.code in codes, exc.code, getattr(exc, "detail", "")
    return False, "no-error-raised", ""


def _call_count(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM api_calls").fetchone()[0]


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


HIST_ROWS = [
    ("UW-H-01", "2026-09-05T08:00:00Z"),
    ("UW-H-02", "2026-09-12T09:30:00Z"),
    ("UW-H-03", "2026-09-20T14:00:00Z"),
    ("UW-H-04", "2026-09-28T18:45:00Z"),
]


def _inject_hist(conn, key_id):
    for call_ref, called_utc in HIST_ROWS:
        conn.execute(
            "INSERT INTO api_calls (call_ref, key_id, kind,"
            " engine_ref, window, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (call_ref, key_id, "backtest", "engine:%s" % call_ref,
             HIST_WIN, called_utc))
    conn.commit()


def _manual_refs(conn, key_id, window=None):
    sql = ("SELECT call_ref FROM api_calls WHERE key_id = ?")
    args = [key_id]
    if window is not None:
        sql += " AND window = ?"
        args.append(window)
    sql += " ORDER BY called_utc, call_ref"
    return [r[0] for r in conn.execute(sql, args).fetchall()]


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-usagewin-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-UW-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada-uw", "suite funding ada")
    conn = sqlite3.connect(db_path)
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # key with 6 current-month product rows + 4 fixture rows in
        # the historical month = 10 all-months rows, 6 in-window.
        k10 = dk.issue_key("usr:ada", "uw-full", 20, ["backtest"],
                           False)
        dk.buy_credits(k10["api_key"], 14, 1, "PACK-UW-A")
        refs_cur = _make_calls(dk, clock, k10["api_key"], "UW-A", 6)
        k10_id = conn.execute(
            "SELECT key_id FROM api_dev_keys"
            " WHERE dev_account = ? AND key_name = ?",
            ("usr:ada", "uw-full")).fetchone()[0]
        _inject_hist(conn, k10_id)
        refs_hist = [r[0] for r in HIST_ROWS]

        # -- AC-UW1 contract + default zero-drift ---------------------
        full = dk.usage_log(k10["api_key"])
        manual_all = _manual_refs(conn, k10_id)
        env_keys = set(full.keys())
        row_keys = set(full["calls"][0].keys())
        ok_unknown_badwin, code_unknown_badwin, _d1 = expect_ad_error(
            lambda: dk.usage_log("sk-nonexistent", 0, "2026-13"),
            D.E_AD_UNKNOWN_KEY)
        ok_dbl, code_dbl, det_dbl = expect_ad_error(
            lambda: dk.usage_log(k10["api_key"], -1, "2026-13"),
            D.E_AD_BAD_ARGS)
        uw1 = (env_keys == {"api_key", "calls", "disclaimer"}
               and len(full["calls"]) == 10
               and [c["call_ref"] for c in full["calls"]]
               == refs_hist + refs_cur
               and [c["call_ref"] for c in full["calls"]]
               == manual_all
               and row_keys == {"call_ref", "kind", "engine_ref",
                                "window", "called_utc"}
               and ok_unknown_badwin
               and code_unknown_badwin == D.E_AD_UNKNOWN_KEY
               and ok_dbl and code_dbl == D.E_AD_BAD_ARGS
               and det_dbl == "limit must be an integer >= 0")
        record("AC-UW1", uw1,
               "default envelope keys=%s (3-key set), 10 rows in"
               " ascending order=%s (manual SQL cross-check %s),"
               " row fields=%s; unknown key + bad window -> %s"
               " (key gate first); double-bad limit+window -> %s"
               " detail=%r (limit gate before window gate)"
               % (sorted(env_keys),
                  [c["call_ref"] for c in full["calls"]]
                  == refs_hist + refs_cur,
                  [c["call_ref"] for c in full["calls"]]
                  == manual_all,
                  sorted(row_keys), code_unknown_badwin, code_dbl,
                  det_dbl))

        # -- AC-UW2 bad window shapes fail-closed ----------------------
        calls_before = _call_count(conn)
        codes = []
        oks = []
        for bad in ("2026-13", "2026-00", "2026-1", "2026/10",
                    "2026", "202610", "abcd", "", 2026, True, 2.5):
            ok_bad, code_bad, _d2 = expect_ad_error(
                lambda b=bad: dk.usage_log(k10["api_key"], 0, b),
                D.E_AD_BAD_ARGS)
            oks.append(ok_bad)
            codes.append(code_bad)
        calls_after = _call_count(conn)
        uw2 = (all(oks) and codes == [D.E_AD_BAD_ARGS] * 11
               and calls_after == calls_before)
        record("AC-UW2", uw2,
               "11 bad shapes -> %s (api_calls %d==%d, zero rows"
               " read); empty string is NOT the default sentinel"
               " (only None is)" % (codes, calls_after,
                                    calls_before))

        # -- AC-UW3 historical / future / separation -------------------
        hist = dk.usage_log(k10["api_key"], window=HIST_WIN)
        fut = dk.usage_log(k10["api_key"], window=FUT_WIN)
        manual_hist = _manual_refs(conn, k10_id, HIST_WIN)
        cur_refs_in_hist = [c for c in hist["calls"]
                            if c["window"] != HIST_WIN]
        hist_refs_in_full = [c["call_ref"] for c in full["calls"]
                             if c["window"] == HIST_WIN]
        uw3 = (set(hist.keys()) == {"api_key", "calls", "window",
                                    "disclaimer"}
               and hist["window"] == HIST_WIN
               and [c["call_ref"] for c in hist["calls"]]
               == refs_hist
               and [c["call_ref"] for c in hist["calls"]]
               == manual_hist
               and all(c["window"] == HIST_WIN
                       for c in hist["calls"])
               and len(cur_refs_in_hist) == 0
               and fut["calls"] == [] and fut["window"] == FUT_WIN
               and sorted(hist_refs_in_full) == sorted(refs_hist)
               and len(full["calls"]) == 10)
        record("AC-UW3", uw3,
               "fixture-injected 2026-09 rows read back=%s"
               " (manual SQL equal=%s, all window=%s); future"
               " %s honest empty read calls=%s; separation:"
               " default full read keeps %d rows (historical"
               " included=%s), historical read has zero"
               " current-month rows"
               % ([c["call_ref"] for c in hist["calls"]]
                  == refs_hist,
                  [c["call_ref"] for c in hist["calls"]]
                  == manual_hist,
                  hist["calls"][0]["window"] if hist["calls"]
                  else "n/a",
                  FUT_WIN, fut["calls"], len(full["calls"]),
                  sorted(hist_refs_in_full)
                  == sorted(refs_hist)))

        # -- AC-UW4 window x cap orthogonality ------------------------
        t3 = dk.usage_log(k10["api_key"], 3, window=CUR_WIN)
        mirror = conn.execute(
            "SELECT call_ref FROM api_calls"
            " WHERE key_id = ? AND window = ?"
            " ORDER BY called_utc DESC, call_ref DESC LIMIT ?",
            (k10_id, CUR_WIN, 3)).fetchall()
        mirror_refs = [r[0] for r in reversed(mirror)]
        cur_full = [c for c in full["calls"]
                    if c["window"] == CUR_WIN]
        under = dk.usage_log(k10["api_key"], 50, window=CUR_WIN)
        exact = dk.usage_log(k10["api_key"], 6, window=CUR_WIN)
        uw4 = (set(t3.keys()) == {"api_key", "calls", "limit",
                                  "total", "returned", "truncated",
                                  "window", "disclaimer"}
               and t3["limit"] == 3 and t3["total"] == 6
               and t3["returned"] == 3
               and t3["truncated"] is True
               and t3["window"] == CUR_WIN
               and [c["call_ref"] for c in t3["calls"]]
               == mirror_refs
               and t3["calls"] == cur_full[-3:]
               and under["total"] == 6 and under["returned"] == 6
               and under["truncated"] is False
               and under["calls"] == cur_full
               and exact["limit"] == 6 and exact["total"] == 6
               and exact["returned"] == 6
               and exact["truncated"] is False
               and exact["calls"] == cur_full)
        record("AC-UW4", uw4,
               "window=%s over 6 in-window rows (all-months=10):"
               " limit=3 -> total=%d (in-window, NOT 10)"
               " returned=%d truncated=%s, rows=%s == mirror SQL"
               " %s == ascending tail %s; limit=50 -> returned=%d"
               " truncated=%s; limit=6==total -> truncated=%s;"
               " explicit-window envelope keys=%s (additive"
               " window key)"
               % (CUR_WIN, t3["total"], t3["returned"],
                  t3["truncated"],
                  [c["call_ref"] for c in t3["calls"]],
                  mirror_refs,
                  [c["call_ref"] for c in cur_full[-3:]],
                  under["returned"], under["truncated"],
                  exact["truncated"], sorted(t3.keys())))

        # -- AC-UW5 boundary states ----------------------------------
        k0 = dk.issue_key("usr:ada", "uw-empty", 5, ["backtest"],
                          False)
        empty_cap = dk.usage_log(k0["api_key"], 3, window=CUR_WIN)
        empty_full = dk.usage_log(k0["api_key"], window=CUR_WIN)
        one = dk.usage_log(k10["api_key"], 1, window=CUR_WIN)
        uw5 = (empty_cap["calls"] == [] and empty_cap["total"] == 0
               and empty_cap["returned"] == 0
               and empty_cap["truncated"] is False
               and empty_cap["window"] == CUR_WIN
               and empty_full["calls"] == []
               and set(empty_full.keys())
               == {"api_key", "calls", "window", "disclaimer"}
               and one["returned"] == 1 and one["total"] == 6
               and one["truncated"] is True
               and one["calls"] == cur_full[-1:])
        record("AC-UW5", uw5,
               "zero-row window + limit=3: calls=%s total=%d"
               " returned=%d truncated=%s window=%s; zero-row"
               " window + limit=0: calls=%s keys=%s; limit=1:"
               " returned=%d truncated=%s tail=%s"
               % (empty_cap["calls"], empty_cap["total"],
                  empty_cap["returned"], empty_cap["truncated"],
                  empty_cap["window"], empty_full["calls"],
                  sorted(empty_full.keys()), one["returned"],
                  one["truncated"],
                  [c["call_ref"] for c in one["calls"]]))

        # -- AC-UW6 read-only law + dead-key faces --------------------
        reads_before = _call_count(conn)
        dk.usage_log(k10["api_key"])
        dk.usage_log(k10["api_key"], 2, window=CUR_WIN)
        dk.usage_log(k10["api_key"], window=HIST_WIN)
        dk.usage_log(k0["api_key"], 3, window=CUR_WIN)
        reads_after = _call_count(conn)
        krev = dk.issue_key("usr:ada", "uw-rev", 20, ["backtest"],
                            False)
        dk.buy_credits(krev["api_key"], 8, 1, "PACK-UW-R")
        refs_3 = _make_calls(dk, clock, krev["api_key"], "UW-R", 3)
        dk.revoke_key(krev["api_key"])
        rev_win = dk.usage_log(krev["api_key"], window=CUR_WIN)
        rev_cap = dk.usage_log(krev["api_key"], 2, window=CUR_WIN)
        krot = dk.issue_key("usr:ada", "uw-rot", 20, ["backtest"],
                            False)
        dk.buy_credits(krot["api_key"], 6, 1, "PACK-UW-T")
        _make_calls(dk, clock, krot["api_key"], "UW-T", 2)
        dk.rotate_key(krot["api_key"], "uw-rot-v2")
        rot_win = dk.usage_log(krot["api_key"], window=CUR_WIN)
        rot_cap = dk.usage_log(krot["api_key"], 1, window=CUR_WIN)
        uw6 = (reads_after == reads_before
               and len(rev_win["calls"]) == 3
               and [c["call_ref"] for c in rev_win["calls"]]
               == refs_3
               and rev_cap["total"] == 3
               and rev_cap["returned"] == 2
               and rev_cap["truncated"] is True
               and rev_cap["calls"] == rev_win["calls"][-2:]
               and len(rot_win["calls"]) == 2
               and rot_cap["total"] == 2 and rot_cap["returned"] == 1
               and rot_cap["truncated"] is True
               and rot_cap["calls"] == rot_win["calls"][-1:])
        record("AC-UW6", uw6,
               "window-filtered reads leave api_calls %d==%d;"
               " revoked key window read open (3 rows, capped"
               " total=%d returned=%d truncated=%s), rotated-out"
               " key window read open (2 rows, capped total=%d"
               " returned=%d)"
               % (reads_after, reads_before, rev_cap["total"],
                  rev_cap["returned"], rev_cap["truncated"],
                  rot_cap["total"], rot_cap["returned"]))

        # -- AC-UW8 month-rollover truth-preservation (R1739) ---------
        # quota-ring roll first (the same _window_utc source the
        # window filter reads through): a key capped out in
        # October must accept calls again after the frozen clock
        # crosses the month boundary; the all-months default read
        # then carries both months with the new rows record-time
        # stamped into the new window.
        kroll = dk.issue_key("usr:ada", "uw-roll", 3,
                             ["backtest", "visualize"], False)
        dk.buy_credits(kroll["api_key"], 10, 1, "PACK-UW-M")
        refs_oct = _make_calls(dk, clock, kroll["api_key"],
                               "UW-M", 3)
        ok_oct_q, code_oct_q, _d3 = expect_ad_error(
            lambda: dk.call(kroll["api_key"], "backtest",
                            "UW-M-04", "e"),
            D.E_AD_QUOTA)
        kroll_id = conn.execute(
            "SELECT key_id FROM api_dev_keys"
            " WHERE dev_account = ? AND key_name = ?",
            ("usr:ada", "uw-roll")).fetchone()[0]
        clock.advance(23 * 86400)
        dk.call(kroll["api_key"], "backtest", "UW-N-01", "e")
        dk.call(kroll["api_key"], "visualize", "UW-N-02", "e")
        nov_win = "2026-11"
        refs_nov = ["UW-N-01", "UW-N-02"]
        roll_def = dk.usage_log(kroll["api_key"])
        manual_roll_all = _manual_refs(conn, kroll_id)
        stamp_nov = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE key_id = ? AND window = ?"
            " AND call_ref LIKE 'UW-N-%'",
            (kroll_id, nov_win)).fetchone()[0]
        roll_oct = dk.usage_log(kroll["api_key"],
                                window="2026-10")
        roll_nov = dk.usage_log(kroll["api_key"],
                               window=nov_win)
        manual_oct = _manual_refs(conn, kroll_id, "2026-10")
        manual_nov = _manual_refs(conn, kroll_id, nov_win)
        k10_oct = dk.usage_log(k10["api_key"],
                               window="2026-10")
        k10_sep = dk.usage_log(k10["api_key"], window=HIST_WIN)
        k10_all_after = dk.usage_log(k10["api_key"])
        # window x cap orthogonal read after the roll: overflow
        # total = new-month in-window row count (2, not 5).
        cap_nov = dk.usage_log(kroll["api_key"], 1,
                               window=nov_win)
        mirror_nov = conn.execute(
            "SELECT call_ref FROM api_calls"
            " WHERE key_id = ? AND window = ?"
            " ORDER BY called_utc DESC, call_ref DESC LIMIT ?",
            (kroll_id, nov_win, 1)).fetchall()
        mirror_nov_refs = [r[0] for r in reversed(mirror_nov)]
        all_time = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE key_id = ?", (kroll_id,)).fetchone()[0]
        uw8 = (ok_oct_q and code_oct_q == D.E_AD_QUOTA
               and set(roll_def.keys())
               == {"api_key", "calls", "disclaimer"}
               and len(roll_def["calls"]) == 5
               and [c["call_ref"] for c in roll_def["calls"]]
               == refs_oct + refs_nov
               and [c["call_ref"] for c in roll_def["calls"]]
               == manual_roll_all
               and stamp_nov == 2
               and [c["call_ref"] for c in roll_oct["calls"]]
               == refs_oct
               and [c["call_ref"] for c in roll_oct["calls"]]
               == manual_oct
               and all(c["window"] == "2026-10"
                       for c in roll_oct["calls"])
               and [c["call_ref"] for c in roll_nov["calls"]]
               == refs_nov
               and [c["call_ref"] for c in roll_nov["calls"]]
               == manual_nov
               and all(c["window"] == nov_win
                       for c in roll_nov["calls"])
               and len(k10_oct["calls"]) == 6
               and len(k10_sep["calls"]) == 4
               and len(k10_all_after["calls"]) == 10
               and cap_nov["limit"] == 1
               and cap_nov["total"] == 2
               and cap_nov["returned"] == 1
               and cap_nov["truncated"] is True
               and cap_nov["window"] == nov_win
               and [c["call_ref"] for c in cap_nov["calls"]]
               == mirror_nov_refs
               and all_time == 5)
        record("AC-UW8", uw8,
               "month roll (frozen clock +23d): October cap"
               " exhausted first (%s on 4th call), November calls"
               " succeed = quota ring rolled with _window_utc;"
               " default all-months read carries both months"
               " rows=%d (%s, manual SQL equal=%s, record-time"
               " %s stamps=%d, envelope keys=%s); old 2026-10"
               " explicit read intact rows=%s (quota-rejected"
               " call left zero rows, manual equal=%s); new %s"
               " explicit read rows=%s (manual equal=%s, zero"
               " October penetration); k10 2026-10 rows=%d"
               " unchanged, k10 %s fixture rows=%d unchanged,"
               " k10 all-months=%d; orthogonal cap read after"
               " roll: limit=1 window=%s -> total=%d"
               " (in-window, NOT 5) returned=%d truncated=%s"
               " tail=%s == mirror SQL %s; all-time rows=%d"
               " (3+2, immutable rows never lost)"
               % (code_oct_q, len(roll_def["calls"]),
                  [c["call_ref"] for c in roll_def["calls"]],
                  [c["call_ref"] for c in roll_def["calls"]]
                  == manual_roll_all, nov_win, stamp_nov,
                  sorted(roll_def.keys()),
                  [c["call_ref"] for c in roll_oct["calls"]],
                  [c["call_ref"] for c in roll_oct["calls"]]
                  == manual_oct, nov_win,
                  [c["call_ref"] for c in roll_nov["calls"]],
                  [c["call_ref"] for c in roll_nov["calls"]]
                  == manual_nov, len(k10_oct["calls"]),
                  HIST_WIN, len(k10_sep["calls"]),
                  len(k10_all_after["calls"]), nov_win,
                  cap_nov["total"], cap_nov["returned"],
                  cap_nov["truncated"],
                  [c["call_ref"] for c in cap_nov["calls"]],
                  mirror_nov_refs, all_time))

        # -- AC-UW7 hygiene + delivery carriers ----------------------
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
        win_face = re.search(r"def usage_log\(self, api_key,"
                             r" limit=0, window=None\)",
                             source) is not None
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "r",
                  encoding="utf-8") as handle:
            runner_src = handle.read()
        registered = re.search(
            r'\("ledger-apidev-usagewin",\s*'
            r'os\.path\.join\("ledger",\s*'
            r'"test_apidev_usagewin\.py"\),\s*8\)',
            runner_src) is not None
        dk.close()
        closed = []
        for handle_conn in (dk._conn, dk._lconn, dk._rconn):
            try:
                handle_conn.execute("SELECT 1")
                closed.append(False)
            except sqlite3.ProgrammingError:
                closed.append(True)
        uw7 = (cfg_bytes_end == cfg_bytes
               and is_ascii and not has_update and not has_rng
               and len(imports_net) == 0 and win_face
               and registered
               and len(RESULTS) == 7
               and all(ok for _, ok in RESULTS)
               and closed == [True, True, True])
        record("AC-UW7", uw7,
               "hygiene: config.json byte-stable=%s, source"
               " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
               " net-imports=%d, window face exported=%s,"
               " reconcile_all SUITES row registered=%s, close()"
               " shuts all three connections=%s; suite self-"
               "carrier: %d prior criteria all green=%s"
               % (cfg_bytes_end == cfg_bytes, is_ascii,
                  not has_update, not has_rng, len(imports_net),
                  win_face, registered, closed == [True, True, True],
                  len(RESULTS), all(ok for _, ok in RESULTS)))
    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-usagewin: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
