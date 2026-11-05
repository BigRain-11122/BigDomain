"""R2480 closeout: tick +1 and the verification narrative for the battery the
R2479 tech window owed. The evidence was produced by an earlier, unclosed
attempt of this same round (launcher plus green log left untracked on disk),
so this window ADOPTS it after measuring it rather than re-running it, and
says so in the log instead of implying it launched the run.
"""

import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-06 R2480 VERIFICATION window on the battery R2479 owed "
    "(reconcile-battery-R2479, pre-registered at 567 suites / 4378 criteria), "
    "because the R2168 mixed-tree rule puts the battery ahead of any further "
    "product byte. Five-silence scan at open: git status carried ONLY this "
    "round's own two untracked artifacts (qa/reconcile-all-R2480.log and "
    "src/os/launch_battery_R2480.py) with no .git/index.lock and HEAD cd78883c "
    "equal to origin/main, the ledger read atbd_lines=0 unreplied_groups=0, the "
    "content-addressed decisions diff read rows=221 tokens=142 new=0 against "
    "the stored baseline, the group orders tail was unchanged at 2026-11-05 "
    "20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 "
    "sit inside the seven-day gate. PROVENANCE DISCLOSED RATHER THAN HIDDEN: an "
    "earlier attempt at this same round launched the battery detached at 00:26 "
    "and never closed out, leaving the launcher plus a green evidence file on "
    "disk at 00:48 while state.json still read tick 2479; this window ADOPTED "
    "that leg and re-measured it byte for byte instead of spending another "
    "1300 seconds, the R2458/R2437 shape, and no live process held the tree.",
    "2026-11-06 R2480 BATTERY GREEN, MEASURED NOT QUOTED: qa/reconcile-all-R2480.log "
    "is 863364B, no BOM, crlf=0, lone_cr=0, 6336 LF bytes, and its own closing "
    "line reads 'PASS suites 567/567 green, expected criteria total=4378, suite "
    "cap=600s overrides=0' - i.e. EXACTLY the total pre-registered at R2479, "
    "and the summary line now names the R2479 cap work in the same breath. An "
    "independent recomputation over 567 per-suite rows sums to 4378 criteria "
    "with zero FAIL rows and zero non-zero exits, so the prediction matched the "
    "measurement and nothing had to be named or swept. Two honest notes about "
    "the body: its first line reads 'no evidence path: shell-capture mode', so "
    "this leg is a caller-dialect capture rather than the battery_stream single "
    "writer (the R2458 precedent), and qa_writer_census --check afterwards read "
    "files=2572 tee=2043 baselined=529 flags=0 verdict DRIFT-CLEAN with the "
    "529-entry baseline untouched; and the tree at launch carried this round's "
    "own two untracked artifacts but no modified tracked byte.",
    "2026-11-06 R2480 the four follow-up sections produced the designed order: "
    "the dry run read SECTION matrix FAIL matrix mismatch on-disk=54575B "
    "regenerated=54551B with NO byte written while fingerprint PASS CLEAN "
    "domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN for "
    "VERDICT R2480 FAIL failing=matrix at exit 2; then src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md from THIS round's own green "
    "evidence through --evidence plus --stamp-from and printed 'PASS generated "
    "... 54551 bytes ... registry suites=567 criteria=4378 "
    "evidence=qa/reconcile-all-R2480.log green=567/567', with --check reading "
    "byte-identical at 54551B / 567 / 4378; the write leg then read all four "
    "sections PASS - matrix byte-identical, fingerprint CLEAN domains=5, profile "
    "byte-identical, census DRIFT-CLEAN - for VERDICT R2480 PASS failing=none "
    "(APPENDED 1950B eol_ok=True). The matrix is self-describing this round at "
    "green=567/567 because it names this round's own battery rather than a "
    "borrowed older leg, which also un-stales the document R2479 had to disclose.",
    "2026-11-06 R2480 debt register closed through its own writer: "
    "reconcile-battery-R2479 closed through debt_close at its predicted "
    "124971B -> 124975B (line=205, open 3->2, done 183->184, readback=ok) after "
    "a dry run that named exactly those deltas. NO successor battery was "
    "registered because this window changed no product src byte and the "
    "registry is unmoved at 567 suites / 4378 criteria - the only file added is "
    "a one-off launcher, not a module. The gate therefore reads CLAIM-FIRST "
    "item=product-face-R2456 opened=R2455, and the two rows now open are that "
    "carried internal audit row (tech head state/queue/tech.md:522 prefix "
    "AC-PFKC1 row_key_carrier_scope) and the elevated-shell row "
    "loop-s4u-reconcile; the NEXT window should ship a BUSINESS face and name "
    "the supersession, per the CEO standing order OB-20261105-003656-879.",
    "2026-11-06 R2480 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt and no P-47 "
    "business surface was touched; what it bought is a proved registry (567 "
    "suites, 4378 criteria) on the exact tree R2479 committed, so the 600s cap "
    "shipped there is now PROVED rather than merely shipped, and the three "
    "ledger suites that kept losing the old 300s cap finished inside the new "
    "one; (b) the battery was ADOPTED, not re-run, and that is stated in the "
    "round narrative as well as here - re-running would have cost 22 minutes to "
    "reproduce a file already on disk; (c) the adopted body is a caller-dialect "
    "capture rather than the single-writer stream, measured crlf=0 / lone_cr=0 "
    "/ no BOM and census-clean, so no evidence byte is at risk but the "
    "provenance is weaker than a battery_stream leg; (d) Docker is absent on "
    "this host, so a containerised bring-up of the sandbox faces stays unproved "
    "and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items (merchant id, mini-program appid/secret); (f) "
    "tasks.md was not touched, it is the P-47 canonical board; (g) no fold was "
    "due: src/os/state.json measured 49836B at open against the 78500B "
    "waterline.",
    "R2480 tokens: local=~7k api=0 api_reason=verification window - one adopted "
    "and byte-measured reconcile battery (567/567 suites, controls 7/7, 4378 "
    "criteria exactly as pre-registered, 1301.2s, cap=600s), one census "
    "DRIFT-CLEAN read, one designed matrix FAIL followed by a stamp-aligned "
    "regeneration and a byte-identical --check, four follow-up sections PASS for "
    "VERDICT R2480 PASS, one battery row closed through its shipped CLI, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external "
    "API touches",
    "2026-11-06 R2480 self-heal check: BigDomain-OSLoop exists and reads "
    "Running, but its Principal.LogonType still reads InteractiveToken, which "
    "the 2026-09-29 machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 needs an elevated shell while this session is "
    "unelevated, so the definition was left untouched again (carried as the "
    "stale row loop-s4u-reconcile).",
]


def main():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "os"))
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("log already carries these lines")
        return
    state["tick"] = int(state["tick"]) + 1
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if int(back["tick"]) != int(state["tick"]) or len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("tick=%d log +%d bytes=%d" % (back["tick"], len(LINES), os.path.getsize(PATH)))


if __name__ == "__main__":
    main()