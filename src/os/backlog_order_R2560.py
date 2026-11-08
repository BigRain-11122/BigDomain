"""R2560 backlog order fix: put the newest row on top.

The edit script inserted the new open row below the R2559 done row instead of
above it. This reorders the first three lines so the board reads newest first:
R2561 open, R2560 done, R2559 done. No content changes.
"""

import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "backlog.md")


def main():
    text = io.open(PATH, encoding="utf-8").read()
    lines = text.split("\n")
    if not (lines[0].startswith("- [x] [done 2026-11-08 R2559]")
            and lines[1].startswith("- [ ] [carried 2026-11-08 R2560] R2561")
            and lines[2].startswith("- [x] [done 2026-11-08 R2560]")):
        print("REFUSE: unexpected head order")
        return 2
    lines[0], lines[1], lines[2] = lines[1], lines[2], lines[0]
    io.open(PATH, "wb").write("\n".join(lines).encode("utf-8"))
    back = io.open(PATH, encoding="utf-8").read().split("\n")
    ok = (back[0].startswith("- [ ] [carried 2026-11-08 R2560] R2561")
          and back[1].startswith("- [x] [done 2026-11-08 R2560]")
          and back[2].startswith("- [x] [done 2026-11-08 R2559]"))
    print("ORDER head_ok=%s lines=%d" % (ok, len(back)))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())