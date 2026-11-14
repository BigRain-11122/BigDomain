"""state_append_R2744b - record the refused fold through the canonical writer."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2744

LINES = [
    "R2744 THE FOLD WAS ATTEMPTED, REFUSED AND ROLLED BACK, and the refusal is a MEASURED "
    "TWO-TOOL CONFLICT rather than a defect this window could repair safely at closeout: "
    "src/os/state.json stood at 80939B against the 78500B waterline (margin -2439B, 88 items, "
    "CANON-CLEAN off_indent=0), logs_toolkit fold --round R2744 --fold-no 13 --window-tail 6 "
    "refused with E_STATE_LAYOUT PS item-line layout mismatch and hinted at logs_toolkit eol "
    "--fix-indent, that hint was run first as a dry run and then with --execute (it self-verified "
    "content_eq json_eq verify_pass all true, 80939B -> 82185B, repaired_lines 89), and "
    "state_io --check then read CANON-DRIFT off_indent=88 on the SAME file. So the fold caliber "
    "wants 4-space log item lines while the write_document caliber R2738 shipped wants 2-space, "
    "and both shipped tools cannot be right. The pre-surgery bytes were restored from a temp copy "
    "and state_io reads CANON-CLEAN 80939B off_indent=0 again, so nothing was folded and nothing "
    "was left half-written. OWED to the next window that touches this file: align the fold caliber "
    "with the canonical writer (or teach fold to accept 2-space items), then fold the R2744 "
    "window; the waterline stays RED at -2439B and is declared rather than papered over. Named "
    "beside it: the R2743 window left two of its own log items at 4-space indent inside a "
    "2-space document, which is the shape that made the fold refuse in the first place.",
]


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    before = len(data["log"])
    data["log"].extend(LINES)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    ok = (back.get("tick") == TICK
          and len(back.get("log") or []) == before + len(LINES)
          and back["log"][-len(LINES):] == LINES)
    sys.stdout.write("APPENDED tick=%s log %d->%d ok=%s\n"
                     % (back.get("tick"), before, len(back.get("log") or []), ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
