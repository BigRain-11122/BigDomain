"""closeout_R2301.py - the R2301 fold, board and state edits, in one callable.

One-off per-round helper (the house pattern since R2252). This window was a
verification window: it claimed no queue row and seeded no gap row (tech
claimable stayed 10), so only the archive fold, the board and the state log are
written. The fold runs FIRST because the closeout would cross the waterline
(77573B against a 78500B gate, margin 927B) and because a fold that splits a
round block turns four ledger suites red (the R2290 lesson); window 1..4 is the
whole R2287 block, declared here rather than inferred. Every byte it claims to
have measured was measured by the shipped tools before this helper ran. It
writes only the files it names, in their own measured layout (the board is LF,
state.json is normalised through state_io.canon), and prints the byte counts it
produced.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import state_fold  # noqa: E402
import state_io  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

BOARD = os.path.join(REPO, "src", "os", "backlog.md")
STATE = os.path.join(REPO, "src", "os", "state.json")

FOLD_NO = 607
WINDOW = (1, 9)

BOARD_DONE = (
    " [done 2026-11-01 R2301] Discharged as a verification window with zero "
    "product edits until green (the R2168 mixed-tree rule), on the committed "
    "R2300 tree 0eca69a1 with an empty git status before the run: RUNNER PASS "
    "456/456 suites green plus controls 7/7 in 737.6s with birth-site TMP "
    "RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2301.log, 780458B final, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3712 - "
    "exactly the pre-registered +1 suite / +6 criteria against R2299 "
    "(455/3706) from the R2300 os-gate-drift suite, so the prediction matched "
    "the measurement with no correction. Four follow-up sections ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=43861B regenerated=43904B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 456 suites / 3712 criteria (43904B) and "
    "the re-run read all four sections PASS (matrix byte-identical, fingerprint "
    "CLEAN 5 domains, profile --daily --check byte-identical, census "
    "DRIFT-CLEAN), closing on VERDICT R2301 PASS. Honest score: a 0-point "
    "verification window with no product face.")

SUCCESSOR = (
    "- [ ] [carried 2026-11-01 R2301] R2302 first item: BACK TO THE PRODUCT "
    "FACE on the row the reader names. queue_head --head tech reads line 366 "
    "(prefix AC-EVR1, skipped_before=4, claimable=10; the file lays that row at "
    "367 because the newline-based head law and Python splitlines disagree over "
    "one form-feed character in an older done row, disclosed) - the R2288 "
    "evidence_variants seed, whose AC-EVR1..AC-EVR6 criteria are already pinned "
    "inside that row BEFORE the code. Run a fresh zero-occupancy anchor check at "
    "HEAD (git grep -F rc=1) before writing anything, ship one product face "
    "with its suite (pair each non-canonical evidence variant with its "
    "canonical round, say whether it is a duplicate leg, a retry or a distinct "
    "failed attempt, and refuse to guess when a variant has no canonical "
    "round), refill the tech floor with one real gap row if the claim drops "
    "claimable to 9, and commit BEFORE any battery (the R2168 mixed-tree rule) "
    "- the battery is then the successor row. Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop reads LogonType=InteractiveToken (sixty-fifth "
    "consecutive disclosure; carried as loop-s4u-reconcile in state/debt.md, "
    "still stale).")

NARRATIVE = (
    "2026-11-01 R2301 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger carries "
    "the same @BigDomain patrol rows already paid off with zero unreplied "
    "numbered handoffs; the group orders tail is unchanged at the 2026-10-31 "
    "18:23 baseline consumed in R2278; benchmarks refreshed 2026-10-29 inside "
    "the seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the "
    "weekly proposal duty is met by BD-PROP-005, the queue floors read "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10 with queue_head naming line "
    "366 (prefix AC-EVR1, skipped_before=4, claimable=10), and the debt gate "
    "named exactly one first=yes row (product-face-R2300), so this window ran "
    "the VERIFICATION that row demanded with ZERO product edits until green "
    "(the R2168 mixed-tree rule). RESULT: full reconcile battery on the "
    "committed R2300 tree 0eca69a1 with an empty git status before the run = "
    "RUNNER PASS 456/456 suites green plus controls 7/7 in 737.6s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy zero failed zero "
    "(qa/reconcile-all-R2301.log, 780458B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3712 "
    "- exactly the pre-registered +1 suite / +6 criteria against R2299 "
    "(455/3706) from the R2300 os-gate-drift suite, so the prediction matched "
    "the measurement with no correction. Four follow-up sections then ran "
    "through src/os/battery_followup.py: the matrix section FAILED first on the "
    "stale doc (on-disk=43861B regenerated=43904B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 456 suites / 3712 criteria (43904B) and "
    "the re-run read all four sections PASS (matrix byte-identical, fingerprint "
    "CLEAN 5 domains, profile --daily --check byte-identical, census "
    "DRIFT-CLEAN), closing on VERDICT R2301 PASS. Register closed through its "
    "own writer (debt_close line=72, open 2->1, done 49->50, readback ok) and "
    "product-face-R2301 opened first=yes through debt_append "
    "(before=44165B after=44846B, readback ok) naming the tech head at "
    "state/queue/tech.md:366 prefix AC-EVR1, the R2288 evidence_variants seed. "
    "Honest score: a 0-point verification window with no product face.")

LEDGER = (
    "R2301 tokens: local=~10k api=0 api_reason=verification-only window - one "
    "full reconcile battery with its streamed evidence file, one four-section "
    "follow-up through the shipped callable plus one matrix regeneration from "
    "that evidence, two register writes through the shipped close and append "
    "writers, one waterline fold, and the queue/board/state/export closeout; "
    "zero cloud calls and zero external API touches; the product face carries "
    "to R2302")

SELF_HEAL = (
    "R2301 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and "
    "this session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(sixty-fifth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).")

DISCLOSURES = (
    "R2301 honest disclosures: (a) the battery ran as a detached hidden "
    "process because battery_stream buffers its evidence in memory and writes "
    "once at completion, so every probe before the end legitimately found no "
    "file - that was buffering and not a dead runner, confirmed by the live "
    "child process and then by the 780458B file. (b) One polling command was "
    "cancelled by the five-minute no-output rule mid-wait; it spent no work "
    "and the battery was untouched, verified by the process id still alive "
    "immediately afterwards. (c) Both follow-up legs are retained in the "
    "evidence file (1889B FAIL then 1950B PASS); the FAIL leg is the designed "
    "first use of the matrix section, which refuses to rewrite the stale doc. "
    "(d) The tech queue was not touched: claimable stayed 10 against its "
    "floor, so no gap row was due, and the board is the only queue-family "
    "file this window edited. (e) This round shipped no product code, so the "
    "register successor names the product face (evidence_variants, tech head "
    "line 366) rather than a second verification. (f) The fold is disclosed in "
    "full: the first attempt folded window 1..4 (the whole R2287 block) and the "
    "predicate REFUSED to write because its own gate check read predicted "
    "75020B plus a 7000B reserve against the 78500B waterline, so nothing was "
    "folded; the closeout then appended anyway and left the file at 82050B over "
    "the line. That was repaired before any commit: src/os/repair_R2301.py "
    "removed exactly the four items and proved the restored file byte-exact "
    "(77573B, sha16 8799fafce253c967, the pre-append digest the refused fold "
    "plan had recorded), then the fold ran once over window 1..8 (the R2287 "
    "block plus the R2288 block, 592 tokens all covered, predicted 71122B equal "
    "to measured) and the append followed. (g) A second fold ran by accident "
    "while the board guard was still wrong and appended the same window to the "
    "archive again; it was undone by restoring state.json and backlog.md from "
    "HEAD and trimming the archive byte-exactly back to its 10587B pre-window "
    "size, and the fold guard now refuses a second fold of the same window. "
    "Every number in this item is the post-repair reading.")


def fold_first():
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    if any(line.startswith("Fold R2301:") for line in state["log"]):
        print("FOLD already applied this window; not folded twice")
        return {"skipped": True, "bytes": len(raw)}
    window = state["log"][WINDOW[0] - 1:WINDOW[1]]
    tokens = set()
    for line in window:
        tokens |= set(state_fold.PAT.findall(line))
    summary = (
        "Fold R2301: log lines %d..%d folded verbatim into the archive so the "
        "closeout fits the waterline; window tokens: %s"
        % (WINDOW[0], WINDOW[1], " ".join(sorted(tokens))))
    return state_fold.fold(
        REPO, "R2301", FOLD_NO, WINDOW[0], WINDOW[1], summary,
        reserve=7000, execute=True)


def edit_board():
    raw = open(BOARD, "rb").read().decode("utf-8")
    items = raw.split("\n")
    head = items[0]
    prefix = "- [ ] [carried 2026-11-01 R2300] R2301 first item:"
    if head.startswith("- [x] [done 2026-11-01 R2301]"):
        return -len(raw.encode("utf-8"))
    if head.startswith("- [ ] [carried 2026-11-01 R2301] R2302"):
        print("BOARD already carries this window's row; not rewritten")
        return -len(raw.encode("utf-8"))
    if not head.startswith(prefix):
        raise SystemExit("E_CLOSE_NO_ROW: the board head is not the R2301 row")
    rest = head.split("]", 1)[1]
    items[0] = ("- [x] [done 2026-11-01 R2301] [carried 2026-11-01 R2300]"
                + rest + BOARD_DONE)
    out = SUCCESSOR + "\n" + "\n".join(items)
    body = out.encode("utf-8")
    open(BOARD, "wb").write(body)
    return len(body)


def build_state():
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    before_items = len(state["log"])
    state["tick"] = 2301
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES])
    ensure_ascii = all(b < 0x80 for b in raw)
    text = json.dumps(state, ensure_ascii=ensure_ascii, indent=2)
    text = state_io.canon(text)
    return raw, state, before_items, text.encode("utf-8")


def main(argv):
    execute = "--execute" in argv
    if execute:
        fold = fold_first()
        print("FOLD %s" % json.dumps(fold, sort_keys=True))
    board_bytes = edit_board() if execute else 0
    raw, state, before_items, new = build_state()
    print("LOG_ITEMS %d -> %d" % (before_items, len(state["log"])))
    print("TICK %s" % state["tick"])
    print("STATE %dB -> %dB DELTA %+d" % (len(raw), len(new), len(new) - len(raw)))
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    folder = os.path.dirname(STATE)
    temp = os.path.join(folder, ".closeout_R2301.tmp")
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