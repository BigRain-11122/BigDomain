"""export_driver_self_drive_health suite (R2595).

Criteria AC-EDSH1..AC-EDSH6 were pinned in state/queue/tech.md as the R2595
repair row. They were authored AFTER the repair byte was written, which makes
this suite weaker evidence than a pre-registered one; that ordering is
disclosed in the round log rather than dressed up.

What this proves: the round export driver's health term compared
log_lines_in_window against substantive_non_idle_mention_lines and demanded
them EQUAL. The recompute caliber counts a tokens line as a window line and
never as substantive (check_export_consistency.recompute), so any window
holding one tokens line made a healthy refresh read ok=False and exit 2 - which
is exactly how the R2595 battery found it (51 window lines, 50 substantive,
os-export-driver-queue-face AC-EDQF2 + AC-EDQF5 red). The term now compares the
document's whole self_drive block with a FRESH recompute at call time.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402
import export_driver_queue_face as EDQF  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_R2431.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-driver-self-drive-health"
WIRED_EXPECT = '"test_export_driver_self_drive_health.py"), 6),'

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


def copy_export(directory):
    target = os.path.join(directory, "status-export.json")
    shutil.copyfile(EXPORT, target)
    return target


def run_driver(target):
    """Run the driver against a copied document; return (code, printed)."""
    saved = base.EXPORT
    base.EXPORT = target
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = base.main()
    finally:
        base.EXPORT = saved
    return code, buffer.getvalue()


class two_shot_self_drive(object):
    """First call as shipped, second call with one field bumped."""

    def __init__(self, field_name):
        self.field_name = field_name
        self.calls = 0
        self.saved = None

    def __enter__(self):
        self.saved = base.self_drive

        def cell():
            self.calls += 1
            block = self.saved()
            if self.calls > 1:
                block = dict(block)
                block[self.field_name] = block[self.field_name] + 1
            return block

        base.self_drive = cell
        return self

    def __exit__(self, *exc):
        base.self_drive = self.saved
        return False


class doctor_on_write(object):
    """Publish normally, then move one stored self_drive field on disk."""

    def __init__(self, field_name, delta):
        self.field_name = field_name
        self.delta = delta
        self.saved = None
        self.published = 0

    def __enter__(self):
        self.saved = EDQF.publish

        def cell(root, path, text):
            proof = self.saved(root, path, text)
            data = json.loads(read(path))
            data["self_drive"][self.field_name] += self.delta
            with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(data, ensure_ascii=False, indent=2)
                             + "\n")
            self.published += 1
            return proof

        EDQF.publish = cell
        return self

    def __exit__(self, *exc):
        EDQF.publish = self.saved
        return False


class stale_gate(object):
    """Publish normally but answer a non-CURRENT gate word."""

    def __init__(self):
        self.saved = None
        self.calls = 0

    def __enter__(self):
        self.saved = EDQF.publish

        def cell(root, path, text):
            proof = dict(self.saved(root, path, text))
            proof["gate"] = "STALE"
            self.calls += 1
            return proof

        EDQF.publish = cell
        return self

    def __exit__(self, *exc):
        EDQF.publish = self.saved
        return False


def ac_edsh1():
    """AC-EDSH1: the health term asks a FRESH recompute at call time."""
    directory = tempfile.mkdtemp(prefix="edsh1-")
    try:
        target = copy_export(directory)
        with two_shot_self_drive("proposals_total") as shot:
            code, printed = run_driver(target)
        # R2596 birth-site repair: this criterion pinned code == 2 for a
        # block that moved with the LOG. That false refusal is exactly what
        # the R2596 row was chartered to name apart, so the INTENT is kept
        # (the term is still not canned: a moved block must not read plain
        # PASS) while the healthy outcome is the named word instead.
        ok = (shot.calls >= 2 and code == 0 and "ok=True" in printed
              and "VERDICT DRIFT-UNDER-WRITE" in printed)
        check(ok, "AC-EDSH1 the health term is not canned: a self_drive block "
                  "that moves between the write and the read-back is named "
                  "DRIFT-UNDER-WRITE rather than reading a plain PASS")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edsh2():
    """AC-EDSH2: the exact regression - a tokens line does not fail the run."""
    derived = CEC.recompute()[0]
    total = derived["log_lines_in_window"]
    subst = derived["substantive_non_idle_mention_lines"]
    directory = tempfile.mkdtemp(prefix="edsh2-")
    try:
        target = copy_export(directory)
        code, printed = run_driver(target)
        stored = json.loads(read(target))["self_drive"]
        ok = (subst < total
              and stored["log_lines_in_window"] == total
              and stored["substantive_non_idle_mention_lines"] == subst
              and code == 0
              and "ok=True" in printed)
        check(ok, "AC-EDSH2 a window holding a tokens line counts MORE window "
                  "lines than substantive lines and the driver still exits 0 "
                  "(the equality this repair replaced could never hold)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edsh3():
    """AC-EDSH3: the verdict reads the DOCUMENT, not the in-memory dict."""
    directory = tempfile.mkdtemp(prefix="edsh3-")
    try:
        target = copy_export(directory)
        with doctor_on_write("proposals_open", 1) as shot:
            code, printed = run_driver(target)
        stored = json.loads(read(target))["self_drive"]["proposals_open"]
        fresh = CEC.recompute()[0]["proposals_open"]
        ok = (shot.published == 1
              and stored == fresh + 1
              and code == 2
              and "ok=False" in printed)
        check(ok, "AC-EDSH3 a self_drive field doctored on disk AFTER the "
                  "write reads ok=False and exits 2, so the proof binds the "
                  "bytes rather than the dict it just built")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edsh4():
    """AC-EDSH4: the queue gate term still gates the verdict."""
    directory = tempfile.mkdtemp(prefix="edsh4-")
    try:
        target = copy_export(directory)
        with stale_gate() as shot:
            code, printed = run_driver(target)
        ok = (shot.calls == 1 and code == 2 and "ok=False" in printed)
        check(ok, "AC-EDSH4 a non-CURRENT gate word keeps the run red, so the "
                  "queue verdict is not swallowed by the self_drive repair")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_edsh5():
    """AC-EDSH5: no other ok term was dropped by the repair."""
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    terms = ('r[1] == label',
             'str(r[0]) == tick',
             'back["outs"][0] == latest',
             'back["ceo_face"]["latest_artifact"] == latest',
             'back["ceo_face"]["current"] == current',
             'back["ceo_face"]["next_milestone"] == milestone',
             'back["export_ts"] == STAMP',
             # R2596 birth-site repair: the literal fresh-recompute term
             # WAS the defect (it re-read the tree after the write), so the
             # stamped-block term and the surviving fresh read are pinned
             # separately instead of the old defective literal.
             'back["self_drive"] == at_write',
             "fresh = self_drive()",
             'proof.get("gate") == "CURRENT"')
    missing = [term for term in terms if term not in source]
    check(not missing,
          "AC-EDSH5 every earlier health term survives beside the repaired one "
          "(tick row, outs, three ceo fields, stamp, fresh self_drive, gate; "
          "missing=%s)" % (",".join(missing) or "none"))


def ac_edsh6():
    """AC-EDSH6: hygiene and registration."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = not any(byte > 127 for byte in raw)
    # The driver legitimately derives its 48h due date from the state log, so
    # datetime is NOT banned here; only egress is. This clause was corrected
    # after the first run measured 'import datetime' in the module and the
    # assertion refused rather than the module being bent to fit it.
    banned = ("import socket", "import urllib", "import requests",
              "import http.client")
    hits = [word for word in banned if word in raw.decode("ascii")]
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = WIRED_EXPECT in runner and LABEL in runner
    check(ascii_ok and not hits and wired,
          "AC-EDSH6 the driver stays pure ASCII stdlib with no network egress "
          "(datetime is legitimately used for the 48h due), and the runner "
          "carries this row at 6 criteria (ascii=%s banned=%s wired=%s)"
          % (ascii_ok, ",".join(hits) or "none", wired))


def main():
    for name, fn in (("AC-EDSH1", ac_edsh1), ("AC-EDSH2", ac_edsh2),
                     ("AC-EDSH3", ac_edsh3), ("AC-EDSH4", ac_edsh4),
                     ("AC-EDSH5", ac_edsh5), ("AC-EDSH6", ac_edsh6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())