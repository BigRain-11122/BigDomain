"""heartbeat_R2370.py - append this round's heartbeat row (tick token included).

The five-silence scan reads the LAST non-blank line and matches "tick (\\d+)",
so the token is written into the line itself rather than as a second numeric
row (the R2367 shape defect). Read-back proved.

Usage: python src/os/heartbeat_R2370.py
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(REPO, "heartbeat.txt")

LINE = (
    "R2370 (tick 2370): verification then product - the battery ran first on "
    "the committed 6b918367 tree and read RUNNER PASS 496/496 suites plus "
    "controls 7/7 in 990.9s with criteria total 3952 EXACTLY as pre-registered "
    "(qa/reconcile-all-R2370.log), and the four follow-up sections PASS after "
    "the designed matrix FAIL and its regeneration to 496/3952 (47476B); then "
    "the claimed tech row AC-FSFW1 shipped followup_section_foreign_wire, so "
    "the follow-up matrix section finally ASKS the foreign-section reader - a "
    "FOREIGN-SECTION pile refuses before any matrix byte, a clean pile keeps "
    "the matrix byte-identical, and a census disagreement is reported on a "
    "clean pile - six criteria green twice plus four adjacent suites "
    "(qa/followup-section-foreign-wire-R2370.log) and a live reading of the "
    "real pile as VOCABULARY-CLEAN over 460 rounds; one measured gap row "
    "seeded (followup_guard_evidence_scope) and the gauge stays FLOOR-MET 5/5 "
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
    ok = back == text and "tick 2370" in last
    print("HEARTBEAT appended readback=%s last=%r" % (ok, last[:60]))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())