"""R2365 backlog repair: restore the R2364 row that an over-broad edit glued.

The replacement matched only the R2364 row prefix, so the R2365 text was
spliced onto the R2364 remainder. This restores the missing boundary by
inserting the R2364 prefix back after the R2365 row's own closing sentence.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

MARK = "Two product points."
TAIL = ("- [x] [done 2026-11-02 R2364] verification window: THE CARRIED "
        "BATTERY RAN FIRST, on the committed tree, and it had genuinely "
        "never run there")

raw = open(PATH, "rb").read()
text = raw.decode("utf-8")
nl = "\r\n" if "\r\n" in text else "\n"
lines = text.split(nl)
first = lines[0]
assert first.startswith("- [x] [done 2026-11-02 R2365]")
assert MARK in first
head, sep, rest = first.partition(MARK)
assert rest.startswith(" - reconcile-battery-R2362"), repr(rest[:60])
lines[0] = head + MARK
lines.insert(1, TAIL + rest)
out = nl.join(lines)
# The row count must be one higher and the R2364 row must read as before.
assert out.count("[done 2026-11-02 R2364]") == 1
assert out.count("[done 2026-11-02 R2365]") == 1
io.open(PATH, "w", encoding="utf-8", newline="").write(out)
print("repaired: rows", len(lines), "bytes", len(out.encode("utf-8")))
print("R2364 line head:", lines[1][:90])