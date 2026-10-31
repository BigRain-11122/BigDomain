"""export_fix_R2294.py - put the derived counters back in line with the tree.

The waterline fold moved log lines 1..10 (the R2279 and R2280 blocks) into the
archive, and the export's self_drive counters are recomputed over the LIVE log
window, so two of them legitimately changed. The tick row also still carries
the previous round's tick. This script re-derives both from the checker's own
recompute() - it invents nothing and writes only the two agreed keys.
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_export_consistency as CEC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

DERIVED_KEYS = (
    "window",
    "window_days",
    "log_lines_in_window",
    "idle_fast_mention_lines",
    "no_pullable_mention_lines",
    "substantive_non_idle_mention_lines",
    "proposals_total",
    "proposals_open",
    "queue_main_open",
    "queue_tech_open",
    "queue_explore_open",
)


def main(argv):
    execute = "--execute" in argv
    derived, state, export, pat = CEC.recompute()
    label = pat["tick_row_label"]
    changed = []
    sd = export.setdefault("self_drive", {})
    for key in DERIVED_KEYS:
        if key in derived and sd.get(key) != derived[key]:
            changed.append("self_drive.%s %r -> %r" % (key, sd.get(key),
                                                      derived[key]))
            sd[key] = derived[key]
    tick = state.get("tick")
    hits = [row for row in export.get("results", [])
            if isinstance(row, list) and len(row) >= 2
            and row[1] == label and str(row[0]) != str(tick)]
    for row in hits:
        changed.append("results tick row %r -> %r" % (row[0], tick))
        row[0] = str(tick)
    print("CHANGES %d" % len(changed))
    for line in changed:
        print("  %s" % line)
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    blob = json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8")
    if not blob.endswith(b"\n"):
        blob += b"\n"
    temp = EXPORT + ".tmp"
    with open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, EXPORT)
    print("WROTE %dB" % len(blob))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))