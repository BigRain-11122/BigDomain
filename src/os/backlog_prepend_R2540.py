"""R2540 backlog prepend: close the verification row, open the product row.

The carried row owed the battery this window ran green; the new row names the
product face the register names next on tech line 577 (AC-PNSP1).
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

OLD_HEAD = "- [ ] [carried 2026-11-07 R2539] R2540 first item:"

NEW_ROW = (
    "- [ ] [carried 2026-11-07 R2540] R2541 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:577 prefix "
    "AC-PNSP1 probe_seam_name_binding_position_scope, criteria AC-PNSP1.."
    "AC-PNSP6 pinned in that row at R2539 BEFORE any code. The measured limit: "
    "source position is not read, so a binding declared AFTER the loop still "
    "resolves; a class body is not a scope this reading follows; a "
    "comprehension loop is dropped silently. Re-read the row with python "
    "src/os/queue_head.py --head tech rather than trusting this line, run a "
    "fresh zero-occupancy anchor check at HEAD, ship ONE face with its "
    "pre-registered suite, refill the tech floor if claiming drops claimable "
    "below 10, and commit BEFORE any battery (the R2168 mixed-tree rule holds "
    "at open: the registry is unmoved by R2540 at 599 suites / 4570 criteria, "
    "so NO successor battery is owed). NOTE measured many times: a commit that "
    "moves the queue must also re-derive docs/status-export.json and land its "
    "queue block through queue_export_gate_wire --execute, otherwise the next "
    "battery reads the queue face STALE. Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop still reads InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task (carried as the "
    "ceo-pending physical item loop-s4u-reconcile)."
)


def main():
    text = io.open(PATH, encoding="utf-8").read()
    lines = text.split("\n")
    hits = [i for i, row in enumerate(lines) if row.startswith(OLD_HEAD)]
    if len(hits) != 1:
        print("FAIL prepend: hits=%d" % (len(hits),))
        return 2
    at = hits[0]
    lines[at] = ("- [x] [done 2026-11-07 R2540]" + lines[at][len("- [ ]"):])
    lines.insert(at, NEW_ROW)
    payload = "\n".join(lines)
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(PATH, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [ ] [carried 2026-11-07 R2540] R2541")
          and back[at + 1].startswith("- [x] [done 2026-11-07 R2540]"))
    print("backlog %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             len("\n".join(back).encode("utf-8"))))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())