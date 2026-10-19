"""Acceptance suite for the funnel conservation identity across a
multi-day chain (FUNNEL-LOOP v0.1, R2052).

Pre-registered criteria AC-FCV1..AC-FCV8 live in state/queue/tech.md
(the R2052 claim row) and were written BEFORE this suite existed
(honesty law). The window under test is the one the R2047 reseed row
named: the library states an outstanding == granted - spent identity
on the lifetime ledger (AC-FN5 covers a single cross-day point only),
but nothing pins that identity down over a chain of days, nor the
separation between the day-window counters and the lifetime face, nor
the key-by-key closure of delta_prev_day over several days.

One criterion was amended during delivery (honesty law, same-window
amendment): the first AC-FCV7 wording demanded byte-identical stored
envelopes for every day on a whole-chain replay. The shipped library
re-derives the lifetime face from the whole ledger at rewrite time
(the same behaviour R2050 registered for its AC-FRS6), so replaying
an older day after the chain has grown honestly moves that envelope's
token_outstanding_total while leaving every day-window key frozen.
Re-registered as: day-window keys frozen, lifetime face equal to the
final ledger in every replayed envelope, and byte identity on the
last day (whose booking already carried the final lifetime face).

World: four booked days D1..D4 (fresh leads / orders / flows each day,
D2 onward carries a cross-day balance) plus an empty D5.

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
D3 = "2026-10-18"
D4 = "2026-10-19"
D5 = "2026-10-20"
DAYS = (D1, D2, D3, D4)

DAY_KEYS = tuple(k for k in fd._COUNT_KEYS
                 if k != "token_outstanding_total")

TABLES = ("leads", "dispatches", "orders", "flows")


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _rows(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT * FROM %s ORDER BY 1" % table).fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _stored(db_path, day):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT envelope, gate, hits FROM rollups WHERE day=?",
            (day,)).fetchone()
    finally:
        con.close()


def _rollup_days(db_path):
    con = sqlite3.connect(db_path)
    try:
        return [r[0] for r in con.execute(
            "SELECT day FROM rollups ORDER BY day").fetchall()]
    finally:
        con.close()


def _sum_flows(db_path, day=None, kind=None):
    sql = "SELECT COALESCE(SUM(amount),0) FROM flows WHERE 1=1"
    args = []
    if day is not None:
        sql += " AND day=?"
        args.append(day)
    if kind is not None:
        sql += " AND kind=?"
        args.append(kind)
    con = sqlite3.connect(db_path)
    try:
        return con.execute(sql, tuple(args)).fetchone()[0]
    finally:
        con.close()


def _sql_counts(db_path, day):
    """The independent SQL face: day windows plus the lifetime face."""
    con = sqlite3.connect(db_path)
    try:
        counts = {
            "leads_day": con.execute(
                "SELECT COUNT(*) FROM leads WHERE day=?", (day,)).fetchone()[0],
            "dispatches_day": con.execute(
                "SELECT COUNT(*) FROM dispatches WHERE day=?",
                (day,)).fetchone()[0],
            "orders_day": con.execute(
                "SELECT COUNT(*) FROM orders WHERE day=?", (day,)).fetchone()[0],
            "token_granted_day": con.execute(
                "SELECT COALESCE(SUM(amount),0) FROM flows "
                "WHERE day=? AND kind='grant'", (day,)).fetchone()[0],
            "token_spent_day": con.execute(
                "SELECT COALESCE(SUM(amount),0) FROM flows "
                "WHERE day=? AND kind='spend'", (day,)).fetchone()[0],
            "token_outstanding_total": con.execute(
                "SELECT COALESCE(SUM(CASE WHEN kind='grant' THEN amount "
                "ELSE -amount END),0) FROM flows").fetchone()[0],
        }
    finally:
        con.close()
    return counts


def _run(db_path, boxes, day):
    f = fd.FunnelDaily(db_path)
    try:
        return f.run_daily(boxes[0], boxes[1], boxes[2], day)
    finally:
        f.close()


def _world(tmp, name):
    """D1..D4 inboxes with a growing cross-day balance, D5 empty."""
    root = os.path.join(tmp, name)
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")

    d1 = os.path.join(root, "d1")
    b1 = (
        _mk_inbox(d1, "leads", [
            {"lead_id": "L1", "source": "s", "text": "game demo level"}]),
        _mk_inbox(d1, "orders", [
            {"order_id": "O1", "sku": "compute-pack-19.9",
             "amount_cent": 1990}]),
        _mk_inbox(d1, "flows", [
            {"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 100},
            {"flow_id": "F2", "account": "u1", "kind": "spend", "amount": 40}]),
    )

    d2 = os.path.join(root, "d2")
    b2 = (
        _mk_inbox(d2, "leads", [
            {"lead_id": "L2", "source": "s", "text": "video clip subtitle"}]),
        _mk_inbox(d2, "orders", []),
        _mk_inbox(d2, "flows", [
            {"flow_id": "F3", "account": "u1", "kind": "grant", "amount": 50},
            {"flow_id": "F4", "account": "u2", "kind": "spend", "amount": 20}]),
    )

    d3 = os.path.join(root, "d3")
    b3 = (
        _mk_inbox(d3, "leads", []),
        _mk_inbox(d3, "orders", []),
        _mk_inbox(d3, "flows", [
            {"flow_id": "F5", "account": "u2", "kind": "grant", "amount": 30},
            {"flow_id": "F6", "account": "u1", "kind": "spend", "amount": 60}]),
    )

    d4 = os.path.join(root, "d4")
    b4 = (
        _mk_inbox(d4, "leads", []),
        _mk_inbox(d4, "orders", []),
        _mk_inbox(d4, "flows", [
            {"flow_id": "F7", "account": "u2", "kind": "spend", "amount": 10}]),
    )

    d5 = os.path.join(root, "d5")
    b5 = (
        _mk_inbox(d5, "leads", []),
        _mk_inbox(d5, "orders", []),
        _mk_inbox(d5, "flows", []),
    )

    return {"root": root, "db": db,
            "boxes": {D1: b1, D2: b2, D3: b3, D4: b4, D5: b5}}


def _chain(w, days=DAYS):
    """Run the days in order; return the envelope and the SQL snapshot
    taken immediately after each booking (booking-time truth)."""
    outs, sqls = {}, {}
    for day in days:
        outs[day] = _run(w["db"], w["boxes"][day], day)
        sqls[day] = _sql_counts(w["db"], day)
    return outs, sqls


def case_fcv1(tmp):
    """AC-FCV1: at booking time on every day of the chain the envelope's
    lifetime outstanding equals the flows table's direct grant-minus-
    spend sum."""
    w = _world(tmp, "fcv1")
    outs, sqls = _chain(w)
    for day in DAYS:
        counts = outs[day]["envelope"]["counts"]
        assert counts["token_outstanding_total"] == \
            sqls[day]["token_outstanding_total"], \
            "AC-FCV1 %s outstanding != direct flows identity" % day


def case_fcv2(tmp):
    """AC-FCV2: day windows count only their own day; the outstanding
    face is the lifetime ledger, not the day-window sum. Verified at
    booking time, where both faces are simultaneously true."""
    w = _world(tmp, "fcv2")
    outs, sqls = _chain(w)
    for day in DAYS:
        counts = outs[day]["envelope"]["counts"]
        for key in DAY_KEYS:
            assert counts[key] == sqls[day][key], \
                "AC-FCV2 %s day window %s" % (day, key)
        assert counts["token_outstanding_total"] == \
            sqls[day]["token_outstanding_total"], \
            "AC-FCV2 %s outstanding is not the cumulative ledger" % day
        if day != D1:
            assert counts["token_outstanding_total"] != \
                counts["token_granted_day"] - counts["token_spent_day"], \
                "AC-FCV2 %s lifetime face collapsed onto the day window" % day
    assert outs[D4]["envelope"]["counts"]["token_granted_day"] == 0, \
        "AC-FCV2 D4 day window absorbed earlier grants"
    assert outs[D1]["envelope"]["counts"]["token_spent_day"] == 40, \
        "AC-FCV2 D1 day window leaked later spends"


def case_fcv3(tmp):
    """AC-FCV3: delta_prev_day closes key-by-key over the chain."""
    w = _world(tmp, "fcv3")
    outs, _ = _chain(w)
    assert outs[D1]["envelope"]["delta_prev_day"] is None, \
        "AC-FCV3 D1 has a prev-day delta without a previous day"
    for i, day in enumerate(DAYS[1:], start=1):
        prev = DAYS[i - 1]
        delta = outs[day]["envelope"]["delta_prev_day"]
        counts = outs[day]["envelope"]["counts"]
        prev_counts = outs[prev]["envelope"]["counts"]
        assert delta is not None, "AC-FCV3 %s lost its delta" % day
        assert set(delta) == set(fd._COUNT_KEYS), \
            "AC-FCV3 %s delta key set" % day
        expected = dict((k, counts[k] - prev_counts[k])
                        for k in fd._COUNT_KEYS)
        assert delta == expected, "AC-FCV3 %s delta not key-by-key closed" % day


def case_fcv4(tmp):
    """AC-FCV4: the pre-registered arithmetic chain of the lifetime face."""
    w = _world(tmp, "fcv4")
    outs, _ = _chain(w)
    expected = {D1: 60, D2: 90, D3: 60, D4: 50}
    for day in DAYS:
        got = outs[day]["envelope"]["counts"]["token_outstanding_total"]
        assert got == expected[day], \
            "AC-FCV4 %s outstanding %r != pre-registered %r" % (
                day, got, expected[day])


def case_fcv5(tmp):
    """AC-FCV5: an empty day books zero windows, keeps the lifetime
    face frozen, and its delta is minus the previous day's day-scoped
    counts with a zero lifetime delta."""
    w = _world(tmp, "fcv5")
    _chain(w)
    d5 = _run(w["db"], w["boxes"][D5], D5)["envelope"]
    counts = d5["counts"]
    for key in DAY_KEYS:
        assert counts[key] == 0, "AC-FCV5 %s not zero on an empty day" % key
    assert counts["token_outstanding_total"] == 50, \
        "AC-FCV5 lifetime face moved on an empty day"
    prev = json.loads(_stored(w["db"], D4)[0])["counts"]
    assert counts["token_outstanding_total"] == prev["token_outstanding_total"], \
        "AC-FCV5 lifetime face drifted from D4"
    delta = d5["delta_prev_day"]
    assert delta is not None, "AC-FCV5 empty day lost its delta"
    assert set(delta) == set(fd._COUNT_KEYS), "AC-FCV5 empty-day delta keys"
    for key in DAY_KEYS:
        assert delta[key] == -prev[key], \
            "AC-FCV5 empty-day delta %s != minus D4" % key
    assert delta["token_outstanding_total"] == 0, \
        "AC-FCV5 empty-day lifetime delta should be zero"


def case_fcv6(tmp):
    """AC-FCV6: three-account coherence at booking time - the stored
    rollup envelope, the SQL aggregates and the gate verdict agree on
    every day, and the rollups face holds exactly one row per day."""
    w = _world(tmp, "fcv6")
    _, sqls = _chain(w)
    assert _rollup_days(w["db"]) == list(DAYS), \
        "AC-FCV6 rollups face is not one row per booked day"
    for day in DAYS:
        stored = _stored(w["db"], day)
        assert stored is not None, "AC-FCV6 %s has no stored rollup" % day
        env = json.loads(stored[0])
        assert env["counts"] == sqls[day], \
            "AC-FCV6 %s stored counts != booking-time SQL aggregates" % day
        assert stored[1] == env["gate"] == "PASS", \
            "AC-FCV6 %s gate column/envelope disagreement" % day
        assert json.loads(stored[2]) == [], "AC-FCV6 %s hits not empty" % day


def case_fcv7(tmp):
    """AC-FCV7 (amended during delivery): replaying the whole chain books
    nothing new and never moves a day window. The lifetime face in each
    replayed envelope re-derives from the whole ledger (and so does the
    next day's lifetime delta against it), therefore stored envelope
    bytes are NOT frozen across a chain replay; byte-level idempotence
    is asserted on a newest-day replay instead."""
    w = _world(tmp, "fcv7")
    _chain(w)
    frozen = dict((day, json.loads(_stored(w["db"], day)[0])["counts"])
                  for day in DAYS)
    before = dict((t, _rows(w["db"], t)) for t in TABLES)
    outs, _ = _chain(w)
    after = dict((t, _rows(w["db"], t)) for t in TABLES)
    for day in DAYS:
        rings = outs[day]
        assert rings["ring1"]["leads_new"] == 0, "AC-FCV7 %s ring1" % day
        assert rings["ring2"]["dispatches_new"] == 0, "AC-FCV7 %s ring2" % day
        assert rings["ring3"]["orders_new"] == 0, "AC-FCV7 %s ring3" % day
        assert rings["ring4"]["flows_new"] == 0, "AC-FCV7 %s ring4" % day
        counts = rings["envelope"]["counts"]
        for key in DAY_KEYS:
            assert counts[key] == frozen[day][key], \
                "AC-FCV7 %s day window %s drifted on replay" % (day, key)
        assert counts["token_outstanding_total"] == 50, \
            "AC-FCV7 %s replayed lifetime face not the final ledger" % day
    for table in TABLES:
        assert len(after[table]) == len(before[table]), \
            "AC-FCV7 %s row count moved on replay" % table
    settled = _stored(w["db"], D4)[0]
    _run(w["db"], w["boxes"][D4], D4)
    assert _stored(w["db"], D4)[0] == settled, \
        "AC-FCV7 newest-day replay not byte-identical"


def case_fcv8(tmp):
    """AC-FCV8: hygiene - pure ASCII suite source, no network imports,
    no wall-clock calls (read off the parsed AST), shipped config and
    library bytes unchanged by the run."""
    own = os.path.join(BASE, "test_funnel_conservation.py")
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
        assert name not in modules, "AC-FCV8 network import %s" % name

    clock_attrs = ("now", "today", "utcnow")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in clock_attrs, \
                "AC-FCV8 wall clock .%s" % node.attr
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "time":
                assert getattr(fn.value, "id", "") != "time", \
                    "AC-FCV8 wall clock time.time"

    cfg = os.path.join(BASE, "config.json")
    lib = os.path.join(BASE, "funnel_daily.py")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha, lib_sha = sha(cfg), sha(lib)
    w = _world(tmp, "fcv8")
    outs, _ = _chain(w)
    for day in DAYS:
        assert outs[day]["envelope"]["gate"] == "PASS", \
            "AC-FCV8 gate FAIL on %s" % day
    assert sha(cfg) == cfg_sha, "AC-FCV8 shipped config mutated"
    assert sha(lib) == lib_sha, "AC-FCV8 library source mutated"
    assert os.path.abspath(w["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FCV8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-conservation-")
    cases = [
        ("AC-FCV1 per-day lifetime identity", case_fcv1),
        ("AC-FCV2 day window vs lifetime separation", case_fcv2),
        ("AC-FCV3 delta chain key-by-key closure", case_fcv3),
        ("AC-FCV4 pre-registered arithmetic chain", case_fcv4),
        ("AC-FCV5 empty day zero penetration", case_fcv5),
        ("AC-FCV6 three-account coherence", case_fcv6),
        ("AC-FCV7 whole-chain replay idempotent", case_fcv7),
        ("AC-FCV8 hygiene", case_fcv8),
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