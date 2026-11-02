"""closeout_R2372 - tick, log items and the backlog row for this window."""

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
RESERVE = 6000
FOLD_BASE = 648

ITEMS = [
    "2026-11-02 R2372 verification-then-product window (five-silence scan "
    "clean at open: git status empty at HEAD 674adfa9, no .git/index.lock; "
    "scan_five_still read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=124 "
    "tokens=81 new=0, the group orders tail still the 2026-11-01 10:4x "
    "model-policy baseline already acknowledged as non-execution, and "
    "benchmarks refreshed 2026-11-02 inside the seven-day gate). The debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2371, so the battery ran FIRST "
    "on the committed tree, unfiltered: RUNNER PASS 498/498 suites green plus "
    "reconcile controls 7/7 in 933.3s with birth-site TMP RECLAIM 932/932 "
    "worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2372.log, 806182B, "
    "single writer utf-8 LF through src/os/battery_stream.py, never a shell "
    "redirection) and criteria total 3964 EXACTLY as pre-registered, so the "
    "prediction matched the measurement with no correction and nothing to "
    "name.",

    "R2372 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=47582B regenerated=47697B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 498 suites / 3964 criteria (47697B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2372 PASS. The evidence and the matrix were committed ALONE as be1ac6a "
    "before any product byte changed (the R2168 mixed-tree rule).",

    "R2372 product face, the row the reader named: CLAIMED state/queue/tech.md"
    ":418 prefix AC-RTRI1 (residue_triage_repin_idempotent), whose "
    "AC-RTRI1..AC-RTRI6 were pinned INSIDE that row at R2363 BEFORE any code, "
    "after a fresh anchor check at HEAD: residue_triage_repin_idempotent, "
    "AC-RTRI, E_RTRI, os-residue-triage-repin-idempotent and "
    "test_residue_triage_repin_idempotent hit ONLY prose and state files "
    "(src/os/backlog.md, src/os/closeout_R2363.py, src/os/closeout_R2371.py, "
    "src/os/export_R2371.py, src/os/state.json, docs/status-export.json, "
    "state/queue/tech.md) with zero executable occupancy.",

    "R2372 the wire: shipped src/os/residue_triage_repin_idempotent.py plus "
    "src/os/test_residue_triage_repin_idempotent.py. The re-pin composed a "
    "declaration and wrote it, but it could not tell 'nothing to do' from 'I "
    "rewrote the declaration' - R2363 measured a second plan composing bytes "
    "identical to the file and still reading PLANNED, so --execute rewrote the "
    "same bytes as PINNED. The wire composes through "
    "residue_triage_repin.build and asks the FILE: identical bytes read NOOP "
    "with executed=False, and the branch returns BEFORE the writer is entered, "
    "so no temp file is created and the single atomic write path is not "
    "doubled. The decision is BYTES and never the head round - the module does "
    "not mention declared_by at all - so a declaration already pinned at an "
    "older round still reads NOOP at that round. Every non-NOOP path is the "
    "shipped writer's own report, printed through the shipped renderer and "
    "serialiser, so the CLI codes and the pinned PLAN_KEYS order cannot drift.",

    "R2372 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/residue-triage-repin-idempotent-R2372.log, 3090B, legs=2 "
    "identical=True adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired "
    "os-residue-triage-repin-idempotent(6) in src/sandbox/reconcile_all.py. "
    "LIVE, not a plan: on the real tree both CLIs are byte-identical over one "
    "declaration (qa/residue-triage-repin-idempotent-live-R2372.log, "
    "LIVE-PARITY) and the declaration's sha256 and byte count are unchanged "
    "across the two dry runs (65393B), while the same invocation still "
    "composes 65210B - i.e. the live declaration IS stale, so the NOOP reading "
    "is proved on fixtures and is NOT claimed as a live catch. Tech row 418 "
    "stamped [done 2026-11-02 R2372] (predicted=measured 1472542B) and one "
    "REAL measured gap row seeded (repin_noop_parity, AC-RNP1..AC-RNP6 "
    "pre-registered in that row, five anchors zero-occupancy): the NOOP exists "
    "in the wire and NOT in the tool operators run, so one act has two "
    "answers. Gauge after the stamp and the seed reads FLOOR-MET main 5/5 tech "
    "10/10 explore 10/10 and the reader now offers line 419 prefix AC-CUR1. "
    "Register: reconcile-battery-R2371 closed through debt_close (open 3->2, "
    "done 100->101, 79308B->79311B, readback ok) and reconcile-battery-R2372 "
    "opened first=yes through debt_append at the measured successor target 499 "
    "suites / 3970 criteria (79311B->79854B, readback ok).",

    "R2372 honest disclosures: (a) the suite's first run was RED on AC-RTRI1 "
    "because the fixture had no declaration at all - `residue_triage_repin` "
    "refuses to invent one by design - so the fixture now writes the standing "
    "declaration as data and every byte this window measured after the pin is "
    "the shipped writer's own. (b) AC-RTRI3 was written as a predicted BYTE "
    "COUNT delta of one, but a same-length substitution keeps the count, so "
    "the criterion is now measured as CONTENT: the composition differs from "
    "the file at exactly one byte position with both lengths equal. No "
    "criterion was widened. (c) AC-RTRI6 was RED only because the registry "
    "entry did not exist yet; the wiring was added and the assertion was not "
    "touched. (d) `decide` calls the shipped `build` and, on the non-NOOP "
    "path, the shipped `plan`, which recomposes - a second reading of the same "
    "declaration inside one call; it is disclosed rather than hidden because "
    "reproducing the write here would have created the second writer AC-RTRI6 "
    "forbids. (e) tasks.md was left untouched: it is the P-47 canonical board "
    "and carries no row for this tech slice, disclosed rather than silently "
    "skipped. (f) the seed deliberately repeats the R2371 parity class on a "
    "different pair rather than inventing a novel shape - the seam is real and "
    "measured, and saying so is more honest than dressing it up as new.",

    "R2372 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply, and this session runs "
    "unelevated, so the definition of the loop hosting this window was left "
    "untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-seventh consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",

    "R2372 tokens: local=~33k api=0 api_reason=verification-then-product "
    "window - one full battery (498 suites, 933.3s) plus its four follow-up "
    "sections and one matrix regeneration, one NOOP wire and its six-criteria "
    "suite written to criteria pinned nine rounds earlier, one registry wiring "
    "line, one two-leg evidence capture with four adjacent suites, one live "
    "parity capture written through a single utf-8 LF writer, one board stamp "
    "and one measured gap row seeded, one register close and one successor row "
    "opened, and the state/backlog/export/heartbeat closeout; zero cloud calls "
    "and zero external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2372] verification-then-product-R2372: the debt "
    "gate named CLAIM-FIRST item=reconcile-battery-R2371, so the battery ran "
    "FIRST on the committed 674adfa9 tree with an empty git status - RUNNER "
    "PASS 498/498 suites green plus reconcile controls 7/7 in 933.3s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2372.log, 806182B, single writer utf-8 LF through "
    "src/os/battery_stream.py) and criteria total 3964 EXACTLY as "
    "pre-registered, so the prediction matched the measurement with nothing to "
    "name; the four follow-up sections ran through src/os/battery_followup.py, "
    "the matrix section FAILED first on the stale doc and did NOT rewrite it "
    "(on-disk=47582B regenerated=47697B), suite_matrix regenerated "
    "docs/sandbox-suite-matrix.md to 498 suites / 3964 criteria and the re-run "
    "read all four PASS for VERDICT R2372 PASS; evidence and matrix committed "
    "alone as be1ac6a before any product byte changed (the R2168 mixed-tree "
    "rule). PRODUCT: claimed state/queue/tech.md:418 prefix AC-RTRI1 "
    "(residue_triage_repin_idempotent), whose AC-RTRI1..AC-RTRI6 were pinned "
    "inside that row at R2363 BEFORE any code, after a fresh anchor check at "
    "HEAD (every anchor prose and state only, zero executable occupancy). "
    "SHIPPED src/os/residue_triage_repin_idempotent.py plus "
    "src/os/test_residue_triage_repin_idempotent.py: the re-pin finally has a "
    "NOOP - identical composed bytes read NOOP with executed=False before the "
    "writer is entered (no temp file, write path not doubled), the decision is "
    "BYTES and never the head round (the module never mentions declared_by, so "
    "a declaration pinned at an older round still reads NOOP there), a "
    "one-byte content drift reads PLANNED again, and every non-NOOP path is "
    "the shipped writer's own report through the shipped renderer and "
    "serialiser (the suite proves both CLIs byte-identical on PLANNED and on "
    "refusals, same codes 0/2/5, same PLAN_KEYS order, NOOP at exit 0). SUITE "
    "PASS 6/6 twice with an identical criterion digest plus four adjacent "
    "suites green (qa/residue-triage-repin-idempotent-R2372.log, 3090B, "
    "legs=2 identical=True adjacent=4 fails=0), wired "
    "os-residue-triage-repin-idempotent(6). LIVE: both CLIs byte-identical "
    "over the real declaration and its sha256 unchanged across two dry runs "
    "(65393B), while the same call still composes 65210B - the live "
    "declaration IS stale, so NOOP is proved on fixtures and not claimed as a "
    "live catch (qa/residue-triage-repin-idempotent-live-R2372.log, "
    "LIVE-PARITY). Row 418 stamped (predicted=measured 1472542B) and one REAL "
    "measured gap seeded (repin_noop_parity, AC-RNP1..6: the NOOP exists in "
    "the wire and not in the shipped CLI, so one act has two answers), floor "
    "FLOOR-MET 5/5 10/10 10/10, reader now offers line 419 AC-CUR1. Register: "
    "battery-R2371 closed and battery-R2372 opened first=yes at 499 suites / "
    "3970 criteria. Disclosed: two suite reds were this window own fixture and "
    "assertion (a missing seeded declaration, and a byte-count delta where a "
    "content delta was meant), one red was the absent registry entry, and "
    "`decide` reads the declaration twice on the non-NOOP path rather than "
    "reproducing the writer."
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
    print("FOLD needed=%s margin=%d archive=%s"
          % (measure["fold_needed"], measure["margin"], FOLD_BASE))
    prepend_backlog()
    return 0


if __name__ == "__main__":
    sys.exit(main())