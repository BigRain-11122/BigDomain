"""state_append_R2452c - record the delivered push and refresh the export last.

The R2449 ordering law: refresh the export AFTER every state append, never
before, or check_export_consistency reads a stale self_drive count.
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
    "2026-11-05 R2452 push: git push origin main SUCCEEDED this window "
    "(05e6a47e..a0c44523 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at a0c44523, so the R2452 product commit is delivered and "
    "nothing is left staged. The self-heal check measured BigDomain-OSLoop "
    "present with Principal.LogonType reading InteractiveToken, unchanged and "
    "still carried as the stale row loop-s4u-reconcile because this session is "
    "unelevated."
)


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["log"] and payload["log"][-1] == LINE:
        raise SystemExit("E_R2452C_ALREADY append line already present")
    if not execute:
        print("DRY RUN tick=%s appends=1 bytes_before=%d"
              % (payload["tick"], len(raw)))
        return 0
    payload["log"].append(LINE)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2452C_PAYLOAD canon moved the payload")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2452c-state-")
    with os.fdopen(handle, "wb") as sink:
        sink.write(canonical.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    if back != canonical.encode("utf-8"):
        raise SystemExit("E_R2452C_BACK read-back does not match the write")
    print("STATE bytes=%d log_len=%d" % (len(back), len(payload["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))