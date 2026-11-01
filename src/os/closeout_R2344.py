"""state_close_R2344 - the round record for the R2344 window.

The window opened on the five-silence scan [DEC] FLAG of 54 "new" decision
rows, traced it to a parse defect at its birth site (last_dec_tokens is a JSON
array; [string] on an array joins with spaces, so the comma-only split
collapsed the 65-token baseline into ONE token and every row-owner token
re-flagged forever), shipped the fix plus a collapse guard, and re-ran the scan
to a true [DEC] PASS. It then ran THE BATTERY the board top carried, on the
committed tree that includes that fix.

The battery figures are read out of the evidence file at write time and
embedded verbatim; this script never invents a suite or criterion count.

Dry run by default; --execute writes with a read-back proof and leaves no
temp residue.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2344.log")
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

TICK = 2344
DATE_RE = re.compile(r"^(20\d\d-\d\d-\d\d R\d+ |R\d+ tokens:|tokens:)")
RUNNER_RE = re.compile(r"RUNNER\s+(PASS|FAIL).*", re.IGNORECASE)
BATCH_RE = re.compile(r"BATTERY rc=(-?\d+) ([\d.]+)s")


def evidence_reading(path):
    """Return (runner_line, runtime_line) verbatim from the evidence file."""
    if not os.path.exists(path):
        return ("EVIDENCE-ABSENT", "EVIDENCE-ABSENT")
    text = io.open(path, "r", encoding="utf-8", errors="replace").read()
    runner = ""
    batch = ""
    for line in text.splitlines():
        if RUNNER_RE.search(line):
            runner = line.strip()
        if BATCH_RE.search(line):
            batch = line.strip()
    if not batch and runner:
        tail = re.search(r"in ([\d.]+)s", runner)
        batch = "wall %ss (from the RUNNER line)" % tail.group(1) if tail else ""
    return (runner or "NO-RUNNER-LINE", batch or "NO-RUNTIME-LINE")


def read_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fold_window(state):
    log = state["log"]
    limit = min(16, len(log) - 1)
    candidates = []
    for end in range(1, limit + 1):
        follows = log[end] if end < len(log) else ""
        if DATE_RE.match(follows):
            candidates.append(end)
    return candidates[-1] if candidates else None


def build_items(runner, batch):
    live = (
        "2026-11-01 R2344 tooling-defect window (five-silence scan at open: "
        "clean tree, no .git/index.lock; the evolution ledger carries zero "
        "@BigDomain rows; the local orders board tail is unchanged and the "
        "group orders tail still reads the 2026-11-01 10:4x baseline already "
        "acked as non-execution; benchmarks refreshed 2026-11-01, inside the "
        "seven-day gate). THE SCAN ITSELF WAS THE FINDING: [DEC] raised 54 "
        "\"new\" decision rows, all of them historical (D-20261028-01 .. "
        "D-20261101-22). Root cause read at the birth site, not guesses: "
        "state.json last_dec_tokens is a JSON array, [string] on an array "
        "joins with SPACES, and the gate split the baseline on commas only, "
        "so 65 tokens collapsed into one and no row-owner token could ever "
        "match. Proven live before the fix (comma split of the stored "
        "baseline returned exactly 1 token). Fixed in "
        "tools/skills/bigdomain-loop-scan/scripts/scan_five_still.ps1: split "
        "on commas AND whitespace, accept the array form directly, and add a "
        "collapse guard that says baseline_parse_collapsed instead of "
        "re-flagging the whole board if the parse regresses again. Re-run "
        "after the fix: [DEC] PASS rows=134 known_tokens=65 "
        "row_owner_tokens=54. Committed as 44b79820 with a targeted add. "
        "The same defect had already killed this repo's PYTHON twin gate: "
        "src/os/scan_five_still.py line 31 called .split(',') on the same "
        "field and died with AttributeError on a list, so that scan face has "
        "been unavailable since the field type drifted; repaired with a "
        "norm_tokens helper that accepts both forms, proven by running it "
        "(LEDGER unreplied=0, DEC tokens=65 new=0, BENCH 2026-11-01). "
        "THEN THE BOARD TOP: the battery on the committed tree, evidence in "
        "qa/reconcile-all-R2344.log - %s / %s." % (runner, batch))
    tokens = (
        "R2344 tokens: local=~21k api=0 api_reason=tooling-defect window - "
        "one five-silence scan, one birth-site trace of a recurring false "
        "positive, one script fix with its guard, one verifying re-scan, one "
        "committed-tree battery, and the state/export/heartbeat/board "
        "closeout; zero cloud calls and zero external API touches")
    gate = (
        "R2344 decision gate (D-20260930-19 step 2): the content-addressed "
        "diff of the group decisions.md against the stored baseline is what "
        "exposed this window's defect - after the fix it reads NO new tokens "
        "(new=[] over 65 live tokens against 54 row-owner rows), so nothing "
        "was executed, rejected or acknowledged this window and the baseline "
        "is unchanged at last_decision_rows=135.")
    honest = (
        "R2344 honest disclosures: (a) the 54-row flag was a defect in THIS "
        "repo's own gate, not a group-side change, and the first reading of "
        "it cost a full diff dump before the cause was located - the "
        "disclosure is that a red gate was read as news for one pass. (b) No "
        "product module shipped: the tech queue head is line 391 AC-RWH1 "
        "(review_window_history, six pre-registered criteria) and it was NOT "
        "claimed this window, so it stays at the head of the queue rather "
        "than being half-built; the queue is not empty and that is stated "
        "plainly instead of dressed as a no-pullable round. (c) The battery "
        "is a verification act and scores no product point under the "
        "product-first law; the round's only shippable artifact is the scan "
        "fix, which removes a per-round token burn rather than adding a "
        "feature. (d) BigDomain-OSLoop still reads LogonType=InteractiveToken, "
        "which the 2026-09-29 machine law forbids for lane tasks; "
        "src/os/register_loop_task.ps1 already passes an explicit S4U "
        "principal and needs an elevated shell to apply, so the task "
        "definition is untouched again this window and the item stays open "
        "as the debt row loop-s4u-reconcile. (e) tasks.md was left untouched: "
        "it is the P-47 canonical board and carries no row for a tooling "
        "slice, disclosed rather than silently skipped.")
    return [live, tokens, gate, honest]


def main(argv):
    state = read_state()
    raw = io.open(STATE, "rb").read()
    print("state before=%dB log=%d tick=%d"
          % (len(raw), len(state["log"]), state["tick"]))
    runner, batch = evidence_reading(EVIDENCE)
    print("evidence: %s | %s" % (runner, batch))
    items = build_items(runner, batch)
    print("append items=%d" % len(items))
    plan = None
    end = fold_window(state)
    water = SF.check(ROOT)
    print("fold gate: needed=%s bytes=%s gate=%s margin=%s"
          % (water["fold_needed"], water["bytes"], water["gate"],
             water["margin"]))
    if end is not None and water["fold_needed"]:
        plan = SF.fold(ROOT, "R2344", 632, 1, end, "fold R2344", execute=False)
        print("fold plan window=1:%d lines=%d predicted=%dB gate_ok=%s"
              % (end, plan["window_lines"], plan["predicted_bytes"],
                 plan["gate_ok"]))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    if plan is not None:
        done = SF.fold(ROOT, "R2344", 632, 1, end, "fold R2344", execute=True)
        print("fold done predicted=%s measured=%s"
              % (done["predicted_bytes"], done["post_bytes"]))
    state = read_state()
    state["tick"] = TICK
    state["log"].extend(items)
    body = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temp = STATE + ".tmp"
    # state.json canon is CRLF; a bare-LF write trips the STATE eol gate and the
    # next fold refuses E_STATE_LAYOUT (R2344 birth-site note).
    with io.open(temp, "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(body)
    os.replace(temp, STATE)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body or os.path.exists(temp):
        print("E_READBACK")
        return 3
    print("APPENDED state=%dB log=%d tick=%d readback=ok"
          % (len(back.encode("utf-8")), len(state["log"]), state["tick"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))