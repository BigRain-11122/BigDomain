"""board writer for R2501: close the claimed tech row and seed two measured gaps.

Dry run by default (writes nothing). --execute performs ONE atomic replace with
a byte read-back. The claimed row is state/queue/tech.md:535 (prefix AC-CEPM1,
criteria pinned at R2454 BEFORE any code).
"""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BOARD = os.path.join(REPO, "state", "queue", "tech.md")
LINE_NO = 535
CLAIM_MARK = "- [ ] P2 tech seed (R2454,"
ACCEPT = "- [ ] P2 tech seed (R2478,"
PATTERNS = "- [ ] P2 tech seed (R2494, from this window own measured limit): `src/os/patterns_label_readability.py`"

DISCHARGED = (
    "  DISCHARGED R2501 (line 535, AC-CEPM1..AC-CEPM6 pinned at R2454 BEFORE "
    "any code): src/os/closeout_export_parity_text_binding.py plus its suite "
    "shipped. The binding is asked through the SHIPPED composition at CALL time "
    "(closeout_export_parity_wire.compose, proved by patching it and watching "
    "the refusal appear), the comparison normalises line endings ONLY so "
    "transport stays the target own business, and a composition made from a "
    "DIFFERENT document is refused with E_CEPM_BINDING naming the first "
    "differing field from the shipped difference law before any byte is "
    "staged, leaving the target byte-identical with no residue. The wire seven "
    "reading keys keep their names, positions and values; binding and differs "
    "are strictly additional. Proof: AC-CEPM1..AC-CEPM6 SUITE PASS 21/21 TWICE "
    "with identical verdicts plus three adjacent suites green "
    "(qa/closeout-export-parity-text-binding-R2501.log, 2898B, legs=2 "
    "identical=True adjacent=3 fails=0). MEASURED on the REAL tree: the "
    "shipped export composes to "
    "itself with difference=(none) at 215518 bytes, publishing that same "
    "composition reads WRITTEN/BOUND, and a composition made from a doctored "
    "copy reads REFUSED with differs=self_drive.window_days while the target "
    "stays byte-identical and no .parity-stage residue exists "
    "(qa/closeout-export-parity-text-binding-live-R2501.log). Wired "
    "os-closeout-export-parity-text-binding(6) so the registry reads 579 "
    "suites / 4450 criteria, recounted by importing reconcile_all.SUITES "
    "rather than quoted."
)

SEED_BINDING = (
    "- [ ] P2 tech seed (R2501, from this window own measured limit): "
    "`src/os/closeout_export_parity_wire_binding_consumer.py` - R2501 shipped a "
    "binding face, but MEASURED this window the wire it guards still trusts its "
    "caller: `git grep -c CEPW.publish(REPO, EXPORT, text=text)` over src/os "
    "reads TWELVE closeout scripts handing their own composed text straight to "
    "closeout_export_parity_wire.publish, and not one of them asks the binding, "
    "so the new face only protects the callers that choose it. Product: the "
    "caller set is DERIVED from the tree at CALL time and each caller is "
    "reported BOUND / UNBOUND (naming the file and the first differing field) / "
    "OUT-OF-SCOPE, so a closeout that hands in another document composition is "
    "named rather than run. Criteria AC-CEPB1..AC-CEPB6 pre-registered HERE "
    "BEFORE any code: AC-CEPB1 the caller set is derived from the shipped tree "
    "at CALL time, never a hardcoded list; AC-CEPB2 a caller that hands in its "
    "OWN document composition reads BOUND and its bytes are unchanged; AC-CEPB3 "
    "a caller whose text is another document composition reads UNBOUND naming "
    "the file and the first differing field, and the caller is not run; "
    "AC-CEPB4 a file that does not call the wire publish reads OUT-OF-SCOPE "
    "rather than being silently counted; AC-CEPB5 the reading writes nothing "
    "and changes no caller bytes; AC-CEPB6 pure ASCII, stdlib only, no clock, "
    "zero network, own reconcile label and suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: closeout_export_parity_wire_binding_consumer, "
    "AC-CEPB, E_CEPB, os-closeout-export-parity-wire-binding-consumer, "
    "test_closeout_export_parity_wire_binding_consumer."
)

SEED_ORDER = (
    "- [ ] P2 tech seed (R2501, from this window own measured limit): "
    "`src/os/export_parity_difference_order_field.py` - the refusal R2501 "
    "ships names its field through export_closeout_gate_parity.first_difference, "
    "and MEASURED this window that law answers the SHAPE WORD `bytes` when the "
    "only difference is key ORDER: `{\"x\": 1, \"y\": 2}` against "
    "`{\"y\": 2, \"x\": 1}` reads `bytes`, while a real value difference reads "
    "`y`. So an operator refused for a reordered document is told nothing, and "
    "the R2501 refusal inherits that blind spot. Product: the order-only "
    "difference is named by the first key that moved, beside - never instead of "
    "- the shipped answer, so a value difference keeps the field the shipped law "
    "names. Criteria AC-DFOB1..AC-DFOB6 pre-registered HERE BEFORE any code: "
    "AC-DFOB1 the reading asks the shipped difference law at CALL time and "
    "publishes its answer unchanged; AC-DFOB2 an order-only difference is named "
    "by the first key that moved, proved in BOTH orders, instead of a shape "
    "word; AC-DFOB3 a real value difference still names exactly the field the "
    "shipped law names; AC-DFOB4 byte-identical texts read no difference and an "
    "unparseable pair still reads the shipped shape word; AC-DFOB5 read-only: "
    "writes nothing and reads no clock; AC-DFOB6 pure ASCII, stdlib only, zero "
    "network, own reconcile label and suite. Five anchors to re-check "
    "zero-occupancy at HEAD before any code: export_parity_difference_order_field, "
    "AC-DFOB, E_DFOB, os-export-parity-difference-order-field, "
    "test_export_parity_difference_order_field."
)


def main(argv):
    execute = "--execute" in argv
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")
    if len(lines) < LINE_NO:
        print("E_B2501 SHORT board lines=%d" % len(lines))
        return 3
    target = lines[LINE_NO - 1]
    if not target.startswith(CLAIM_MARK):
        print("E_B2501_NOT_THE_CLAIM line=%d head=%r" % (LINE_NO, target[:60]))
        return 3
    if ACCEPT not in text:
        print("W_NOTE the carried AC-RSC1 row is not on this board")
    lines[LINE_NO - 1] = target.replace("- [ ] ", "- [x] [done 2026-11-07 R2501] ", 1)
    lines.insert(LINE_NO, DISCHARGED)
    lines.append(SEED_BINDING)
    lines.append(SEED_ORDER)
    composed = "\n".join(lines)
    print("PLAN board=%s bytes=%d->%d rows=%d->%d"
          % (BOARD, len(text.encode("utf-8")), len(composed.encode("utf-8")),
             len(text.split("\n")), len(lines)))
    if not execute:
        print("DRY no byte written")
        return 0
    handle, temp = tempfile.mkstemp(prefix="board-R2501-",
                                    dir=os.path.dirname(BOARD))
    os.close(handle)
    try:
        with io.open(temp, "w", encoding="utf-8", newline="") as out:
            out.write(composed)
        os.replace(temp, BOARD)
    finally:
        if os.path.exists(temp):
            os.remove(temp)
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    print("WROTE bytes=%d readback=%s" % (len(back.encode("utf-8")),
                                          back == composed))
    return 0 if back == composed else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))