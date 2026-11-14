"""R2725 product closeout: the unknown-shape refusal face, debt, matrix, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2725 PRODUCT window on AC-EPDU1..AC-EPDU6 (state/queue/tech.md:695, "
    "pinned at R2723 BEFORE any code): shipped "
    "src/os/evidence_capture_precedence_unknown_shape.py plus "
    "src/os/test_evidence_capture_precedence_unknown_shape.py. Five readings at "
    "open: git status EMPTY at HEAD 58f90c0b equal to origin/main with no "
    "index.lock; ZERO @BigDomain rows new in the group ledger; the "
    "content-addressed decisions face read rows=120 tokens=64 new=0; the group "
    "orders tail is the 2026-11-14 00:30 master-control audit row already "
    "carried as knowledge-only; benchmarks_refreshed 2026-11-14 inside the "
    "seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2724, "
    "queue_head read tech line=695 prefix AC-EPDU1 claimable=13, queue_floor "
    "read FLOOR-MET 5/5 13/10 10/10.",
    "R2725 THE DEFECT WAS RE-MEASURED ON A PRIVATE WORLD BEFORE ANY BYTE, rather "
    "than taken from the queue note: with the shipped BOM-guard law patched to "
    "answer E_EBOM_UTF16 for a byte-order-marked payload, a payload earning nul, "
    "utf8 and tail read report code E_EBOM_UTF16 beside shapes nul,utf8,tail and "
    "shape_codes E_EBOM_NUL,E_EUC_NOT_UTF8,E_ETAIL_TAIL, so the published list "
    "OMITTED the defect the chain named first and CODES[shapes[0]] read "
    "E_EBOM_NUL against that code (list_omits_code=True code_mismatch=True); a "
    "payload earning ONLY the unknown shape read report None, i.e. ACCEPT, while "
    "chain_code read E_EBOM_UTF16, so bytes the shipped chain refuses would have "
    "been LANDED. The face refuses any first code outside the six known shapes, "
    "names it FIRST so no published list can omit it, keeps every six-known-shape "
    "answer by handing it to the R2723 face unchanged, and reads both the derived "
    "order and the first code at CALL time.",
    "R2725 PROOF: AC-EPDU1..AC-EPDU6 SUITE PASS 6/6 twice through the shipped "
    "capture callable with an IDENTICAL digest "
    "(qa/evidence-capture-precedence-unknown-shape-R2725.log, 13634 bytes, "
    "utf-8, bom=False, crlf=0, lone_cr=0, nul=0, legs=2 identical=True "
    "adjacent=5 fails=0, digest ADA4EEE3F6E3F64E), and one bounded live leg "
    "landed BY the shipped capture guard "
    "(qa/evidence-capture-precedence-unknown-shape-live-R2725.log, 462 bytes, "
    "utf-8 LF): on the patched law the chain names E_EBOM_UTF16 for both "
    "fixtures, the R2723 reader reads sole=ACCEPT with mix_shapes nul,utf8,tail "
    "while the R2725 reader reads sole=REFUSED:E_EBOM_UTF16 with mix_shapes "
    "E_EBOM_UTF16,nul,utf8,tail, the real committed qa/reconcile-all-R2723.log "
    "reads ACCEPT bytes=1220981 digest=27D9568AF888F827 on both readers, and "
    "restoring the shipped law restores ACCEPT on the sole fixture.",
    "R2725 REGISTRY, BOARD AND MATRIX: one runner row "
    "os-evidence-capture-precedence-unknown-shape(6) wired after the derived "
    "row; docs/sandbox-suite-matrix.md read ROWS-MISMATCH first (doc-rows 672 "
    "against registry 673, evidence qa/reconcile-all-R2723.log) as the designed "
    "first measurement with NO byte written, and was then regenerated "
    "stamp-aligned from this company own green leg to 71262 bytes at 673 rows "
    "with --check DOC-CURRENT; tech row 695 was closed with its discharge note "
    "and ONE row was seeded as AC-EPTYP1..AC-EPTYP6 from this window own "
    "measured limit (the published shapes list carries a CODE token where every "
    "other entry is a shape NAME, so CODES[shapes[0]] raises KeyError on "
    "exactly the payload this face exists to refuse), so the queue head is now "
    "state/queue/tech.md:697 prefix AC-EPTYP1 with claimable 13 and queue_floor "
    "still reads FLOOR-MET 5/5 13/10 10/10. Registry 672 suites / 5008 criteria "
    "-> 673 / 5014 measured by import at 673 unique names and 673 unique paths.",
    "R2725 DEBT THROUGH THE SHIPPED WRITERS: product-face-R2724 was closed at "
    "233595B -> 233598B (line 433, open 50->49, done 365->366, readback ok), "
    "product-face-R2725 was appended first=no at 233598B -> 234226B naming queue "
    "head state/queue/tech.md:697 prefix AC-EPTYP1 with claimable 13 and criteria "
    "AC-EPTYP1..AC-EPTYP6 pinned there at R2725 BEFORE any code, and "
    "reconcile-battery-R2725 was appended first=yes at 234226B -> 234823B "
    "because this window moved product src bytes and one registry row, so the "
    "R2168 mixed-tree rule puts the FULL battery on the committed tree BEFORE "
    "the next product byte; debt_gate --check now reads CLAIM-FIRST "
    "item=reconcile-battery-R2725 at 673 suites / 5014 criteria.",
    "R2725 THREE OWN DEFECTS WERE BORN HERE AND EACH WAS REPAIRED AT ITS BIRTH "
    "SITE, disclosed rather than smoothed: (1) the first capture leg refused "
    "with E_EVC_DRIFT because one criterion line printed the refusal line "
    "verbatim, and that line carries the per-leg pid inside the scratch path - "
    "the label was routed through the suite own sanitise() so two legs read the "
    "same line, and the criterion was NOT loosened; (2) the sanitise() helper was "
    "referenced before it existed anywhere in this suite (a straight NameError "
    "on the second capture attempt), fixed by adding it and re-reading; (3) the "
    "face first carried an E_UNRANKED constant that no branch ever raised, and a "
    "dead code constant is a lie about what the face can refuse, so it was "
    "removed before the commit rather than left for a reader to trust.",
    "R2725 honest disclosures: (a) ONE product point by the Executive Protocol "
    "scale - a runnable refusal face with a green six-criteria suite, five "
    "adjacent suites green and a live reading on the real tree - but nothing a "
    "CEO can newly open, and every P-47 business face still waits on CEO "
    "physical pieces (merchant id, mini-program appid/secret); (b) this window "
    "DID NOT run a battery and claims none: it moved product src bytes and one "
    "registry row, so reconcile-battery-R2725 is registered first=yes and the "
    "matrix green line will be one leg behind BY DESIGN until that battery "
    "lands; (c) the shapes-typing limit was MEASURED and carried to the queue "
    "rather than fixed here, because the criteria pinned at R2723 cover the "
    "unknown-code refusal only; (d) qa/reconcile-all-R2723.log now measures "
    "1220981B rather than the 1218994B R2724 recorded, which is the 1987B "
    "verdict block R2724 itself appended after its own byte measurement - named "
    "here so the next window does not read it as post-hoc byte drift; (e) "
    "src/os still carries more than 190 one-off state_append_R*.py scripts, "
    "pre-existing bloat this window neither created nor cleaned; (f) tasks.md "
    "was not touched, it is the P-47 canonical board; (g) Docker is absent on "
    "this host; (h) BigDomain-OSLoop still reads InteractiveToken and needs an "
    "ELEVATED shell for its S4U re-registration (carried ceo-pending physical "
    "item loop-s4u-reconcile).",
    "R2725 tokens: local=~12k api=0 api_reason=product window - one five-silence "
    "scan with the debt gate, the queue head, the queue floor and the ledger "
    "face, one private-world probe of the unknown-shape defect plus one "
    "shape-typing probe before any byte, one face plus one suite shipped, one "
    "suite run green, one drifted capture leg and one red capture leg each "
    "repaired at its birth site, one twice-through capture with an identical "
    "digest and five adjacent suites, one bounded live leg on both readers, one "
    "registry count by import on four axes, one designed matrix ROWS-MISMATCH "
    "then one stamp-aligned regeneration checked DOC-CURRENT, one board close and "
    "one seeded row, one debt close and two debt appends with readback, and the "
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2725p_")
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
