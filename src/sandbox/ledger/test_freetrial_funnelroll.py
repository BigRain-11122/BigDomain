"""Acceptance suite for the free-trial conversion-funnel
board month-roll fidelity example (BigDomain R1874
tech-queue claim row; seed = the conversion_funnel_board
window parameter R1793, the month-roll family symmetric
gap - the funnel board was the window-parameter family
member without a roll pin). Asserts the pre-registered
criteria AC-CVR1..AC-CVR7 from the R1874 tech.md claim
line (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (the R1858 callroll dedicated-suite
precedent): the existing funnelwin suite world rides the
real clock, so roll reads there would be contaminated by
real-month rows - this suite builds a fresh isolated face
instance in its own temp world and freezes the freetrial
module clock (T._now_utc patched onto a deterministic
holder, restored with a probe; the R1678 frozen-clock
precedent).

World (all stamps ride the frozen clock, the live product
write path - zero fixture injection): BASE_DT 2026-10-15;
two registered plans roll-fp / roll-hq (registry-driven
dense board axis). October phase: three grants on roll-fp
(usr:fun-a converts the same month; usr:fun-b stays
active; usr:fun-c converts ONLY after the roll = the
cross-month conversion anchor) and zero activity on
roll-hq (honest zero row). After +23d crosses the month
boundary: usr:fun-d takes a fresh November grant + same
-month conversion on roll-hq, and usr:fun-c's November
conversion lands cross-month (grant 2026-10, conversion
2026-11). The end-of-window active_trials snapshot walks
with the window: the SAME fun-c row reads as still-active
inside the October window and already-converted inside
the November window (time-travel verdict); the windowed
conversion rate keeps the window-filtered ratio under the
zero-grant guard (November roll-fp converted=1 over
granted=0 shows the guard honestly). Zero product bytes:
the roll semantics already live in the face, this suite
only pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_funnelroll.py
"""

import datetime
import hashlib
import inspect
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700 registry)
import freetrial as T                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"

ROW_KEYS = {"plan_id", "plan_key", "title", "ai_label",
            "granted", "converted", "active_trials",
            "conversion_rate"}
DEF_ENV_KEYS = {"conversion_funnel_board", "disclaimer"}
WIN_ENV_KEYS = DEF_ENV_KEYS | {"window"}

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
BANNED_WRITES = ("INSERT INTO", "REPLACE INTO", "UPDATE ",
                 "DELETE FROM")


class _FrozenClock(object):
    """Deterministic UTC clock holder: the freetrial module
    _now_utc is patched onto this holder so grant/conversion
    stamps roll only when the suite moves the clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def main():
    tmp = tempfile.mkdtemp(prefix="freetrial-funnelroll-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "freetrial.py"), "rb") as handle:
        face_bytes = handle.read()
    face_sha = hashlib.sha256(face_bytes).hexdigest()
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)
    ftconn = sqlite3.connect(ft.db_path)

    def _count(table):
        return ftconn.execute(
            "SELECT COUNT(*) FROM " + table).fetchone()[0]

    def _row(env, plan_key):
        for r in env["conversion_funnel_board"]:
            if r["plan_key"] == plan_key:
                return r
        return None

    clock = _FrozenClock()
    real_now = T._now_utc
    try:
        T._now_utc = clock.now_utc

        # -- October world ---------------------------------------
        pa = ft.register_trial_plan("roll-fp", "Roll Funnel P",
                                    10, False)
        qb = ft.register_trial_plan("roll-hq", "Roll Funnel Q",
                                    5, False)
        for who, key in (("usr:fun-a", "fun-a-key"),
                         ("usr:fun-b", "fun-b-key"),
                         ("usr:fun-c", "fun-c-key")):
            dk.issue_key(who, key, 100, ["backtest"], False)
            ft.grant_trial(who, pa["plan_id"])
            clock.advance(60)
        ft.convert_upgrade("usr:fun-a", pa["plan_id"],
                           "tier-pro")

        # -- AC-CVR1 October anchor ------------------------------
        oct_g_sql = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants WHERE"
            " substr(granted_utc, 1, 7) = ?",
            (OLD_WIN,)).fetchone()[0]
        oct_c_sql = ftconn.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " substr(converted_utc, 1, 7) = ?",
            (OLD_WIN,)).fetchone()[0]
        wenv = ft.conversion_funnel_board(OLD_WIN)
        denv = ft.conversion_funnel_board()
        rows = wenv["conversion_funnel_board"]
        fp, hq = _row(wenv, "roll-fp"), _row(wenv, "roll-hq")
        ok1 = (oct_g_sql == 3 and oct_c_sql == 1
               and set(wenv.keys()) == WIN_ENV_KEYS
               and wenv["window"] == OLD_WIN
               and wenv["disclaimer"] == DISCLAIMER
               and len(rows) == 2
               and [r["plan_key"] for r in rows]
               == ["roll-fp", "roll-hq"]
               and set(fp.keys()) == ROW_KEYS
               and fp["granted"] == 3
               and fp["converted"] == 1
               and fp["active_trials"] == 2
               and fp["conversion_rate"] == 0.3333
               and fp["ai_label"] == 0
               and hq["granted"] == 0 and hq["converted"] == 0
               and hq["active_trials"] == 0
               and hq["conversion_rate"] == 0.0
               and set(denv.keys()) == DEF_ENV_KEYS
               and json.dumps(denv["conversion_funnel_board"])
               == json.dumps(rows))
        S_oct = json.dumps(wenv, sort_keys=True)
        record("AC-CVR1", ok1,
               "October anchor: frozen-clock record-time stamps"
               " (SQL %s grants=%d conversions=%d); explicit %s"
               " window read - roll-fp granted=3 converted=1"
               " active=2 (g_cum 3 - c_cum 1: end-of-window"
               " snapshot, usr:fun-c still active), rate=0.3333;"
               " roll-hq honest zero row (registry-driven dense"
               " axis, rate=0.0); default rows == window rows in"
               " the October-only era; pre-roll snapshot anchored"
               % (OLD_WIN, oct_g_sql, oct_c_sql, OLD_WIN))

        # -- month roll: +23d crosses the boundary ---------------
        clock.advance(23 * 86400)

        # -- November world --------------------------------------
        dk.issue_key("usr:fun-d", "fun-d-key", 100,
                     ["backtest"], False)
        ft.grant_trial("usr:fun-d", qb["plan_id"])
        ft.convert_upgrade("usr:fun-d", qb["plan_id"],
                           "tier-pro")
        ft.convert_upgrade("usr:fun-c", pa["plan_id"],
                           "tier-pro")

        # -- AC-CVR2 new-month rows land in the new window ------
        cross_ts = ftconn.execute(
            "SELECT converted_utc FROM trial_conversions WHERE"
            " dev_account = ?", ("usr:fun-c",)).fetchone()[0]
        nov_g_sql = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants WHERE"
            " substr(granted_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        nov_c_sql = ftconn.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " substr(converted_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        nenv = ft.conversion_funnel_board(NEW_WIN)
        ndenv = ft.conversion_funnel_board()
        nfp = _row(nenv, "roll-fp")
        nhq = _row(nenv, "roll-hq")
        dfp = _row(ndenv, "roll-fp")
        dhq = _row(ndenv, "roll-hq")
        ok2 = (cross_ts.startswith(NEW_WIN)
               and nov_g_sql == 1 and nov_c_sql == 2
               and nenv["window"] == NEW_WIN
               and nfp["granted"] == 0
               and nfp["converted"] == 1
               and nfp["active_trials"] == 1
               and nfp["conversion_rate"] == 0.0
               and nhq["granted"] == 1 and nhq["converted"] == 1
               and nhq["active_trials"] == 0
               and nhq["conversion_rate"] == 1.0
               and dfp["granted"] == 3 and dfp["converted"] == 2
               and dfp["active_trials"] == 1
               and dfp["conversion_rate"] == 0.6667
               and dhq["granted"] == 1 and dhq["converted"] == 1
               and dhq["active_trials"] == 0
               and dhq["conversion_rate"] == 1.0)
        record("AC-CVR2", ok2,
               "frozen clock +23d crossed the month boundary;"
               " usr:fun-c conversion stamps converted_utc=%s"
               " (grant %s = cross-month conversion anchor; SQL"
               " %s grants=%d conversions=%d). Explicit %s window:"
               " roll-fp granted=0 converted=1 rate=0.0 (the"
               " cross-month conversion counts in converted_w"
               " while its grant stays outside the denominator -"
               " zero-grant guard, AC-CFW5 carried forward),"
               " active=1; roll-hq granted=1 converted=1 active=0"
               " rate=1.0. Default all-window read carries the"
               " cross-month rows: roll-fp 3/2/1 rate=0.6667,"
               " roll-hq 1/1/0 rate=1.0"
               % (cross_ts, OLD_WIN, NEW_WIN, nov_g_sql,
                  nov_c_sql, NEW_WIN))

        # -- AC-CVR3 old-month window original-value preservation
        oct2 = ft.conversion_funnel_board(OLD_WIN)
        ok3 = (json.dumps(oct2, sort_keys=True) == S_oct
               and oct2["window"] == OLD_WIN)
        nov2 = ft.conversion_funnel_board(NEW_WIN)
        nfp2 = _row(nov2, "roll-fp")
        ok3 = (ok3
               and nfp2["granted"] == 0
               and nfp2["converted"] == 1)
        record("AC-CVR3", ok3,
               "post-roll explicit %s window read is"
               " byte-identical to the pre-roll snapshot (the"
               " November conversion never leaks back into the"
               " October window - record-time immutability); the"
               " %s window read carries zero October-only"
               " leakage (roll-fp granted=0, converted=1 = the"
               " cross-month conversion alone, usr:fun-a's October"
               " conversion stays out) - the two windows never"
               " leak into each other in either direction"
               % (OLD_WIN, NEW_WIN))

        # -- AC-CVR4 active snapshot walks with the window ------
        def _cum(plan_id, win):
            g = ftconn.execute(
                "SELECT COUNT(*) FROM trial_grants WHERE"
                " plan_id = ? AND substr(granted_utc, 1, 7)"
                " <= ?", (plan_id, win)).fetchone()[0]
            c = ftconn.execute(
                "SELECT COUNT(*) FROM trial_conversions WHERE"
                " plan_id = ? AND substr(converted_utc, 1, 7)"
                " <= ?", (plan_id, win)).fetchone()[0]
            return g, c

        ok4 = True
        for env, win in ((oct2, OLD_WIN), (nov2, NEW_WIN)):
            for row in env["conversion_funnel_board"]:
                g, c = _cum(row["plan_id"], win)
                ok4 = (ok4
                       and row["active_trials"] == g - c)
        walk = []
        for row in nov2["conversion_funnel_board"]:
            oct_row = _row(oct2, row["plan_key"])
            nov_g = ftconn.execute(
                "SELECT COUNT(*) FROM trial_grants WHERE"
                " plan_id = ? AND substr(granted_utc, 1, 7)"
                " = ?", (row["plan_id"], NEW_WIN)).fetchone()[0]
            nov_c = ftconn.execute(
                "SELECT COUNT(*) FROM trial_conversions WHERE"
                " plan_id = ? AND substr(converted_utc, 1, 7)"
                " = ?", (row["plan_id"], NEW_WIN)).fetchone()[0]
            ok4 = (ok4
                   and row["active_trials"]
                   == oct_row["active_trials"] + nov_g - nov_c)
            walk.append("%s %d+%d-%d=%d"
                        % (row["plan_key"],
                           oct_row["active_trials"], nov_g,
                           nov_c, row["active_trials"]))
        g_fp_10, c_fp_10 = _cum(pa["plan_id"], OLD_WIN)
        g_fp_11, c_fp_11 = _cum(pa["plan_id"], NEW_WIN)
        ok4 = (ok4 and g_fp_10 == 3 and c_fp_10 == 1
               and g_fp_11 == 3 and c_fp_11 == 2)
        record("AC-CVR4", ok4,
               "end-of-window snapshot semantics: every"
               " active_trials == cumulative SQL grants(<=W)"
               " minus conversions(<=W) per plan per window"
               " (mirror cross); the snapshot WALKS with the"
               " window - active_Nov == active_Oct +"
               " granted_Nov - converted_Nov [%s]; the SAME"
               " usr:fun-c row reads two states in two windows"
               " (c_cum roll-fp %s->%s: still-active inside the"
               " %s window, already-converted inside the %s"
               " window - time-travel verdict)"
               % ("; ".join(walk), c_fp_10, c_fp_11, OLD_WIN,
                  NEW_WIN))

        # -- AC-CVR5 rate window-path carried forward -----------
        checks = []
        ok5 = True
        for env, tag in ((oct2, "oct"), (nov2, "nov"),
                         (ndenv, "all")):
            for row in env["conversion_funnel_board"]:
                want = (round(row["converted"] / row["granted"], 4)
                        if row["granted"] > 0 else 0.0)
                ok5 = (ok5 and row["conversion_rate"] == want)
                checks.append("%s/%s=%s"
                              % (tag, row["plan_key"],
                                 row["conversion_rate"]))
        ok5 = (ok5
               and nfp2["conversion_rate"] == 0.0
               and nfp2["converted"] == 1
               and nfp2["granted"] == 0)
        record("AC-CVR5", ok5,
               "conversion rate stays the window-filtered ratio"
               " round(converted_w/granted_w, 4) under the"
               " zero-grant guard on every read [%s]; the"
               " November roll-fp row (converted_w=1 over"
               " granted_w=0) shows the guard honestly - the"
               " ratio is a windowed flow measure, never the"
               " all-window ratio, and the guard does not lie"
               % ", ".join(checks))

        # -- AC-CVR6 immutable rows never lost ------------------
        pre_counts = (_count("trial_plans"),
                      _count("trial_grants"),
                      _count("trial_conversions"),
                      _count("trial_calls"))
        g_total = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants").fetchone()[0]
        c_total = ftconn.execute(
            "SELECT COUNT(*) FROM trial_conversions"
        ).fetchone()[0]
        sum_g = sum(r["granted"] for r in
                    ndenv["conversion_funnel_board"])
        sum_c = sum(r["converted"] for r in
                    ndenv["conversion_funnel_board"])
        ok6 = (pre_counts == (2, 4, 3, 0)
               and g_total == 4 and c_total == 3
               and sum_g == g_total and sum_c == c_total)
        record("AC-CVR6", ok6,
               "immutable rows never lost: four-table counts"
               " %s (plans/grants/conversions/calls) constant;"
               " all-window board granted sum %d == SQL grants"
               " %d, converted sum %d == SQL conversions %d"
               % (pre_counts, sum_g, g_total, sum_c, c_total))

        # -- AC-CVR7 pure-read + determinism + hygiene -----------
        src = inspect.getsource(
            T.FreeTrialFace.conversion_funnel_board)
        ok7 = not any(b in src for b in BANNED_WRITES)
        dumps = []
        for args in ((), (OLD_WIN,), (NEW_WIN,)):
            env1 = ft.conversion_funnel_board(*args)
            env2 = ft.conversion_funnel_board(*args)
            dumps.append((json.dumps(env1, sort_keys=True),
                          json.dumps(env2, sort_keys=True),
                          json.dumps(env1), json.dumps(env2)))
        ok7 = (ok7
               and all(a == b and c == d
                       for (a, b, c, d) in dumps)
               and (_count("trial_plans"),
                    _count("trial_grants"),
                    _count("trial_conversions"),
                    _count("trial_calls")) == pre_counts)
        with open(os.path.join(BASE, "freetrial.py"),
                  "rb") as h3:
            ok7 = ok7 and (hashlib.sha256(
                h3.read()).hexdigest() == face_sha)
        with open(os.path.join(BASE, "config.json"),
                  "rb") as h4:
            ok7 = ok7 and (hashlib.sha256(
                h4.read()).hexdigest() == cfg_sha)
        with open(os.path.abspath(__file__), "rb") as h5:
            self_bytes = h5.read()
        ok7 = (ok7 and all(b < 128 for b in self_bytes)
               and all(b < 128 for b in face_bytes))
        imports = [ln.strip() for ln in
                   self_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok7 = (ok7
               and not any(lib in ln for ln in imports
                           for lib in NET_LIBS))
        reg_path = os.path.join(os.path.dirname(BASE),
                                "reconcile_all.py")
        with open(reg_path, "r", encoding="utf-8") as h6:
            reg_text = h6.read()
        ok7 = (ok7
               and "ledger-freetrial-funnelroll" in reg_text
               and "test_freetrial_funnelroll.py" in reg_text
               and len(RESULTS) + 1 == EXPECTED)
        # explicit clock restore + probe (R1865 restore-probe
        # precedent): the restored clock differs from the
        # frozen stamp; the finally clause re-restores safely.
        T._now_utc = real_now
        ok7 = ok7 and (T._now_utc() != clock.now_utc())
        record("AC-CVR7", ok7,
               "conversion_funnel_board source free of"
               " data-changing statements; four-table counts"
               " unchanged across the double-read battery;"
               " default + both window dumps byte-identical"
               " (sorted and insertion order); freetrial.py +"
               " config.json sha256 stable across the whole run"
               " (zero product bytes - pin-only suite); suite +"
               " face sources pure ASCII with network-free"
               " import lines (%d imports); SUITES registration"
               " row present (ledger-freetrial-funnelroll,"
               " criteria %d); frozen clock restored with probe"
               % (len(imports), EXPECTED))

        fail = sum(1 for _, ok in RESULTS if not ok)
        print("SUITE %s %d/%d exit=%d"
              % ("PASS" if fail == 0 else "FAIL",
                 len(RESULTS) - fail, len(RESULTS),
                 0 if fail == 0 else 1), flush=True)
        ftconn.close()
        ft.close()
        dk.close()
        metered.close()
        led.close()
        shutil.rmtree(tmp, ignore_errors=True)
        return 0 if fail == 0 else 1
    finally:
        T._now_utc = real_now


if __name__ == "__main__":
    sys.exit(main())
