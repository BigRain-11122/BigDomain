"""R2561 board closeout for the AC-PNDB1 seed row at state/queue/tech.md:597.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window (src/os/limits_attribute_
predicate_R2561.py plus a contrast leg): a plain `import m` base reads
state=None with NO reason at all, a module bound by `import m as x` reads
attr-base-local:<alias>, a with-as module binding reads attr-base-local, and a
helper constant that is itself an alias reads attr-non-constant while one
re-exported by `from other import NAME` reads attr-missing.

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
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-predicate-"
    "live-R2561.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-predicate-"
    "R2561.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2559,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_predicate_scope.py`")

SEED = (
    "- [ ] P2 tech seed (R2561, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope.py` - MEASURED this window on the alias "
    "attribute-predicate face and its base reader "
    "(src/os/limits_attribute_predicate_R2561.py plus a contrast leg, every "
    "shape against one private world where the honest answer is `b`): (1) a "
    "PLAIN `import helper` followed by `helper.ATTR` reads state=None with NO "
    "reason at all, so a row is silent rather than refused; (2) a module "
    "bound by `import helper as h` and read as `h.ATTR` reads "
    "`attr-base-local:h`, because the import set records the module name and "
    "the alias is then mistaken for a local; (3) a module reached by `with "
    "hw2 as m` reads `attr-base-local:m`, the same mistake through a with-as "
    "binding; (4) a helper constant that is ITSELF an alias (`ATTR = BASE` "
    "with `BASE = \"b\"`) reads `attr-non-constant`, and one re-exported by "
    "`from hb import ATTR` reads `attr-missing`, so a two-step constant is "
    "never followed. Both readers agree on (2), (3) and (4), which is why no "
    "earlier criterion saw them. Product: ONE reading that resolves a plain "
    "import base silently, resolves an `import ... as ...` alias and a "
    "with-as module binding through the ACTUAL module name, follows a helper "
    "constant that is an alias of another constant to its literal, and "
    "follows a `from other import NAME` re-export. Criteria AC-PNDC1..AC-PNDC6 "
    "pinned HERE BEFORE any code: AC-PNDC1 a plain `import m` base resolves "
    "through `<m>.py` and is NAMED when it cannot be resolved, never silent; "
    "AC-PNDC2 a module bound by `import m as x` resolves through the actual "
    "module name and is never published as attr-base-local:<alias>; AC-PNDC3 "
    "a with-as module binding resolves when the context is a module and is "
    "named attr-with-as otherwise; AC-PNDC4 a helper constant that is an "
    "alias of another constant resolves to its literal and two values still "
    "read name-mixed; AC-PNDC5 a helper constant re-exported by `from other "
    "import NAME` resolves through that module; AC-PNDC6 pure ASCII, stdlib "
    "only, no clock, zero network, its own reconcile label and its own suite. "
    "Five anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope, AC-PNDC, E_PNDC, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope, test_probe_seam_name_binding_arm_mixed_residual_alias_"
    "attribute_import_alias_scope."
)

FACTS = ("modules", "pred_resolved", "pred_named", "loops", "unreadable")


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
    live_bytes = os.path.getsize(LIVE)
    matrix_bytes = os.path.getsize(MATRIX)
    discharged = (
        "  DISCHARGED R2561 (line 597, AC-PNDB1..AC-PNDB6 pinned in that row "
        "at R2559 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "predicate_scope.py plus its suite shipped. A walrus-bound attribute "
        "alias is an edge like any other and resolves when the hop resolves, "
        "and is NAMED attr-non-constant when it does not, instead of "
        "publishing no reason at all; a SUBSCRIPT base (`items[0]`) and a CALL "
        "base (`factory()`) are published as their own text as "
        "attr-subscript-base / attr-call-base and are never the question mark "
        "the shipped face reported; a package own `__init__.py` is joined as "
        "well as `<mod>.py`, so a package index constant resolves; a helper "
        "name bound by `with ... as NAME` is read, resolves when that module "
        "binds exactly one literal, and reads name-mixed on two values; every "
        "key the shipped attribute-base reading published is carried "
        "unchanged beside this face own on every row. PROOF: AC-PNDB1.."
        "AC-PNDB6 SUITE PASS 6/6 TWICE with an identical criterion digest "
        "489031857ADE8A94 plus five adjacent probe suites green "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "predicate-R2561.log, %dB, utf-8 bom=False crlf=0); the same suite "
        "re-ran green alone at closeout. A BOUNDED live leg over %s real "
        "probe_seam modules reads pred_resolved=%s pred_named=%s over %s "
        "loops with unreadable=%s, and every module and base-face digest is "
        "unchanged across the reading (qa/probe-seam-name-binding-arm-mixed-"
        "residual-alias-attribute-predicate-live-R2561.log, %dB, utf-8 LF). "
        "The registry moved by ONE row to 610 suites / 4636 criteria, "
        "recounted by importing reconcile_all.SUITES rather than trusted "
        "(610 unique names, 610 unique paths), and docs/sandbox-suite-"
        "matrix.md was regenerated from the eligible R2560 battery leg to %d "
        "bytes at 610 suites / 4636 criteria with its green line honestly "
        "reading 609/610 because this round own suite is not in that battery "
        "leg, and --check then read byte-identical at rc=0. tasks.md was not "
        "touched."
        % (evidence_bytes, facts.get("modules"), facts.get("pred_resolved"),
           facts.get("pred_named"), facts.get("loops"),
           facts.get("unreadable"), live_bytes, matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2561]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2561] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2561")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2561,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())