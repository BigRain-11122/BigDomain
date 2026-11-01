"""state_close_R2329 - the round ledger for the stamp_exempt_prune window.

Bumps the tick, appends the four log lines this window owes (live reading,
self-heal disclosure, honest disclosures, token ledger), repairs the decision
token baseline that had been stored as a list of single characters since an
unknown window, and closes the debt row this window opened with. Dry run by
default; --execute writes utf-8 with LF.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
DECISIONS = os.path.join(os.path.dirname(os.path.dirname(ROOT)),
                         "docs", "decisions.md")
DEBT = os.path.join(ROOT, "state", "debt.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

TICK = 2329
TOKEN_RE = re.compile(r"[DC]-\d{8}-\d{2}")

LIVE = (
    "R2329 product window: shipped stamp_exempt_prune (the accepted-stamp "
    "declaration can shrink). Retire set derived from stamp_exempt_review's "
    "own MISSING list and queue_done_stamp_exempt's own EXPIRED row status, "
    "dry run default, span surgery keeps every surviving entry byte-identical "
    "on both layouts, post validated through read_declaration, one atomic "
    "replace proved by read-back. LIVE on the real 381-entry declaration: "
    "NOTHING-TO-RETIRE (missing=0 expired=0, 79026B unchanged). SUITE PASS "
    "6/6 twice identical through evidence_capture "
    "(qa/stamp-exempt-prune-R2329.log, 1665B) with four adjacent suites green; "
    "wired os-stamp-exempt-prune(6)."
)

SELF_HEAL = (
    "R2329 self-heal check: BigDomain-OSLoop is still registered and its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal and needs an elevated shell to "
    "apply, so this session reports it instead of guessing (ninety-first "
    "consecutive disclosure, carried as loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2329 honest disclosures: (a) two real module defects were caught before "
    "any evidence and fixed in the module, never by widening a criterion: the "
    "reviewer's entry index is 1-BASED and collided with my 0-based expired "
    "index (one retiral was silently dropped, which is exactly the shape a "
    "product face must never ship), and the per-index descending splice mapped "
    "an earlier index onto bytes a later cut had already deleted; one "
    "this-window test defect (sliced the pre-splice text) was fixed in the "
    "test. (b) The live declaration reads NOTHING-TO-RETIRE, so no surgery was "
    "performed on the real file - the module is the treatment, not a forced "
    "operation, and a window that pruned a healthy declaration would be the "
    "defect. (c) The decision token baseline in state.json had been stored as "
    "a list of single CHARACTERS (2911 entries of ',', '-', digits) rather "
    "than the D-/C- ids, so every window since it broke re-judged all 61 "
    "tokens as new; repaired this window to the real token set and disclosed "
    "here rather than quietly resetting it."
)

LEDGER = (
    "R2329 tokens: local=~42k api=0 api_reason=one product window with its "
    "suite, its evidence ritual and its queue/export bookkeeping - no cloud "
    "call was needed for a stdlib-only module with a live local oracle"
)

DEBT_CLOSE = (
    "- [x] opened=R2328 | item=product-face-R2329 | note=R2329 claimed tech "
    "line 382 (AC-SEPR1..AC-SEPR6 pinned inside the row before the code) and "
    "shipped stamp_exempt_prune with its suite, evidence and one runner entry; "
    "tech row closed and one seed added so claimable stays 10 | closed=R2329"
)

BACKLOG_DONE = (
    "- [x] [done 2026-11-01 R2329] R2329 first item: BACK TO THE PRODUCT FACE "
    "on the row the reader names - claimed tech line 382 prefix AC-SEPR1 "
    "(claimable=10), ran a fresh zero-occupancy anchor check at HEAD, and "
    "shipped stamp_exempt_prune with AC-SEPR1..AC-SEPR6 green 6/6 twice "
    "identical (qa/stamp-exempt-prune-R2329.log, 1665B, four adjacent suites "
    "green), committed BEFORE any battery per the R2168 mixed-tree rule. LIVE: "
    "NOTHING-TO-RETIRE on the real 381-entry declaration. Tech floor refilled "
    "with one real gap row (stamp_exempt_guard, AC-SEG1..AC-SEG6 "
    "pre-registered). Next item is the battery on this committed tree with the "
    "pre-registered target of 472 suites / 3808 criteria."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != text:
        raise SystemExit("E_READBACK %s" % path)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % path)


def main(argv):
    state = json.loads(read_text(STATE))
    decisions = read_text(DECISIONS) if os.path.isfile(DECISIONS) else ""
    tokens = sorted(set(TOKEN_RE.findall(decisions)))
    backlog = read_text(BACKLOG).split("\n")
    debt = read_text(DEBT).split("\n")
    print("tick %d -> %d" % (state.get("tick"), TICK))
    print("decision tokens: was %d (types=%s) -> %d real ids"
          % (len(state.get("last_dec_tokens") or []),
             sorted({type(x).__name__ for x in
                     (state.get("last_dec_tokens") or [])}), len(tokens)))
    print("backlog line 1 starts with: %s" % backlog[0][:60])
    open_rows = [row for row in debt if row.startswith("- [ ] opened=")]
    print("debt open rows: %d" % len(open_rows))
    for row in open_rows:
        print("  " + row[:90])
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    state["tick"] = TICK
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = len(decisions.split("\n"))
    log = state.get("log") or []
    for line in (LIVE, SELF_HEAL, HONEST, LEDGER):
        log.append(line)
    state["log"] = log
    write_text(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    backlog[0] = BACKLOG_DONE + (
        " [carried " + backlog[0].split("[carried ", 1)[1]
        if "[carried " in backlog[0] else "")
    write_text(BACKLOG, "\n".join(backlog))
    for index, row in enumerate(debt):
        if row.startswith("- [ ] opened=R2328 | item=product-face-R2329"):
            debt[index] = DEBT_CLOSE
            break
    write_text(DEBT, "\n".join(debt))
    print("WROTE state.json, backlog.md, debt.md with read-back")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))