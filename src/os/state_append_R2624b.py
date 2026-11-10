"""R2624 push and export receipt: one log line, one tick.

Lands AFTER the commit it describes, which is why it is a second append.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2624 push and export: git push origin main SUCCEEDED (f271f7fc.."
    "3a4deb07 main -> main) and git rev-parse read HEAD equal to origin/main "
    "at 3a4deb07 with an EMPTY git status after the commit, so the whole "
    "window is delivered and this receipt lands in the follow-up commit it "
    "describes. Fold 684 moved log items 91..96 (the complete R2623 "
    "verification-round block ending on its push and receipt line) into the "
    "archive at a true round-block boundary, 75511B -> 69705B with the "
    "archive VERIFIED after a dry run that agreed exactly on the window and "
    "the byte count; the append then took the file to 75563B and state_fold "
    "--check reads FOLD-CLEAR against the 78500B gate (margin 2937, 96 log "
    "lines) while ledger_lines --check reads CLEAN with no round without a "
    "ledger and no ledger without a round. The export was refreshed AFTER the "
    "state append and after the fold through src/os/export_R2431.py to 402230 "
    "bytes at tick 2626 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS "
    "(proposals=7/5, so the weekly quota stays discharged) with its three CEO "
    "lines derived rather than typed. The debt gate now names "
    "reconcile-battery-R2624 first=yes at the pre-registered 643 suites / "
    "4834 criteria, so the next window owes that battery on this committed "
    "tree BEFORE any further product byte, and the product face behind it is "
    "the queue head state/queue/tech.md:653 prefix AC-EDMI1.",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
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
    inserted = [" " * item_indent + json.dumps(item, ensure_ascii=False) + ","
                for item in LINES[:-1]]
    inserted.append(" " * item_indent
                    + json.dumps(LINES[-1], ensure_ascii=False))
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    out = _retick(out, data["tick"], expected["tick"])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2624b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


def _retick(text, old, new):
    needle = '"tick": %d' % int(old)
    if needle not in text:
        raise SystemExit("REFUSED tick field not found as %r" % needle)
    return text.replace(needle, '"tick": %d' % int(new), 1)


if __name__ == "__main__":
    sys.exit(main())
