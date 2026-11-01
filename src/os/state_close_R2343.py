"""state_close_R2343 - the round record for the R2343 window.

The window ran THE GREEN FULL BATTERY the board top carried (478 suites /
3844 criteria, exactly the pre-registered figure against R2342 477/3838), took
the four follow-up sections through their designed matrix FAIL and the
regeneration that closes it, then shipped one product face (followup_incomplete_cause)
with its six pre-registered criteria, closed the tech head row, seeded one real
gap row and moved the debt register.

It folds first (the closeout would cross the waterline), then appends the items
this window owes and bumps the tick. Dry run by default; --execute writes with a
read-back proof and leaves no temp residue.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

TICK = 2343
ROUND_RE = re.compile(r"^(20\d\d-\d\d-\d\d R\d+ |R\d+ tokens:|tokens:)")
DATE_RE = re.compile(r"^20\d\d-\d\d-\d\d R\d+ ")

LIVE = (
    "2026-11-01 R2343 verification-then-product window (five-silence scan "
    "clean at open: empty git status --short at d722df04 and no "
    ".git/index.lock; the content-addressed diff of the group decisions.md "
    "against the stored baseline read NEW=0 over 65 live tokens, so no "
    "decision row was owed; the evolution ledger carries zero @BigDomain rows; "
    "the local orders board tail is unchanged at its 2026-09-28 rows and the "
    "group orders tail still reads the 2026-11-01 10:4x baseline already "
    "acked as non-execution; benchmarks refreshed 2026-11-01, inside the "
    "seven-day gate). FIRST ITEM, the board top: THE BATTERY ON THE COMMITTED "
    "R2342 TREE with zero product edits until green (the R2168 mixed-tree "
    "rule), pre-registered at 478 suites / 3844 criteria - exactly +1 suite / "
    "+6 criteria against R2342 (477/3838) from the os-orphan-promotion-ledger "
    "suite. MEASURED: RUNNER PASS 478/478 suites green plus controls 7/7 in "
    "896.0s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2343.log, 792889B re-read at close, single "
    "writer utf-8 LF through src/os/battery_stream.py), criteria total 3844 - "
    "the prediction matched the measurement with no correction and no swept "
    "delta. Four follow-up sections through src/os/battery_followup.py ran in "
    "their pinned order: matrix FAILED first on the stale shipped doc "
    "(on-disk=45670B regenerated=45769B) and did NOT rewrite it, which is the "
    "designed order; src/sandbox/suite_matrix.py then regenerated "
    "docs/sandbox-suite-matrix.md to 478 suites / 3844 criteria (45769B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --daily --check byte-identical, census DRIFT-CLEAN), "
    "closing VERDICT R2343 PASS. PRODUCT after green: claimed the queue head "
    "the reader named, state/queue/tech.md:389 prefix AC-FIC1 "
    "(followup_incomplete_cause), whose AC-FIC1..AC-FIC6 were pinned INSIDE "
    "that row at R2325 BEFORE any code (re-read, not re-run; the fresh anchor "
    "check at HEAD found zero executable occupancy - followup_incomplete_cause, "
    "AC-FIC and os-followup-incomplete-cause hit only prose in backlog.md, "
    "state/debt.md, state/queue/tech.md, state.json, closeout_R2325.py and "
    "closeout_R2342.py). SHIPPED src/os/followup_incomplete_cause.py plus "
    "src/os/test_followup_incomplete_cause.py: INCOMPLETE stops being one "
    "word. The section vocabulary and the SECTION/VERDICT reading are asked of "
    "followup_history (the suite patches FH.parse and watches the reading move, "
    "and asserts the module carries no re.compile and no SECTION literal, so "
    "there is no second scan); every round lands in exactly one of four "
    "disjoint causes - LEGACY-DIALECT (no sections and no verdict: debt no "
    "rerun can heal), NO-VERDICT (sections ran, verdict never written), "
    "MISSING-SECTION (a verdict exists while named sections are ABSENT, listed "
    "by name), COMPLETE (nothing absent) - and the cause is derived from the "
    "log body alone, with no clock and no round threshold. The legacy round "
    "range is ordered by the round DIGITS rather than the label text, which "
    "was a real defect this window fixed at its birth site after the live "
    "reading printed R1000..R999. SUITE PASS 6/6 twice with an identical "
    "criterion digest through evidence_capture with three adjacent suites "
    "green (qa/followup-incomplete-cause-R2343.log, 1358B), wired "
    "os-followup-incomplete-cause(6).")

TOKENS = (
    "R2343 tokens: local=~26k api=0 api_reason=verification-then-product "
    "window - one full reconcile battery (478 suites, 3844 criteria, 896.0s) "
    "with its streamed evidence file, one four-section follow-up run plus one "
    "matrix regeneration and the closing re-run, one classifier module with "
    "its six pre-registered criteria and its suite (green on the third run "
    "after two this-window test fixtures and one real module defect were "
    "fixed at their birth sites), one dogfooded evidence capture with three "
    "adjacent suites, one queue close with one real gap row seeded, one debt "
    "row closed and one successor opened, and the state/export/heartbeat/board "
    "closeout; zero cloud calls and zero external API touches")

SELF_HEAL = (
    "R2343 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-fourth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).")

DECISION = (
    "R2343 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read NO new tokens "
    "(new=[] over 65 live tokens), and the evolution ledger carries no "
    "@BigDomain row, so nothing was executed, rejected or acknowledged this "
    "window and the baseline is unchanged.")

DISCLOSURES = (
    "R2343 honest disclosures: (a) the FIRST battery launch was piped through "
    "a truncating selector, produced no output for five minutes and was "
    "cancelled by the shell guard with zero surviving processes, no evidence "
    "file and a clean tree, so nothing is claimed from the dead run (the R2211 "
    "trap re-proven). (b) The product suite was red twice on THIS window's own "
    "fixtures (a default file name that did not follow the round label, and an "
    "import set that did not allow the followup_history import) and once more "
    "on a REAL module defect - the legacy range sorted labels as text, so the "
    "live reading printed R1000..R999; the module now orders by the round "
    "digits and no criterion was widened anywhere. (c) The live reading is a "
    "finding, not a green claim: 421 of 448 rounds are LEGACY-DIALECT, which "
    "means most of the incompleteness debt will never heal by re-reading - "
    "that is exactly the split the face was built to expose, and the number is "
    "reported rather than dressed up. (d) no_verdict=0 and missing_section=0 "
    "on today's pile, so two of the four causes are pinned by the suite only; "
    "they are named here rather than claimed as live coverage. (e) The debt "
    "row reconcile-battery-R2340 was closed as stale - R2340 and R2341 both "
    "ran that battery - and the successor battery row was opened at 479 suites "
    "/ 3850 criteria (+1 suite / +6 criteria from this window's suite). (f) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries "
    "no row for this tech slice, disclosed rather than silently skipped.")

ITEMS = [LIVE, TOKENS, SELF_HEAL, DECISION, DISCLOSURES]


def read_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fold_window(state):
    """Pick a window that ends exactly at a round-block boundary.

    A round block always STARTS with a dated round line, so the largest index
    whose NEXT item starts a dated block is a boundary that cuts no block in
    half (the R2336 defect shape).
    """
    log = state["log"]
    limit = min(16, len(log) - 1)
    candidates = []
    for end in range(1, limit + 1):
        follows = log[end] if end < len(log) else ""
        if DATE_RE.match(follows):
            candidates.append(end)
    return candidates[-1] if candidates else None


def main(argv):
    state = read_state()
    raw = io.open(STATE, "rb").read()
    print("state before=%dB log=%d tick=%d"
          % (len(raw), len(state["log"]), state["tick"]))
    plan = None
    end = fold_window(state)
    if end is not None:
        window = state["log"][:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2343: log lines 1..%d folded verbatim into the "
                   "archive on a round-block boundary; window tokens: %s"
                   % (end, " ".join(sorted(tokens))))
        plan = SF.fold(ROOT, "R2343", 631, 1, end, summary, execute=False)
        print("fold plan window=1:%d lines=%d predicted=%dB gate_ok=%s "
              "tokens_missing=%s"
              % (end, plan["window_lines"], plan["predicted_bytes"],
                 plan["gate_ok"], plan["tokens_missing"]))
    # predicted post-fold + append size
    body = {"tick": TICK, "log": (["FOLD"] * (len(state["log"]) - (end or 0) + 1))
            + ITEMS}
    print("append items=%d" % len(ITEMS))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    if plan is not None:
        done = SF.fold(ROOT, "R2343", 631, 1, end,
                       ("Fold R2343: log lines 1..%d folded verbatim into the "
                        "archive on a round-block boundary; window tokens: %s"
                        % (end, " ".join(sorted(
                            set().union(*[set(SF.PAT.findall(x))
                                          for x in state["log"][:end]]))))),
                       execute=True)
        print("fold done predicted=%s measured=%s"
              % (done["predicted_bytes"], done["post_bytes"]))
    state = read_state()
    state["tick"] = TICK
    state["log"].extend(ITEMS)
    body = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, STATE)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body or os.path.exists(temp):
        print("E_READBACK")
        return 3
    print("APPENDED state=%dB log=%d tick=%d readback=ok"
          % (len(back.encode("utf-8")), len(state["log"]), state["tick"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))