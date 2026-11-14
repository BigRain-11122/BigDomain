"""state_append_R2752 - attribute the red R2747 leg and open the successor.

The R2747 retry leg was settled on measured bytes this window: evidence
qa/reconcile-all-R2747.log, 10472 lines, 676 suites with 672 green, five
failed assertions across four export-facing suites, and a closing
RUNNER FAIL line with no BATTERY rc= row. Nothing is adopted here.

All four red suites were then re-run individually on the committed tree
e1c854de and read green (26 criteria total). The cause is the pre-named
R2614 hazard and it is now MEASURED rather than assumed: rounds R2748 to
R2751 refreshed docs/status-export.json while the detached leg was still
reading it, so suites that compare the live CEO face against itself saw
the bytes move between two reads inside one suite.

R2751 also carried the planning trap that the loop is structurally unable
to avoid the overlap because every round must refresh the export. This
window breaks the trap by ORDER, not by new mechanism: refresh, commit,
then launch, so no export write lands while the successor leg reads.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2752

LINES = [
    (
        "R2752 THE R2747 LEG SETTLED RED ON MEASURED BYTES AND IS NOT ADOPTED: "
        "evidence qa/reconcile-all-R2747.log 10472 lines, 676 suites with 672 "
        "green, five failed assertions over four export-facing suites "
        "(reconcile-daily-census, os-status-export-writer-dialect-wire, "
        "os-queue-floor-export-face, os-export-consistency-queue-face 3/6), and "
        "a closing RUNNER FAIL line with NO BATTERY rc= row. The leg is kept as "
        "evidence and was not relaunched over."
    ),
    (
        "R2752 ROOT CAUSE ATTRIBUTED BY RE-RUN, NOT BY ASSERTION: all four red "
        "suites re-run individually on committed tree e1c854de read green "
        "(15+6+6+8 criteria, zero fail-lines, 18.5s). Evidence "
        "qa/battery-R2747-write-sensitive-rerun.log. Two more export-side gate "
        "suites (queue export gate wire, queue export freshness gate) were run "
        "green in the same pass, six suites total. The cause is therefore the "
        "pre-named R2614 hazard and it is measured: rounds R2748 to R2751 "
        "refreshed docs/status-export.json at 03:2x, 03:4x and 04:26 while the "
        "detached leg was still reading that same file, so a suite comparing the "
        "live CEO face against itself saw the bytes move between two reads."
    ),
    (
        "R2752 THE OVERLAP TRAP IS BROKEN BY ORDER AND THE LIMIT IS DECLARED: "
        "R2751 wrote that every round must refresh the export, so a leg launched "
        "before closeout can never be measured clean. This window instead "
        "refreshes, commits, and only THEN launches the successor leg, so no "
        "export write can land inside its reading window. R2614 IS NOT CLAIMED "
        "CLOSED: this pass covered the four red suites plus both export gate "
        "suites, and the remainder of the pre-named set (ledger round coverage, "
        "the six readability suites, queue head/floor/row) is CARRIED to the "
        "adopting window with its own criteria rather than swept."
    ),
    (
        "R2752 tokens: local=~6k api=0 api_reason=monitored-wait attribution - "
        "one five-silence scan, one token-set diff against the decisions "
        "baseline (zero new tokens, the 157 to 158 line drift is layout not "
        "content), one liveness and evidence read of the red leg, four "
        "single-suite re-runs plus two adjacent export gate suites written as "
        "one evidence file, one state append and one board rewrite; zero cloud "
        "calls and zero external API touches"
    ),
]


def main():
    data = state_io.parse(state_io.decode(state_io.read_raw(STATE)))
    log = data["log"]
    if any(l.startswith("R2752 THE R2747 LEG SETTLED RED") for l in log):
        sys.stdout.write("NOOP\n")
        return 0
    for line in LINES:
        log.append(line)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    sys.stdout.write("APPENDED %d lines tick=%d\n" % (len(LINES), TICK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
