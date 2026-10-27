"""R2171: write the price-volatility suite evidence with one bare-LF
UTF-8 writer (never a shell redirection, whose dialect trips the census),
then verify both files classify as clean."""

import io
import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LEDGER = os.path.join(BASE, "src", "sandbox", "ledger")
SUITE = os.path.join(LEDGER, "test_apimarket_pricevolatility.py")
QA = os.path.join(BASE, "qa")


def run_once(name):
    proc = subprocess.run([sys.executable, SUITE], cwd=LEDGER,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    path = os.path.join(QA, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("%s rc=%d bytes=%d" % (name, proc.returncode,
                                 len(text.encode("utf-8"))))
    return proc.returncode, path


def main():
    rc_a, path_a = run_once("apimarket-pricevolatility-R2171-a.log")
    rc_b, path_b = run_once("apimarket-pricevolatility-R2171-b.log")
    with open(path_a, "rb") as handle:
        blob_a = handle.read()
    with open(path_b, "rb") as handle:
        blob_b = handle.read()
    print("identical=%r crlf=%d/%d" % (
        blob_a == blob_b, blob_a.count(b"\r\n"), blob_b.count(b"\r\n")))
    return 0 if (rc_a == 0 and rc_b == 0 and blob_a == blob_b) else 1


if __name__ == "__main__":
    sys.exit(main())