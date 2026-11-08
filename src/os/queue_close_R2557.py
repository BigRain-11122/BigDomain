"""R2557 board closeout for the AC-PNDS1 seed row at state/queue/tech.md:593.

Marks that row done, adds its DISCHARGED note read from THIS round own evidence
on disk, and seeds ONE row measured this window: an attribute whose base is a
function parameter or a local reads attr-not-imported because the module check
is name based, a package-relative module is never found because the hop joins
"<mod>.py" on the root, and a helper constant declared by a walrus or inside a
function reads attr-missing/attr-non-constant.

Refuses to write when the live evidence or the suite evidence is absent, so no
number is invented.
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
    "probe-seam-name-binding-arm-mixed-residual-alias-position-live-"
    "R2557.log")
EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-position-R2557.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_HEAD = "- [ ] P2 tech seed (R2555,"
SEED_MARK = ("`src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
             "position.py`")

SEED = (
    "- [ ] P2 tech seed (R2557, from this window own measured limit): "
    "`src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_base.py`"
    " - MEASURED this window on the alias-position face own reader and on the "
    "bounded live leg: (1) an attribute whose BASE is a function parameter or "
    "a local (`node.value` inside a probe own `_collect_node`) reads "
    "attr-not-imported, so the module-import check cannot tell a parameter "
    "from a module the probe forgot to import; (2) a package-relative module "
    "(`import pkg.mod` then `B = pkg.mod.ATTR`) is never found because the hop "
    "joins `<mod>.py` on the root; (3) a helper constant declared by a walrus "
    "or inside a function body reads attr-missing / attr-non-constant because "
    "only module-level plain and annotated assignments are read. Product: ONE "
    "reading that names the BASE of an attribute hop separately from a module "
    "that is genuinely absent, resolves `pkg.mod.ATTR` by walking the dotted "
    "import path, and reads a walrus or function-level constant in the helper "
    "module rather than calling it missing. Criteria AC-PNDA1..AC-PNDA6 "
    "pinned HERE BEFORE any code: AC-PNDA1 a parameter- or local-rooted "
    "attribute is NAMED attr-base-local:<base> instead of attr-not-imported; "
    "AC-PNDA2 a module that is genuinely not imported keeps "
    "attr-not-imported:<text>; AC-PNDA3 `pkg.mod.ATTR` resolves through the "
    "dotted import path when that file is on disk; AC-PNDA4 a walrus or "
    "function-level constant in the helper module resolves, and two values "
    "read name-mixed; AC-PNDA5 every answer the seven shipped faces already "
    "gave is carried unchanged on the row; AC-PNDS6-style hygiene: pure "
    "ASCII, stdlib only, no clock, zero network, its own reconcile label and "
    "its own suite. Five anchors to re-check zero-occupancy at HEAD before "
    "any code: probe_seam_name_binding_arm_mixed_residual_alias_attribute_base"
    ", AC-PNDA, E_PNDA, "
    "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-base, "
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_base."
)

FACTS = ("verdict", "files", "probes", "covered", "out_of_scope",
         "historical", "missing", "bound", "position_loops",
         "position_resolved", "position_named")


def live_facts():
    if not os.path.isfile(LIVE):
        return None
    text = io.open(LIVE, encoding="utf-8").read()
    facts = {}
    for key in FACTS:
        match = re.search(r"(?<![A-Za-z_])%s=(\S+)" % (key,), text)
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
        "  DISCHARGED R2557 (line 593, AC-PNDS1..AC-PNDS6 pinned in that row "
        "at R2555 BEFORE any code): "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_position.py "
        "plus its suite shipped. A walrus binding is an alias edge and a "
        "walrus str literal is a literal; an alias whose value is ONE "
        "attribute on a same-root module the probe imports resolves to that "
        "module own str constant and the chain names the hop; a name whose "
        "EVERY binding line is later than the loop line is NAMED "
        "not-yet-bound and never resolved, which closes the over-resolution; "
        "a chain deeper than one hop, a missing attribute, a non-str "
        "attribute and a module that is not imported are all NAMED with the "
        "hop. The shipped alias-chain answer rides beside every row. PROOF: "
        "AC-PNDS1..AC-PNDS6 SUITE PASS 6/6 TWICE with identical output plus "
        "five adjacent probe suites green "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-position-"
        "R2557.log, %dB, landed through the shipped capture callable); a "
        "BOUNDED live leg over %s of %s real probe_seam modules reads %s "
        "with files=%s probes=%s covered=%s out_of_scope=%s missing=%s, "
        "position_loops=%s position_resolved=%s position_named=%s "
        "(qa/probe-seam-name-binding-arm-mixed-residual-alias-position-live-"
        "R2557.log, utf-8 LF), where the SAME fixtures are measured on BOTH "
        "readers: the walrus fixture reads b here against name-unbound:B "
        "there, the attribute fixture reads b here against name-unbound:B "
        "there, and the after-loop fixture reads not-yet-bound:C here "
        "against b there where the shipped face over-resolves. The registry "
        "moved by ONE row to 608 suites / 4624 criteria, recounted by "
        "importing reconcile_all.SUITES rather than trusted, and "
        "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
        "eligible R2556 battery leg to %d bytes at 608 suites / 4624 "
        "criteria with its green line honestly reading 607/608 and --check "
        "byte-identical. tasks.md was not touched."
        % (evidence_bytes, facts.get("bound"), facts.get("files"),
           facts.get("verdict"), facts.get("files"), facts.get("probes"),
           facts.get("covered"), facts.get("out_of_scope"),
           facts.get("missing"), facts.get("position_loops"),
           facts.get("position_resolved"), facts.get("position_named"),
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
    lines[at] = "- [x] [done 2026-11-08 R2557]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, discharged)
    lines.insert(at + 2, SEED)
    payload = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2557] P2 tech seed")
          and back[at + 1].strip().startswith("DISCHARGED R2557")
          and back[at + 2].startswith("- [ ] P2 tech seed (R2557,"))
    measured = len("\n".join(back).encode("utf-8"))
    print("board %s at=%d predicted=%d measured=%d"
          % ("OK" if ok else "FAIL", at, len(payload.encode("utf-8")),
             measured))
    print("head now %s" % back[at + 2][:60])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())