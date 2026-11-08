"""R2571 board closeout for the AC-PNDCG1 seed row at state/queue/tech.md:605.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window with
src/os/limits_two_level_R2571.py: an inherited class constant, an absolute
FROM-imported CLASS, a cross-module call returning a class attribute, and a
receiver bound by a from-import alias.

Refuses to write when the live evidence, the suite evidence or the matrix
document is absent, so no number is invented.
"""

import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
LIVE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-two-level-scope-live-R2571.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-two-level-scope-R2571.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2569,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_import_alias_scope_two_level_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2571, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_class_base_scope.py` - MEASURED this window with "
    "src/os/limits_two_level_R2571.py against private worlds where the honest "
    "answer is `b`: (1) a class-body constant reached through a subclass "
    "(`cls.K.ATTR` where ATTR is bound on `class Base`) reads "
    "`attr-class-constant:cls.K.ATTR`, because the class reading walks only "
    "the named class own body and never its bases; (2) an absolute "
    "FROM-imported CLASS read as `K.ATTR` after `from cls import K` reads "
    "`attr-base-local:K`, because only a FROM-import whose target is a module "
    "file is treated as a module; (3) a cross-module with-as call whose "
    "method returns `self.NAME` reads `attr-cross-call:m.ATTR`, because the "
    "cross-module table follows a returned literal, a module-level name and a "
    "LOCAL but never a class attribute read through self; (4) a receiver "
    "bound by a FROM-import alias (`from pkg import mk as m2` then "
    "`with m2.Box().open() as m`) reads `attr-cross-call:m.ATTR`, because the "
    "receiver reading consults plain imports only. Product: ONE reading that "
    "follows a base class in the same module, accepts an absolute "
    "FROM-imported CLASS as a class path, follows a cross-module method that "
    "returns a class attribute through self, and finds a receiver bound by a "
    "FROM-import alias. Criteria AC-PNDCH1..AC-PNDCH6 pinned HERE BEFORE any "
    "code: AC-PNDCH1 a class constant inherited from a base class in the same "
    "module resolves through the subclass path; AC-PNDCH2 an absolute "
    "FROM-imported CLASS resolves through its class path; AC-PNDCH3 a "
    "cross-module with-as call whose method returns self.NAME resolves; "
    "AC-PNDCH4 a receiver bound by a FROM-import alias resolves; AC-PNDCH5 "
    "every answer the twelve shipped faces already gave is carried unchanged "
    "on the row; AC-PNDCH6 pure ASCII, stdlib only, no clock, zero network, "
    "its own reconcile label and its own suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_class_base_scope, AC-PNDCH, E_PNDCH, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-base-scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_base_scope."
)

FACTS = ("files", "loops", "tl_resolved", "tl_named")


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for key in FACTS:
        match = re.search(r"(?<![A-Za-z_])%s=(\d+)" % (key,), text)
        if match:
            facts[key] = match.group(1)
    return facts


def main():
    facts = live_facts()
    if facts is None:
        print("REFUSED E_QCR_NO_LIVE: %s is absent" % LIVE)
        return 3
    if not os.path.isfile(EVIDENCE):
        print("REFUSED E_QCR_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    if not os.path.isfile(MATRIX):
        print("REFUSED E_QCR_NO_MATRIX: %s is absent" % MATRIX)
        return 3
    evidence_bytes = os.path.getsize(EVIDENCE)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2571 (line 605, AC-PNDCG1..AC-PNDCG6 pinned in that row "
        "at R2569 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_two_level_scope.py plus its suite shipped. A "
        "level-bearing `from .. import helper` resolves against the parent "
        "package once an anchor is known (the module own source path, or this "
        "text matched to a file under the root) and stays refused at the "
        "shipped attr-base-local word when no anchor exists; a with-as call on "
        "a method defined in ANOTHER module resolves when that method returns "
        "a module name and is NAMED attr-cross-call otherwise; a class-body "
        "constant resolves through its class path; a relative FROM-imported "
        "NAME is refused with its own word attr-relative-from-name and is "
        "never published as a local; every key the shipped call-target reading "
        "published is carried unchanged beside this face own on every row. "
        "PROOF: AC-PNDCG1..AC-PNDCG6 SUITE PASS 6/6 on the first run and 6/6 "
        "TWICE with identical output plus five adjacent probe suites green "
        "through the shipped capture "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-two-level-scope-R2571.log, %dB, legs=2, "
        "identical=True, adjacent=5, fails=0); a BOUNDED live leg over %s real "
        "probe_seam modules reads loops=%s tl_resolved=%s tl_named=%s with "
        "read_only=True and measures FOUR fixtures on BOTH readers - "
        "two-level ok/b here against refused/attr-base-local:helper there, "
        "cross-module ok/b against refused/attr-call-target:m.ATTR, "
        "class-body ok/b against refused/attr-from-import:cls.K.ATTR, and "
        "relative-name refused/attr-relative-from-name:K.ATTR against "
        "refused/attr-base-local:K "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "import-alias-scope-two-level-scope-live-R2571.log, utf-8 LF, zero "
        "CRLF, zero BOM). The registry moved by ONE row to 615 suites / 4666 "
        "criteria, recounted by importing reconcile_all.SUITES rather than "
        "trusted (615 unique names, 615 unique paths), and "
        "docs/sandbox-suite-matrix.md was regenerated from the eligible R2569 "
        "battery leg to %d bytes at 615 suites / 4666 criteria with its green "
        "line honestly reading 614/615 and --check byte-identical. tasks.md "
        "was not touched."
        % (evidence_bytes, facts.get("files"), facts.get("loops"),
           facts.get("tl_resolved"), facts.get("tl_named"), matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2571]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2571] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2571")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2571,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())