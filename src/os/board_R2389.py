"""board_R2389 - stamp the claimed row and seed one measured gap row.

Predicted-delta discipline: the two edits are exact, the file is written once,
and the caller proves the byte count against this script's own prediction.
"""

import io
import sys

PATH = "state/queue/tech.md"
STAMP_FROM = "- [ ] P2 tech seed (R2388, from this window own measured seam):"
STAMP_TO = ("- [x] [done 2026-11-02 R2389] P2 tech seed (R2388, from this "
            "window own measured seam):")

SEED = (
    "- [ ] P2 tech seed (R2389, from this window own measured seam): "
    "`src/os/declaration_writer_dialect_preservation.py` - the four writers "
    "now ask ONE NOOP comparison before they replace a declaration, so a "
    "document that already carries the composition is never rewritten. That "
    "fixes the POINTLESS write and leaves the REAL one: measured this window "
    "at the source, `residue_triage_append.compose` builds its entry with "
    "hard-coded `\\n` and `apply` encodes the whole document as UTF-8 LF, so a "
    "genuine append to a CRLF declaration silently converts every line of the "
    "file (the same transport rewrite R2388 closed for the no-op case, now on "
    "the content case), and head renew/entry retire carry the same shape. "
    "Product: a writer that rewrites a document it actually changed keeps the "
    "declaration's OWN dialect - the inserted or removed region is rendered in "
    "the detected dialect and every untouched byte stays byte-identical - or "
    "refuses rather than converting, and the dialect is reported on the "
    "existing report line. Criteria AC-DWPP1..AC-DWPP6 pre-registered HERE "
    "BEFORE any code: AC-DWPP1 an append to a CRLF declaration lands and the "
    "result is still CRLF with every untouched line byte-identical; AC-DWPP2 "
    "an LF declaration keeps today's bytes exactly (the change is dialect "
    "preservation, not a re-render); AC-DWPP3 the NOOP path still writes "
    "nothing on all four writers; AC-DWPP4 every refusal code, exit code and "
    "printed line of the three writers is unchanged, proven by running each "
    "CLI on the same world before and after; AC-DWPP5 the dialect is taken "
    "from the SHARED law (repin_noop_eol_dialect.dialect_of, asked at call "
    "time) so a patched reading moves all four faces; AC-DWNP-style purity: "
    "pure ASCII, stdlib only, zero network, no clock, plus its own reconcile "
    "label. Five anchors to re-check zero-occupancy at HEAD before any code: "
    "declaration_writer_dialect_preservation, AC-DWPP, E_DWPP, "
    "os-declaration-writer-dialect-preservation, "
    "test_declaration_writer_dialect_preservation."
)


def main(path=PATH):
    with io.open(path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(STAMP_FROM) != 1:
        sys.stdout.write("REFUSE stamp anchor found %d times\n"
                         % text.count(STAMP_FROM))
        return 2
    stamped = text.replace(STAMP_FROM, STAMP_TO, 1)
    if not stamped.endswith("\n"):
        stamped += "\n"
    after = stamped + SEED + "\n"
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(after)
    sys.stdout.write("BOARD STAMPED row=AC-DWNP1 seeded=AC-DWPP1 "
                     "before=%d after=%d\n"
                     % (len(text.encode("utf-8")),
                        len(after.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())