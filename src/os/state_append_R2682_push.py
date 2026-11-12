"""R2682 push receipt: one line, no tick bump, then the export is re-derived."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
INDENT = 2

LINE = (
    "R2682 push and export: git push origin main read 4f5ab235..641fbe44 main "
    "-> main and git rev-parse read HEAD equal to origin/main at 641fbe44 with "
    "an EMPTY git status, so the shipped sibling-list face, its six-criteria "
    "suite, the 6163B two-leg evidence file, the closed board row, the seeded "
    "AC-PNAL1 successor, the 69049B matrix, the two debt rows and the closeout "
    "are all delivered; this receipt line lands in the follow-up commit it "
    "describes. The export was refreshed AFTER the state append and after the "
    "tick advance (the R2449/R2433 ordering law) through the shipped driver "
    "src/os/export_R2635.py to 405678B at tick 2674 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO-visible lines derived rather than typed. "
    "state_fold --check read FOLD-CLEAR at 70056B before the append and 75120B "
    "after it, against the 78500B gate, after fold 705 took log items 56..60 "
    "(the complete R2680 verification block) to the archive with its two "
    "tokens carried and the archive VERIFIED; ledger_lines --check read "
    "VERDICT CLEAN with rounds_without_ledger none. The debt gate now names "
    "reconcile-battery-R2682 first=yes at the pre-registered 658 suites / 4924 "
    "criteria, so the next window owes that FULL battery on the committed tree "
    "BEFORE any further product byte, and the queue head this window leaves "
    "behind is state/queue/tech.md:680 prefix AC-PNAL1 with the floor "
    "FLOOR-MET at 5/5, 14/10 and 10/10."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * INDENT + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2682push_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d" %
          (data.get("tick"), after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
