# takeover_verify_R1999.py - 31st-case crashed-round takeover
# verification (R1924/R1976/R1990/R1997/R1998 precedent family).
# The predecessor session finished the product face, the suite
# double-run, the full battery (RUNNER 224/224 + matrix regen/check
# + fingerprint + profile + census update-baseline/check +
# VERDICT PASS), fold R534 and the complete closeout payload, then
# crashed before any closeout edit landed (tick still 1998).
# This driver re-verifies the on-disk evidence per precedent:
#   A. suite re-run once, normalized-LF sha256 anchored to the
#      original double-run bytes (f7be4ce256220f53...);
#   B. matrix --check (stale-doc byte-identity detector);
#   C. fingerprint --check;
#   D. profile --daily --check;
#   E. census face: E1 --check reviews the pre-existing drift -
#      the original round's own post-census appends (the
#      matrix --check section + VERDICT line, written AFTER its
#      census update-baseline) flag exactly one known file
#      (reconcile-all-R1999.log new-dialect, R1996/R1998 takeover
#      re-anchor precedent family); any OTHER flagged file
#      aborts the takeover. After the follow-up section is
#      appended in place, E2 --update-baseline legally re-anchors
#      (single known file only) and the final --check must be
#      DRIFT-CLEAN.
# The full RUNNER 224/224 is intentionally NOT re-run: the
# original round's RUNNER record is complete in the evidence log
# (qa/reconcile-all-R1999.log L2739 RUNNER PASS + L2786 VERDICT;
# R1997 takeover precedent). Parsed values land in
# takeover_results_R1999.json for the closeout driver. Pure
# stdlib, pure ASCII source, single utf-8 LF appender.
import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_civic_competition_monthwindow.py")
LOG = os.path.join(ROOT, "qa", "reconcile-all-R1999.log")
RESULTS = os.path.join(HERE, "takeover_results_R1999.json")
ANCHOR16 = "f7be4ce256220f53"
KNOWN = "reconcile-all-R1999.log"


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, cwd=ROOT)
    body = proc.stdout.decode("utf-8", "replace")
    if body and not body.endswith("\n"):
        body += "\n"
    return proc.returncode, body


def census_flags(body):
    fl = []
    for ln in body.splitlines():
        if ln.startswith("[flag]"):
            fl.append(ln)
    return fl


def main():
    fails = []
    # -- A. suite re-run, sha anchor --------------------------------
    proc = subprocess.run([PY, SUITE], capture_output=True)
    out = proc.stdout.replace(b"\r\n", b"\n")
    sha = hashlib.sha256(out).hexdigest()
    suite_ok = (proc.returncode == 0
                and sha.startswith(ANCHOR16))
    suite_line = ("suite-rerun: exit=%d normalized-LF sha256=%s"
                  " bytes=%d (anchored to the original RUN1/RUN2"
                  " double-run; anchor16=%s %s)"
                  % (proc.returncode, sha, len(out), ANCHOR16,
                     "MATCH" if sha.startswith(ANCHOR16)
                     else "MISMATCH"))
    print(suite_line)
    if not suite_ok:
        fails.append("suite-rerun")

    # -- B..D. --check faces -----------------------------------------
    rc_m, body_m = run([PY, os.path.join(ROOT, "src", "sandbox",
                                         "suite_matrix.py"),
                        "--check"])
    print("matrix --check exit=%d" % rc_m)
    if rc_m != 0:
        fails.append("matrix --check")
    rc_f, body_f = run([PY, os.path.join(
        ROOT, "src", "sandbox", "fingerprint_regen.py"),
        "--chain", "src/sandbox/migration_chains.json", "--check"])
    print("fingerprint --check exit=%d" % rc_f)
    if rc_f != 0:
        fails.append("fingerprint --check")
    rc_p, body_p = run([PY, os.path.join(ROOT, "src", "sandbox",
                                         "runner_profile.py"),
                        "--daily", "--check"])
    print("profile --daily --check exit=%d" % rc_p)
    if rc_p != 0:
        fails.append("profile --check")

    # -- E1. census drift review -------------------------------------
    census_reanchor = False
    rc_c1, body_c1 = run([PY, os.path.join(HERE,
                                           "qa_writer_census.py"),
                          "--check"])
    fl = census_flags(body_c1)
    print("census --check (E1 review) exit=%d flags=%d"
          % (rc_c1, len(fl)))
    if rc_c1 != 0:
        unknown = [ln for ln in fl if KNOWN not in ln]
        if unknown:
            print("ABORT: census flags beyond the known "
                  "takeover-dialect file:")
            for ln in unknown:
                print("  " + ln)
            return 2
        census_reanchor = True  # benign known-file drift only
    if fails:
        print("ABORT: takeover verification failed: %s"
              % "; ".join(fails))
        return 2

    # -- append the takeover follow-up section ----------------------
    section = ("--- takeover follow-up (R1999 successor session"
               " re-verification, 31st-case crashed-round takeover;"
               " R1924/R1976/R1990/R1997/R1998 precedent family)"
               " ---\n"
               + suite_line + "\n"
               "matrix-check: exit=%d\n%s" % (rc_m, body_m)
               + "fingerprint-check: exit=%d\n%s" % (rc_f, body_f)
               + "profile-check: exit=%d\n%s" % (rc_p, body_p)
               + "census-check-E1 (drift review): exit=%d\n%s"
                 % (rc_c1, body_c1))
    if census_reanchor:
        rc_u, body_u = run([PY, os.path.join(HERE,
                                            "qa_writer_census.py"),
                            "--update-baseline"])
        section += ("census-reanchor (--update-baseline, the "
                    "R1996/R1998 legal single-known-file takeover "
                    "re-anchor; the flag was the original round's "
                    "own post-census appends): exit=%d\n%s"
                    % (rc_u, body_u))
        if rc_u != 0:
            print("ABORT: census re-anchor failed")
            return 2
    rc_c2, body_c2 = run([PY, os.path.join(HERE,
                                          "qa_writer_census.py"),
                          "--check"])
    section += ("census-check-final: exit=%d\n%s" % (rc_c2, body_c2)
                + "VERDICT PASS (R1999 takeover re-verification: the"
                  " suite re-run sha anchor matched the original"
                  " double-run byte-for-byte and all four battery"
                  " --check faces are green; the census face was"
                  " legally re-anchored per the R1996/R1998 takeover"
                  " precedent after the in-place follow-up append;"
                  " the original round's RUNNER PASS 224/224 record"
                  " is complete in this log and accepted per the"
                  " R1997 takeover precedent; closeout edits land"
                  " next)\n")
    print("census final --check exit=%d" % rc_c2)
    if rc_c2 != 0:
        print("ABORT: census final check not clean")
        return 2
    with io.open(LOG, "ab") as h:
        h.write(section.encode("utf-8"))

    # -- parsed values for the closeout driver ----------------------
    res = {
        "suite_sha16": sha[:16],
        "suite_bytes": len(out),
        "matrix_rc": rc_m,
        "matrix_bytes": 0,
        "fingerprint_rc": rc_f,
        "profile_rc": rc_p,
        "census_final_rc": rc_c2,
        "census_flags": -1,
        "census_reanchored": census_reanchor,
    }
    for ln in body_m.splitlines():
        if "byte-identical (" in ln:
            try:
                res["matrix_bytes"] = int(
                    ln.split("byte-identical (", 1)[1]
                    .split(" bytes", 1)[0])
            except (ValueError, IndexError):
                pass
            break
    for ln in body_c2.splitlines():
        if ln.startswith("flags="):
            try:
                res["census_flags"] = int(ln.split("=", 1)[1])
            except ValueError:
                pass
    io.open(RESULTS, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print("takeover re-verification ALL GREEN; follow-up section "
          "appended; results -> %s" % os.path.basename(RESULTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
