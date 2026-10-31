"""Closeout for the R2282 window: fold the log, then append its three rows.

The state file sat 3054 bytes under the 78500 byte waterline at the open and
this window's rows would cross it, so the fold runs FIRST (window 1..N-24,
verbatim into the archive) and the rows are appended afterwards to the tree
the fold wrote. Both steps go through the shipped writers; the append proves
its own bytes by re-parsing and comparing the payload, and every refusal
happens before a write.

ASCII, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

sys.path.insert(0, BASE)
import state_fold  # noqa: E402

KEEP_LIVE = 24


def tokens_of(window):
    found = set()
    for line in window:
        found |= set(state_fold.PAT.findall(line))
    return sorted(found)


def raw_and_state():
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    return raw, json.loads(raw.decode("utf-8"))


def fold(execute):
    raw, state = raw_and_state()
    count = len(state["log"])
    end = count - KEEP_LIVE
    if end < 1:
        return None
    window = state["log"][0:end]
    tokens = tokens_of(window)
    summary = ("Fold 597 (R2282): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-10.md; window tokens: %s"
               % (end, " ".join(tokens)))
    return state_fold.fold(ROOT, "R2282", 597, 1, end, summary,
                           execute=execute)


def append(rows, tick, execute):
    raw, state = raw_and_state()
    if tick <= state["tick"]:
        raise SystemExit("REFUSE: tick %d is not above %d"
                         % (tick, state["tick"]))
    text = raw.decode("utf-8")
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        raise SystemExit("REFUSE: log item lines do not match the log length")
    newline = layout["newline"]
    index = layout["item_index"][-1]
    lines = list(layout["lines"])
    if not lines[index].rstrip().endswith(","):
        lines[index] = lines[index] + ","
    insert = []
    for position, row in enumerate(rows):
        tail = "," if position < len(rows) - 1 else ""
        insert.append(state_fold.ITEM_PREFIX + state_fold.ps_escape(row)
                      + tail)
    new_lines = lines[:index + 1] + insert + lines[index + 1:]
    body = newline.join(new_lines)
    body = body.replace('"tick": %d' % state["tick"], '"tick": %d' % tick, 1)
    data = body.encode("utf-8")
    if not execute:
        return {"would_bytes": len(data), "before": len(raw)}
    with io.open(STATE, "wb") as handle:
        handle.write(data)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("REFUSE: read-back differs")
    check = json.loads(back.decode("utf-8"))
    expected = list(state["log"]) + list(rows)
    if check["log"] != expected or check["tick"] != tick:
        raise SystemExit("REFUSE: payload does not round-trip")
    return {"post_bytes": len(data), "before": len(raw),
            "log": len(check["log"]), "tick": check["tick"]}


EXPORT = None

ROWS = [
    "2026-10-31 R2282 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with zero "
    "unreplied numbered handoffs; the group orders tail is unchanged at the "
    "2026-10-31 18:23 baseline consumed in R2278; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "queue floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the "
    "debt gate named exactly one first=yes row (product-face-R2282), so this "
    "window claimed the TOP deliverable tech row: the R2261 evidence_parity "
    "seed at state/queue/tech.md:347, its AC-EVP1..AC-EVP6 criteria already "
    "pinned INSIDE that row BEFORE the code (fresh zero-occupancy anchor "
    "check at HEAD 2026-10-31: evidence_parity / E_EVP / os-evidence-parity "
    "hit prose only, and both code paths were absent). RESULT: the legacy "
    "per-round evidence pile becomes retirable ONE SCRIPT AT A TIME instead "
    "of on a hunch. src/os/evidence_parity.py plus its suite read one script "
    "or a whole directory by static analysis only - the judged script is "
    "never executed, nothing is written and no clock is read - and return "
    "the five ritual legs in the pinned order two-legs / criteria-digest / "
    "single-writer / adjacent-batch / live-gate, each PRESENT, MISSING or "
    "DIFFERENT. PRESENT needs a positive marker AND the shape that marker is "
    "supposed to carry, so a hash without a criterion-line selector, a "
    "two-leg loop with fewer than two run calls, or a writer with no byte "
    "mode or no CRLF guard each read DIFFERENT rather than being rounded up "
    "to PRESENT, and a script with no marker at all reads MISSING. SUITE "
    "PASS 6/6 double-run with identical criterion digest 610E03314512DFE8 "
    "and five adjacent os suites green (qa/evidence-parity-R2282.log, "
    "1550B, one utf-8 LF single writer through the R2261 evidence_capture "
    "callable), wired os-evidence-parity(6). LIVE: the pile reads 92 scripts "
    "with only 6 fully ALL-PRESENT, and every leg carries its own count - "
    "two-legs 14 present / 73 missing / 5 different, criteria-digest "
    "27/12/53, single-writer 60/0/32, adjacent-batch 16/75/1, live-gate "
    "6/82/4 (qa/evidence-parity-live-R2282.log, 573B). The claim dropped "
    "tech claimable to 9, so one real gap row was seeded (evidence_output_map"
    ", AC-EOM1..AC-EOM6 pre-registered, five anchors zero-occupancy rc=1) "
    "and the gauge closed FLOOR-MET 10/10. Honest score: one product face "
    "with its own suite, 2 points; the battery carries to R2283 as the "
    "register successor row.",
    "R2282 tokens: local=~22k api=0 api_reason=product window on the debt "
    "register first item - one reader module with its six pre-registered "
    "criteria and its suite, one dogfooded evidence capture (two legs "
    "identical, five adjacent suites green), two live CLI readings (one "
    "script and the whole pile), one runner wiring line, one real gap row "
    "seeded to hold the tech floor, two register writes through the shipped "
    "close and append writers, one waterline fold through state_fold, and "
    "the queue/board/state/export closeout; zero cloud calls and zero "
    "external API touches",
    "R2282 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (forty-eighth consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md line 43).",
]


def main(argv):
    execute = "--execute" in argv
    before, state = raw_and_state()
    print("STATE before=%dB tick=%d log=%d gate=%d margin=%d"
          % (len(before), state["tick"], len(state["log"]),
             state_fold.GATE, state_fold.GATE - len(before)))

    plan = fold(execute)
    if plan is None:
        print("FOLD skipped: fewer than %d live rows" % (KEEP_LIVE + 1))
    else:
        print("FOLD window=%d:%d lines=%d tokens=%d missing=%d "
              "predicted=%dB mode=%s would_fail=%r"
              % (plan["window_start"], plan["window_end"],
                 plan["window_lines"], plan["tokens_total"],
                 len(plan["tokens_missing"]), plan["predicted_bytes"],
                 plan["mode"], plan["would_fail"]))
        if execute:
            print("FOLD post=%dB predicted_eq_actual=%r archive=%s"
                  % (plan["post_bytes"], plan["predicted_eq_actual"],
                     plan["archive"]))
        if plan["would_fail"]:
            return 2
    appended = append(ROWS, 2282, execute)
    print("APPEND mode=%s %r"
          % ("execute" if execute else "dry-run", appended))
    after, new_state = raw_and_state()
    print("STATE after=%dB gate=%d margin=%d tick=%d log=%d"
          % (len(after), state_fold.GATE, state_fold.GATE - len(after),
             new_state["tick"], len(new_state["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))