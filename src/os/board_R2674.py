"""R2674 board closeout: the carried R2673 item becomes a done row, and the
next window carried row is seeded at the same top line.

Both rows are written in the board own dialect (one bullet per line, ASCII
body, dates in the header) and appended/replaced by exact line index so the
residual carried items are not swept.
"""

import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "backlog.md")

DONE = (
    "- [x] [done 2026-11-12 R2674] R2674 VERIFICATION window ADOPTED the "
    "detached leg R2673 launched and CLOSED reconcile-battery-R2671 GREEN at "
    "the pre-registered 654 suites / 4900 criteria. MEASURED NOT QUOTED: the "
    "pid chain (63200, 38276, 72800) was gone by command line before any byte "
    "was read; the stream closed RUNNER PASS (654/654 suites green, reconcile "
    "controls 7/7, 3238.7s) and BATTERY rc=0 3241.0s after TMP RECLAIM 697/697 "
    "at 241.16 MiB; qa/reconcile-all-R2673.log read 1104914B, utf-8, "
    "bom=False, crlf=0, lone_cr=0, nul=0, 8663 lines, 654 suite rows with 654 "
    "UNIQUE names, 654 PASS and ZERO FAIL rows, ZERO non-zero exits, and an "
    "INDEPENDENT criteria recount of EXACTLY 4900; the registry was re-measured "
    "by import at 654 suites / 654 unique names / 654 unique paths. R2614 "
    "DISCIPLINE HONOURED: because two commits (7c6930d6, 80a0e9d1) landed UNDER "
    "the leg, the export write-sensitive trio was re-run on the FINAL committed "
    "tree and read SUITE PASS 6/6, SUITE PASS 6/6 and SUMMARY pass=15 fail=0 "
    "with ledger_lines --check VERDICT CLEAN. FOLLOW-UP in the designed order: "
    "designed matrix FAIL first (on-disk 67177B vs regenerated 67174B, NO byte "
    "written) with fingerprint CLEAN domains=5, profile byte-identical and "
    "census DRIFT-CLEAN; then a stamp-aligned regeneration from THIS round own "
    "green leg to 67174B at 654 rows through src/os/suite_matrix_reconcile.py "
    "--write (readback DOC-CURRENT, --check rc=0) and four sections PASS for "
    "VERDICT R2673 PASS failing=none (APPENDED 1951B, eol_ok=True). DEBT: "
    "reconcile-battery-R2671 closed 212438B -> 212441B (line 393, open 45->44, "
    "done 330->331, readback ok); product-face-R2674 opened first=yes 212441B "
    "-> 212772B at its predicted and measured size - the carried line asked for "
    "the name R2675 while the register convention names an item after the "
    "window that opens it, so R2674 is the durable name and the next window "
    "claims it; NO successor battery is owed because this window moved no "
    "product src byte and the registry is unmoved at 654/4900. HONEST: zero "
    "product points, nothing a CEO could newly open, every P-47 item still "
    "waits on CEO physical pieces, and this window ran past its budget because "
    "the leg itself measured 3238.7s. STILL CARRIED AND NAMED: state_io."
    "ITEM_INDENT is 16 while this file own log items sit at 2 - this window "
    "hard-coded the two-space indent in its own appender instead of touching "
    "the shared constant, which still deserves its own six-criteria suite; "
    "src/os/scan_five_still.py still crashes at its final [ORD-TOP] print on "
    "the GBK console and was WORKED AROUND under PYTHONIOENCODING=utf-8; and "
    "BigDomain-OSLoop still reads InteractiveToken against the 2026-09-29 "
    "machine law, carried as the ceo-pending physical item loop-s4u-reconcile "
    "which needs an ELEVATED shell."
)

CARRIED = (
    "- [ ] [carried 2026-11-12 R2674] R2675 first item: a PRODUCT face on the "
    "queue head the debt register now names - product-face-R2674 first=yes, "
    "state/queue/tech.md:676 prefix AC-PNAG1, criteria AC-PNAG1..AC-PNAG6 "
    "pinned in that row at R2594 BEFORE any code. Re-read the row with python "
    "src/os/queue_head.py --head tech rather than trusting this line "
    "(claimable=14), run a fresh zero-occupancy anchor check at HEAD before any "
    "code, measure the row own limits on private worlds BEFORE writing the "
    "face, ship ONE face with its pre-registered suite, prove it twice through "
    "the shipped capture callable with an identical digest, run the adjacent "
    "suites, and add a bounded live leg that measures the SAME fixture on BOTH "
    "readers. This product window WILL move the registry by one row, so a full "
    "battery becomes owed on the committed tree BEFORE the next product byte "
    "(the R2168 mixed-tree rule). ALSO: a commit that moves the queue must "
    "re-derive docs/status-export.json through the shipped driver, and a "
    "per-round appender must NEVER be probed with --help (R2615 duplicated a "
    "block that way). Still carried from R2673: state_io.ITEM_INDENT 16 vs the "
    "file own 2; src/os/scan_five_still.py GBK crash at [ORD-TOP]; and "
    "BigDomain-OSLoop InteractiveToken needing an ELEVATED shell "
    "(loop-s4u-reconcile)."
)


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    if not lines[0].startswith("- [ ] [carried 2026-11-12 R2673]"):
        print("REFUSED top line is not the R2673 carried item")
        return 3
    if "|" in DONE or "|" in CARRIED:
        print("REFUSED a pipe reached the board row")
        return 3
    lines[0:1] = [CARRIED, DONE]
    out = eol.join(lines).encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2674_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(out)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    readback = io.open(PATH, "rb").read()
    if readback != out:
        print("REFUSED read-back mismatch")
        return 4
    print("BOARD ok lines=%d bytes=%d eol=%s" %
          (len(lines), len(out), "crlf" if eol == "\r\n" else "lf"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
