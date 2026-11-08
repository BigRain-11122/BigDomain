"""R2567 state append (tick 2567) with a proved round-trip.

The layout defect that made this check necessary (state_fold refusing the real
json layout) was repaired this window; the proof stays anyway, because a writer
that cannot round-trip its own target must never mutate it.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LOG = [
    "2026-11-08 R2567 PRODUCT face: the fold that state_fold.py could only "
    "REPORT is now a face an operator can run - src/os/state_fold_run.py plus "
    "src/os/test_state_fold_run.py, criteria AC-SFOLD1..AC-SFOLD6 pinned at "
    "R2548 in state/queue/tech.md BEFORE any code. The predicate, the "
    "verbatim append and the waterline read are the shipped ones (imported, "
    "never copied); this face adds the refusals and the proofs. AC-SFOLD4 "
    "found the birth site of the layout defect open since R2522 and closed "
    "it there: state_fold.split_layout insisted on a 16-space item indent "
    "while the shipped append path writes 2-space items, so the reader "
    "refused the REAL file with E_SF_BAD_LAYOUT at open this window - the "
    "repair derives the item indent from the file itself, inserts with that "
    "same indent, and refuses items that disagree with each other with the "
    "shipped code instead of reformatting anything. PROOF: SUITE PASS 6/6 "
    "twice with an identical body and five adjacent suites green through the "
    "shipped evidence capture (qa/state-fold-run-R2567.log, 2353B, legs=2 "
    "identical=True adjacent=5 fails=0), and the shipped fold suite re-ran "
    "6/6 after the reader repair. LIVE, measured: the real state.json was "
    "folded through this face - 327622B -> 71125B, gate 78500, margin 7375, "
    "247 -> 56 live log lines, window 1..192 moved into "
    "logs/state-log-archive-2026-11.md as an APPEND-ONLY block of 257082B "
    "with every one of the 192 lines proved byte-equal in the archive and "
    "all 124 tokens preserved in the summary line, field set preserved, "
    "layout AGREE, ledger coverage 1368 -> 1369 rounds (the summary line "
    "itself names R2567, so the count can only hold or grow - nothing was "
    "lost), and state_fold --check now reads FOLD-CLEAR at 71125B against "
    "the 78500B waterline (qa/state-fold-live-R2567.log). The pre-op copy "
    "logs/state-preop-R2567.bak keeps the exact pre-fold bytes. HONEST: this "
    "is the first window in three rounds that displaces the waterline debt "
    "instead of apologising for it; it is a tooling face, not a CEO-facing "
    "product - no user-visible surface was created and none is claimed. The "
    "first=yes row named tech.md:603 AC-PNDCF1 (the probe-seam call-target "
    "face) and this window chose the fold instead, because that row's own "
    "predecessor disclosures name the fold as the OWED obligation gating "
    "every append; the probe-seam row stays open and is named, not dropped. "
    "Registry moved 612 -> 613 suites / 4648 -> 4654 criteria, so the next "
    "window OWES a full battery (R2168 mixed-tree rule). Zero cloud calls, "
    "zero external API touches.",

    "R2567 tokens: local=~12k api=0 api_reason=product window - five-silence "
    "scan at open, one registry anchor check, one shipped-suite double run "
    "with five adjacent suites through the evidence capture, one birth-site "
    "layout repair measured on the REAL state file, one live fold through "
    "the new face with archive verification and gate proof, one ledger "
    "coverage read through the archive, one debt row closed and one opened "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    trial = json.dumps(data, indent=1, ensure_ascii=False)
    if trial != text:
        print("REFUSED E_SA_RT_LAYOUT: load+dump is not byte-identical "
              "(on-disk %dB, round-trip %dB)"
              % (len(raw), len(trial.encode("utf-8"))))
        return 3
    before = len(raw)
    data["tick"] = 2567
    for line in LOG:
        data["log"].append(line)
    data["last_decision_rows"] = 273
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    after = os.path.getsize(STATE)
    ok = (back["tick"] == 2567 and len(back["log"]) == len(data["log"]))
    print("STATE tick=2567 log=%d before=%dB after=%dB wrote=%s"
          % (len(back["log"]), before, after, "yes" if ok else "no"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())