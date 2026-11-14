"""state_append_R2747b - disclose that two commits landed under the retry leg.

R2614 discipline: the closeout commits and the queue seed land UNDER the
detached battery leg, so a green verdict is admissible only beside an
individual re-run of the write-sensitive set on the FINAL committed tree.
This line exists so the adopting window cannot mistake the leg for a clean
measurement of the tree it will read.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINE = (
    "R2747 R2614 DISCIPLINE IS OWED AND PRE-NAMED on the retry leg this window "
    "launched detached (pid 77080, stream logs/battery-R2747.stream, evidence "
    "qa/reconcile-all-R2747.log): the closeout commit fcb62d58 and the queue-seed "
    "commit 8c1874a3 BOTH land under that leg, and the seed appends a claimable "
    "AC-QREG1..AC-QREG6 row to state/queue/tech.md, so the leg is NOT a clean "
    "measurement of the final tree. The adopting window must confirm the pid chain "
    "is gone by command line AND that the stream carries a closing BATTERY rc= line "
    "before reading any byte, then re-run the write-sensitive set (export trio, "
    "ledger round coverage, the six readability suites, both export health suites) "
    "and the queue-sensitive set (queue head, queue floor, queue row) individually "
    "on the FINAL committed tree rather than adopting the leg green on its own "
    "word. A red row caused by these two commits is evidence about the tree, not a "
    "product defect, and must be attributed before any repair."
)


def main():
    data = state_io.parse(state_io.decode(state_io.read_raw(STATE)))
    log = data["log"]
    if any(l.startswith("R2747 R2614 DISCIPLINE") for l in log):
        sys.stdout.write("NOOP\n")
        return 0
    before = len(log)
    log.append(LINE)
    state_io.write_document(STATE, data)
    after = len(state_io.parse(state_io.decode(state_io.read_raw(STATE)))["log"])
    sys.stdout.write("log %d->%d\n" % (before, after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
