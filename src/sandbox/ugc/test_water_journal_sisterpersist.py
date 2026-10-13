"""Acceptance suite: water journal three-sister read faces
(kind_tally / monthly_flow / cell_totals) windowed-read
cross-restart persistence example (BigDomain R1910 tech-queue
FIFO head claim; seed = the R1905 reseed - the window params
(R1807 AC-MW family), the roll law (R1864 AC-WMR family) and
the board persist example (R1905 AC-JL8..AC-JL14) are in-book
while the three sister aggregation faces (R1801 / R1802 /
R1805) had no pinned cross-instance restart example: R1800
AC-WJ6 pins the core whole-board restart face only). This
suite pins the three read shapes per sister (default / October
explicit window / empty-month honest-empty) across
WaterJournalFace close -> new instance same-db reopen, then
the November recompute + October freeze + third-instance
sequential identity.

Asserts the pre-registered criteria AC-KT8..AC-KT10,
AC-MF8..AC-MF10, AC-CT8..AC-CT10 and AC-MW6..AC-MW8 from the
R1910 claim line in state/queue/tech.md (criteria were
registered before this code existed; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Claim rulings (three, registered in the tech.md claim line):
1. restart carrier = WaterJournalFace close then a fresh
   instance on the same db path with the same disclaimer
   (independent sqlite single-writer face; instance-level
   restart; zero cross-file dependencies).
2. world construction = frozen-clock real record() path
   (zero fixture injection): six October windows across five
   kinds, then the clock advances +23d and two November
   windows land with fresh (kind, delta) combinations.
3. snapshot set = three read shapes per sister plus the
   cross-face agreements (KT total == MF total windows,
   CT total == MF net_delta over the same set, composition
   law CT total == noise.total + review.suspended cells;
   verdicted cells keep their own keys out of the envelope
   total, R1785 law); every cross-restart comparison walks
   dumps(sort_keys=True) byte equality.

Zero product bytes change: the persistence semantics already
live in the three faces; this suite only pins them
(suite-only round). This source stays pure ASCII per the
encoding discipline.

Usage: python test_water_journal_sisterpersist.py
"""

import datetime
import hashlib
import inspect
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import water_journal as W             # noqa: E402 (R1800 face under test)

RESULTS = []
EXPECTED = 12

DISCLAIMER = ("sandbox stand-in disclaimer: non-advisory "
              "observable water ledger")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"
EMPTY_WIN = "2026-12"
BAD_WIN = "2026-13"

WRITE_KEYWORDS = ("INSERT INTO", "REPLACE INTO", "UPDATE ",
                  "DELETE FROM")
NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")

KT_DEF_KEYS = {"kind_tally", "total", "ai_generated",
               "disclaimer", "persistent"}
MF_DEF_KEYS = {"monthly_flow", "total", "net_delta",
               "ai_generated", "disclaimer", "persistent"}
CT_DEF_KEYS = {"cell_totals", "total", "ai_generated",
               "disclaimer", "persistent"}


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


def tri(f):
    """The three read shapes of one sister face: default,
    October explicit window, empty-month honest-empty."""
    return (dumps(f()), dumps(f(window=OLD_WIN)),
            dumps(f(window=EMPTY_WIN)))


def main():
    tmp = tempfile.mkdtemp(prefix="water-sisterpersist-")
    with open(os.path.join(BASE, "water_journal.py"), "rb") as h:
        face_bytes = h.read()
    face_sha = hashlib.sha256(face_bytes).hexdigest()
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as h:
        cfg_bytes = h.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    db_path = os.path.join(tmp, "water_journal.db")

    face = W.WaterJournalFace(db_path, DISCLAIMER)

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
            face.record(kind, {"pool_water_delta": delta,
                               "total_delta": total})

        # ---- AC-KT8: kind_tally pre-close snapshot -----------
        kt_default = face.kind_tally()
        kt_oct = face.kind_tally(window=OLD_WIN)
        kt_empty = face.kind_tally(window=EMPTY_WIN)
        s_kt_def, s_kt_oct, s_kt_empty = (
            dumps(kt_default), dumps(kt_oct), dumps(kt_empty))
        grid = {"batch": 1, "drain": 1, "ingest": 1,
                "submit": 2, "verdict": 1}
        kt8_ok = (
            kt_default["kind_tally"] == grid
            and kt_default["total"] == 6
            and kt_oct["kind_tally"] == grid
            and kt_oct["total"] == 6
            and set(kt_default) == KT_DEF_KEYS
            and set(kt_oct) == KT_DEF_KEYS | {"window"}
            and kt_oct["window"] == OLD_WIN
            and all(e["ai_generated"] == 0
                    and e["disclaimer"] == DISCLAIMER
                    and e["persistent"] is True
                    for e in (kt_default, kt_oct, kt_empty))
            and kt_default["total"]
            == sum(kt_default["kind_tally"].values())
            and dumps(face.kind_tally()) == s_kt_def
            and dumps(face.kind_tally(window=OLD_WIN))
            == s_kt_oct)
        record("AC-KT8", kt8_ok,
               "October anchor (6 windows, frozen-clock real"
               " record() path): kind_tally dense five-kind grid"
               " pinned %s total=%d; default keys %d exact,"
               " window read keys %d exact with window echo"
               " '%s'; total==sum-of-cells; compliance"
               " three-piece resident; same-param double reads"
               " byte-identical"
               % (grid, kt_default["total"], len(KT_DEF_KEYS),
                  len(KT_DEF_KEYS | {"window"}), kt_oct["window"]))

        # ---- AC-MF8: monthly_flow pre-close snapshot --------
        mf_default = face.monthly_flow()
        mf_oct = face.monthly_flow(window=OLD_WIN)
        mf_empty = face.monthly_flow(window=EMPTY_WIN)
        s_mf_def, s_mf_oct, s_mf_empty = (
            dumps(mf_default), dumps(mf_oct), dumps(mf_empty))
        oct_row = {"month": OLD_WIN, "windows": 6,
                   "total_delta": 4}
        mf8_ok = (
            mf_default["monthly_flow"] == [oct_row]
            and mf_oct["monthly_flow"] == [oct_row]
            and dumps(mf_oct["monthly_flow"])
            == dumps(mf_default["monthly_flow"])
            and mf_default["total"] == 6
            and mf_default["net_delta"] == 4
            and set(mf_default) == MF_DEF_KEYS
            and set(mf_oct) == MF_DEF_KEYS | {"window"}
            and mf_oct["window"] == OLD_WIN
            and all(set(r) == {"month", "windows",
                               "total_delta"}
                    for r in mf_default["monthly_flow"])
            and mf_default["total"] == sum(
                r["windows"] for r in mf_default["monthly_flow"])
            and mf_default["net_delta"] == sum(
                r["total_delta"]
                for r in mf_default["monthly_flow"])
            and mf_empty["monthly_flow"] == []
            and mf_empty["total"] == 0
            and mf_empty["net_delta"] == 0
            and mf_empty["window"] == EMPTY_WIN
            and dumps(face.monthly_flow()) == s_mf_def)
        record("AC-MF8", mf8_ok,
               "monthly_flow pre-close: default rows exactly"
               " [%s] with total==%d==sum-windows and"
               " net_delta==%d==sum-total_delta; row keys"
               " exact {month,windows,total_delta}; October"
               " window read == the same single row; empty"
               " month %s reads honest empty (rows=[],"
               " total=0, net_delta=0); default keys %d"
               " exact; same-param double read byte-identical"
               % (oct_row, mf_default["total"],
                  mf_default["net_delta"], EMPTY_WIN,
                  len(MF_DEF_KEYS)))

        # ---- AC-CT8: cell_totals pre-close snapshot ---------
        ct_default = face.cell_totals()
        ct_oct = face.cell_totals(window=OLD_WIN)
        ct_empty = face.cell_totals(window=EMPTY_WIN)
        s_ct_def, s_ct_oct, s_ct_empty = (
            dumps(ct_default), dumps(ct_oct), dumps(ct_empty))
        cells = {"noise.by_reason.fw": 1, "noise.total": 3,
                 "review.suspended": 1,
                 "review.verdicted.pass": 1}
        ct8_ok = (
            ct_default["cell_totals"] == cells
            and ct_oct["cell_totals"] == cells
            and ct_default["total"] == 4
            and ct_oct["total"] == 4
            and list(ct_default["cell_totals"])
            == sorted(ct_default["cell_totals"])
            and set(ct_default) == CT_DEF_KEYS
            and set(ct_oct) == CT_DEF_KEYS | {"window"}
            and ct_oct["window"] == OLD_WIN
            and ct_default["total"]
            == ct_default["cell_totals"]["noise.total"]
            + ct_default["cell_totals"]["review.suspended"]
            and ct_default["total"] == mf_default["net_delta"]
            and ct_empty["cell_totals"] == {}
            and ct_empty["total"] == 0
            and ct_empty["window"] == EMPTY_WIN
            and dumps(face.cell_totals()) == s_ct_def)
        record("AC-CT8", ct8_ok,
               "cell_totals pre-close: cells pinned %s"
               " (keys ascending), total=%d; composition law"
               " total==noise.total(%d)+review.suspended(%d);"
               " verdicted cells keep their own keys out of the"
               " envelope total (R1785); cross-face CT total=="
               "MF net_delta (%d==%d); empty month %s honest"
               " empty cells {} total=0; default keys %d exact;"
               " same-param double read byte-identical"
               % (cells, ct_default["total"],
                  ct_default["cell_totals"]["noise.total"],
                  ct_default["cell_totals"]["review.suspended"],
                  ct_default["total"], mf_default["net_delta"],
                  EMPTY_WIN, len(CT_DEF_KEYS)))

        # ---- AC-MW6: three-sister window gate trio ----------
        n_pre = conn_count(db_path)
        gate_hits = []
        for f in (face.kind_tally, face.monthly_flow,
                  face.cell_totals):
            try:
                f(window=BAD_WIN)
                gate_hits.append("NO-RAISE")
            except ValueError as exc:
                gate_hits.append(
                    W.E_WJ_BAD_WINDOW in str(exc)
                    and "raised-with-code")
        n_post = conn_count(db_path)
        empty_shapes_ok = (
            kt_empty["kind_tally"]
            == {"batch": 0, "drain": 0, "ingest": 0,
                "submit": 0, "verdict": 0}
            and kt_empty["total"] == 0
            and mf_empty["monthly_flow"] == []
            and ct_empty["cell_totals"] == {}
            and kt_empty["window"] == EMPTY_WIN
            and mf_empty["window"] == EMPTY_WIN
            and ct_empty["window"] == EMPTY_WIN)
        mw6_ok = (gate_hits
                  == ["raised-with-code"] * 3
                  and n_pre == n_post == 6
                  and empty_shapes_ok)
        record("AC-MW6", mw6_ok,
               "window gate trio: malformed window '%s' rejected"
               " by all three sisters with the same code"
               " %s and zero rows touched (count %d==%d);"
               " window echo key byte-exact on every windowed"
               " read of all three faces; empty-month honest"
               " shapes cross-verified (KT dense all-zero grid"
               " total=0 / MF empty row list / CT empty cells)"
               % (BAD_WIN, W.E_WJ_BAD_WINDOW, n_pre, n_post))

        # ---- AC-KT9/MF9/CT9: cross-restart identity ----------
        face.close()
        face2 = W.WaterJournalFace(db_path, DISCLAIMER)
        kt9_ok = (dumps(face2.kind_tally()) == s_kt_def
                  and dumps(face2.kind_tally(window=OLD_WIN))
                  == s_kt_oct
                  and dumps(face2.kind_tally(window=EMPTY_WIN))
                  == s_kt_empty
                  and dumps(face2.kind_tally(
                      window=OLD_WIN)) == s_kt_oct)
        record("AC-KT9", kt9_ok,
               "kind_tally cross-restart: face.close() -> fresh"
               " instance on the same db path replays the"
               " default / October / empty reads byte-identical"
               " to the pre-close snapshots (zero in-memory"
               " drift in the derived face)")
        mf9_ok = (dumps(face2.monthly_flow()) == s_mf_def
                  and dumps(face2.monthly_flow(window=OLD_WIN))
                  == s_mf_oct
                  and dumps(face2.monthly_flow(
                      window=EMPTY_WIN)) == s_mf_empty)
        record("AC-MF9", mf9_ok,
               "monthly_flow cross-restart: all three read"
               " shapes replay byte-identical from the fresh"
               " instance (rows, total and net_delta intact)")
        ct9_ok = (dumps(face2.cell_totals()) == s_ct_def
                  and dumps(face2.cell_totals(window=OLD_WIN))
                  == s_ct_oct
                  and dumps(face2.cell_totals(window=EMPTY_WIN))
                  == s_ct_empty)
        record("AC-CT9", ct9_ok,
               "cell_totals cross-restart: all three read"
               " shapes replay byte-identical from the fresh"
               " instance (cells, composition total intact)")

        # ---- November injection on the fresh instance -------
        clock.advance(23 * 86400)
        face2.record("drain", {
            "pool_water_delta": {"noise.total": 1,
                                 "noise.by_reason.emoji_only": 1},
            "total_delta": 1})
        clock.advance(9)
        face2.record("verdict", {
            "pool_water_delta": {"review.suspended": -1,
                                 "review.verdicted.risky": 1},
            "total_delta": -1})

        # ---- AC-KT10: kind_tally recompute + freeze ---------
        kt_def2 = face2.kind_tally()
        kt_nov = face2.kind_tally(window=NEW_WIN)
        kt_oct2 = face2.kind_tally(window=OLD_WIN)
        grid_nov = {"batch": 0, "drain": 1, "ingest": 0,
                    "submit": 0, "verdict": 1}
        kt10_ok = (
            kt_def2["total"] == 8
            and kt_def2["kind_tally"] == {"batch": 1,
                                          "drain": 2, "ingest": 1,
                                          "submit": 2,
                                          "verdict": 2}
            and dumps(kt_def2) != s_kt_def
            and kt_nov["kind_tally"] == grid_nov
            and kt_nov["total"] == 2
            and kt_nov["window"] == NEW_WIN
            and dumps(kt_oct2) == s_kt_oct)
        record("AC-KT10", kt10_ok,
               "kind_tally recompute + freeze: frozen clock +23d"
               " then two real November windows (drain noise+1,"
               " verdict risky -1 - fresh combinations) via the"
               " record() path on the fresh instance: default"
               " read recomputes total 6->8 and byte-differs from"
               " the pre-close default snapshot (zero cache);"
               " November window read active %s total=%d; the"
               " October window read stays byte-frozen to the"
               " pre-close snapshot (record-time rows immutable,"
               " zero permeation)"
               % (grid_nov, kt_nov["total"]))

        # ---- AC-MF10: monthly_flow recompute + freeze -------
        mf_def2 = face2.monthly_flow()
        mf_nov = face2.monthly_flow(window=NEW_WIN)
        mf_oct2 = face2.monthly_flow(window=OLD_WIN)
        nov_row = {"month": NEW_WIN, "windows": 2,
                   "total_delta": 0}
        mf10_ok = (
            mf_def2["monthly_flow"]
            == [oct_row, nov_row]
            and mf_def2["total"] == 8
            and mf_def2["net_delta"] == 4
            and dumps(mf_def2) != s_mf_def
            and mf_nov["monthly_flow"] == [nov_row]
            and mf_nov["total"] == 2
            and mf_nov["net_delta"] == 0
            and mf_nov["window"] == NEW_WIN
            and dumps(mf_oct2) == s_mf_oct
            and mf_oct2["monthly_flow"][0] == oct_row)
        record("AC-MF10", mf10_ok,
               "monthly_flow recompute + freeze: default rows"
               " now two months (October row values frozen"
               " %s + November row %s), total 6->8,"
               " net_delta 4 stable; the October window read"
               " stays byte-frozen; the November window read =="
               " the November single row; telescope oct 6 +"
               " nov 2 == default total 8" % (oct_row, nov_row))

        # ---- AC-CT10: cell_totals recompute + freeze ---------
        ct_def2 = face2.cell_totals()
        ct_nov = face2.cell_totals(window=NEW_WIN)
        ct_oct2 = face2.cell_totals(window=OLD_WIN)
        cells2 = {"noise.by_reason.emoji_only": 1,
                  "noise.by_reason.fw": 1, "noise.total": 4,
                  "review.suspended": 0,
                  "review.verdicted.pass": 1,
                  "review.verdicted.risky": 1}
        ct10_ok = (
            ct_def2["cell_totals"] == cells2
            and ct_def2["total"] == 4
            and dumps(ct_def2) != s_ct_def
            and ct_nov["cell_totals"]
            == {"noise.by_reason.emoji_only": 1,
                "noise.total": 1, "review.suspended": -1,
                "review.verdicted.risky": 1}
            and ct_nov["total"] == 0
            and ct_nov["total"]
            == ct_nov["cell_totals"]["noise.total"]
            + ct_nov["cell_totals"]["review.suspended"]
            and dumps(ct_oct2) == s_ct_oct
            and kt_def2["total"] == mf_def2["total"] == 8
            and ct_def2["total"] == mf_def2["net_delta"] == 4
            and ct_def2["total"]
            == ct_def2["cell_totals"]["noise.total"]
            + ct_def2["cell_totals"]["review.suspended"])
        record("AC-CT10", ct10_ok,
               "cell_totals recompute + freeze: default cells"
               " recompute to %s (fresh cells"
               " noise.by_reason.emoji_only /"
               " review.verdicted.risky merged in) and"
               " byte-differ from the pre-close default"
               " (zero cache); the October window read stays"
               " byte-frozen; cross-face on the new set: KT"
               " total==MF total windows==8 and CT total==MF"
               " net_delta==4; composition law holds on the"
               " November set (total 0 == noise.total 1 +"
               " review.suspended -1) and on the default set"
               " (4 == 4 + 0)" % cells2)

        # ---- AC-MW7: third instance sequential identity -----
        st = {}
        for name, fn in (("kt", face2.kind_tally),
                         ("mf", face2.monthly_flow),
                         ("ct", face2.cell_totals)):
            st[name] = (dumps(fn()),
                        dumps(fn(window=OLD_WIN)),
                        dumps(fn(window=NEW_WIN)))
        face2.close()
        face3 = W.WaterJournalFace(db_path, DISCLAIMER)
        f3 = {}
        for name, fn in (("kt", face3.kind_tally),
                         ("mf", face3.monthly_flow),
                         ("ct", face3.cell_totals)):
            f3[name] = (dumps(fn()),
                        dumps(fn(window=OLD_WIN)),
                        dumps(fn(window=NEW_WIN)))
        mw7_ok = (f3 == st
                  and dumps(face3.kind_tally(
                      window=OLD_WIN)) == s_kt_oct
                  and dumps(face3.monthly_flow(
                      window=OLD_WIN)) == s_mf_oct
                  and dumps(face3.cell_totals(
                      window=OLD_WIN)) == s_ct_oct
                  and face3.kind_tally()["total"] == 8
                  and face3.monthly_flow()["total"] == 8
                  and face3.cell_totals()["total"] == 4)
        record("AC-MW7", mw7_ok,
               "third instance triple-open on the same db: the"
               " three sisters' default / October / November"
               " reads replay the instance-2 captured state"
               " pairwise byte-identical (nine reads, zero"
               " drift), and the October windowed reads still"
               " equal the ORIGINAL pre-close snapshots"
               " (restart x new-data double hijack never"
               " scratches the old window; totals 8/8/4)")

        # ---- AC-MW8: pure-read law + hygiene ----------------
        n_a = conn_count(db_path)
        shapes = []
        for fn in (face3.kind_tally, face3.monthly_flow,
                   face3.cell_totals):
            shapes.extend([
                dumps(fn()), dumps(fn(window=OLD_WIN)),
                dumps(fn(window=NEW_WIN)),
                dumps(fn(window=EMPTY_WIN))])
        shapes2 = []
        for fn in (face3.kind_tally, face3.monthly_flow,
                   face3.cell_totals):
            shapes2.extend([
                dumps(fn()), dumps(fn(window=OLD_WIN)),
                dumps(fn(window=NEW_WIN)),
                dumps(fn(window=EMPTY_WIN))])
        n_b = conn_count(db_path)
        battery_ok = shapes == shapes2
        src_ok = all(
            not any(k in inspect.getsource(
                getattr(W.WaterJournalFace, m))
                for k in WRITE_KEYWORDS)
            for m in ("kind_tally", "monthly_flow",
                      "cell_totals"))
        with open(os.path.join(BASE, "water_journal.py"),
                  "rb") as h:
            ok_h = (hashlib.sha256(h.read()).hexdigest()
                    == face_sha)
        with open(cfg_path, "rb") as h:
            ok_h = ok_h and (hashlib.sha256(
                h.read()).hexdigest() == cfg_sha)
        ok_h = ok_h and all(b < 128 for b in face_bytes)
        face_imports = [ln.strip() for ln in
                        face_bytes.decode("ascii").splitlines()
                        if ln.strip().startswith("import ")]
        ok_h = ok_h and not any(
            lib in ln for ln in face_imports for lib in NET_LIBS)
        suite_path = os.path.abspath(__file__)
        with open(suite_path, "rb") as h:
            suite_bytes = h.read()
        ok_h = ok_h and all(b < 128 for b in suite_bytes)
        suite_imports = [ln.strip() for ln in
                         suite_bytes.decode("ascii").splitlines()
                         if ln.strip().startswith("import ")
                         or ln.strip().startswith("from ")]
        ok_h = ok_h and not any(
            lib in ln for ln in suite_imports for lib in NET_LIBS)
        W._utc_now_iso = real_now
        probe_ok = (W._utc_now_iso is real_now
                    and W._utc_now_iso() != clock.now_iso())
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as h:
            reg_src = h.read()
        reg_ok = ('"ugc-water-sisterpersist"' in reg_src
                  and "test_water_journal_sisterpersist.py"
                  in reg_src)
        record("AC-MW8",
               battery_ok and n_a == n_b == 8 and src_ok
               and ok_h and probe_ok and reg_ok
               and len(RESULTS) + 1 == EXPECTED,
               "pure-read law: the 12-shape read battery"
               " (three sisters x default/oct/nov/empty)"
               " double-read byte-identical with"
               " water_windows=%d constant before/after;"
               " kind_tally / monthly_flow / cell_totals method"
               " sources free of data-changing statements;"
               " water_journal.py sha256 stable and shipped"
               " config.json sha256 stable (zero product"
               " bytes); face + suite sources pure ASCII with"
               " network-free import lines (%d face imports);"
               " frozen-clock restore probe = %s; SUITES"
               " registration row present; criteria drift"
               " self-check %d+1==%d"
               % (n_b, len(face_imports), probe_ok,
                  len(RESULTS), EXPECTED))

        fail = sum(1 for _, ok in RESULTS if not ok)
        print("SUITE %s %d/%d exit=%d"
              % ("PASS" if fail == 0 else "FAIL",
                 len(RESULTS) - fail, len(RESULTS),
                 0 if fail == 0 else 1), flush=True)
        face3.close()
        return 0 if fail == 0 else 1
    finally:
        W._utc_now_iso = real_now
        for handle in (face, face2, face3):
            if handle is not None:
                try:
                    handle.close()
                except Exception:
                    pass


def conn_count(db_path):
    """Independent read-only count: the row-count truth the
    pure-read law pins against (never a second writer)."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
