"""R2720 product closeout: one face, its proof, the board, the debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2720 PRODUCT window on AC-ECMP1..AC-ECMP6 (state/queue/tech.md:693, "
    "pinned at R2718 BEFORE any code): shipped src/os/evidence_capture_compound_refusal.py "
    "plus src/os/test_evidence_capture_compound_refusal.py. Five readings at open: git "
    "status EMPTY at HEAD f908e32c equal to origin/main with no index.lock; ZERO "
    "@BigDomain rows new in the group ledger; the content-addressed decisions face read "
    "no new token; the group orders tail is the 2026-11-14 01:3x BigStream seat row "
    "already carried as knowledge-only; benchmarks_refreshed 2026-11-14 inside the "
    "seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2719, queue_head read "
    "tech line=693 prefix AC-ECMP1 claimable=13, queue_floor read FLOOR-MET 5/5 13/10 "
    "10/10.",
    "R2720 THE DEFECT WAS MEASURED ON THE SHIPPED TRIO BEFORE ANY BYTE, four shapes: NUL "
    "plus an unterminated tail reads only E_EBOM_NUL, a BOM prefix plus a tail reads only "
    "E_EBOM_BOM, BOM plus NUL plus tail reads only E_EBOM_BOM, and CRLF plus NUL reads "
    "only E_EBOM_NUL - so only the FIRST defect is ever named and an operator learns the "
    "second one only after fixing the first. The face reports EVERY earned shape with its "
    "own counter, in the shipped precedence order, BESIDE the shipped first code which is "
    "asked from the shipped chain at CALL time; it lands every clean payload through the "
    "tail guard unchanged and keeps the zero-byte ACCEPT decision.",
    "R2720 PROOF: SUITE PASS 6/6 twice through the shipped capture callable with an "
    "identical digest (qa/evidence-capture-compound-refusal-R2720.log, 8828 bytes, legs=2 "
    "identical=True adjacent=2 both green fails=0), and one bounded live leg landed BY "
    "this face (qa/evidence-capture-compound-refusal-live-R2720.log, 491 bytes): the four "
    "compound fixtures name their two or three shapes each while the shipped first code "
    "stays byte-identical, the clean LF fixture reads ACCEPT on all three readers, and "
    "the real committed qa/reconcile-all-R2719.log reads ACCEPT on all three with its "
    "digest unchanged. Registry 670 suites / 4996 criteria -> 671 / 5002 measured by "
    "import at 671 unique names and 671 unique paths.",
    "R2720 ONE OWN DEFECT WAS BORN AND REPAIRED AT ITS BIRTH SITE, disclosed rather than "
    "smoothed: the first suite run read 5/6 because the CRLF-plus-NUL fixture did not end "
    "in LF and therefore ALSO earned the tail shape, so the expected list was wrong "
    "rather than the face - the fixture was corrected to end in LF and the criterion was "
    "NOT loosened, after which the suite read 6/6 on the same code.",
    "R2720 REGISTRY, BOARD AND MATRIX: one runner row os-evidence-capture-compound-refusal(6) "
    "wired after the tail-guard row; docs/sandbox-suite-matrix.md read ROWS-MISMATCH first "
    "(doc-rows 670 against registry 671) as the designed first measurement with NO byte "
    "written, and was then regenerated stamp-aligned from this company own green leg "
    "qa/reconcile-all-R2719.log to 70985 bytes at 671 rows with --check DOC-CURRENT; tech "
    "row 693 was closed with its discharge note and ONE row was seeded as "
    "AC-ECORD1..AC-ECORD6 from this window own measured limit - the shape ORDER is a "
    "hardcoded tuple while the first code is asked at call time, and with that tuple "
    "patched to tail-first the same payload still reports first code E_EBOM_BOM while the "
    "shape list starts with tail - so the queue head is now state/queue/tech.md:694 prefix "
    "AC-ECORD1 with claimable 13 and queue_floor still reads FLOOR-MET 5/5 13/10 10/10.",
    "R2720 DEBT THROUGH THE SHIPPED WRITERS: product-face-R2719 was closed at 229691B -> "
    "229694B (line 427, open 48->47, done 361->362, readback ok), product-face-R2720 was "
    "appended first=no at 229694B -> 230206B naming queue head state/queue/tech.md line "
    "694 prefix AC-ECORD1 with claimable 13 and criteria AC-ECORD1..AC-ECORD6 pinned there "
    "at R2720 BEFORE any code, and reconcile-battery-R2720 was appended first=yes at "
    "230206B -> 230744B because this window moved product src bytes and one registry row, "
    "so the R2168 mixed-tree rule puts the FULL battery on the committed tree BEFORE the "
    "next product byte; debt_gate --check now reads CLAIM-FIRST item=reconcile-battery-R2720 "
    "at 671 suites / 5002 criteria.",
    "R2720 honest disclosures: (a) ONE product point by the Executive Protocol scale - a "
    "runnable compound report with a green six-criteria suite and a live reading on the "
    "real tree - but nothing a CEO can newly open, and every P-47 business face still "
    "waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) this "
    "window did NOT run a battery and claims none: it moved product src bytes and one "
    "registry row, so reconcile-battery-R2720 is registered first=yes and the matrix green "
    "line will be one leg behind BY DESIGN until that battery lands; (c) the derived-"
    "precedence gap was MEASURED and carried to the queue rather than fixed here, because "
    "the criteria pinned at R2718 cover the compound report only; (d) R2614 is NOT owed "
    "this window because no battery leg was launched under the closeout commit; (e) "
    "tasks.md was not touched, it is the P-47 canonical board; (f) Docker is absent on "
    "this host; (g) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED "
    "shell for its S4U re-registration (ceo-pending physical item loop-s4u-reconcile).",
    "R2720 tokens: local=~9k api=0 api_reason=product window - one five-silence scan with "
    "the debt gate, the queue head, the queue floor and the ledger face, one measured-"
    "defect probe over four compound shapes before any byte, one face plus one suite "
    "shipped, two suite runs (the first red on MY OWN fixture expectation), one "
    "twice-through capture with an identical digest, one live leg landed by the face "
    "itself, one registry count by import on four axes, one designed matrix "
    "ROWS-MISMATCH then one stamp-aligned regeneration, one queue close and one seeded "
    "row after a patched-tuple probe, one debt close and two debt appends with readback, "
    "and the state/export/heartbeat closeout; zero cloud calls and zero external API "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2720_")
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
