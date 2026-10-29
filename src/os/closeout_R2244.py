"""R2244 closeout: bump tick, append the three round log lines, verify.

String surgery on the log array only, so the canonical 16-space indent
and the LF dialect of the existing file are preserved byte for byte
outside the three inserted lines (the R2243 layout repair precedent).
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

NARRATIVE = (
    "2026-10-29 R2244 (five-silence scan clean at open: decisions.md carries "
    "283 non-empty rows and 185 content-addressed D/C tokens with ZERO "
    "additions against the stored 190-token baseline - the five apparent "
    "losses are the known truncation artefacts, and the baseline is "
    "deliberately left as a superset so a later-restored token cannot "
    "masquerade as a new decision - so zero domain action; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with "
    "zero unreplied; the group orders tail is unchanged at the 2026-10-29 "
    "02:1x CEO-PROXY fleet event round R2.48 already consumed in R2226; "
    "benchmarks refreshed 2026-10-29 inside the seven-day gate; tree clean, "
    "no index.lock) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, and both queues sit BELOW the "
    "standing floors (tech 8 open, explore 5 open), so this window claimed "
    "the tech head instead of opening a new product face. Product: "
    "src/os/queue_floor.py, the read-only floor gauge the R2240-a seed "
    "named. The floors (main >= 5, tech >= 10, explore >= 10) were until "
    "now enforced by eyeballing a grep count mid-window, so a shortfall was "
    "discovered only after the queue had already starved and the round had "
    "to spend its budget on seeding. The gauge reads the three queue files "
    "and prints one line - QUEUE FLOOR main=1/5 tech=7/10 explore=5/10 "
    "verdict=FLOOR-DEBT shortfall=12 - plus one line per queue. The row law "
    "is narrow on purpose: column-0 anchored '- [ ]' with a space or end "
    "after the box, so '- [ ]text', indented continuations, prose and table "
    "rows are not rows; the first suite run caught exactly the '- [ ]text' "
    "case and the implementation was tightened to the pre-registered "
    "intent rather than the criterion widened. Eight gate marker forms are "
    "reported as gated_rows and never counted as claimable, so a queue of "
    "pure gates reads as debt rather than as stock. An empty queue is an "
    "honest zero (claimable 0, shortfall == the whole floor) and a missing "
    "queue file reads MISSING with exit 3 and the whole floor as shortfall. "
    "The CLI exits 0 met / 2 short or bad flags / 3 missing, and --json "
    "carries the five pinned report keys byte-stably. Criteria ran as "
    "AC-QF1..AC-QF8: the seed pre-registered six before the code, and this "
    "window added AC-QF7 (one line plus a live-tree recount through an "
    "independent code path) and AC-QF8 (purity plus ASCII/no-network plus "
    "the battery wiring) - both additions disclosed as landing in the same "
    "window as the code, with no pre-registered criterion relaxed. Evidence: "
    "SUITE PASS 8/8 double-run byte-identical criterion sha16 "
    "8D4D43DB92838EA2 (qa/queue-floor-R2244-a.log and -b.log, 762B each, "
    "single writer utf-8 LF by src/os/evidence_R2244.py, never a shell "
    "redirection); wired os-queue-floor(8); five adjacent os suites green "
    "(qa/regression-R2244.log, fails=0). Live reading at closeout: "
    "main=1/5 (2 open of which 1 gated), tech=7/10 (8 open of which 1 "
    "gated), explore=5/10 -> FLOOR-DEBT shortfall=12, which from now on is a "
    "measurement instead of a mid-window discovery. Gap named for the next "
    "window: the full reconcile battery and the suite-matrix regeneration "
    "were NOT run here (25-minute budget, the R2168 mixed-tree rule) and are "
    "the top carried item."
)

LEDGER = (
    "R2244 tokens: local=~15k api=0 api_reason=product window on the tech "
    "head - one read-only floor gauge with its eight-criterion suite, one "
    "single-writer double-run evidence pair, five adjacent os regressions, "
    "and the queue/backlog/state/export closeout; zero cloud calls and zero "
    "external API touches; the reconcile battery and the matrix regeneration "
    "are deferred and recorded"
)

SELF_HEAL = (
    "R2244 self-heal check: BigDomain-OSLoop exists and is Running, but its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal but applying it needs an "
    "elevated shell and this session is unelevated, so the definition of the "
    "loop hosting this window was left untouched. Open local-lane item for "
    "an elevated window (fourteenth consecutive disclosure)."
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        text = handle.read()
    state = json.loads(text)
    before_tick = state["tick"]
    before_lines = len(state["log"])

    state["tick"] = before_tick + 1
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL])

    tick_old = '"tick": %d,' % before_tick
    tick_new = '"tick": %d,' % state["tick"]
    if text.count(tick_old) != 1:
        raise SystemExit("E_TICK_ANCHOR: tick line is not unique")
    text = text.replace(tick_old, tick_new)

    tail_marker = '\n  ]\n}\n'
    if not text.endswith(tail_marker):
        raise SystemExit("E_TAIL_LAYOUT: unexpected state.json tail")
    body = text[:-len(tail_marker)]
    for line in (NARRATIVE, LEDGER, SELF_HEAL):
        escaped = json.dumps(line, ensure_ascii=True)
        body += ',\n                ' + escaped
    new_text = body + tail_marker

    parsed = json.loads(new_text)
    if parsed != state:
        raise SystemExit("E_JSON_MISMATCH")

    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)

    print("TICK %d -> %d" % (before_tick, parsed["tick"]))
    print("LOG %d -> %d lines" % (before_lines, len(parsed["log"])))
    print("BYTES %d -> %d" % (len(text.encode("utf-8")),
                              len(new_text.encode("utf-8"))))
    print("CRLF %d LONE_CR %d" % (new_text.count("\r\n"),
                                  new_text.count("\r") -
                                  new_text.count("\r\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())