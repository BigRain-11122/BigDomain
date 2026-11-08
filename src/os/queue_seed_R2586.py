"""R2586 board seed: ONE row pinned BEFORE any code.

The R2586 verification window measured a real defect on the committed tree:
`src/os/state_seq.py` decides "stamped but never logged" from the LIVE log
only, so a round whose block was folded into logs/state-log-archive-*.md
reads `queue_only` for ever and `state/residue_triage.json` hands it back as
untriaged residue (R2575 is the live instance, measured through
`residue_triage.py --check --round R2574` as `untriaged=1`).

This writer appends the criteria row only. It refuses when the measured
evidence is absent, so no number is invented.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2586.log")

SEED = (
    "- [ ] P2 tech seed (R2586, from this window own measured battery red): "
    "`src/os/state_seq.py` stamped-but-never-logged reads the LIVE log only - "
    "MEASURED this window through the pre-registered 623-suite battery, whose "
    "ONLY failing suite was os-residue-triage AC-RTR6 at "
    "residue=327 triaged=326 untriaged=1, and "
    "`python src/os/residue_triage.py --check --round R2574` names the one "
    "untriaged round as R2575, whose complete block sits in "
    "logs/state-log-archive-2026-11.md (10 mentions) because the R2585 fold "
    "moved it there. `state_seq.audit` computes queue_only from "
    "`extract_labels(state)` alone, so any folded round whose queue row was "
    "closed becomes permanent false residue. Product: ONE reading that also "
    "counts archived log items when deciding what was logged. Criteria "
    "AC-SEQAF1..AC-SEQAF6 pinned HERE BEFORE any code: AC-SEQAF1 archived "
    "labels are read from logs/state-log-archive-*.md through the SAME "
    "`round_evidence.item_round` reader the live log uses, never a second "
    "parser; AC-SEQAF2 a round whose block was folded into the archive is no "
    "longer queue_only; AC-SEQAF3 a round that stamped a queue row and has NO "
    "log item in the live log OR the archive is still queue_only, so the gap "
    "the face exists for is not widened away; AC-SEQAF4 the sequence checks "
    "(gaps/repeats/backwards) still read the LIVE log only and their answers "
    "on this tree are unchanged; AC-SEQAF5 a missing logs/ directory or no "
    "archive file reads zero archived labels and never raises, while an "
    "unreadable archive file fails closed naming the file; AC-SEQAF6 pure "
    "ASCII, stdlib only, no clock, zero network, its own reconcile label and "
    "its own suite, plus a live reading on this tree whose residue verdict is "
    "measured rather than claimed. Five anchors to re-check zero-occupancy at "
    "HEAD before any code: archived_labels, AC-SEQAF, E_SEQAF, "
    "os-state-seq-archive, test_state_seq_archive."
)


def main():
    if not os.path.isfile(EVIDENCE):
        print("REFUSED E_QSR2586_NO_EVIDENCE: %s is absent" % EVIDENCE)
        return 3
    before = os.path.getsize(EVIDENCE)
    text = io.open(QUEUE, encoding="utf-8").read()
    marker = "AC-SEQAF1..AC-SEQAF6 pinned HERE BEFORE any code"
    if marker in text:
        print("REFUSED E_QSR2586_ALREADY_SEEDED: the row text is on the board")
        return 3
    tail = "" if text.endswith("\n") else "\n"
    payload = text + tail + SEED + "\n"
    predicted = len(payload.encode("utf-8"))
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(QUEUE, encoding="utf-8").read()
    lines = back.split("\n")
    measured = len(back.encode("utf-8"))
    ok = (lines[-2].startswith("- [ ] P2 tech seed (R2586,")
          and "Criteria AC-SEQAF1..AC-SEQAF6 pinned HERE BEFORE any code"
          in lines[-2])
    print("board %s evidence=%dB predicted=%d measured=%d rows=%d"
          % ("OK" if ok else "FAIL", before, predicted, measured, len(lines)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())