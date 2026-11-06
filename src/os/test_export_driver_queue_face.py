"""export_driver_queue_face suite (R2497).

Criteria AC-EDQF1..AC-EDQF6 were pinned inside state/queue/tech.md:531 (the
R2453 tech seed row) BEFORE this code existed.

What this proves: the round export driver re-derived the CEO-visible queue
block itself out of `queue_floor --check --json` while the published section
the house reads is queue_floor_export_face.face - the DISCOUNTED reading with
delivered_total. Two derivations of one document meant a freshly re-derived
export could carry a stale queue block, and R2452 and R2453 both paid for it by
landing the block by hand. One module now owns the driver's queue section and
its write: the section is the shipped face's own reading asked at call time, the
document is refreshed in place, and the bytes are staged and proved with the
shipped freshness gate before any replace.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
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

import export_R2431 as base  # noqa: E402
import export_driver_queue_face as EDQF  # noqa: E402
import queue_export_freshness_gate as GATE  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_driver_queue_face.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-driver-queue-face"
WIRED_EXPECT = '"test_export_driver_queue_face.py"), 6),'

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


def fixture(claimable, discounted=0, delivered_total=None):
    """A published-section shape with one row per queue."""

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
        "delivered_total": (discounted * 3 if delivered_total is None
                            else delivered_total),
    }


class patched(object):
    """Temporarily replace QFE.face with a fixed reading."""

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


class moved(object):
    """Two readings: the first the caller sees, the second the proof sees."""

    def __init__(self, first, second):
        self.values = [first, second]
        self.saved = None

    def __enter__(self):
        self.saved = QFE.face

        def cell(root):
            if len(self.values) > 1:
                return self.values.pop(0)
            return self.values[0]

        QFE.face = cell
        return self

    def __exit__(self, *exc):
        QFE.face = self.saved
        return False


def copy_export(directory):
    target = os.path.join(directory, "status-export.json")
    shutil.copyfile(EXPORT, target)
    return target


def ac_edqf1():
    """AC-EDQF1: the section IS queue_floor_export_face.face at call time."""
    shot = fixture(42)
    directory = tempfile.mkdtemp(prefix="edqf1-")
    try:
        target = copy_export(directory)
        data = json.loads(read(target))
        with patched(shot):
            direct = EDQF.section(REPO)
            EDQF.refresh(data, REPO)
        ok = (direct == shot
              and data[EDQF.FACE_KEY] == shot
              and data[EDQF.FACE_KEY]["queues"][0]["claimable"] == 42)
        if not ok:
            print("  measured: direct=%r section_claimable=%r"
                  % (direct == shot,
                     data[EDQF.FACE_KEY]["queues"][0]["claimable"]), flush=True)
        check(ok, "AC-EDQF1 the section IS queue_floor_export_face.face asked "
                  "at call time (patching that reading moves the driver "
                  "section, no gross re-derivation survives)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edqf2():
    """AC-EDQF2: a driver run on the real tree leaves the block CURRENT."""
    directory = tempfile.mkdtemp(prefix="edqf2-")
    saved = base.EXPORT
    try:
        target = copy_export(directory)
        base.EXPORT = target
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = base.main()
        printed = buffer.getvalue()
        on_disk = json.loads(read(target))[EDQF.FACE_KEY]
        live = EDQF.section(REPO)
        verdict, gate_code = GATE.check(REPO, target)
        face_code = QFE.main(["--check", "--root", REPO, "--export", target])
        ok = (code == 0
              and on_disk == live
              and gate_code == 0
              and verdict.get("drifted") == []
              and face_code == 0
              and "queue=CURRENT" in printed)
        if not ok:
            print("  measured: code=%r equal=%r gate=%r drifted=%r face=%r "
                  "printed=%r" % (code, on_disk == live, gate_code,
                                  verdict.get("drifted"), face_code,
                                  printed.strip()[:160]), flush=True)
        check(ok, "AC-EDQF2 a driver run leaves the queue block CURRENT, the "
                  "gate reports no drift and the queue face itself re-reads "
                  "CURRENT")
    finally:
        base.EXPORT = saved
        shutil.rmtree(directory, ignore_errors=True)


def ac_edqf3():
    """AC-EDQF3: a queue that moved before the write refuses, document intact."""
    directory = tempfile.mkdtemp(prefix="edqf3-")
    try:
        target = copy_export(directory)
        before = open(target, "rb").read()
        data = json.loads(read(target))
        first = fixture(7)
        second = fixture(4, discounted=1)
        code = None
        detail = ""
        with moved(first, second):
            EDQF.refresh(data, REPO)
            text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            try:
                EDQF.publish(REPO, target, text)
            except EDQF.ExportDriverQueueFaceError as exc:
                code = exc.code
                detail = exc.detail
        after = open(target, "rb").read()
        residue = os.path.exists(target + EDQF.STAGE_SUFFIX)
        ok = (before == after and not residue
              and code == "STALE"
              and isinstance(detail, str))
        if not ok:
            print("  measured: unchanged=%r residue=%r code=%r"
                  % (before == after, residue, code), flush=True)
        check(ok, "AC-EDQF3 a queue that moved between the reading and the "
                  "write refuses with the gate own verdict word and leaves the "
                  "document byte-identical with no residue")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edqf4():
    """AC-EDQF4: published keys keep their value and position."""
    shot = fixture(11, discounted=2)
    directory = tempfile.mkdtemp(prefix="edqf4-")
    try:
        target = copy_export(directory)
        data = json.loads(read(target))
        order = list(data.keys())
        others = dict((key, data[key]) for key in order
                      if key != EDQF.FACE_KEY)
        had_section = EDQF.FACE_KEY in order
        with patched(shot):
            EDQF.refresh(data, REPO)
        after = list(data.keys())
        same_others = all(data[key] == others[key] for key in others)
        expected = order if had_section else order + [EDQF.FACE_KEY]
        ok = (after == expected
              and same_others
              and data[EDQF.FACE_KEY] == shot)
        if not ok:
            print("  measured: order=%r others=%r equal=%r"
                  % (after == expected, same_others,
                     data[EDQF.FACE_KEY] == shot), flush=True)
        check(ok, "AC-EDQF4 every already-published key keeps its value and "
                  "its position, and the queue section is refreshed in place "
                  "rather than reordered")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edqf5():
    """AC-EDQF5: the gate verdict and the byte count reach the driver output."""
    directory = tempfile.mkdtemp(prefix="edqf5-")
    saved = base.EXPORT
    try:
        target = copy_export(directory)
        base.EXPORT = target
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = base.main()
        printed = buffer.getvalue().strip()
        size = os.path.getsize(target)
        ok = (code == 0
              and ("queue=CURRENT" in printed)
              and ("queue_bytes=%d" % size) in printed
              and ("queue_drifted=(none)" in printed))
        if not ok:
            print("  measured: code=%r size=%d printed=%r"
                  % (code, size, printed[-200:]), flush=True)
        check(ok, "AC-EDQF5 the driver prints the gate verdict and the byte "
                  "count, so a refused or drifted run is visible rather than "
                  "silent")
    finally:
        base.EXPORT = saved
        shutil.rmtree(directory, ignore_errors=True)


def ac_edqf6():
    """AC-EDQF6: pure ASCII, stdlib only, no clock, no network, own row."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = not any(byte > 127 for byte in raw)
    source = raw.decode("utf-8")
    net_ok = not any(token in source for token in
                     ("socket", "urllib", "http.client", "requests"))
    clock_ok = not any(token in source for token in
                       ("import time", "time.time", "datetime", "random"))
    runner_src = read(RUNNER)
    wired = (('"%s"' % LABEL) in runner_src and WIRED_EXPECT in runner_src)
    proc = subprocess.run([sys.executable, MODULE, "--help"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    help_ok = (proc.returncode == 0
               and b"usage: export_driver_queue_face.py" in proc.stdout)
    ok = ascii_ok and net_ok and clock_ok and wired and help_ok
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r help=%r"
              % (ascii_ok, net_ok, clock_ok, wired, help_ok), flush=True)
    check(ok, "AC-EDQF6 pure ASCII, stdlib only, no clock, no network, one "
              "runner entry at 6 criteria and a help face of its own")


def main():
    print("SUITE export_driver_queue_face (R2497) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-EDQF1", ac_edqf1), ("AC-EDQF2", ac_edqf2),
                     ("AC-EDQF3", ac_edqf3), ("AC-EDQF4", ac_edqf4),
                     ("AC-EDQF5", ac_edqf5), ("AC-EDQF6", ac_edqf6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())