"""R2551 backlog closeout: mark the carried R2550 row done and prepend the next
window own carried row (the battery the register now names first).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(BASE, "backlog.md")

OLD_HEAD = "- [ ] [carried 2026-11-08 R2550]"
NEW_HEAD = "- [x] [done 2026-11-08 R2551] [was carried 2026-11-08 R2550]"

ROW = (
    "- [ ] [carried 2026-11-08 R2551] R2552 first item: the battery the debt "
    "register now names first - reconcile-battery-R2551, pre-registered 605 "
    "suites / 4606 criteria and recounted by importing reconcile_all.SUITES "
    "before the launch. This window moved product src bytes and one registry "
    "row, so a full green leg on the committed tree is owed BEFORE any further "
    "product byte. Land the evidence through src/os/battery_stream.py as a "
    "single-writer utf-8 LF file, measure the encoding counters rather than "
    "quoting them, recount the PASS suite rows independently, run the four "
    "follow-up sections in the designed order (dry run first so the matrix "
    "FAILS by design with no byte written, then fingerprint, profile, census), "
    "regenerate docs/sandbox-suite-matrix.md through suite_matrix "
    "--stamp-from and prove --check byte-identical, and append the verdict. "
    "DEBT: close reconcile-battery-R2551 through the shipped debtor and, since "
    "no product byte will move in a verification window, open product-face-R2552 "
    "naming the tech head state/queue/tech.md:589 prefix AC-PNDQ1 "
    "probe_seam_name_binding_arm_mixed_residual_naming, whose six criteria were "
    "pinned in that row at R2551 BEFORE any code. Also open and misc: state.json "
    "reads 216786B against the 78500B waterline so state_fold --check reads "
    "FOLD-DUE and this build ships only a --check face, so the fold stays an "
    "OWED obligation seeded as state_fold_run (AC-SFOLD1..6); queue_row --check "
    "still reads pre-existing VIOLATIONS on tech:88, :415, :524, :537, :594 and "
    "explore:295, all rows that predate this window; and BigDomain-OSLoop still "
    "reads InteractiveToken, which the 2026-09-29 machine law forbids for every "
    "lane task (carried as the ceo-pending physical item loop-s4u-reconcile, "
    "needs an ELEVATED shell)."
)


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if not text.startswith(OLD_HEAD):
        print("FAIL head: %r" % text[:60])
        return 2
    body = NEW_HEAD + text[len(OLD_HEAD):]
    body = ROW + "\n" + body
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = io.open(BACKLOG, encoding="utf-8").read()
    ok = (back.startswith("- [ ] [carried 2026-11-08 R2551]")
          and NEW_HEAD in back and back.count("R2552 first item") == 1
          and "\r" not in back)
    print("BACKLOG %s lines=%d bytes=%d"
          % ("OK" if ok else "FAIL", len(back.splitlines()),
             len(back.encode("utf-8"))))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())