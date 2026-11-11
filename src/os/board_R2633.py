"""R2633 board writer: close the AC-EDMJ row and seed the successor row the
limits measured this window, through one atomic write with a read-back.
"""

import io

P = "state/queue/tech.md"

DISCHARGED = (
    "   DISCHARGED R2633 (line 654, AC-EDMJ1..AC-EDMJ6 pinned there at R2630"
    " BEFORE any code): the row walk of src/os/suite_matrix_reconcile.py now"
    " REFUSES to absorb a block it cannot classify. A table-shaped run that"
    " opens with a header and carries NO separator of its own width ENDS the"
    " first table and names itself - STRAY-HEADER with BOTH widths when a"
    " separator of another width follows (E_EDMJ_STRAY), HEADER-UNSEPARATED"
    " naming the absent separator when none follows (E_EDMJ_UNSEP) - and the"
    " answer carries the first table own doc_rows instead of an inflated"
    " number. The header is recognised by its CELLS: a matrix data row always"
    " carries a numeric criteria cell and a numeric seconds cell, so a pipe"
    " row whose cells are ALL non-numeric is a header, while AC-EDMI1 own"
    " malformed row (non-numeric FIRST cell, numeric 4th and 6th) is still"
    " ONE non-row and never ends the table. Measured BEFORE any byte with"
    " src/os/limits_matrix_reconcile_row_membership_next_R2630.py on the"
    " current tree: narrow-separator header delta +1, no-separator header"
    " delta +1, two adjacent malformed rows -2, numeric footer 0. Measured"
    " AFTER the change with"
    " src/os/limits_matrix_reconcile_second_table_separator_R2633.py"
    " (qa/limits-matrix-reconcile-second-table-separator-R2633.log): both"
    " header shapes delta 0 with problem=(6, 2) and (6, None), the two"
    " adjacent malformed rows still -2 with no problem, the numeric footer"
    " still 0. Proof: AC-EDMJ1..AC-EDMJ6 SUITE PASS 6/6 TWICE with identical"
    " criterion lines through the shipped capture callable"
    " (qa/suite-matrix-reconcile-second-table-separator-R2633.log, 2597"
    " bytes, legs=2 identical=True adjacent=6 fails=0, digest"
    " FB8528404DDBA127) with six adjacent matrix suites green beside it"
    " (row-membership, row-shape, fence-table, fence-rows, table-shape,"
    " shape, each 6/6 rc=0). ONE own defect was caught and repaired at its"
    " birth site rather than by loosening an assertion: AC-EDMJ4 first handed"
    " the check face a fixture whose ROW COUNT differed, so it read"
    " ROWS-MISMATCH where the criterion needs the content word, and the"
    " fixture was replaced with a count-preserving content difference rather"
    " than the criterion being weakened. REGISTRY 644/4840 -> 645/4846 by"
    " exactly one row, recounted by import, and docs/sandbox-suite-matrix.md"
    " was regenerated from that registry through the shipped write face at"
    " the R2631 green leg to 65960 bytes / 645 rows / 4846 criteria, after"
    " which --check read byte-identical at rc=0 and the live report read"
    " DOC-CURRENT."
)

SEED = (
    "- [ ] P2 tech seed (R2633, from this window own measured limit):"
    " `src/os/suite_matrix_reconcile.py` data-row vs header decision - limits"
    " MEASURED this window with"
    " src/os/limits_matrix_reconcile_second_table_separator_next_R2633.py"
    " against private copies"
    " (qa/limits-matrix-reconcile-second-table-separator-next-R2633.log):"
    " (a) a second-table header whose FIRST CELL is numeric"
    " (`| 1 | Suite | Path | Criteria | State | Secs |`) is counted as a"
    " matrix DATA row before the header law is ever asked, so with its own"
    " narrow separator and one row under it the count rose by +2 (measured"
    " delta +2, problem=None); (b) the same header followed by a separator of"
    " its OWN width also read +2 for the same reason, because ROW_RE is asked"
    " before is_second_table_header; (c) a trailing header whose first cell"
    " is numeric read delta 0 and is named as already quiet rather than"
    " claimed as a gap. Product: ONE reading that decides data-row vs header"
    " by the cells a matrix row must carry (a numeric criteria cell and a"
    " numeric seconds cell) rather than by a digit in the first cell, so a"
    " numbered second-table header ends the first table instead of being"
    " counted as one of its rows, while every AC-EDMJ answer survives."
    " Criteria AC-EDMK1..AC-EDMK6 pinned HERE BEFORE any code: AC-EDMK1 a"
    " second-table header whose first cell is numeric ENDS the first table"
    " and is NOT counted as a data row, and the count stays at the first"
    " table own rows; AC-EDMK2 a numbered header followed by a separator of"
    " its own width still ends the table and is still never counted;"
    " AC-EDMK3 a well-formed data row that happens to carry a numeric first"
    " cell is still counted exactly once (the AC-EDMJ and AC-EDMI answers"
    " survive byte for byte); AC-EDMK4 the shipped check face is still asked"
    " exactly once per reading and a content difference keeps its content"
    " word; AC-EDMK5 every AC-EDMJ answer survives beside the new ones"
    " (narrow-separator header named with both widths, no-separator header"
    " named as unseparated, malformed data row still one non-row, all shape"
    " words, both counts, the named evidence source); AC-EDMK6 pure ASCII,"
    " stdlib only, no clock, zero network, its own reconcile label and its"
    " own suite."
)


def main():
    with io.open(P, encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")
    target = lines[653]
    assert target.startswith("- [ ] P2 tech seed (R2630"), target[:60]
    lines[653] = target.replace("- [ ] P2 tech seed (R2630",
                                "- [x] [done 2026-11-11 R2633] P2 tech seed"
                                " (R2630", 1)
    lines.insert(654, DISCHARGED)
    body = "\n".join(lines).rstrip("\n")
    body = body + "\n" + SEED + "\n"
    with io.open(P, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(P, encoding="utf-8") as handle:
        back = handle.read()
    ok = ("[x] [done 2026-11-11 R2633]" in back
          and "DISCHARGED R2633" in back
          and "AC-EDMK1..AC-EDMK6 pinned HERE BEFORE any code" in back)
    print("BOARD ok=%s bytes=%d->%d" % (ok, len(text.encode("utf-8")),
                                        len(back.encode("utf-8"))))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
