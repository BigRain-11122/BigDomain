"""Battery suite: the CEO face's chain block carries the QUALIFICATION (R3619).

AC-EXA1..AC-EXA5 were pinned in src/os/backlog.md BEFORE this file existed.
The defect they hold: docs/status-export.json published `chain.broken=5` and
nothing else, so on the one face a reader is asked to believe, five broken
links read as five lost records - while the shipped owner of that judgement
(tools/qa_chain_diagnose.py) read verdict=OK unexplained=0 on the same bytes.
The command-line station learned this last window (AC-LADJ, R3618); the export
did not.

What is measured here: the four new values come from qa_log.chain_reading (the
shipped helper, no second link law), they equal that helper field by field in a
private world, an unreadable adjudicator reads UNADJUDICATED with null numbers
rather than 0/OK, the live export carries all eight keys agreeing with the live
ledger, the four old keys keep their values and their order, and the face
writes nothing.

Isolation: every world lives in the system temp dir; the live export is only
read. Stdlib only, ASCII source, no network.
"""

import ast
import inspect
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
TOOLS = os.path.join(ROOT, "tools")
for _path in (TOOLS, BASE):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import status_export_fresh as sx  # noqa: E402
import qa_log as QL  # noqa: E402

CRITERIA = ("AC-EXA1", "AC-EXA2", "AC-EXA3", "AC-EXA4", "AC-EXA5")
FAILS = []
CHECKS = [0]

NEW_KEYS = ["adjudication", "broken", "declared", "excused", "partial",
            "path", "present", "rows", "unexplained"]
OLD_ORDER = ["present", "rows", "broken", "path"]


def check(ac, ok, evidence):
    CHECKS[0] += 1
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)
    if not ok:
        FAILS.append(ac)


def write_ledger(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def row(name, old_sha, new_sha, old_bytes=1, new_bytes=2, kind=None):
    record = {"event": "REPLACED", "name": name, "old_sha16": old_sha,
              "new_sha16": new_sha, "old_bytes": old_bytes,
              "new_bytes": new_bytes, "ts": "2026-11-28T00:00:00+08:00"}
    if kind is not None:
        record["prev_kind"] = kind
    return record


def world(ledger_rows):
    root = tempfile.mkdtemp(prefix="export-exa-")
    os.makedirs(os.path.join(root, "state"))
    os.makedirs(os.path.join(root, "qa"))
    write_ledger(os.path.join(root, "state", QL.LEDGER_NAME), ledger_rows)
    return root


def word_world():
    """A world whose single break no progress writer can explain."""
    return world([row("not-a-shard.log", "a" * 16, "b" * 16),
                  row("not-a-shard.log", "c" * 16, "d" * 16,
                      old_bytes=9, new_bytes=10)])


def declared_world():
    return world([row("x.log", "a" * 16, "b" * 16),
                  row("x.log", "c" * 16, "d" * 16, old_bytes=9, new_bytes=10,
                      kind=QL.PREV_KIND_PROGRESS)])


def body_dump(fn):
    """The function's CODE, with the docstring removed.

    The first run of AC-EXA1 reddened on the word "progress-partials" inside
    the helper's own docstring, which explains the law rather than restating
    it; the criterion is about code, so prose is stripped before the scan.
    """
    tree = ast.parse(inspect.getsource(fn))
    body = tree.body[0].body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return "\n".join(ast.dump(part) for part in body)


def shared_definition_arm(red_root):
    source = inspect.getsource(sx)
    helper = body_dump(sx.adjudication_face)
    once = source.count("QL.chain_reading(") == 1
    no_law = ("old_sha16" not in helper and "new_sha16" not in helper
              and "progress-partial" not in helper)

    saved = QL.chain_reading
    QL.chain_reading = lambda path=None: None
    try:
        blind = sx.chain_face(red_root)
    finally:
        QL.chain_reading = saved
    # A face that invented its own numbers would keep reading the red world's
    # counts here; asking and getting nothing must read as nothing.
    proves_shared = (blind["adjudication"] == "UNADJUDICATED"
                     and blind["partial"] is None and blind["unexplained"] is None)
    restored = sx.chain_face(red_root)

    check("AC-EXA1",
          once and no_law and proves_shared
          and restored["adjudication"] == "RED",
          "one chain_reading() call=%s, helper carries no second law=%s, "
          "patched-away helper reads %r, restored reads %r"
          % (once, no_law, blind["adjudication"], restored["adjudication"]))


def field_arms(red_root, ok_root):
    import closeout_gate as CG
    ledger = os.path.join(red_root, "state", QL.LEDGER_NAME)
    block = sx.chain_face(red_root)
    expected = QL.chain_reading(ledger)
    report = QL.ledger_report(ledger, evidence_dir=os.path.join(red_root, "qa"))
    counts = {}
    CG.check_ledger(red_root, counts)
    same = (block["partial"] == expected["partial"]
            and block["declared"] == expected["declared"]
            and block["unexplained"] == expected["unexplained"]
            and block["adjudication"] == expected["verdict"]
            and block["broken"] == len(report["broken"])
            and block["rows"] == counts["rows"]
            and block["present"] == counts["present"])
    order_kept = list(block)[:4] == OLD_ORDER

    ok_block = sx.chain_face(ok_root)
    declared_only = (ok_block["adjudication"] == "OK"
                     and ok_block["declared"] == 1
                     and ok_block["unexplained"] == 0
                     and ok_block["partial"] == 0)

    check("AC-EXA2", same and order_kept and declared_only,
          "red world block=%s expected=%r; old-key order kept=%s; "
          "declared-only world reads adjudication=%s declared=%d"
          % (json.dumps(block, sort_keys=True), expected, order_kept,
             ok_block["adjudication"], ok_block["declared"]))


def unreadable_arm(red_root):
    saved = sys.modules.get("qa_chain_diagnose", "absent")
    sys.modules["qa_chain_diagnose"] = None
    try:
        block = sx.chain_face(red_root)
    finally:
        if saved == "absent":
            sys.modules.pop("qa_chain_diagnose", None)
        else:
            sys.modules["qa_chain_diagnose"] = saved
    # Round-trip through JSON: null must stay null, never collapse to 0.
    landed = json.loads(json.dumps(block, sort_keys=True))
    ok = (landed["adjudication"] == "UNADJUDICATED"
          and landed["partial"] is None and landed["declared"] is None
          and landed["unexplained"] is None
          and landed["broken"] == 1)
    restored = sx.chain_face(red_root)

    check("AC-EXA3", ok and restored["adjudication"] == "RED",
          "blocked adjudicator reads %s; restored reads %r"
          % (json.dumps(landed, sort_keys=True), restored["adjudication"]))


def live_arm():
    export = os.path.join(ROOT, "docs", "status-export.json")
    doc = json.loads(io.open(export, encoding="utf-8").read())
    block = doc.get("chain") or {}
    live = QL.chain_reading(QL.LEDGER)
    report = QL.ledger_report(QL.LEDGER)
    keys_ok = sorted(block) == NEW_KEYS
    values_ok = (live is not None
                 and block.get("partial") == live["partial"]
                 and block.get("declared") == live["declared"]
                 and block.get("unexplained") == live["unexplained"]
                 and block.get("adjudication") == live["verdict"]
                 and block.get("broken") == len(report["broken"])
                 and isinstance(block.get("present"), bool))
    check("AC-EXA4", keys_ok and values_ok,
          "live export chain keys=%s, block=%s, live reading=%r"
          % (",".join(sorted(block)), json.dumps(block, sort_keys=True), live))


def additive_arm(red_root):
    export = os.path.join(ROOT, "docs", "status-export.json")
    before = (os.path.getsize(export), os.stat(export).st_mtime_ns)
    first = sx.chain_face(red_root)
    second = sx.chain_face(red_root)
    after = (os.path.getsize(export), os.stat(export).st_mtime_ns)
    pure = before == after
    deterministic = (json.dumps(first, sort_keys=True)
                     == json.dumps(second, sort_keys=True))

    tool_source = io.open(os.path.join(TOOLS, "status_export_fresh.py"),
                          "rb").read()
    try:
        tool_source.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    text = tool_source.decode("ascii", "replace")
    no_network = all(token not in text
                     for token in ("import socket", "import urllib",
                                   "import http", "import requests"))

    # The old arms still pin the block EXACTLY, at the new eight keys: a
    # dropped or added key reddens them, so the contract is not loosened.
    # Four arms pin it, not the three the PIN row counted (measured here).
    old_suite = io.open(os.path.join(BASE, "test_status_export_fresh.py"),
                        encoding="utf-8").read()
    pinned = ('"adjudication", "broken", "declared", "excused", "partial", '
              '"path"')
    exact = old_suite.count(pinned) == 4
    stale_old = '["broken", "path", "present", "rows"]' in old_suite
    registry = io.open(os.path.join(ROOT, "src", "sandbox", "reconcile_all.py"),
                       encoding="utf-8").read()
    wired = '("os-export-chain-adjudication",' in registry

    check("AC-EXA5",
          pure and deterministic and ascii_ok and no_network and exact
          and not stale_old and wired,
          "export (size,mtime_ns) unchanged=%s, twin reads identical=%s, "
          "ASCII=%s, no network=%s, old arms pin new keys=%d, stale four-key "
          "pin left=%s, wired in reconcile_all=%s"
          % (pure, deterministic, ascii_ok, no_network,
             old_suite.count(pinned), stale_old, wired))


def main():
    red_root = word_world()
    ok_root = declared_world()
    shared_definition_arm(red_root)
    field_arms(red_root, ok_root)
    unreadable_arm(red_root)
    live_arm()
    additive_arm(red_root)
    verdict = "PASS" if not FAILS else "FAIL:" + ",".join(FAILS)
    print("SUITE %s %d/%d" % (verdict, CHECKS[0] - len(FAILS), CHECKS[0]),
          flush=True)
    print("SUITE criteria=%d failed=%s"
          % (len(CRITERIA), ",".join(FAILS) or "(none)"), flush=True)
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
