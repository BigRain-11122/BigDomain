"""closeout_R2370.py - append this window's items, then fold if the gate demands.

One-off for the round, same shape as closeout_R2369: the state file is written
through state_io.canon, the backlog row is prepended at the claimed-board top,
and any fold runs through state_fold.fold.

Usage: python src/os/closeout_R2370.py
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
GATE = 78500
RESERVE = 6000
FOLD_BASE = 646

ITEMS = [
    "2026-11-02 R2370 verification-then-product window (five-silence scan "
    "clean at open: empty git status at 6b918367, no .git/index.lock; LEDGER "
    "atbd_lines=0 unreplied_groups=0, DEC rows=124 tokens=81 new=0, group "
    "orders tail still the 2026-11-01 10:4x model-policy baseline already "
    "acknowledged as non-execution, benchmarks refreshed 2026-11-02 inside "
    "the seven-day gate). The debt gate named CLAIM-FIRST "
    "item=product-face-R2370, so the battery ran FIRST on the committed tree: "
    "RUNNER PASS 496/496 suites green plus reconcile controls 7/7 in 990.9s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2370.log, 804005B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection) and criteria total "
    "3952 EXACTLY as pre-registered, so the prediction matched the measurement "
    "with no correction and nothing to name.",
    "R2370 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=47371B regenerated=47476B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 496 suites / 3952 criteria (47476B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2370 PASS. The evidence and the matrix were committed ALONE as bd736b53 "
    "before any product byte changed (the R2168 mixed-tree rule).",
    "R2370 product face, the row the reader named: CLAIMED the tech head the "
    "OFFER reader reported, state/queue/tech.md:416 prefix AC-FSFW1 "
    "(followup_section_foreign_wire), whose AC-FSFW1..AC-FSFW6 were pinned "
    "INSIDE that row at R2357 BEFORE any code, after a fresh anchor check at "
    "HEAD: followup_section_foreign_wire / AC-FSFW / E_FSFW / "
    "os-followup-section-foreign-wire / test_followup_section_foreign_wire hit "
    "ONLY prose and state files (src/os/backlog.md, src/os/closeout_R2357.py, "
    "state/queue/tech.md) with zero executable occupancy. Note the debt note "
    "called the head residue_batch_status_face; the reader, which is the "
    "authority, named line 416 - recorded rather than silently reconciled.",
    "R2370 the wire: shipped src/os/followup_section_foreign_wire.py plus "
    "src/os/test_followup_section_foreign_wire.py. followup_section_foreign "
    "had NO consumer - the matrix section regenerated the doc over whatever "
    "the pile contained, so a ritual rename would have regenerated the matrix "
    "over foreign sections in silence while the reader stayed a manual call. "
    "The wire makes the section ask the reader FIRST: a FOREIGN-SECTION pile "
    "REFUSES (E_FSFW_FOREIGN_SECTION naming the rounds AND the names) before "
    "matrix_core is entered at all, so no matrix byte is rendered; a clean "
    "pile runs the unchanged core and matches the doc byte for byte; and a "
    "census disagreement is reported on the one-line detail even when every "
    "round reads clean. Two authorities stay apart on purpose: the reading is "
    "followup_section_foreign's (this file parses no log - it does not even "
    "import os) and the matrix core stays battery_followup's matrix_core, "
    "whose body is unchanged; battery_followup.section_matrix now delegates "
    "through a call-time import so the two modules never import each other at "
    "load. A pile the reader cannot speak about (no recognisable evidence "
    "name, unreadable log, duplicate round) is NOT a refusal: the section runs "
    "as before and the guard code travels on the detail, because a guard must "
    "never invent a refusal for a pile it could not read.",
    "R2370 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/followup-section-foreign-wire-R2370.log, 1380B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-followup-section-foreign-wire(6) in "
    "src/sandbox/reconcile_all.py. LIVE, not a plan: the guard reads the real "
    "pile at VOCABULARY-CLEAN over 460 rounds in rc=0 "
    "(qa/followup-section-foreign-wire-live-R2370.log, 1460B, utf-8 LF no "
    "BOM) and the follow-up dry run shows the guarded section in front of the "
    "real matrix. Tech row 416 stamped [done 2026-11-02 R2370] and one REAL "
    "measured gap row seeded (followup_guard_evidence_scope, AC-FGES1..6 "
    "pre-registered in that row, five anchors zero-occupancy), from this "
    "window own seam: matrix_section takes the evidence path it is given and "
    "guards the literal directory 'qa', so a matrix built from another pile is "
    "protected by a reading of a pile it is not comparing. Gauge after the "
    "stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 explore 10/10 "
    "(tech done 349 -> 350, claimable held at 10). Register: product-face-R2370 "
    "closed through debt_close (open 3->2, done 98->99, 78189B->78192B, "
    "readback ok) and reconcile-battery-R2370 opened first=yes through "
    "debt_append at the measured target 497 suites / 3958 criteria "
    "(78192B->78746B, readback ok).",
    "R2370 honest disclosures: (a) AC-FSFW5 was RED on the first run for a "
    "REAL module defect - to_json emitted the census object after code while "
    "the pinned GUARD_KEYS order puts census before code - and the MODULE was "
    "fixed, not the criterion. (b) The second red was this window own fixture: "
    "it asserted the render line 'verdict=VOCABULARY-CLEAN' against the --json "
    "payload, which carries a JSON key instead; the assertion was corrected to "
    "the pinned serialisation and no criterion was widened. (c) The live dry "
    "run honestly reads matrix FAIL (on-disk=47476B regenerated=47587B) and "
    "that is NOT a defect: the shipped doc describes the R2370 battery (496 "
    "suites / 3952 criteria) and this window added the 497th suite AFTER that "
    "green run, so the doc is stale until the next battery regenerates it; the "
    "FAIL names '(no rewrite)', which is also the read-only proof. (d) The "
    "seed row is appended at the queue tail, so the row at line 417 now reads "
    "BEHIND-HEAD - the standing shape of every tail seed in this queue. (e) "
    "src/os/seed_R2370.py stamps the row by rewriting the whole 1.4MB file in "
    "one write with a read-back; the delta is reported but not predicted, "
    "which is weaker than the shipped writers' byte-prediction discipline - "
    "disclosed rather than dressed up. (f) tasks.md was left untouched: it is "
    "the P-47 canonical board and carries no row for this tech slice, "
    "disclosed rather than silently skipped. (g) This window ran past its "
    "25-minute budget: the battery alone measured 990.9s, and the product face "
    "was still shipped rather than deferred, because the tree was committed "
    "and clean before the battery.",
    "R2370 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply, and this session runs "
    "unelevated, so the definition of the loop hosting this window was left "
    "untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-fifth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2370 tokens: local=~32k api=0 api_reason=verification-then-product "
    "window - one full battery (496 suites, 990.9s) plus its four follow-up "
    "sections and one matrix regeneration, one guard wire and its six-criteria "
    "suite written to criteria pinned thirteen rounds earlier, one caller "
    "rerouted through the wire, one registry wiring line, one two-leg evidence "
    "capture with four adjacent suites, one live capture written through a "
    "single utf-8 LF writer, one board stamp and one measured gap row seeded, "
    "one register close and one successor row opened, and the "
    "state/backlog/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2370] verification-then-product-R2370: the debt "
    "gate named product-face-R2370, so the battery ran FIRST on the committed "
    "6b918367 tree with an empty git status - RUNNER PASS 496/496 suites green "
    "plus reconcile controls 7/7 in 990.9s with birth-site TMP RECLAIM 932/932 "
    "worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2370.log, 804005B, "
    "single writer utf-8 LF through src/os/battery_stream.py) and criteria "
    "total 3952 EXACTLY as pre-registered, so the prediction matched the "
    "measurement with nothing to name; the four follow-up sections ran through "
    "src/os/battery_followup.py, the matrix section FAILED first on the stale "
    "doc and did NOT rewrite it (on-disk=47371B regenerated=47476B), "
    "suite_matrix regenerated docs/sandbox-suite-matrix.md to 496 suites / "
    "3952 criteria and the re-run read all four PASS for VERDICT R2370 PASS; "
    "evidence and matrix committed alone as bd736b53 before any product byte "
    "changed (the R2168 mixed-tree rule). PRODUCT: claimed the tech head the "
    "OFFER reader reported, state/queue/tech.md:416 prefix AC-FSFW1 "
    "(followup_section_foreign_wire), whose AC-FSFW1..AC-FSFW6 were pinned "
    "inside that row at R2357 BEFORE any code, after a fresh anchor check at "
    "HEAD (all five anchors prose and state only, zero executable occupancy). "
    "SHIPPED src/os/followup_section_foreign_wire.py plus "
    "src/os/test_followup_section_foreign_wire.py: the follow-up matrix "
    "section now asks the foreign-section reader FIRST, so a FOREIGN-SECTION "
    "pile REFUSES (E_FSFW_FOREIGN_SECTION naming the rounds and the names) "
    "before matrix_core is entered at all and no matrix byte is rendered, a "
    "clean pile keeps the matrix byte-identical to the pre-wire section, and a "
    "census disagreement is reported on the detail even when every round reads "
    "clean; the reading stays followup_section_foreign's and the matrix core "
    "stays battery_followup's matrix_core (body unchanged), so each law keeps "
    "one owner. SUITE PASS 6/6 twice with an identical criterion digest plus "
    "four adjacent suites green (qa/followup-section-foreign-wire-R2370.log, "
    "1380B, legs=2 identical=True adjacent=4 fails=0), wired "
    "os-followup-section-foreign-wire(6). LIVE: the real pile reads "
    "VOCABULARY-CLEAN over 460 rounds at rc=0 and the guarded section runs in "
    "front of the real matrix (qa/followup-section-foreign-wire-live-R2370.log, "
    "1460B); the REFUSAL branch is proved on fixtures and is NOT claimed as a "
    "live catch. Row stamped and one REAL measured gap seeded "
    "(followup_guard_evidence_scope, AC-FGES1..6: the guard asks a fixed 'qa' "
    "while the section compares the evidence path it was given), floor "
    "FLOOR-MET 5/5 10/10 10/10. Disclosed: (a) AC-FSFW5 first red was a REAL "
    "module defect in the pinned key order and the module was fixed; (b) the "
    "second red was this window own fixture asserting the render line against "
    "a --json payload, corrected without widening a criterion; (c) the live "
    "dry run honestly reads matrix FAIL because this window added the 497th "
    "suite after its own green battery, so the doc is stale until the next "
    "battery - designed state, named '(no rewrite)'; (d) tasks.md untouched: "
    "the P-47 board carries no row for this tech slice."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def block_boundaries(log):
    out = []
    for index, line in enumerate(log):
        if re.match(r"^(?:\d{4}-\d{2}-\d{2} )?R\d+ tokens:", line.strip()):
            out.append(index + 1)
    return out


def prepend_backlog():
    text = read_text(BACKLOG)
    if BACKLOG_ROW[:40] in text:
        print("BACKLOG already carries this row")
        return len(text.encode("utf-8")), len(text.encode("utf-8"))
    before = len(text.encode("utf-8"))
    text = BACKLOG_ROW + "\n" + text
    back = write_text(BACKLOG, text)
    ok = back == text
    print("BACKLOG before=%dB after=%dB readback=%s"
          % (before, len(back.encode("utf-8")), ok))
    return before, len(back.encode("utf-8"))


def main():
    raw = read_text(STATE)
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    tick = data.get("tick", 0) + 1
    data["tick"] = tick
    data["benchmarks_refreshed"] = "2026-11-02"
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    back = write_text(STATE, text)
    if back != text:
        print("STATE readback FAILED")
        return 2
    size = len(text.encode("utf-8"))
    print("STATE tick=%d items=+%d before=%dB after=%dB"
          % (tick, len(ITEMS), before, size))

    prepend_backlog()

    guard = 0
    while True:
        measure = state_fold.measure(size, GATE)
        if not measure["fold_needed"]:
            print("FOLD none needed bytes=%d margin=%d"
                  % (size, measure["margin"]))
            break
        current = read_text(STATE)
        state = json.loads(current)
        log = state["log"]
        ends = block_boundaries(log)
        target = GATE - RESERVE
        chosen = None
        for end in ends:
            if end >= len(log):
                continue
            window = log[:end]
            found = set()
            for line in window:
                found |= set(state_fold.PAT.findall(line))
            rounds = sorted(set(re.findall(r"R(\d{4})", " ".join(window))))
            summary = ("Fold %d: log lines 1..%d folded verbatim into the "
                       "archive at a TRUE round-block boundary; rounds %s; "
                       "tokens %s"
                       % (FOLD_BASE + guard, end,
                          ",".join("R" + r for r in rounds),
                          " ".join(sorted(found))))
            try:
                plan, _folded = state_fold.plan_fold(
                    current.encode("utf-8"), state, 1, end, summary,
                    reserve=0, gate=GATE)
            except Exception as exc:  # noqa: BLE001 - reported, not hidden
                print("FOLD plan refused end=%d %s" % (end, exc))
                continue
            if not plan["token_ok"]:
                print("FOLD token gap end=%d missing=%d"
                      % (end, len(plan["tokens_missing"])))
                continue
            if plan["predicted_bytes"] <= target:
                chosen = (end, summary, plan)
        if chosen is None:
            print("FOLD none fits target=%d bytes=%d" % (target, size))
            break
        end, summary, plan = chosen
        state_fold.fold(REPO, "R2370", FOLD_BASE + guard, 1, end, summary,
                        reserve=0, gate=GATE, execute=True)
        size = os.path.getsize(STATE)
        print("FOLD %d window=1..%d predicted=%dB measured=%dB"
              % (FOLD_BASE + guard, end, plan["predicted_bytes"], size))
        guard += 1
        if guard > 6:
            print("FOLD guard tripped")
            break
    final = state_fold.measure(os.path.getsize(STATE), GATE)
    print("FINAL bytes=%d margin=%d fold_needed=%s verdict=%s"
          % (final["bytes"], final["margin"], final["fold_needed"],
             final["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())