"""R2274 disclosure append: one honest row about the evidence retry.

The first evidence capture (qa/debt-close-R2274.log) was taken while the
suite's live leg probed a fixed item name, which this window then closed in
the live register - the suite measured 5/6 on the very register this window
had changed. The defect was in the TEST leg (a fixed probe), fixed by
deriving the probe from the live register; the module and every criterion
were untouched. The retry capture is the authoritative one. This helper
appends that disclosure to state.json and proves the payload grew by
exactly one row.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)

import state_io  # noqa: E402

ROW = (
    "R2274 disclosure (test-side defect, not a module or criterion defect): "
    "the first evidence capture qa/debt-close-R2274.log (1658B, two legs "
    "identical, five adjacent suites green) was taken while the suite live "
    "leg probed a FIXED item name, and this window then closed that very item "
    "in the live register through the new writer, so a later run of the same "
    "suite read 5/6 - the live leg was asserting a transient register fact "
    "rather than the law. The fix was in the test: the probe is now derived "
    "from the live register own open rows (and the leg degrades honestly to "
    "the unknown-item path when the register carries none), so no criterion "
    "was widened and no module code changed. The authoritative evidence is "
    "the retry capture qa/debt-close-R2274-retry.log (1658B, two legs "
    "identical digest, five adjacent suites green, one utf-8 LF single "
    "writer); the first capture is retained unchanged beside it, the same "
    "retry-naming convention R2238 pinned for correction reruns."
)


def main(argv):
    execute = "--execute" in argv
    raw = io.open(STATE, "rb").read().decode("utf-8")
    before = json.loads(raw)
    after = json.loads(raw)
    after["log"] = list(before["log"]) + [ROW]
    text = json.dumps(after, indent=2, ensure_ascii=True)
    canon = state_io.canon(text)
    if json.loads(canon) != after:
        raise SystemExit("ABORT canon moved the payload")
    if json.loads(canon)["log"][:-1] != before["log"]:
        raise SystemExit("ABORT existing rows moved")
    print("PLAN before=%dB after=%dB" % (len(raw.encode("utf-8")),
                                         len(canon.encode("utf-8"))))
    if not execute:
        return 0
    data = canon.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".disclose_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
    os.replace(temp, STATE)
    back = io.open(STATE, "rb").read()
    if back != data:
        raise SystemExit("ABORT read-back differs from the write")
    measured = state_io.layout(back.decode("utf-8"))
    print("WROTE bytes=%d log_items=%d layout_ok=%s count_ok=%s"
          % (len(back), measured["log_items"], measured["layout_ok"],
             measured["count_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))