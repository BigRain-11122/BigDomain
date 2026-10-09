"""Daily reconciliation entry point (O-2026-0930-027 window-first item, R1186).

Thin wiring only (no-reinvent-wheel law): derive a dated evidence log
path under qa/, run the full product health-check runner
(reconcile_all.py) as a child process with that path as its tee target,
propagate the exit code, and print a one-line verdict for the OSLoop
daily round. All scenario logic stays inside reconcile_all.py; verdict
reading and the same-day closure path live in
docs/ops/reconcile-daily-runbook.md.

R1714 schema-drift sentinel (criteria AC-FS1..AC-FS6 pre-registered in
state/queue/tech.md before this code existed - honesty law): after the
full runner, run fingerprint_regen.py --check against the shipped
migration_chains.json and append its output to the same dated evidence
log behind a section marker. Daily exit aggregates: runner failure
propagates (sentinel still runs and is logged - a failed day must not
skip the drift check); a clean runner defers to the sentinel exit, so
any baseline drift fails the day. Default on, zero config knobs - the
sentinel is the whole point of daily-ization.

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

SENTINEL_MARKER = "--- sentinel: fingerprint-regen --check ---"


def evidence_path(stamp):
    path = os.path.join(QA, "reconcile-daily-%s.log" % stamp)
    n = 2
    while os.path.exists(path):
        path = os.path.join(QA, "reconcile-daily-%s-%d.log" % (stamp, n))
        n += 1
    return path


def sentinel_command():
    return [sys.executable, os.path.join(BASE, "fingerprint_regen.py"),
            "--chain", os.path.join(BASE, "migration_chains.json"),
            "--check"]


def run_sentinel(log_path):
    """AC-FS1: append the schema-drift sentinel section to the daily log.

    Returns the sentinel exit code. Append mode only - the runner
    section written earlier in the same file is never rewritten.
    """
    proc = subprocess.run(sentinel_command(), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=600, cwd=BASE)
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(SENTINEL_MARKER + "\n")
        out = (proc.stdout or "").strip()
        if out:
            handle.write(out + "\n")
        err = (proc.stderr or "").strip()
        if err:
            handle.write(err + "\n")
        handle.write("sentinel exit=%d\n" % proc.returncode)
    return proc.returncode


def main():
    stamp = datetime.now().strftime("%Y%m%d")
    os.makedirs(QA, exist_ok=True)
    path = evidence_path(stamp)
    code = subprocess.call(
        [sys.executable, os.path.join(BASE, "reconcile_all.py"), path])
    scode = run_sentinel(path)
    exit_code = code if code != 0 else scode
    verdict = "PASS" if exit_code == 0 else "FAIL"
    sentinel = "ok" if scode == 0 else "drift(exit=%d)" % scode
    print("RECONCILE-DAILY %s verdict=%s exit=%d log=%s "
          "runner_exit=%d sentinel=%s"
          % (stamp, verdict, exit_code, path, code, sentinel), flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
