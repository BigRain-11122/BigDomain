"""test_status_export_writer_dialect_wire - the six criteria for the export
writer dialect wire.

Criteria AC-SEWD1..AC-SEWD6 were pinned inside the R2448 tech seed row of
state/queue/tech.md:516 BEFORE this code existed.

What this proves: three writers land docs/status-export.json and none of them
asked the shared payload derivation, so the CEO-visible document was rewritten
in whichever transport the running writer felt like. The wire derives that
writer set from the shipped audit at CALL time (no list of names), then proves
both transports with REAL writer calls: an LF copy must come back byte for
byte as today's composition, and a CRLF copy must come back CRLF with zero lone
LF. The three writers keep their own refusal contracts, which their own suites
still assert.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import status_export_writer_dialect_wire as SEWD  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "status_export_writer_dialect_wire.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-status-export-writer-dialect-wire"
WIRED_EXPECT = '"test_status_export_writer_dialect_wire.py"), 6),'
WRITERS = ("closeout_export_parity_wire", "queue_export_gate_wire",
           "queue_floor_export_face")

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def read(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def ac_sewd1():
    """AC-SEWD1 the writer set is derived from the audit reading at CALL time."""
    real = GWDA.report
    try:
        GWDA.report = lambda root: {
            "rows": [
                {"name": "a.py", "kind": "KEEPS",
                 "target": "docs/status-export.json", "asks": True},
                {"name": "b.py", "kind": "KEEPS",
                 "target": "docs/other.json", "asks": False},
                {"name": "c.py", "kind": "KEEPS",
                 "target": "docs\\status-export.json", "asks": True},
            ],
            "routed": 2,
            "verdict": "AUDIT-CLEAN",
        }
        reading = SEWD.check(REPO, None)
    finally:
        GWDA.report = real
    names = sorted(row["name"] for row in reading["rows"])
    moved = names == ["a.py", "c.py"] and reading["derived"] == 2
    # a hardcoded set would show up as ONE literal sequence carrying two or
    # more of the writer names; prose may name them, code may not
    import ast
    worst = 0
    tree = ast.parse(read(MODULE))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            hits = [el.value for el in ast.walk(node)
                    if isinstance(el, ast.Constant)
                    and isinstance(el.value, str)
                    and el.value in WRITERS]
            worst = max(worst, len(set(hits)))
    no_list = worst <= 1
    ok = moved and no_list and reading["verdict"] == SEWD.WIRED
    if not ok:
        print("  measured: names=%r moved=%r worst_literal=%d verdict=%r"
              % (names, moved, worst, reading["verdict"]), flush=True)
    check(ok, "AC-SEWD1 the writer set is derived from the audit reading at "
              "CALL time, never a fixed list of three names")


def ac_sewd2():
    """AC-SEWD2 a CRLF export keeps CRLF through a real writer call."""
    folder = tempfile.mkdtemp(prefix="sewd2-")
    calls = []
    real = QFE.write
    try:
        def counting(root, path):
            calls.append(path)
            return real(root, path)
        QFE.write = counting
        row = SEWD.transport(folder, EXPORT)
    finally:
        QFE.write = real
        shutil.rmtree(folder, ignore_errors=True)
    ok = (row["crlf_kept"] and row["crlf_lone_lf"] == 0 and len(calls) == 2)
    if not ok:
        print("  measured: kept=%r lone=%r calls=%d"
              % (row["crlf_kept"], row["crlf_lone_lf"], len(calls)), flush=True)
    check(ok, "AC-SEWD2 a CRLF docs/status-export.json keeps CRLF through a "
              "real writer call with zero lone LF")


def ac_sewd3():
    """AC-SEWD3 an LF export keeps exactly today's bytes."""
    folder = tempfile.mkdtemp(prefix="sewd3-")
    try:
        row = SEWD.transport(folder, EXPORT)
        target = os.path.join(folder, "lf.json")
        with io.open(target, "rb") as handle:
            lf = handle.read()
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    ok = (row["lf_today_exact"] and lf.count(b"\r\n") == 0
          and row["lf_bytes"] == len(lf))
    if not ok:
        print("  measured: exact=%r crlf=%d bytes=%d"
              % (row["lf_today_exact"], lf.count(b"\r\n"), row["lf_bytes"]),
              flush=True)
    check(ok, "AC-SEWD3 an LF export keeps exactly today's bytes")


def ac_sewd4():
    """AC-SEWD4 every one of the three writers keeps its refusal contract."""
    expected = {"test_queue_floor_export_face.py": "SUITE PASS 6/6",
                "test_queue_export_gate_wire.py": "SUITE PASS 6/6",
                "test_closeout_export_parity_wire.py": "SUITE PASS 16/16"}
    seen = {}
    for suite, want in expected.items():
        proc = subprocess.run([sys.executable, os.path.join(BASE, suite)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              cwd=REPO)
        out = proc.stdout.decode("utf-8", "replace")
        seen[suite] = (proc.returncode, want in out)
    ok = all(code == 0 and hit for code, hit in seen.values())
    if not ok:
        print("  measured: %r" % (sorted(seen.items()),), flush=True)
    check(ok, "AC-SEWD4 every one of the three writers keeps its existing "
              "refusal code, exit code and printed line")


def ac_sewd5():
    """AC-SEWD5 the audit reads AUDIT-CLEAN with routed == keeps."""
    reading = GWDA.report(REPO)
    keeps = [row for row in reading["rows"] if row["kind"] == "KEEPS"]
    routed = [row for row in reading["rows"]
              if row["kind"] == "KEEPS" and row["asks"]]
    live = SEWD.check(REPO, None)
    export_keeps = [row for row in keeps
                    if SEWD.spell(row["target"]) == SEWD.TARGET]
    ok = (reading["verdict"] == "AUDIT-CLEAN"
          and len(routed) == len(keeps) == reading["routed"]
          and reading["unrouted"] == 0
          and live["verdict"] == SEWD.WIRED
          and live["derived"] == len(export_keeps) > 0)
    if not ok:
        print("  measured: verdict=%r keeps=%d routed=%d unrouted=%d export=%d "
              "live=%r/%d"
              % (reading["verdict"], len(keeps), len(routed),
                 reading["unrouted"], len(export_keeps), live["verdict"],
                 live["derived"]), flush=True)
    check(ok, "AC-SEWD5 the audit reads AUDIT-CLEAN with routed == keeps "
              "after the wire")


def ac_sewd6():
    """AC-SEWD6 pure ASCII, stdlib only, no clock, zero network, wired."""
    source = read(MODULE)
    ascii_ok = all(ord(ch) < 128 for ch in source)
    net_ok = not any(token in source for token in
                     ("urllib", "requests", "socket", "http.client"))
    clock_ok = "import time" not in source and "time.time" not in source
    runner = read(RUNNER)
    wired = WIRED_EXPECT in runner and LABEL in runner
    proc = subprocess.run([sys.executable, MODULE, "--help"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          cwd=REPO)
    help_out = proc.stdout.decode("utf-8", "replace")
    no_run = "VERDICT " not in help_out and proc.returncode == 0
    ok = ascii_ok and net_ok and clock_ok and wired and no_run
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r help=%r"
              % (ascii_ok, net_ok, clock_ok, wired, no_run), flush=True)
    check(ok, "AC-SEWD6 pure ASCII, stdlib only, no clock, zero network, own "
              "reconcile label and suite")


def main():
    print("SUITE status_export_writer_dialect_wire (R2450) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-SEWD1", ac_sewd1), ("AC-SEWD2", ac_sewd2),
                     ("AC-SEWD3", ac_sewd3), ("AC-SEWD4", ac_sewd4),
                     ("AC-SEWD5", ac_sewd5), ("AC-SEWD6", ac_sewd6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())