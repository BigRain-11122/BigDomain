"""Acceptance suite for funnel_daily late-arrival re-rollup on an
already-booked day (FUNNEL-LOOP v0.1, R2051).

Pre-registered criteria AC-FRL1..AC-FRL8 live in state/queue/tech.md
(the R2051 claim row) and were written BEFORE this suite existed
(honesty law). The window under test is the one the R2047 reseed row
named: source rows are INSERT OR IGNORE keyed and rollups are a
derived face rewritten with INSERT OR REPLACE, so when a late inbox
row for day D arrives AFTER D was rolled up, re-running run_daily(D)
must book the late row, re-derive the day-D counts, keep exactly one
rollup row per day, stay byte-identical on a second re-run, and leak
nothing into other days' stored envelopes.

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

PREV = "2026-10-19"
DAY = "2026-10-20"
NEXT = "2026-10-21"

TABLES = ("leads", "dispatches", "orders", "flows")


def _mk_inbox(root, name, rows, start=0):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % (start + i)), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _dump(env):
    return json.dumps(env, ensure_ascii=False, sort_keys=True)


def _rows(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT * FROM %s ORDER BY 1" % table).fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _count(db_path, table, where=""):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT COUNT(*) FROM %s%s" % (table, where)).fetchone()[0]
    finally:
        con.close()


def _stored(db_path, day):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT envelope, gate, hits FROM rollups WHERE day=?",
            (day,)).fetchone()
    finally:
        con.close()


def _world(tmp, name):
    """A previous day, a booked day D, and D's inbox dirs kept live so
    late rows can be dropped in after the first D run."""
    root = os.path.join(tmp, name)
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")

    prev = os.path.join(root, "prev")
    leads_p = _mk_inbox(prev, "leads", [
        {"lead_id": "L0", "source": "s", "text": "platform billing idea"}])
    orders_p = _mk_inbox(prev, "orders", [
        {"order_id": "O0", "sku": "compute-pack-19.9", "amount_cent": 1990}])
    flows_p = _mk_inbox(prev, "flows", [
        {"flow_id": "F0", "account": "u1", "kind": "grant", "amount": 40},
        {"flow_id": "F1", "account": "u1", "kind": "spend", "amount": 10}])

    day_dir = os.path.join(root, "day")
    leads_d = _mk_inbox(day_dir, "leads", [
        {"lead_id": "L1", "source": "s", "text": "game demo level"}])
    orders_d = _mk_inbox(day_dir, "orders", [
        {"order_id": "O1", "sku": "compute-pack-29.9", "amount_cent": 2990}])
    flows_d = _mk_inbox(day_dir, "flows", [
        {"flow_id": "F2", "account": "u1", "kind": "grant", "amount": 100},
        {"flow_id": "F3", "account": "u1", "kind": "spend", "amount": 30},
        {"flow_id": "F4", "account": "u1", "kind": "spend", "amount": 20}])

    next_dir = os.path.join(root, "next")
    leads_n = _mk_inbox(next_dir, "leads", [])
    orders_n = _mk_inbox(next_dir, "orders", [])
    flows_n = _mk_inbox(next_dir, "flows", [])

    return {
        "root": root, "db": db,
        "prev": (leads_p, orders_p, flows_p),
        "day": (leads_d, orders_d, flows_d),
        "next": (leads_n, orders_n, flows_n),
        "leads_d": leads_d, "orders_d": orders_d, "flows_d": flows_d,
    }


def _run(w, day, boxes):
    f = fd.FunnelDaily(w["db"])
    try:
        return f.run_daily(boxes[0], boxes[1], boxes[2], day)
    finally:
        f.close()


def _base(w):
    prev_out = _run(w, PREV, w["prev"])
    day_out = _run(w, DAY, w["day"])
    return prev_out, day_out


def _add_late(w, start):
    _mk_inbox(w["leads_d"], "", [
        {"lead_id": "L2", "source": "late", "text": "video clip subtitle"}],
        start=start)
    _mk_inbox(w["orders_d"], "", [
        {"order_id": "O2", "sku": "compute-pack-49.9", "amount_cent": 4990}],
        start=start)
    _mk_inbox(w["flows_d"], "", [
        {"flow_id": "F5", "account": "u2", "kind": "grant", "amount": 25}],
        start=start)


def _place(directory, rows, start):
    """Drop extra rows into an already-populated inbox dir."""
    for i, row in enumerate(rows):
        with open(os.path.join(directory, "%03d.json" % (start + i)), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)


def case_frl1(tmp):
    """AC-FRL1: a late row for day D books on the re-run, one row per
    source table, and D's first-round rows stay byte-frozen."""
    w = _world(tmp, "frl1")
    _base(w)
    before = dict((t, _rows(w["db"], t)) for t in TABLES)
    _place(w["leads_d"], [
        {"lead_id": "L2", "source": "late", "text": "video clip subtitle"}], 100)
    _place(w["orders_d"], [
        {"order_id": "O2", "sku": "compute-pack-49.9",
         "amount_cent": 4990}], 100)
    _place(w["flows_d"], [
        {"flow_id": "F5", "account": "u2", "kind": "spend", "amount": 20}], 100)
    out = _run(w, DAY, w["day"])
    after = dict((t, _rows(w["db"], t)) for t in TABLES)

    assert out["ring1"]["leads_new"] == 1, "AC-FRL1 late lead not booked"
    assert out["ring3"]["orders_new"] == 1, "AC-FRL1 late order not booked"
    assert out["ring4"]["flows_new"] == 1, "AC-FRL1 late flow not booked"
    assert out["ring2"]["dispatches_new"] == 1, \
        "AC-FRL1 late lead not dispatched same day"
    for table in TABLES:
        assert len(after[table]) == len(before[table]) + 1, \
            "AC-FRL1 %s row delta" % table
    for table in ("leads", "orders", "flows", "dispatches"):
        old = [r for r in before[table]]
        kept = [r for r in after[table] if r in old]
        assert len(kept) == len(old), \
            "AC-FRL1 %s first-round rows rewritten" % table
    assert ("L2", DAY, "late", "media", "video clip subtitle") in after["leads"], \
        "AC-FRL1 late lead row shape"
    assert ("O2", DAY, "compute-pack-49.9", 4990) in after["orders"], \
        "AC-FRL1 late order row shape"
    assert ("F5", DAY, "u2", "spend", 20) in after["flows"], \
        "AC-FRL1 late flow row shape"


def case_frl2(tmp):
    """AC-FRL2: the re-derived day-D envelope follows the late rows and
    the rollups face still holds exactly one row for D."""
    w = _world(tmp, "frl2")
    _, day_first = _base(w)
    first_counts = day_first["envelope"]["counts"]
    _add_late(w, 0)
    out = _run(w, DAY, w["day"])
    counts = out["envelope"]["counts"]

    assert counts["leads_day"] == first_counts["leads_day"] + 1, \
        "AC-FRL2 leads_day did not follow"
    assert counts["dispatches_day"] == first_counts["dispatches_day"] + 1, \
        "AC-FRL2 dispatches_day did not follow"
    assert counts["orders_day"] == first_counts["orders_day"] + 1, \
        "AC-FRL2 orders_day did not follow"
    assert counts["token_granted_day"] == 125, "AC-FRL2 granted_day"
    assert counts["token_spent_day"] == 50, "AC-FRL2 spent_day"
    assert counts["token_outstanding_total"] == 105, \
        "AC-FRL2 outstanding (165 granted - 60 spent)"
    assert _count(w["db"], "rollups", " WHERE day='%s'" % DAY) == 1, \
        "AC-FRL2 rollups grew a duplicate day row"
    stored = _stored(w["db"], DAY)[0]
    assert stored == _dump(out["envelope"]), \
        "AC-FRL2 stored envelope is not the re-derived one"


def case_frl3(tmp):
    """AC-FRL3: after the late absorption a second re-run of D books
    zero new rows and reproduces the envelope bytes exactly."""
    w = _world(tmp, "frl3")
    _base(w)
    _add_late(w, 0)
    first = _run(w, DAY, w["day"])
    counts_before = dict((t, _count(w["db"], t)) for t in TABLES)
    second = _run(w, DAY, w["day"])
    counts_after = dict((t, _count(w["db"], t)) for t in TABLES)

    for ring, key in (("ring1", "leads_new"), ("ring2", "dispatches_new"),
                      ("ring3", "orders_new"), ("ring4", "flows_new")):
        assert second[ring][key] == 0, "AC-FRL3 %s booked on re-run" % ring
    for table in TABLES:
        assert counts_before[table] == counts_after[table], \
            "AC-FRL3 %s row count drifted" % table
    assert _dump(second["envelope"]) == _dump(first["envelope"]), \
        "AC-FRL3 envelope drifted on the second re-run"


def case_frl4(tmp):
    """AC-FRL4: the earlier day's stored envelope stays byte-frozen and
    the re-derived D delta is still anchored to the PREV stored face."""
    w = _world(tmp, "frl4")
    prev_first, _ = _base(w)
    prev_stored_before = _stored(w["db"], PREV)[0]
    prev_rows_before = _count(w["db"], "rollups", " WHERE day='%s'" % PREV)
    _add_late(w, 0)
    out = _run(w, DAY, w["day"])

    assert _stored(w["db"], PREV)[0] == prev_stored_before, \
        "AC-FRL4 PREV stored envelope absorbed the D re-derive"
    assert _count(w["db"], "rollups", " WHERE day='%s'" % PREV) == prev_rows_before, \
        "AC-FRL4 PREV rollups row count drifted"
    delta = out["envelope"]["delta_prev_day"]
    assert delta is not None, "AC-FRL4 D lost its prev-day delta"
    assert set(delta) == set(fd._COUNT_KEYS), "AC-FRL4 delta key set"
    prev_counts = prev_first["envelope"]["counts"]
    expected = dict((k, out["envelope"]["counts"][k] - prev_counts[k])
                    for k in fd._COUNT_KEYS)
    assert delta == expected, "AC-FRL4 delta not anchored to PREV stored face"


def case_frl5(tmp):
    """AC-FRL5: the conservation identity holds after a late spend, and
    the day windows only see the late rows booked on that day."""
    w = _world(tmp, "frl5")
    _base(w)
    _place(w["flows_d"], [
        {"flow_id": "F5", "account": "u2", "kind": "spend", "amount": 20}], 100)
    out = _run(w, DAY, w["day"])
    counts = out["envelope"]["counts"]

    con = sqlite3.connect(w["db"])
    try:
        granted = con.execute(
            "SELECT COALESCE(SUM(amount),0) FROM flows WHERE kind='grant'"
        ).fetchone()[0]
        spent = con.execute(
            "SELECT COALESCE(SUM(amount),0) FROM flows WHERE kind='spend'"
        ).fetchone()[0]
    finally:
        con.close()
    assert counts["token_outstanding_total"] == granted - spent, \
        "AC-FRL5 outstanding identity broken"
    assert counts["token_outstanding_total"] == 60, \
        "AC-FRL5 outstanding value (140 granted - 80 spent)"
    assert counts["token_granted_day"] == 100, "AC-FRL5 day grant window"
    assert counts["token_spent_day"] == 70, "AC-FRL5 day spend window"
    assert counts["leads_day"] == 1, "AC-FRL5 day lead window"
    assert counts["orders_day"] == 1, "AC-FRL5 day order window"


def case_frl6(tmp):
    """AC-FRL6: a late row that duplicates an existing day-D id with a
    different payload is a no-op on every face (first write wins)."""
    w = _world(tmp, "frl6")
    _base(w)
    rows_before = dict((t, _rows(w["db"], t)) for t in TABLES)
    env_before = _stored(w["db"], DAY)[0]
    _place(w["leads_d"], [
        {"lead_id": "L1", "source": "late", "text": "quant factor"}], 100)
    _place(w["orders_d"], [
        {"order_id": "O1", "sku": "changed", "amount_cent": 9999}], 100)
    _place(w["flows_d"], [
        {"flow_id": "F2", "account": "u9", "kind": "spend", "amount": 7}], 100)
    out = _run(w, DAY, w["day"])
    rows_after = dict((t, _rows(w["db"], t)) for t in TABLES)

    for ring, key in (("ring1", "leads_new"), ("ring2", "dispatches_new"),
                      ("ring3", "orders_new"), ("ring4", "flows_new")):
        assert out[ring][key] == 0, "AC-FRL6 %s booked a duplicate" % ring
    for table in TABLES:
        assert rows_before[table] == rows_after[table], \
            "AC-FRL6 %s drifted on a duplicate late row" % table
    assert _stored(w["db"], DAY)[0] == env_before, \
        "AC-FRL6 envelope changed on a duplicate late row"


def case_frl7(tmp):
    """AC-FRL7: the correction propagates forward - the next day's
    delta is computed off the corrected D face, and D stays frozen."""
    w = _world(tmp, "frl7")
    _base(w)
    _add_late(w, 0)
    corrected = _run(w, DAY, w["day"])
    day_stored = _stored(w["db"], DAY)[0]
    out = _run(w, NEXT, w["next"])
    counts = out["envelope"]["counts"]
    delta = out["envelope"]["delta_prev_day"]

    assert counts["leads_day"] == 0 and counts["orders_day"] == 0, \
        "AC-FRL7 NEXT booked rows from an empty inbox"
    assert delta is not None, "AC-FRL7 NEXT lost its prev-day delta"
    assert set(delta) == set(fd._COUNT_KEYS), "AC-FRL7 NEXT delta key set"
    expected = dict((k, counts[k] - corrected["envelope"]["counts"][k])
                    for k in fd._COUNT_KEYS)
    assert delta == expected, "AC-FRL7 NEXT delta not off the corrected D face"
    assert delta["leads_day"] == -2, "AC-FRL7 NEXT leads delta"
    assert delta["token_granted_day"] == -125, "AC-FRL7 NEXT granted delta"
    assert delta["token_spent_day"] == -50, "AC-FRL7 NEXT spent delta"
    assert delta["token_outstanding_total"] == 0, \
        "AC-FRL7 NEXT lifetime delta (85 -> 85)"
    assert _stored(w["db"], DAY)[0] == day_stored, \
        "AC-FRL7 D stored envelope drifted after the NEXT run"


def case_frl8(tmp):
    """AC-FRL8: hygiene - pure ASCII suite source, no network imports,
    no wall-clock calls, shipped config and library bytes unchanged.
    The import/clock faces are read off the parsed AST (the R2048
    substring lesson applied at birth)."""
    own = os.path.join(BASE, "test_funnel_rerollup.py")
    text = open(own, "rb").read().decode("ascii")

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
        assert name not in modules, "AC-FRL8 network import %s" % name

    clock_attrs = ("now", "today", "utcnow")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in clock_attrs, \
                "AC-FRL8 wall clock .%s" % node.attr
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "time":
                assert getattr(fn.value, "id", "") != "time", \
                    "AC-FRL8 wall clock time.time"

    cfg = os.path.join(BASE, "config.json")
    lib = os.path.join(BASE, "funnel_daily.py")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha, lib_sha = sha(cfg), sha(lib)
    w = _world(tmp, "frl8")
    _base(w)
    _add_late(w, 0)
    out = _run(w, DAY, w["day"])
    assert out["envelope"]["gate"] == "PASS", "AC-FRL8 gate"
    assert sha(cfg) == cfg_sha, "AC-FRL8 shipped config mutated"
    assert sha(lib) == lib_sha, "AC-FRL8 library source mutated"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-rerollup-")
    cases = [
        ("AC-FRL1 late row booked, first-round rows frozen", case_frl1),
        ("AC-FRL2 re-derived counts follow, one rollup row", case_frl2),
        ("AC-FRL3 second re-run stable", case_frl3),
        ("AC-FRL4 other-day freeze and delta anchor", case_frl4),
        ("AC-FRL5 conservation after a late spend", case_frl5),
        ("AC-FRL6 duplicate late id is a no-op", case_frl6),
        ("AC-FRL7 correction propagates forward", case_frl7),
        ("AC-FRL8 hygiene", case_frl8),
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