"""Acceptance suite for the funnel order-sku type gate (R2061).

Pre-registered criteria AC-FSK1..AC-FSK8 live in state/queue/tech.md
(the R2061 claim row) and were written BEFORE this suite existed
(honesty law). The window under test is the gap the R2058 claim round
found in the shipped code: book_orders stringified the sku with a bare
str() call, so an integer booked as "5" and a list / dict booked as its
Python repr - while order_id and amount_cent both had strict type
doors. The ruling registered with this window is: absent -> the honest
blank bucket; JSON scalars -> a declared canonical text form; a
container -> E_FN_BAD_ARGS with zero new rows (the zero-row law).

The library is exercised as shipped - this file changes nothing under
test. Pure ASCII source: non-ASCII is injected through escapes so no
non-ASCII literal enters this file (coding law).
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


def _inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _world(tmp, name, orders_rows, flows_rows=None):
    root = os.path.join(tmp, name)
    os.makedirs(root, exist_ok=True)
    return {
        "root": root,
        "db": os.path.join(root, "funnel.db"),
        "orders": _inbox(root, "orders", orders_rows),
        "flows": _inbox(root, "flows", flows_rows or []),
    }


def _skus(db_path):
    con = sqlite3.connect(db_path)
    try:
        return dict(con.execute("SELECT order_id, sku FROM orders"))
    finally:
        con.close()


def _count(db_path):
    con = sqlite3.connect(db_path)
    try:
        return con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    finally:
        con.close()


def case_fsk1(tmp):
    """AC-FSK1: absence stays the honest blank bucket - a missing sku
    key and an explicit null both land as text "" and appear as the
    blank bucket of sku_totals / sku_top, exactly as before the gate."""
    w = _world(tmp, "fsk1", [
        {"order_id": "O1", "amount_cent": 100},
        {"order_id": "O2", "sku": None, "amount_cent": 200},
    ])
    f = fd.FunnelDaily(w["db"])
    try:
        out = f.book_orders(w["orders"], DAY1)
        totals = f.sku_totals()
        top = f.sku_top(5)
    finally:
        f.close()
    assert out["orders_new"] == 2, "AC-FSK1 rows not booked"
    assert _skus(w["db"]) == {"O1": "", "O2": ""}, "AC-FSK1 sku text"
    assert totals == {"": {"orders": 2, "amount_cent": 300}}, \
        "AC-FSK1 blank bucket law"
    assert top[0]["sku"] == "" and top[0]["rank"] == 1, \
        "AC-FSK1 blank bucket competes for rank"


def case_fsk2(tmp):
    """AC-FSK2: text skus are stored verbatim - no trimming, no case
    folding, no escaping (a leading/trailing space and a non-ASCII
    escape survive byte-for-byte as one bucket)."""
    wordy = " \u96fb\u8111\u5305 "  # " compute pack " in CJK escapes
    w = _world(tmp, "fsk2", [
        {"order_id": "O1", "sku": "compute-pack-19.9", "amount_cent": 1990},
        {"order_id": "O2", "sku": "Compute-Pack-19.9", "amount_cent": 1},
        {"order_id": "O3", "sku": wordy, "amount_cent": 2},
    ])
    f = fd.FunnelDaily(w["db"])
    try:
        f.book_orders(w["orders"], DAY1)
        totals = f.sku_totals()
    finally:
        f.close()
    rows = _skus(w["db"])
    assert rows["O1"] == "compute-pack-19.9", "AC-FSK2 verbatim"
    assert rows["O2"] == "Compute-Pack-19.9", "AC-FSK2 case folded"
    assert rows["O3"] == wordy, "AC-FSK2 whitespace trimmed"
    assert set(totals) == {"compute-pack-19.9", "Compute-Pack-19.9", wordy}, \
        "AC-FSK2 buckets merged"


def case_fsk3(tmp):
    """AC-FSK3: JSON scalars take the declared canonical form -
    integers as decimal digits, floats by shortest repr, booleans as
    the lower-case JSON literals - and the canonical form is what the
    read faces bucket on (an int 5 and the text "5" are one bucket,
    the documented consequence of a single canonical text form)."""
    w = _world(tmp, "fsk3", [
        {"order_id": "O1", "sku": 5, "amount_cent": 10},
        {"order_id": "O2", "sku": -3, "amount_cent": 20},
        {"order_id": "O3", "sku": 2.5, "amount_cent": 30},
        {"order_id": "O4", "sku": True, "amount_cent": 40},
        {"order_id": "O5", "sku": False, "amount_cent": 50},
        {"order_id": "O6", "sku": "5", "amount_cent": 60},
    ])
    f = fd.FunnelDaily(w["db"])
    try:
        f.book_orders(w["orders"], DAY1)
        totals = f.sku_totals()
    finally:
        f.close()
    rows = _skus(w["db"])
    assert rows["O1"] == "5", "AC-FSK3 int canonical"
    assert rows["O2"] == "-3", "AC-FSK3 negative int canonical"
    assert rows["O3"] == "2.5", "AC-FSK3 float canonical"
    assert rows["O4"] == "true", "AC-FSK3 bool true canonical"
    assert rows["O5"] == "false", "AC-FSK3 bool false canonical"
    assert "True" not in rows.values(), "AC-FSK3 python bool repr leaked"
    assert totals["5"] == {"orders": 2, "amount_cent": 70}, \
        "AC-FSK3 canonical bucket merge (int 5 + text 5)"
    assert totals["true"]["orders"] == 1 and totals["false"]["orders"] == 1, \
        "AC-FSK3 boolean buckets"


def case_fsk4(tmp):
    """AC-FSK4: a container sku has no stable data identity, so it
    rejects the whole ring - E_FN_BAD_ARGS, zero new order rows, and
    the good file in the same inbox is not booked either (all-or-
    nothing per ring, the zero-row law)."""
    for name, bad in (("fsk4a", [1, 2]), ("fsk4b", {"a": 1})):
        w = _world(tmp, name, [
            {"order_id": "OK", "sku": "good-sku", "amount_cent": 100},
            {"order_id": "BAD", "sku": bad, "amount_cent": 200},
        ])
        f = fd.FunnelDaily(w["db"])
        try:
            try:
                f.book_orders(w["orders"], DAY1)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, \
                    "AC-FSK4 error code %r" % str(exc)
            else:
                raise AssertionError("AC-FSK4 container accepted (%s)" % name)
        finally:
            f.close()
        assert _count(w["db"]) == 0, "AC-FSK4 rows booked (%s)" % name
        assert _skus(w["db"]) == {}, "AC-FSK4 sku face touched (%s)" % name


def case_fsk5(tmp):
    """AC-FSK5: the gate does not disturb the idempotency key law - a
    replayed order_id books zero new rows and never rewrites the sku
    already on disk, even when the replay carries a different sku."""
    w = _world(tmp, "fsk5", [
        {"order_id": "O1", "sku": 7, "amount_cent": 100},
    ])
    f = fd.FunnelDaily(w["db"])
    try:
        first = f.book_orders(w["orders"], DAY1)
        again = f.book_orders(w["orders"], DAY1)
        rewrite = _inbox(w["root"], "orders2", [
            {"order_id": "O1", "sku": "other-sku", "amount_cent": 999},
        ])
        third = f.book_orders(rewrite, DAY1)
    finally:
        f.close()
    assert first["orders_new"] == 1, "AC-FSK5 first booking"
    assert again["orders_new"] == 0, "AC-FSK5 replay booked again"
    assert third["orders_new"] == 0, "AC-FSK5 replay rewrote the row"
    assert _count(w["db"]) == 1, "AC-FSK5 row count"
    assert _skus(w["db"]) == {"O1": "7"}, "AC-FSK5 stored sku drifted"


def case_fsk6(tmp):
    """AC-FSK6: an explicit empty string stays its own blank bucket and
    never merges into a named sku (the blank-bucket law of the read
    faces holds under the new canonical form)."""
    w = _world(tmp, "fsk6", [
        {"order_id": "O1", "sku": "", "amount_cent": 10},
        {"order_id": "O2", "sku": "empty", "amount_cent": 20},
    ])
    f = fd.FunnelDaily(w["db"])
    try:
        f.book_orders(w["orders"], DAY1)
        totals = f.sku_totals()
    finally:
        f.close()
    assert totals[""] == {"orders": 1, "amount_cent": 10}, \
        "AC-FSK6 blank bucket"
    assert totals["empty"] == {"orders": 1, "amount_cent": 20}, \
        "AC-FSK6 named bucket"


def case_fsk7(tmp):
    """AC-FSK7: hygiene - the suite source is pure ASCII, carries zero
    network imports and zero wall-clock calls (read off the parsed AST,
    never by substring scan), and the shipped config plus the library
    bytes are unchanged by a run."""
    own = os.path.join(BASE, "test_funnel_sku_gate.py")
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
        assert name not in modules, "AC-FSK7 network import %s" % name
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("now", "today", "utcnow"), \
                "AC-FSK7 wall clock .%s" % node.attr
    assert "funnel_daily." in text

    cfg = os.path.join(BASE, "config.json")
    lib = os.path.join(BASE, "funnel_daily.py")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha, lib_sha = sha(cfg), sha(lib)
    w = _world(tmp, "fsk7", [
        {"order_id": "O1", "sku": 5, "amount_cent": 10},
    ])
    f = fd.FunnelDaily(w["db"])
    try:
        out = f.book_orders(w["orders"], DAY1)
    finally:
        f.close()
    assert out["orders_new"] == 1
    assert sha(cfg) == cfg_sha, "AC-FSK7 shipped config mutated"
    assert sha(lib) == lib_sha, "AC-FSK7 library mutated during run"
    closed = json.load(open(cfg, encoding="utf-8"))
    assert isinstance(closed.get("banned_words"), list) and \
        isinstance(closed.get("standing_lines"), dict), \
        "AC-FSK7 config shape"


def case_fsk8(tmp):
    """AC-FSK8: the window is wired into the reconciliation battery -
    reconcile_all's registry carries the funnel-sku-gate entry with the
    registered criteria count, declared before the suite was counted
    green."""
    reg = os.path.join(BASE, "..", "reconcile_all.py")
    text = open(reg, encoding="utf-8").read()
    assert '"funnel-sku-gate"' in text, "AC-FSK8 registry entry absent"
    assert 'test_funnel_sku_gate.py' in text, "AC-FSK8 suite path absent"
    tail = text.split('"funnel-sku-gate"', 1)[1][:200]
    assert ", 8)" in tail, "AC-FSK8 criteria count not 8"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-sku-gate-")
    cases = [
        ("AC-FSK1 absent sku blank bucket", case_fsk1),
        ("AC-FSK2 text sku verbatim", case_fsk2),
        ("AC-FSK3 scalar canonical form", case_fsk3),
        ("AC-FSK4 container rejects ring", case_fsk4),
        ("AC-FSK5 idempotency key law intact", case_fsk5),
        ("AC-FSK6 explicit empty string bucket", case_fsk6),
        ("AC-FSK7 hygiene", case_fsk7),
        ("AC-FSK8 battery wiring", case_fsk8),
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