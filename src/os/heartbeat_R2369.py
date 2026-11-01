"""heartbeat_R2369.py - append this round's heartbeat row (tick token included).

The five-silence scan reads the LAST non-blank line and matches "tick (\\d+)",
so the token is written into the line itself rather than as a second numeric
row. Read-back proved.

Usage: python src/os/heartbeat_R2369.py
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(REPO, "heartbeat.txt")

LINE = (
    "R2369 (tick 2369): verification then product - the battery ran first on "
    "the committed 74d94279 tree and read RUNNER PASS 495/495 suites plus "
    "controls 7/7 in 945.9s with criteria total 3946 EXACTLY as pre-registered "
    "(qa/reconcile-all-R2369.log), and the four follow-up sections PASS after "
    "the designed matrix FAIL and its regeneration to 495/3946 (47371B); then "
    "the claimed tech row AC-RTAB1 shipped residue_triage_append_batch, so "
    "several residue rounds are declared in one atomic write with the judge "
    "run before it, six criteria green twice plus four adjacent suites "
    "(qa/residue-triage-append-batch-R2369.log) and a live check reading the "
    "real declaration as TRIAGED with nothing to append; one measured gap row "
    "seeded (residue_batch_status_face) and the gauge stays FLOOR-MET 5/5 "
    "10/10 10/10."
)


def main():
    raw = io.open(PATH, "r", encoding="utf-8", newline="").read()
    if not raw.endswith("\n"):
        raw += "\n"
    text = raw + LINE + "\n"
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    back = io.open(PATH, "r", encoding="utf-8", newline="").read()
    last = [row for row in back.splitlines() if row.strip()][-1]
    ok = back == text and "tick 2369" in last
    print("HEARTBEAT appended readback=%s last=%r" % (ok, last[:60]))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())