"""R2677 push receipt: one honest log line, no tick advance."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
INDENT = 2

LINE = (
    "R2677 push and export: git push origin main read d4c50260..d39deed2 "
    "main -> main and git rev-parse read HEAD equal to origin/main at d39deed2 "
    "with an EMPTY git status, so the adopted verdict, the regenerated matrix, "
    "the write-sensitive evidence, the closed debt row, the opened successor and "
    "the closeout are all delivered; this receipt line lands in the follow-up "
    "commit it describes. The export was refreshed AFTER the state append "
    "(the R2449/R2433 ordering law) through the shipped driver "
    "src/os/export_R2635.py to 405214B at tick 2668 with queue=CURRENT and "
    "queue_drifted=(none), and check_export_consistency read pass=21 fail=0 "
    "VERDICT PASS with the three CEO-visible lines derived rather than typed. "
    "state_fold --check read FOLD-CLEAR at 65040B against the 78500B gate with "
    "margin 13460, 61 log lines and the archive present. The debt gate now "
    "names product-face-R2677 first=yes and NO battery, because this window "
    "moved no product src byte and the registry is unmoved at 655 suites / 4906 "
    "criteria re-measured by import, so the next window owes a PRODUCT face on "
    "queue head state/queue/tech.md:677 prefix AC-PNAH1."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * INDENT + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2677p_")
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
