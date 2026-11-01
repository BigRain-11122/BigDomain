"""state_close_R2341 - the round ledger for the verification window.

This window shipped no product code: it ran the green battery the R2340 row
carried (477 suites / 3838 criteria, exactly the pre-registered figure), took
the four follow-up sections through their designed matrix FAIL and the
regeneration that closes it, and acknowledges the four new group decision rows
as non-execution for this company. Bumps the tick, appends the log lines this
window owes, closes the carried board row and opens the successor product row.
Dry run by default; --execute writes utf-8 with LF and a read-back proof.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
DECISIONS = os.path.join(os.path.dirname(os.path.dirname(ROOT)),
                         "docs", "decisions.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

TICK = 2341
TOKEN_RE = re.compile(r"[DC]-\d{8}-\d{2}")

LIVE = (
    "2026-11-01 R2341 verification window (five-silence scan clean at open: "
    "empty git status --short at 50b88267 and no index.lock; the "
    "content-addressed diff of the group decisions.md read FOUR new rows, "
    "D-20261101-19..D-20261101-22, and GONE=0, so this window owed an ack "
    "line rather than a rescan - see the decision line below; the evolution "
    "ledger carries zero @BigDomain rows, so no transfer was owed; the local "
    "orders board tail is unchanged at its 2026-09-28 rows and the group "
    "orders tail still reads the 2026-11-01 10:4x baseline R2321 already "
    "acked as non-execution; benchmarks refreshed 2026-11-01, inside the "
    "seven-day gate). The board TOP row was the R2340 carry: THE GREEN FULL "
    "BATTERY on the committed R2340 tree, pre-registered at 477 suites / "
    "3838 criteria - exactly +1 suite / +6 criteria against R2338 "
    "(476/3832) from the R2339 os-orphan-promote suite - with the census "
    "baseline already re-frozen and committed by R2340 before its run, so "
    "the tree was empty when this run started. MEASURED RESULT: RUNNER PASS "
    "477/477 suites green plus controls 7/7 in 826.5s with birth-site TMP "
    "RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2341.log, 791836B, single writer utf-8 LF through "
    "src/os/battery_stream.py), criteria total 3838 - the prediction matched "
    "the measurement with no correction and no swept delta. Four follow-up "
    "sections through src/os/battery_followup.py ran in their pinned order: "
    "matrix FAILED first on the stale shipped doc (on-disk=45594B "
    "regenerated=45670B) and did NOT rewrite it, which is the designed "
    "order; src/sandbox/suite_matrix.py then regenerated "
    "docs/sandbox-suite-matrix.md to 477 suites / 3838 criteria (45670B) and "
    "the re-run read all four sections PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing VERDICT R2341 PASS. No product file was "
    "touched before, during or after the battery."
)

DECISION = (
    "R2341 group decision ack: the content-addressed diff against the stored "
    "baseline read NEW=D-20261101-19, D-20261101-20, D-20261101-21, "
    "D-20261101-22 and GONE=0 (65 live tokens, baseline 61). Judgement: all "
    "four are NON-EXECUTION for this company - D-19 and D-20 dispatch lane "
    "task-guard re-registration and a scanning-domain evidence rule to "
    "@BigCompute and @HQ, D-21 rewrites Q-TTS-1202R to no-exec-leg for "
    "@BigStream, and D-22 extracts the 35-round read state where this "
    "company appears only as a no-op row (its own HQ-FEEDBACK last write "
    "2026-10-29 05:15) plus a physical-reminder naming the BigDomain "
    "bootstrap files as still waiting on the CEO. Acknowledged by number, no "
    "action taken here, no new law written. Baseline moved to the current "
    "token set and the current row count (120 lines, one fewer than the "
    "stored 121 because of a formatting edit, with GONE=0 proving no row was "
    "lost - the reason this law is content-addressed and not line-addressed)."
)

SELF_HEAL = (
    "R2341 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-second consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2341 honest disclosures: (a) this window shipped NO product code and "
    "scores 0 product points; its work was the battery the board carried plus "
    "the four follow-up sections that battery owes. (b) The green run is the "
    "SECOND attempt at this exact target: R2340 measured it red on one leg "
    "and repaired the criterion stricter, and that red leg stays committed as "
    "evidence at qa/reconcile-all-R2340.log rather than being overwritten by "
    "this green log. (c) No new suite, module or criterion came from this "
    "window, so the +1 suite / +6 criteria against R2338 still resolves "
    "entirely to the R2339 os-orphan-promote suite - counted, not assumed. "
    "(d) The matrix doc is the only tracked file this window changed before "
    "the closeout, and it changed because the registry grew, not because the "
    "doc was edited by hand. (e) tasks.md untouched: the P-47 board carries "
    "no row for a verification window, disclosed rather than silently "
    "skipped. (f) The tech queue head was re-read live at open and reads "
    "state/queue/tech.md:388 prefix AC-OPL1 (orphan_promotion_ledger, "
    "claimable=10, floor met), so the successor row below names the row the "
    "reader actually named instead of a remembered line."
)

LEDGER = (
    "R2341 tokens: local=~28k api=0 api_reason=verification window - one "
    "full reconcile battery (826.5s, 477 suites), one four-section follow-up "
    "run plus one matrix regeneration and the closing re-run, one "
    "content-addressed decision diff, one live queue-head read and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero "
    "external API touches; the product face resumes at R2342 on AC-OPL1"
)

SUCCESSOR = (
    "- [ ] [carried 2026-11-01 R2341] R2342 first item: BACK TO THE PRODUCT "
    "FACE on the row the reader names. `python src/os/queue_head.py --head "
    "tech` reads state/queue/tech.md:388 prefix AC-OPL1 (claimable=10) - the "
    "R2339 orphan_promotion_ledger seed, whose AC-OPL1..AC-OPL6 criteria are "
    "already pinned INSIDE that row BEFORE the code, so re-read the row "
    "rather than trusting this line. Ship one product face with its suite "
    "(promotion acts recorded as one append-only ledger row each: the source "
    "leg, the canonical target, byte count, digest, whether bytes were "
    "actually copied or the target already matched, the round that ordered "
    "it, and a refusal when a promotion is recorded for a trace that does not "
    "exist), commit BEFORE any battery (the R2168 mixed-tree rule) - the "
    "battery that follows is pre-registered at 478 suites / 3844 criteria "
    "against this window 477/3838. Refill the tech floor with one real gap "
    "row if the claim drops claimable to 9. ALSO OPEN AS A REAL MECHANISM "
    "GAP, unchanged from R2340: fold-block-boundary - a fold that picks its "
    "window by item count or byte arithmetic can cut a round block in half "
    "and leave round lines live with their ledger line archived; the guard "
    "belongs in the successor row that touches folds. Also open and needing "
    "an ELEVATED shell: BigDomain-OSLoop reads LogonType=InteractiveToken "
    "(hundred-and-second consecutive disclosure; carried as "
    "loop-s4u-reconcile in state/debt.md).\n"
)

DONE_TAG = " [done 2026-11-01 R2341 - RUNNER PASS 477/477 suites plus " \
           "controls 7/7 in 826.5s, criteria total 3838 EXACTLY as " \
           "pre-registered against R2338 (476/3832), four follow-up sections " \
           "PASS after the designed matrix FAIL and its regeneration to " \
           "45670B (477 suites / 3838 criteria), VERDICT R2341 PASS; zero " \
           "product code, 0 product points]"


def read_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def tokens():
    with io.open(DECISIONS, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    found = []
    for token in TOKEN_RE.findall(text):
        if token not in found:
            found.append(token)
    return found


def close_state(state, token_set):
    state["tick"] = TICK
    old = list(state.get("last_dec_tokens") or [])
    merged = old + [t for t in token_set if t not in old]
    state["last_dec_tokens"] = merged
    with io.open(DECISIONS, "r", encoding="utf-8", errors="replace") as handle:
        rows = len(handle.read().split("\n"))
    state["last_decision_rows"] = rows
    log = state["log"]
    log.append(LIVE)
    log.append(DECISION)
    log.append(SELF_HEAL)
    log.append(HONEST)
    log.append(LEDGER)
    return state


def close_board(text):
    marker = "- [ ] [carried 2026-11-01 R2339] R2340 first item: THE BATTERY"
    index = text.find(marker)
    if index < 0:
        raise SystemExit("E_BOARD_ROW_MISSING")
    end = text.find("\n", index)
    if end < 0:
        end = len(text)
    row = text[index:end]
    if "[done 2026-11-01 R2341" in row:
        raise SystemExit("E_BOARD_ALREADY_CLOSED")
    row = row.replace("- [ ] ", "- [x] ", 1) + DONE_TAG
    text = text[:index] + row + text[end:]
    return SUCCESSOR + text


def main(argv):
    state = read_state()
    token_set = tokens()
    old_tokens = list(state.get("last_dec_tokens") or [])
    new = [t for t in token_set if t not in old_tokens]
    gone = [t for t in old_tokens if t not in token_set]
    state = close_state(state, token_set)
    with io.open(BACKLOG, "r", encoding="utf-8") as handle:
        board = handle.read()
    board = close_board(board)
    body = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    print("NEW=%s GONE=%s tokens=%d tick=%d log=%d state=%dB board=%dB"
          % (new, gone, len(state["last_dec_tokens"]), TICK, len(state["log"]),
             len(body.encode("utf-8")), len(board.encode("utf-8"))))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, STATE)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body:
        print("E_READBACK")
        return 3
    if os.path.exists(temp):
        print("E_RESIDUE")
        return 3
    btemp = BACKLOG + ".tmp"
    with io.open(btemp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(board)
    os.replace(btemp, BACKLOG)
    with io.open(BACKLOG, "r", encoding="utf-8") as handle:
        bback = handle.read()
    if bback != board:
        print("E_BOARD_READBACK")
        return 3
    if os.path.exists(btemp):
        print("E_BOARD_RESIDUE")
        return 3
    print("WROTE state and board, readback ok, temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))