"""R2524 correction append: record the post-follow-up evidence size.

The green leg was measured at 910866B BEFORE the four follow-up sections ran;
src/os/battery_followup.py then APPENDED its 1950B block to the same file, so
the delivered file reads 912816B. Both numbers are true of different moments
and the round log quoted only the first, which would read as a wrong size to
anyone who checks the file. This appends the measured fact rather than editing
the earlier sentence.

Same writer law as the closeout: proved load+dump round-trip, no reformat.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

ROW = (
    "2026-11-07 R2524 MEASURED CORRECTION, appended rather than edited into "
    "the row above: qa/reconcile-all-R2524-retry.log is 912816B as delivered, "
    "not the 910866B quoted for the green leg, because "
    "src/os/battery_followup.py appended its own 1950B block to the same file "
    "after that leg was measured - the appended block records the pre-append "
    "size itself (bytes=910866), so both numbers are true of their own moment "
    "and the difference is exactly the follow-up write. Re-read after the "
    "append: crlf=0, lone_cr=0, bom=False, six RUNNER PASS lines (one per leg "
    "and per section banner) and the closing line still VERDICT R2524 PASS "
    "failing=none. The results row already written into "
    "docs/status-export.json carries the green-leg figure; this line is the "
    "recorded correction rather than a silent rewrite.")


def raw():
    with io.open(STATE, "rb") as handle:
        data = handle.read()
    return data, json.loads(data.decode("utf-8"))


def dump(state):
    return json.dumps(state, indent=4, ensure_ascii=False) + "\n"


def main():
    data, state = raw()
    if dump(state).encode("utf-8").rstrip(b"\n") != data.rstrip(b"\n"):
        raise SystemExit("REFUSE: file does not round-trip through load+dump")
    state["log"] = list(state["log"]) + [ROW]
    out = dump(state).encode("utf-8")
    with io.open(STATE, "wb") as handle:
        handle.write(out)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    if back != out:
        raise SystemExit("REFUSE: read-back differs")
    check = json.loads(back.decode("utf-8"))
    print("APPENDED bytes %d->%d log=%d tick=%d tail_ok=%s"
          % (len(data), len(out), len(check["log"]), check["tick"],
             check["log"][-1] == ROW))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())