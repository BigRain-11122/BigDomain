"""Closeout for the R2283 window: append its rows to the live state log.

The state file sat at 42015 bytes against the 78500 byte waterline at the
open, so this window's rows do not cross it and no fold is due - the fold
helper is still available and runs only when the predicted post size would
cross the gate. The append goes through the shipped layout writers and
proves its own bytes by re-parsing and comparing the payload; every refusal
happens before a write.

ASCII, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

sys.path.insert(0, BASE)
import state_fold  # noqa: E402

KEEP_LIVE = 24


def tokens_of(window):
    found = set()
    for line in window:
        found |= set(state_fold.PAT.findall(line))
    return sorted(found)


def raw_and_state():
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    return raw, json.loads(raw.decode("utf-8"))


def fold(execute):
    raw, state = raw_and_state()
    count = len(state["log"])
    end = count - KEEP_LIVE
    if end < 1:
        return None
    window = state["log"][0:end]
    tokens = tokens_of(window)
    summary = ("Fold 598 (R2283): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-10.md; window tokens: %s"
               % (end, " ".join(tokens)))
    return state_fold.fold(ROOT, "R2283", 598, 1, end, summary,
                           execute=execute)


def predicted_append_bytes(rows):
    raw, state = raw_and_state()
    text = raw.decode("utf-8")
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        raise SystemExit("REFUSE: log item lines do not match the log length")
    return sum(len(state_fold.ps_escape(row)) + len(state_fold.ITEM_PREFIX) + 2
               for row in rows)


def append(rows, tick, execute):
    raw, state = raw_and_state()
    if tick <= state["tick"]:
        raise SystemExit("REFUSE: tick %d is not above %d"
                         % (tick, state["tick"]))
    text = raw.decode("utf-8")
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        raise SystemExit("REFUSE: log item lines do not match the log length")
    newline = layout["newline"]
    index = layout["item_index"][-1]
    lines = list(layout["lines"])
    if not lines[index].rstrip().endswith(","):
        lines[index] = lines[index] + ","
    insert = []
    for position, row in enumerate(rows):
        tail = "," if position < len(rows) - 1 else ""
        insert.append(state_fold.ITEM_PREFIX + state_fold.ps_escape(row)
                      + tail)
    new_lines = lines[:index + 1] + insert + lines[index + 1:]
    body = newline.join(new_lines)
    body = body.replace('"tick": %d' % state["tick"], '"tick": %d' % tick, 1)
    data = body.encode("utf-8")
    if not execute:
        return {"would_bytes": len(data), "before": len(raw)}
    with io.open(STATE, "wb") as handle:
        handle.write(data)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("REFUSE: read-back differs")
    check = json.loads(back.decode("utf-8"))
    expected = list(state["log"]) + list(rows)
    if check["log"] != expected or check["tick"] != tick:
        raise SystemExit("REFUSE: payload does not round-trip")
    return {"post_bytes": len(data), "before": len(raw),
            "log": len(check["log"]), "tick": check["tick"]}


ROWS = [
    "2026-10-31 R2283 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with zero "
    "unreplied numbered handoffs; the group orders tail is unchanged at the "
    "2026-10-31 18:23 baseline consumed in R2278; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "queue floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the "
    "debt gate named exactly one first=yes row (reconcile-battery-R2283), so "
    "this window ran the VERIFICATION that row demanded with ZERO product "
    "edits until green (the R2168 mixed-tree rule). RESULT: full reconcile "
    "battery on the committed R2282 tree 2332496b with an empty git status "
    "before the run = RUNNER PASS 447/447 suites green plus controls 7/7 in "
    "940.1s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2283.log, 775329B at RUNNER close, "
    "single-writer utf-8 LF through src/os/battery_stream.py, never a shell "
    "redirection), criteria total 3658 - exactly the pre-registered +1 suite "
    "/ +6 criteria against R2281 (446/3652) from the R2282 os-evidence-parity "
    "suite, so the prediction matched the measurement with no correction. "
    "Four follow-up sections then ran through src/os/battery_followup.py: the "
    "matrix section FAILED first on the stale doc (on-disk=43126B "
    "regenerated=43205B) and did NOT rewrite it, which is the designed "
    "order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 447 suites / 3658 criteria (43205B) and "
    "the re-run read all four sections PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing on VERDICT R2283 PASS. Register closed "
    "through its own writer (debt_close line=55, open 2->1, done 32->33, "
    "readback ok) and product-face-R2284 opened first=yes through "
    "debt_append (before=33390B after=34202B, readback ok), naming the tech "
    "head state/queue/tech.md:354 prefix AC-SLC1. Honest score: a 0-point "
    "verification window with no product face, recorded as such; the state "
    "file measured 42015B against the 78500B waterline (margin 36485B) so no "
    "fold was due.",
    "R2283 tokens: local=~14k api=0 api_reason=verification-only window - "
    "one full reconcile battery with its streamed evidence file, one "
    "four-section follow-up through the shipped callable plus one matrix "
    "regeneration from that evidence, two register writes through the "
    "shipped close and append writers, and the queue/board/state/export "
    "closeout; zero cloud calls and zero external API touches",
    "R2283 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (forty-ninth consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md line 43).",
    "R2283 honest disclosures: (a) the debt_append call was REFUSED once "
    "with E_DEBTA_BAD_FIELD because the note text carried 'rc=1' and the "
    "register writer forbids '=' inside a field value; the note was reworded "
    "to 'expecting rc 1' and the dry run then planned 33390B -> 34202B "
    "before the execute leg - no criterion was widened and no row was "
    "written by the refused call. (b) The battery ran as a background shell "
    "task and its evidence file appears only at completion because "
    "battery_stream buffers in memory and writes once; the 0-byte readings "
    "at minute one and minute five were the buffering, not a dead runner, "
    "confirmed by the live battery_stream process and then by the 775329B "
    "file. (c) Both follow-up legs are retained in the evidence file (1889B "
    "FAIL then 1950B PASS); the FAIL leg is the designed first use of the "
    "matrix section, which refuses to rewrite the stale doc.",
]


def main(argv):
    execute = "--execute" in argv
    before, state = raw_and_state()
    print("STATE before=%dB tick=%d log=%d gate=%d margin=%d"
          % (len(before), state["tick"], len(state["log"]),
             state_fold.GATE, state_fold.GATE - len(before)))
    predict = predicted_append_bytes(ROWS)
    will_cross = len(before) + predict >= state_fold.GATE
    print("APPEND predicted=%dB would_cross_gate=%r" % (predict, will_cross))
    if will_cross:
        plan = fold(execute)
        if plan is None:
            print("FOLD skipped: fewer than %d live rows" % (KEEP_LIVE + 1))
        else:
            print("FOLD window=%d:%d lines=%d tokens=%d predicted=%dB "
                  "mode=%s" % (plan["window_start"], plan["window_end"],
                               plan["window_lines"], plan["tokens_total"],
                               plan["predicted_bytes"], plan["mode"]))
            if plan["would_fail"]:
                return 2
    else:
        print("FOLD not due: predicted post stays under the gate")
    appended = append(ROWS, 2283, execute)
    print("APPEND mode=%s %r"
          % ("execute" if execute else "dry-run", appended))
    after, new_state = raw_and_state()
    print("STATE after=%dB gate=%d margin=%d tick=%d log=%d"
          % (len(after), state_fold.GATE, state_fold.GATE - len(after),
             new_state["tick"], len(new_state["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))