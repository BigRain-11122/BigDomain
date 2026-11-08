"""R2565 backlog surgery and heartbeat: close the carried row, seed R2566.

Reads src/os/backlog.md as bytes, rewrites line 0 in place (the carried row
discharged by this window) and prepends the next carried row, then writes the
heartbeat line. A read-back refuses when either edit did not land.
"""

import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEART_PATH = os.path.join(ROOT, "heartbeat.txt")

DONE = (
    "- [x] [done 2026-11-08 R2565] R2565 PRODUCT window on the tech head the "
    "register named (product-face-R2564, state/queue/tech.md:601 prefix "
    "AC-PNDCE1). SHIPPED src/os/probe_seam_name_binding_arm_mixed_residual_"
    "alias_attribute_import_alias_scope_from_scope.py plus its six-criteria "
    "suite: a module bound by `from pkg import helper`, plain or aliased, is a "
    "MODULE base resolved through pkg/helper.py instead of a local; a helper "
    "constant declared only inside a function body resolves when that function "
    "returns it and is NAMED attr-function-constant when it does not; a "
    "`with call() as NAME` binding whose call returns a module name resolves "
    "while a call returning anything else keeps the shipped attr-with-as word; "
    "every shipped import-alias key rides unchanged beside this face own. "
    "PROOF measured: SUITE PASS 6/6 TWICE with an identical digest plus five "
    "adjacent probe suites green (qa/...from-scope-R2565.log, 5397B, legs=2 "
    "identical=True adjacent=5 fails=0) through the shipped capture callable; a "
    "BOUNDED live leg over 6 real probe_seam modules reads loops=123 "
    "from_resolved=0 from_named=0 read_only=True with the SAME fixtures "
    "measured on BOTH readers. Registry 611/4642 -> 612/4648 recounted by "
    "import; matrix regenerated stamp-aligned from the eligible R2564 leg to "
    "59929B with green honestly 611/612 and --check byte-identical; board row "
    "601 closed at 1785857B and AC-PNDCF1 seeded at line 603; debt "
    "product-face-R2564 closed, reconcile-battery-R2565 opened first=yes, "
    "product-face-R2565 opened first=no; residue R2565 TRIAGED until R2575."
)

NEW = (
    "- [ ] [carried 2026-11-08 R2565] R2566 first item: a VERIFICATION window "
    "on the battery the register now names first - reconcile-battery-R2565 at "
    "the re-measured 612 suites / 4648 criteria, because this window moved the "
    "registry by one row and shipped a document (the R2168 mixed-tree rule). "
    "Re-measure the target by importing reconcile_all.SUITES before the launch, "
    "run the full battery on a CLEAN committed tree with git status empty, "
    "launch it detached through a python Popen with the stream and the pid in "
    "SEPARATE files and NEVER a shell redirection into qa/ (the ps-utf16 trap "
    "has cost this repository several whole legs), keep a red leg as evidence "
    "and commit a birth-site repair ALONE before any retry, then run the four "
    "follow-up sections through src/os/battery_followup.py (its matrix section "
    "FAILS first on a stale doc by design and must NOT rewrite it; regenerate "
    "with src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after) and land the verdict. On green go back "
    "to the product face the queue head names - re-read it with `python "
    "src/os/queue_head.py --head tech`, which this window left at "
    "state/queue/tech.md:603 prefix AC-PNDCF1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_call_target_scope (criteria AC-PNDCF1..AC-PNDCF6 pinned in that row "
    "THIS window before any code): a with-as call on an ATTRIBUTE or a class "
    "method is never resolved, a call returning its module name through a "
    "LOCAL variable is never resolved, a relative `from . import helper` stays "
    "a local, and a constant bound only inside a NESTED function IS resolved - "
    "an over-resolution. NOTE measured many times: a commit that moves the "
    "queue must also re-derive docs/status-export.json and land its queue block "
    "through queue_export_gate_wire --execute. Also open and misc: state.json "
    "reads far past the 78500B waterline so state_fold --check reads FOLD-DUE "
    "and its layout reader still refuses this file (the layout is indent=1 "
    "ensure_ascii=False with no trailing newline, proved by round-trip this "
    "window), so the fold stays an OWED obligation seeded as state_fold_run "
    "(AC-SFOLD1..6); the stored last_decision_rows field reads 273 against a "
    "measured 164 row tokens and was disclosed rather than rewritten; the open "
    "rows product-face-R2511, R2513, R2515, R2517 and R2522 still overstate "
    "outstanding work and were disclosed rather than hand-closed; queue_row "
    "--check still reads pre-existing VIOLATIONS on rows that predate this "
    "window; and BigDomain-OSLoop still reads InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task (carried as the "
    "ceo-pending physical item loop-s4u-reconcile, needs an ELEVATED shell)."
)

HEART_LINE = (
    "tick 2565 2026-11-08 R2565 product window: the from-scope face shipped "
    "with its six criteria proved twice and a bounded live leg on both readers, "
    "registry 612 suites / 4648 criteria recounted by import, matrix 59929B "
    "byte-identical, board row 601 closed and AC-PNDCF1 seeded at line 603, "
    "debt battery R2565 owed first, residue R2565 TRIAGED until R2575\n"
)


def main():
    raw = io.open(BACKLOG, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    already = lines[0].startswith("- [ ] [carried 2026-11-08 R2565]")
    if not already:
        if not lines[0].startswith("- [ ] [carried 2026-11-08 R2564]"):
            print("REFUSE: line 0 is neither the carried row nor this round row")
            return 2
        lines[0] = DONE
        lines.insert(0, NEW)
        io.open(BACKLOG, "wb").write("\n".join(lines).encode("utf-8"))
    back = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    ok = (back[0].startswith("- [ ] [carried 2026-11-08 R2565]")
          and back[1].startswith("- [x] [done 2026-11-08 R2565]"))
    io.open(HEART_PATH, "wb").write(HEART_LINE.encode("utf-8"))
    print("BACKLOG lines=%d already=%s ok=%s bytes=%d"
          % (len(back), already, ok, len(io.open(BACKLOG, "rb").read())))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())