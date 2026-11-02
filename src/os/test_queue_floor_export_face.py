"""queue_floor_export_face suite (R2374).

Criteria AC-QFE1..AC-QFE6 were pinned inside the R2368 tech seed row of
state/queue/tech.md:420 BEFORE this code existed.

What this proves: R2368 shipped ONE discounted floor reading, but the
CEO-visible export published no queue line at all, so the corrected number had
no consumer on the face the reader opens. One module now writes that section,
and it writes queue_floor_reading_wire.published itself - not a copy and not a
re-derivation - so the discounted claimable and every discounted row travel
unchanged. Patching the reading moves the exported section, which is the only
proof that no canned number sits in the module.

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

import check_export_consistency as CEC  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import queue_floor_reading_wire as QFRW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_floor_export_face.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-floor-export-face"
WIRED_EXPECT = '"test_queue_floor_export_face.py"), 6),'

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


def published(claimable, discounted=0, delivered=None):
    """A published report shape with one row per queue."""

    rows = []
    for name, floor in (("main", 5), ("tech", 10), ("explore", 10)):
        rows.append({
            "queue": name,
            "path": "state/queue/%s.md" % name,
            "present": True,
            "open_rows": claimable + discounted,
            "done_rows": 1,
            "gated_rows": 0,
            "claimable": claimable,
            "discounted": discounted,
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
        "delivered_total": discounted * 3,
    }


class patched(object):
    """Temporarily replace QFRW.published with a fixture."""

    def __init__(self, value):
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = QFRW.published
        QFRW.published = lambda root: self.value
        return self

    def __exit__(self, *exc):
        QFRW.published = self.saved
        return False


def copy_export(directory):
    target = os.path.join(directory, "status-export.json")
    shutil.copyfile(EXPORT, target)
    return target


def ac_qfe1():
    """AC-QFE1: the section comes from queue_floor_reading_wire.published."""
    fixture = published(42)
    directory = tempfile.mkdtemp(prefix="qfe1-")
    try:
        target = copy_export(directory)
        with patched(fixture):
            text = QFE.compose(".", target)
            direct = QFE.face(".")
        data = json.loads(text)
        ok = (direct == fixture
              and data[QFE.FACE_KEY] == fixture
              and data[QFE.FACE_KEY]["queues"][0]["claimable"] == 42)
        check(ok, "AC-QFE1 the section IS queue_floor_reading_wire.published "
                  "(patching its reading moves the export)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qfe2():
    """AC-QFE2: discounted claimable plus every discounted row, never gross."""
    delivered = [{"line": 413, "prefix": "AC-QFR1"}]
    fixture = published(9, discounted=1, delivered=delivered)
    directory = tempfile.mkdtemp(prefix="qfe2-")
    try:
        target = copy_export(directory)
        with patched(fixture):
            data = json.loads(QFE.compose(".", target))
        row = data[QFE.FACE_KEY]["queues"][0]
        gross = row["claimable"] + row["discounted"]
        ok = (row["claimable"] == 9
              and row["discounted"] == 1
              and row["delivered"] == delivered
              and data[QFE.FACE_KEY]["delivered_total"] == 3
              and "gross" not in row
              and gross == 10)
        check(ok, "AC-QFE2 publishes the discounted claimable plus every "
                  "discounted row (line+prefix), never the gross alone")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qfe3():
    """AC-QFE3: the consistency checker still reads 21/21 with the field."""
    directory = tempfile.mkdtemp(prefix="qfe3-")
    saved = CEC.P_EXPORT
    try:
        target = copy_export(directory)
        QFE.write(".", target)
        CEC.P_EXPORT = target
        report, n_pass, n_fail = CEC.check()
        source = read(MODULE)
        no_second_reading = ("open_rows\"] = " not in source
                             and "re.compile" not in source)
        ok = (n_pass == 21 and n_fail == 0 and no_second_reading)
        if not ok:
            print("  measured: pass=%d fail=%d second=%r"
                  % (n_pass, n_fail, not no_second_reading), flush=True)
        check(ok, "AC-QFE3 check_export_consistency reads 21/21 with the new "
                  "field, and the field is not a second derivation")
    finally:
        CEC.P_EXPORT = saved
        shutil.rmtree(directory, ignore_errors=True)


def ac_qfe4():
    """AC-QFE4: one stable key order, one trailing LF, byte-stable."""
    fixture = published(10)
    directory = tempfile.mkdtemp(prefix="qfe4-")
    try:
        target = copy_export(directory)
        before = list(json.loads(read(target)).keys())
        with patched(fixture):
            first = QFE.compose(".", target)
            second = QFE.compose(".", target)
        after = list(json.loads(first).keys())
        # One stable order: the section is the LAST key, whether the document
        # already carried it (append once) or not (append here). The order is
        # what is proved, not the presence of a duplicate.
        expected = before if QFE.FACE_KEY in before else before + [QFE.FACE_KEY]
        ok = (first == second
              and first.endswith("\n")
              and not first.endswith("\n\n")
              and after == expected
              and after[-1] == QFE.FACE_KEY
              and first.count("\n\n") == 0)
        check(ok, "AC-QFE4 one stable key order plus one trailing LF, "
                  "byte-stable across two runs")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qfe5():
    """AC-QFE5: derived at write time, so a changed queue moves the export."""
    directory = tempfile.mkdtemp(prefix="qfe5-")
    try:
        target = copy_export(directory)
        with patched(published(10)):
            first = QFE.compose(".", target)
        with patched(published(7)):
            second = QFE.compose(".", target)
        first_row = json.loads(first)[QFE.FACE_KEY]["queues"][0]
        second_row = json.loads(second)[QFE.FACE_KEY]["queues"][0]
        ok = (first != second
              and first_row["claimable"] == 10
              and second_row["claimable"] == 7)
        check(ok, "AC-QFE5 the value is derived at write time (a changed "
                  "queue moves it, no canned copy)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_qfe6():
    """AC-QFE6: pure ASCII, stdlib only, no clock, no network, own label."""
    ascii_ok = True
    net_ok = True
    clock_ok = True
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    if any(byte > 127 for byte in raw):
        ascii_ok = False
    source = raw.decode("utf-8")
    if any(token in source for token in
           ("socket", "urllib", "http.client", "requests")):
        net_ok = False
    if any(token in source for token in
           ("import time", "time.time", "datetime", "random")):
        clock_ok = False
    runner_src = read(RUNNER)
    wired = (('"%s"' % LABEL) in runner_src and WIRED_EXPECT in runner_src)
    proc = subprocess.run([sys.executable, MODULE, "--help"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    help_out = proc.stdout.decode("utf-8", "replace")
    no_section_run = "VERDICT " not in help_out and proc.returncode == 0
    ok = ascii_ok and net_ok and clock_ok and wired and no_section_run
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r help=%r"
              % (ascii_ok, net_ok, clock_ok, wired, no_section_run), flush=True)
    check(ok, "AC-QFE6 pure ASCII, stdlib only, no clock, no network, one "
              "runner entry at 6 criteria")


def main():
    print("SUITE queue_floor_export_face (R2374) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-QFE1", ac_qfe1), ("AC-QFE2", ac_qfe2),
                     ("AC-QFE3", ac_qfe3), ("AC-QFE4", ac_qfe4),
                     ("AC-QFE5", ac_qfe5), ("AC-QFE6", ac_qfe6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())