"""R2511 evidence capture: two identical legs plus three adjacent suites."""
import hashlib
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SUITE = "src/os/test_stamp_text_coverage.py"
ADJACENT = [
    "src/os/test_evidence_name_text_coverage.py",
    "src/os/test_artifact_disk_text_readability.py",
    "src/os/test_patterns_label_readability.py",
]
OUT = "qa/stamp-text-coverage-R2511.log"


def run(path):
    done = subprocess.run([sys.executable, path], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return done.returncode, done.stdout.decode("utf-8", "replace")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16].upper()


lines = ["EVIDENCE CAPTURE round=R2511 suite=%s legs=2" % SUITE]
digests = []
for leg in ("A", "B"):
    rc, out = run(SUITE)
    lines.append("== LEG %s rc=%d digest=%s" % (leg, rc, digest(out)))
    lines.extend(out.rstrip("\n").split("\n"))
    digests.append(digest(out))
    if "SUITE PASS" not in out or rc != 0:
        lines.append("SUITE FAIL")
        break
lines.append("== ADJACENT %d" % len(ADJACENT))
fails = 0
for path in ADJACENT:
    rc, out = run(path)
    verdict = [line for line in out.split("\n") if line.startswith("SUITE ")]
    tail = verdict[-1] if verdict else out.strip().split("\n")[-1]
    lines.append("== %s rc=%d %s" % (path, rc, tail))
    if rc != 0:
        fails += 1
lines.append("EVIDENCE identical=%s adjacent=%d fails=%d digest=%s"
             % (digests[0] == digests[-1], len(ADJACENT), fails, digests[0]))
text = "\n".join(lines) + "\n"
io.open(os.path.join(ROOT, OUT), "w", encoding="utf-8", newline="\n").write(text)
print(text)