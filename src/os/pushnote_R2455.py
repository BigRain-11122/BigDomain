"""Append the R2455 push line to the state log (append-only evidence)."""

import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINE = ("2026-11-05 R2455 push: git push origin main SUCCEEDED this window "
        "(b216bfa9..e56c34dd main -> main) and git rev-parse read HEAD equal "
        "to origin/main at e56c34dd, so the R2455 verification commit is "
        "delivered and nothing is left staged. The export was re-derived and "
        "the queue block re-applied through the shipped gate AFTER this state "
        "append (the R2449 ordering law), so the published document carries "
        "this line rather than predating it.")


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if any("R2455 push:" in item for item in payload["log"]):
        raise SystemExit("E_R2455PUSH_ALREADY present")
    if not execute:
        print("DRY RUN log_len=%d" % (len(payload["log"]) + 1))
        return 0
    payload["log"].append(LINE)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2455PUSH_PAYLOAD canon moved the payload")
    folder = os.path.dirname(STATE)
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2455push-")
    data = canonical.encode("utf-8")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    if open(STATE, "rb").read() != data:
        raise SystemExit("E_R2455PUSH_BACK read-back mismatch")
    print("STATE bytes=%d log_len=%d" % (len(data), len(payload["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))