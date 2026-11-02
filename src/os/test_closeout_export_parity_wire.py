"""closeout_export_parity_wire suite (R2378).

Criteria AC-CEPW1..AC-CEPW6 were pinned inside the R2377 tech seed row of
state/queue/tech.md:424 BEFORE this code existed.

What this proves: the export parity shipped at R2377 was a CLI with no caller,
so a closeout could still publish a queue block nobody proved. This wire is
the caller - it stages the bytes it is about to publish, asks
export_closeout_gate_parity.check over the staged document, and only replaces
the export on AGREES. The suite proves the parity is the real one (patching
its check moves what gets published), that a refusal leaves the export
byte-identical with no residue, that an AGREES reading writes and reads back,
that a refusal writes nothing and no clock is read, and that the CLI keeps its
four exit codes with a byte-stable JSON face.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import closeout_export_parity_wire as CEPW  # noqa: E402
import export_closeout_gate_parity as ECGP  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "closeout_export_parity_wire.py")
SUITE = os.path.join(BASE, "test_closeout_export_parity_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-closeout-export-parity-wire"
WIRED_EXPECT = '"test_closeout_export_parity_wire.py"), 6),'

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


def section(claimable=10):
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


class patched_check(object):
    """Temporarily replace export_closeout_gate_parity.check."""

    def __init__(self, result, code):
        self.result = result
        self.code = code
        self.saved = None
        self.calls = []

    def __call__(self, root, path):
        self.calls.append((root, path))
        return self.result, self.code

    def __enter__(self):
        self.saved = ECGP.check
        ECGP.check = self
        return self

    def __exit__(self, *exc):
        ECGP.check = self.saved
        return False


def refused_report(path):
    return {
        "label": ECGP.LABEL,
        "verdict": "DISAGREES",
        "path": path,
        "gate": "WRITTEN",
        "drifted": [],
        "closeout_bytes": 10,
        "wire_bytes": 12,
        "differs": "queue.verdict",
    }


def ac_cepw1():
    """AC-CEPW1: the parity is the real check; patching it moves the bytes."""
    directory = tempfile.mkdtemp(prefix="cepw1-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 1}})
            baseline, code_baseline = CEPW.publish(REPO, target)
            after_baseline = read(target)

            second = write_export(directory,
                                  {"self_drive": {"tick": 1}},
                                  name="second.json")
            second_before = read(second)
            with patched_check(refused_report(second), 2) as guard:
                spoofed, code_spoofed = CEPW.publish(REPO, second)
            calls = len(guard.calls)
            after_spoofed = read(second)

            third = write_export(directory,
                                 {"self_drive": {"tick": 1}},
                                 name="third.json")
            published, code_published = CEPW.publish(REPO, third)
            after_published = read(third)

        compose_owner = True
        saved = ECGP.closeout_style
        try:
            ECGP.closeout_style = lambda root, path: "PROBE\n"
            compose_owner = CEPW.compose(".", "unused") == "PROBE\n"
        finally:
            ECGP.closeout_style = saved

        check(code_baseline == 0 and baseline["verdict"] == "WRITTEN",
              "AC-CEPW1a publish writes through the real parity")
        check(calls == 1 and code_spoofed == 2
              and spoofed["reading"] == "DISAGREES"
              and after_spoofed == second_before
              and code_published == 0
              and after_published != second_before
              and '"queue"' in after_published,
              "AC-CEPW1b patching check moves what is published")
        check(compose_owner,
              "AC-CEPW1c the closeout byte shape stays owned by the parity")
    finally:
        _cleanup(directory)


def ac_cepw2():
    """AC-CEPW2: a refused reading leaves the export byte-identical."""
    directory = tempfile.mkdtemp(prefix="cepw2-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 2}})
            before = read(target)
            before_names = sorted(os.listdir(directory))

            with patched_check(refused_report(target), 2):
                report, code = CEPW.publish(REPO, target)

            after = read(target)
            after_names = sorted(os.listdir(directory))

        check(code == 2 and report["verdict"] == "REFUSED"
              and report["reading"] == "DISAGREES",
              "AC-CEPW2a a refusal is named with its reading")
        check(after == before and before_names == after_names,
              "AC-CEPW2b the export is untouched and no residue is left")
    finally:
        _cleanup(directory)


def ac_cepw3():
    """AC-CEPW3: AGREES writes the closeout-shaped bytes, read back."""
    directory = tempfile.mkdtemp(prefix="cepw3-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 3}})
            expected = CEPW.compose(".", target)
            report, code = CEPW.publish(REPO, target)
            written = read(target)
            names = sorted(os.listdir(directory))

        check(code == 0 and report["verdict"] == "WRITTEN"
              and report["reading"] == "AGREES",
              "AC-CEPW3a an agreeing reading writes")
        check(written == expected
              and report["bytes"] == len(written.encode("utf-8")),
              "AC-CEPW3b the written bytes are the closeout shape")
        check("status-export.json.parity-stage" not in names,
              "AC-CEPW3c the staged file does not survive the publish")
    finally:
        _cleanup(directory)


def ac_cepw4():
    """AC-CEPW4: the wire writes nothing when it refuses and reads no clock."""
    directory = tempfile.mkdtemp(prefix="cepw4-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 4}})
            before = _census(directory)
            with patched_check(refused_report(target), 2):
                CEPW.publish(REPO, target)
            after = _census(directory)

        check(before == after,
              "AC-CEPW4a a refusal leaves every file and every size alone")

        source = read(MODULE)
        clock = [line for line in source.splitlines()
                 if line.startswith(("import time", "import datetime",
                                     "from time", "from datetime"))]
        network = [line for line in source.splitlines()
                   if line.startswith(("import socket", "import urllib",
                                       "import http", "import requests"))]
        check(not clock and not network,
              "AC-CEPW4b no clock and no network import in the wire")
    finally:
        _cleanup(directory)


def ac_cepw5():
    """AC-CEPW5: exit 0 written, 2 refused, 3 missing, 5 bad flags."""
    directory = tempfile.mkdtemp(prefix="cepw5-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 5}})
            proc = subprocess.run(
                [sys.executable, MODULE, "--publish", "--root", REPO,
                 "--export", target, "--json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            payload = json.loads(proc.stdout.decode("utf-8"))
            order = tuple(payload.keys())

            second = write_export(directory, {"self_drive": {"tick": 5}},
                                  name="second.json")
            with patched_check(refused_report(second), 2):
                refused = CEPW.main(["--publish", "--root", REPO,
                                     "--export", second])

        missing = CEPW.main(["--publish", "--root", REPO,
                             "--export", os.path.join(directory, "absent.json")])
        bad = CEPW.main(["--publish", "--nope"])
        no_publish = CEPW.main(["--root", REPO])

        check(proc.returncode == 0 and payload["verdict"] == "WRITTEN",
              "AC-CEPW5a exit 0 on a written export")
        check(refused == 2 and missing == 3 and bad == 5 and no_publish == 5,
              "AC-CEPW5b refusals keep their own codes (2/3/5/5)")
        check(order == CEPW.REPORT_KEYS,
              "AC-CEPW5c the json face is the pinned key order")
    finally:
        _cleanup(directory)


def ac_cepw6():
    """AC-CEPW6: ASCII, stdlib only, no network, its own reconcile label."""
    source = read(MODULE)
    suite = read(SUITE)
    wired = read(RUNNER)

    check(all(ord(ch) < 128 for ch in source + suite),
          "AC-CEPW6a the wire and its suite are pure ASCII")
    check('"os-closeout-export-parity-wire"' in source
          and WIRED_EXPECT in wired,
          "AC-CEPW6b the wire carries its own label and is registry-wired")
    check(EXPECTED_CRITERIA == 6
          and 'test_closeout_export_parity_wire.py"), 6),' in wired,
          "AC-CEPW6c six criteria declared to the registry")


def _census(directory):
    """Every file name and size in the directory, sorted."""
    rows = []
    for name in sorted(os.listdir(directory)):
        rows.append((name, os.path.getsize(os.path.join(directory, name))))
    return rows


def _cleanup(directory):
    for name in os.listdir(directory):
        try:
            os.remove(os.path.join(directory, name))
        except OSError:
            pass
    try:
        os.rmdir(directory)
    except OSError:
        pass


def main():
    ac_cepw1()
    ac_cepw2()
    ac_cepw3()
    ac_cepw4()
    ac_cepw5()
    ac_cepw6()
    total = PASSES + FAILS
    print("SUITE %s %d/%d" % ("PASS" if not FAILS else "FAIL",
                              PASSES, total), flush=True)
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())