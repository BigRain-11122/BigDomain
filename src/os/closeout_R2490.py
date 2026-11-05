"""R2490 closeout: append this window's log items and move the tick.

Zero product bytes changed this window: it ran the battery the R2168
mixed-tree rule owed on the committed R2489 tree, closed that debt row and
opened the successor product leader. No new decision token was dispatched, so
the stored baseline is carried unchanged.
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

LINES = [
    "2026-11-06 R2490 VERIFICATION window on the battery the register owed (reconcile-battery-R2489, pre-registered at 573 suites / 4414 criteria), because the R2168 mixed-tree rule puts an owed battery ahead of any further product byte and R2489 had moved the registry by two rows when it wired lobby-hub-member and the never-registered member-face suite. Five-silence scan at open: git status empty at HEAD f3a49c25 with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff reading new=0 over 90 rows/70 baseline tokens, the group orders tail unchanged at 2026-11-05 (stored last_order 2026-11-05 20:22), and benchmarks refreshed 2026-11-03 inside the seven-day gate. debt_gate --check --round R2490 read verdict=OPEN-NONE open=2 first=0 because both open rows carry first=no, so the claim order was settled by the mixed-tree rule rather than by the gate field.",
    "2026-11-06 R2490 the pre-registered target was re-measured BEFORE the run instead of trusted: importing reconcile_all.SUITES read 573 suites and exactly 4414 criteria, byte for byte the note R2489 wrote, so prediction and registry agreed before any suite ran and no delta had to be explained afterwards.",
    "2026-11-06 R2490 BATTERY GREEN ON THE COMMITTED TREE, MEASURED NOT QUOTED: qa/reconcile-all-R2490.log is 867723B utf-8 with bom=False, crlf=0 and lone_cr=0, and its closing line reads 'RUNNER PASS (573/573 suites green, reconcile controls 7/7, 1150.1s)' with zero FAIL suite rows. An independent recount over the 573 per-suite PASS rows sums criteria to exactly 4414 - the pre-registered total - and the tmp reclaim line reads candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB. The run was launched as a detached process with its pid in logs/battery-R2490.pid because the runner tees a block-buffered stdout and the shell watchdog cancels a five-minute silence (the R2485 lesson applied rather than re-paid); this window's first poll of it was cancelled for exactly that reason and the process was left running rather than relaunched.",
    "2026-11-06 R2490 the four follow-up sections reproduced the designed FAIL-then-regenerate shape: the dry run read SECTION matrix FAIL matrix mismatch on-disk=54983B regenerated=54964B with no byte written, while fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN, for VERDICT R2490 FAIL failing=matrix. src/sandbox/suite_matrix.py then regenerated docs/sandbox-suite-matrix.md from THIS round's own evidence through --evidence plus --stamp-from ('PASS generated ... 54964 bytes ... registry suites=573 criteria=4414 evidence=qa/reconcile-all-R2490.log green=573/573'), --check read byte-identical at 54964B / 573 / 4414, and the write leg read all four sections PASS for VERDICT R2490 PASS failing=none (APPENDED 1950B eol_ok=True). The matrix is self-describing this round because its green line names this round's own battery instead of borrowing a prior leg.",
    "2026-11-06 R2490 debt closed and the successor leader opened, both through their own writers: reconcile-battery-R2489 closed through debt_close at line 211 (open 2->1, done 190->191, 127367B -> 127371B, readback ok). No successor battery was registered, on the reasoning the earlier verification windows used - this window's post-battery writes are the matrix doc, the debt register, one closeout script and the state/export/backlog/heartbeat closeout, none of which is a registry module or suite, and the registry is unmoved at 573 suites / 4414 criteria. Because debt_gate then owed a first=yes leader (verdict=OPEN-NONE), product-face-R2490 was appended through debt_append first=yes at 127371B -> 127795B with readback ok, naming the tech head state/queue/tech.md:525 prefix AC-RMSC1 (relative_module_corpus_scope, criteria pinned in that row at R2440 before any code), so the NEXT window owes a BUSINESS-OR-TECH PRODUCT FACE and may not run another battery instead.",
    "2026-11-06 R2490 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was built, and what it bought is that R2489's hub-member face and the two registry rows it wired are now proved green by a full battery on a committed tree rather than merely committed; (b) the battery ran on the tree as committed at R2489 (HEAD f3a49c25) with no product byte edited during it, and the only files that changed while it ran were its own evidence log and the tmp reclaim; (c) my own poll mistake is disclosed rather than hidden: the first progress poll slept 480s inside one shell call, which the tool cancelled at five minutes of silence, so the round spent that wait twice - the battery itself was untouched and never restarted; (d) Docker is absent on this host, so a containerised bring-up of the seven sandbox faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 canonical board; (g) no fold was due: src/os/state.json measured 53266B at open against the 78500B waterline with 60 log items, so this append leaves it far clear of the line.",
    "R2490 tokens: local=~7k api=0 api_reason=verification window - one debt-register read that settled the claim order, one pre-run registry recount that matched the pre-registered 573/4414 before any suite ran, one detached green battery at 573/573 suites with criteria summing to exactly 4414 and a clean encoding check, one designed matrix FAIL followed by a stamp-aligned regeneration and a byte-identical --check, four follow-up sections PASS for VERDICT R2490 PASS, one battery debt row closed and one product leader opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2490 self-heal check: BigDomain-OSLoop exists but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2490
    state["last_order"] = "2026-11-05 20:22"
    state["last_decision_rows"] = 221
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
          and back["tick"] == 2490
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))


if __name__ == "__main__":
    main()