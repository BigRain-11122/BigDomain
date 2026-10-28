"""R2183: run four adjacent watch-family suites as a regression log."""

import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NAMES = ["test_apimarket_watchlist.py",
         "test_apimarket_watchalerts.py",
         "test_apimarket_watchconversion.py",
         "test_apimarket_listingdemand.py"]
LEDGER = os.path.join(BASE, "src", "sandbox", "ledger")


def main():
    ok = True
    lines = []
    for name in NAMES:
        proc = subprocess.run([sys.executable, os.path.join(LEDGER, name)],
                              cwd=BASE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        body = proc.stdout.replace(b"\r\n", b"\n").decode("utf-8", "replace")
        tails = [l for l in body.split("\n") if l.startswith("SUITE ")]
        lines.append("%s rc=%d %s" % (name, proc.returncode,
                                      tails[-1] if tails else "NO-VERDICT"))
        ok = ok and proc.returncode == 0
    blob = ("\n".join(lines) + "\n").encode("utf-8")
    with open(os.path.join(BASE, "qa", "regression-R2183.log"), "wb") as h:
        h.write(blob)
    sys.stdout.write(blob.decode("utf-8"))
    print("ALL-GREEN %r" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())