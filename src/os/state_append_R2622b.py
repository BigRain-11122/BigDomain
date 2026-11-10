"""R2622 push receipt: ONE log line, no tick change.

The tick belongs to the round, not to its receipt, so this writer appends the
closeout reading without moving it.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2622 push, fold and export receipt: git push origin main SUCCEEDED "
    "(406ad940..f53fad0a main -> main) and git rev-parse read HEAD equal to "
    "origin/main at f53fad0a with an EMPTY git status after the commit, so "
    "the whole window is delivered and this receipt lands in the follow-up "
    "commit it describes. The leg was re-read a third time BEFORE the commit "
    "and reads LIVE at pid 59736 with 111 PASS suite rows, ZERO FAIL rows, "
    "201493 stream bytes and 412s elapsed, with qa/reconcile-all-R2622.log "
    "still absent because the single writer only writes at the end - so the "
    "row reconcile-battery-R2621 STAYS OPEN at its registered 642 suites / "
    "4828 criteria and the next window ADOPTS this pid 59736 leg, closing the "
    "row only against a measured evidence file, and re-runs the write-"
    "sensitive suites on the FINAL committed tree before any verdict (the "
    "R2614 lesson). FOLD AND LAYOUT, both through shipped faces: fold 682 ran "
    "over items 89..96 (the complete R2621 product-round block ending on its "
    "push line) after a dry run whose prediction agreed exactly, "
    "81510B -> 72621B with archive VERIFIED, layout AGREE and 8 tokens "
    "preserved verbatim; state_io --check THEN read CANON-DRIFT with "
    "off_indent=95 - EVERY live item sat at two spaces instead of the "
    "canonical sixteen, a drift this window INHERITED rather than caused - so "
    "state_io --fix --execute restored the canon to 73951B and --check then "
    "read CANON-CLEAN off_indent=0, leaving state_fold --check FOLD-CLEAR at "
    "73951B against the 78500B gate with margin 4549 and 95 live lines. The "
    "export was refreshed AFTER the state append and after fold 682 through "
    "src/os/export_R2431.py to 401754 bytes at tick 2624 with queue=CURRENT "
    "and queue_drifted=(none), and check_export_consistency read pass=21 "
    "fail=0 VERDICT PASS (proposals=7/5, so the weekly quota is discharged)."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
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
    inserted = [" " * item_indent + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2622b_")
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


if __name__ == "__main__":
    sys.exit(main())
