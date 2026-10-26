"""Funnel first-write-wins + rescan divergence register (R2155).

Pre-registered criteria AC-FSW1..AC-FSW8 live in state/queue/tech.md
(the R2155 claim row) and were written BEFORE this suite or the
product face existed (honesty law). The window under test: the four
rings have always been idempotent on their natural key (AC-FIN /
AC-FRS), but a LATER submission of an already-booked key carrying
DIFFERENT money data was swallowed in silence - INSERT OR IGNORE kept
the first row and nobody could learn that two sources disagreed about
the amount of one order. This suite pins both halves of the ruling:
first write still wins, and every divergence on the two money rings
(orders / flows) lands once in an append-only register readable
through book_conflicts(). Rings 1 and 2 stay unregistered by law (a
lead-text disagreement is a UGC content-safety matter, not something
a bookkeeping register arbitrates); their first-write-wins behaviour
is pinned here instead.

The library is exercised as shipped - this file changes nothing under
test. Pure ASCII source (non-ASCII is injected through escapes only).
"""

import ast
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402

D1 = "2026-10-19"
D2 = "2026-10-20"
D3 = "2026-10-21"
D4 = "2026-10-22"
D5 = "2026-10-23"
D9 = "2026-10-27"


def _inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _world(tmp, name):
    root = os.path.join(tmp, name)
    os.makedirs(root, exist_ok=True)
    return {"root": root, "db": os.path.join(root, "funnel.db")}


def _drop(root, name, rows):
    """A fresh inbox directory (new name) holding exactly these rows."""
    return _inbox(root, "%s-%d" % (name, len(os.listdir(root))), rows)


def _one(db_path, sql, params=()):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def _tables(db_path):
    con = sqlite3.connect(db_path)
    try:
        names = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "ORDER BY name").fetchall()]
        dump = {}
        for name in names:
            dump[name] = con.execute(
                "SELECT * FROM %s ORDER BY rowid" % name).fetchall()
        return dump
    finally:
        con.close()


def case_fsw1(tmp):
    """AC-FSW1: first write wins on the order book. A later day's
    conflicting offer of the same order_id books nothing, rewrites
    nothing, and never re-attributes the row to the later day."""
    w = _world(tmp, "fsw1")
    f = fd.FunnelDaily(w["db"])
    try:
        first = f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D1)
        second = f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "B", "amount_cent": 999}]), D2)
        d1_totals = f.sku_totals(D1)
        d2_totals = f.sku_totals(D2)
    finally:
        f.close()
    assert first == {"orders_seen": 1, "orders_new": 1}, \
        "AC-FSW1 first booking %r" % (first,)
    assert second == {"orders_seen": 1, "orders_new": 0}, \
        "AC-FSW1 conflicting re-offer booked again %r" % (second,)
    assert _one(w["db"], "SELECT day, sku, amount_cent FROM orders") == \
        [(D1, "A", 100)], "AC-FSW1 booked row rewritten"
    assert d1_totals == {"A": {"orders": 1, "amount_cent": 100}}, \
        "AC-FSW1 day-one totals %r" % (d1_totals,)
    assert d2_totals == {}, "AC-FSW1 later day re-counted the row"


def case_fsw2(tmp):
    """AC-FSW2: the divergence is registered once per distinct claim -
    repeated identical submissions add nothing, an identical-to-booked
    submission is not a divergence at all, and a third distinct claim
    gets its own row."""
    w = _world(tmp, "fsw2")
    f = fd.FunnelDaily(w["db"])
    try:
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D1)
        clash = [{"order_id": "o1", "sku": "B", "amount_cent": 999}]
        for day in (D2, D3, D4):
            f.book_orders(_drop(w["root"], "o", clash), day)
        once = f.book_conflicts()
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D5)
        same_as_booked = f.book_conflicts()
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "C", "amount_cent": 777}]), D5)
        twice = f.book_conflicts()
    finally:
        f.close()
    assert once["conflict_count"] == 1, \
        "AC-FSW2 repeated clash re-registered %r" % (once,)
    row = once["rows"][0]
    assert row["ring"] == "orders" and row["natural_key"] == "o1", \
        "AC-FSW2 register identity %r" % (row,)
    assert row["booked_day"] == D1, "AC-FSW2 booked day %r" % (row,)
    assert json.loads(row["booked_text"]) == ["A", 100], \
        "AC-FSW2 booked payload %r" % (row,)
    assert row["offered_day"] == D2, \
        "AC-FSW2 first-offer day moved on re-submission %r" % (row,)
    assert json.loads(row["offered_text"]) == ["B", 999], \
        "AC-FSW2 offered payload %r" % (row,)
    assert same_as_booked["conflict_count"] == 1, \
        "AC-FSW2 identical-to-booked claim registered %r" % (same_as_booked,)
    assert twice["conflict_count"] == 2, \
        "AC-FSW2 second distinct claim not registered %r" % (twice,)
    assert [r["conflict_id"] for r in twice["rows"]] == sorted(
        r["conflict_id"] for r in twice["rows"]), \
        "AC-FSW2 register not in insertion order"
    assert json.loads(twice["rows"][1]["offered_text"]) == ["C", 777], \
        "AC-FSW2 second claim payload %r" % (twice["rows"][1],)


def case_fsw3(tmp):
    """AC-FSW3: first write wins on the token ledger too - a later
    conflicting flow never flips kind or amount, so the outstanding
    identity stays exactly where the first writer put it."""
    w = _world(tmp, "fsw3")
    f = fd.FunnelDaily(w["db"])
    try:
        first = f.book_token_flows(_drop(w["root"], "f", [
            {"flow_id": "f1", "kind": "grant", "amount": 10}]), D1)
        second = f.book_token_flows(_drop(w["root"], "f", [
            {"flow_id": "f1", "kind": "spend", "amount": 40}]), D2)
        ledger = f.account_ledger()
        registers = f.book_conflicts()
    finally:
        f.close()
    assert first == {"flows_seen": 1, "flows_new": 1}, \
        "AC-FSW3 first flow booking %r" % (first,)
    assert second == {"flows_seen": 1, "flows_new": 0}, \
        "AC-FSW3 conflicting flow booked again %r" % (second,)
    assert _one(w["db"],
                "SELECT day, account, kind, amount FROM flows") == \
        [(D1, "", "grant", 10)], "AC-FSW3 flow row rewritten"
    assert ledger == {"": {"granted": 10, "spent": 0,
                           "outstanding": 10}}, \
        "AC-FSW3 outstanding identity moved %r" % (ledger,)
    assert registers["conflict_count"] == 1 and \
        registers["by_ring"] == {"flows": 1}, \
        "AC-FSW3 flow divergence not registered %r" % (registers,)
    assert json.loads(registers["rows"][0]["offered_text"]) == \
        ["", "spend", 40], "AC-FSW3 offered flow payload"


def case_fsw4(tmp):
    """AC-FSW4: the boundary is honest - rings 1 and 2 keep first
    write wins (text not rewritten, route not re-derived) but are NOT
    registered, because a lead-text disagreement belongs to the UGC
    content-safety pipeline, not to a bookkeeping register."""
    w = _world(tmp, "fsw4")
    f = fd.FunnelDaily(w["db"])
    try:
        r1a = f.scan_leads(_drop(w["root"], "l", [
            {"lead_id": "l1", "source": "form", "text": "game demo"}]), D1)
        r2a = f.dispatch_leads(D1)
        r1b = f.scan_leads(_drop(w["root"], "l", [
            {"lead_id": "l1", "source": "form",
             "text": "quant strategy backtest"}]), D2)
        r2b = f.dispatch_leads(D2)
        stored = _one(w["db"], "SELECT day, domain, text FROM leads")
        routes = f.route_tally()
        registers = f.book_conflicts()
    finally:
        f.close()
    assert r1a == {"files_leads": 1, "leads_seen": 1, "leads_new": 1}, \
        "AC-FSW4 first lead %r" % (r1a,)
    assert r1b == {"files_leads": 1, "leads_seen": 1, "leads_new": 0}, \
        "AC-FSW4 conflicting lead booked again %r" % (r1b,)
    assert stored == [(D1, "game", "game demo")], \
        "AC-FSW4 lead row rewritten %r" % (stored,)
    assert r2a["dispatches_new"] == 1 and r2b["dispatches_new"] == 0, \
        "AC-FSW4 re-scan re-dispatched %r / %r" % (r2a, r2b)
    assert routes == {"game": 1}, "AC-FSW4 route re-derived %r" % (routes,)
    assert registers == {"conflict_count": 0, "by_ring": {}, "rows": []}, \
        "AC-FSW4 non-money ring registered %r" % (registers,)


def case_fsw5(tmp):
    """AC-FSW5: the read face contract - exactly three envelope keys,
    a consistent count, seven-key rows, honest empty world, and a
    bad day form failing closed before any read."""
    w = _world(tmp, "fsw5")
    f = fd.FunnelDaily(w["db"])
    try:
        empty = f.book_conflicts()
        assert set(empty) == {"conflict_count", "by_ring", "rows"}, \
            "AC-FSW5 envelope keys %r" % (sorted(empty),)
        assert empty == {"conflict_count": 0, "by_ring": {}, "rows": []}, \
            "AC-FSW5 empty envelope not honest %r" % (empty,)
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D1)
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "B", "amount_cent": 999}]), D2)
        f.book_token_flows(_drop(w["root"], "f", [
            {"flow_id": "f1", "kind": "grant", "amount": 10}]), D1)
        f.book_token_flows(_drop(w["root"], "f", [
            {"flow_id": "f1", "kind": "spend", "amount": 3}]), D2)
        out = f.book_conflicts()
        bad = 0
        for form in ("2026-13-01", "bad", "", "2026/10/19", 20261019, True):
            try:
                f.book_conflicts(form)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, "AC-FSW5 code"
                bad += 1
        still = f.book_conflicts()
    finally:
        f.close()
    assert out["conflict_count"] == 2, "AC-FSW5 count %r" % (out,)
    assert out["conflict_count"] == len(out["rows"]) == \
        sum(out["by_ring"].values()), "AC-FSW5 count identity broken"
    assert out["by_ring"] == {"flows": 1, "orders": 1}, \
        "AC-FSW5 by_ring %r" % (out["by_ring"],)
    for row in out["rows"]:
        assert set(row) == {"conflict_id", "ring", "natural_key",
                            "booked_day", "booked_text", "offered_day",
                            "offered_text"}, \
            "AC-FSW5 row keys %r" % (sorted(row),)
    assert bad == 6, "AC-FSW5 bad day forms accepted (%d/6)" % bad
    assert still == out, "AC-FSW5 rejected forms moved the register"


def case_fsw6(tmp):
    """AC-FSW6: the day window reads the day a divergence was FIRST
    presented - a later re-submission never moves it, and a day with
    no divergence is an honest empty envelope."""
    w = _world(tmp, "fsw6")
    f = fd.FunnelDaily(w["db"])
    try:
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D1)
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "B", "amount_cent": 999}]), D2)
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "B", "amount_cent": 999}]), D5)
        f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "C", "amount_cent": 777}]), D5)
        on_d2 = f.book_conflicts(D2)
        on_d5 = f.book_conflicts(D5)
        on_d9 = f.book_conflicts(D9)
        lifetime = f.book_conflicts()
    finally:
        f.close()
    assert on_d2["conflict_count"] == 1 and \
        json.loads(on_d2["rows"][0]["offered_text"]) == ["B", 999], \
        "AC-FSW6 D2 window %r" % (on_d2,)
    assert on_d5["conflict_count"] == 1 and \
        json.loads(on_d5["rows"][0]["offered_text"]) == ["C", 777], \
        "AC-FSW6 D5 window (retry re-dated?) %r" % (on_d5,)
    assert on_d9 == {"conflict_count": 0, "by_ring": {}, "rows": []}, \
        "AC-FSW6 empty day not honest %r" % (on_d9,)
    assert lifetime["conflict_count"] == 2, \
        "AC-FSW6 lifetime %r" % (lifetime,)


def case_fsw7(tmp):
    """AC-FSW7: reading is pure (no row, no token moves), the register
    is shared across independent connections on the same carrier, and
    a close/reopen replays it byte-for-byte."""
    w = _world(tmp, "fsw7")
    a = fd.FunnelDaily(w["db"])
    b = fd.FunnelDaily(w["db"])
    try:
        a.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D1)
        b.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "B", "amount_cent": 999}]), D2)
        before = _tables(w["db"])
        seen_by_a = a.book_conflicts()
        seen_by_b = b.book_conflicts()
        assert a.book_conflicts() == a.book_conflicts(), "AC-FSW7 unstable"
        after = _tables(w["db"])
        first_text = json.dumps(a.book_conflicts(), sort_keys=True)
    finally:
        a.close()
        b.close()
    assert before == after, "AC-FSW7 the read face wrote rows"
    assert seen_by_a["conflict_count"] == 1, \
        "AC-FSW7 writer instance cannot see its own divergence %r" \
        % (seen_by_a,)
    assert seen_by_b == seen_by_a, \
        "AC-FSW7 second connection disagrees %r vs %r" % (seen_by_b, seen_by_a)
    assert _one(w["db"], "SELECT kind, amount FROM flows") == [], \
        "AC-FSW7 register touched the ledger"
    reopened = fd.FunnelDaily(w["db"])
    try:
        assert json.dumps(reopened.book_conflicts(), sort_keys=True) == \
            first_text, "AC-FSW7 register not persistent across restart"
    finally:
        reopened.close()


def case_fsw8(tmp):
    """AC-FSW8: hygiene and wiring - ASCII source, no network import,
    no wall clock, ring return dictionaries unchanged, and the suite
    registered in the battery with its criteria count."""
    lib = os.path.join(BASE, "funnel_daily.py")
    text = open(lib, encoding="utf-8").read()
    text.encode("ascii")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in (
                    "socket", "http", "urllib", "requests", "asyncio"), \
                    "AC-FSW8 network import %s" % alias.name
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in (
                "socket", "http", "urllib", "requests", "asyncio"), \
                "AC-FSW8 network import %r" % (node.module,)
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("now", "today", "utcnow"), \
                "AC-FSW8 wall clock .%s" % node.attr

    w = _world(tmp, "fsw8")
    f = fd.FunnelDaily(w["db"])
    try:
        r3 = f.book_orders(_drop(w["root"], "o", [
            {"order_id": "o1", "sku": "A", "amount_cent": 100}]), D1)
        r4 = f.book_token_flows(_drop(w["root"], "f", [
            {"flow_id": "f1", "kind": "grant", "amount": 10}]), D1)
        r1 = f.scan_leads(_drop(w["root"], "l", [
            {"lead_id": "l1", "text": "game demo"}]), D1)
        r2 = f.dispatch_leads(D1)
    finally:
        f.close()
    assert set(r1) == {"files_leads", "leads_seen", "leads_new"}, \
        "AC-FSW8 leads keys changed %r" % (sorted(r1),)
    assert set(r2) == {"dispatches_new", "routes"}, \
        "AC-FSW8 dispatch keys changed %r" % (sorted(r2),)
    assert set(r3) == {"orders_seen", "orders_new"}, \
        "AC-FSW8 order keys changed %r" % (sorted(r3),)
    assert set(r4) == {"flows_seen", "flows_new"}, \
        "AC-FSW8 flow keys changed %r" % (sorted(r4),)

    reg = os.path.join(BASE, "..", "reconcile_all.py")
    reg_text = open(reg, encoding="utf-8").read()
    assert '"funnel-firstwrite"' in reg_text, "AC-FSW8 registry entry absent"
    assert "test_funnel_firstwrite.py" in reg_text, "AC-FSW8 suite path absent"
    tail = reg_text.split('"funnel-firstwrite"', 1)[1][:200]
    assert ", 8)" in tail, "AC-FSW8 criteria count not 8"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-firstwrite-")
    cases = [
        ("AC-FSW1 first write wins orders", case_fsw1),
        ("AC-FSW2 divergence registered once", case_fsw2),
        ("AC-FSW3 first write wins flows", case_fsw3),
        ("AC-FSW4 rings 1/2 boundary", case_fsw4),
        ("AC-FSW5 read face contract", case_fsw5),
        ("AC-FSW6 day window first offer", case_fsw6),
        ("AC-FSW7 pure read and persistence", case_fsw7),
        ("AC-FSW8 hygiene and wiring", case_fsw8),
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