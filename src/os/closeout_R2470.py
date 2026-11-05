"""R2470 closeout: state tick and log lines, backlog row, heartbeat row."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
BACKLOG = os.path.join(SRC, "backlog.md")
BEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2470

LINES = [
    "2026-11-05 R2470 VERIFICATION window on the battery the R2469 business face "
    "owed (reconcile-battery-R2469, pre-registered at 562 suites / 4348 criteria), "
    "because the R2168 mixed-tree rule puts the battery ahead of the carried audit "
    "row product-face-R2456 (still open, still claimable, CARRIED not dropped). "
    "Five-silence scan at open: git status empty at HEAD 73111332 equal to "
    "origin/main with no .git/index.lock, zero unreplied @BigDomain rows in the "
    "evolution ledger, the content-addressed decisions diff new=0 against the "
    "135-token / 211-row baseline, the group orders tail unchanged at 2026-11-05 "
    "00:36 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside "
    "the seven-day gate, queue head state/queue/tech.md:522 prefix AC-PFKC1 with "
    "the floor MET. The debt gate read open=3 first=1 and named product-face-R2456, "
    "but the register also carried the open reconcile-battery-R2469 row, so the "
    "battery ran FIRST and no product byte was touched.",

    "2026-11-05 R2470 BATTERY GREEN on the committed tree 73111332 with an empty "
    "git status before the run: RUNNER PASS 562/562 suites green plus reconcile "
    "controls 7/7 in 1042.3s (1042.8s wall) and the closing summary line reads "
    "'PASS suites 562/562 green, expected criteria total=4348', i.e. EXACTLY the "
    "total pre-registered in the debt register at R2469; birth-site TMP RECLAIM "
    "candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence "
    "qa/reconcile-all-R2470.log written by ONE utf-8 LF single writer through "
    "src/os/battery_stream.py (860725B at the green leg, 862675B with both "
    "follow-up legs), re-measured byte-wise: crlf=0 bom=False. The battery was "
    "launched detached and unfiltered into logs/battery-R2470-stdout.log, so the "
    "R2211/R2268/R2289/R2348/R2453/R2458/R2461 filtering-pipe trap was not "
    "re-paid, and no red leg exists because none was produced.",

    "2026-11-05 R2470 the four follow-up sections produced the designed order: "
    "LEG 1 (--dry-run) read SECTION matrix FAIL matrix mismatch on-disk=54192B "
    "regenerated=54185B with no byte written, fingerprint PASS CLEAN domains=5, "
    "profile PASS byte-identical, census PASS DRIFT-CLEAN; then "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from "
    "THIS round own green evidence through --evidence plus --stamp-from and "
    "printed 'PASS generated ... 54185 bytes ... registry suites=562 "
    "criteria=4348 evidence=qa/reconcile-all-R2470.log green=562/562', with "
    "--check reading byte-identical at 54185B / 562 suites / 4348 criteria. "
    "LEG 2 then read all four sections PASS - matrix byte-identical 54185B, "
    "fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN - "
    "for VERDICT R2470 PASS failing=none (APPENDED 1950B eol_ok=True). The "
    "matrix is self-describing this round: its own green line reads 562/562 "
    "because it names this round own battery rather than a borrowed older leg.",

    "2026-11-05 R2470 debt register closed through its own writer: "
    "reconcile-battery-R2469 closed through debt_close at its predicted "
    "121819B -> 121823B (line=199, open 3->2, done 177->178, readback=ok) after "
    "a dry run that named exactly those deltas. NO successor battery was "
    "registered because this window changed no product src byte and the registry "
    "is unmoved at 562 suites / 4348 criteria. The gate still reads "
    "verdict=CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=16 "
    "stale=yes, naming the tech head state/queue/tech.md:522 prefix AC-PFKC1 "
    "row_key_carrier_scope, whose AC-PFKC1..AC-PFKC6 were pinned in that row at "
    "R2446 BEFORE any code.",

    "2026-11-05 R2470 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt, no P-47 "
    "business surface was touched, and every P-47 item beyond the shipped "
    "sandbox faces remains blocked on CEO physical items; what the window bought "
    "is a proven registry (562 suites, 4348 criteria) on the exact tree R2469 "
    "committed, so the token-ledger console shipped there is now PROVED rather "
    "than merely shipped; (b) the debt gate leader is still the internal audit "
    "row product-face-R2456, now sixteen windows carried and stale, while the "
    "CEO standing order OB-20261105-003656-879 asks for real output, so the next "
    "window should ship a BUSINESS face and say plainly that it supersedes the "
    "audit row rather than serving the gate blindly - the one named candidate "
    "is wiring the R2469 ledger console into the lobby hub payload, which R2469 "
    "disclosed as not yet done; (c) the first poll of the detached battery was "
    "auto-cancelled by the shell five-minute no-output gate while the battery "
    "kept running as a SEPARATE process; it was verified ALIVE by process id "
    "(99856) afterwards and the evidence file was written at close, so no "
    "second launch happened and no evidence byte was lost; (d) Docker is absent "
    "on this host, so the compose bring-up of the sandbox faces stays unproved "
    "and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items (merchant id, mini-program appid/secret); "
    "(f) READ-ONLY observation outside this repo: FluxGroup/docs/orders.md "
    "still carries its leftover empty conflict markers, already reported in "
    "HQ-FEEDBACK.md; (g) the window ran past its 25-minute budget on a 1042.8s "
    "battery plus two follow-up legs, named rather than hidden; (h) the fold was "
    "DUE at closeout (state.json 77589B against the 78500B waterline, 911B of "
    "margin) and it is discharged in this closeout at a true round-block "
    "boundary; (i) tasks.md was not touched, it is the P-47 canonical board.",

    "R2470 tokens: local=~8k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (562/562 suites, controls 7/7, "
    "4348 criteria exactly as pre-registered, 1042.3s), one detached launch "
    "through the single-writer stream, one designed matrix FAIL followed by a "
    "stamp-aligned regeneration from this round own green evidence and a "
    "byte-identical --check, four follow-up sections PASS for VERDICT R2470 "
    "PASS, one battery row closed through its shipped CLI, one waterline fold, "
    "and the state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",

    "2026-11-05 R2470 self-heal check: BigDomain-OSLoop exists and is Running, "
    "but its Principal.LogonType still reads Interactive, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "needs an elevated shell while this session is unelevated, so the definition "
    "was left untouched again (two-hundred-and-twenty-sixth consecutive "
    "disclosure, carried as the stale row loop-s4u-reconcile).",
]

ROW = (
    "- [x] [done 2026-11-05 R2470] R2470 VERIFICATION window on the battery the "
    "R2469 business face owed (reconcile-battery-R2469, pre-registered at 562 "
    "suites / 4348 criteria), per the R2168 mixed-tree rule: zero product code "
    "changed. Five-silence scan at open was clean at HEAD 73111332 equal to "
    "origin/main with no index.lock, zero unreplied @BigDomain ledger rows, the "
    "content-addressed decisions diff new=0, the group orders tail unchanged at "
    "2026-11-05 00:36, benchmarks refreshed 2026-11-03 inside the seven-day "
    "gate, queue head AC-PFKC1 with the floor MET. BATTERY on the committed tree "
    "with an empty git status: RUNNER PASS 562/562 suites green plus controls "
    "7/7 in 1042.3s at criteria total 4348 EXACTLY as pre-registered "
    "(qa/reconcile-all-R2470.log, 860725B at the green leg, one utf-8 LF single "
    "writer through src/os/battery_stream.py, crlf=0 bom=False), TMP RECLAIM "
    "932/932 worlds 326.59 MiB busy=0 failed=0. Four follow-up sections in the "
    "designed order: dry-run read VERDICT FAIL failing=matrix at on-disk=54192B "
    "against regenerated=54185B with no byte written, suite_matrix regenerated "
    "docs/sandbox-suite-matrix.md from this round own green evidence through "
    "--evidence plus --stamp-from, --check read byte-identical at 54185B / 562 "
    "suites / 4348 criteria, and the write leg read VERDICT R2470 PASS "
    "failing=none (fingerprint CLEAN 5 domains, profile byte-identical, census "
    "DRIFT-CLEAN, APPENDED 1950B eol_ok=True). Debt: reconcile-battery-R2469 "
    "closed through the shipped debt_close at its predicted 121819B -> 121823B "
    "(line=199, open 3->2, done 177->178, readback ok); NO successor battery "
    "owed because no product src byte changed and the registry is unmoved at "
    "562/4348. Zero product points claimed; the debt gate leader is still the "
    "internal audit row product-face-R2456 (carried=16, stale) so the NEXT "
    "window should ship a BUSINESS face and name the supersession - the named "
    "candidate is wiring the R2469 ledger console into the lobby hub payload, "
    "which R2469 disclosed as not yet done. Also disclosed: one poll command was "
    "auto-cancelled by the shell no-output gate while the battery kept running "
    "as a separate process (verified alive by pid, no second launch), Docker is "
    "absent, the real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items, and the waterline fold ran at a true round-block boundary."
)

BEAT_LINE = (
    "R2470 verification window | 2026-11-05 | battery green 562/562 at the "
    "pre-registered 4348 criteria on the first leg, four follow-up sections to "
    "VERDICT R2470 PASS, matrix restamped 54185B byte-identical | "
    "reconcile-battery-R2469 CLOSED, no successor owed | zero product points | "
    "fold due at 77589B discharged at a true round-block boundary"
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
    if "R2470 VERIFICATION window" not in text:
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