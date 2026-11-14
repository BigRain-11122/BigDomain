"""R2717 verification closeout: adopted leg, verdict, board, debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2717 VERIFICATION ADOPTION window on the battery the debt gate "
    "named first (reconcile-battery-R2716, pre-registered 669 suites / 4990 "
    "criteria at R2716): the R2168 mixed-tree rule owed the full battery BEFORE "
    "any product byte because R2716 moved product src (the BOM and NUL guard plus "
    "its six-criteria suite) and one registry row. Five readings at open: git "
    "status EMPTY at HEAD fbd34c92 equal to origin/main with no index.lock; ZERO "
    "@BigDomain rows new in the group ledger; the content-addressed decisions face "
    "read no new token; the group orders tail is the 2026-11-14 01:3x BigStream "
    "seat row already carried as knowledge-only; benchmarks_refreshed 2026-11-14 "
    "inside the seven-day gate. The target was RE-MEASURED BY IMPORT at 669 suites "
    "/ 4990 criteria / 669 unique names / 669 unique paths, byte for byte the "
    "pre-registered tuple, and a process-table scan matched NOTHING for "
    "battery_stream or reconcile_all before the launch.",
    "R2717 THE LEG RAN ON THE COMMITTED TREE AND WAS ADOPTED BY ITS EVIDENCE PATH, "
    "never relaunched: src/os/launch_battery_R2717.py pins the target and refuses "
    "on a moved registry, a non-unique name or path, an existing evidence path or a "
    "live pid read through ctypes OpenProcess plus WaitForSingleObject, then starts "
    "src/os/battery_stream.py detached with the stream and the pid in SEPARATE files "
    "under logs/ (battery-R2717.stream, battery-R2717.pid, pid 54604) so "
    "qa/reconcile-all-R2717.log is written by the shipped single utf-8 LF writer "
    "alone. The guard was NEGATIVE-CONTROLLED in the same window: a second run read "
    "E_LAUNCH_PID_EXISTS pid=54604 at rc=2, so a leg cannot be double-fired over the "
    "file it is already writing. Progress was read at bounded intervals rather than "
    "quoted - 4 PASS rows at open+70s, 111 at about 13 minutes, 329, 430, 648, 655, "
    "666 and finally the closing line - with ZERO FAIL suite rows at every reading.",
    "R2717 THE GREEN WAS MEASURED ON BYTES, not taken from the stream: "
    "qa/reconcile-all-R2717.log reads 1203070B, utf-8, bom=False, crlf=0, lone_cr=0, "
    "nul=0, 9822 lines, 669 rows beginning PASS suite carrying 669 UNIQUE names with "
    "ZERO duplicates, ZERO rows beginning FAIL suite, ZERO rows whose exit is "
    "non-zero and ZERO rows without a criteria field, and an INDEPENDENT recount "
    "over their declared criteria summing to EXACTLY 4990, byte for byte the number "
    "the debt row pre-registered at 669/4990. The stream closes on 'RUNNER PASS "
    "(669/669 suites green, reconcile controls 7/7, 3841.0s)' and 'BATTERY rc=0 "
    "3841.1s'.",
    "R2717 DESIGNED ORDER EXECUTED AND THE FIRST MEASUREMENT WAS THE DESIGNED FAIL: "
    "battery_followup --dry-run read SECTION matrix FAIL on-disk 70768B against "
    "regenerated 70765B with NO byte written, because the document still stamped the "
    "R2715b leg. suite_matrix_reconcile was then stamped from THIS window own green "
    "leg (--write --evidence qa/reconcile-all-R2717.log) to 70765 bytes at 669 rows "
    "and --check read DOC-CURRENT, after which the four pinned sections read matrix "
    "PASS byte-identical 70765B, fingerprint CLEAN domains=5, profile byte-identical "
    "PASS and census DRIFT-CLEAN for VERDICT reconcile-battery-R2716 PASS "
    "failing=none (APPENDED 1987B, eol_ok=True).",
    "R2717 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: reconcile-battery-R2716 was "
    "closed at its predicted and measured 227544B -> 227547B (line 423, open 47->46, "
    "done 358->359, readback ok) and one product row was appended first=yes at "
    "227547B -> 228105B naming queue head state/queue/tech.md line 692 prefix "
    "AC-ETAIL1 with claimable 13 and criteria AC-ETAIL1..AC-ETAIL6 pinned there at "
    "R2716 BEFORE any code; debt_gate --check now reads CLAIM-FIRST "
    "item=product-face-R2717 first=1. NO successor battery is owed because this "
    "window moved no product src byte, no registry row and no code: the registry is "
    "unmoved at 669 suites / 4990 criteria and the only bytes it added are the "
    "restamped matrix, the QA evidence and this file.",
    "R2717 honest disclosures: (a) ZERO product points - a green 669-suite battery, "
    "a restamped matrix and a closed debt row are evidence, not something a CEO can "
    "newly open, and every P-47 business face still waits on CEO physical pieces "
    "(merchant id, mini-program appid/secret); (b) this round ran about 75 minutes "
    "past its 25 minute budget on purpose: a full leg measures 3841 seconds here and "
    "adopting it by measurement, restamping, appending a verdict and closing debt is "
    "the whole face; (c) the leg was launched on the committed tree 54604 and adopted "
    "by evidence path, and the duplicate-leg mistake of R2708/R2709 was NOT repeated; "
    "(d) the earlier live counter read 670 PASS-looking rows once while the file "
    "carried 669, a stream-versus-file counting artefact that the byte measurement "
    "settled rather than guessed; (e) tasks.md was not touched, it is the P-47 "
    "canonical board; (f) Docker is absent on this host; (g) BigDomain-OSLoop still "
    "reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile).",
    "R2717 tokens: local=~7k api=0 api_reason=verification adoption window - one "
    "five-silence scan with the debt gate and the queue face, one registry "
    "measurement by import on four axes, one evidence-path and one process-table "
    "occupancy check, one launcher written and fired and negative-controlled, about "
    "eleven bounded progress readings across a 3841-second leg, one byte measurement "
    "with an independent criteria recount of 4990, one designed matrix FAIL then one "
    "stamp-aligned regeneration checked DOC-CURRENT, one four-section verdict append, "
    "one debt close and one debt append with readback, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES
    expected["tick"] = tick + 1

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    bumped = []
    old_tick = '"tick": %d' % tick
    new_tick = '"tick": %d' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip().rstrip(",") == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + inserted + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2717_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d" %
          (tick + 1, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
