# evidence_normalize_R2233.py - rewrite the two R2231 seller-question
# evidence legs through the canonical writer dialect (utf-8, LF, no BOM,
# exactly one trailing newline) without changing a byte of payload text.
#
# Why: the R2231 window captured the suite through a PowerShell pipe, so
# both legs landed as CRLF (10 CRLF, 0 LF) and the writer census flagged
# them as class=pwsh-capture, which turned the live census gate red at
# the R2233 battery. The content is untouched; only the line endings are
# normalised, and the two legs must come out byte-identical afterwards.
#
# Stdlib only, ASCII source, single utf-8 LF writer.
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import run_identity as RI  # noqa: E402

NAMES = [
    "apimarket-sellerquestionmonths-R2231-a.log",
    "apimarket-sellerquestionmonths-R2231-b.log",
]


def sha16(payload):
    return hashlib.sha256(payload).hexdigest()[:16]


def main():
    bodies = []
    for name in NAMES:
        path = os.path.join(ROOT, "qa", name)
        with open(path, "rb") as handle:
            before = handle.read()
        text = before.decode("utf-8")
        fixed = RI.normalize(text).encode("utf-8")
        with open(path, "wb") as handle:
            handle.write(fixed)
        bodies.append(fixed)
        print("%s bytes %d -> %d crlf_after=%d sha16 %s -> %s" % (
            name, len(before), len(fixed),
            fixed.count(b"\r\n"), sha16(before), sha16(fixed)))
    same = bodies[0] == bodies[1]
    print("legs byte-identical=%s sha16=%s" % (same, sha16(bodies[0])))
    return 0 if same else 2


if __name__ == "__main__":
    sys.exit(main())