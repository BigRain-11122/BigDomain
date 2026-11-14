"""Close the tech queue head row R2730 discharged (shape-typing face)."""

import io

PATH = "state/queue/tech.md"

DISCHARGE = (
    " DISCHARGED R2730: shipped src/os/evidence_capture_precedence_shape_typing.py "
    "plus its six-criteria suite. MEASURED on the shipped face BEFORE any byte: with "
    "one shipped refusal law patched to answer E_EBOM_UTF16, the R2725 report reads "
    "code E_EBOM_UTF16 beside shapes [E_EBOM_UTF16, nul, utf8, tail] and "
    "CODES[shapes[0]] raises KeyError on the mixed fixture, while the sole-unknown "
    "fixture publishes the code alone and raises the same KeyError; this face keeps "
    "every list names-only, carries that code in its own unknown_code field, and "
    "returns every six-known-shape answer unchanged. SUITE PASS 6/6 twice with an "
    "identical digest 11835F727853560A "
    "(qa/evidence-capture-precedence-shape-typing-R2730b.log, 899B, utf-8 LF, landed "
    "BY the shipped capture callable) and five adjacent suites green (fails=0); the "
    "live leg reads ACCEPT on qa/reconcile-all-R2725.log on BOTH readers. wired "
    "os-evidence-capture-precedence-shape-typing(6) -> registry 673/5014 to 674/5020 "
    "measured by import; matrix restamped stamp-aligned at 674 rows after the "
    "designed ROWS-MISMATCH read 673 against 674 with no byte written."
)

text = io.open(PATH, "rb").read().decode("utf-8")
lines = text.split("\n")
row = lines[696]
assert row.startswith("- [ ] P2 tech seed (R2725,"), row[:40]
lines[696] = "- [x] [done 2026-11-14 R2730]" + row[len("- [ ]"):] + DISCHARGE
io.open(PATH, "wb").write(("\n".join(lines)).encode("utf-8"))
print("lines=%d closed_row=%d" % (len(lines), len(lines[696])))
