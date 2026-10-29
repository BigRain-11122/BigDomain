"""Adjacent regression battery for the R2243 window.

The window changed only maintenance surfaces (state layout repair, fold
R593, archive append, export refresh), so it re-runs the suites that read
those surfaces: the logs toolkit, the archive integrity checks, the
evidence writer/naming pair and the export consistency checker. Writes
qa/regression-R2243.log through one python writer (UTF-8 LF, no shell
redirection).
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

SUITES = [
    ("os-logs-toolkit", os.path.join(BASE, "test_logs_toolkit.py")),
    ("os-ledger-archive", os.path.join(BASE, "test_ledger_archive.py")),
    ("os-ledger-lines", os.path.join(BASE, "test_ledger_lines.py")),
    ("os-evidence-writer", os.path.join(BASE, "test_evidence_writer.py")),
    ("os-run-identity", os.path.join(BASE, "test_run_identity.py")),
    ("os-export-consistency", os.path.join(BASE,
                                           "check_export_consistency.py")),
]


def main():
    lines = []
    failed = 0
    for label, script in SUITES:
        out = subprocess.run(
            [sys.executable, script], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = out.stdout.decode("utf-8", "replace").replace(
            "\r\n", "\n")
        tail = [ln for ln in text.splitlines()
                if ln.startswith(("SUITE ", "VERDICT ", "SUMMARY "))]
        verdict = tail[-1] if tail else "MISSING"
        lines.append("%s rc=%d %s" % (label, out.returncode, verdict))
        if out.returncode != 0:
            failed += 1
            for ln in text.splitlines():
                if ln.startswith("FAIL "):
                    lines.append("  " + ln)
    path = os.path.join(ROOT, "qa", "regression-R2243.log")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line, flush=True)
    print("REGRESSION %s (%d/%d green)"
          % ("PASS" if not failed else "FAIL",
             len(SUITES) - failed, len(SUITES)))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())