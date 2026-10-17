# evidence_R2018.py - double-run stdout byte-identity evidence
# harness for the R2018 retract-persist suite (R1880 family law:
# subprocess byte capture + LF normalization, dialect prevention).
# Writes qa/showcase-statsmonthretract-R2018.log. Pure stdlib,
# pure ASCII source.
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_showcase_statsmonthretractpersist.py")
LOG = os.path.join(ROOT, "qa",
                   "showcase-statsmonthretract-R2018.log")


def run_once():
    proc = subprocess.run([sys.executable, SUITE],
                          capture_output=True, cwd=ROOT)
    return proc.returncode, proc.stdout


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    a = out1.replace(b"\r\n", b"\n")
    b = out2.replace(b"\r\n", b"\n")
    ident = (a == b)
    sha_a = hashlib.sha256(a).hexdigest()[:16]
    sha_b = hashlib.sha256(b).hexdigest()[:16]
    both_ok = (rc1 == 0 and rc2 == 0)
    verdict = both_ok and ident
    with open(LOG, "wb") as handle:
        handle.write(b"--- R2018 evidence: suite double-run"
                     b" byte-identity (LF-normalized) ---\n")
        handle.write(b"--- run 1 rc=%d sha16=%s ---\n"
                     % (rc1, sha_a.encode("ascii")))
        handle.write(a)
        handle.write(b"\n--- run 2 rc=%d sha16=%s ---\n"
                     % (rc2, sha_b.encode("ascii")))
        handle.write(b)
        handle.write(b"\n--- byte-identity: %s (bytes=%d) ---\n"
                     % (b"PASS" if ident else b"FAIL", len(a)))
        handle.write(b"--- VERDICT %s ---\n"
                     % (b"PASS" if verdict else b"FAIL"))
    print("run1 rc=%d sha16=%s" % (rc1, sha_a))
    print("run2 rc=%d sha16=%s" % (rc2, sha_b))
    print("byte-identity=%s verdict=%s log=%s"
          % (ident, verdict, LOG))
    return 0 if verdict else 2


if __name__ == "__main__":
    sys.exit(main())
