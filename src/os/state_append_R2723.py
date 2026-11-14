"""R2723 product closeout: derived precedence face, board, debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2723 PRODUCT window on AC-ECORD1..AC-ECORD6 "
    "(state/queue/tech.md:694, pinned at R2720 BEFORE any code): shipped "
    "src/os/evidence_capture_precedence_derived.py plus "
    "src/os/test_evidence_capture_precedence_derived.py. Five readings at open: "
    "git status EMPTY at HEAD aab289e7 equal to origin/main with no index.lock; "
    "ZERO @BigDomain rows new in the group ledger; the content-addressed "
    "decisions face read rows=120 tokens=64 new=0; the group orders tail is the "
    "2026-11-14 01:3x BigStream seat row already carried as knowledge-only; "
    "benchmarks_refreshed 2026-11-14 inside the seven-day gate. debt_gate read "
    "CLAIM-FIRST item=product-face-R2722, queue_head read tech line=694 prefix "
    "AC-ECORD1 claimable=13, queue_floor read FLOOR-MET 5/5 13/10 10/10.",
    "R2723 THE DEFECT WAS RE-MEASURED ON THE SHIPPED TREE BEFORE ANY BYTE rather "
    "than taken from the queue note: for each of the fifteen shape pairs this "
    "window builds a payload carrying EXACTLY those two shapes, re-checks that "
    "isolation against the shipped counters, asks the shipped chain which code "
    "it publishes first on that payload and reads the winner off the answer. On "
    "the shipped chain the derived order read (bom,nul,utf8,crlf,lone_cr,tail), "
    "byte for byte the constant R2720 published; with the shipped BOM-guard law "
    "patched to check NUL before BOM the derived order MOVED to "
    "(nul,bom,utf8,crlf,lone_cr,tail) and the published report followed it to "
    "code E_EBOM_NUL with shapes nul,bom,tail - the divergence R2720 could only "
    "name is now impossible by construction. A relation that is not total, a "
    "seed that no longer isolates its pair and an answer naming a third shape "
    "are REFUSED by name (E_EPD_ORDER / E_EPD_SEED / E_EPD_ANSWER), never "
    "guessed.",
    "R2723 PROOF: AC-ECORD1..AC-ECORD6 SUITE PASS 6/6 twice through the shipped "
    "suite file with an identical digest (qa/evidence-capture-precedence-"
    "derived-R2723.log, 7540 bytes, legs=2 identical=True adjacent=True "
    "both_green=True fails=0), and one bounded live leg landed on the real tree "
    "(qa/evidence-capture-precedence-derived-live-R2723.log, 516 bytes): the "
    "order line reads derived=bom,nul,utf8,crlf,lone_cr,tail probes=15 items=6, "
    "the real committed qa/reconcile-all-R2721.log reads ACCEPT bytes=1213193, "
    "and the two real compound fixtures read REFUSED with their derived lists "
    "(bom+nul+tail -> code E_EBOM_BOM shapes bom,nul,tail; crlf+nul -> code "
    "E_EBOM_NUL shapes nul,crlf). Registry 671 suites / 5002 criteria -> 672 / "
    "5008 measured by import at 672 unique names and 672 unique paths.",
    "R2723 REGISTRY, BOARD AND MATRIX: one runner row "
    "os-evidence-capture-precedence-derived(6) wired after the shipped compound "
    "row; docs/sandbox-suite-matrix.md read ROWS-MISMATCH first (doc-rows 671 "
    "against registry 672) as the designed first measurement with NO byte "
    "written, and was then regenerated stamp-aligned from this company own green "
    "leg qa/reconcile-all-R2721.log to 71107 bytes at 672 rows with --check "
    "DOC-CURRENT; tech row 694 was closed with its discharge note and ONE row "
    "was seeded as AC-EPDU1..AC-EPDU6 from this window own measured limit (an "
    "earned shape whose code is outside the six known shapes is invisible to the "
    "detector while the first code still names it - patched to answer "
    "E_EBOM_UTF16 the face published that code beside shapes nul,utf8,tail and "
    "CODES[shapes[0]] read E_EBOM_NUL), so the queue head is now "
    "state/queue/tech.md:695 prefix AC-EPDU1 with claimable 13 and queue_floor "
    "still reads FLOOR-MET 5/5 13/10 10/10.",
    "R2723 DEBT THROUGH THE SHIPPED WRITERS: product-face-R2722 was closed at "
    "231233B -> 231236B (line 430, open 49->48, done 363->364, readback ok), "
    "product-face-R2723 was appended first=no at 231236B -> 231810B naming queue "
    "head state/queue/tech.md:695 prefix AC-EPDU1 with claimable 13 and criteria "
    "AC-EPDU1..AC-EPDU6 pinned there at R2723 BEFORE any code, and "
    "reconcile-battery-R2723 was appended first=yes at 231810B -> 232420B "
    "because this window moved product src bytes and one registry row, so the "
    "R2168 mixed-tree rule puts the FULL battery on the committed tree BEFORE "
    "the next product byte; debt_gate --check now reads CLAIM-FIRST "
    "item=reconcile-battery-R2723 at 672 suites / 5008 criteria.",
    "R2723 THREE OWN DEFECTS WERE BORN HERE AND EACH WAS REPAIRED AT ITS BIRTH "
    "SITE, disclosed rather than smoothed: (1) SEEDS was keyed by hand-written "
    "pair order while the probe list is name-sorted, so the first run died on "
    "KeyError('crlf','nul'); the keys are now canonicalised at import and the "
    "probe list carries no bias; (2) the first suite run read 5/6 because "
    "AC-ECORD5 own banned-token list used the bare substring 'time.' and matched "
    "the docstring phrase 'at CALL time.' - the ASSERTION was tightened to real "
    "clock call shapes and the criterion was NOT loosened; (3) one fixture line "
    "carried a dead conditional referencing an undefined name, rewritten to the "
    "literal bytes before the suite could hide it.",
    "R2723 honest disclosures: (a) ONE product point by the Executive Protocol "
    "scale - a runnable face that derives its precedence at call time, with a "
    "green six-criteria suite and a live reading on the real tree - but nothing a "
    "CEO can newly open, and every P-47 business face still waits on CEO "
    "physical pieces (merchant id, mini-program appid/secret); (b) this window "
    "did NOT run a battery and claims none: it moved product src bytes and one "
    "registry row, so reconcile-battery-R2723 is registered first=yes and the "
    "matrix green line will be one leg behind BY DESIGN until that battery "
    "lands; (c) the unknown-shape gap was MEASURED and carried to the queue "
    "rather than fixed here, because the criteria pinned at R2720 cover the "
    "derived order only; (d) src/os/queue_row.py --check reads GATE-DEBT with 13 "
    "violations, NONE of them this window own row (they are legacy rows at "
    "tech.md:41/54/88/415/524/537/702 and main.md:4/9/10/12/13 and "
    "explore.md:295), pre-existing debt this window neither created nor fixed; "
    "(e) tasks.md was not touched, it is the P-47 canonical board; (f) Docker is "
    "absent on this host; (g) BigDomain-OSLoop still reads InteractiveToken and "
    "needs an ELEVATED shell for its S4U re-registration (carried ceo-pending "
    "physical item loop-s4u-reconcile).",
    "R2723 tokens: local=~11k api=0 api_reason=product window - one five-silence "
    "scan with the debt gate, the queue head, the queue floor and the ledger "
    "face, one measured probe of all fifteen shape pairs plus one patched-law "
    "run before any byte, one face plus one suite shipped, one suite run twice "
    "with an identical digest, one live leg on the real tree, one registry count "
    "by import on four axes, one designed matrix ROWS-MISMATCH then one "
    "stamp-aligned regeneration checked DOC-CURRENT, one board close and one "
    "seeded row, one debt close and two debt appends with readback, and the "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2723p_")
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
