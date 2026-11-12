"""R2675 receipt append: one push/export receipt line plus one tick."""

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
    "R2675 push and export: git push origin main read 32badef3..e41fd647 main "
    "-> main and git rev-parse read HEAD equal to origin/main at e41fd647 with "
    "an EMPTY git status, so the shipped face, its suite, the limits probe, the "
    "board row, the seeded successor, the regenerated matrix and the two debt "
    "rows are all delivered; this receipt line lands in the follow-up commit it "
    "describes. The export was refreshed AFTER the state append (the "
    "R2449/R2433 ordering law) through the shipped driver "
    "src/os/export_R2635.py to 405164B at tick 2664 with queue=CURRENT and "
    "queue_drifted=(none), check_export_consistency read pass=21 fail=0 VERDICT "
    "PASS with the three CEO-visible lines derived rather than typed, "
    "state_fold --check read FOLD-CLEAR after fold 704 and ledger_lines --check "
    "read rounds_without_ledger none. The debt gate names "
    "reconcile-battery-R2675 first=yes at the pre-registered 655 suites / 4906 "
    "criteria, so the next window owes that FULL battery on the committed tree "
    "BEFORE any further product byte, and the queue head this window leaves "
    "behind is state/queue/tech.md:676 prefix AC-PNAH1."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
    expected["tick"] = tick + 1
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = " " * INDENT + json.dumps(LINE, ensure_ascii=False)
    old_tick = '"tick": %d,' % tick
    new_tick = '"tick": %d,' % (tick + 1)
    bumped = []
    seen = 0
    for row in doc_lines:
        if row.strip() == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + [inserted] + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2675r_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("RECEIPT ok tick=%d bytes=%d log_len=%d" %
          (tick + 1, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
