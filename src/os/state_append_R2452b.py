"""state_append_R2452b - one honest line after the closeout.

The export driver for this round (export_R2431 module) does not carry the
queue section, so the refresh left docs/status-export.json STALE against the
live queue floor and the shipped gate wire was needed to land it (STALE ->
CURRENT). The state log is append-only evidence, so the correction is a line
rather than a rewrite.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINE = (
    "2026-11-05 R2452 post-closeout measurement, appended rather than edited "
    "in: after export_R2452 refreshed the document, "
    "queue_floor_export_face --check read STALE on the live section "
    "(claimable=5,10,10), because the round export driver derives do/latest/"
    "next/results but does not apply the queue face - so a CEO-visible "
    "document can be freshly re-derived and still carry a stale queue block. "
    "Landed through the shipped gate wire (QUEUE EXPORT GATE verdict=WRITTEN "
    "gate=CURRENT bytes=104879 drifted=(none)), after which the face reads "
    "CURRENT and check_export_consistency reads pass=21 fail=0 VERDICT PASS. "
    "The gate and the face both did their job; what was missing is a caller in "
    "the export driver, and that gap is named here for the next window rather "
    "than quietly worked around."
)


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["log"] and payload["log"][-1] == LINE:
        raise SystemExit("E_R2452B_ALREADY append line already present")
    if not execute:
        print("DRY RUN tick=%s appends=1 bytes_before=%d"
              % (payload["tick"], len(raw)))
        return 0
    payload["log"].append(LINE)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2452B_PAYLOAD canon moved the payload")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2452b-state-")
    with os.fdopen(handle, "wb") as sink:
        sink.write(canonical.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    if back != canonical.encode("utf-8"):
        raise SystemExit("E_R2452B_BACK read-back does not match the write")
    layout = state_io.layout(canonical)
    print("STATE bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (len(back), len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))