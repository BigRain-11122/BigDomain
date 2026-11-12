"""R2671 product face: the seventh wave of the composed/landed BOM precedence.

Two lines are appended - the product face and its tokens ledger - and the tick
is advanced by exactly one. The numbers in the face line were measured at run
time (evidence bytes, registry counts by import, matrix bytes) rather than
typed.
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
ROOT = os.path.dirname(os.path.dirname(HERE))
EVIDENCE = os.path.join(ROOT, "qa",
                        "export-composed-landed-seventh-wave-R2671.log")
MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    ev = len(io.open(EVIDENCE, "rb").read())
    matrix = len(io.open(MATRIX, "rb").read())
    lines = [
        "R2671 PRODUCT window on the queue head the register named "
        "(state/queue/tech.md:666 prefix AC-EDXC1, criteria pinned in that row "
        "at R2661 BEFORE any code). SHIPPED the seventh wave of "
        "src/os/export_composed_landed_face.py plus "
        "src/os/test_export_composed_landed_bom_precedence_seventh_wave.py: the "
        "equal-length UTF-16 branch now compares BYTES instead of lengths, so a "
        "body of the right SIZE and the wrong CONTENT is named "
        "UTF16-BOM-BODY-MISMATCH with composed/disk/delta and body_differs=1 "
        "instead of reading agrees=True (AC-EDXC1/AC-EDXC2); one shared "
        "cut_facts() names the code UNITS a cut lost apart from the WHOLE "
        "CHARACTERS it lost, so a tail that is half a surrogate pair reads "
        "cut_units=1 cut_chars=0 surrogate_half=1 rather than being counted as "
        "a whole character (AC-EDXC3); the same call names a CUT that sits "
        "behind the UTF-8 BOM and a UTF-16 marker at once while the parent word "
        "BOM-DOUBLE-MARKER stays, because a parent fixture pinned it "
        "(AC-EDXC4). PROOF: SUITE PASS 6/6 on the first run and 6/6 TWICE with "
        "an identical criterion digest plus SEVEN adjacent suites green through "
        "the shipped capture callable (qa/export-composed-landed-seventh-wave-"
        "R2671.log, %dB, legs=2 identical=True adjacent=7 fails=0, single "
        "writer utf-8 LF); the two remaining consumers "
        "test_export_composed_landed_face and "
        "test_export_composed_landed_wordspace still exit 0, and the four "
        "measured shapes were re-read BEFORE any byte was written "
        "(qa/limits-export-composed-landed-seventh-wave-before-R2671.log). "
        "Registry moved 653/4894 -> 654/4900 by exactly one row, recounted by "
        "importing reconcile_all.SUITES at 654 unique names and 654 unique "
        "paths; docs/sandbox-suite-matrix.md was regenerated stamp-aligned from "
        "the same R2665 leg to %dB at 654 suites / 4900 criteria with its green "
        "line honestly reading 653/654 because this suite is not in that leg, "
        "and --check re-read DOC-CURRENT." % (ev, matrix),
        "R2671 tokens: local=~9k api=0 api_reason=product window - one "
        "five-silence scan with the content-addressed decisions scan, the group "
        "orders tail and the ledger face read, one debt gate plus queue head "
        "read, one limits probe re-run on the committed tree, one module "
        "extension with one shared cut-facts callable, one new six-criteria "
        "suite run twice through the shipped capture writer with seven adjacent "
        "suites, one registry re-measurement by import on four axes, one "
        "stamp-aligned matrix regeneration checked byte-identical, one debt row "
        "closed and one successor battery opened through their shipped writers, "
        "one board row stamped with its discharge note, and the "
        "state/export/heartbeat closeout; zero cloud calls and zero external API "
        "touches",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2671_")
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
