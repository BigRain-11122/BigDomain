# battery_followup_R2010.py - run the four post-RUNNER battery
# sections (matrix regen + --check, fingerprint --check, profile
# --daily --check, census --update-baseline then --check), then
# append all sections + a VERDICT line to the RUNNER evidence
# log. Same shape as battery_followup_R1999.py. Pure stdlib,
# pure ASCII source, single utf-8 LF appender.
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2010.log")

MATRIX_EVIDENCE = "qa/reconcile-all-R2010.log"


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
    # 3. runner wall-time profile
    prof = run([PY, os.path.join(ROOT, "src", "sandbox",
                                 "runner_profile.py"),
                "--daily", "--check"])
    chunks.append(section(
        "--- RUNNER_PROFILE: runner_profile.py --daily --check"
        " ---", prof))
    if prof.returncode != 0:
        fails.append("profile")
    # 4. census: the two new R2010 evidence files land in the
    # baseline (legal re-anchor, R1996/R1998/R2009 precedent),
    # then the drift check
    upd = run([PY, os.path.join(HERE, "qa_writer_census.py"),
               "--update-baseline"])
    chk = run([PY, os.path.join(HERE, "qa_writer_census.py"),
               "--check"])
    body = (upd.stdout.decode("utf-8", "replace")
            + chk.stdout.decode("utf-8", "replace"))
    chunks.append("--- qa-writer-census: --update-baseline then"
                  " --check ---\nexit=%d\n%s"
                  % (chk.returncode,
                     body if body.endswith("\n") else body + "\n"))
    if chk.returncode != 0:
        fails.append("census")
    verdict = ("VERDICT %s (R2010 battery: matrix regen + check;"
               " fingerprint; profile; census update-baseline"
               " + check)"
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
