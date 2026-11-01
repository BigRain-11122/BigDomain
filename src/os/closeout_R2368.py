"""closeout_R2368.py - append this window's items and fold if the gate demands.

One-off for the round, same shape as closeout_R2367: the state file is written
through state_io.canon and any fold runs through state_fold.fold.

Usage: python src/os/closeout_R2368.py
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
GATE = 78500
RESERVE = 6000
FOLD_BASE = 644

ITEMS = [
    "2026-11-02 R2368 verification window first, on the committed tree: the "
    "debt gate read CLAIM-FIRST item=reconcile-battery-R2367 opened=R2366 "
    "carried=2 and named the measured target 494 suites / 3940 criteria (the "
    "matrix doc at HEAD read 492/3928 from the R2364 leg, plus the R2365 "
    "os-queue-floor-delivered-wire suite and the R2366 "
    "os-battery-followup-help-wire suite, six criteria each). The battery ran "
    "on the committed dffdd007 tree with an empty git status before the run: "
    "RUNNER PASS 494/494 suites green plus reconcile controls 7/7 in 914.6s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2368.log, 802737B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection) and criteria total "
    "3940 EXACTLY as pre-registered, so the prediction matched the measurement "
    "with no correction and nothing to name. The four follow-up sections then "
    "ran through src/os/battery_followup.py: the matrix section FAILED first "
    "on the stale doc (on-disk=47070B regenerated=47273B) and did NOT rewrite "
    "it, which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 494 suites / 3940 criteria (47273B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN "
    "5 domains, profile --check byte-identical, census DRIFT-CLEAN) for "
    "VERDICT R2368 PASS. The evidence and the matrix were committed alone as "
    "cee549f7 before any product byte changed (the R2168 mixed-tree rule).",
    "R2368 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:413 prefix AC-QFR1 (queue_floor_reading_wire), whose "
    "AC-QFR1..AC-QFR6 were pinned INSIDE that row at R2365 BEFORE any code, "
    "after a fresh zero-occupancy anchor check at HEAD - all five anchors hit "
    "only prose and state files (src/os/backlog.md, src/os/closeout_R2365.py, "
    "src/os/export_R2365.py, docs/status-export.json, state/queue/tech.md, "
    "src/os/closeout_R2367.py) with zero executable occupancy. SHIPPED "
    "src/os/queue_floor_reading_wire.py plus "
    "src/os/test_queue_floor_reading_wire.py: the wire publishes ONE floor "
    "reading whose claimable IS the discounted number, with the discount count "
    "and the discounted rows (line + prefix, exactly as queue_occupancy "
    "reported them, never reformatted) travelling beside it so gross "
    "reconciles as claimable + discounted. Nothing is re-derived: the report is "
    "queue_floor_delivered_wire.gauge itself (AC-QFR1 proven by patching that "
    "gauge and watching the published number move) and every row law, count, "
    "floor and status stays with queue_floor, so a queue with nothing delivered "
    "publishes queue_floor's row byte for byte on every shared key. It is a "
    "pure read of a root - no write, no clock, no network.",
    "R2368 live action, not a plan: `python src/os/queue_floor_reading_wire.py "
    "--check` on the real tree reads main=5/5 tech=9/10-1 explore=10/10 "
    "verdict=FLOOR-DEBT shortfall=1 delivered=1 with the discounted row named "
    "as line 413 prefix AC-QFR1, while `queue_floor.py --check` on the SAME "
    "tree at the SAME instant still reads main=5/5 tech=10/10 explore=10/10 "
    "verdict=FLOOR-MET - two readers, two answers, and the undiscounted one "
    "was the published one. The row it discounts is this window's own claimed "
    "row, whose module and suite now exist on disk, so the seed's described "
    "defect reproduced itself at the birth site "
    "(qa/queue-floor-reading-wire-live-R2368.log, 1134B, written utf-8 LF "
    "through src/os/evidence_R2368.py).",
    "R2368 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/queue-floor-reading-wire-R2368.log, 1723B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-queue-floor-reading-wire(6) in "
    "src/sandbox/reconcile_all.py. Tech row 413 stamped "
    "[done 2026-11-02 R2368] and one REAL measured gap row seeded so the floor "
    "stays 10/10 with no filler: queue_floor_export_face (AC-QFE1..AC-QFE6 "
    "pre-registered in that row, five anchors claimed zero-occupancy), from "
    "this window own measurement that git grep -F for claimable / floor / "
    "FLOOR over docs/status-export.json and src/os/check_export_consistency.py "
    "returns ZERO hits - the CEO-visible face publishes no queue line at all, "
    "so the discounted number has no consumer on the export yet. Gauge after "
    "the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 explore 10/10; "
    "the debt register closed reconcile-battery-R2367 (open 3->2, done 96->97, "
    "77029B->77032B, readback ok) and opened reconcile-battery-R2368 first=yes "
    "at the measured successor target 495 suites / 3946 criteria "
    "(77032B->77635B, readback ok).",
    "R2368 honest disclosures: (a) the first battery invocation was piped "
    "through a filtering selector and was cancelled by the five-minute "
    "no-output rule - the R2235/R2247/R2268 trap repeated. An ownership check "
    "proved zero surviving reconcile/battery processes, no evidence file and a "
    "clean git status before the direct-stream rerun, whose numbers are the "
    "ones above; nothing was lost or cleaned. (b) AC-QFR2 was RED on the first "
    "run and the red was this window own fixture, not the module: it asserted "
    "the delivered prefix was 'AC-ALP' while queue_occupancy legitimately "
    "reports 'AC-ALP1' (the whole prefix token), so the assertion now compares "
    "against queue_occupancy's OWN reported list instead of a hand-written "
    "string - the criterion was not widened, the reading never reformats. (c) "
    "AC-QFR1's first fixture built its doctored report from QF.gauge, which "
    "carries no claimable_effective key, and the suite died on a KeyError; the "
    "fixture now doctors FDW.gauge, which is the surface the criterion names. "
    "(d) tasks.md was left untouched: it is the P-47 canonical board and "
    "carries no row for this tech slice, disclosed rather than silently "
    "skipped. (e) The innovation-proposal quota for this window is already "
    "met by BD-PROP-006 (opened 2026-11-02), so no new proposal was written "
    "rather than manufacturing one to fill a slot.",
    "R2368 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply, and this session runs "
    "unelevated, so the definition of the loop hosting this window was left "
    "untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-third consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2368 tokens: local=~31k api=0 api_reason=verification-then-product "
    "window - one full battery (494 suites, 914.6s) plus its four follow-up "
    "sections and one matrix regeneration, one product wire and its "
    "six-criteria suite written to criteria pinned one round earlier, one "
    "registry wiring line, one two-leg evidence capture with four adjacent "
    "suites, one live capture written through a single utf-8 LF writer, one "
    "board stamp and one measured gap row seeded, one register close and one "
    "successor row opened, and the state/export/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]


def read_state():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_state(text):
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    return back


def block_boundaries(log):
    out = []
    for index, line in enumerate(log):
        if re.match(r"^(?:\d{4}-\d{2}-\d{2} )?R\d+ tokens:", line.strip()):
            out.append(index + 1)
    return out


def main():
    raw = read_state()
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    tick = data.get("tick", 0) + 1
    data["tick"] = tick
    data["benchmarks_refreshed"] = "2026-11-02"
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    write_state(text)
    size = len(text.encode("utf-8"))
    print("STATE tick=%d items=+%d before=%dB after=%dB"
          % (tick, len(ITEMS), before, size))

    guard = 0
    while True:
        measure = state_fold.measure(size, GATE)
        if not measure["fold_needed"]:
            print("FOLD none needed bytes=%d margin=%d"
                  % (size, measure["margin"]))
            break
        current = read_state()
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
        state_fold.fold(REPO, "R2368", FOLD_BASE + guard, 1, end, summary,
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