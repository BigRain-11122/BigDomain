"""Insert the R2673 carried row at the top of the board.

The battery this window launched is still live at closeout, so the adopt
recipe is written onto the board rather than kept in a window memory. The row
names the evidence path, the pid, the measured target and the R2614 discipline
that governs a verdict reached across commits.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")

ROW = (
    "- [ ] [carried 2026-11-12 R2673] R2675 first item: ADOPT the battery leg "
    "this window launched and CLOSE reconcile-battery-R2671 before any further "
    "product byte (the debt gate own first=yes plus the R2168 mixed-tree rule). "
    "The leg was launched detached at a target re-measured by import at 654 "
    "suites / 4900 criteria / 654 unique names / 654 unique paths, pid 63200 "
    "with its reconcile_all child, stream logs/battery-R2673.stream and "
    "evidence qa/reconcile-all-R2673.log written by the shipped single writer "
    "alone (the one-off launcher was deleted before the commit, so adopt by the "
    "evidence path and not by a launcher). MEASURE rather than quote: (a) "
    "confirm the process chain is gone and the stream carries a closing "
    "'BATTERY rc=' line; (b) re-measure the evidence on bytes - size, utf-8, "
    "bom=False, crlf=0, lone_cr=0, nul=0, PASS/FAIL suite row counts with 654 "
    "unique names, and an INDEPENDENT criteria recount that must sum to 4900; "
    "(c) DISCLOSED GAP TO CLOSE: TWO commits landed UNDER this leg (7c6930d6 "
    "and f57a83bf), so a green verdict is admissible only beside an individual "
    "re-run of the write-sensitive suites on the FINAL committed tree (the "
    "export trio, the ledger round-coverage suite if it has a registry row, "
    "and the readability suites); (d) if the leg went RED, keep the red leg as "
    "evidence and commit a birth-site repair ALONE before any retry, then "
    "relaunch through src/os/battery_stream.py with stream and pid in separate "
    "files; (e) then run the four follow-up sections in the designed order "
    "through src/os/battery_followup.py (its matrix section FAILS first on a "
    "stale doc by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py --stamp-from docs/sandbox-suite-matrix.md "
    "after) and land the verdict. DEBT: close reconcile-battery-R2671 through "
    "the shipped debtor; NO successor battery is owed by THIS window because it "
    "moved no product src byte and the registry is unmoved at 654/4900, but a "
    "verification window that only closes the row still owes the next PRODUCT "
    "face, so open product-face-R2675 naming the queue head "
    "state/queue/tech.md:676 prefix AC-PNAG1, whose criteria were pinned in "
    "that row at R2594 BEFORE any code. ALSO OPEN AND NAMED: the shared writer "
    "constant state_io.ITEM_INDENT is 16 while this file own log items are "
    "indented by 2 - the template defect R2671 repaired by hand and R2673 "
    "repaired again by script, left UNCHANGED on purpose because other shipped "
    "writers read that module and a change there deserves its own six-criteria "
    "suite; src/os/scan_five_still.py still crashes at its final [ORD-TOP] "
    "print on the GBK console, so the scan runs under PYTHONIOENCODING=utf-8, "
    "WORKED AROUND rather than repaired; and BigDomain-OSLoop still reads "
    "InteractiveToken against the 2026-09-29 machine law, carried as the "
    "ceo-pending physical item loop-s4u-reconcile which needs an ELEVATED "
    "shell.\n"
)


def main():
    with io.open(BOARD, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    if "carried 2026-11-12 R2673" in text:
        print("E_BOARD_EXISTS already carried")
        return 2
    updated = ROW + text
    payload = updated.encode("utf-8")
    with io.open(BOARD, "wb") as handle:
        handle.write(payload)
        handle.flush()
    with io.open(BOARD, "rb") as handle:
        if handle.read() != payload:
            print("E_BOARD_READBACK")
            return 3
    print("BOARD inserted bytes=%d -> %d" % (len(raw), len(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
