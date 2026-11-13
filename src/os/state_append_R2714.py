"""R2714 product closeout: one face, its proof, the board and one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2714 PRODUCT window on AC-EUC1..AC-EUC6 (state/queue/tech.md:689, "
    "pinned at R2494 BEFORE any code): shipped src/os/evidence_utf8_capture.py plus "
    "src/os/test_evidence_utf8_capture.py. MEASURED on the shipped tree BEFORE any "
    "byte: evidence_capture._flat rewrites CRLF into LF silently (13 -> 11 bytes on "
    "the same fixture), evidence_capture.run_suite decodes child output with "
    "errors='replace' so an invalid byte becomes U+FFFD and its offset is lost, and "
    "the census family only names a bad artifact on the NEXT battery. The face asks "
    "the bytes at CALL time and refuses with its own codes and measured counters - "
    "E_EUC_CRLF, E_EUC_LONE_CR, E_EUC_NOT_UTF8 carrying the first offending offset, "
    "E_EUC_EXISTS, E_EUC_BADDIR and E_EUC_WRITE - and only clean bytes are landed "
    "through one atomic write with a read-back. PROOF: SUITE PASS 6/6 twice with an "
    "identical digest through the shipped capture callable "
    "(qa/evidence-utf8-capture-R2714.log, 6776 bytes, legs=2 identical=True "
    "adjacent=2 both green fails=0), one bounded live leg "
    "(qa/evidence-utf8-capture-live-R2714.log, 573 bytes, landed BY this guard), "
    "registry 667 suites / 4978 criteria -> 668 / 4984 measured by import.",
    "R2714 THE LIVE LEG IS THE PRODUCT SENTENCE IN BYTES: two real committed "
    "evidence files (qa/write-sensitive-R2713.log 14192B and "
    "qa/evidence-utf8-capture-R2714.log 6776B) read ACCEPT here and IDENTICAL "
    "through the shipped normaliser with their digests unchanged, while the SAME "
    "CRLF fixture the shipped reader rewrites to 11 bytes is refused E_EUC_CRLF "
    "here with crlf=2, and the same invalid byte the shipped decode turns into "
    "U+FFFD is refused E_EUC_NOT_UTF8 here with offset=2; the live log itself was "
    "landed by the guard, so the artifact proves its own capture path.",
    "R2714 THREE OWN DEFECTS WERE BORN AND REPAIRED HERE, disclosed rather than "
    "smoothed: (1) refusal_line did not map the measured bad_offset to the printed "
    "offset field, found by the suite own AC-EUC4 and fixed at that building site "
    "so the line now prints offset=2; (2) the suite printed U+FFFD and a "
    "pid-carrying scratch path into criterion lines, which broke the shipped "
    "capture twice - first a GBK UnicodeEncodeError, then E_EVC_DRIFT "
    "D796BBBB12B553B2/473309E04234DC85 when the two legs differed by pid - both "
    "repaired at their birth sites by ASCII-only shown() and sanitise(), and NO "
    "criterion was loosened; (3) the NUL measurement fixture was first named "
    "'nul', which Windows resolves as a reserved device and so returned "
    "E_EUC_EXISTS, so it was renamed and re-measured - a measurement defect, not "
    "a face defect, and the shipped face really does land a NUL byte with nul=1.",
    "R2714 REGISTRY, BOARD AND MATRIX: one runner row os-evidence-utf8-capture(6) "
    "so the registry reads 668 suites / 4984 criteria (recounted by importing "
    "reconcile_all.SUITES); docs/sandbox-suite-matrix.md read ROWS-MISMATCH first "
    "(doc-rows 667 against registry 668) as the designed first measurement with NO "
    "byte written, and was then regenerated stamp-aligned from "
    "qa/reconcile-all-R2713.log to 70651 bytes at 668 rows with --check "
    "DOC-CURRENT; tech row 689 was closed with its discharge note and ONE row was "
    "seeded as AC-EBOM1..AC-EBOM6 from this window own measured limit (a UTF-8 BOM "
    "payload LANDS while battery_followup.eol_state then reads eol_ok=False on "
    "that very file, and a NUL byte LANDS with nul=1 measured and never "
    "enforced); the queue head is now state/queue/tech.md:691 prefix AC-EBOM1 with "
    "claimable 13 and queue_floor reads FLOOR-MET 5/5 13/10 10/10.",
    "R2714 DEBT THROUGH THE SHIPPED WRITERS, including one flag correction made by "
    "hand and disclosed: product-face-R2713 was closed at 224993B -> 224996B (line "
    "418, open 45->44, done 355->356, readback ok), then product-face-R2714 was "
    "appended first=yes at 224996B -> 225558B and reconcile-battery-R2714 was "
    "appended first=no at 225558B -> 226035B. That order was WRONG against the "
    "shipped gate contract (the single first=yes row is what the next window leads "
    "with, and the R2168 mixed-tree rule puts a battery before the next product "
    "byte), so the trailing flags of EXACTLY those two rows were swapped in a "
    "two-line data edit and re-proved: debt_register --check reads "
    "first=reconcile-battery-R2714 open=46 done=356 and debt_gate --check reads "
    "CLAIM-FIRST item=reconcile-battery-R2714 first=1 at the pre-registered 668 "
    "suites / 4984 criteria.",
    "R2714 honest disclosures: (a) ONE product point by the Executive Protocol "
    "scale - a runnable guard with a green six-criteria suite and a live reading "
    "on the real tree - but nothing a CEO can newly open, and every P-47 business "
    "face still waits on CEO physical pieces (merchant id, mini-program "
    "appid/secret); (b) this window did NOT run a battery and claims none: it "
    "moved product src bytes and one registry row, so the battery is registered "
    "first=yes and is owed on the committed tree BEFORE the next product byte; "
    "(c) the matrix document now records the R2713 leg as its evidence and its "
    "green line honestly reads 667/668 because no battery ran this window, so the "
    "next battery will find it one leg behind BY DESIGN; (d) the one-off live "
    "leg, limit-measurement script and their scratch dirs under tmp/ are DELETED "
    "before the commit rather than staged; (e) tasks.md was not touched, it is "
    "the P-47 canonical board; (f) Docker is absent on this host; (g) "
    "BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell "
    "for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",
    "R2714 tokens: local=~10k api=0 api_reason=product window - one five-silence "
    "scan with the queue face, one debt gate plus one queue floor plus one fold "
    "gate plus one state IO read, one zero-occupancy anchor check at HEAD, one "
    "measured-defect probe over three shapes, one face plus one suite shipped, two "
    "individual suite runs and one capture that first drifted on my own pid-bearing "
    "output, one live leg landed by the guard itself, one registry count by "
    "import, one designed matrix ROWS-MISMATCH then one stamp-aligned "
    "regeneration, one board close plus one seeded row, one debt close and two "
    "debt appends plus one disclosed flag correction, and the "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2714_")
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
