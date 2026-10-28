"""Adjacent question-family regression for the R2234 window."""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")

SUITES = ["test_apimarket_questionmonths.py",
          "test_apimarket_sellerquestionmonths.py",
          "test_apimarket_buyeranswerwait.py",
          "test_apimarket_categoryquestionmonths.py"]


def main():
    path = os.path.join(ROOT, "qa", "regression-R2234.log")
    lines = []
    bad = 0
    for name in SUITES:
        out = subprocess.run(
            [sys.executable, os.path.join(LEDGER, name)],
            cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        text = out.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        verdict = [ln for ln in text.splitlines()
                   if ln.startswith("SUITE ")] or ["SUITE MISSING"]
        lines.append("%s rc=%d %s" % (name, out.returncode, verdict[-1]))
        if out.returncode != 0:
            bad += 1
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line, flush=True)
    print("ADJACENT %d/%d" % (len(SUITES) - bad, len(SUITES)), flush=True)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())