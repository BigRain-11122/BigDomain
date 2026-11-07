"""R2546 closeout append: a verification window that moved no product byte.

The shipped state_fold layout reader still refuses this file (E_SF_BAD_LAYOUT,
reproduced this round), so the append is a PROVED load+dump round-trip: the
bytes are read, decoded, re-encoded and compared byte for byte BEFORE any
mutation, and only then are the tick and the log rows written.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-08 R2546 VERIFICATION window on the battery the register owed ("
    "reconcile-battery-R2545, pre-registered 602 suites / 4588 criteria). "
    "Five-silence scan at open: ONE untracked battery leg qa/reconcile-all-R2546.log "
    "was already on disk from an earlier attempt of this same round, with no index.lock "
    "and no live reconcile process, so it was READ rather than restarted; git status "
    "otherwise empty at HEAD b0d32e12; zero @BigDomain rows in cph4/evolution-ledger.md; "
    "the content-addressed decisions scan read new=0 over the stored 182-token baseline "
    "at a measured 46 file tokens (the group file keeps shrinking under a group-level "
    "fold, disclosed rather than smoothed); the group orders tail still reads "
    "2026-11-08 00:04 (a lane-batch dispatch already judged knowledge-only); benchmarks "
    "2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST item="
    "reconcile-battery-R2545 first=1, and the target was RE-MEASURED before anything "
    "ran by importing reconcile_all.SUITES: 602 suites / 4588 criteria, byte for byte "
    "the registered number.",

    "2026-11-08 R2546 GREEN ON THE FIRST LEG, measured not quoted: "
    "qa/reconcile-all-R2546.log is 967255B on disk (963416B at the green leg, plus the "
    "1889B designed FAIL block and the 1950B PASS block), utf-8 bom=False crlf=0 "
    "lone_cr=0, closing RUNNER PASS (602/602 suites green, reconcile controls 7/7, "
    "1688.0s), ZERO FAIL suite rows, 602 UNIQUE suite rows with zero duplicates, and an "
    "independent recount over their own criteria fields summing to EXACTLY 4588 - the "
    "pre-registered total matched by measurement, and the registry re-read by import "
    "matching at 602 suites / 4588 criteria. No shell redirection ever touched qa/, so "
    "the evidence is one single-writer utf-8 LF artifact. FOUR FOLLOW-UP SECTIONS in the "
    "designed order: the dry run read SECTION matrix FAIL at on-disk 58228B against "
    "regenerated 58224B with NO byte written while fingerprint read CLEAN domains=5, "
    "profile byte-identical and census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then "
    "regenerated stamp-aligned from THIS round own green evidence through "
    "src/sandbox/suite_matrix.py --stamp-from to 58224 bytes at 602 suites / 4588 "
    "criteria with its green line honestly reading 602/602 self-describing, --check read "
    "byte-identical at rc=0, and the re-run read all four PASS for VERDICT R2546 PASS "
    "failing=none (APPENDED 1950B eol_ok=True).",

    "2026-11-08 R2546 DEBT AND BOARD: reconcile-battery-R2545 was closed through the "
    "shipped debtor at its predicted 169253B -> 169256B (line 282, open 20->19, done "
    "244->245, readback ok). NO successor battery is owed because this window moved no "
    "product src byte and the registry is unmoved at 602 suites / 4588 criteria, which is "
    "exactly what the green leg measured; the count was re-read by import rather than "
    "trusted. The gate then owed a leader, so product-face-R2546 was appended first=yes "
    "through the shipped appender at its predicted 169256B -> 169517B (readback ok) naming "
    "the next window a PRODUCT face on the queue head state/queue/tech.md:583 prefix "
    "AC-PNCT1 probe_seam_name_binding_control_flow_guard_exhaustive, whose AC-PNCT1.."
    "AC-PNCT6 were pinned in that row at R2545 BEFORE any code. queue_head read "
    "claimable=11 at line 583 with the floor MET. No queue row was opened or closed this "
    "window, because a verification window writes no board row.",

    "2026-11-08 R2546 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - nothing a CEO could open was built this window and none is claimed; "
    "the deliverable is a green 602/4588 battery and a matrix document whose evidence "
    "column names THIS round own green leg. (b) THIS WINDOW OPENED ON AN INTERRUPTED "
    "ATTEMPT: a battery leg was already on disk when the window opened, its cause unknown "
    "then, and it was read first rather than restarted - it happened to be green, which is "
    "stated rather than dressed as a prediction. (c) MEASURED DEFECT STILL OPEN from "
    "R2522: state.json stands at 175002B against the 78500B waterline so state_fold "
    "--check reads FOLD-DUE, and the fold could NOT run because the shipped layout reader "
    "still refuses a json.dump layout with E_SF_BAD_LAYOUT (log item lines do not match "
    "log length 142) - reproduced here rather than assumed, so the fold is CARRIED as an "
    "owed obligation and this append used a PROVED load+dump round-trip. (d) The residual "
    "battery open rows product-face-R2511, R2513, R2515, R2517 and R2522 still name "
    "product windows whose suites demonstrably shipped, and the shipped readers still do "
    "not age them; this window declined to mass-close them by hand and did not invent a "
    "reading to hide them. (e) Docker is absent on this host so no containerised bring-up "
    "of the sandbox faces is claimed. (f) The real 19.9 debit and the real msgSecCheck "
    "still wait on CEO physical items (merchant id, mini-program appid/secret). (g) "
    "tasks.md was not touched, it is the P-47 canonical board. (h) The S4U lane "
    "re-registration needs an ELEVATED shell and D-20261107-14 has classified it as a "
    "ceo-pending physical item with zero chase, so loop-s4u-reconcile stays a physical "
    "item rather than a loop obligation. (i) The window overshot its 25-minute budget on "
    "a 1688.0s battery plus two follow-up passes and says so.",

    "R2546 tokens: local=~8k api=0 api_reason=verification window - five-silence scan, "
    "one pre-existing battery leg read rather than restarted, one content-addressed "
    "decisions scan reading new=0, one registry target re-measured by import, one full "
    "602-suite battery green on the first leg at the pre-registered 4588 criteria with an "
    "independent criteria recount and a duplicate check, one designed matrix FAIL with no "
    "byte written, one stamp-aligned matrix regeneration from this round own green "
    "evidence checked byte-identical, one four-section follow-up re-run to a PASS verdict, "
    "one debt row closed and one opened through their shipped writers, one fold attempt "
    "refused at its shipped layout reader and carried, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    replay = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if replay.encode("utf-8") != raw:
        print("REFUSED E_APP_ROUNDTRIP: dump does not reproduce the file")
        return 3
    state["tick"] = 2546
    state["log"].extend(LINES)
    out = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    print("APPENDED before=%dB after=%dB tick=%d log=%d readback=%s"
          % (len(raw), len(back), state["tick"], len(state["log"]),
             "ok" if back == out else "MISMATCH"))
    return 0


if __name__ == "__main__":
    sys.exit(main())