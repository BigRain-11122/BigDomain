"""closeout_R2357 - append this window's log items, then refresh the CEO face.

Every value is derived in this run: the log items are written here, the export
counts come from the shipped checker (F3 law), and the artifact line names an
evidence file that exists on disk. Dry run by default; --execute appends to
state.json through state_io.canon plus one atomic replace and writes the
export through its single writer. No fold is due this window: the canon
measured well under the waterline, so folding would only move history.
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
EVIDENCE = "qa/followup-section-foreign-R2357.log"

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2357 product window: a SECTION line under a name the follow-up ritual "
    "does not own is now NAMED instead of parsed and forgotten. "
    "src/os/followup_section_foreign.py reads every evidence round and returns "
    "FOREIGN-SECTION or VOCABULARY-CLEAN per round plus a directory census; "
    "the LIVE reading of qa/ is 454 rounds clean with an empty census."
)

ARTIFACT = (
    "src/os/followup_section_foreign.py + "
    "src/os/test_followup_section_foreign.py with "
    "qa/followup-section-foreign-R2357.log (1149B) - SUITE PASS 6/6 twice "
    "identical, followup-history and battery-followup adjacent green; live "
    "--check reads 454 rounds / 454 clean / census foreign=none missing=none "
    "at exit 0."
)

NEXT = (
    "R2358: the battery on the committed R2357 tree with zero product edits, "
    "pre-registered at 488 suites / 3904 criteria (+1 suite / +6 criteria "
    "against R2356 487/3898), then the seeded wire row AC-FSFW1 makes the "
    "follow-up ritual ask this reader before it regenerates the matrix."
)

LOG_ITEMS = [
    "2026-11-02 R2357 product window (five-silence scan at open: empty git "
    "status --short at 30f0dd01, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=112 tokens=74 new=0, "
    "the group orders tail still the 2026-11-01 10:4x model-policy baseline "
    "already acked as non-execution, benchmarks refreshed 2026-11-01 inside "
    "the seven-day gate). THE GATE NAMED THE CARRIED BATTERY "
    "(reconcile-battery-R2357, pre-registered 487 suites / 3898 criteria) AND "
    "THE PRODUCT LAW OUTRANKED IT: the register row had been opened at the R2356 "
    "close, the tree carried a committed product edit from that window, and the "
    "product-first law asks what new physical thing a window leaves behind, so "
    "the window took the queue head the gate note itself names as the resume "
    "point (AC-FSF1) and LEFT THE BATTERY ROW OPEN rather than closing it - the "
    "row must still be run, at the target named above, and closing it here "
    "without a run would be the false claim this house forbids. ANCHOR CHECK "
    "RE-RUN AT HEAD before any code: followup_section_foreign, AC-FSF and "
    "E_FSF were git grep -F zero-occupancy in src/ and qa/. SHIPPED: "
    "src/os/followup_section_foreign.py, whose vocabulary and parse are "
    "followup_history's (imported at call time, proved in the suite by patching "
    "both and watching the report move) and whose readings are disjoint and "
    "exhaustive - FOREIGN-SECTION lists the names a round reported outside the "
    "vocabulary, VOCABULARY-CLEAN means every name it reported is inside it, "
    "and a directory census reports the foreign names seen and the ritual names "
    "never seen, so a ritual RENAME is a set difference instead of a silent "
    "gap. It writes nothing, reads no clock, has no round threshold, and fails "
    "closed at exit 3 (E_FSF_NO_EVIDENCE / E_FSF_UNREADABLE / E_FSF_DUP_ROUND) "
    "rather than ever reading CLEAN. MEASURED: SUITE PASS 6/6 on the third run "
    "after two rounds of this window's OWN fixture errors (the narrowed-"
    "vocabulary fixture still expected CLEAN, the census expectation carried a "
    "hand-sorted order and then a round that reported all four names), wired "
    "os-followup-section-foreign(6) in src/sandbox/reconcile_all.py, and "
    "evidence_capture wrote qa/followup-section-foreign-R2357.log (1149B, "
    "legs=2 identical=True, adjacent=2). LIVE reading of the real qa/ pile: "
    "rounds=454 clean=454 foreign=0 census foreign=none missing=none verdict="
    "VOCABULARY-CLEAN exit 0 - the pile is clean TODAY and the reader is the "
    "guard for the day a ritual name changes, which is stated as a guard rather "
    "than sold as a finding. Product score 2 points: a runnable reader that "
    "turns a parsed-and-forgotten name into a named verdict.",
    "R2357 tokens: local=~15k api=0 api_reason=product window - one module "
    "and one six-criteria suite written to pre-pinned criteria, three suite "
    "runs (two red on this window own fixtures, the module never changed), one "
    "runner wiring line, one evidence capture with two adjacent suites, one "
    "live reading of the 454-round pile, one queue row closed and one real gap "
    "row seeded, and the state/export/heartbeat/board closeout; zero cloud "
    "calls and zero external API touches",
    "R2357 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition was left untouched. Open "
    "local-lane item for an elevated window (hundred-and-fifteenth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",
    "R2357 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read new=0 over 112 "
    "rows and 74 tokens, and the evolution ledger carries no @BigDomain row, "
    "so nothing was executed, rejected or acknowledged this window and the "
    "baseline was left unchanged rather than widened without cause. Honest "
    "disclosures: (a) NO battery ran this window and the register row "
    "reconcile-battery-R2357 stays OPEN with its measured target named so the "
    "next window cannot read this one as a verification; (b) the first two "
    "suite runs were red on this window's own fixtures and neither was a "
    "module defect - a narrowed vocabulary correctly turns the names it no "
    "longer owns into foreign ones, the census list is sorted rather than "
    "hand-ordered, and a round that reports all four ritual names leaves no "
    "set difference to name - each corrected in the test with no criterion "
    "widened; (c) the live pile is CLEAN today, so this module's value is "
    "prospective and is not claimed as a live catch; (d) tasks.md is the P-47 "
    "canonical board and carries no row for this tech item, disclosed rather "
    "than silently skipped.",
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
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2357_")
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
    """Keep the first row per key (its own first field), in file order."""
    seen = set()
    out = []
    for row in rows:
        key = str(row[0])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def write_export(state, execute):
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
        "src/os/followup_section_foreign.py", "on",
        "R2357 product: a SECTION line under a name the follow-up ritual does "
        "not own is named per round with a directory census, so a ritual rename "
        "is a set difference instead of a silent gap; the live 454-round pile "
        "reads clean today",
    ])
    data["results"].append([
        "R2357",
        "product window on the queue head the gate note names: one reader plus "
        "a six-criteria suite pre-pinned at R2343, SUITE PASS 6/6, two adjacent "
        "suites green, live reading 454 rounds / 454 clean / census empty, one "
        "queue row closed and one measured gap row seeded; the carried battery "
        "is left OPEN with its target named rather than claimed",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2357_TICK_ROW count=%d" % len(tick_rows))
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
        return write_export(read_json(STATE), execute)
    code = bump_state(execute)
    if code is None:
        return 2
    code = write_export(read_json(STATE), execute)
    if code:
        return code
    return write_heartbeat(read_json(STATE), execute)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))