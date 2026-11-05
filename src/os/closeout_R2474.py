"""R2474 closeout: state tick, log lines, decisions baseline, backlog row, heartbeat."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
BACKLOG = os.path.join(SRC, "backlog.md")
BEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2474
DEC_ROWS = 292
NEW_DEC = "D-20261105-17"

LINES = [
    "2026-11-05 R2474 VERIFICATION window on the battery the R2473 business face "
    "owed (reconcile-battery-R2473, pre-registered at 564 suites / 4360 criteria), "
    "because the R2168 mixed-tree rule puts the battery ahead of the carried audit "
    "row product-face-R2456 (still open, still claimable, CARRIED not dropped). "
    "Five-silence scan at open: git status empty at HEAD 5cbdfe22 with no "
    ".git/index.lock, zero @BigDomain rows in the evolution ledger, the "
    "content-addressed decisions diff named exactly ONE new token D-20261105-17 "
    "(the 15:07 duty round: a P1 backfill dispatch to @BigCompute, the bm-b 5.8d / "
    "bm-c 5.1d blackout escalated to E1, and the PROBE A five-item ack demand on "
    "@CPH4), judged KNOWLEDGE-ONLY because none of it is a BigDomain execution "
    "face, with the baseline widened by that one token; the group orders tail "
    "unchanged at 2026-11-05 00:36 equal to the stored last_order; benchmarks "
    "refreshed 2026-11-03 inside the seven-day gate; queue head "
    "state/queue/tech.md:522 prefix AC-PFKC1 with claimable=11 and the floor MET. "
    "The debt gate read open=3 first=1 and named product-face-R2456, but the "
    "register also carried the open reconcile-battery-R2473 row, so the battery "
    "ran FIRST and no product byte was touched.",

    "2026-11-05 R2474 BATTERY GREEN on the committed tree 5cbdfe22 with an empty "
    "git status before the run: RUNNER PASS 564/564 suites green plus reconcile "
    "controls 7/7 in 1047.8s (1047.9s wall) and the closing summary line reads "
    "'PASS suites 564/564 green, expected criteria total=4360', i.e. EXACTLY the "
    "total pre-registered in the debt register at R2473; birth-site TMP RECLAIM "
    "candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence "
    "qa/reconcile-all-R2474.log written by ONE utf-8 LF single writer through "
    "src/os/battery_stream.py (862025B at the green leg, 863975B with both "
    "follow-up legs), re-measured byte-wise: crlf=0 lone_cr=0 bom=False. The "
    "battery was launched detached and unfiltered into "
    "logs/battery-R2474-stdout.log, so the "
    "R2211/R2268/R2289/R2348/R2453/R2458/R2461 filtering-pipe trap was not "
    "re-paid, and no red leg exists because none was produced.",

    "2026-11-05 R2474 the four follow-up sections produced the designed order: "
    "LEG 1 (--dry-run) read SECTION matrix FAIL matrix mismatch on-disk=54354B "
    "regenerated=54326B with no byte written, fingerprint PASS CLEAN domains=5, "
    "profile PASS byte-identical, census PASS DRIFT-CLEAN for VERDICT R2474 FAIL "
    "failing=matrix at exit 2; then src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md from THIS round own green evidence through "
    "--evidence plus --stamp-from and printed 'PASS generated ... 54326 bytes ... "
    "registry suites=564 criteria=4360 evidence=qa/reconcile-all-R2474.log "
    "green=564/564', with --check reading byte-identical at 54326B / 564 suites / "
    "4360 criteria. LEG 2 then read all four sections PASS - matrix byte-identical "
    "54326B, fingerprint CLEAN domains=5, profile byte-identical, census "
    "DRIFT-CLEAN - for VERDICT R2474 PASS failing=none (APPENDED 1950B "
    "eol_ok=True). The matrix is self-describing this round: its own green line "
    "reads 564/564 because it names this round own battery rather than a borrowed "
    "older leg.",

    "2026-11-05 R2474 debt register closed through its own writer: "
    "reconcile-battery-R2473 closed through debt_close at its predicted 122765B -> "
    "122769B (line=201, open 3->2, done 179->180, readback=ok) after a dry run "
    "that named exactly those deltas. NO successor battery was registered because "
    "this window changed no product src byte and the registry is unmoved at 564 "
    "suites / 4360 criteria - the only src file added is a one-off closeout "
    "script, not a module. The gate therefore still reads CLAIM-FIRST "
    "item=product-face-R2456 opened=R2455 carried=19 stale=yes, naming the tech "
    "head state/queue/tech.md:522 prefix AC-PFKC1 row_key_carrier_scope, whose "
    "AC-PFKC1..AC-PFKC6 were pinned in that row at R2446 BEFORE any code. The NEXT "
    "window should ship a BUSINESS face and name the supersession, per the CEO "
    "standing order OB-20261105-003656-879.",

    "2026-11-05 R2474 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt, no P-47 business "
    "surface was touched, and every P-47 item beyond the shipped sandbox faces "
    "remains blocked on CEO physical items; what the window bought is a proven "
    "registry (564 suites, 4360 criteria) plus a self-describing matrix on the "
    "exact tree R2473 committed, so the UGC console shipped there is now PROVED "
    "rather than merely shipped; (b) the battery passed on its FIRST leg, so no "
    "repair was needed and none is claimed - that is the honest opposite of the "
    "R2465/R2466/R2472 red-then-green windows and it is stated rather than "
    "dressed up as diligence; (c) the debt gate leader is still the internal audit "
    "row product-face-R2456, now nineteen windows carried and stale, while the CEO "
    "standing order asks for real output, so the next window should ship a "
    "BUSINESS face and say plainly that it supersedes the audit row rather than "
    "serving the gate blindly - the one named candidate is wiring the R2469 ledger "
    "console AND the R2473 UGC console into the lobby hub live map, which both "
    "business windows disclosed as not yet done; (d) Docker is absent on this "
    "host, so a containerised bring-up of the sandbox faces stays unproved and is "
    "not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was "
    "not touched, it is the P-47 canonical board; (g) no fold was due: "
    "src/os/state.json measured 72307B at open against the 78500B waterline; "
    "(h) READ-ONLY observation outside this repo: FluxGroup/docs/orders.md still "
    "carries its leftover empty conflict markers, already reported in "
    "HQ-FEEDBACK.md.",

    "R2474 tokens: local=~8k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (564/564 suites, controls 7/7, 4360 "
    "criteria exactly as pre-registered, 1047.8s), one detached launch through the "
    "single-writer stream, one designed matrix FAIL followed by a stamp-aligned "
    "regeneration from this round own green evidence and a byte-identical --check, "
    "four follow-up sections PASS for VERDICT R2474 PASS, one group decision "
    "judged KNOWLEDGE-ONLY with the baseline widened, one battery row closed "
    "through its shipped CLI, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches",
]

ROW = (
    "- [x] [done 2026-11-05 R2474] R2474 VERIFICATION window on the battery the "
    "R2473 business face owed (reconcile-battery-R2473, pre-registered 564 suites "
    "/ 4360 criteria), per the R2168 mixed-tree rule: zero product code changed. "
    "Five-silence scan at open was clean at HEAD 5cbdfe22 equal to origin/main "
    "with no index.lock, zero unreplied @BigDomain ledger rows, the "
    "content-addressed decisions diff naming exactly ONE new token D-20261105-17 "
    "(a group duty-round @BigCompute backfill dispatch plus the bm-b/bm-c E1 "
    "escalation and the PROBE A acks on @CPH4) judged KNOWLEDGE-ONLY with the "
    "baseline widened by it, the group orders tail unchanged at 2026-11-05 00:36, "
    "benchmarks refreshed 2026-11-03 inside the seven-day gate, queue head "
    "AC-PFKC1 with claimable=11 and the floor MET. BATTERY on the committed tree "
    "with an empty git status before the run, GREEN ON THE FIRST LEG: RUNNER PASS "
    "564/564 suites green plus controls 7/7 in 1047.8s at criteria total 4360 "
    "EXACTLY as pre-registered (qa/reconcile-all-R2474.log, 862025B at the green "
    "leg and 863975B with both follow-up legs, one utf-8 LF single writer through "
    "src/os/battery_stream.py, crlf=0 lone_cr=0 bom=False), TMP RECLAIM 932/932 "
    "worlds 326.59 MiB busy=0 failed=0. Four follow-up sections in the designed "
    "order: dry-run read VERDICT FAIL failing=matrix at on-disk=54354B against "
    "regenerated=54326B with no byte written, suite_matrix regenerated "
    "docs/sandbox-suite-matrix.md from this round own green evidence through "
    "--evidence plus --stamp-from, --check read byte-identical at 54326B / 564 "
    "suites / 4360 criteria, and the write leg read VERDICT R2474 PASS "
    "failing=none (fingerprint CLEAN 5 domains, profile byte-identical, census "
    "DRIFT-CLEAN, APPENDED 1950B eol_ok=True). Debt: reconcile-battery-R2473 "
    "closed through the shipped debt_close at its predicted 122765B -> 122769B "
    "(line=201, open 3->2, done 179->180, readback ok); NO successor battery owed "
    "because no product src byte changed and the registry is unmoved at 564/4360. "
    "Zero product points claimed; the debt gate leader is still the internal audit "
    "row product-face-R2456 (carried=19, stale) so the NEXT window should ship a "
    "BUSINESS face and name the supersession - the named candidate is wiring the "
    "ledger and UGC consoles into the lobby hub live map, which both business "
    "windows disclosed as not yet done."
)

BEAT_LINE = (
    "tick=2474 R2474 verification: battery GREEN on the FIRST leg at 564/564 "
    "suites / 4360 criteria exactly as pre-registered (1047.8s, controls 7/7, TMP "
    "RECLAIM 932/932, evidence 863975B crlf=0) | matrix restamped self-describing "
    "54326B at 564/564 with --check byte-identical | reconcile-battery-R2473 "
    "closed 122765B -> 122769B (open 3->2) | D-20261105-17 judged KNOWLEDGE-ONLY "
    "| zero product points, next window owes a BUSINESS face"
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
        if NEW_DEC not in state["last_dec_tokens"]:
            state["last_dec_tokens"].append(NEW_DEC)
        state["last_dec_tokens"] = sorted(set(state["last_dec_tokens"]))
        state["last_decision_rows"] = DEC_ROWS
        size = write_state(state)
        print("state tick %d, log +%d, bytes=%d, dec_tokens=%d"
              % (TICK, len(LINES), size, len(state["last_dec_tokens"])))

    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    marker = "- [x] [done 2026-11-05 R2474] R2474 VERIFICATION window"
    if marker in text:
        print("backlog row already present")
    else:
        text = ROW + "\n" + text
        tmp = BACKLOG + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, BACKLOG)
        print("backlog row prepended")

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