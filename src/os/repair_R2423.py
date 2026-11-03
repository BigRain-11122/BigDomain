"""R2423 birth-site repair: two R2422 evidence logs were captured through a
PowerShell redirect, so they landed as ps-utf16 by BOM and the qa writer census
read them as new-dialect. The payload is intact; only the transport is wrong.

This script decodes utf-16, asks the shipped run_identity.normalize for the
allowed normalisation, writes utf-8 LF through one atomic replace, and proves
the line set is identical on both sides before and after the write.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_identity  # noqa: E402

TARGETS = [
    "qa/plain-import-alias-gate-R2422.log",
    "qa/plain-import-alias-gate-live-R2422.log",
]


def repair(path):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full = os.path.join(root, path)
    raw = open(full, "rb").read()
    text = raw.decode("utf-16")
    norm = run_identity.normalize(text)
    before_lines = [ln for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
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
    print("REPAIRED %s before=%dB after=%dB crlf=%d lone_cr=%d lines=%d sha16=%s"
          % (path, len(raw), len(back), back.count(b"\r\n"), back.count(b"\r"),
             len(back.split(b"\n")) - 1, hashlib.sha256(back).hexdigest()[:16]))


for target in TARGETS:
    repair(target)