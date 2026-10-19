"""Acceptance suite for funnel_daily inbox cross-day re-scan
idempotency and first-write-wins attribution (FUNNEL-LOOP v0.1, R2050).

Pre-registered criteria AC-FRS1..AC-FRS8 live in state/queue/tech.md
(the R2050 claim row) and were written BEFORE this suite existed
(honesty law). The window under test is the one the R2047 reseed row
named: the source tables are INSERT OR IGNORE keyed, so when an id is
re-scanned on a LATER day with a different payload the first day's row
must stay byte-frozen, the day-two ring counters must only count new
ids, the day-scoped rollup counts must not absorb earlier days while
the lifetime outstanding face keeps the whole ledger, and the
dispatches full-table re-scan must book only genuinely new leads.

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

DAY1 = "2026-10-19"
DAY2 = "2026-10-20"

TABLES = ("leads", "dispatches", "orders", "flows")
DAY1_KEYS = {"leads": ("L1",), "dispatches": ("L1",),
             "orders": ("O1",), "flows": ("F1",)}


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
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


def _count(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return con.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    finally:
        con.close()


def _stored_rollup(db_path, day):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT envelope, gate, hits FROM rollups WHERE day=?",
            (day,)).fetchone()
    finally:
        con.close()


def _world(tmp, name):
    """Two populated days over one carrier.

    Day one: leads L1/L2, order O1, flows F1 grant 100 / F2 spend 30.
    Day two: L1 and O1 and F1 re-appear with DIFFERENT payloads plus
    one genuinely new row per source table (L3/O2/F3).
    """
    root = os.path.join(tmp, name)
    os.makedirs(root)
    d1 = os.path.join(root, "d1")
    d2 = os.path.join(root, "d2")
    os.makedirs(d2)
    leads1 = _mk_inbox(d1, "leads", [
        {"lead_id": "L1", "source": "s", "text": "I want a game demo level"},
        {"lead_id": "L2", "source": "s", "text": "persona story for a resident"},
    ])
    orders1 = _mk_inbox(d1, "orders", [
        {"order_id": "O1", "sku": "compute-pack-19.9", "amount_cent": 1990},
    ])
    flows1 = _mk_inbox(d1, "flows", [
        {"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 100},
        {"flow_id": "F2", "account": "u1", "kind": "spend", "amount": 30},
    ])
    leads2 = _mk_inbox(d2, "leads", [
        {"lead_id": "L1", "source": "s2", "text": "quant strategy factor"},
        {"lead_id": "L3", "source": "s2", "text": "video clip script"},
    ])
    orders2 = _mk_inbox(d2, "orders", [
        {"order_id": "O1", "sku": "changed-sku", "amount_cent": 9999},
        {"order_id": "O2", "sku": "compute-pack-29.9", "amount_cent": 2990},
    ])
    flows2 = _mk_inbox(d2, "flows", [
        {"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 999},
        {"flow_id": "F3", "account": "u2", "kind": "grant", "amount": 50},
    ])
    return {
        "root": root,
        "db": os.path.join(root, "funnel.db"),
        "leads1": leads1, "orders1": orders1, "flows1": flows1,
        "leads2": leads2, "orders2": orders2, "flows2": flows2,
    }


def _run_day1(w):
    f = fd.FunnelDaily(w["db"])
    try:
        return f.run_daily(w["leads1"], w["orders1"], w["flows1"], DAY1)
    finally:
        f.close()


def _run_day2(w):
    f = fd.FunnelDaily(w["db"])
    try:
        return f.run_daily(w["leads2"], w["orders2"], w["flows2"], DAY2)
    finally:
        f.close()


def case_frs1(tmp):
    """AC-FRS1: first write wins on all three keyed source tables -
    a day-two re-scan of the same ids with different payloads leaves
    the day-one rows byte-frozen (new rows are pure tail additions)."""
    w = _world(tmp, "frs1")
    _run_day1(w)
    before = dict((t, _rows(w["db"], t)) for t in TABLES)
    _run_day2(w)
    after = dict((t, _rows(w["db"], t)) for t in TABLES)

    for table in ("leads", "orders", "flows"):
        keys = DAY1_KEYS[table]
        old_before = [r for r in before[table] if r[0] in keys]
        old_after = [r for r in after[table] if r[0] in keys]
        assert old_before, "AC-FRS1 %s day-one seed missing" % table
        assert old_before == old_after, \
            "AC-FRS1 %s day-one rows rewritten by re-scan" % table
        assert len(after[table]) == len(before[table]) + 1, \
            "AC-FRS1 %s did not add exactly one new row" % table

    assert after["leads"] == [("L1", DAY1, "s", "game",
                               "I want a game demo level"),
                              ("L2", DAY1, "s", "life",
                               "persona story for a resident"),
                              ("L3", DAY2, "s2", "media",
                               "video clip script")], \
        "AC-FRS1 leads table drifted"
    assert after["orders"] == [("O1", DAY1, "compute-pack-19.9", 1990),
                               ("O2", DAY2, "compute-pack-29.9", 2990)], \
        "AC-FRS1 orders table drifted"
    assert after["flows"] == [("F1", DAY1, "u1", "grant", 100),
                              ("F2", DAY1, "u1", "spend", 30),
                              ("F3", DAY2, "u2", "grant", 50)], \
        "AC-FRS1 flows table drifted"


def case_frs2(tmp):
    """AC-FRS2: day-two ring counters count only genuinely new ids
    while the seen/files counters still read the whole inbox."""
    w = _world(tmp, "frs2")
    _run_day1(w)
    out = _run_day2(w)
    r1, r2, r3, r4 = out["ring1"], out["ring2"], out["ring3"], out["ring4"]
    assert r1["files_leads"] == 2, "AC-FRS2 lead inbox not re-read"
    assert r1["leads_seen"] == 2, "AC-FRS2 leads_seen"
    assert r1["leads_new"] == 1, "AC-FRS2 leads_new"
    assert r2["dispatches_new"] == 1, "AC-FRS2 dispatches_new"
    assert r2["routes"] == {"media": 1}, "AC-FRS2 routes"
    assert r3["orders_seen"] == 2, "AC-FRS2 orders_seen"
    assert r3["orders_new"] == 1, "AC-FRS2 orders_new"
    assert r4["flows_seen"] == 2, "AC-FRS2 flows_seen"
    assert r4["flows_new"] == 1, "AC-FRS2 flows_new"


def case_frs3(tmp):
    """AC-FRS3: day-window counts exclude earlier days while the
    lifetime outstanding face keeps the whole ledger."""
    w = _world(tmp, "frs3")
    _run_day1(w)
    out = _run_day2(w)
    counts = out["envelope"]["counts"]
    assert counts["leads_day"] == 1, "AC-FRS3 leads_day"
    assert counts["dispatches_day"] == 1, "AC-FRS3 dispatches_day"
    assert counts["orders_day"] == 1, "AC-FRS3 orders_day"
    assert counts["token_granted_day"] == 50, "AC-FRS3 granted_day"
    assert counts["token_spent_day"] == 0, "AC-FRS3 spent_day"
    assert counts["token_outstanding_total"] == 120, \
        "AC-FRS3 lifetime outstanding (150 granted - 30 spent)"


def case_frs4(tmp):
    """AC-FRS4: the dispatches full-table re-scan books only new
    leads, and an old lead keeps its original dispatch day."""
    w = _world(tmp, "frs4")
    _run_day1(w)
    _run_day2(w)
    rows_before = _rows(w["db"], "dispatches")
    f = fd.FunnelDaily(w["db"])
    try:
        again = f.dispatch_leads(DAY2)
        rows_after = _rows(w["db"], "dispatches")
    finally:
        f.close()
    assert again["dispatches_new"] == 0, "AC-FRS4 re-scan booked rows"
    assert again["routes"] == {}, "AC-FRS4 re-scan reported routes"
    assert rows_before == rows_after, "AC-FRS4 dispatches table drifted"
    day_by_lead = dict((r[0], r[1]) for r in rows_after)
    assert day_by_lead["L1"] == DAY1, "AC-FRS4 L1 dispatch day rewritten"
    assert day_by_lead["L2"] == DAY1, "AC-FRS4 L2 dispatch day"
    assert day_by_lead["L3"] == DAY2, "AC-FRS4 L3 dispatch day"
    assert len(rows_after) == 3, "AC-FRS4 duplicate dispatch row"


def case_frs5(tmp):
    """AC-FRS5: with cross-day history present, re-running the same
    day books zero new rows and reproduces the envelope bytes."""
    w = _world(tmp, "frs5")
    _run_day1(w)
    first = _run_day2(w)
    env_first = _dump(first["envelope"])
    counts_before = dict((t, _count(w["db"], t)) for t in TABLES)
    second = _run_day2(w)
    counts_after = dict((t, _count(w["db"], t)) for t in TABLES)
    for ring, key in (("ring1", "leads_new"), ("ring2", "dispatches_new"),
                      ("ring3", "orders_new"), ("ring4", "flows_new")):
        assert second[ring][key] == 0, "AC-FRS5 %s booked on replay" % ring
    for t in TABLES:
        assert counts_before[t] == counts_after[t], \
            "AC-FRS5 %s row count drifted on replay" % t
    assert _dump(second["envelope"]) == env_first, \
        "AC-FRS5 day-two envelope drifted on replay"


def case_frs6(tmp):
    """AC-FRS6: the earlier day's STORED envelope stays byte-frozen
    after later work, and each day owns exactly one rollup row. Re-
    deriving the old day is checked as a dual face (R2050 amendment,
    found by the first run): the day-scoped counts and the other
    envelope fields reproduce exactly, while token_outstanding_total
    is a lifetime face that follows the whole ledger (70 -> 120 once
    day two books a grant). That key is compared separately, never as
    part of a whole-envelope byte identity."""
    w = _world(tmp, "frs6")
    first = _run_day1(w)
    env_day1 = _dump(first["envelope"])
    stored_before = _stored_rollup(w["db"], DAY1)[0]
    _run_day2(w)
    f = fd.FunnelDaily(w["db"])
    try:
        stored_after = _stored_rollup(w["db"], DAY1)[0]
        redo = f.rollup(DAY1)
        day_rows = _count(w["db"], "rollups")
    finally:
        f.close()
    assert stored_before.encode("utf-8") == stored_after.encode("utf-8"), \
        "AC-FRS6 day-one stored envelope drifted without a re-derive"
    original = json.loads(env_day1)
    for key in ("day", "delta_prev_day", "verdict_line", "focus",
                "standing_lines", "gate", "hits"):
        assert redo[key] == original[key], \
            "AC-FRS6 re-derive drifted on %s" % key
    day_scoped = dict((k, v) for k, v in redo["counts"].items()
                      if k != "token_outstanding_total")
    original_scoped = dict((k, v) for k, v in original["counts"].items()
                           if k != "token_outstanding_total")
    assert day_scoped == original_scoped, \
        "AC-FRS6 re-derive rewrote day-scoped counts"
    assert original["counts"]["token_outstanding_total"] == 70, \
        "AC-FRS6 original lifetime face"
    assert redo["counts"]["token_outstanding_total"] == 120, \
        "AC-FRS6 re-derive must refresh the lifetime face"
    assert day_rows == 2, "AC-FRS6 rollups day-row count"


def case_frs7(tmp):
    """AC-FRS7: the day-two delta closes over the previous day, day
    one has no delta, and the day windows do not cross-penetrate."""
    w = _world(tmp, "frs7")
    day1 = _run_day1(w)
    day2 = _run_day2(w)
    assert day1["envelope"]["delta_prev_day"] is None, \
        "AC-FRS7 day one grew a prev-day delta"
    delta = day2["envelope"]["delta_prev_day"]
    assert delta is not None, "AC-FRS7 day two lost the prev-day delta"
    assert set(delta) == set(fd._COUNT_KEYS), "AC-FRS7 delta key set"
    assert delta["leads_day"] == -1, "AC-FRS7 leads delta"
    assert delta["dispatches_day"] == -1, "AC-FRS7 dispatches delta"
    assert delta["orders_day"] == 0, "AC-FRS7 orders delta"
    assert delta["token_granted_day"] == -50, "AC-FRS7 granted delta"
    assert delta["token_spent_day"] == -30, "AC-FRS7 spent delta"
    assert delta["token_outstanding_total"] == 50, \
        "AC-FRS7 lifetime outstanding delta"

    d1_counts = json.loads(_stored_rollup(w["db"], DAY1)[0])["counts"]
    d2_counts = json.loads(_stored_rollup(w["db"], DAY2)[0])["counts"]
    assert d1_counts["leads_day"] == 2 and d2_counts["leads_day"] == 1, \
        "AC-FRS7 day windows cross-penetrated"
    assert d1_counts["token_outstanding_total"] == 70, \
        "AC-FRS7 day-one lifetime face absorbed day two"


def case_frs8(tmp):
    """AC-FRS8: hygiene - pure ASCII suite source, no network imports,
    no wall-clock calls, shipped config and library bytes unchanged.
    The import/clock faces are read off the parsed AST (the R2048
    substring lesson applied at birth)."""
    own = os.path.join(BASE, "test_funnel_rescan.py")
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
        assert name not in modules, "AC-FRS8 network import %s" % name

    clock_attrs = ("now", "today", "utcnow")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in clock_attrs, \
                "AC-FRS8 wall clock .%s" % node.attr
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "time":
                assert getattr(fn.value, "id", "") != "time", \
                    "AC-FRS8 wall clock time.time"

    cfg = os.path.join(BASE, "config.json")
    lib = os.path.join(BASE, "funnel_daily.py")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha, lib_sha = sha(cfg), sha(lib)
    w = _world(tmp, "frs8")
    _run_day1(w)
    out = _run_day2(w)
    assert out["envelope"]["gate"] == "PASS", "AC-FRS8 gate"
    assert sha(cfg) == cfg_sha, "AC-FRS8 shipped config mutated"
    assert sha(lib) == lib_sha, "AC-FRS8 library source mutated"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-rescan-")
    cases = [
        ("AC-FRS1 first-write-wins on source tables", case_frs1),
        ("AC-FRS2 cross-day new-count arithmetic", case_frs2),
        ("AC-FRS3 day window vs lifetime account", case_frs3),
        ("AC-FRS4 dispatch full-table re-scan", case_frs4),
        ("AC-FRS5 same-day replay with history", case_frs5),
        ("AC-FRS6 earlier-day envelope frozen", case_frs6),
        ("AC-FRS7 prev-day delta closure", case_frs7),
        ("AC-FRS8 hygiene", case_frs8),
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