"""export_closeout_gate_parity suite (R2377).

Criteria AC-ECGP1..AC-ECGP6 were pinned inside the R2376 tech seed row of
state/queue/tech.md:423 BEFORE this code existed.

What this proves: two writers publish the CEO-visible export - the closeout
(QFE.apply then json.dumps itself) and queue_export_gate_wire (compose, prove
with the freshness gate, then replace) - and until now nothing compared them,
so the gate had no caller in the real path. This suite proves the parity is
derived from those two real recipes, that they agree on one document, that a
closeout block the gate would refuse is named as a bypass with the queue
named, that the check writes nothing in the repository, and that the CLI keeps
its four exit codes.

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

import export_closeout_gate_parity as ECGP  # noqa: E402
import queue_export_gate_wire as QEG  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_closeout_gate_parity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-closeout-gate-parity"
WIRED_EXPECT = '"test_export_closeout_gate_parity.py"), 6),'

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
    """A queue section shape: one row per queue, all at the same claimable."""
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


def write_export(directory, data, name="status-export.json"):
    target = os.path.join(directory, name)
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return target


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


class patched_apply(object):
    """Temporarily replace queue_floor_export_face.apply with a fixture."""

    def __init__(self, value):
        self.value = value
        self.saved = None
        self.calls = []

    def __call__(self, data, root):
        self.calls.append(root)
        if self.value is not None:
            self.value(data, root)
        return data

    def __enter__(self):
        self.saved = QFE.apply
        QFE.apply = self
        return self

    def __exit__(self, *exc):
        QFE.apply = self.saved
        return False


class patched_publish(object):
    """Temporarily replace queue_export_gate_wire.publish with a fixture."""

    def __init__(self, result, code):
        self.result = result
        self.code = code
        self.saved = None
        self.calls = []

    def __call__(self, root, path):
        self.calls.append((root, path))
        return self.result, self.code

    def __enter__(self):
        self.saved = QEG.publish
        QEG.publish = self
        return self

    def __exit__(self, *exc):
        QEG.publish = self.saved
        return False


def live_section(directory):
    live = QFE.face(REPO)
    target = write_export(directory, {"self_drive": {"tick": 1},
                                      "queue": live})
    return target


def ac_ecgp1():
    """AC-ECGP1: both writers are the real ones; patching either moves verdict."""
    directory = tempfile.mkdtemp(prefix="ecgp1-")
    try:
        target = live_section(directory)
        baseline, code_baseline = ECGP.check(REPO, target)

        def drop_queue(data, root):
            data.pop("queue", None)

        with patched_apply(drop_queue) as apply_guard:
            patched_closeout, code_closeout = ECGP.check(REPO, target)
        closeout_calls = len(apply_guard.calls)

        refused = {"label": QEG.LABEL, "verdict": "REFUSED",
                   "path": target, "gate": "STALE",
                   "drifted": ["queue:tech"], "bytes": 1}
        with patched_publish(refused, 2) as publish_guard:
            patched_wire, code_wire = ECGP.check(REPO, target)
        wire_calls = len(publish_guard.calls)

        ok = (baseline["verdict"] == "AGREES" and code_baseline == 0
              and patched_closeout["verdict"] == "BYPASS" and code_closeout == 2
              and closeout_calls >= 1
              and patched_wire["verdict"] == "BYPASS" and code_wire == 2
              and wire_calls == 1)
        if not ok:
            print("  measured: base=%r/%r closeout=%r/%r calls=%d "
                  "wire=%r/%r calls=%d"
                  % (baseline["verdict"], code_baseline,
                     patched_closeout["verdict"], code_closeout, closeout_calls,
                     patched_wire["verdict"], code_wire, wire_calls),
                  flush=True)
        check(ok, "AC-ECGP1 the parity is derived from the two real writers "
                  "(patching QFE.apply or QEG.publish moves the verdict)")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_ecgp2():
    """AC-ECGP2: both recipes publish identical bytes over one document."""
    directory = tempfile.mkdtemp(prefix="ecgp2-")
    try:
        target = live_section(directory)
        closeout_text = ECGP.closeout_style(REPO, target)
        wire_text, wire_result, wire_code = ECGP._wire_reading(REPO, target)
        result, code = ECGP.check(REPO, target)
        ok = (wire_code == 0 and wire_text == closeout_text
              and wire_result.get("verdict") == "WRITTEN"
              and result["verdict"] == "AGREES" and code == 0
              and result["differs"] == ""
              and result["closeout_bytes"] == result["wire_bytes"])
        if not ok:
            print("  measured: wire=%r bytes_same=%r verdict=%r code=%r "
                  "differs=%r %r/%r"
                  % (wire_code, wire_text == closeout_text,
                     result["verdict"], code, result["differs"],
                     result["closeout_bytes"], result["wire_bytes"]),
                  flush=True)
        check(ok, "AC-ECGP2 a closeout-style write and a wire write over the "
                  "same document publish identical bytes")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_ecgp3():
    """AC-ECGP3: an unproven closeout block is named as the bypass."""
    directory = tempfile.mkdtemp(prefix="ecgp3-")
    try:
        target = write_export(directory, {"self_drive": {"tick": 2},
                                          "queue": section(9)})

        def keep(data, root):
            return data

        with patched_face(section(10)):
            with patched_apply(keep):
                result, code = ECGP.check(".", target)
        names = list(result["drifted"])
        ok = (result["verdict"] == "BYPASS" and code == 2
              and "queue:tech" in names
              and result["gate"] == "REFUSED"
              and result["differs"] == "wire-refused"
              and result["wire_bytes"] == 0)
        if not ok:
            print("  measured: verdict=%r code=%r drifted=%r gate=%r "
                  "differs=%r"
                  % (result["verdict"], code, names, result["gate"],
                     result["differs"]), flush=True)
        check(ok, "AC-ECGP3 a closeout-style write the gate would refuse is "
                  "named BYPASS with the queue named")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_ecgp4():
    """AC-ECGP4: the check writes nothing in the repo and reads no clock."""
    source = read(MODULE)
    clock_ok = not any(token in source for token in
                       ("import time", "time.time", "datetime", "random"))
    directory = tempfile.mkdtemp(prefix="ecgp4-")
    try:
        target = live_section(directory)
        before = io.open(target, "rb").read()
        listing_before = sorted(os.listdir(directory))
        ECGP.check(REPO, target)
        after = io.open(target, "rb").read()
        listing_after = sorted(os.listdir(directory))
        ok = (clock_ok and before == after
              and listing_before == listing_after)
        if not ok:
            print("  measured: clock=%r bytes_same=%r listing=%r vs %r"
                  % (clock_ok, before == after, listing_before,
                     listing_after), flush=True)
        check(ok, "AC-ECGP4 the check writes nothing (no residue) and the "
                  "module reads no clock")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_ecgp5():
    """AC-ECGP5: exit 0 = AGREES, 2 = BYPASS/DISAGREES, 3 and 5 for the rest."""
    directory = tempfile.mkdtemp(prefix="ecgp5-")
    try:
        target = live_section(directory)
        absent = os.path.join(directory, "absent.json")

        def run(extra):
            proc = subprocess.run(
                [sys.executable, MODULE] + extra,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO)
            return proc.returncode

        code_agrees = run(["--check", "--root", REPO, "--export", target])
        code_missing = run(["--check", "--root", REPO, "--export", absent])
        code_bad = run(["--bogus"])

        def keep(data, root):
            return data

        with patched_face(section(10)):
            with patched_apply(keep):
                code_bypass = ECGP.main(["--check", "--root", ".",
                                         "--export", target])
        ok = (code_agrees == 0 and code_bypass == 2
              and code_missing == 3 and code_bad == 5)
        if not ok:
            print("  measured: agrees=%r bypass=%r missing=%r bad=%r"
                  % (code_agrees, code_bypass, code_missing, code_bad),
                  flush=True)
        check(ok, "AC-ECGP5 exit 0 = AGREES, 2 = BYPASS or DISAGREES, "
                  "3 = missing file, 5 = bad flags")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def ac_ecgp6():
    """AC-ECGP6: pure ASCII, stdlib only, no network, own label wired at 6."""
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
    check(ok, "AC-ECGP6 pure ASCII, stdlib only, no network, one runner "
              "entry at 6 criteria")


def main():
    print("SUITE export_closeout_gate_parity (R2377) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for fn in (ac_ecgp1, ac_ecgp2, ac_ecgp3, ac_ecgp4, ac_ecgp5, ac_ecgp6):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())