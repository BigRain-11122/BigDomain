"""Acceptance suite for the funnel per-sku order totals read face
across restarts (FUNNEL-LOOP v0.1, R2058).

Pre-registered criteria AC-FSP1..AC-FSP8 live in state/queue/tech.md
(the R2058 claim row, written BEFORE this file existed - honesty law).
The gap the R2054 reseed row named: AC-FST7 proves only a single
close/reopen of the same read face; the three-instance cascade, the
new-order injection between restarts and the frozen earlier windows
had no example. This suite fills exactly that.

Behaviour under test (shipped library, nothing here changes it):
  - sku_totals() is a pure read over the append-only orders table
    with one bucket per sku, carrying order count and summed
    amount_cent, ordered by ascending sku (byte order); the blank sku
    is its own honest bucket and is never merged into a named one.
  - The face derives nothing from memory: a restart reproduces it
    byte-for-byte, an earlier day window stays frozen when new orders
    land in a later day, and a re-booked order id keeps the book
    idempotent across restarts.

Pure ASCII source (coding law). The suite writes only inside a
temporary directory, never into the repository.
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

DAY1 = "2026-10-19"
DAY2 = "2026-10-20"
DAY3 = "2026-10-21"
NO_ROWS_DAY = "2026-10-22"

DAY1_ORDERS = [
    {"order_id": "O1", "sku": "compute-pack-19.9", "amount_cent": 1990},
    {"order_id": "O2", "sku": "compute-pack-19.9", "amount_cent": 2990},
    {"order_id": "O3", "sku": "", "amount_cent": 500},
]
DAY2_ORDERS = [
    {"order_id": "O4", "sku": "media-pack-9.9", "amount_cent": 990},
    {"order_id": "O5", "sku": "compute-pack-19.9", "amount_cent": 1000},
]
DAY3_ORDERS = [
    {"order_id": "O6", "sku": "new-sku-1", "amount_cent": 100},
]
DAY3_LATE_ORDERS = [
    {"order_id": "O7", "sku": "new-sku-1", "amount_cent": 200},
    {"order_id": "O8", "sku": "compute-pack-19.9", "amount_cent": 500},
    {"order_id": "O9", "sku": "", "amount_cent": 300},
]

# Snapshots / state shared across criteria (each criterion keeps its
# own world, so the dict is keyed by world name).
SNAP = {}


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _rows(db_path):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT order_id, day, sku, amount_cent FROM orders "
            "ORDER BY order_id").fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _count(db_path):
    con = sqlite3.connect(db_path)
    try:
        return con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    finally:
        con.close()


def _world(tmp, name):
    """One populated three-day order world (layered later by the
    restart criteria). Returns the db path and the inbox dirs."""
    root = os.path.join(tmp, name)
    os.makedirs(root)
    return {
        "root": root,
        "db": os.path.join(root, "funnel.db"),
        "day1": _mk_inbox(root, "orders-day1", DAY1_ORDERS),
        "day2": _mk_inbox(root, "orders-day2", DAY2_ORDERS),
        "day3": _mk_inbox(root, "orders-day3", DAY3_ORDERS),
        "day3late": _mk_inbox(root, "orders-day3-late", DAY3_LATE_ORDERS),
    }


def _faces(carrier):
    """The five read faces the window pins: lifetime, three day
    windows, and a day with no rows (honest empty)."""
    return {
        "lifetime": carrier.sku_totals(),
        "day1": carrier.sku_totals(DAY1),
        "day2": carrier.sku_totals(DAY2),
        "day3": carrier.sku_totals(DAY3),
        "no_rows": carrier.sku_totals(NO_ROWS_DAY),
    }


def _book(carrier, w):
    carrier.book_orders(w["day1"], DAY1)
    carrier.book_orders(w["day2"], DAY2)
    carrier.book_orders(w["day3"], DAY3)


def _assert_shape(face, where):
    for sku, bucket in face.items():
        assert isinstance(sku, str), "%s non-str sku bucket" % where
        assert set(bucket.keys()) == {"orders", "amount_cent"}, \
            "%s bucket keys drifted: %r" % (where, sorted(bucket.keys()))
        assert isinstance(bucket["orders"], int) and bucket["orders"] > 0, \
            "%s empty bucket %r" % (where, sku)
        assert isinstance(bucket["amount_cent"], int), \
            "%s non-int amount for %r" % (where, sku)
    assert list(face.keys()) == sorted(face.keys()), \
        "%s bucket order is not ascending byte order" % where


def case_fsp1(tmp):
    """AC-FSP1: instance one anchors the world through the product
    path; the five read faces are snapshotted, the bucket shape is
    exactly {orders, amount_cent}, buckets are in ascending byte
    order, the blank sku is its own bucket, and the lifetime book
    carries six orders."""
    w = _world(tmp, "fsp1")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
        faces = _faces(f)
    finally:
        f.close()

    for name, face in faces.items():
        _assert_shape(face, "AC-FSP1 %s" % name)

    life = faces["lifetime"]
    assert life["compute-pack-19.9"] == {"orders": 3, "amount_cent": 5980}, \
        "AC-FSP1 named bucket %r" % (life["compute-pack-19.9"],)
    assert life["media-pack-9.9"] == {"orders": 1, "amount_cent": 990}
    assert life["new-sku-1"] == {"orders": 1, "amount_cent": 100}
    assert life[""] == {"orders": 1, "amount_cent": 500}, \
        "AC-FSP1 blank sku merged or lost: %r" % (life[""],)
    assert sum(b["orders"] for b in life.values()) == 6, \
        "AC-FSP1 lifetime total drifted"

    assert faces["day1"] == {
        "": {"orders": 1, "amount_cent": 500},
        "compute-pack-19.9": {"orders": 2, "amount_cent": 4980},
    }, "AC-FSP1 day1 window %r" % (faces["day1"],)
    assert faces["day2"] == {
        "compute-pack-19.9": {"orders": 1, "amount_cent": 1000},
        "media-pack-9.9": {"orders": 1, "amount_cent": 990},
    }, "AC-FSP1 day2 window %r" % (faces["day2"],)
    assert faces["day3"] == {
        "new-sku-1": {"orders": 1, "amount_cent": 100},
    }, "AC-FSP1 day3 window %r" % (faces["day3"],)
    assert faces["no_rows"] == {}, \
        "AC-FSP1 no-row day is not an honest empty face"

    SNAP["fsp1_faces"] = _dump(faces)
    SNAP["fsp1_rows"] = _rows(w["db"])
    assert len(SNAP["fsp1_rows"]) == 6, "AC-FSP1 order rows drifted"


def case_fsp2(tmp):
    """AC-FSP2: close and reopen the carrier on the same database -
    the five read faces come back byte-for-byte, and an immediate
    second read is identical (no memory state on the read path)."""
    w = _world(tmp, "fsp2")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
        first = _dump(_faces(f))
    finally:
        f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        reopened = _dump(_faces(g))
        again = _dump(_faces(g))
    finally:
        g.close()

    assert reopened == first, "AC-FSP2 faces drifted across restart"
    assert again == reopened, "AC-FSP2 second read not identical"
    SNAP["fsp2_faces"] = first
    SNAP["fsp2_db"] = w["db"]


def case_fsp3(tmp):
    """AC-FSP3: after the restart, a late order batch for day three
    lands through the product path - the lifetime face grows, the new
    sku takes its byte-order position, and the earlier day windows
    stay frozen against the pre-restart snapshot."""
    assert SNAP.get("fsp2_faces"), "AC-FSP3 depends on AC-FSP2 world"
    w = _world(tmp, "fsp3")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
    finally:
        f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        before = _faces(g)
        before_dump = _dump(before)
        out = g.book_orders(w["day3late"], DAY3)
        after = _faces(g)
    finally:
        g.close()

    assert out["orders_new"] == 3 and out["orders_seen"] == 3, \
        "AC-FSP3 late batch booking %r" % (out,)
    life = after["lifetime"]
    assert life["compute-pack-19.9"] == {"orders": 4, "amount_cent": 6480}, \
        "AC-FSP3 named bucket did not grow: %r" % (life["compute-pack-19.9"],)
    assert life[""] == {"orders": 2, "amount_cent": 800}, \
        "AC-FSP3 blank bucket did not grow: %r" % (life[""],)
    assert life["new-sku-1"] == {"orders": 2, "amount_cent": 300}, \
        "AC-FSP3 new sku bucket %r" % (life["new-sku-1"],)
    assert list(life.keys()) == sorted(life.keys()), \
        "AC-FSP3 bucket order broken by the new sku"

    assert _dump(after["day1"]) == _dump(before["day1"]), \
        "AC-FSP3 day1 window thawed under new data"
    assert _dump(after["day2"]) == _dump(before["day2"]), \
        "AC-FSP3 day2 window thawed under new data"
    assert after["day3"] == {
        "": {"orders": 1, "amount_cent": 300},
        "compute-pack-19.9": {"orders": 1, "amount_cent": 500},
        "new-sku-1": {"orders": 2, "amount_cent": 300},
    }, "AC-FSP3 day3 window %r" % (after["day3"],)

    SNAP["fsp3_faces"] = _dump(after)
    SNAP["fsp3_before"] = before_dump
    SNAP["fsp3_db"] = w["db"]


def case_fsp4(tmp):
    """AC-FSP4: re-booking the original day-one inbox on the reopened
    carrier is idempotent - zero new rows - and the lifetime face does
    not move (primary-key idempotency, no double counting)."""
    w = _world(tmp, "fsp4")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
    finally:
        f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        g.book_orders(w["day3late"], DAY3)
        before = _dump(_faces(g))
        out = g.book_orders(w["day1"], DAY1)
        after = _dump(_faces(g))
    finally:
        g.close()

    assert out["orders_seen"] == 3 and out["orders_new"] == 0, \
        "AC-FSP4 re-book was not idempotent: %r" % (out,)
    assert after == before, "AC-FSP4 lifetime face moved on re-book"


def case_fsp5(tmp):
    """AC-FSP5: the default lifetime face drifts with the injected
    orders (6 -> 9) while the earlier windows stay constant, and the
    no-row day is an honest empty face at all three points in time
    (before the restart, after it, and after the injection)."""
    w = _world(tmp, "fsp5")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
        pre = _faces(f)
    finally:
        f.close()
    assert pre["no_rows"] == {}, "AC-FSP5 pre-restart no-row face"

    g = fd.FunnelDaily(w["db"])
    try:
        g.book_orders(w["day3late"], DAY3)
        post = _faces(g)
    finally:
        g.close()

    assert sum(b["orders"] for b in pre["lifetime"].values()) == 6
    assert sum(b["orders"] for b in post["lifetime"].values()) == 9, \
        "AC-FSP5 lifetime drift missing"
    assert _dump(post["day1"]) == _dump(pre["day1"]), \
        "AC-FSP5 day1 window drifted with lifetime growth"
    assert _dump(post["day2"]) == _dump(pre["day2"]), \
        "AC-FSP5 day2 window drifted with lifetime growth"
    assert post["no_rows"] == {}, "AC-FSP5 post-injection no-row face"


def case_fsp6(tmp):
    """AC-FSP6: pure-read law plus a zero-write restart - the order
    row set is identical before and after a full read batch, and the
    reopened instance sees exactly the rows the first one left."""
    w = _world(tmp, "fsp6")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
        rows_first = _rows(w["db"])
        count_first = _count(w["db"])
    finally:
        f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        rows_open = _rows(w["db"])
        _faces(g)
        _faces(g)
        rows_after = _rows(w["db"])
        count_after = _count(w["db"])
    finally:
        g.close()

    assert rows_open == rows_first, "AC-FSP6 restart wrote rows"
    assert rows_after == rows_first, "AC-FSP6 read batch wrote rows"
    assert count_after == count_first == 6, "AC-FSP6 row count drifted"


def case_fsp7(tmp):
    """AC-FSP7: a second restart keeps the injected state stable - the
    five faces still match the post-injection state, the day-one
    window still equals the original anchor snapshot, and the final
    order count is pinned."""
    w = _world(tmp, "fsp7")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
        anchor = _dump(_faces(f))
    finally:
        f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        g.book_orders(w["day3late"], DAY3)
        injected = _dump(_faces(g))
    finally:
        g.close()

    h = fd.FunnelDaily(w["db"])
    try:
        third = _faces(h)
        third_dump = _dump(third)
        count = _count(w["db"])
    finally:
        h.close()

    assert third_dump == injected, "AC-FSP7 faces drifted on 3rd open"
    anchor_faces = json.loads(anchor)
    assert _dump(third["day1"]) == _dump(anchor_faces["day1"]), \
        "AC-FSP7 day1 window thawed across double restart"
    assert third["no_rows"] == {}, "AC-FSP7 no-row face on 3rd open"
    assert count == 9, "AC-FSP7 final order count %r" % (count,)


def case_fsp8(tmp):
    """AC-FSP8: hygiene - pure ASCII suite source, AST-checked import
    and wall-clock faces (never a substring scan, which self-matches
    its own literals), and shipped config/library bytes unchanged.
    The double-run stdout identity is measured by the round's
    verification step, not inside the suite."""
    own = os.path.join(BASE, "test_funnel_sku_persist.py")
    raw = open(own, "rb").read()
    text = raw.decode("ascii")

    tree = ast.parse(text)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    for name in ("socket", "urllib", "http", "requests", "ssl"):
        assert name not in modules, "AC-FSP8 network import %s" % name

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("now", "today", "utcnow"), \
                "AC-FSP8 wall clock .%s" % node.attr
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "time":
                assert getattr(fn.value, "id", "") != "time", \
                    "AC-FSP8 wall clock time.time"

    cfg = os.path.join(BASE, "config.json")
    lib = os.path.join(BASE, "funnel_daily.py")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha, lib_sha = sha(cfg), sha(lib)
    w = _world(tmp, "fsp8")
    f = fd.FunnelDaily(w["db"])
    try:
        _book(f, w)
        f.sku_totals()
    finally:
        f.close()
    assert sha(cfg) == cfg_sha, "AC-FSP8 shipped config mutated"
    assert sha(lib) == lib_sha, "AC-FSP8 library source mutated"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-sku-persist-")
    cases = [
        ("AC-FSP1 anchor world and five-face snapshot", case_fsp1),
        ("AC-FSP2 restart byte identity", case_fsp2),
        ("AC-FSP3 late injection, earlier windows frozen", case_fsp3),
        ("AC-FSP4 cross-restart idempotent re-book", case_fsp4),
        ("AC-FSP5 lifetime drift, no-row honest empty", case_fsp5),
        ("AC-FSP6 pure-read law and zero-write restart", case_fsp6),
        ("AC-FSP7 double-restart stability", case_fsp7),
        ("AC-FSP8 hygiene", case_fsp8),
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