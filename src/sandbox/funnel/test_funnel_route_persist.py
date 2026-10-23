"""Acceptance suite for the funnel dispatch route distribution read face
across restarts (FUNNEL-LOOP v0.1, R2060).

Pre-registered criteria AC-FRTP1..AC-FRTP8 live in state/queue/tech.md
(the R2060 claim row) and were written BEFORE this suite existed
(honesty law). The gap under test: route_tally (R2055) was proven only
inside one live instance. Nothing yet pins the restart semantics - the
same db reopened must answer byte-identically, a later day's injection
must drift the lifetime face while the already-read day windows stay
frozen, a re-dropped inbox must stay idempotent across the restart, and
a third instance must not drift again.

World: three dispatched days over nine leads.

  D1: game, media, quant, unrouted
  D2: life, platform, unrouted
  D3: game, unrouted
  D3 batch 2 (after restart): media, unrouted

Lifetime at the anchor: game 2, life 1, media 1, platform 1, quant 1,
unrouted 3 (9 rows). After batch 2: media 2, unrouted 4 (11 rows).

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
EMPTY_DAY = "2026-10-25"

ANCHOR_LIFETIME = {
    "game": 2,
    "life": 1,
    "media": 1,
    "platform": 1,
    "quant": 1,
    "unrouted": 3,
}
ANCHOR_D1 = {"game": 1, "media": 1, "quant": 1, "unrouted": 1}
ANCHOR_D2 = {"life": 1, "platform": 1, "unrouted": 1}
ANCHOR_D3 = {"game": 1, "unrouted": 1}

AFTER_LIFETIME = {
    "game": 2,
    "life": 1,
    "media": 2,
    "platform": 1,
    "quant": 1,
    "unrouted": 4,
}
AFTER_D3 = {"game": 1, "media": 1, "unrouted": 2}

D1_LEADS = [
    {"lead_id": "a1", "text": "game level demo"},
    {"lead_id": "a2", "text": "video clip script"},
    {"lead_id": "a3", "text": "quant factor etf"},
    {"lead_id": "a4", "text": "nothing matches here"},
]
D2_LEADS = [
    {"lead_id": "b1", "text": "resident persona story"},
    {"lead_id": "b2", "text": "platform billing"},
    {"lead_id": "b3", "text": "no keyword at all"},
]
D3_LEADS = [
    {"lead_id": "c1", "text": "game level demo"},
    {"lead_id": "c2", "text": "no keyword at all"},
]
D3_LEADS_BATCH2 = [
    {"lead_id": "c3", "text": "video clip script"},
    {"lead_id": "c4", "text": "nothing matches here"},
]


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _dispatch_rows(db_path):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT * FROM dispatches ORDER BY lead_id").fetchall()
    finally:
        con.close()
    return [tuple(r) for r in rows]


def _schema(db_path):
    con = sqlite3.connect(db_path)
    try:
        return [tuple(r) for r in con.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()]
    finally:
        con.close()


def _faces(face):
    return {
        "lifetime": face.route_tally(),
        "d1": face.route_tally(D1),
        "d2": face.route_tally(D2),
        "d3": face.route_tally(D3),
        "empty": face.route_tally(EMPTY_DAY),
    }


def _dumps(faces):
    return {key: json.dumps(value, sort_keys=True)
            for key, value in faces.items()}


def _sha(path):
    with open(path, "rb") as h:
        return hashlib.sha256(h.read()).hexdigest()


def _init_world(tmp):
    root = os.path.join(tmp, "route-persist")
    os.makedirs(root, exist_ok=True)
    db = os.path.join(root, "funnel.db")
    orders = _mk_inbox(root, "orders", [])
    flows = _mk_inbox(root, "flows", [])
    leads = {
        "d1": _mk_inbox(root, "leads1", D1_LEADS),
        "d2": _mk_inbox(root, "leads2", D2_LEADS),
        "d3": _mk_inbox(root, "leads3", D3_LEADS),
        "d3b2": _mk_inbox(root, "leads3b2", D3_LEADS_BATCH2),
    }
    face = fd.FunnelDaily(db)
    try:
        face.run_daily(leads["d1"], orders, flows, D1)
        face.run_daily(leads["d2"], orders, flows, D2)
        face.run_daily(leads["d3"], orders, flows, D3)
        snapshot = _dumps(_faces(face))
        rows = _dispatch_rows(db)
    finally:
        face.close()
    return {
        "db": db,
        "root": root,
        "orders": orders,
        "flows": flows,
        "leads": leads,
        "snapshot": snapshot,
        "rows_anchor": rows,
        "state": {},
    }


def _frtp1(world, tmp):
    snap = world["snapshot"]
    assert json.loads(snap["lifetime"]) == ANCHOR_LIFETIME, \
        "AC-FRTP1 lifetime %r" % snap["lifetime"]
    assert json.loads(snap["d1"]) == ANCHOR_D1, \
        "AC-FRTP1 d1 %r" % snap["d1"]
    assert json.loads(snap["d2"]) == ANCHOR_D2, \
        "AC-FRTP1 d2 %r" % snap["d2"]
    assert json.loads(snap["d3"]) == ANCHOR_D3, \
        "AC-FRTP1 d3 %r" % snap["d3"]
    assert json.loads(snap["empty"]) == {}, \
        "AC-FRTP1 empty %r" % snap["empty"]
    assert len(world["rows_anchor"]) == 9, \
        "AC-FRTP1 rows %d" % len(world["rows_anchor"])


def _frtp2(world, tmp):
    face = fd.FunnelDaily(world["db"])
    try:
        first = _dumps(_faces(face))
        second = _dumps(_faces(face))
    finally:
        face.close()
    assert first == world["snapshot"], \
        "AC-FRTP2 reopen drifted %r" % first
    assert second == world["snapshot"], \
        "AC-FRTP2 repeat read drifted %r" % second


def _frtp3(world, tmp):
    face = fd.FunnelDaily(world["db"])
    try:
        ring = face.run_daily(world["leads"]["d3b2"], world["orders"],
                              world["flows"], D3)
        faces = _faces(face)
    finally:
        face.close()
    assert ring["ring2"]["dispatches_new"] == 2, \
        "AC-FRTP3 dispatches_new %r" % ring["ring2"]
    assert faces["lifetime"] == AFTER_LIFETIME, \
        "AC-FRTP3 lifetime %r" % faces["lifetime"]
    assert faces["d1"] == ANCHOR_D1, \
        "AC-FRTP3 d1 not frozen %r" % faces["d1"]
    assert faces["d2"] == ANCHOR_D2, \
        "AC-FRTP3 d2 not frozen %r" % faces["d2"]
    assert faces["d3"] == AFTER_D3, \
        "AC-FRTP3 d3 %r" % faces["d3"]
    assert faces["empty"] == {}, "AC-FRTP3 empty %r" % faces["empty"]
    world["state"]["after_batch2"] = _dumps(faces)


def _frtp4(world, tmp):
    face = fd.FunnelDaily(world["db"])
    try:
        ring = face.run_daily(world["leads"]["d1"], world["orders"],
                              world["flows"], D1)
        faces = _faces(face)
    finally:
        face.close()
    assert ring["ring1"]["leads_new"] == 0, \
        "AC-FRTP4 leads_new %r" % ring["ring1"]
    assert ring["ring2"]["dispatches_new"] == 0, \
        "AC-FRTP4 dispatches_new %r" % ring["ring2"]
    assert _dumps(faces) == world["state"]["after_batch2"], \
        "AC-FRTP4 lifetime drifted on re-drop"


def _frtp5(world, tmp):
    face = fd.FunnelDaily(world["db"])
    try:
        faces = _faces(face)
        rows = _dispatch_rows(world["db"])
    finally:
        face.close()
    assert len(rows) == 11, "AC-FRTP5 rows %d" % len(rows)
    assert sum(json.loads(world["snapshot"]["lifetime"]).values()) == 9, \
        "AC-FRTP5 anchor lifetime sum"
    assert sum(faces["lifetime"].values()) == 11, \
        "AC-FRTP5 lifetime sum %r" % faces["lifetime"]
    assert faces["d1"] == ANCHOR_D1, "AC-FRTP5 d1 drifted"
    assert faces["d2"] == ANCHOR_D2, "AC-FRTP5 d2 drifted"
    assert json.loads(world["snapshot"]["empty"]) == {}, \
        "AC-FRTP5 empty at anchor"
    assert faces["empty"] == {}, "AC-FRTP5 empty after injection"
    world["state"]["terminal"] = _dumps(faces)


def _frtp6(world, tmp):
    rows_before = _dispatch_rows(world["db"])
    schema_before = _schema(world["db"])
    face = fd.FunnelDaily(world["db"])
    try:
        batch = []
        for _ in range(3):
            batch.append(_dumps(_faces(face)))
        rows_after = _dispatch_rows(world["db"])
        schema_after = _schema(world["db"])
    finally:
        face.close()
    assert rows_after == rows_before, "AC-FRTP6 read wrote dispatches"
    assert schema_after == schema_before, "AC-FRTP6 read changed schema"
    assert batch[0] == batch[1] == batch[2], "AC-FRTP6 read not stable"
    assert batch[0] == world["state"]["terminal"], \
        "AC-FRTP6 reopen drifted from terminal"
    assert rows_before == world["rows_anchor"] + [
        ("c3", D3, "media"), ("c4", D3, "unrouted")] or \
        sorted(rows_before) == sorted(world["rows_anchor"] + [
            ("c3", D3, "media"), ("c4", D3, "unrouted")]), \
        "AC-FRTP6 restart itself wrote rows"


def _frtp7(world, tmp):
    face = fd.FunnelDaily(world["db"])
    try:
        faces = _faces(face)
        rows = _dispatch_rows(world["db"])
    finally:
        face.close()
    assert _dumps(faces) == world["state"]["terminal"], \
        "AC-FRTP7 third instance drifted"
    assert faces["d1"] == ANCHOR_D1, \
        "AC-FRTP7 d1 lost anchor after double restart"
    assert len(rows) == 11, "AC-FRTP7 rows %d" % len(rows)


def _frtp8(world, tmp):
    lib = os.path.join(BASE, "funnel_daily.py")
    raw = open(lib, "rb").read()
    assert all(b < 128 for b in raw), "AC-FRTP8 library not ASCII"
    tree = ast.parse(raw.decode("ascii"))
    banned = ("socket", "urllib", "requests", "http", "asyncio")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, \
                    "AC-FRTP8 network import %s" % alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned, \
                "AC-FRTP8 network import %s" % node.module
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("now", "today", "utcnow"), \
                "AC-FRTP8 wall clock call %s" % node.func.attr

    suite_raw = open(os.path.abspath(__file__), "rb").read()
    assert all(b < 128 for b in suite_raw), "AC-FRTP8 suite not ASCII"

    cfg = os.path.join(BASE, "config.json")
    cfg_sha = _sha(cfg)
    face = fd.FunnelDaily(world["db"])
    try:
        one = json.dumps(_faces(face), sort_keys=True)
        two = json.dumps(_faces(face), sort_keys=True)
    finally:
        face.close()
    assert one == two, "AC-FRTP8 read not deterministic"
    assert _sha(cfg) == cfg_sha, "AC-FRTP8 shipped config mutated"
    assert os.path.abspath(world["root"]).startswith(
        os.path.abspath(tempfile.gettempdir())), \
        "AC-FRTP8 world not outside the repo"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-route-persist-")
    failed = 0
    try:
        world = _init_world(tmp)
        cases = [
            ("AC-FRTP1 three-day anchor world", _frtp1),
            ("AC-FRTP2 restart byte-identical", _frtp2),
            ("AC-FRTP3 post-restart injection, old windows frozen",
             _frtp3),
            ("AC-FRTP4 idempotent re-drop across restart", _frtp4),
            ("AC-FRTP5 lifetime drift and honest empty day", _frtp5),
            ("AC-FRTP6 pure read and restart zero write", _frtp6),
            ("AC-FRTP7 second restart stability", _frtp7),
            ("AC-FRTP8 hygiene and determinism", _frtp8),
        ]
        for name, fn in cases:
            try:
                fn(world, tmp)
                print("PASS %s" % name)
            except AssertionError as exc:
                failed += 1
                print("FAIL %s :: %s" % (name, exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases)
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())