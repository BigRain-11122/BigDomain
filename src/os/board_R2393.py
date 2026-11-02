"""Close the claimed tech row and update the carried battery rows (R2393).

Text edits only, each proven by an exact occurrence count and a predicted
byte delta, so a wrong anchor refuses instead of corrupting a board. ASCII
source, stdlib only, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

TECH = os.path.join(REPO, "state", "queue", "tech.md")
DEBT = os.path.join(REPO, "state", "debt.md")

ROW_HEAD = ("- [ ] P2 tech seed (R2392, from this window own measured seam): "
            "`src/os/refused_check_declaration_face.py`")

DISCHARGED = (
    "  DISCHARGED R2393 (line 451, AC-RCDF1..AC-RCDF6): "
    "src/os/refused_check_declaration_face.py plus its suite shipped against "
    "the criteria pinned at R2392. The module owns ONE derivation - the "
    "declaration's own declared_by, read through residue_triage."
    "load_declaration at call time - and ages nothing, so the refusal code a "
    "check already reported cannot move; residue_triage_append carries it on "
    "the refused payload, so --json and the detail prose name one boundary. "
    "SUITE PASS 6/6, two legs identical digest A2958D41F7D143ED, three "
    "adjacent suites green (residue_triage_append, "
    "append_check_status_precedence, residue_triage), wired "
    "os-refused-check-declaration-face(6). LIVE: --check --round R1755 --json "
    "now reads declared_by=R2391 where R2392 measured \"-\", at exit 3 with "
    "the same E_RTA_UNREADABLE (qa/refused-check-declaration-face-live-"
    "R2393.log). DISCLOSED: AC-RCDF2's pinned wording said a MISSING "
    "declaration keeps E_RTA_UNREADABLE, but the shipped check answers "
    "UNPINNED/RESIDUE at exit 2 because the status face still speaks - the "
    "leg pins that reading plus the unreadable case where the refusal really "
    "is E_RTA_UNREADABLE, so the substance (the unknown stays \"-\" and no "
    "code moves) is what is measured, and no behaviour was changed to fit "
    "the wording.")

SEED_TIMEOUT = (
    "- [ ] P2 tech seed (R2393, from this window own measured seam): "
    "`src/os/runner_suite_timeout_headroom.py` - the battery's per-suite cap "
    "is 300s and the slowest registered suite MEASURED 183.3s (R2393 leg 1) "
    "and 194.9s (leg 2), so a loaded machine aborts a whole battery with no "
    "code defect at all: R2393 leg 3 died on "
    "ledger/test_apimarket_report_claims.py after exactly 300s, and a third "
    "of the machine's day belonged to other companies' lanes. Product: a "
    "reading that derives every registered suite's own measured duration from "
    "the evidence pile and reports the HEADROOM each carries against the "
    "cap, naming the suites inside a warning band instead of leaving the "
    "first sign of load to be a dead battery. Criteria AC-RTH1..AC-RTH6 "
    "pre-registered HERE BEFORE any code: AC-RTH1 the durations are read "
    "from the runner's own evidence lines and a patched reader moves them; "
    "AC-RTH2 headroom is cap minus the slowest measured leg, reported "
    "per suite, never a canned number; AC-RTH3 a suite inside the band is "
    "named and the verdict reads BAND-HIT while an all-comfortable pile "
    "reads HEADROOM-CLEAN at exit 0; AC-RTH4 a suite with no measured leg "
    "reads NO-MEASURE rather than being counted comfortable; AC-RTH5 CLI "
    "exits 0/2/3/5 with a byte-stable --json over pinned keys; AC-RTH6 pure "
    "ASCII, stdlib only, no clock, no network, read-only, plus its own "
    "reconcile label. Anchors zero-occupancy at HEAD 2026-11-03: "
    "runner_suite_timeout_headroom, AC-RTH, E_RTH, "
    "os-runner-suite-timeout-headroom, test_runner_suite_timeout_headroom.")

SEED_LEDGER = (
    "- [ ] P2 tech seed (R2393, from this window own measured seam): "
    "`src/os/ledger_line_shape_guard.py` - the ledger law is "
    "LEDGER_PREFIX_RE = ^R(\\d{3,5}) tokens: and nothing checks a ledger line "
    "BEFORE it is appended, so the R2392 closeout wrote "
    "\"2026-11-02 R2392 tokens: ...\" with a date prefix, round 2392 read "
    "rounds_without_ledger, and four ledger suites plus the census went red "
    "on a tree nobody had touched (measured at R2393 and repaired by an "
    "11-byte surgical edit). Product: the shape is asked of ledger_lines own "
    "law at the write path, so a candidate line that does not parse is "
    "refused with the failing token named instead of being appended and "
    "discovered a window later. Criteria AC-LLSG1..AC-LLSG6 pre-registered "
    "HERE BEFORE any code: AC-LLSG1 the acceptance law is imported from "
    "ledger_lines.parse_ledger_line and a patched parser moves the verdict; "
    "AC-LLSG2 a date-prefixed candidate is refused naming the prefix, and a "
    "conforming one is accepted; AC-LLSG3 the local and api fields are "
    "validated by the shipped parse, never re-parsed here; AC-LLSG4 a "
    "refusal writes no byte and a dry run predicts the exact post size; "
    "AC-LLSG5 CLI exits 0/2/3/5 with a byte-stable --json over pinned keys; "
    "AC-LLSG6 pure ASCII, stdlib only, no clock, no network, plus its own "
    "reconcile label. Anchors zero-occupancy at HEAD 2026-11-03: "
    "ledger_line_shape_guard, AC-LLSG, E_LLSG, os-ledger-line-shape-guard, "
    "test_ledger_line_shape_guard.")

R2387_TAIL = "runs FIRST next window on the committed tree with zero product edits"
R2387_EXTRA = (
    " | note_appended_R2393: the battery DID run three times this window on "
    "the committed tree and is still not discharged - leg 1 (qa/reconcile-all-"
    "R2393.log) read 514/519 suites with 6 failed assertions and named two "
    "REAL birth-site defects nobody had touched (the R2392 ledger item "
    "carried a date prefix the ^R<n> tokens: law refuses, and the R2388 live "
    "capture was mixed-dialect), both repaired and committed alone as "
    "a9c946e7; leg 2 (qa/reconcile-all-R2393-retry.log) read 518/519 with the "
    "ONLY red being a derived counter the repair invalidated "
    "(self_drive.log_lines_in_window stored 8 recomputed 7), re-derived from "
    "the checker own recomputation and now 21/21 PASS; leg 3 "
    "(qa/reconcile-all-R2393-retry2.log) aborted on a per-suite 300s timeout "
    "in ledger/test_apimarket_report_claims.py, which MEASURED 183.3s and "
    "194.9s in the two earlier legs - a load artefact, not a code defect, and "
    "now its own seed row. No RUNNER PASS exists for this tree, so the row "
    "stays OPEN with the successor target 521 suites / 4102 criteria (520/4096 "
    "plus this window os-refused-check-declaration-face suite).")

R2392_TAIL = "the fold runs after the layout is proven canonical."
R2392_EXTRA = (
    " | note_appended_R2393: this row is the same obligation the "
    "reconcile-battery-R2387 row carries and stays OPEN until one green "
    "RUNNER PASS walks the tree; R2393 attempted it three times (see that "
    "row) and measured two real defects, repairing both, without reaching a "
    "green leg.")


def edit(path, pairs):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    before = len(text.encode("utf-8"))
    for needle, replacement in pairs:
        count = text.count(needle)
        if count != 1:
            raise SystemExit("REFUSED: %r appears %d times in %s"
                             % (needle[:60], count, os.path.basename(path)))
        text = text.replace(needle, replacement, 1)
    after = len(text.encode("utf-8"))
    print("%s %d -> %d bytes (delta %+d)"
          % (os.path.basename(path), before, after, after - before),
          flush=True)
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return len(handle.read().encode("utf-8")) == after


def main(argv):
    dry = "--execute" not in argv
    tech_pairs = [
        (ROW_HEAD, "- [x] [done 2026-11-03 R2393] "
         + ROW_HEAD[len("- [ ] "):]),
    ]
    if dry:
        print("DRY: tech row close + discharged line + two seeds; "
              "debt row notes appended")
        return 0
    # 1. stamp the row
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    head = "- [ ] P2 tech seed (R2392, from this window own measured seam):"
    if text.count(head) != 1:
        raise SystemExit("REFUSED: the claimed row head is not unique")
    text = text.replace(head, "- [x] [done 2026-11-03 R2393] P2 tech seed "
                        "(R2392, from this window own measured seam):", 1)
    # 2. the discharged line goes right after that row's own line
    lines = text.split("\n")
    index = [i for i, line in enumerate(lines)
             if line.startswith("- [x] [done 2026-11-03 R2393] P2 tech seed")
             and "refused_check_declaration_face" in line]
    if len(index) != 1:
        raise SystemExit("REFUSED: the stamped row is not unique")
    lines.insert(index[0] + 1, DISCHARGED)
    # 3. two seed rows at the tail
    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("")
    lines.append(SEED_TIMEOUT)
    lines.append("")
    lines.append(SEED_LEDGER)
    lines.append("")
    body = "\n".join(lines)
    with io.open(TECH, "w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    print("tech.md written %d bytes" % len(body.encode("utf-8")), flush=True)
    ok_debt = edit(DEBT, [(R2387_TAIL, R2387_TAIL + R2387_EXTRA),
                          (R2392_TAIL, R2392_TAIL + R2392_EXTRA)])
    print("debt.md verified=%s" % ok_debt, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))