# battery_followup_R2264.py - run the post-RUNNER battery sections
# (matrix regen+check, fingerprint --check, profile --daily --check,
# census re-freeze + check), append them to the R2264 evidence log,
# then prove the whole log is single-dialect utf-8 LF with no BOM.
# Same shape as battery_followup_R2262.py: every captured body is
# CRLF-normalized before it is appended and the census runs LAST so
# the log it measures is already complete (the R2262 defect).
# Pure stdlib, pure ASCII source, single utf-8 LF writer.
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
EVIDENCE = "qa/reconcile-all-R2264.log"
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2264.log")

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
]


def clean(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def run_step(caption, cmd):
    proc = subprocess.run(cmd, capture_output=True, cwd=ROOT)
    body = clean(proc.stdout.decode("utf-8", "replace"))
    if not body.endswith("\n"):
        body += "\n"
    return "%s\nexit=%d\n%s" % (caption, proc.returncode, body)


def eol_state(path):
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8", "replace")
    crlf = text.count("\r\n")
    bare = text.count("\r") - crlf
    bom = raw.startswith(b"\xef\xbb\xbf")
    return crlf, bare, bom, len(raw)


def main():
    if not os.path.exists(LOG):
        print("MISSING EVIDENCE %s" % EVIDENCE)
        return 2
    chunks = []
    fails = []
    for caption, cmd in STEPS:
        chunk = run_step(caption, cmd)
        chunks.append(chunk)
        if "exit=%d" % 0 not in chunk.split("\n")[1]:
            fails.append(caption)
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(chunks))
    cap = ("--- qa-writer-census: --update-baseline then --check"
           " (last, so this log is complete) ---")
    upd = subprocess.run([PY, os.path.join(HERE, "qa_writer_census.py"),
                          "--update-baseline"], capture_output=True, cwd=ROOT)
    chk = subprocess.run([PY, os.path.join(HERE, "qa_writer_census.py"),
                          "--check"], capture_output=True, cwd=ROOT)
    body = clean(upd.stdout.decode("utf-8", "replace")
                 + chk.stdout.decode("utf-8", "replace"))
    if not body.endswith("\n"):
        body += "\n"
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s\nexit=%d\n%s" % (cap, chk.returncode, body))
    if chk.returncode != 0:
        fails.append(cap)
    crlf, bare, bom, size = eol_state(LOG)
    eol_ok = crlf == 0 and bare == 0 and not bom
    if not eol_ok:
        fails.append("eol-self-check")
    verdict = "PASS" if not fails else "FAIL"
    tail = ("--- VERDICT R2264: %s (failing sections: %s) eol crlf=%d"
            " bare_cr=%d bom=%s bytes=%d ---\n"
            % (verdict, ", ".join(fails) if fails else "none",
               crlf, bare, bom, size))
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(tail)
    print("".join(chunks) + body + tail)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())