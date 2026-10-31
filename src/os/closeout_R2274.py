"""R2274 closeout: append this round rows to state.json, preserving layout.

Same shape as closeout_R2272.py minus the fold (the file measures 62334B
against the 78500B waterline, so a fold is not due and is not run). It
serialises the mutated payload, hands the text to state_io.canon (which
pins the 16-space log item layout and refuses rather than guesses), writes
atomically with a read-back byte proof, then re-parses to prove the
payload only grew by exactly the rows this window appended.

Usage: python src/os/closeout_R2274.py --plan
       python src/os/closeout_R2274.py --execute
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)

import state_io  # noqa: E402

TICK = 2274

ROWS = [
    "2026-10-31 R2274 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger last "
    "@BigDomain lines are patrol briefings with no numbered handoff among "
    "them, so zero unreplied; the group orders tail is unchanged at the "
    "2026-10-31 14:13 baseline consumed in R2271; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "queue floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, the debt "
    "gate named product-face-R2274 first=yes and queue_head named the same "
    "row (line 340, prefix AC-DEBC1, skipped_before=4, claimable=10), so "
    "this window claimed it. PRODUCT: src/os/debt_close.py plus "
    "src/os/test_debt_close.py - closing a carried-debt row stops being hand "
    "surgery. debt_append gave the register a writer for OPEN rows, but a "
    "close was still an operator flipping the open box to a done box, typing "
    "the closed stamp and remembering to drop first=; a wrong stamp, or a "
    "first flag left on a done row, stayed invisible until debt_register "
    "refused the whole file. render_closed() rewrites only what the done law "
    "requires (box flipped, first= dropped, closed stamp appended, note "
    "untouched), plan() refuses E_DEBC_UNKNOWN / E_DEBC_ALREADY_DONE / "
    "E_DEBC_AMBIGUOUS / E_DEBC_BAD_ROUND before any byte changes and then "
    "re-parses through debt_register requiring the open and done counts to "
    "move by exactly one each way, and the write is one atomic os.replace "
    "re-measured through debt_register.register so a register that cannot "
    "parse after the edit is an error rather than a silent write. Criteria "
    "AC-DEBC1..AC-DEBC6 were already pinned in the R2251 seed row BEFORE the "
    "code. Evidence: SUITE PASS 6/6 on the first run, two legs with an "
    "identical criterion digest and five adjacent os suites green "
    "(debt_register, debt_append, debt_gate, queue_head, seed_anchor), "
    "qa/debt-close-R2274.log 1658B written as one utf-8 LF single writer "
    "through the R2261 evidence_capture callable, wired os-debt-close(6). "
    "LIVE dogfood at the close: the shipped callable closed "
    "product-face-R2274 itself (line=41, open 2->1, done 23->24, readback "
    "ok) and debt_append opened the successor reconcile-battery-R2275 "
    "first=yes, so the register now reads open=2 done=24. The claim dropped "
    "tech claimable to 9, so one real gap row was seeded in the same window: "
    "the live register was found to carry the item "
    "reconcile-battery-and-matrix on TWO done rows - a duplicate "
    "debt_register never checks, which makes this window own ALREADY-DONE "
    "and AMBIGUOUS refusals depend on which duplicate a caller takes - so "
    "debt_item_unique (AC-DIU1..AC-DIU6 pre-registered, five anchors git "
    "grep -F zero-occupancy rc=1) now holds the tech floor, which closed "
    "FLOOR-MET 10/10. Honest notes: (a) the register was measured LF-only "
    "(64 lines, zero CR) before the write so the text round-trip introduces "
    "no EOL drift; (b) state.json measured 62334B against the 78500B "
    "waterline, so no fold was due and none was run.",

    "R2274 tokens: local=~14k api=0 api_reason=product window on the debt "
    "register first item - one new os module with its six pre-registered "
    "criteria and its suite, one dogfooded evidence capture (two legs with "
    "an identical criterion digest, five adjacent suites green) through the "
    "R2261 evidence_capture callable, one live dry run plus two live writes "
    "through the shipped close writer and the existing append writer, one "
    "real gap row seeded from a live duplicate finding, and the "
    "queue/backlog/debt/state/export closeout; zero cloud calls and zero "
    "external API touches; the battery carries to R2275 as the register "
    "successor row",

    "R2274 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (fortieth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
]


def main(argv):
    execute = "--execute" in argv
    raw = io.open(STATE, "rb").read().decode("utf-8")
    before = json.loads(raw)
    after = json.loads(raw)
    after["log"] = list(before["log"]) + ROWS
    after["tick"] = TICK
    text = json.dumps(after, indent=2, ensure_ascii=True)
    canon = state_io.canon(text)
    if json.loads(canon) != after:
        raise SystemExit("ABORT canon moved the payload")
    old_log = list(before["log"])
    if json.loads(canon)["log"][:len(old_log)] != old_log:
        raise SystemExit("ABORT the existing rows moved")
    print("PLAN rows=%d tick=%d before=%dB after=%dB"
          % (len(ROWS), TICK, len(raw.encode("utf-8")),
             len(canon.encode("utf-8"))))
    if not execute:
        return 0
    data = canon.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".closeout_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
    os.replace(temp, STATE)
    back = io.open(STATE, "rb").read()
    if back != data:
        raise SystemExit("ABORT read-back differs from the write")
    measured = state_io.layout(back.decode("utf-8"))
    print("WROTE bytes=%d log_items=%d layout_ok=%s count_ok=%s"
          % (len(back), measured["log_items"], measured["layout_ok"],
             measured["count_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))