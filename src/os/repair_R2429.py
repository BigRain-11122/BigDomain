"""R2429 birth-site repair: one R2428 live-capture evidence log carries a single
CRLF line inside a utf-8 LF body, so the qa writer census reads it class=other
and the whole battery's census station refuses the real tree (DRIFT-FLAG).

The payload is intact - all six readings the R2428 round reported are present.
Only the transport is wrong. This script asks the shipped run_identity.normalize
for the allowed normalisation, proves the line set identical on both sides,
writes utf-8 LF through one atomic replace and reads the bytes back.

It also measures and prints the byte count so the round can disclose the number
instead of repeating the recalled one.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_identity  # noqa: E402

TARGETS = [
    "qa/comma-binding-consumer-wire-live-R2428.log",
]

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def repair(path):
    full = os.path.join(ROOT, path)
    raw = open(full, "rb").read()
    text = raw.decode("utf-8")
    norm = run_identity.normalize(text)
    before_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    after_lines = norm.split("\n")
    if before_lines != after_lines:
        raise SystemExit("E_REPAIR_PAYLOAD_DIFF %s" % path)
    payload = norm.encode("utf-8")
    tmp = full + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(payload)
    os.replace(tmp, full)
    back = open(full, "rb").read()
    if back != payload:
        raise SystemExit("E_REPAIR_READBACK %s" % path)
    print("REPAIRED %s before=%dB after=%dB crlf=%d lone_cr=%d lines=%d readback=ok"
          % (path, len(raw), len(back), back.count(b"\r\n"),
             back.count(b"\r") - back.count(b"\r\n"), len(after_lines)))


if __name__ == "__main__":
    for target in TARGETS:
        repair(target)