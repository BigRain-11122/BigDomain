"""Wire the R2395 suite into the registry (R2395).

Anchored on the R2393 entry, which is unique in the file, and refuses
unless that anchor appears exactly once. ASCII source, stdlib only.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

ANCHOR = ('    ("os-refused-check-declaration-face",\n'
          '     os.path.join("..", "os", '
          '"test_refused_check_declaration_face.py"), 6),\n')

ADD = (
    "    # R2395: the 300s per-suite cap is a reading now - each registered\n"
    "    # suite's own slowest measured leg and the headroom it carries, so a\n"
    "    # loaded machine is named in a warning band instead of killing a\n"
    "    # whole battery in silence. (AC-RTH1..AC-RTH6 pinned in\n"
    "    # state/queue/tech.md line 462 as the R2393 seed BEFORE the code.)\n"
    '    ("os-runner-suite-timeout-headroom",\n'
    '     os.path.join("..", "os", '
    '"test_runner_suite_timeout_headroom.py"), 6),\n')


def main(argv):
    with io.open(RUNNER, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    before = len(text.encode("utf-8"))
    if text.count(ANCHOR) != 1:
        print("REFUSED: anchor appears %d times" % text.count(ANCHOR))
        return 2
    text = text.replace(ANCHOR, ANCHOR + ADD, 1)
    after = len(text.encode("utf-8"))
    print("reconcile_all.py %d -> %d bytes (delta %+d)"
          % (before, after, after - before), flush=True)
    if "--execute" not in argv:
        print("DRY: no write")
        return 0
    temp = RUNNER + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, RUNNER)
    with io.open(RUNNER, "r", encoding="utf-8", newline="") as handle:
        readback = len(handle.read().encode("utf-8"))
    print("readback=%d verified=%s" % (readback, readback == after))
    return 0 if readback == after else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))