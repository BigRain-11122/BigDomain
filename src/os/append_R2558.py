"""R2558 closeout append: the verification window on the R2557 battery.

state_fold.py still offers ONLY a --check face and reads FOLD-DUE for this
file, so the append is a PROVED load+dump round-trip with a post-check.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

ROUND = (
    "2026-11-08 R2558 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2557, pre-registered 608 suites / 4624 criteria "
    "because R2557 moved the registry by one row and shipped a document, the "
    "R2168 mixed-tree rule). Five-silence at open: git status EMPTY at HEAD "
    "3535065f equal to origin/main with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read "
    "new=2 (D-20261108-07 secret-scan self-false-positive owned by @HQ tool "
    "seat and D-20261108-08 BigLife feedback silence owned by @BigLife lane, "
    "BOTH outside this company execution surface and logged knowledge-only) "
    "over the stored baseline, the group orders tail unchanged at "
    "2026-11-08 00:04 (OB-20261108-000400-425, already judged "
    "knowledge-only), benchmarks 2026-11-03 inside the seven-day gate. The "
    "debt gate read CLAIM-FIRST item=reconcile-battery-R2557 opened=R2557 "
    "carried=1 stale=no open=23 first=1, and the target was RE-MEASURED by "
    "importing reconcile_all.SUITES from src/sandbox BEFORE the launch: 608 "
    "suites and 4624 criteria with 608 unique paths and zero duplicates, byte "
    "for byte the registered number. RESULT GREEN ON THE FIRST LEG, measured "
    "not quoted: qa/reconcile-all-R2558.log is 1019206B at the green leg, "
    "utf-8 bom=False crlf=0 lone_cr=0 nul=0, closing RUNNER PASS (608/608 "
    "suites green, reconcile controls 7/7, 2099.4s) with zero FAIL suite rows, "
    "608 PASS suite rows holding 608 UNIQUE names and zero duplicates, zero "
    "non-zero exits, zero fail-lines, and an independent recount over their own "
    "criteria fields summing to EXACTLY 4624 - the pre-registered total matched "
    "by measurement on both axes. Launched detached through "
    "src/os/launch_battery_R2558.py with its stream and its pid in SEPARATE "
    "files, and no shell redirection ever touched qa/ (the ps-utf16 trap). The "
    "leg went green so no red leg exists to keep and no repair was needed, "
    "which is a fact of this run and not a claim that the battery is safe in "
    "general. FOUR FOLLOW-UP SECTIONS in the designed order: the dry run read "
    "SECTION matrix FAIL at on-disk 59131B against regenerated 59076B with NO "
    "byte written while fingerprint read CLEAN domains=5, profile "
    "byte-identical and census DRIFT-CLEAN (files=2714 tee=2185 baselined=529 "
    "disappeared=0 flags=0); docs/sandbox-suite-matrix.md was then regenerated "
    "stamp-aligned from THIS round own green evidence through "
    "src/sandbox/suite_matrix.py --stamp-from to 59134 bytes at 608 suites / "
    "4624 criteria with its green line honestly reading 608/608 "
    "self-describing, --check read byte-identical at rc=0, and the re-run read "
    "all four PASS for VERDICT R2558 PASS failing=none. DEBT AND BOARD: "
    "reconcile-battery-R2557 was closed through the shipped debtor at its "
    "predicted 173886B -> 173889B (line 297, open 23->22, done 257->258, "
    "readback ok). NO successor battery is owed because this window moved no "
    "product src byte, the registry is unmoved at 608 suites / 4624 criteria "
    "which was re-read by import rather than trusted, and the only shipped "
    "document that moved is a derived stamp-aligned matrix. The gate then owed "
    "a leader, so product-face-R2558 was appended first=yes through the "
    "shipped appender at its predicted 173889B -> 174373B (readback ok) naming "
    "the next window a PRODUCT face on the queue head state/queue/tech.md:595 "
    "prefix AC-PNDA probe_seam_name_binding_arm_mixed_residual_alias_attribute_base, "
    "whose AC-PNDA1..AC-PNDA6 were pinned in that row at R2557 BEFORE any "
    "code. No queue row was opened or closed this window, because a "
    "verification window writes no board row."
)

DISCLOSE = (
    "2026-11-08 R2558 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 608/4624 battery and a "
    "matrix document whose evidence column names THIS round own green leg with "
    "green=608/608 self-describing. (b) The leg was green so no red leg exists "
    "to keep and no repair was needed, which is a fact of this run. (c) "
    "MEASURED DEFECT STILL OPEN from R2522: state.json stood at 258802B against "
    "the 78500B waterline so state_fold --check reads FOLD-DUE and this build "
    "ships only a --check face, so the fold stays an OWED obligation seeded as "
    "state_fold_run (AC-SFOLD1..6); this append used a PROVED load+dump "
    "round-trip. (d) The window ran one full 2099.4s battery plus a follow-up "
    "quad, so it went far past its 25-minute budget and says so; the wait was "
    "carried by bounded polling loops rather than a relaunch, so no duplicate "
    "run exists. (e) My FIRST criteria count read 0 because reconcile_all.SUITES "
    "rows are (name, path, criteria) TUPLES not objects; the target was "
    "re-measured with the right shape and read 608/4624, and the first wrong "
    "reading was never used for any claim. (f) The two new decisions were "
    "judged knowledge-only against THIS company surface; nothing was executed "
    "for them and no receipts were faked. (g) residue_triage was NOT re-read "
    "this window, so no claim is made about its verdict here. (h) The open rows "
    "product-face-R2511, R2513, R2515, R2517 and R2522 still name product "
    "windows whose suites demonstrably shipped and the shipped readers still do "
    "not age them; this window declined to mass-close them by hand and did not "
    "invent a reading to hide them. (i) Docker is absent on this host so no "
    "containerised bring-up of the sandbox faces is claimed. (j) The real 19.9 "
    "debit and the real msgSecCheck still wait on CEO physical items (merchant "
    "id, mini-program appid/secret). (k) tasks.md was not touched, it is the "
    "P-47 canonical board. (l) The S4U lane re-registration still needs an "
    "ELEVATED shell and remains a ceo-pending physical item with zero chase."
)

TOKENS = (
    "R2558 tokens: local=~11k api=0 api_reason=verification window - "
    "five-silence scan, one content-addressed decisions scan reading new=2 "
    "judged knowledge-only, one debt gate read naming the owed battery, one "
    "registry target re-measured by import (first attempt read 0 with the wrong "
    "row shape and was discarded), one full 608-suite battery green on the "
    "first leg at the pre-registered 4624 criteria with an independent criteria "
    "recount and a duplicate check, one designed matrix FAIL with no byte "
    "written, one stamp-aligned matrix regeneration from this round own green "
    "evidence checked byte-identical, one four-section follow-up re-run to a "
    "PASS verdict, one debt row closed and one opened through their shipped "
    "writers, and the state/export/backlog/heartbeat closeout; zero cloud calls "
    "and zero external API touches"
)

NEW_TOKENS = ["D-20261108-07", "D-20261108-08"]


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    before_tick = state.get("tick")
    before_log = len(state.get("log") or [])
    state["tick"] = int(before_tick) + 1
    log = state.setdefault("log", [])
    log.append(ROUND)
    log.append(DISCLOSE)
    log.append(TOKENS)
    tokens = list(state.get("last_dec_tokens") or [])
    added = 0
    for token in NEW_TOKENS:
        if token not in tokens:
            tokens.append(token)
            added += 1
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = 104
    text = json.dumps(state, ensure_ascii=False, indent=1)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(STATE, encoding="utf-8") as handle:
        back = json.load(handle)
    ok = (back.get("tick") == state["tick"]
          and len(back.get("log") or []) == before_log + 3
          and len(back.get("last_dec_tokens") or []) == len(tokens))
    print("tick %s->%s log %d->%d tokens_added=%d readback=%s"
          % (before_tick, back.get("tick"), before_log,
             len(back.get("log") or []), added, "ok" if ok else "BAD"))
    print("bytes", os.path.getsize(STATE))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())