"""R2722 receipt append: one line, no tick bump."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2722 write-sensitive receipt: the R2614 discipline was OWED because the R2721 "
    "launch window left no receipt line for the leg it fired, so the SAME fifteen "
    "suites R2709 pinned were re-run INDIVIDUALLY on the FINAL committed tree at HEAD "
    "befed0ed through the shipped SUITES registry and its own subprocess capture "
    "(utf-8 pipes, a 1200-second per-suite ceiling, cwd at each suite own directory); "
    "the set read SUMMARY PASS green=15 red=0 with every suite rc=0 "
    "(qa/write-sensitive-R2722.log, 14193B, utf-8 LF, header naming the leg window, "
    "the two commits under it and the tree it measured). qa_writer_census --check "
    "--dir qa then read flags=0 verdict=DRIFT-CLEAN, so the new evidence file needed "
    "NO baseline-add disposition and no drift was masked, and the export was "
    "re-derived afterwards to pick the receipt up in outs (rows=178 outs=299 "
    "bytes=408555 queue CURRENT).",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2722r_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok bytes=%d log_len=%d" % (after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
