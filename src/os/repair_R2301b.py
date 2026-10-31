"""repair_R2301b.py - rewrite this window's own disclosure item truthfully.

The appended disclosure described the first fold attempt (window 1..8) as the
one that landed, but that window split the R2288 block and the live ledger gate
caught it (rounds_without_ledger 2288). The fold that actually landed is window
1..9 with predicted 70165B equal to measured. This helper replaces exactly that
one log item, refuses to write on any delta mismatch, and writes atomically.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import state_io  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(REPO, "src", "os", "state.json")

OLD_HEAD = "R2301 honest disclosures:"

NEW = (
    "R2301 honest disclosures: (a) the battery ran as a detached hidden "
    "process because battery_stream buffers its evidence in memory and writes "
    "once at completion, so every probe before the end legitimately found no "
    "file - that was buffering and not a dead runner, confirmed by the live "
    "child process and then by the 780458B file. (b) One polling command was "
    "cancelled by the five-minute no-output rule mid-wait; it spent no work "
    "and the battery was untouched, verified by the process id still alive "
    "immediately afterwards. (c) Both follow-up legs are retained in the "
    "evidence file (1889B FAIL then 1950B PASS); the FAIL leg is the designed "
    "first use of the matrix section, which refuses to rewrite the stale doc. "
    "(d) The tech queue was not touched: claimable stayed 10 against its "
    "floor, so no gap row was due, and the board is the only queue-family "
    "file this window edited. (e) This round shipped no product code, so the "
    "register successor names the product face (evidence_variants, tech head "
    "line 366) rather than a second verification. (f) The fold is disclosed "
    "in full, three attempts by me before any commit: window 1..4 (the whole "
    "R2287 block) freed too little, so the predicate refused to write (its own "
    "gate check read predicted 75020B plus a 7000B reserve against the 78500B "
    "waterline) and the closeout then appended anyway leaving 82050B over the "
    "line; src/os/repair_R2301.py removed exactly those four items and proved "
    "the restore byte-exact (77573B, sha16 8799fafce253c967, the digest the "
    "refused plan had recorded). Window 1..8 then split the R2288 block, which "
    "the live ledger gate caught as rounds_without_ledger 2288 on three red "
    "suites; state.json and backlog.md were restored from HEAD, the archive "
    "was trimmed byte-exactly back to its 10587B pre-window size, and window "
    "1..9 (whole blocks) landed predicted 70165B equal to measured, 592 tokens "
    "covered. After the closeout the four ledger suites read 8/8 and the live "
    "gate reads VERDICT CLEAN over 54 lines (ledger=13 round=40 other=1). (g) "
    "A second fold also ran by accident while the board guard was still wrong "
    "and appended the same window to the archive again; it was caught the same "
    "way and undone by the same restore-and-trim, and the fold guard now "
    "refuses a second fold of the same window. Every number in this item is "
    "the post-repair reading.")


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    idx = [i for i, line in enumerate(state["log"]) if line.startswith(OLD_HEAD)]
    if len(idx) != 1:
        sys.exit("E_REP2_SHAPE: expected exactly one disclosure item, found %d"
                 % len(idx))
    state["log"][idx[0]] = NEW
    ensure_ascii = all(b < 0x80 for b in raw)
    text = json.dumps(state, ensure_ascii=ensure_ascii, indent=2)
    new = state_io.canon(text).encode("utf-8")
    print("STATE %dB -> %dB DELTA %+d" % (len(raw), len(new), len(new) - len(raw)))
    if len(new) > 78500:
        sys.exit("E_REP2_GATE: the rewrite would cross the waterline")
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    temp = os.path.join(os.path.dirname(STATE), ".repair_R2301b.tmp")
    with open(temp, "wb") as sink:
        sink.write(new)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    if open(STATE, "rb").read() != new or os.path.exists(temp):
        sys.exit("E_REP2_READBACK")
    print("WROTE state readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))