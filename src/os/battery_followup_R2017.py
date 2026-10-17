# battery_followup_R2017.py - 34th-case takeover closeout:
# run the four post-RUNNER battery sections (matrix regen +
# --check, fingerprint --check, profile --daily --check plus
# the main profile --check, census --check only - the crashed
# round already re-anchored the baseline for R2016.log and the
# takeover battery log is Tee-written, so no re-freeze here),
# then append all sections + a VERDICT line to the takeover
# RUNNER evidence log. Same shape as battery_followup_R2016.py.
# Pure stdlib, pure ASCII source, single utf-8 LF appender.
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2017-3.log")

MATRIX_EVIDENCE = "qa/reconcile-all-R2017-3.log"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, cwd=ROOT)


def section(caption, proc):
    body = proc.stdout.decode("utf-8", "replace")
    if proc.stderr:
        err = proc.stderr.decode("utf-8", "replace")
        body += "--- stderr ---\n" + err
    return "%s\nexit=%d\n%s" % (
        caption, proc.returncode,
        body if body.endswith("\n") else body + "\n")


def main():
    chunks = []
    fails = []
    # 1. matrix regen then --check (byte-identity face)
    regen = run([PY, os.path.join(ROOT, "src", "sandbox",
                                  "suite_matrix.py"),
                 "--evidence", MATRIX_EVIDENCE])
    chunks.append(section(
        "--- MATRIX regen: suite_matrix.py --evidence %s ---"
        % MATRIX_EVIDENCE, regen))
    if regen.returncode != 0:
        fails.append("matrix regen")
    check = run([PY, os.path.join(ROOT, "src", "sandbox",
                                  "suite_matrix.py"),
                 "--evidence", MATRIX_EVIDENCE, "--check"])
    chunks.append(section(
        "--- MATRIX --check: byte-identical face ---", check))
    if check.returncode != 0:
        fails.append("matrix check")
    # 2. fingerprint sentinel
    fp = run([PY, os.path.join(ROOT, "src", "sandbox",
                               "fingerprint_regen.py"),
              "--chain", "src/sandbox/migration_chains.json",
              "--check"])
    chunks.append(section(
        "--- FINGERPRINT: fingerprint_regen.py --chain"
        " src/sandbox/migration_chains.json --check ---", fp))
    if fp.returncode != 0:
        fails.append("fingerprint")
    # 3. runner wall-time profile: daily face and main face
    prof = run([PY, os.path.join(ROOT, "src", "sandbox",
                                  "runner_profile.py"),
                "--daily", "--check"])
    chunks.append(section(
        "--- RUNNER_PROFILE: runner_profile.py --daily --check"
        " ---", prof))
    if prof.returncode != 0:
        fails.append("profile-daily")
    prof_main = run([PY, os.path.join(ROOT, "src", "sandbox",
                                      "runner_profile.py"),
                     "--check"])
    chunks.append(section(
        "--- RUNNER_PROFILE main: runner_profile.py --check ---",
        prof_main))
    if prof_main.returncode != 0:
        fails.append("profile-main")
    # 4. census: --check only. The crashed round's own fix
    # (re-anchor of reconcile-all-R2016.log) is already on
    # disk and the takeover log is Tee-written (never a flag
    # face), so the drift check alone is the honest section.
    chk = run([PY, os.path.join(HERE, "qa_writer_census.py"),
               "--check"])
    chunks.append(section(
        "--- qa-writer-census: --check (takeover log is Tee"
        " dialect, no re-freeze needed) ---", chk))
    if chk.returncode != 0:
        fails.append("census")
    verdict = ("VERDICT %s (R2017 takeover battery: matrix"
               " regen + check; fingerprint; profile daily +"
               " main; census check)"
               % ("PASS" if not fails else "FAIL"))
    chunks.append(verdict + "\n")
    with open(LOG, "ab") as h:
        for chunk in chunks:
            h.write(chunk.encode("utf-8"))
    print(verdict)
    for f in fails:
        print("FAILED SECTION: %s" % f)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
