"""R1953 evidence driver: sistercity persist suite double-run
determinism probe (the R1880 capture-dialect family - a python
driver captures child stdout and writes the evidence file
single-writer LF, so no PS-capture CRLF dialect can touch it).
Runs the suite twice, requires exit 0/0 and byte-identical
stdout, records both sha16 digests, and writes the canonical
suite section of qa/sistercity-persist-R1953.log. Pure ASCII,
stdlib only."""

import hashlib
import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    "..", ".."))
SUITE = os.path.join(BASE, "src", "sandbox", "ledger",
                     "test_sistercity_persist.py")
OUT = os.path.join(BASE, "qa", "sistercity-persist-R1953.log")


def run_once():
    proc = subprocess.run([sys.executable, SUITE], cwd=BASE,
                          capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    same = out1 == out2
    sha1 = hashlib.sha256(out1.encode("utf-8")).hexdigest()[:16]
    sha2 = hashlib.sha256(out2.encode("utf-8")).hexdigest()[:16]
    verdict = (rc1 == 0 and rc2 == 0 and same)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("--- [1] suite double-run (sistercity persist,"
                 " R1953; python driver capture, LF single-writer)"
                 " ---\n")
        fh.write(out1 if out1.endswith("\n") else out1 + "\n")
        fh.write("double-run: rc=%d/%d stdout-byte-identical=%s"
                 " sha16=%s/%s\n"
                 % (rc1, rc2, str(same).lower(), sha1, sha2))
        fh.write("verdict %s\n"
                 % ("PASS" if verdict else "FAIL"))
    print("rc=%d/%d identical=%s sha16=%s/%s verdict=%s"
          % (rc1, rc2, str(same).lower(), sha1, sha2,
             "PASS" if verdict else "FAIL"), flush=True)
    sys.exit(0 if verdict else 2)


if __name__ == "__main__":
    main()
