"""R2485 closeout: append this window's log items and move the tick. One
atomic replace in the state canon, proved by a read-back. No decision token
moved this window, so the baseline list is carried unchanged and said so.
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

NEW_TOKENS = []

LINES = [
    "2026-11-06 R2485 VERIFICATION window on the battery the register owed (reconcile-battery-R2484, pre-registered at 570 suites / 4396 criteria), because the R2168 mixed-tree rule puts that battery ahead of any further product byte and R2484's own closeout named it as the next window's obligation. Five-silence scan at open: git status empty with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff reading new=0 against the stored baseline (newest token D-20261105-23, file 304 lines), the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 inside the seven-day gate.",
    "2026-11-06 R2485 the debt register was read before anything else and settled the claim question in one line: state/debt.md line 208 carries an OPEN row item=reconcile-battery-R2484 whose note names the 570/4396 target, and debt_gate --check --round R2485 printed CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=30 stale=yes open=3 first=1 with a note naming the tech queue row state/queue/tech.md:522 prefix AC-PFKC1. BOTH rows are open; the mixed-tree rule ranks the battery first, so this window claimed the battery and left product-face-R2456 untouched and claimable for the next window.",
    "2026-11-06 R2485 FIRST BATTERY ATTEMPT WAS KILLED BY THE TOOL WATCHDOG AND IS DISCLOSED, NOT DRESSED UP: reconcile_all.py tees its evidence through a block-buffered stdout, so the shell tool saw five minutes of silence and auto-cancelled the command, leaving a 172868B partial qa/reconcile-all-R2485.log and a dead python process. The partial file was DELETED rather than kept or quoted, and the battery was re-run as an independent hidden process with its pid recorded in logs/battery-R2485.pid, polled through completion. This is a workflow fact about the runner (buffered output versus a five-minute silence watchdog), not a defect in the product tree, and it is the honest reason this window's wall clock reads longer than its file diff suggests.",
    "2026-11-06 R2485 BATTERY GREEN ON THE COMMITTED TREE, MEASURED: qa/reconcile-all-R2485.log closes with 'RUNNER PASS (570/570 suites green, reconcile controls 7/7, 1280.9s)' and carries zero '^FAIL suite' rows. An independent recount over the 570 per-suite PASS lines sums criteria to exactly 4396 - byte for byte the total pre-registered at R2484 - and the bytes were verified after the fact as utf-8 LF with bom=False, crlf=0 and lone_cr=0. The tmp reclaim line reads candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB.",
    "2026-11-06 R2485 the four follow-up sections ran in the designed order and reproduced the same FAIL-then-regenerate shape the earlier batteries taught: the dry run read SECTION matrix FAIL on-disk=54765B regenerated=54732B with fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN, for VERDICT R2485 FAIL failing=matrix. The 33-byte shrink is honest bookkeeping rather than drift: R2484 restamped the matrix from the previous battery and had to print 569/570 green, while this round's own battery really is 570/570. suite_matrix.py then regenerated docs/sandbox-suite-matrix.md from THIS round's own evidence through --evidence plus --stamp-from ('PASS generated ... 54732 bytes ... registry suites=570 criteria=4396 evidence=qa/reconcile-all-R2485.log green=570/570'), --check read byte-identical at 54732B / 570 / 4396, and the write leg read all four sections PASS for VERDICT R2485 PASS failing=none (APPENDED 1950B eol_ok=True). The matrix is now self-describing again instead of borrowing a prior leg.",
    "2026-11-06 R2485 debt register closed through its own writer: reconcile-battery-R2484 closed at line 208 (open 3->2, done 186->187, 125931B -> 125935B, readback ok). No successor battery was registered, on the same reasoning the earlier verification windows used: this window's post-battery writes are the matrix doc, the debt register, the state/backlog/export closeout and one one-off closeout script, none of which is a registry module or suite, and the registry is unmoved at 570 suites / 4396 criteria. The gate therefore still names CLAIM-FIRST item=product-face-R2456 (prefix AC-PFKC1, open=2), so the NEXT window owes a BUSINESS face and may not run another battery instead.",
    "2026-11-06 R2485 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was built, and what it bought is that R2484's hub-to-panel face is now proved green by a full battery on a committed tree rather than merely committed; (b) the first attempt's five-minute cancellation is disclosed above and its partial evidence was deleted, so no evidence file is claimed that this window did not actually produce; (c) the battery ran on the tree as committed at R2484 with no product byte edited during it, and the only files that changed while it ran were its own evidence log and the tmp reclaim; (d) Docker is absent on this host, so a containerised bring-up of the six sandbox faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 canonical board; (g) no fold was due: src/os/state.json measured 21965B at open against the 78500B waterline, so this append leaves it far clear of the line.",
    "R2485 tokens: local=~11k api=0 api_reason=verification window - one debt-register read that settled the claim order, one cancelled battery attempt disclosed and discarded, one detached green battery at 570/570 suites and exactly 4396 criteria with an independent recount and encoding check, one designed matrix FAIL followed by a stamp-aligned regeneration and a byte-identical --check, four follow-up sections PASS for VERDICT R2485 PASS, one battery debt row closed through its shipped writer, and the state/export/backlog closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2485 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2485
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
          and back["tick"] == 2485
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())