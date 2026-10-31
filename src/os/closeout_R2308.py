"""closeout_R2308.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  append    - tick 2308 and the four R2308 log items, in the canonical layout
  export    - refresh docs/status-export.json from state/export_face_R2308.json
  heartbeat - append the tick 2308 row

ASCII source only; the Chinese CEO face lives in the JSON data file.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import state_io as SIO

ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2308.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = "R2308"
TICK = 2308

NARRATIVE = (
    "2026-11-01 R2308 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with zero "
    "unreplied numbered handoffs; the group orders tail is unchanged at the "
    "2026-10-31 18:23 baseline; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, the floors read FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10, and the debt gate named exactly one first=yes "
    "row (product-face-R2308), so this window claimed the TOP deliverable "
    "tech row: the R2296 evidence_output_audit seed at state/queue/tech.md:370 "
    "(prefix AC-EOA1), whose AC-EOA1..AC-EOA6 criteria were already pinned "
    "INSIDE that row BEFORE the code (fresh zero-occupancy anchor check at "
    "HEAD 2026-11-01: evidence_output_audit, AC-EOA, E_EOA, "
    "os-evidence-output-audit and test_evidence_output_audit hit only prose "
    "and state files, with no code path). PRODUCT: src/os/"
    "evidence_output_audit.py plus src/os/test_evidence_output_audit.py - a "
    "declaration that stopped being true becomes a finding instead of a green "
    "row. The output map names what each legacy copy DECLARES, so a script "
    "can declare qa/<name>.log that was never written and the map still "
    "counts it as owned while the parity reader judges it stale; the audit "
    "joins the two and resolves every literal to EXISTS or ABSENT, every "
    "template to FAMILY-HIT with its match count or FAMILY-NONE with zero, "
    "and a script whose declarations resolve to nothing to STALE with its own "
    "reason (NO-DECLARATION or ALL-UNRESOLVED). The declaration law is "
    "imported (the module calls eom.build and eom.is_literal and carries no "
    "second scanner), and the suite proves that seam by patching "
    "eom.declarations and watching an injected declaration flow straight "
    "through as ABSENT at its own line. SUITE PASS 6/6 double-run identical "
    "with five adjacent suites green through the R2261 evidence_capture "
    "callable (qa/evidence-output-audit-R2308.log, 1216B, one utf-8 LF single "
    "writer), wired os-evidence-output-audit(6). LIVE over the real pile (92 "
    "scripts, 164 declarations) exists=132 absent=0 family_hit=26 "
    "family_none=6 stale=1 verdict=FINDINGS exit 2: the one STALE is "
    "evidence_R2213.py reading NO-DECLARATION, the same script the map read "
    "NONE at R2296, so the two readers agree instead of pointing opposite "
    "ways; the six FAMILY-NONE legs are R2029/R2030/R2035/R2036/R2043/R2044, "
    "rounds whose reconcile leg was never written under the name their own "
    "script declares. The claim dropped tech claimable to 9, so one real gap "
    "row was seeded (retire_candidate, AC-RET1..AC-RET6 pre-registered, five "
    "anchors zero-occupancy) and the gauge closed FLOOR-MET 5/5 10/10 10/10. "
    "Honest score: 2 points (a runnable reader plus a reusable suite)."
)

TOKENS = (
    "R2308 tokens: local=~19k api=0 api_reason=product window on the debt "
    "register first item - one audit module with its six pre-registered "
    "criteria and its suite, one this-window test expectation corrected "
    "against the measured truth, one dogfooded evidence capture (two legs "
    "identical, five adjacent suites green), one LIVE reading of the whole "
    "92-script pile, one runner wiring line, one real gap row seeded to hold "
    "the tech floor, one close and one seed row through the shipped walkers, "
    "one register close and one register append, and the queue/board/state/"
    "export closeout; zero cloud calls and zero external API touches; the "
    "battery carries to R2309"
)

SELF_HEAL = (
    "R2308 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply, "
    "and this session runs unelevated, so the definition of the loop hosting "
    "this window was left untouched. Open local-lane item for an elevated "
    "window (seventy-second consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2308 honest disclosures: (a) the first suite run was red 2/6 and only "
    "one red was a this-window expectation defect - the AC-EOA4 fixture "
    "expected three stale scripts while the world honestly held four, because "
    "R9006 declares a literal that is itself absent and is therefore stale "
    "too; corrected in the test, no criterion relaxed. (b) The other red was "
    "the honest wiring red: AC-EOA6 read red because the runner label was not "
    "yet in place, and the wiring landed before the green run. (c) Two "
    "commands in this window were one-off round scripts from earlier rounds "
    "that execute on invocation rather than printing help: queue_close_R2248 "
    "refreshed the export face to the CURRENT live self-drive numbers and "
    "append_log_R2250 appended a stale R2250 item to state.json - the latter "
    "was reverted byte-exactly with git checkout before any commit and is "
    "disclosed rather than swept, and this window's own log rows are written "
    "by closeout_R2308 itself. (d) the audit reads a template only inside the "
    "folder its declaration names, and a template that names no folder is "
    "matched against the evidence folder; both forms are what the live pile "
    "actually contains and the six FAMILY-NONE readings are the truth of the "
    "pile rather than a defect of the reader. (e) tasks.md was left untouched: "
    "it is the P-47 canonical board and carries no row for this tech slice, "
    "disclosed rather than silently skipped. (f) queue_row --check and "
    "queue_done_stamp --check both read GATE-DEBT and DONE-STAMP-DEBT over "
    "the legacy rows (289 unstamped done rows predate the stamp law); this "
    "window's own closed row carries [done 2026-11-01 R2308] and lands on the "
    "ok side, so the debt is inherited and named, not added. (g) The queue "
    "closeout one-off and this bookkeeping script were both first written "
    "under the name closeout_R2308.py; the queue one ran and proved its own "
    "readback before being overwritten, so the closed row is on disk while "
    "that source is not kept - disclosed rather than dressed up as two "
    "artifacts."
)

ITEMS = [NARRATIVE, TOKENS, SELF_HEAL, DISCLOSURES]

HEARTBEAT_2308 = (
    "tick 2308 2026-11-01 product window: evidence_output_audit shipped "
    "(src/os/evidence_output_audit.py plus its suite, AC-EOA1..AC-EOA6 pinned "
    "in the queue row before the code). Every declared literal resolves to "
    "EXISTS or ABSENT, every template to a family count, and a script with "
    "nothing resolvable reads STALE. SUITE PASS 6/6 double-run identical, "
    "five adjacent suites green, evidence qa/evidence-output-audit-R2308.log. "
    "LIVE over 92 scripts / 164 declarations: exists=132 absent=0 family_hit=26 "
    "family_none=6 stale=1 (evidence_R2213.py NO-DECLARATION, agreeing with "
    "the map NONE reading). Wired os-evidence-output-audit(6); retire_candidate "
    "seeded to hold the tech floor; 2 product points."
)


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2308"
    with io.open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    return len(blob)


def step_append(argv):
    raw = load(STATE)
    state = json.loads(raw.decode("utf-8"))
    if state["tick"] != TICK - 1:
        print("E_TICK expected %d found %s" % (TICK - 1, state["tick"]))
        return 3
    log = state["log"]
    have = [item for item in log if item.startswith("2026-11-01 R2308 ")]
    if have:
        print("ALREADY appended")
        return 0
    state["tick"] = TICK
    log.extend(ITEMS)
    text = json.dumps(state, ensure_ascii=False, indent=4) + "\n"
    text = SIO.canon(text)
    measured = SIO.layout(text)
    if not measured["layout_ok"]:
        print("E_LAYOUT %r" % (measured,))
        return 3
    if json.loads(text) != state:
        print("E_PAYLOAD")
        return 3
    blob = text.encode("utf-8")
    if len(blob) > 78500:
        print("E_WATERLINE predicted=%d gate=78500" % len(blob))
        return 3
    if "--execute" not in argv:
        print("DRY RUN append predicted=%d log=%d" % (len(blob), len(log)))
        return 0
    size = write_atomic(STATE, blob)
    back = json.loads(load(STATE).decode("utf-8"))
    if back["tick"] != TICK or len(back["log"]) != len(log):
        print("E_READBACK")
        return 3
    print("APPEND %dB tick=%d log=%d" % (size, back["tick"], len(back["log"])))
    return 0


def step_export(argv):
    face = json.loads(load(FACE).decode("utf-8"))
    data = json.loads(load(EXPORT).decode("utf-8"))
    import datetime
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    data["export_ts"] = now.isoformat()
    data["do"] = face["do"]
    block = data.setdefault("ceo_face", {})
    block["current"] = face["current"]
    block["latest_artifact"] = face["latest"]
    block["next_milestone"] = face["next"]
    block["next_milestone_due"] = (
        now + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()
    block["last_artifact"] = face["last"]
    data["results"] = [[ROUND, face["result"]]] + data["results"]
    data["outs"] = [[face["out"], "on", face["result"]]] + data["outs"]
    import check_export_consistency as consistency
    derived, _, _, pattern = consistency.recompute()
    data["self_drive"] = derived
    label = pattern["tick_row_label"]
    rows = [row for row in data["results"]
            if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(rows) != 1:
        print("E_TICK_ROW found %d" % len(rows))
        return 3
    rows[0][0] = str(TICK)
    blob = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8")
    if "--execute" not in argv:
        print("DRY RUN export results=%d outs=%d"
              % (len(data["results"]), len(data["outs"])))
        return 0
    size = write_atomic(EXPORT, blob)
    back = json.loads(load(EXPORT).decode("utf-8"))
    if back["export_ts"] != data["export_ts"]:
        print("E_EXPORT_READBACK")
        return 3
    print("EXPORT %dB results=%d outs=%d" % (size, len(back["results"]),
                                             len(back["outs"])))
    return 0


def step_heartbeat(argv):
    text = load(HEARTBEAT).decode("utf-8")
    have = set(line.split()[1] for line in text.splitlines()
               if line.startswith("tick ") and len(line.split()) > 1)
    if str(TICK) in have:
        print("HEARTBEAT already carries tick %d" % TICK)
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2308 + "\n"
    if "--execute" not in argv:
        print("DRY RUN heartbeat +1 row")
        return 0
    size = write_atomic(HEARTBEAT, text.encode("utf-8"))
    print("HEARTBEAT +1 row %dB" % size)
    return 0


STEPS = {"append": step_append, "export": step_export,
         "heartbeat": step_heartbeat}


def main(argv):
    if len(argv) < 2 or argv[1] not in STEPS:
        sys.stdout.write("usage: closeout_R2308.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))