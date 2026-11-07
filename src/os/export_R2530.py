"""export_R2530 - refresh docs/status-export.json for the R2530 window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies this
round's result row and its outs row. The three CEO lines are derived at call
time from state, from what actually landed under qa/ for this tick, and from
the open first=yes debt row - never typed as constants that can go stale.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.RESULT = (
    "2026-11-07 R2530 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2529, pre-registered 594 suites / 4540 criteria, "
    "re-measured by import and matched byte for byte). LEG 1 WAS RED AND IS "
    "KEPT (qa/reconcile-all-R2530.log, 922666B): RUNNER FAIL at 593/594 with "
    "reconcile-daily-census 7/8 red on cd7-live-real-tree exit=2 drift, and the "
    "shipped writer census named the cause exactly - flags=2 new-dialect, the "
    "two R2529 evidence logs in UTF-16 (bom16=True, 7456 and 2120 nul bytes) "
    "because that window landed them through a PowerShell redirection instead "
    "of the tee writer. REPAIRED AT THE BIRTH SITE with "
    "src/os/repair_dialect_R2530.py, the explicit rewrite face the census does "
    "not ship: my first pass converted the encoding but left CRLF (crlf=86 and "
    "12, still flagged class pwsh-capture) and a second pass normalised CRLF to "
    "LF, after which both files read bom=False nul=0 crlf=0 at 7370B and 2108B, "
    "the census read flags=0 DRIFT-CLEAN at rc=0 and the red suite alone read "
    "SUITE PASS 8/8; repair plus red leg were committed ALONE as 4ee6f301. The "
    "defect was also pinned in git because core.autocrlf reads true with no "
    ".gitattributes: qa/*.log is now marked -text (11bcf106) so evidence is "
    "stored and checked out byte-exact, and both the census and the follow-up "
    "dry run were re-read clean after that change. LEG 2 GREEN measured not "
    "quoted: qa/reconcile-all-R2530-retry.log 922689B, utf-8 bom=False crlf=0 "
    "lone_cr=0, RUNNER PASS (594/594 suites green, reconcile controls 7/7, "
    "1190.4s), zero FAIL rows, and an independent recount over the 594 PASS "
    "rows sums to EXACTLY 4540. FOUR FOLLOW-UP SECTIONS: matrix FAIL first by "
    "design (57227B vs 57251B, no byte written) then stamp-aligned regeneration "
    "from this round own green leg to 57251B at 594/4540 with green=594/594 "
    "self-describing and --check byte-identical, then all four PASS for VERDICT "
    "R2530 PASS failing=none (APPENDED 1950B). DEBT: reconcile-battery-R2529 "
    "closed at its predicted 160450B -> 160453B (line 258, open 13->12, done "
    "228->229, readback ok); NO successor battery owed because the registry is "
    "unmoved at 594/4540 and the only new src byte is a tool with no suite of "
    "its own; product-face-R2530 appended first=yes at 160453B -> 160679B "
    "naming the next window a PRODUCT face on tech.md:567 prefix AC-PCAF1 "
    "probe_seam_for_container_name, criteria pinned at R2529 BEFORE any code. "
    "HONEST: zero product points and nothing a CEO could open was built; leg 1 "
    "was red and kept; my first repair pass was incomplete and was corrected "
    "against measurement; the rewrite helper carries no suite; the window "
    "overshot its 25-minute budget about twofold; Docker is absent; the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items; "
    "tasks.md was not touched; the state_fold layout defect from R2522 is still "
    "open so the append used a proved load+dump round-trip; five stale "
    "product-face rows still overstate outstanding work and were not "
    "hand-closed.")

base.OUTS = (
    "qa/reconcile-all-R2530.log (red leg, 922666B) + "
    "qa/reconcile-all-R2530-retry.log (green leg, 922689B) + "
    "qa/probe-seam-alias-expression-scope-R2529.log + "
    "qa/probe-seam-alias-expression-scope-live-R2529.log + "
    "src/os/repair_dialect_R2530.py + .gitattributes + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/closeout_R2530.py + "
    "src/os/export_R2530.py + src/os/state.json + docs/status-export.json + "
    "src/os/backlog.md + heartbeat.txt")

if __name__ == "__main__":
    print(base.main())