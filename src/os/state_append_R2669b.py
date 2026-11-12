"""R2669 push receipt and the R2614 discipline re-run verdict."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2669 receipt: git push origin main read d0ee050c..aada4668 main -> main, and the R2614 discipline re-run of NINE write-sensitive suites on the FINAL committed tree aada4668 read rc=0 on every one (the export trio, the three readability suites and the three text-coverage suites) with VERDICT PASS failing=0 landed in qa/verify-reinsert-R2669.log through a python writer in utf-8 LF, so the R2665 battery verdict now stands unconditional rather than conditional; the ledger round-coverage suite named at R2614 still has NO registry row under that name, so it was not run and that substitution is named; NO successor battery is owed because this window moved no product src byte and the registry is unmoved at 653 suites / 4894 criteria.",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2669b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d" %
          (int(data["tick"]), after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
