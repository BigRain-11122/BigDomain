"""R2553 evidence driver: prove AC-PNDQ1..AC-PNDQ6 twice plus five adjacent.

The suite is run twice by the shipped capture callable and the two criterion
bodies must agree byte for byte before ONE evidence file is written. Five
adjacent probe suites must also be green.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import evidence_capture as EVC  # noqa: E402

SUITE = "src/os/test_probe_seam_name_binding_arm_mixed_residual_naming.py"

ADJACENT = (
    "src/os/test_probe_seam_name_binding_nested_arm_mixed_scope.py",
    "src/os/test_probe_seam_name_binding_nested_exhaustive_path.py",
    "src/os/test_probe_seam_name_binding_control_flow_guard_exhaustive.py",
    "src/os/test_probe_seam_dynamic_import_scope.py",
    "src/os/test_probe_seam_registry.py",
)

EVIDENCE = "qa/probe-seam-name-binding-arm-mixed-residual-naming-R2553.log"


def main():
    try:
        report = EVC.capture(ROOT, "R2553", SUITE, adjacent=ADJACENT,
                             evidence=EVIDENCE)
    except EVC.EvidenceError as exc:
        print("EVIDENCE REFUSED %s: %s" % (exc.code, exc.detail))
        return 2
    rows = [row for row in report["adjacent"]]
    print("EVIDENCE %s legs=%d identical=%s adjacent=%d fails=%d"
          % (os.path.basename(report["evidence"]), report["legs"],
             report["identical"], len(rows),
             len([row for row in rows if row["rc"] != 0])))
    for row in rows:
        print("  ADJACENT %s rc=%d %s"
              % (row["name"].split("/")[-1], row["rc"], row["suite_line"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())