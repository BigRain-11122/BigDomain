"""R2560 backlog edit: close the verification row and open the next one.

Line 2 of src/os/backlog.md is the open R2560 verification item; it is marked
done in place and one open row is inserted above it naming the product face the
debt register now owes (tech head line 597, prefix AC-PNDB1, criteria pinned at
R2559 BEFORE any code). Everything else is left byte-identical.
"""

import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "backlog.md")

HEAD = "- [ ] [carried 2026-11-08 R2559] R2560 first item: a VERIFICATION window"

DONE_NOTE = (
    " DONE (R2560): the battery was measured, not re-run - it was launched by "
    "an interrupted earlier attempt of this same round and its legs were read "
    "first. RED LEG KEPT (qa/reconcile-all-R2560-red.log, 1022274B): RUNNER "
    "FAIL 607/609 with os-matrix-stamp-compare 5/6 and os-stamp-text-coverage "
    "exit=1, cause read as a matrix document regenerated WITHOUT --stamp-from "
    "so it lost its provenance line while --check still passed on content. "
    "GREEN LEG (qa/reconcile-all-R2560.log, 1023672B): RUNNER PASS 609/609 "
    "suites, controls 7/7, 2276.6s, zero FAIL rows, runner summary 'expected "
    "criteria total=4630' and the 609/4630 target re-read by import; "
    "provenance checked against the commit time. Follow-up: one designed "
    "matrix FAIL at EQUAL byte counts (59313 vs 59313, different content), "
    "then a stamp-aligned regeneration from this round own green leg to "
    "59313B at 609 suites / 4630 criteria with green=609/609 "
    "self-describing, --check byte-identical at rc=0, and all four sections "
    "PASS for VERDICT R2560 PASS failing=none (APPENDED 1951B). Debt: "
    "reconcile-battery-R2559 closed (line 300, open 24->23, done 259->260) "
    "and product-face-R2560 opened first=yes. Registry unmoved at 609/4630 so "
    "no successor battery is owed. Honest: zero product points, the export "
    "driver left by the interrupted attempt asserted a narrative this window "
    "did not perform so it was deleted rather than reused, and the fold stays "
    "owed (state_fold ships --check only)."
)

NEW = (
    "- [ ] [carried 2026-11-08 R2560] R2561 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:597 prefix "
    "AC-PNDB1 probe_seam_name_binding_arm_mixed_residual_alias_attribute_base_"
    "residual, criteria AC-PNDB1..AC-PNDB6 pinned in that row at R2559 BEFORE "
    "any code. Re-read the row with `python src/os/queue_head.py --head tech` "
    "(R2560 measured line=597 claimable=12, floor MET). Ship the reading the "
    "four measured limits demand - a WALRUS attribute alias records nothing at "
    "all and publishes NO reason, a SUBSCRIPT base is published as "
    "attr-not-imported:?.ATTR where the base text is a question mark, a "
    "package own __init__ constant reads attr-missing because the hop asks for "
    "<mod>.py, and a with-as helper binding reads attr-missing - each NAMED "
    "with its own shape rather than collapsing into one refusal word, with "
    "every shipped answer carried beside it. Then: suite twice with an "
    "identical digest plus adjacent probe suites green, a bounded live leg "
    "with the same fixtures measured on BOTH readers, one registry row "
    "recounted by import, the matrix regenerated stamp-aligned from an "
    "eligible battery leg and --check byte-identical, the board row closed "
    "with its DISCHARGED note and ONE row seeded from this window own measured "
    "limit, and because the registry will move, a successor battery registered "
    "first=yes at the new totals to run BEFORE any further product byte."
)


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hit = [i for i, line in enumerate(lines) if line.startswith(HEAD)]
    if len(hit) != 1:
        print("REFUSE: expected exactly one open R2560 row, found %d"
              % len(hit))
        return 2
    i = hit[0]
    body = lines[i]
    if body.startswith("- [ ]"):
        body = "- [x] [done 2026-11-08 R2560]" + body[len("- [ ]"):] + DONE_NOTE
    lines[i] = body
    lines.insert(i, NEW)
    out = "\n".join(lines).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = io.open(PATH, "rb").read().decode("utf-8").split("\n")
    ok = (back[0].startswith("- [ ] [carried 2026-11-08 R2560] R2561")
          and back[1].startswith("- [x] [done 2026-11-08 R2560]")
          and "DONE (R2560)" in back[1])
    print("BACKLOG lines=%d open_next=%s closed_prev=%s ok=%s"
          % (len(back), back[0][:40], back[1][:40], ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())