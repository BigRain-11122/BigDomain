"""R2561 backlog + heartbeat: mark the carried item done and carry the battery.

The row that was carried into this window is closed here with the measured
registry numbers, and the next window first item (the battery the debt gate now
names first) is carried on top. heartbeat.txt is read first and rewritten only
when the tick token actually differs.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

CARRIED_HEAD = "- [ ] [carried 2026-11-08 R2560] R2561 first item:"

DONE = (
    "- [x] [done 2026-11-08 R2561] [was carried 2026-11-08 R2560] R2561 first "
    "item: a PRODUCT face on the tech head the register named - "
    "state/queue/tech.md:597 prefix AC-PNDB1 (probe_seam_name_binding_arm_"
    "mixed_residual_alias_attribute_predicate_scope). MEASURED not quoted: the "
    "suite re-ran SUITE PASS 6/6 alone at closeout (30 PASS lines, exit 0) and "
    "the earlier capture log holds legs=2 with an identical digest "
    "489031857ADE8A94 plus adjacent=5 green; a bounded live leg reads modules=5 "
    "loops=161 pred_resolved=0 pred_named=2 unreadable=0 BOUNDED-READ-CLEAN "
    "with both readers proved read-only. The face names a walrus-bound "
    "attribute alias, publishes a subscript or call base as its own text "
    "instead of the shipped question mark, joins a package own `__init__.py` "
    "as well as `<mod>.py`, and reads a with-as helper binding, carrying every "
    "shipped key beside its own. Registry 610 suites / 4636 criteria recounted "
    "by import; matrix regenerated from the eligible R2560 battery leg to "
    "59508B and --check byte-identical; board row 597 closed and one row "
    "seeded as AC-PNDC1..AC-PNDC6 from this window own measured limits. THIS "
    "WINDOW OPENED ON AN INTERRUPTED ATTEMPT and the face, suite, registry row "
    "and evidence were re-measured rather than rebuilt."
)

NEXT = (
    "- [ ] [carried 2026-11-08 R2561] R2562 first item: a VERIFICATION window "
    "on the battery the debt gate now names first - reconcile-battery-R2561 at "
    "the re-measured 610 suites / 4636 criteria, run on this committed tree "
    "BEFORE any further product byte (R2168 mixed-tree rule). Launch detached "
    "and unfiltered through src/os/battery_stream.py with the stream and the "
    "pid in SEPARATE files, never a shell redirection into qa/ (the ps-utf16 "
    "trap has cost six windows). Then the four follow-up sections in the "
    "designed order and one debt row closed through its shipped writer."
)


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    lines = text.split("\n")
    idx = [i for i, row in enumerate(lines) if row.startswith(CARRIED_HEAD)]
    if len(idx) != 1:
        print("REFUSED E_BL_CLAIM: carried rows=%d" % (len(idx),))
        return 2
    at = idx[0]
    lines[at] = DONE
    lines.insert(at + 1, NEXT)
    payload = "\n".join(lines)
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2561]")
          and back[at + 1].startswith("- [ ] [carried 2026-11-08 R2561] "
                                      "R2562 first item:"))
    print("backlog %s at=%d lines=%d" % ("OK" if ok else "FAIL", at,
                                         len(back)))
    beat = ("tick 2561 2026-11-08 R2561 product window: attribute-predicate "
            "face verified by re-run 6/6, registry 610/4636, matrix 59508B "
            "byte-identical, battery R2561 owed next\n")
    old = io.open(HEARTBEAT, encoding="utf-8").read() if \
        os.path.isfile(HEARTBEAT) else ""
    if old != beat:
        with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(beat)
    print("heartbeat %dB" % (len(beat.encode("utf-8")),))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())