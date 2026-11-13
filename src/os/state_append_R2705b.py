"""R2705 adoption closeout: the green leg, the verdict and one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2705 THE LEG WAS ADOPTED BY ITS EVIDENCE PATH AND MEASURED, NEVER "
    "RELAUNCHED: no battery_stream and no reconcile_all process survived by "
    "command line before any byte was read; qa/reconcile-all-R2705.log measured "
    "1406487B at adoption - utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 10852 "
    "lines - carrying 664 suite rows with 664 UNIQUE names, ZERO FAIL rows, ZERO "
    "non-zero exits and ZERO rows without a criteria field, and an INDEPENDENT "
    "recount over their declared criteria summing to EXACTLY 4960, byte for byte "
    "the number the debt row pre-registered at 664/4960; the stream closed on "
    "'RUNNER PASS (664/664 suites green, reconcile controls 7/7, 3161.8s)' and "
    "'BATTERY rc=0 3162.2s'. The designed FAIL-first step was measured BEFORE any "
    "write: suite_matrix_reconcile --check read EVIDENCE-FACE "
    "recorded-evidence=qa/reconcile-all-R2702.log named-evidence="
    "qa/reconcile-all-R2705.log at registry-rows=664 (4960 criteria) with the "
    "stamp still claiming the R2702 leg green 663/663, then the document was "
    "regenerated STAMP-ALIGNED from THIS round own green leg to 70199 bytes at "
    "664 rows and --check read DOC-CURRENT at rc=0 measured through subprocess.",
    "R2705 FOLLOWUP AND THE R2614 DISCIPLINE HONOURED: battery_followup ran the "
    "four pinned sections in the designed order - matrix PASS byte-identical "
    "70199B, fingerprint CLEAN domains=5, profile byte-identical, census "
    "DRIFT-CLEAN - for VERDICT battery-R2705 PASS failing=none (APPENDED 1967B, "
    "eol_ok=True to 1408454B). The leg window was 21:14:59..22:07:41 and TWO "
    "commits landed under it - 4b6e48d1 (launch receipt) and f784ff27 (the "
    "adopted green leg, restamped matrix, evidence) - so the write-sensitive set "
    "was re-run INDIVIDUALLY on the final committed tree over fifteen suites "
    "through the shipped run_cmd and registry lookup: RERUN PASS green=15 red=0 "
    "with every suite printing rc=0 and zero FAIL lines (qa/"
    "write-sensitive-R2705.log, 14067B, header naming the leg window and both "
    "commits).",
    "R2705 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: reconcile-battery-R2704 "
    "was closed at its predicted and measured 222261B -> 222264B (line 413, open "
    "45->44, done 350->351, readback ok) and product-face-R2705 was appended "
    "first=yes at 222264B -> 222834B naming queue head state/queue/tech.md line "
    "685 prefix AC-PNAT1 with claimable 14, so the debt gate now reads CLAIM-FIRST "
    "item=product-face-R2705. NO successor battery is owed because this window "
    "moved no product src byte, no registry row and no code: the registry is "
    "unmoved at 664 suites / 4960 criteria and the only src bytes it added are "
    "the launcher and the two state appenders. Queue head and queue floor are "
    "unchanged (tech line 685 AC-PNAT1 claimable 14; FLOOR-MET 5/5, 14/10, 10/10) "
    "and tasks.md was not touched because it is the P-47 canonical board.",
    "R2705 honest disclosures: (a) ZERO product points - a green battery, a "
    "restamped matrix and a fifteen-suite write-sensitive pass are evidence, not "
    "something a CEO can newly open, and every P-47 business face still waits on "
    "CEO physical pieces (merchant id, mini-program appid/secret); (b) the leg "
    "needed 52 minutes of wall clock and this window held it to adoption instead "
    "of deferring, which is why the round ran far past its 25 minute budget - "
    "the alternative was leaving a green leg unadopted and the debt open; (c) the "
    "double fire I caused earlier in the window is disclosed in the launch line "
    "and cost four minutes, with no evidence ever written by the killed legs; (d) "
    "this closeout changes only docs/status-export.json, the debt register, this "
    "file, heartbeat.txt and qa/, so no product src byte moved; (e) the one-off "
    "write-sensitive runner in tmp/ and the matrix/evidence commits were staged "
    "deliberately and the runner is DELETED before this commit rather than "
    "staged; (f) Docker is absent on this host; (g) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile).",
    "R2705 tokens: local=~8k api=0 api_reason=verification adoption window - one "
    "five-silence scan, one debt gate read, one queue head plus one queue floor "
    "plus one fold gate plus one ledger gate plus one state IO read, one registry "
    "re-measure by import, one launcher written and fired, one mistaken double "
    "fire found by process listing and cleaned with a zero-survivor check, one "
    "guard repair with a proved negative control, one single relaunch, about "
    "twenty bounded progress polls across the leg, one process-liveness read and "
    "one evidence measurement with an independent criteria recount, one designed "
    "matrix FAIL-first then one stamp-aligned regeneration, one four-section "
    "followup, one fifteen-suite write-sensitive re-run on the final committed "
    "tree, one debt close and one debt append with readback, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
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
    old_tick = '"tick": %d,' % tick
    new_tick = '"tick": %d,' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip() == old_tick and not seen:
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2705b_")
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
