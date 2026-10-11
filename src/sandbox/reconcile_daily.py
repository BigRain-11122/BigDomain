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

R1733 daily profile step (criteria AC-PD1..AC-PD7 pre-registered in
state/queue/tech.md before this code existed): after the sentinel,
run runner_profile.py --daily --check (daily-baseline staleness
detector, R1715 daily variant) and append its output to the same dated
evidence log behind a section marker. Observation window: the profile
exit is recorded in the verdict line but never gates the daily exit
(PROFILE_OBSERVATION_WINDOW); promotion to a gating face is decided
at the drift-threshold revisit (seed wording: "zhuan-zheng window =
drift-threshold revisit"). Failed days still run and log the profile
step (same discipline as the sentinel).

R1848 writer-census sentinel step (criteria AC-WCD1..AC-WCD7
pre-registered in state/queue/tech.md before this code existed):
after the profile step, run qa_writer_census.py --check (R1841
writer-dialect drift detector) and append its output to the same dated
evidence log behind a section marker. Gating law: with the baseline
present (deployed R1841) any nonzero probe exit fails the day
(exit 2 = new non-tee dialect / class-migration FLAG, exit 3 = empty
evidence-dir refusal - both honest anomalies, zero silence); a
MISSING baseline file is an honest INFO face (recorded in the log and
verdict line, never gating) - the AC-WCB5 "probe not deployed"
refusal translated into the watch-duty face per the seed ruling.
Daily exit aggregates: runner failure propagates first, then the
fingerprint sentinel, then this census step (failed days still run
and log every step - same discipline as AC-FS2).

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
import time
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.normpath(os.path.join(BASE, "..", "..", "qa"))

SENTINEL_MARKER = "--- sentinel: fingerprint-regen --check ---"
PROFILE_MARKER = "--- profile: runner-profile --daily --check ---"
CENSUS_MARKER = "--- census: qa-writer-census --check ---"
CENSUS_BASELINE = "writer-census-baseline.json"

# AC-PD2: observation window - profile exit is recorded, never gating.
# Promotion to a gating face is a deliberate flip at the drift-threshold
# revisit (tech.md seed: promotion window = revisit decides).
PROFILE_OBSERVATION_WINDOW = True


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


def profile_command():
    return [sys.executable, os.path.join(BASE, "runner_profile.py"),
            "--daily", "--check"]


def census_command():
    # qa_writer_census.py lives in src/os/ (R1836 probe home), the
    # baseline defaults to <dir>/writer-census-baseline.json inside
    # the probe itself - same QA dir this wrapper writes evidence to.
    return [sys.executable,
            os.path.join(os.path.dirname(BASE), "os",
                         "qa_writer_census.py"),
            "--check", "--dir", QA]


def census_baseline_path():
    return os.path.join(QA, CENSUS_BASELINE)


def run_census(log_path):
    """AC-WCD1..AC-WCD2: append the writer-census drift section to the
    daily log. Returns (gating_exit, verdict_label).

    Baseline missing (AC-WCD2) -> zero subprocess calls, honest INFO
    section, (0, "not-deployed") - recorded, never gating (AC-WCB5
    "probe not deployed" refusal translated per the seed ruling).
    Baseline present (AC-WCD1) -> subprocess --check; exit 0 -> ok;
    any nonzero exit is an honest day-failing anomaly (2 = drift FLAG,
    3 = empty-dir refusal). Elapsed mirrors the sentinel tail line
    (R1737 AC-SN1 precedent). Append mode only - earlier sections in
    the same file are never rewritten.
    """
    t0 = time.monotonic()
    if not os.path.exists(census_baseline_path()):
        with open(log_path, "a", encoding="utf-8", newline="\n") as h:
            h.write(CENSUS_MARKER + "\n")
            h.write("census baseline missing: %s (probe not deployed"
                    " - honest INFO, recorded, not gating)\n"
                    % CENSUS_BASELINE)
            h.write("census not-deployed (recorded, not gating)\n")
        return 0, "not-deployed"
    proc = subprocess.run(census_command(), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=600, cwd=BASE)
    elapsed = time.monotonic() - t0
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(CENSUS_MARKER + "\n")
        out = (proc.stdout or "").strip()
        if out:
            handle.write(out + "\n")
        err = (proc.stderr or "").strip()
        if err:
            handle.write(err + "\n")
        handle.write("census exit=%d elapsed=%.1fs\n"
                     % (proc.returncode, elapsed))
    if proc.returncode == 0:
        return 0, "ok"
    if proc.returncode == 3:
        return 3, "refusal(exit=3)"
    if proc.returncode == 2:
        return 2, "drift(exit=2)"
    return proc.returncode, "anomaly(exit=%d)" % proc.returncode


def run_sentinel(log_path):
    """AC-FS1: append the schema-drift sentinel section to the daily log.

    Returns the sentinel exit code. Append mode only - the runner
    section written earlier in the same file is never rewritten.

    R1737 (AC-SN1, pre-registered in tech.md before this change): the
    tail line now carries the sentinel subprocess elapsed time
    ("sentinel exit=N elapsed=X.Xs") so the daily profile face
    (runner_profile.py --daily) can consume the sentinel segment
    duration; the marker line, captured output lines and the
    RECONCILE-DAILY verdict line are unchanged.
    """
    t0 = time.monotonic()
    proc = subprocess.run(sentinel_command(), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=600, cwd=BASE)
    elapsed = time.monotonic() - t0
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(SENTINEL_MARKER + "\n")
        out = (proc.stdout or "").strip()
        if out:
            handle.write(out + "\n")
        err = (proc.stderr or "").strip()
        if err:
            handle.write(err + "\n")
        handle.write("sentinel exit=%d elapsed=%.1fs\n"
                     % (proc.returncode, elapsed))
    return proc.returncode


def run_profile_step(log_path):
    """AC-PD1: append the daily-profile check section to the daily log.

    Returns the profile exit code. Append mode only - earlier sections
    written in the same file are never rewritten. Observation window
    (AC-PD2): the caller records this exit but never lets it gate the
    daily verdict while PROFILE_OBSERVATION_WINDOW is True.
    """
    proc = subprocess.run(profile_command(), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=600, cwd=BASE)
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(PROFILE_MARKER + "\n")
        out = (proc.stdout or "").strip()
        if out:
            handle.write(out + "\n")
        err = (proc.stderr or "").strip()
        if err:
            handle.write(err + "\n")
        handle.write("profile exit=%d (observation-window: recorded, "
                     "not gating)\n" % proc.returncode)
    return proc.returncode


def main():
    stamp = datetime.now().strftime("%Y%m%d")
    os.makedirs(QA, exist_ok=True)
    path = evidence_path(stamp)
    code = subprocess.call(
        [sys.executable, os.path.join(BASE, "reconcile_all.py"), path])
    scode = run_sentinel(path)
    pcode = run_profile_step(path)
    ccode, clabel = run_census(path)
    exit_code = code if code != 0 else (scode if scode != 0 else ccode)
    verdict = "PASS" if exit_code == 0 else "FAIL"
    sentinel = "ok" if scode == 0 else "drift(exit=%d)" % scode
    profile = "ok" if pcode == 0 else "flag(exit=%d)" % pcode
    print("RECONCILE-DAILY %s verdict=%s exit=%d log=%s "
          "runner_exit=%d sentinel=%s profile=%s census=%s"
          % (stamp, verdict, exit_code, path, code, sentinel, profile,
             clabel), flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
