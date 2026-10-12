"""Acceptance suite for the free-trial conversion-funnel
board capped-window read cross-restart persistence
(BigDomain R1890 tech-queue claim row; seed = the R1880
re-seeded row - the funnel board had the window (R1793),
the roll (R1874) and the read cap (R1880) pinned while the
derived-read purity across a face restart stayed unpinned).
Asserts the pre-registered criteria AC-CVR15..AC-CVR21
from the R1890 tech.md claim line (criteria were
registered before this code existed; honesty law).

Carrier verdict (the R1884/R1889 restart-family precedent
extended to the full dependency-injection chain): the
FreeTrialFace owns no db file of its own choice - it
derives its path from the injected DevKeyFace, so the
restart proof must carry the whole four-piece stack
(Ledger -> MeteredFace -> DevKeyFace -> FreeTrialFace).
The stack closes in reverse dependency order and reopens
on the same db path with the same config; every capped or
windowed read must return byte-identical to the
pre-close snapshot (zero in-memory drift on a derived
face), new November rows must recompute the default
capped read (zero cache) while the October windowed
capped read stays byte-identical (window isolation
across restart AND across new data), and a second
reopen must read sequentially identical.

World (R1874 funnelroll reuse, frozen clock, real product
write path - zero fixture injection): BASE_DT 2026-10-15;
two registered plans roll-fp / roll-hq. October phase:
usr:fun-a grant + same-month conversion and usr:fun-b
grant staying active on roll-fp; roll-hq honest zero row.
After +23d crosses the month boundary: usr:fun-d takes a
fresh November grant + same-month conversion on roll-hq.
Row-level injection only (the registry stays at two
plans) so the dense-axis total stays 2 and the old-window
snapshot - overflow block included - stays byte-identical
(the registry-growth break note is pinned in the claim
line). Zero product bytes: the restart semantics already
live in the faces, this suite only pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_funnelpersist.py
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
OCT_BARE_KEYS = {"conversion_funnel_board", "window",
                 "disclaimer"}
OCT_CAP_KEYS = (OCT_BARE_KEYS
                | {"limit", "total", "returned", "truncated"})
DEF_CAP_KEYS = {"conversion_funnel_board", "limit", "total",
                "returned", "truncated", "disclaimer"}
DEF_BARE_KEYS = {"conversion_funnel_board", "disclaimer"}

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


def row_of(env, plan_key):
    for r in env["conversion_funnel_board"]:
        if r["plan_key"] == plan_key:
            return r
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="freetrial-funnelpersist-")
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

    clock = _FrozenClock()
    real_now = T._now_utc
    try:
        T._now_utc = clock.now_utc

        # -- October world (real product write path) ----------
        pa = ft.register_trial_plan("roll-fp", "Roll Funnel P",
                                    10, False)
        qb = ft.register_trial_plan("roll-hq", "Roll Funnel Q",
                                    5, False)
        for who, key in (("usr:fun-a", "fun-a-key"),
                         ("usr:fun-b", "fun-b-key")):
            dk.issue_key(who, key, 100, ["backtest"], False)
            ft.grant_trial(who, pa["plan_id"])
            clock.advance(60)
        ft.convert_upgrade("usr:fun-a", pa["plan_id"],
                           "tier-pro")

        # -- AC-CVR15 world load + pre-close snapshots -------
        oct_g_sql = obs.execute(
            "SELECT COUNT(*) FROM trial_grants WHERE"
            " substr(granted_utc, 1, 7) = ?",
            (OLD_WIN,)).fetchone()[0]
        oct_c_sql = obs.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " substr(converted_utc, 1, 7) = ?",
            (OLD_WIN,)).fetchone()[0]
        ob = ft.conversion_funnel_board(OLD_WIN)
        oc = ft.conversion_funnel_board(OLD_WIN, 1)
        dc = ft.conversion_funnel_board(None, 1)
        db = ft.conversion_funnel_board()
        oc_tail = row_of(oc, "roll-hq")
        fp_row = row_of(ob, "roll-fp")
        ok15 = (oct_g_sql == 2 and oct_c_sql == 1
                and set(ob.keys()) == OCT_BARE_KEYS
                and ob["window"] == OLD_WIN
                and ob["disclaimer"] == DISCLAIMER
                and len(ob["conversion_funnel_board"]) == 2
                and set(fp_row.keys()) == ROW_KEYS
                and fp_row["granted"] == 2
                and fp_row["converted"] == 1
                and fp_row["active_trials"] == 1
                and fp_row["conversion_rate"] == 0.5
                and set(oc.keys()) == OCT_CAP_KEYS
                and oc["limit"] == 1 and oc["total"] == 2
                and oc["returned"] == 1
                and oc["truncated"] is True
                and len(oc["conversion_funnel_board"]) == 1
                and set(oc_tail.keys()) == ROW_KEYS
                and oc_tail["granted"] == 0
                and oc_tail["converted"] == 0
                and oc_tail["active_trials"] == 0
                and oc_tail["conversion_rate"] == 0.0
                and set(dc.keys()) == DEF_CAP_KEYS
                and dc["total"] == 2 and dc["returned"] == 1
                and dc["truncated"] is True
                and set(db.keys()) == DEF_BARE_KEYS
                and len(db["conversion_funnel_board"]) == 2)
        S_ob = json.dumps(ob, sort_keys=True)
        S_oc = json.dumps(oc, sort_keys=True)
        S_dc = json.dumps(dc, sort_keys=True)
        S_db = json.dumps(db, sort_keys=True)
        record("AC-CVR15", ok15,
               "stack1 loaded under the frozen clock; SQL %s"
               " record-time stamps (grants=%d conversions=%d);"
               " roll-fp granted=2 converted=1 active=1"
               " rate=0.5; four pre-close snapshots anchored"
               " (oct windowed bare 3 keys / oct windowed"
               " capped 7 keys with overflow block total=2"
               " returned=1 truncated=True and the roll-hq"
               " honest-zero tail row / default capped 6 keys"
               " / default bare 2 keys)"
               % (OLD_WIN, oct_g_sql, oct_c_sql))

        # -- restart: full four-piece stack close + reopen ----
        close_stack(led, metered, dk, ft)
        led, metered, dk, ft = build_stack(db_path, cfg)

        # -- AC-CVR16 capped windowed read restored -----------
        oc2 = ft.conversion_funnel_board(OLD_WIN, 1)
        oc2b = ft.conversion_funnel_board(OLD_WIN, 1)
        ob2 = ft.conversion_funnel_board(OLD_WIN)
        ok16 = (json.dumps(oc2, sort_keys=True) == S_oc
                and json.dumps(oc2b, sort_keys=True) == S_oc
                and json.dumps(ob2, sort_keys=True) == S_ob)
        record("AC-CVR16", ok16,
               "four-piece stack closed in reverse dependency"
               " order and reopened on the same db path with"
               " the same config; the %s windowed capped read"
               " is byte-identical to the pre-close snapshot"
               " (7-key envelope with the window echo and the"
               " overflow block; the plan_key-ordered tail row"
               " is stable across restart - zero in-memory"
               " drift on the derived face), a same-param"
               " second read is self-identical, and the oct"
               " windowed bare read matches its snapshot too"
               % OLD_WIN)

        # -- AC-CVR17 default capped read restored ------------
        dc2 = ft.conversion_funnel_board(None, 1)
        db2 = ft.conversion_funnel_board()
        ok17 = (json.dumps(dc2, sort_keys=True) == S_dc
                and json.dumps(db2, sort_keys=True) == S_db
                and json.dumps(
                    dc2["conversion_funnel_board"], sort_keys=True)
                == json.dumps(
                    oc2["conversion_funnel_board"],
                    sort_keys=True))
        record("AC-CVR17", ok17,
               "post-restart default capped read is"
               " byte-identical to the pre-close snapshot (6-key"
               " envelope without the window echo, total=2,"
               " roll-hq tail row); the default bare read"
               " matches its snapshot; in the October-only era"
               " the default capped rows equal the oct windowed"
               " capped rows (same shape apart from the window"
               " key)")

        # -- month roll: +23d, new data on the reopened face --
        clock.advance(23 * 86400)
        dk.issue_key("usr:fun-d", "fun-d-key", 100,
                     ["backtest"], False)
        ft.grant_trial("usr:fun-d", qb["plan_id"])
        ft.convert_upgrade("usr:fun-d", qb["plan_id"],
                           "tier-pro")

        # -- AC-CVR18 recompute face + old-window isolation --
        dc3 = ft.conversion_funnel_board(None, 1)
        oc3 = ft.conversion_funnel_board(OLD_WIN, 1)
        nc3 = ft.conversion_funnel_board(NEW_WIN, 1)
        dc3_tail = row_of(dc3, "roll-hq")
        nc3_tail = row_of(nc3, "roll-hq")
        nov_c_sql = obs.execute(
            "SELECT COUNT(*) FROM trial_conversions WHERE"
            " substr(converted_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        ok18 = (nov_c_sql == 1
                and dc3["total"] == 2 and dc3["returned"] == 1
                and dc3_tail["granted"] == 1
                and dc3_tail["converted"] == 1
                and dc3_tail["active_trials"] == 0
                and dc3_tail["conversion_rate"] == 1.0
                and json.dumps(dc3, sort_keys=True) != S_dc
                and json.dumps(oc3, sort_keys=True) == S_oc
                and nc3["window"] == NEW_WIN
                and nc3["total"] == 2
                and nc3_tail["granted"] == 1
                and nc3_tail["converted"] == 1)
        record("AC-CVR18", ok18,
               "clock +23d crossed the month boundary on the"
               " reopened face; the November usr:fun-d grant +"
               " same-month conversion (SQL %s conversions=%d)"
               " recomputed the default capped read (limit=1"
               " tail row roll-hq granted=1 converted=1"
               " rate=1.0 - byte-different from the pre-close"
               " default snapshot, zero cached state on the"
               " face) while the %s windowed capped read"
               " stayed byte-identical to the pre-close"
               " snapshot (old window zero leakage across"
               " restart AND across new data; registry-dense"
               " axis total stays 2) and the %s windowed"
               " capped read carries the new-month row"
               % (NEW_WIN, nov_c_sql, OLD_WIN, NEW_WIN))

        # -- AC-CVR19 window semantics across restart --------
        ob3 = ft.conversion_funnel_board(OLD_WIN)
        nb3 = ft.conversion_funnel_board(NEW_WIN)
        db3 = ft.conversion_funnel_board()
        ob3_hq = row_of(ob3, "roll-hq")
        nb3_hq = row_of(nb3, "roll-hq")
        db3_fp = row_of(db3, "roll-fp")
        db3_hq = row_of(db3, "roll-hq")
        ok19 = (json.dumps(ob3, sort_keys=True) == S_ob
                and nb3_hq["granted"] == 1
                and nb3_hq["converted"] == 1
                and db3_fp["granted"] == 2
                and db3_fp["converted"] == 1
                and db3_fp["active_trials"] == 1
                and db3_hq["granted"] == 1
                and db3_hq["converted"] == 1
                and ob3_hq["granted"] == 0
                and db3_hq["granted"] != ob3_hq["granted"])
        record("AC-CVR19", ok19,
               "the oct windowed bare read still equals the"
               " pre-close snapshot; the %s windowed bare read"
               " carries the new-month row (roll-hq granted=1)"
               " while the oct window still shows the roll-hq"
               " zero row - the two row sets differ, window"
               " filtering and the default face stay orthogonal;"
               " the default bare read carries both eras"
               " (roll-fp 2/1/1 rate=0.5 + roll-hq 1/1/0"
               " rate=1.0)"
               % NEW_WIN)

        # -- AC-CVR20 second reopen, sequential identity -----
        f2 = {"oc": json.dumps(
                  ft.conversion_funnel_board(OLD_WIN, 1),
                  sort_keys=True),
              "dc": json.dumps(
                  ft.conversion_funnel_board(None, 1),
                  sort_keys=True),
              "nc": json.dumps(
                  ft.conversion_funnel_board(NEW_WIN, 1),
                  sort_keys=True),
              "db": json.dumps(
                  ft.conversion_funnel_board(),
                  sort_keys=True)}
        f2b = {"oc": json.dumps(
                   ft.conversion_funnel_board(OLD_WIN, 1),
                   sort_keys=True),
               "dc": json.dumps(
                   ft.conversion_funnel_board(None, 1),
                   sort_keys=True),
               "nc": json.dumps(
                   ft.conversion_funnel_board(NEW_WIN, 1),
                   sort_keys=True),
               "db": json.dumps(
                   ft.conversion_funnel_board(),
                   sort_keys=True)}
        counts_before = (_count("trial_plans"),
                         _count("trial_grants"),
                         _count("trial_conversions"),
                         _count("trial_calls"))
        close_stack(led, metered, dk, ft)
        led, metered, dk, ft = build_stack(db_path, cfg)
        f3 = {"oc": json.dumps(
                  ft.conversion_funnel_board(OLD_WIN, 1),
                  sort_keys=True),
              "dc": json.dumps(
                  ft.conversion_funnel_board(None, 1),
                  sort_keys=True),
              "nc": json.dumps(
                  ft.conversion_funnel_board(NEW_WIN, 1),
                  sort_keys=True),
              "db": json.dumps(
                  ft.conversion_funnel_board(),
                  sort_keys=True)}
        counts_after = (_count("trial_plans"),
                        _count("trial_grants"),
                        _count("trial_conversions"),
                        _count("trial_calls"))
        ok20 = (f2 == f2b and f3 == f2
                and counts_before == (2, 3, 2, 0)
                and counts_after == counts_before)
        record("AC-CVR20", ok20,
               "stack2 four reads re-read self-identical, then"
               " closed and reopened as stack3 on the same db;"
               " all four reads (oct windowed capped / default"
               " capped / %s windowed capped / default bare)"
               " are pairwise byte-identical across the two"
               " instances - zero cross-instance drift; final"
               " four-table counts pinned %s"
               " (plans/grants/conversions/calls)"
               % (NEW_WIN, counts_after))

        # -- AC-CVR21 pure-read + determinism + hygiene -------
        src = inspect.getsource(
            T.FreeTrialFace.conversion_funnel_board)
        ok21 = not any(b in src for b in BANNED_WRITES)
        dumps = []
        for args in ((), (OLD_WIN,), (NEW_WIN,),
                     (None, 1), (OLD_WIN, 1), (NEW_WIN, 1)):
            env1 = ft.conversion_funnel_board(*args)
            env2 = ft.conversion_funnel_board(*args)
            dumps.append((json.dumps(env1, sort_keys=True),
                          json.dumps(env2, sort_keys=True)))
        ok21 = (ok21
                and all(a == b for (a, b) in dumps)
                and (_count("trial_plans"),
                     _count("trial_grants"),
                     _count("trial_conversions"),
                     _count("trial_calls")) == counts_after)
        with open(os.path.join(BASE, "freetrial.py"),
                  "rb") as h3:
            ok21 = ok21 and (hashlib.sha256(
                h3.read()).hexdigest() == face_sha)
        with open(os.path.join(BASE, "config.json"),
                  "rb") as h4:
            ok21 = ok21 and (hashlib.sha256(
                h4.read()).hexdigest() == cfg_sha)
        with open(os.path.abspath(__file__), "rb") as h5:
            self_bytes = h5.read()
        ok21 = (ok21 and all(b < 128 for b in self_bytes)
               and all(b < 128 for b in face_bytes))
        imports = [ln.strip() for ln in
                   self_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok21 = (ok21
                and not any(lib in ln for ln in imports
                           for lib in NET_LIBS))
        reg_path = os.path.join(os.path.dirname(BASE),
                                "reconcile_all.py")
        with open(reg_path, "r", encoding="utf-8") as h6:
            reg_text = h6.read()
        ok21 = (ok21
                and "ledger-freetrial-funnelpersist" in reg_text
                and "test_freetrial_funnelpersist.py"
                in reg_text
                and len(RESULTS) + 1 == EXPECTED)
        T._now_utc = real_now
        ok21 = ok21 and (T._now_utc() != clock.now_utc())
        record("AC-CVR21", ok21,
               "conversion_funnel_board source free of"
               " data-changing statements; four-table counts"
               " unchanged across the six-arg double-read"
               " battery; freetrial.py + config.json sha256"
               " stable across the whole run (zero product"
               " bytes - pin-only suite); suite + face sources"
               " pure ASCII with network-free import lines"
               " (%d imports); SUITES registration row present"
               " (ledger-freetrial-funnelpersist, criteria %d);"
               " frozen clock restored with probe"
               % (len(imports), EXPECTED))

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
