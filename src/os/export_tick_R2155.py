"""R2155 export repair: restore the F3 derivation of the results face.

The tick row (the one whose label matches the patterns file) must carry
the live state tick, and the results container must carry one row per
round recorded in state.json#log. R2153/R2154 appended their narratives
to the state log but never extended the results container, so the
consistency checker read a stale 2153 label. This repairs both from the
actual state (nothing is hand-written: each row's text is the round's
own narrative line).

Reads state + export, writes the export through temp + os.replace.
ASCII source, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")

sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402

MISSING_ROUNDS = ("R2153", "R2154", "R2155")


def write_json(path, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2,
                      sort_keys=False)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n")
    os.replace(tmp, path)


def narrative_for(state, round_id):
    for line in state["log"]:
        if round_id in line[:40] and line[:4].isdigit():
            return line
    return None


def main():
    pat = CEC._load_patterns()
    label = pat["tick_row_label"]
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    results = export.setdefault("results", [])
    hits = [r for r in results
            if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    if len(hits) != 1:
        sys.stderr.write("E_TICKROW: %d rows\n" % len(hits))
        return 2
    hits[0][0] = str(state["tick"])
    have = set(r[0] for r in results
               if isinstance(r, list) and len(r) >= 2)
    added = 0
    for round_id in MISSING_ROUNDS:
        if round_id in have:
            continue
        text = narrative_for(state, round_id)
        if text is None:
            sys.stderr.write("E_NARRATIVE: %s absent\n" % round_id)
            return 2
        results.append([round_id, text])
        added += 1
    write_json(EXPORT, export)
    print("tick_row=%s added=%d results=%d"
          % (str(state["tick"]), added, len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())