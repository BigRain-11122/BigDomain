"""R2692 product window closeout: measured log lines plus one tick.

Every number typed here was measured in this window rather than copied from
the register: five-silence readings, debt gate, queue head and floor, the
fold gate, the registry recounted by import, the evidence bytes and digest,
the matrix byte count, and the board and debt writers own printed deltas.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "2026-11-13 R2692 PRODUCT window on the queue head the debt gate "
        "named (product-face-R2691, state/queue/tech.md line 681 prefix "
        "AC-PNAP1, criteria AC-PNAP1..AC-PNAP6 pinned in that row at R2689 "
        "BEFORE any code). Five readings at open, all clean: git status EMPTY "
        "at HEAD 873fab8f with no index.lock; ZERO @BigDomain rows in the "
        "group ledger (atbd_lines=0); the content-addressed decisions scan "
        "read tokens=66 against the stored 256-token union baseline with "
        "new=0; the group orders tail max timestamp is still 2026-11-12 12:45, "
        "the bm-a station ONBOARD row already carried as last_order and "
        "judged knowledge-only for this company; benchmarks_refreshed "
        "2026-11-10 sitting three days inside the seven-day gate. debt_gate "
        "read CLAIM-FIRST item=product-face-R2691 opened=R2691 carried=1 "
        "stale=no open=45 first=1, queue_head read tech line=681 prefix "
        "AC-PNAP1 claimable=14, queue_floor read FLOOR-MET 5/5, 14/10, 10/10, "
        "state_fold --check read FOLD-CLEAR at 74399B against the 78500B gate "
        "with margin 4101 and 68 live log lines, and ledger_lines --check "
        "read VERDICT CLEAN with new_missing none and new_orphan none.",

        "2026-11-13 R2692 THE MISSING PEDIGREE WAS MEASURED BEFORE ANY BYTE "
        "through tmp/limits_dialect_marker_R2692.py against the SHIPPED R2685 "
        "and R2689 faces: R2685 published the SAME string "
        "`strict-prefix-of:ab+duplicate:2` for the one-label shape "
        "['a','ab+duplicate:2'] AND for the genuine sibling-plus-copy shape "
        "['a','ab','a'] (SAME_STRING=True measured), and R2689 read that one "
        "legacy string as {'siblings': ['ab'], 'duplicate': 2} - the tail lost "
        "at the legacy publisher - while its own word for the one-label shape "
        "is `strict-prefix-of:ab\\\\+duplicate:2`. Neither publisher stamps "
        "which dialect produced a word, so a consumer holding a pre-R2689 "
        "string cannot tell what was meant; the measured marker probe read "
        "`any marker part present? legacy=False current=False`.",

        "2026-11-13 R2692 SHIPPED src/os/probe_seam_unnameable_dialect_marker_"
        "scope.py plus its six-criteria suite. Every word this face publishes "
        "carries `dialect:1` as its FIRST part and the marker is READ BACK "
        "from the bytes rather than assumed: `read_word` reports dialect 1 "
        "for `dialect:1+strict-prefix-of:ab\\\\+duplicate:2` (one label) and "
        "`dialect:1+strict-prefix-of:ab+duplicate:2` (genuine sibling plus "
        "copy), so the two words are now distinct AND each names its "
        "publisher; `read_word('strict-prefix-of:ab+duplicate:2')` reports "
        "dialect None with exactly the readings R2689 gave; a marker appended "
        "to the TAIL reports None, so pedigree cannot be claimed by adding "
        "one; `strip_marker` hands a legacy word back byte for byte. PROOF "
        "measured not quoted: AC-PNAP1..AC-PNAP6 SUITE PASS 6/6 TWICE "
        "byte-identical through the shipped capture callable "
        "(qa/prefix-dialect-marker-R2692.log, 17649B, digest 21708D12384D9072, "
        "legs=2 identical=True, adjacent=2 both SUITE PASS 6/6, fails=0, "
        "verdict CAPTURED) with one bounded live leg reading 5 real modules / "
        "68 loops read-only that measures the SAME fixture on BOTH readers. "
        "REGISTRY 660 suites / 4936 criteria -> 661 / 4942 by exactly one row "
        "recounted by import (661 unique names); docs/sandbox-suite-matrix.md "
        "read FAIL stale BEFORE any byte with the evidence FACE agreeing "
        "(doc-recorded and check-resolved both qa/reconcile-all-R2690.log, so "
        "the drift was content, not a face mismatch) and was regenerated "
        "stamp-aligned to 69834 bytes at 661 suites / 4942 criteria with its "
        "green line honestly reading 660/661, after which --check read "
        "byte-identical.",

        "R2692 BOARD AND DEBT THROUGH THE SHIPPED WRITERS: row 681 was closed "
        "through src/os/queue_close_R2692.py at its predicted and measured "
        "1958624B -> 1962130B (lines 701 -> 702, readback ok) and ONE row was "
        "seeded from this window own MEASURED limit as AC-PNAQ1..AC-PNAQ6 - "
        "the marker names the DIALECT but nothing validates the tag, so "
        "`read_word('dialect:2+strict-prefix-of:ab')` reports dialect None and "
        "the whole body verbatim, i.e. a FUTURE dialect is silently mis-typed "
        "as a legacy word instead of being refused, and "
        "`read_word('dialect:1+dialect:1+strict-prefix-of:ab')` reports "
        "dialect 1 with markers=2, a string this face would never publish. "
        "queue_head now reads tech line=682 prefix AC-PNAQ1 claimable=14 with "
        "queue_floor FLOOR-MET 5/5, 14/10, 10/10. DEBT: product-face-R2691 was "
        "closed at its predicted and measured 218533B -> 218536B (line 406, "
        "open 45->44, done 343->344, readback ok) and reconcile-battery-R2692 "
        "was appended first=yes at 218536B -> 218815B naming 661 suites / 4942 "
        "criteria, because this window moved product src bytes, one registry "
        "row and one document and the R2168 mixed-tree rule puts the full "
        "battery on the committed tree BEFORE any further product byte.",

        "R2692 honest disclosures: (a) TWO product points on the Executive "
        "Protocol scale - a runnable face with its own six-criteria suite a "
        "maintainer can rerun, proved on both readers - but nothing a CEO "
        "could newly open and no P-47 business surface moved, so every P-47 "
        "item still waits on CEO physical pieces (merchant id, mini-program "
        "appid/secret); (b) the marker proves which DIALECT wrote a word, not "
        "which label set, and an unknown tag or a doubled marker is still "
        "read without refusal - that is MEASURED above and is the seeded "
        "successor, not a claim of closure; (c) residue_triage --check "
        "--round R2692 reads RESIDUE with residue=1 untriaged=1 unmatched=1 "
        "expired=1, which are the INHERITED R2165 (STAMP-ONLY-OPEN, expired "
        "until R2660) and R2653 (UNMATCHED) entries carried rather than "
        "triaged this window; (d) the one-off scan, limits, register and "
        "evidence scripts in tmp/ are DELETED before the commit rather than "
        "staged; (e) Docker is absent on this host; (f) tasks.md was not "
        "touched, it is the P-47 canonical board; (g) BigDomain-OSLoop still "
        "reads InteractiveToken and needs an ELEVATED shell for its S4U "
        "re-registration (carried ceo-pending physical item loop-s4u-"
        "reconcile).",

        "R2692 tokens: local=~13k api=0 api_reason=product window - one "
        "five-silence scan with the content-addressed decisions face, the "
        "group orders tail and the ledger face read, one debt gate read, one "
        "queue head plus one queue floor plus one fold gate plus one ledger "
        "gate read, one limits script measuring the missing pedigree BEFORE "
        "any code on both shipped faces, one face module plus one six-criteria "
        "suite written and registered as exactly one row, two byte-identical "
        "evidence legs through the shipped capture callable with two adjacent "
        "suites, one registry recount by import, one designed matrix FAIL then "
        "one stamp-aligned regeneration checked byte-identical, one board row "
        "closed and one seeded through their shipped writer, two debt rows "
        "moved through their shipped writers, and the state/export/heartbeat "
        "closeout; zero cloud calls and zero external API touches",
    ]

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + lines
    expected["tick"] = tick + 1
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2692_")
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
