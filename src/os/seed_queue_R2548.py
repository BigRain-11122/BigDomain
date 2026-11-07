"""R2548 seed: append ONE tech queue row with criteria pinned BEFORE the
code, for the state fold gap this verification window measured.

MEASURED at R2548 (not quoted): src/os/state.json reads 189280 bytes against
the 78500 waterline, so the shipped src/os/state_fold.py --check answers
gate=78500 margin=-110780 log_lines=154 verdict=FOLD-DUE. That same shipped
module offers ONLY a --check face (its usage block lists --check and --json
and nothing else), so no fold can be run at all, and every window since
R2522 has carried the same disclosure: the append path uses a proved
load+dump round-trip while the fold stays an owed obligation. A disclosure
repeated 26 times is not a plan. This window declines to implement a fold
inside a verification window that already overran its budget on a 1558.5s
battery, and seeds the work instead with its criteria pinned.

Writes only state/queue/tech.md, appends one line, utf-8 LF, and reads the
file back to prove the row landed exactly once.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BASE)
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

ROW = (
    "- [ ] P2 tech seed (R2548, from this window own measured limit): "
    "`src/os/state_fold_run.py` - MEASURED this window that the shipped "
    "src/os/state_fold.py ships NO fold face (its usage lists only --check "
    "and --json) while state.json reads 189280B against the 78500B waterline "
    "with 154 log lines and verdict FOLD-DUE, so the waterline gate can only "
    "ever report and never be discharged. Criteria AC-SFOLD1..AC-SFOLD6 were "
    "pinned BEFORE the code: "
    "AC-SFOLD1 the fold is DETERMINISTIC and LOSSLESS: the closed log lines "
    "are moved verbatim into the shipped archive face (append-only, same "
    "utf-8 LF law) and for every moved line the archive carries a byte-equal "
    "copy, so no sentence and no round token is dropped; the remaining live "
    "block keeps a stated minimum of the most recent rounds rather than an "
    "empty log. "
    "AC-SFOLD2 the round ledger law is preserved: after the fold a shipped "
    "coverage reader still finds a ledger line for every round it found "
    "before, and the ledger token count is unchanged, because the archive is "
    "read by that reader rather than ignored. "
    "AC-SFOLD3 the fold is PROVED by round-trip: the pre-fold state is "
    "loadable, the post-fold state loads to the same field set with only "
    "log and archive differing, and a re-run of the fold on its own output "
    "writes zero bytes and reports ALREADY-FOLDED. "
    "AC-SFOLD4 the layout defect open since R2522 is closed at its birth "
    "site rather than bypassed: whatever layout reader ships is agreed on by "
    "BOTH the append path and this fold, so the two can never disagree about "
    "the same file again, and the disagreement is refused with one named "
    "code rather than a silent reformat. "
    "AC-SFOLD5 the gate is honest: state_fold --check reads FOLD-CLEAR only "
    "after the measured bytes are at or under the waterline, a fold that "
    "would leave the file over the waterline refuses instead of claiming "
    "success, and the size before and after is printed as a number. "
    "AC-SFOLD6 hygiene and registration: pure ASCII stdlib module, no clock, "
    "no network, wired as os-state-fold-run(6) with its suite in the "
    "registry, a live run on the real state file taken this window with its "
    "sizes reported, and --dry-run writing zero bytes proved by a "
    "whole-file digest."
)


def main():
    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    before = len(text.splitlines())
    if "state_fold_run" in text:
        print("REFUSED already seeded")
        return 2
    body = text
    if not body.endswith("\n"):
        body += "\n"
    body += ROW + "\n"
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = open(QUEUE, "rb").read().decode("utf-8")
    after = len(back.splitlines())
    ok = (back.count("state_fold_run") == 1 and after == before + 1
          and back.endswith("\n") and "\r" not in back)
    print("SEED lines %d->%d once=%s lf_only=%s"
          % (before, after, back.count("state_fold_run") == 1,
             "\r" not in back))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())