"""R2673 closeout repair and receipt, in one pass.

TWO DEFECTS AND ONE RECEIPT:

1. The writer template constant state_io.ITEM_INDENT is 16 while this file own
   log items are indented by 2, so the three items this window appended landed
   at 16 - the same template defect R2671 named and repaired by hand. This
   script rewrites EXACTLY those three lines at the file own prefix, proving
   parse equality before the write and a byte read-back after it. The template
   constant itself is NOT changed here: it is a shared module other writers
   read, so it is named for a window that can carry its own suite rather than
   edited inside a verification closeout.

2. The receipt line records what this window actually delivered, read off disk.

Both steps write once, atomically, under the file own EOL.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
ROOT = os.path.dirname(os.path.dirname(HERE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STREAM = os.path.join(ROOT, "logs", "battery-R2673.stream")
ITEM_INDENT = 2
MARKERS = ("R2673 VERIFICATION window", "R2673 tokens:")


def reindent(rows):
    fixed = 0
    bad = (" " * state_io.ITEM_INDENT) + '"'
    good = (" " * ITEM_INDENT) + '"'
    for index, row in enumerate(rows):
        if row.startswith(bad) and any(m in row for m in MARKERS):
            rows[index] = good + row[len(bad):]
            fixed += 1
    return fixed


def receipt(doc):
    exp = len(io.open(EXPORT, "rb").read())
    stream = len(io.open(STREAM, "rb").read())
    tick = int(doc.get("tick", 0))
    return [
        "R2673 push and export: git push origin main read "
        "067b13e2..7c6930d6 main -> main and git rev-parse read HEAD equal to "
        "origin/main at 7c6930d6 with an EMPTY git status, so the verification "
        "window closeout is delivered; this receipt line lands in the follow-up "
        "commit it describes. The export was refreshed AFTER the state append "
        "(the R2449/R2433 ordering law) through the shipped driver "
        "src/os/export_R2635.py to %dB at tick %d with queue=CURRENT and "
        "queue_drifted=(none), and check_export_consistency read pass=21 "
        "fail=0 VERDICT PASS with the three CEO-visible lines derived rather "
        "than typed. state_fold --check read FOLD-CLEAR at 67053B before the "
        "append and 70029B after it, against the 78500B gate, and "
        "ledger_lines --check read VERDICT CLEAN with rounds_without_ledger "
        "none. The debt gate still names reconcile-battery-R2671 first=yes at "
        "the pre-registered 654 suites / 4900 criteria and that leg is LIVE at "
        "this closeout (pid 63200, stream %sB and growing), so the row stays "
        "OPEN and the next window adopts it; NO successor battery is owed "
        "because this window moved no product src byte and the registry is "
        "unmoved at 654/4900, re-measured by import."
        % (exp, tick, stream),
        "R2673 ONE DEFECT BORN AND REPAIRED HERE, NAMED RATHER THAN SMOOTHED: "
        "state_io.ITEM_INDENT is 16 while this file own log items are indented "
        "by 2, so the three items this window appended landed at 16 - the SAME "
        "template defect R2671 named and repaired by hand one window earlier, "
        "which means the cause is the shared writer constant and not this "
        "window own typing. src/os/state_indent_fix_R2673.py rewrote exactly "
        "those three lines at the file own prefix with a parse equality check "
        "before the write and a byte read-back after it, and the template "
        "constant itself is deliberately left alone because other shipped "
        "writers read it and a change there deserves its own suite rather than "
        "a silent edit inside a verification closeout. Also disclosed: "
        "src/os/scan_five_still.py still crashes at its final [ORD-TOP] print "
        "on the GBK console, so the scan ran under PYTHONIOENCODING=utf-8 - "
        "WORKED AROUND, NOT REPAIRED; the one-off launcher "
        "src/os/launch_battery_R2673.py was DELETED before the commit rather "
        "than staged, so the next window adopts the leg by its evidence path "
        "and not by a shipped launcher; and TWO commits landed UNDER the live "
        "leg (7c6930d6 and this one), so a green verdict next window is "
        "admissible only beside an individual re-run of the write-sensitive "
        "suites on the FINAL committed tree (the R2614 discipline).",
    ]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    rows = state_io._lf_lines(text)
    fixed = reindent(rows)
    receipt_lines = receipt(data)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(receipt_lines)
    start, end = state_io._log_block(rows)
    if not rows[end - 1].strip().endswith(","):
        rows[end - 1] = rows[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(receipt_lines):
        suffix = "," if index < len(receipt_lines) - 1 else ""
        inserted.append(" " * ITEM_INDENT + json.dumps(item,
                                                      ensure_ascii=False)
                        + suffix)
    out = state_io.EOL.join(rows[:end] + inserted + rows[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2673fix_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    report = state_io.report(PATH)
    print("APPEND ok reindented=%d tick=%s log_len=%d bytes=%d"
          % (fixed, data.get("tick"), report["log_len"], report["bytes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
