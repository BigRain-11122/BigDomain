"""R2556 closeout append: the verification window on the R2555 battery.

The shipped state_fold layout reader still refuses this file and state_fold.py
offers ONLY a --check face, so the append is a PROVED load+dump round-trip.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

ROUND = (
    "2026-11-08 R2556 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2555, pre-registered 607 suites / 4618 criteria "
    "because R2555 moved the registry by one row and a shipped document, the "
    "R2168 mixed-tree rule). Five-silence at open: git status EMPTY at HEAD "
    "ccb9f656 equal to origin/main with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read new=0 "
    "over the stored baseline at a measured 70 rows, the group orders tail "
    "unchanged at 2026-11-08 00:04 (OB-20261108-000400-425, already judged "
    "knowledge-only), benchmarks 2026-11-03 inside the seven-day gate. The "
    "debt gate read CLAIM-FIRST item=reconcile-battery-R2555 opened=R2555 "
    "carried=1 stale=no open=22 first=1, and the target was RE-MEASURED by "
    "importing reconcile_all.SUITES from src/sandbox BEFORE the launch: 607 "
    "suites and 4618 criteria, byte for byte the registered number. "
    "RESULT GREEN ON THE FIRST LEG, measured not quoted: "
    "qa/reconcile-all-R2556.log is 1016619B at the green leg, utf-8 bom=False "
    "crlf=0 lone_cr=0 nul=0, closing RUNNER PASS (607/607 suites green, "
    "reconcile controls 7/7, 1492.6s) with zero FAIL suite rows, 607 PASS suite "
    "rows holding 607 UNIQUE names and zero duplicates, and an independent "
    "recount over their own criteria fields summing to EXACTLY 4618 - the "
    "pre-registered total matched by measurement on both axes. Launched "
    "detached through src/os/launch_battery_R2556.py with its stream and its "
    "pid in SEPARATE files, and no shell redirection ever touched qa/ (the "
    "ps-utf16 trap). The leg went green so no red leg exists to keep and no "
    "repair was needed, which is a fact of this run and not a claim that the "
    "battery is safe in general. "
    "FOUR FOLLOW-UP SECTIONS in the designed order: the dry run read SECTION "
    "matrix FAIL at on-disk 58970B against regenerated 58964B with NO byte "
    "written while fingerprint read CLEAN domains=5, profile byte-identical and "
    "census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then regenerated "
    "stamp-aligned from THIS round own green evidence through "
    "src/sandbox/suite_matrix.py --stamp-from to 58964 bytes at 607 suites / "
    "4618 criteria with its green line honestly reading 607/607 "
    "self-describing, --check read byte-identical at rc=0, and the re-run read "
    "all four PASS for VERDICT R2556 PASS failing=none (APPENDED 1951B "
    "eol_ok=True). "
    "DEBT AND BOARD: reconcile-battery-R2555 was closed through the shipped "
    "debtor at its predicted 173311B -> 173314B (line 294, open 22->21, done "
    "255->256, readback ok). NO successor battery is owed because this window "
    "moved no product src byte and the registry is unmoved at 607 suites / "
    "4618 criteria, which is exactly what the green leg measured; the count "
    "was re-read by import rather than trusted. The gate then owed a leader, "
    "so product-face-R2556 was appended first=yes through the shipped appender "
    "at its predicted 173314B -> 173595B (readback ok) naming the next window "
    "a PRODUCT face on the queue head state/queue/tech.md:593 prefix AC-PNDS1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_position, whose "
    "AC-PNDS1..AC-PNDS6 were pinned in that row at R2555 BEFORE any code; "
    "queue_head read line 593 claimable=12 with the floor MET. No queue row was "
    "opened or closed this window, because a verification window writes no "
    "board row."
)


def honest_line(size):
    return (
        "2026-11-08 R2556 honest disclosures: (a) ZERO product points on the "
        "Executive Protocol scale - nothing a CEO could open was built this "
        "window and none is claimed; the deliverable is a green 607/4618 "
        "battery and a matrix document whose evidence column names THIS round "
        "own green leg with green=607/607 self-describing. (b) The leg was "
        "green so no red leg exists to keep and no repair was needed, which is "
        "a fact of this run. (c) MEASURED DEFECT STILL OPEN from R2522: "
        "state.json stands at %dB against the 78500B waterline so state_fold "
        "--check reads FOLD-DUE and this build ships only a --check face, so "
        "the fold stays an OWED obligation seeded as state_fold_run "
        "(AC-SFOLD1..6); this append used a PROVED load+dump round-trip. (d) "
        "The window ran one full 1492.6s battery plus a follow-up pair and two "
        "polling loops, so it went far past its 25-minute budget and says so; "
        "one polling loop was auto-cancelled by the shell tool own five-minute "
        "silence limit and the detached battery was UNAFFECTED because it is a "
        "separate process, so the wait was resumed with a heartbeat loop rather "
        "than relaunched and no duplicate run exists. (e) residue_triage was "
        "NOT re-read this window, so no claim is made about its verdict here. "
        "(f) The open rows product-face-R2511, R2513, R2515, R2517 and R2522 "
        "still name product windows whose suites demonstrably shipped and the "
        "shipped readers still do not age them; this window declined to "
        "mass-close them by hand and did not invent a reading to hide them. "
        "(g) Docker is absent on this host so no containerised bring-up of the "
        "sandbox faces is claimed. (h) The real 19.9 debit and the real "
        "msgSecCheck still wait on CEO physical items (merchant id, "
        "mini-program appid/secret). (i) tasks.md was not touched, it is the "
        "P-47 canonical board. (j) The S4U lane re-registration still needs an "
        "ELEVATED shell and remains a ceo-pending physical item with zero "
        "chase." % (size,)
    )


TOKENS = (
    "R2556 tokens: local=~9k api=0 api_reason=verification window - "
    "five-silence scan, one content-addressed decisions scan reading new=0, "
    "one debt gate read naming the owed battery, one registry target "
    "re-measured by import, one full 607-suite battery green on the first leg "
    "at the pre-registered 4618 criteria with an independent criteria recount "
    "and a duplicate check, one designed matrix FAIL with no byte written, one "
    "stamp-aligned matrix regeneration from this round own green evidence "
    "checked byte-identical, one four-section follow-up re-run to a PASS "
    "verdict, one debt row closed and one opened through their shipped "
    "writers, and the state/export/backlog/heartbeat closeout; zero cloud "
    "calls and zero external API touches"
)


def main():
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    replay = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if replay.encode("utf-8") != raw:
        print("REFUSED E_APP_ROUNDTRIP: dump does not reproduce the file")
        return 3
    state["tick"] = 2556
    state["last_decision_rows"] = 70
    state["log"].extend([ROUND, honest_line(len(raw)), TOKENS])
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