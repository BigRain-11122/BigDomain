"""R2714 push receipt: append the delivered line, no tick change."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2714 push and receipt: git push origin main read ed13c1e9..2cf70f8b main "
    "-> main and git rev-parse read HEAD equal to origin/main at 2cf70f8b, so the "
    "shipped face src/os/evidence_utf8_capture.py, its six-criteria suite, the "
    "registry row os-evidence-utf8-capture(6) taking the tree from 667 suites / "
    "4978 criteria to 668 / 4984, the restamped matrix at 70651 bytes and 668 "
    "rows, the closed tech row 689 with the seeded AC-EBOM1..AC-EBOM6 row, the "
    "debt close plus the two appends with the disclosed first=yes flag "
    "correction, and the refreshed export at tick 2707 are all delivered; this "
    "receipt line lands in the follow-up commit it describes. NO battery verdict "
    "is claimed: reconcile-battery-R2714 is registered first=yes at the "
    "pre-registered 668 suites / 4984 criteria and the NEXT window runs it on a "
    "committed tree, measuring the target by import before the launch and "
    "keeping a red leg as evidence.",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2714p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok bytes=%d log_len=%d tick=%s" %
          (after["bytes"], after["log_len"], data.get("tick")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
