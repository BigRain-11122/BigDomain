"""closeout_R2303.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  fold     - fold one whole round block so the closeout fits the waterline
  append   - tick 2303 and the four R2303 log items, in the canonical layout
  export   - refresh docs/status-export.json from state/export_face_R2303.json
  heartbeat- append the tick 2303 row

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
FACE = os.path.join(ROOT, "state", "export_face_R2303.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = "R2303"
TICK = 2303
FOLD_LABEL = "R2303"

NARRATIVE = (
    "2026-11-01 R2303 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline so no new decision "
    "row is presented; the group ledger carries the same @BigDomain patrol "
    "rows already paid off with zero unreplied numbered handoffs; the group "
    "orders tail is unchanged at the 2026-10-31 18:23 baseline; benchmarks "
    "refreshed 2026-10-29 inside the seven-day gate) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the debt "
    "gate named exactly one first=yes row (product-face-R2302), so this "
    "window claimed the TOP deliverable tech row: the R2289 "
    "followup_retry_legs seed at state/queue/tech.md:367, whose "
    "AC-FRTL1..AC-FRTL6 criteria were already pinned INSIDE that row BEFORE "
    "the code (fresh zero-occupancy anchor check at HEAD 2026-11-01: "
    "followup_retry_legs, test_followup_retry_legs, os-followup-retry-legs "
    "and E_FRTL were all zero in src, hitting only prose and state files). "
    "PRODUCT: src/os/followup_retry_legs.py plus "
    "src/os/test_followup_retry_legs.py - a round recovered by its green "
    "retry stops reading INCOMPLETE forever. followup_history reads only the "
    "canonical reconcile-all-R<nnnn>.log and reports the law-mandated -retry "
    "leg as IGNORED, so R2289 (red first battery, green retry) and R2277 "
    "both read FAIL/INCOMPLETE although the green leg is on disk with its "
    "own RUNNER line. The joiner asks retry_naming for the suffix constant, "
    "the retry predicate and the base-stem law, derives the retry order from "
    "that same naming expression, takes the round verdict from the LAST leg "
    "while every earlier leg keeps its own runner line, returns exactly the "
    "followup_history row for a canonical-only round, and refuses "
    "E_FRTL_ORPHAN_RETRY when a retry leg has no canonical leg instead of "
    "inventing a round. SUITE PASS 6/6 double-run identical with five "
    "adjacent suites green through evidence_capture "
    "(qa/followup-retry-legs-R2303.log, 1304B, one utf-8 LF single writer, "
    "never a shell redirection), wired os-followup-retry-legs(6). LIVE: R2289 "
    "reads PASS through 2 legs (canonical INCOMPLETE runner=FAIL, retry PASS "
    "runner=PASS) and the whole pile reads rounds=427 canonical_only=423 "
    "retried=4 red=412 - the four retried rounds are the R2262/R2277/R2289/"
    "R2299 red-then-green corrections. The claim dropped tech claimable to 9, "
    "so one real gap row was seeded (followup_retry_history, "
    "AC-FRH1..AC-FRH6 pre-registered, five anchors zero-occupancy in src) and "
    "the gauge closed FLOOR-MET main 5/5 tech 10/10 explore 10/10."
)

LEDGER = (
    "R2303 tokens: local=~14k api=0 api_reason=product window on the debt "
    "register first item - one joiner module with its six pre-registered "
    "criteria and its suite, one real module defect and two this-window test "
    "defects caught by that suite before any evidence, one dogfooded evidence "
    "capture (two legs identical, five adjacent suites green), one live "
    "reading of the round the seed was found from, one runner wiring line, "
    "one close and one seed row through the shipped walkers, and the "
    "queue/board/state/export closeout; zero cloud calls and zero external "
    "API touches; the battery carries to R2304"
)

SELF_HEAL = (
    "R2303 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (sixty-seventh consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2303 honest disclosures: (a) the first suite run was red 3/6, and the "
    "reds were one REAL module defect plus two this-window test defects - "
    "the discovery path passed followup_history's round LABEL as a stem, so "
    "leg_names looked for R1506.log and refused E_FRTL_NO_EVIDENCE, fixed in "
    "the MODULE by resolving the canonical stem first; the two test defects "
    "were fixtures writing 'VERDICT PASS' as two tokens while the house law "
    "is 'VERDICT <label> PASS' (three tokens), and an exit-0 expectation on a "
    "world whose only red round had been recovered by its retry - the module "
    "was right and the expectation now uses a genuinely unfixed red world. "
    "(b) The evidence capture first refused E_EVC_NO_SUITE for "
    "src/os/test_retry_naming.py; the real file is test_os_retry_naming.py, "
    "nothing was written by the refused call, and the capture then passed. "
    "(c) The R2289 canonical leg reads INCOMPLETE even though its runner line "
    "says FAIL, because that red log carries no SECTION or VERDICT line at "
    "all: the runner is reported as its own field and INCOMPLETE is the "
    "honest suite reading rather than a guessed FAIL. (d) tasks.md was left "
    "untouched - it is the P-47 canonical board and carries no row for this "
    "tech slice, disclosed rather than silently skipped."
)

ITEMS = (NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES)

HEARTBEAT_2303 = (
    "tick 2303 2026-11-01 product window: a round recovered by its green "
    "retry stops reading INCOMPLETE forever. src/os/followup_retry_legs.py "
    "resolves the canonical leg plus every retry leg through retry_naming "
    "(suffix, predicate, base-stem) and orders them by that same naming "
    "expression, takes the round verdict from the LAST leg while every "
    "earlier leg keeps its own runner line, returns exactly the "
    "followup_history row for a canonical-only round, and refuses a retry leg "
    "whose canonical leg is absent. SUITE PASS 6/6 double-run identical with "
    "five adjacent suites green (qa/followup-retry-legs-R2303.log, 1304B, "
    "single utf-8 LF writer), wired os-followup-retry-legs(6). LIVE: R2289 "
    "reads PASS through 2 legs (canonical INCOMPLETE runner=FAIL, retry PASS) "
    "and the pile reads rounds=427 canonical_only=423 retried=4 red=412. The "
    "claim dropped tech claimable to 9, so a real gap row was seeded "
    "(followup_retry_history, AC-FRH1..AC-FRH6) and the floor closed "
    "FOLD-MET 5/5 10/10 10/10."
)


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2303"
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
        text = load(os.path.join(ROOT, "logs", name)).decode(
            "utf-8", "replace")
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
             os.path.getsize(STATE), SF.measure(os.path.getsize(STATE)
                                                )["margin"]))
    return 0


def step_append(argv):
    raw = load(STATE)
    state = json.loads(raw.decode("utf-8"))
    if state["tick"] != TICK - 1:
        print("E_TICK expected %d found %s" % (TICK - 1, state["tick"]))
        return 3
    log = state["log"]
    have = [item for item in log if item.startswith("2026-11-01 R2303 ")]
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
    text += HEARTBEAT_2303 + "\n"
    if "--execute" not in argv:
        print("DRY RUN heartbeat +1 row")
        return 0
    size = write_atomic(HEARTBEAT, text.encode("utf-8"))
    print("HEARTBEAT +1 row %dB" % size)
    return 0


STEPS = {"fold": step_fold, "append": step_append, "export": step_export,
         "heartbeat": step_heartbeat}


def main(argv):
    args = list(argv)
    if not args or args[0] not in STEPS:
        print("usage: closeout_R2303.py fold|append|export|heartbeat "
              "[--execute]")
        return 5
    return STEPS[args[0]](args[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))