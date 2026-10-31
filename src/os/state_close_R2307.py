"""state_close_R2307.py - fold the log window and append the R2307 items.

The closeout would cross the 78500B waterline by itself (76790B at open), so
the fold runs FIRST, over whole round blocks, with a summary that carries
every window token (the filter iterates until tokens_missing is empty and
refuses otherwise). The fold number is derived from the real archive headers
rather than from a byte scan. The append then goes through state_io.canon and
one atomic replace with a read-back proof.

Dry run by default; --execute writes.
"""

import datetime
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_fold as SF  # noqa: E402
import state_io  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

WINDOW_START = 1
WINDOW_END = 11

HEAD = ("Fold R2307: log lines 1..11 (fold summaries plus the whole R2294 and "
        "R2295 round blocks, disabled and archived verbatim):")

NARRATIVE = (
    "2026-11-01 R2307 (five-silence scan clean at open: tree clean with an empty git "
    "status --short and no index.lock; decisions.md carries 289 non-empty rows EQUAL to "
    "the stored 289-row baseline so no new decision row is presented and zero domain "
    "action is owed; the group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied numbered handoffs; the group orders tail is "
    "unchanged at the 2026-10-31 18:23 baseline; benchmarks refreshed 2026-10-29 inside "
    "the seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, the floors read FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10 with the tech head at line 369 prefix AC-SAP1, and the debt gate "
    "named exactly one first=yes row (product-face-R2307), so this window claimed the "
    "TOP deliverable tech row: the R2294 stamp_exempt_append seed, whose AC-SAP1..AC-SAP6 "
    "criteria were already pinned INSIDE that row BEFORE the code (fresh zero-occupancy "
    "anchor check at HEAD 2026-11-01: stamp_exempt_append, AC-SAP, E_SEAP, "
    "os-stamp-exempt-append and test_stamp_exempt_append hit only prose and state files - "
    "the seed row, the board, state.json, state/debt.md, status-export.json and three "
    "closeout helpers - with no code path). PRODUCT: src/os/stamp_exempt_append.py plus "
    "src/os/test_stamp_exempt_append.py - accepting a NEW closed row stops being a hand "
    "edit of a 380-entry JSON. The declaration own reader is the authority on shape: the "
    "module materialises the post text in a throwaway world and runs "
    "queue_done_stamp_exempt.read_declaration over it instead of carrying a second copy "
    "of the entry rules, and the live (queue, identity) join is the reviewer own "
    "stamp_exempt_review.live_pairs - the suite proves both by patching each import and "
    "watching the reading move. A missing row, an already-declared pair and an ambiguous "
    "pair (one entry covering two live rows) each refuse before any byte of the real file "
    "changes; a dry run is the default and prints before and predicted bytes; an executed "
    "append is one os.replace proved by read-back with no temp residue. SUITE PASS 6/6 "
    "double-run identical with five adjacent suites green through the R2261 "
    "evidence_capture callable (qa/stamp-exempt-append-R2307.log, 850B, one utf-8 LF "
    "single writer), wired os-stamp-exempt-append(6). LIVE on the real 78774B "
    "declaration: a fabricated identity reads E_SEAP_NO_ROW and an already-declared live "
    "pair (main:N1-N7#a69002dc) reads E_SEAP_DUP, both exit 2, and the file sha256 stays "
    "cf14161f0f1df99d. The claim dropped tech claimable to 9, so one real gap row was "
    "seeded (stamp_exempt_prune, AC-SEPR1..AC-SEPR6 pre-registered, five anchors "
    "zero-occupancy) and the gauge closed FLOOR-MET 5/5 10/10 10/10. The battery carries "
    "to R2308 as the register successor row.")

LEDGER = (
    "R2307 tokens: local=~21k api=0 api_reason=product window on the debt register first "
    "item - one writer module with its six pre-registered criteria and its suite, one "
    "REAL module defect and two this-window test defects caught before any evidence, one "
    "dogfooded evidence capture (two legs identical, five adjacent suites green), two "
    "live CLI refusals against the real 78774B declaration with the file proved "
    "byte-identical, one runner wiring line, one real gap row seeded to hold the tech "
    "floor, one close and one seed row through the shipped walkers, one waterline fold, "
    "and the queue/board/state/export closeout; zero cloud calls and zero external API "
    "touches; the battery carries to R2308")

SELF_HEAL = (
    "R2307 self-heal check: BigDomain-OSLoop is registered and its principal still reads "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task; src/os/register_loop_task.ps1 already passes an explicit S4U principal and "
    "needs an elevated shell to apply it, and this session runs unelevated, so the "
    "definition of the loop hosting this window was left untouched. Open local-lane item "
    "for an elevated window (seventy-first consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).")

FOLD_NOTE = (
    " The fold ran BEFORE the append because the closeout would have crossed the "
    "waterline: this window was planned over log lines 1..11 and covered every window "
    "token before writing, and the fold number was derived from the real archive headers "
    "rather than from a byte scan.")

DISCLOSURES = (
    "R2307 honest disclosures: (a) the first suite run was red 2/6 and both reds were "
    "this-window TEST defects, never criteria widened - the patched join fixture returned "
    "a bare pair map where stamp_exempt_review.live_pairs returns (rows, pairs), so the "
    "module unpacked one value into two and both legs died E_SEAP_BAD_GATE; corrected in "
    "the fixture. (b) The next red was a REAL module defect: the reader normalises every "
    "entry to carry until (None when absent) in the order queue/identity/declared/until/"
    "reason, so comparing the post reading with the rendered entry by raw dict equality "
    "refused every append; the fix compares the five fields in the MODULE and no "
    "criterion was relaxed. (c) The third red was the honest one: AC-SAP6 read red "
    "because the runner label was not yet wired, and the wiring landed before the green "
    "run. (d) The live reading could not perform an honest append and that is disclosed "
    "rather than dressed up: every live debt row is already declared, so both live CLI "
    "legs are refusals and the positive path is proven on fixture worlds instead. (e) "
    "tasks.md was left untouched - it is the P-47 canonical board and carries no row for "
    "this tech slice. (f) The gap seed is this window own finding: the writer can now "
    "grow the declaration but nothing can retire a dead acceptance, which is the "
    "opposite rot the reviewer names.")


def fold_number():
    """The next fold number, derived from the real archive headers."""
    stamp = datetime.datetime.now()
    archive = SF.default_archive(ROOT, stamp)
    count = 0
    if os.path.isfile(archive):
        with io.open(archive, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.startswith("# ---") and "fold append" in line:
                    count += 1
    return count + 1, archive


def plan_with_tokens(fold_no):
    """Iterate the summary until the plan reports no missing window token."""
    summary = HEAD
    for _ in range(4):
        plan = SF.fold(ROOT, "R2307", fold_no, WINDOW_START, WINDOW_END,
                       summary, reserve=6000, execute=False)
        missing = plan.get("tokens_missing") or []
        if not missing:
            return plan, summary
        summary = HEAD + " Window tokens: " + " ".join(missing)
    raise SystemExit("E_TOKENS: the summary never covered the window")


def build(text):
    state = json.loads(text.decode("utf-8"))
    before_items = len(state["log"])
    state["tick"] = 2307
    state["log"].extend([NARRATIVE + FOLD_NOTE, LEDGER, SELF_HEAL, DISCLOSURES])
    ascii_only = all(byte < 0x80 for byte in text)
    body = json.dumps(state, ensure_ascii=ascii_only, indent=2)
    return before_items, state_io.canon(body).encode("utf-8")


def write(path, data, label):
    temp = os.path.join(os.path.dirname(path), ".%s.tmp" % label)
    with open(temp, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_READBACK %s" % label)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % label)


def main(argv):
    execute = "--execute" in argv
    fold_no, archive = fold_number()
    plan, summary = plan_with_tokens(fold_no)
    if plan.get("would_fail"):
        raise SystemExit("E_PLAN %r" % (plan.get("would_fail"),))
    print("FOLD %d window %d..%d lines=%d tokens=%d predicted=%dB"
          % (fold_no, WINDOW_START, WINDOW_END, plan["window_lines"],
             plan["tokens_total"], plan["predicted_bytes"]))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    result = SF.fold(ROOT, "R2307", fold_no, WINDOW_START, WINDOW_END,
                     summary, reserve=6000, execute=True)
    if result.get("would_fail"):
        raise SystemExit("E_FOLD %r" % (result.get("would_fail"),))
    post = open(STATE, "rb").read()
    print("FOLD written %dB (predicted %dB) archive=%s"
          % (len(post), result["predicted_bytes"],
             os.path.basename(archive)))
    if len(post) != result["predicted_bytes"]:
        raise SystemExit("E_FOLD_PREDICT")
    before_items, new = build(post)
    print("LOG_ITEMS %d -> %d TICK 2307 BEFORE %dB AFTER %dB DELTA %+d"
          % (before_items, before_items + 4, len(post), len(new),
             len(new) - len(post)))
    write(STATE, new, "state_close_R2307")
    print("WROTE %dB readback ok temp clean" % len(new))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))