"""Acceptance suite for the free-trial calls_by_* profile
family month-roll fidelity example (BigDomain R1858
tech-queue claim row; seed = the calls_by_month/kind/plan/
engine/account five window-parameter profiles R1828/R1829/
R1830/R1831/R1837, the R1730/R1738/R1739/R1839/R1845/R1854
month-roll family symmetric gap - the five call profiles
were the window-parameter family members without roll pins).
Asserts the pre-registered criteria AC-CFR1..AC-CFR7 from
the R1858 tech.md claim line (criteria were registered
before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL.

Carrier verdict (the R1845 devboard_roll / R1854 caproll
dedicated-suite precedent): the existing
test_freetrial_callby* suite worlds are built on the real
clock and the calls_by_* faces are global aggregations, so
roll reads there would be contaminated by real-month rows -
this suite builds a fresh isolated face instance in its own
temp world and freezes the freetrial module clock
(T._now_utc patched onto a deterministic holder, restored in
finally; the R1678 frozen-clock precedent).

World (all stamps ride the frozen clock, the live product
write path - zero fixture injection for the roll scenario):
BASE_DT 2026-10-15; usr:roll-a granted plan roll-p (cap 10)
with 2 October calls, then the clock advances +23d across
the month boundary; the surviving October grant takes a
third cross-month call (visualize/eng-y) and usr:roll-b
takes a fresh November grant roll-q with 1 call. Every
window slices CALL rows by their own called_utc record-time
stamp - never by the grant's birth month - and the
calls_by_month month axis telescopes: the sum of the
observed month-window totals equals the all-window total.
Zero product bytes change: the roll semantics already live
in the five faces, this suite only pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_callroll.py
"""

import datetime
import hashlib
import inspect
import json
import os
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

FACES = ("calls_by_month", "calls_by_kind", "calls_by_plan",
         "calls_by_engine", "calls_by_account")

BASE_ENV_KEYS = {"calls_by_month", "total", "disclaimer"}
WIN_ENV_KEYS = BASE_ENV_KEYS | {"window"}

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")


class _FrozenClock(object):
    """Deterministic UTC clock holder: the freetrial module
    _now_utc is patched onto this holder so grant/call stamps
    roll only when the suite moves the clock."""

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
    tmp = tempfile.mkdtemp(prefix="freetrial-callroll-")
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

    def _env(face, *args):
        return getattr(ft, face)(*args)

    clock = _FrozenClock()
    real_now = T._now_utc
    try:
        T._now_utc = clock.now_utc

        # -- October anchor world --------------------------------
        dk.issue_key("usr:roll-a", "roll-a-key", 100,
                     ["backtest", "visualize"], False)
        pa = ft.register_trial_plan("roll-p", "Roll Plan P",
                                    10, False)
        ft.grant_trial("usr:roll-a", pa["plan_id"])
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rc1-oct", "eng-x")
        clock.advance(7)
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rc2-oct", "eng-x")
        clock.advance(7)

        oct_cells = {
            "calls_by_month": {OLD_WIN: 2},
            "calls_by_kind": {"backtest": 2},
            "calls_by_plan": {pa["plan_id"]: 2},
            "calls_by_engine": {"eng-x": 2},
            "calls_by_account": {"usr:roll-a": 2},
        }

        # -- AC-CFR1 October anchor ------------------------------
        oct_sql = ftconn.execute(
            "SELECT COUNT(*) FROM trial_calls WHERE"
            " substr(called_utc, 1, 7) = ?",
            (OLD_WIN,)).fetchone()[0]
        snapshots = {}
        ok1 = (oct_sql == 2)
        for face in FACES:
            key = face
            wenv = _env(face, OLD_WIN)
            denv = _env(face)
            snapshots[face] = json.dumps(wenv, sort_keys=True)
            ok1 = (ok1
                   and set(wenv.keys())
                   == (WIN_ENV_KEYS - {"calls_by_month"})
                   | {face}
                   and wenv["window"] == OLD_WIN
                   and wenv[key] == oct_cells[face]
                   and wenv["total"] == 2
                   and wenv["disclaimer"] == DISCLAIMER
                   and set(denv.keys()) == BASE_ENV_KEYS - {"calls_by_month"} | {face}
                   and denv[key] == oct_cells[face]
                   and denv["total"] == 2)
        record("AC-CFR1", ok1,
               "October anchor: frozen-clock record-time stamps"
               " (SQL %s prefix count %d); five profile faces"
               " explicit %s window reads carry exactly the"
               " October cells (month=%s kind=backtest:2"
               " plan=%s engine=eng-x:2 account=usr:roll-a:2),"
               " 4-key explicit envelopes + 3-key default"
               " envelopes, total=2 each; pre-roll snapshots"
               " anchored for all five faces"
               % (OLD_WIN, oct_sql, OLD_WIN, OLD_WIN,
                  pa["plan_id"]))

        # -- month roll: +23d crosses the boundary ---------------
        clock.advance(23 * 86400)

        # -- new-month calls land in the new-month cells ---------
        ft.trial_call("usr:roll-a", pa["plan_id"], "visualize",
                      "rc3-nov", "eng-y")
        clock.advance(86400)
        pq = ft.register_trial_plan("roll-q", "Roll Plan Q",
                                    5, False)
        dk.issue_key("usr:roll-b", "roll-b-key", 100,
                     ["backtest"], False)
        ft.grant_trial("usr:roll-b", pq["plan_id"])
        ft.trial_call("usr:roll-b", pq["plan_id"], "backtest",
                      "rb1-nov", "eng-x")

        nov_cells = {
            "calls_by_month": {NEW_WIN: 2},
            "calls_by_kind": {"backtest": 1, "visualize": 1},
            "calls_by_plan": {pa["plan_id"]: 1,
                              pq["plan_id"]: 1},
            "calls_by_engine": {"eng-x": 1, "eng-y": 1},
            "calls_by_account": {"usr:roll-a": 1,
                                 "usr:roll-b": 1},
        }
        all_cells = {
            "calls_by_month": {OLD_WIN: 2, NEW_WIN: 2},
            "calls_by_kind": {"backtest": 3, "visualize": 1},
            "calls_by_plan": {pa["plan_id"]: 3,
                              pq["plan_id"]: 1},
            "calls_by_engine": {"eng-x": 3, "eng-y": 1},
            "calls_by_account": {"usr:roll-a": 3,
                                 "usr:roll-b": 1},
        }

        # -- AC-CFR2 new-month calls land in new-month cells -----
        cross_ts = ftconn.execute(
            "SELECT called_utc FROM trial_calls WHERE"
            " call_ref = ?", ("rc3-nov",)).fetchone()[0]
        nov_sql = ftconn.execute(
            "SELECT COUNT(*) FROM trial_calls WHERE"
            " substr(called_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        ok2 = (cross_ts.startswith(NEW_WIN) and nov_sql == 2)
        for face in FACES:
            key = face
            wenv = _env(face, NEW_WIN)
            denv = _env(face)
            ok2 = (ok2
                   and wenv[key] == nov_cells[face]
                   and wenv["window"] == NEW_WIN
                   and wenv["total"] == 2
                   and denv[key] == all_cells[face]
                   and denv["total"] == 4)
        record("AC-CFR2", ok2,
               "frozen clock +23d crossed the month boundary;"
               " the cross-month call on the SURVIVING October"
               " grant stamps called_utc=%s (SQL %s prefix"
               " count %d) - every window slices CALL rows by"
               " their own record-time stamp, never by the"
               " grant's birth month; five profile faces"
               " explicit %s window reads carry exactly the"
               " new-month cells %s with total=2; default"
               " all-window reads carry the cross-month rows"
               " with total=4 (%s)"
               % (cross_ts, NEW_WIN, nov_sql, NEW_WIN,
                  {f: nov_cells[f] for f in
                   ("calls_by_kind", "calls_by_account")},
                  {f: all_cells[f] for f in
                   ("calls_by_month", "calls_by_engine")}))

        # -- AC-CFR3 old-month window original-value preservation -
        ok3 = True
        for face in FACES:
            oct2 = _env(face, OLD_WIN)
            ok3 = (ok3
                   and json.dumps(oct2, sort_keys=True)
                   == snapshots[face]
                   and oct2["total"] == 2)
            nov = _env(face, NEW_WIN)
            nov_key = face
            if face == "calls_by_month":
                ok3 = ok3 and OLD_WIN not in nov[nov_key]
            else:
                ok3 = ok3 and sum(nov[nov_key].values()) == 2
        record("AC-CFR3", ok3,
               "post-roll explicit %s window reads are"
               " byte-identical to the pre-roll snapshots for"
               " all five faces (original cell values and"
               " totals preserved, zero November leakage);"
               " %s window reads carry zero October cells -"
               " the two windows never leak into each other in"
               " either direction" % (OLD_WIN, NEW_WIN))

        # -- AC-CFR4 calls_by_month month-axis telescoping --------
        m_old = _env("calls_by_month", OLD_WIN)
        m_new = _env("calls_by_month", NEW_WIN)
        m_all = _env("calls_by_month")
        sql_old = ftconn.execute(
            "SELECT COUNT(*) FROM trial_calls WHERE"
            " substr(called_utc, 1, 7) = ?",
            (OLD_WIN,)).fetchone()[0]
        sql_new = ftconn.execute(
            "SELECT COUNT(*) FROM trial_calls WHERE"
            " substr(called_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        ok4 = (m_old["calls_by_month"][OLD_WIN] == sql_old == 2
               and m_new["calls_by_month"][NEW_WIN] == sql_new == 2
               and m_old["total"] + m_new["total"]
               == m_all["total"] == 4
               and sum(m_all["calls_by_month"].values())
               == m_all["total"])
        record("AC-CFR4", ok4,
               "month-axis telescoping: month-window totals"
               " %s(%d) + %s(%d) == all-window total %d; each"
               " month cell equals its SQL record-time COUNT"
               " cross-check (%d/%d)"
               % (OLD_WIN, m_old["total"], NEW_WIN,
                  m_new["total"], m_all["total"], sql_old,
                  sql_new))

        # -- AC-CFR5 immutable rows + pure-read law --------------
        calls_n = _count("trial_calls")
        ok5 = (calls_n == 4)
        banned = ("INSERT INTO", "REPLACE INTO", "UPDATE ",
                  "DELETE FROM")
        for face in FACES:
            src = inspect.getsource(getattr(T.FreeTrialFace,
                                            face))
            ok5 = ok5 and not any(b in src for b in banned)
        pre_counts = (_count("trial_plans"),
                      _count("trial_grants"), calls_n,
                      _count("trial_conversions"))
        dumps = []
        for face in FACES:
            for args in ((), (OLD_WIN,), (NEW_WIN,)):
                env1 = _env(face, *args)
                env2 = _env(face, *args)
                dumps.append((json.dumps(env1, sort_keys=True),
                              json.dumps(env2, sort_keys=True),
                              json.dumps(env1),
                              json.dumps(env2)))
        ok5 = (ok5
               and all(a == b and c == d
                       for (a, b, c, d) in dumps)
               and (_count("trial_plans"),
                    _count("trial_grants"),
                    _count("trial_calls"),
                    _count("trial_conversions"))
               == pre_counts)
        record("AC-CFR5", ok5,
               "immutable rows never lost: trial_calls=%d"
               " (2 October + 2 November); all five method"
               " sources free of data-changing statements;"
               " four-table counts %s unchanged across reads;"
               " double-call dumps byte-identical for default"
               " and both explicit windows on all five faces"
               " (sorted and insertion order)"
               % (calls_n, pre_counts))

        # -- AC-CFR6 hygiene --------------------------------------
        with open(os.path.join(BASE, "freetrial.py"),
                  "rb") as h3:
            ok6 = (hashlib.sha256(h3.read()).hexdigest()
                   == face_sha)
        with open(os.path.join(BASE, "config.json"),
                  "rb") as h4:
            ok6 = ok6 and (hashlib.sha256(
                h4.read()).hexdigest() == cfg_sha)
        ok6 = ok6 and all(b < 128 for b in face_bytes)
        imports = [ln.strip() for ln in
                   face_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok6 = ok6 and not any(
            lib in ln for ln in imports for lib in NET_LIBS)
        record("AC-CFR6", ok6,
               "freetrial.py sha256 stable across the whole run"
               " (zero product bytes - pin-only suite); shipped"
               " config.json sha256 stable; face source pure"
               " ASCII with network-free import lines (%d"
               " imports)" % len(imports))

        # -- AC-CFR7 registration + criteria drift ----------------
        reg_path = os.path.join(os.path.dirname(BASE),
                                "reconcile_all.py")
        with open(reg_path, "r", encoding="utf-8") as h5:
            reg_text = h5.read()
        ok7 = ("ledger-freetrial-callroll" in reg_text
               and "test_freetrial_callroll.py" in reg_text
               and len(RESULTS) + 1 == EXPECTED)
        record("AC-CFR7", ok7,
               "SUITES registration row present"
               " (ledger-freetrial-callroll, criteria 7);"
               " criteria drift self-check %d+1==%d"
               % (len(RESULTS), EXPECTED))

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
        return 0 if fail == 0 else 1
    finally:
        T._now_utc = real_now


if __name__ == "__main__":
    sys.exit(main())
