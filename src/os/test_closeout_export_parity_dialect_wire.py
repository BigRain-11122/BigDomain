"""closeout_export_parity_dialect_wire suite (R2454).

Criteria AC-CEPD1..AC-CEPD6 were pinned inside the R2452 tech seed row of
state/queue/tech.md:520 BEFORE this code existed.

What this proves: MEASURED at R2452 the closeout wire could not publish a
CRLF-dialect export at all - it read REFUSED at exit 2 with the document
byte-identical while its LF leg wrote normally, because the parity compared LF
composition against the dialect the gate wire keeps. The composition now lands
the target's OWN transport, asked of the shipped dialect law at CALL time, and
this suite proves the round trip both ways: a CRLF export publishes with zero
lone LF and exactly the LF composition with CRLF endings, an LF export keeps
today's bytes, the checker still names content drift instead of a transport
noise ("bytes"), the old reading keys keep their values while the transport
reading is added, and the wire keeps its own label, CLI and registry entry.

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

import closeout_export_parity_dialect_wire as CEPD  # noqa: E402
import closeout_export_parity_wire as CEPW  # noqa: E402
import export_closeout_gate_parity as ECGP  # noqa: E402
import general_writer_dialect_audit as GWDA  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "closeout_export_parity_dialect_wire.py")
SUITE = os.path.join(BASE, "test_closeout_export_parity_dialect_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-closeout-export-parity-dialect-wire"
WIRED_EXPECT = '"test_closeout_export_parity_dialect_wire.py"), 6),'

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
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def raw(path):
    with io.open(path, "rb") as handle:
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


def write_export(directory, data, name="status-export.json", crlf=False):
    """Write the fixture in the requested transport and return its path."""
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    target = os.path.join(directory, name)
    with io.open(target, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return target


def expected_text(root, path):
    """The closeout shape an LF document must land, computed independently."""
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    QFE.apply(data, root)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


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

    def __call__(self, root, path):
        return self.result, self.code

    def __enter__(self):
        self.saved = ECGP.check
        ECGP.check = self
        return self

    def __exit__(self, *exc):
        ECGP.check = self.saved
        return False


def ac_cepd1():
    """AC-CEPD1: the closeout composition lands the target's OWN dialect."""
    directory = tempfile.mkdtemp(prefix="cepd1-")
    try:
        with patched_face(section()):
            crlf = write_export(directory, {"self_drive": {"tick": 1}},
                                name="crlf.json", crlf=True)
            composed = ECGP.closeout_style(REPO, crlf)
            lf = write_export(directory, {"self_drive": {"tick": 1}},
                              name="lf.json")
            lf_composed = ECGP.closeout_style(REPO, lf)
            lf_expected = expected_text(REPO, lf)

            saved = GWDA.payload_for

            def probe(path, text):
                return b"PROBE"

            GWDA.payload_for = probe
            try:
                moved = ECGP.closeout_style(REPO, lf)
            finally:
                GWDA.payload_for = saved

        lone = composed.replace("\r\n", "").count("\n")
        check(lone == 0 and "\r\n" in composed,
              "AC-CEPD1a a CRLF document composes with zero lone LF")
        check(lf_composed == lf_expected,
              "AC-CEPD1b an LF document keeps today's bytes")
        check(moved == "PROBE",
              "AC-CEPD1c the dialect law is asked at CALL time")
    finally:
        _cleanup(directory)


def ac_cepd2():
    """AC-CEPD2: a CRLF export publishes through the closeout wire."""
    directory = tempfile.mkdtemp(prefix="cepd2-")
    try:
        with patched_face(section()):
            cf = write_export(directory, {"self_drive": {"tick": 2}},
                              name="crlf.json", crlf=True)
            lf_copy = write_export(directory, {"self_drive": {"tick": 2}},
                                   name="lf.json")
            expected = expected_text(REPO, lf_copy).replace("\n", "\r\n")
            report, code = CEPD.publish(REPO, cf)
            landed = raw(cf)

        check(code == 0 and report["verdict"] == "WRITTEN"
              and report["reading"] == "AGREES",
              "AC-CEPD2a the CRLF document is WRITTEN, parity AGREEing")
        check(landed == expected.encode("utf-8"),
              "AC-CEPD2b the bytes are the LF composition with CRLF endings")
        check(landed.replace(b"\r\n", b"").count(b"\n") == 0
              and landed.count(b"\r\n") > 0
              and report["lone_lf"] == 0
              and report["transport"] == "CRLF",
              "AC-CEPD2c zero lone LF, declared CRLF transport")
    finally:
        _cleanup(directory)


def ac_cepd3():
    """AC-CEPD3: an LF export keeps exactly today's bytes."""
    directory = tempfile.mkdtemp(prefix="cepd3-")
    try:
        with patched_face(section()):
            lf = write_export(directory, {"self_drive": {"tick": 3}},
                              name="lf.json")
            expected = expected_text(REPO, lf)
            report, code = CEPD.publish(REPO, lf)
            landed = raw(lf)

        check(code == 0 and report["verdict"] == "WRITTEN",
              "AC-CEPD3a the LF document is WRITTEN")
        check(landed == expected.encode("utf-8") and b"\r" not in landed,
              "AC-CEPD3b today's LF bytes are unchanged")
        check(report["transport"] == "LF" and report["bytes"] == len(landed),
              "AC-CEPD3c the reading names LF and the landed size")
    finally:
        _cleanup(directory)


def ac_cepd4():
    """AC-CEPD4: content drift is still named; the document is untouched."""
    directory = tempfile.mkdtemp(prefix="cepd4-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 4}})
            before = raw(target)
            saved = ECGP.closeout_style

            def doctored(root, path):
                data = json.loads(saved(root, path))
                data["self_drive"]["tick"] = 4004
                text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
                return text

            ECGP.closeout_style = doctored
            try:
                reading, code = ECGP.check(REPO, target)
                after_check = raw(target)
                report = {
                    "label": ECGP.LABEL,
                    "verdict": "DISAGREES",
                    "path": target,
                    "transport": "LF",
                    "gate": "WRITTEN",
                    "drifted": [],
                    "closeout_bytes": 10,
                    "wire_bytes": 11,
                    "differs": "self_drive.tick",
                }
                with patched_check(report, 2):
                    refused, refused_code = CEPD.publish(REPO, target)
            finally:
                ECGP.closeout_style = saved
            after_refusal = raw(target)
            names = sorted(os.listdir(directory))

        check(reading["verdict"] == "DISAGREES"
              and code == 2
              and reading["differs"] == "self_drive.tick",
              "AC-CEPD4a a doctored value reads DISAGREES with its own name")
        check(after_check == before,
              "AC-CEPD4b the check leaves the document byte-identical")
        check(refused_code == 2 and refused["verdict"] == "REFUSED"
              and refused["reading"] == "DISAGREES"
              and after_refusal == before
              and "status-export.json.parity-stage" not in names,
              "AC-CEPD4c a content refusal publishes nothing, leaves no residue")
    finally:
        _cleanup(directory)


def ac_cepd5():
    """AC-CEPD5: old reading keys keep their values; transport is added."""
    directory = tempfile.mkdtemp(prefix="cepd5-")
    try:
        with patched_face(section()):
            lf = write_export(directory, {"self_drive": {"tick": 5}},
                              name="lf.json")
            lf_expected = expected_text(REPO, lf)
            lf_reading, lf_code = ECGP.check(REPO, lf)

            cf = write_export(directory, {"self_drive": {"tick": 5}},
                              name="crlf.json", crlf=True)
            crlf_expected = lf_expected.replace("\n", "\r\n")
            crlf_reading, crlf_code = ECGP.check(REPO, cf)

        check(lf_code == 0
              and lf_reading["label"] == ECGP.LABEL
              and lf_reading["verdict"] == "AGREES"
              and lf_reading["gate"] == "WRITTEN"
              and lf_reading["drifted"] == []
              and lf_reading["differs"] == "",
              "AC-CEPD5a the LF reading keys keep their values")
        check(lf_reading["closeout_bytes"] == len(lf_expected.encode("utf-8"))
              and lf_reading["wire_bytes"] == lf_reading["closeout_bytes"]
              and lf_reading["transport"] == "LF",
              "AC-CEPD5b the LF byte counts are unchanged, transport added")
        check(crlf_code == 0
              and crlf_reading["verdict"] == "AGREES"
              and crlf_reading["differs"] == ""
              and crlf_reading["closeout_bytes"]
              == len(crlf_expected.encode("utf-8"))
              and crlf_reading["wire_bytes"] == crlf_reading["closeout_bytes"]
              and crlf_reading["transport"] == "CRLF",
              "AC-CEPD5c the CRLF reading agrees in its own transport")
    finally:
        _cleanup(directory)


def ac_cepd6():
    """AC-CEPD6: ASCII, stdlib only, no clock, own label, wired at six."""
    source = read(MODULE)
    suite = read(SUITE)
    wired = read(RUNNER)

    check(all(ord(ch) < 128 for ch in source + suite),
          "AC-CEPD6a the wire and its suite are pure ASCII")
    clock = [line for line in source.splitlines()
             if line.startswith(("import time", "import datetime",
                                 "from time", "from datetime"))]
    network = [line for line in source.splitlines()
               if line.startswith(("import socket", "import urllib",
                                   "import http", "import requests"))]
    check(not clock and not network,
          "AC-CEPD6b no clock and no network import in the wire")
    check('"' + LABEL + '"' in source and WIRED_EXPECT in wired,
          "AC-CEPD6c the wire carries its own label and is registry-wired")

    directory = tempfile.mkdtemp(prefix="cepd6-")
    try:
        with patched_face(section()):
            target = write_export(directory, {"self_drive": {"tick": 6}})
            proc = subprocess.run(
                [sys.executable, MODULE, "--publish", "--root", REPO,
                 "--export", target, "--json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            payload = json.loads(proc.stdout.decode("utf-8"))
        order = tuple(payload.keys())
        missing = CEPD.main(["--publish", "--root", REPO,
                             "--export", os.path.join(directory, "absent.json")])
        bad = CEPD.main(["--publish", "--nope"])
        no_publish = CEPD.main(["--root", REPO])
        check(proc.returncode == 0 and payload["verdict"] == "WRITTEN"
              and order == CEPD.REPORT_KEYS,
              "AC-CEPD6d the json face is the pinned key order")
        check(missing == 3 and bad == 5 and no_publish == 5
              and EXPECTED_CRITERIA == 6,
              "AC-CEPD6e the CLI keeps its codes and six criteria")
    finally:
        _cleanup(directory)


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
    ac_cepd1()
    ac_cepd2()
    ac_cepd3()
    ac_cepd4()
    ac_cepd5()
    ac_cepd6()
    total = PASSES + FAILS
    print("SUITE %s %d/%d" % ("PASS" if not FAILS else "FAIL",
                              PASSES, total), flush=True)
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())