"""R2510 closeout: prepend the two board rows and append the heartbeat row.

Row 1 records what this window actually discharged (the owed battery).
Row 2 carries the product face to R2511, because the R2168 mixed-tree rule
ranked the battery ahead of it and no product byte was shipped here.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
BACKLOG = os.path.join(BASE, "backlog.md")
HEART = os.path.join(REPO, "heartbeat.txt")

DONE = (
    "- [x] [done 2026-11-07 R2510] R2510 VERIFICATION window on the battery the "
    "register owed (reconcile-battery-R2509, opened by the R2509 product window "
    "as first=yes at a pre-registered 584 suites / 4480 criteria). Five-silence "
    "scan clean at HEAD 66b99a20 (git status empty, no index.lock, zero "
    "@BigDomain ledger rows, content-addressed decisions diff new=0 over the "
    "stored 89-token baseline at a measured 190 rows, group orders tail "
    "unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the gate); "
    "debt_gate read CLAIM-FIRST item=reconcile-battery-R2509 opened=R2509 "
    "carried=1 stale=no, so the R2168 mixed-tree rule ranked the battery ahead "
    "of tech line 549 AC-STPT1. TARGET RE-MEASURED BY IMPORT BEFORE THE RUN: "
    "584 suites and 4480 criteria, byte for byte the register number. RESULT: "
    "GREEN ON THE FIRST LEG, measured not quoted - qa/reconcile-all-R2510.log "
    "is 889025B, utf-8 with bom=False, crlf=0 and lone_cr=0, closing with "
    "RUNNER PASS (584/584 suites green, reconcile controls 7/7, 1062.1s), zero "
    "FAIL suite rows, an independent recount over the 584 PASS rows summing to "
    "EXACTLY 4480, tmp reclaim 932/932 at 326.59 MiB, launched detached and "
    "unfiltered through battery_stream.py (pid 67884) so no capture landed in "
    "qa by shell redirection. FOUR FOLLOW-UP SECTIONS in the designed order: "
    "the dry run read matrix FAIL at on-disk 56176B against regenerated 56172B "
    "with no byte written while fingerprint/profile/census read PASS, then "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from THIS round "
    "own green evidence through the evidence flag plus stamp-from at 56172B / "
    "584 / 4480 with green=584/584, the check read byte-identical, and the "
    "re-run read all four sections PASS for VERDICT R2510 PASS failing=none "
    "(APPENDED 1950B eol_ok=True). DEBT: reconcile-battery-R2509 closed at line "
    "230 (open 2->1, done 210->211, 143413B -> 143416B measured exactly, "
    "readback ok) and product-face-R2510 appended first=yes (143416B -> "
    "145469B, readback ok) naming the next window a PRODUCT face on tech head "
    "state/queue/tech.md:549 prefix AC-STPT1 stamp_text_coverage, criteria "
    "pinned there at R2509 BEFORE any code. NO successor battery is registered: "
    "no registry module and no suite moved, so the registry stands unmoved at "
    "584 suites / 4480 criteria. The first append attempt was REFUSED "
    "E_DEBTA_BAD_FIELD because the note carried equals signs and the note was "
    "rewritten without them rather than the field law loosened; the export "
    "driver was probed with an unsupported --help flag and performed its real "
    "refresh (tick 2510, queue=CURRENT, no drift, 225792B), which is the "
    "intended action and is disclosed rather than hidden."
)

CARRIED = (
    "- [ ] [carried 2026-11-07 R2510] R2511 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:549 prefix AC-STPT1 "
    "stamp_text_coverage, criteria AC-STPT1..AC-STPT6 pinned in that row at "
    "R2509 BEFORE any code (render prints the generation stamp and, when one is "
    "given, the --stamp-from provenance source, and NO shipped reading covers "
    "either: composing the real render with a stamp and a stamp_from carrying "
    "U+FFFD printed both codepoints into docs/sandbox-suite-matrix.md while "
    "artifact_disk_text_readability and evidence_name_text_coverage both still "
    "returned publishable=True). Re-read the row with `python src/os/"
    "queue_head.py --head tech` rather than trusting this line, run a fresh "
    "zero-occupancy anchor check at HEAD, ship ONE face with its pre-registered "
    "suite, refill the tech floor if claiming drops claimable below 10, and "
    "remember the measured twice trap: a commit that moves the queue must also "
    "re-derive docs/status-export.json and land the queue block through "
    "queue_export_gate_wire --execute. No battery is owed this window because "
    "R2510 discharged it and nothing moved but qa/, docs/ and state/. Also open "
    "and needing an ELEVATED shell: BigDomain-OSLoop exists but its "
    "Principal.LogonType still reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task (carried as the stale row "
    "loop-s4u-reconcile)."
)

HEART_LINE = "2026-11-07 07:2x R2510 verification window: battery green 584/584 at 4480 criteria\r\n"


def main():
    raw = io.open(BACKLOG, "rb").read()
    text = raw.decode("utf-8")
    if not text.startswith("- [ ] [carried 2026-11-07 R2509]"):
        print("FAIL backlog head %r" % text[:60])
        return 2
    text = DONE + "\n" + CARRIED + "\n" + text
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write(text)

    hb = io.open(HEART, "rb").read()
    htext = hb.decode("utf-8")
    if not htext.endswith("\r\n"):
        print("FAIL heartbeat tail %r" % htext[-20:])
        return 2
    io.open(HEART, "w", encoding="utf-8", newline="").write(htext + HEART_LINE)

    after = io.open(BACKLOG, "rb").read()
    print("backlog bytes=%d crlf=%d lf_only=%d"
          % (len(after), after.count(b"\r\n"),
             after.count(b"\n") - after.count(b"\r\n")))
    print("heartbeat tail=%r" % io.open(HEART, "rb").read()[-90:])
    return 0 if len(after) > len(raw) else 1


if __name__ == "__main__":
    sys.exit(main())