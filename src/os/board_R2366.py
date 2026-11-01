"""board_R2366.py - prepend this round's row to the认领 work board (backlog.md).

One-off for the round: the board is newest-first, so the row is prepended and
read back.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(ROOT, "src", "os", "backlog.md")

ROW = (
    "- [x] [done 2026-11-02 R2366] product-face-R2366: state/queue/tech.md:412 "
    "AC-BFH1 battery_followup_help_wire - the follow-up CLI finally answers the "
    "question an operator asks. The debt gate read CLAIM-FIRST "
    "item=product-face-R2365 and that was FINISHED work (R2365 had shipped it: "
    "module, suite, two evidence logs and the runner wiring all on disk), so "
    "the row was verified by measurement and closed through debt_close (open "
    "3->2, done 95->96, readback ok) instead of being re-run - the "
    "R2345/R2354 shape, named as the round first finding. The claimed row 412 "
    "had AC-BFH1..AC-BFH6 pinned at R2365 BEFORE any code and was re-anchored "
    "at HEAD (E_BFH, os-battery-followup-help-wire and "
    "test_battery_followup_help_wire zero-occupancy; battery_followup_help_"
    "wire and AC-BFH only in prose and state files). SHIPPED "
    "src/os/battery_followup_help_wire.py plus its six-criteria suite, and "
    "battery_followup.py now carries module-level TAKES/FLAGS and raises "
    "HelpAsked on --help, answered at exit 0 through the wire. Both halves of "
    "the usage block are IMPORTED: the house line from reconcile_all."
    "CLI_CONTRACT read through runner_arg_guard.load_contract, the flag lines "
    "from the parser own tables, and the wire validates the three keys it "
    "reads so a short contract refuses E_BFH_NO_CONTRACT rather than raising a "
    "KeyError inside a renderer. SUITE PASS 6/6 twice identical "
    "(qa/battery-followup-help-wire-R2366.log, 1411B, single utf-8 LF writer "
    "through src/os/evidence_R2366.py), os-battery-followup and "
    "os-run-argument-guard still 6/6 unchanged, wired "
    "os-battery-followup-help-wire(6). LIVE: "
    "battery_followup.py --help answers exit 0 with the derived usage and the "
    "house line (qa/battery-followup-help-wire-live-R2366.log, 380B), where "
    "the same call was exit 5 E_BFU_BAD_ARGS before. Row stamped and one REAL "
    "measured gap seeded (contract_usage_renderer, AC-CUR1..6: the guard and "
    "this wire now render two usage blocks for one shape), floor FLOOR-MET "
    "5/5 10/10 10/10. Disclosed and repaired at the birth site: the first "
    "closeout fold chose a tokens LINE as its boundary and archived this round "
    "own narrative; the second chose one inside the R2365 block, so "
    "ledger_lines read rounds_without_ledger=2365 - the archive section was "
    "trimmed, the state restored byte-exact from the fold backup and refolded "
    "at the true boundary (line 69, which is log_len-8), predicted=measured "
    "16702B with 771 tokens covered and ledger CLEAN; the nine fold-created "
    "residue rounds were then spliced in ONE atomic replace through the "
    "shipped reader/shape/composer/judge (213->222 entries, 62765B->65393B "
    "measured, TRIAGED 222/222). Two product points.\n"
)


def main():
    with io.open(PATH, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    if "R2366] product-face-R2366" in text:
        print("REFUSE already present")
        return 2
    body = ROW + text
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(PATH, "r", encoding="utf-8", errors="replace") as handle:
        back = handle.read()
    ok = back.startswith(ROW)
    print("BOARD prepended=%s lines=%d" % (ok, len(back.splitlines())))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())