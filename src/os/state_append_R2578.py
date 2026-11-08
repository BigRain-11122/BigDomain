"""Append the R2578 round block to src/os/state.json in place."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2578 VERIFICATION window on the battery the register owed (reconcile-battery-R2577, pre-registered 618 suites / 4684 criteria at R2577 because that window moved the registry by one row and shipped a document). Five-silence at open: git status EMPTY at HEAD a996d630 equal to origin/main with no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the decisions file read 284 rows against the stored 284 baseline (no new token), the group orders tail held last_tok=2026-11-08 18:03 (OB-20261108-180341-868, an @BigMoney re-dispatch, knowledge-only for this company; the 12:06 row OB-20261108-120628-589 is @BigMoney too), benchmarks 2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST item=reconcile-battery-R2577 opened=R2577 carried=1 stale=no open=32 first=1, so the R2168 mixed-tree rule ranked the battery ahead of product bytes; queue_head named tech line 613 prefix AC-PNMA1 claimable=11 and queue_floor read FLOOR-MET at main 5/5 tech 11/10 explore 10/10. The target was RE-MEASURED by importing reconcile_all.SUITES BEFORE the launch: 618 suites, 4684 criteria, 618 unique names, 618 unique paths, byte for byte the registered number.",
    "2026-11-08 R2578 GREEN ON THE FIRST LEG, measured not quoted (qa/reconcile-all-R2577.log, 1045040B at delivery, 1046991B after one follow-up block and 1048942B after a second identical block, utf-8 bom=False crlf=0 lone_cr=0 nul=0, 8038 lines): RUNNER PASS (618/618 suites green, reconcile controls 7/7, 1542.2s), ZERO FAIL suite rows, 618 unique suite names, and an INDEPENDENT recount over their own criteria fields summing to EXACTLY 4684 - the pre-registered total matched by measurement on both axes, with the registry re-read by import matching at 618 / 4684. Launched detached through src/os/battery_stream.py with its stream and its pid in SEPARATE files under logs/ and NEVER a shell redirection into qa/, so the ps-utf16 trap was not re-paid. TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB. The leg went green so no red leg exists to keep and no repair was needed, which is a fact of this run and not a claim that the battery is safe in general.",
    "2026-11-08 R2578 FOLLOW-UP in the designed order: the dry run read SECTION matrix FAIL first BY DESIGN at on-disk 61209B against regenerated 61204B with NO byte written while fingerprint read PASS CLEAN domains=5, profile read PASS byte-identical and census read PASS DRIFT-CLEAN, for VERDICT R2578 FAIL failing=matrix; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS round own green evidence through src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2577.log --stamp-from docs/sandbox-suite-matrix.md to 61204 bytes at 618 suites / 4684 criteria with its green line honestly reading 618/618 self-describing, --check read byte-identical at rc=0, and the four sections re-ran to VERDICT R2578 PASS failing=none (APPENDED 1951B eol_ok=True, and the appended block own trailer line reads bytes=1046991 eol bom=False).",
    "2026-11-08 R2578 DEBT AND BOARD: reconcile-battery-R2577 was closed through the shipped debtor at its predicted and measured 182931B -> 182934B (line 326, open 32->31, done 277->278, readback ok), and product-face-R2578 was appended first=yes through the shipped appender at its predicted 182934B -> 183511B (readback ok) naming the next window a PRODUCT face on the queue head state/queue/tech.md:613 prefix AC-PNMA1, whose AC-PNMA1..AC-PNMA6 were pinned in that row at R2577 BEFORE any code. NO successor battery is owed: this window moved no product src byte and the registry is unmoved at 618 suites / 4684 criteria, which is exactly what the green leg measured, and the count was re-read by import rather than trusted. queue_head re-read line 613 claimable=11 and queue_floor re-read FLOOR-MET at 5/5 11/10 10/10; no queue row was opened or closed, because a verification window writes no board row.",
    "2026-11-08 R2578 honest disclosures: (a) ZERO product points on the Executive Protocol scale - nothing a CEO could open was built this window and none is claimed; the deliverable is a green 618/4684 battery on disk, a matrix document whose evidence column names THIS round own green leg with green=618/618 self-describing, and one closed debt row. (b) The leg went green so no red leg exists to keep and no repair was needed, which is a fact of this run. (c) MY OWN SLIPPAGE IS NAMED RATHER THAN HIDDEN: I ran the follow-up write leg TWICE (the second time only to capture its exit code after the PowerShell wrapper printed -1 for a native python.exe), so qa/reconcile-all-R2577.log carries TWO identical 1951B follow-up blocks instead of one and grew 1046991B -> 1048942B; the blocks are byte-identical and neither was edited by hand. (d) The first follow-up invocation with --round R2578 was refused E_BFU_BAD_ARGS because that flag wants an integer, and the integer form was used afterwards. (e) state.json read 74233B against the 78500B waterline at open (FOLD-CLEAR margin 4267) and this append was checked for the indent=1 no-trailing-newline round-trip before mutation; the append pushes the file past the gate, so a fold at a true round-block boundary is run in this window and its result is reported by the next line rather than assumed here. (f) last_decision_rows stands at 284 and the content-addressed token set is unchanged because the scan read no new token. (g) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (h) tasks.md was not touched, it is the P-47 canonical board. (i) The S4U lane re-registration still needs an ELEVATED shell and D-20261107-14 has classified it as a ceo-pending physical item with zero chase.",
    "R2578 tokens: local=~9k api=0 api_reason=verification window - one five-silence scan with the decisions and orders faces actually read, one debt gate read naming the owed battery, one queue head and floor read, one registry target re-measured by import on both axes, one full 618-suite battery green on the first leg at the pre-registered 4684 criteria with an independent criteria recount, one designed matrix FAIL with no byte written, one stamp-aligned regeneration from this round own green evidence checked byte-identical, one four-section follow-up to a PASS verdict, one debt row closed and one opened through their shipped writers, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    proved = json.dumps(data, ensure_ascii=False, indent=1)
    if proved != text:
        sys.stdout.write("E_APPEND_ROUNDTRIP: layout is not indent=1\n")
        return 2
    data["tick"] = data["tick"] + 1
    data["last_order"] = "2026-11-08 18:03"
    data["last_decision_rows"] = 284
    data["log"].extend(LINES)
    out = json.dumps(data, ensure_ascii=False, indent=1)
    io.open(PATH, "wb").write(out.encode("utf-8"))
    back = io.open(PATH, "rb").read().decode("utf-8")
    check = json.loads(back)
    sys.stdout.write("APPENDED bytes %d -> %d tick=%d log_lines=%d ok=%s\n" % (
        len(raw), len(out.encode("utf-8")), check["tick"], len(check["log"]),
        check["log"][-1].startswith("R2578 tokens:")))
    return 0


if __name__ == "__main__":
    sys.exit(main())