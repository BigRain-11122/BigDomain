"""R2549 backlog closeout: mark the carried R2548 row done and prepend the
next window own carried row (the battery reconcile-battery-R2549 owes).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(BASE, "backlog.md")

OLD_HEAD = "- [ ] [carried 2026-11-08 R2547]"
NEW_HEAD = "- [x] [done 2026-11-08 R2548] [was carried 2026-11-08 R2547]"

ROW = (
    "- [ ] [carried 2026-11-08 R2549] R2550 first item: a VERIFICATION window on "
    "the battery the register owes - reconcile-battery-R2549 at the pre-registered "
    "604 suites / 4600 criteria, because R2549 moved the registry by one row "
    "(os-probe-seam-name-binding-nested-exhaustive-path) and a shipped document "
    "(the R2168 mixed-tree rule). Re-measure the target by importing "
    "reconcile_all.SUITES before the launch rather than trusting the register, run "
    "the full battery on a CLEAN committed tree with git status empty before the "
    "run, launch it detached and unfiltered through src/os/battery_stream.py with "
    "an explicit --evidence path and NEVER a shell redirection of its stdout into "
    "qa/ (the ps-utf16 trap has cost this repository several whole legs), keep the "
    "red leg if it goes red and commit a birth-site repair ALONE before any retry, "
    "then run the four follow-up sections through src/os/battery_followup.py (its "
    "matrix section FAILS first on a stale doc by design and must NOT rewrite it; "
    "regenerate with src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after). On green go back to the product face the "
    "queue head names - re-read it with python src/os/queue_head.py --head tech, "
    "which this window left at state/queue/tech.md:587 prefix AC-PNDP1 "
    "probe_seam_name_binding_nested_arm_mixed_scope (criteria AC-PNDP1..AC-PNDP6 "
    "pinned in that row THIS window before any code): an arm that binds the name "
    "directly AND contains a nested guard reads mixed:<arm> and never resolves, a "
    "try nested under an arm carrying an else or a finally reads "
    "incomplete:<group> even when every leaf agrees, and a with-as binding reads "
    "non-literal:<arm> rather than with-as. NOTE measured many times: a commit that "
    "moves the queue must also re-derive docs/status-export.json and land its queue "
    "block through queue_export_gate_wire --execute. Also open and misc: "
    "state.json stands at 205706B against the 78500B waterline so state_fold "
    "--check reads FOLD-DUE and this build of the tool ships only a --check face, "
    "so the fold stays an OWED obligation seeded as state_fold_run (AC-SFOLD1..6); "
    "and BigDomain-OSLoop still reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task (carried as the ceo-pending physical "
    "item loop-s4u-reconcile, needs an ELEVATED shell)."
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
    ok = (back.startswith("- [ ] [carried 2026-11-08 R2549]")
          and NEW_HEAD in back and back.count("R2550 first item") == 1
          and "\r" not in back)
    print("BACKLOG %s lines=%d bytes=%d"
          % ("OK" if ok else "FAIL", len(back.splitlines()),
             len(back.encode("utf-8"))))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())