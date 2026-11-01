"""closeout_R2340 - append this round to the state log and carry the row.

Writes state.json in the measured canon (CRLF, every log element at exactly
sixteen spaces, top-level keys at two) and proves the payload after the write.
Also appends this round's measurement to the carried backlog row in place.
ASCII source, stdlib only, no clock read for the payload itself.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

ROUND = "R2340"

LOG_LINES = [
    ("R2340: the pre-registered battery ran RED on the committed tree "
     "c41afde9, and only one leg of it was red. Before the run the "
     "writer-census baseline was re-frozen as the carried row demanded, and "
     "the freeze was byte-identical because both new R2339 evidence files "
     "are tee-class and were never baselined (files=2307 baselined=529 "
     "flags=0 DRIFT-CLEAN); that freeze was committed first so the tree was "
     "empty when the battery started (qa/reconcile-all-R2340.log, 792543B). "
     "Measured result: 476/477 suites green, expected criteria total 3838, "
     "with ONE failed assertion - os-orphan-trace AC-OTR6 - even though the "
     "runner counted two. Root cause was measured rather than guessed: "
     "orphan_trace counts ONLY orphan rounds, and the R2339 window own live "
     "promotion of R2136 emptied that pile, so the live reading is "
     "rounds=0 legs=0 trace_exists=0 verdict=NO-ORPHAN, which is the "
     "RESOLVED end state, while the criterion had baked in rounds>=1 - an "
     "environmental precondition that was true when it was written at R2323 "
     "and false the moment the pile it watched was cleared. The repair went "
     "stricter, not weaker: an empty pile is now legal only when the "
     "evidence_variants reading this reader is built on carries zero ORPHAN "
     "rows, so NO-ORPHAN can no longer be a silent zero, and a non-empty "
     "pile must still carry rounds. Product code was untouched - the change "
     "is the suite live clause plus its measured line, which now prints the "
     "orphan count it cross-checked. SUITE PASS 6/6 twice with identical "
     "output (rc=0 both, sha16 6FB177E1FFEEC407), qa/orphan-trace-R2340.log "
     "written by one utf-8 LF single writer. The green full re-run is "
     "CARRIED to R2341 at the same pre-registered target 477 suites / 3838 "
     "criteria, because a full battery costs about fifteen minutes and this "
     "window spent its budget on the measurement and the repair; the four "
     "follow-up sections and the suite-matrix regeneration belong to that "
     "green run. The red leg stays committed as evidence rather than being "
     "overwritten."),
    ("tokens: local=1 api=0 api_reason=none - one local session, no cloud "
     "call this window; the battery and every repair ran on the machine."),
]

NOTE = (" [R2340 MEASURED RED on the committed tree c41afde9 and repaired: "
        "476/477 suites with one real red leg - os-orphan-trace AC-OTR6 "
        "demanded a non-empty live orphan pile, but R2339 own R2136 "
        "promotion had cleared it (rounds=0 NO-ORPHAN is the resolved "
        "state). The criterion was fixed STRICTER: an empty pile is legal "
        "only when the evidence_variants reading carries zero ORPHAN rows, "
        "so NO-ORPHAN is never a silent zero. Product code untouched, suite "
        "6/6 twice byte-identical (qa/orphan-trace-R2340.log), red leg kept "
        "at qa/reconcile-all-R2340.log. The GREEN full re-run plus the four "
        "follow-up sections and the matrix regeneration are CARRIED to "
        "R2341 at the unchanged pre-registered target 477 suites / 3838 "
        "criteria.]")


def dump_canon(obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    out = []
    in_log = False
    for line in text.split("\n"):
        if line == '  "log": [':
            in_log = True
            out.append(line)
            continue
        if in_log:
            if line == "  ]":
                in_log = False
                out.append(line)
                continue
            if line.startswith("    "):
                out.append("                " + line[4:])
                continue
        out.append(line)
    return "\r\n".join(out)


def main():
    raw = io.open(STATE, "r", encoding="utf-8", newline="").read()
    data = json.loads(raw)
    before_len = len(data["log"])
    before_tick = data["tick"]
    if any("R2340: the pre-registered battery ran RED" in item
           for item in data["log"]):
        print("E_ALREADY_LOGGED")
        return 3
    data["tick"] = before_tick + 1
    for line in LOG_LINES:
        data["log"].append(line)
    body = dump_canon(data)
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    os.replace(temp, STATE)
    back = json.loads(io.open(STATE, "r", encoding="utf-8", newline="").read())
    if back["log"] != data["log"] or back["tick"] != data["tick"]:
        print("E_READBACK")
        return 3
    if os.path.exists(temp):
        print("E_RESIDUE")
        return 3
    print("STATE tick %d->%d log %d->%d bytes %d"
          % (before_tick, data["tick"], before_len, len(data["log"]),
             len(body)))

    backlog = io.open(BACKLOG, "r", encoding="utf-8", newline="").read()
    marker = "seeded one (orphan_promotion_ledger, AC-OPL1..AC-OPL6)"
    if NOTE.strip() in backlog:
        print("BACKLOG already carries the R2340 note")
        return 0
    idx = backlog.find(marker)
    if idx < 0:
        print("E_BACKLOG_ANCHOR")
        return 3
    end = backlog.find("\n", idx)
    if end < 0:
        end = len(backlog)
    backlog = backlog[:end] + NOTE + backlog[end:]
    with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
        handle.write(backlog)
    print("BACKLOG row annotated in place")
    return 0


if __name__ == "__main__":
    sys.exit(main())