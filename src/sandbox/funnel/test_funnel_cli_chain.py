"""FUNNEL daily CLI multi-day evidence determinism suite (R2056).

Pre-registered criteria AC-FCC1..AC-FCC8 live in state/queue/tech.md
and were written BEFORE this suite existed (honesty law). The seed is
the R2052 conservation-neighbour reseed row: the CLI accepted
--evidence (R2033, self-tee single dialect) and the rejected-argument
family was pinned (AC-FCG, R2048), but the MULTI-DAY chain face had
no example - does a run over D1/D2/D3 produce one evidence file per
day, is a second identical chain byte-identical, and does the
printed envelope agree with the stored rollup?

World: a throwaway temp tree with an explicit --db, three explicit
inbox dirs per day, and explicit --evidence paths. The CLI is driven
as a real subprocess (the production face), never by importing main.

Note on the self-tee comparison: on Windows the text stdout stream
translates "\n" to "\r\n" while the evidence file is opened with
newline="\n" (coding law), so stdout is normalised to LF before the
byte comparison. That is stated here so the assertion is honest.

Pure ASCII source (coding law).
"""

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
SCRIPT = os.path.join(BASE, "funnel_daily.py")
SHIPPED_CONFIG = os.path.join(BASE, "config.json")

D1 = "2026-10-17"
D2 = "2026-10-18"
D3 = "2026-10-19"

# Captured at import, i.e. before any case runs (AC-FCC8 drift anchor).
_SHA_BEFORE = {}

# Day-window count keys: deterministic across a chain rerun. The
# lifetime key token_outstanding_total is deliberately excluded - it
# recomputes from the whole ledger by product design (R2052 AC-FCV7).
_WINDOW_KEYS = (
    "leads_day",
    "dispatches_day",
    "orders_day",
    "token_granted_day",
    "token_spent_day",
)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as fh:
            json.dump(row, fh, ensure_ascii=False)
    return d


def _world(root):
    """Three-day chain world: D1 two rings active, D2 one lead plus
    one order plus one flow, D3 a single lead (honest sparse day)."""
    day_rows = {
        D1: {
            "leads": [{"lead_id": "L1", "source": "s",
                       "text": "I want a game demo level"}],
            "orders": [{"order_id": "O1", "sku": "compute-pack-19.9",
                        "amount_cent": 1990}],
            "flows": [
                {"flow_id": "F1", "account": "u1", "kind": "grant",
                 "amount": 100},
                {"flow_id": "F2", "account": "u1", "kind": "spend",
                 "amount": 30},
            ],
        },
        D2: {
            "leads": [{"lead_id": "L2", "source": "s",
                       "text": "need an analytics dashboard"}],
            "orders": [{"order_id": "O2", "sku": "report-pack-9.9",
                        "amount_cent": 990}],
            "flows": [{"flow_id": "F3", "account": "u2", "kind": "grant",
                       "amount": 50}],
        },
        D3: {
            "leads": [{"lead_id": "L3", "source": "s",
                       "text": "visual demo for a game"}],
            "orders": [],
            "flows": [],
        },
    }
    boxes = {}
    for day, faces in day_rows.items():
        tag = day.replace("-", "")
        boxes[day] = {
            "leads": _mk_inbox(root, "leads-" + tag, faces["leads"]),
            "orders": _mk_inbox(root, "orders-" + tag, faces["orders"]),
            "flows": _mk_inbox(root, "flows-" + tag, faces["flows"]),
        }
    return boxes, day_rows


def _run(db, day, boxes, evidence, config=None):
    cmd = [sys.executable, SCRIPT,
           "--day", day,
           "--db", db,
           "--leads-inbox", boxes["leads"],
           "--orders-inbox", boxes["orders"],
           "--flows-inbox", boxes["flows"],
           "--evidence", evidence]
    if config is not None:
        cmd.extend(["--config", config])
    proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout


def _run_chain(root, db, boxes, tag):
    ev = {}
    outs = {}
    rcs = {}
    for day in (D1, D2, D3):
        path = os.path.join(root, "evidence-%s-%s.log"
                            % (tag, day.replace("-", "")))
        rc, out = _run(db, day, boxes[day], path)
        ev[day] = path
        outs[day] = out
        rcs[day] = rc
    return ev, outs, rcs


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def _envelope_of(evidence_bytes):
    for raw in evidence_bytes.decode("utf-8").split("\n"):
        if raw.startswith("envelope "):
            return json.loads(raw[len("envelope "):])
    raise AssertionError("evidence has no envelope line")


def _neutral(line):
    """Blank the per-pass activity fields so two runs can be compared on
    everything else: the ring 'new=N' counter and ring 2's routes dict
    both legitimately report "nothing new this pass" on a rerun."""
    import re
    line = re.sub(r"new=\d+", "new=0", line)
    return re.sub(r"routes=.*$", "routes={}", line)


def _rollup_of(db, day):
    con = sqlite3.connect(db)
    try:
        row = con.execute("SELECT envelope FROM rollups WHERE day=?",
                          (day,)).fetchone()
    finally:
        con.close()
    if row is None:
        raise AssertionError("no stored rollup for day %s" % day)
    return json.loads(row[0])


def _counts(db):
    con = sqlite3.connect(db)
    try:
        return {
            t: con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
            for t in ("leads", "dispatches", "orders", "flows", "rollups")
        }
    finally:
        con.close()


def case_fcc1(tmp):
    """AC-FCC1: single-day self-tee law - the evidence file is exactly
    the stdout block (CRLF normalised to LF), strict utf-8, no BOM,
    LF only."""
    root = os.path.join(tmp, "fcc1")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, _ = _world(root)
    ev = os.path.join(root, "evidence.log")
    rc, out = _run(db, D1, boxes[D1], ev)
    assert rc == 0, "clean world must exit 0, got %d" % rc
    raw = _read_bytes(ev)
    assert raw[:3] != b"\xef\xbb\xbf", "evidence must carry no BOM"
    assert b"\r" not in raw, "evidence must be LF only, no CR"
    raw.decode("utf-8")  # strict decode: zero UnicodeDecodeError
    assert raw == out.replace(b"\r\n", b"\n"), (
        "evidence bytes must equal the stdout block after LF normalisation"
    )


def case_fcc2(tmp):
    """AC-FCC2: the three-day chain is day-isolated - each evidence
    file carries its own day and its own ring counts, and no other
    day's lead text leaks in."""
    root = os.path.join(tmp, "fcc2")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, rows = _world(root)
    ev, _, rcs = _run_chain(root, db, boxes, "a")
    want = {
        D1: (1, 1, 1, 130),
        D2: (1, 1, 1, 50),
        D3: (1, 1, 0, 0),
    }
    for day in (D1, D2, D3):
        assert rcs[day] == 0, "%s must exit 0, got %d" % (day, rcs[day])
        text = _read_bytes(ev[day]).decode("utf-8")
        assert "FUNNEL-DAILY day=%s " % day in text, (
            "%s evidence must name its own day" % day
        )
        env = _envelope_of(_read_bytes(ev[day]))
        c = env["counts"]
        got = (c["leads_day"], c["dispatches_day"], c["orders_day"],
               c["token_granted_day"] + c["token_spent_day"])
        assert got == want[day], (
            "%s ring counts wrong: got %r want %r" % (day, got, want[day])
        )
        # Ring "new" counts equal the rows newly booked on that day.
        new_leads = len(rows[day]["leads"])
        new_orders = len(rows[day]["orders"])
        new_flows = len(rows[day]["flows"])
        assert ("ring1 leads: files=%d seen=%d new=%d"
                % (new_leads, new_leads, new_leads)) in text, (
            "%s ring1 new count wrong" % day
        )
        assert ("ring3 orders: seen=%d new=%d"
                % (new_orders, new_orders)) in text, (
            "%s ring3 new count wrong" % day
        )
        assert ("ring4 flows: seen=%d new=%d"
                % (new_flows, new_flows)) in text, (
            "%s ring4 new count wrong" % day
        )
        # Day isolation: only this day's lead texts appear.
        for other in (D1, D2, D3):
            if other == day:
                continue
            for row in rows[other]["leads"]:
                assert row["text"] not in text, (
                    "%s evidence leaks %s lead text" % (day, other)
                )


def case_fcc3(tmp):
    """AC-FCC3: chain-rerun evidence determinism, as the product really
    behaves. The pre-registered wording said "every evidence file is
    byte-identical across the rerun"; delivery-time measurement showed
    two legitimate product behaviours: (a) the ring lines flip their
    per-pass activity fields on a rerun (new=0, ring 2 routes={}), and
    (b) the envelope's lifetime key token_outstanding_total recomputes
    from the then-current whole ledger, so it (and the derived lifetime
    delta) can move when a later day already booked flows in the first
    pass - exactly the R2052 AC-FCV7 finding.

    Honest law pinned here: ring lines may differ only in those two
    activity fields with files/seen unchanged; every day-window count
    key and its delta are identical across the rerun; the summary and
    focus lines are byte-identical; and the stored rollup equals the
    printed envelope of its own run. The amendment is recorded in the
    tech.md claim row.
    """
    root = os.path.join(tmp, "fcc3")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, _ = _world(root)
    ev_a, _, _ = _run_chain(root, db, boxes, "a")
    first = {d: _read_bytes(ev_a[d]) for d in (D1, D2, D3)}
    stored_a = {d: _rollup_of(db, d) for d in (D1, D2, D3)}
    ev_b, _, rcs = _run_chain(root, db, boxes, "b")
    for day in (D1, D2, D3):
        assert rcs[day] == 0, "%s rerun must exit 0" % day
        lines_a = first[day].decode("utf-8").split("\n")
        lines_b = _read_bytes(ev_b[day]).decode("utf-8").split("\n")
        assert len(lines_a) == len(lines_b), (
            "%s evidence line count drifted" % day
        )
        for la, lb in zip(lines_a, lines_b):
            if la.startswith("ring"):
                assert _neutral(la) == lb, (
                    "%s ring line changed by more than the per-pass"
                    " fields: %r vs %r" % (day, la, lb)
                )
                assert "new=0" in lb, (
                    "%s rerun ring new counter must be 0: %r" % (day, lb)
                )
                if lb.startswith("ring2"):
                    assert "routes={}" in lb, (
                        "%s rerun ring2 must report no new routes: %r"
                        % (day, lb)
                    )
            elif la.startswith("envelope "):
                env_a = json.loads(la[len("envelope "):])
                env_b = json.loads(lb[len("envelope "):])
                for key in _WINDOW_KEYS:
                    assert env_a["counts"][key] == env_b["counts"][key], (
                        "%s day-window key %s drifted on rerun"
                        % (day, key)
                    )
                da, db_ = env_a["delta_prev_day"], env_b["delta_prev_day"]
                if da is None or db_ is None:
                    assert da is db_, (
                        "%s delta presence drifted on rerun" % day
                    )
                else:
                    for key in _WINDOW_KEYS:
                        assert da[key] == db_[key], (
                            "%s day-window delta %s drifted on rerun"
                            % (day, key)
                        )
                assert env_a["day"] == env_b["day"]
                assert env_a["gate"] == env_b["gate"]
                assert env_a["verdict_line"] == env_b["verdict_line"]
            else:
                assert la == lb, (
                    "%s evidence line drifted: %r vs %r"
                    % (day, la, lb)
                )
        fresh = _rollup_of(db, day)
        printed = _envelope_of(_read_bytes(ev_b[day]))
        assert fresh == printed, (
            "%s stored rollup must equal its own printed envelope" % day
        )
        for key in _WINDOW_KEYS:
            assert fresh["counts"][key] == stored_a[day]["counts"][key], (
                "%s stored day-window key %s drifted" % (day, key)
            )


def case_fcc4(tmp):
    """AC-FCC4: the printed envelope equals the stored rollup envelope
    for that day, and the gate field agrees with the exit code."""
    root = os.path.join(tmp, "fcc4")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, _ = _world(root)
    ev, _, rcs = _run_chain(root, db, boxes, "a")
    for day in (D1, D2, D3):
        env = _envelope_of(_read_bytes(ev[day]))
        stored = _rollup_of(db, day)
        assert env == stored, (
            "%s printed envelope must equal the stored rollup" % day
        )
        assert env["gate"] == "PASS" and rcs[day] == 0, (
            "%s gate PASS must pair with exit 0" % day
        )


def case_fcc5(tmp):
    """AC-FCC5: gate/exit contract pair - the clean chain is PASS/0,
    and a banned-word config world is FAIL/2 while still writing the
    evidence file (fail-closed never swallows the evidence)."""
    root = os.path.join(tmp, "fcc5")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, _ = _world(root)
    cfg = os.path.join(root, "config.json")
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump({"banned_words": ["pipeline readiness"],
                   "standing_lines": {"aigc": "AIGC generated content; "
                                             "not investment advice"}},
                  fh, ensure_ascii=False)
    ev = os.path.join(root, "evidence-fail.log")
    rc, out = _run(db, D1, boxes[D1], ev, config=cfg)
    assert rc == 2, "banned-word world must exit 2, got %d" % rc
    raw = _read_bytes(ev)
    assert raw, "evidence must still be written on a FAIL day"
    env = _envelope_of(raw)
    assert env["gate"] == "FAIL", "gate field must read FAIL"
    assert env["hits"], "a FAIL envelope must name its hits"
    assert b"gate=FAIL" in raw, "the summary line must show gate=FAIL"


def case_fcc6(tmp):
    """AC-FCC6: evidence purity - every byte is ASCII (<128), the repo
    root never leaks into the file, and no date other than the
    injected days appears (zero wall clock)."""
    root = os.path.join(tmp, "fcc6")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, _ = _world(root)
    ev, _, _ = _run_chain(root, db, boxes, "a")
    root_b = REPO_ROOT.encode("ascii")
    for day in (D1, D2, D3):
        raw = _read_bytes(ev[day])
        assert all(b < 128 for b in raw), (
            "%s evidence must stay ascii-escaped" % day
        )
        assert root_b not in raw, (
            "%s evidence leaks the repo root path" % day
        )
        text = raw.decode("ascii")
        for token in ("2026-10-20", "2099", "1970"):
            assert token not in text, (
                "%s evidence carries an un-injected date %s"
                % (day, token)
            )


def case_fcc7(tmp):
    """AC-FCC7: source-table idempotency - the chain rerun leaves every
    source table at the same row counts (first write wins, no ghosts)."""
    root = os.path.join(tmp, "fcc7")
    os.makedirs(root)
    db = os.path.join(root, "funnel.db")
    boxes, _ = _world(root)
    _run_chain(root, db, boxes, "a")
    after_first = _counts(db)
    _run_chain(root, db, boxes, "b")
    after_second = _counts(db)
    assert after_first == after_second, (
        "chain rerun must not add rows: %r vs %r"
        % (after_first, after_second)
    )
    assert after_first["rollups"] == 3, (
        "one stored rollup row per day, got %d" % after_first["rollups"]
    )


def case_fcc8(tmp):
    """AC-FCC8: hygiene - pure ASCII source, AST audit finds no network
    imports and no wall-clock calls, shipped config and the product
    module keep their sha256, and the world lives outside the repo."""
    src_path = os.path.abspath(__file__)
    raw = _read_bytes(src_path)
    assert all(b < 128 for b in raw), "suite source must be pure ASCII"
    tree = ast.parse(raw.decode("ascii"))
    banned_modules = {"socket", "urllib", "requests", "http", "ftplib",
                      "time"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_modules, (
                    "network/time import is banned: %s" % alias.name
                )
        elif isinstance(node, ast.ImportFrom):
            root_name = (node.module or "").split(".")[0]
            assert root_name not in banned_modules, (
                "network/time import is banned: %s" % node.module
            )
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                assert func.attr not in ("now", "today", "utcnow"), (
                    "wall-clock call is banned: %s" % func.attr
                )
    assert not os.path.abspath(tmp).startswith(REPO_ROOT), (
        "the temp world must live outside the repo"
    )
    after = {"config": _sha(SHIPPED_CONFIG), "module": _sha(SCRIPT)}
    assert after == _SHA_BEFORE, (
        "shipped config / product module drifted: %r vs %r"
        % (_SHA_BEFORE, after)
    )


def main():
    _SHA_BEFORE.update({
        "config": _sha(SHIPPED_CONFIG),
        "module": _sha(SCRIPT),
    })
    tmp = tempfile.mkdtemp(prefix="funnel-cli-chain-")
    cases = [
        ("AC-FCC1 single-day self-tee bytes", case_fcc1),
        ("AC-FCC2 multi-day chain day isolation", case_fcc2),
        ("AC-FCC3 chain rerun determinism (day-window law)", case_fcc3),
        ("AC-FCC4 envelope equals stored rollup", case_fcc4),
        ("AC-FCC5 gate/exit contract pair", case_fcc5),
        ("AC-FCC6 evidence purity", case_fcc6),
        ("AC-FCC7 source-table idempotency", case_fcc7),
        ("AC-FCC8 hygiene + zero drift", case_fcc8),
    ]
    failed = 0
    try:
        for name, fn in cases:
            try:
                fn(tmp)
                print("PASS %s" % name)
            except AssertionError as exc:
                failed += 1
                print("FAIL %s :: %s" % (name, exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases)
    print("SUITE %s %d/%d"
          % ("PASS" if not failed else "FAIL", total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())