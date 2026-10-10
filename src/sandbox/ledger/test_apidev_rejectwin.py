"""Acceptance suite for the apidev reject-tally window-
parameterized read face (BigDomain R1730; canon = tech-queue
"apidev reject_tally window-parameterized read face" row, the
R1728 reject-tally successor). Asserts the pre-registered
criteria AC-RJW1..AC-RJW7 from the R1730 tech-queue claim note
(criteria were registered before this suite ran; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Covered semantics: reject_tally(api_key, window=None) keeps the
default (None = current UTC month) byte-stable with the R1728
behavior -- the six-key envelope, the frozen-clock current
window value and the GROUP BY aggregation all stay identical;
an explicit "YYYY-MM" string reads any month window at read
time over the immutable reject rows (strict format gate, only
None is the default sentinel; every other shape fails closed
with E_AD_BAD_ARGS after the key gate, the call-chain
key-gate-first law); historical and future windows are honest
reads (injected fixture rows prove the window separation in
both directions); the embedded faces (key_view, dev_board)
keep the current-month default untouched; dead keys (revoked,
rotated_out) stay readable on explicit windows with the same
semantics; the aggregation is cross-checked against manual SQL
and the frozen clock proves the month roll (new rejects land
in the new month, the old month stays readable forever).

Fixture provenance note (pre-registered in AC-RJW3): the
historical-month rows are direct test-fixture INSERTs into the
reject_events store -- the product record path always stamps
its own record-time window (AC-RJ2), so a historical row can
only exist via this fixture injection, which is exactly what
the window-parameterized read face makes readable.

Deterministic clock: module-level _now_utc/_minute_utc/
_window_utc are monkeypatched onto a frozen clock holder (R1678
frozen-clock precedent), restored in finally. This suite
reaches the product only through the apidev public API (the
fixture INSERTs are the stated exception). Pure ASCII per the
encoding discipline.

Usage: python test_apidev_rejectwin.py
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
import apidev as D                      # noqa: E402 (R1700..R1730)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 10, 5, 0, 0)

HIST_WINDOW = "2026-09"
FUTURE_WINDOW = "2026-11"


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


def _key_id(conn, key_name):
    return conn.execute(
        "SELECT key_id FROM api_dev_keys"
        " WHERE dev_account = ? AND key_name = ?",
        ("usr:ada", key_name)).fetchone()[0]


def _manual_by_reason(rj_conn, key_id, window):
    rows = rj_conn.execute(
        "SELECT reason, COUNT(*) FROM reject_events"
        " WHERE key_id = ? AND window = ?"
        " GROUP BY reason ORDER BY reason",
        (key_id, window)).fetchall()
    return {r[0]: int(r[1]) for r in rows}


def _manual_board_total(rj_conn, window):
    rows = rj_conn.execute(
        "SELECT reason, COUNT(*) FROM reject_events"
        " WHERE window = ? GROUP BY reason ORDER BY reason",
        (window,)).fetchall()
    return {r[0]: int(r[1]) for r in rows}


def _reject_count(rj_conn):
    return rj_conn.execute(
        "SELECT COUNT(*) FROM reject_events").fetchone()[0]


def _inject_hist(rj_conn, key_id, reason, detail,
                 window=HIST_WINDOW):
    """Direct test-fixture INSERT of one historical-window reject
    event (AC-RJW3 provenance note: the product path always
    self-stamps the record-time window, so historical rows exist
    only through this fixture injection)."""
    rj_conn.execute(
        "INSERT INTO reject_events (key_id, reason, detail,"
        " window, minute, called_utc) VALUES (?,?,?,?,?,?)",
        (key_id, reason, detail, window,
         window + "-05T04:00", window + "-05T04:00:00Z"))
    rj_conn.commit()


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


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-rejectwin-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-RJW-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada-rjw", "suite funding ada")
    conn = sqlite3.connect(db_path)
    rj_conn = sqlite3.connect(dk._rj_path)
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # key w1: two live calls at window_cap=2, then two quota
        # rejects -- all landing in the frozen current month
        w1 = dk.issue_key("usr:ada", "w1", 2, ["backtest"], False)
        dk.buy_credits(w1["api_key"], 10, 1, "PACK-RJW-W0")
        dk.call(w1["api_key"], "backtest", "RJW-A-1", "e")
        dk.call(w1["api_key"], "backtest", "RJW-A-2", "e")
        ok_q1, code_q1 = expect_ad_error(
            lambda: dk.call(w1["api_key"], "backtest", "RJW-A-3",
                            "e"),
            D.E_AD_QUOTA)
        ok_q2, code_q2 = expect_ad_error(
            lambda: dk.call(w1["api_key"], "backtest", "RJW-A-4",
                            "e"),
            D.E_AD_QUOTA)
        w1_id = _key_id(conn, "w1")

        # -- AC-RJW1 contract + default byte-stability ---------------
        t_def = dk.reject_tally(w1["api_key"])
        envelope = set(t_def.keys())
        expected_envelope = {"api_key", "key_name", "window",
                             "by_reason", "total", "disclaimer"}
        manual_cur = _manual_by_reason(rj_conn, w1_id, "2026-10")
        ok_gate, code_gate = expect_ad_error(
            lambda: dk.reject_tally("sk-nonexistent",
                                    window="2026-13"),
            D.E_AD_UNKNOWN_KEY)
        rjw1 = (ok_q1 and code_q1 == D.E_AD_QUOTA
                and ok_q2 and code_q2 == D.E_AD_QUOTA
                and envelope == expected_envelope
                and t_def["window"] == "2026-10"
                and t_def["key_name"] == "w1"
                and t_def["by_reason"] == {D.E_AD_QUOTA: 2}
                and t_def["total"] == 2
                and t_def["by_reason"] == manual_cur
                and ok_gate and code_gate == D.E_AD_UNKNOWN_KEY)
        record("AC-RJW1", rjw1,
               "default read window=%s by_reason=%s total=%d"
               " (manual SQL %s), envelope exactly %s%s,"
               " key gate before window gate: unknown key + bad"
               " window -> %s"
               % (t_def["window"], t_def["by_reason"],
                  t_def["total"],
                  "equal" if t_def["by_reason"] == manual_cur
                  else "DRIFT",
                  sorted(envelope),
                  "" if envelope == expected_envelope
                  else " DRIFT",
                  code_gate))

        # -- AC-RJW2 bad window shapes fail closed --------------------
        # R1748 anchor hardening: the trailing-newline form is the
        # gap form (pre-fix '$' accepted it); space/CR tails are
        # regression guards (already rejected by '$').
        bad_shapes = ["2026-13", "2026-00", "2026-1", "2026/10",
                      "2026", "202610", "abcd", "",
                      2026, True, 2.5,
                      "2026-10\n", "2026-10 ", "2026-10\r"]
        n_before = _reject_count(rj_conn)
        codes = []
        for shape in bad_shapes:
            ok_bad, code_bad = expect_ad_error(
                lambda s=shape: dk.reject_tally(
                    w1["api_key"], window=s),
                D.E_AD_BAD_ARGS)
            codes.append(code_bad if ok_bad else
                         ("NO-RAISE:%s" % code_bad))
        n_after = _reject_count(rj_conn)
        all_bad = all(c == D.E_AD_BAD_ARGS for c in codes)
        rjw2 = (all_bad and n_after == n_before)
        record("AC-RJW2", rjw2,
               "14 bad shapes (%s) all -> E_AD_BAD_ARGS on an"
               " in-register key; empty string is NOT the default"
               " sentinel (only None is); reject rows %d==%d"
               " zero side effects"
               % (codes, n_after, n_before))

        # -- AC-RJW3 historical + future window reads ----------------
        _inject_hist(rj_conn, w1_id, D.E_AD_RATE, "hist-rate-1")
        _inject_hist(rj_conn, w1_id, D.E_AD_RATE, "hist-rate-2")
        _inject_hist(rj_conn, w1_id, D.E_AD_KIND, "hist-kind-1")
        t_hist = dk.reject_tally(w1["api_key"],
                                 window=HIST_WINDOW)
        t_future = dk.reject_tally(w1["api_key"],
                                   window=FUTURE_WINDOW)
        t_def2 = dk.reject_tally(w1["api_key"])
        rjw3 = (t_hist["window"] == HIST_WINDOW
                and t_hist["by_reason"] == {D.E_AD_RATE: 2,
                                            D.E_AD_KIND: 1}
                and t_hist["total"] == 3
                and t_future["window"] == FUTURE_WINDOW
                and t_future["by_reason"] == {}
                and t_future["total"] == 0
                and t_def2["by_reason"] == {D.E_AD_QUOTA: 2}
                and D.E_AD_QUOTA not in t_hist["by_reason"]
                and D.E_AD_RATE not in t_def2["by_reason"])
        record("AC-RJW3", rjw3,
               "fixture-injected %s rows read back by_reason=%s"
               " total=%d; future %s honest empty read %s/%d;"
               " window separation: default stays %s (no"
               " historical penetration), historical read has no"
               " current-month keys (%s absent)"
               % (HIST_WINDOW, t_hist["by_reason"],
                  t_hist["total"], FUTURE_WINDOW,
                  t_future["by_reason"], t_future["total"],
                  t_def2["by_reason"],
                  D.E_AD_QUOTA))

        # -- AC-RJW4 embedded faces keep the current-month default ---
        v_w1 = dk.key_view(w1["api_key"])
        board = dk.dev_board("usr:ada")
        board_w1 = [k for k in board["keys"]
                    if k["key_name"] == "w1"][0]
        manual_board = _manual_board_total(rj_conn, "2026-10")
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
        rjw4 = (v_w1["reject_tally"] == {D.E_AD_QUOTA: 2}
                and board_w1["reject_tally"] == {D.E_AD_QUOTA: 2}
                and board["reject_tally_total"] == manual_board
                and kv_sig_ok and db_sig_ok)
        record("AC-RJW4", rjw4,
               "key_view reject_tally=%s, dev_board row=%s, board"
               " merged total=%s (manual all-key SQL equal=%s),"
               " zero historical penetration; source signatures"
               " window-free: key_view=%s dev_board=%s"
               % (v_w1["reject_tally"], board_w1["reject_tally"],
                  board["reject_tally_total"],
                  board["reject_tally_total"] == manual_board,
                  kv_sig_ok, db_sig_ok))

        # -- AC-RJW5 dead keys read on explicit windows --------------
        rev = dk.issue_key("usr:ada", "w5-rev", 5, ["backtest"],
                           False)
        dk.revoke_key(rev["api_key"])
        ok_rev_call, code_rev_call = expect_ad_error(
            lambda: dk.call(rev["api_key"], "backtest",
                            "RJW-REV-1", "e"),
            D.E_AD_REVOKED)
        rev_id = _key_id(conn, "w5-rev")
        _inject_hist(rj_conn, rev_id, D.E_AD_RATE, "hist-rev-1")
        t_rev_hist = dk.reject_tally(rev["api_key"],
                                     window=HIST_WINDOW)
        t_rev_def = dk.reject_tally(rev["api_key"])
        rot = dk.issue_key("usr:ada", "w5-rot", 1, ["backtest"],
                           False)
        dk.buy_credits(rot["api_key"], 5, 1, "PACK-RJW-RT")
        dk.call(rot["api_key"], "backtest", "RJW-RT-1", "e")
        ok_rot_q, code_rot_q = expect_ad_error(
            lambda: dk.call(rot["api_key"], "backtest",
                            "RJW-RT-2", "e"),
            D.E_AD_QUOTA)
        rot_id = _key_id(conn, "w5-rot")
        rot_new = dk.rotate_key(rot["api_key"], "w5-rot-v2")
        _inject_hist(rj_conn, rot_id, D.E_AD_KIND, "hist-rot-1")
        t_rot_hist = dk.reject_tally(rot["api_key"],
                                     window=HIST_WINDOW)
        t_rot_def = dk.reject_tally(rot["api_key"])
        t_new_fresh = dk.reject_tally(rot_new["api_key"],
                                      window=HIST_WINDOW)
        rjw5 = (ok_rev_call and code_rev_call == D.E_AD_REVOKED
                and t_rev_hist["by_reason"] == {D.E_AD_RATE: 1}
                and t_rev_def["by_reason"] == {D.E_AD_REVOKED: 1}
                and ok_rot_q and code_rot_q == D.E_AD_QUOTA
                and t_rot_hist["by_reason"] == {D.E_AD_KIND: 1}
                and t_rot_def["by_reason"] == {D.E_AD_QUOTA: 1}
                and t_new_fresh["by_reason"] == {}
                and t_new_fresh["total"] == 0)
        record("AC-RJW5", rjw5,
               "revoked dead key: current=%s historical=%s (read"
               " open); rotated_out dead key: current=%s"
               " historical=%s (read open); successor fresh"
               " historical read=%s/%d"
               % (t_rev_def["by_reason"],
                  t_rev_hist["by_reason"],
                  t_rot_def["by_reason"],
                  t_rot_hist["by_reason"],
                  t_new_fresh["by_reason"],
                  t_new_fresh["total"]))

        # -- AC-RJW6 aggregation cross-check + month roll ------------
        cross_hist = dk.reject_tally(w1["api_key"],
                                     window=HIST_WINDOW)
        manual_hist = _manual_by_reason(rj_conn, w1_id,
                                       HIST_WINDOW)
        clock.advance(23 * 86400)
        dk.call(w1["api_key"], "backtest", "RJW-N-1", "e")
        dk.call(w1["api_key"], "backtest", "RJW-N-2", "e")
        ok_nq, code_nq = expect_ad_error(
            lambda: dk.call(w1["api_key"], "backtest", "RJW-N-3",
                            "e"),
            D.E_AD_QUOTA)
        t_rolled = dk.reject_tally(w1["api_key"])
        manual_nov = _manual_by_reason(rj_conn, w1_id, "2026-11")
        t_old_oct = dk.reject_tally(w1["api_key"],
                                    window="2026-10")
        t_old_sep = dk.reject_tally(w1["api_key"],
                                    window=HIST_WINDOW)
        all_time = rj_conn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE key_id = ?", (w1_id,)).fetchone()[0]
        clock.dt = BASE_DT
        rjw6 = (cross_hist["by_reason"] == manual_hist
                and ok_nq and code_nq == D.E_AD_QUOTA
                and t_rolled["window"] == "2026-11"
                and t_rolled["by_reason"] == {D.E_AD_QUOTA: 1}
                and t_rolled["by_reason"] == manual_nov
                and t_old_oct["by_reason"] == {D.E_AD_QUOTA: 2}
                and t_old_sep["by_reason"] == {D.E_AD_RATE: 2,
                                               D.E_AD_KIND: 1}
                and all_time == 6)
        record("AC-RJW6", rjw6,
               "explicit %s read == manual SQL %s; clock +23d"
               " month roll: default follows to %s by_reason=%s"
               " (manual SQL equal), old %s explicit read intact"
               " %s, old %s explicit read intact %s, all-time"
               " rows %d (2+3+1) never lost"
               % (HIST_WINDOW,
                  "equal" if cross_hist["by_reason"] == manual_hist
                  else "DRIFT",
                  t_rolled["window"], t_rolled["by_reason"],
                  "2026-10", t_old_oct["by_reason"],
                  HIST_WINDOW, t_old_sep["by_reason"], all_time))

        # -- AC-RJW7 hygiene + registration self-check ---------------
        with open(os.path.join(BASE, "config.json"), "rb") as h2:
            cfg_bytes_end = h2.read()
        code_only = re.sub(r'"""[\s\S]*?"""', '""', src)
        code_only = "\n".join(re.sub(r"#.*$", "", line)
                              for line in code_only.splitlines())
        has_update = re.search(r"\bUPDATE\b", code_only) is not None
        imports_net = [line for line in src.splitlines()
                       if re.match(r"\s*(?:import|from)\s", line)
                       and re.search(r"urllib|requests|socket|http",
                                     line)]
        is_ascii = all(ord(ch) < 128 for ch in src)
        has_rng = re.search(r"\brandom\b", src) is not None
        dk.close()
        closed = []
        for handle_conn in (dk._conn, dk._lconn, dk._rconn):
            try:
                handle_conn.execute("SELECT 1")
                closed.append(False)
            except sqlite3.ProgrammingError:
                closed.append(True)
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "r",
                  encoding="utf-8") as handle:
            runner_src = handle.read()
        registered = re.search(
            r'\("ledger-apidev-rejectwin",\s*'
            r'os\.path\.join\("ledger",\s*'
            r'"test_apidev_rejectwin\.py"\),\s*7\)',
            runner_src) is not None
        rjw7 = (cfg_bytes_end == cfg_bytes
                and is_ascii and not has_update and not has_rng
                and len(imports_net) == 0 and registered
                and closed == [True, True, True]
                and len(RESULTS) == 6
                and all(ok for _, ok in RESULTS))
        record("AC-RJW7", rjw7,
               "hygiene: config.json byte-stable=%s, source"
               " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
               " net-imports=%d, close() shuts all three=%s;"
               " reconcile_all SUITES row registered=%s"
               " (ledger-apidev-rejectwin / 7 criteria); %d prior"
               " criteria all green=%s"
               % (cfg_bytes_end == cfg_bytes, is_ascii,
                  not has_update, not has_rng, len(imports_net),
                  closed == [True, True, True], registered,
                  len(RESULTS),
                  all(ok for _, ok in RESULTS)))
    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-rejectwin: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    rj_conn.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
