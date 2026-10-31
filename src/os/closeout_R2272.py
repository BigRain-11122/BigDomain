"""R2272 closeout: append this round rows to state.json, preserving layout.

Same shape as closeout_R2271.py minus the fold (the file measures well under
the waterline, so a fold is not due and is not run). It rewrites the file in
the canonical 16-space item layout state_fold owns only when the on-disk
layout is already non-canonical, appends the rows with a json round-trip
proof, then bumps the tick.

Usage: python src/os/closeout_R2272.py --plan --rows FILE
       python src/os/closeout_R2272.py --execute --rows FILE
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)

import state_fold  # noqa: E402

TICK = 2272


def load():
    return json.loads(io.open(STATE, encoding="utf-8").read())


def normalize(state):
    text = json.loads(io.open(STATE, encoding="utf-8").read())
    raw = io.open(STATE, "rb").read().decode("utf-8")
    layout = state_fold.split_layout(raw, len(text["log"]))
    if layout is not None and all(
            layout["lines"][i].startswith(state_fold.ITEM_PREFIX)
            for i in layout["item_index"]):
        return raw
    out = ["{"]
    names = [k for k in state if k != "log"] + ["log"]
    for index, key in enumerate(names):
        tail = "," if index < len(names) - 1 else ""
        value = state[key]
        if isinstance(value, list):
            out.append("  %s: [" % state_fold.ps_escape(key))
            for i, item in enumerate(value):
                comma = "," if i < len(value) - 1 else ""
                out.append(state_fold.ITEM_PREFIX
                           + state_fold.ps_escape(item) + comma)
            out.append("  ]" + tail)
        elif isinstance(value, int):
            out.append("  %s: %d%s" % (state_fold.ps_escape(key), value, tail))
        else:
            out.append("  %s: %s%s" % (state_fold.ps_escape(key),
                                       state_fold.ps_escape(value), tail))
    out.append("}")
    text = "\n".join(out) + "\n"
    if json.loads(text) != state:
        raise SystemExit("ABORT normalize round-trip mismatch")
    return text


def run(rows, execute=False):
    state = load()
    text = normalize(state)
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        print("ABORT layout")
        return 3
    lines = list(layout["lines"])
    last = layout["item_index"][-1]
    if not lines[last].rstrip().endswith(","):
        lines[last] = lines[last] + ","
    new_items = []
    for i, row in enumerate(rows):
        literal = state_fold.ITEM_PREFIX + state_fold.ps_escape(row)
        if i < len(rows) - 1:
            literal += ","
        new_items.append(literal)
    joined = layout["newline"].join(lines[:last + 1] + new_items
                                    + lines[last + 1:])
    parsed = json.loads(joined)
    if parsed["log"] != state["log"] + list(rows):
        print("ABORT round-trip mismatch")
        return 3
    joined = joined.replace('"tick": %d' % state["tick"],
                            '"tick": %d' % TICK, 1)
    final = json.loads(joined)
    if final["tick"] != TICK or final["log"][-1] != rows[-1]:
        print("ABORT tick or tail")
        return 3
    size = len(joined.encode("utf-8"))
    if size > state_fold.GATE:
        print("ABORT over waterline %d > %d" % (size, state_fold.GATE))
        return 2
    if not execute:
        print("PLAN rows=%d tick=%d bytes=%d log_lines=%d"
              % (len(rows), TICK, size, len(final["log"])))
        return 0
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(joined)
    print("APPEND rows=%d tick=%d bytes=%d log_lines=%d"
          % (len(rows), TICK, size, len(final["log"])))
    return 0


def main(argv):
    if "--rows" not in argv:
        print("usage: --plan|--execute --rows FILE")
        return 5
    rows = json.loads(io.open(argv[argv.index("--rows") + 1],
                              encoding="utf-8").read())
    return run(rows, execute="--execute" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))