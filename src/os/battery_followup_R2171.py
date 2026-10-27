# battery_followup_R2171.py - run the post-RUNNER battery sections
# (matrix regen+check, fingerprint --check, profile --daily --check,
# census --update-baseline then --check), then append all sections
# plus a VERDICT line to the R2171 RUNNER evidence log.
# Captions mirror the established follow-up format. Pure stdlib,
# pure ASCII source, single utf-8 LF writer.
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
EVIDENCE = "qa/reconcile-all-R2171.log"
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2171.log")

STEPS = [
    ("--- MATRIX regen + --check: suite_matrix.py --evidence"
     " %s ---" % EVIDENCE,
     [PY, os.path.join(ROOT, "src", "sandbox", "suite_matrix.py"),
      "--evidence", EVIDENCE]),
    ("--- FINGERPRINT: fingerprint_regen.py --chain"
     " src/sandbox/migration_chains.json --check ---",
     [PY, os.path.join(ROOT, "src", "sandbox",
                       "fingerprint_regen.py"),
      "--chain", "src/sandbox/migration_chains.json", "--check"]),
    ("--- RUNNER_PROFILE: runner_profile.py --daily --check ---",
     [PY, os.path.join(ROOT, "src", "sandbox", "runner_profile.py"),
      "--daily", "--check"]),
    ("--- qa-writer-census: --update-baseline then --check ---",
     [PY, os.path.join(HERE, "qa_writer_census.py"),
      "--update-baseline"]),
]


def main():
    if not os.path.exists(LOG):
        print("MISSING EVIDENCE %s" % EVIDENCE)
        return 2
    chunks = []
    fails = []
    for caption, cmd in STEPS[:3]:
        proc = subprocess.run(cmd, capture_output=True, cwd=ROOT)
        body = proc.stdout.decode("utf-8", "replace")
        chunks.append("%s\nexit=%d\n%s" % (
            caption, proc.returncode,
            body if body.endswith("\n") else body + "\n"))
        if proc.returncode != 0:
            fails.append(caption)
    upd = subprocess.run(STEPS[3][1], capture_output=True, cwd=ROOT)
    chk = subprocess.run([PY, os.path.join(HERE,
                                           "qa_writer_census.py"),
                          "--check"], capture_output=True, cwd=ROOT)
    body = (upd.stdout.decode("utf-8", "replace")
            + chk.stdout.decode("utf-8", "replace"))
    chunks.append("%s\nexit=%d\n%s" % (
        STEPS[3][0], chk.returncode,
        body if body.endswith("\n") else body + "\n"))
    if chk.returncode != 0:
        fails.append(STEPS[3][0])
    verdict = ("VERDICT %s (R2171 post-battery follow-up: matrix "
               "regen+check; fingerprint; profile; census "
               "update-baseline + check)"
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