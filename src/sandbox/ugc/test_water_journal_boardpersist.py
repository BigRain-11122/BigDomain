"""Acceptance suite: water journal journal_board cap-window
combined read cross-restart persistence example (BigDomain R1905
tech-queue FIFO head claim; seed = the R1900 reseed - the read-cap
x month-window orthogonal reads (R1812 AC-JL1..JL7) and the
month-window filter (R1807 AC-MW family) are in-book while the
cap-window combined-read derivation purity across an instance
restart had no pinned example: R1800 AC-WJ6 pins the core
whole-board restart face only). This suite pins the four read
shapes (capped-combined / default / bare-window / default-cap)
across WaterJournalFace close -> new instance same-db reopen.

Asserts the pre-registered criteria AC-JL8..AC-JL14 from the
R1905 claim line in state/queue/tech.md (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Claim rulings (three, registered in the tech.md claim line):
1. restart carrier = WaterJournalFace close then a fresh instance
   on the same db path with the same disclaimer (independent
   sqlite single-writer face; instance-level restart; zero
   cross-file dependencies).
2. world construction = frozen-clock real record() path
   (water_journal._utc_now_iso patched onto a deterministic
   holder, restored in finally - the R1864 roll-suite law; zero
   fixture injection): six October windows across five kinds,
   then the clock advances +23d and two November windows land
   with fresh (kind, delta) combinations.
3. snapshot quadruple = oct capped-combined read
   journal_board(window='2026-10', limit=2) + default
   whole-board read + oct bare-window read + default capped read;
   every cross-restart comparison walks dumps(sort_keys=True)
   byte equality.

Zero product bytes change: the persistence semantics already
live in the journal_board face; this suite only pins them
(suite-only round). This source stays pure ASCII per the
encoding discipline.

Usage: python test_water_journal_boardpersist.py
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

import water_journal as W             # noqa: E402 (R1800 face under test)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: non-advisory "
              "observable water ledger")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"

WRITE_KEYWORDS = ("INSERT INTO", "REPLACE INTO", "UPDATE ",
                  "DELETE FROM")
NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")


class _FrozenClock(object):
    """Deterministic UTC clock holder: the water_journal module
    _utc_now_iso is patched onto this holder so record stamps
    move only when the suite advances the clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_iso(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def mirror_tail(conn, win, limit):
    """Mirror-SQL law (R1812): the capped read's ascending tail
    window == DESC/DESC LIMIT then reversed, full row dicts."""
    cur = conn.execute(
        "SELECT window_id, kind, delta, total_delta, ts_utc"
        " FROM water_windows WHERE substr(ts_utc, 1, 7) = ?"
        " ORDER BY ts_utc DESC, window_id DESC LIMIT ?",
        (win, limit))
    fetched = list(cur)
    fetched.reverse()
    rows = []
    for window_id, kind, delta, total_delta, ts_utc in fetched:
        rows.append({"window_id": window_id, "kind": kind,
                     "delta": json.loads(delta),
                     "total_delta": total_delta, "ts_utc": ts_utc})
    return rows


def main():
    tmp = tempfile.mkdtemp(prefix="water-boardpersist-")
    with open(os.path.join(BASE, "water_journal.py"), "rb") as h:
        face_bytes = h.read()
    face_sha = hashlib.sha256(face_bytes).hexdigest()
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as h:
        cfg_bytes = h.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    db_path = os.path.join(tmp, "water_journal.db")

    face = W.WaterJournalFace(db_path, DISCLAIMER)
    conn = sqlite3.connect(db_path)

    def _count():
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]

    def _win_count(win):
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows WHERE"
            " substr(ts_utc, 1, 7) = ?", (win,)).fetchone()[0]

    oct_ids = []
    nov_ids = []
    clock = _FrozenClock()
    real_now = W._utc_now_iso
    face2 = None
    face3 = None
    try:
        W._utc_now_iso = clock.now_iso

        # -- October anchor world: 6 windows, real record() path
        world = [
            ("ingest", {"noise.total": 1,
                        "noise.by_reason.fw": 1}, 1),
            ("submit", {"review.suspended": 1}, 1),
            ("batch", {"noise.total": 2}, 2),
            ("drain", {}, 0),
            ("verdict", {"review.suspended": -1,
                         "review.verdicted.pass": 1}, -1),
            ("submit", {"review.suspended": 1}, 1),
        ]
        for i, (kind, delta, total) in enumerate(world):
            if i:
                clock.advance(7)
            rec = face.record(kind, {"pool_water_delta": delta,
                                     "total_delta": total})
            oct_ids.append(rec["window_id"])

        # ---- AC-JL8: October anchor + pre-close quadruple -----
        oct_sql = _win_count(OLD_WIN)
        ts_stamps = [r[0] for r in conn.execute(
            "SELECT ts_utc FROM water_windows"
            " ORDER BY ts_utc, window_id")]
        stamp_ok = (oct_sql == 6 and len(ts_stamps) == 6
                    and all(a < b for a, b in
                            zip(ts_stamps, ts_stamps[1:])))
        oct_cap = face.journal_board(window=OLD_WIN, limit=2)
        default_read = face.journal_board()
        oct_bare = face.journal_board(window=OLD_WIN)
        default_cap = face.journal_board(limit=2)
        s_oct_cap = dumps(oct_cap)
        s_default = dumps(default_read)
        s_oct_bare = dumps(oct_bare)
        s_default_cap = dumps(default_cap)
        def_keys = {"journal_board", "total", "ai_generated",
                    "disclaimer", "persistent"}
        cap_keys = def_keys | {"limit", "returned", "truncated",
                               "window"}
        bare_keys = def_keys | {"window"}
        dcap_keys = def_keys | {"limit", "returned", "truncated"}
        keys_ok = (set(oct_cap) == cap_keys
                   and set(default_read) == def_keys
                   and set(oct_bare) == bare_keys
                   and set(default_cap) == dcap_keys)
        comp_ok = all(e["ai_generated"] == 0
                      and e["disclaimer"] == DISCLAIMER
                      and e["persistent"] is True
                      for e in (oct_cap, default_read, oct_bare,
                                default_cap))
        mirror = mirror_tail(conn, OLD_WIN, 2)
        mirror_ok = (oct_cap["journal_board"] == mirror
                     and [r["window_id"]
                          for r in oct_cap["journal_board"]]
                     == oct_ids[-2:]
                     and oct_cap["limit"] == 2
                     and oct_cap["total"] == 6
                     and oct_cap["returned"] == 2
                     and oct_cap["truncated"] is True
                     and oct_cap["window"] == OLD_WIN
                     and all(r["ts_utc"].startswith(OLD_WIN)
                             for r
                             in oct_cap["journal_board"]))
        bare_ok = (dumps({k: v for k, v in default_read.items()})
                   == dumps({k: v for k, v in oct_bare.items()
                             if k != "window"})
                   and oct_bare["total"] == 6
                   and [r["window_id"]
                        for r in oct_bare["journal_board"]]
                   == oct_ids
                   and default_read["total"] == 6
                   and len(default_read["journal_board"]) == 6
                   and all(r["ts_utc"].startswith(OLD_WIN)
                           for r in
                           default_read["journal_board"]))
        dcap_ok = (default_cap["limit"] == 2
                   and default_cap["total"] == 6
                   and default_cap["returned"] == 2
                   and default_cap["truncated"] is True
                   and [r["window_id"]
                        for r in default_cap["journal_board"]]
                   == oct_ids[-2:])
        self_ok = (dumps(face.journal_board(
            window=OLD_WIN, limit=2)) == s_oct_cap
            and dumps(face.journal_board()) == s_default)
        record("AC-JL8",
               stamp_ok and keys_ok and comp_ok and mirror_ok
               and bare_ok and dcap_ok and self_ok,
               "October anchor: 6 windows via the frozen-clock"
               " record() path (SQL %s prefix count %d, ts"
               " strictly ascending); quadruple key sets"
               " exact-pinned (capped-combined %d keys / default"
               " %d / bare-window %d / default-cap %d);"
               " capped-combined tail rows == mirror-SQL rows"
               " (full row dicts, ids %s), overflow block"
               " {limit=2,total=6,returned=2,truncated=True};"
               " compliance three-piece resident on all four"
               " reads; bare-window read == default read minus"
               " the window key; same-param double reads"
               " byte-identical"
               % (OLD_WIN, oct_sql, len(cap_keys), len(def_keys),
                  len(bare_keys), len(dcap_keys), oct_ids[-2:]))

        # ---- AC-JL9: cross-restart capped-combined identity ---
        face.close()
        face2 = W.WaterJournalFace(db_path, DISCLAIMER)
        r_oct_cap_2 = face2.journal_board(window=OLD_WIN, limit=2)
        restart_ok = (dumps(r_oct_cap_2) == s_oct_cap
                      and dumps(face2.journal_board(
                          window=OLD_WIN, limit=2)) == s_oct_cap
                      and r_oct_cap_2["total"] == 6
                      and r_oct_cap_2["truncated"] is True)
        record("AC-JL9", restart_ok,
               "face.close() -> fresh instance on the same db"
               " path with the same disclaimer: the October"
               " capped-combined read replays byte-identical to"
               " the pre-close snapshot (%d keys, tail ids %s,"
               " total=%d, truncated=%s); the same-param second"
               " read is self-identical - the derived face"
               " carries zero in-memory drift across the restart"
               % (len(r_oct_cap_2),
                  [r["window_id"]
                   for r in r_oct_cap_2["journal_board"]],
                  r_oct_cap_2["total"],
                  r_oct_cap_2["truncated"]))

        # ---- AC-JL10: three companion reads restored ----------
        r_default_2 = face2.journal_board()
        r_oct_bare_2 = face2.journal_board(window=OLD_WIN)
        r_default_cap_2 = face2.journal_board(limit=2)
        ok10 = (dumps(r_default_2) == s_default
                and dumps(r_oct_bare_2) == s_oct_bare
                and dumps(r_default_cap_2) == s_default_cap
                and set(r_default_2) == def_keys
                and set(r_oct_bare_2) == bare_keys
                and set(r_default_cap_2) == dcap_keys)
        record("AC-JL10", ok10,
               "default whole-board read, October bare-window"
               " read and default capped read all replay"
               " byte-identical from the fresh instance; key"
               " sets follow the read shape with zero drift"
               " (%d/%d/%d keys)"
               % (len(r_default_2), len(r_oct_bare_2),
                  len(r_default_cap_2)))

        # ---- AC-JL11: post-restart new-month recompute -------
        clock.advance(23 * 86400)
        rec7 = face2.record("drain", {
            "pool_water_delta": {"noise.total": 1,
                                 "noise.by_reason.emoji_only": 1},
            "total_delta": 1})
        clock.advance(9)
        rec8 = face2.record("verdict", {
            "pool_water_delta": {"review.suspended": -1,
                                 "review.verdicted.risky": 1},
            "total_delta": -1})
        nov_ids.extend([rec7["window_id"], rec8["window_id"]])
        nov_sql = _win_count(NEW_WIN)
        stamp_ok11 = (nov_sql == 2
                      and rec7["ts_utc"].startswith(NEW_WIN)
                      and rec8["ts_utc"].startswith(NEW_WIN)
                      and rec7["ts_utc"] < rec8["ts_utc"])
        d2 = face2.journal_board()
        recompute_ok = (d2["total"] == 8
                        and dumps(d2) != s_default
                        and [r["window_id"]
                             for r in d2["journal_board"][-2:]]
                        == nov_ids
                        and len(d2["journal_board"]) == 8)
        dcap2 = face2.journal_board(limit=2)
        dcap_ok11 = (dcap2["total"] == 8
                     and dcap2["returned"] == 2
                     and dcap2["truncated"] is True
                     and [r["window_id"]
                          for r in dcap2["journal_board"]]
                     == nov_ids)
        nov_cap = face2.journal_board(window=NEW_WIN, limit=2)
        nov_bare = face2.journal_board(window=NEW_WIN)
        nov_ok11 = (nov_cap["total"] == 2
                    and nov_cap["returned"] == 2
                    and nov_cap["truncated"] is False
                    and nov_cap["window"] == NEW_WIN
                    and nov_cap["journal_board"]
                    == mirror_tail(conn, NEW_WIN, 2)
                    and [r["window_id"]
                         for r in nov_cap["journal_board"]]
                    == nov_ids
                    and nov_bare["total"] == 2
                    and [r["window_id"]
                         for r in nov_bare["journal_board"]]
                    == nov_ids
                    and all(r["ts_utc"].startswith(NEW_WIN)
                            for r in nov_cap["journal_board"]))
        record("AC-JL11",
               stamp_ok11 and recompute_ok and dcap_ok11
               and nov_ok11,
               "frozen clock +23d then two real windows (drain"
               " noise+1, verdict risky -1 - fresh (kind,delta)"
               " combinations, SQL %s count %d): the default read"
               " recomputes total 6->8 and byte-differs from the"
               " pre-close default snapshot (zero cache); the"
               " default capped read tail drifts to the November"
               " rows {limit=2,total=8,returned=2,"
               "truncated=True}; the November capped-combined"
               " read is exactly full {total=2,returned=2,"
               "truncated=False} == mirror-SQL full rows, zero"
               " October leakage" % (NEW_WIN, nov_sql))

        # ---- AC-JL12: old-window freeze + immutable rows -----
        oc12 = face2.journal_board(window=OLD_WIN, limit=2)
        ob12 = face2.journal_board(window=OLD_WIN)
        freeze_ok = (dumps(oc12) == s_oct_cap
                     and dumps(ob12) == s_oct_bare
                     and oc12["total"] == 6
                     and [r["window_id"]
                          for r in oc12["journal_board"]]
                     == oct_ids[-2:])
        tele_ok = (_count() == 8
                   and oc12["total"] + nov_cap["total"]
                   == d2["total"] == 8
                   and all(r["ts_utc"].startswith(OLD_WIN)
                           for r in oc12["journal_board"]))
        record("AC-JL12", freeze_ok and tele_ok,
               "old-window zero penetration: the October"
               " capped-combined and bare-window reads stay"
               " byte-identical to the pre-close snapshots after"
               " the restart x new-data double exposure (tail"
               " ids %s frozen, total 6); telescope oct 6 +"
               " nov 2 == default 8 == table count - immutable"
               " record-time rows never lost" % oct_ids[-2:])

        # ---- AC-JL13: third instance sequential identity -----
        st_oct_cap = dumps(
            face2.journal_board(window=OLD_WIN, limit=2))
        st_default = dumps(face2.journal_board())
        st_nov_cap = dumps(
            face2.journal_board(window=NEW_WIN, limit=2))
        st_default_cap = dumps(face2.journal_board(limit=2))
        face2.close()
        face3 = W.WaterJournalFace(db_path, DISCLAIMER)
        f3_oct_cap = face3.journal_board(window=OLD_WIN, limit=2)
        f3_default = face3.journal_board()
        f3_nov_cap = face3.journal_board(window=NEW_WIN, limit=2)
        f3_default_cap = face3.journal_board(limit=2)
        ok13 = (dumps(f3_oct_cap) == st_oct_cap
                and dumps(f3_default) == st_default
                and dumps(f3_nov_cap) == st_nov_cap
                and dumps(f3_default_cap) == st_default_cap
                and dumps(f3_oct_cap) == s_oct_cap
                and dumps(face3.journal_board(
                    window=OLD_WIN, limit=2)) == dumps(f3_oct_cap)
                and f3_oct_cap["total"] == 6
                and f3_nov_cap["total"] == 2
                and f3_default["total"] == 8)
        record("AC-JL13", ok13,
               "third instance triple-open on the same db: four"
               " reads (oct capped-combined / default / nov"
               " capped-combined / default-cap) replay the"
               " instance-2 captured state pairwise"
               " byte-identical, the same-param re-read is"
               " self-identical, and the October capped-combined"
               " read still equals the pre-close original"
               " snapshot (restart x new-data double hijack,"
               " zero drift; totals 6/2/8)")

        # ---- AC-JL14: pure-read law + hygiene ----------------
        n_a = _count()
        shapes = [
            dumps(face3.journal_board()),
            dumps(face3.journal_board(window=OLD_WIN)),
            dumps(face3.journal_board(window=NEW_WIN)),
            dumps(face3.journal_board(limit=2)),
            dumps(face3.journal_board(window=OLD_WIN, limit=2)),
            dumps(face3.journal_board(window=NEW_WIN, limit=2)),
        ]
        battery_ok = (shapes == [
            dumps(face3.journal_board()),
            dumps(face3.journal_board(window=OLD_WIN)),
            dumps(face3.journal_board(window=NEW_WIN)),
            dumps(face3.journal_board(limit=2)),
            dumps(face3.journal_board(window=OLD_WIN, limit=2)),
            dumps(face3.journal_board(window=NEW_WIN, limit=2)),
        ])
        n_b = _count()
        src = inspect.getsource(W.WaterJournalFace.journal_board)
        src_clean = not any(k in src for k in WRITE_KEYWORDS)
        with open(os.path.join(BASE, "water_journal.py"),
                  "rb") as h:
            ok14 = (hashlib.sha256(h.read()).hexdigest()
                    == face_sha)
        with open(cfg_path, "rb") as h:
            ok14 = ok14 and (hashlib.sha256(
                h.read()).hexdigest() == cfg_sha)
        ok14 = ok14 and all(b < 128 for b in face_bytes)
        imports = [ln.strip() for ln in
                   face_bytes.decode("ascii").splitlines()
                   if ln.strip().startswith("import ")]
        ok14 = ok14 and not any(
            lib in ln for ln in imports for lib in NET_LIBS)
        suite_path = os.path.abspath(__file__)
        with open(suite_path, "rb") as h:
            suite_bytes = h.read()
        ok14 = ok14 and all(b < 128 for b in suite_bytes)
        suite_imports = [ln.strip() for ln in
                         suite_bytes.decode("ascii").splitlines()
                         if ln.strip().startswith("import ")
                         or ln.strip().startswith("from ")]
        ok14 = ok14 and not any(
            lib in ln for ln in suite_imports for lib in NET_LIBS)
        W._utc_now_iso = real_now
        probe_ok = (W._utc_now_iso is real_now
                    and W._utc_now_iso() != clock.now_iso())
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as h:
            reg_src = h.read()
        reg_ok = ('"ugc-water-journalboardpersist"' in reg_src
                  and "test_water_journal_boardpersist.py"
                  in reg_src)
        record("AC-JL14",
               battery_ok and n_a == n_b == 8 and src_clean
               and ok14 and probe_ok and reg_ok
               and len(RESULTS) + 1 == EXPECTED,
               "pure-read law: six read shapes double-read"
               " byte-identical with water_windows=%d constant"
               " before/after; journal_board method source free"
               " of data-changing statements; water_journal.py"
               " sha256 stable and shipped config.json sha256"
               " stable (zero product bytes); face + suite"
               " sources pure ASCII with network-free import"
               " lines (%d face imports); frozen-clock restore"
               " probe (function identity + real stamp differs"
               " from the frozen stamp) = %s; SUITES"
               " registration row present; criteria drift"
               " self-check %d+1==%d"
               % (n_b, len(imports), probe_ok,
                  len(RESULTS), EXPECTED))

        fail = sum(1 for _, ok in RESULTS if not ok)
        print("SUITE %s %d/%d exit=%d"
              % ("PASS" if fail == 0 else "FAIL",
                 len(RESULTS) - fail, len(RESULTS),
                 0 if fail == 0 else 1), flush=True)
        conn.close()
        face3.close()
        return 0 if fail == 0 else 1
    finally:
        W._utc_now_iso = real_now
        try:
            conn.close()
        except Exception:
            pass
        for handle in (face, face2, face3):
            if handle is not None:
                try:
                    handle.close()
                except Exception:
                    pass


if __name__ == "__main__":
    sys.exit(main())
