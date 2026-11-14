"""R2722 verification closeout: adopted leg, verdict, debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2722 VERIFICATION ADOPTION window that closed "
    "reconcile-battery-R2720 at its pre-registered 671 suites / 5002 criteria: the leg "
    "was launched at R2721 own launch window as pid 55868 on the committed tree "
    "691f66e8 and was ADOPTED by its evidence path qa/reconcile-all-R2721.log, never "
    "relaunched. Five readings at open: git status carried ONE untracked item (the "
    "evidence file the leg itself wrote) at HEAD a2b37732 equal to origin/main with no "
    "index.lock; ZERO @BigDomain rows new in the group ledger; the content-addressed "
    "decisions face read rows=120 tokens=64 new=0; the group orders tail is the "
    "2026-11-14 01:3x BigStream seat row already carried as knowledge-only; "
    "benchmarks_refreshed 2026-11-14 inside the seven-day gate. The leg had already "
    "closed before this window opened, so nothing was waited on and nothing was "
    "re-fired.",
    "R2722 THE GREEN WAS MEASURED ON BYTES: qa/reconcile-all-R2721.log reads 1211206B, "
    "utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 9931 lines, 671 rows beginning PASS "
    "suite carrying 671 UNIQUE names with ZERO duplicates, ZERO rows beginning FAIL "
    "suite, ZERO rows whose exit is non-zero, and an INDEPENDENT recount over their "
    "declared criteria summing to EXACTLY 5002, byte for byte the pre-registered "
    "target; the summary row reads PASS suites 671/671 green, expected criteria "
    "total=5002, suite cap=600s overrides=1, and the stream closes on RUNNER PASS "
    "(671/671 suites green, reconcile controls 7/7, 3961.6s) and BATTERY rc=0 3961.8s "
    "with TMP RECLAIM removed=697 reclaimed=241.16 MiB.",
    "R2722 DESIGNED ORDER EXECUTED AND THE FIRST MEASUREMENT WAS THE DESIGNED FAIL: "
    "battery_followup --dry-run read SECTION matrix FAIL on-disk 70985B against "
    "regenerated 70984B with NO byte written, because the document still stamped the "
    "R2719 leg. suite_matrix_reconcile was then stamped from THIS window own green leg "
    "(--write --evidence qa/reconcile-all-R2721.log) to 70984 bytes at 671 rows and "
    "--check read DOC-CURRENT, after which the four pinned sections read matrix PASS "
    "byte-identical 70984B, fingerprint CLEAN domains=5, profile byte-identical PASS and "
    "census DRIFT-CLEAN for VERDICT reconcile-battery-R2720 PASS failing=none "
    "(APPENDED 1987B, eol_ok=True).",
    "R2722 DEBT THROUGH THE SHIPPED WRITERS: reconcile-battery-R2720 was closed at its "
    "predicted and measured 230744B -> 230747B (line 429, open 49->48, done 362->363, "
    "readback ok) and one product row was appended first=yes at 230747B -> 231233B "
    "naming queue head state/queue/tech.md:694 prefix AC-ECORD1 with claimable 13 and "
    "criteria AC-ECORD1..AC-ECORD6 pinned there at R2720 BEFORE any code; debt_gate "
    "--check now reads CLAIM-FIRST item=product-face-R2722 first=1. queue_head reads "
    "line=694 prefix=AC-ECORD1 claimable=13 skipped_before=7 and queue_floor reads "
    "FLOOR-MET 5/5 13/10 10/10. NO successor battery is owed because this window moved "
    "no product src byte, no registry row and no code: the registry is unmoved at 671 "
    "suites / 5002 criteria and the only bytes it added are the restamped matrix, the QA "
    "evidence and this file.",
    "R2722 honest disclosures: (a) ZERO product points - a green 671-suite battery, a "
    "restamped matrix and a closed debt row are evidence, not something a CEO can newly "
    "open, and every P-47 business face still waits on CEO physical pieces (merchant id, "
    "mini-program appid/secret); (b) this window ran inside a short budget because the "
    "leg had already finished, measured 3961.6s and closed before open; (c) the R2721 "
    "launch window left NO write-sensitive receipt line, so the R2614 discipline was "
    "OWED and this window ran the same fifteen suites individually on its own closeout "
    "tree, appending that receipt as its own line; (d) tasks.md was not touched, it is "
    "the P-47 canonical board; (e) Docker is absent on this host; (f) BigDomain-OSLoop "
    "still reads InteractiveToken and needs an ELEVATED shell for its S4U "
    "re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2722 tokens: local=~8k api=0 api_reason=verification adoption window - one "
    "five-silence scan with the debt gate, the queue head and queue floor, one "
    "byte-level measurement with an independent criteria recount of 5002, one designed "
    "matrix FAIL then one stamp-aligned regeneration checked DOC-CURRENT, one "
    "four-section verdict append, one debt close and one debt append with readback, one "
    "write-sensitive receipt over fifteen suites, and the state/export/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2722v_")
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
