"""Acceptance suite for the funnel ranked per-sku order totals read face
(FUNNEL-LOOP v0.1, R2059).

Pre-registered criteria AC-FTP1..AC-FTP8 live in state/queue/tech.md
(the R2059 claim row) and were written BEFORE this suite existed
(honesty law). The gap under test: sku_totals (R2054) reports every
bucket in ascending sku order, which answers "what is in the book?" but
not "which sku earns most?". Nothing ranked the buckets by money, so
the amount leaderboard face was missing.

World: two booked days over four sku buckets - named sku "pack-basic",
named sku "pack-mini", named sku "pack-pro", and the blank sku "".

  D1: pack-basic 1990, pack-pro 2990, pack-basic 1990
  D2: "" 500, pack-pro 2990, pack-mini 3980

Lifetime: "" 1/500, pack-basic 2/3980, pack-mini 1/3980,
          pack-pro 2/5980.

Lifetime rank: pack-pro 5980 (1), pack-basic 3980 (2), pack-mini 3980
(3, tie broken by sku byte order), "" 500 (4).

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

D1_ROWS = [
    {"order_id": "o1", "sku": "pack-basic", "amount_cent": 1990},
    {"order_id": "o2", "sku": "pack-pro", "amount_cent": 2990},
    {"order_id": "o3", "sku": "pack-basic", "amount_cent": 1990},
]
D2_ROWS = [
    {"order_id": "o4", "sku": "", "amount_cent": 500},
    {"order_id": "o5", "sku": "pack-pro", "amount_cent": 2990},
    {"order_id": "o6", "sku": "pack-mini", "amount_cent": 3980},
]

LIFETIME_ORDER = [
    ("pack-pro", 2, 5980),
    ("pack-basic", 2, 3980),
    ("pack-mini", 1, 3980),
    ("", 1, 500),
]
D1_ORDER = [
    ("pack-basic", 2, 3980),
    ("pack-pro", 1, 2990),
]
D2_ORDER = [
    ("pack-mini", 1, 3980),
    ("pack-pro", 1, 2990),
    ("", 1, 500),
]


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _orders_rows(db_path):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT * FROM orders ORDER BY order_id").fetchall()
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
    return 0


def _world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    empty = _mk_inbox(root, "leads", [])
    orders1 = _mk_inbox(root, "orders1", D1_ROWS)
    orders2 = _mk_inbox(root, "orders2", D2_ROWS)
    flows = _mk_inbox(root, "flows", [])
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    face.run_daily(empty, orders1, flows, D1)
    face.run_daily(empty, orders2, flows, D2)
    face.close()
    return {"db": db, "root": root}


def _open(world):
    return fd.FunnelDaily(world["db"])


def _empty_world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    db = os.path.join(root, "funnel.db")
    fd.FunnelDaily(db).close()
    return {"db": db, "root": root}


def _shape(board):
    return [(row["sku"], row["orders"], row["amount_cent"]) for row in board]


# AC-FTP1: an empty order book is an honest empty board; bad n fails closed.
def case_ftp1(tmp):
    world = _empty_world(tmp, "ftp1")
    face = _open(world)
    try:
        assert face.sku_top(3) == [], "AC-FTP1 lifetime not empty"
        assert face.sku_top(3, D1) == [], "AC-FTP1 day not empty"
        orders_before = _orders_rows(world["db"])
        rollups_before = _count(world["db"], "rollups")
        for bad in (0, -1, True, "3", 2.5, None):
            try:
                face.sku_top(bad)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, \
                    "AC-FTP1 code %r" % str(exc)
            else:
                raise AssertionError("AC-FTP1 bad n accepted %r" % (bad,))
        assert _orders_rows(world["db"]) == orders_before, \
            "AC-FTP1 rejection touched orders"
        assert _count(world["db"], "rollups") == rollups_before, \
            "AC-FTP1 rejection touched rollups"
    finally:
        face.close()


# AC-FTP2: lifetime ranking by money, ties by sku byte order, ranks dense.
def case_ftp2(tmp):
    world = _world(tmp, "ftp2")
    face = _open(world)
    try:
        board = face.sku_top(10)
        totals = face.sku_totals()
    finally:
        face.close()
    assert _shape(board) == LIFETIME_ORDER, "AC-FTP2 order %r" % _shape(board)
    assert [row["rank"] for row in board] == [1, 2, 3, 4], \
        "AC-FTP2 ranks %r" % [row["rank"] for row in board]
    for row in board:
        assert sorted(row.keys()) == ["amount_cent", "orders", "rank", "sku"], \
            "AC-FTP2 key set %r" % sorted(row.keys())
        want = totals[row["sku"]]
        assert row["orders"] == want["orders"], "AC-FTP2 orders drift"
        assert row["amount_cent"] == want["amount_cent"], \
            "AC-FTP2 amount drift"
    assert board[1]["amount_cent"] == board[2]["amount_cent"], \
        "AC-FTP2 tie not exercised"
    assert board[1]["sku"] < board[2]["sku"], "AC-FTP2 tie not byte-ordered"


# AC-FTP3: day window isolation, honest empty day, bad day fail-closed.
def case_ftp3(tmp):
    world = _world(tmp, "ftp3")
    face = _open(world)
    try:
        day1 = face.sku_top(10, D1)
        day2 = face.sku_top(10, D2)
        empty = face.sku_top(10, EMPTY_DAY)
        ranks = face.sku_top(10)
        for bad in (20261020, "2026-13-01", "", "x"):
            try:
                face.sku_top(3, bad)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, \
                    "AC-FTP3 code %r" % str(exc)
            else:
                raise AssertionError("AC-FTP3 bad day accepted %r" % (bad,))
    finally:
        face.close()
    assert _shape(day1) == D1_ORDER, "AC-FTP3 D1 %r" % _shape(day1)
    assert _shape(day2) == D2_ORDER, "AC-FTP3 D2 %r" % _shape(day2)
    assert empty == [], "AC-FTP3 empty day %r" % empty
    assert all(row["sku"] != "" for row in day1), "AC-FTP3 D2 leaked into D1"
    assert all(row["sku"] != "pack-basic" for row in day2), \
        "AC-FTP3 D1 leaked into D2"
    assert len(ranks) == 4 and len(day1) == 2 and len(day2) == 3, \
        "AC-FTP3 window faces share buckets"


# AC-FTP4: the cap is a prefix cut - no padding, no phantom rows.
def case_ftp4(tmp):
    world = _world(tmp, "ftp4")
    face = _open(world)
    try:
        full = face.sku_top(4)
        over = face.sku_top(10)
        one = face.sku_top(1)
        pair = face.sku_top(2)
        three = face.sku_top(3)
    finally:
        face.close()
    assert full == over, "AC-FTP4 over-cap board drifted %r" % over
    assert len(full) == 4, "AC-FTP4 full board %r" % full
    assert _shape(one) == LIFETIME_ORDER[:1], "AC-FTP4 limit 1 %r" % _shape(one)
    assert one[0]["rank"] == 1, "AC-FTP4 limit 1 rank"
    assert _shape(pair) == LIFETIME_ORDER[:2], "AC-FTP4 limit 2 %r" % _shape(pair)
    assert _shape(three) == LIFETIME_ORDER[:3], \
        "AC-FTP4 limit 3 %r" % _shape(three)
    assert len(three) == 3, "AC-FTP4 prefix length"


# AC-FTP5: the blank sku competes on money like any named bucket.
def case_ftp5(tmp):
    world = _world(tmp, "ftp5")
    face = _open(world)
    try:
        lifetime = face.sku_top(10)
        day2 = face.sku_top(10, D2)
        totals = face.sku_totals()
    finally:
        face.close()
    blank = [row for row in lifetime if row["sku"] == ""]
    assert len(blank) == 1, "AC-FTP5 blank bucket missing %r" % lifetime
    assert blank[0]["rank"] == 4, "AC-FTP5 blank rank %r" % blank[0]
    assert blank[0]["amount_cent"] == totals[""]["amount_cent"], \
        "AC-FTP5 blank amount not from its own bucket"
    assert _shape(day2)[-1] == ("", 1, 500), "AC-FTP5 blank window rank"
    assert [row["sku"] for row in day2].count("") == 1, \
        "AC-FTP5 blank duplicated"
    assert lifetime[1]["amount_cent"] == 3980, \
        "AC-FTP5 blank merged into a named bucket"


# AC-FTP6: pure read law and restart stability on both faces.
def case_ftp6(tmp):
    world = _world(tmp, "ftp6")
    face = _open(world)
    try:
        orders_before = _orders_rows(world["db"])
        rollups_before = _count(world["db"], "rollups")
        schema_before = face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()
        lifetime = json.dumps(face.sku_top(10), sort_keys=True)
        daytwo = json.dumps(face.sku_top(10, D2), sort_keys=True)
        assert _orders_rows(world["db"]) == orders_before, \
            "AC-FTP6 read face wrote orders"
        assert _count(world["db"], "rollups") == rollups_before, \
            "AC-FTP6 read face wrote rollups"
        assert face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall() == schema_before, "AC-FTP6 read face changed schema"
    finally:
        face.close()
    face = _open(world)
    try:
        reopened = json.dumps(face.sku_top(10), sort_keys=True)
        reopened_day = json.dumps(face.sku_top(10, D2), sort_keys=True)
    finally:
        face.close()
    assert reopened == lifetime, "AC-FTP6 lifetime drifted across restart"
    assert reopened_day == daytwo, "AC-FTP6 day drifted across restart"


# AC-FTP7: deterministic double read and the conservation upper bound.
def case_ftp7(tmp):
    world = _world(tmp, "ftp7")
    face = _open(world)
    try:
        one = json.dumps(face.sku_top(2), sort_keys=True)
        two = json.dumps(face.sku_top(2), sort_keys=True)
        top2 = face.sku_top(2)
        totals = face.sku_totals()
        dayone = json.dumps(face.sku_top(1, D1), sort_keys=True)
        dayone_two = json.dumps(face.sku_top(1, D1), sort_keys=True)
    finally:
        face.close()
    assert one == two, "AC-FTP7 lifetime read not deterministic"
    assert dayone == dayone_two, "AC-FTP7 day read not deterministic"
    lifetime_total = sum(bucket["amount_cent"] for bucket in totals.values())
    assert sum(row["amount_cent"] for row in top2) <= lifetime_total, \
        "AC-FTP7 truncated board exceeds the book"
    assert sum(row["amount_cent"] for row in top2) == 5980 + 3980, \
        "AC-FTP7 top-2 money %r" % top2


# AC-FTP8: hygiene - ASCII source, zero network/clock, shipped config intact.
def case_ftp8(tmp):
    lib = os.path.join(BASE, "funnel_daily.py")
    raw = open(lib, "rb").read()
    assert all(b < 128 for b in raw), "AC-FTP8 library not ASCII"
    tree = ast.parse(raw.decode("ascii"))
    banned = ("socket", "urllib", "requests", "http", "asyncio")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, \
                    "AC-FTP8 banned import %s" % alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned, \
                    "AC-FTP8 banned import %s" % node.module
    # Calendar validation imports datetime; the law is no wall clock, so
    # the clock keeps its own check: zero now()/utcnow()/today() calls.
    clock_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("now", "utcnow", "today"):
                clock_calls.append(node.func.attr)
    assert clock_calls == [], "AC-FTP8 wall clock calls %r" % clock_calls

    cfg = os.path.join(BASE, "config.json")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha = sha(cfg)
    world = _world(tmp, "ftp8")
    face = _open(world)
    try:
        face.sku_top(3)
        face.sku_top(3, D1)
    finally:
        face.close()
    assert sha(cfg) == cfg_sha, "AC-FTP8 shipped config mutated"
    assert os.path.abspath(world["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FTP8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-skutop-")
    cases = [
        ("AC-FTP1 empty board and bad n", case_ftp1),
        ("AC-FTP2 lifetime money ranking", case_ftp2),
        ("AC-FTP3 day window law", case_ftp3),
        ("AC-FTP4 cap prefix law", case_ftp4),
        ("AC-FTP5 blank sku competes", case_ftp5),
        ("AC-FTP6 pure read and restart", case_ftp6),
        ("AC-FTP7 determinism and bound", case_ftp7),
        ("AC-FTP8 hygiene and shipped config", case_ftp8),
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