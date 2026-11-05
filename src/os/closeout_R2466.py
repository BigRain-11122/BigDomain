"""R2466 closeout: state tick, log lines, waterline fold (one-off)."""
import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
GATE = 78500
RESERVE = 6000
BLOCK_END = re.compile(r"^R\d+ tokens:")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-05 R2466 VERIFICATION window on the battery the R2464 src edits owed and R2465 could not discharge (reconcile-battery-R2465, pre-registered at 560 suites / 4336 criteria). Five-silence scan at open: git status empty at HEAD 06f4473d with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the group orders tail unchanged at 2026-11-05 00:36, benchmarks refreshed 2026-11-03 inside the seven-day gate, queue head AC-PFKC1 with the floor MET. The debt gate read open=3 first=1 and named product-face-R2456, but the mixed-tree rule put the battery first, so product-face-R2456 is CARRIED, never dropped.",

    "2026-11-05 R2466 BATTERY LEG 1 RED on the committed tree in 929.9s: RUNNER FAIL (3 failed assertions) with two suites red, os-status-export-writer-dialect-wire 5/6 and os-queue-floor-export-face 5/6, and the cause was measured rather than guessed - check_export_consistency read self_drive.log_lines_in_window stored=90 recomputed=91. R2465 appended its self-heal line AFTER its last export refresh, which is the R2433/R2441 closeout-ordering shape exactly, and the AC-SEWD4 red is downstream of it (its third writer suite re-run inherits the stale export).",

    "2026-11-05 R2466 FIX AT THE BIRTH SITE: the export was re-derived through the shipped drivers only - export_R2465.py then queue_export_gate_wire.py --execute (verdict=WRITTEN gate=CURRENT bytes=130209) - after which check_export_consistency reads pass=21 fail=0 VERDICT PASS and both red suites read SUITE PASS 6/6. No criterion was loosened and no baseline was widened. The repair is data only and was committed ALONE as dc3a6f05 so the retry started on a clean tree.",

    "2026-11-05 R2466 BATTERY LEG 2 ABORTED, and the abort is a real runner defect rather than a product one: the run died with subprocess.TimeoutExpired on ledger/test_apimarket_report_refundregister.py after exactly the 300s per-suite cap (BATTERY rc=1 771.4s, no verdict). That suite own slowest measured leg is 268.1s per the R2395 headroom reading, so this is load, not code - and the R2393 shape repeated: one slow suite kills a whole battery.",

    "2026-11-05 R2466 the runner was repaired at its birth site: run_cmd now catches subprocess.TimeoutExpired and records ONE failed suite carrying every line the child produced plus a TIMEOUT marker at exit 124, so a loaded machine produces a readable red leg instead of a dead run; no cap, threshold or assertion was changed and the timeout headroom suite plus the argument guard suite still read 6/6. Committed ALONE as f7728805.",

    "2026-11-05 R2466 BATTERY LEG 3 GREEN on the committed repair tree in 1143.3s: RUNNER PASS 560/560 suites green, reconcile controls 7/7, and the summary line reads expected criteria total=4336, i.e. EXACTLY the number pre-registered at R2462, plus birth-site TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence qa/reconcile-all-R2466-retry2.log written by ONE utf-8 LF single writer through src/os/battery_stream.py (860658B with both follow-up legs, crlf=0 bom=False), launched detached and unfiltered so the filtering-pipe trap was not re-paid; the two red legs are kept as qa/reconcile-all-R2466.log and qa/reconcile-all-R2466-retry.log and neither is counted as green.",

    "2026-11-05 R2466 the four follow-up sections produced the designed order: LEG 1 matrix FAIL at on-disk=54033B against regenerated=54061B with no byte written, then src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round own green evidence through --stamp-from and printed 'PASS generated ... 54061 bytes ... registry suites=560 criteria=4336 evidence=qa/reconcile-all-R2466-retry2.log green=560/560', --check read byte-identical; LEG 2 then read all four sections PASS - matrix byte-identical 54061B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN - for VERDICT R2466 PASS failing=none. Both legs stay in the evidence tail (1950B PASS appended, eol_ok=True).",

    "2026-11-05 R2466 debt register closed through its own writer: reconcile-battery-R2465 closed through debt_close at its predicted 121067B -> 121071B (line=197, open 3->2, done 175->176, readback=ok) after a dry run that named exactly those deltas. NO successor battery was registered because the registry is unmoved at 560 suites / 4336 criteria and the only src edit is the runner survival fix, which this very green leg has now exercised; the gate reads open=2 with product-face-R2456 first=yes, still the internal audit row at tech line 522 prefix AC-PFKC1 and still claimable.",

    "2026-11-05 R2466 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO can open was rebuilt, no P-47 business surface was touched, and every P-47 item beyond the shipped sandbox faces remains blocked on CEO physical pieces; what the window bought is a proven registry (560 suites, 4336 criteria) plus two real birth-site repairs; (b) the window ran THREE batteries, about 48 minutes of wall clock against a 25-minute budget, named rather than hidden; (c) the first red was a closeout-ordering defect two windows old that nothing but the whole battery caught, and the second was the 300s cap that R2393 also paid - the survival fix does not remove the load itself, so a future leg may still read one TIMEOUT line and that will be named, not hidden; (d) Docker is absent on this host, the real 19.9 debit and the real msgSecAuth wait on CEO physical items (merchant id, mini-program appid/secret); (e) tasks.md was not touched, it is the P-47 canonical board; (f) the fold was DUE at open (state.json 81282B over the 78500B waterline, deferred one window by R2465) and is discharged in this closeout at a true round-block boundary.",

    "R2466 tokens: local=~12k api=0 api_reason=verification window - three full reconcile batteries launched detached through the single-writer stream (one red on a stale export, one aborted on the 300s cap, one green at the pre-registered 560 suites / 4336 criteria), two birth-site repairs each committed alone (the export re-derived through its shipped drivers, the runner taught to survive a suite timeout), four follow-up sections with one intended matrix FAIL and one green verdict after a stamp-aligned regeneration, one battery debt row closed through its shipped CLI, one waterline fold, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


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
    before = state["tick"]
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("log already carries this window (rerun after a fold refusal)")
        size = os.path.getsize(PATH)
    else:
        state["tick"] = before + 1
        state["log"].extend(LINES)
        size = write_state(state)
    print("tick %d lines=%d bytes=%d" % (state["tick"], len(state["log"]), size))
    if size <= GATE - RESERVE:
        print("fold not due gate=%d reserve=%d" % (GATE, RESERVE))
        return
    import state_fold
    ends = [i + 1 for i, item in enumerate(state["log"])
            if BLOCK_END.match(str(item).strip())]
    chosen = None
    for end in ends:
        if end < 2:
            continue
        window = state["log"][1:end]
        if state_fold.round_split(window, state["log"][end:]):
            continue
        with io.open(PATH, "rb") as handle:
            raw = handle.read()
        tokens = set()
        for line in window:
            tokens |= set(state_fold.PAT.findall(str(line)))
        summary = ("Fold R2466: log items 2..%d moved verbatim to the monthly "
                   "archive at a true round-block boundary; tokens covered "
                   "%s, none missing." % (end, ",".join(sorted(tokens))))
        plan, _ = state_fold.plan_fold(raw, state, 2, end, summary,
                                       reserve=RESERVE, gate=GATE)
        if plan.get("gate_ok") and not plan.get("tokens_missing"):
            chosen = (end, summary)
            break
    if not chosen:
        print("NO CLEAN FOLD WINDOW - state kept at %dB" % size)
        return
    end, summary = chosen
    result = state_fold.fold(ROOT, "R2466", 652, 2, end, summary,
                             reserve=RESERVE, gate=GATE, execute=True)
    print("fold end=%d post=%s missing=%s"
          % (end, result.get("post_disk_bytes"),
             result.get("token_missing")))


if __name__ == "__main__":
    main()