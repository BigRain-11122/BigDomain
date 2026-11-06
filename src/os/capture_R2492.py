"""R2492 evidence capture: two identical legs plus three adjacent suites."""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SUITE = "src/os/test_relative_package_presence_refusal.py"
ADJACENT = [
    "src/os/test_relative_module_corpus_scope.py",
    "src/os/test_relative_module_existence_face.py",
    "src/os/test_publish_relative_package_identity.py",
]
OUT = "qa/relative-package-presence-refusal-R2492.log"


def run(path):
    done = subprocess.run([sys.executable, path], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return done.returncode, done.stdout.decode("utf-8", "replace")


def digest(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16].upper()


lines = ["EVIDENCE CAPTURE round=R2492 suite=%s legs=2" % SUITE]
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