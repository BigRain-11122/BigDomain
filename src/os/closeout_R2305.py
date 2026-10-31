"""closeout_R2305.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  queue    - close the claimed tech row at line 368 and append one real seed
  append   - tick 2305 and the four R2305 log items, in the canonical layout
  export   - refresh docs/status-export.json from state/export_face_R2305.json
  heartbeat- append the tick 2305 row

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
FACE = os.path.join(ROOT, "state", "export_face_R2305.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")

ROUND = "R2305"
TICK = 2305
FOLD_LABEL = "R2305"

CLAIM_ANCHOR = ("- [ ] P2 tech seed (R2292, from this window own live "
                "finding): `src/os/review_window_decl.py`")

CLAIM_DONE = (
    " [done 2026-11-01 R2305] Discharged as the product face and committed "
    "BEFORE any battery (the R2168 mixed-tree rule). CLAIMED: this row, whose "
    "AC-RWD1..AC-RWD6 were already pinned inside it BEFORE the code, after a "
    "fresh zero-occupancy anchor check at HEAD 2026-11-01 (review_window, "
    "review_window_decl, AC-RWD, E_RWD, os-review-window and "
    "test_review_window hit only prose and state files - this row, the board, "
    "state.json, status-export.json, state/debt.md, heartbeat.txt and "
    "closeout_R2304.py - with no code path). DELIVERED: "
    "src/os/review_window_decl.py plus src/os/test_review_window.py plus the "
    "pinned declaration state/review_window.json. One pinned shape only "
    "(window a positive int that is not a bool, declared_by a round, a "
    "non-empty reason, a non-empty declarations list) and each refusal "
    "carries its own code - E_RWD_UNPINNED for an absent file (never a "
    "fabricated pass), E_RWD_UNREADABLE for unparseable JSON, E_RWD_BAD_SHAPE "
    "for every shape violation, E_RWD_DECL_FUTURE when the declaring round is "
    "later than the round being checked (judged BEFORE the declaration is "
    "used), E_RWD_REFUSED when declared_by predates its own last row, and "
    "E_RWD_DRIFT when the effective window moved without a new declaration "
    "row. UNPINNED, DRIFT and every refusal hand back NO window - there is no "
    "default, because the default is what the per-call argument was already "
    "doing wrong. A caller window is compared, not trusted: equal reads "
    "AGREES, different reads DISAGREES naming both numbers. SUITE PASS 6/6 "
    "double-run identical with five adjacent suites green through "
    "evidence_capture (qa/review-window-R2305.log, 1270B, one utf-8 LF single "
    "writer), wired os-review-window(6). LIVE: REVIEW WINDOW window=100 "
    "declared=100 declared_by=R2305 round=R2305 declarations=1 caller=100 "
    "verdict=AGREES - the pinned number is exactly the window exempt_review "
    "already defaulted to in its CLI, so the two faces agree on the day the "
    "boundary is finally dated instead of inferred. The claim dropped tech "
    "claimable to 9, so one real gap row was seeded in the same window "
    "(review_window_wire, AC-RWW1..AC-RWW6 pre-registered, five anchors "
    "git grep -F zero-occupancy) and the gauge closed FLOOR-MET main 5/5 tech "
    "10/10 explore 10/10. Honest notes: (a) the first suite run was red 3/6 "
    "and all three reds were THIS WINDOW's fixture defect - the drift "
    "fixtures bumped the top-level window AND rewrote the last declaration "
    "row to match, which is not a silent bump at all, so the three fixtures "
    "were corrected to leave the row at 100 and no criterion was widened; (b) "
    "the module was unchanged by those reds; (c) AC-RWD3 asks for both rounds "
    "to be named and the DRIFT detail therefore carries the declaring round "
    "and the round of the last declaration row, plus both windows; (d) "
    "tasks.md was not touched: it is the P-47 canonical board and carries no "
    "row for this tech slice, disclosed rather than silently skipped."
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2305, from this window own live finding): "
    "`src/os/review_window_wire.py` - review_window_decl now pins and dates "
    "the window a review is judged against, but nothing consumes it: "
    "`exempt_review` still takes `--window` as a per-call argument with its "
    "own CLI default of 100, so the declaration can read PINNED while every "
    "actual age reading used another number and that divergence is invisible "
    "- exactly the seam `queue_only_floor_wire` closed for the queue-only "
    "floor at R2269. Product: `exempt_review` gains "
    "`--window-from-declaration`, which takes the window from "
    "`review_window_decl.resolve` and refuses an UNPINNED, DRIFT or "
    "consistency-refused declaration before any entry is aged; `--window` and "
    "the new flag are mutually exclusive; the FRESH/STALE classification for "
    "the same world stays byte-identical when the caller passes the pinned "
    "number explicitly, so the wire changes where the number comes from and "
    "nothing about the age law. Criteria AC-RWW1..AC-RWW6 pre-registered HERE "
    "BEFORE any code: AC-RWW1 the window is imported from "
    "review_window_decl.resolve and never re-derived, and a patched resolver "
    "flows straight through; AC-RWW2 an UNPINNED, DRIFT or refused "
    "declaration refuses at exit 2 with zero counts and names its own code, "
    "instead of falling back to the CLI default; AC-RWW3 `--window` together "
    "with `--window-from-declaration` is refused rather than resolved by "
    "precedence; AC-RWW4 for the same world the FRESH/STALE rows are "
    "byte-identical whether the pinned number is passed explicitly or read "
    "from the declaration, and the reported window is the pinned one; "
    "AC-RWW5 CLI 0/2/5 with a byte-stable --json whose pinned keys carry the "
    "window source; AC-RWW6 pure ASCII, stdlib only, zero network, no clock, "
    "plus its own reconcile label. Anchor check at HEAD 2026-11-01: "
    "`review_window_wire`, `AC-RWW`, `E_RWW`, `os-review-window-wire` and "
    "`test_review_window_wire` were all git grep -F zero-occupancy rc=1."
)

NARRATIVE = (
    "2026-11-01 R2305 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline so no new decision "
    "row is presented; the group ledger carries the same three @BigDomain "
    "patrol rows already paid off with zero unreplied numbered handoffs; the "
    "group orders tail is unchanged at the 2026-10-31 18:23 baseline; "
    "benchmarks refreshed 2026-10-29 inside the seven-day gate) - the P1 "
    "canonical rows stay blocked-on-CEO, the weekly proposal duty is met by "
    "BD-PROP-005, the floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, "
    "and the debt gate named exactly one first=yes row (product-face-R2305), "
    "so this window claimed the TOP deliverable tech row: the R2292 "
    "review_window_decl seed at state/queue/tech.md:368, whose "
    "AC-RWD1..AC-RWD6 criteria were already pinned INSIDE that row BEFORE the "
    "code (fresh zero-occupancy anchor check at HEAD 2026-11-01: "
    "review_window, review_window_decl, AC-RWD, E_RWD, os-review-window and "
    "test_review_window hit only prose and state files, with no code path). "
    "PRODUCT: src/os/review_window_decl.py plus src/os/test_review_window.py "
    "plus state/review_window.json - the window a review is judged against "
    "stops being a per-call argument. exempt_review aged every accepted entry "
    "against a window supplied at call time whose only default lived in the "
    "CLI, so two reviewers could read the SAME declaration as FRESH and STALE "
    "on the same day and neither reading was wrong; the live exempt "
    "declaration also carries no until on any of its nine entries, so the age "
    "window was the only thing that could ever end a waiver. The resolver "
    "accepts exactly one pinned shape, refuses a declaring round later than "
    "the round being checked BEFORE using the declaration (E_RWD_DECL_FUTURE), "
    "reads a window that moved without a new declaration row as DRIFT naming "
    "both windows and both rounds, and hands back NO window for UNPINNED, "
    "DRIFT or any refusal - never a default. A caller window is compared "
    "rather than trusted. SUITE PASS 6/6 double-run identical with five "
    "adjacent suites green through evidence_capture "
    "(qa/review-window-R2305.log, 1270B, one utf-8 LF single writer), wired "
    "os-review-window(6). LIVE: window=100 declared=100 declared_by=R2305 "
    "declarations=1 caller=100 verdict=AGREES - the pinned number equals the "
    "exempt_review CLI default, so the two faces agree on the day the "
    "boundary is dated. The claim dropped tech claimable to 9, so one real gap "
    "row was seeded (review_window_wire, AC-RWW1..AC-RWW6 pre-registered) and "
    "the gauge closed FLOOR-MET 5/5 10/10 10/10. This window is 2 points (a "
    "runnable reader plus a reusable suite); the battery on this tree is the "
    "register successor row, R2306."
)

TOKENS = (
    "R2305 tokens: local=~21k api=0 api_reason=product window on the debt "
    "register first item - one resolver module with its six pre-registered "
    "criteria and its suite, three this-window fixture defects corrected "
    "against the measured truth, one dogfooded evidence capture (two legs "
    "identical, five adjacent suites green), one pinned live declaration "
    "file, one live CLI reading of the real declaration, one runner wiring "
    "line, one real gap row seeded to hold the tech floor, and the "
    "queue/board/state/export closeout; zero cloud calls and zero external "
    "API touches; the battery carries to R2306"
)

SELF_HEAL = (
    "R2305 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply it, "
    "and this session runs unelevated, so the definition of the loop hosting "
    "this window was left untouched. Open local-lane item for an elevated "
    "window (sixty-ninth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2305 honest disclosures: (a) the first suite run was red 3/6 and all "
    "three reds were this-window fixture defects, never criteria widened - "
    "the AC-RWD3 and AC-RWD4 drift worlds and the AC-RWD5 drift CLI world "
    "bumped the top-level window AND rewrote the last declaration row to "
    "match it, which is not a silent bump and must not read as drift, so the "
    "three fixtures were corrected to leave the row at 100 while the module "
    "stayed byte-identical; (b) AC-RWD4 is stricter than its nearest "
    "precedent by design - log_floor hands the drifted floor back with its "
    "verdict while this resolver raises instead, because the seed row asks "
    "for NO floor on DRIFT and a returned number is what a caller consumes; "
    "(c) AC-RWD3 names both rounds by carrying the top-level declared_by and "
    "the round of the last declaration row in the DRIFT detail, which is the "
    "pair that differs when a window is bumped by a new round without a row; "
    "(d) the live declaration is PINNED at 100 because that is the number "
    "exempt_review already defaulted to - this window dates the boundary, it "
    "does not change any age reading, and the consumer wire is the seeded "
    "review_window_wire row rather than a silent second edit; (e) tasks.md "
    "was left untouched: it is the P-47 canonical board and carries no row "
    "for this tech slice, disclosed rather than silently skipped."
)

ITEMS = [NARRATIVE, TOKENS, SELF_HEAL, DISCLOSURES]

HEARTBEAT_2305 = (
    "tick 2305 2026-11-01 product window: review_window_decl shipped with its "
    "six pre-registered criteria pinned in the tech row before the code. One "
    "pinned state/review_window.json (window 100, declared_by R2305) plus a "
    "resolver that accepts exactly one shape, refuses a future declaration "
    "before it is used (E_RWD_DECL_FUTURE), reads a silent window bump as "
    "DRIFT with both windows and both rounds named, and hands back NO window "
    "for UNPINNED, DRIFT or any refusal - never a default. A caller window is "
    "compared (AGREES/DISAGREES naming both), and nothing is written or "
    "clocked. Suite PASS 6/6 double-run identical with five adjacent suites "
    "green (qa/review-window-R2305.log, 1270B, one utf-8 LF single writer), "
    "wired os-review-window(6). LIVE window=100 declared=100 declared_by="
    "R2305 verdict=AGREES, exactly the window exempt_review already defaulted "
    "to. Three reds on the first run were this window's fixtures, corrected "
    "without widening a criterion. Claim dropped tech claimable to 9, so one "
    "real seed (review_window_wire) held the floor at 10/10. 2 product points."
)


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob, suffix):
    temp = path + ".tmp-" + suffix
    with io.open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    return len(blob)


def step_queue(argv):
    """Close the claimed row and append one real seed, both guarded."""
    raw = load(QUEUE)
    text = raw.decode("utf-8")
    lines = text.split("\n")
    if len(lines) < 368:
        print("E_QUEUE short file %d lines" % len(lines))
        return 3
    target = lines[367]
    if not target.startswith(CLAIM_ANCHOR):
        print("E_QUEUE line 368 is not the claimed row: %r" % target[:80])
        return 3
    if "[done 2026-11-01 R2305]" in target:
        print("QUEUE already closed")
        return 0
    closed = "- [x]" + target[len("- [ ]"):] + CLAIM_DONE
    lines[367] = closed
    if SEED_ROW.split(" ")[0] in text and "review_window_wire" in text:
        print("E_QUEUE seed row already present")
        return 3
    body = "\n".join(lines)
    if not body.endswith("\n"):
        body += "\n"
    body += SEED_ROW + "\n"
    blob = body.encode("utf-8")
    if "--execute" not in argv:
        print("DRY RUN queue before=%d after=%d closed_line=368 seed=1"
              % (len(raw), len(blob)))
        return 0
    size = write_atomic(QUEUE, blob, "r2305q")
    back = load(QUEUE).decode("utf-8")
    if "[done 2026-11-01 R2305]" not in back.split("\n")[367]:
        print("E_QUEUE_READBACK")
        return 3
    if "review_window_wire" not in back:
        print("E_QUEUE_SEED_READBACK")
        return 3
    print("QUEUE %dB closed=368 seed=1" % size)
    return 0


def step_append(argv):
    raw = load(STATE)
    state = json.loads(raw.decode("utf-8"))
    if state["tick"] != TICK - 1:
        print("E_TICK expected %d found %s" % (TICK - 1, state["tick"]))
        return 3
    log = state["log"]
    have = [item for item in log if item.startswith("2026-11-01 R2305 ")]
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
    gate = SF.measure(len(blob))
    print("APPEND plan bytes=%d margin=%d verdict=%s"
          % (len(blob), gate["margin"], gate["verdict"]))
    if "--execute" not in argv:
        print("DRY RUN append predicted=%d log=%d" % (len(blob), len(log)))
        return 0
    size = write_atomic(STATE, blob, "r2305s")
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
    size = write_atomic(EXPORT, blob, "r2305e")
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
    text += HEARTBEAT_2305 + "\n"
    if "--execute" not in argv:
        print("DRY RUN heartbeat +1 row")
        return 0
    size = write_atomic(HEARTBEAT, text.encode("utf-8"), "r2305h")
    print("HEARTBEAT +1 row %dB" % size)
    return 0


STEPS = {"queue": step_queue, "append": step_append, "export": step_export,
         "heartbeat": step_heartbeat}


def main(argv):
    if len(argv) < 2 or argv[1] not in STEPS:
        sys.stdout.write("usage: closeout_R2305.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))