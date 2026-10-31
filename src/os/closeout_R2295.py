"""closeout_R2295.py - the R2295 board and state edits, in one callable.

One-off per-round helper (the house pattern since R2252). This window was a
verification window: it claimed no queue row and seeded no gap row (tech
claimable stayed 10), so only the board and the state log are written. Every
byte it claims to have measured was measured by the shipped tools before this
helper ran. It writes only the two files it names, in their own measured layout
(the board is LF, state.json is normalised through state_io.canon), and prints
the byte counts it produced.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import state_io  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

BOARD = os.path.join(REPO, "src", "os", "backlog.md")
STATE = os.path.join(REPO, "src", "os", "state.json")

BOARD_DONE = (
    " [done 2026-11-01 R2295] Discharged as a verification window with zero "
    "product edits until green (the R2168 mixed-tree rule), on the committed "
    "R2294 tree 46fddee2 with an empty git status before the run: RUNNER PASS "
    "453/453 suites green plus controls 7/7 in 809.2s with birth-site TMP "
    "RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2295.log, 782769B final, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3694 - "
    "exactly the pre-registered +1 suite / +6 criteria against R2293 (452/3688) "
    "from the R2294 os-stamp-exempt-review suite, so the prediction matched the "
    "measurement with no correction. Four follow-up sections ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=43590B regenerated=43675B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 453 suites / 3694 criteria (43675B) and "
    "the re-run read all four sections PASS (matrix byte-identical, fingerprint "
    "CLEAN 5 domains, profile --daily --check byte-identical, census "
    "DRIFT-CLEAN), closing on VERDICT R2295 PASS. Honest score: a 0-point "
    "verification window with no product face.")

SUCCESSOR = (
    "- [ ] [carried 2026-11-01 R2295] R2296 first item: BACK TO THE PRODUCT "
    "FACE on the row the reader names. queue_head --head tech reads line 362 "
    "(prefix AC-EOM1, skipped_before=4, claimable=10) - the R2282 "
    "evidence_output_map seed, whose AC-EOM1..AC-EOM6 criteria are already "
    "pinned inside that row BEFORE the code. Run a fresh zero-occupancy anchor "
    "check at HEAD (git grep -F rc=1) before writing anything, ship one product "
    "face with its suite (per script the declared qa output paths, every "
    "collision naming both scripts and its line, and the declared-but-absent "
    "set, read-only and refusing rather than guessing), refill the tech floor "
    "with one real gap row if the claim drops claimable to 9, and commit BEFORE "
    "any battery (the R2168 mixed-tree rule) - the battery is then the successor "
    "row. Also open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (sixtieth consecutive disclosure; carried as "
    "loop-s4u-reconcile in state/debt.md).")

NARRATIVE = (
    "2026-11-01 R2295 (five-silence scan clean at open: tree clean with an empty "
    "git status --short and no index.lock; decisions.md carries 289 non-empty "
    "rows EQUAL to the stored 289-row baseline, so no new decision row is "
    "presented and zero domain action is owed; the group ledger carries the same "
    "@BigDomain patrol rows already paid off with zero unreplied numbered "
    "handoffs; the group orders tail is unchanged at the 2026-10-31 18:23 "
    "baseline consumed in R2278; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, the queue floors read FLOOR-MET main "
    "5/5 tech 10/10 explore 10/10 with queue_head naming line 362 (prefix "
    "AC-EOM1, skipped_before=4, claimable=10), and the debt gate named exactly "
    "one first=yes row (product-face-R2295), so this window ran the VERIFICATION "
    "that row demanded with ZERO product edits until green (the R2168 mixed-tree "
    "rule). RESULT: full reconcile battery on the committed R2294 tree 46fddee2 "
    "= RUNNER PASS 453/453 suites green plus controls 7/7 in 809.2s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy zero failed zero "
    "(qa/reconcile-all-R2295.log, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3694 - "
    "exactly the pre-registered +1 suite / +6 criteria against R2293 (452/3688) "
    "from the R2294 os-stamp-exempt-review suite, so the prediction matched the "
    "measurement with no correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=43590B regenerated=43675B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 453 suites / 3694 criteria (43675B) and the "
    "re-run read all four sections PASS (matrix byte-identical, fingerprint "
    "CLEAN 5 domains, profile --daily --check byte-identical, census "
    "DRIFT-CLEAN), closing on VERDICT R2295 PASS at eol crlf=0 bare_cr=0 "
    "bom=False. Register closed through its own writer and product-face-R2296 "
    "opened first=yes naming the tech head at state/queue/tech.md:362 prefix "
    "AC-EOM1. Honest score: a 0-point verification window with no product face.")

LEDGER = (
    "R2295 tokens: local=~14k api=0 api_reason=verification-only window - one "
    "full reconcile battery with its streamed evidence file, one four-section "
    "follow-up through the shipped callable plus one matrix regeneration from "
    "that evidence, one failed launch naming a wrong runner path (deleted before "
    "the sanctioned run), two register writes through the shipped close and "
    "append writers, and the queue/board/state/export closeout; zero cloud calls "
    "and zero external API touches")

SELF_HEAL = (
    "R2295 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes an "
    "explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window (sixtieth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).")

DISCLOSURES = (
    "R2295 honest disclosures: (a) the first launch passed --runner "
    "src/sandbox/reconcile_all.py, but battery_stream resolves runners relative "
    "to src/, so it tried src/src/sandbox/reconcile_all.py and exited before any "
    "suite ran, leaving a 215B evidence file that named the missing path; the "
    "artefact was deleted and the sanctioned run used the DEFAULT runner path "
    "with no --runner flag. (b) The battery runs as a detached hidden process "
    "because battery_stream buffers its evidence in memory and writes once at "
    "completion, so every probe before the end legitimately found no file - that "
    "was buffering and not a dead runner, confirmed by the live child process and "
    "then by the 782769B file. (c) Both follow-up legs are retained in the "
    "evidence file (1889B FAIL then 1950B PASS); the FAIL leg is the designed "
    "first use of the matrix section, which refuses to rewrite the stale doc. (d) "
    "The tech queue was not touched: claimable stayed 10 against its floor, so no "
    "gap row was due, and the board is the only queue-family file this window "
    "edited. (e) The state file measured 72147B before this append against the "
    "78500B gate (margin 6353B), so no fold was due and none was run.")


def edit_board():
    raw = open(BOARD, "rb").read().decode("utf-8")
    items = raw.split("\n")
    head = items[0]
    if not head.startswith("- [ ] [carried 2026-10-31 R2294] R2295"):
        raise SystemExit("E_CLOSE_NO_ROW: the board head is not the R2295 row")
    rest = head.split("]", 1)[1]
    items[0] = "- [x] [carried 2026-10-31 R2294]" + rest + BOARD_DONE
    out = SUCCESSOR + "\n" + "\n".join(items)
    body = out.encode("utf-8")
    open(BOARD, "wb").write(body)
    return len(body)


def build_state():
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    before_items = len(state["log"])
    state["tick"] = 2295
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES])
    ensure_ascii = all(b < 0x80 for b in raw)
    text = json.dumps(state, ensure_ascii=ensure_ascii, indent=2)
    text = state_io.canon(text)
    return raw, state, before_items, text.encode("utf-8")


def main(argv):
    execute = "--execute" in argv
    board_bytes = edit_board() if execute else 0
    raw, state, before_items, new = build_state()
    print("LOG_ITEMS %d -> %d" % (before_items, len(state["log"])))
    print("TICK %s" % state["tick"])
    print("STATE %dB -> %dB DELTA %+d" % (len(raw), len(new), len(new) - len(raw)))
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    folder = os.path.dirname(STATE)
    temp = os.path.join(folder, ".closeout_R2295.tmp")
    with open(temp, "wb") as sink:
        sink.write(new)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    if back != new:
        print("E_BACK read-back does not match")
        return 3
    if os.path.exists(temp):
        print("E_TEMP residue left")
        return 3
    print("WROTE state %dB readback ok temp clean; board %dB"
          % (len(back), board_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))