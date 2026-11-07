"""R2530 closeout: state append, backlog row and heartbeat, one write each.

The state file is appended through a PROVED load+dump round-trip (the shipped
state_fold layout reader still does not match this file, disclosed since R2522),
so the only bytes added are this round own rows.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

ROWS = [
    "2026-11-07 R2530 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2529, pre-registered 594 suites / 4540 criteria). "
    "Five-silence scan at open: the tree was clean at HEAD 225d6e4b with no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the "
    "content-addressed decisions scan read new=0 over the stored 160-token "
    "baseline at a measured 95 tokens, the group orders tail carried only "
    "2026-11-07 00:19 fleet events rows judged knowledge-only, benchmarks "
    "2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST "
    "item=reconcile-battery-R2529 opened=R2529 carried=1 stale=no open=13 "
    "first=1, and the target was RE-MEASURED before anything ran by importing "
    "reconcile_all.SUITES from src/sandbox: 594 suites and 4540 criteria, byte "
    "for byte the registered number.",

    "2026-11-07 R2530 LEG 1 RED AND KEPT (qa/reconcile-all-R2530.log, 922666B, "
    "utf-8 bom=False crlf=0): RUNNER FAIL (2 failed assertions) at 593/594 "
    "suites with reconcile-daily-census 7/8 red on AC cd7-live-real-tree, whose "
    "measured label was exit=2 drift(exit=2). The shipped writer census named "
    "the cause exactly: flags=2, both new-dialect, "
    "probe-seam-alias-expression-scope-R2529.log and its live sibling, class "
    "ps-utf16 - measured bom16=True with 7456 and 2120 nul bytes, i.e. the R2529 "
    "evidence was landed by a PowerShell redirection instead of the tee writer "
    "the census defines as healthy. REPAIRED AT THE BIRTH SITE: the census ships "
    "no rewrite face, so src/os/repair_dialect_R2530.py was written as an "
    "explicit one (detect the encoding, decode, write utf-8 with newline LF "
    "through tempfile + os.replace, then read the bytes back and print the "
    "measured dialect). My first pass left CRLF in place - measured crlf=86 and "
    "crlf=12, census still flagged class pwsh-capture - and a second pass "
    "normalised CRLF to LF, after which the two files read 7370B and 2108B with "
    "bom=False nul=0 crlf=0 bare_cr=0, the census read files=2670 tee=2141 "
    "baselined=529 disappeared=0 flags=0 verdict DRIFT-CLEAN at rc=0, and the "
    "red suite alone read SUITE PASS 8/8 with cd7 exit=0 label=ok. The repair "
    "and the red leg were committed ALONE as 4ee6f301.",

    "2026-11-07 R2530 BIRTH SITE ALSO PINNED IN GIT: core.autocrlf reads true "
    "and no .gitattributes existed, so a committed LF evidence log is "
    "materialised as CRLF on the next checkout and the census - which "
    "classifies ON-DISK bytes - would flag it again. .gitattributes now marks "
    "qa/*.log as -text so evidence is stored and checked out byte-exact; both "
    "the census and the follow-up dry run were re-read after that change and "
    "still read DRIFT-CLEAN and all four sections PASS. Committed separately as "
    "11bcf106.",

    "2026-11-07 R2530 LEG 2 GREEN, measured not quoted: "
    "qa/reconcile-all-R2530-retry.log is 922689B as delivered, utf-8 "
    "bom=False crlf=0 lone_cr=0, closing RUNNER PASS (594/594 suites green, "
    "reconcile controls 7/7, 1190.4s), zero FAIL suite rows, and an independent "
    "recount over the 594 PASS rows sums to EXACTLY 4540 - the pre-registered "
    "total matched by measurement. Launched detached and unfiltered through "
    "src/os/battery_stream.py (pid in logs/battery-R2530-retry.pid) so the "
    "filtering-pipe trap was not re-paid. FOUR FOLLOW-UP SECTIONS in the "
    "designed order: the dry run read SECTION matrix FAIL at on-disk 57227B "
    "against regenerated 57251B with NO byte written while fingerprint read "
    "CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS "
    "round own green evidence through src/sandbox/suite_matrix.py --stamp-from "
    "(57251 bytes, 594 suites / 4540 criteria, green=594/594 self-describing), "
    "--check read byte-identical at rc=0, and the re-run read all four PASS for "
    "VERDICT R2530 PASS failing=none (APPENDED 1950B eol_ok=True).",

    "2026-11-07 R2530 DEBT AND BOARD: reconcile-battery-R2529 was closed through "
    "the shipped debtor at its predicted 160450B -> 160453B (line 258, open "
    "13->12, done 228->229, readback ok). NO successor battery is owed: the "
    "registry is unmoved at 594 suites / 4540 criteria, re-read by import, and "
    "the only new src byte is the dialect rewrite helper, which carries no suite "
    "of its own - disclosed rather than implied. The gate then owed a leader, so "
    "product-face-R2530 was appended first=yes at its predicted 160453B -> "
    "160679B (readback ok) naming the next window a PRODUCT face on the queue "
    "head state/queue/tech.md:567 prefix AC-PCAF1 probe_seam_for_container_name, "
    "whose AC-PCAF1..AC-PCAF6 were pinned in that row at R2529 BEFORE any code; "
    "queue_head re-read line 567 claimable=11 with the floor MET. No queue row "
    "was opened or closed this window, because a verification window writes no "
    "board row.",

    "2026-11-07 R2530 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 594/4540 battery, a matrix "
    "document whose evidence column names THIS round own green leg, and a real "
    "dialect defect repaired at its birth site. (b) LEG 1 WAS RED and is kept: "
    "the R2529 evidence really did ship in UTF-16, so that window PROOF lines "
    "were not landed through the tee writer. (c) My first repair pass was "
    "incomplete - it converted the encoding but left CRLF, and the census still "
    "flagged both files; a second pass normalised the line endings, reported "
    "rather than smoothed. (d) The rewrite helper ships with no suite of its "
    "own; it was exercised on the two real files with a byte read-back each and "
    "is committed as a tool, not as a registered claim. (e) The window overshot "
    "its 25-minute budget by roughly a factor of two on two full batteries plus "
    "two follow-up passes, and it says so. (f) An early census invocation used "
    "a flag that does not exist and hung for five minutes producing no output; "
    "the shipped --check command was used instead. (g) Docker is absent on this "
    "host so no containerised bring-up is claimed. (h) The real 19.9 debit and "
    "the real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret). (i) tasks.md was not touched, it is the P-47 "
    "canonical board. (j) MEASURED DEFECT STILL OPEN from R2522: the shipped "
    "state_fold layout reader no longer matches the state file written with "
    "json.dump, so this window appended through a proved load+dump round-trip. "
    "(k) The open rows product-face-R2511, product-face-R2513, "
    "product-face-R2515, product-face-R2517 and product-face-R2522 still name "
    "product windows whose suites demonstrably shipped, and the shipped readers "
    "still do not age them; this window declined to mass-close them by hand and "
    "did not invent a reading to hide them.",

    "R2530 tokens: local=~13k api=0 api_reason=verification window - "
    "five-silence scan at the committed tree, one content-addressed decisions "
    "scan reading new=0, one debt gate read naming the owed battery, one "
    "registry target re-measured by import, one full 594-suite battery RED and "
    "kept with its cause measured by the shipped census, one dialect repair "
    "tool written and run twice until the readback was byte-clean, one git "
    "attribute pin so the repair survives a checkout, one red suite re-run "
    "green alone, one second full battery green at the pre-registered 4540 "
    "criteria, four follow-up sections plus one stamp-aligned matrix "
    "regeneration from this round own green evidence checked byte-identical, "
    "one debt row closed and one opened through their shipped writers, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-07 R2530] R2530 VERIFICATION window on the battery the "
    "register owed (reconcile-battery-R2529, pre-registered 594 suites / 4540 "
    "criteria, re-measured by import from src/sandbox and matched byte for "
    "byte). Five-silence scan clean at HEAD 225d6e4b; debt gate CLAIM-FIRST "
    "reconcile-battery-R2529 first=1; queue_head line 567 claimable=11 with the "
    "floor MET. LEG 1 RED AND KEPT (qa/reconcile-all-R2530.log, 922666B): "
    "RUNNER FAIL at 593/594 with reconcile-daily-census 7/8 red on "
    "cd7-live-real-tree exit=2 drift, and the shipped writer census named the "
    "cause - flags=2 new-dialect, the two R2529 evidence logs in UTF-16 "
    "(bom16=True, 7456 and 2120 nul bytes) because that window landed them by "
    "PowerShell redirection instead of the tee writer. REPAIRED AT THE BIRTH "
    "SITE with src/os/repair_dialect_R2530.py (the census ships no rewrite "
    "face): first pass converted the encoding but left CRLF (crlf=86 and 12, "
    "still flagged class pwsh-capture) and a second pass normalised CRLF to LF, "
    "after which both files read bom=False nul=0 crlf=0 at 7370B and 2108B, the "
    "census read flags=0 DRIFT-CLEAN at rc=0 and the red suite alone read SUITE "
    "PASS 8/8; repair plus red leg committed ALONE as 4ee6f301. The defect was "
    "also pinned in git: core.autocrlf reads true with no .gitattributes, so "
    "qa/*.log is now marked -text (11bcf106) and the census plus the follow-up "
    "dry run were re-read clean after that change. LEG 2 GREEN: "
    "qa/reconcile-all-R2530-retry.log 922689B utf-8 bom=False crlf=0, RUNNER "
    "PASS (594/594 suites green, controls 7/7, 1190.4s), zero FAIL rows, "
    "independent recount summing to EXACTLY 4540. FOUR FOLLOW-UP SECTIONS: "
    "matrix FAIL first by design (57227B vs 57251B, no byte written) then "
    "stamp-aligned regeneration from this round own green leg to 57251B at "
    "594/4540 with green=594/594 and --check byte-identical, then all four PASS "
    "for VERDICT R2530 PASS failing=none (APPENDED 1950B). DEBT: "
    "reconcile-battery-R2529 closed (160450B -> 160453B, line 258, open 13->12, "
    "done 228->229); NO successor battery owed because the registry is unmoved "
    "at 594/4540 and the only new src byte is a tool with no suite of its own; "
    "product-face-R2530 appended first=yes (160453B -> 160679B) naming the next "
    "window a PRODUCT face on tech.md:567 prefix AC-PCAF1 "
    "probe_seam_for_container_name, criteria pinned at R2529 BEFORE any code. "
    "HONEST: zero product points, nothing a CEO could open was built; leg 1 was "
    "red and kept; my first repair pass was incomplete and was corrected "
    "against measurement; the rewrite helper has no suite; the window overshot "
    "its 25-minute budget about twofold; Docker absent; the real 19.9 debit and "
    "the real msgSecCheck still wait on CEO physical items; tasks.md untouched; "
    "the state_fold layout defect from R2522 is still open so the append used a "
    "proved load+dump round-trip; five stale product-face rows still overstate "
    "outstanding work and were not hand-closed."
)


def main():
    raw = io.open(STATE, encoding="utf-8").read()
    obj = json.loads(raw)
    round_trip = json.dumps(obj, indent=4, ensure_ascii=False) + "\n"
    if round_trip != raw:
        print("FAIL round-trip: %d vs %d" % (len(round_trip), len(raw)))
        return 3
    before = len(raw.encode("utf-8"))
    obj["tick"] = 2530
    obj["log"].extend(ROWS)
    payload = json.dumps(obj, indent=4, ensure_ascii=False) + "\n"
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    ok = back["tick"] == 2530 and back["log"][-len(ROWS):] == ROWS
    print("state %s tick=%s rows=%d before=%d after=%d"
          % ("OK" if ok else "FAIL", back["tick"], len(ROWS), before,
             len(payload.encode("utf-8"))))

    text = io.open(BACKLOG, encoding="utf-8").read()
    rows = text.split("\n")
    if BACKLOG_ROW in text:
        print("backlog SKIP already present")
    else:
        rows.insert(0, BACKLOG_ROW)
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(rows))
        print("backlog OK prepended %d bytes"
              % (len(BACKLOG_ROW.encode("utf-8")),))

    hb = io.open(HEARTBEAT, encoding="utf-8").read()
    line = ("tick=2530 2026-11-07 R2530 verification window: battery red leg "
            "kept and repaired at its birth site (two R2529 evidence logs were "
            "UTF-16, census flagged them, rewrite tool plus a git -text pin), "
            "retry green 594/594 at exactly 4540 criteria, no successor battery "
            "owed, next window owes the product face on tech.md:567\n")
    if "tick=2530" in hb:
        print("heartbeat SKIP already present")
    else:
        with io.open(HEARTBEAT, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
        print("heartbeat OK %d bytes" % (len(line.encode("utf-8")),))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())