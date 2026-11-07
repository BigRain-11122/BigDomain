"""R2541 backlog prepend: close the product row, open the battery row.

The carried row owed the product face this window shipped; the new row names
the battery the R2168 mixed-tree rule now owes on this committed tree at the
pre-registered 600 suites / 4576 criteria.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

OLD_HEAD = "- [ ] [carried 2026-11-07 R2540] R2541 first item:"

NEW_ROW = (
    "- [ ] [carried 2026-11-07 R2541] R2542 first item: a VERIFICATION window "
    "on the battery the register now owes - reconcile-battery-R2541 at the "
    "pre-registered 600 suites / 4576 criteria, because this window moved the "
    "registry by one row and a shipped document (the R2168 mixed-tree rule). "
    "Re-measure the target by importing reconcile_all.SUITES before the "
    "launch rather than trusting the register, run the full battery on a "
    "CLEAN committed tree with git status empty before the run, launch it "
    "detached and unfiltered through src/os/battery_stream.py with an "
    "explicit --evidence path and NEVER a shell redirection of its stdout "
    "into qa/ (the ps-utf16 trap has cost several windows a whole leg), keep "
    "the red leg if it goes red and commit a birth-site repair ALONE before "
    "any retry, then run the four follow-up sections through "
    "src/os/battery_followup.py (its matrix section FAILS first on a stale "
    "doc by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after). On green go back to the product "
    "face the queue head names - re-read it with python src/os/queue_head.py "
    "--head tech, which this window left at state/queue/tech.md:579 prefix "
    "AC-PNCF1 probe_seam_name_binding_control_flow_scope (criteria pinned "
    "there THIS window before any code): a binding inside a branch that may "
    "not run still resolves, a with-as binding is not collected at all, and "
    "two exclusive try/except branches read one ambiguous word. NOTE measured "
    "many times: a commit that moves the queue must also re-derive "
    "docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute. Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop still reads InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task (carried as the "
    "ceo-pending physical item loop-s4u-reconcile)."
)


def main():
    text = io.open(PATH, encoding="utf-8").read()
    if not text.startswith(OLD_HEAD):
        print("FAIL head is not the carried row")
        return 2
    payload = NEW_ROW + "\n" + text
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(PATH, encoding="utf-8").read()
    ok = back.startswith("- [ ] [carried 2026-11-07 R2541]") \
        and OLD_HEAD in back
    print("backlog %s predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", len(payload.encode("utf-8")),
             len(back.encode("utf-8"))))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())