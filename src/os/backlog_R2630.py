"""backlog_R2630 - land this round own done row at the head of the claim board.

The row is built from this round own measured numbers, and the write is refused
when the anchor line is not found exactly once or when the row already exists.
"""

import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(BASE, "src", "os", "backlog.md")

ROW = (
    "- [x] [done 2026-11-11 R2630] R2630 PRODUCT window on the queue head the "
    "debt gate named (product-face-R2628, state/queue/tech.md:653 prefix "
    "AC-EDMI1, criteria AC-EDMI1..AC-EDMI6 pinned there at R2624 BEFORE any "
    "code). SHIPPED an in-place extension of "
    "src/os/suite_matrix_reconcile.py plus its own six-criteria suite "
    "src/os/test_suite_matrix_reconcile_row_membership.py: table membership is "
    "decided by the SEPARATOR row a header carries (is_second_table_header "
    "asks whether the next significant row is a separator of the SAME cell "
    "count) instead of by a digit in the first cell, so a malformed row whose "
    "first cell is not numeric is ONE non-row and the count falls by one "
    "instead of collapsing, while a row followed by a separator of its own "
    "width still ENDS the first table and the footer/total row stays a "
    "non-row. The gap was MEASURED BEFORE any byte with "
    "src/os/limits_matrix_reconcile_row_membership_R2630.py (delta -643 on a "
    "643-row registry) and the same script re-run after the change reads "
    "delta -1 with the three neighbour shapes unmoved. PROOF: "
    "AC-EDMI1..AC-EDMI6 SUITE PASS 6/6 on the first run and 6/6 TWICE "
    "identical through the shipped capture callable "
    "(qa/suite-matrix-reconcile-row-membership-R2630.log, 1857B, legs=2 "
    "identical=True adjacent=3 fails=0, digest 416AB5BAA29629DE) plus six "
    "adjacent matrix suites 6/6 rc=0. REGISTRY 643/4834 -> 644/4840 recounted "
    "by import; docs/sandbox-suite-matrix.md regenerated through the shipped "
    "write face at the R2627 green leg to 65817B and read byte-identical at "
    "rc=0. BOARD: row 653 closed at its predicted and measured 1898873B -> "
    "1903678B with its DISCHARGED note and ONE row seeded as "
    "AC-EDMJ1..AC-EDMJ6 at line 654 from two limits measured after the fix "
    "(a second-table header with a width-mismatched separator and one with no "
    "separator both read +1). DEBT: product-face-R2628 closed (200661B -> "
    "200664B) and reconcile-battery-R2630 opened first=yes at the "
    "pre-registered 644/4840, so the next window owes that battery on this "
    "committed tree before any further product byte. HONEST: two product "
    "points, nothing a CEO could newly open, every P-47 item still waits on "
    "CEO physical pieces.\n"
)

ANCHOR = "- [ ] [carried 2026-11-10 R2615] R2616 first item"


def main():
    raw = open(P, "rb").read()
    text = raw.decode("utf-8")
    if ROW.strip() in text:
        print("REFUSED already landed")
        return 4
    lines = text.split("\n")
    hits = [index for index, line in enumerate(lines) if line.startswith(ANCHOR)]
    if len(hits) != 1:
        print("REFUSED anchor hits=%s" % (hits,))
        return 3
    index = hits[0]
    new_text = "\n".join(lines[:index] + [ROW.rstrip("\n")] + lines[index:])
    with io.open(P, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)
    back = io.open(P, encoding="utf-8").read()
    ok = ROW.strip() in back and back.startswith(ROW.rstrip("\n"))
    print("BACKLOG landed at line %d bytes %d -> %d head_ok=%s"
          % (index + 1, len(raw), len(back.encode("utf-8")), ok))
    return 0 if ok else 5


if __name__ == "__main__":
    raise SystemExit(main())
