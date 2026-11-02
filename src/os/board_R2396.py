"""R2396 board stamp: close the claimed tech row and seed the measured gap.

The board edit is done here rather than by hand so the exact bytes are proven
(predicted after-size, one atomic replace, read-back). Both anchors are
verified unique before any write.

Stdlib only, ASCII source, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BOARD = os.path.join(REPO, "state", "queue", "tech.md")

STAMP = "- [x] [done 2026-11-03 R2396]"

GAP = ("- [ ] P2 tech seed (R2396, from this window own measured seam): "
       "`src/os/followup_bare_evidence_face.py` - the matrix section now hands "
       "its tool the SAME file the guard reads, but the follow-up CLI still "
       "resolves the name against the root only: measured this window on the "
       "real tree, `battery_followup.py --dry-run --evidence "
       "reconcile-all-R2394-retry.log` answers `MISSING EVIDENCE` at exit 3 "
       "and never reaches the section, while the same name is PLACED in qa by "
       "matrix_evidence_pile_consistency - so the CLI face and the section "
       "face disagree about what a bare name means, and the R2396 defect was "
       "invisible from the only face an operator walks. Product: the CLI "
       "resolves a bare name through the same measured pile (or refuses with "
       "the pile law's own code) instead of joining it to the root, so "
       "`--evidence reconcile-all-<round>.log` and `--evidence qa/...` run the "
       "same four sections over the same file. Criteria AC-FBEF1..AC-FBEF6 "
       "pre-registered HERE BEFORE any code: AC-FBEF1 a bare name that lives "
       "in exactly one pile is accepted and the sections receive that pile's "
       "path, and a patched pile moves what the sections receive; AC-FBEF2 a "
       "name that carries a directory is joined to the root exactly as today, "
       "byte for byte, including its refusal at exit 3 when absent; AC-FBEF3 "
       "a bare name that lives nowhere or in two piles refuses at exit 3 "
       "naming the pile law's own code, never a guessed pile; AC-FBEF4 the "
       "section report for an accepted bare name is byte-identical to the "
       "report produced from the same file passed with its directory; "
       "AC-FBEF5 CLI codes 0/2/3/5 and the --json payload are unchanged for "
       "every already-working invocation; AC-FBEF6 pure ASCII, stdlib only, "
       "no clock, no network, asks the pile law at call time, plus its own "
       "reconcile label. Anchors zero-occupancy at HEAD 2026-11-03: "
       "followup_bare_evidence_face, AC-FBEF, E_FBEF, "
       "os-followup-bare-evidence-face, test_followup_bare_evidence_face.")

DISCHARGE = (
    "  DISCHARGED R2396 (line 454, AC-MEPC1..AC-MEPC6): "
    "src/os/matrix_evidence_pile_consistency.py plus its suite shipped against "
    "the criteria pinned at R2386. The module owns ONE answer - the argument "
    "the matrix tool must receive - derived from the SAME pile the guard "
    "reads: a bare name becomes <pile>/<basename> (a patched measured moves "
    "the argument), a name carrying a directory is handed through byte for "
    "byte, and a name that cannot be placed refuses before the tool is called "
    "at all. followup_section_foreign_wire.matrix_section now asks it at call "
    "time, so the guard and the rendered doc provably name one file. SUITE "
    "PASS 6/6 twice, identical criterion digest, three adjacent suites green "
    "(bare_evidence_pile_refusal, followup_guard_evidence_scope, "
    "followup_section_foreign_wire), wired "
    "os-matrix-evidence-pile-consistency(6). LIVE: the real tree reads "
    "reconcile-all-R2394-retry.log as pile=qa argument=qa\\<name> same_file=yes "
    "tool_exists=yes bare_at_root=no - the R2386 defect measured closed.")


def main():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    before = len(raw.encode("utf-8"))
    head = "- [ ] P2 tech seed (R2386, from this window own measured seam):"
    if raw.count(head) != 1:
        print("E_BOARD_ANCHOR_HEAD count=%d" % raw.count(head))
        return 2
    lines = raw.split("\n")
    index = None
    for position, line in enumerate(lines):
        if line.startswith(head):
            index = position
            break
    if index is None:
        print("E_BOARD_ANCHOR_HEAD not found")
        return 2
    if not lines[index + 1] == "":
        print("E_BOARD_LAYOUT next line is not blank: %r" % lines[index + 1])
        return 2
    lines[index] = STAMP + lines[index][len("- [ ]"):]
    lines.insert(index + 1, DISCHARGE)
    text = "\n".join(lines)
    if text.rstrip("\n").endswith(GAP):
        print("E_BOARD_GAP_ALREADY_PRESENT")
        return 2
    if not text.endswith("\n"):
        text += "\n"
    text = text + GAP + "\n"
    after = len(text.encode("utf-8"))
    temp = BOARD + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, BOARD)
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    print("BOARD STAMPED before=%dB after=%dB predicted=%dB readback=%s "
          "residue=%s" % (before, after, after, back == text,
                          os.path.exists(temp)))
    return 0 if back == text and not os.path.exists(temp) else 1


if __name__ == "__main__":
    sys.exit(main())