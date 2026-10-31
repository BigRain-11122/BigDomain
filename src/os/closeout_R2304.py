"""closeout_R2304.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  fold     - fold one whole round block so the closeout fits the waterline
  append   - tick 2304 and the four R2304 log items, in the canonical layout
  export   - refresh docs/status-export.json from state/export_face_R2304.json
  heartbeat- append the tick 2304 row

ASCII source only; the Chinese CEO face lives in the JSON data file.
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import state_fold as SF
import state_io as SIO

ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2304.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = "R2304"
TICK = 2304
FOLD_LABEL = "R2304"

NARRATIVE = (
    "2026-11-01 R2304 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline so no new decision "
    "row is presented; the group ledger carries the same @BigDomain patrol "
    "rows already paid off with zero unreplied numbered handoffs; the group "
    "orders tail is unchanged at the 2026-10-31 18:23 baseline; benchmarks "
    "refreshed 2026-10-29 inside the seven-day gate) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the debt "
    "gate named exactly one first=yes row (product-face-R2304), so this "
    "window ran the VERIFICATION that row demanded with ZERO product edits "
    "until green (the R2168 mixed-tree rule). R2302 and R2303 both shipped "
    "product code and neither ran a battery, so two new suites were "
    "unwitnessed by the whole registry. RESULT: full reconcile battery on the "
    "committed R2303 tree d43e1eb6 with an empty git status before the run = "
    "RUNNER PASS 458/458 suites green plus controls 7/7 in 816.6s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy zero failed zero "
    "(qa/reconcile-all-R2304.log, 781477B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total "
    "3724 - exactly the pre-registered +2 suites / +12 criteria against R2301 "
    "(456/3712) from the R2302 os-evidence-variants and the R2303 "
    "os-followup-retry-legs suites, so the prediction matched the measurement "
    "with no correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=43904B regenerated=44075B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 458 suites / 3724 criteria (44075B) and "
    "the re-run read all four sections PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing on VERDICT R2304 PASS at exit 0. The new "
    "reader from R2303 was then read on the live pile exactly as the carried "
    "row demanded: `followup_retry_legs.py --legs` reads rounds=428 "
    "canonical_only=424 retried=4 red=412, and both recovered rounds resolve "
    "through their LAST leg - R2277 PASS legs=2 and R2289 PASS legs=2, each "
    "keeping its canonical leg as INCOMPLETE runner=FAIL with its own "
    "evidence path, which is the exact reading the product face was built to "
    "produce. Honest score: a 0-point verification window with no product "
    "face."
)

TOKENS = (
    "R2304 tokens: local=~9k api=0 api_reason=verification-only window - one "
    "full reconcile battery on the committed tree with its streamed evidence "
    "file, one four-section follow-up through the shipped callable plus one "
    "matrix regeneration from that evidence, one live reading of the retry "
    "reader over the whole pile, two register writes through the shipped "
    "close and append writers, and the queue/board/state/export closeout; "
    "zero cloud calls and zero external API touches; the product face resumes "
    "at the tech head R2305"
)

SELF_HEAL = (
    "R2304 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply, "
    "and this session runs unelevated, so the definition of the loop hosting "
    "this window was left untouched. Open local-lane item for an elevated "
    "window (sixty-eighth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2304 honest disclosures: (a) the battery ran as a detached hidden "
    "process because battery_stream buffers its evidence in memory and writes "
    "once at completion, so every probe before the end legitimately found no "
    "file - that was buffering and not a dead runner, confirmed at the end by "
    "the 781477B file. (b) Both follow-up legs are retained in the evidence "
    "file (1889B FAIL then 1950B PASS); the FAIL leg is the designed first use "
    "of the matrix section, which refuses to rewrite the stale doc. (c) The "
    "live pile reading is red=412 and that is disclosed rather than dressed "
    "up: it is the truth of the pile (the same family read 413 INCOMPLETE at "
    "R2288), and this window's four retried rounds are the only ones that can "
    "resolve through a later leg. (d) This round shipped no product code, so "
    "the register successor names the product face (review_window_decl, tech "
    "head line 368 prefix AC-RWD1) rather than a second verification. (e) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries "
    "no row for this tech slice, disclosed rather than silently skipped."
)

ITEMS = [NARRATIVE, TOKENS, SELF_HEAL, DISCLOSURES]

HEARTBEAT_2304 = (
    "tick 2304 2026-11-01 verification window: the two product suites shipped "
    "at R2302 and R2303 are now witnessed by the whole registry. Full "
    "reconcile battery on the committed tree d43e1eb6 with an empty git status "
    "before the run = RUNNER PASS 458/458 suites plus controls 7/7 in 816.6s, "
    "birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0, "
    "criteria total 3724 - exactly the pre-registered +2 suites / +12 criteria "
    "against R2301. Four follow-up sections PASS after the matrix section "
    "refused to rewrite the stale doc and suite_matrix regenerated it to 458/"
    "3724 at 44075B. The R2303 retry reader was read live: rounds=428 "
    "canonical_only=424 retried=4 red=412, with R2277 and R2289 both PASS "
    "through 2 legs and their canonical legs kept as INCOMPLETE runner=FAIL. "
    "Zero product edits, so 0 product points, honestly recorded."
)


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2304"
    with io.open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    return len(blob)


def last_fold_number():
    best = 0
    for name in os.listdir(os.path.join(ROOT, "logs")):
        if not (name.startswith("state-log-archive-") and
                name.endswith(".md")):
            continue
        text = load(os.path.join(ROOT, "logs", name)).decode("utf-8", "replace")
        for found in re.findall(r"fold (\d+) window", text):
            best = max(best, int(found))
    if not best:
        raise SystemExit("E_CLOSE_NO_FOLD_NUMBER")
    return best


def block_window(state, blocks=2):
    """The first `blocks` whole round blocks after the fold marker."""
    log = state["log"]
    start = None
    for index, item in enumerate(log):
        if re.match(r"^\d{4}-\d{2}-\d{2} R\d+ ", item):
            start = index
            break
    if start is None:
        raise SystemExit("E_CLOSE_NO_BLOCK")
    seen = 0
    end = len(log)
    for index in range(start, len(log)):
        if re.match(r"^\d{4}-\d{2}-\d{2} R\d+ ", log[index]):
            seen += 1
            if seen > blocks:
                end = index
                break
    label = log[start].split()[1]
    return start + 1, end, label


def step_fold(argv):
    raw, state = SF.read_state(STATE)
    window_start, window_end, label = block_window(state)
    window = state["log"][window_start - 1:window_end]
    tokens = sorted(set(SF.PAT.findall(" ".join(window))))
    number = last_fold_number() + 1
    summary = ("Fold %s: log lines %d..%d (%s, whole round block) folded "
               "verbatim into the archive; window tokens: %s"
               % (FOLD_LABEL, window_start, window_end, label,
                  " ".join(tokens)))
    plan = SF.fold(ROOT, FOLD_LABEL, number, window_start, window_end,
                   summary, reserve=7000, execute=False)
    print("FOLD PLAN no=%d window=%d..%d lines=%s tokens=%d missing=%s "
          "predicted=%d margin=%d gate_ok=%s"
          % (number, window_start, window_end, plan["window_lines"],
             plan["tokens_total"], plan["tokens_missing"],
             plan["predicted_bytes"], plan["margin"], plan["gate_ok"]))
    if not plan["gate_ok"]:
        print("FOLD REFUSED: reserve does not fit")
        return 2
    if "--execute" not in argv:
        print("DRY RUN fold")
        return 0
    result = SF.fold(ROOT, FOLD_LABEL, number, window_start, window_end,
                     summary, reserve=7000, execute=True)
    print("FOLD DONE no=%d bytes=%d margin=%d"
          % (result["fold"]["number"] if "fold" in result else number,
             os.path.getsize(STATE),
             SF.measure(os.path.getsize(STATE))["margin"]))
    return 0


def step_append(argv):
    raw = load(STATE)
    state = json.loads(raw.decode("utf-8"))
    if state["tick"] != TICK - 1:
        print("E_TICK expected %d found %s" % (TICK - 1, state["tick"]))
        return 3
    log = state["log"]
    have = [item for item in log if item.startswith("2026-11-01 R2304 ")]
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
    text += HEARTBEAT_2304 + "\n"
    if "--execute" not in argv:
        print("DRY RUN heartbeat +1 row")
        return 0
    size = write_atomic(HEARTBEAT, text.encode("utf-8"))
    print("HEARTBEAT +1 row %dB" % size)
    return 0


STEPS = {"fold": step_fold, "append": step_append, "export": step_export,
         "heartbeat": step_heartbeat}


def main(argv):
    if len(argv) < 2 or argv[1] not in STEPS:
        sys.stdout.write("usage: closeout_R2304.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))