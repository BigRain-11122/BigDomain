"""Battery suite: the face names the row its break count withholds (R3621).

AC-EXE1..AC-EXE5 were pinned in src/os/backlog.md BEFORE this file existed.
The defect they hold: the live ledger answers rows=106 broken=5 excused=1 while
the adjudicator counts six unlinked rows (partial=5 declared=1 unexplained=0),
so a reader who tries to reconcile broken=5 with partial+declared=6 finds one
row that has no name on either face - the row the count station withholds from
`broken` because its later row declares it replaced a progress partial.

What is measured here: `excused` comes from the SAME qa_log.ledger_report the
count station already read (no new parse, no second link law), it equals that
report in private and live worlds, a reading that stops carrying it publishes
null rather than 0, the two stations reconcile as broken + excused == partial +
declared + unexplained on the export and on the page, an unreadable adjudicator
publishes UNADJUDICATED while `excused` still reports its own count, and the
face writes nothing.

Isolation: every world lives in the system temp dir; the live export and the
landed pair are read, never written. No network (the money legs run on an
in-process world through the shipped sandbox modules). ASCII only.
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
import closeout_gate as CG  # noqa: E402
import qa_log as QL  # noqa: E402
import first_yuan_chain as FY  # noqa: E402

CRITERIA = ("AC-EXE1", "AC-EXE2", "AC-EXE3", "AC-EXE4", "AC-EXE5")
FAILS = []
CHECKS = [0]

OLD_ORDER = ["present", "rows", "broken", "path"]
NEW_KEYS = ["adjudication", "broken", "declared", "excused", "landed_missing",
            "landed_ok", "partial", "path", "present", "rewritten", "rows",
            "unexplained"]
ELEVEN_KEYS = ["adjudication", "broken", "declared", "landed_missing",
               "landed_ok", "partial", "path", "present", "rewritten", "rows",
               "unexplained"]
IDENTITY = ("broken", "excused", "partial", "declared", "unexplained")

HTML_PATH = os.path.join(ROOT, "preview", "first-yuan-chain.html")
JSON_PATH = os.path.join(ROOT, "preview", "first-yuan-chain.json")
EXPORT_PATH = os.path.join(ROOT, "docs", "status-export.json")


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
    root = tempfile.mkdtemp(prefix="export-exe-")
    os.makedirs(os.path.join(root, "state"))
    os.makedirs(os.path.join(root, "qa"))
    write_ledger(os.path.join(root, "state", QL.LEDGER_NAME), ledger_rows)
    return root


def mixed_world():
    """One excused row and one break no declaration explains."""
    return world([row("x.log", "a" * 16, "b" * 16),
                  row("x.log", "c" * 16, "d" * 16, old_bytes=9, new_bytes=10,
                      kind=QL.PREV_KIND_PROGRESS),
                  row("not-a-shard.log", "e" * 16, "f" * 16),
                  row("not-a-shard.log", "1" * 16, "2" * 16,
                      old_bytes=7, new_bytes=8)])


def declared_world():
    """Only the excused row: the count station charges nothing, the
    adjudicator counts one break. This is the shape that read as a contradiction."""
    return world([row("x.log", "a" * 16, "b" * 16),
                  row("x.log", "c" * 16, "d" * 16, old_bytes=9, new_bytes=10,
                      kind=QL.PREV_KIND_PROGRESS)])


def body_dump(fn):
    """The function's CODE with its docstring stripped: prose explains a law,
    a second call restates it, and only the latter is a defect."""
    tree = ast.parse(inspect.getsource(fn))
    body = tree.body[0].body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return "\n".join(ast.dump(part) for part in body)


def identity(block):
    """broken + excused == partial + declared + unexplained, or None if either
    station could not read (a missing number is not a zero)."""
    five = [block.get(key) for key in IDENTITY]
    if not all(isinstance(value, int) and not isinstance(value, bool)
               for value in five):
        return None
    broken, excused, partial, declared, unexplained = five
    return broken + excused == partial + declared + unexplained


def shared_definition_arm(mixed):
    gate_text = io.open(os.path.join(TOOLS, "closeout_gate.py"),
                        encoding="utf-8").read()
    face = gate_text[gate_text.index("def check_ledger("):]
    face = face[:face.index("def check_census(")]
    once = face.count('report["excused"]') == 1
    no_second_parse = ("read_ledger" not in face and "json." not in face
                       and "hashlib" not in face)
    helper = body_dump(sx.chain_face)
    no_law = ("ledger_report" not in helper and "old_sha16" not in helper
              and "new_sha16" not in helper)

    # Negative control: a reading that stops carrying the field publishes None.
    # A face that invented a number locally would still answer 1 here.
    saved = CG.check_ledger

    def stripped(root, reading=None):
        if reading is not None:
            reading.update({"present": True, "rows": 4, "names": 2, "bad": 0,
                            "stale": 0, "missing": 0, "broken": 0})
        return True, ["LEDGER stub"]

    CG.check_ledger = stripped
    try:
        blind = sx.chain_face(mixed)
    finally:
        CG.check_ledger = saved
    restored = sx.chain_face(mixed)

    check("AC-EXE1",
          once and no_second_parse and no_law
          and blind["excused"] is None and restored["excused"] == 1,
          "one report[\"excused\"]=%s, no new parse=%s, helper carries no law=%s, "
          "stripped reading publishes %r, restored reads %r"
          % (once, no_second_parse, no_law, blind["excused"],
             restored["excused"]))


def field_arms(mixed, declared_root):
    ledger = os.path.join(mixed, "state", QL.LEDGER_NAME)
    report = QL.ledger_report(ledger, evidence_dir=os.path.join(mixed, "qa"))
    block = sx.chain_face(mixed)
    same = block["excused"] == len(report["excused"]) == 1
    closed = identity(block) is True
    order_kept = list(block)[:4] == OLD_ORDER
    live = sx.chain_face(ROOT)
    live_report = QL.ledger_report(QL.LEDGER)
    live_ok = (live["excused"] == len(live_report["excused"])
               and live["broken"] == len(live_report["broken"])
               and identity(live) is True)
    withholds = sx.chain_face(declared_root)
    only_excused = (withholds["broken"] == 0 and withholds["excused"] == 1
                    and withholds["adjudication"] == "OK"
                    and identity(withholds) is True)

    check("AC-EXE2", same and closed and order_kept and live_ok and only_excused,
          "mixed world block=%s report excused=%d identity=%s; old-key order "
          "kept=%s; live excused=%r broken=%r identity=%s; declared-only world "
          "broken=%r excused=%r"
          % (json.dumps(block, sort_keys=True), len(report["excused"]),
             identity(block), order_kept, live["excused"], live["broken"],
             identity(live), withholds["broken"], withholds["excused"]))


def unreadable_arm(mixed):
    saved = sys.modules.get("qa_chain_diagnose", "absent")
    sys.modules["qa_chain_diagnose"] = None
    try:
        block = sx.chain_face(mixed)
    finally:
        if saved == "absent":
            sys.modules.pop("qa_chain_diagnose", None)
        else:
            sys.modules["qa_chain_diagnose"] = saved
    landed = json.loads(json.dumps(block, sort_keys=True))
    qualifier_blind = (landed["adjudication"] == "UNADJUDICATED"
                       and landed["partial"] is None
                       and landed["declared"] is None
                       and landed["unexplained"] is None
                       # the count station is a DIFFERENT station: its own
                       # number survives the other one going blind.
                       and landed["excused"] == 1
                       and identity(landed) is None)

    absent_root = tempfile.mkdtemp(prefix="export-exe-absent-")
    os.makedirs(os.path.join(absent_root, "state"))
    os.makedirs(os.path.join(absent_root, "qa"))
    absent = sx.chain_face(absent_root)
    measured_empty = (absent["present"] is False and absent["rows"] == 0
                      and absent["excused"] == 0 and identity(absent) is True)
    restored = sx.chain_face(mixed)

    check("AC-EXE3", qualifier_blind and measured_empty
          and restored["adjudication"] == "RED",
          "blind adjudicator reads %s (identity=%s); absent ledger reads "
          "present=%r rows=%r excused=%r; restored reads %r"
          % (json.dumps(landed, sort_keys=True), identity(landed),
             absent["present"], absent["rows"], absent["excused"],
             restored["adjudication"]))


def live_arm():
    doc = json.loads(io.open(EXPORT_PATH, encoding="utf-8").read())
    block = doc.get("chain") or {}
    report = QL.ledger_report(QL.LEDGER)
    keys_ok = sorted(block) == NEW_KEYS
    value_ok = (block.get("excused") == len(report["excused"])
                and identity(block) is True)

    landed = json.loads(io.open(JSON_PATH, encoding="utf-8").read())
    page = io.open(HTML_PATH, encoding="utf-8").read()
    same = landed.get("record_chain") == FY.record_chain_face()
    rendered = landed.get("record_chain") or {}
    printed = ("excused=" in page
               and ("excused=%s" % FY.shown(rendered.get("excused"))) in page)
    rc = FY.do_check()
    source = io.open(os.path.join(TOOLS, "first_yuan_chain.py"),
                     encoding="utf-8").read()
    guarded = ("E_RECORD_CHAIN unreconciled" in source
               and "E_RECORD_CHAIN excused label missing" in source)

    check("AC-EXE4",
          keys_ok and value_ok and same and printed and rc == 0 and guarded,
          "live chain keys=%s excused=%r identity=%s; landed record_chain "
          "equals the face=%s; page prints excused=%r; --check rc=%d; identity "
          "assertion shipped=%s"
          % (",".join(sorted(block)), block.get("excused"), identity(block),
             same, rendered.get("excused"), rc, guarded))


def additive_arm(mixed):
    block = sx.chain_face(mixed)
    eight = dict((key, value) for key, value in block.items()
                 if key != "excused")
    unchanged = (sorted(eight) == ELEVEN_KEYS
                 and block["broken"] == 1 and block["rows"] == 4)
    live = json.loads(io.open(EXPORT_PATH, encoding="utf-8").read())["chain"]
    live_eight = dict((key, value) for key, value in live.items()
                      if key != "excused")
    live_old = sorted(live_eight) == ELEVEN_KEYS

    ascii_ok = True
    for name in ("closeout_gate.py", "status_export_fresh.py",
                 "first_yuan_chain.py"):
        raw = io.open(os.path.join(TOOLS, name), "rb").read()
        try:
            raw.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
    text = io.open(os.path.join(TOOLS, "first_yuan_chain.py"),
                   encoding="utf-8").read()
    no_network = all(token not in text
                     for token in ("import socket", "import urllib",
                                   "import http", "import requests"))

    registry = io.open(os.path.join(ROOT, "src", "sandbox", "reconcile_all.py"),
                       encoding="utf-8").read()
    wired = '("os-export-chain-excused",' in registry

    old_suite = io.open(os.path.join(BASE, "test_status_export_fresh.py"),
                        encoding="utf-8").read()
    pinned = ('"adjudication", "broken", "declared", "excused", '
              '"landed_missing"')
    exact = old_suite.count(pinned) == 4
    stale = '"adjudication", "broken", "declared", "partial", "path"' in old_suite

    check("AC-EXE5",
          unchanged and live_old and ascii_ok and no_network and wired
          and exact and not stale,
          "private block minus the new key keeps the eight=%s (broken=%r "
          "rows=%r); live minus new key keeps the eight=%s; ASCII=%s; no "
          "network=%s; wired=%s; old arms pin nine keys=%d; stale eight-key "
          "pin left=%s"
          % (unchanged, block["broken"], block["rows"], live_old, ascii_ok,
             no_network, wired, old_suite.count(pinned), stale))


def main():
    mixed = mixed_world()
    declared_root = declared_world()
    shared_definition_arm(mixed)
    field_arms(mixed, declared_root)
    unreadable_arm(mixed)
    live_arm()
    additive_arm(mixed)
    verdict = "PASS" if not FAILS else "FAIL:" + ",".join(FAILS)
    print("SUITE %s %d/%d" % (verdict, CHECKS[0] - len(FAILS), CHECKS[0]),
          flush=True)
    print("SUITE criteria=%d failed=%s"
          % (len(CRITERIA), ",".join(FAILS) or "(none)"), flush=True)
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
