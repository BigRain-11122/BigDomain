"""Single-writer evidence for the R2240 seller-price-demand window.

Runs the suite twice and writes
qa/apimarket-sellerpricedemandmonths-R2240-a.log and -b.log as UTF-8 LF
with no shell redirection (the ps-utf16 dialect trap of R2230/R2233).
Prints the byte comparison of the two files.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_sellerpricedemandmonths.py")


def run_once(path):
    out = subprocess.run([sys.executable, SUITE], cwd=ROOT,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    text = out.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return out.returncode, text


def sha_bytes(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    a = os.path.join(ROOT, "qa",
                     "apimarket-sellerpricedemandmonths-R2240-a.log")
    b = os.path.join(ROOT, "qa",
                     "apimarket-sellerpricedemandmonths-R2240-b.log")
    rc_a, text_a = run_once(a)
    rc_b, text_b = run_once(b)
    same = sha_bytes(a) == sha_bytes(b)
    with open(a, "rb") as handle:
        raw = handle.read()
    print("rc_a=%d rc_b=%d bytes_same=%r size=%d crlf=%d bom=%r"
          % (rc_a, rc_b, same, len(raw), raw.count(b"\r\n"),
             raw.startswith(b"\xef\xbb\xbf")), flush=True)
    print("sha256=%s" % sha_bytes(a), flush=True)
    print("suite_line_a=%r"
          % ([ln for ln in text_a.splitlines()
              if ln.startswith("SUITE ")] or ["MISSING"]), flush=True)
    print("PRODUCT_SHA_STABLE=%r"
          % ("PRODUCT_SHA_STABLE True" in text_a), flush=True)
    return 0 if (rc_a == 0 and rc_b == 0 and same) else 1


if __name__ == "__main__":
    sys.exit(main())