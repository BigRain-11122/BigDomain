"""R2404 board stamp: close the claimed tech row and seed the measured gap.

Done here rather than by hand so the exact bytes are proven (predicted
after-size, one atomic replace, read-back). The head anchor is verified unique
before any write.

Stdlib only, ASCII source, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BOARD = os.path.join(REPO, "state", "queue", "tech.md")

STAMP = "- [x] [done 2026-11-03 R2404]"

HEAD = ("- [ ] P2 tech seed (R2396, from this window own measured seam): "
        "`src/os/followup_bare_evidence_face.py`")

DISCHARGE = (
    "  DISCHARGED R2404 (line 476, AC-FBEF1..AC-FBEF6): "
    "src/os/followup_bare_evidence_face.py plus its suite shipped against the "
    "criteria pinned at R2396. The module owns ONE answer - the argument the "
    "four sections must receive - and asks matrix_evidence_pile_consistency at "
    "CALL time, so a bare evidence name resolves through the SAME measured "
    "pile the matrix section already used: <pile>/<basename>, while a name "
    "carrying a directory and a file already sitting at the root keep today's "
    "string byte for byte, and a name the pile law cannot place refuses with "
    "that law's own code instead of a guessed pile. battery_followup.main now "
    "goes through it, so the only face an operator walks agrees with the face "
    "that guards the pile. SUITE PASS 6/6 twice, identical criterion digest, "
    "three adjacent suites green (six adjacent suites re-run directly: "
    "battery_followup, matrix_evidence_pile_consistency, "
    "bare_evidence_pile_refusal, battery_followup_help_wire, "
    "followup_section_foreign_wire, followup_guard_evidence_scope), wired "
    "os-followup-bare-evidence-face(6). LIVE: the real tree reads "
    "reconcile-all-R2394-retry.log as pile=qa argument=qa\\<name> exists=yes "
    "where the old join to the root measured exists=no, which is exactly the "
    "MISSING EVIDENCE exit 3 the seed row described.")

GAP = ("- [ ] P2 tech seed (R2404, from this window own measured limit): "
       "`src/os/bare_evidence_deep_pile.py` - the CLI face now resolves a bare "
       "name through the measured pile, but that measurement only walks the "
       "root and its ONE-LEVEL subdirectories: MEASURED this window on a "
       "stand-in root, a bare name whose only copy lives at qa/rounds/<name> "
       "reads `file-exists=yes verdict=REFUSED code=E_BEPR_NOT_FOUND`, so an "
       "evidence file filed one level deeper is still invisible to both faces "
       "even though it is on disk. Product: the pile measurement walks a "
       "bounded, DECLARED depth (or refuses with a code that names the depth "
       "it searched) so a filed-away log is either found or reported as "
       "beyond the search rather than as absent. Criteria AC-BEDP1..AC-BEDP6 "
       "pre-registered HERE BEFORE any code: AC-BEDP1 a bare name at depth 2 "
       "under the root resolves and the argument names that path; AC-BEDP2 "
       "the depth is asked of the pile law at CALL time, so a patched depth "
       "moves this reading; AC-BEDP3 a name beyond the declared depth refuses "
       "with a code that names the depth searched, never E_BEPR_NOT_FOUND "
       "alone; AC-BEDP4 two copies within the searched depth still refuse as "
       "ambiguous rather than being chosen; AC-BEDP5 CLI 0/2/3/5 with a "
       "byte-stable --json; AC-BEDP6 writes nothing, reads no clock, ASCII, "
       "stdlib only, plus its own reconcile label and its own suite file.")


def main():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    before = len(raw.encode("utf-8"))
    if raw.count(HEAD) != 1:
        print("E_BOARD_ANCHOR_HEAD count=%d" % raw.count(HEAD))
        return 2
    lines = raw.split("\n")
    index = None
    for position, line in enumerate(lines):
        if line.startswith(HEAD):
            index = position
            break
    if index is None:
        print("E_BOARD_ANCHOR_HEAD not found")
        return 2
    lines[index] = STAMP + lines[index][len("- [ ]"):]
    lines.insert(index + 1, DISCHARGE)
    text = "\n".join(lines)
    if GAP in text:
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