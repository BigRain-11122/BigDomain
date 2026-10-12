"""Acceptance suite for the free-trial cap_usage_board month-roll
fidelity example (BigDomain R1854 tech-queue claim row; seed = the
freetrial.py cap_usage_board window R1842 + read cap R1849 faces,
the R1730/R1738/R1739/R1839/R1845 month-roll family symmetric
gap - cap_usage_board was the one window-parameter family member
without a roll pin). Asserts the pre-registered criteria
AC-CRU1..AC-CRU7 from the R1854 tech.md claim line (criteria
were registered before this code existed; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Carrier verdict (the R1845 devboard_roll dedicated-suite
precedent): the existing test_freetrial_capusage.py world is
built on the real clock and cap_usage_board is a global board,
so roll reads there would be contaminated by real-month rows -
this suite builds a fresh isolated face instance in its own
temp world and freezes the freetrial module clock
(T._now_utc patched onto a deterministic holder, restored in
finally; the R1678 frozen-clock precedent).

World (all stamps ride the frozen clock, the live product
write path - zero fixture injection for the roll scenario):
BASE_DT 2026-10-15, usr:roll-a granted plan roll-p (cap 3)
with 2 October calls, then the clock advances +23d across the
month boundary; November grants roll-q (usr:roll-a) and roll-r
(usr:roll-b) land in the new-month window; the surviving
October grant then takes a third cross-month call - the
lifetime count domain never slices by the window (the R1842
count-domain verdict) while the window keeps slicing the GRANT
row set. Zero product bytes change: the roll semantics already
live in cap_usage_board, this suite only pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_caproll.py
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

ROW_KEYS = {"dev_account", "plan_id", "plan_key", "title",
            "trial_cap", "calls_used", "remaining",
            "granted_utc", "ai_label"}
BASE_ENV_KEYS = {"cap_usage_board", "total", "disclaimer"}
WIN_ENV_KEYS = BASE_ENV_KEYS | {"window"}
CAP_ENV_KEYS = WIN_ENV_KEYS | {"limit", "returned", "truncated"}

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
    tmp = tempfile.mkdtemp(prefix="freetrial-caproll-")
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

    def _pairs(env):
        return [(r["dev_account"], r["plan_id"])
                for r in env["cap_usage_board"]]

    def _row(env, dev, plan_id):
        return [r for r in env["cap_usage_board"]
                if r["dev_account"] == dev
                and r["plan_id"] == plan_id][0]

    clock = _FrozenClock()
    real_now = T._now_utc
    try:
        T._now_utc = clock.now_utc

        # -- AC-CRU1 October anchor world ------------------------
        dk.issue_key("usr:roll-a", "roll-a-key", 100,
                     ["backtest"], False)
        pa = ft.register_trial_plan("roll-p", "Roll Plan P",
                                   3, False)
        ft.grant_trial("usr:roll-a", pa["plan_id"])
        grant_ts = ftconn.execute(
            "SELECT granted_utc FROM trial_grants"
            " WHERE dev_account = ? AND plan_id = ?",
            ("usr:roll-a", pa["plan_id"])).fetchone()[0]
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rc1", "eng-x")
        clock.advance(7)
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rc2", "eng-x")
        clock.advance(7)

        oct_env = ft.cap_usage_board(OLD_WIN)
        ok1 = (grant_ts.startswith(OLD_WIN)
               and set(oct_env.keys()) == WIN_ENV_KEYS
               and oct_env["window"] == OLD_WIN
               and oct_env["total"] == 1
               and len(oct_env["cap_usage_board"]) == 1
               and set(oct_env["cap_usage_board"][0].keys())
               == ROW_KEYS
               and oct_env["cap_usage_board"][0]["calls_used"]
               == 2
               and oct_env["cap_usage_board"][0]["remaining"]
               == 1
               and oct_env["cap_usage_board"][0]["granted_utc"]
               == grant_ts
               and oct_env["disclaimer"] == DISCLAIMER)
        def_env = ft.cap_usage_board()
        ok1 = (ok1
               and def_env["total"] == 1
               and set(def_env.keys()) == BASE_ENV_KEYS
               and _pairs(def_env)
               == [("usr:roll-a", pa["plan_id"])])
        s_oct = json.dumps(oct_env, sort_keys=True)
        record("AC-CRU1", ok1,
               "October anchor: frozen-clock grant stamp %s"
               " (record-time %s prefix); 2 calls -> used=2"
               " remaining=1; explicit %s window read exactly 1"
               " row with 9-key row shape and 4-key envelope;"
               " default all-window read total=%s same row set;"
               " pre-roll snapshot anchored"
               % (grant_ts, OLD_WIN, OLD_WIN, def_env["total"]))

        # -- month roll: +23d crosses the boundary ---------------
        clock.advance(23 * 86400)

        # -- AC-CRU2 new-month grants land in the new window -----
        pq = ft.register_trial_plan("roll-q", "Roll Plan Q",
                                    5, True)
        ft.grant_trial("usr:roll-a", pq["plan_id"])
        clock.advance(7)
        dk.issue_key("usr:roll-b", "roll-b-key", 100,
                     ["backtest"], False)
        pr = ft.register_trial_plan("roll-r", "Roll Plan R",
                                    4, False)
        ft.grant_trial("usr:roll-b", pr["plan_id"])
        clock.advance(7)
        nov_ts = ftconn.execute(
            "SELECT COUNT(*) FROM trial_grants"
            " WHERE substr(granted_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        nov_env = ft.cap_usage_board(NEW_WIN)
        nov_pairs = _pairs(nov_env)
        ok2 = (nov_ts == 2
               and nov_env["window"] == NEW_WIN
               and nov_env["total"] == 2
               and len(nov_env["cap_usage_board"]) == 2
               and nov_pairs
               == [("usr:roll-a", pq["plan_id"]),
                   ("usr:roll-b", pr["plan_id"])]
               and all(r["calls_used"] == 0
                       for r in nov_env["cap_usage_board"])
               and nov_env["cap_usage_board"][0]["ai_label"] == 1
               and nov_env["cap_usage_board"][1]["ai_label"] == 0)
        def2 = ft.cap_usage_board()
        ok2 = (ok2
               and def2["total"] == 3
               and len(def2["cap_usage_board"]) == 3
               and _pairs(def2)
               == [("usr:roll-a", pa["plan_id"]),
                   ("usr:roll-a", pq["plan_id"]),
                   ("usr:roll-b", pr["plan_id"])])
        record("AC-CRU2", ok2,
               "frozen clock +23d crossed the month boundary;"
               " 2 November grants stamped in %s (SQL prefix"
               " count %s); explicit %s window read exactly 2"
               " rows in (dev,plan) ascending order %s, total"
               " %s, zero October rows; default all-window board"
               " carries %d rows including the cross-month rows"
               % (NEW_WIN, nov_ts, NEW_WIN, nov_pairs,
                  nov_env["total"], def2["total"]))

        # -- AC-CRU3 old-month window original-value preservation -
        oct2_env = ft.cap_usage_board(OLD_WIN)
        ok3 = (json.dumps(oct2_env, sort_keys=True) == s_oct
               and oct2_env["total"] == 1
               and _pairs(oct2_env)
               == [("usr:roll-a", pa["plan_id"])])
        ok3 = ok3 and not any(
            p == ("usr:roll-a", pa["plan_id"])
            for p in nov_pairs)
        record("AC-CRU3", ok3,
               "post-roll (before any cross-month call) explicit"
               " %s window read is byte-identical to the"
               " pre-roll snapshot (grant row set and values"
               " preserved, zero November leakage); %s window"
               " read carries zero October rows - the two"
               " windows never leak into each other in either"
               " direction" % (OLD_WIN, NEW_WIN))

        # -- AC-CRU4 count domain never slices (core) ------------
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rc3-nov", "eng-x")
        call_ts = ftconn.execute(
            "SELECT called_utc FROM trial_calls"
            " WHERE call_ref = ?", ("rc3-nov",)).fetchone()[0]
        oct3_env = ft.cap_usage_board(OLD_WIN)
        nov3_env = ft.cap_usage_board(NEW_WIN)
        def3 = ft.cap_usage_board()
        ok4 = (call_ts.startswith(NEW_WIN)
               and oct3_env["total"] == 1
               and oct3_env["cap_usage_board"][0]["calls_used"]
               == 3
               and oct3_env["cap_usage_board"][0]["remaining"]
               == 0
               and _pairs(oct3_env)
               == [("usr:roll-a", pa["plan_id"])]
               and _row(nov3_env, "usr:roll-a",
                        pq["plan_id"])["calls_used"] == 0
               and all(p != ("usr:roll-a", pa["plan_id"])
                       for p in _pairs(nov3_env))
               and _row(def3, "usr:roll-a",
                        pa["plan_id"])["calls_used"] == 3
               and _row(def3, "usr:roll-a",
                        pa["plan_id"])["remaining"] == 0)
        record("AC-CRU4", ok4,
               "cross-month call %s on the surviving October"
               " grant passed the live gate (used 2 < cap 3);"
               " the %s windowed read still holds the surviving"
               " grant row with LIFETIME calls_used=3 and"
               " remaining=0 (the legal full-cap conversion-gate"
               " trigger state) - the count domain never slices"
               " by the window (R1842 verdict); the October row"
               " stays OUT of the %s window (the window slices"
               " the grant row set, not the counts); the"
               " November roll-q row still shows used=0; default"
               " read carries the same lifetime values"
               % (call_ts, OLD_WIN, NEW_WIN))

        # -- AC-CRU5 read cap rides along across the month -------
        cap1 = ft.cap_usage_board(NEW_WIN, 1)
        nov_full = ft.cap_usage_board(NEW_WIN)
        ok5 = (set(cap1.keys()) == CAP_ENV_KEYS
               and cap1["limit"] == 1
               and cap1["total"] == 2
               and cap1["returned"] == 1
               and cap1["truncated"] is True
               and json.dumps(cap1["cap_usage_board"])
               == json.dumps(nov_full["cap_usage_board"][-1:]))
        cap5 = ft.cap_usage_board(NEW_WIN, 5)
        ok5 = (ok5
               and cap5["total"] == 2
               and cap5["returned"] == 2
               and cap5["truncated"] is False)
        capO = ft.cap_usage_board(OLD_WIN, 1)
        ok5 = (ok5
               and capO["total"] == 1
               and capO["returned"] == 1
               and capO["truncated"] is False)
        record("AC-CRU5", ok5,
               "read cap x window orthogonal combination in the"
               " rolled world: (%s,1) envelope exact 7 keys,"
               " total=%s (the new-month grant-row count, not"
               " the all-window 3 - an honest truncated read),"
               " returned=%s truncated=%s, rows == the new-month"
               " full read tail slice; (%s,5) full return"
               " truncated=False; (%s,1) single-row old-month"
               " cap read total=1 truncated=False - window"
               " filtering runs before the cap"
               % (NEW_WIN, cap1["total"], cap1["returned"],
                  cap1["truncated"], NEW_WIN, OLD_WIN))

        # -- AC-CRU6 immutable rows + pure-read law --------------
        grants_n = _count("trial_grants")
        calls_n = _count("trial_calls")
        ok6 = (grants_n == 3 and calls_n == 3)
        src = inspect.getsource(T.FreeTrialFace.cap_usage_board)
        banned = ("INSERT INTO", "REPLACE INTO",
                  "UPDATE ", "DELETE FROM")
        ok6 = ok6 and not any(b in src for b in banned)
        pre_counts = (_count("trial_plans"), grants_n,
                       calls_n, _count("trial_conversions"))
        d1 = json.dumps(ft.cap_usage_board(), sort_keys=True)
        d2 = json.dumps(ft.cap_usage_board(), sort_keys=True)
        p1 = json.dumps(ft.cap_usage_board())
        p2 = json.dumps(ft.cap_usage_board())
        w1 = json.dumps(ft.cap_usage_board(OLD_WIN),
                        sort_keys=True)
        w2 = json.dumps(ft.cap_usage_board(OLD_WIN),
                        sort_keys=True)
        n1 = json.dumps(ft.cap_usage_board(NEW_WIN),
                        sort_keys=True)
        n2 = json.dumps(ft.cap_usage_board(NEW_WIN),
                        sort_keys=True)
        ok6 = (ok6
               and d1 == d2 and p1 == p2
               and w1 == w2 and n1 == n2
               and (_count("trial_plans"), _count("trial_grants"),
                    _count("trial_calls"),
                    _count("trial_conversions")) == pre_counts)
        record("AC-CRU6", ok6,
               "after the roll: trial_grants=%d trial_calls=%d"
               " (2 October + 1 November call - immutable rows"
               " never lost); method source free of"
               " data-changing statements; four-table counts"
               " %s unchanged across board reads; double-call"
               " dumps byte-identical for default and both"
               " explicit windows (sorted and insertion order)"
               % (grants_n, calls_n, pre_counts))

        # -- AC-CRU7 hygiene and registration --------------------
        with open(os.path.join(BASE, "freetrial.py"),
                  "rb") as h3:
            ok7 = (hashlib.sha256(h3.read()).hexdigest()
                   == face_sha)
        with open(os.path.join(BASE, "config.json"),
                  "rb") as h4:
            ok7 = ok7 and (hashlib.sha256(
                h4.read()).hexdigest() == cfg_sha)
        ok7 = ok7 and all(b < 128 for b in face_bytes)
        imports = [ln.strip() for ln in
                   face_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok7 = ok7 and not any(
            lib in ln for ln in imports for lib in NET_LIBS)
        reg_path = os.path.join(os.path.dirname(BASE),
                                "reconcile_all.py")
        with open(reg_path, "r", encoding="utf-8") as h5:
            reg_text = h5.read()
        ok7 = (ok7
               and "ledger-freetrial-caproll" in reg_text
               and "test_freetrial_caproll.py" in reg_text)
        ok7 = ok7 and (len(RESULTS) + 1 == EXPECTED)
        record("AC-CRU7", ok7,
               "freetrial.py sha256 stable across the whole run"
               " (zero product bytes - pin-only suite); shipped"
               " config.json sha256 stable; face source pure"
               " ASCII with network-free import lines (%d"
               " imports); SUITES registration row present;"
               " criteria drift self-check %d+1==%d"
               % (len(imports), len(RESULTS), EXPECTED))

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
