"""heartbeat_R2373.py - append this round's heartbeat row (tick token included).

The five-silence scan reads the LAST non-blank line and matches "tick (\\d+)",
so the token is written into the line itself rather than as a second numeric
row (the R2367 shape defect). Read-back proved.

Usage: python src/os/heartbeat_R2373.py
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(REPO, "heartbeat.txt")

LINE = (
    "2026-11-02 R2373 OSLoop tick 2373: the battery ran first on the committed "
    "tree and its FIRST leg was red on evidence, not code (498/499 suites, "
    "reconcile-daily-census cd7 DRIFT-FLAG) because the R2372 live evidence had "
    "six CRLF lines inside a file the census reads as one utf-8 LF dialect; "
    "repaired at the birth site with a transport-EOL normalisation in its own "
    "writer, file regenerated with the payload intact, census DRIFT-CLEAN with "
    "the baseline untouched, and the retry read RUNNER PASS 499/499 with "
    "criteria 3970 exactly as pre-registered (qa/reconcile-all-R2373-retry.log), "
    "matrix 47836B, VERDICT R2373 PASS. Then the runner contract finally had "
    "ONE usage renderer: contract_usage_renderer owns the required keys, the "
    "flag spelling and the honest (none) in the two shapes both published texts "
    "need, the guard exports it and the wire asks the guard, so neither CLI "
    "writes a format string while every already-published line stays "
    "byte-identical (six criteria green twice plus three adjacent suites, live "
    "LIVE-COLLAPSED); row 419 stamped, one measured gap seeded "
    "(own_usage_block_renderer), gauge FLOOR-MET 5/5 10/10 10/10."
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
    ok = back == text and "tick 2373" in last
    print("HEARTBEAT appended readback=%s last=%r" % (ok, last[:60]))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())