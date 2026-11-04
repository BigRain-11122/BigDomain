"""One-off: append the R2449 push result so the closeout line states what
actually happened, then leave the tree ready for one commit."""
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
LINE = ("2026-11-05 R2449 push: git push origin main SUCCEEDED this window "
        "(31a30fd5..0e367aff main -> main), so the R2449 closeout commit "
        "0e367aff is delivered to origin and nothing is left staged. The "
        "self-heal check measured BigDomain-OSLoop present with "
        "Principal.LogonType reading InteractiveToken, unchanged and still "
        "carried as the stale row loop-s4u-reconcile because this session is "
        "unelevated.")


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if any(line.startswith("2026-11-05 R2449 push:") for line in payload["log"]):
        print("ALREADY PRESENT")
        return 0
    payload["log"].append(LINE)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2449P_PAYLOAD canon moved the payload")
    if not execute:
        print("DRY RUN bytes=%d" % len(canonical.encode("utf-8")))
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2449p-")
    data = canonical.encode("utf-8")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    print("WRITTEN bytes=%d readback=%s" % (len(back), back == data))
    return 0 if back == data else 1


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))