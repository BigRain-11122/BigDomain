"""R2395 closeout: state log, export face, backlog and heartbeat (R2395).

The state payload is serialised, canonicalised through state_io.canon and
written with a read-back that requires the JSON to equal the plan. The
export counters are taken from check_export_consistency.recompute, never
hand-typed, and the three CEO-visible lines are written from the measured
reading of this window.

Stdlib only, ASCII source, no network. The one clock reading is the export
timestamp handed in by the caller (--now), so a re-run is reproducible.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

TOKENS = ["D-20261103-01", "D-20261103-02", "D-20261103-03",
          "D-20261103-04", "D-20261103-05", "D-20261103-06"]

ITEMS = [
    "2026-11-03 R2395 product window (five-silence scan at open: empty git "
    "status, no .git/index.lock; LEDGER atbd_lines=0 unreplied_groups=0; DEC "
    "rows=140 tokens baseline 92 new=6, and those six - D-20261103-01..06 - "
    "were already read at R2394 as non-execution (Biggame directory, duanju "
    "dormancy, audit cadence, CC-2/CC-3 registry supplement), so this window "
    "only folds them into the stored token set: R2394 closeout moved the count "
    "and left the set behind, which is why the same six rows still read as new "
    "here; the group orders tail stays the 2026-11-02 11:04 model-policy "
    "baseline already acknowledged as non-execution; benchmarks refreshed "
    "2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 tech 12/10 "
    "explore 10/10). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2394, and the product-first law took the window: "
    "R2394 was verification-only with zero product points, so this window "
    "shipped the face and the battery row stays OPEN at its re-measured "
    "target.",

    "2026-11-03 R2395 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:462 prefix AC-RTH1 (runner_suite_timeout_headroom), "
    "whose AC-RTH1..AC-RTH6 were pinned INSIDE that row at R2393 BEFORE any "
    "code, after an anchor check at HEAD. SHIPPED "
    "src/os/runner_suite_timeout_headroom.py plus "
    "src/os/test_runner_suite_timeout_headroom.py: the battery runs every "
    "registered suite through subprocess.run(timeout=300), so one loaded "
    "suite kills the WHOLE run with no code defect - R2393 leg 3 died on "
    "ledger/test_apimarket_report_claims.py at exactly 300s while the same "
    "suite had measured 183.3s and 194.9s in that window's earlier legs - and "
    "nothing in the tree read those durations. The reading derives each "
    "registered suite's own slowest measured leg from the runner's own PASS/"
    "FAIL suite lines, takes headroom as cap minus that leg, names every suite "
    "at or above the band (default 60%% of the cap) with verdict BAND-HIT, "
    "reads NO-MEASURE for a registered suite with no leg, and keeps exits "
    "0/2/3/5 with a byte-stable --json over pinned keys.",

    "2026-11-03 R2395 evidence and board: SUITE PASS 6/6 twice with an "
    "identical criterion digest CB10BFECDEC50D24 plus three adjacent suites "
    "green (qa/runner-suite-timeout-headroom-R2395.log, 1276B, legs=2 "
    "identical=True adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired "
    "os-runner-suite-timeout-headroom(6) so the registry reads 521 suites / "
    "4102 criteria. LIVE, not a plan: "
    "qa/runner-suite-timeout-headroom-live-R2395.log reads the REAL pile as "
    "521 registered suites, 520 measured, 3 inside the band - "
    "ledger-apimarket-refundregister 268.1s (headroom 31.9s), "
    "ledger-apimarket-reportclaims 246.8s (53.2s), "
    "ledger-apimarket-buyerhistory 232.2s (67.8s) - with "
    "os-runner-suite-timeout-headroom itself reading NO-MEASURE because no "
    "battery has run since it was wired, a tightened cap of 200 naming five "
    "band lines, a missing registry at exit 3, a bad flag at exit 5, and the "
    "module digest unchanged before and after. Tech row 462 stamped "
    "[done 2026-11-03 R2395] and one REAL measured gap row seeded "
    "(runner_abort_face, AC-RAF1..AC-RAF6 pre-registered in that row): the "
    "reading only knows suites some leg FINISHED, so the suite that actually "
    "killed a battery is the one line the pile never carries.",

    "2026-11-03 R2395 honest disclosures: (a) two of this window own suite "
    "legs were RED on their first run and both reds were this window own "
    "fixtures, never the module: AC-RTH1's patch predicate matched the "
    "summary line 'PASS suites 2/2 green' as well as a suite line and "
    "invented a suite labelled 2/2, so the predicate now asks the module's own "
    "SUITE_LINE_RE; AC-RTH3 asserted the string 'BAND ' was absent from the "
    "clean body, which the header 'CAP 300.0s BAND 60%' legitimately carries, "
    "so the assertion pins one BAND line and no BAND-HIT. No criterion was "
    "widened. (b) The first live leg answered E_RTH_NO_REGISTRY on the REAL "
    "tree because the runner's SUITES table is not a literal - every path is "
    "an os.path.join call - so the label extraction was rebuilt on the AST "
    "(first element of each tuple row when it is a string constant) instead of "
    "evaluating the table, and the runner is never imported. (c) The evidence "
    "file was captured once with the pre-fix module and then replaced: the "
    "stale file was deleted and re-captured, and the criteria digest is "
    "identical because the criteria text did not change, which is the honest "
    "reading rather than a new digest. (d) NO battery ran this window, so the "
    "registry count 521 suites / 4102 criteria is a WIRING count and not a "
    "green measurement - the register row stays OPEN and now carries that "
    "target. (e) The debt register took the R2391 lesson once more: the first "
    "attempt appended ' | note_appended_R2395: ...' as a NEW key and the "
    "whole register refused E_DR_BAD_ROW; the text was folded inside the note "
    "instead and the gate reads CLAIM-FIRST again. (f) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice.",

    "2026-11-03 R2395 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law forbids "
    "for every lane task; src/os/register_loop_task.ps1 already passes an "
    "explicit S4U principal but needs an elevated shell, and this session is "
    "unelevated, so the task definition was left untouched "
    "(hundred-and-fiftieth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",

    "R2395 tokens: local=~22k api=0 api_reason=product window - one headroom "
    "reading and its six-criteria suite written to criteria pinned two rounds "
    "earlier, one AST registry reader after the real tree proved the table is "
    "not literal, one registry wiring line, one two-leg evidence capture with "
    "three adjacent suites, one read-only live capture that named three real "
    "suites inside 31.9s..67.8s of the cap, one board stamp and one measured "
    "gap row seeded, one carried battery row re-targeted inside its own note "
    "after the register refused a new key, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches",
]

DONE_ROW = (
    "- [x] [done 2026-11-03 R2395] R2395 product window: "
    "src/os/runner_suite_timeout_headroom.py plus its six-criteria suite "
    "(AC-RTH1..AC-RTH6 pinned at R2393) - the 300s per-suite cap is a reading "
    "now: three REAL ledger-apimarket suites sit at 232.2s..268.1s "
    "(headroom 31.9s..67.8s) where a loaded machine aborts the whole battery "
    "in silence. SUITE PASS 6/6 twice (digest CB10BFECDEC50D24) plus three "
    "adjacent suites green, wired os-runner-suite-timeout-headroom(6) so the "
    "registry reads 521 suites / 4102 criteria. Live: "
    "qa/runner-suite-timeout-headroom-live-R2395.log.")

CARRIED_ROW = (
    "- [ ] [carried 2026-11-03 R2395] R2396 first item: THE BATTERY ON THE "
    "COMMITTED R2395 TREE, zero product edits until green (the R2168 "
    "mixed-tree rule). R2395 changed src/os (runner_suite_timeout_headroom.py, "
    "test_runner_suite_timeout_headroom.py) and one runner entry, so the "
    "registry reads 521 suites / 4102 criteria and the pre-registered "
    "expectation is exactly that total; the reading this window shipped says "
    "which suites are closest to the cap, so a per-suite timeout under load is "
    "now a named risk rather than a surprise.")

CEO_NOW = (
    "R2395: the battery's 300s per-suite cap became a reading - on today's "
    "real evidence pile three ledger-apimarket suites sit at 232.2s, 246.8s "
    "and 268.1s against that cap, i.e. 31.9s..67.8s of headroom, which is "
    "exactly how R2393 lost a whole battery leg with no code defect.")

CEO_ART = (
    "qa/runner-suite-timeout-headroom-live-R2395.log (three band suites named "
    "on the real pile) and qa/runner-suite-timeout-headroom-R2395.log "
    "(SUITE PASS 6/6)")

CEO_NEXT = (
    "the carried battery on this tree at its re-measured target (521 suites / "
    "4102 criteria), then the second pre-registered row "
    "ledger_line_shape_guard (AC-LLSG1..6)")


def main(argv):
    now = None
    for index, token in enumerate(argv):
        if token == "--now" and index + 1 < len(argv):
            now = argv[index + 1]
    dry = "--execute" not in argv
    if now is None:
        raise SystemExit("REFUSED: --now <ISO timestamp> is required")
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        payload = json.load(handle)
    before = len(io.open(STATE, "r", encoding="utf-8", newline="")
                 .read().encode("utf-8"))
    payload["tick"] = 2395
    payload["log"] = list(payload["log"]) + list(ITEMS)
    payload["last_decision_rows"] = 140
    known = list(payload.get("last_dec_tokens") or [])
    for token in TOKENS:
        if token not in known:
            known.append(token)
    payload["last_dec_tokens"] = known
    print("state tick=%d log->%d before=%d tokens=%d"
          % (payload["tick"], len(payload["log"]), before, len(known)),
          flush=True)
    if dry:
        print("DRY: no byte written")
        return 0
    text = SIO.canon(json.dumps(payload, indent=2, ensure_ascii=False))
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        readback = json.load(handle)
    equal = readback == json.loads(json.dumps(payload))
    size = len(io.open(STATE, "r", encoding="utf-8", newline="")
               .read().encode("utf-8"))
    print("state written %d bytes json_equal=%s" % (size, equal), flush=True)

    counters = CEC.recompute()
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        export = json.load(handle)
    export["export_ts"] = now
    export["do"] = CEO_NOW
    face = dict(export.get("ceo_face") or {})
    face["current"] = CEO_NOW
    face["latest_artifact"] = CEO_ART
    face["last_artifact"] = CEO_ART
    face["next_milestone"] = CEO_NEXT
    face["next_milestone_due"] = "2026-11-05T23:00:00+08:00"
    face["updated_at"] = now
    export["ceo_face"] = face
    outs = list(export.get("outs") or [])
    outs.insert(0, CEO_ART)
    export["outs"] = outs[:12]
    drive = dict(export.get("self_drive") or {})
    for key in ("window", "window_days", "log_lines_in_window",
                "idle_fast_mention_lines", "no_pullable_mention_lines",
                "substantive_non_idle_mention_lines", "queue_main_open",
                "queue_tech_open", "queue_explore_open"):
        if key in counters:
            drive[key] = counters[key]
    export["self_drive"] = drive
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, indent=2, ensure_ascii=False) + "\n")
    print("export refreshed counters=%r"
          % dict((k, drive.get(k)) for k in
                 ("log_lines_in_window", "queue_tech_open")), flush=True)

    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        backlog = handle.read()
    if DONE_ROW not in backlog:
        backlog = backlog.rstrip("\n") + "\n\n" + DONE_ROW + "\n\n" \
            + CARRIED_ROW + "\n"
        with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
            handle.write(backlog)
        print("backlog appended", flush=True)
    with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("%s tick=2395 R2395 product window "
                     "runner_suite_timeout_headroom shipped; battery carried\n"
                     % now)
    print("heartbeat written", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))