"""R2507 repair: split the carried row that landed inside the done row, and
append the heartbeat row in the file's own UTF-16LE + CRLF transport.

Birth-site repair of this window's own writer defect (the carried row was
inserted where the newline WAS instead of after it). ASCII source, stdlib only.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
BEAT = os.path.join(REPO, "heartbeat.txt")

GLUE = "loop-s4u-reconcile).- [ ] [carried 2026-11-07 R2507]"
FIXED = "loop-s4u-reconcile).\n- [ ] [carried 2026-11-07 R2507]"

LINE = ("2507 tick 2507 product face: artifact disk-text readability shipped "
        "and wired, suite 6/6 twice, registry 583/4474, matrix restamped "
        "56095B, live leg CLEAN over 1226 strings\r\n")


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if text.count(GLUE) == 1:
        text = text.replace(GLUE, FIXED, 1)
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        print("backlog repaired")
    else:
        print("backlog glue hits=%d" % text.count(GLUE))
    lines = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    ok = (lines[0].startswith("- [x] [done 2026-11-07 R2507]")
          and lines[1].startswith("- [ ] [carried 2026-11-07 R2507] R2508")
          and lines[2].startswith("- [x] [done 2026-11-07 R2506]"))
    print("backlog %s order=%r|%r|%r"
          % ("OK" if ok else "FAIL", lines[0][:32], lines[1][:40],
             lines[2][:32]))

    raw = open(BEAT, "rb").read()
    beat = raw.decode("utf-16")
    if "tick 2507" not in beat:
        beat = beat + LINE
        with open(BEAT, "wb") as handle:
            handle.write(beat.encode("utf-16"))
    again = open(BEAT, "rb").read().decode("utf-16")
    hb = again.rstrip().endswith("1226 strings")
    print("heartbeat %s bytes=%d" % ("OK" if hb else "FAIL",
                                     len(open(BEAT, "rb").read())))
    return 0 if (ok and hb) else 2


if __name__ == "__main__":
    sys.exit(main())