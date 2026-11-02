"""closeout_R2373 - tick, log items and the backlog row for this window."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
GATE = 78500

ITEMS = [
    "2026-11-02 R2373 verification-then-product window (five-silence scan "
    "clean at open: empty git status at HEAD ee2bab1e, no .git/index.lock; "
    "scan_five_still read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=124 "
    "tokens=81 new=0, the group orders tail still the 2026-11-01 10:4x "
    "model-policy baseline already acknowledged as non-execution, and "
    "benchmarks refreshed 2026-11-02 inside the seven-day gate). The debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2372, so the battery ran FIRST "
    "on the committed tree: RUNNER FAIL 498/499 suites with TWO failed "
    "assertions, kept as the red leg (qa/reconcile-all-R2373.log, 807598B, "
    "single writer utf-8 LF through src/os/battery_stream.py).",

    "R2373 the red was an EVIDENCE DIALECT, found at its birth site and not "
    "widened away: reconcile-daily-census read cd7-live-real-tree exit=2 "
    "DRIFT-FLAG, and qa_writer_census.py --check named the file and the class "
    "- qa/residue-triage-repin-idempotent-live-R2372.log class=other, because "
    "that writer embedded a child CLI stdout VERBATIM and the Windows console "
    "had put six CRLF lines inside a file the census reads as one utf-8 LF "
    "dialect. src/os/evidence_R2372.py gained one transport() call that "
    "normalises the child EOL only, the file was regenerated through that "
    "writer (1117B, crlf=0), and its line payload is identical to the old one "
    "except the two byte-count lines which now measure the normalised text "
    "(190 -> 186 after stripping the CR). The census then read DRIFT-CLEAN "
    "files=2359 tee=1830 baselined=529 flags=0 with the BASELINE UNTOUCHED. "
    "Committed alone before the retry.",

    "R2373 retry and follow-ups: on the committed repair tree the battery read "
    "RUNNER PASS 499/499 suites plus reconcile controls 7/7 in 1267.0s with "
    "criteria total 3970 EXACTLY as pre-registered against R2372 (498/3964) "
    "and birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2373-retry.log, 807623B, crlf=0, single writer utf-8 "
    "LF through src/os/battery_stream.py, never a shell redirection). The four "
    "sections ran through src/os/battery_followup.py and the matrix section "
    "FAILED first on the stale doc (on-disk=47697B regenerated=47836B) and did "
    "NOT rewrite it, which is the designed order; src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md to 499 suites / 3970 criteria "
    "(47836B) and the re-run read all four PASS for VERDICT R2373 PASS. The "
    "evidence and the matrix were committed ALONE as 4b2b4f7d before any "
    "product byte changed (the R2168 mixed-tree rule).",

    "R2373 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:419 prefix AC-CUR1 (contract_usage_renderer), whose "
    "AC-CUR1..AC-CUR6 were pinned INSIDE that row at R2366 BEFORE any code, "
    "after a fresh anchor check at HEAD: contract_usage_renderer, AC-CUR, "
    "E_CUR, os-contract-usage-renderer and test_contract_usage_renderer hit "
    "ONLY prose and state files (docs/status-export.json, src/os/backlog.md, "
    "src/os/board_R2366.py, src/os/closeout_R2366.py, src/os/exit_R2372-era "
    "export scripts, src/os/heartbeat_R2366.py, src/os/seed_R2366.py, "
    "src/os/state.json, state/queue/tech.md) with zero executable occupancy.",

    "R2373 the collapse: shipped src/os/contract_usage_renderer.py, which now "
    "owns the ONE vocabulary of a CLI contract block - the three required keys, "
    "the flag spelling and the honest '(none)' - in two shapes: block() for "
    "the guard's two-line usage and inline() for the wire's one-line house "
    "line. Both shapes are the only format strings in the tree for this "
    "contract (the guard writes none, the wire writes none, and the wire asks "
    "runner_arg_guard.contract_line rather than importing the renderer "
    "directly, so the guard stays the exported door). A contract that lost a "
    "key refuses with E_CUR_CONTRACT_MISSING_<KEY> instead of rendering a "
    "partial block, a non-sequence known_flags reads "
    "E_CUR_CONTRACT_BAD_KNOWN_FLAGS, and the guard's asked path turns that "
    "refusal into its own exit 3 while the wire keeps its published "
    "E_BFH_NO_CONTRACT at exit 5.",

    "R2373 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus three adjacent suites green "
    "(qa/contract-usage-renderer-R2373.log, 1665B, legs=2 identical=True "
    "adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-contract-usage-renderer(6) so the "
    "registry reads 500 suites / 3976 criteria. LIVE, not a plan: on the real "
    "tree qa/contract-usage-renderer-live-R2373.log (477B, crlf=0) reads "
    "verdict=LIVE-COLLAPSED with block_guard_equals_module True, "
    "line_guard_equals_module True, guard_published_identical True and "
    "wire_house_identical True, i.e. both CLIs answer through the one module "
    "and both texts are byte-identical to what R2366 published. Tech row 419 "
    "stamped [done 2026-11-02 R2373] (bracket payload 22 chars inside the "
    "60-char stamp law, predicted=measured 1472542B -> 1474273B) and one REAL "
    "measured gap row seeded (own_usage_block_renderer, AC-OUB1..AC-OUB6 "
    "pre-registered in that row, five anchors zero-occupancy): the guard's own "
    "--guard-help is a hand-written literal and the wire composes its own flag "
    "line from strings inside usage_text, so a tool's OWN block still has no "
    "owner one layer below the contract block this window collapsed. Gauge "
    "after the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 explore "
    "10/10 and the reader now offers line 420 prefix AC-QFE1. Register: "
    "reconcile-battery-R2372 closed through debt_close (open 3->2, done "
    "101->102, 79854B->79857B, readback ok) and reconcile-battery-R2373 "
    "opened first=yes through debt_append at the measured successor target 500 "
    "suites / 3976 criteria (79857B->80360B, readback ok).",

    "R2373 honest disclosures: (a) the FIRST battery invocation was piped "
    "through Out-Null and was cancelled by the five-minute no-output rule - "
    "the R2235/R2247/R2268/R2349/R2371 trap repeated; an ownership check "
    "proved zero surviving reconcile/battery processes, no evidence file and a "
    "clean git status before the unfiltered rerun, so nothing was lost and "
    "nothing was cleaned. (b) The red leg was a REAL defect in a previous "
    "window's writer and it was repaired at the birth site with the payload "
    "proved, not by adding a census waiver and not by widening the baseline. "
    "(c) AC-CUR2 forced TWO shapes to survive in the renderer, because the "
    "guard's block and the wire's house line are genuinely different texts and "
    "both are published; the honest reading is one OWNER of the vocabulary, "
    "not one line shape, and that is what this window built. (d) The suite's "
    "first AC-CUR1 run was RED because it patched a function and then spawned "
    "a fresh CLI, where the patch cannot travel; the assertion now patches "
    "in-process and reads the printed block through a redirected stdout, and "
    "no criterion was widened. (e) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice, disclosed rather "
    "than silently skipped. (f) This window ran past its 25-minute budget by a "
    "wide margin because the first battery went red and the retry cost another "
    "1267.0s; the product face was still shipped rather than deferred, because "
    "the retry tree was committed and clean before any product byte changed.",

    "R2373 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply, and this session runs "
    "unelevated, so the definition of the loop hosting this window was left "
    "untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-eighth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",

    "R2373 tokens: local=~41k api=0 api_reason=verification-then-product "
    "window - two full batteries (499 suites each; the first red on an "
    "evidence dialect, the retry 1267.0s) plus one census diagnosis, one "
    "birth-site writer repair with its regenerated evidence, four follow-up "
    "sections and one matrix regeneration, one renderer module and its "
    "six-criteria suite written to criteria pinned seven rounds earlier, two "
    "callers rerouted through it with byte-identical published text, one "
    "registry wiring line, one two-leg evidence capture with three adjacent "
    "suites, one live capture through a single utf-8 LF writer, one board "
    "stamp and one measured gap row seeded, one register close and one "
    "successor row opened, and the state/backlog/export/heartbeat closeout; "
    "zero cloud calls and zero external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2373] verification-then-product-R2373: the debt "
    "gate named CLAIM-FIRST item=reconcile-battery-R2372, so the battery ran "
    "FIRST on the committed ee2bab1e tree - and it came back RED ON EVIDENCE, "
    "NOT CODE: 498/499 suites with two failed assertions, kept as the red leg "
    "(qa/reconcile-all-R2373.log), both reading reconcile-daily-census cd7 "
    "exit=2 DRIFT-FLAG. qa_writer_census.py --check named the cause: "
    "qa/residue-triage-repin-idempotent-live-R2372.log carried six CRLF lines "
    "inside a file the census reads as one utf-8 LF dialect (class=other), "
    "because that writer embedded a child CLI stdout verbatim. Repaired at the "
    "birth site (one transport() normalisation in src/os/evidence_R2372.py, "
    "file regenerated through it, payload identical except the two byte-count "
    "lines), census then DRIFT-CLEAN files=2359 tee=1830 baselined=529 flags=0 "
    "with the baseline UNTOUCHED. Retry on the committed repair tree: RUNNER "
    "PASS 499/499 suites plus controls 7/7 in 1267.0s, criteria total 3970 "
    "EXACTLY as pre-registered, TMP RECLAIM 932/932 (qa/reconcile-all-R2373-"
    "retry.log, 807623B, crlf=0); four follow-up sections PASS after the "
    "designed matrix FAIL and its regeneration to 499/3970 at 47836B, VERDICT "
    "R2373 PASS, evidence and matrix committed alone as 4b2b4f7d. PRODUCT: "
    "claimed state/queue/tech.md:419 prefix AC-CUR1 (contract_usage_renderer), "
    "criteria pinned in that row at R2366 BEFORE any code, anchors prose-only "
    "at HEAD. SHIPPED src/os/contract_usage_renderer.py: the contract block "
    "now has ONE owner - the three required keys, the flag spelling and the "
    "honest '(none)' - in two shapes (block for the guard's two-line usage, "
    "inline for the wire's one-line house line) because both texts are "
    "published and must not change; the guard writes no format string and the "
    "wire writes none and asks runner_arg_guard.contract_line, so the guard "
    "stays the exported door. A missing key refuses with "
    "E_CUR_CONTRACT_MISSING_<KEY> (guard exit 3, wire keeps its published "
    "E_BFH_NO_CONTRACT at exit 5) instead of rendering a partial block. SUITE "
    "PASS 6/6 twice with an identical criterion digest plus three adjacent "
    "suites green (qa/contract-usage-renderer-R2373.log, 1665B), wired "
    "os-contract-usage-renderer(6) so the registry reads 500/3976. LIVE: "
    "qa/contract-usage-renderer-live-R2373.log (477B, crlf=0) reads "
    "verdict=LIVE-COLLAPSED with both published texts byte-identical to R2366. "
    "Row 419 stamped (1472542B -> 1474273B) and one REAL measured gap seeded "
    "(own_usage_block_renderer, AC-OUB1..6: a tool's OWN argument block is "
    "still a hand-written literal and the wire's own flag line is composed "
    "from strings, so a third tool would copy one), gauge FLOOR-MET 5/5 10/10 "
    "10/10, reader now offers line 420 AC-QFE1. Register: battery-R2372 "
    "closed, battery-R2373 opened first=yes at 500 suites / 3976 criteria. "
    "Disclosed: the first battery invocation died to the Out-Null no-output "
    "trap with zero survivors and zero evidence; AC-CUR2 forced two shapes to "
    "survive; AC-CUR1's first assertion patched a function and then spawned a "
    "process, so it now patches in-process; the window overran its budget "
    "because of the red-then-retry."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def prepend_backlog():
    text = read_text(BACKLOG)
    if BACKLOG_ROW[:60] in text:
        print("BACKLOG already carries this row")
        return 0
    before = len(text.encode("utf-8"))
    back = write_text(BACKLOG, BACKLOG_ROW + "\n" + text)
    print("BACKLOG before=%dB after=%dB readback=%s"
          % (before, len(back.encode("utf-8")), back == BACKLOG_ROW + "\n"
             + text))
    return 0


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
    measure = state_fold.measure(size, GATE)
    print("FOLD needed=%s margin=%d"
          % (measure["fold_needed"], measure["margin"]))
    prepend_backlog()
    return 0


if __name__ == "__main__":
    sys.exit(main())