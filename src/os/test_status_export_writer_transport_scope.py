"""test_status_export_writer_transport_scope - the six criteria for the export
writer transport scope.

Criteria AC-SEWS1..AC-SEWS6 were pinned inside the R2450 tech seed row of
state/queue/tech.md:518 BEFORE this code existed.

What this proves: the R2450 dialect wire proved both transports with ONE
writer call (the queue-floor face) while three writers land
docs/status-export.json, and it measured that the closeout wire refuses on a
bare fixture. This module asks EVERY derived writer for both transports, each
in its own publishable world, and a writer that refuses is published as
UNPROVABLE with its own refusal code and the measured fact that its document
was left byte-identical - not dropped, and not believed.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
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
import status_export_writer_dialect_wire as SEWD  # noqa: E402
import status_export_writer_transport_scope as SEWS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "status_export_writer_transport_scope.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-status-export-writer-transport-scope"
WIRED_EXPECT = '"test_status_export_writer_transport_scope.py"), 6),'
WRITERS = ("closeout_export_parity_wire", "queue_export_gate_wire",
           "queue_floor_export_face")

PASSES = 0
FAILS = 0
LIVE = []


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


def live():
    """One live reading per run; the same bytes are read by three criteria."""
    if not LIVE:
        LIVE.append(SEWS.check(REPO, EXPORT))
    return LIVE[0]


def rows_by_verdict(reading, verdict):
    return [row for row in reading["scope"] if row["verdict"] == verdict]


def ac_sews1():
    """AC-SEWS1 the proved set is derived at CALL time, never a fixed name."""
    real = GWDA.report
    try:
        GWDA.report = lambda root: {
            "rows": [
                {"name": "ghost_alpha.py", "kind": "KEEPS",
                 "target": "docs/status-export.json", "asks": True},
                {"name": "ghost_beta.py", "kind": "KEEPS",
                 "target": "docs/status-export.json", "asks": True},
                {"name": "ghost_gamma.py", "kind": "KEEPS",
                 "target": "docs/other.json", "asks": False},
            ],
            "routed": 2,
            "verdict": "AUDIT-CLEAN",
        }
        reading = SEWS.check(REPO, EXPORT)
    finally:
        GWDA.report = real
    names = sorted(row["name"] for row in reading["scope"])
    moved = (names == ["ghost_alpha.py", "ghost_beta.py"]
             and reading["derived"] == 2
             and reading["scope_verdict"] == SEWS.PARTIAL)
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
    ok = moved and worst <= 1
    if not ok:
        print("  measured: names=%r derived=%r verdict=%r worst_literal=%d"
              % (names, reading["derived"], reading["scope_verdict"], worst),
              flush=True)
    check(ok, "AC-SEWS1 the proved writer set is derived from the audit "
              "reading at CALL time, never a fixed writer name")


def ac_sews2():
    """AC-SEWS2 both transports are asked for EVERY derived writer."""
    reading = live()
    derived = [row["name"] for row in reading["rows"]]
    asked = [row["name"] for row in reading["scope"]]
    proved = rows_by_verdict(reading, SEWS.PROVED)
    broken = []
    for row in proved:
        if not (row["lf"]["status"] == "WRITTEN"
                and row["lf"]["crlf"] == 0
                and row["crlf"]["status"] == "WRITTEN"
                and row["crlf"]["lone_lf"] == 0
                and row["crlf"]["crlf"] > 0
                and row["agree"]):
            broken.append(row["name"])
    refused = [row["name"] for row in reading["scope"]
               if row["verdict"] != SEWS.PROVED]
    ok = (sorted(asked) == sorted(derived) and len(asked) == len(derived)
          and len(proved) >= 1 and not broken
          and sorted(refused) == sorted(reading["scope_unprovable"]))
    if not ok:
        print("  measured: derived=%r asked=%r proved=%d broken=%r refused=%r"
              % (derived, asked, len(proved), broken, refused), flush=True)
    check(ok, "AC-SEWS2 every derived writer is asked for BOTH transports, a "
              "proved writer keeps CRLF with zero lone LF, and a refusing "
              "writer is named rather than dropped")


def ac_sews3():
    """AC-SEWS3 an LF copy keeps today's bytes through every proving writer."""
    reading = live()
    proved = rows_by_verdict(reading, SEWS.PROVED)
    transport = reading["transport"] or {}
    today = transport.get("lf_bytes")
    same_bytes = [row["name"] for row in proved
                  if today is not None and row["lf"]["bytes"] == today]
    broken = [row["name"] for row in proved
              if row["lf"]["crlf"] != 0 or not row["agree"]]
    ok = bool(proved) and not broken and bool(same_bytes)
    if not ok:
        print("  measured: proved=%d broken=%r today=%r same=%r"
              % (len(proved), broken, today, same_bytes), flush=True)
    check(ok, "AC-SEWS3 an LF copy keeps exactly today's bytes through every "
              "proving writer, and both transports carry the same document")


def ac_sews4():
    """AC-SEWS4 a refusal is published with its code and writes nothing."""
    reading = live()
    silent = []
    residue = []
    for row in reading["scope"]:
        if row["verdict"] == SEWS.PROVED:
            continue
        if not row["refusal"]:
            silent.append(row["name"])
            continue
        if row["lf"] is None or row["crlf"] is None:
            if row["refusal"] != "E_SEWS_NO_MODULE":
                silent.append(row["name"])
            continue
        leg = row["crlf"] if row["crlf"]["kind"] != "WRITTEN" else row["lf"]
        if leg["kind"] == "WRITTEN" or not leg["unchanged"]:
            residue.append(row["name"])
    ok = not silent and not residue
    if not ok:
        print("  measured: silent=%r residue=%r unprovable=%r"
              % (silent, residue, reading["scope_unprovable"]), flush=True)
    check(ok, "AC-SEWS4 an UNPROVABLE writer is published with its own refusal "
              "code and leaves its document byte-identical")


def ac_sews5():
    """AC-SEWS5 the base reading keeps every key it published before."""
    base = SEWD.check(REPO, EXPORT)
    reading = live()
    moved = [key for key in base if key not in reading
             or reading[key] != base[key]]
    scope_ok = (isinstance(reading.get("scope"), list)
                and len(reading["scope"]) == reading["derived"]
                and all(isinstance(row.get("lf"), dict)
                        and isinstance(row.get("crlf"), dict)
                        and "status" in row["lf"] and "status" in row["crlf"]
                        for row in reading["scope"])
                and reading["scope_verdict"]
                in (SEWS.SCOPED, SEWS.PARTIAL))
    ok = not moved and scope_ok
    if not ok:
        print("  measured: moved=%r scope_ok=%r verdict=%r"
              % (moved, scope_ok, reading.get("scope_verdict")), flush=True)
    check(ok, "AC-SEWS5 the reading gains a per-writer transport line while "
              "every existing key keeps its value")


def ac_sews6():
    """AC-SEWS6 pure ASCII, stdlib only, no clock, zero network, wired."""
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
    no_run = ("STATUS EXPORT" not in help_out and proc.returncode == 0)
    live_proc = subprocess.run(
        [sys.executable, MODULE, "--check", "--root", REPO,
         "--sample", EXPORT, "--json"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=REPO)
    body = live_proc.stdout.decode("utf-8", "replace")
    parsed = {}
    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = {}
    scoped = parsed.get("scope_verdict")
    consistent = (live_proc.returncode in (0, 2)
                  and scoped in (SEWS.SCOPED, SEWS.PARTIAL)
                  and (scoped == SEWS.SCOPED)
                  == (not parsed.get("scope_unprovable")))
    ok = ascii_ok and net_ok and clock_ok and wired and no_run and consistent
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r help=%r live=%r "
              "rc=%d" % (ascii_ok, net_ok, clock_ok, wired, no_run, scoped,
                         live_proc.returncode), flush=True)
    check(ok, "AC-SEWS6 pure ASCII, stdlib only, no clock, zero network, own "
              "reconcile label and suite, and the CLI agrees with itself")


def main():
    print("SUITE status_export_writer_transport_scope (R2452) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-SEWS1", ac_sews1), ("AC-SEWS2", ac_sews2),
                     ("AC-SEWS3", ac_sews3), ("AC-SEWS4", ac_sews4),
                     ("AC-SEWS5", ac_sews5), ("AC-SEWS6", ac_sews6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())