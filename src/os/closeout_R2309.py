"""closeout_R2309.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  append    - tick 2309 and the four R2309 log items, in the canonical layout
  export    - refresh docs/status-export.json from state/export_face_R2309.json
  heartbeat - append the tick 2309 row

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
FACE = os.path.join(ROOT, "state", "export_face_R2309.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = "R2309"
TICK = 2309

NARRATIVE = (
    "2026-11-01 R2309 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with zero "
    "unreplied numbered handoffs; the group orders tail is unchanged at the "
    "2026-10-31 18:23 baseline; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, the floors read FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10 with the tech head at line 372 prefix AC-RTR1, "
    "and the debt gate named exactly one first=yes row (product-face-R2309), "
    "so this window ran the VERIFICATION that row and the carried board row "
    "both demanded with ZERO product edits until green (the R2168 mixed-tree "
    "rule). R2307 and R2308 both shipped product code and neither ran a "
    "battery, so two new suites were unwitnessed by the whole registry. "
    "RESULT: full reconcile battery on the committed R2308 tree b3112739 with "
    "an empty git status before the run = RUNNER PASS 461/461 suites green "
    "plus controls 7/7 in 779.9s with birth-site TMP RECLAIM 932/932 worlds "
    "326.57 MiB busy zero failed zero (qa/reconcile-all-R2309.log, 787786B, "
    "single writer utf-8 LF through src/os/battery_stream.py, never a shell "
    "redirection), criteria total 3742 - exactly +2 suites / +12 criteria "
    "against R2306 (459/3730) from the R2307 os-stamp-exempt-append and the "
    "R2308 os-evidence-output-audit suites, so the delta resolves to two named "
    "suites and no prediction error is swept. Four follow-up sections then ran "
    "through src/os/battery_followup.py: the matrix section FAILED first on "
    "the stale doc (on-disk=44151B regenerated=44329B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 461 suites / 3742 criteria (44329B) and "
    "the re-run read all four sections PASS (matrix byte-identical 44329B, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing on VERDICT R2309 PASS. The R2308 product "
    "face was then read live exactly as the carried row demanded: "
    "evidence_output_audit over the real pile resolves every declared literal "
    "and reports its STALE row, and queue_head --head tech re-reads line 372 "
    "(prefix AC-RTR1, skipped_before=4, claimable=10) rather than trusting the "
    "carried line. Honest score: a 0-point verification window with no product "
    "face, declared as such."
)

TOKENS = (
    "R2309 tokens: local=~9k api=0 api_reason=verification-only window - one "
    "full reconcile battery on the committed tree with its streamed evidence "
    "file, one four-section follow-up through the shipped callable plus one "
    "matrix regeneration from that evidence and one re-run that read all four "
    "PASS, one live reading of the R2308 product face over the real pile, one "
    "queue_head re-read of the tech head, two register writes through the "
    "shipped close and append writers, and the queue/board/state/export "
    "closeout; zero cloud calls and zero external API touches; the product "
    "face resumes at R2310"
)

SELF_HEAL = (
    "R2309 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(seventy-third consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2309 honest disclosures: (a) the battery was launched as a detached "
    "hidden process with its streamed stdout redirected to a temp file, "
    "because battery_stream buffers its evidence in memory and writes once at "
    "completion, so any probe before the end legitimately finds no evidence "
    "file - that is buffering and not a dead runner, confirmed by four "
    "progress probes growing 170399B to 787786B and then by the RUNNER line. "
    "(b) Both follow-up legs are retained in the evidence file (1889B FAIL "
    "then 1950B PASS); the FAIL leg is the designed first use of the matrix "
    "section, which refuses to rewrite the stale doc. (c) The prediction "
    "carried in the board row said +1 suite / +6 criteria against R2306, and "
    "the measurement is +2 suites / +12 criteria; that is not a prediction "
    "error swept aside but two product windows (R2307 and R2308) landing after "
    "the last battery, and both suites are named above. (d) The launch probe "
    "printed a line from inside the runner ('no evidence path: shell-capture "
    "mode') before any suite ran; it is the runner's own notice about the "
    "child suites' evidence dialect and not a failure, and the run then "
    "proceeded for 779.9s. (e) This round shipped no product code, so the "
    "register successor names the product face (residue_triage, tech head "
    "line 372 prefix AC-RTR1) rather than a second verification. (f) tasks.md "
    "was left untouched: it is the P-47 canonical board and carries no row for "
    "this tech slice, disclosed rather than silently skipped. (g) The one "
    "STALE finding read live (evidence_R2213.py, NO-DECLARATION) is the same "
    "reading R2308 shipped with; this window confirms it and does not repair "
    "it, and the repair is not part of this round's claim."
)

ITEMS = [NARRATIVE, TOKENS, SELF_HEAL, DISCLOSURES]

HEARTBEAT_2309 = (
    "tick 2309 2026-11-01 verification window: full reconcile battery on the "
    "committed R2308 tree b3112739 with an empty git status = RUNNER PASS "
    "461/461 suites plus controls 7/7 in 779.9s, birth-site TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2309.log, "
    "787786B, single writer utf-8 LF through battery_stream), criteria total "
    "3742 = +2 suites / +12 criteria against R2306, resolving exactly to the "
    "R2307 os-stamp-exempt-append and R2308 os-evidence-output-audit suites. "
    "Four follow-up sections: matrix FAILed first on the stale doc and did not "
    "rewrite it, suite_matrix regenerated 461 suites / 3742 criteria "
    "(44329B), re-run read all four PASS, VERDICT R2309 PASS. Zero product "
    "code changed; 0 product points, honestly recorded."
)


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2309"
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
    have = [item for item in log if item.startswith("2026-11-01 R2309 ")]
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
    text += HEARTBEAT_2309 + "\n"
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
        sys.stdout.write("usage: closeout_R2309.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))