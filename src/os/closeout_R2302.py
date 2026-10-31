"""R2302 closeout: fold if the waterline demands it, then append the log items.

Every step is measured, not assumed: the fold is block-aligned so a round's
narrative and its ledger line never split (the R2301 lesson), the fold number
is derived from the real archive headers (the R2290 lesson), and the append is
a predicted-delta atomic write with a read-back proof and no temp residue.
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import state_fold as SF
import state_io as SIO

ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
ROUND = "R2302"
RESERVE = 7000

NARRATIVE = (
    "2026-11-01 R2302 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, and the four tokens "
    "the set diff reported new are REFERENCES inside rows this window already "
    "consumed - D-20261006-05, D-20261007-04, D-20261007-05 and D-20261008-05 "
    "appear only as 'executed under D-...' text in BigMoney and BigStream "
    "rows, so no new decision row is presented and zero domain action is owed "
    "- disclosed as a false-positive class of content addressing rather than "
    "swept; the group ledger carries the same @BigDomain patrol rows already "
    "paid off with zero unreplied numbered handoffs; the group orders tail is "
    "unchanged at the 2026-10-31 18:23 baseline consumed in R2278; benchmarks "
    "refreshed 2026-10-29 inside the seven-day gate) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the debt "
    "gate named exactly one first=yes row (product-face-R2301), so this "
    "window claimed the TOP deliverable tech row: the R2288 evidence_variants "
    "seed at state/queue/tech.md:366, whose AC-EVR1..AC-EVR6 criteria were "
    "already pinned INSIDE that row BEFORE the code (fresh zero-occupancy "
    "anchor check at HEAD 2026-11-01: evidence_variants, AC-EVR, E_EVR, "
    "os-evidence-variants and test_evidence_variants hit only prose and state "
    "files - the row, the board, state.json, status-export.json, "
    "state/debt.md and three closeout helpers - with no code path). PRODUCT: "
    "src/os/evidence_variants.py plus src/os/test_evidence_variants.py - the "
    "evidence pile the history had been rounding becomes a classified fact. "
    "followup_history reads only the canonical reconcile-all-R<nnnn>.log and "
    "reports every other name as IGNORED, so a failure leg written under a "
    "variant name is invisible while the canonical leg of the same round "
    "still reads green. The reader ASKS followup_history.NAME_RE instead of "
    "restating it: the scope prefix is sliced out of that pattern text and "
    "every candidate split of a name is handed back to the same pattern, so "
    "patching the one law moves both readers (the suite proves it by "
    "re-patching the pattern to a different prefix and watching this reader "
    "classify the new names and refuse the old ones). Each variant pairs with "
    "its canonical round; DUPLICATE or DISTINCT is decided by CONTENT digest "
    "with both digests named, never by name, so two different suffix names "
    "carrying one body both read DUPLICATE; a variant whose canonical leg is "
    "absent reads ORPHAN and is listed, never dropped; retry-ness is asked "
    "through retry_naming.is_retry so the retry law keeps one owner. SUITE "
    "PASS 6/6 double-run identical digest 4C1B9787CFCC43E7 with five adjacent "
    "suites green through the R2261 evidence_capture callable "
    "(qa/evidence-variants-R2302.log, 1307B, one utf-8 LF single writer, "
    "crlf=0, no BOM), wired os-evidence-variants(6). LIVE: EVIDENCE VARIANTS "
    "variants=61 duplicate=0 distinct=59 orphan=2 retry=4 "
    "verdict=UNRESOLVED - the honest size of the pile the history reported as "
    "noise: the two orphans are the R2136 b/c legs whose canonical log was "
    "never committed, and the four retries are exactly the "
    "R2262/R2277/R2289/R2299 red-then-green corrections that followup_history "
    "counted as IGNORED. The claim dropped tech claimable to 9, so one real "
    "gap row was seeded from this window's own live finding (orphan_trace, "
    "AC-OTR1..AC-OTR6 pre-registered, five anchors git grep -F "
    "zero-occupancy rc=1) and the gauge closed FLOOR-MET. The battery carries "
    "to R2303 as the register successor row."
)

TOKENS = (
    "R2302 tokens: local=~17k api=0 api_reason=product window on the debt "
    "register first item - one reader module with its six pre-registered "
    "criteria and its suite, three this-window test expectations corrected "
    "against the measured truth, one dogfooded evidence capture (two legs "
    "identical, five adjacent suites green), one live reading of the whole 61 "
    "leg evidence pile, one runner wiring line, one real gap row seeded to "
    "hold the tech floor, two register writes through the shipped close and "
    "append writers, and the queue/board/state/export closeout; zero cloud "
    "calls and zero external API touches; the battery carries to R2303"
)

SELF_HEAL = (
    "R2302 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (sixty-sixth consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2302 honest disclosures: (a) the first suite run was red 3/6 and all "
    "three reds were this-window defects, never criteria widened - the "
    "AC-EVR1 no-regex probe matched the substring 'import re' inside 'import "
    "retry_naming', so the probe now reads whole statements, and the AC-EVR5 "
    "key assertion was real: to_json built dir/counts/variants/verdict while "
    "REPORT_KEYS promised dir/variants/counts/verdict, so the pinned order "
    "was corrected in the MODULE rather than in the test; the third red was "
    "the honest one - the runner label was not yet wired and the wiring "
    "landed before the green run. (b) The evidence capture's first invocation "
    "was refused E_EVC_NO_SUITE for src/os/test_retry_naming.py, a file that "
    "does not exist; the adjacent list was re-measured against the real "
    "directory and nothing was written by the refused call. (c) The tech seed "
    "was inserted by a script whose first two attempts aborted on their own "
    "guards before writing (a wrong 0-based index, then an assertion naming "
    "the expected anchor), and both left the queue byte-intact. (d) The live "
    "reading is UNRESOLVED and that is disclosed rather than dressed up: 59 "
    "of 61 legs differ from their canonical log, which is the truth of the "
    "pile and not a defect of the reader; this window names them, it does not "
    "rewrite history. (e) The three stale open rows in tasks.md and the "
    "superseded R2250/R2266/R2274-style rows in src/os/backlog.md were left "
    "untouched: tasks.md is the P-47 canonical board and carries no row for "
    "this tech slice, so there was no checkbox to tick, which is disclosed "
    "rather than silently skipped."
)


def round_of(item):
    """The round label an item belongs to, or None when it carries none."""
    match = re.match(r"^(?:\d{4}-\d{2}-\d{2}\s+)?(R\d{4})\b", item.strip())
    return match.group(1) if match else None


def fold_number(archive_dir):
    """Derive the next fold number from the real archive headers."""
    best = 0
    for name in os.listdir(archive_dir):
        if not name.startswith("state-log-archive-"):
            continue
        path = os.path.join(archive_dir, name)
        try:
            text = io.open(path, "r", encoding="utf-8",
                           errors="replace").read()
        except OSError:
            continue
        for value in re.findall(r"fold (\d+) window", text):
            best = max(best, int(value))
    if not best:
        raise SystemExit("E_R2302_NO_FOLD_NUMBER")
    return best + 1


def plan_window(raw, state):
    """The largest whole-round window that still clears the gate with reserve."""
    log = state["log"]
    count = len(log)
    labels = [round_of(item) for item in log]
    ends = []
    for index in range(1, count + 1):
        here = labels[index - 1]
        after = labels[index] if index < count else None
        if here is not None and after != here:
            ends.append(index)
    for end in ends:
        window = log[0:end]
        tokens = set()
        for item in window:
            tokens |= set(SF.PAT.findall(item))
        summary = ("Fold %s: log lines 1..%d (%s..%s, whole round blocks) "
                   "folded verbatim into the archive; window tokens: %s"
                   % (ROUND, end, labels[0], labels[end - 1],
                      " ".join(sorted(tokens))))
        plan, text = SF.plan_fold(raw, state, 1, end, summary,
                                  reserve=RESERVE)
        if not plan["tokens_missing"] and plan["gate_ok"]:
            return end, summary, plan, text
    raise SystemExit("E_R2302_NO_FOLD_WINDOW")


def append_items(text, items):
    """Splice items onto the log array of a canonical state document."""
    lines = text.split("\r\n")
    start = None
    end = None
    for index, line in enumerate(lines):
        if line.strip().startswith('"log": ['):
            start = index
            break
    if start is None:
        raise SystemExit("E_R2302_NO_LOG_BLOCK")
    for index in range(start + 1, len(lines)):
        if lines[index].strip() in ("]", "],"):
            end = index
            break
    if end is None:
        raise SystemExit("E_R2302_UNTERMINATED_LOG")
    last = end - 1
    if not lines[last].rstrip().endswith('"'):
        raise SystemExit("E_R2302_LAST_ITEM_SHAPE")
    lines[last] = lines[last] + ","
    fresh = [SF.ITEM_PREFIX + SF.ps_escape(item) for item in items]
    fresh[-1] = fresh[-1]
    lines[end:end] = [line + "," for line in fresh[:-1]] + [fresh[-1]]
    return "\r\n".join(lines)


def patch_scalars(text, values):
    """Rewrite top-level scalar lines in place so the text matches the payload."""
    lines = text.split("\r\n")
    seen = {}
    for index, line in enumerate(lines):
        stripped = line.strip()
        for key in values:
            head = '"%s":' % key
            if stripped.startswith(head):
                lines[index] = "  %s %s," % (head,
                                             json.dumps(values[key]))
                seen[key] = True
    missing = [key for key in values if key not in seen]
    if missing:
        raise SystemExit("E_R2302_MISSING_SCALAR %r" % (missing,))
    return "\r\n".join(lines)


def write_state(text, expected):
    """One atomic replace with a predicted delta and a read-back proof."""
    before = SIO.read_raw(STATE)
    payload = SIO.parse(text)
    if payload != expected:
        raise SystemExit("E_R2302_PAYLOAD_MISMATCH")
    new_bytes = text.encode("utf-8")
    predicted = len(new_bytes)
    handle, temp = __import__("tempfile").mkstemp(
        dir=os.path.dirname(STATE), prefix=".r2302_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(new_bytes)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = SIO.read_raw(STATE)
    if back != new_bytes:
        raise SystemExit("E_R2302_READBACK")
    residue = [name for name in os.listdir(os.path.dirname(STATE))
               if name.startswith(".r2302_")]
    if residue:
        raise SystemExit("E_R2302_TEMP_RESIDUE %r" % (residue,))
    return len(before), predicted


def main():
    raw, state = SF.read_state(STATE)
    if not SIO.layout(raw.decode("utf-8"))["layout_ok"]:
        raise SystemExit("E_R2302_STATE_NOT_CANON")
    items = [NARRATIVE, TOKENS, SELF_HEAL, DISCLOSURES]
    estimated = sum(len(item) + 24 for item in items)
    print("measured: state=%dB gate=%d estimated_items=%dB"
          % (len(raw), SF.GATE, estimated))

    text = raw.decode("utf-8")
    if len(raw) + estimated > SF.GATE:
        end, summary, plan, folded = plan_window(raw, state)
        print("fold: window=1..%d lines=%d tokens_missing=%d predicted=%dB"
              % (end, plan["window_lines"], len(plan["tokens_missing"]),
                 len(folded.encode("utf-8"))))
        number = fold_number(os.path.join(ROOT, "logs"))
        print("fold: number=%d" % number)
        result = SF.fold(ROOT, ROUND, number, 1, end, summary,
                         reserve=RESERVE, execute=True)
        print("fold done: wrote=%r bytes=%r"
              % (result.get("wrote"), result.get("bytes")))
        raw, state = SF.read_state(STATE)
        text = raw.decode("utf-8")

    tokens = set(value for value in state["last_dec_tokens"].split(",")
                 if value)
    tokens |= set(["D-20261006-05", "D-20261007-04", "D-20261007-05",
                   "D-20261008-05"])
    state["tick"] = 2302
    state["last_dec_tokens"] = ",".join(sorted(tokens))
    state["last_decision_rows"] = 289
    state["log"] = list(state["log"]) + items
    expected = json.loads(json.dumps(state))

    updated = append_items(text, items)
    updated = patch_scalars(updated, {
        "tick": expected["tick"],
        "last_dec_tokens": expected["last_dec_tokens"],
        "last_decision_rows": expected["last_decision_rows"],
    })
    before, after = write_state(updated, expected)
    measured = SIO.layout(SIO.read_raw(STATE).decode("utf-8"))
    print("append: %dB -> %dB log_items=%d off_indent=%d layout_ok=%r"
          % (before, after, measured["log_items"],
             measured["items_off_indent"], measured["layout_ok"]))
    print("state: tick=%d log=%d margin=%d"
          % (expected["tick"], len(expected["log"]), SF.GATE - after))


if __name__ == "__main__":
    main()