"""Daily reconciliation entry point (O-2026-0930-027 window-first item, R1186).

Thin wiring only (no-reinvent-wheel law): derive a dated evidence log
path under qa/, run the full product health-check runner
(reconcile_all.py) as a child process with that path as its tee target,
propagate the exit code, and print a one-line verdict for the OSLoop
daily round. All scenario logic stays inside reconcile_all.py; verdict
reading and the same-day closure path live in
docs/ops/reconcile-daily-runbook.md.

Same-day reruns never overwrite earlier evidence: an existing path gets
a -2, -3 ... suffix.

Usage:
    python reconcile_daily.py

Run under the same full-assembly python used for reconcile_all.py
(see the interpreter note in reconcile_all.py's docstring).
"""

import os
import subprocess
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.normpath(os.path.join(BASE, "..", "..", "qa"))


def evidence_path(stamp):
    path = os.path.join(QA, "reconcile-daily-%s.log" % stamp)
    n = 2
    while os.path.exists(path):
        path = os.path.join(QA, "reconcile-daily-%s-%d.log" % (stamp, n))
        n += 1
    return path


def main():
    stamp = datetime.now().strftime("%Y%m%d")
    os.makedirs(QA, exist_ok=True)
    path = evidence_path(stamp)
    code = subprocess.call(
        [sys.executable, os.path.join(BASE, "reconcile_all.py"), path])
    verdict = "PASS" if code == 0 else "FAIL"
    print("RECONCILE-DAILY %s verdict=%s exit=%d log=%s"
          % (stamp, verdict, code, path), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
