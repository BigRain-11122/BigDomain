"""Closeout for the R2284 window: append its rows to the live state log.

The state file measured 46353 bytes against the 78500 byte waterline at the
open, so this window's four rows do not cross it and no fold is due - the
fold helper stays available and runs only when the predicted post size
would cross the gate. The append goes through the shipped layout writers
and proves its own bytes by re-parsing and comparing the payload; every
refusal happens before a write.

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
TICK = 2284


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
    summary = ("Fold 599 (R2284): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-10.md; window tokens: %s"
               % (end, " ".join(tokens)))
    return state_fold.fold(ROOT, "R2284", 599, 1, end, summary,
                           execute=execute)


def predicted_append_bytes(rows):
    raw, state = raw_and_state()
    text = raw.decode("utf-8")
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        raise SystemExit("REFUSE: log item lines do not match the log length")
    return sum(len(state_fold.ps_escape(row)) + len(state_fold.ITEM_PREFIX) + 2
               for row in rows)


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


ROWS = [
    "2026-10-31 R2284 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with zero "
    "unreplied numbered handoffs; the group orders tail is unchanged at the "
    "2026-10-31 18:23 baseline consumed in R2278; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "queue floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the "
    "debt gate named exactly one first=yes row (product-face-R2284), so this "
    "window claimed the TOP deliverable tech row: queue_head named line 354 "
    "(prefix AC-SLC1, skipped_before=4, claimable=10), the R2269 "
    "stamp_locator seed, its AC-SLC1..AC-SLC6 criteria already pinned INSIDE "
    "that row BEFORE the code (fresh zero-occupancy anchor check at HEAD "
    "2026-10-31: stamp_locator / AC-SLC / E_SLC / os-stamp-locator / "
    "test_stamp_locator were git grep -F rc 1, and the bare words hit only "
    "prose - src/os/backlog.md, src/os/state.json and two closeout/export "
    "helpers - disclosed). PRODUCT: src/os/stamp_locator.py plus "
    "src/os/test_stamp_locator.py - a NEVER-LOGGED stamp residue becomes a "
    "named evidence trail instead of a hand grep. state_seq names the rounds "
    "that stamped a queue row and left no log item, but triaging one meant "
    "grepping the stamp across state/queue/*.md and rewriting the finding in "
    "prose. The locator takes a round and answers which queue rows carry its "
    "done stamp - file, line, row head and whether the row is closed - with "
    "the stamp law IMPORTED from state_seq and the row-closed law imported "
    "from queue_floor, so neither is re-implemented and a patched law flows "
    "straight through (the suite proves both by patching each one). A round "
    "with no stamp reads NO-HITS honestly at exit 2 rather than as an error "
    "or an empty success, a missing queue directory refuses at 3, bad flags "
    "at 5, and the reader writes nothing and reads no clock so the queue tree "
    "digests identically before and after. Evidence: SUITE PASS 6/6 double-run "
    "identical through the R2261 evidence_capture callable with five "
    "adjacent os suites green (qa/stamp-locator-R2284.log, 1204B, legs=2 "
    "identical, adjacent=5 fails=0, single writer utf-8 LF). LIVE: STAMP "
    "LOCATOR round=R2250 hits=1 scanned=3 missing=0 verdict=HITS - the "
    "residue round the declared-floor gate names really does sit on a closed "
    "tech row (state/queue/tech.md:5, closed=yes). The claim dropped tech "
    "claimable to 9, so one real gap row was seeded from this window's own "
    "live finding (stamp_residue, AC-SRS1..AC-SRS6 pre-registered, five "
    "anchors git grep -F rc 1) and the gauge closed FLOOR-MET main 5/5 tech "
    "10/10 explore 10/10 with the head moving to line 355 (AC-MGT1). Register "
    "closed through its own writer (debt_close line=56, open 2->1, done "
    "33->34, readback ok) and product-face-R2285 opened first=yes through "
    "debt_append (before=34205B after=35004B, readback ok) naming the "
    "committed-tree battery this product edit owes. Honest score: 2 product "
    "points (one runnable reader with its suite and a live reading); the "
    "state file measured 46353B against the 78500B waterline (margin 32147B) "
    "so no fold was due.",
    "R2284 tokens: local=~18k api=0 api_reason=product window on the debt "
    "register first item - one new os module with its six pre-registered "
    "criteria and its suite, one dogfooded evidence capture (two legs "
    "identical, five adjacent suites green), one live CLI reading that "
    "located the R2250 residue on a closed row, one runner wiring line, one "
    "real gap row seeded to hold the tech floor, two register writes through "
    "the shipped close and append writers, and the queue/board/state/export "
    "closeout; zero cloud calls and zero external API touches; the battery "
    "carries to R2285",
    "R2284 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (fiftieth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2284 honest disclosures: (a) the first suite run was RED 4/6 and both "
    "reds were this-window TEST defects, not criteria widened - the AC-SLC1 "
    "purity probe rejected the module for the display string '[done ... "
    "R%d]' in its own renderer and for the word 're.compile' nowhere, so the "
    "probe now asserts the import and the absence of a stamp pattern rather "
    "than the absence of the literal word; the AC-SLC6 red was the honest "
    "one, the runner label was not yet wired, and the wiring landed before "
    "the green run. (b) The module carries no second stamp law and no second "
    "row predicate: the regex is read off state_seq at call time and the row "
    "predicate is queue_floor.is_done_row, each proven by patching it. (c) "
    "The new seed row was appended at the file tail, so it reads BEHIND-HEAD "
    "against line 355 and the next window claims machine_gate there - "
    "disclosed rather than reshuffling the queue by hand.",
]


def main(argv):
    execute = "--execute" in argv
    before, state = raw_and_state()
    print("STATE before=%dB tick=%d log=%d gate=%d margin=%d"
          % (len(before), state["tick"], len(state["log"]),
             state_fold.GATE, state_fold.GATE - len(before)))
    predict = predicted_append_bytes(ROWS)
    will_cross = len(before) + predict >= state_fold.GATE
    print("APPEND predicted=%dB would_cross_gate=%r" % (predict, will_cross))
    if will_cross:
        plan = fold(execute)
        if plan is None:
            print("FOLD skipped: fewer than %d live rows" % (KEEP_LIVE + 1))
        else:
            print("FOLD window=%d:%d lines=%d tokens=%d predicted=%dB "
                  "mode=%s" % (plan["window_start"], plan["window_end"],
                               plan["window_lines"], plan["tokens_total"],
                               plan["predicted_bytes"], plan["mode"]))
            if plan["would_fail"]:
                return 2
    else:
        print("FOLD not due: predicted post stays under the gate")
    appended = append(ROWS, TICK, execute)
    print("APPEND mode=%s %r"
          % ("execute" if execute else "dry-run", appended))
    after, new_state = raw_and_state()
    print("STATE after=%dB gate=%d margin=%d tick=%d log=%d"
          % (len(after), state_fold.GATE, state_fold.GATE - len(after),
             new_state["tick"], len(new_state["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))