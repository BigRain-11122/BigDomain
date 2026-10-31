"""R2274 board closeout: prepend the this-window rows to the claim board and
append the heartbeat row, each with a read-back proof.

Two files only, both appends of already-measured text: src/os/backlog.md
(the claim work board) and heartbeat.txt (the scan-readable tick trail).
Nothing here derives a number; every figure was measured in this window.
"""

import io

BACKLOG = "src/os/backlog.md"
HEARTBEAT = "heartbeat.txt"

DONE_ROW = (
    "- [x] [done 2026-10-31 R2274] R2274 first item: PRODUCT FACE ON THE ROW "
    "THE READER NAMED (discharged: src/os/debt_close.py + "
    "src/os/test_debt_close.py with AC-DEBC1..AC-DEBC6 already pinned in the "
    "R2251 seed row at state/queue/tech.md:340; SUITE PASS 6/6 on the first "
    "run, two legs with an identical criterion digest, five adjacent os "
    "suites green, qa/debt-close-R2274.log 1658B written as one utf-8 LF "
    "single writer through the R2261 evidence_capture callable, wired "
    "os-debt-close(6)). The shipped callable then closed product-face-R2274 "
    "in the live register itself (line=41, open 2->1, done 23->24, readback "
    "ok) and debt_append opened reconcile-battery-R2275 first=yes, so the "
    "register reads open=2 done=24. The claim dropped tech claimable to 9, so "
    "one real gap row was seeded from a live finding: the register carries "
    "reconcile-battery-and-matrix on two done rows and duplicate items are "
    "simply unchecked, so debt_item_unique (AC-DIU1..AC-DIU6 pre-registered, "
    "five anchors git grep -F zero-occupancy rc=1) holds the floor, which "
    "closed FLOOR-MET 10/10. Honest notes: the register was measured LF-only "
    "before the write; state.json measured 62334B against the 78500B "
    "waterline so no fold was due.")

CARRIED_ROW = (
    "- [ ] [carried 2026-10-31 R2274] R2275 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule). R2274 changed src/os (debt_close.py, test_debt_close.py, "
    "closeout_R2274.py, export_R2274.py), one runner entry and the "
    "queue/board files, so the next window runs the full reconcile battery on "
    "the committed tree with an empty git status before and after. The "
    "registry read 442 suites / 3628 criteria at R2273 and the pre-registered "
    "expectation is +1 suite / +6 criteria (443 suites / 3634 criteria) from "
    "the os-debt-close suite - measure it, and if a delta does not resolve to "
    "a named suite disclose the prediction error instead of sweeping it. Then "
    "run the four follow-up sections through src/os/battery_followup.py, "
    "whose matrix section will FAIL first on the stale doc and must not "
    "rewrite it: regenerate from the new battery evidence with "
    "src/sandbox/suite_matrix.py and re-run. After that the product face "
    "resumes at the tech head, state/queue/tech.md line 342 (prefix AC-QRX1, "
    "the R2253 queue_row_exempt seed). Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop reads LogonType=InteractiveToken (fortieth "
    "consecutive disclosure; carried as loop-s4u-reconcile in state/debt.md, "
    "now stale at 43 windows).")

TICK_ROW = (
    "tick 2274 2026-10-31 product window: closing a carried-debt register row "
    "is one callable instead of hand surgery (src/os/debt_close.py, "
    "AC-DEBC1..6 SUITE PASS 6/6 first run, two legs identical digest, five "
    "adjacent suites green); the shipped writer closed product-face-R2274 "
    "itself and debt_append opened reconcile-battery-R2275 first=yes "
    "(register open=2 done=24); a live duplicate item "
    "(reconcile-battery-and-matrix on two done rows) seeded the real gap row "
    "debt_item_unique and the tech floor closed FLOOR-MET 10/10; battery "
    "carried to R2275")


def prepend(path, rows):
    with io.open(path, "r", encoding="utf-8") as handle:
        old = handle.read()
    text = "\n".join(rows) + "\n" + old
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != text or not back.endswith(old):
        raise SystemExit("ABORT backlog read-back mismatch")
    return len(text.encode("utf-8"))


def append_line(path, row):
    with io.open(path, "r", encoding="utf-8") as handle:
        old = handle.read()
    sep = "" if old.endswith("\n") else "\n"
    text = old + sep + row + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != text or not back.startswith(old):
        raise SystemExit("ABORT heartbeat read-back mismatch")
    return len(text.encode("utf-8"))


board = prepend(BACKLOG, [DONE_ROW, CARRIED_ROW])
heart = append_line(HEARTBEAT, TICK_ROW)
print("BOARDS backlog=%dB heartbeat=%dB" % (board, heart))