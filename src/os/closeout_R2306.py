"""closeout_R2306.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  append    - tick 2306 and the four R2306 log items, in the canonical layout
  export    - refresh docs/status-export.json from state/export_face_R2306.json
  heartbeat - append the tick 2306 row

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
FACE = os.path.join(ROOT, "state", "export_face_R2306.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = "R2306"
TICK = 2306

NARRATIVE = (
    "2026-11-01 R2306 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with zero "
    "unreplied numbered handoffs; the group orders tail is unchanged at the "
    "2026-10-31 18:23 baseline; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, the floors read FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10 with tech head line 369 prefix AC-SAP1, and the "
    "debt gate named exactly one first=yes row (reconcile-battery-R2306), so "
    "this window ran the VERIFICATION that row demanded with ZERO product "
    "edits until green (the R2168 mixed-tree rule). RESULT: full reconcile "
    "battery on the committed R2305 tree d813bfc8 with an empty git status "
    "before the run = RUNNER PASS 459/459 suites green plus controls 7/7 in "
    "838.2s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy zero "
    "failed zero (qa/reconcile-all-R2306.log, 781983B at RUNNER close growing "
    "to 785822B after both follow-up legs, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total "
    "3730 - exactly the pre-registered +1 suite / +6 criteria against R2304 "
    "(458/3724) from the R2305 os-review-window suite, so the prediction "
    "matched the measurement with no correction. Four follow-up sections then "
    "ran through src/os/battery_followup.py: the matrix section FAILED first "
    "on the stale doc (on-disk=44075B regenerated=44151B) and did NOT rewrite "
    "it, which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 459 suites / 3730 criteria (44151B) and "
    "the re-run read all four sections PASS (matrix byte-identical 44151B, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing on VERDICT R2306 PASS at exit 0. Register "
    "closed through its own writer (open 2 to 1, done 54 to 55, 46496B to "
    "46499B, read back ok) and product-face-R2307 opened first=yes naming the "
    "product face at the tech head. Honest score: a 0-point verification "
    "window with no product face."
)

TOKENS = (
    "R2306 tokens: local=~10k api=0 api_reason=verification-only window - one "
    "full reconcile battery on the committed tree with its streamed evidence "
    "file, one four-section follow-up through the shipped callable plus one "
    "matrix regeneration from that evidence and one re-run that read all four "
    "PASS, two register writes through the shipped close and append writers, "
    "and the queue/board/state/export closeout; zero cloud calls and zero "
    "external API touches; the product face resumes at the tech head R2307"
)

SELF_HEAL = (
    "R2306 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply, "
    "and this session runs unelevated, so the definition of the loop hosting "
    "this window was left untouched. Open local-lane item for an elevated "
    "window (seventieth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2306 honest disclosures: (a) the battery was launched as a background "
    "task and battery_stream buffers its evidence in memory, so the two "
    "probes before completion legitimately found no file - that was buffering "
    "and not a dead runner, confirmed by the live battery_stream and "
    "reconcile_all child processes and then by the 781983B file at RUNNER "
    "close. (b) Both follow-up legs are retained in the evidence file (1889B "
    "FAIL then 1950B PASS); the FAIL leg is the designed first use of the "
    "matrix section, which refuses to rewrite the stale doc. (c) This round "
    "shipped no product code, so the register successor names the product "
    "face (stamp_exempt_append, tech head line 369 prefix AC-SAP1) rather "
    "than a second verification. (d) The tech queue was not touched: "
    "claimable stayed 10 against its floor, so no gap row was due, and the "
    "board and register are the only bookkeeping files this window edited. "
    "(e) tasks.md was left untouched: it is the P-47 canonical board and "
    "carries no row for this tech slice, disclosed rather than silently "
    "skipped."
)

ITEMS = [NARRATIVE, TOKENS, SELF_HEAL, DISCLOSURES]

HEARTBEAT_2306 = (
    "tick 2306 2026-11-01 verification window: the R2305 review-window suite "
    "is now witnessed by the whole registry. Full reconcile battery on the "
    "committed tree d813bfc8 with an empty git status before the run = RUNNER "
    "PASS 459/459 suites plus controls 7/7 in 838.2s, birth-site TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0 failed=0, criteria total 3730 - exactly "
    "the pre-registered +1 suite / +6 criteria against R2304. Four follow-up "
    "sections PASS after the matrix section refused to rewrite the stale doc "
    "and suite_matrix regenerated it to 459/3730 at 44151B. Zero product "
    "edits, so 0 product points, honestly recorded."
)


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2306"
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
    have = [item for item in log if item.startswith("2026-11-01 R2306 ")]
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
    text += HEARTBEAT_2306 + "\n"
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
        sys.stdout.write("usage: closeout_R2306.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))