"""R2468 closeout state append (one-off): verification window receipt."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

NEW_TOKENS = [
    "D-20261105-12",
    "D-20261105-13",
    "D-20261105-14",
    "D-20261105-15",
    "D-20261105-16",
]

LINES = [
    "2026-11-05 R2468 VERIFICATION window on the battery the R2467 business face owed (reconcile-battery-R2467, pre-registered at 561 suites / 4342 criteria). Five-silence scan at open: git status empty at HEAD 660d794d with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the group orders tail unchanged at 2026-11-05 00:36 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day gate, queue head AC-PFKC1 with the floor MET. The content-addressed decisions diff named five NEW tokens - D-20261105-12 through D-20261105-16 - and each was read before judging: D-12 is the 46-round cross-company mtime patrol, D-13 is the group task-health table landing, D-14 is the group merge-driver and orders-file ruling, D-15 is the bm-m lane handover to bm-a, D-16 is the biggame-playable NO-REPO verdict on the gaming repository. All five are group/fleet or other-company execution faces, so this station took the KNOWLEDGE-ONLY path on every one of them (log line only, no action) and widened its token baseline by exactly those five.",

    "2026-11-05 R2468 BATTERY GREEN on the committed tree 660d794d with an empty git status before the run: RUNNER PASS 561/561 suites green plus reconcile controls 7/7 in 1205.5s (1207.5s wall) and the summary line reads 'PASS suites 561/561 green, expected criteria total=4342', i.e. EXACTLY the total pre-registered in the debt register at R2467; birth-site TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence qa/reconcile-all-R2468.log written by ONE utf-8 LF single writer through src/os/battery_stream.py (859447B at the green leg, 861397B with both follow-up legs), re-measured byte-wise: crlf=0 lone_cr=0 bom=False. The battery was launched detached and unfiltered into logs/battery-R2468-stdout.log, so the R2211/R2268/R2289/R2348/R2453/R2458/R2461 filtering-pipe trap was not re-paid, and no red leg exists because none was produced.",

    "2026-11-05 R2468 the four follow-up sections produced the designed order: LEG 1 (--dry-run) read SECTION matrix FAIL matrix mismatch on-disk=54146B regenerated=54116B with no byte written, fingerprint PASS CLEAN domains=5, profile PASS byte-identical, census PASS DRIFT-CLEAN; then src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round own green evidence through --evidence plus --stamp-from and printed 'PASS generated ... 54116 bytes ... registry suites=561 criteria=4342 evidence=qa/reconcile-all-R2468.log green=561/561', with --check reading byte-identical at 54116B / 561 suites / 4342 criteria. LEG 2 then read all four sections PASS - matrix byte-identical 54116B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN - for VERDICT R2468 PASS failing=none (APPENDED 1950B eol_ok=True). The matrix is self-describing this round: its own green line reads 561/561 because it names this round own battery rather than a borrowed older leg.",

    "2026-11-05 R2468 debt register closed through its own writer: reconcile-battery-R2467 closed through debt_close at its predicted 121381B -> 121385B (line=198, open 3->2, done 176->177, readback=ok) after a dry run that named exactly those deltas. NO successor battery was registered because this window changed no product src byte and the registry is unmoved at 561 suites / 4342 criteria. The gate now reads verdict=CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=13 stale=yes open=2 first=1, naming the tech head state/queue/tech.md:522 prefix AC-PFKC1 row_key_carrier_scope, whose AC-PFKC1..AC-PFKC6 were pinned in that row at R2446 BEFORE any code.",

    "2026-11-05 R2468 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was rebuilt, no P-47 business surface was touched, and every P-47 item beyond the shipped sandbox faces remains blocked on CEO physical items; what the window bought is a proven registry (561 suites, 4342 criteria) on the exact tree R2467 committed, so the content-gate console shipped there is now PROVED rather than merely shipped; (b) the unsupported-flag trap was paid AGAIN and is recorded rather than swept: probing src/sandbox/reconcile_all.py with --help started a real suite run, a 5-byte file literally named '--help' was left in the repo root, and it was deleted before any commit with the tree read clean afterwards - the next reader should use battery_followup.py --help, whose help wire is the one face that answers a question without starting work; (c) the debt gate leader is still the internal audit row product-face-R2456, now thirteen windows carried and stale, while the CEO standing order OB-20261105-003656-879 asks for real output, so the next window should ship a BUSINESS face and say plainly that it supersedes the audit row rather than serving the gate blindly; (d) Docker is absent on this host, so the compose bring-up of the sandbox faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) READ-ONLY observation outside this repo: FluxGroup/docs/orders.md still carries its leftover empty conflict markers, already reported in HQ-FEEDBACK.md; (g) the window ran past its 25-minute budget on a 1207.5s battery plus two follow-up legs, named rather than hidden; (h) tasks.md was not touched, it is the P-47 canonical board; (i) no fold was due: src/os/state.json measured 68327B at open against the 78500B waterline.",

    "R2468 tokens: local=~8k api=0 api_reason=verification window - one full reconcile battery on the committed tree (561/561 suites, controls 7/7, 4342 criteria exactly as pre-registered, 1205.5s), one detached launch through the single-writer stream, one designed matrix FAIL followed by a stamp-aligned regeneration from this round own green evidence and a byte-identical --check, four follow-up sections PASS for VERDICT R2468 PASS, five group decisions judged KNOWLEDGE-ONLY with the baseline widened, one battery row closed through its shipped CLI, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return
    state["tick"] = 2468
    state["log"].extend(LINES)
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_TOKENS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = sorted(tokens)
    state["last_decision_rows"] = 289
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if len(back["log"]) != len(state["log"]) or back["tick"] != 2468:
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d tokens=%d bytes=%d"
          % (len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH)))


if __name__ == "__main__":
    main()