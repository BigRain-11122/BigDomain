"""R2623 push receipt: ONE log line, no tick change."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINE = (
    "R2623 push and receipt: git push origin main SUCCEEDED "
    "(a7343636..40dfb0bb main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 40dfb0bb with an EMPTY git status after the commit, so "
    "the window is delivered and this receipt lands in the follow-up commit "
    "it describes. The write-sensitive set was re-run INDIVIDUALLY on that "
    "FINAL committed tree and every one read rc=0 - the export trio "
    "(os-status-export-writer-dialect-wire, os-queue-floor-export-face, "
    "os-export-consistency-queue-face pass=15 fail=0) and the six readability "
    "suites (patterns-label-readability, "
    "patterns-label-readability-render-consumer, "
    "patterns-non-label-text-readability, artifact-disk-text-readability, "
    "evidence-name-text-coverage, stamp-text-coverage, each SUITE PASS 6/6) - "
    "which is what makes the adopted green leg admissible beside the two "
    "commits that landed under it. The tenth name carried by the precedent, "
    "os-seq-stamped-never-logged, does not exist under that name in the "
    "642-row registry (measured by import), so nothing is claimed for it. "
    "Fold 683 and this append leave the state at 73842B against the 78500B "
    "gate with CANON-CLEAN off_indent=0, and the export was refreshed AFTER "
    "the state append through src/os/export_R2431.py to 401783B at tick 2625 "
    "with queue=CURRENT and queue_drifted=(none), where "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS (proposals=7/5, "
    "so the weekly quota is discharged). The debt gate now names "
    "product-face-R2623 first=yes on the queue head state/queue/tech.md:652 "
    "prefix AC-EDMH1, and no successor battery is owed because no product src "
    "byte moved and the registry is unmoved at 642 suites / 4828 criteria."
)


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + [LINE]
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = [" " * item_indent + json.dumps(LINE, ensure_ascii=False)]
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2623b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
