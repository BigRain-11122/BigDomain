"""repair_R2301.py - undo the R2301 append so the fold can run first.

The closeout helper appended four log items on top of a 77573B state because
its fold window (1..4) freed too little to satisfy the fold predicate's own
gate check, which refused to write and said so. This helper removes exactly
those four items, restores tick 2300, rewrites through state_io.canon and
refuses to finish unless the result is byte-identical to the pre-append file
(77573B, sha16 8799fafce253c967 recorded by the refused fold plan).
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import state_io  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(REPO, "src", "os", "state.json")

EXPECT_BYTES = 77573
EXPECT_SHA16 = "8799fafce253c967"

MARKS = (
    "2026-11-01 R2301 (five-silence scan clean at open",
    "R2301 tokens: local=",
    "R2301 self-heal check:",
    "R2301 honest disclosures:",
)


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    tail = state["log"][-4:]
    for item, mark in zip(tail, MARKS):
        if not item.startswith(mark):
            sys.exit("E_REPAIR_SHAPE: tail item does not match: %r" % item[:40])
    state["log"] = state["log"][:-4]
    state["tick"] = 2300
    ensure_ascii = all(b < 0x80 for b in raw)
    text = json.dumps(state, ensure_ascii=ensure_ascii, indent=2)
    text = state_io.canon(text)
    new = text.encode("utf-8")
    digest = hashlib.sha256(new).hexdigest()[:16]
    print("STATE %dB -> %dB sha16 %s" % (len(raw), len(new), digest))
    if len(new) != EXPECT_BYTES or digest != EXPECT_SHA16:
        sys.exit("E_REPAIR_MISMATCH: expected %dB/%s"
                 % (EXPECT_BYTES, EXPECT_SHA16))
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    temp = os.path.join(os.path.dirname(STATE), ".repair_R2301.tmp")
    with open(temp, "wb") as sink:
        sink.write(new)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    if open(STATE, "rb").read() != new or os.path.exists(temp):
        sys.exit("E_REPAIR_READBACK")
    print("WROTE state restored byte-exact, temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))