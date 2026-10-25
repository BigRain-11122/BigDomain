"""Correct a false claim written into the R2119 state log by this same
window (honesty law): the decisions watermark's blob_bytes/sha256 were
NOT stale - the earlier 144258 reading came from a PowerShell pipeline
that re-encoded the blob, so the byte count was a character count. The
record was only advanced to the new HEAD and the bytes/sha256 are
identical. ASCII source."""

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

OLD_1 = ("- the drifted blob_bytes/sha256 fields were re-recorded from"
         " HEAD 5373b7d9 this window;")
NEW_1 = ("- the commit sha advanced twice more (5373b7d9 then b2739176)"
         " and the watermark was re-recorded to b2739176 with the SAME"
         " blob_bytes 222683 and sha256 f94a284c;")
OLD_2 = (" Also refreshed the decisions watermark v2 record to HEAD"
         " 5373b7d9 (144258 bytes, sha256 cbc8d872) since the stored"
         " bytes/sha were stale.")
NEW_2 = (" Also corrected an in-window measurement error: a PowerShell"
         " pipeline re-encoded the decisions blob, so the 144258 reading"
         " was a character count, not bytes - the stored 222683/f94a284c"
         " were right all along and the watermark never needed repair.")


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    log = state.get("log", [])
    changed = 0
    for i in range(len(log) - 3, len(log)):
        if i < 0:
            continue
        text = log[i]
        if OLD_1 in text:
            text = text.replace(OLD_1, NEW_1)
            changed += 1
        if OLD_2 in text:
            text = text.replace(OLD_2, NEW_2)
            changed += 1
        log[i] = text
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(state, ensure_ascii=False, indent=1) + "\n")
    print("replacements=%d" % changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())