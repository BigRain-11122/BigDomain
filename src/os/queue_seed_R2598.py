"""R2598 seed: ONE P2 tech row measured this window, inserted above the head.

MEASURED at R2598: src/os/runner_suite_timeout_headroom.py derives every
suite cap from the flat SUITE_TIMEOUT_S literal and never reads
SUITE_TIMEOUT_OVERRIDES, so a declared per-suite override (the AC-RSC2
mechanism, shipped exactly for this case) is invisible to the headroom
report: this window declared 900s for ledger-apimarket-refundregister and
the report still printed "slowest=600.0s headroom=0.0s" at cap 600.

Every number printed here is read from the files on disk.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
ANCHOR = "- [ ] P2 tech seed (R2596,"

SEED = (
    "- [ ] P2 tech seed (R2598, from this window own measured limit): "
    "`src/os/runner_suite_timeout_headroom.py` override blindness - "
    "MEASURED this window: the reader derives each suite cap from the flat "
    "`SUITE_TIMEOUT_S` literal only and never reads `SUITE_TIMEOUT_OVERRIDES`, "
    "so the AC-RSC2 mechanism shipped for exactly this case is invisible to "
    "the report: this window declared 900s for "
    "`ledger-apimarket-refundregister` after it finished in 296s alone at "
    "04:22-04:27 but lost the 600s cap inside the R2598 battery, and the "
    "reader still printed `slowest=600.0s headroom=0.0s` against cap 600. "
    "Criteria AC-EDWU1..AC-EDWU6 pinned HERE BEFORE any code: AC-EDWU1 the "
    "reader parses the runner override table by AST and uses the per-suite "
    "cap where one is declared, so the same evidence prints "
    "`slowest=600.0s headroom=300.0s`; AC-EDWU2 an undeclared suite still "
    "reads the flat global cap byte for byte; AC-EDWU3 a malformed or "
    "non-literal override table refuses with its own code instead of "
    "silently falling back to the global cap; AC-EDWU4 the report names the "
    "cap it used for every row so a reader can tell a declared ceiling from "
    "the global one; AC-EDWU5 every R2395 answer survives beside the new "
    "ones (band words, COMFORTABLE, NO-MEASURE, the json key set); AC-EDWU6 "
    "pure ASCII, stdlib only, no clock, zero network, read-only, its own "
    "reconcile label and its own suite.\n"
)


def main():
    text = io.open(QUEUE, "r", encoding="utf-8").read()
    if "AC-EDWU1" in text:
        raise SystemExit("already seeded")
    lines = text.splitlines(True)
    at = None
    for index, line in enumerate(lines):
        if line.startswith(ANCHOR):
            at = index
            break
    if at is None:
        raise SystemExit("anchor row not found: %s" % ANCHOR[:40])
    before = len(text.encode("utf-8"))
    lines.insert(at, SEED)
    out = "".join(lines)
    after = len(out.encode("utf-8"))
    io.open(QUEUE, "w", encoding="utf-8", newline="").write(out)
    back = io.open(QUEUE, "r", encoding="utf-8").read()
    print("inserted at line %d, bytes %d -> %d, readback_ok=%s"
          % (at + 1, before, after, "AC-EDWU1" in back))
    return 0


if __name__ == "__main__":
    sys.exit(main())