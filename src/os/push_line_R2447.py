"""push_line_R2447 - replace this round's pending push line with the measured
result, then leave the document otherwise byte-identical.

One atomic replace with a byte read-back; refuses if the pending line is absent
or already resolved. Run with --execute to write.
"""

import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
PENDING = ("2026-11-05 R2447 push: pending at closeout write; recorded after "
           "the push attempt so the line states what actually happened.")
RESOLVED = ("2026-11-05 R2447 push: git push origin main SUCCEEDED this window "
            "(54535c88..431e17df main -> main), so the R2447 closeout commit is "
            "delivered to origin and nothing is left staged.")


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    log = payload["log"]
    hits = [i for i, line in enumerate(log) if line == PENDING]
    if len(hits) != 1:
        raise SystemExit("E_PLR2447_PENDING hits=%d" % len(hits))
    index = hits[0]
    if not execute:
        print("DRY RUN index=%d before=%dB" % (index, len(raw)))
        return 0
    log[index] = RESOLVED
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_PLR2447_PAYLOAD canon moved the payload")
    data = canonical.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2447-push-")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(STATE, "rb").read()
    if back != data:
        raise SystemExit("E_PLR2447_BACK read-back does not match the write")
    layout = state_io.layout(canonical)
    print("STATE index=%d bytes=%d -> %d layout_ok=%s crlf=%d"
          % (index, len(raw), len(back), layout["layout_ok"], layout["crlf"]))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))