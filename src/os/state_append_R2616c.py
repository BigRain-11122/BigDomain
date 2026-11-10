"""R2616 push and export receipt."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2616 push and export: git push origin main SUCCEEDED (ea808bba..4ed69b9a main -> main) and git rev-parse read HEAD equal to origin/main at 4ed69b9a with an EMPTY git status after the commit, so the whole window is delivered; this line lands in the follow-up commit it describes. The export was refreshed AFTER the two state appends and after both folds (the R2449/R2433 ordering law) through src/os/export_R2431.py to 401637 bytes at tick 2619 with queue=CURRENT and queue_drifted=(none), and check_export_consistency read pass=21 fail=0 VERDICT PASS with the three CEO lines DERIVED - current from this round own opening item, latest naming the four qa artifacts with their byte sizes, next naming reconcile-battery-R2616 inside a 48h window. state_fold --check read FOLD-CLEAR at 77038B against the 78500B gate with margin 1462 and 94 log lines, ledger_lines --check read CLEAN with no round without a ledger line and no ledger line without a round, the writer census read DRIFT-CLEAN with flags=0, and the five export suites this window touched were re-run green by measurement (queue-face 15/15, driver-queue-face 6/6, self-drive-health 6/6, health-verdict 6/6, publish-from-import-law 8 passes 0 fails). The debt gate now names reconcile-battery-R2616 first=yes at 641 suites / 4822 criteria, so the next window owes that battery on this committed tree BEFORE any further product byte.",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    item_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith('"') and not stripped.startswith('"log"'):
            item_indent = len(line) - len(stripped)
            break
    if item_indent is None:
        print("REFUSED no item line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * item_indent +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2616c_")
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
