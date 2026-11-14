"""state_append_R2744 - append this window's log lines through the canonical writer."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2744

LINES = [
    "2026-11-15 R2744 MONITORED-WAIT window with a SECOND verified debt sweep, ZERO product "
    "bytes by the R2168 mixed-tree rule because reconcile-battery-R2742 is still OPEN and its leg "
    "is still running. Five readings at open: git status EMPTY at HEAD 5e4cbca4 equal to "
    "origin/main with no index.lock; ZERO unreplied @BigDomain rows in the group ledger "
    "(atbd_lines=0 unreplied_groups=0); the content-addressed decisions face read rows=131 "
    "tokens=67 new=0; the group orders tail is the carried 2026-11-14 00:30 main-control row, "
    "older than the carried 01:3x baseline and therefore knowledge-only; benchmarks_refreshed "
    "2026-11-14 inside the seven-day gate. debt_gate read CLAIM-FIRST item="
    "reconcile-battery-R2742 first=1 open=37 and leg_status read LEG-ALIVE-NO-EVIDENCE "
    "pid=64528, so no product src byte, no registry row, no queue row and no matrix stamp moved.",

    "R2744 THE LEG WAS MEASURED RATHER THAN TRUSTED, twice, and it is young: leg_status read 119 "
    "PASS suite rows over 119 unique names with ZERO FAIL at 221714B / 1663 lines at open and 253 "
    "PASS rows with ZERO FAIL at 491925B / 2998 lines at closeout, against the pre-registered 676 "
    "suites / 5032 criteria, so 423 suites are still ahead. No evidence file exists and no closing "
    "BATTERY rc= line exists, so the verdict is not this window's to write and nothing was "
    "relaunched - a killed leg is not a red one and an unfinished leg is not a green one.",

    "R2744 THE CHRONIC GAP WAS SWEPT BY VERIFICATION A SECOND TIME AND 26 ROWS CLOSED: R2732 "
    "closed 17 of 52 open rows by a three-part rule and named the 33 it deliberately did not "
    "touch, and this window re-applied that rule where the QUEUE TEXT HAD MOVED since - rows 702 "
    "and 703 have closed in the meantime, so rows pointing at them could now pass where they "
    "could not at R2732. The rule, applied read-only to all 37 open rows through a probe that "
    "writes nothing (tmp/probe_debt_sweep_R2744.py): the queue path:line the row own note names "
    "must read [x]; that line must carry no superseded and no carried marker; and the PRIMARY "
    "face that line names (its first src/os/<name>.py, else its prefix token) must exist in "
    "src/os WITH its test file. 26 rows passed all three and were closed through the shipped "
    "writer src/os/debt_close.py --item ... --round R2744 --execute, every call returning rc=0 "
    "with zero refusals. Independent readback: rows=427, open 37->11, done 390->416, exactly 26 "
    "rows carry closed=R2744, 240479B.",

    "R2744 THE ELEVEN ROWS THAT STAYED OPEN ARE NAMED RATHER THAN SILENTLY DROPPED, and two of "
    "them are not closetable by any rule: product-face-R2742b points at the queue line still open "
    "(state/queue/tech.md:713 AC-LKNF1, claimable 10, floor MET) because that work is not done; "
    "reconcile-battery-R2742 is the battery this window is waiting on; loop-s4u-reconcile is a CEO "
    "physical item; and eight product-face rows (R2527 R2529 R2535 R2537 R2539 R2559 R2565 R2602) "
    "carry no parseable queue path:line in their own note, so the rule "
    "has nothing to measure against them and guessing would be the blind batch sweep R2732 warned "
    "about. Disclosed the same way R2732 disclosed it: a discharge note records the round, not the "
    "per-row verification, and the method plus the exact item list live in this line.",

    "R2744 honest disclosures: (a) ZERO product points by the Executive Protocol scale - a "
    "verified debt sweep is bookkeeping even when every row is checked by rule, this window "
    "shipped no artifact a CEO can newly open, and every P-47 business face still waits on CEO "
    "physical pieces (merchant id, mini-program appid/secret); (b) this is a monitored wait that "
    "the abolished idle-fast path does NOT excuse, so work was pulled from a named chronic gap "
    "instead of re-scanning the same waiting object, and no claimable product byte was skipped "
    "because product bytes are frozen by the mixed-tree rule until this battery is green; (c) no "
    "proposal was written because docs/proposals.md already carries BD-PROP-009 this week with its "
    "two-week visit on 2026-11-28; (d) the probe lives in tmp/ and is not a registry artifact, so "
    "the registry is unmoved at 676 suites / 5032 criteria and no successor battery is owed on top "
    "of the one already open; (e) tasks.md was not touched, it is the P-47 canonical board; "
    "(f) Docker is absent on this host; (g) BigDomain-OSLoop still reads InteractiveToken and "
    "needs an ELEVATED shell for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",

    "R2744 tokens: local=~9k api=0 api_reason=monitored-wait plus verified sweep - one "
    "five-silence scan on tokens and tails, one debt_gate read, one queue head read, two "
    "leg_status reads with a stream size and row census, one read-only probe calibrated twice "
    "against real rows before it closed anything, one 26-call debtor sweep with zero refusals and "
    "one independent readback, one export driver and one state append through the shipped "
    "writers, and the closeout commit; zero cloud calls and zero external API touches",
]


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    before = len(data["log"])
    data["log"].extend(LINES)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    ok = (back.get("tick") == TICK
          and len(back.get("log") or []) == before + len(LINES)
          and back["log"][-len(LINES):] == LINES)
    sys.stdout.write("APPENDED tick=%s log %d->%d ok=%s\n"
                     % (back.get("tick"), before, len(back.get("log") or []),
                        ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
