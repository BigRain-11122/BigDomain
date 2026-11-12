"""R2669 verification closeout append: the R2665 leg watched to green and the debt row closed."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-12 R2669 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2661 at 653 suites / 4894 criteria). Five readings at open: git status EMPTY at HEAD d0ee050c equal to origin/main with no index.lock; atbd_lines=0 unreplied_groups=0 in cph4/evolution-ledger.md; the content-addressed decisions scan read rows=114 tokens=63 with new=0; the group orders tail still carried the 2026-11-12 12:45 bm-a station_drive row already recorded as last_order and judged knowledge-only for this company; benchmarks_refreshed 2026-11-10 sitting two days inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2661 opened=R2661 carried=8 stale=yes open=45 first=1; queue_head named tech line 666 prefix AC-EDXC1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10. state_fold --check read FOLD-CLEAR at 71726B against the 78500B gate with margin 6774 and 99 live log lines.",
    "R2669 THE R2665 LEG WAS ADOPTED, WATCHED TO COMPLETION AND MEASURED ON BYTES - NOT RESTARTED AND NOT QUOTED: pids 45996 and its reconcile_all child 53916 were live by command line at open (started 2026-11-12 12:36:39, stream 1088013B at 646/653 rows and 0 FAIL), and bounded polls took it to 648, 649 and then to its closing line, so the leg finished at 13:29:08 on RUNNER PASS (653/653 suites green, reconcile controls 7/7, 3144.0s) with BATTERY rc=0 3144.2s and its single-writer evidence qa/reconcile-all-R2665.log landed at 1103320B. MEASURED before any follow-up append: utf-8 True, bom=False, crlf=0, lone_cr=0, nul=0, 8656 lines, 653 real suite rows with 653 UNIQUE names, 653 PASS and ZERO FAIL rows, and an INDEPENDENT criteria recount over the per-row fields summing to EXACTLY 4894 against the pre-registered 653/4894; the registry was re-measured by importing reconcile_all.SUITES at 653 suites / 4894 criteria / 653 unique names / 653 unique paths, byte for byte the registered number.",
    "R2669 FOLLOW-UP IN THE DESIGNED ORDER, PLUS ONE DISCLOSURE THAT MATTERS MORE THAN THE GREEN: the four sections ran as designed - matrix FAIL first by design (on-disk 67021B against regenerated 67024B, NO byte written) while fingerprint read CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN - then docs/sandbox-suite-matrix.md was regenerated stamp-aligned from THIS round own green leg to 67024B at 653 suites / 4894 criteria with its green line honestly reading 653/653 and --check byte-identical at rc=0, then the write leg read four PASS for VERDICT R2665 PASS failing=none (APPENDED 1951B eol_ok=True). THE DISCLOSURE: commit d0ee050c landed at 13:01:02, INSIDE this leg window 12:36:39-13:29:08, so under the R2614 discipline this green verdict is admissible only beside individual re-runs of the write-sensitive suite family (the export trio, the ledger round-coverage face and the readability family) on the FINAL committed tree - those re-runs follow this closeout commit and land in their own utf-8 LF evidence file through the shipped capture writer, and until they do the verdict is named as conditional rather than claimed as unconditional.",
    "R2669 DEBT, BOARD AND HONEST: reconcile-battery-R2661 was closed through the shipped debtor at its predicted and measured 211760B -> 211763B (line 391, open 45->44, done 328->329, readback ok) and product-face-R2669 was appended first=yes (212161B, readback ok) naming the next window a PRODUCT face on the queue head state/queue/tech.md:666 prefix AC-EDXC1; the dry run predicted 212155B and the execute landed 212161B because I corrected one typo in the note text between them, which is disclosed rather than smoothed. NO successor battery is owed because this window moved no product src byte and the registry is unmoved at 653/4894, re-measured by import. HONEST: (a) ZERO product points on the Executive Protocol scale and no product byte written - the owed battery held the tree, and nothing a CEO could newly open was built, so every P-47 item still waits on CEO physical items (merchant id, mini-program appid/secret); (b) the leg was authored by R2665 and this window only adopted, watched and measured it, which is the third window in a row to inherit this row and the FIRST to close it; (c) the leg ran 52.5 minutes against a 25-minute window budget so this window overran, named rather than hidden; (d) src/os/scan_five_still.py still crashes at its final [ORD-TOP] print on the GBK console, so the scan was run under PYTHONIOENCODING=utf-8 - WORKED AROUND, NOT REPAIRED; (e) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed; (f) tasks.md was not touched, it is the P-47 canonical board; (g) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2669 tokens: local=~13k api=0 api_reason=verification window - one five-silence scan with the content-addressed decisions scan, the group orders tail and the ledger face read, one debt gate plus queue head and floor plus fold gate read, one live leg adopted from two confirmed pids and watched through four bounded polls to its closing line, one byte-level re-measurement of the evidence on seven axes with an independent criteria recount, one registry re-measurement by import on four axes, one designed matrix FAIL with no byte written, one stamp-aligned regeneration checked byte-identical, one four-section write leg to a PASS verdict, one debt row closed and one successor opened through their shipped writers, one state fold check and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    for index in range(start):
        if lines[index].strip().startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            break
    else:
        print("REFUSED no tick line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2669_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
