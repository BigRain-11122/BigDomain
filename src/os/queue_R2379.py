# queue_R2379.py - stamp the claimed tech row and seed one measured gap
# One write, predicted size proved by re-read, no temp residue.
# Pure ASCII, stdlib only, no clock, no network.

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

HEAD = "- [ ] P2 tech seed (R2369, from this window own measured pain)"
STAMP = "- [x] [done 2026-11-02 R2379] P2 tech seed (R2369"

SEED = (
    "- [ ] P2 tech seed (R2379, from this window own measured gap): "
    "`src/os/single_append_status_face.py` - the batch writer now names the "
    "live status of every residue round, but the SINGLE-entry writer still "
    "does not: residue_triage_append.py --check prints the rounds awaiting an "
    "entry and no status at all, so a one-round --append costs exactly the "
    "refused call the batch CLI no longer costs. Measured this window: the "
    "face was wired into residue_triage_append_batch.check only, and the "
    "batch suite AC-RTAB5 shows the single CLI still answering without "
    "statuses. Product: the single writer --check asks the same face and "
    "names the round live status, and a round outside the residue reads "
    "NOT-RESIDUE. Criteria AC-SASF1..AC-SASF6 pre-registered HERE BEFORE any "
    "code: AC-SASF1 the status of the asked round is residue_batch_status_"
    "face's reading (patching that face moves the printed status) and no "
    "second residue scan is written; AC-SASF2 --check names the asked round "
    "with its live status so a single --append is composed from one call; "
    "AC-SASF3 a round outside the live residue reads NOT-RESIDUE with its own "
    "code rather than an invented status; AC-SASF4 every existing --append "
    "refusal code and printed line stays byte-identical and the append path "
    "never calls the face; AC-SASF5 CLI exits 0/2/3 with a byte-stable --json "
    "over the pinned report keys; AC-SASF6 pure ASCII, stdlib only, no clock, "
    "no network, plus its own reconcile label. Five anchors zero-occupancy at "
    "HEAD 2026-11-02: single_append_status_face, AC-SASF, E_SASF, "
    "os-single-append-status-face, test_single_append_status_face."
)


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="\n") as handle:
        before = handle.read()
    lines = before.split("\n")
    hits = [index for index, line in enumerate(lines)
            if line.startswith(HEAD)]
    if len(hits) != 1:
        sys.stdout.write("E_QR2379_HEAD: %d rows start with the seed head\n"
                         % len(hits))
        return 2
    index = hits[0]
    lines[index] = lines[index].replace("- [ ]", STAMP, 1)
    while lines and lines[-1] == "":
        lines.pop()
    lines.append("")
    lines.append(SEED)
    after = "\n".join(lines) + "\n"
    predicted = len(after.encode("utf-8"))
    payload = after.encode("utf-8")
    temp = QUEUE + ".tmp-q2379"
    with open(temp, "wb") as handle:
        handle.write(payload)
    os.replace(temp, QUEUE)
    with open(QUEUE, "rb") as handle:
        back = handle.read()
    ok = back == payload
    sys.stdout.write("QUEUE R2379 rows=%d stamped=%d seed_bytes=%d "
                     "before=%dB after=%dB predicted=%d readback=%s\n"
                     % (len(lines), 1, len(SEED.encode("utf-8")),
                        len(before.encode("utf-8")), len(back), predicted,
                        "ok" if ok else "MISMATCH"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())