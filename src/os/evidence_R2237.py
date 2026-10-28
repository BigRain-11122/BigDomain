"""R2237 evidence writer: runs the category watch-conversion suite
twice and writes both legs through ONE python writer (no shell
redirection, the R2233 dialect lesson), then prints the criterion-line
sha16 so the double run can be compared byte for byte."""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(ROOT, "qa")
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
SUITE = "test_apimarket_categorywatchconversionmonths.py"
REL = os.path.join("qa",
                   "apimarket-categorywatchconversionmonths-R2237-%s.log")


def normalize(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text if text.endswith("\n") else text + "\n"


def main():
    digests = []
    for leg in ("a", "b"):
        proc = subprocess.run(
            [sys.executable, SUITE],
            cwd=LEDGER, capture_output=True)
        out = (proc.stdout or b"").decode("utf-8", "replace")
        err = (proc.stderr or b"").decode("utf-8", "replace")
        body = normalize(out + err)
        path = os.path.join(QA, os.path.basename(REL % leg))
        with open(path, "wb") as handle:
            handle.write(body.encode("utf-8"))
        crit = "\n".join(line for line in body.splitlines()
                         if line.startswith(("PASS AC-", "FAIL AC-")))
        digests.append(hashlib.sha256(
            crit.encode("utf-8")).hexdigest()[:16])
        print("LEG %s rc=%d bytes=%d %s"
              % (leg, proc.returncode, len(body.encode("utf-8")),
                 os.path.basename(path)))
        print(body.strip().splitlines()[-1])
    print("CRITERION_SHA16_A %s" % digests[0])
    print("CRITERION_SHA16_B %s" % digests[1])
    print("PAIR_IDENTICAL %r" % (digests[0] == digests[1]))
    return 0 if digests[0] == digests[1] else 1


if __name__ == "__main__":
    sys.exit(main())