"""Acceptance suite for the apidev usage by-kind window-count
read face (BigDomain R1735; canon = tech-queue "apidev usage
by-kind window-count read" row, seed = usage_log window-filtered
read R1732). Asserts the pre-registered criteria AC-UK1..AC-UK7
(the criteria were registered on the tech-queue claim row before
this code ran; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Covered semantics: usage_kind_tally(api_key, window=None) is the
read-face family's third symmetric member (reject_tally counts by
reason, usage_log returns rows, this face counts by API kind)
answering the developer panel's "which kinds am I actually using
this month" question that quota_used's single total cannot.
window=None (the default) reads the current UTC month through the
same _window_utc source as the quota ring; an explicit "YYYY-MM"
string reads any month window at read time over the immutable
call rows (a historical month stays readable forever, a future
month is an honest empty read); 11 bad window shapes reject
E_AD_BAD_ARGS fail-closed with zero rows read (empty string is a
bad shape, only None is the default sentinel); the key gate fires
first (the call-chain key-gate-first law). Aggregation is
read-time GROUP BY kind COUNT over the append-only api_calls rows
(zero new tables, zero UPDATE); rows are attributed to the exact
key, so a rotated successor does not inherit ancestor kinds
(panel face, not enforcement face, the R1728 attribution note).
The embedded faces (key_view, dev_board) gain the current-month
by-kind profile additively and keep window-free signatures (the
AC-RJW4 embedded-face law); dead keys (revoked, rotated-out)
keep the face open with the tally intact.

Historical rows enter through a direct fixture INSERT (the
product record path stamps the window column at record time from
the live clock, so a past month cannot be produced through the
public API; the fixture injects what a real past month would have
stamped -- same honest note as the R1730/R1732 suites).

Deterministic clock: module-level _now_utc/_minute_utc/
_window_utc are monkeypatched onto a frozen clock holder
(R1678 frozen-clock precedent), restored in finally. The metered
face is the real product injected by reference (no copy); this
suite reaches the billing ring only through the apidev public
API. This source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_usagekind.py
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
import apidev as D                      # noqa: E402 (R1700..R1735)

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


def _make_calls(dk, clock, api_key, prefix, n, kind, start=1):
    refs = ["%s-%02d" % (prefix, i) for i in range(start, start + n)]
    for ref in refs:
        dk.call(api_key, kind, ref, "engine:%s" % ref)
        clock.advance(7)
    return refs


# fixture-injected rows for the historical month: 2 backtest +
# 1 visualize (the product record path stamps the window at
# record time, so a past month needs the direct honest INSERT)
HIST_ROWS = [
    ("UK-H-01", "backtest", "2026-09-05T08:00:00Z"),
    ("UK-H-02", "backtest", "2026-09-12T09:30:00Z"),
    ("UK-H-03", "visualize", "2026-09-20T14:00:00Z"),
]


def _inject_hist(conn, key_id):
    for call_ref, kind, called_utc in HIST_ROWS:
        conn.execute(
            "INSERT INTO api_calls (call_ref, key_id, kind,"
            " engine_ref, window, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (call_ref, key_id, kind, "engine:%s" % call_ref,
             HIST_WIN, called_utc))
    conn.commit()


def _manual_kinds(conn, key_id, window):
    return {r[0]: int(r[1]) for r in conn.execute(
        "SELECT kind, COUNT(*) FROM api_calls"
        " WHERE key_id = ? AND window = ?"
        " GROUP BY kind ORDER BY kind",
        (key_id, window)).fetchall()}


def _manual_board_kinds(conn, dev_account, window):
    return {r[0]: int(r[1]) for r in conn.execute(
        "SELECT a.kind, COUNT(*) FROM api_calls a"
        " JOIN api_dev_keys k ON a.key_id = k.key_id"
        " WHERE k.dev_account = ? AND a.window = ?"
        " GROUP BY a.kind ORDER BY a.kind",
        (dev_account, window)).fetchall()}


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-usagekind-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-UK-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada-uk", "suite funding ada")
    conn = sqlite3.connect(db_path)
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # multi-kind key: 4 backtest + 2 visualize current-month
        # product rows + 3 fixture rows in the historical month.
        k10 = dk.issue_key("usr:ada", "uk-full", 20,
                           ["backtest", "visualize"], False)
        dk.buy_credits(k10["api_key"], 14, 1, "PACK-UK-A")
        _make_calls(dk, clock, k10["api_key"], "UK-B", 4, "backtest")
        _make_calls(dk, clock, k10["api_key"], "UK-V", 2, "visualize")
        k10_id = conn.execute(
            "SELECT key_id FROM api_dev_keys"
            " WHERE dev_account = ? AND key_name = ?",
            ("usr:ada", "uk-full")).fetchone()[0]
        _inject_hist(conn, k10_id)

        # -- AC-UK1 contract + default current-month -------------------
        t_def = dk.usage_kind_tally(k10["api_key"])
        manual_cur = _manual_kinds(conn, k10_id, CUR_WIN)
        ok_unknown_badwin, code_unknown_badwin, _d1 = expect_ad_error(
            lambda: dk.usage_kind_tally("sk-nonexistent", "2026-13"),
            D.E_AD_UNKNOWN_KEY)
        uk1 = (set(t_def.keys())
               == {"api_key", "key_name", "window", "by_kind",
                   "total", "disclaimer"}
               and t_def["window"] == CUR_WIN
               and t_def["by_kind"] == {"backtest": 4,
                                       "visualize": 2}
               and t_def["by_kind"] == manual_cur
               and t_def["total"] == 6
               and t_def["key_name"] == "uk-full"
               and ok_unknown_badwin
               and code_unknown_badwin == D.E_AD_UNKNOWN_KEY)
        record("AC-UK1", uk1,
               "default envelope keys=%s (reject_tally mirror"
               " 6-key set), window=%s, by_kind=%s (manual SQL"
               " equal=%s), total=%d; unknown key + bad window"
               " -> %s (key gate first)"
               % (sorted(t_def.keys()), t_def["window"],
                  t_def["by_kind"], t_def["by_kind"] == manual_cur,
                  t_def["total"], code_unknown_badwin))

        # -- AC-UK2 bad window shapes fail-closed -----------------------
        calls_before = _call_count(conn)
        codes = []
        oks = []
        for bad in ("2026-13", "2026-00", "2026-1", "2026/10",
                    "2026", "202610", "abcd", "", 2026, True, 2.5):
            ok_bad, code_bad, _d2 = expect_ad_error(
                lambda b=bad: dk.usage_kind_tally(k10["api_key"], b),
                D.E_AD_BAD_ARGS)
            oks.append(ok_bad)
            codes.append(code_bad)
        calls_after = _call_count(conn)
        uk2 = (all(oks) and codes == [D.E_AD_BAD_ARGS] * 11
               and calls_after == calls_before)
        record("AC-UK2", uk2,
               "11 bad shapes -> %s (api_calls %d==%d, zero rows"
               " read); empty string is NOT the default sentinel"
               " (only None is)" % (codes, calls_after,
                                    calls_before))

        # -- AC-UK3 historical / future / separation -------------------
        t_hist = dk.usage_kind_tally(k10["api_key"], window=HIST_WIN)
        t_fut = dk.usage_kind_tally(k10["api_key"], window=FUT_WIN)
        manual_hist = _manual_kinds(conn, k10_id, HIST_WIN)
        hist_expected = {"backtest": 2, "visualize": 1}
        uk3 = (set(t_hist.keys())
               == {"api_key", "key_name", "window", "by_kind",
                   "total", "disclaimer"}
               and t_hist["window"] == HIST_WIN
               and t_hist["by_kind"] == hist_expected
               and t_hist["by_kind"] == manual_hist
               and t_hist["total"] == 3
               and t_fut["by_kind"] == {} and t_fut["total"] == 0
               and t_fut["window"] == FUT_WIN
               and t_def["by_kind"] == {"backtest": 4,
                                        "visualize": 2})
        record("AC-UK3", uk3,
               "fixture-injected %s rows read back=%s (manual SQL"
               " equal=%s total=%d); future %s honest empty"
               " by_kind=%s total=%d; separation: default"
               " current-month by_kind=%s (zero historical"
               " permeation), historical read excludes"
               " current rows" % (HIST_WIN, t_hist["by_kind"],
                                  t_hist["by_kind"] == manual_hist,
                                  t_hist["total"], FUT_WIN,
                                  t_fut["by_kind"], t_fut["total"],
                                  t_def["by_kind"]))

        # -- AC-UK4 aggregation semantics -------------------------------
        kvis = dk.issue_key("usr:ada", "uk-vis", 10, ["visualize"],
                            False)
        dk.buy_credits(kvis["api_key"], 6, 1, "PACK-UK-V")
        _make_calls(dk, clock, kvis["api_key"], "UK-S", 2,
                    "visualize")
        kvis_id = conn.execute(
            "SELECT key_id FROM api_dev_keys"
            " WHERE dev_account = ? AND key_name = ?",
            ("usr:ada", "uk-vis")).fetchone()[0]
        t_vis = dk.usage_kind_tally(kvis["api_key"])
        manual_vis = _manual_kinds(conn, kvis_id, CUR_WIN)
        k0 = dk.issue_key("usr:ada", "uk-empty", 5, ["backtest"],
                          False)
        t_zero = dk.usage_kind_tally(k0["api_key"])
        zero_total_ok = (t_zero["by_kind"] == {} and t_zero["total"] == 0)
        sum_law = all(
            t["total"] == sum(t["by_kind"].values())
            for t in (t_def, t_hist, t_vis, t_zero))
        uk4 = (t_vis["by_kind"] == {"visualize": 2}
               and t_vis["by_kind"] == manual_vis
               and t_def["total"] == 6 and zero_total_ok
               and sum_law)
        record("AC-UK4", uk4,
               "single-kind key counts only its own kind:"
               " by_kind=%s (manual SQL equal=%s, zero phantom"
               " backtest); zero-row key honest empty=%s"
               " total=%d; total==sum(by_kind) law on all four"
               " reads=%s" % (t_vis["by_kind"],
                              t_vis["by_kind"] == manual_vis,
                              t_zero["by_kind"], t_zero["total"],
                              sum_law))

        # -- AC-UK5 embedded faces keep the current-month default -------
        v_full = dk.key_view(k10["api_key"])
        prior_keys = {"api_key", "dev_account", "key_name",
                      "metered_client", "window_cap", "enabled_kinds",
                      "ai_label", "minute_cap", "status",
                      "rotated_from_key_id", "window", "quota_used",
                      "quota_remaining", "minute_window",
                      "minute_used", "reject_tally", "disclaimer"}
        board = dk.dev_board("usr:ada")
        rows_have_kinds = all("usage_kind_tally" in k
                              for k in board["keys"])
        board_full = [k for k in board["keys"]
                      if k["key_name"] == "uk-full"][0]
        manual_board = _manual_board_kinds(conn, "usr:ada",
                                           CUR_WIN)
        src = open(os.path.join(BASE, "apidev.py"), "r",
                   encoding="ascii").read()
        kv_sig_ok = (re.search(r"def key_view\(self, api_key\)",
                               src) is not None
                     and re.search(
                         r"def key_view\(self, api_key,\s*window",
                         src) is None)
        db_sig_ok = (re.search(
                         r"def dev_board\(self, dev_account\)",
                         src) is not None
                     and re.search(
                         r"def dev_board\(self, dev_account,\s*"
                         r"window",
                         src) is None)
        uk5 = (prior_keys.issubset(set(v_full.keys()))
               and v_full["usage_kind_tally"]
               == {"backtest": 4, "visualize": 2}
               and rows_have_kinds
               and board_full["usage_kind_tally"]
               == {"backtest": 4, "visualize": 2}
               and board["usage_kind_tally_total"] == manual_board
               and kv_sig_ok and db_sig_ok)
        record("AC-UK5", uk5,
               "key_view usage_kind_tally=%s additive (prior key"
               " set preserved=%s), dev_board rows all carry"
               " usage_kind_tally (uk-full=%s), board merged"
               " total=%s (manual all-key SQL equal=%s), zero"
               " historical penetration; source signatures"
               " window-free: key_view=%s dev_board=%s"
               % (v_full["usage_kind_tally"],
                  prior_keys.issubset(set(v_full.keys())),
                  board_full["usage_kind_tally"],
                  board["usage_kind_tally_total"],
                  board["usage_kind_tally_total"] == manual_board,
                  kv_sig_ok, db_sig_ok))

        # -- AC-UK6 read-only law + dead-key faces ---------------------
        reads_before = _call_count(conn)
        dk.usage_kind_tally(k10["api_key"])
        dk.usage_kind_tally(k10["api_key"], window=HIST_WIN)
        dk.usage_kind_tally(k0["api_key"])
        reads_after = _call_count(conn)
        krev = dk.issue_key("usr:ada", "uk-rev", 20,
                            ["backtest", "visualize"], False)
        dk.buy_credits(krev["api_key"], 8, 1, "PACK-UK-R")
        _make_calls(dk, clock, krev["api_key"], "UK-R", 2,
                    "backtest")
        _make_calls(dk, clock, krev["api_key"], "UK-RV", 1,
                    "visualize")
        dk.revoke_key(krev["api_key"])
        rev_t = dk.usage_kind_tally(krev["api_key"])
        rev_hist = dk.usage_kind_tally(krev["api_key"],
                                       window=HIST_WIN)
        krot = dk.issue_key("usr:ada", "uk-rot", 20, ["backtest"],
                            False)
        dk.buy_credits(krot["api_key"], 6, 1, "PACK-UK-T")
        _make_calls(dk, clock, krot["api_key"], "UK-T", 2,
                    "backtest")
        rot_result = dk.rotate_key(krot["api_key"], "uk-rot-v2")
        rot_old_t = dk.usage_kind_tally(krot["api_key"])
        rot_new_t = dk.usage_kind_tally(rot_result["api_key"])
        uk6 = (reads_after == reads_before
               and rev_t["by_kind"] == {"backtest": 2,
                                        "visualize": 1}
               and rev_hist["by_kind"] == {}
               and rot_old_t["by_kind"] == {"backtest": 2}
               and rot_new_t["by_kind"] == {}
               and rot_new_t["total"] == 0)
        record("AC-UK6", uk6,
               "kind-tally reads leave api_calls %d==%d; revoked"
               " key face open by_kind=%s (explicit hist window"
               " %s open empty=%s); rotated-out key face open"
               " by_kind=%s, successor tally=%s (own rows only,"
               " zero ancestor inheritance)"
               % (reads_after, reads_before, rev_t["by_kind"],
                  HIST_WIN, rev_hist["by_kind"],
                  rot_old_t["by_kind"], rot_new_t["by_kind"]))

        # -- AC-UK7 hygiene + delivery carriers ------------------------
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
        kind_face = re.search(
            r"def usage_kind_tally\(self, api_key, window=None\)",
            source) is not None
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "r",
                  encoding="utf-8") as handle:
            runner_src = handle.read()
        registered = re.search(
            r'\("ledger-apidev-usagekind",\s*'
            r'os\.path\.join\("ledger",\s*'
            r'"test_apidev_usagekind\.py"\),\s*7\)',
            runner_src) is not None
        dk.close()
        closed = []
        for handle_conn in (dk._conn, dk._lconn, dk._rconn):
            try:
                handle_conn.execute("SELECT 1")
                closed.append(False)
            except sqlite3.ProgrammingError:
                closed.append(True)
        uk7 = (cfg_bytes_end == cfg_bytes
               and is_ascii and not has_update and not has_rng
               and len(imports_net) == 0 and kind_face
               and registered
               and len(RESULTS) == 6
               and all(ok for _, ok in RESULTS)
               and closed == [True, True, True])
        record("AC-UK7", uk7,
               "hygiene: config.json byte-stable=%s, source"
               " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
               " net-imports=%d, kind face exported=%s,"
               " reconcile_all SUITES row registered=%s, close()"
               " shuts all three connections=%s; suite self-"
               "carrier: %d prior criteria all green=%s"
               % (cfg_bytes_end == cfg_bytes, is_ascii,
                  not has_update, not has_rng, len(imports_net),
                  kind_face, registered, closed == [True, True, True],
                  len(RESULTS), all(ok for _, ok in RESULTS)))
    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-usagekind: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
