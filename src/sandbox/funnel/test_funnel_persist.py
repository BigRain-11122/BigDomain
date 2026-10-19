"""Acceptance suite for funnel_daily cross-restart persistence
(FUNNEL-LOOP v0.1, R2049).

Pre-registered criteria AC-FPR1..AC-FPR8 live in state/queue/tech.md
(the R2049 claim row) and were written BEFORE this suite existed
(honesty law). The window under test is the one the R2047 reseed row
named: the four-ring counters and the rollup envelope must survive a
carrier restart byte-for-byte, a same-day re-run on the reopened
instance must book zero new rows and reproduce the same envelope, and
the previous-day envelope must be read back from disk (not from
memory) when the next day rolls up.

The library is exercised as shipped - this file changes nothing under
test. Pure ASCII source: the injected banned word uses a unicode
escape so no non-ASCII literal enters this file (coding law).
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
    """One populated day-one world: inboxes + carrier path."""
    root = os.path.join(tmp, name)
    os.makedirs(root)
    leads = _mk_inbox(root, "leads", [
        {"lead_id": "L1", "source": "s", "text": "I want a game demo level"},
        {"lead_id": "L2", "source": "s", "text": "persona story for a resident"},
    ])
    orders = _mk_inbox(root, "orders", [
        {"order_id": "O1", "sku": "compute-pack-19.9", "amount_cent": 1990},
    ])
    flows = _mk_inbox(root, "flows", [
        {"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 100},
        {"flow_id": "F2", "account": "u1", "kind": "spend", "amount": 30},
    ])
    empty = os.path.join(root, "empty")
    os.makedirs(empty)
    return {
        "root": root,
        "db": os.path.join(root, "funnel.db"),
        "leads": leads,
        "orders": orders,
        "flows": flows,
        "empty": empty,
    }


def case_fpr1(tmp):
    """AC-FPR1: source-row persistence - close then reopen the same
    db file; the four source tables come back row-for-row identical,
    with identical counts."""
    w = _world(tmp, "fpr1")
    f = fd.FunnelDaily(w["db"])
    f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    before = dict((t, _rows(w["db"], t)) for t in TABLES)
    counts_before = dict((t, _count(w["db"], t)) for t in TABLES)
    f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        after = dict((t, _rows(w["db"], t)) for t in TABLES)
        counts_after = dict((t, _count(w["db"], t)) for t in TABLES)
    finally:
        g.close()
    for t in TABLES:
        assert before[t] == after[t], "AC-FPR1 %s rows drifted" % t
        assert counts_before[t] == counts_after[t], \
            "AC-FPR1 %s count drifted" % t
        assert counts_after[t] > 0, "AC-FPR1 %s world not populated" % t
    assert counts_after["leads"] == 2
    assert counts_after["dispatches"] == 2
    assert counts_after["orders"] == 1
    assert counts_after["flows"] == 2


def case_fpr2(tmp):
    """AC-FPR2: the stored rollup envelope is byte-identical after a
    restart (json equality is not enough - the bytes are compared)."""
    w = _world(tmp, "fpr2")
    f = fd.FunnelDaily(w["db"])
    out = f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    env_text = _dump(out["envelope"])
    stored_before = _stored_rollup(w["db"], DAY1)
    f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        stored_after = _stored_rollup(w["db"], DAY1)
    finally:
        g.close()
    assert stored_before is not None, "AC-FPR2 no stored rollup"
    assert stored_after[0].encode("utf-8") == stored_before[0].encode("utf-8"), \
        "AC-FPR2 envelope bytes drifted across restart"
    assert json.loads(stored_after[0]) == json.loads(env_text)

    counts = json.loads(stored_after[0])["counts"]
    assert counts["leads_day"] == 2, "AC-FPR2 leads_day"
    assert counts["dispatches_day"] == 2, "AC-FPR2 dispatches_day"
    assert counts["orders_day"] == 1, "AC-FPR2 orders_day"
    assert counts["token_granted_day"] == 100, "AC-FPR2 granted"
    assert counts["token_spent_day"] == 30, "AC-FPR2 spent"
    assert counts["token_outstanding_total"] == 70, "AC-FPR2 outstanding"


def case_fpr3(tmp):
    """AC-FPR3: same-day re-run on the REOPENED instance books zero
    new rows in all four rings and reproduces the envelope dump."""
    w = _world(tmp, "fpr3")
    f = fd.FunnelDaily(w["db"])
    first = f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    env_first = _dump(first["envelope"])
    counts_before = dict((t, _count(w["db"], t)) for t in TABLES)
    f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        second = g.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
        counts_after = dict((t, _count(w["db"], t)) for t in TABLES)
    finally:
        g.close()
    assert second["ring1"]["leads_new"] == 0, "AC-FPR3 ring1 booked"
    assert second["ring2"]["dispatches_new"] == 0, "AC-FPR3 ring2 booked"
    assert second["ring3"]["orders_new"] == 0, "AC-FPR3 ring3 booked"
    assert second["ring4"]["flows_new"] == 0, "AC-FPR3 ring4 booked"
    assert second["ring3"]["orders_seen"] == 1, "AC-FPR3 inbox re-read"
    assert second["ring4"]["flows_seen"] == 2, "AC-FPR3 flow re-read"
    for t in TABLES:
        assert counts_before[t] == counts_after[t], \
            "AC-FPR3 %s row count grew on replay" % t
    assert _dump(second["envelope"]) == env_first, \
        "AC-FPR3 envelope drifted on same-day replay"


def case_fpr4(tmp):
    """AC-FPR4: cross-day delta survives the restart - day two on a
    second reopened instance reads day one's envelope from disk. The
    delta is the day-over-day difference, so with zero day-two
    activity each day-scoped key equals minus the day-one value while
    the lifetime outstanding key is unchanged at 0 (AC-FPR4 amendment
    note, R2049: the first draft read "six keys all zero", which is
    not what a day-over-day delta means - the zero-delta control is
    AC-FPR5's fresh-db face)."""
    w = _world(tmp, "fpr4")
    f = fd.FunnelDaily(w["db"])
    f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    f.close()

    g = fd.FunnelDaily(w["db"])
    g.close()

    h = fd.FunnelDaily(w["db"])
    try:
        day2 = h.run_daily(w["empty"], w["empty"], w["empty"], DAY2)
    finally:
        h.close()
    delta = day2["envelope"]["delta_prev_day"]
    assert delta is not None, "AC-FPR4 prev-day envelope lost"
    for key in fd._COUNT_KEYS:
        assert key in delta, "AC-FPR4 delta missing %s" % key
    day_scoped = dict((k, v) for k, v in delta.items()
                      if k != "token_outstanding_total")
    assert day_scoped["leads_day"] == -2, "AC-FPR4 leads_day delta"
    assert day_scoped["dispatches_day"] == -2, "AC-FPR4 dispatches delta"
    assert day_scoped["orders_day"] == -1, "AC-FPR4 orders delta"
    assert day_scoped["token_granted_day"] == -100, "AC-FPR4 granted delta"
    assert day_scoped["token_spent_day"] == -30, "AC-FPR4 spent delta"
    assert delta["token_outstanding_total"] == 0, \
        "AC-FPR4 lifetime outstanding delta"
    assert all(v <= 0 for v in day_scoped.values()), \
        "AC-FPR4 day-two delta must not be positive"
    counts = day2["envelope"]["counts"]
    assert counts["token_outstanding_total"] == 70, \
        "AC-FPR4 lifetime outstanding not carried"
    assert counts["leads_day"] == 0, "AC-FPR4 day-two ring not empty"


def case_fpr5(tmp):
    """AC-FPR5: empty-db control - a brand new carrier on day two has
    no previous envelope at all (delta_prev_day is None), so AC-FPR4
    is not vacuously true."""
    root = os.path.join(tmp, "fpr5")
    os.makedirs(root)
    empty = os.path.join(root, "empty")
    os.makedirs(empty)
    fresh = os.path.join(root, "fresh.db")
    f = fd.FunnelDaily(fresh)
    try:
        out = f.run_daily(empty, empty, empty, DAY2)
    finally:
        f.close()
    assert out["envelope"]["delta_prev_day"] is None, \
        "AC-FPR5 fresh db reported a delta"
    assert out["envelope"]["counts"]["token_outstanding_total"] == 0


def case_fpr6(tmp):
    """AC-FPR6: two close/reopen cycles leave the envelope bytes
    exactly as first written (the recorded face is stable, not just
    readable once)."""
    w = _world(tmp, "fpr6")
    f = fd.FunnelDaily(w["db"])
    out = f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    env_first = _dump(out["envelope"])
    f.close()

    for cycle in (1, 2):
        g = fd.FunnelDaily(w["db"])
        try:
            stored = _stored_rollup(w["db"], DAY1)
            assert stored is not None, "AC-FPR6 cycle %d lost row" % cycle
            assert stored[0] == env_first, \
                "AC-FPR6 cycle %d bytes drifted" % cycle
            redo = g.rollup(DAY1)
            assert _dump(redo) == env_first, \
                "AC-FPR6 cycle %d re-derive drifted" % cycle
        finally:
            g.close()


def case_fpr7(tmp):
    """AC-FPR7: stored-face coherence - the gate/hits columns agree
    with the envelope across restarts and a same-day replay never
    creates a second row for that day."""
    w = _world(tmp, "fpr7")
    f = fd.FunnelDaily(w["db"])
    out = f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    assert out["envelope"]["gate"] == "PASS", "AC-FPR7 shipped config"
    assert out["envelope"]["hits"] == [], "AC-FPR7 unexpected hits"
    f.close()

    g = fd.FunnelDaily(w["db"])
    try:
        g.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
        stored = _stored_rollup(w["db"], DAY1)
        day_rows = _count(w["db"], "rollups")
    finally:
        g.close()
    envelope, gate, hits = stored
    parsed = json.loads(envelope)
    assert gate == parsed["gate"] == "PASS", "AC-FPR7 gate column drift"
    assert json.loads(hits) == parsed["hits"] == [], "AC-FPR7 hits drift"
    assert day_rows == 1, "AC-FPR7 duplicate day row after replay"


def case_fpr8(tmp):
    """AC-FPR8: hygiene - pure ASCII suite source, zero network
    imports, zero wall-clock calls, shipped config bytes unchanged and
    the library source untouched. The import/clock faces are read off
    the parsed AST rather than by substring scan: the earlier draft
    scanned text and self-matched the literal names it was searching
    for (the R2048 substring/paren lesson, applied at birth)."""
    own = os.path.join(BASE, "test_funnel_persist.py")
    raw = open(own, "rb").read()
    raw.decode("ascii")

    tree = ast.parse(raw.decode("ascii"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    banned_modules = ("socket", "urllib", "http", "requests", "ssl")
    for name in banned_modules:
        assert name not in modules, "AC-FPR8 network import %s" % name

    clock_attrs = ("now", "today", "utcnow")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in clock_attrs, \
                "AC-FPR8 wall clock .%s" % node.attr
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "time":
                owner = getattr(fn.value, "id", "")
                assert owner != "time", "AC-FPR8 wall clock time.time"
    assert "funnel_daily." in raw.decode("ascii")  # library used as shipped

    cfg = os.path.join(BASE, "config.json")
    lib = os.path.join(BASE, "funnel_daily.py")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha, lib_sha = sha(cfg), sha(lib)
    w = _world(tmp, "fpr8")
    f = fd.FunnelDaily(w["db"])
    out = f.run_daily(w["leads"], w["orders"], w["flows"], DAY1)
    f.close()
    assert out["envelope"]["gate"] == "PASS"
    assert sha(cfg) == cfg_sha, "AC-FPR8 shipped config mutated"
    assert sha(lib) == lib_sha, "AC-FPR8 library source mutated"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-persist-")
    cases = [
        ("AC-FPR1 source-row persistence", case_fpr1),
        ("AC-FPR2 envelope byte persistence", case_fpr2),
        ("AC-FPR3 same-day replay after restart", case_fpr3),
        ("AC-FPR4 cross-day delta survives restart", case_fpr4),
        ("AC-FPR5 fresh-db control no delta", case_fpr5),
        ("AC-FPR6 double-cycle stability", case_fpr6),
        ("AC-FPR7 stored-face coherence", case_fpr7),
        ("AC-FPR8 hygiene", case_fpr8),
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