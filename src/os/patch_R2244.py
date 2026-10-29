"""R2244 correction pass: the main queue path, and the readings that named it.

check_export_consistency.py recomputes queue_main_open from
state/queue/main.md (6 open) while this window's gauge had pointed at the
canonical tasks.md board (2 open), so the gauge was fixed and everything
that quoted the wrong reading is corrected here with the disclosure kept.
"""

import datetime
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

OLD_LINE = ("QUEUE FLOOR main=1/5 tech=7/10 explore=5/10 "
            "verdict=FLOOR-DEBT shortfall=12")
NEW_LINE = ("QUEUE FLOOR main=5/5 tech=6/10 explore=5/10 "
            "verdict=FLOOR-DEBT shortfall=9")

OLD_LIVE = ("Live reading at closeout: main=1/5 (2 open of which 1 gated), "
            "tech=7/10 (8 open of which 1 gated), explore=5/10 -> "
            "FLOOR-DEBT shortfall=12, which from now on is a measurement "
            "instead of a mid-window discovery.")
NEW_LIVE = ("Live reading at closeout: main=5/5 (6 open of which 1 gated), "
            "tech=6/10 (7 open of which 1 gated), explore=5/10 -> "
            "FLOOR-DEBT shortfall=9, which from now on is a measurement "
            "instead of a mid-window discovery. Correction disclosed: the "
            "first reading of this window pointed main at the canonical "
            "tasks.md board (2 open rows) instead of the self-drive work "
            "queue state/queue/main.md (6 open) that the export checker "
            "also reads, so the gauge reported main=1/5 shortfall=12; "
            "check_export_consistency.py caught the mismatch mid-closeout, "
            "the QUEUE_PATHS mapping was corrected, the suite fixtures and "
            "its independent live recount were repointed to the same three "
            "files, and the reading above is the re-measured one. Both "
            "numbers are recorded so the defect is visible.")

OLD_DEBT = ("the measured floor shortfall of 12 (main 4, tech 3, "
            "explore 5) is the next seeding duty.")
NEW_DEBT = ("the measured floor shortfall of 9 (tech 4, explore 5, main 0) "
            "is the next seeding duty.")

OLD_BACKLOG_LIVE = ("Live reading at closeout: main=1/5 (2 open of which 1 "
                    "gated), tech=7/10 (8 open of which 1 gated), "
                    "explore=5/10 -> FLOOR-DEBT shortfall=12.")
NEW_BACKLOG_LIVE = ("Live reading at closeout: main=5/5 (6 open of which 1 "
                    "gated), tech=6/10 (7 open of which 1 gated), "
                    "explore=5/10 -> FLOOR-DEBT shortfall=9 (disclosed "
                    "correction: the first reading pointed main at tasks.md "
                    "with 2 open rows, the export checker recomputes from "
                    "state/queue/main.md with 6, the QUEUE_PATHS mapping was "
                    "fixed and the suite repointed).")

OLD_BACKLOG_DEBT = ("the new gauge reads main=1/5, tech=7/10, explore=5/10, "
                    "FLOOR-DEBT shortfall=12 (main 4, tech 3, explore 5), so "
                    "the next window must seed real gaps up to the floors and "
                    "claim the top real one.")
NEW_BACKLOG_DEBT = ("the new gauge reads main=5/5, tech=6/10, explore=5/10, "
                    "FLOOR-DEBT shortfall=9 (tech 4, explore 5), so the next "
                    "window must seed real gaps up to the floors and claim the "
                    "top real one.")

OLD_TECH_LIVE = ("Live reading on the real tree at closeout: main=1/5 (2 "
                 "open, 1 gated), tech=7/10 (8 open, 1 gated), explore=5/10 "
                 "-> FLOOR-DEBT shortfall=12, which is now a measurement "
                 "rather than a mid-window discovery.")
NEW_TECH_LIVE = ("Live reading on the real tree at closeout: main=5/5 (6 "
                 "open, 1 gated), tech=6/10 (7 open, 1 gated), explore=5/10 "
                 "-> FLOOR-DEBT shortfall=9, which is now a measurement "
                 "rather than a mid-window discovery (disclosed correction: "
                 "the first reading pointed main at tasks.md, 2 open rows; "
                 "the export checker recomputes from state/queue/main.md, 6; "
                 "QUEUE_PATHS was fixed and the suite plus its independent "
                 "live recount repointed to that file).")

OLD_TECH_DEBT = ("the measured floor shortfall of 12 (main 4, tech 3, "
                 "explore 5) is the next seeding duty.")
NEW_TECH_DEBT = ("the measured floor shortfall of 9 (tech 4, explore 5, "
                 "main 0) is the next seeding duty.")

EXPORT_CURRENT_OLD = ("一行讀出 main=1/5 tech=7/10 explore=5/10 "
                      "verdict=FLOOR-DEBT shortfall=12")
EXPORT_CURRENT_NEW = ("一行讀出 main=5/5 tech=6/10 explore=5/10 "
                      "verdict=FLOOR-DEBT shortfall=9")

EXPORT_OUT_OLD = ("prints one line - QUEUE FLOOR main=1/5 tech=7/10 "
                  "explore=5/10 verdict=FLOOR-DEBT shortfall=12 - plus one "
                  "line per queue.")
EXPORT_OUT_NEW = ("prints one line - QUEUE FLOOR main=5/5 tech=6/10 "
                  "explore=5/10 verdict=FLOOR-DEBT shortfall=9 - plus one "
                  "line per queue. The main line is state/queue/main.md, the "
                  "same file the export checker recomputes from: the first "
                  "build pointed at the canonical tasks.md board (2 open rows "
                  "against the house reading of 6), check_export_consistency "
                  "caught it mid-closeout, QUEUE_PATHS was corrected and the "
                  "suite fixtures plus its independent live recount were "
                  "repointed.")

EXPORT_NEXT_OLD = ("②按本輪量規讀出的缺口 12（main 4 / tech 3 / explore 5）"
                   "補真種子到地板並認領最上真活項")
EXPORT_NEXT_NEW = ("②按本輪量規讀出的缺口 9（tech 4 / explore 5 / main 0）"
                   "補真種子到地板並認領最上真活項")

QUEUE_FLOOR_OLD = ("prints one line - QUEUE FLOOR main=1/5 tech=7/10 "
                   "explore=5/10 verdict=FLOOR-DEBT shortfall=12 - plus one "
                   "line per queue")
QUEUE_FLOOR_NEW = ("prints one line - QUEUE FLOOR main=5/5 tech=6/10 "
                   "explore=5/10 verdict=FLOOR-DEBT shortfall=9 - plus one "
                   "line per queue")


def patch(path, pairs, count_expect=1):
    with io.open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    for old, new in pairs:
        seen = text.count(old)
        if seen != count_expect:
            print("WARN %s: %r occurrences=%d"
                  % (os.path.basename(path), old[:50], seen))
            if seen == 0:
                continue
        text = text.replace(old, new, count_expect)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return len(text.encode("utf-8"))


def main():
    print("STATE bytes=%d" % patch(STATE, [
        (OLD_LINE, NEW_LINE),
        (OLD_LIVE, NEW_LIVE),
        (OLD_DEBT, NEW_DEBT),
    ]))
    print("BACKLOG bytes=%d" % patch(BACKLOG, [
        (OLD_BACKLOG_LIVE, NEW_BACKLOG_LIVE),
        (OLD_BACKLOG_DEBT, NEW_BACKLOG_DEBT),
    ]))
    print("TECH bytes=%d" % patch(TECH, [
        (OLD_TECH_LIVE, NEW_TECH_LIVE),
        (OLD_TECH_DEBT, NEW_TECH_DEBT),
    ]))
    print("EXPORT bytes=%d" % patch(EXPORT, [
        (EXPORT_CURRENT_OLD, EXPORT_CURRENT_NEW),
        (EXPORT_OUT_OLD, EXPORT_OUT_NEW),
        (EXPORT_NEXT_OLD, EXPORT_NEXT_NEW),
        (QUEUE_FLOOR_OLD, QUEUE_FLOOR_NEW),
    ]))

    # export_ts must carry the local offset; the results tick row must
    # name the tick this window actually closed.
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        text = handle.read()
    offset = datetime.datetime.now().astimezone().strftime("%z")
    offset = offset[:3] + ":" + offset[3:]
    text = re.sub(r'"export_ts": "[^"]*"',
                  lambda match: '"export_ts": %s'
                  % json.dumps(datetime.datetime.now().replace(
                      microsecond=0).isoformat() + offset), text, count=1)
    text = text.replace('[\n      "2243",', '[\n      "2244",', 1)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    parsed = json.loads(text)
    print("EXPORT ts=%s first_result=%r"
          % (parsed["export_ts"], parsed["results"][0]))
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    print("STATE tick=%d log=%d" % (state["tick"], len(state["log"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())