"""R2212 adjacent regression: run the feed, month-axis and stats suites
that share the seam this window touched, and write one transcript with
an in-process utf-8 LF single writer."""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")

SUITES = [
    "test_apimarket_marketfeed.py",
    "test_apimarket_feeddev.py",
    "test_apimarket_marketfeed_listing.py",
    "test_apimarket_ratingmonths.py",
    "test_apimarket_questionmonths.py",
    "test_apimarket_sellermonths.py",
    "test_apimarket_categorywatchmonths.py",
    "test_apimarket_marketrelistmonths.py",
    "test_apimarket_marketstats.py",
]


def main():
    lines = []
    failed = []
    for name in SUITES:
        path = os.path.join(LEDGER, name)
        if not os.path.exists(path):
            lines.append("MISSING suite %s" % name)
            failed.append(name)
            continue
        proc = subprocess.run([sys.executable, path], cwd=LEDGER,
                              capture_output=True)
        body = (proc.stdout + proc.stderr).replace(b"\r\n", b"\n")
        tail = [l for l in body.decode("utf-8", "replace").splitlines()
                if l.startswith("SUITE ") or l.startswith("FAIL ")]
        verdict = "PASS" if proc.returncode == 0 else "FAIL"
        lines.append("%s suite %s rc=%d %s"
                     % (verdict, name, proc.returncode,
                        " | ".join(tail) if tail else "no-summary"))
        if proc.returncode != 0:
            failed.append(name)
        print(lines[-1], flush=True)
    lines.append("ADJACENT %d/%d green"
                 % (len(SUITES) - len(failed), len(SUITES)))
    body = ("\n".join(lines) + "\n").encode("utf-8")
    out = os.path.join(ROOT, "qa", "regression-R2212.log")
    with open(out, "wb") as handle:
        handle.write(body)
    print("wrote %s size=%d sha256=%s"
          % (out, len(body), hashlib.sha256(body).hexdigest()))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())