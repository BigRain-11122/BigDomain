"""R2730 evidence driver: prove the shape-typing face twice, then land the log.

Runs the pre-registered suite twice through its own process, proves the two
legs are byte-identical, runs five adjacent probe suites, measures the SAME
live fixture on BOTH readers (the R2725 face and this face), and only then
composes the evidence text and lands it through the shipped capture callable
so a red capture can never become an artifact. ASCII source, stdlib only.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(SRC, "sandbox"))

import evidence_capture_precedence_shape_typing as STP  # noqa
import evidence_capture_precedence_unknown_shape as WSU  # noqa
import evidence_utf8_capture as EUC  # noqa

SUITE = "test_evidence_capture_precedence_shape_typing.py"
ADJACENT = ("test_evidence_capture_precedence_unknown_shape.py",
            "test_evidence_capture_precedence_derived.py",
            "test_evidence_capture_compound_refusal.py",
            "test_evidence_capture_tail_guard.py",
            "test_evidence_utf8_capture_bom_guard.py")
TARGET = os.path.join(ROOT, "qa",
                      "evidence-capture-precedence-shape-typing-R2730b.log")
LIVE = os.path.join(ROOT, "qa", "reconcile-all-R2725.log")


def run(name):
    proc = subprocess.Popen([sys.executable, os.path.join(BASE, name)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            cwd=BASE)
    out, _ = proc.communicate()
    return proc.returncode, out


def main():
    lines = ["# R2730 evidence-capture-precedence-shape-typing",
             "# module src/os/evidence_capture_precedence_shape_typing.py",
             "# suite src/os/test_evidence_capture_precedence_shape_typing.py",
             "# criteria AC-EPTYP1..AC-EPTYP6 pinned at R2725 tech.md:697"]
    legs = []
    leg_green = True
    for index in (1, 2):
        rc, out = run(SUITE)
        digest = EUC.digest(out)
        legs.append((index, rc, digest, len(out)))
        tail = [line for line in out.decode("utf-8").splitlines()
                if line.startswith("SUITE ")]
        verdict = tail[0] if tail else "SUITE missing"
        if rc != 0 or "SUITE PASS" not in verdict:
            leg_green = False
        lines.append("LEG %d rc=%d bytes=%d sha256=%s %s"
                     % (index, rc, len(out), digest, verdict))
    identical = legs[0][2] == legs[1][2]
    lines.append("DIGEST identical=%s legs=%d" % (identical, len(legs)))
    fails = 0
    for name in ADJACENT:
        rc, out = run(name)
        tail = [line for line in out.decode("utf-8").splitlines()
                if line.startswith("SUITE ")]
        verdict = tail[0] if tail else "SUITE missing"
        if rc != 0 or "SUITE PASS" not in verdict:
            fails += 1
        lines.append("ADJACENT %s rc=%d %s" % (name, rc, verdict))
    lines.append("ADJACENT suites=%d fails=%d" % (len(ADJACENT), fails))
    if os.path.isfile(LIVE):
        raw = open(LIVE, "rb").read()
        mine = STP.report_of(raw)
        theirs = WSU.report_of(raw)
        lines.append("LIVE fixture=%s bytes=%d digest=%s mine=%s theirs=%s"
                     % (os.path.basename(LIVE), len(raw), EUC.digest(raw),
                        "ACCEPT" if mine is None else mine["code"],
                        "ACCEPT" if theirs is None else theirs["code"]))
    else:
        lines.append("LIVE fixture=absent")
    ok = leg_green and identical and fails == 0
    lines.append("VERDICT %s" % ("SUITE PASS 6/6 twice" if ok else "RED"))
    text = ("\n".join(lines) + "\n").encode("utf-8")
    landed = STP.capture(TARGET, text)
    print("\n".join(lines))
    print("LANDED %s bytes=%d sha256=%s verdict=%s"
          % (landed["target"], landed["bytes"], landed["sha256"],
             landed["verdict"]))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
