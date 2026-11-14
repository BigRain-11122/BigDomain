"""Close the tech queue head row R2742 discharged (order-field face)."""

import io

PATH = "state/queue/tech.md"
NEEDLE = "- [ ] P2 tech seed (R2501, from this window own measured limit): `src/os/export_parity_difference_order_field.py`"

DISCHARGE = (
    " DISCHARGED R2742: shipped src/os/export_parity_difference_order_field.py "
    "plus its six-criteria suite. The blind spot was RE-MEASURED on the shipped "
    "law before any byte and it is real: first_difference answers the shape word "
    "bytes for a reordered document and a value difference still names its own "
    "field. This face asks that law on its module at CALL time, publishes the "
    "answer unchanged in differs, and adds order_field naming the FIRST KEY THAT "
    "MOVED in BOTH orders (x then y on the two-key pair, b then c on a three-key "
    "pair, a.x then a.y nested, rows[0].x then rows[0].y through a list) plus a "
    "FORMAT verdict for a whitespace-only difference; a value difference keeps "
    "the shipped field and claims no order. SUITE PASS 6/6 twice with an "
    "IDENTICAL digest DC582D20F8A0EA12 (qa/export-parity-difference-order-field-"
    "R2742b.log, 8139B, utf-8 LF, landed BY the shipped capture callable) and "
    "three adjacent suites green at rc=0 (fails=0). LIVE on the REAL document: "
    "docs/status-export.json against itself reads IDENTICAL 411953B, and the "
    "SAME document re-emitted in sorted key order reads differs=bytes ORDER-ONLY "
    "order_field=export_ts - the shipped law alone would have said bytes. wired "
    "os-export-parity-difference-order-field(6) -> registry 675/5026 to 676/5032 "
    "measured by import on four axes; matrix restamped stamp-aligned at 71635B "
    "after --check read stale with NO byte written, and --check is now byte-"
    "identical rc=0."
)


def main():
    text = io.open(PATH, "rb").read().decode("utf-8")
    lines = text.split("\n")
    hits = [index for index, line in enumerate(lines)
            if line.startswith(NEEDLE)]
    if len(hits) != 1:
        print("E_BOARD expected exactly 1 head row, found %d" % (len(hits),))
        return 2
    index = hits[0]
    row = lines[index]
    if not row.startswith("- [ ]"):
        print("E_BOARD head row already closed at line %d" % (index + 1,))
        return 2
    lines[index] = ("- [x] [done 2026-11-15 R2742]" + row[len("- [ ]"):]
                    + DISCHARGE)
    io.open(PATH, "wb").write(("\n".join(lines)).encode("utf-8"))
    print("lines=%d closed_row=%d bytes=%d"
          % (len(lines), index + 1,
             len("\n".join(lines).encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
