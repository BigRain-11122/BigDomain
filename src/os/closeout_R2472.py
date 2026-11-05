"""R2472 closeout: state tick and log lines, backlog row, heartbeat row."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
BACKLOG = os.path.join(SRC, "backlog.md")
BEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2472

LINES = [
    "2026-11-05 R2472 VERIFICATION window on the battery the R2471 business face "
    "owed (reconcile-battery-R2471, pre-registered at 563 suites / 4354 criteria), "
    "because the R2168 mixed-tree rule puts the battery ahead of the carried audit "
    "row product-face-R2456 (still open, still claimable, CARRIED not dropped). "
    "Five-silence scan at open: git status empty at HEAD b1938c87 equal to "
    "origin/main with no .git/index.lock, zero @BigDomain rows in the evolution "
    "ledger, the content-addressed decisions diff new=0 against the 135-token / "
    "211-row baseline, the group orders tail unchanged at 2026-11-05 00:36 equal to "
    "the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day "
    "gate, queue head state/queue/tech.md:522 prefix AC-PFKC1 with the floor MET. "
    "The debt gate read open=3 first=1 and named product-face-R2456, but the "
    "register also carried the open reconcile-battery-R2471 row, so the battery ran "
    "FIRST and no product byte was touched.",

    "2026-11-05 R2472 BATTERY LEG 1 RED, and the cause was named by the shipped "
    "checker rather than guessed: RUNNER FAIL (2 failed assertions) in 1046.4s with "
    "562/563 suites green and the single failing suite reconcile-daily-census 7/8, "
    "whose AC-CD7 live leg read exit=2 label=drift against DRIFT-CLEAN. "
    "src/os/qa_writer_census.py --check then named the three files and their class: "
    "qa/hub-ledger-R2471-a.log, -b.log and qa/hub-ledger-live-R2471.log were "
    "ps-utf16 captures, i.e. PowerShell redirects instead of the one utf-8 LF single "
    "writer - the same shell-capture debt R2362, R2405, R2439 and R2451 each paid. "
    "The red leg is kept as qa/reconcile-all-R2472.log and is not counted as green.",

    "2026-11-05 R2472 FIX AT THE BIRTH SITE, not by widening the baseline: "
    "src/os/repair_R2472.py decoded each capture, proved its LINE SET identical to "
    "the decoded original through run_identity.normalize, then wrote utf-8 LF with "
    "one atomic os.replace and a byte read-back (952B->468B twice, 2662B->1319B, "
    "crlf=0, readback=True). The repair and the three normalised files were "
    "committed ALONE as d5332644, so the retry below started on a clean tree. "
    "qa_writer_census then re-read flags=0 verdict=DRIFT-CLEAN with its 529-entry "
    "baseline UNTOUCHED, and test_reconcile_daily_census re-read SUITE PASS 8/8 with "
    "AC-CD7 at exit=0 DRIFT-CLEAN. No criterion was loosened.",

    "2026-11-05 R2472 BATTERY LEG 2 GREEN on the committed repair tree d5332644 with "
    "an empty git status before the run: RUNNER PASS 563/563 suites green plus "
    "reconcile controls 7/7 in 1074.7s and the closing summary line reads 'PASS "
    "suites 563/563 green, expected criteria total=4354', i.e. EXACTLY the total "
    "pre-registered in the debt register at R2471; birth-site TMP RECLAIM "
    "candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence "
    "qa/reconcile-all-R2472-retry.log written by ONE utf-8 LF single writer through "
    "src/os/battery_stream.py (861296B at the green leg, 863246B with both follow-up "
    "legs), re-measured byte-wise: crlf=0 lone_cr=0 bom=False. The battery was "
    "launched detached and unfiltered into logs/battery-R2472-retry-stdout.log, so "
    "the R2211/R2268/R2289/R2348/R2453/R2458/R2461 filtering-pipe trap was not "
    "re-paid.",

    "2026-11-05 R2472 the four follow-up sections produced the designed order: LEG 1 "
    "(--dry-run) read SECTION matrix FAIL matrix mismatch on-disk=54266B "
    "regenerated=54284B with no byte written, fingerprint PASS CLEAN domains=5, "
    "profile PASS byte-identical, census PASS DRIFT-CLEAN; then "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS "
    "round own green evidence through --evidence plus --stamp-from and printed "
    "'PASS generated ... 54284 bytes ... registry suites=563 criteria=4354 "
    "evidence=qa/reconcile-all-R2472-retry.log green=563/563', with --check reading "
    "byte-identical at 54284B / 563 suites / 4354 criteria. LEG 2 then read all four "
    "sections PASS - matrix byte-identical 54284B, fingerprint CLEAN domains=5, "
    "profile byte-identical, census DRIFT-CLEAN - for VERDICT R2472 PASS "
    "failing=none (APPENDED 1950B eol_ok=True). The matrix is self-describing this "
    "round: its own green line reads 563/563 because it names this round own battery "
    "rather than a borrowed older leg.",

    "2026-11-05 R2472 debt register closed through its own writer: "
    "reconcile-battery-R2471 closed through debt_close at its predicted 122265B -> "
    "122269B (line=200, open 3->2, done 178->179, readback=ok) after a dry run that "
    "named exactly those deltas. NO successor battery was registered because this "
    "window changed no product src byte and the registry is unmoved at 563 suites / "
    "4354 criteria - the only src file added is a one-off repair script, not a "
    "module. The gate now reads verdict=CLAIM-FIRST item=product-face-R2456 "
    "opened=R2455 carried=17 stale=yes open=2 first=1, naming the tech head "
    "state/queue/tech.md:522 prefix AC-PFKC1 row_key_carrier_scope, whose "
    "AC-PFKC1..AC-PFKC6 were pinned in that row at R2446 BEFORE any code. The "
    "NEXT window should ship a BUSINESS face and name the supersession, per the CEO "
    "standing order OB-20261105-003656-879.",

    "2026-11-05 R2472 waterline and residue, measured rather than assumed: the fold "
    "was DUE at open (state.json 79291B against the 78500B gate, margin -791) and "
    "ran as fold 655 at a TRUE round-block boundary - window 1..9, the previous fold "
    "summary plus the whole R2461 block ending on its own push line, with line 10 "
    "opening R2462 - predicted=measured 72428B, margin 6072, tokens_total=258 with "
    "tokens_missing=[] and round_split=None. The dated residue declaration had "
    "expired at until=R2470, so it was renewed through its shipped re-pin writer at "
    "declared_by=R2472 until=R2482: 283 entries, dropped=0, 79146B -> 78996B, and "
    "residue_triage --check now reads every entry TRIAGED at exit 0. A SECOND fold "
    "runs after this append so the round lands under the gate rather than over it.",

    "2026-11-05 R2472 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt, no P-47 business "
    "surface was touched, and every P-47 item beyond the shipped sandbox faces "
    "remains blocked on CEO physical items; what the window bought is a proven "
    "registry (563 suites, 4354 criteria) on the exact tree R2471 committed plus one "
    "real evidence-dialect repair; (b) the first battery was red on debt R2471 left "
    "behind - three PowerShell UTF-16 captures - not on a product defect, and the "
    "repair is dialect only with the payload line set proved identical; (c) my own "
    "first launch passed an over-qualified --runner path, died in 0.1s and left a "
    "215-byte stub evidence file, which was deleted before any commit and before the "
    "real launch, disclosed rather than swept; (d) Docker is absent on this host, so "
    "the compose bring-up of the sandbox faces stays unproved and is not claimed; "
    "(e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items (merchant id, mini-program appid/secret); (f) the window ran far past its "
    "25-minute budget on two full batteries (1046.4s red + 1074.7s green) plus two "
    "follow-up legs and two folds, named rather than hidden; (g) tasks.md was not "
    "touched, it is the P-47 canonical board; (h) READ-ONLY observation outside this "
    "repo: FluxGroup/docs/orders.md still carries its leftover empty conflict "
    "markers, already reported in HQ-FEEDBACK.md.",

    "R2472 tokens: local=~11k api=0 api_reason=verification window - two full "
    "reconcile batteries launched detached through the single-writer stream (one red "
    "on three PowerShell UTF-16 evidence captures named by the shipped census, one "
    "green at the pre-registered 563 suites / 4354 criteria), one birth-site dialect "
    "repair committed alone with its payload lines proved identical and the census "
    "baseline untouched, one suite re-read green, four follow-up sections with one "
    "designed matrix FAIL and one green verdict after a stamp-aligned regeneration, "
    "one battery debt row closed through its shipped CLI, one round-block fold, one "
    "dated residue declaration renewed from a live reading, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]

ROW = (
    "- [x] [done 2026-11-05 R2472] R2472 VERIFICATION window on the battery the R2471 "
    "business face owed (reconcile-battery-R2471, pre-registered 563 suites / 4354 "
    "criteria), per the R2168 mixed-tree rule: zero product code changed. BATTERY LEG "
    "1 RED in 1046.4s - 562/563 suites, one red suite reconcile-daily-census AC-CD7 "
    "reading exit=2 drift, and qa_writer_census named the cause as three R2471 "
    "evidence captures stored as PowerShell UTF-16 (ps-utf16). FIX AT THE BIRTH SITE: "
    "src/os/repair_R2472.py decoded each file, proved the line set identical through "
    "run_identity.normalize, rewrote utf-8 LF with atomic replace and byte read-back "
    "(952B->468B twice, 2662B->1319B, crlf=0), committed ALONE as d5332644; census "
    "then flags=0 DRIFT-CLEAN with its 529-entry baseline untouched and the suite "
    "re-read 8/8 with AC-CD7 at exit=0. BATTERY LEG 2 GREEN on the committed repair "
    "tree: RUNNER PASS 563/563 suites, controls 7/7, 1074.7s, criteria total=4354 "
    "EXACTLY as pre-registered (qa/reconcile-all-R2472-retry.log, 861296B green / "
    "863246B with both legs, crlf=0 lone_cr=0 bom=False, one utf-8 LF single writer, "
    "TMP RECLAIM 932/932). Follow-up four sections: designed matrix FAIL at 54266B vs "
    "54284B with no byte written, stamp-aligned regeneration to 54284B at 563/4354 "
    "green=563/563 with --check byte-identical, then VERDICT R2472 PASS failing=none. "
    "Debt: reconcile-battery-R2471 closed through debt_close at its predicted "
    "122265B -> 122269B (line=200, open 3->2, done 178->179, readback ok); no "
    "successor battery owed because no product src byte moved and the registry is "
    "unmoved. Fold 655 at a true round-block boundary (window 1..9 = previous fold "
    "summary + whole R2461 block, predicted=measured 72428B, margin 6072, tokens 258 "
    "none missing); residue declaration had expired at R2470 so it was renewed from "
    "one live reading at declared_by=R2472 until=R2482 (283 entries, dropped=0, "
    "79146B->78996B, check exit 0 TRIAGED). Zero product points; next window owes a "
    "BUSINESS face per CEO standing order OB-20261105-003656-879 and should name the "
    "supersession of the carried audit row product-face-R2456 (carried=17, stale)."
)

BEAT_LINE = (
    "tick=2472 R2472 verification: battery red on three UTF-16 evidence captures, "
    "repaired at birth site (d5332644), retry green 563/563 suites at 4354 criteria, "
    "matrix restamped 54284B byte-identical, fold 655 + residue renewed | "
    "reconcile-battery-R2471 CLOSED, no successor owed | zero product points"
)


def write_state(state):
    import state_io
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if back["tick"] != state["tick"] or len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    return os.path.getsize(PATH)


def main():
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("log already carries this window")
    else:
        state["tick"] = TICK
        state["log"].extend(LINES)
        size = write_state(state)
        print("state tick %d, log +%d, bytes=%d" % (TICK, len(LINES), size))

    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2472 VERIFICATION window" not in text:
        newline = "\r\n" if "\r\n" in text else "\n"
        text = ROW + newline + text
        tmp = BACKLOG + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, BACKLOG)
        print("backlog row prepended")
    else:
        print("backlog row already present")

    with io.open(BEAT, "r", encoding="utf-8", newline="") as handle:
        beat = handle.read()
    if BEAT_LINE not in beat:
        newline = "\r\n" if "\r\n" in beat else "\n"
        if not beat.endswith(("\n", "\r")):
            beat += newline
        beat += BEAT_LINE + newline
        tmp = BEAT + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(beat)
        os.replace(tmp, BEAT)
        print("heartbeat row appended")
    else:
        print("heartbeat row already present")


if __name__ == "__main__":
    main()