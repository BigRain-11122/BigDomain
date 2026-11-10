"""R2619 push and export receipt."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2619 push and export: git push origin main SUCCEEDED (4cc513e8..dc599288 main -> main) and git rev-parse read HEAD equal to origin/main at dc599288 with an EMPTY git status after the commit, so the whole window is delivered; this line lands in the follow-up commit it describes. The export was refreshed AFTER both state appends and after fold 679 (the R2449/R2433 ordering law) through src/os/export_R2431.py to 401277 bytes at tick 2620 with queue=CURRENT and queue_drifted=(none), and check_export_consistency read pass=21 fail=0 VERDICT PASS with the three CEO lines derived rather than typed. state_fold --check read FOLD-CLEAR at 72837B against the 78500B gate with margin 5663 and 93 log lines, and ledger_lines --check read CLEAN with rounds_without_ledger=none and ledger_without_round=none. The debt gate still names reconcile-battery-R2616 first=yes at its registered 641 suites / 4822 criteria with that leg LIVE at closeout (stream 175012B, 98 PASS suite rows, ZERO FAIL rows), so the next window ADOPTS the leg, closes the row only on a measured evidence file, and re-runs the write-sensitive suites on the FINAL committed tree before any verdict (the R2614 lesson).",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2619c_")
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
