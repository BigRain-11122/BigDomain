"""R2476 closeout: append this verification window's log items and move the
scan baselines (tick, orders tail, decision tokens). The write is one atomic
replace in the state canon, proved by a read-back.
"""
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
    "D-20261105-18", "D-20261105-19", "D-20261105-20",
    "D-20261105-21", "D-20261105-22", "D-20261105-23",
]

LINES = [
    "2026-11-05 R2476 VERIFICATION window on the battery R2475 owed (reconcile-battery-R2475, pre-registered at 565 suites / 4366 criteria), because the R2168 mixed-tree rule puts the battery ahead of any further product byte. Five-silence scan at open: git status empty at HEAD a64317af with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the content-addressed decisions diff naming SIX new tokens D-20261105-18..23 (fleet lane receipts and the bm-b/bm-c 24h evidence, the docs/orders.md leftover conflict markers, the CEO physical-item S4U reminder for seven Bigmoney tasks on bm-a, the subsidiary mtime patrol, the bm-a branch split at 413/194 and the 21:07 night audit window) ALL judged KNOWLEDGE-ONLY because none of them is a BigDomain execution face, with the baseline widened by exactly those six; the group orders tail read a NEW CEO order at 2026-11-05 20:22 (cloud quota temporarily unlimited for FINAL DELIVERABLES and MUST-USE only, local-first unchanged, the >500 point confirm gate unchanged and still CEO-signed) which dispatches no BigDomain task this window and is recorded as a knowledge row, so last_order moved to 2026-11-05 20:22; benchmarks refreshed 2026-11-03 inside the seven-day gate; tech head AC-PFKC1 with claimable=11. The debt gate read CLAIM-FIRST item=product-face-R2456 carried=21 stale=yes open=3 first=1, but the register also carried the open reconcile-battery-R2475 row, so the battery ran FIRST and no product byte was touched.",
    "2026-11-05 R2476 BATTERY GREEN ON THE FIRST LEG on the committed tree a64317af with an empty git status before the run: RUNNER PASS 565/565 suites green plus reconcile controls 7/7 in 1444.8s and the closing summary line reads 'PASS suites 565/565 green, expected criteria total=4366', i.e. EXACTLY the total pre-registered in the debt register at R2475, so the prediction matched the measurement and nothing had to be named or swept. Birth-site TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence qa/reconcile-all-R2476.log written by ONE utf-8 LF single writer through src/os/battery_stream.py, launched detached and unfiltered into logs/battery-R2476-stdout.log so the R2211/R2268/R2289/R2348/R2453/R2458/R2461 filtering-pipe trap was not re-paid; re-measured byte-wise: 862587B, crlf=0, lone_cr=0, bom=False. No red leg exists because none was produced, stated rather than implied.",
    "2026-11-05 R2476 the four follow-up sections produced the designed order: the dry run read SECTION matrix FAIL matrix mismatch on-disk=54396B regenerated=54399B with no byte written while fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN for VERDICT R2476 FAIL failing=matrix at exit 2; then src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round's own green evidence through --evidence plus --stamp-from and printed 'PASS generated ... 54399 bytes ... registry suites=565 criteria=4366 evidence=qa/reconcile-all-R2476.log green=565/565', with --check reading byte-identical at 54399B / 565 suites / 4366 criteria; the write leg then read all four sections PASS - matrix byte-identical 54399B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN - for VERDICT R2476 PASS failing=none, APPENDED 1950B eol_ok=True. The matrix is self-describing this round at green=565/565 because it names this round's own battery rather than a borrowed older leg.",
    "2026-11-05 R2476 debt register closed through its own writer: reconcile-battery-R2475 closed through debt_close at its predicted 123176B -> 123180B (line=202, open 3->2, done 180->181, readback=ok) after a dry run that named exactly that single delta. NO successor battery was registered because this window changed no product src byte and the registry is unmoved at 565 suites / 4366 criteria - the only src file added is a one-off closeout script, not a module. The gate therefore still reads CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=21 stale=yes, naming the tech head state/queue/tech.md:522 prefix AC-PFKC1 row_key_carrier_scope, whose AC-PFKC1..AC-PFKC6 were pinned in that row at R2446 BEFORE any code. The NEXT window should ship a BUSINESS face and name the supersession, per the CEO standing order OB-20261105-003656-879.",
    "2026-11-05 R2476 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was rebuilt, no P-47 business surface was touched, and every P-47 item beyond the shipped sandbox faces remains blocked on CEO physical items; what the window bought is a proved registry (565 suites, 4366 criteria) on the exact tree R2475 committed, so the fifth hub face shipped there is now PROVED rather than merely shipped; (b) the battery passed on its FIRST leg, so no repair was needed and none is claimed; (c) the debt gate leader is still the internal audit row product-face-R2456, now twenty-one windows carried and stale, so the next window should ship a BUSINESS face and say plainly that it supersedes the audit row rather than serving the gate blindly - the named candidate remains making the hub able to START a face, which the R2475 window disclosed as not yet done; (d) this window re-paid the R2349/R2318 trap and says so: a probe of reconcile_all.py with --help STARTED a real battery, the Shell tool cancelled it for silence, no process survived, and the stray 13859B repo-root file literally named --help was deleted before any commit, leaving the tree clean; the runner contract was then read from source instead; (e) Docker is absent on this host, so a containerised bring-up of the sandbox faces stays unproved and is not claimed; (f) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (g) tasks.md was not touched, it is the P-47 canonical board; (h) no fold was due: src/os/state.json measured 17351B at open against the 78500B waterline; (i) READ-ONLY observation outside this repo: FluxGroup/docs/orders.md still carries its leftover empty conflict markers, already reported in HQ-FEEDBACK.md, and D-20261105-19 now records the same finding at group level.",
    "R2476 tokens: local=~9k api=0 api_reason=verification window - one full reconcile battery on the committed tree (565/565 suites, controls 7/7, 4366 criteria exactly as pre-registered, 1444.8s), one detached launch through the single-writer stream, one designed matrix FAIL followed by a stamp-aligned regeneration from this round's own green evidence and a byte-identical --check, four follow-up sections PASS for VERDICT R2476 PASS, six group decision rows and one new CEO order judged KNOWLEDGE-ONLY with the baselines widened, one battery row closed through its shipped CLI, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-05 R2476 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2476
    state["last_order"] = "2026-11-05 20:22"
    state["last_decision_rows"] = 221
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_TOKENS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2476
          and back["last_order"] == "2026-11-05 20:22"
          and len(back["last_dec_tokens"]) == len(tokens))
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())