"""R2646 capture driver: the AC-EDWX suite through the SHIPPED capture
callable (two legs, identical criterion lines), the three parent export suites
as adjacent readings, and the second-wave limits measurement folded into the
same evidence file.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import evidence_capture as EC  # noqa: E402

ROUND = "R2646"
SUITE = "src/os/test_export_composed_landed_bom_precedence_second_wave.py"
EVIDENCE = os.path.join(
    REPO, "qa", "export-composed-landed-bom-precedence-second-wave-R2646.log")
LIMITS = os.path.join(BASE, "limits_export_composed_landed_next_R2643.py")
ADJACENT = [
    "src/os/test_export_composed_landed_bom_precedence.py",
    "src/os/test_export_composed_landed_wordspace.py",
    "src/os/test_export_composed_landed_face.py",
    "src/os/test_status_export_writer_dialect_wire.py",
]


def main():
    report = EC.capture(REPO, ROUND, SUITE, adjacent=ADJACENT,
                        evidence=EVIDENCE)
    with io.open(EVIDENCE, encoding="utf-8") as handle:
        payload = handle.read()
    limits = subprocess.run([sys.executable, LIMITS],
                            capture_output=True, text=True)
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.write("== limits rc=%d ==\n%s" % (limits.returncode,
                                                 limits.stdout))
    print("legs=%s identical=%s adjacent=%s fails=%s digest=%s verdict=%s"
          " limits=%d"
          % (report.get("legs"), report.get("identical"),
             report.get("adjacent"), report.get("fails"),
             report.get("digest"), report.get("verdict"),
             limits.returncode))
    ok = (report.get("verdict") in ("PASS", "CAPTURED")
          and report.get("identical")
          and not report.get("fails") and limits.returncode == 0)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
