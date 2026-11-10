"""R2621 push receipt and adopt-after-commit re-run: ONE log line, no tick
change (the tick belongs to the round, not to its receipt).
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2621 push and adopt-after-commit re-run: git push origin main SUCCEEDED "
    "(1d9a00c4..5c3cf83d main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 5c3cf83d with an EMPTY git status after the commit, so the "
    "whole window is delivered. The R2614 lesson was then discharged on the "
    "FINAL COMMITTED TREE: the four suites that write or read the artifacts "
    "this window moved (its own AC-EDMG suite, the R2616 fence-rows parent, "
    "the R2608 fence suite and the R2601 reconciliation suite) were re-run "
    "after the push and read PASS green=4 red=0 (qa/write-sensitive-rerun-"
    "R2621.log), so the green verdict and the document it regenerated hold on "
    "the tree a reader can clone. The export was refreshed AFTER the state "
    "append and after the fold (the R2449/R2433 ordering law) through "
    "src/os/export_R2621.py to 401786 bytes at tick 2623 with queue=CURRENT "
    "and queue_drifted=(none), check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO lines derived rather than typed, "
    "state_fold --check read FOLD-CLEAR at 75459B against the 78500B gate "
    "(margin 3041, 95 live lines) and ledger_lines --check read CLEAN with "
    "rounds_without_ledger=none and ledger_without_round=none. The debt gate "
    "now names reconcile-battery-R2621 first=yes at the pre-registered 642 "
    "suites / 4828 criteria, so the next window owes that battery on this "
    "committed tree BEFORE any further product byte."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = [" " * item_indent + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2621b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d"
          % (expected["tick"], after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
