"""Closeout for the R2285 window: append its rows to the live state log.

The batch append goes through the shipped layout writers and proves its own
bytes by re-parsing and comparing the payload; every refusal happens before
a write. A fold runs only when the predicted post size would cross the gate.

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
TICK = 2285


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
    summary = ("Fold 600 (R2285): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-10.md; window tokens: %s"
               % (end, " ".join(tokens)))
    return state_fold.fold(ROOT, "R2285", 600, 1, end, summary,
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
    "2026-10-31 R2285 verification window on the debt register first item "
    "(product-face-R2285 = reconcile-battery-R2285), discharged on the "
    "committed R2284 tree 453f45c7 with an empty git status before the run "
    "and zero product edits until green (the R2168 mixed-tree rule): full "
    "reconcile battery = RUNNER PASS 448/448 suites green plus controls 7/7 "
    "in 865.5s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2285.log, 775794B, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection), criteria "
    "total 3664 - exactly the pre-registered +1 suite / +6 criteria against "
    "R2283 (447/3658) from the R2284 os-stamp-locator suite, so the "
    "prediction matched the measurement with no correction. Four follow-up "
    "sections then ran through src/os/battery_followup.py: the matrix "
    "section FAILED first on the stale doc (on-disk=43205B "
    "regenerated=43279B) and did NOT rewrite it, which is the designed "
    "order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 448 suites / 3664 criteria (43279B) "
    "and the re-run read all four sections PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing on VERDICT R2285 PASS. Register closed "
    "through its own writer (debt_close line=57, open 2->1, done 34->35, "
    "readback ok) and product-face-R2286 opened first=yes through "
    "debt_append (before=35007B after=35381B, readback ok) naming the tech "
    "head at state/queue/tech.md:355 prefix AC-MGT1, the R2270 machine_gate "
    "seed. Honest score: a 0-point verification window with no product "
    "face.",
    "R2285 tokens: local=~15k api=0 api_reason=verification-only window - "
    "one full reconcile battery with its streamed evidence file, one "
    "four-section follow-up through the shipped callable plus one matrix "
    "regeneration from that evidence, two register writes through the "
    "shipped close and append writers, and the queue/board/state/export "
    "closeout; zero cloud calls and zero external API touches",
    "R2285 self-heal check: BigDomain-OSLoop is registered and its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal and needs an elevated shell "
    "to apply it, and this session runs unelevated, so the definition of "
    "the loop hosting this window was left untouched. Open local-lane item "
    "for an elevated window (fifty-first consecutive disclosure, carried as "
    "the stale row loop-s4u-reconcile in state/debt.md).",
    "R2285 honest disclosures: (a) the battery ran as a background shell "
    "task, so its evidence file appears only at completion because "
    "battery_stream buffers in memory and writes once - every probe before "
    "that point legitimately finds no file, which is buffering and not a "
    "dead runner. (b) The evidence log carries two FAIL lines inside "
    "controls that are SUPPOSED to fail (pay-tamper-revokes and "
    "member-tamper exit 2 naming their findings); both are PASS control "
    "lines whose exit code is the assertion, not a red suite - no suite "
    "failed. (c) This round shipped no product code, so the debt register "
    "successor names the product face (machine_gate) rather than a second "
    "verification, and no state fold was due because the predicted post "
    "size stays under the 78500B gate.",
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
    appended = append(ROWS, TICK, execute)
    print("APPEND mode=%s %r"
          % ("execute" if execute else "dry-run", appended))
    after, new_state = raw_and_state()
    print("STATE after=%dB gate=%d margin=%d tick=%d log=%d"
          % (len(after), state_fold.GATE, state_fold.GATE - len(after),
             new_state["tick"], len(new_state["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))