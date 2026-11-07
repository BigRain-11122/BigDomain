"""R2539 backlog prepend: close the carried row and open the next one.

The carried row named the product face this window shipped; the new row names
the battery the register now owes on the committed tree.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

OLD_HEAD = "- [ ] [carried 2026-11-07 R2538] R2539 first item:"

NEW_ROW = (
    "- [ ] [carried 2026-11-07 R2539] R2540 first item: a VERIFICATION window "
    "on the battery the register now owes - reconcile-battery-R2539 at the "
    "pre-registered 599 suites / 4570 criteria, because this window moved the "
    "registry by one row and a shipped document (the R2168 mixed-tree rule). "
    "Re-measure the target by importing reconcile_all.SUITES before the launch "
    "rather than trusting the register, run the full battery on a CLEAN "
    "committed tree with git status empty before the run, launch it detached "
    "and unfiltered through src/os/battery_stream.py with an explicit "
    "--evidence path and NEVER a shell redirection of its stdout into qa/ (the "
    "ps-utf16 trap has cost five windows a whole leg), keep the red leg if it "
    "goes red and commit a birth-site repair ALONE before any retry, then run "
    "the four follow-up sections through src/os/battery_followup.py (its "
    "matrix section FAILS first on a stale doc by design and must NOT rewrite "
    "it; regenerate with src/sandbox/suite_matrix.py --stamp-from after). On "
    "green go back to the product face the queue head names - re-read it with "
    "python src/os/queue_head.py --head tech, which this window left at "
    "state/queue/tech.md:577 prefix AC-PNSP1 "
    "probe_seam_name_binding_position_scope (criteria pinned there THIS window "
    "before any code): source position is not read so a binding declared AFTER "
    "the loop still resolves, a class body is not a scope this reading follows, "
    "and a comprehension loop is dropped silently. NOTE measured many times: a "
    "commit that moves the queue must also re-derive docs/status-export.json "
    "and land its queue block through queue_export_gate_wire --execute. Also "
    "open and needing an ELEVATED shell: BigDomain-OSLoop still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task (carried as the ceo-pending physical item loop-s4u-reconcile)."
)


def main():
    text = io.open(PATH, encoding="utf-8").read()
    lines = text.split("\n")
    hits = [i for i, row in enumerate(lines) if row.startswith(OLD_HEAD)]
    if len(hits) != 1:
        print("FAIL prepend: hits=%d" % (len(hits),))
        return 2
    at = hits[0]
    lines[at] = ("- [x] [done 2026-11-07 R2539]" + lines[at][len("- [ ]"):])
    lines.insert(at, NEW_ROW)
    payload = "\n".join(lines)
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(PATH, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [ ] [carried 2026-11-07 R2539] R2540")
          and back[at + 1].startswith("- [x] [done 2026-11-07 R2539]"))
    print("backlog %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             len("\n".join(back).encode("utf-8"))))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())