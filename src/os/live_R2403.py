# live_R2403.py - one read-only live capture, one utf-8 LF writer.
# Reads the REAL evidence pile through runner_abort_face: every
# reconcile-all-*.log under qa/ is classified COMPLETE / ABORTED / UNREADABLE
# so the aborted suite is named where the pile used to carry silence, and the
# R2393 leg that died on ledger/test_apimarket_report_claims.py is shown as a
# fixture-level abort whose suite the registry-minus-body law derives. Writes
# exactly one file.
import hashlib
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import runner_abort_face as RAF

OUT = os.path.join(ROOT, "qa", "runner-abort-face-live-R2403.log")
MODULE = os.path.join(BASE, "runner_abort_face.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def pile():
    qa = os.path.join(ROOT, "qa")
    return [os.path.join(qa, name) for name in sorted(os.listdir(qa))
            if name.startswith("reconcile-all-") and name.endswith(".log")]


def main():
    lines = []
    before = digest(MODULE)
    labels = RAF.registry_labels(RUNNER)
    lines.append("REGISTRY suites=%d" % len(labels))
    counts = {"COMPLETE": 0, "ABORTED": 0, "UNREADABLE": 0}
    aborts = []
    for path in pile():
        report = RAF.check(path, RUNNER)
        counts[report["verdict"]] += 1
        if report["verdict"] == "ABORTED":
            aborts.append((report["evidence"], report["suite"],
                           report["seen"], report["registered"]))
    lines.append("PILE logs=%d COMPLETE=%d ABORTED=%d UNREADABLE=%d"
                 % (len(pile()), counts["COMPLETE"], counts["ABORTED"],
                    counts["UNREADABLE"]))
    for name, suite, seen, registered in aborts:
        lines.append("ABORT %s suite=%s seen=%d/%d"
                     % (name, suite, seen, registered))
    fixture_body = "\n".join([
        "PASS suite lobby exit=0 pass-lines=3 fail-lines=0 criteria=3 43.0s",
        "PASS suite ledger exit=0 pass-lines=3 fail-lines=0 criteria=3 0.4s",
        "  | FAIL AC-X1: still streaming when the 300s cap hit",
    ])
    fixture = RAF.analyse(fixture_body, labels)
    lines.append("FIXTURE-abort verdict=%s suite=%s missing=%d"
                 % (fixture["verdict"], fixture["suite"],
                    len(fixture["missing"])))
    complete_body = fixture_body + "\n" + (
        "RUNNER FAIL (2 failed assertions)")
    complete = RAF.analyse(complete_body, labels)
    lines.append("FIXTURE-verdict verdict=%s suite=%s code=%d"
                 % (complete["verdict"], complete["suite"],
                    complete["code"]))
    blind = RAF.analyse("no suite line at all here", labels)
    lines.append("FIXTURE-blind verdict=%s code=%d" % (blind["verdict"],
                                                       blind["code"]))
    after = digest(MODULE)
    lines.append("DIGEST before=%s after=%s same=%s"
                 % (before, after, before == after))
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    print("WROTE %s bytes=%d" % (OUT, len(body.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())