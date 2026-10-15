# matrix_check_insert_R1999.py - run suite_matrix.py --check (the
# stale-doc byte-identity detector) and insert its section before
# the VERDICT line of the R1999 battery evidence log. Pure stdlib,
# pure ASCII source.
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
LOG = os.path.join(ROOT, "qa", "reconcile-all-R1999.log")


def main():
    proc = subprocess.run(
        [PY, os.path.join(ROOT, "src", "sandbox", "suite_matrix.py"),
         "--check"], capture_output=True, cwd=ROOT)
    body = proc.stdout.decode("utf-8", "replace")
    section = ("--- MATRIX --check: suite_matrix.py --check"
               " (stale-doc byte-identity detector, inserted before"
               " VERDICT) ---\nexit=%d\n%s"
               % (proc.returncode,
                  body if body.endswith("\n") else body + "\n"))
    with open(LOG, "rb") as h:
        raw = h.read()
    text = raw.decode("utf-8")
    marker = "VERDICT PASS (R1999 battery"
    idx = text.index(marker)
    text = text[:idx] + section + text[idx:]
    with open(LOG, "wb") as h:
        h.write(text.encode("utf-8"))
    print(section)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
