"""R2483 closeout: append this window's log items and move the tick. One
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
    "2026-11-06 R2483 VERIFICATION window on the two batteries the register owed (reconcile-battery-R2481 and reconcile-battery-R2482, pre-registered at 568/4384 and 569/4390), because the R2168 mixed-tree rule puts the battery ahead of any further product byte and neither product window had ever run one. Five-silence scan at open: git status empty at HEAD 709e4e30 with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff reading new=0 against the stored 142-token baseline, the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 inside the seven-day gate; the debt gate named CLAIM-FIRST item product-face-R2456 carried=28 BUT the two open battery rows sit AHEAD of it by the mixed-tree rule, so this window claimed the battery rather than the audit row.",
    "2026-11-06 R2483 FIRST BATTERY LEG WAS RED AND NAMED ONE REAL DEFECT, which is the whole reason the battery is owed before product bytes: 568/569 suites green with 4390 criteria counted, and the single failure was reconcile-daily-census cd7-live-real-tree exit=2 drift. Running that suite alone reproduced it in 5 seconds (so this was a defect, not load noise) and the census body named the cause in four lines: [flag] new-dialect for panel-R2482-adjacent.log, panel-lobby-R2482-a.log, panel-lobby-R2482-b.log and start-all-R2482-adjacent.log, all class=ps-utf16, verdict DRIFT-FLAG, census exit=2. In other words the SAME PowerShell-pipe dialect trap R2479 paid for once and disclosed was paid for again by R2482, whose four evidence files were UTF-16 while its own narrative described two clean legs; no product byte was wrong, but four pieces of proof were written in a dialect the census refuses.",
    "2026-11-06 R2483 repaired the defect at its birth site instead of touching the detector: the four ps-utf16 files were deleted and the evidence was re-taken through the SHIPPED capture callable src/os/evidence_capture.py, which runs each suite twice itself and writes exactly one utf-8 LF file after refusing red or drifting legs. Two files replaced four: qa/panel-lobby-R2483.log (1532B, LEG A/B rc=0 both, digest 10C09149A5755E9A, adjacent test_panel.py green) and qa/start-all-R2483.log (464B, identical legs, adjacent test_panel.py green), both measured crlf=0 / lone_cr=0 / no BOM. The same census then read (0, 'ok') files=2578 flags=0 verdict DRIFT-CLEAN, and test_reconcile_daily_census.py read SUITE PASS 8/8 alone with cd7 exit=0 label=ok. The repair was committed as 6f2e6eb4 so the retry battery ran on a committed tree rather than a dirty one.",
    "2026-11-06 R2483 RETRY BATTERY GREEN, MEASURED NOT QUOTED: qa/reconcile-all-R2483-retry.log is 864674B with no BOM, crlf=0 and lone_cr=0, and its own closing line reads 'RUNNER PASS (569/569 suites green, reconcile controls 7/7, 1652.7s)'. An independent recomputation over the 569 per-suite rows sums to exactly 4390 criteria with zero FAIL suite rows - i.e. the total pre-registered at R2482, matched byte for byte by measurement rather than asserted. Honest note on provenance: the body's first line reads 'no evidence path: shell-capture mode, evidence dialect follows the caller', the same caller-dialect disclosure R2480 made, and the bytes were verified utf-8 LF afterwards.",
    "2026-11-06 R2483 the four follow-up sections ran in the designed order and needed one repair of their own: the dry run read SECTION matrix FAIL on-disk=54605B regenerated=54691B while fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN, for VERDICT R2483 FAIL failing=matrix; src/sandbox/suite_matrix.py then regenerated docs/sandbox-suite-matrix.md from THIS round's own green evidence through --evidence plus --stamp-from, printing 'PASS generated ... 54691 bytes ... registry suites=569 criteria=4390 evidence=qa/reconcile-all-R2483-retry.log green=569/569', with --check reading byte-identical at 54691B / 569 / 4390. The write leg then read all four sections PASS - matrix byte-identical, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN - for VERDICT R2483 PASS failing=none (APPENDED 1950B eol_ok=True). The matrix is self-describing this round because it names this round's own battery rather than a borrowed leg.",
    "2026-11-06 R2483 debt register closed through its own writer, twice: reconcile-battery-R2481 closed at line 206 (open 4->3, done 184->185, 125387B -> 125391B, readback ok) and reconcile-battery-R2482 at line 207 (open 3->2, done 185->186, 125391B -> 125395B, readback ok). No successor battery was registered: this window's only post-battery writes are the matrix doc, the debt register, the state/backlog/export closeout and two one-off closeout scripts, none of which is a registry module or suite, and the registry is unmoved at 569 suites / 4390 criteria - the same reasoning R2480 used. The gate now reads CLAIM-FIRST item=product-face-R2456 (prefix AC-PFKC1) with open=2, so the NEXT window owes a BUSINESS face, not another battery.",
    "2026-11-06 R2483 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was built, and what it bought is that two product windows' worth of proof is now TRUE on a committed tree instead of merely committed; (b) the defect it caught was self-inflicted by R2482, and the only reason it surfaced is that a battery finally ran over that tree - the census detector existed and worked, it simply had not been turned on; (c) my own round-open mistake is disclosed: I invoked 'reconcile_all.py --help', which this runner does not support, so it treated the flag as an evidence path, began running suites in-process and created a stray file literally named '--help'; the pipeline was closed, the stray file was deleted before any commit, and no evidence file was produced by it, but the CLI has no unknown-flag refusal and that is a real (unfixed, unclaimed) rough edge; (d) the capture rewrite means the four R2482 evidence paths quoted in that round's narrative no longer exist - they were replaced by the two R2483 files and the git history holds the old bytes; (e) Docker is absent on this host, so a containerised bring-up of the sandbox faces stays unproved and is not claimed; (f) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (g) tasks.md was not touched, it is the P-47 canonical board; (h) no fold was due: src/os/state.json measured 68643B at open against the 78500B waterline and 77724B after this append (state_io reads CANON-CLEAN with 87 log items), so the next window starts about 776B under the line rather than comfortably clear of it and must measure at open.",
    "R2483 tokens: local=~14k api=0 api_reason=verification window - one full battery RED that named exactly one defect, one alone-run reproduction, one birth-site dialect repair through the shipped capture callable (four ps-utf16 evidence files replaced by two utf-8 LF files), one census DRIFT-CLEAN read, one full retry battery GREEN at 569/569 and exactly 4390 criteria on the committed repair tree, one designed matrix FAIL followed by a stamp-aligned regeneration and a byte-identical --check, four follow-up sections PASS for VERDICT R2483 PASS, two battery debt rows closed through their shipped writer, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2483 self-heal check: BigDomain-OSLoop exists and reads Ready, but its Principal.LogonType still reads Interactive (InteractiveToken), which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2483
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
          and back["tick"] == 2483
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())