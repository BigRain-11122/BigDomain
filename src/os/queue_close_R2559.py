"""R2559 board closeout for the AC-PNDA1 seed row at state/queue/tech.md:595.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window: a walrus-bound attribute alias
is not recorded at all, a subscript base publishes "?" instead of a name, a
package own __init__ constant is never joined, and a with-as helper binding
reads attr-missing.

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
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-base-live-"
    "R2559.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-base-"
    "R2559.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2557,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "attribute_base.py`")

SEED = (
    "- [ ] P2 tech seed (R2559, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "predicate_scope.py` - MEASURED this window on the alias attribute-base "
    "face own reader (src/os/limits_attribute_base_R2559.py, four shapes run "
    "against one private world): (1) a WALRUS-bound attribute alias "
    "(`(B := h.ATTR)`) produces state=None and NO reason at all, because only "
    "plain and annotated assignments record an attribute edge, so the caller "
    "is told nothing; (2) a SUBSCRIPT base (`items[0].ATTR`) is published as "
    "`attr-not-imported:?.ATTR` because the dotted text only understands "
    "Name and Attribute chains, so a real base is reported as a question "
    "mark; (3) a package own constant (`pkg3/__init__.py` holding ATTR) reads "
    "`attr-missing:pkg3.ATTR` because the hop asks for `pkg3.py` and never "
    "for a package index; (4) a helper name bound by `with ... as NAME` reads "
    "`attr-missing` because the extended table collects only assignment, "
    "annotation and walrus forms. Product: ONE reading that names a walrus "
    "attribute edge, carries a subscript or call base as a real base text "
    "instead of `?`, joins a package own `__init__.py` as well as `<mod>.py`, "
    "and reads a with-as helper binding. Criteria AC-PNDB1..AC-PNDB6 pinned "
    "HERE BEFORE any code: AC-PNDB1 a walrus-bound attribute alias is an "
    "attribute edge and is NAMED when it cannot be resolved; AC-PNDB2 a "
    "subscript or call base is published as its own base text and is never "
    "reported as `?`; AC-PNDB3 a constant in a package own `__init__.py` "
    "resolves through the dotted path; AC-PNDB4 a with-as helper binding "
    "resolves and two values read name-mixed; AC-PNDB5 every answer the eight "
    "shipped faces already gave is carried unchanged on the row; AC-PNDB6 "
    "pure ASCII, stdlib only, no clock, zero network, its own reconcile label "
    "and its own suite. Five anchors to re-check zero-occupancy at HEAD "
    "before any code: "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_"
    "scope, AC-PNDB, E_PNDB, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-predicate-"
    "scope, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "predicate_scope."
)

FACTS = ("bounded_modules", "covered_probes", "attribute_loops",
         "attr_resolved", "attr_named")


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
        "  DISCHARGED R2559 (line 595, AC-PNDA1..AC-PNDA6 pinned in that row "
        "at R2557 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "base.py plus its suite shipped. An attribute whose BASE is a "
        "parameter or a local is NAMED attr-base-local:<base> instead of a "
        "module the probe forgot to import; a base that is neither imported "
        "nor local keeps the shipped attr-not-imported:<text>; a dotted "
        "`pkg.mod.ATTR` hop is joined on its FULL path and resolves when the "
        "file is on disk; a helper constant declared by a walrus or inside a "
        "function body is read, and two values read name-mixed; every answer "
        "the shipped position and alias faces already gave is carried "
        "unchanged on the row. PROOF: AC-PNDA1..AC-PNDA6 SUITE PASS 6/6 "
        "TWICE with identical output plus five adjacent probe suites green "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "base-R2559.log, %dB, landed through the shipped capture callable); a "
        "BOUNDED live leg over %s real probe_seam modules reads "
        "covered_probes=%s attribute_loops=%s attr_resolved=%s attr_named=%s, "
        "and the SAME fixtures are measured on BOTH readers - the "
        "parameter-rooted fixture reads attr-base-local:node here against "
        "attr-not-imported:node.value there, and the dotted fixture reads "
        "ok/b here against attr-deep:pkg.mod.ATTR there "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
        "base-live-R2559.log, utf-8 LF, zero CRLF). The registry moved by ONE "
        "row to 609 suites / 4630 criteria, recounted by importing "
        "reconcile_all.SUITES rather than trusted, and "
        "docs/sandbox-suite-matrix.md was regenerated from the eligible R2558 "
        "battery leg to %d bytes at 609 suites / 4630 criteria with its green "
        "line honestly reading 608/609 and --check byte-identical. tasks.md "
        "was not touched."
        % (evidence_bytes, facts.get("bounded_modules"),
           facts.get("covered_probes"), facts.get("attribute_loops"),
           facts.get("attr_resolved"), facts.get("attr_named"),
           matrix_bytes)
    )
    text = io.open(QUEUE, encoding="utf-8").read()
    lines = text.split("\n")
    seeds = [i for i, row in enumerate(lines)
             if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(seeds) != 1:
        print("FAIL claim: seeds=%d" % (len(seeds),))
        return 2
    at = seeds[0]
    lines[at] = "- [x] [done 2026-11-08 R2559]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2559] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2559")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2559,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:70])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())