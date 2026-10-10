"""Acceptance suite for the apidev reject-tally read face
(BigDomain R1728; canon = tech-queue "apidev reject-reason
classified count read face" row, the R1712 rate-ring successor).
Asserts the pre-registered criteria AC-RJ1..AC-RJ7 from the R1728
tech-queue claim note (criteria were registered before this code
ran; honesty law). Each criterion prints PASS/FAIL with evidence;
the process exits non-zero on any FAIL.

Covered semantics: key-attributed call-chain rejects land one
immutable diagnostic event each in a separate sqlite file
(api_rejects.db, single writer, zero ledger-schema touch); the
revoked/kind/rate/quota/duplicate gates plus the billing ring's
own business rejects (metered codes) are recorded, while
unattributable rejects (bad args, unknown key) and issuance /
purchase rejects stay unrecorded; recording is best-effort (a
diagnostic write failure never masks the primary reject); the
tally read faces (reject_tally, key_view, dev_board) aggregate
the rows at read time with GROUP BY COUNT per reason over the
current UTC month window; rotation attributes rejects to the
exact key (ancestor rejects are not inherited by the successor,
the old key keeps its readable tally).

Gate-order note: the dup pre-check sits after the quota gate in
the call chain, so the duplicate-reject case runs on its own key
with spare quota (a key at its quota cap would surface E_AD_QUOTA
first).

Deterministic clock: module-level _now_utc/_minute_utc/
_window_utc are monkeypatched onto a frozen clock holder (R1678
frozen-clock precedent), restored in finally. The metered face
is the real product injected by reference (no copy); this suite
reaches the billing ring only through the apidev public API.
This source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_reject.py
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
import apidev as D                      # noqa: E402 (R1700..R1712)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 10, 5, 0, 0)


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


def _tables(conn):
    return set(r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall())


def _reject_count(rj_conn):
    return rj_conn.execute(
        "SELECT COUNT(*) FROM reject_events").fetchone()[0]


def _reject_reasons(rj_conn, key_id):
    rows = rj_conn.execute(
        "SELECT reason, COUNT(*) FROM reject_events"
        " WHERE key_id = ? GROUP BY reason ORDER BY reason",
        (key_id,)).fetchall()
    return {r[0]: int(r[1]) for r in rows}


def _key_id(conn, key_name):
    return conn.execute(
        "SELECT key_id FROM api_dev_keys"
        " WHERE dev_account = ? AND key_name = ?",
        ("usr:ada", key_name)).fetchone()[0]


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
    tmp = tempfile.mkdtemp(prefix="apidev-reject-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "MINT-RJ-A", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada-rj", "suite funding ada")
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

        # -- AC-RJ1 event source + wiring law -----------------------
        rejects_path = dk._rj_path
        ledger_tables = _tables(conn)
        rejects_tables = _tables(rj_conn)
        dk.issue_key("usr:ada", "rj1-dup", 5, ["backtest"], False)
        n_before = _reject_count(rj_conn)
        ok_dup_issue, code_dup_issue = expect_ad_error(
            lambda: dk.issue_key("usr:ada", "rj1-dup", 5,
                                 ["backtest"], False),
            D.E_AD_DUP_KEY)
        n_after_dup = _reject_count(rj_conn)
        scratch = dk.issue_key("usr:ada", "rj1-scratch", 5,
                               ["backtest"], False)
        dk.revoke_key(scratch["api_key"])
        n_before_rev = _reject_count(rj_conn)
        ok_buy_rev, code_buy_rev = expect_ad_error(
            lambda: dk.buy_credits(scratch["api_key"], 5, 1,
                                   "PACK-RJ-SX"),
            D.E_AD_REVOKED)
        n_after_buy = _reject_count(rj_conn)
        ok_call_rev, code_call_rev = expect_ad_error(
            lambda: dk.call(scratch["api_key"], "backtest",
                            "RJ-SX-1", "e"),
            D.E_AD_REVOKED)
        n_after_call = _reject_count(rj_conn)
        cap_key = dk.issue_key("usr:ada", "rj1-cap", 1,
                               ["backtest"], False)
        dk.buy_credits(cap_key["api_key"], 5, 1, "PACK-RJ-C0")
        dk.call(cap_key["api_key"], "backtest", "RJ-C-1", "e")
        orig_exec = dk._rconn

        class _BoomConn(object):
            def execute(self, *args, **kwargs):
                raise sqlite3.OperationalError(
                    "mock diagnostic fault")

        dk._rconn = _BoomConn()
        try:
            ok_swallow, code_swallow = expect_ad_error(
                lambda: dk.call(cap_key["api_key"], "backtest",
                                "RJ-C-2", "e"),
                D.E_AD_QUOTA)
        finally:
            dk._rconn = orig_exec
        n_after_swallow = _reject_count(rj_conn)
        ok_health, _ = expect_ad_error(
            lambda: dk.call(cap_key["api_key"], "backtest",
                            "RJ-C-2", "e"),
            D.E_AD_QUOTA)
        n_after_health = _reject_count(rj_conn)
        rj1 = (os.path.basename(rejects_path) == "api_rejects.db"
               and os.path.dirname(rejects_path)
               == os.path.dirname(db_path)
               and "reject_events" not in ledger_tables
               and "api_dev_keys" in ledger_tables
               and "api_calls" in ledger_tables
               and "reject_events" in rejects_tables
               and ok_dup_issue and code_dup_issue == D.E_AD_DUP_KEY
               and n_after_dup == n_before
               and ok_buy_rev and code_buy_rev == D.E_AD_REVOKED
               and n_after_buy == n_before_rev
               and ok_call_rev and code_call_rev == D.E_AD_REVOKED
               and n_after_call == n_before_rev + 1
               and ok_swallow and code_swallow == D.E_AD_QUOTA
               and n_after_swallow == n_after_call
               and ok_health and n_after_health
               == n_after_swallow + 1)
        record("AC-RJ1", rj1,
               "separate store %s next to ledger db; ledger tables:"
               " reject_events absent=%s, api pair present=%s/%s;"
               " rejects store has reject_events=%s; re-issue %s"
               " left rows %d==%d; buy on revoked %s left %d==%d;"
               " call on revoked %s recorded +%d; swallowed"
               " diagnostic fault still raised %s at %d rows;"
               " healthy re-run recorded +%d"
               % (os.path.basename(rejects_path),
                  "reject_events" not in ledger_tables,
                  "api_dev_keys" in ledger_tables,
                  "api_calls" in ledger_tables,
                  "reject_events" in rejects_tables,
                  code_dup_issue, n_after_dup, n_before,
                  code_buy_rev, n_after_buy, n_before_rev,
                  code_call_rev, n_after_call - n_before_rev,
                  code_swallow, n_after_swallow,
                  n_after_health - n_after_swallow))

        # -- AC-RJ2 per-reject row semantics -------------------------
        q1 = dk.issue_key("usr:ada", "q1", 2, ["backtest"], False)
        dk.buy_credits(q1["api_key"], 10, 1, "PACK-RJ-Q0")
        dk.call(q1["api_key"], "backtest", "RJ-Q-1", "e1")
        dk.call(q1["api_key"], "backtest", "RJ-Q-2", "e2")
        calls_before = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        ok_q, code_q = expect_ad_error(
            lambda: dk.call(q1["api_key"], "backtest", "RJ-Q-3",
                            "e3"),
            D.E_AD_QUOTA)
        calls_at_reject = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        ok_q2, _ = expect_ad_error(
            lambda: dk.call(q1["api_key"], "backtest", "RJ-Q-3",
                            "e3"),
            D.E_AD_QUOTA)
        dupk = dk.issue_key("usr:ada", "dupk", 5, ["backtest"],
                            False)
        dk.buy_credits(dupk["api_key"], 10, 1, "PACK-RJ-D0")
        dk.call(dupk["api_key"], "backtest", "RJ-D-1", "e")
        ok_dup, code_dup = expect_ad_error(
            lambda: dk.call(dupk["api_key"], "backtest", "RJ-D-1",
                            "e"),
            D.E_AD_DUP)
        z = dk.issue_key("usr:ada", "z-key", 5, ["backtest"], False)
        calls_before_z = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        ok_mt, code_mt = expect_ad_error(
            lambda: dk.call(z["api_key"], "backtest", "RJ-Z-1",
                            "e"),
            M.E_MT_NO_CREDITS)
        calls_after_z = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        q1_id = _key_id(conn, "q1")
        dupk_id = _key_id(conn, "dupk")
        z_id = _key_id(conn, "z-key")
        rows_q1 = rj_conn.execute(
            "SELECT reason, detail, window, minute, called_utc"
            " FROM reject_events WHERE key_id = ?"
            " ORDER BY reject_id", (q1_id,)).fetchall()
        row_dupk = rj_conn.execute(
            "SELECT reason, detail FROM reject_events"
            " WHERE key_id = ?", (dupk_id,)).fetchall()
        row_z = rj_conn.execute(
            "SELECT reason, detail FROM reject_events"
            " WHERE key_id = ?", (z_id,)).fetchall()
        first = rows_q1[0]
        rj2 = (ok_q and code_q == D.E_AD_QUOTA
               and calls_at_reject == calls_before
               and ok_q2 and ok_dup and code_dup == D.E_AD_DUP
               and ok_mt and code_mt == M.E_MT_NO_CREDITS
               and calls_after_z == calls_before_z
               and len(rows_q1) == 2
               and first[0] == D.E_AD_QUOTA
               and first[1] == "2026-10"
               and first[2] == "2026-10"
               and first[3] == "2026-10-10T05:00"
               and first[4] == "2026-10-10T05:00:00Z"
               and rows_q1[1][0] == D.E_AD_QUOTA
               and row_dupk[0][0] == D.E_AD_DUP
               and row_dupk[0][1] == "RJ-D-1"
               and row_z[0][0] == M.E_MT_NO_CREDITS)
        record("AC-RJ2", rj2,
               "quota reject at cap: api_calls %d==%d (zero-row"
               " law), q1 rows=%s (detail=%s window=%s minute=%s"
               " utc=%s, double reject = 2 rows), dup gate row"
               " (%s, detail carries call_ref %s), billing ring"
               " reject recorded as %s with api_calls %d==%d"
               % (calls_at_reject, calls_before,
                  [(r[0], r[1]) for r in rows_q1],
                  first[1], first[2], first[3], first[4],
                  row_dupk[0][0], row_dupk[0][1], row_z[0][0],
                  calls_after_z, calls_before_z))

        # -- AC-RJ3 reject_tally read face --------------------------
        fresh = dk.issue_key("usr:ada", "fresh", 5, ["backtest"],
                             False)
        dk.buy_credits(fresh["api_key"], 10, 1, "PACK-RJ-F0")
        t_q1 = dk.reject_tally(q1["api_key"])
        manual_q1 = _reject_reasons(rj_conn, q1_id)
        t_fresh = dk.reject_tally(fresh["api_key"])
        ok_unknown, code_unknown = expect_ad_error(
            lambda: dk.reject_tally("sk-nonexistent"),
            D.E_AD_UNKNOWN_KEY)
        clock.advance(23 * 86400)
        t_next = dk.reject_tally(q1["api_key"])
        all_time = rj_conn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE key_id = ?", (q1_id,)).fetchone()[0]
        clock.dt = BASE_DT
        rj3 = (t_q1["window"] == "2026-10"
               and t_q1["by_reason"] == {D.E_AD_QUOTA: 2}
               and t_q1["total"] == 2
               and t_q1["by_reason"] == manual_q1
               and t_q1["key_name"] == "q1"
               and t_fresh["by_reason"] == {} and t_fresh["total"] == 0
               and ok_unknown and code_unknown == D.E_AD_UNKNOWN_KEY
               and t_next["window"] == "2026-11"
               and t_next["by_reason"] == {}
               and t_next["total"] == 0
               and all_time == 2)
        record("AC-RJ3", rj3,
               "tally window=%s by_reason=%s total=%d (manual SQL"
               " GROUP BY cross-check %s), fresh key %s/%d,"
               " unknown key -> %s, month roll -> window %s"
               " by_reason=%s (all-time rows still %d)"
               % (t_q1["window"], t_q1["by_reason"], t_q1["total"],
                  "equal" if t_q1["by_reason"] == manual_q1
                  else "DRIFT",
                  t_fresh["by_reason"], t_fresh["total"],
                  code_unknown, t_next["window"], t_next["by_reason"],
                  all_time))

        # -- AC-RJ4 embedded diagnostic profiles ---------------------
        v_q1 = dk.key_view(q1["api_key"])
        prior_keys = {"api_key", "dev_account", "key_name",
                      "metered_client", "window_cap", "enabled_kinds",
                      "ai_label", "minute_cap", "status",
                      "rotated_from_key_id", "window", "quota_used",
                      "quota_remaining", "minute_window",
                      "minute_used", "disclaimer"}
        board = dk.dev_board("usr:ada")
        rows_have_tally = all("reject_tally" in k
                              for k in board["keys"])
        board_q1 = [k for k in board["keys"]
                    if k["key_name"] == "q1"][0]
        expected_total = {D.E_AD_QUOTA: 3, D.E_AD_DUP: 1,
                          D.E_AD_REVOKED: 1, M.E_MT_NO_CREDITS: 1}
        v_dead = dk.key_view(scratch["api_key"])
        rj4 = (prior_keys.issubset(set(v_q1.keys()))
               and v_q1["reject_tally"] == {D.E_AD_QUOTA: 2}
               and rows_have_tally
               and board_q1["reject_tally"] == {D.E_AD_QUOTA: 2}
               and board["reject_tally_total"] == expected_total
               and v_dead["status"] == "revoked"
               and v_dead["reject_tally"] == {D.E_AD_REVOKED: 1})
        record("AC-RJ4", rj4,
               "key_view reject_tally=%s additive (prior key set"
               " preserved=%s), dev_board rows all carry"
               " reject_tally (q1=%s), board merged total=%s, dead"
               " key readable status=%s tally=%s"
               % (v_q1["reject_tally"],
                  prior_keys.issubset(set(v_q1.keys())),
                  board_q1["reject_tally"],
                  board["reject_tally_total"], v_dead["status"],
                  v_dead["reject_tally"]))

        # -- AC-RJ5 rotation attribution ------------------------------
        r1 = dk.issue_key("usr:ada", "rot-src", 1, ["backtest"],
                          False)
        dk.buy_credits(r1["api_key"], 5, 1, "PACK-RJ-R0")
        dk.call(r1["api_key"], "backtest", "RJ-R-1", "e")
        expect_ad_error(
            lambda: dk.call(r1["api_key"], "backtest", "RJ-R-2",
                            "e"),
            D.E_AD_QUOTA)
        rot = dk.rotate_key(r1["api_key"], "rot-src-v2")
        v_old_before = dk.key_view(r1["api_key"])
        v_new_before = dk.key_view(rot["api_key"])
        dk.buy_credits(rot["api_key"], 5, 1, "PACK-RJ-R2")
        ok_kind, code_kind = expect_ad_error(
            lambda: dk.call(rot["api_key"], "visualize", "RJ-R2-1",
                            "e"),
            D.E_AD_KIND)
        v_old_after = dk.key_view(r1["api_key"])
        v_new_after = dk.key_view(rot["api_key"])
        rj5 = (v_old_before["status"] == "rotated_out"
               and v_old_before["reject_tally"] == {D.E_AD_QUOTA: 1}
               and v_new_before["reject_tally"] == {}
               and ok_kind and code_kind == D.E_AD_KIND
               and v_new_after["reject_tally"] == {D.E_AD_KIND: 1}
               and v_old_after["reject_tally"] == {D.E_AD_QUOTA: 1})
        record("AC-RJ5", rj5,
               "pre-rotation quota reject stays on the old key"
               " (status=%s tally=%s), successor starts empty %s"
               " (ancestor not inherited), successor own kind"
               " reject %s accumulates on the successor"
               " (tally=%s), old key unchanged (%s)"
               % (v_old_before["status"],
                  v_old_before["reject_tally"],
                  v_new_before["reject_tally"],
                  code_kind, v_new_after["reject_tally"],
                  v_old_after["reject_tally"]))

        # -- AC-RJ6 hygiene face ---------------------------------------
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
        tally_face = "def reject_tally" in source
        dk.close()
        closed = []
        for handle_conn in (dk._conn, dk._lconn, dk._rconn):
            try:
                handle_conn.execute("SELECT 1")
                closed.append(False)
            except sqlite3.ProgrammingError:
                closed.append(True)
        rj6 = (cfg_bytes_end == cfg_bytes
               and is_ascii and not has_update and not has_rng
               and len(imports_net) == 0 and tally_face
               and closed == [True, True, True])
        record("AC-RJ6", rj6,
               "hygiene: config.json byte-stable=%s, source"
               " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
               " net-imports=%d, reject_tally face exported=%s,"
               " close() shuts all three connections=%s"
               % (cfg_bytes_end == cfg_bytes, is_ascii, not has_update,
                  not has_rng, len(imports_net), tally_face,
                  closed == [True, True, True]))

        # -- AC-RJ7 delivery carrier (registration self-check) --------
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "r",
                  encoding="utf-8") as handle:
            runner_src = handle.read()
        registered = re.search(
            r'\("ledger-apidev-reject",\s*'
            r'os\.path\.join\("ledger",\s*'
            r'"test_apidev_reject\.py"\),\s*7\)',
            runner_src) is not None
        rj7 = (registered and len(RESULTS) == 6
               and all(ok for _, ok in RESULTS))
        record("AC-RJ7", rj7,
               "reconcile_all SUITES row registered=%s"
               " (ledger-apidev-reject / test_apidev_reject.py /"
               " 7 criteria), suite self-carrier: %d prior"
               " criteria all green=%s"
               % (registered, len(RESULTS),
                  all(ok for _, ok in RESULTS)))
    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-reject: %d/%d criteria pass"
          % (passed, total), flush=True)
    metered.close()
    rj_conn.close()
    conn.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
