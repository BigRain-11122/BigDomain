"""closeout_R2354 - append this window's log items, fold, then refresh the
CEO face.

Every value is derived in this run: the log items are written here, the export
counts come from the shipped checker (F3 law), and the artifact line names an
evidence file that exists on disk. Dry run by default; --execute appends to
state.json through state_io.canon plus one atomic replace, folds the oldest
log window on a round boundary, and writes the export through its single
writer.
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
import state_fold as SF  # noqa: E402
import check_export_consistency as CC  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
EVIDENCE = "qa/queue-head-delivered-R2354.log"

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

FOLD_NO = 638
RESERVE = 200

DO = (
    "R2354 产品窗：队列的「报价」终于先问占用读数——已交付的行不再被端给新"
    "窗，而是被越过并点名是哪件模块交付的，报价继续走到下一条可认领行；全部"
    "前缀行都已交付时读 ALL-DELIVERED 而非 NO-HEAD。同窗清欠：债务簿里指向"
    "R2352 残留漂移的那行在 R2353 已被真实治好（本窗实测 TRIAGED 206/206、"
    "退出码 0、红套件转绿），故按 R2345 先例就地收口并开出继任电池行。"
)

ARTIFACT = (
    "src/os/queue_head_delivered.py + src/os/test_queue_head_delivered.py，"
    "证据 qa/queue-head-delivered-R2354.log（1476B，两次同一摘要，6/6，三条"
    "邻接套件全绿）；实况读数 QUEUE OFFER tech line=400 prefix=AC-OPW1 "
    "walked_over=1 verdict=OFFERED——本窗认领的 line 398 现在读 DELIVERED "
    "并被越过。"
)

NEXT = (
    "R2355：在已提交的 R2354 树上跑全量电池（预注册 485 套件 / 3886 判据，"
    "对 R2352 的 484/3880 恰为 +1 套件 / +6 判据），随后交付队列头 line 400 "
    "AC-OPW1 orphan_promotion_wire——让晋升写入器先问晋升账本"
)

LOG_ITEMS = [
    "2026-11-01 R2354 product window (five-silence scan clean at open: empty "
    "git status --short at 25ed012d, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=101 tokens=65 new=0, "
    "so no decision row was owed; the group orders tail still reads the "
    "2026-11-01 10:4x model-policy baseline already acked by R2350 as "
    "non-execution; benchmarks refreshed 2026-11-01, inside the seven-day "
    "gate). THE GATE NAMED A REPAIR THAT WAS ALREADY DONE, and that was this "
    "window first finding: debt_gate read CLAIM-FIRST "
    "item=residue-triage-live-drift opened=R2352, while R2353 had in fact "
    "discharged it - verified here by MEASUREMENT rather than by trusting "
    "prose: `residue_triage.py --check --round R2354` reads declaration=PINNED "
    "residue=206 triaged=206 untriaged=0 verdict=TRIAGED at exit 0, and the "
    "suite that was red at R2352 (os-residue-triage) reads SUITE PASS 6/6. "
    "So the register row was closed through its own writer (debt_close: open "
    "3->2, done 87->88, before=71943B after=71946B, readback ok) instead of "
    "re-running work, and the successor battery row was opened first=yes "
    "through debt_append (reconcile-battery-R2355, 71946B -> 72488B, readback "
    "ok) at the measured target of 485 suites / 3886 criteria. PRODUCT: "
    "claimed the queue head the reader named, state/queue/tech.md:398 prefix "
    "AC-QHO1 (queue_head_delivered), whose AC-QHO1..AC-QHO6 were written "
    "INSIDE that row at R2337 BEFORE any code, and the stale zero-occupancy "
    "claim was re-measured at HEAD (queue_head_delivered, AC-QHO, E_QHO, "
    "os-queue-head-delivered and test_queue_head_delivered hit prose only - "
    "the seed row, the backlog, the export and three closeout scripts). "
    "Shipped src/os/queue_head_delivered.py plus "
    "src/os/test_queue_head_delivered.py: the offer now asks "
    "queue_occupancy.audit_root before it hands a row out (patched in the "
    "suite, and the offer moves; this module carries no module-path regex and "
    "no os.path.exists of its own), walks the occupancy reading in FILE order "
    "over every DELIVERED row naming the modules that shipped it, offers the "
    "first row that is not DELIVERED, and reads ALL-DELIVERED - never NO-HEAD "
    "- when every prefixed row has shipped, because a full queue is not an "
    "empty one; only rows BEFORE the chosen head count as walked over. SUITE "
    "PASS 6/6 twice with an identical criterion digest through evidence_capture "
    "(qa/queue-head-delivered-R2354.log, 1476B, legs=2 identical=True) plus "
    "three adjacent suites green in the same capture, wired "
    "os-queue-head-delivered(6). LIVE: QUEUE OFFER tech line=400 prefix=AC-OPW1 "
    "walked_over=1 claimable=10 verdict=OFFERED - and the walked-over row is "
    "line 398 AC-QHO1 DELIVERED modules=queue_head_delivered, i.e. the very "
    "row this window claimed now reads DELIVERED and is skipped, which is "
    "exactly the shape that used to point a fresh window at finished work. "
    "Board: the AC-QHO row closed against the files on disk, one REAL gap row "
    "seeded from this window own live finding (queue_floor_delivered_wire, "
    "AC-FDW1..AC-FDW6 pre-registered, three anchors zero-occupancy), and the "
    "gauge reads FLOOR-MET main 5/5 tech 10/10 explore 10/10. The battery was "
    "NOT run: this window shipped a product face, and the register carries it "
    "to R2355 at the measured target.",
    "R2354 tokens: local=~19k api=0 api_reason=product window that discharged "
    "a stale register row - one live verification that the R2352 drift was "
    "already repaired (triage reading plus its suite), one register close and "
    "one successor row opened through their own writers, one product module "
    "with its six pre-registered criteria and its suite (red once on this "
    "window own CLI fixture, the module never changed), one dogfooded evidence "
    "capture with three adjacent suites, one live offer reading, one runner "
    "wiring line, one queue close and one real gap row seeded, and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero external "
    "API touches; the battery carries to R2355",
    "R2354 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-twelfth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2354 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read NO new tokens "
    "(new=[] over 65 live tokens), and the evolution ledger carries no "
    "@BigDomain row, so nothing was executed, rejected or acknowledged this "
    "window and the baseline is unchanged.",
    "R2354 honest disclosures: (a) the register row this window closed was "
    "discharged by R2353 and left open, so the gate spent one pass pointing a "
    "fresh window at finished work - the R2345 shape again - and it is named "
    "as the round first finding rather than quietly re-running the repair. "
    "(b) The first suite run was RED on AC-QHO5 and the red was this window "
    "own CLI fixture: it built an 'offered' world whose second row was ALSO "
    "delivered (it wrote both suites), so the CLI correctly read ALL-DELIVERED "
    "and returned 2 where the test expected 0; the fixture was corrected and "
    "no criterion was widened, the module never changed across the fix. (c) "
    "The module keeps the whole occupancy reading in one call rather than "
    "producing its own per-row signals, which is a deliberate narrowing: the "
    "suite proves there is no second module-path scan in the source, and that "
    "narrowing means the offer cannot answer 'CLAIMABLE' for a row the "
    "occupancy reader never judged - rows with no module named are simply "
    "offered, as they are today. (d) The seeded gap row "
    "(queue_floor_delivered_wire) is a real measured inconsistency (the gauge "
    "counts a DELIVERED row as claimable supply, so FLOOR-MET can stand over "
    "rows that already shipped) and it is NOT repaired in this window. (e) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries "
    "no row for this tech slice, disclosed rather than silently skipped.",
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
    print("STATE tick=%d log_items=%d bytes=%d"
          % (state["tick"], len(state["log"]), len(data)))
    if not execute:
        return data
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2354_")
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


def fold(execute, data):
    """Fold the oldest log window ending on a round boundary (a tokens line).

    The size the gate is judged on is the size the closeout is ABOUT to leave
    on disk, so a dry run and an executed run pick the same window.
    """
    if data is None:
        raise SystemExit("E_R2354_STATE_WRITE")
    raw = data
    state = json.loads(raw.decode("utf-8"))
    print("FOLD gate at predicted %dB margin=%dB"
          % (len(raw), 78500 - len(raw)))
    chosen = None
    for end in range(3, 30):
        if " tokens: local=" not in state["log"][end - 1]:
            continue
        window = state["log"][0:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2354: log lines 1..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window ends "
                   "on a tokens ledger line (round boundary); window "
                   "tokens: %s" % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 1, end, summary,
                                   reserve=RESERVE)
        print("FOLD candidate end=%d predicted=%dB gate_ok=%r missing=%d"
              % (end, plan["predicted_bytes"], plan["gate_ok"],
                 len(plan["tokens_missing"])))
        if plan["gate_ok"] and not plan["tokens_missing"]:
            chosen = (end, summary)
            break
    if not chosen:
        raise SystemExit("E_R2354_NO_WINDOW")
    if not execute:
        print("DRY RUN: fold wrote nothing")
        return 0
    result = SF.fold(ROOT, "R2354", FOLD_NO, 1, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=1..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))
    return 0


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
        "src/os/queue_head_delivered.py", "on",
        "R2354 product: the queue offer finally asks the occupancy reading - a "
        "row whose module and suite already shipped is walked over and NAMED "
        "with its module, the offer continues to the next claimable row, and a "
        "queue of shipped rows reads ALL-DELIVERED instead of NO-HEAD",
    ])
    data["results"].append([
        "R2354",
        "product window that discharged a stale register row: verified the "
        "R2352 residue drift was already repaired (TRIAGED 206/206, suite "
        "green), closed that row and opened reconcile-battery-R2355 at 485 "
        "suites / 3886 criteria, then shipped queue_head_delivered with "
        "AC-QHO1..AC-QHO6 (6/6 twice plus three adjacent suites) and read it "
        "live - the row this window claimed now reads DELIVERED and is walked "
        "over; one real gap row seeded (queue_floor_delivered_wire); no battery "
        "ran",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2354_TICK_ROW count=%d" % len(tick_rows))
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
    code = fold(execute, code)
    if code:
        return code
    code = write_export(read_json(STATE), execute)
    if code:
        return code
    return write_heartbeat(read_json(STATE), execute)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))