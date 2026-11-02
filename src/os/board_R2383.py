"""board_R2383: stamp the claimed tech row and seed ONE measured gap row."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED = (
    "- [ ] P2 tech seed (R2383, from this window own measured seam): "
    "`src/os/owner_table_parity.py` - a tool's own block is now rendered from "
    "ONE shape, but the TABLE it is rendered from is still hand-written beside "
    "the parser that actually accepts the flags. Measured this window: "
    "`runner_arg_guard.guard_usage()` renders `GUARD_FLAGS = (\"--json\",)` "
    "while `runner_arg_guard.main()` accepts `--json`, `--guard-help` and `--` "
    "as literals inside its own loop, so a flag added to the loop silently "
    "never appears in the help block and nothing reads that. Product: one "
    "reader that derives a tool's declared own-flag table against the tokens "
    "its parser accepts and names every flag present in one and missing from "
    "the other. Criteria AC-OTP1..AC-OTP6 pre-registered HERE BEFORE any "
    "code: AC-OTP1 the reader takes the table and the parser source from the "
    "tool it is pointed at and names each flag on the side it is missing from; "
    "AC-OTP2 a tool whose table and parser agree reads PARITY-AGREES at exit 0 "
    "while a tool with one-sided flag reads PARITY-DISAGREES naming the flag "
    "and its side, so the reading is a property of the code and not a "
    "whitelist; AC-OTP3 the reader writes nothing and reads no clock; AC-OTP4 "
    "a tool with no own-flag table reads NO-TABLE at exit 2 rather than "
    "PARITY-AGREES by accident; AC-OTP5 exit 0 = AGREES, 2 = DISAGREES or "
    "NO-TABLE, 3 = missing path, 5 = bad flags, with a byte-stable --json over "
    "pinned keys; AC-OTP6 pure ASCII, stdlib only, zero network, plus its own "
    "reconcile label. Five anchors zero-occupancy at HEAD 2026-11-02: "
    "owner_table_parity, AC-OTP, E_OTP, os-owner-table-parity, "
    "test_owner_table_parity.\n")


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    marker = "- [ ] P2 tech seed (R2373, from this window own measured seam):"
    assert text.count(marker) == 1, text.count(marker)
    stamped = text.replace(
        marker,
        "- [x] [done 2026-11-02 R2383] P2 tech seed (R2373, from this window "
        "own measured seam):", 1)
    head, sep, tail = stamped.rpartition("\n- [ ]")
    assert sep, "no open row found to append after"
    rebuilt = head + "\n- [ ]" + tail + SEED
    with io.open(QUEUE, "w", encoding="utf-8", newline="") as handle:
        handle.write(rebuilt)
    print("before=%d after=%d" % (len(text.encode("utf-8")),
                                  len(rebuilt.encode("utf-8"))))


if __name__ == "__main__":
    main()