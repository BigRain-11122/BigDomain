"""R2687 push receipt: one honest log line, no tick move.

Indent hard-coded at two spaces: state_io.ITEM_INDENT is 16 against this file's 2.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
INDENT = 2


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    lines = [
        "R2687 push and export: git push origin main read fd5857d7..0ab0cf0a "
        "main -> main and git rev-parse read HEAD equal to origin/main at "
        "0ab0cf0a with an EMPTY git status, so the measured red leg, the "
        "birth-site repair that was already committed under it, the three-suite "
        "write-sensitive evidence, the state append and the re-derived export "
        "are all delivered; this receipt line lands in the follow-up commit it "
        "describes. The export was refreshed AFTER the state append and after "
        "the tick advance (the R2449/R2433 ordering law) through the shipped "
        "driver src/os/export_R2635.py to 405885B at tick 2679 with "
        "queue=CURRENT and queue_drifted=(none), and check_export_consistency "
        "read pass=21 fail=0 VERDICT PASS with the three CEO-visible lines "
        "derived rather than typed. state_fold --check read FOLD-CLEAR at "
        "44909B before this window append against the 78500B gate, and the "
        "append landed at a predicted and measured 57465B leaving margin 21035, "
        "so no fold was owed or run. THE RETRY LEG WAS STILL LIVE AND GROWING "
        "AT THIS CLOSEOUT AND THAT IS THE HONEST STATE OF THE ROUND: pid 75488 "
        "with its reconcile_all child 89156 alive by command line, "
        "logs/battery-R2686-retry.stream at 577730B carrying 329 PASS suite "
        "rows and ZERO FAIL suite rows with no RUNNER and no BATTERY closing "
        "line, against a full leg that has measured 1600-4100s here, so "
        "reconcile-battery-R2685 stays OPEN at its registered 659 suites / "
        "4930 criteria and the next window ADOPTS it by its evidence path "
        "qa/reconcile-all-R2686-retry.log rather than relaunching, then lands "
        "the write-sensitive set on the FINAL committed tree before any verdict "
        "(the R2614 discipline, which this round closeout makes owed). The debt "
        "gate still names reconcile-battery-R2685 first=yes and the queue head "
        "this window leaves behind is state/queue/tech.md line 681 prefix "
        "AC-PNAO1 with claimable 14 and the queue floor FLOOR-MET 5/5, 14/10, "
        "10/10.",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * INDENT + json.dumps(item, ensure_ascii=False) +
                        suffix)
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    if "--dry" in sys.argv:
        print("DRY run, nothing written")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2687p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok bytes=%d log_len=%d" % (after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
