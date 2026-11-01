"""closeout_R2343 (queue half): close the tech head row and seed one real gap
row measured by this window's own live reading.

Discharged row: state/queue/tech.md:389 prefix AC-FIC1 (followup_incomplete_cause).
Seeded row: followup_section_foreign, from the measured blind spot that
followup_history.parse collects a SECTION line under ANY name while
vocabulary() only requires its own four, so a foreign section name is held in
`runs` and never looked at again.

Writes with one atomic replace and prints before/after byte counts.
"""

import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")

DISCHARGED = (
    " DISCHARGED: src/os/followup_incomplete_cause.py plus "
    "src/os/test_followup_incomplete_cause.py, AC-FIC1..AC-FIC6 green 6/6 "
    "twice identical through evidence_capture "
    "(qa/followup-incomplete-cause-R2343.log, 1358B) with three adjacent "
    "suites green (followup_history, followup_retry_history, "
    "followup_retry_legs), wired os-followup-incomplete-cause(6). LIVE: "
    "rounds=448 complete=27 legacy=421 no_verdict=0 missing_section=0 "
    "legacy_range=R594..R2330 verdict=SPLIT - 421 of 448 rounds are debt no "
    "rerun can heal, which the aggregate used to print as the same word as a "
    "fixable gap.")

NEW_ROW = (
    "- [ ] P2 tech seed (R2343, from this window own live reading): "
    "`src/os/followup_section_foreign.py` - followup_incomplete_cause now names "
    "WHY a round is incomplete, and this reading exposed a blind spot the same "
    "live pass measured: followup_history.parse collects a SECTION line under "
    "ANY name, while vocabulary() only requires its own four, so a log "
    "carrying a section name outside the ritual (an older or a future one) is "
    "neither reported nor refused - `runs` holds it and nothing ever looks at "
    "it again. Product: one reader whose verdict is derived per round from the "
    "log alone - FOREIGN-SECTION (names present in runs but absent from the "
    "vocabulary, listed per round with its own line), VOCABULARY-CLEAN when "
    "none, plus a directory-level foreign-name census so a ritual rename shows "
    "up as a set difference instead of a silent gap. Criteria prefix "
    "AC-FSF1..AC-FSF6 pre-registered HERE BEFORE any code: AC-FSF1 the "
    "vocabulary and the parse are asked of followup_history and a patched "
    "vocabulary flows straight through; AC-FSF2 the two readings are disjoint "
    "and every round lands in exactly one; AC-FSF3 derived from the log alone, "
    "no clock and no round threshold; AC-FSF4 an unreadable or absent log "
    "refuses at exit 3 with its own code and never reads CLEAN; AC-FSF5 "
    "read-only with the tree digest identical before and after, CLI 0 when "
    "every round is clean, 2 when any round carries a foreign section, 5 on "
    "bad flags, byte-stable --json over pinned keys; AC-FSF6 pure-ASCII "
    "source, stdlib only, zero network, plus its own reconcile label. Anchor "
    "check at HEAD to be re-run before the code.")


def main():
    raw = io.open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    index = 388
    head = lines[index]
    assert head.startswith(
        "- [ ] P2 tech seed (R2325, from this window own live reading): "
        "`src/os/followup_incomplete_cause.py`"), head[:60]
    lines[index] = head.replace("- [ ] P2 tech seed (R2325",
                               "- [x] [done 2026-11-01 R2343] P2 tech seed "
                               "(R2325", 1) + DISCHARGED
    assert lines[-1].startswith("- [ ]"), lines[-1][:60]
    lines.append(NEW_ROW)
    out = ("\n".join(lines) + "\n").encode("utf-8")
    temp = QUEUE + ".tmp"
    with open(temp, "wb") as handle:
        handle.write(out)
    os.replace(temp, QUEUE)
    with open(QUEUE, "rb") as handle:
        back = handle.read()
    assert back == out, "read-back mismatch"
    print("QUEUE CLOSE before=%d after=%d readback=ok"
          % (len(raw), len(back)))


if __name__ == "__main__":
    main()