"""closeout_R2315.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  append    - tick 2315 and the R2315 log items, in the canonical layout
  boards    - append this window's done row plus the R2316 carried row
  export    - refresh docs/status-export.json from the R2315 face
  heartbeat - append the tick 2315 row

The debt register is closed and reopened through its own writers
(debt_close.py / debt_append.py), never by editing that file here.

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
FACE = os.path.join(ROOT, "state", "export_face_R2315.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

ROUND = "R2315"
TICK = 2315

NARRATIVE = (
    "2026-11-01 R2315 window (five-silence scan clean at open: empty git "
    "status --short, no index.lock; decisions.md token diff empty against the "
    "stored union, so no new decision row is owed; group ledger carries the "
    "same three @BigDomain patrol rows already paid off with zero unreplied "
    "numbered handoffs; group orders tail unchanged at 2026-10-31 18:23; "
    "benchmarks refreshed 2026-10-29 inside the seven-day gate). The debt "
    "gate named exactly one first=yes row (product-face-R2315), so this "
    "window ran the VERIFICATION first with ZERO product edits until green "
    "(the R2168 mixed-tree rule): full reconcile battery on the committed "
    "R2314 tree 99a47702 = RUNNER PASS 464/464 suites green plus controls 7/7 "
    "in 834.4s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy "
    "zero failed zero (qa/reconcile-all-R2315.log, 784297B, single writer "
    "utf-8 LF through src/os/battery_stream.py), criteria total 3760 - exactly "
    "the pre-registered +1 suite / +6 criteria against R2313 (463/3754) from "
    "the R2314 os-gate-decl-identity suite, so prediction matched measurement "
    "with no correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (44486B vs 44573B) and did NOT rewrite it; src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md to 464 suites / 3760 criteria "
    "(44573B) and the re-run read all four PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), VERDICT R2315 PASS. The product face the register "
    "then pointed at was shipped: src/os/gate_decl_identity_wire.py makes the "
    "gate declaration writer ask gate_decl_identity before it plans, so "
    "UNMATCHED and AMBIGUOUS refuse before any byte with the reader state and "
    "its carrier lines, MATCHED stays a duplicate refusal, and only a MATCHED "
    "identity reaches gate_decl_append.plan. Suite 6/6 twice "
    "(sha16 669cc7f355d76d38) plus four adjacent gate suites green; live "
    "reading: the exact R2314 finding, --identity '-', now refuses "
    "E_GDIW_AMBIGUOUS at exit 2 naming 281 shared carriers and the declaration "
    "stays byte-identical. Product points: one face with its own suite."
)

DISCLOSURES = (
    "R2315 honest disclosures: (a) three first-run suite failures were all "
    "this-window TEST defects, never a criterion widened: AC-GDIW1 failed on "
    "its own docstring (the probe searched for the literal 'state/queue' that "
    "the header comment carries) so it now proves the property it promised - "
    "no queue_head import and no queue file opened - while the patched-reader "
    "legs stay the real evidence; AC-GDIW2 hard-coded carrier lines L4/L5 "
    "while the fixture measures L8/L9. (b) One five-minute polling command was "
    "cancelled by the no-output rule while the battery ran in its own "
    "background task; only the poller died and the battery was untouched "
    "(784297B evidence and the RUNNER PASS line are the proof). (c) The "
    "product face ships AFTER the battery by design - the battery measured the "
    "committed R2314 tree, and R2315's own changes are the successor "
    "verification's subject. (d) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice, disclosed rather "
    "than silently skipped. (e) The tech queue row this face answers "
    "(gate_decl_identity_wire, line 382) is left open for the next window to "
    "stamp through the shipped queue law rather than hand-edited here."
)

TOKENS = (
    "R2315 tokens: local=~20k api=0 api_reason=verification plus one product "
    "face in one window - a full reconcile battery and its four follow-up "
    "sections, one new reader-wire module with six pre-registered criteria and "
    "its suite (two green runs plus four adjacent suites), one live refusal "
    "reading against the real queue, one debt close and one successor open "
    "through their own writers, and the board/state/export/heartbeat closeout; "
    "zero cloud calls and zero external API touches; the successor battery "
    "carries to R2316."
)

SELF_HEAL = (
    "R2315 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the loop definition was left untouched. Open "
    "local-lane item for an elevated window (seventy-seventh consecutive "
    "disclosure, carried as the stale row loop-s4u-reconcile in state/debt.md)."
)

BOARD_DONE = (
    "- [x] [done 2026-11-01 R2315] R2315 first item: THE BATTERY ON THE "
    "COMMITTED R2314 TREE, zero product edits until green - RUNNER PASS 464/464 "
    "suites plus controls 7/7 in 834.4s, criteria 3760 exactly the "
    "pre-registered +1/+6, TMP RECLAIM 932/932 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2315.log 784297B, single writer utf-8 LF). Four "
    "follow-up sections ran after the matrix doc was regenerated to 464 "
    "suites/3760 criteria (44573B) and read all PASS. Then the product face: "
    "src/os/gate_decl_identity_wire.py refuses UNMATCHED/AMBIGUOUS identities "
    "before any byte and hands only a MATCHED one to the writer - suite 6/6 "
    "twice (sha16 669cc7f355d76d38) plus four adjacent gate suites green, live "
    "--identity '-' now refused E_GDIW_AMBIGUOUS over 281 carriers."
)

BOARD_CARRY = (
    "- [ ] [carried 2026-11-01 R2315] R2316 first item: THE BATTERY ON THE "
    "COMMITTED R2315 TREE, zero product edits until green (the R2168 "
    "mixed-tree rule). R2315 changed src/os (gate_decl_identity_wire.py, "
    "test_gate_decl_identity_wire.py) and one runner entry, so the registry "
    "reads 464 suites / 3760 criteria at R2315 and the pre-registered "
    "expectation is +1 suite / +6 criteria (465 suites / 3766 criteria); if a "
    "delta does not resolve to a named suite, disclose the prediction error "
    "instead of sweeping it. Then the four follow-up sections through "
    "src/os/battery_followup.py (its matrix section FAILs first on the stale "
    "doc and must not rewrite it). After that the product face resumes at the "
    "tech head the reader names. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop reads LogonType=InteractiveToken (seventy-seventh "
    "consecutive disclosure; carried as loop-s4u-reconcile in state/debt.md)."
)

HEARTBEAT_2315 = (
    "tick 2315 2026-11-01 R2315 battery 464/464 green criteria 3760 controls "
    "7/7 plus gate_decl_identity_wire face suite 6/6 twice"
)


def load(path):
    with open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".r2315-tmp"
    with open(temp, "wb") as handle:
        handle.write(blob)
    os.replace(temp, path)
    return len(blob)


def step_append(argv):
    raw = load(STATE)
    state = json.loads(raw.decode("utf-8"))
    if state["tick"] != TICK - 1:
        print("E_TICK expected %d found %s" % (TICK - 1, state["tick"]))
        return 3
    log = state["log"]
    if [item for item in log if item.startswith("2026-11-01 R2315 ")]:
        print("ALREADY appended")
        return 0
    state["tick"] = TICK
    log.extend([NARRATIVE, DISCLOSURES, TOKENS, SELF_HEAL])
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


def step_boards(argv):
    text = load(BACKLOG).decode("utf-8")
    if BOARD_DONE[:40] in text:
        print("ALREADY on the board")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    post = text + BOARD_DONE + "\n\n" + BOARD_CARRY + "\n"
    if "--execute" not in argv:
        print("DRY RUN boards append %dB -> %dB"
              % (len(text.encode("utf-8")), len(post.encode("utf-8"))))
        return 0
    size = write_atomic(BACKLOG, post.encode("utf-8"))
    print("BOARDS appended %dB" % size)
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
    text += HEARTBEAT_2315 + "\n"
    if "--execute" not in argv:
        print("DRY RUN heartbeat +1 row")
        return 0
    size = write_atomic(HEARTBEAT, text.encode("utf-8"))
    print("HEARTBEAT +1 row %dB" % size)
    return 0


STEPS = {"append": step_append, "boards": step_boards, "export": step_export,
         "heartbeat": step_heartbeat}


def main(argv):
    if len(argv) < 2 or argv[1] not in STEPS:
        sys.stdout.write("usage: closeout_R2315.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))