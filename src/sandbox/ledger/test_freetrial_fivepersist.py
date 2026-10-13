"""Acceptance suite for the free-trial five count faces
(calls_by_month / calls_by_kind / calls_by_plan /
calls_by_engine / calls_by_account) windowed-read
cross-restart persistence (BigDomain R1914 tech-queue claim
row; seed = the R1909 re-seeded row - the five count faces
carry their window parameterization (R1828/R1829/R1830/
R1831/R1837) while the derived-read purity across a face
restart stayed unpinned). Asserts the pre-registered criteria
AC-CFP1..AC-CFP7 from the R1914 tech.md claim line (criteria
were registered before this code existed; honesty law).

Carrier verdict (the R1890/R1895 freetrial persist precedent):
the FreeTrialFace owns no db file of its own choice - it
derives its path from the injected DevKeyFace, so the restart
proof must carry the whole stack (Ledger -> MeteredFace ->
DevKeyFace -> FreeTrialFace). The stack closes in reverse
dependency order and reopens on the same db path with the same
config; every windowed read must return byte-identical to the
pre-close snapshot (zero in-memory drift on a derived face),
November calls written through the reopened face must recompute
the default reads (zero cache) while the October windowed
reads stay byte-identical (window isolation across restart AND
across new data - the five faces are row-filter windows over
the record-time column, so no cross-month call ban applies
here, unlike the R1895 cap board's lifetime-count domain), and
a third instance must read sequentially identical.

World (the R1858 callroll recipe, restart-shaped): frozen
clock BASE_DT 2026-10-15; the October era holds two devs and
two plans with three calls (usr:five-a on five-pa with two
backtest calls on eng-x, usr:five-b on five-pb with one
visualize call on eng-y); the November era, written on the
reopened stack, adds usr:five-c on five-pc with one backtest
and one visualize call, both on eng-z. Zero product bytes: the
restart semantics already live in the faces, this suite only
pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_fivepersist.py
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
EMPTY_WIN = "2026-12"

FACES = [
    ("month", "calls_by_month", "substr(called_utc, 1, 7)"),
    ("kind", "calls_by_kind", "kind"),
    ("plan", "calls_by_plan", "plan_id"),
    ("engine", "calls_by_engine", "engine_ref"),
    ("account", "calls_by_account", "dev_account"),
]

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
BANNED_WRITES = ("INSERT INTO", "REPLACE INTO", "UPDATE ",
                 "DELETE FROM")


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


def build_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)
    return led, metered, dk, ft


def close_stack(led, metered, dk, ft):
    ft.close()
    dk.close()
    metered.close()
    led.close()


def face_call(ft, name, window):
    return getattr(ft, name)(window)


def manual_group(obs, col, window):
    if window is None:
        rows = obs.execute(
            "SELECT " + col + ", COUNT(*) FROM trial_calls"
            " GROUP BY " + col + " ORDER BY " + col
        ).fetchall()
    else:
        rows = obs.execute(
            "SELECT " + col + ", COUNT(*) FROM trial_calls"
            " WHERE substr(called_utc, 1, 7) = ?"
            " GROUP BY " + col + " ORDER BY " + col,
            (window,)).fetchall()
    if col == "plan_id":
        return {int(r[0]): int(r[1]) for r in rows}
    return {str(r[0]): int(r[1]) for r in rows}


def main():
    tmp = tempfile.mkdtemp(prefix="freetrial-fivepersist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "freetrial.py"), "rb") as handle:
        face_bytes = handle.read()
    face_sha = hashlib.sha256(face_bytes).hexdigest()
    db_path = os.path.join(tmp, "ledger.db")

    led, metered, dk, ft = build_stack(db_path, cfg)
    obs = sqlite3.connect(ft.db_path)

    def _count(table):
        return obs.execute(
            "SELECT COUNT(*) FROM " + table).fetchone()[0]

    def _win_count(table, col, win):
        return obs.execute(
            "SELECT COUNT(*) FROM " + table
            + " WHERE substr(" + col + ", 1, 7) = ?",
            (win,)).fetchone()[0]

    clock = _FrozenClock()
    real_now = T._now_utc
    try:
        T._now_utc = clock.now_utc

        # -- October world (real product write path) ----------
        dk.issue_key("usr:five-a", "five-a-key", 100,
                     ["backtest"], False)
        pa = ft.register_trial_plan("five-pa", "Five Persist A",
                                   5, False)
        ft.grant_trial("usr:five-a", pa["plan_id"])
        ft.trial_call("usr:five-a", pa["plan_id"], "backtest",
                      "fp1", "eng-x")
        clock.advance(7)
        ft.trial_call("usr:five-a", pa["plan_id"], "backtest",
                      "fp2", "eng-x")
        clock.advance(7)
        dk.issue_key("usr:five-b", "five-b-key", 100,
                     ["visualize"], False)
        pb = ft.register_trial_plan("five-pb", "Five Persist B",
                                   4, True)
        ft.grant_trial("usr:five-b", pb["plan_id"])
        ft.trial_call("usr:five-b", pb["plan_id"], "visualize",
                      "fb1", "eng-y")

        oct_g = _win_count("trial_grants", "granted_utc",
                           OLD_WIN)
        oct_c = _win_count("trial_calls", "called_utc",
                           OLD_WIN)
        W = obs.execute(
            "SELECT substr(called_utc, 1, 7) FROM"
            " trial_calls ORDER BY called_utc, call_ref"
            " LIMIT 1").fetchone()[0]

        # -- AC-CFP1 world load + pre-close snapshots ---------
        expect_def = {
            "month": {OLD_WIN: 3},
            "kind": {"backtest": 2, "visualize": 1},
            "plan": {pa["plan_id"]: 2, pb["plan_id"]: 1},
            "engine": {"eng-x": 2, "eng-y": 1},
            "account": {"usr:five-a": 2, "usr:five-b": 1},
        }
        S_def = {}
        S_oct = {}
        ok1 = (oct_g == 2 and oct_c == 3 and W == OLD_WIN)
        for key, name, col in FACES:
            env_d = face_call(ft, name, None)
            env_o = face_call(ft, name, OLD_WIN)
            env_d2 = face_call(ft, name, None)
            S_def[key] = json.dumps(env_d, sort_keys=True)
            S_oct[key] = json.dumps(env_o, sort_keys=True)
            base_keys = {name, "total", "disclaimer"}
            ok1 = (ok1
                   and set(env_d.keys()) == base_keys
                   and set(env_o.keys())
                   == base_keys | {"window"}
                   and env_o["window"] == OLD_WIN
                   and env_d[name] == expect_def[key]
                   and env_o[name] == expect_def[key]
                   and env_d["total"] == 3
                   and env_o["total"] == 3
                   and env_d["total"]
                   == sum(env_d[name].values())
                   and env_d["disclaimer"] == DISCLAIMER
                   and json.dumps(env_d2, sort_keys=True)
                   == S_def[key]
                   and env_d[name]
                   == manual_group(obs, col, None)
                   and env_o[name]
                   == manual_group(obs, col, OLD_WIN))
        record("AC-CFP1", ok1,
               "stack1 loaded under the frozen clock; SQL %s"
               " record-time stamps (grants=%d calls=%d); W"
               " derived from the first call row (%s); ten"
               " pre-close snapshots anchored - five default"
               " envelopes pinned to exactly 3 keys with cell"
               " values month=%s kind=%s plan=%s engine=%s"
               " account=%s (total==3 == sum per face) and"
               " five %s windowed envelopes pinned to exactly"
               " 4 keys with the window echo; manual SQL"
               " GROUP BY cross-checks equal on all ten reads;"
               " same-param double reads self-identical"
               % (OLD_WIN, oct_g, oct_c, W,
                  expect_def["month"], expect_def["kind"],
                  expect_def["plan"], expect_def["engine"],
                  expect_def["account"], OLD_WIN))

        # -- restart: four-piece stack close + reopen ---------
        close_stack(led, metered, dk, ft)
        led, metered, dk, ft = build_stack(db_path, cfg)

        # -- AC-CFP2 windowed reads restored -----------------
        ok2 = True
        for key, name, _col in FACES:
            env_o = face_call(ft, name, OLD_WIN)
            env_o2 = face_call(ft, name, OLD_WIN)
            ok2 = (ok2
                   and json.dumps(env_o, sort_keys=True)
                   == S_oct[key]
                   and json.dumps(env_o2, sort_keys=True)
                   == S_oct[key])
        record("AC-CFP2", ok2,
               "four-piece stack closed in reverse dependency"
               " order and reopened on the same db path with"
               " the same config; all five %s windowed reads"
               " are byte-identical to the pre-close snapshots"
               " (4-key envelopes with the window echo; group"
               " keys walk in query order so the dicts are"
               " stable across restart - zero in-memory drift"
               " on the derived faces); same-param second"
               " reads self-identical" % OLD_WIN)

        # -- AC-CFP3 default reads restored -------------------
        ok3 = True
        for key, name, _col in FACES:
            env_d = face_call(ft, name, None)
            ok3 = (ok3
                   and json.dumps(env_d, sort_keys=True)
                   == S_def[key]
                   and set(env_d.keys())
                   == {name, "total", "disclaimer"})
        record("AC-CFP3", ok3,
               "post-restart default reads are byte-identical"
               " to the pre-close default snapshots on all"
               " five faces (3-key envelopes, zero window key);"
               " in the October-only era the default cell"
               " values equal the oct windowed cell values"
               " (the month face keeps month cells, the other"
               " four keep row-filter windows - same values"
               " while only one month holds rows)")

        # -- month roll: +23d, new dev written on reopened ---
        clock.advance(23 * 86400)
        dk.issue_key("usr:five-c", "five-c-key", 100,
                     ["backtest", "visualize"], False)
        pc = ft.register_trial_plan("five-pc", "Five Persist C",
                                   6, True)
        ft.grant_trial("usr:five-c", pc["plan_id"])
        ft.trial_call("usr:five-c", pc["plan_id"], "backtest",
                      "fc1", "eng-z")
        clock.advance(3)
        ft.trial_call("usr:five-c", pc["plan_id"], "visualize",
                      "fc2", "eng-z")

        # -- AC-CFP4 recompute face + old-window isolation ----
        nov_c = _win_count("trial_calls", "called_utc",
                           NEW_WIN)
        expect_def2 = {
            "month": {OLD_WIN: 3, NEW_WIN: 2},
            "kind": {"backtest": 3, "visualize": 2},
            "plan": {pa["plan_id"]: 2, pb["plan_id"]: 1,
                     pc["plan_id"]: 2},
            "engine": {"eng-x": 2, "eng-y": 1, "eng-z": 2},
            "account": {"usr:five-a": 2, "usr:five-b": 1,
                        "usr:five-c": 2},
        }
        expect_nov = {
            "month": {NEW_WIN: 2},
            "kind": {"backtest": 1, "visualize": 1},
            "plan": {pc["plan_id"]: 2},
            "engine": {"eng-z": 2},
            "account": {"usr:five-c": 2},
        }
        ok4 = (nov_c == 2)
        for key, name, _col in FACES:
            env_d = face_call(ft, name, None)
            env_n = face_call(ft, name, NEW_WIN)
            env_o = face_call(ft, name, OLD_WIN)
            ok4 = (ok4
                   and env_d[name] == expect_def2[key]
                   and env_d["total"] == 5
                   and json.dumps(env_d, sort_keys=True)
                   != S_def[key]
                   and env_n[name] == expect_nov[key]
                   and env_n["total"] == 2
                   and env_n["window"] == NEW_WIN
                   and json.dumps(env_o, sort_keys=True)
                   == S_oct[key])
        record("AC-CFP4", ok4,
               "clock +23d crossed the month boundary; the"
               " November usr:five-c grant on five-pc with one"
               " backtest and one visualize call (SQL %s"
               " calls=%d, written through the reopened stack)"
               " recomputed all five default reads (month=%s"
               " kind=%s plan=%s engine=%s account=%s,"
               " total==5, byte-different from the pre-close"
               " default snapshots - zero cached state on the"
               " faces) while all five %s windowed reads"
               " stayed byte-identical to the pre-close"
               " snapshots (trial_calls rows keep their"
               " record-time stamps - old window zero leakage"
               " across restart AND across new data); the %s"
               " windowed reads carry the new-month cells"
               " (total==2 on every face)"
               % (NEW_WIN, nov_c,
                  expect_def2["month"], expect_def2["kind"],
                  expect_def2["plan"], expect_def2["engine"],
                  expect_def2["account"], OLD_WIN, NEW_WIN))

        # -- AC-CFP5 window totals + honest empty + sum -------
        ok5 = True
        for key, name, col in FACES:
            env_o = face_call(ft, name, OLD_WIN)
            env_n = face_call(ft, name, NEW_WIN)
            env_e = face_call(ft, name, EMPTY_WIN)
            env_d = face_call(ft, name, None)
            ok5 = (ok5
                   and env_o["total"] == 3
                   and env_n["total"] == 2
                   and env_e[name] == {}
                   and env_e["total"] == 0
                   and env_e["window"] == EMPTY_WIN
                   and set(env_e.keys())
                   == {name, "total", "disclaimer",
                       "window"}
                   and env_d["total"]
                   == env_o["total"] + env_n["total"]
                   and env_n[name]
                   == manual_group(obs, col, NEW_WIN))
        record("AC-CFP5", ok5,
               "oct windowed totals stay %d across restart and"
               " new data on all five faces (zero penetration);"
               " %s windowed totals==%d; the empty-month %s"
               " reads are honest empties on all five faces"
               " ({} total=0, 4 keys present, zero phantom"
               " cells); the composition law holds per face -"
               " default total == oct total + %s total"
               " (3+2==5, the row-partition telescoping);"
               " nov cells equal the manual SQL window-"
               " predicate GROUP BY cross-checks"
               % (3, NEW_WIN, 2, EMPTY_WIN, NEW_WIN))

        # -- AC-CFP6 third instance, sequential identity ------
        def _battery():
            out = {}
            for key, name, _col in FACES:
                out[("def", key)] = json.dumps(
                    face_call(ft, name, None),
                    sort_keys=True)
                out[("oct", key)] = json.dumps(
                    face_call(ft, name, OLD_WIN),
                    sort_keys=True)
                out[("nov", key)] = json.dumps(
                    face_call(ft, name, NEW_WIN),
                    sort_keys=True)
            return out

        f2 = _battery()
        f2b = _battery()
        close_stack(led, metered, dk, ft)
        led, metered, dk, ft = build_stack(db_path, cfg)
        f3 = _battery()
        ok6 = (f2 == f2b and f3 == f2
               and all(f3[("oct", key)] == S_oct[key]
                       for key, _n, _c in FACES))
        record("AC-CFP6", ok6,
               "stack2 fifteen reads (five faces x default /"
               " %s window / %s window) re-read self-identical,"
               " then closed and reopened as stack3 on the same"
               " db; all fifteen reads are pairwise"
               " byte-identical across the two instances - zero"
               " cross-instance drift; the five oct windowed"
               " reads still equal the ORIGINAL pre-close"
               " snapshots (the persistence core: explicit"
               " window reads survive restart x new data"
               " double hijack without drift)"
               % (OLD_WIN, NEW_WIN))

        # -- AC-CFP7 pure-read law + hygiene -------------------
        ok7 = True
        for _key, name, _col in FACES:
            src = inspect.getsource(
                getattr(T.FreeTrialFace, name))
            ok7 = ok7 and not any(
                b in src for b in BANNED_WRITES)
        counts_before = (_count("trial_plans"),
                         _count("trial_grants"),
                         _count("trial_calls"),
                         _count("trial_conversions"))
        dumps = []
        for _key, name, _col in FACES:
            for win in (None, OLD_WIN, NEW_WIN, EMPTY_WIN):
                e1 = face_call(ft, name, win)
                e2 = face_call(ft, name, win)
                dumps.append((json.dumps(e1, sort_keys=True),
                              json.dumps(e2, sort_keys=True)))
        counts_after = (_count("trial_plans"),
                        _count("trial_grants"),
                        _count("trial_calls"),
                        _count("trial_conversions"))
        ok7 = (ok7
               and all(a == b for (a, b) in dumps)
               and counts_before == (3, 3, 5, 0)
               and counts_after == counts_before)
        with open(os.path.join(BASE, "freetrial.py"),
                  "rb") as h3:
            ok7 = (ok7 and hashlib.sha256(
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
               and "ledger-freetrial-fivepersist" in reg_text
               and "test_freetrial_fivepersist.py" in reg_text
               and len(RESULTS) + 1 == EXPECTED)
        T._now_utc = real_now
        ok7 = ok7 and (T._now_utc() != clock.now_utc())
        record("AC-CFP7", ok7,
               "five face sources free of data-changing"
               " statements; four-table counts pinned"
               " plans/grants/calls/conversions=%s unchanged"
               " across the twenty-shape double-read battery"
               " (five faces x four windows); every shape"
               " double-read byte-identical; freetrial.py +"
               " shipped config.json sha256 stable across the"
               " whole run (zero product bytes - pin-only"
               " suite); suite + face sources pure ASCII with"
               " network-free import lines (%d imports);"
               " SUITES registration row present"
               " (ledger-freetrial-fivepersist, criteria %d);"
               " criteria drift self-check %d+1==%d; frozen"
               " clock restored with probe"
               % (counts_after, len(imports), EXPECTED,
                  len(RESULTS), EXPECTED))

        fail = sum(1 for _, ok in RESULTS if not ok)
        print("SUITE %s %d/%d exit=%d"
              % ("PASS" if fail == 0 else "FAIL",
                 len(RESULTS) - fail, len(RESULTS),
                 0 if fail == 0 else 1), flush=True)
        obs.close()
        close_stack(led, metered, dk, ft)
        shutil.rmtree(tmp, ignore_errors=True)
        return 0 if fail == 0 else 1
    finally:
        T._now_utc = real_now


if __name__ == "__main__":
    sys.exit(main())
