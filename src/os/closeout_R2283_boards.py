"""R2283 board closeout: prepend the this-window rows to the claim board and
append the heartbeat row, each with a read-back proof.

Two files only, both appends of already-measured text: src/os/backlog.md
(the claim work board) and heartbeat.txt (the scan-readable tick trail).
Nothing here derives a number; every figure was measured in this window.
"""

import io

BACKLOG = "src/os/backlog.md"
HEARTBEAT = "heartbeat.txt"

DONE_ROW = (
    "- [x] [done 2026-10-31 R2283] R2283 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule) - discharged on the committed R2282 tree 2332496b with an empty "
    "git status before the run: RUNNER PASS 447/447 suites plus controls 7/7 "
    "in 940.1s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB "
    "busy=0 failed=0 (qa/reconcile-all-R2283.log, 775329B, single writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), "
    "criteria total 3658 - exactly the pre-registered +1 suite / +6 criteria "
    "against R2281 (446/3652) from the R2282 os-evidence-parity suite, so the "
    "prediction matched the measurement with no correction. Four follow-up "
    "sections all PASS through src/os/battery_followup.py: the matrix section "
    "FAILED first on the stale doc (on-disk=43126B regenerated=43205B) and "
    "did NOT rewrite it, which is the designed order; src/sandbox/"
    "suite_matrix.py regenerated docs/sandbox-suite-matrix.md to 447 suites / "
    "3658 criteria (43205B) and the re-run read all four sections PASS "
    "(matrix byte-identical, fingerprint CLEAN 5 domains, profile --daily "
    "--check byte-identical, census DRIFT-CLEAN), closing on VERDICT R2283 "
    "PASS. The register was closed through its own writer (line=55, open 2->1, "
    "done 32->33, readback ok) and product-face-R2284 opened first=yes through "
    "debt_append (before=33390B after=34202B, readback ok). Honest score: a "
    "0-point verification window with no product face; no state fold was due "
    "at 42015B against the 78500B waterline.")

CARRIED_ROW = (
    "- [ ] [carried 2026-10-31 R2283] R2284 first item: BACK TO THE PRODUCT "
    "FACE on the row the reader names. queue_head --head tech reads line 354 "
    "(prefix AC-SLC1, skipped_before=4, claimable=10) - the R2269 "
    "stamp_locator seed, whose AC-SLC1..AC-SLC6 criteria are already pinned "
    "inside that row BEFORE the code. Run a fresh zero-occupancy anchor check "
    "at HEAD (git grep -F, expecting rc 1) before writing anything, ship one "
    "product face with its suite, refill the tech floor with one real gap row "
    "if the claim drops claimable to 9, and commit BEFORE any battery (the "
    "R2168 mixed-tree rule) - the battery is then the successor row. Also "
    "open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (forty-ninth consecutive disclosure; carried "
    "as loop-s4u-reconcile in state/debt.md line 43, still stale).")

TICK_ROW = (
    "tick 2283 2026-10-31 verification window: the full 447-suite reconcile "
    "battery ran on the committed R2282 tree (RUNNER PASS 447/447 plus "
    "controls 7/7 in 940.1s, criteria 3658, exactly the pre-registered "
    "+1 suite/+6 criteria) and the four follow-up sections closed green after "
    "the matrix regeneration to 43205B; register closed and "
    "product-face-R2284 opened first=yes naming the tech head line 354 "
    "(AC-SLC1, stamp_locator); honest 0 product points")


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