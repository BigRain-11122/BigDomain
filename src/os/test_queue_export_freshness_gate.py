"""queue_export_freshness_gate suite (R2375).

Criteria AC-QEF1..AC-QEF6 were pinned inside the R2374 tech seed row of
state/queue/tech.md:421 BEFORE this code existed.

What this proves: R2374 gave the export a queue section derived at write time,
but nothing watched it - check_export_consistency opens only the twelve
self_drive fields, so the block could age silently after a queue edit. One gate
now recomputes the live reading through queue_floor_export_face.face and names
every drifted queue, refusing to call a stale block CURRENT.

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

import queue_export_freshness_gate as QEF  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_export_freshness_gate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-export-freshness-gate"
WIRED_EXPECT = '"test_queue_export_freshness_gate.py"), 6),'

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


def section(claimable, delivered=None):
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
            "delivered": list(delivered or []),
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
        "delivered_total": len(delivered or []),
    }


class patched(object):
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


def write_export(directory, data, name="status-export.json"):
    target = os.path.join(directory, name)
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return target


def ac_qef1():
    """AC-QEF1: the live side IS queue_floor_export_face.face."""
    directory = tempfile.mkdtemp(prefix="qef1-")
    try:
        on_disk = section(10)
        target = write_export(directory, {"self_drive": {}, "queue": on_disk})
        with patched(copy.deepcopy(on_disk)):
            same, same_code = QEF.check(".", target)
        with patched(section(9)):
            moved, moved_code = QEF.check(".", target)
        ok = (same["verdict"] == "CURRENT" and same_code == 0
              and moved["verdict"] == "STALE" and moved_code == 2
              and "queue:main" in moved["drifted"])
        check(ok, "AC-QEF1 the live side IS queue_floor_export_face.face "
                  "(patching that face moves the verdict)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qef2():
    """AC-QEF2: a drifted claimable OR a drifted delivered row names the queue."""
    directory = tempfile.mkdtemp(prefix="qef2-")
    try:
        on_disk = section(10)
        target = write_export(directory, {"queue": on_disk})

        drifted_claimable = section(10)
        drifted_claimable["queues"][1]["claimable"] = 4
        names_claimable = QEF.drift(drifted_claimable, on_disk)

        delivered = [{"line": 421, "prefix": "AC-QEF1"}]
        drifted_delivered = section(10)
        drifted_delivered["queues"][2]["delivered"] = delivered
        names_delivered = QEF.drift(drifted_delivered, on_disk)

        shifted = section(10)
        shifted["queues"][0]["delivered"] = delivered
        moved_row = section(10)
        moved_row["queues"][0]["delivered"] = [{"line": 422,
                                                "prefix": "AC-QEF1"}]
        names_row = QEF.drift(shifted, moved_row)

        ok = (names_claimable == ["queue:tech"]
              and names_delivered == ["queue:explore"]
              and names_row == ["queue:main"])
        if not ok:
            print("  measured: %r %r %r"
                  % (names_claimable, names_delivered, names_row), flush=True)
        check(ok, "AC-QEF2 a drifted claimable or a drifted delivered row "
                  "names that queue and refuses")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qef3():
    """AC-QEF3: an export with no queue section reads MISSING, never CURRENT."""
    directory = tempfile.mkdtemp(prefix="qef3-")
    try:
        target = write_export(directory, {"self_drive": {"tick": 1}})
        with patched(section(10)):
            result, code = QEF.check(".", target)
        text = json.dumps(result)
        ok = (result["verdict"] == "MISSING" and code == 2
              and "CURRENT" not in text)
        check(ok, "AC-QEF3 a section-less export reads MISSING and never "
                  "CURRENT")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qef4():
    """AC-QEF4: the gate writes nothing and reads no clock."""
    source = read(MODULE)
    clock_ok = not any(token in source for token in
                       ("import time", "time.time", "datetime", "random"))
    write_ok = not any(token in source for token in
                       ("'w'", '"w"', "'a'", '"a"', "os.replace", "os.remove"))
    directory = tempfile.mkdtemp(prefix="qef4-")
    try:
        on_disk = section(10)
        target = write_export(directory, {"queue": on_disk})
        before = io.open(target, "rb").read()
        with patched(section(10)):
            QEF.check(".", target)
        after = io.open(target, "rb").read()
        # No temp file may be left behind either.
        leftovers = [name for name in os.listdir(directory)
                     if name != "status-export.json"]
        ok = clock_ok and write_ok and before == after and not leftovers
        if not ok:
            print("  measured: clock=%r write=%r bytes_same=%r leftovers=%r"
                  % (clock_ok, write_ok, before == after, leftovers),
                  flush=True)
        check(ok, "AC-QEF4 writes nothing and reads no clock")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qef5():
    """AC-QEF5: exit 0 = CURRENT, 2 = STALE, 3 = missing file, 5 = bad flags."""
    directory = tempfile.mkdtemp(prefix="qef5-")
    try:
        live = QFE.face(REPO)
        current_target = write_export(directory, {"queue": live})
        stale = copy.deepcopy(live)
        stale["queues"][0]["claimable"] = 999
        stale_target = write_export(
            directory, {"queue": stale}, name="stale.json")
        missing_section = write_export(
            directory, {"self_drive": {}}, name="nosection.json")
        absent = os.path.join(directory, "absent.json")

        def run(extra):
            proc = subprocess.run(
                [sys.executable, MODULE, "--check", "--root", REPO] + extra,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO)
            return proc.returncode

        code_current = run(["--export", current_target])
        code_stale = run(["--export", stale_target])
        code_missing_section = run(["--export", missing_section])
        code_absent = run(["--export", absent])
        code_bad = run(["--bogus"])
        ok = (code_current == 0 and code_stale == 2
              and code_missing_section == 2 and code_absent == 3
              and code_bad == 5)
        if not ok:
            print("  measured: %r %r %r %r %r"
                  % (code_current, code_stale, code_missing_section,
                     code_absent, code_bad), flush=True)
        check(ok, "AC-QEF5 exit 0 = CURRENT, 2 = STALE or MISSING, "
                  "3 = missing file, 5 = bad flags")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qef6():
    """AC-QEF6: pure ASCII, stdlib only, no network, own label at 6 criteria."""
    ascii_ok = True
    net_ok = True
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    if any(byte > 127 for byte in raw):
        ascii_ok = False
    source = raw.decode("utf-8")
    if any(token in source for token in
           ("socket", "urllib", "http.client", "requests")):
        net_ok = False
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
    check(ok, "AC-QEF6 pure ASCII, stdlib only, no network, one runner entry "
              "at 6 criteria")
    return ok


def main():
    print("SUITE queue_export_freshness_gate (R2375) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-QEF1", ac_qef1), ("AC-QEF2", ac_qef2),
                     ("AC-QEF3", ac_qef3), ("AC-QEF4", ac_qef4),
                     ("AC-QEF5", ac_qef5), ("AC-QEF6", ac_qef6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())