"""R2718 product closeout: one face, its proof, the board, the debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2718 PRODUCT window on AC-ETAIL1..AC-ETAIL6 (state/queue/tech.md:692, "
    "pinned at R2716 BEFORE any code): shipped src/os/evidence_capture_tail_guard.py "
    "plus src/os/test_evidence_capture_tail_guard.py. Five readings at open: git status "
    "EMPTY at HEAD cd5f5e7d equal to origin/main with no index.lock; ZERO @BigDomain rows "
    "new in the group ledger; the content-addressed decisions face read no new token; the "
    "group orders tail is the 2026-11-14 01:3x BigStream seat row already carried as "
    "knowledge-only; benchmarks_refreshed 2026-11-14 inside the seven-day gate. debt_gate "
    "read CLAIM-FIRST item=product-face-R2717, queue_head read tech line=692 prefix "
    "AC-ETAIL1 claimable=13, queue_floor read FLOOR-MET 5/5 13/10 10/10.",
    "R2718 THE DEFECT WAS MEASURED ON THE SHIPPED TREE BEFORE ANY BYTE: a payload whose "
    "last line is unterminated LANDS on BOTH shipped readers (bytes=18 on the two-line "
    "fixture alpha plus unterminated), a single-LF payload lands as its one byte, and a "
    "ZERO-byte payload lands as an empty file - so nothing in the pair refused an "
    "unterminated tail and every downstream line reader counts that fragment as a line. "
    "The face refuses such a payload as E_ETAIL_TAIL naming the measured byte count and "
    "the last byte, hands every other payload to the BOM guard unchanged, and names its "
    "one positive decision rather than leaving it to chance: a ZERO-byte payload is "
    "ACCEPTED and landed as an empty file.",
    "R2718 PROOF: SUITE PASS 6/6 twice through the shipped capture callable with an "
    "identical digest (qa/evidence-capture-tail-guard-R2718.log, 6980 bytes, legs=2 "
    "identical=True adjacent=2 both green fails=0), and one bounded live leg landed BY this "
    "guard itself (qa/evidence-capture-tail-guard-live-R2718.log, 399 bytes): the tail "
    "fixture reads LANDED on the shipped capture AND on the BOM guard but E_ETAIL_TAIL here "
    "with tail_last=0x64, the clean LF fixture and the empty fixture read ACCEPT, and the "
    "real committed qa/reconcile-all-R2717.log reads ACCEPT on ALL THREE readers with its "
    "digest unchanged. Registry 669 suites / 4990 criteria -> 670 / 4996 measured by "
    "import at 670 unique names and 670 unique paths.",
    "R2718 REGISTRY, BOARD AND MATRIX: one runner row os-evidence-capture-tail-guard(6) "
    "wired after the BOM guard row; docs/sandbox-suite-matrix.md read ROWS-MISMATCH first "
    "(doc-rows 669 against registry 670) as the designed first measurement with NO byte "
    "written, and was then regenerated stamp-aligned from this company own green leg "
    "qa/reconcile-all-R2717.log to 70872 bytes at 670 rows with --check DOC-CURRENT; tech "
    "row 692 was closed with its discharge note and ONE row was seeded as AC-ECMP1..AC-ECMP6 "
    "from this window own measured limit, so the queue head is now state/queue/tech.md:693 "
    "prefix AC-ECMP1 with claimable 13 and queue_floor still reads FLOOR-MET 5/5 13/10 10/10.",
    "R2718 THE SEEDED ROW NAMED A REAL COMPOUND LIMIT THAT WAS MEASURED BEFORE IT WAS "
    "WRITTEN: on the shipped trio a payload can carry TWO shapes at once and only the FIRST "
    "code is reported - a NUL byte plus an unterminated tail reads only E_EBOM_NUL, a BOM "
    "prefix plus an unterminated tail reads only E_EBOM_BOM, and BOM plus NUL plus tail "
    "reads only E_EBOM_NUL - so an operator fixes one defect, retries and is told about the "
    "next one only then. That gap is OUTSIDE this window criteria and is carried as the "
    "next queue row rather than folded in mid-window.",
    "R2718 DEBT THROUGH THE SHIPPED WRITERS: product-face-R2717 was closed at 228105B -> "
    "228108B (line 424, open 47->46, done 359->360, readback ok), product-face-R2718 was "
    "appended first=no at 228108B -> 228593B naming queue head state/queue/tech.md line 693 "
    "prefix AC-ECMP1 with claimable 13 and criteria AC-ECMP1..AC-ECMP6 pinned there at R2718 "
    "BEFORE any code, and reconcile-battery-R2718 was appended first=yes at 228593B -> "
    "229131B because this window moved product src bytes and one registry row, so the R2168 "
    "mixed-tree rule puts the FULL battery on the committed tree BEFORE the next product "
    "byte; debt_gate --check now reads CLAIM-FIRST item=reconcile-battery-R2718 at 670 "
    "suites / 4996 criteria.",
    "R2718 THREE OWN DEFECTS WERE BORN HERE AND EACH WAS REPAIRED AT ITS BIRTH SITE, "
    "disclosed rather than smoothed: (1) the first seeded queue row was written through a "
    "shell-quoted one-liner that turned the intended backticks into bare backslashes and put "
    "raw BOM bytes into a UTF-8 text file, which broke the row for every reader and even "
    "made a repr print fail on a GBK console - the row was rewritten from a standalone ASCII "
    "script and re-proved ASCII end to end, with the queue_head readback naming the intended "
    "path; (2) the first fold window I picked (items 8..64) was refused for token-missing "
    "and live-floor, and the second (8..58) for a round split, so the window was re-derived "
    "from measured block edges and a DRY RUN preceded the execute pass (8..55, live 81->34, "
    "77755B -> 31564B, margin 46936, archive VERIFIED, layout AGREE); (3) the receipt "
    "appender first resolved state_io from the scratch directory and died on ImportError "
    "before touching any byte, repaired by resolving the module from src/os.",
    "R2718 honest disclosures: (a) ONE product point by the Executive Protocol scale - a "
    "runnable refusal face with a green six-criteria suite and a live reading on the real "
    "tree - but nothing a CEO can newly open, and every P-47 business face still waits on "
    "CEO physical pieces (merchant id, mini-program appid/secret); (b) this window did NOT "
    "run a battery and claims none: it moved product src bytes and one registry row, so "
    "reconcile-battery-R2718 is registered first=yes and the matrix green line will be one "
    "leg behind BY DESIGN until that battery lands; (c) the compound-defect gap was "
    "MEASURED and carried to the queue rather than fixed here, because the criteria pinned "
    "at R2716 cover the tail shape only; (d) src/os still carries more than 180 one-off "
    "state_append_R*.py scripts, pre-existing bloat this window neither created nor cleaned; "
    "(e) tasks.md was not touched, it is the P-47 canonical board; (f) Docker is absent on "
    "this host; (g) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED "
    "shell for its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2718 tokens: local=~9k api=0 api_reason=product window - one five-silence scan with "
    "the debt gate, the queue head, the queue floor and the ledger face, one measured-defect "
    "probe over three shapes before any byte, one face plus one suite shipped, one suite run "
    "and one twice-through capture with an identical digest, one live leg landed by the "
    "guard itself, one registry count by import on four axes, one designed matrix "
    "ROWS-MISMATCH then one stamp-aligned regeneration, one board close and one seeded row "
    "rewritten after a shell-quoting defect, one fold window re-derived across three dry "
    "runs, one debt close and two debt appends with readback, and the "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2718_")
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
