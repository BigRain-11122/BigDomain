"""Acceptance suite for the funnel per-account token ledger read face
(FUNNEL-LOOP v0.1, R2053).

Pre-registered criteria AC-FAR1..AC-FAR8 live in state/queue/tech.md
(the R2053 claim row) and were written BEFORE this suite existed
(honesty law). The gap under test: the rollup envelope states one
lifetime token outstanding total (AC-FN5), and the day window counts
grant/spend per day (AC-FCV2), but nothing reads the flows ledger
GROUPED BY ACCOUNT - there is no per-account granted/spent/outstanding
face at all.

World: two booked days over three buckets - named account A, named
account B, and the blank account "" (a flow row may honestly carry no
account yet). D2 makes B an honest overdraft (spend > grant).

  D1: A grant 100, B grant 50, A spend 30
  D2: A grant 20, B spend 80, "" grant 5

Lifetime: A 120/30/90, B 50/80/-30, "" 5/0/5.

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
    "": {"granted": 5, "spent": 0, "outstanding": 5},
    "A": {"granted": 120, "spent": 30, "outstanding": 90},
    "B": {"granted": 50, "spent": 80, "outstanding": -30},
}
WINDOW_D1 = {
    "A": {"granted": 100, "spent": 30, "outstanding": 70},
    "B": {"granted": 50, "spent": 0, "outstanding": 50},
}
WINDOW_D2 = {
    "": {"granted": 5, "spent": 0, "outstanding": 5},
    "A": {"granted": 20, "spent": 0, "outstanding": 20},
    "B": {"granted": 0, "spent": 80, "outstanding": -80},
}


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _flows_rows(db_path):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT * FROM flows ORDER BY flow_id").fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _world(tmp, tag):
    root = os.path.join(tmp, tag)
    os.makedirs(root, exist_ok=True)
    empty = _mk_inbox(root, "leads", [])
    orders = _mk_inbox(root, "orders", [])
    f1 = _mk_inbox(root, "flows1", [
        {"flow_id": "f1", "account": "A", "kind": "grant", "amount": 100},
        {"flow_id": "f2", "account": "B", "kind": "grant", "amount": 50},
        {"flow_id": "f3", "account": "A", "kind": "spend", "amount": 30},
    ])
    f2 = _mk_inbox(root, "flows2", [
        {"flow_id": "f4", "account": "A", "kind": "grant", "amount": 20},
        {"flow_id": "f5", "account": "B", "kind": "spend", "amount": 80},
        {"flow_id": "f6", "account": "", "kind": "grant", "amount": 5},
    ])
    db = os.path.join(root, "funnel.db")
    face = fd.FunnelDaily(db)
    out1 = face.run_daily(empty, orders, f1, D1)
    out2 = face.run_daily(empty, orders, f2, D2)
    face.close()
    return {"db": db, "out1": out1, "out2": out2, "root": root}


def _open(world):
    return fd.FunnelDaily(world["db"])


# AC-FAR1: three keys per account, sorted-account order.
def case_far1(tmp):
    world = _world(tmp, "far1")
    face = _open(world)
    try:
        face_out = face.account_ledger()
    finally:
        face.close()
    assert list(face_out.keys()) == ["", "A", "B"], \
        "AC-FAR1 account order %r" % list(face_out.keys())
    for account, expected in LIFETIME.items():
        got = face_out[account]
        assert list(got.keys()) == ["granted", "spent", "outstanding"], \
            "AC-FAR1 key set %r" % list(got.keys())
        assert got == expected, \
            "AC-FAR1 %r got %r want %r" % (account, got, expected)


# AC-FAR2: per-account outstanding closes the lifetime identity.
def case_far2(tmp):
    world = _world(tmp, "far2")
    face = _open(world)
    try:
        face_out = face.account_ledger()
        env = face.rollup(D2)
    finally:
        face.close()
    total = sum(v["outstanding"] for v in face_out.values())
    assert total == 65, "AC-FAR2 sum outstanding %r" % total
    assert total == env["counts"]["token_outstanding_total"], \
        "AC-FAR2 identity %r vs rollup %r" % (
            total, env["counts"]["token_outstanding_total"])
    granted = sum(v["granted"] for v in face_out.values())
    spent = sum(v["spent"] for v in face_out.values())
    assert granted - spent == total, "AC-FAR2 granted-spent drift"


# AC-FAR3: window law - explicit day vs lifetime vs honest empty day.
def case_far3(tmp):
    world = _world(tmp, "far3")
    face = _open(world)
    try:
        day1 = face.account_ledger(D1)
        day2 = face.account_ledger(D2)
        lifetime = face.account_ledger()
        empty = face.account_ledger(EMPTY_DAY)
    finally:
        face.close()
    assert day1 == WINDOW_D1, "AC-FAR3 D1 %r" % day1
    assert day2 == WINDOW_D2, "AC-FAR3 D2 %r" % day2
    assert lifetime == LIFETIME, "AC-FAR3 lifetime %r" % lifetime
    assert empty == {}, "AC-FAR3 empty day %r" % empty
    assert "B" not in day2 or day2["B"]["granted"] == 0, \
        "AC-FAR3 window leaked lifetime grants"


# AC-FAR4: the blank account is its own bucket, never merged.
def case_far4(tmp):
    world = _world(tmp, "far4")
    face = _open(world)
    try:
        face_out = face.account_ledger()
        day2 = face.account_ledger(D2)
    finally:
        face.close()
    assert "" in face_out and "" in day2, "AC-FAR4 blank bucket missing"
    assert face_out[""]["granted"] == 5, "AC-FAR4 blank grant"
    assert face_out["A"]["granted"] == 120, "AC-FAR4 A merged blank"
    assert face_out["B"]["granted"] == 50, "AC-FAR4 B merged blank"


# AC-FAR5: overdraft is honest - negative outstanding, no clamp.
def case_far5(tmp):
    world = _world(tmp, "far5")
    face = _open(world)
    try:
        face_out = face.account_ledger()
    finally:
        face.close()
    assert face_out["B"]["outstanding"] == -30, \
        "AC-FAR5 overdraft %r" % face_out["B"]["outstanding"]
    assert face_out["B"]["spent"] == 80, "AC-FAR5 spend"
    assert face_out["B"]["granted"] == 50, "AC-FAR5 grant"


# AC-FAR6: cross-restart persistence - zero cache, byte-identical reads.
def case_far6(tmp):
    world = _world(tmp, "far6")
    face = _open(world)
    try:
        before_life = json.dumps(face.account_ledger(), sort_keys=True)
        before_day = json.dumps(face.account_ledger(D2), sort_keys=True)
    finally:
        face.close()
    rows_before = _flows_rows(world["db"])
    face = _open(world)
    try:
        after_life = json.dumps(face.account_ledger(), sort_keys=True)
        after_day = json.dumps(face.account_ledger(D2), sort_keys=True)
    finally:
        face.close()
    assert before_life == after_life, "AC-FAR6 lifetime drifted"
    assert before_day == after_day, "AC-FAR6 day drifted"
    assert _flows_rows(world["db"]) == rows_before, \
        "AC-FAR6 read face wrote rows"
    assert json.loads(after_life) == LIFETIME, "AC-FAR6 reopened face"


# AC-FAR7: pure-read law + bad-day fail-closed before any touch.
def case_far7(tmp):
    world = _world(tmp, "far7")
    face = _open(world)
    try:
        rows_before = _flows_rows(world["db"])
        face.account_ledger()
        face.account_ledger(D1)
        rows_after = _flows_rows(world["db"])
        assert rows_before == rows_after, "AC-FAR7 read face wrote rows"
        for bad in (20261020, "2026-13-01", "", None, "x"):
            if bad is None:
                continue
            try:
                face.account_ledger(bad)
            except fd.FunnArgError as exc:
                assert str(exc) == fd.E_FN_BAD_ARGS, \
                    "AC-FAR7 code %r" % str(exc)
            else:
                raise AssertionError("AC-FAR7 bad day accepted %r" % (bad,))
        assert _flows_rows(world["db"]) == rows_before, \
            "AC-FAR7 rejection touched rows"
    finally:
        face.close()


# AC-FAR8: hygiene - ASCII source, zero network/clock, shipped bytes.
def case_far8(tmp):
    lib = os.path.join(BASE, "funnel_daily.py")
    raw = open(lib, "rb").read()
    assert all(b < 128 for b in raw), "AC-FAR8 library not ASCII"
    tree = ast.parse(raw.decode("ascii"))
    banned = ("socket", "urllib", "requests", "http", "asyncio")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, \
                    "AC-FAR8 network import %s" % alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned, \
                "AC-FAR8 network import %s" % node.module
    clock_attrs = ("now", "today", "utcnow")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in clock_attrs, \
                "AC-FAR8 wall clock .%s" % node.attr
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "time":
                assert getattr(fn.value, "id", "") != "time", \
                    "AC-FAR8 wall clock time.time"

    cfg = os.path.join(BASE, "config.json")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha = sha(cfg)
    world = _world(tmp, "far8")
    face = _open(world)
    try:
        assert face.account_ledger() == LIFETIME, "AC-FAR8 live face"
    finally:
        face.close()
    assert sha(cfg) == cfg_sha, "AC-FAR8 shipped config mutated"
    assert os.path.abspath(world["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FAR8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-account-")
    cases = [
        ("AC-FAR1 per-account three keys", case_far1),
        ("AC-FAR2 lifetime identity closure", case_far2),
        ("AC-FAR3 day window law", case_far3),
        ("AC-FAR4 blank account bucket", case_far4),
        ("AC-FAR5 honest overdraft", case_far5),
        ("AC-FAR6 cross-restart persistence", case_far6),
        ("AC-FAR7 pure read and fail-closed", case_far7),
        ("AC-FAR8 hygiene", case_far8),
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