"""Acceptance suite for the funnel sku_top ranking semantics battery
(FUNNEL-LOOP v0.1, R2069).

Pre-registered criteria AC-FTS1..AC-FTS8 live in state/queue/tech.md
(the R2069 claim row) and were written BEFORE this suite existed
(honesty law). The rows that seeded this window were the four R2059
sku_top extension seeds whose criteria text had been destroyed by '?'
substitution; the backlog ruling allowed merging them into one rebuilt
window, and the four original sub-faces (zero/negative buckets, late
arrival re-rank, cut order, equal-amount cut boundary) are carried by
AC-FTS2..AC-FTS4 and AC-FTS5 below.

Worlds (all booked through the real product path, run_daily):

  BASE  D1 pack-basic 1990 / pack-pro 2990 / pack-basic 1990
        D2 "" 500 / pack-pro 2990 / pack-mini 3980
        lifetime: pack-pro 5980, pack-basic 3980, pack-mini 3980, "" 500
  SIGN  S1 m-pos 250 / m-zero 0 / m-neg -250 / "" 0
        lifetime: m-pos 250, "" 0, m-zero 0, m-neg -250
  TIE   T1 k4 900 / k3 500 / k2 500 / k1 500
        lifetime: k4 900, k1 500, k2 500, k3 500
  LATE  BASE plus D3 pack-mini 5000
        lifetime: pack-mini 8980, pack-pro 5980, pack-basic 3980, "" 500

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import funnel_daily as fd  # noqa: E402

D1 = "2026-10-16"
D2 = "2026-10-17"
D3 = "2026-10-18"
S1 = "2026-10-19"
T1 = "2026-10-20"

BASE_D1 = [
    {"order_id": "o1", "sku": "pack-basic", "amount_cent": 1990},
    {"order_id": "o2", "sku": "pack-pro", "amount_cent": 2990},
    {"order_id": "o3", "sku": "pack-basic", "amount_cent": 1990},
]
BASE_D2 = [
    {"order_id": "o4", "sku": "", "amount_cent": 500},
    {"order_id": "o5", "sku": "pack-pro", "amount_cent": 2990},
    {"order_id": "o6", "sku": "pack-mini", "amount_cent": 3980},
]
BASE_D3 = [
    {"order_id": "o7", "sku": "pack-mini", "amount_cent": 5000},
]
SIGN_S1 = [
    {"order_id": "s1", "sku": "m-pos", "amount_cent": 250},
    {"order_id": "s2", "sku": "m-zero", "amount_cent": 0},
    {"order_id": "s4", "sku": "", "amount_cent": 0},
]
TIE_T1 = [
    {"order_id": "t4", "sku": "k4", "amount_cent": 900},
    {"order_id": "t3", "sku": "k3", "amount_cent": 500},
    {"order_id": "t2", "sku": "k2", "amount_cent": 500},
    {"order_id": "t1", "sku": "k1", "amount_cent": 500},
]

BASE_LIFETIME = [
    ("pack-pro", 2, 5980),
    ("pack-basic", 2, 3980),
    ("pack-mini", 1, 3980),
    ("", 1, 500),
]
SIGN_ZERO_LIFETIME = [
    ("m-pos", 1, 250),
    ("", 1, 0),
    ("m-zero", 1, 0),
]
SIGN_INJECTED_LIFETIME = [
    ("m-pos", 1, 250),
    ("", 1, 0),
    ("m-zero", 1, 0),
    ("m-neg", 1, -250),
]
TIE_LIFETIME = [
    ("k4", 1, 900),
    ("k1", 1, 500),
    ("k2", 1, 500),
    ("k3", 1, 500),
]
LATE_LIFETIME = [
    ("pack-mini", 2, 8980),
    ("pack-pro", 2, 5980),
    ("pack-basic", 2, 3980),
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


def _shape(board):
    return [(row["sku"], row["orders"], row["amount_cent"]) for row in board]


def _count(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    finally:
        con.close()


def _orders_rows(db_path):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT * FROM orders ORDER BY order_id").fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _world(tmp, tag, days):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    leads = _mk_inbox(root, "leads", [])
    flows = _mk_inbox(root, "flows", [])
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    try:
        for day, rows in days:
            orders = _mk_inbox(root, "orders-" + day, rows)
            face.run_daily(leads, orders, flows, day)
    finally:
        face.close()
    return {"db": db, "root": root}


def _open(world):
    return fd.FunnelDaily(world["db"])


# AC-FTS1: the shipped ranking still reproduces the AC-FTP2/FTP4 anchor.
def case_fts1(tmp):
    world = _world(tmp, "fts1", [(D1, BASE_D1), (D2, BASE_D2)])
    face = _open(world)
    try:
        lifetime = face.sku_top(10)
        day1 = face.sku_top(10, D1)
        day2 = face.sku_top(10, D2)
        full = face.sku_top(4)
        pair = face.sku_top(2)
    finally:
        face.close()
    assert _shape(lifetime) == BASE_LIFETIME, \
        "AC-FTS1 lifetime anchor %r" % _shape(lifetime)
    assert _shape(day1) == [("pack-basic", 2, 3980), ("pack-pro", 1, 2990)], \
        "AC-FTS1 D1 anchor %r" % _shape(day1)
    assert _shape(day2) == [
        ("pack-mini", 1, 3980), ("pack-pro", 1, 2990), ("", 1, 500)], \
        "AC-FTS1 D2 anchor %r" % _shape(day2)
    assert full == lifetime, "AC-FTS1 full board drifted"
    assert _shape(pair) == BASE_LIFETIME[:2], \
        "AC-FTS1 cap-2 anchor %r" % _shape(pair)
    assert [row["rank"] for row in lifetime] == [1, 2, 3, 4], \
        "AC-FTS1 dense ranks %r" % [row["rank"] for row in lifetime]


# AC-FTS2: a zero-amount bucket keeps its place; equal zeros go by sku bytes.
def case_fts2(tmp):
    world = _world(tmp, "fts2", [(S1, SIGN_S1)])
    face = _open(world)
    try:
        board = face.sku_top(10)
        totals = face.sku_totals()
    finally:
        face.close()
    assert _shape(board) == SIGN_ZERO_LIFETIME, \
        "AC-FTS2 zero bucket order %r" % _shape(board)
    zeros = [row for row in board if row["amount_cent"] == 0]
    assert len(zeros) == 2, "AC-FTS2 zero buckets dropped %r" % board
    assert [row["sku"] for row in zeros] == ["", "m-zero"], \
        "AC-FTS2 zero tie not byte-ordered %r" % [r["sku"] for r in zeros]
    assert zeros[0]["rank"] == 2 and zeros[1]["rank"] == 3, \
        "AC-FTS2 zero ranks %r" % [r["rank"] for r in zeros]
    for row in zeros:
        assert row["amount_cent"] == totals[row["sku"]]["amount_cent"], \
            "AC-FTS2 zero amount not from its own bucket"


# AC-FTS3: negative money never enters through the booking gate (fail-closed,
# zero rows), and a directly injected negative row (test fixture, annotated)
# still shows at the last rank with its amount unclamped - the face never
# hides data.
def case_fts3(tmp):
    world = _world(tmp, "fts3", [(S1, SIGN_S1)])
    bad = _mk_inbox(world["root"], "orders-bad", [
        {"order_id": "sx", "sku": "m-neg", "amount_cent": -250},
    ])
    face = _open(world)
    try:
        orders_before = _orders_rows(world["db"])
        try:
            face.book_orders(bad, S1)
        except fd.FunnArgError as exc:
            assert str(exc) == fd.E_FN_BAD_ARGS, \
                "AC-FTS3 gate code %r" % str(exc)
        else:
            raise AssertionError("AC-FTS3 negative amount booked")
        assert _orders_rows(world["db"]) == orders_before, \
            "AC-FTS3 gate wrote rows on rejection"
    finally:
        face.close()

    # Fixture injection: the booking gate makes a negative row unreachable
    # through the product path, so the ranking face is probed with a direct
    # append (the same tamper posture as earlier read-face windows).
    con = sqlite3.connect(world["db"])
    try:
        con.execute(
            "INSERT INTO orders (order_id, day, sku, amount_cent) "
            "VALUES (?,?,?,?)", ("sx", S1, "m-neg", -250))
        con.commit()
    finally:
        con.close()

    face = _open(world)
    try:
        board = face.sku_top(10)
        capped = face.sku_top(3)
    finally:
        face.close()
    assert _shape(board) == SIGN_INJECTED_LIFETIME, \
        "AC-FTS3 negative rank order %r" % _shape(board)
    assert board[-1]["sku"] == "m-neg", "AC-FTS3 negative not last %r" % board
    assert board[-1]["amount_cent"] == -250, \
        "AC-FTS3 negative clamped %r" % board[-1]
    assert board[-1]["rank"] == 4, "AC-FTS3 negative rank %r" % board[-1]
    assert all(row["sku"] != "m-neg" for row in capped), \
        "AC-FTS3 negative leaked above the cut %r" % capped
    assert len(board) == 4, "AC-FTS3 negative bucket dropped"


# AC-FTS4: with three equal amounts the cap is a strict prefix of the full
# board - cutting never re-sorts, ranks stay dense.
def case_fts4(tmp):
    world = _world(tmp, "fts4", [(T1, TIE_T1)])
    face = _open(world)
    try:
        full = face.sku_top(4)
        one = face.sku_top(1)
        pair = face.sku_top(2)
        three = face.sku_top(3)
    finally:
        face.close()
    assert _shape(full) == TIE_LIFETIME, \
        "AC-FTS4 tie board %r" % _shape(full)
    assert _shape(one) == TIE_LIFETIME[:1], "AC-FTS4 cap 1 %r" % _shape(one)
    assert _shape(pair) == TIE_LIFETIME[:2], "AC-FTS4 cap 2 %r" % _shape(pair)
    assert _shape(three) == TIE_LIFETIME[:3], \
        "AC-FTS4 cap 3 %r" % _shape(three)
    for board in (one, pair, three, full):
        assert [row["rank"] for row in board] == list(
            range(1, len(board) + 1)), "AC-FTS4 ranks %r" % board
    tied = [row["sku"] for row in full if row["amount_cent"] == 500]
    assert tied == ["k1", "k2", "k3"], "AC-FTS4 tie order %r" % tied
    assert _shape(pair)[1] == TIE_LIFETIME[1], \
        "AC-FTS4 cut boundary re-sorted the tie"


# AC-FTS5: a late day re-ranks the lifetime face while earlier day windows
# stay byte-frozen.
def case_fts5(tmp):
    world = _world(tmp, "fts5", [(D1, BASE_D1), (D2, BASE_D2)])
    face = _open(world)
    try:
        day1_before = json.dumps(face.sku_top(10, D1), sort_keys=True)
        day2_before = json.dumps(face.sku_top(10, D2), sort_keys=True)
        lifetime_before = face.sku_top(10)
        orders = _mk_inbox(world["root"], "orders-" + D3, BASE_D3)
        face.run_daily(_mk_inbox(world["root"], "leads", []), orders,
                       _mk_inbox(world["root"], "flows", []), D3)
        lifetime_after = face.sku_top(10)
        day1_after = json.dumps(face.sku_top(10, D1), sort_keys=True)
        day2_after = json.dumps(face.sku_top(10, D2), sort_keys=True)
    finally:
        face.close()
    assert _shape(lifetime_before) == BASE_LIFETIME, \
        "AC-FTS5 pre-append anchor %r" % _shape(lifetime_before)
    assert _shape(lifetime_after) == LATE_LIFETIME, \
        "AC-FTS5 late re-rank %r" % _shape(lifetime_after)
    assert lifetime_after[0]["sku"] == "pack-mini" and \
        lifetime_after[0]["amount_cent"] == 8980, \
        "AC-FTS5 late leader %r" % lifetime_after[0]
    assert day1_after == day1_before, "AC-FTS5 D1 window drifted"
    assert day2_after == day2_before, "AC-FTS5 D2 window drifted"


# AC-FTS6: pure read law and byte-identical reads after a restart.
def case_fts6(tmp):
    world = _world(tmp, "fts6", [(D1, BASE_D1), (D2, BASE_D2)])
    face = _open(world)
    try:
        orders_before = _orders_rows(world["db"])
        rollups_before = _count(world["db"], "rollups")
        schema_before = face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()
        lifetime = json.dumps(face.sku_top(10), sort_keys=True)
        daytwo = json.dumps(face.sku_top(10, D2), sort_keys=True)
        assert _orders_rows(world["db"]) == orders_before, \
            "AC-FTS6 read wrote orders"
        assert _count(world["db"], "rollups") == rollups_before, \
            "AC-FTS6 read wrote rollups"
        assert face.db.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall() == schema_before, "AC-FTS6 read changed schema"
    finally:
        face.close()
    face = _open(world)
    try:
        reopened = json.dumps(face.sku_top(10), sort_keys=True)
        reopened_day = json.dumps(face.sku_top(10, D2), sort_keys=True)
    finally:
        face.close()
    assert reopened == lifetime, "AC-FTS6 lifetime drifted across restart"
    assert reopened_day == daytwo, "AC-FTS6 day drifted across restart"


# AC-FTS7: deterministic double read and the money conservation bound.
def case_fts7(tmp):
    world = _world(tmp, "fts7", [(D1, BASE_D1), (D2, BASE_D2)])
    face = _open(world)
    try:
        one = json.dumps(face.sku_top(2), sort_keys=True)
        two = json.dumps(face.sku_top(2), sort_keys=True)
        full = face.sku_top(10)
        top2 = face.sku_top(2)
        totals = face.sku_totals()
    finally:
        face.close()
    assert one == two, "AC-FTS7 lifetime read not deterministic"
    book_total = sum(bucket["amount_cent"] for bucket in totals.values())
    assert len(full) == len(totals), "AC-FTS7 full board lost a bucket"
    assert sum(row["amount_cent"] for row in full) == book_total, \
        "AC-FTS7 full board money %r != book %r" % (full, book_total)
    assert sum(row["amount_cent"] for row in top2) <= book_total, \
        "AC-FTS7 truncated board exceeds the book"
    for row in full:
        assert sorted(row.keys()) == [
            "amount_cent", "orders", "rank", "sku"], \
            "AC-FTS7 key set %r" % sorted(row.keys())


# AC-FTS8: hygiene - ASCII sources, zero network imports, shipped config
# intact, and the runner registry carries the suite at 8 criteria.
def case_fts8(tmp):
    lib = os.path.join(BASE_DIR, "funnel_daily.py")
    suite = os.path.join(BASE_DIR, "test_funnel_sku_top_rank.py")
    banned = ("socket", "urllib", "requests", "http", "asyncio")
    for path in (lib, suite):
        raw = open(path, "rb").read()
        assert all(b < 128 for b in raw), \
            "AC-FTS8 not ASCII: %s" % os.path.basename(path)
        tree = ast.parse(raw.decode("ascii"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in banned, \
                        "AC-FTS8 banned import %s" % alias.name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in banned, \
                    "AC-FTS8 banned import %s" % node.module
    clock_calls = []
    for node in ast.walk(ast.parse(open(lib, "rb").read().decode("ascii"))):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("now", "utcnow", "today"):
                clock_calls.append(node.func.attr)
    assert clock_calls == [], "AC-FTS8 wall clock calls %r" % clock_calls

    runner = os.path.join(BASE_DIR, "..", "reconcile_all.py")
    text = open(runner, "rb").read().decode("ascii")
    assert '"funnel-sku-top-rank"' in text.replace("'", '"'), \
        "AC-FTS8 registry label missing"
    assert '"test_funnel_sku_top_rank.py"' in text.replace("'", '"'), \
        "AC-FTS8 registry path missing"

    cfg = os.path.join(BASE_DIR, "config.json")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha = sha(cfg)
    world = _world(tmp, "fts8", [(D1, BASE_D1)])
    face = _open(world)
    try:
        face.sku_top(3)
        face.sku_top(3, D1)
    finally:
        face.close()
    assert sha(cfg) == cfg_sha, "AC-FTS8 shipped config mutated"
    assert os.path.abspath(world["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FTS8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-skutoprank-")
    cases = [
        ("AC-FTS1 anchor board", case_fts1),
        ("AC-FTS2 zero buckets keep rank", case_fts2),
        ("AC-FTS3 negative bucket last", case_fts3),
        ("AC-FTS4 equal-amount cut prefix", case_fts4),
        ("AC-FTS5 late arrival re-rank", case_fts5),
        ("AC-FTS6 pure read and restart", case_fts6),
        ("AC-FTS7 determinism and money bound", case_fts7),
        ("AC-FTS8 hygiene and registry", case_fts8),
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