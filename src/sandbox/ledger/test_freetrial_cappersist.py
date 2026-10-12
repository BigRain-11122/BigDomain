"""Acceptance suite for the free-trial cap_usage_board
capped-window read cross-restart persistence (BigDomain R1895
tech-queue claim row; seed = the R1890 re-seeded row - the cap
board had the window (R1842), the read cap (R1849) and the
month roll (R1854) pinned while the derived-read purity across
a face restart stayed unpinned). Asserts the pre-registered
criteria AC-CRU8..AC-CRU15 from the R1895 tech.md claim line
(criteria were registered before this code existed; honesty
law).

Carrier verdict (the R1890 funnelpersist four-piece restart
precedent): the FreeTrialFace owns no db file of its own choice
- it derives its path from the injected DevKeyFace, so the
restart proof must carry the whole stack (Ledger ->
MeteredFace -> DevKeyFace -> FreeTrialFace). The stack closes
in reverse dependency order and reopens on the same db path
with the same config; every capped or windowed read must
return byte-identical to the pre-close snapshot (zero
in-memory drift on a derived face), a November grant on the
reopened face must recompute the default capped read (zero
cache) while the October windowed capped read stays
byte-identical (window isolation across restart AND across
new data), and a second reopen must read sequentially
identical.

World (the R1854 caproll recipe extended to a two-grant October
era so the limit=1 read produces a real truncated overflow
block - the byte-preservation assertions then carry a
non-trivial block; all stamps ride the frozen clock, the live
product write path, zero fixture injection): BASE_DT
2026-10-15; usr:roll-a granted plan roll-p (cap 3) with 2
October calls and usr:roll-c granted plan roll-s (cap 2) with 1
October call. The cross-month call ban (claim-verdict 3): the
surviving October grants take NO November call in this window,
because a lifetime count change would byte-shift the October
windowed read - the count-domain roll example already lives in
R1854; this window pins the grant-row-set immutability face.
After the restart and +23d: the new dev usr:roll-z (lexically
last, so the default capped tail must drift) takes a November
grant on roll-q (cap 5, ai_label 1). Zero product bytes: the
restart semantics already live in the faces, this suite only
pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_cappersist.py
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
EXPECTED = 8

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"
EMPTY_WIN = "2026-12"

ROW_KEYS = {"dev_account", "plan_id", "plan_key", "title",
            "trial_cap", "calls_used", "remaining",
            "granted_utc", "ai_label"}
BASE_ENV_KEYS = {"cap_usage_board", "total", "disclaimer"}
WIN_ENV_KEYS = BASE_ENV_KEYS | {"window"}
DEF_CAP_KEYS = BASE_ENV_KEYS | {"limit", "returned", "truncated"}
WIN_CAP_KEYS = WIN_ENV_KEYS | {"limit", "returned", "truncated"}

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


def pairs_of(env):
    return [(r["dev_account"], r["plan_id"])
            for r in env["cap_usage_board"]]


def tail_row(env):
    return env["cap_usage_board"][-1]


def main():
    tmp = tempfile.mkdtemp(prefix="freetrial-cappersist-")
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
        dk.issue_key("usr:roll-a", "roll-a-key", 100,
                     ["backtest"], False)
        pa = ft.register_trial_plan("roll-p", "Roll Persist P",
                                    3, False)
        ft.grant_trial("usr:roll-a", pa["plan_id"])
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rp1", "eng-x")
        clock.advance(7)
        ft.trial_call("usr:roll-a", pa["plan_id"], "backtest",
                      "rp2", "eng-x")
        clock.advance(7)
        dk.issue_key("usr:roll-c", "roll-c-key", 100,
                     ["visualize"], False)
        ps = ft.register_trial_plan("roll-s", "Roll Persist S",
                                    2, False)
        ft.grant_trial("usr:roll-c", ps["plan_id"])
        ft.trial_call("usr:roll-c", ps["plan_id"], "visualize",
                      "rs1", "eng-y")

        # -- AC-CRU8 world load + pre-close snapshots ---------
        oct_g = _win_count("trial_grants", "granted_utc",
                           OLD_WIN)
        oct_c = _win_count("trial_calls", "called_utc",
                           OLD_WIN)
        ob = ft.cap_usage_board(OLD_WIN)
        oc = ft.cap_usage_board(OLD_WIN, 1)
        dc = ft.cap_usage_board(None, 1)
        dbare = ft.cap_usage_board()
        oc_tail = tail_row(oc)
        ra = ob["cap_usage_board"][0]
        rc = oc_tail
        ok8 = (oct_g == 2 and oct_c == 3
               and set(ob.keys()) == WIN_ENV_KEYS
               and ob["window"] == OLD_WIN
               and ob["total"] == 2
               and ob["disclaimer"] == DISCLAIMER
               and pairs_of(ob)
               == [("usr:roll-a", pa["plan_id"]),
                   ("usr:roll-c", ps["plan_id"])]
               and set(ra.keys()) == ROW_KEYS
               and ra["calls_used"] == 2
               and ra["remaining"] == 1
               and ra["ai_label"] == 0
               and set(oc.keys()) == WIN_CAP_KEYS
               and oc["window"] == OLD_WIN
               and oc["limit"] == 1 and oc["total"] == 2
               and oc["returned"] == 1
               and oc["truncated"] is True
               and (rc["dev_account"], rc["plan_id"])
               == ("usr:roll-c", ps["plan_id"])
               and rc["calls_used"] == 1
               and rc["remaining"] == 1
               and set(dc.keys()) == DEF_CAP_KEYS
               and dc["limit"] == 1 and dc["total"] == 2
               and dc["returned"] == 1
               and dc["truncated"] is True
               and set(dbare.keys()) == BASE_ENV_KEYS
               and dbare["total"] == 2
               and len(dbare["cap_usage_board"]) == 2)
        S_ob = json.dumps(ob, sort_keys=True)
        S_oc = json.dumps(oc, sort_keys=True)
        S_dc = json.dumps(dc, sort_keys=True)
        S_db = json.dumps(dbare, sort_keys=True)
        record("AC-CRU8", ok8,
               "stack1 loaded under the frozen clock; SQL %s"
               " record-time stamps (grants=%d calls=%d);"
               " usr:roll-a used=2 remaining=1 + usr:roll-c"
               " used=1 remaining=1; four pre-close snapshots"
               " anchored (oct windowed bare 4 keys with"
               " window echo / oct windowed capped 7 keys"
               " overflow block limit=1 total=2 returned=1"
               " truncated=True with the usr:roll-c tail row"
               " / default capped 6 keys same tail row /"
               " default bare 3 keys, 2 rows)"
               % (OLD_WIN, oct_g, oct_c))

        # -- restart: full four-piece stack close + reopen ----
        close_stack(led, metered, dk, ft)
        led, metered, dk, ft = build_stack(db_path, cfg)

        # -- AC-CRU9 capped windowed read restored ------------
        oc2 = ft.cap_usage_board(OLD_WIN, 1)
        oc2b = ft.cap_usage_board(OLD_WIN, 1)
        ob2 = ft.cap_usage_board(OLD_WIN)
        ok9 = (json.dumps(oc2, sort_keys=True) == S_oc
               and json.dumps(oc2b, sort_keys=True) == S_oc
               and json.dumps(ob2, sort_keys=True) == S_ob)
        record("AC-CRU9", ok9,
               "four-piece stack closed in reverse dependency"
               " order and reopened on the same db path with"
               " the same config; the %s windowed capped read"
               " is byte-identical to the pre-close snapshot"
               " (7-key envelope with the window echo and the"
               " non-trivial overflow block; the (dev,plan)"
               " double-key ordering is stable across restart"
               " - zero in-memory drift on the derived face);"
               " a same-param second read is self-identical;"
               " the oct windowed bare read matches its"
               " snapshot too" % OLD_WIN)

        # -- AC-CRU10 default reads restored ------------------
        dc2 = ft.cap_usage_board(None, 1)
        db2 = ft.cap_usage_board()
        ok10 = (json.dumps(dc2, sort_keys=True) == S_dc
                and json.dumps(db2, sort_keys=True) == S_db
                and json.dumps(dc2["cap_usage_board"],
                              sort_keys=True)
                == json.dumps(oc2["cap_usage_board"],
                              sort_keys=True))
        record("AC-CRU10", ok10,
               "post-restart default capped read is"
               " byte-identical to the pre-close snapshot (6-key"
               " envelope without the window echo, total=2,"
               " usr:roll-c tail row); the default bare read"
               " matches its snapshot; in the October-only era"
               " the default capped rows equal the oct windowed"
               " capped rows (same shape apart from the window"
               " key)")

        # -- month roll: +23d, new grant on the reopened face --
        clock.advance(23 * 86400)
        dk.issue_key("usr:roll-z", "roll-z-key", 100,
                     ["backtest"], False)
        pq = ft.register_trial_plan("roll-q", "Roll Persist Q",
                                    5, True)
        ft.grant_trial("usr:roll-z", pq["plan_id"])

        # -- AC-CRU11 recompute face + old-window isolation --
        nov_g = _win_count("trial_grants", "granted_utc",
                           NEW_WIN)
        dc3 = ft.cap_usage_board(None, 1)
        oc3 = ft.cap_usage_board(OLD_WIN, 1)
        nc3 = ft.cap_usage_board(NEW_WIN, 1)
        dc3_tail = tail_row(dc3)
        ok11 = (nov_g == 1
                and dc3["total"] == 3
                and dc3["returned"] == 1
                and dc3["truncated"] is True
                and (dc3_tail["dev_account"],
                     dc3_tail["plan_id"])
                == ("usr:roll-z", pq["plan_id"])
                and dc3_tail["calls_used"] == 0
                and dc3_tail["remaining"] == 5
                and dc3_tail["ai_label"] == 1
                and json.dumps(dc3, sort_keys=True) != S_dc
                and json.dumps(oc3, sort_keys=True) == S_oc
                and nc3["window"] == NEW_WIN
                and nc3["total"] == 1
                and nc3["returned"] == 1
                and nc3["truncated"] is False
                and (tail_row(nc3)["dev_account"],
                     tail_row(nc3)["plan_id"])
                == ("usr:roll-z", pq["plan_id"]))
        record("AC-CRU11", ok11,
               "clock +23d crossed the month boundary on the"
               " reopened face; the November usr:roll-z grant"
               " on roll-q (SQL %s grants=%d) recomputed the"
               " default capped read (limit=1 tail window"
               " drifted [usr:roll-c row] -> [usr:roll-z row]"
               " used=0 remaining=5 ai_label=1 - byte-different"
               " from the pre-close default snapshot, zero"
               " cached state on the face) while the %s"
               " windowed capped read stayed byte-identical to"
               " the pre-close snapshot (old window zero"
               " leakage across restart AND across new data;"
               " grant rows keep their record-time stamps) and"
               " the %s windowed capped read carries the"
               " new-month row (total=1 truncated=False)"
               % (NEW_WIN, nov_g, OLD_WIN, NEW_WIN))

        # -- AC-CRU12 window totals + honest empty + sum -----
        ob3 = ft.cap_usage_board(OLD_WIN)
        nb3 = ft.cap_usage_board(NEW_WIN)
        ec = ft.cap_usage_board(EMPTY_WIN, 1)
        db3 = ft.cap_usage_board()
        ok12 = (json.dumps(oc3, sort_keys=True) == S_oc
                and ob3["total"] == 2
                and nb3["total"] == 1
                and set(ec.keys()) == WIN_CAP_KEYS
                and ec["window"] == EMPTY_WIN
                and ec["cap_usage_board"] == []
                and ec["total"] == 0
                and ec["returned"] == 0
                and ec["truncated"] is False
                and db3["total"] == 3
                and db3["total"]
                == ob3["total"] + nb3["total"])
        record("AC-CRU12", ok12,
               "oct windowed total stays %d across restart and"
               " new data (zero penetration); nov windowed"
               " total=%d; the empty-month %s capped windowed"
               " read is an honest empty (rows=[] total=0"
               " returned=0 truncated=False, all 7 keys"
               " present, zero phantom rows); composition law"
               " holds - default bare total=%d == oct %d + nov"
               " %d (telescoping)"
               % (ob3["total"], nb3["total"], EMPTY_WIN,
                  db3["total"], ob3["total"], nb3["total"]))

        # -- AC-CRU13 pure-read law across restart ------------
        src = inspect.getsource(T.FreeTrialFace.cap_usage_board)
        ok13 = not any(b in src for b in BANNED_WRITES)
        counts_before = (_count("trial_plans"),
                         _count("trial_grants"),
                         _count("trial_calls"),
                         _count("trial_conversions"))
        dumps = []
        for args in ((), (OLD_WIN,), (NEW_WIN,),
                     (None, 1), (OLD_WIN, 1), (NEW_WIN, 1)):
            env1 = ft.cap_usage_board(*args)
            env2 = ft.cap_usage_board(*args)
            dumps.append((json.dumps(env1, sort_keys=True),
                          json.dumps(env2, sort_keys=True)))
        counts_after = (_count("trial_plans"),
                        _count("trial_grants"),
                        _count("trial_calls"),
                        _count("trial_conversions"))
        ok13 = (ok13
                and all(a == b for (a, b) in dumps)
                and counts_before == (3, 3, 3, 0)
                and counts_after == counts_before)
        record("AC-CRU13", ok13,
               "cap_usage_board source free of data-changing"
               " statements; four-table counts pinned"
               " plans/grants/calls/conversions=%s unchanged"
               " across the six-shape double-read battery;"
               " every shape double-read byte-identical"
               " (default and bare windows, default and capped"
               " windows)" % (counts_after,))

        # -- AC-CRU14 second reopen, sequential identity -----
        f2 = {"oc": json.dumps(
                  ft.cap_usage_board(OLD_WIN, 1),
                  sort_keys=True),
              "dc": json.dumps(
                  ft.cap_usage_board(None, 1),
                  sort_keys=True),
              "nc": json.dumps(
                  ft.cap_usage_board(NEW_WIN, 1),
                  sort_keys=True),
              "db": json.dumps(
                  ft.cap_usage_board(),
                  sort_keys=True)}
        f2b = {"oc": json.dumps(
                   ft.cap_usage_board(OLD_WIN, 1),
                   sort_keys=True),
               "dc": json.dumps(
                   ft.cap_usage_board(None, 1),
                   sort_keys=True),
               "nc": json.dumps(
                   ft.cap_usage_board(NEW_WIN, 1),
                   sort_keys=True),
               "db": json.dumps(
                   ft.cap_usage_board(),
                   sort_keys=True)}
        close_stack(led, metered, dk, ft)
        led, metered, dk, ft = build_stack(db_path, cfg)
        f3 = {"oc": json.dumps(
                  ft.cap_usage_board(OLD_WIN, 1),
                  sort_keys=True),
              "dc": json.dumps(
                  ft.cap_usage_board(None, 1),
                  sort_keys=True),
              "nc": json.dumps(
                  ft.cap_usage_board(NEW_WIN, 1),
                  sort_keys=True),
              "db": json.dumps(
                  ft.cap_usage_board(),
                  sort_keys=True)}
        ok14 = (f2 == f2b and f3 == f2
                and f3["oc"] == S_oc)
        record("AC-CRU14", ok14,
               "stack2 four reads re-read self-identical, then"
               " closed and reopened as stack3 on the same db;"
               " all four reads (oct windowed capped / default"
               " capped / %s windowed capped / default bare)"
               " are pairwise byte-identical across the two"
               " instances - zero cross-instance drift; the oct"
               " windowed capped read still equals the ORIGINAL"
               " pre-close snapshot (the persistence core:"
               " explicit window reads survive restart x new"
               " data double hijack without drift)"
               % NEW_WIN)

        # -- AC-CRU15 hygiene + registration -------------------
        with open(os.path.join(BASE, "freetrial.py"),
                  "rb") as h3:
            ok15 = (hashlib.sha256(h3.read()).hexdigest()
                    == face_sha)
        with open(os.path.join(BASE, "config.json"),
                  "rb") as h4:
            ok15 = ok15 and (hashlib.sha256(
                h4.read()).hexdigest() == cfg_sha)
        with open(os.path.abspath(__file__), "rb") as h5:
            self_bytes = h5.read()
        ok15 = (ok15 and all(b < 128 for b in self_bytes)
                and all(b < 128 for b in face_bytes))
        imports = [ln.strip() for ln in
                   self_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok15 = (ok15
                and not any(lib in ln for ln in imports
                           for lib in NET_LIBS))
        reg_path = os.path.join(os.path.dirname(BASE),
                                "reconcile_all.py")
        with open(reg_path, "r", encoding="utf-8") as h6:
            reg_text = h6.read()
        ok15 = (ok15
                and "ledger-freetrial-cappersist" in reg_text
                and "test_freetrial_cappersist.py" in reg_text
                and len(RESULTS) + 1 == EXPECTED)
        T._now_utc = real_now
        ok15 = ok15 and (T._now_utc() != clock.now_utc())
        record("AC-CRU15", ok15,
               "freetrial.py + shipped config.json sha256"
               " stable across the whole run (zero product"
               " bytes - pin-only suite); suite + face sources"
               " pure ASCII with network-free import lines (%d"
               " imports); SUITES registration row present"
               " (ledger-freetrial-cappersist, criteria %d);"
               " criteria drift self-check %d+1==%d; frozen"
               " clock restored with probe"
               % (len(imports), EXPECTED,
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
