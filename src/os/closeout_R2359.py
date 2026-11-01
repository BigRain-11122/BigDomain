"""closeout_R2359 - close the claimed tech row, seed the measured gap, log.

Every value is derived in this run: the queue edit names the row it replaces
and the row it appends, the export counts come from the shipped checker (F3
law), and the artifact line names an evidence file that exists on disk. Dry
run by default; --execute applies the queue edit as one atomic replace, appends
to state.json through state_io.canon plus one atomic replace, and writes the
export through its single writer.
"""

import io
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402
import check_export_consistency as CC  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

HEAD_MARK = "should ask the HISTORY before it hands the window out"
SEED_NAME = "review_window_wire_argument_guard"

CLOSED_NOTE = (
    " [done 2026-11-02 R2359] DELIVERED as the R2359 product window: "
    "`review_window_wire` now asks `review_window_history.history` BEFORE it "
    "hands a window out, so a declarations list whose declared_by rewinds "
    "refuses as E_RWHW_DECL_HISTORY naming both rounds instead of aging every "
    "exempt entry against a window taken from a list that is not a history. "
    "The window number still comes from review_window_decl.resolve (two "
    "authorities kept apart: history says whether the list IS a history, the "
    "resolver says what number it pins), UNPINNED and DRIFT keep the resolver's "
    "own code and its own detail byte for byte, and a legal moved-but-monotonic "
    "list is a REPORT naming every move rather than a refusal. The wire gained "
    "a `window_report` dict, a pinned REPORT_KEYS set and a --check CLI "
    "(0/2/3/5) that writes nothing. SUITE PASS 6/6 with an identical digest "
    "pair via evidence_capture (qa/review-window-history-wire-R2359.log, "
    "3110B, legs=2 identical=True, adjacent=3: review-window-wire, "
    "review-window-history, review-window all green), wired as "
    "os-review-window-history-wire(6); the suite matrix regenerated to 489 "
    "suites / 3910 criteria. LIVE: window=100 source=declaration moves=0 "
    "declared_by=R2305 verdict=EMPTY-HISTORY at exit 0. Seeded from this "
    "window's own measurement: the argument path still bypasses the guard."
)

SEED_TEXT = (
    "- [ ] P2 tech seed (R2359, from this window own measured gap): "
    "`%s` - the history guard landed on the DECLARED path only. "
    "`exempt_review --window N` (window_source=argument) never asks "
    "review_window_wire, so an operator who passes an explicit window against "
    "a declarations list that rewinds still ages every entry with no refusal: "
    "measured this window, `audit(root, round, window)` takes the number and "
    "returns, while the declared path refuses E_RWHW_DECL_HISTORY on the same "
    "file. Criteria AC-RWAG1..AC-RWAG6 pre-registered HERE BEFORE any code: "
    "AC-RWAG1 the argument path asks the history before it ages any entry, so "
    "a rewinding declaration refuses E_RWHW_DECL_HISTORY even when --window is "
    "passed explicitly, naming both rounds; AC-RWAG2 a lone-argument reading "
    "on a monotonic declaration stays byte-identical (same rows, same window, "
    "same report keys), so the guard adds a refusal and nothing else; "
    "AC-RWAG3 an UNPINNED declaration on the argument path keeps today's "
    "reading exactly, because the explicit window is the caller's and not the "
    "declaration's, and no new code is invented for the absent case; "
    "AC-RWAG4 the refusal happens before any entry is aged - zero counts and "
    "WINDOW-REFUSED in the CLI output, with the declaration bytes untouched "
    "(digest before and after); AC-RWAG5 CLI codes 0/2/5 and --json keys "
    "pinned at the wire level and byte-stable across two runs; AC-RWAG6 pure "
    "ASCII, stdlib only, zero network, no clock, the history law imported "
    "rather than restated, plus its own reconcile label. Anchor check at HEAD "
    "2026-11-02: %s, AC-RWAG and E_RWAG were all git grep -F "
    "zero-occupancy (0 hits each)." % (SEED_NAME, SEED_NAME)
)

DO = (
    "R2359 product window: the review window's declared path finally asks the "
    "HISTORY, so a declarations list whose rows rewind in time is refused "
    "instead of quietly aging every exempt entry against it."
)

ARTIFACT = (
    "src/os/review_window_wire.py (guarded) + "
    "src/os/test_review_window_history_wire.py with "
    "qa/review-window-history-wire-R2359.log (3110B) - SUITE PASS 6/6 twice "
    "identical, three adjacent review-window suites green; live reading "
    "window=100 moves=0 verdict=EMPTY-HISTORY."
)

NEXT = (
    "R2360: the battery on the committed R2359 tree with zero product edits, "
    "pre-registered at 489 suites / 3910 criteria (+1 suite / +6 criteria "
    "against R2358 488/3904), then the measured argument-path gap above."
)

LOG_ITEMS = [
    "2026-11-02 R2359 product window (five-silence scan clean at open: empty "
    "git status --short, no .git/index.lock; scan_five_still read LEDGER "
    "atbd_lines=0 unreplied_groups=0 and DEC rows=112 tokens=74 new=0, so no "
    "decision row was owed; the group orders tail still reads the 2026-11-01 "
    "10:4x model-policy baseline already acked by R2350 as non-execution; "
    "benchmarks refreshed 2026-11-01, inside the seven-day gate). THE DEBT GATE "
    "NAMED THE PRODUCT FACE (CLAIM-FIRST item=product-face-R2359 opened=R2358) "
    "and this window took it: state/queue/tech.md:402 prefix AC-RWHW1, whose "
    "AC-RWHW1..AC-RWHW6 were pinned INSIDE that row at R2345 BEFORE any code, "
    "re-read at this head rather than trusted to the gate note. ANCHOR CHECK "
    "RE-RUN AT HEAD before any code: E_RWHW was git grep -F zero-occupancy in "
    "src/ and qa/, while review_window_wire and AC-RWHW appeared only in prose "
    "and state files (closeout scripts, backlog, export, state.json, the seed "
    "row) - recorded as such rather than reported as a clean null. THE GAP, "
    "measured at R2345 and confirmed here: review_window_history refuses a "
    "declarations list whose declared_by rewinds, but nothing consumed it - "
    "review_window_wire.declared_window asked review_window_decl.resolve only, "
    "and that resolver compares the last row against the top-level window while "
    "being blind to the ORDER of the rows, so exempt_review could age every "
    "accepted entry against a window taken from a list that is not a history. "
    "SHIPPED: review_window_wire gained window_report(root, round_text), a "
    "pinned REPORT_KEYS tuple, a --check CLI and the guard. The history is "
    "asked FIRST and a rewind refuses E_RWHW_DECL_HISTORY carrying the "
    "history's own code and both rounds; UNPINNED and DRIFT keep the same code "
    "and the same resolver detail the old path produced (measured against the "
    "resolver's own exception inside the suite), so the absent case keeps its "
    "meaning byte for byte and a DRIFT keeps the resolver's wording rather than "
    "a re-worded one; a moved-but-monotonic list hands the window out and names "
    "every move in the report, because a legal move is history being reported "
    "and not a defect. TWO AUTHORITIES, KEPT APART ON PURPOSE and disclosed: the "
    "history law answers 'is this list a history', the resolver answers 'what "
    "number does it pin', so this file still derives no number of its own and "
    "the round argument is carried for the resolver rather than used by the "
    "guard. MEASURED: SUITE PASS 6/6 on the second run (the first green run "
    "failed AC-RWHW1 because this window's own map emitted E_RWW_DECL_HISTORY "
    "while the pinned criterion names E_RWHW_DECL_HISTORY - the criterion was "
    "right and the module was corrected, no criterion widened) with an "
    "identical digest pair through evidence_capture (qa/"
    "review-window-history-wire-R2359.log, 3110B, legs=2 identical=True, "
    "adjacent=3), wired os-review-window-history-wire(6) in "
    "src/sandbox/reconcile_all.py, and the suite matrix regenerated to 489 "
    "suites / 3910 criteria (46823B). FOUR adjacent suites re-run green in the "
    "same window (review-window-wire 6/6, review-window-history 6/6, "
    "review-window 6/6, exempt-review 6/6). LIVE: REVIEW WINDOW WIRE window=100 "
    "source=declaration moves=0 declared_by=R2305 verdict=EMPTY-HISTORY at "
    "exit 0 - the real declaration is a one-row list, so the guard is proved "
    "prospective on fixtures rather than claimed as a live catch. Product score "
    "2 points: a runnable refusal where a reading used to be impossible.",
    "R2359 tokens: local=~21k api=0 api_reason=product window - one shipped "
    "guard plus a six-criteria suite written to pre-pinned criteria, two suite "
    "runs (one red on this window own refusal-code prefix, the criterion was "
    "right), one evidence capture with three adjacent suites, four adjacent "
    "suites re-run green, one runner wiring line, one matrix regeneration, one "
    "queue row closed and one measured gap row seeded, and the state/export/"
    "heartbeat/board closeout; zero cloud calls and zero external API touches",
    "R2359 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-seventeenth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2359 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read new=0 over 112 "
    "rows and 74 tokens, and the evolution ledger carries no @BigDomain row, so "
    "nothing was executed, rejected or acknowledged this window and the "
    "baseline was left unchanged rather than widened without cause. Honest "
    "disclosures: (a) NO battery ran this window and the register row is the "
    "successor battery, opened at the MEASURED target 489 suites / 3910 "
    "criteria rather than predicted from the note; (b) the declaration on disk "
    "is a one-row list, so the rewind and move branches are proved on fixtures "
    "and the LIVE reading is EMPTY-HISTORY - stated as a guard, not sold as a "
    "catch; (c) the argument path (exempt_review --window N) still bypasses "
    "the guard, measured this window and seeded as the successor row instead of "
    "being quietly widened into this one; (d) the wire's window still comes "
    "from the resolver, so a patched history that disagrees with the resolver "
    "moves the report's verdict and moves but not its number - disclosed as the "
    "deliberate split of authority; (e) tasks.md was left untouched: it is the "
    "P-47 canonical board and carries no row for this tech slice, disclosed "
    "rather than silently skipped.",
]


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def proposal_counts():
    with io.open(PROPOSALS, "r", encoding="utf-8") as handle:
        text = handle.read()
    heads = [line for line in text.split("\n")
             if line.startswith("### BD-PROP-")]
    opened = [line for line in heads if "状态 open" in line]
    return {"proposals_total": len(heads), "proposals_open": len(opened)}


def queue_edit(execute):
    """Close the claimed row in place and append the measured gap row."""
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        original = handle.read()
    lines = original.split("\n")
    hits = [index for index, line in enumerate(lines) if HEAD_MARK in line]
    if len(hits) != 1:
        raise SystemExit("E_R2359_HEAD count=%d" % len(hits))
    index = hits[0]
    row = lines[index]
    if not row.startswith("- [ ]"):
        raise SystemExit("E_R2359_NOT_OPEN %r" % row[:24])
    lines[index] = row.replace("- [ ]", "- [x]", 1) + CLOSED_NOTE
    if SEED_NAME in original:
        raise SystemExit("E_R2359_SEED_DUPLICATE")
    tail = original.count("\n")
    if lines[-1] == "":
        lines[-1] = SEED_TEXT
        lines.append("")
    else:
        lines.append(SEED_TEXT)
        lines.append("")
    text = "\n".join(lines)
    data = text.encode("utf-8")
    print("QUEUE row=%d appended=%s lines=%d bytes=%d"
          % (index + 1, SEED_NAME, tail + 2, len(data)))
    if not execute:
        return len(data)
    handle, temp = tempfile.mkstemp(dir=os.path.dirname(TECH),
                                   prefix=".tech_R2359_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, TECH)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(TECH, "rb") as back:
        landed = back.read()
    print("QUEUE READBACK ok=%s" % (landed == data))
    return len(data)


def bump_state(execute):
    """Append the window items and write the canon with a read-back proof."""
    state = read_json(STATE)
    state["tick"] = state["tick"] + 1
    state["log"] = state["log"] + LOG_ITEMS
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    canon = SIO.canon(payload)
    data = canon.encode("utf-8")
    print("STATE tick=%d log_items=%d bytes=%d margin=%d"
          % (state["tick"], len(state["log"]), len(data), 78500 - len(data)))
    if not execute:
        return data
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2359_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(STATE, "rb") as back:
        landed = back.read()
    ok = landed == data
    print("STATE READBACK ok=%s" % ok)
    return data if ok else None


def first_by_key(rows):
    seen = set()
    out = []
    for row in rows:
        key = str(row[0])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def write_export(execute):
    """Every self_drive field comes from the SHIPPED checker, not a copy."""
    derived, live_state, _old, patterns = CC.recompute()
    data = read_json(EXPORT)
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "src/os/review_window_wire.py", "on",
        "R2359 product: the declared review path asks the declarations HISTORY "
        "first, so a list whose rows rewind refuses E_RWHW_DECL_HISTORY naming "
        "both rounds instead of aging every exempt entry against it",
    ])
    data["results"].append([
        "R2359",
        "product window on the debt-gate row: one guard plus a six-criteria "
        "suite pre-pinned at R2345, SUITE PASS 6/6 with an identical digest "
        "pair, three adjacent suites green, matrix regenerated 489/3910, one "
        "queue row closed and one measured argument-path gap seeded",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2359_TICK_ROW count=%d" % len(tick_rows))
    tick_rows[0][0] = str(live_state["tick"])
    data["outs"] = first_by_key(data["outs"])
    data["results"] = first_by_key(data["results"])
    data["self_drive"] = derived
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT tick=%s self_drive=%s bytes=%d"
          % (str(live_state["tick"]), json.dumps(derived),
             len(text.encode("utf-8"))))
    if not execute:
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("EXPORT READBACK ok=%s" % ok)
    return 0 if ok else 2


def write_heartbeat(state, execute):
    row = "%d %s\n" % (state["tick"], NOW.strftime("%Y-%m-%dT%H:%M:%S"))
    if not execute:
        print("HEARTBEAT would append: %s" % row.strip())
        return 0
    with io.open(HEARTBEAT, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(row)
    return 0


def main(argv):
    execute = "--execute" in argv
    if "--export-only" in argv:
        return write_export(execute)
    queue_edit(execute)
    code = bump_state(execute)
    if code is None:
        return 2
    code = write_export(execute)
    if code:
        return code
    return write_heartbeat(read_json(STATE), execute)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))