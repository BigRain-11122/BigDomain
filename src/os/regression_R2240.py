"""Adjacent regression battery for the R2240 window.

Runs four neighbouring apimarket month-axis suites and writes
qa/regression-R2240.log through one python writer (UTF-8 LF, no shell
redirection).
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")

SUITES = [
    "test_apimarket_sellerpricecadencemonths.py",
    "test_apimarket_sellerwatchmonths.py",
    "test_apimarket_sellerquestionmonths.py",
    "test_apimarket_marketwatchmonths.py",
]


def main():
    lines = []
    failed = 0
    for name in SUITES:
        out = subprocess.run(
            [sys.executable, os.path.join(LEDGER, name)],
            cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        text = out.stdout.decode("utf-8", "replace").replace(
            "\r\n", "\n")
        suite = [ln for ln in text.splitlines()
                 if ln.startswith("SUITE ")]
        verdict = suite[-1] if suite else "MISSING"
        lines.append("%s rc=%d %s" % (name, out.returncode, verdict))
        if out.returncode != 0:
            failed += 1
            for ln in text.splitlines():
                if ln.startswith("FAIL "):
                    lines.append("  " + ln)
    path = os.path.join(ROOT, "qa", "regression-R2240.log")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line, flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())