"""R2633 capture driver: the AC-EDMJ suite through the SHIPPED capture
callable (two legs, identical criterion lines), the adjacent matrix suites,
and the after-fix limit measurement folded into the same evidence file.
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

ROUND = "R2633"
SUITE = "src/os/test_suite_matrix_reconcile_second_table_separator.py"
EVIDENCE = os.path.join(
    REPO, "qa", "suite-matrix-reconcile-second-table-separator-R2633.log")
LIMITS = os.path.join(
    BASE, "limits_matrix_reconcile_second_table_separator_R2633.py")
ADJACENT = [
    "src/os/test_suite_matrix_reconcile_row_membership.py",
    "src/os/test_suite_matrix_reconcile_row_shape.py",
    "src/os/test_suite_matrix_reconcile_fence_table.py",
    "src/os/test_suite_matrix_reconcile_fence_rows.py",
    "src/os/test_suite_matrix_reconcile_table_shape.py",
    "src/os/test_suite_matrix_reconcile_shape.py",
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
    ok = (report.get("verdict") in ("PASS", "CAPTURED") and report.get("identical")
          and not report.get("fails") and limits.returncode == 0)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
