"""closeout_export_parity_text_binding suite (R2501).

Criteria AC-CEPM1..AC-CEPM6 were pinned inside the R2454 tech seed row of
state/queue/tech.md:535 BEFORE this code existed.

What this proves: closeout_export_parity_wire.publish proves the bytes it is
handed against the parity, but the parity recomposes the STAGED bytes - it
never asks whether those bytes are what the document being replaced composes
to. MEASURED at R2454: a composition made from document A published over
document B read WRITTEN/AGREES and wrote A's content into B. One face now
binds the handed text to the target's own composition at CALL time and
refuses, naming the first differing field from the shipped difference law,
before any byte is staged.

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

import closeout_export_parity_text_binding as CEPTB  # noqa: E402
import closeout_export_parity_wire as CEPW  # noqa: E402
import export_closeout_gate_parity as ECGP  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "closeout_export_parity_text_binding.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
LABEL = "os-closeout-export-parity-text-binding"
WIRED_EXPECT = '"test_closeout_export_parity_text_binding.py"), 6),'
ALLOWED_IMPORTS = {"io", "json", "os", "sys",
                   "closeout_export_parity_wire",
                   "export_closeout_gate_parity"}

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


def read_text(path, newline=None):
    with io.open(path, "r", encoding="utf-8-sig", newline=newline) as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


class patched(object):
    """Temporarily replace one attribute so a CALL-time ask is observable."""

    def __init__(self, module, name, value):
        self.module = module
        self.name = name
        self.value = value

    def __enter__(self):
        self.old = getattr(self.module, self.name)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.old)
        return False


def fixture(directory, name, transport="LF"):
    """A private copy of the real export in the transport asked for."""
    text = read_text(EXPORT)
    if transport == "CRLF":
        text = text.replace("\n", "\r\n")
    path = os.path.join(directory, name)
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


def doctored_fixture(directory, name):
    """A copy of the real export whose own composition DIFFERS from the real one.

    self_drive.window_days is the field moved, so the shipped difference law
    has a real dotted field name to hand back - never a shape word.
    """
    data = json.loads(read_text(EXPORT))
    block = data.get("self_drive")
    if not isinstance(block, dict):
        return None
    block["window_days"] = 999
    path = os.path.join(directory, name)
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return path


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args, cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode, proc.stdout.decode("utf-8"),
            proc.stderr.decode("utf-8"))


def ac_cepm1_call_time():
    """AC-CEPM1 the binding is asked through the SHIPPED composition at CALL."""
    src = read_text(MODULE)
    check("indent=" not in src and "queue_floor_export_face" not in src
          and "QFE." not in src,
          "AC-CEPM1 the module carries no formatter of its own")
    tmpdir = tempfile.mkdtemp(prefix="ceptb1-")
    try:
        path = fixture(tmpdir, "export.json")
        before = read_bytes(path)
        hand = CEPW.compose(REPO, path)
        moving = {"state": "real"}
        real_compose = CEPW.compose

        def fake_compose(root, target):
            moving["state"] = "patched"
            return real_compose(root, target).replace('"window_days": 7',
                                                      '"window_days": 8')

        with patched(CEPW, "compose", fake_compose):
            result, code = CEPTB.publish(REPO, path, hand)
        check(moving["state"] == "patched" and code == 2
              and result["binding"] == "REFUSED",
              "AC-CEPM1 patching the shipped composition moves the verdict")
        check(read_bytes(path) == before,
              "AC-CEPM1 the refusal wrote no byte")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ac_cepm2_same_document_publishes():
    """AC-CEPM2 text composed from the SAME document still publishes."""
    tmpdir = tempfile.mkdtemp(prefix="ceptb2-")
    try:
        today = fixture(tmpdir, "today.json")
        ours = fixture(tmpdir, "ours.json")
        text = CEPW.compose(REPO, today)
        CEPW.publish(REPO, today, text)
        result, code = CEPTB.publish(REPO, ours, text)
        check(code == 0 and result["verdict"] == "WRITTEN"
              and result["binding"] == "BOUND" and result["differs"] == "",
              "AC-CEPM2 the same document publishes and reads BOUND")
        check(read_bytes(ours) == read_bytes(today),
              "AC-CEPM2 the published bytes are byte-identical to today's route")

        crlf_today = fixture(tmpdir, "crlf-today.json", transport="CRLF")
        crlf_ours = fixture(tmpdir, "crlf-ours.json", transport="CRLF")
        crlf_text = CEPW.compose(REPO, crlf_today)
        CEPW.publish(REPO, crlf_today, crlf_text)
        result, code = CEPTB.publish(REPO, crlf_ours, crlf_text)
        payload = read_bytes(crlf_ours)
        check(code == 0 and result["binding"] == "BOUND"
              and payload == read_bytes(crlf_today)
              and payload.count(b"\n") == payload.count(b"\r\n") > 0,
              "AC-CEPM2 a CRLF document keeps its transport byte-identically")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ac_cepm3_foreign_text_refused():
    """AC-CEPM3 text composed from a DIFFERENT document refuses, writes nothing."""
    tmpdir = tempfile.mkdtemp(prefix="ceptb3-")
    try:
        other = doctored_fixture(tmpdir, "other.json")
        target = fixture(tmpdir, "target.json")
        check(other is not None, "AC-CEPM3 doctored fixture built")
        if other is None:
            return
        text = CEPW.compose(REPO, other)
        before = read_bytes(target)
        result, code = CEPTB.publish(REPO, target, text)
        check(code == 2 and result["verdict"] == "REFUSED"
              and result["binding"] == "REFUSED" and result["bytes"] == 0,
              "AC-CEPM3 a foreign composition is refused with its own code")
        check(read_bytes(target) == before
              and not os.path.exists(target + ".parity-stage"),
              "AC-CEPM3 the target is byte-identical with no residue")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ac_cepm4_difference_named():
    """AC-CEPM4 the refusal names the first differing field of the shipped law."""
    tmpdir = tempfile.mkdtemp(prefix="ceptb4-")
    try:
        other = doctored_fixture(tmpdir, "other.json")
        target = fixture(tmpdir, "target.json")
        if other is None:
            check(False, "AC-CEPM4 doctored fixture built")
            return
        text = CEPW.compose(REPO, other)
        expected = ECGP.first_difference(
            CEPTB._normalise(CEPW.compose(REPO, target)),
            CEPTB._normalise(text))
        result, _code = CEPTB.publish(REPO, target, text)
        check(expected == "self_drive.window_days"
              and result["differs"] == expected,
              "AC-CEPM4 the refusal names the first differing field")
        check(result["differs"] not in ("", "bytes"),
              "AC-CEPM4 the named field is a real field, not a shape word")
        code, out, err = run_cli(["--publish", "--root", REPO,
                                  "--export", target, "--text-from", other,
                                  "--json"])
        payload = json.loads(out)
        check(code == 2 and payload["differs"] == expected and err == "",
              "AC-CEPM4 the CLI reports the same field at exit 2")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ac_cepm5_report_shape():
    """AC-CEPM5 existing keys keep their values; binding is additional."""
    check(tuple(CEPTB.REPORT_KEYS) == tuple(CEPW.REPORT_KEYS) + ("binding",
                                                                "differs"),
          "AC-CEPM5 the wire's seven keys keep their names and positions")
    tmpdir = tempfile.mkdtemp(prefix="ceptb5-")
    try:
        path = fixture(tmpdir, "export.json")
        before = read_bytes(path)
        text = CEPW.compose(REPO, path)
        ours, code = CEPTB.publish(REPO, path, text)
        check(code == 0 and set(ours) == set(CEPTB.REPORT_KEYS)
              and ours["binding"] == "BOUND",
              "AC-CEPM5 the published report carries exactly the nine keys")
        with io.open(path, "wb") as handle:
            handle.write(before)
        today, today_code = CEPW.publish(REPO, path, text)
        keys = tuple(CEPW.REPORT_KEYS)
        check(code == today_code
              and all(ours[key] == today[key] for key in keys),
              "AC-CEPM5 the seven shipped readings are byte-equal to today")

        other = doctored_fixture(tmpdir, "other.json")
        target = fixture(tmpdir, "refused.json")
        if other is None:
            check(False, "AC-CEPM5 doctored fixture built")
            return
        refused, refused_code = CEPTB.publish(REPO, target,
                                              CEPW.compose(REPO, other))
        check(refused_code == 2 and set(refused) == set(CEPTB.REPORT_KEYS)
              and refused["label"] == CEPW.LABEL,
              "AC-CEPM5 the refusal carries the same nine keys")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ac_cepm6_hygiene():
    """AC-CEPM6 pure ASCII, stdlib plus two shipped faces, one registry row."""
    raw = read_bytes(MODULE)
    check(all(byte < 128 for byte in raw), "AC-CEPM6 module source is pure ASCII")
    text = read_text(MODULE)
    names = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("import "):
            names.add(line.split()[1].split(".")[0])
        elif line.startswith("from ") and " import " in line:
            names.add(line.split()[1].split(".")[0])
    check(names <= ALLOWED_IMPORTS
          and names - {"closeout_export_parity_wire",
                       "export_closeout_gate_parity"} <= {"io", "json", "os", "sys"},
          "AC-CEPM6 imports are stdlib plus the two shipped faces only")
    check("import time" not in text and "datetime" not in text
          and "socket" not in text and "urllib" not in text
          and "http" not in text,
          "AC-CEPM6 no clock and zero network")
    runner = read_text(RUNNER)
    check(runner.count(WIRED_EXPECT) == 1
          and runner.count('"%s"' % LABEL) == 1,
          "AC-CEPM6 exactly one registry row wires this suite with 6 criteria")
    check(EXPECTED_CRITERIA == 6, "AC-CEPM6 six criteria declared")


def main():
    ac_cepm1_call_time()
    ac_cepm2_same_document_publishes()
    ac_cepm3_foreign_text_refused()
    ac_cepm4_difference_named()
    ac_cepm5_report_shape()
    ac_cepm6_hygiene()
    print("SUMMARY pass=%d fail=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())