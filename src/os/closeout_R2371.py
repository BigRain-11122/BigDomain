"""closeout_R2371.py - append this window's items, then fold if the gate demands.

One-off for the round, same shape as closeout_R2370: the state file is written
through state_io.canon, the backlog row is prepended at the claimed-board top,
and any fold runs through state_fold.fold.

Usage: python src/os/closeout_R2371.py
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
FOLD_BASE = 647

ITEMS = [
    "2026-11-02 R2371 verification-then-product window (five-silence scan "
    "clean at open: empty git status at ee715015-era HEAD 5d9485d2 after the "
    "evidence commit, no .git/index.lock; LEDGER atbd_lines=0 "
    "unreplied_groups=0, DEC rows=124 tokens=81 new=0, group orders tail "
    "still the 2026-11-01 10:4x model-policy baseline already acknowledged as "
    "non-execution, benchmarks refreshed 2026-11-02 inside the seven-day "
    "gate). The debt gate named CLAIM-FIRST item=reconcile-battery-R2370, so "
    "the battery ran FIRST on the committed tree: RUNNER PASS 497/497 suites "
    "green plus reconcile controls 7/7 in 987.8s with birth-site TMP RECLAIM "
    "932/932 worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2371.log, "
    "804580B, single writer utf-8 LF through src/os/battery_stream.py, never "
    "a shell redirection) and criteria total 3958 EXACTLY as pre-registered, "
    "so the prediction matched the measurement with no correction and nothing "
    "to name.",
    "R2371 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=47476B regenerated=47582B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 497 suites / 3958 criteria (47582B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2371 PASS. The evidence and the matrix were committed ALONE as 5d9485d2 "
    "before any product byte changed (the R2168 mixed-tree rule).",
    "R2371 product face, the row the reader named: CLAIMED state/queue/tech.md"
    ":417 prefix AC-RWAG1 (review_window_wire_argument_guard), whose "
    "AC-RWAG1..AC-RWAG6 were pinned INSIDE that row at R2359 BEFORE any code, "
    "after a fresh anchor check at HEAD: review_window_wire_argument_guard / "
    "AC-RWAG / E_RWAG hit only prose and state files (the seed row, "
    "src/os/closeout_R2359.py, src/os/backlog.md) and "
    "os-review-window-wire-argument-guard / "
    "test_review_window_wire_argument_guard were zero-occupancy at HEAD.",
    "R2371 the guard: shipped src/os/review_window_wire_argument_guard.py plus "
    "src/os/test_review_window_wire_argument_guard.py, and exempt_review now "
    "asks it on the ARGUMENT path. The rewind law is IMPORTED "
    "(review_window_history.history at call time, proved by patching it and "
    "watching both the guard report and the CLI move) and the refusal code is "
    "CARRIED through review_window_wire.carry_history_code, so "
    "`exempt_review --window N` refuses a rewinding declarations list with the "
    "declared path's own E_RWHW_DECL_HISTORY naming both rounds - where before "
    "this window an explicit window silently aged every entry. Scope is "
    "deliberately narrow: UNPINNED, DRIFT, a moved list and an unreadable file "
    "all leave the explicit window's reading byte-identical, because that "
    "window is the caller's and not the declaration's; only a provable rewind "
    "changes the answer, and the refusal lands before any entry is aged with "
    "zero counts and WINDOW-REFUSED on the CLI while the declaration bytes are "
    "untouched (whole-tree digest identical).",
    "R2371 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/review-window-wire-argument-guard-R2371.log, 3426B, legs=2 "
    "identical=True adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired "
    "os-review-window-wire-argument-guard(6) in src/sandbox/reconcile_all.py. "
    "LIVE, not a plan: on the real tree `review_window_wire_argument_guard.py "
    "--check` reads verdict=ARGUMENT-CLEAN history=EMPTY-HISTORY window=100 "
    "moves=0 declared_by=R2305 at exit 0, and both exempt_review paths read "
    "9 entries 0 stale with the declaration sha256 identical before and after "
    "(qa/review-window-wire-argument-guard-live-R2371.log, 907B, written "
    "through src/os/evidence_R2371.py). Tech row 417 stamped [done 2026-11-02 "
    "R2371] (bracket payload 21 chars inside the 60-char stamp law) and one "
    "REAL measured gap row seeded at the tail (review_window_guard_parity, "
    "AC-RWGP1..AC-RWGP6 pre-registered in that row, five anchors "
    "zero-occupancy at HEAD) from this window own seam: the declared path and "
    "the argument path now both refuse a rewinding list with the same code, "
    "but the pair was never run over ONE declaration to say AGREES or "
    "DISAGREES, so a future edit to either law could split them silently. "
    "Gauge after the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10, and the reader now offers line 418 prefix AC-RTRI1.",
    "R2371 register: reconcile-battery-R2370 closed through debt_close "
    "(open 3->2, done 99->100, 78746B->78749B, readback ok) and "
    "reconcile-battery-R2371 opened first=yes through debt_append at the "
    "measured successor target 498 suites / 3964 criteria "
    "(78749B->79308B, readback ok).",
    "R2371 honest disclosures: (a) the first battery invocation was piped "
    "through a truncating selector and was cancelled by the five-minute "
    "no-output rule - the R2235/R2247/R2268/R2349 trap repeated. An ownership "
    "check proved zero surviving reconcile/battery processes, no evidence file "
    "and a clean git status before the direct-stream rerun, whose numbers are "
    "the ones above; nothing was lost or cleaned. (b) Three suite criteria "
    "were RED on the first runs and all three were this window own fixtures "
    "and assertions, never the module: AC-RWAG1 asserted the history call by "
    "the full module name while the guard imports it under an alias, AC-RWAG3 "
    "expected exempt_review's `declaration` field to read UNPINNED when that "
    "field describes the EXEMPT declaration (which is on disk) and not the "
    "window declaration, and AC-RWAG5/AC-RWAG2 expected exit 0 for a fixture "
    "whose entry is legitimately stale. Each was corrected to the measured "
    "truth and no criterion was widened. (c) One REAL module defect was also "
    "found while fixing them: the guard's refusal detail carried only the "
    "history's words and not its code, so the operator could not see WHICH law "
    "refused; the detail now carries the history code exactly as the declared "
    "path's wire already does, and the MODULE was changed rather than the "
    "criterion. (d) tasks.md was left untouched: it is the P-47 canonical "
    "board and carries no row for this tech slice, disclosed rather than "
    "silently skipped. (e) This window ran past its 25-minute budget: the "
    "battery alone measured 987.8s, and the product face was still shipped on "
    "the same budget rather than deferred, because the tree was committed and "
    "clean before the battery.",
    "R2371 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply, and this session runs "
    "unelevated, so the definition of the loop hosting this window was left "
    "untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-sixth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2371 tokens: local=~30k api=0 api_reason=verification-then-product "
    "window - one full battery (497 suites, 987.8s) plus its four follow-up "
    "sections and one matrix regeneration, one guard module and its "
    "six-criteria suite written to criteria pinned twelve rounds earlier, one "
    "caller rerouted through the guard, one registry wiring line, one two-leg "
    "evidence capture with four adjacent suites, one live capture written "
    "through a single utf-8 LF writer, one board stamp and one measured gap "
    "row seeded, one register close and one successor row opened, and the "
    "state/backlog/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2371] verification-then-product-R2371: the debt "
    "gate named CLAIM-FIRST item=reconcile-battery-R2370, so the battery ran "
    "FIRST on the committed 5d9485d2 tree with an empty git status - RUNNER "
    "PASS 497/497 suites green plus reconcile controls 7/7 in 987.8s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2371.log, 804580B, single writer utf-8 LF through "
    "src/os/battery_stream.py) and criteria total 3958 EXACTLY as "
    "pre-registered, so the prediction matched the measurement with nothing to "
    "name; the four follow-up sections ran through src/os/battery_followup.py, "
    "the matrix section FAILED first on the stale doc and did NOT rewrite it "
    "(on-disk=47476B regenerated=47582B), suite_matrix regenerated "
    "docs/sandbox-suite-matrix.md to 497 suites / 3958 criteria and the re-run "
    "read all four PASS for VERDICT R2371 PASS; evidence and matrix committed "
    "alone as 5d9485d2 before any product byte changed (the R2168 mixed-tree "
    "rule). PRODUCT: claimed state/queue/tech.md:417 prefix AC-RWAG1 "
    "(review_window_wire_argument_guard), whose AC-RWAG1..AC-RWAG6 were pinned "
    "inside that row at R2359 BEFORE any code, after a fresh anchor check at "
    "HEAD (prose and state only, zero executable occupancy). SHIPPED "
    "src/os/review_window_wire_argument_guard.py plus "
    "src/os/test_review_window_wire_argument_guard.py: `exempt_review --window "
    "N` now asks review_window_history FIRST, so a declarations list whose "
    "declared_by rewinds refuses with the declared path's own "
    "E_RWHW_DECL_HISTORY naming both rounds, where before this window an "
    "explicit window silently aged every entry; the rewind law is imported at "
    "call time and the code is carried through the wire's own mapping, so no "
    "second rewind comparison exists; UNPINNED, DRIFT, a moved list and an "
    "unreadable file keep the argument path's reading byte-identical because "
    "that window is the caller's, and the refusal lands before any entry is "
    "aged with zero counts and WINDOW-REFUSED while the declaration bytes stay "
    "untouched. SUITE PASS 6/6 twice with an identical criterion digest plus "
    "four adjacent suites green "
    "(qa/review-window-wire-argument-guard-R2371.log, 3426B, legs=2 "
    "identical=True adjacent=4 fails=0), wired "
    "os-review-window-wire-argument-guard(6). LIVE: the real declarations list "
    "reads verdict=ARGUMENT-CLEAN history=EMPTY-HISTORY window=100 "
    "declared_by=R2305 at exit 0 and both exempt_review paths read 9 entries 0 "
    "stale with the declaration sha256 unchanged "
    "(qa/review-window-wire-argument-guard-live-R2371.log, 907B). Row stamped "
    "and one REAL measured gap seeded (review_window_guard_parity, "
    "AC-RWGP1..AC-RWGP6 pre-registered in that row, five anchors "
    "zero-occupancy): the two paths now refuse the same file with the same "
    "code but nothing measures that they agree over ONE declaration. Register: "
    "reconcile-battery-R2370 closed and reconcile-battery-R2371 opened at 498 "
    "suites / 3964 criteria. Gauge FLOOR-MET 5/5 10/10 10/10."
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
    if BACKLOG_ROW[:60] in text:
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
        state_fold.fold(REPO, "R2371", FOLD_BASE + guard, 1, end, summary,
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