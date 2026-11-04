"""R2453b: append the push confirmation line to the state log.

One atomic replace with a byte read-back. The export is refreshed by its own
driver afterwards (the R2449 ordering law), never from here.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINE = (
    "2026-11-05 R2453 push: git push origin main SUCCEEDED this window "
    "(4e2d8535..0d1040dc main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 0d1040dc, so the R2453 verification commit is delivered "
    "and nothing is left staged. The self-heal check measured BigDomain-OSLoop "
    "present with Principal.LogonType reading InteractiveToken, unchanged and "
    "still carried as the stale row loop-s4u-reconcile because this session is "
    "unelevated."
)


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if any("R2453 push:" in item for item in payload["log"]):
        raise SystemExit("E_R2453B_LOG already present")
    payload["log"].append(LINE)
    canonical = state_io.canon(
        json.dumps(payload, ensure_ascii=False, indent=2))
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2453B_PAYLOAD canon moved the payload")
    print("DRY RUN state %dB -> %dB log_len=%d"
          % (len(raw), len(canonical.encode("utf-8")), len(payload["log"])))
    if not execute:
        return 0
    import tempfile
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2453b-state-")
    data = canonical.encode("utf-8")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    if open(STATE, "rb").read() != data:
        raise SystemExit("E_R2453B_BACK read-back mismatch")
    print("STATE bytes=%d" % len(data))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))