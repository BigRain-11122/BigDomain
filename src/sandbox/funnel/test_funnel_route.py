"""Acceptance suite for the funnel dispatch route distribution read face
(FUNNEL-LOOP v0.1, R2055).

Pre-registered criteria AC-FRT1..AC-FRT8 live in state/queue/tech.md
(the R2055 claim row) and were written BEFORE this suite existed
(honesty law). The gap under test: ring 2 reports the routes of ONE
run (the routes dict in the dispatch_leads return), and the rollup
envelope only counts dispatches per day - nothing reads the dispatches
table GROUPED BY ROUTE across runs, so the cross-round route
distribution (which six-domain route took how much of the pipeline,
plus the honest unrouted archive) has no read face at all.

World: two dispatched days over seven leads.

  D1: game lead, unrouted lead, quant lead
  D2: media lead, life lead, unrouted lead, platform lead

Lifetime: game 1, life 1, media 1, platform 1, quant 1, unrouted 2.

The library is exercised as shipped - this file changes nothing under
test. Pure ASCII source (coding law).
"""

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402

D1 = "2026-10-16"
D2 = "2026-10-17"
EMPTY_DAY = "2026-10-25"

LIFETIME = {
    "game": 1,
    "life": 1,
    "media": 1,
    "platform": 1,
    "quant": 1,
    "unrouted": 2,
}
WINDOW_D1 = {"game": 1, "quant": 1, "unrouted": 1}
WINDOW_D2 = {
    "life": 1,
    "media": 1,
    "platform": 1,
    "unrouted": 1,
}

D1_LEADS = [
    {"lead_id": "a1", "text": "game level demo"},
    {"lead_id": "a2", "text": "nothing matches here"},
    {"lead_id": "a3", "text": "quant factor etf"},
]
D2_LEADS = [
    {"lead_id": "b1", "text": "video clip script"},
    {"lead_id": "b2", "text": "resident persona story"},
    {"lead_id": "b3", "text": "no keyword at all"},
    {"lead_id": "b4", "text": "platform billing"},
]


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _dispatch_rows(db_path):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT * FROM dispatches ORDER BY lead_id").fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _count(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    finally:
        con.close()


def _manual_tally(db_path, day=None):
    con = sqlite3.connect(db_path)
    try:
        if day is None:
            rows = con.execute(
                "SELECT route, COUNT(*) FROM dispatches "
                "GROUP BY route ORDER BY route").fetchall()
        else:
            rows = con.execute(
                "SELECT route, COUNT(*) FROM dispatches WHERE day=? "
                "GROUP BY route ORDER BY route", (day,)).fetchall()
    finally:
        con.close()
    return {str(route): int(count) for route, count in rows}


def _world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    leads1 = _mk_inbox(root, "leads1", D1_LEADS)
    leads2 = _mk_inbox(root, "leads2", D2_LEADS)
    empty = _mk_inbox(root, "empty", [])
    flows = _mk_inbox(root, "flows", [])
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    face.run_daily(leads1, empty, flows, D1)
    face.run_daily(leads2, empty, flows, D2)
    face.close()
    return {"db": db, "root": root, "leads1": leads1, "leads2": leads2,
            "empty": empty, "flows": flows}


def _open(world):
    return fd.FunnelDaily(world["db"])


def _empty_world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    face.close()
    return {"db": db, "root": root}


# AC-FRT1: a fresh carrier is an honest empty face on both windows.
def case_frt1(tmp):
    world = _empty_world(tmp, "frt1")
    face = _open(world)
    try:
        lifetime = face.route_tally()
        windowed = face.route_tally(D1)
    finally:
        face.close()
    assert lifetime == {}, "AC-FRT1 lifetime %r" % lifetime
    assert windowed == {}, "AC-FRT1 window %r" % windowed


# AC-FRT2: lifetime distribution per route, sorted, matches manual SQL.
def case_frt2(tmp):
    world = _world(tmp, "frt2")
    face = _open(world)
    try:
        out = face.route_tally()
    finally:
        face.close()
    assert out == LIFETIME, "AC-FRT2 %r" % out
    assert list(out.keys()) == sorted(out.keys()), \
        "AC-FRT2 not sorted %r" % list(out.keys())
    assert out == _manual_tally(world["db"]), \
        "AC-FRT2 differs from manual SQL"


# AC-FRT3: day window law both ways plus an honest empty day.
def case_frt3(tmp):
    world = _world(tmp, "frt3")
    face = _open(world)
    try:
        day1 = face.route_tally(D1)
        day2 = face.route_tally(D2)
        empty = face.route_tally(EMPTY_DAY)
        lifetime = face.route_tally()
    finally:
        face.close()
    assert day1 == WINDOW_D1, "AC-FRT3 D1 %r" % day1
    assert day2 == WINDOW_D2, "AC-FRT3 D2 %r" % day2
    assert empty == {}, "AC-FRT3 empty day %r" % empty
    assert lifetime == LIFETIME, "AC-FRT3 lifetime %r" % lifetime
    assert "media" not in day1, "AC-FRT3 window leaked D2 rows"
    assert "quant" not in day2, "AC-FRT3 window leaked D1 rows"
    assert day1 == _manual_tally(world["db"], D1), \
        "AC-FRT3 D1 differs from manual SQL"


# AC-FRT4: unrouted stays its own bucket; an unknown route is kept.
def case_frt4(tmp):
    world = _world(tmp, "frt4")
    con = sqlite3.connect(world["db"])
    try:
        con.execute(
            "INSERT INTO dispatches (lead_id, day, route) VALUES (?,?,?)",
            ("z9", D1, "legacy-ghost"))
        con.commit()
    finally:
        con.close()
    face = _open(world)
    try:
        lifetime = face.route_tally()
        day1 = face.route_tally(D1)
    finally:
        face.close()
    assert lifetime["unrouted"] == 2, "AC-FRT4 unrouted %r" % lifetime
    assert lifetime["legacy-ghost"] == 1, "AC-FRT4 ghost dropped"
    assert day1["legacy-ghost"] == 1, "AC-FRT4 ghost out of window"
    assert lifetime["game"] == 1, "AC-FRT4 ghost merged into a route"
    assert sorted(lifetime.keys()) == list(lifetime.keys()), \
        "AC-FRT4 order %r" % list(lifetime.keys())
    assert lifetime == _manual_tally(world["db"]), \
        "AC-FRT4 differs from manual SQL"


# AC-FRT5: re-scanning the same inbox is idempotent for the tally.
def case_frt5(tmp):
    world = _world(tmp, "frt5")
    face = _open(world)
    try:
        before = json.dumps(face.route_tally(), sort_keys=True)
        ring1 = face.scan_leads(world["leads1"], D1)
        ring2 = face.dispatch_leads(D1)
        after = json.dumps(face.route_tally(), sort_keys=True)
        rows_after = _dispatch_rows(world["db"])
    finally:
        face.close()
    assert ring1["leads_new"] == 0, "AC-FRT5 re-scan added leads %r" % ring1
    assert ring2["dispatches_new"] == 0, \
        "AC-FRT5 re-dispatch added rows %r" % ring2
    assert before == after, "AC-FRT5 tally drifted on re-dispatch"
    assert len(rows_after) == 7, "AC-FRT5 dispatch rows %r" % len(rows_after)


# AC-FRT6: bad day forms fail closed before any row is touched.
def case_frt6(tmp):
    world = _world(tmp, "frt6")
    face = _open(world)
    try:
        rows_before = _dispatch_rows(world["db"])
        rollups_before = _count(world["db"], "rollups")
        for bad in (20261020, "2026-13-01", "", "x"):
            try:
                face.route_tally(bad)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, \
                    "AC-FRT6 code %r" % str(exc)
            else:
                raise AssertionError("AC-FRT6 bad day accepted %r" % (bad,))
        assert _dispatch_rows(world["db"]) == rows_before, \
            "AC-FRT6 rejection touched dispatches"
        assert _count(world["db"], "rollups") == rollups_before, \
            "AC-FRT6 rejection touched rollups"
    finally:
        face.close()


# AC-FRT7: pure read law plus cross-instance byte-identical reads.
def case_frt7(tmp):
    world = _world(tmp, "frt7")
    face = _open(world)
    try:
        rows_before = _dispatch_rows(world["db"])
        schema_before = face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()
        first = json.dumps(face.route_tally(), sort_keys=True)
        second = json.dumps(face.route_tally(D1), sort_keys=True)
        assert _dispatch_rows(world["db"]) == rows_before, \
            "AC-FRT7 read face wrote dispatches"
        assert face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall() == schema_before, "AC-FRT7 read face changed schema"
    finally:
        face.close()
    face = _open(world)
    try:
        reopened = json.dumps(face.route_tally(), sort_keys=True)
        reopened_day = json.dumps(face.route_tally(D1), sort_keys=True)
    finally:
        face.close()
    assert reopened == first, "AC-FRT7 lifetime drifted across restart"
    assert reopened_day == second, "AC-FRT7 day drifted across restart"
    assert json.loads(reopened) == LIFETIME, "AC-FRT7 reopened face"


# AC-FRT8: hygiene - ASCII source, zero network/clock, deterministic.
def case_frt8(tmp):
    lib = os.path.join(BASE, "funnel_daily.py")
    raw = open(lib, "rb").read()
    assert all(b < 128 for b in raw), "AC-FRT8 library not ASCII"
    tree = ast.parse(raw.decode("ascii"))
    banned = ("socket", "urllib", "requests", "http", "asyncio")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, \
                    "AC-FRT8 network import %s" % alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned, \
                    "AC-FRT8 network import %s" % node.module
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("now", "today", "utcnow"), \
                "AC-FRT8 wall clock call %s" % node.func.attr

    suite_raw = open(os.path.abspath(__file__), "rb").read()
    assert all(b < 128 for b in suite_raw), "AC-FRT8 suite not ASCII"

    cfg = os.path.join(BASE, "config.json")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha = sha(cfg)
    world = _world(tmp, "frt8")
    face = _open(world)
    try:
        one = json.dumps(face.route_tally(), sort_keys=True)
        two = json.dumps(face.route_tally(), sort_keys=True)
        day_one = json.dumps(face.route_tally(D2), sort_keys=True)
        day_two = json.dumps(face.route_tally(D2), sort_keys=True)
    finally:
        face.close()
    assert one == two, "AC-FRT8 lifetime read not deterministic"
    assert day_one == day_two, "AC-FRT8 day read not deterministic"
    assert json.loads(one) == LIFETIME, "AC-FRT8 live face"
    assert sha(cfg) == cfg_sha, "AC-FRT8 shipped config mutated"
    assert os.path.abspath(world["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FRT8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-route-")
    cases = [
        ("AC-FRT1 empty carrier", case_frt1),
        ("AC-FRT2 lifetime route distribution", case_frt2),
        ("AC-FRT3 day window law", case_frt3),
        ("AC-FRT4 unrouted and unknown routes", case_frt4),
        ("AC-FRT5 idempotent re-dispatch", case_frt5),
        ("AC-FRT6 bad day fail-closed", case_frt6),
        ("AC-FRT7 pure read and restart stability", case_frt7),
        ("AC-FRT8 hygiene and determinism", case_frt8),
    ]
    failed = 0
    for name, fn in cases:
        try:
            fn(tmp)
            print("PASS %s" % name)
        except AssertionError as exc:
            failed += 1
            print("FAIL %s :: %s" % (name, exc))
    shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases)
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())