"""R2701 product window closeout: measured log lines and one tick.

Every number typed here was measured in this window rather than copied.
The decisions baseline is left alone because the scan read new=0.
"""

import io  # noqa: F401
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-13 R2701 PRODUCT window on the queue head the debt gate named "
    "(product-face-R2700, state/queue/tech.md line 683 prefix AC-PNAR1, "
    "criteria AC-PNAR1..AC-PNAR6 pinned in that row at R2698 BEFORE any code). "
    "Five readings at open: git status EMPTY at HEAD d5883aad equal to "
    "origin/main with no index.lock; ZERO @BigDomain rows in the group ledger "
    "(atbd_lines=0, unreplied_groups=0); the content-addressed decisions face "
    "read rows=120 tokens=64 new=0 against the stored union baseline; the "
    "group orders tail max timestamp is still 2026-11-12 12:45, the bm-a "
    "station ONBOARD row already carried as last_order and judged "
    "knowledge-only for this company; benchmarks_refreshed 2026-11-13 inside "
    "the seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2700 "
    "opened=R2700 open=45 first=1, queue_head read tech line=683 "
    "prefix=AC-PNAR1 claimable=14, queue_floor --check read FLOOR-MET 5/5, "
    "14/10, 10/10, state_fold --check read FOLD-CLEAR at 61687B against the "
    "78500B gate with margin 16813 and 53 live log lines, and ledger_lines "
    "--check read VERDICT CLEAN; the QA face already carried today own "
    "smoke-R2698.log and smoke-R2698.png, so no charter crawl was owed.",

    "R2701 THE LIMIT WAS MEASURED BEFORE ANY BYTE AND ONE EARLIER NOTE IS "
    "CORRECTED RATHER THAN REPEATED: on the shipped R2698 face "
    "read_word('dialect:1') answered dialect '1' with body 'dialect:1' and "
    "refused None (the marker read back as its own body), "
    "read_word('dialect:1+') answered body '' and refused None, and both "
    "read_word('dialect:1+duplicate:2') and read_word('dialect:1+garbage') "
    "were accepted as legal tag-1 words. The R2698 seed row said this face "
    "never publishes a bare 'duplicate:2' body; MEASURED NOW THAT SENTENCE IS "
    "WRONG - ack_unnameable(['a','a']) publishes exactly "
    "'dialect:1+duplicate:2' - so the shape rule keeps that word LEGAL "
    "instead of refusing it, and the correction is written into the closed "
    "queue row rather than left standing as a claim.",

    "R2701 SHIPPED src/os/probe_seam_dialect_shape_guard_scope.py plus its "
    "six-criteria suite. ONE rule now sits behind the tag guard: a MARKED word "
    "whose body is absent (no-body), empty (empty-body), over two parts "
    "(part-count), or outside the three shapes this face publishes - "
    "'strict-prefix-of:<siblings>', a counted 'duplicate:<n>' with n >= 2, or "
    "that pair in order - is REFUSED naming the shape found (not-published "
    "with the head token, duplicate-not-counted with the integer text, "
    "siblings-empty with none/empty-sibling, part-order with the head that "
    "moved), and a refusal reports dialect None, body None, siblings None and "
    "duplicate None so it can never be mistaken for a tag-1 reading; every "
    "marker-less legacy word is untouched by the shape rule, so a bare "
    "'duplicate:2' stays legal. PROOF measured not quoted: AC-PNAR1..AC-PNAR6 "
    "SUITE PASS 6/6 TWICE byte-identical through the shipped capture callable "
    "(qa/shape-guard-R2701.log, 26280B, legs=2 identical=True, adjacent=1 both "
    "SUITE PASS, fails=0, verdict CAPTURED), with one bounded live leg "
    "reading 5 real modules on BOTH readers. NO OWN DEFECT WAS SMOOTHED: the "
    "first suite run read 5/6 because the R2685 riding face was compared over "
    "the full ten-fixture set instead of the six fixtures that predate "
    "par-on-joiner escaping; the criterion was repaired at its birth site in "
    "the suite (R2689 face over all ten, R2685 face over the six it can "
    "read) and the suite then read 6/6.",

    "R2701 REGISTRY, MATRIX, BOARD AND DEBT THROUGH THEIR SHIPPED FACES: the "
    "registry moved by exactly ONE row recounted BY IMPORT to 663 suites / "
    "4954 criteria with 663 unique names and 663 unique paths, byte for byte "
    "the number its own registry comment pre-registered; "
    "docs/sandbox-suite-matrix.md read ROWS-MISMATCH before any byte (doc 662 "
    "rows against registry 663) and was regenerated stamp-aligned from the "
    "last full green leg qa/reconcile-all-R2699.log to 70086 bytes at 663 "
    "rows with its green line honestly reading 662/662, after which --check "
    "read DOC-CURRENT at rc=0. Queue row 683 was closed through a one-off "
    "writer at its predicted and measured 1965563B -> 1968531B (lines 703 -> "
    "704, readback ok) and ONE row was seeded from this window own MEASURED "
    "limit as AC-PNAS1..AC-PNAS6: the shape is now validated but not the "
    "CANONICAL FORM, so read_word('dialect:1+duplicate:02') reads duplicate 2 "
    "exactly as 'dialect:1+duplicate:2' does and "
    "read_word('dialect:1+strict-prefix-of:ab,ab') reads siblings ['ab','ab'] "
    "- two shapes the publishing face never emits. queue_head now reads tech "
    "line=684 prefix=AC-PNAS1 claimable=14 and queue_floor reads FLOOR-MET "
    "with tech done 498 -> 499. product-face-R2700 was closed at its "
    "predicted and measured 220448B -> 220451B (line 410, open 45->44, done "
    "347->348, readback ok) and reconcile-battery-R2701 was appended "
    "first=yes at 220451B -> 221021B naming 663 suites / 4954 criteria, "
    "because this window moved product src bytes, one registry row, one "
    "document and one queue row and the R2168 mixed-tree rule puts the full "
    "battery on the committed tree BEFORE any further product byte; debt_gate "
    "now reads CLAIM-FIRST item=reconcile-battery-R2701.",

    "R2701 honest disclosures: (a) TWO product points on the Executive "
    "Protocol scale - a runnable face with its own six-criteria suite a "
    "maintainer can rerun, proved twice byte-identically - but nothing a CEO "
    "could newly open and no P-47 business surface moved, so every P-47 item "
    "still waits on CEO physical pieces (merchant id, mini-program "
    "appid/secret); (b) the shape guard validates the SHAPE only, not the "
    "canonical form or the sibling semantics, and both measured holes are "
    "seeded as AC-PNAS1..AC-PNAS6 rather than claimed as closed; (c) the "
    "matrix green line honestly reads 662/662 because the leg it is stamped "
    "from predates this window own suite, and the battery owed for that is "
    "reconcile-battery-R2701; (d) the one-off measure, evidence, queue and "
    "recount scripts in tmp/ are DELETED before the commit rather than "
    "staged; (e) Docker is absent on this host; (f) tasks.md was not touched, "
    "it is the P-47 canonical board; (g) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an ELEVATED shell for its S4U "
    "re-registration (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2701 tokens: local=~12k api=0 api_reason=product window - one "
    "five-silence scan with the content-addressed decisions face, the group "
    "orders tail and the ledger face read, one debt gate read, one queue head "
    "plus one queue floor plus one fold gate plus one ledger gate read, two "
    "measurement scripts run on the shipped R2698 face BEFORE any code (six "
    "shapes, four label sets, then four canonical-form shapes), one face "
    "module plus one six-criteria suite written and registered as exactly one "
    "row, one own fixture-binding defect repaired at its birth site, two "
    "byte-identical evidence legs through the shipped capture callable with "
    "one adjacent suite, one registry recount by import on four axes, one "
    "designed matrix regeneration checked DOC-CURRENT, thirteen adjacent "
    "suites re-run green, one queue row closed and one seeded through their "
    "writer, two debt rows moved through their shipped writers, and the "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2701_")
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
