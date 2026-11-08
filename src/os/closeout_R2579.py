"""Prepend the R2579 done line to src/os/backlog.md and append one heartbeat line.

Both files are written as utf-8 with LF endings and read back for proof.
"""
import io
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEART = os.path.join(ROOT, "heartbeat.txt")

DONE = (
    "- [x] [done 2026-11-08 R2579] R2579 PRODUCT window on the queue head the "
    "debt gate named (product-face-R2578, state/queue/tech.md:613 prefix "
    "AC-PNMA1, criteria pinned at R2577 BEFORE any code). SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_scope.py plus its six-criteria suite: "
    "the extension is applied THROUGH the shipped reading rather than beside "
    "it - the three readers the module-alias-chain face calls at run time are "
    "swapped for this face own inside one guarded block and restored in a "
    "finally - so an attribute-final alias chain, a module-level function "
    "returning a NAME bound to a class attribute, and a with-as call context "
    "on an alias chain name all resolve, while a chain whose attribute link "
    "names a module that is not on disk is NAMED with the link that broke. "
    "The SHIPPED baseline on every row is measured with the readers UNPATCHED "
    "so the row really carries what the face it extends answered. PROOF: "
    "AC-PNMA1..AC-PNMA6 SUITE PASS 6/6 and 6/6 TWICE identical plus two "
    "adjacent probe suites green (qa/...-module-alias-attribute-scope-R2579."
    "log, 5849B, legs=2 identical=True adjacent=2 fails=0); a BOUNDED live "
    "leg over six real probe modules reads loops=159 ma_resolved=0 "
    "ma_named=0 read_only=True and measures the same fixture on BOTH readers "
    "(ok/b and hop module-alias-attribute/attribute/direct here against "
    "refused/attr-with-as:m.ATTR there). REGISTRY 618/4684 -> 619/4690 "
    "recounted by import; matrix regenerated stamp-aligned to 61469B with "
    "green honestly 618/619 and --check byte-identical. BOARD: row 613 closed "
    "at its predicted and measured 1815502B, ONE row seeded as AC-PNAM1.."
    "AC-PNAM6 at line 615 from this window own measured limits (module-alias "
    "attribute head, two-step attribute path, call on a FROM-imported "
    "function name), head claimable=11, floor MET. DEBT: product-face-R2578 "
    "closed, reconcile-battery-R2579 opened first=yes at 619/4690 and "
    "product-face-R2579 opened first=no, all readback ok. STATE folded twice "
    "at true round-block boundaries (81361B -> 78110B -> 73240B, tokens "
    "4+5 ok=True, archive VERIFIED), FOLD-CLEAR margin 5260. EXPORT 395254B "
    "at tick 2579, queue=CURRENT, check_export_consistency pass=21 fail=0 "
    "VERDICT PASS. HONEST: two product points, nothing a CEO could newly open "
    "and no P-47 surface moved; my first bounded leg misused the shipped "
    "module= parameter and read E_PSMR_NO_RENDER on all six modules, so the "
    "leg was rewritten rather than any shipped module edited; both captures "
    "first landed as PowerShell output and were re-taken as utf-8 LF."
)

HEART_MSG = (
    "2026-11-08T23:0x+08:00 R2579 product: the module-alias-attribute face "
    "shipped with six pre-registered criteria green 6/6 twice (5849B, legs=2, "
    "identical=True, adjacent=2) plus a bounded live leg over six real probe "
    "modules; registry 619/4690 recounted by import, matrix 61469B green=618/"
    "619 byte-identical, board row 613 closed at 1815502B and the next face "
    "seeded at line 615 AC-PNAM1; debt: battery R2579 owed next on 619/4690."
)


def main():
    raw = io.open(BACKLOG, "rb").read()
    text = raw.decode("utf-8")
    if text.startswith("- [x] [done 2026-11-08 R2579]"):
        # already written by a first attempt; never prepend the same line twice
        ok_backlog = True
    else:
        payload = DONE + "\n" + text
        io.open(BACKLOG, "wb").write(payload.encode("utf-8"))
        back = io.open(BACKLOG, "rb").read().decode("utf-8")
        ok_backlog = back.startswith("- [x] [done 2026-11-08 R2579]")
    raw = io.open(HEART, "rb").read()
    text = raw.decode("utf-8")
    if text.rstrip("\n").endswith("owed next on 619/4690."):
        ok_heart = True
    else:
        if not text.endswith("\n"):
            text += "\n"
        payload = text + HEART_MSG + "\n"
        io.open(HEART, "wb").write(payload.encode("utf-8"))
        back = io.open(HEART, "rb").read().decode("utf-8")
        ok_heart = back.rstrip("\n").endswith("owed next on 619/4690.")
    sys.stdout.write("BACKLOG %s HEART %s\n"
                     % ("OK" if ok_backlog else "FAIL",
                        "OK" if ok_heart else "FAIL"))
    return 0 if ok_backlog and ok_heart else 2


if __name__ == "__main__":
    sys.exit(main())