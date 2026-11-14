"""board_backlog_R2742 - close the R2742 line and prepend the R2743 line."""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

HEAD = "- [ ] [R2742] "
DONE = "- [x] [done 2026-11-15 R2742] "

DISCHARGE = (
    " Discharge: shipped src/os/export_parity_difference_order_field.py plus its six-criteria "
    "suite and one evidence driver. The blind spot was re-measured on the shipped law before any "
    "byte and it is real (order-only reads the shape word bytes, a value difference names its own "
    "field); the face asks that law on its module at CALL time, publishes the answer unchanged in "
    "differs, and names the FIRST key that moved in BOTH orders across four shapes, with FORMAT "
    "for a whitespace-only difference and no order claim on a value difference. SUITE PASS 6/6 "
    "twice with the identical digest DC582D20F8A0EA12 "
    "(qa/export-parity-difference-order-field-R2742b.log, 8139B, landed BY the shipped capture "
    "callable) and three adjacent suites green at rc=0; the first leg landed red at "
    "...R2742.log because the verdict expression demanded a SUITE PASS line two adjacent suites "
    "never print, and it is kept as an artifact with the repair disclosed. LIVE on the real "
    "docs/status-export.json: IDENTICAL at 411953B against itself, ORDER-ONLY order_field=export_ts "
    "at 410805B against the same document sorted. Registry 675/5026 -> 676/5032 by import; matrix "
    "restamped stamp-aligned to 71635B with --check rc=0."
)

NEXT = (
    "- [ ] [R2743] next window: THE BATTERY FIRST - debt_gate reads CLAIM-FIRST "
    "reconcile-battery-R2742 first=yes because R2742 moved product src (one face, one suite, one "
    "driver) and one registry row from 675 suites / 5026 criteria to 676 / 5032, so the R2168 "
    "mixed-tree rule forbids any further product byte until it is green. Re-measure the target BY "
    "IMPORT on the committed tree (676 / 5032 / 676 unique names / 676 unique paths) and name any "
    "larger delta rather than sweeping it; run it on a CLEAN committed tree, launch detached "
    "through src/os/battery_stream.py with the stream and the pid in SEPARATE files under logs/ "
    "(never a shell redirection into qa/) after committing the launcher, and adopt it by its "
    "evidence path - NEVER relaunch, and settle a stall by a kernel liveness probe plus a child "
    "pid read rather than an empty WMI CommandLine list. A full leg measures 4000-5900s of suite "
    "time on this host, so the honest plan is launch-and-hand-over, not adopt-in-window. On green: "
    "the four follow-up sections through src/os/battery_followup.py in the designed order "
    "(designed matrix FAIL first with NO byte written, then a stamp-aligned regeneration from THAT "
    "leg - note the matrix currently cites qa/reconcile-all-R2739.log at green=675/676 because no "
    "leg has yet run the new suite - then the verdict append), close reconcile-battery-R2742 "
    "through the shipped debtor, run the R2614 write-sensitive set on the FINAL committed tree, "
    "and THEN the first non-battery product window owes the two carried items: (1) the dead "
    "per-round export hook in src/os/export_R2431.py, now overdue by EIGHT windows - its "
    "documented DO / LATEST / NEXT / OUTS constants are no longer read by main() after the R2616 "
    "derivation redesign and a driver patching them is silently ignored; pre-registered criteria "
    "are a driver patching base.LATEST must land its text in ceo_face.latest_artifact or get a "
    "named refusal, an unpatched driver must keep today derived behaviour byte for byte, and the "
    "R2493-style docstring claim must be true or removed; (2) the measured queue head "
    "state/queue/tech.md:713 prefix AC-LKNF1 ledger_lines with claimable 10 and floor MET - ROW "
    "704 IS NOT CLAIMABLE AS WRITTEN (its criteria live in prose and queue_head.py reads it "
    "NO-CRITERIA), which is why product-face-R2742b carries the correction; re-read the head with "
    "python src/os/queue_head.py --head tech rather than trusting this line.\n"
)


def main():
    text = io.open(PATH, "rb").read().decode("utf-8")
    lines = text.split("\n")
    if not lines[0].startswith(HEAD):
        print("E_BACKLOG top line is not the R2742 line: %r" % lines[0][:60])
        return 2
    lines[0] = DONE + lines[0][len(HEAD):] + DISCHARGE
    lines.insert(0, NEXT.rstrip("\n"))
    out = "\n".join(lines)
    io.open(PATH, "wb").write(out.encode("utf-8"))
    print("lines=%d bytes=%d head=%s"
          % (len(lines), len(out.encode("utf-8")), out.split("\n")[1][:56]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
