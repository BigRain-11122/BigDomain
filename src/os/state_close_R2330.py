"""state_close_R2330 - the round ledger for the verification window.

This window shipped no product code: it ran the deferred battery on the
committed R2329 tree, found one suite red, measured the root cause and
repaired it at its birth site, then re-ran to green. Bumps the tick,
appends the four log lines this window owes, closes the carried board row
and opens the successor product row. Dry run by default; --execute writes
utf-8 with LF and a read-back proof.
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

TICK = 2330
TOKEN_RE = re.compile(r"[DC]-\d{8}-\d{2}")

LIVE = (
    "2026-11-01 R2330 verification window (five-silence scan clean at open: "
    "empty git status --short and no index.lock; the content-addressed diff "
    "of the group decisions.md against the stored baseline read NEW=0 over 61 "
    "live tokens, so no decision row was owed; the evolution ledger carries "
    "no @BigDomain row at all; the group orders tail is unchanged at the "
    "2026-11-01 10:4x baseline R2321 already acked by number as "
    "non-execution; benchmarks refreshed 2026-11-01 inside the seven-day "
    "gate). The debt register read open=1 done=73 with first=none - the only "
    "open row is the elevated-shell loop-s4u item and no product-face row was "
    "owed - so this window claimed the board TOP row: THE BATTERY ON THE "
    "COMMITTED TREE with zero product edits, pre-registered at 472 suites / "
    "3808 criteria (+1 suite / +6 criteria against R2328 471/3802 from the "
    "R2329 os-stamp-exempt-prune suite). FIRST RUN WAS RED: 471/472 suites "
    "with 2 failed assertions in ONE suite, ledger-devshare-persist AC-DSVP1 "
    "and AC-DSVP2, criteria total 3808 exactly as pre-registered "
    "(qa/reconcile-all-R2330.log, restored to 789740B from the tool capture "
    "after this window deleted it by accident). ROOT CAUSE MEASURED, NOT "
    "GUESSED: read_battery dumps both dev boards in FULL, and dev_board "
    "exposes the read-time minute ring (minute_window + minute_used) by "
    "design, so any read either side of a minute boundary differs with no "
    "persisted state moving; a probe pinned the exact field-level diff "
    "(minute_window '2026-11-01T14:20' -> '14:21' and nothing else) and a "
    "harness that advances the minute on every read reproduced the red "
    "deterministically (1/7 green) instead of waiting for the 0.5% draw. "
    "REPAIR AT THE BIRTH SITE, committed alone as f14b56fe: project_clock "
    "masks exactly minute_window and minute_used inside the board dumps, and "
    "AC-DSVP1 gained a live guard that the ring is really present in the raw "
    "dump and that a poked persisted counter still reads as a diff, so the "
    "projection can never hide a moved value (a blind projection reads RED - "
    "measured). RETRY ON THE COMMITTED REPAIR TREE: RUNNER PASS 472/472 suites "
    "green plus controls 7/7 in 823.7s with birth-site TMP RECLAIM 932/932 "
    "worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2330-retry.log, "
    "789666B, single writer utf-8 LF through src/os/battery_stream.py), "
    "criteria total 3808 - the prediction matched the measurement with no "
    "correction. Four follow-up sections through src/os/battery_followup.py: "
    "matrix FAILED first on the stale doc (on-disk=45205B regenerated=45292B) "
    "and did NOT rewrite it; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 472 suites / 3808 criteria (45292B) and "
    "the re-run read all four PASS, closing VERDICT R2330 PASS. Live product "
    "re-read: stamp_exempt_prune --round R2330 reads NOTHING-TO-RETIRE over "
    "the real 381-entry declaration (79026B unchanged)."
)

SELF_HEAL = (
    "R2330 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(ninety-second consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2330 honest disclosures: (a) this window shipped NO product code and "
    "scores 0 product points; the work it did was the battery the board named "
    "plus the birth-site repair the battery found. (b) The red leg was "
    "DELETED by this window's own re-launch command (the Remove-Item ran "
    "before the retry) and is disclosed rather than glossed: it was rebuilt "
    "through one python single writer from the shell tool's full capture of "
    "that run, 789740B utf-8 LF ending on the same 'RUNNER FAIL (2 failed "
    "assertions)' line, so the bytes are the run's own stream and not a "
    "rewrite. (c) The first tool invocation of this window was wrong: "
    "reconcile_all.py does not accept --help, so it started a suite and "
    "created an untracked file literally named '--help' plus one orphaned "
    "smoke_test child whose parent had already died; the file was removed, "
    "the orphan was verified by creation time and parent id and terminated, "
    "and no evidence is claimed from that dead run. (d) The repair is a "
    "TEST-side projection, never a product change: the module keeps reporting "
    "the minute ring (that is its design), and the criterion keeps its "
    "meaning - persisted state must survive close/reopen byte-identically - "
    "with the guard proving the projection hides nothing. (e) The residual "
    "exposure is named, not hidden: a MONTH rollover inside the suite would "
    "still move quota_used and the window field, and that remains a real "
    "(if far rarer) clock dependency of this fixture; it is not masked "
    "because the month domain is genuinely part of the reading. (f) tasks.md "
    "was left untouched: it is the P-47 canonical board and carries no row "
    "for a verification window, disclosed rather than silently skipped."
)

LEDGER = (
    "R2330 tokens: local=~30k api=0 api_reason=verification window that "
    "found and repaired a real defect - two full reconcile batteries (the red "
    "leg and the green retry), one field-level clock probe, one forced-"
    "rollover harness twice (red before the repair, green after), one blind-"
    "projection control, one birth-site repair committed alone, one four-"
    "section follow-up twice plus one matrix regeneration, one live product "
    "reading and the state/export/heartbeat/board closeout; zero cloud calls "
    "and zero external API touches; the product face resumes at R2331"
)

BOARD_DONE = (
    "- [x] [done 2026-11-01 R2330 - BATTERY RED THEN GREEN on the committed "
    "tree: first run 471/472 suites with 2 failed assertions in "
    "ledger-devshare-persist (AC-DSVP1/AC-DSVP2), criteria total 3808 exactly "
    "as pre-registered; root cause measured as the read-time minute ring "
    "inside full board dumps (probe pinned minute_window as the only moving "
    "field, forced-rollover harness reproduced 1/7 deterministically); repair "
    "committed alone as f14b56fe (project_clock masks only minute_window and "
    "minute_used, AC-DSVP1 guards ring presence and a poked persisted counter, "
    "a blind projection reads RED); RETRY RUNNER PASS 472/472 plus controls "
    "7/7 in 823.7s, TMP RECLAIM 932/932, criteria 3808; four follow-up "
    "sections PASS after the designed matrix FAIL and its regeneration to "
    "472/3808 (45292B); live stamp_exempt_prune still NOTHING-TO-RETIRE over "
    "381 entries; zero product code, 0 product points]"
)

BOARD_NEXT = (
    "- [ ] [carried 2026-11-01 R2330] R2331 first item: BACK TO THE PRODUCT "
    "FACE on the row the reader names. `python src/os/queue_head.py --head "
    "tech` reads state/queue/tech.md:383 prefix AC-RET1 (claimable=10) - the "
    "R2308 retire_candidate seed, whose AC-RET1..AC-RET6 criteria are already "
    "pinned INSIDE that row BEFORE the code (re-read it rather than trusting "
    "this line): three readers now each hold one half of the retirement "
    "question and none of them answers 'is this declared gate a candidate for "
    "retirement at all'. Run a fresh zero-occupancy anchor check at HEAD "
    "(`git grep -F`, expecting rc 1) before writing anything, ship one "
    "product face with its suite, refill the tech floor with one real gap row "
    "if the claim drops claimable to 9, and commit BEFORE any battery (the "
    "R2168 mixed-tree rule) - the battery is then the successor row with the "
    "pre-registered target of 473 suites / 3814 criteria, exactly +1 suite / "
    "+6 criteria against this window's measured 472/3808, and any larger "
    "delta must be named rather than swept. Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop reads LogonType=InteractiveToken (ninety-second "
    "consecutive disclosure; carried as the stale row loop-s4u-reconcile in "
    "state/debt.md). Also still unshipped and named: the R2310 seed "
    "residue_triage_append, because every fold that archives a round's log "
    "block can recreate residue and the repair has been spliced by hand six "
    "times."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != text:
        raise SystemExit("E_READBACK %s" % path)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % path)


def main(argv):
    state = json.loads(read_text(STATE))
    decisions = read_text(DECISIONS) if os.path.isfile(DECISIONS) else ""
    tokens = sorted(set(TOKEN_RE.findall(decisions)))
    backlog = read_text(BACKLOG).split("\n")
    print("tick %d -> %d" % (state.get("tick"), TICK))
    print("decision tokens: stored=%d live=%d new=%s"
          % (len(state.get("last_dec_tokens") or []), len(tokens),
             sorted(set(tokens) - set(state.get("last_dec_tokens") or []))))
    print("backlog line 1 starts with: %s" % backlog[0][:60])
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    state["tick"] = TICK
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = len(decisions.split("\n"))
    log = state.get("log") or []
    for line in (LIVE, SELF_HEAL, HONEST, LEDGER):
        log.append(line)
    state["log"] = log
    write_text(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    backlog[0] = BOARD_DONE
    backlog.insert(1, BOARD_NEXT)
    write_text(BACKLOG, "\n".join(backlog))
    print("WROTE state.json and backlog.md with read-back")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))