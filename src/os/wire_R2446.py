"""wire_R2446 - record the real push result in the R2446 state log line."""

import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
PENDING = ("2026-11-04 R2446 push: pending at closeout write; recorded after "
           "the push attempt so the line states what actually happened.")
FINAL = ("2026-11-04 R2446 push: git push origin main SUCCEEDED this window "
         "(624fd3fa..84a242b3 main -> main), so the R2446 product commit "
         "b48fa646 and the R2446 closeout commit 84a242b3 are delivered to "
         "origin and nothing is left staged.")


def main():
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    hits = [i for i, line in enumerate(payload["log"]) if line == PENDING]
    if len(hits) != 1:
        raise SystemExit("E_WIRE_R2446 expected one pending line, found %d"
                         % len(hits))
    payload["log"][hits[0]] = FINAL
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_WIRE_R2446 canon moved the payload")
    data = canonical.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2446-wire-")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    if back != data:
        raise SystemExit("E_WIRE_R2446 read-back does not match")
    layout = state_io.layout(canonical)
    print("WIRED line=%d bytes=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (hits[0], len(back), layout["layout_ok"], layout["crlf"],
             layout["bare_lf"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())