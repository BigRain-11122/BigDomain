"""R2716 product closeout: one face, its proof, the board, the debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2716 PRODUCT window on AC-EBOM1..AC-EBOM6 (state/queue/tech.md:691, "
    "pinned at R2714 BEFORE any code): shipped src/os/evidence_utf8_capture_bom_guard.py "
    "plus src/os/test_evidence_utf8_capture_bom_guard.py. Five readings at open: git "
    "status EMPTY at HEAD aba1afde equal to origin/main with no index.lock; ZERO "
    "@BigDomain rows new in the group ledger; the content-addressed decisions face read "
    "no new token; the group orders tail is the 2026-11-14 01:3x BigStream seat row "
    "already carried as knowledge-only; benchmarks_refreshed 2026-11-14 inside the "
    "seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2715, queue_head read "
    "tech line=691 prefix=AC-EBOM1 claimable=13, queue_floor read FLOOR-MET 5/5 13/10 "
    "10/10.",
    "R2716 THE DEFECT WAS MEASURED ON THE SHIPPED TREE BEFORE ANY BYTE, three shapes: a "
    "payload beginning with a UTF-8 BOM LANDS (capture verdict LANDED bytes=9) while "
    "battery_followup.eol_state then reads (0, 0, True, 9) on that very file, i.e. "
    "bom=True and therefore eol_ok=False, so the capture face and the verdict face "
    "disagree about the same bytes; a payload carrying NUL LANDS with nul=1 measured and "
    "published but never enforced; and a payload whose last line is unterminated also "
    "LANDS (bytes=18), which is OUTSIDE this window criteria and is carried to the queue "
    "as the next row rather than folded in. The face asks the SHIPPED eol_state law at "
    "CALL time on exactly those bytes, so the two faces cannot disagree, and refuses BOM "
    "as E_EBOM_BOM and NUL as E_EBOM_NUL with their counters while handing every other "
    "payload to the shipped capture face unchanged.",
    "R2716 PROOF: SUITE PASS 6/6 twice through the shipped capture callable with an "
    "identical digest (qa/evidence-utf8-capture-bom-guard-R2716.log, 7979 bytes, legs=2 "
    "identical=True adjacent=2 both green fails=0), and one bounded live leg landed BY "
    "this guard itself (qa/evidence-utf8-capture-bom-guard-live-R2716.log, 428 bytes): "
    "the BOM and NUL shapes are real on the shipped face and refused here with their "
    "measured counters, the CRLF fixture refuses with the SAME shipped code E_EUC_CRLF "
    "on BOTH readers, and the real committed qa/write-sensitive-R2715.log (8783 bytes) "
    "reads ACCEPT on BOTH readers with its digest 60E952DC85ADD1F0 unchanged. Registry "
    "668 suites / 4984 criteria -> 669 / 4990 measured by import at 669 unique names and "
    "669 unique paths.",
    "R2716 REGISTRY, BOARD AND MATRIX: one runner row os-evidence-utf8-capture-bom-guard(6) "
    "wired after the shipped capture row; docs/sandbox-suite-matrix.md read ROWS-MISMATCH "
    "first (doc-rows 668 against registry 669) as the designed first measurement with NO "
    "byte written, and was then regenerated stamp-aligned from this company own green leg "
    "qa/reconcile-all-R2715b.log to 70768 bytes at 669 rows with --check DOC-CURRENT; tech "
    "row 691 was closed with its discharge note and ONE row was seeded as "
    "AC-ETAIL1..AC-ETAIL6 from this window own measured limit (an unterminated evidence "
    "tail LANDS through both shipped readers and is not refused), so the queue head is now "
    "state/queue/tech.md:692 prefix AC-ETAIL1 with claimable 13 and queue_floor still reads "
    "FLOOR-MET 5/5 13/10 10/10.",
    "R2716 DEBT THROUGH THE SHIPPED WRITERS: product-face-R2715 was closed at 226453B -> "
    "226456B (line 421, open 46->45, done 357->358, readback ok), product-face-R2716 was "
    "appended first=no at 226456B -> 226959B naming queue head state/queue/tech.md line 692 "
    "prefix AC-ETAIL1 with claimable 13 and criteria AC-ETAIL1..AC-ETAIL6 pinned there at "
    "R2716 BEFORE any code, and reconcile-battery-R2716 was appended first=yes at 226959B "
    "-> 227544B because this window moved product src bytes and one registry row, so the "
    "R2168 mixed-tree rule puts the FULL battery on the committed tree BEFORE the next "
    "product byte; debt_gate --check now reads CLAIM-FIRST item=reconcile-battery-R2716 at "
    "669 suites / 4990 criteria.",
    "R2716 THREE OWN DEFECTS WERE BORN HERE AND EACH WAS REPAIRED AT ITS BIRTH SITE, "
    "disclosed rather than smoothed: (1) I first labelled this window R2715, which is the "
    "PREVIOUS window own label already in the log tail at tick 2708, so the two QA "
    "evidence files were deleted and re-cut at R2716 and the registry comment, the queue "
    "labels, the debt rows own opened and closed fields and the note round words were "
    "corrected to R2716 after a readback; (2) a repair pass over a literal backslash plus "
    "backtick sequence also rewrote ONE historical queue row (the R2706 row own escaped "
    "double backslash), which was DETECTED by git diff, RESTORED byte for byte from "
    "git show HEAD:state/queue/tech.md, and re-proved by git diff --numstat reading 3 "
    "added and 1 deleted line; (3) the seeded row first landed with bare backslashes where "
    "backticks were meant, a shell quoting defect, repaired and re-read through queue_head.",
    "R2716 STATE IO WAS RED AT OPEN AND WAS FIXED AT ITS BIRTH SITE BEFORE THE APPEND: "
    "state_io --check read CANON-DRIFT bytes=63762 bare_lf=339 off_indent=64, so the "
    "shipped fixer was run with --execute and the same file read CANON-CLEAN at 63973 "
    "bytes with crlf=339, bare_lf=0, lone_cr=0 and off_indent=0. state_fold read "
    "FOLD-CLEAR at 63762B against the 78500B gate with margin 14738 and 64 live log lines, "
    "ledger_lines read VERDICT CLEAN with rounds_without_ledger none, and qa_writer_census "
    "read DRIFT-CLEAN flags=0 before this window own evidence files were added.",
    "R2716 honest disclosures: (a) ONE product point by the Executive Protocol scale - a "
    "runnable refusal face with a green six-criteria suite and a live reading on the real "
    "tree - but nothing a CEO can newly open, and every P-47 business face still waits on "
    "CEO physical pieces (merchant id, mini-program appid/secret); (b) this window did NOT "
    "run a battery and claims none: it moved product src bytes and one registry row, so "
    "reconcile-battery-R2716 is registered first=yes and the matrix green line will be one "
    "leg behind BY DESIGN until that battery lands; (c) the unterminated-tail shape was "
    "MEASURED and is carried to the queue rather than fixed here, because the criteria "
    "pinned at R2714 cover BOM and NUL only and widening scope mid-window would be an "
    "unregistered change; (d) src/os already carries more than 180 one-off "
    "state_append_R*.py scripts from previous windows, which is pre-existing bloat this "
    "window did not create and did not clean; (e) tasks.md was not touched, it is the "
    "P-47 canonical board; (f) Docker is absent on this host; (g) BigDomain-OSLoop still "
    "reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile).",
    "R2716 tokens: local=~9k api=0 api_reason=product window - one five-silence scan with "
    "the debt gate, the queue head, the queue floor and the ledger face, one measured "
    "defect probe over three shapes before any byte, one face plus one suite shipped, one "
    "suite run and one twice-through capture with an identical digest, one live leg landed "
    "by the guard itself, one registry count by import on four axes, one designed matrix "
    "ROWS-MISMATCH then one stamp-aligned regeneration checked DOC-CURRENT, one board "
    "close and one seeded row, one debt close and two debt appends plus a disclosed "
    "round-label correction, one state IO canon fix, and the state/export/heartbeat "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2716_")
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
