"""R2704 product window closeout: measured log lines and one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-13 R2704 PRODUCT window on the queue head the debt gate named "
    "(product-face-R2703, state/queue/tech.md:684 prefix AC-PNAS1, criteria "
    "AC-PNAS1..AC-PNAS6 pinned in that row at R2701 BEFORE any code). Five "
    "readings at open, all clean: git status EMPTY at HEAD ec2a65f8 equal to "
    "origin/main with no index.lock; ZERO @BigDomain rows in the group ledger "
    "(atbd_lines=0, unreplied_groups=0); the content-addressed decisions face read "
    "rows=120 tokens=64 new=0 against the stored union baseline; the group orders "
    "tail max timestamp is still 2026-11-12 12:45, the bm-a station ONBOARD row "
    "already carried as last_order and judged knowledge-only for this company; "
    "benchmarks_refreshed 2026-11-13 inside the seven-day gate. debt_gate read "
    "CLAIM-FIRST item=product-face-R2703 opened=R2703 first=1 open=45, queue_head "
    "read tech line=684 prefix=AC-PNAS1 claimable=14, queue_floor read FLOOR-MET "
    "5/5, 14/10, 10/10, state_fold --check read FOLD-CLEAR at 49175B against the "
    "78500B gate with margin 29325 and 40 live log lines, ledger_lines --check read "
    "VERDICT CLEAN, state_io --check read CANON-CLEAN.",

    "R2704 FOUR MEASUREMENTS ON THE R2701 FACE BEFORE ANY BYTE, and one of them "
    "narrows the queue note rather than repeating it: read_word('dialect:1+duplicate:02') "
    "returned dialect '1' with duplicate 2 and refused None - byte for byte the "
    "reading of the canonical 'duplicate:2' although the publishing face only ever "
    "writes the canonical integer; read_word('dialect:1+strict-prefix-of:ab,ab') "
    "returned siblings ['ab','ab'] with refused None, a repeated list the publishing "
    "face never emits (ack_unnameable(['a','ab','ab']) publishes 'strict-prefix-of:ab' "
    "and 'duplicate:2'); the sign ('duplicate:+2') and whitespace ('duplicate: 2') "
    "forms the row named were MEASURED to be already refused as duplicate-not-counted "
    "by the R2701 shape rule, so the honestly uncovered forms are the leading zero and "
    "the non-ASCII digit (the Arabic-Indic two, isdigit() True and int() 2); and a "
    "FOURTH measurement found a CRASH rather than a refusal, because a superscript two "
    "after 'duplicate:' is isdigit() True and int() raises ValueError, so the shipped "
    "R2701 face raised where it owed a refusal.",

    "R2704 SHIPPED src/os/probe_seam_dialect_canonical_guard_scope.py plus its "
    "six-criteria suite, and repaired BOTH int() reaches of that defect family at "
    "their birth sites (probe_seam_dialect_shape_guard_scope.duplicate_count_of_part "
    "and probe_seam_unnameable_part_joiner_escaped_scope.parse_duplicate_from_word now "
    "reach int() only after a form it can read). The new face keeps every R2685, "
    "R2689, R2692, R2698 and R2701 reading and adds ONE rule behind the shape guard: a "
    "marked word whose counted duplicate is written non-canonically (leading zero, "
    "non-ASCII digit) and a sibling list naming one label twice are REFUSED naming the "
    "form found, with dialect, body, siblings and duplicate all reported None so a "
    "refusal can never be mistaken for a reading, while a marker-less legacy word is "
    "untouched. PROOF: AC-PNAS1..AC-PNAS6 SUITE PASS 6/6 TWICE byte-identical through "
    "the shipped capture callable (qa/canonical-guard-R2704.log, 471564B, digest "
    "308E0DFB3D65F0FF, legs=2 identical=True, fails=0, verdict CAPTURED) with both "
    "parent suites green adjacently (shape guard 6/6, legacy joiner parser 6/6); the "
    "registry was recounted BY IMPORT at 664 suites / 4960 criteria with 664 unique "
    "names and 664 unique paths, exactly the pre-declared 663 -> 664 / 4954 -> 4960.",

    "R2704 DESIGNED ORDER AND HONEST NUMBERS: suite_matrix_reconcile --check read "
    "ROWS-MISMATCH doc-rows=663 registry-rows=664 (4960 criteria) before any write, "
    "then the document was regenerated with --write --evidence "
    "qa/reconcile-all-R2702.log to 70210 bytes at 664 rows and --check read "
    "DOC-CURRENT at rc=0 - and the stamp line honestly still claims the R2702 leg "
    "green 663/663, because the suite this window adds has no battery row yet, so the "
    "matrix says 664 rows with 663 evidence-green rather than claiming a green it "
    "does not have. The real export was re-derived through the shipped driver "
    "src/os/export_R2635.py to 406700B at tick 2695 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 VERDICT "
    "PASS with the three CEO-visible lines derived rather than typed.",

    "R2704 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: product-face-R2703 was closed "
    "at its predicted and measured 221641B -> 221644B (line 412, open 45->44, done "
    "349->350, readback ok) and reconcile-battery-R2704 was appended first=yes at "
    "221644B -> 222261B, because this window moved product src bytes (the new face and "
    "its suite), repaired two shipped modules, added one registry row, one matrix row "
    "and one queue row, so the R2168 mixed-tree rule puts a FULL BATTERY at the "
    "re-measured 664 suites / 4960 criteria on the committed tree BEFORE any further "
    "product byte. Board row 684 was closed at its predicted and measured 1968531B -> "
    "1971435B (LF only, crlf=0, readback verified) and AC-PNAT1..AC-PNAT6 were seeded "
    "at line 685 from this window own measured limit: an escape the publishing face "
    "cannot emit is accepted, because read_word('dialect:1+strict-prefix-of:a\\bc') "
    "answers siblings ['abc'] exactly as 'strict-prefix-of:abc' does. Queue head is "
    "now tech line=685 prefix=AC-PNAT1 with claimable 14 and queue_floor reads "
    "FLOOR-MET 5/5, 14/10, 10/10.",

    "R2704 honest disclosures: (a) ONE product point - a dev-face reading with a "
    "green suite is real and runnable, but nothing a CEO can newly open, and every "
    "P-47 business face still waits on CEO physical pieces (merchant id, "
    "mini-program appid/secret); (b) the queue note was NARROWED by measurement "
    "rather than honoured verbatim, since two of the three forms it named were already "
    "refused; (c) this window touched TWO shipped modules to repair a measured crash, "
    "which is why a full battery is owed rather than a light re-check; (d) the matrix "
    "carries 664 rows with 663 evidence-green and says so; (e) the one-off queue "
    "editor in tmp/ is DELETED before the commit rather than staged; (f) Docker is "
    "absent on this host; (g) tasks.md was not touched, it is the P-47 canonical "
    "board; (h) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED "
    "shell for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",

    "R2704 tokens: local=~7k api=0 api_reason=product window - one five-silence scan "
    "with the content-addressed decisions face, the group orders tail and the ledger "
    "face read, one debt gate read, one queue head plus one queue floor plus one fold "
    "gate plus one ledger gate plus one state IO read, four defect measurements on the "
    "shipped face before any code (two counts, two siblings, one crash), one suite "
    "written and run green twice through the shipped capture callable, two parent "
    "suites re-run adjacent, one registry row added and recounted by import on four "
    "axes, one designed matrix mismatch then one regenerate checked DOC-CURRENT, one "
    "real export and one consistency check, one debt close and one debt append with "
    "readback, one queue row closed and one seeded with a verified readback, and the "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2704_")
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
