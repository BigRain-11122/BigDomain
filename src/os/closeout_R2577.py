"""R2577 closeout: prepend the backlog row and rewrite the heartbeat line."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEART = os.path.join(REPO, "heartbeat.txt")

ROW = (
    "- [x] [done 2026-11-08 R2577] R2577 PRODUCT window on the queue head the "
    "debt gate named (product-face-R2576, state/queue/tech.md:611 prefix "
    "AC-PNCS1, criteria pinned at R2575 BEFORE any code). SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_chain_scope.py plus its six-criteria suite: a "
    "module-level ALIAS CHAIN ending at a call resolves as a with-as receiver "
    "and names every link; a module-level FUNCTION returning a class attribute "
    "resolves while one returning a non-module literal keeps the shipped "
    "refusal; a class constant aliasing a FROM-imported constant resolves "
    "while a FROM-imported CONSTANT used as a class base is still not read as "
    "a class; and a chain ending at a name bound nowhere is NAMED with that "
    "name on BOTH paths (the with-as receiver and the module-attribute chain, "
    "the second repaired at its birth site after being measured in my own "
    "first pass). Every shipped class-source key rides unchanged. PROOF: "
    "AC-PNCS1..AC-PNCS6 SUITE PASS 6/6 and 6/6 TWICE byte-identical plus two "
    "adjacent probe suites green (qa/...-module-alias-chain-scope-R2577.log, "
    "6337B, legs=2, identical=True, adjacent=2, fails=0); a BOUNDED live leg "
    "over six real probe modules reads probes=6 loops=161 ma_resolved=0 "
    "ma_named=0 read_only=True and measures the same fixture on BOTH readers "
    "(ok/b here against refused/attr-with-as:m.ATTR there; the first capture "
    "landed as PowerShell UTF-16 and was rewritten to utf-8 LF before any "
    "census could read it). REGISTRY 617/4678 -> 618/4684 recounted by import "
    "(618 unique names, 618 unique paths); the matrix read FAIL stale before "
    "any byte was written and was regenerated stamp-aligned from the eligible "
    "R2574 leg to 61209B with green honestly 617/618 and --check "
    "byte-identical. BOARD: row 611 closed at its predicted and measured "
    "1810631B, ONE row seeded as AC-PNMA1..AC-PNMA6 at line 613 from this "
    "window own measured limits (attribute-final alias chain, function "
    "returning a NAME bound to a class attribute, call context on an alias "
    "chain), head claimable=11 and floor MET. DEBT: product-face-R2576 closed "
    "182181B -> 182184B, reconcile-battery-R2577 opened first=yes at 618/4684 "
    "and product-face-R2577 opened first=no, all readback ok. HONEST: two "
    "product points, nothing a CEO could newly open, no P-47 business surface "
    "moved; two of my own assertions were corrected to measurement rather "
    "than loosened; the residue declaration for R2577 was REFUSED with "
    "E_RTAB_NOT_RESIDUE (not yet in the live residue) and stays owed.\n"
)

HEART_LINE = (
    "2026-11-08T21:23+08:00 R2577 product: the module-alias-chain face shipped "
    "with six pre-registered criteria green 6/6 twice (6337B, legs=2, "
    "identical=True, adjacent=2) plus a bounded live leg over six real probe "
    "modules; registry 618/4684 recounted by import, matrix 61209B "
    "green=617/618 byte-identical, board row 611 closed at 1810631B and the "
    "next face seeded at line 613 AC-PNMA1; debt: battery R2577 owed next on "
    "618/4684.\n"
)


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if text.startswith("- [x] [done 2026-11-08 R2577]"):
        print("backlog already carries R2577")
        return 0
    io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(ROW + text)
    io.open(HEART, "w", encoding="utf-8", newline="\n").write(HEART_LINE)
    back = io.open(BACKLOG, encoding="utf-8").read()
    ok = back.startswith("- [x] [done 2026-11-08 R2577] R2577 PRODUCT window")
    heart = io.open(HEART, encoding="utf-8").read()
    print("closeout %s backlog_bytes=%d heart_bytes=%d"
          % ("OK" if ok else "FAIL", len(back.encode("utf-8")),
             len(heart.encode("utf-8"))))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())