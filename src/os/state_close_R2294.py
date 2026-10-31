"""state_close_R2294.py - append the R2294 product window items to the log.

Dry run by default; --execute writes atomically with a read-back proof. The
JSON payload may only change by the intended fields, and the layout is
normalised through state_io.canon so the item indent stays canonical.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_io  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

NARRATIVE = (
    "2026-10-31 R2294 (five-silence scan clean at open: tree clean with an empty git "
    "status --short and no index.lock; decisions.md carries 289 non-empty rows EQUAL to "
    "the stored 289-row baseline, so no new decision row is presented and zero domain "
    "action is owed; the group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied numbered handoffs; the group orders tail is "
    "unchanged at the 2026-10-31 18:23 baseline consumed in R2278; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay blocked-on-CEO, "
    "the weekly proposal duty is met by BD-PROP-005, the queue floors read FLOOR-MET "
    "main 5/5 tech 10/10 explore 10/10 with queue_head naming line 360 (prefix AC-SER1, "
    "skipped_before=4, claimable=10) as the tech head, and the debt gate named exactly "
    "one first=yes row (product-face-R2294), so this window claimed the TOP deliverable "
    "tech row: the R2280 stamp_exempt_review seed, its AC-SER1..AC-SER6 criteria already "
    "pinned INSIDE that row BEFORE the code (fresh zero-occupancy anchor check at HEAD "
    "2026-10-31: stamp_exempt_review, AC-SER, E_SER, os-stamp-exempt-review, "
    "test_stamp_exempt_review and unmatched_review were all git grep -F rc 1, every hit "
    "being prose - the row, the board, the state log and two closeout helpers - "
    "disclosed). PRODUCT: src/os/stamp_exempt_review.py plus "
    "src/os/test_stamp_exempt_review.py - an accepted-stamp declaration that can rot "
    "silently in either direction is now a reading. queue_done_stamp_exempt joins 380 "
    "accepted entries with 380 live debt rows and asks only whether an entry still "
    "matches; it never reports a declared entry whose row was annotated after the fact "
    "(the text digest moves) or a debt row born after the declaration (no entry at all), "
    "so the acceptance stays green while the pair drifts. The reviewer reads BOTH sides "
    "and lists drift BOTH ways - MISSING names a declared entry matching no live row "
    "with its declaration entry index, UNDECLARED names a live debt row carrying no "
    "entry with its file and line - and it never guesses which side is stale. Neither "
    "reading is re-implemented: the gate comes from queue_done_stamp.audit_root and the "
    "declaration plus the row identity law from queue_done_stamp_exempt "
    "(read_declaration, identity_of, queue_of_path), and the suite proves both imports by "
    "patching each one. The split must agree with the reader own numbers before any "
    "verdict is issued (matched equals exempt_today plus exempt_expired, missing equals "
    "unmatched_count, violations equal matched plus undeclared) or it refuses with "
    "E_SER_COUNT instead of printing a drift list nobody can trust. An absent "
    "declaration refuses as E_SER_UNPINNED rather than reading a 380-row drift (with no "
    "acceptance record there is nothing to review), broken JSON as E_SER_BAD_DECL, a "
    "missing queue as E_SER_BAD_GATE and one entry matching two rows in the same queue "
    "as E_SER_AMBIGUOUS. Nothing is written and no clock is read. EVIDENCE: SUITE PASS "
    "6/6 double-run with identical criterion lines and five adjacent queue suites green "
    "through the src/os/evidence_capture.py callable (qa/stamp-exempt-review-R2294.log, "
    "1844B, one utf-8 LF single writer, never a shell redirection), wired "
    "os-stamp-exempt-review(6). LIVE: STAMP EXEMPT REVIEW round=R2294 "
    "declaration=PINNED entries=380 violations=380 matched=380 exempt=380 expired=0 "
    "missing=0 undeclared=0 verdict=NO-DRIFT, with the declaration and tech.md proved "
    "byte-unchanged by the reading. The claim dropped tech claimable to 9, so one real "
    "gap row was seeded from this window own finding (stamp_exempt_append, "
    "AC-SAP1..AC-SAP6 pre-registered, five anchors git grep -F zero-occupancy rc=1) and "
    "the gauge closed FLOOR-MET 5/5 10/10 10/10; the seeded row sits at the file tail and "
    "therefore reads BEHIND-HEAD against line 362, disclosed rather than reshuffling the "
    "queue by hand. Register closed through its own writer (debt_close line 66, open 2 to "
    "1, done 43 to 44, readback ok) and product-face-R2295 opened first=yes through "
    "debt_append (before 39397B after 39875B, readback ok) naming the battery. Honest "
    "score: a 2-point product window."
)

LEDGER = (
    "R2294 tokens: local=~20k api=0 api_reason=product window on the debt register first "
    "item - one reader module with its six pre-registered criteria and its suite, three "
    "this-window test expectations corrected against the measured truth, one dogfooded "
    "evidence capture (two legs identical, five adjacent suites green), one live CLI "
    "reading of the real 380-entry declaration, one runner wiring line, one real gap row "
    "seeded to hold the tech floor, two register writes through the shipped close and "
    "append writers, and the queue/board/state/export closeout; zero cloud calls and zero "
    "external API touches; the battery carries to R2295"
)

SELF_HEAL = (
    "R2294 self-heal check: BigDomain-OSLoop is registered and its principal still reads "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task; src/os/register_loop_task.ps1 already passes an explicit S4U principal and "
    "needs an elevated shell to apply it, and this session runs unelevated, so the "
    "definition of the loop hosting this window was left untouched. Open local-lane item "
    "for an elevated window (fifty-ninth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2294 honest disclosures: (a) the first suite run was red 3/6 and two of the three "
    "reds were this-window TEST defects, never criteria widened - the AC-SER2 leg "
    "expected the patched-reader refusal to cross a subprocess boundary (it cannot: a "
    "child interpreter starts unpatched, so the in-process call proves E_SER_COUNT and "
    "the CLI leg honestly reads its own DRIFT at exit 2), and the AC-SER5 ambiguity "
    "fixture put the two identical rows in DIFFERENT queue files, which is not ambiguous "
    "because identity is keyed per queue, so the fixture now duplicates the row inside "
    "tech.md. (b) The AC-SER6 red was the honest one: the runner label was not yet wired, "
    "and the wiring landed before the green run. (c) The refusal on an absent "
    "declaration is E_SER_UNPINNED at exit 3 rather than a drift reading, which is a "
    "design choice stated here: with no acceptance record every row would read "
    "UNDECLARED and the report would blame the gate for a missing declaration. (d) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries no row for "
    "this tech slice, so there was no checkbox to tick, which is disclosed rather than "
    "silently skipped."
)


def build():
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    before_items = len(state["log"])
    state["tick"] = 2294
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES])
    ensure_ascii = all(b < 0x80 for b in raw)
    text = json.dumps(state, ensure_ascii=ensure_ascii, indent=2)
    text = state_io.canon(text)
    new = text.encode("utf-8")
    return raw, state, before_items, new


def main(argv):
    execute = "--execute" in argv
    raw, state, before_items, new = build()
    print("LOG_ITEMS %d -> %d" % (before_items, len(state["log"])))
    print("TICK %s" % state["tick"])
    print("BEFORE %dB AFTER %dB DELTA %+d" % (len(raw), len(new), len(new) - len(raw)))
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    folder = os.path.dirname(STATE)
    temp = os.path.join(folder, ".closeout_R2294.tmp")
    with open(temp, "wb") as sink:
        sink.write(new)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    if back != new:
        print("E_BACK read-back does not match")
        return 3
    if os.path.exists(temp):
        print("E_TEMP residue left")
        return 3
    print("WROTE %dB readback ok temp clean" % len(back))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))