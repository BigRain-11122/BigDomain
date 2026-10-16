# run_suite_R2010.py - R2010 suite double-run driver: runs the
# boundary-persist suite twice, captures stdout bytes both times
# (byte-identity check across the two runs), computes the sha16
# fingerprint, and writes the evidence log
# qa/showcase-statsboundary-R2010.log as UTF-8 LF (avoids the
# PS5.1 redirect UTF-16 dialect pitfall). Pure stdlib, ASCII
# source.
import hashlib
import io
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CMD = [sys.executable, os.path.join(
    "src", "sandbox", "ledger",
    "test_showcase_statsboundarypersist.py")]
OUT = os.path.join("qa", "showcase-statsboundary-R2010.log")


def run_once():
    proc = subprocess.run(CMD, cwd=ROOT, capture_output=True)
    return proc.returncode, proc.stdout


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    identical = out1 == out2
    sha16 = hashlib.sha256(out1).hexdigest()[:16]
    body = ("--- SUITE run 1 (AC-SSZB1..AC-SSZB7) ---\n"
            "exit=%d\n%s--- SUITE run 2 ---\nexit=%d\n%s"
            "--- DOUBLE-RUN ---\nidentical=%s sha16=%s "
            "bytes=%d\n"
            % (rc1, out1.decode("utf-8", "replace"),
               rc2, out2.decode("utf-8", "replace"),
               identical, sha16, len(out1)))
    with io.open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(body)
    tail = out1.decode("utf-8", "replace").splitlines()[-3:]
    for ln in tail:
        print(ln.encode("ascii", "replace").decode("ascii"))
    print("double-run identical=%s sha16=%s rc=%d/%d"
          % (identical, sha16, rc1, rc2))
    ok = rc1 == 0 and rc2 == 0 and identical
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
