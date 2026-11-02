"""queue_export_gate_wire suite (R2376).

Criteria AC-QEG1..AC-QEG6 were pinned inside the R2375 tech seed row of
state/queue/tech.md:422 BEFORE this code existed.

What this proves: R2375 shipped a gate that can NAME a stale queue block, but
nothing ran it on the write path - queue_floor_export_face.write replaced the
export with whatever section it had just composed, unproven. This suite proves
the wire composes, stages BESIDE the export, asks the gate, and only then
replaces the original; a refusal leaves the original byte-identical.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import copy
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

import queue_export_freshness_gate as GATE  # noqa: E402
import queue_export_gate_wire as QEG  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_export_gate_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-export-gate-wire"
WIRED_EXPECT = '"test_queue_export_gate_wire.py"), 6),'

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


def section(claimable):
    """A live queue section shape: one row per queue."""
    rows = []
    for name, floor in (("main", 5), ("tech", 10), ("explore", 10)):
        rows.append({
            "queue": name,
            "path": "state/queue/%s.md" % name,
            "present": True,
            "open_rows": claimable,
            "done_rows": 1,
            "gated_rows": 0,
            "claimable": claimable,
            "discounted": 0,
            "delivered": [],
            "floor": floor,
            "shortfall": 0,
            "status": "MET",
        })
    return {
        "floors": {"main": 5, "tech": 10, "explore": 10},
        "queues": rows,
        "verdict": "FLOOR-MET",
        "shortfall_total": 0,
        "missing": [],
        "delivered_total": 0,
    }


class patched_face(object):
    """Temporarily replace queue_floor_export_face.face with a fixture."""

    def __init__(self, value):
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = QFE.face
        QFE.face = lambda root: self.value
        return self

    def __exit__(self, *exc):
        QFE.face = self.saved
        return False


class patched_gate(object):
    """Temporarily replace queue_export_freshness_gate.check with a fixture."""

    def __init__(self, verdict, code):
        self.verdict = verdict
        self.code = code
        self.saved = None
        self.calls = []

    def __call__(self, root, path):
        self.calls.append((root, path))
        return self.verdict, self.code

    def __enter__(self):
        self.saved = GATE.check
        GATE.check = self
        return self

    def __exit__(self, *exc):
        GATE.check = self.saved
        return False


def write_export(directory, data, name="status-export.json"):
    target = os.path.join(directory, name)
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return target


def ac_qeg1():
    """AC-QEG1: the write path calls GATE.check; patching it moves the verdict."""
    directory = tempfile.mkdtemp(prefix="qeg1-")
    try:
        target = write_export(directory, {"self_drive": {"tick": 1}})
        stale = {"label": GATE.LABEL, "verdict": "STALE",
                 "path": target, "drifted": ["queue:tech"],
                 "claimable": [5, 9, 10], "delivered_total": 0}
        fresh = {"label": GATE.LABEL, "verdict": "CURRENT",
                 "path": target, "drifted": [],
                 "claimable": [5, 10, 10], "delivered_total": 0}
        with patched_face(section(10)):
            with patched_gate(stale, 2) as gate:
                refused, code_refused = QEG.publish(".", target)
            calls = len(gate.calls)
            with patched_gate(fresh, 0):
                written, code_written = QEG.publish(".", target)
        ok = (refused["verdict"] == "REFUSED" and code_refused == 2
              and written["verdict"] == "WRITTEN" and code_written == 0
              and calls == 1)
        if not ok:
            print("  measured: %r %r %r %r calls=%d"
                  % (refused["verdict"], code_refused, written["verdict"],
                     code_written, calls), flush=True)
        check(ok, "AC-QEG1 the write path calls "
                  "queue_export_freshness_gate.check (patching it moves the "
                  "verdict)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qeg2():
    """AC-QEG2: a refusal happens BEFORE any byte of the export is replaced."""
    directory = tempfile.mkdtemp(prefix="qeg2-")
    try:
        target = write_export(directory, {"self_drive": {"tick": 7},
                                          "queue": section(10)})
        before = io.open(target, "rb").read()
        stale = {"label": GATE.LABEL, "verdict": "STALE", "path": target,
                 "drifted": ["queue:tech"], "claimable": [5, 9, 10],
                 "delivered_total": 0}
        with patched_face(section(9)):
            with patched_gate(stale, 2):
                result, code = QEG.publish(".", target)
        after = io.open(target, "rb").read()
        leftovers = sorted(name for name in os.listdir(directory)
                           if name != "status-export.json")
        ok = (code == 2 and result["verdict"] == "REFUSED"
              and before == after and not leftovers
              and result["drifted"] == ["queue:tech"])
        if not ok:
            print("  measured: code=%r same=%r leftovers=%r drifted=%r"
                  % (code, before == after, leftovers, result["drifted"]),
                  flush=True)
        check(ok, "AC-QEG2 a stale block is refused before any byte is "
                  "replaced (the old file survives intact)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qeg3():
    """AC-QEG3: a proven block is written and reads back identically."""
    directory = tempfile.mkdtemp(prefix="qeg3-")
    try:
        target = write_export(directory, {"self_drive": {"tick": 11}})
        with patched_face(section(10)):
            expected = QFE.compose(".", target)
            result, code = QEG.publish(".", target)
        on_disk = io.open(target, "r", encoding="utf-8", newline="").read()
        leftovers = sorted(name for name in os.listdir(directory)
                           if name != "status-export.json")
        ok = (code == 0 and result["verdict"] == "WRITTEN"
              and on_disk == expected
              and result["bytes"] == len(expected.encode("utf-8"))
              and not leftovers)
        if not ok:
            print("  measured: code=%r identical=%r leftovers=%r"
                  % (code, on_disk == expected, leftovers), flush=True)
        check(ok, "AC-QEG3 a fresh export is written and reads back identical")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qeg4():
    """AC-QEG4: a refusal writes nothing and the module reads no clock."""
    source = read(MODULE)
    clock_ok = not any(token in source for token in
                       ("import time", "time.time", "datetime", "random"))
    directory = tempfile.mkdtemp(prefix="qeg4-")
    try:
        target = write_export(directory, {"self_drive": {"tick": 3}})
        before = io.open(target, "rb").read()
        listing_before = sorted(os.listdir(directory))
        stale = {"label": GATE.LABEL, "verdict": "STALE", "path": target,
                 "drifted": ["section:verdict"], "claimable": [5, 10, 10],
                 "delivered_total": 0}
        with patched_face(section(10)):
            with patched_gate(stale, 2):
                QEG.publish(".", target)
        after = io.open(target, "rb").read()
        listing_after = sorted(os.listdir(directory))
        ok = (clock_ok and before == after
              and listing_before == listing_after)
        if not ok:
            print("  measured: clock=%r bytes_same=%r listing=%r"
                  % (clock_ok, before == after,
                     listing_before == listing_after), flush=True)
        check(ok, "AC-QEG4 a refusal writes nothing (no residue) and the "
                  "module reads no clock")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qeg5():
    """AC-QEG5: exit 0 = written, 2 = refused, 3 = missing file, 5 = bad flags."""
    directory = tempfile.mkdtemp(prefix="qeg5-")
    try:
        live = QFE.face(REPO)
        target = write_export(directory, copy.deepcopy({"queue": live}))
        absent = os.path.join(directory, "absent.json")

        def run(extra):
            proc = subprocess.run(
                [sys.executable, MODULE] + extra,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO)
            return proc.returncode

        code_written = run(["--execute", "--root", REPO,
                            "--export", target])
        code_missing = run(["--execute", "--root", REPO,
                            "--export", absent])
        code_bad = run(["--bogus"])

        stale = {"label": GATE.LABEL, "verdict": "STALE", "path": target,
                 "drifted": ["queue:tech"], "claimable": [5, 9, 10],
                 "delivered_total": 0}
        with patched_face(section(9)):
            with patched_gate(stale, 2):
                code_refused = QEG.main(["--execute", "--root", ".",
                                         "--export", target])

        ok = (code_written == 0 and code_refused == 2
              and code_missing == 3 and code_bad == 5)
        if not ok:
            print("  measured: written=%r refused=%r missing=%r bad=%r"
                  % (code_written, code_refused, code_missing, code_bad),
                  flush=True)
        check(ok, "AC-QEG5 exit 0 = written, 2 = refused, 3 = missing file, "
                  "5 = bad flags")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qeg6():
    """AC-QEG6: pure ASCII, stdlib only, no network, own label at 6 criteria."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = not any(byte > 127 for byte in raw)
    source = raw.decode("utf-8")
    net_ok = not any(token in source for token in
                     ("socket", "urllib", "http.client", "requests"))
    runner_src = read(RUNNER)
    wired = (('"%s"' % LABEL) in runner_src and WIRED_EXPECT in runner_src)
    proc = subprocess.run([sys.executable, MODULE, "--help"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    help_out = proc.stdout.decode("utf-8", "replace")
    help_ok = "VERDICT " not in help_out and proc.returncode == 0
    ok = ascii_ok and net_ok and wired and help_ok
    if not ok:
        print("  measured: ascii=%r net=%r wired=%r help=%r"
              % (ascii_ok, net_ok, wired, help_ok), flush=True)
    check(ok, "AC-QEG6 pure ASCII, stdlib only, no network, one runner entry "
              "at 6 criteria")


def main():
    print("SUITE queue_export_gate_wire (R2376) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for fn in (ac_qeg1, ac_qeg2, ac_qeg3, ac_qeg4, ac_qeg5, ac_qeg6):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())