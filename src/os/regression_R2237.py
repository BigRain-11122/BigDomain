"""R2237 adjacent regression runner: six neighbouring watch and
conversion suites, written through one python writer to
qa/regression-R2237.log (no shell redirection)."""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
QA = os.path.join(ROOT, "qa")
LOG = os.path.join(QA, "regression-R2237.log")

SUITES = [
    "test_apimarket_categorywatchmonths.py",
    "test_apimarket_marketconversionmonths.py",
    "test_apimarket_watchconversion.py",
    "test_apimarket_marketwatchmonths.py",
    "test_apimarket_sellerwatchmonths.py",
    "test_apimarket_buyerwatchmonths.py",
]


def main():
    lines = []
    failed = 0
    for suite in SUITES:
        proc = subprocess.run([sys.executable, suite], cwd=LEDGER,
                              capture_output=True)
        out = (proc.stdout or b"").decode("utf-8", "replace")
        err = (proc.stderr or b"").decode("utf-8", "replace")
        body = out + err
        summary = ""
        for line in body.splitlines():
            if line.startswith("SUITE "):
                summary = line.strip()
        if proc.returncode != 0:
            failed += 1
            summary = summary or "SUITE rc=%d" % proc.returncode
        lines.append("%s rc=%d %s"
                     % (suite, proc.returncode, summary))
        print(lines[-1])
    text = "\n".join(lines) + "\n"
    text = text.replace("\r\n", "\n")
    with open(LOG, "wb") as handle:
        handle.write(text.encode("utf-8"))
    print("REGRESSION %d/%d green"
          % (len(SUITES) - failed, len(SUITES)))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())