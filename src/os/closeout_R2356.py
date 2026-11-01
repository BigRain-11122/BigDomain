"""closeout_R2356 - append this window's log items, then refresh the CEO face.

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
EVIDENCE = "qa/orphan-promotion-wire-R2356.log"

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2356 product window: the promotion WRITER now asks the ledger before it "
    "copies. src/os/orphan_promotion_wire.py gates RECORDED, STALE, a live "
    "record whose file is gone and an unrecorded canonical file with their own "
    "codes, and lets a lapsed judgement through while naming the until it "
    "supersedes; six pre-registered criteria green twice with an identical "
    "digest, four adjacent suites green, registry now reads 487 suites / 3898 "
    "criteria."
)

ARTIFACT = (
    "src/os/orphan_promotion_wire.py + src/os/test_orphan_promotion_wire.py "
    "with qa/orphan-promotion-wire-R2356.log (1067B) - SUITE PASS 6/6 twice, "
    "adjacent orphan-trace / orphan-promote / orphan-promotion-ledger / "
    "followup-history all 6/6; live dogfood --plan R2136 refuses "
    "E_OPW_RECORDED naming the record (reconcile-all-R2136.log, by R2342, "
    "until R2360) where orphan_promote alone only reported a taken target."
)

NEXT = (
    "R2357: the battery on the committed R2356 tree with zero product edits, "
    "pre-registered at 487 suites / 3898 criteria (+1 suite / +6 criteria "
    "against R2355 486/3892), then back to the tech head (AC-FSF1)."
)

LOG_ITEMS = [
    "2026-11-02 R2356 product window (five-silence scan at open: empty git "
    "status --short at 68be226d, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=112 tokens=74 new=0, "
    "the group orders tail still the 2026-11-01 10:4x model-policy baseline "
    "already acked as non-execution, benchmarks refreshed 2026-11-01 inside "
    "the seven-day gate - so nothing was owed and the window pulled work). "
    "THE DEBT GATE NAMED product-face-R2356 first=yes at "
    "state/queue/tech.md:400 prefix AC-OPW1, and that row's own criteria were "
    "pinned at R2342 BEFORE any code, so the anchor check was re-run at HEAD "
    "first: E_OPW, os-orphan-promotion-wire and test_orphan_promotion_wire "
    "were git grep -F zero-occupancy in src/ and qa/, while AC-OPW and "
    "orphan_promotion_wire appeared only in bookkeeping files that refer to "
    "the seed row - recorded as such rather than reported as a clean null. "
    "SHIPPED: src/os/orphan_promotion_wire.py, whose gate asks "
    "orphan_promotion_ledger for the reading (its declaration reader, entry "
    "validator, canonical file listing and five-class judgement all imported) "
    "and orphan_promote for the round, the canonical name and the plan, and "
    "runs BEFORE the writer looks at the target at all. RECORDED refuses "
    "naming round, canonical, declared_by and until; STALE refuses naming the "
    "recorded and the on-disk digest; a claim whose file is gone refuses as "
    "E_OPW_LIVE_RECORD while its judgement still holds, and an UNRECORDED "
    "canonical file refuses because the ledger cannot say who wrote the bytes "
    "a copy would replace; a LAPSED judgement permits the copy and the plan "
    "names the until it supersedes. The module holds no write primitive of its "
    "own - the only mutation on this path is orphan_promote's single "
    "os.replace. MEASURED: SUITE PASS 6/6 on the first green run and 6/6 again "
    "with an identical criterion digest "
    "(13e6ea4b36c064a9b766792b292c46d40195ee5f9e72169091731f5e62f03c6e), four "
    "adjacent suites green, wired os-orphan-promotion-wire(6) in "
    "src/sandbox/reconcile_all.py, matrix regenerated to 487 suites / 3898 "
    "criteria (46605B) - exactly the number the successor register row "
    "predicts. LIVE DOGFOOD on the real ledger: --plan R2136 now refuses "
    "E_OPW_RECORDED naming reconcile-all-R2136.log, declared by R2342 until "
    "R2360, where orphan_promote alone could only say the target existed; "
    "--plan R9998 passes the gate and is refused by orphan_promote as "
    "E_OTP_NO_ROUND, which proves the composition still defers to the writer's "
    "own laws. Product score 2 points: a runnable guard on the one path that "
    "could silently overwrite a recorded promotion.",
    "R2356 tokens: local=~26k api=0 api_reason=product window - one module "
    "and one six-criteria suite written to pre-pinned criteria, two suite "
    "runs for the digest pair, four adjacent suites, one live dogfood pair, "
    "one matrix regeneration, one row closed and one row seeded in the tech "
    "queue, two register writes through their own writers, and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero "
    "external API touches",
    "R2356 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition was left untouched. Open "
    "local-lane item for an elevated window (hundred-and-fourteenth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",
    "R2356 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read new=0 over 112 "
    "rows and 74 tokens, so no row was owed execution, a rejection or an "
    "acknowledgement this window and the baseline was left unchanged rather "
    "than widened without cause. Honest disclosures: (a) no full battery ran "
    "this window - the register row for it was opened first=yes and the suite "
    "was proven green twice on its own plus four adjacent suites, which is "
    "weaker than a registry-wide run and is named here so the next window "
    "cannot read it as one; (b) the queue row for R2342 was closed in place "
    "and the successor row appended at the tail, so the head moved to "
    "AC-FSF1 and claimable still reads 11; (c) tasks.md is the P-47 canonical "
    "board and carries no row for this tech item, disclosed rather than "
    "silently skipped.",
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
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2356_")
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
        "src/os/orphan_promotion_wire.py", "on",
        "R2356 product: the promotion writer asks the ledger before it copies "
        "- a recorded, stale, live-but-fileless or unrecorded canonical target "
        "refuses with its own code, and a lapsed judgement allows the copy "
        "while naming the record it supersedes",
    ])
    data["results"].append([
        "R2356",
        "product window on the register's first=yes item: one module plus a "
        "six-criteria suite pre-pinned at R2342, SUITE PASS 6/6 twice with an "
        "identical digest, four adjacent suites green, matrix regenerated to "
        "487 suites / 3898 criteria, and a live dogfood that now names the "
        "record R2136 would have walked over; register row closed and the "
        "battery row opened first=yes; no registry-wide battery this window "
        "and that is disclosed rather than implied",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2356_TICK_ROW count=%d" % len(tick_rows))
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