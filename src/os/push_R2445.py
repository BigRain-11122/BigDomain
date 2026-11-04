"""push_R2445 - rewrite this window's push line with what actually happened."""

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
    "2026-11-04 R2445 push: git push origin main SUCCEEDED this window "
    "(15719180..3b9534f8 main -> main), so the birth-site matrix repair "
    "2ed31668 and the R2445 closeout commit 3b9534f8 are delivered to origin "
    "and nothing is left staged. The log fold (fold 2445, items 1..47 at a "
    "true round-block boundary) landed at its predicted 54128B against a "
    "78500B gate and the four residue rounds it created "
    "(R2432/R2434/R2436/R2438) were spliced through the shipped batch channel "
    "to TRIAGED 275/275, with the four ledger suites and the triage suite "
    "re-run green afterwards.")


def main(execute):
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    state = json.loads(raw.decode("utf-8"))
    hits = [i for i, line in enumerate(state["log"])
            if line.startswith("2026-11-04 R2445 push:")]
    if len(hits) != 1:
        raise SystemExit("E_R2445_PUSH expected 1 push line, found %d"
                         % len(hits))
    state["log"][hits[0]] = LINE
    text = json.dumps(state, ensure_ascii=False, indent=2)
    canon = state_io.canon(text)
    if json.loads(canon) != state:
        raise SystemExit("E_R2445_PUSH canon moved the payload")
    if not execute:
        print("DRY RUN line=%d bytes=%d" % (hits[0], len(canon.encode())))
        return 0
    handle, temp = tempfile.mkstemp(dir=BASE, prefix=".r2445-push-")
    with os.fdopen(handle, "wb") as sink:
        sink.write(canon.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    with io.open(STATE, "rb") as back:
        done = back.read()
    print("STATE bytes=%d readback=%s"
          % (len(done), done == canon.encode("utf-8")))
    layout = state_io.layout(canon)
    print("layout_ok=%s crlf=%d bare_lf=%d"
          % (layout["layout_ok"], layout["crlf"], layout["bare_lf"]))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))