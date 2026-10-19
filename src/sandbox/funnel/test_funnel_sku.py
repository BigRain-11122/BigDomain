"""Acceptance suite for the funnel per-sku order totals read face
(FUNNEL-LOOP v0.1, R2054).

Pre-registered criteria AC-FST1..AC-FST8 live in state/queue/tech.md
(the R2054 claim row) and were written BEFORE this suite existed
(honesty law). The gap under test: the rollup envelope counts orders
per day (AC-FN5/AC-FCV2) and the per-account ledger reads the flows
table (AC-FAR), but nothing reads the orders table GROUPED BY SKU -
there is no per-sku unit/amount aggregation face at all.

World: two booked days over three sku buckets - named sku "pack-basic",
named sku "pack-pro", and the blank sku "" (an order row may honestly
carry no sku yet).

  D1: pack-basic 1990, pack-pro 2990, pack-basic 1990
  D2: "" 500, pack-pro 2990

Lifetime: "" 1/500, pack-basic 2/3980, pack-pro 2/5980.

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
    "": {"orders": 1, "amount_cent": 500},
    "pack-basic": {"orders": 2, "amount_cent": 3980},
    "pack-pro": {"orders": 2, "amount_cent": 5980},
}
WINDOW_D1 = {
    "pack-basic": {"orders": 2, "amount_cent": 3980},
    "pack-pro": {"orders": 1, "amount_cent": 2990},
}
WINDOW_D2 = {
    "": {"orders": 1, "amount_cent": 500},
    "pack-pro": {"orders": 1, "amount_cent": 2990},
}

D1_ROWS = [
    {"order_id": "o1", "sku": "pack-basic", "amount_cent": 1990},
    {"order_id": "o2", "sku": "pack-pro", "amount_cent": 2990},
    {"order_id": "o3", "sku": "pack-basic", "amount_cent": 1990},
]
D2_ROWS = [
    {"order_id": "o4", "sku": "", "amount_cent": 500},
    {"order_id": "o5", "sku": "pack-pro", "amount_cent": 2990},
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


def _world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    empty = _mk_inbox(root, "leads", [])
    orders1 = _mk_inbox(root, "orders1", D1_ROWS)
    orders2 = _mk_inbox(root, "orders2", D2_ROWS)
    flows = _mk_inbox(root, "flows", [])
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    out1 = face.run_daily(empty, orders1, flows, D1)
    out2 = face.run_daily(empty, orders2, flows, D2)
    face.close()
    return {
        "db": db,
        "root": root,
        "out1": out1,
        "out2": out2,
        "orders1": orders1,
    }


def _open(world):
    return fd.FunnelDaily(world["db"])


def _empty_world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    face.close()
    return {"db": db, "root": root}


# AC-FST1: a fresh empty order book is an honest empty face.
def case_fst1(tmp):
    world = _empty_world(tmp, "fst1")
    face = _open(world)
    try:
        lifetime = face.sku_totals()
        windowed = face.sku_totals(D1)
    finally:
        face.close()
    assert lifetime == {}, "AC-FST1 lifetime %r" % lifetime
    assert windowed == {}, "AC-FST1 window %r" % windowed


# AC-FST2: lifetime aggregation per sku, sorted sku order, merged sums.
def case_fst2(tmp):
    world = _world(tmp, "fst2")
    face = _open(world)
    try:
        out = face.sku_totals()
    finally:
        face.close()
    assert list(out.keys()) == ["", "pack-basic", "pack-pro"], \
        "AC-FST2 sku order %r" % list(out.keys())
    for sku, expected in LIFETIME.items():
        got = out[sku]
        assert list(got.keys()) == ["orders", "amount_cent"], \
            "AC-FST2 key set %r" % list(got.keys())
        assert got == expected, \
            "AC-FST2 %r got %r want %r" % (sku, got, expected)


# AC-FST3: window isolation both ways plus an honest empty day.
def case_fst3(tmp):
    world = _world(tmp, "fst3")
    face = _open(world)
    try:
        day1 = face.sku_totals(D1)
        day2 = face.sku_totals(D2)
        lifetime = face.sku_totals()
        empty = face.sku_totals(EMPTY_DAY)
    finally:
        face.close()
    assert day1 == WINDOW_D1, "AC-FST3 D1 %r" % day1
    assert day2 == WINDOW_D2, "AC-FST3 D2 %r" % day2
    assert lifetime == LIFETIME, "AC-FST3 lifetime %r" % lifetime
    assert empty == {}, "AC-FST3 empty day %r" % empty
    assert "pack-basic" not in day2, "AC-FST3 window leaked D1 rows"
    assert "" not in day1, "AC-FST3 window leaked D2 rows"


# AC-FST4: the blank sku is its own bucket, never merged.
def case_fst4(tmp):
    world = _world(tmp, "fst4")
    face = _open(world)
    try:
        lifetime = face.sku_totals()
        day2 = face.sku_totals(D2)
    finally:
        face.close()
    assert "" in lifetime and "" in day2, "AC-FST4 blank bucket missing"
    assert lifetime[""]["amount_cent"] == 500, "AC-FST4 blank amount"
    assert lifetime["pack-basic"]["amount_cent"] == 3980, \
        "AC-FST4 blank merged into named sku"
    assert lifetime["pack-pro"]["amount_cent"] == 5980, \
        "AC-FST4 blank merged into named sku"
    assert list(lifetime.keys())[0] == "", "AC-FST4 blank not first"


# AC-FST5: re-booking the same inbox leaves the totals unchanged.
def case_fst5(tmp):
    world = _world(tmp, "fst5")
    face = _open(world)
    try:
        before = json.dumps(face.sku_totals(), sort_keys=True)
        again = face.book_orders(world["orders1"], D1)
        after = json.dumps(face.sku_totals(), sort_keys=True)
    finally:
        face.close()
    assert again["orders_new"] == 0, \
        "AC-FST5 duplicate booking added rows %r" % again
    assert before == after, "AC-FST5 totals drifted on re-booking"
    assert json.loads(after) == LIFETIME, "AC-FST5 totals %r" % after


# AC-FST6: bad day forms fail closed before any row is touched.
def case_fst6(tmp):
    world = _world(tmp, "fst6")
    face = _open(world)
    try:
        orders_before = _orders_rows(world["db"])
        rollups_before = _count(world["db"], "rollups")
        for bad in (20261020, "2026-13-01", "", "x"):
            try:
                face.sku_totals(bad)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, \
                    "AC-FST6 code %r" % str(exc)
            else:
                raise AssertionError("AC-FST6 bad day accepted %r" % (bad,))
        assert _orders_rows(world["db"]) == orders_before, \
            "AC-FST6 rejection touched orders"
        assert _count(world["db"], "rollups") == rollups_before, \
            "AC-FST6 rejection touched rollups"
    finally:
        face.close()


# AC-FST7: pure read law + cross-instance stability.
def case_fst7(tmp):
    world = _world(tmp, "fst7")
    face = _open(world)
    try:
        orders_before = _orders_rows(world["db"])
        schema_before = face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()
        first = json.dumps(face.sku_totals(), sort_keys=True)
        second = json.dumps(face.sku_totals(D2), sort_keys=True)
        assert _orders_rows(world["db"]) == orders_before, \
            "AC-FST7 read face wrote orders"
        assert face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall() == schema_before, "AC-FST7 read face changed schema"
    finally:
        face.close()
    face = _open(world)
    try:
        reopened = json.dumps(face.sku_totals(), sort_keys=True)
        reopened_day = json.dumps(face.sku_totals(D2), sort_keys=True)
    finally:
        face.close()
    assert reopened == first, "AC-FST7 lifetime drifted across restart"
    assert reopened_day == second, "AC-FST7 day drifted across restart"
    assert json.loads(reopened) == LIFETIME, "AC-FST7 reopened face"


# AC-FST8: hygiene - ASCII source, zero network/clock, deterministic.
def case_fst8(tmp):
    lib = os.path.join(BASE, "funnel_daily.py")
    raw = open(lib, "rb").read()
    assert all(b < 128 for b in raw), "AC-FST8 library not ASCII"
    tree = ast.parse(raw.decode("ascii"))
    banned = ("socket", "urllib", "requests", "http", "asyncio")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, \
                    "AC-FST8 network import %s" % alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned, \
                "AC-FST8 network import %s" % node.module

    cfg = os.path.join(BASE, "config.json")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha = sha(cfg)
    world = _world(tmp, "fst8")
    face = _open(world)
    try:
        one = json.dumps(face.sku_totals(), sort_keys=True)
        two = json.dumps(face.sku_totals(), sort_keys=True)
        day_one = json.dumps(face.sku_totals(D1), sort_keys=True)
        day_two = json.dumps(face.sku_totals(D1), sort_keys=True)
    finally:
        face.close()
    assert one == two, "AC-FST8 lifetime read not deterministic"
    assert day_one == day_two, "AC-FST8 day read not deterministic"
    assert json.loads(one) == LIFETIME, "AC-FST8 live face"
    assert sha(cfg) == cfg_sha, "AC-FST8 shipped config mutated"
    assert os.path.abspath(world["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FST8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-sku-")
    cases = [
        ("AC-FST1 empty order book", case_fst1),
        ("AC-FST2 lifetime sku aggregation", case_fst2),
        ("AC-FST3 day window law", case_fst3),
        ("AC-FST4 blank sku bucket", case_fst4),
        ("AC-FST5 idempotent booking totals", case_fst5),
        ("AC-FST6 bad day fail-closed", case_fst6),
        ("AC-FST7 pure read and restart stability", case_fst7),
        ("AC-FST8 hygiene and determinism", case_fst8),
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