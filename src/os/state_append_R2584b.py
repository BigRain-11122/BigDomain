"""R2584b state append: the push-and-export receipt line, same proved layout."""

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(ROOT)
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINE = (
    "2026-11-09 R2584 push and export: git push origin main SUCCEEDED "
    "(c9f027ae..675ee786 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 675ee786 with an empty git status after the commit, so the whole "
    "window is delivered; this line lands in the follow-up commit it describes. The "
    "export was refreshed AFTER the state append and after the fold (the R2449/R2433 "
    "ordering law) through this round own driver src/os/export_R2584.py to 395208 "
    "bytes at tick 2584 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS with the three CEO "
    "lines derived rather than typed; state_fold --check read FOLD-CLEAR at 76816B "
    "against the 78500B gate with margin 1684 and 78 log lines, and ledger_lines "
    "--check read CLEAN after the fold. The debt gate now names product-face-R2584 "
    "first=yes on the queue head state/queue/tech.md:617 prefix AC-PNAA1, and no "
    "battery is owed because the registry is unmoved at 622 suites / 4708 criteria "
    "and no product src byte moved, so the next window owes that product face before "
    "any battery."
)


def main(argv):
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    for indent in (1, 2):
        for trail in ("", "\n"):
            if json.dumps(state, indent=indent, ensure_ascii=False) + trail == text:
                print("LAYOUT PROVED indent=%d trail=%r bytes=%d" % (indent, trail, len(raw)))
                layout = (indent, trail)
                break
        else:
            continue
        break
    else:
        print("E_R2584B_BAD_LAYOUT")
        return 3
    block = state.setdefault("log", [])
    start = len(block)
    block.append(LINE)
    new_text = json.dumps(state, indent=layout[0], ensure_ascii=False) + layout[1]
    check = json.loads(new_text)
    if check["log"][start:] != [LINE] or len(check["log"]) != len(block):
        print("E_R2584B_ROUNDTRIP")
        return 4
    execute = "--execute" in argv
    print("APPEND log %d -> %d lines, bytes %d -> %d, execute=%s"
          % (start, len(block), len(raw), len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2584b_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(new_text.encode("utf-8"))
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = json.load(open(STATE, encoding="utf-8"))
    print("READBACK log_lines=%d ok=%s" % (len(back["log"]), back["log"][start:] == [LINE]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))