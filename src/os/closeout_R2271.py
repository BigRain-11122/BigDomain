"""R2271 closeout: restore the canonical state layout, fold, then append rows.

Finding this window had to fix before it could close honestly: the fold gate
in state_fold refuses this file (E_SF_BAD_LAYOUT) because the on-disk state
was rewritten with 4-space items by a later closeout while the module pins a
16-space item layout. So the closeout (1) rewrites the file in the canonical
layout the module owns, proving json equality byte-for-byte in meaning,
(2) folds a window through state_fold.fold with every window token covered by
the summary, (3) appends this round rows layout-preserving with a json
round-trip proof. ASCII source; row text arrives as utf-8 json.

Usage: python src/os/closeout_R2271.py --plan [--window N]
       python src/os/closeout_R2271.py --execute --window N --rows FILE
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

TICK = 2271
KEYS = ("tick", "last_order", "last_decision_rows", "benchmarks_refreshed",
        "last_gord_tbl_rows", "last_dec_tokens", "log")


def canonical_text(state):
    out = ["{"]
    names = [k for k in KEYS if k in state] + [k for k in state
                                               if k not in KEYS]
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
            out.append("  %s: %d%s" % (state_fold.ps_escape(key), value,
                                       tail))
        else:
            out.append("  %s: %s%s" % (state_fold.ps_escape(key),
                                       state_fold.ps_escape(value), tail))
    out.append("}")
    return "\n".join(out) + "\n"


def normalize():
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    text = canonical_text(state)
    if json.loads(text) != state:
        print("ABORT normalize round-trip mismatch")
        return None
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("NORMALIZE bytes %d -> %d layout=canonical-16 items=%d"
          % (len(raw), len(text.encode("utf-8")), len(state["log"])))
    return text


def summary_for(window_lines, start, end):
    tokens = set()
    for line in window_lines:
        tokens |= set(state_fold.PAT.findall(line))
    head = ("R2271 fold: lines %d..%d of the state log moved verbatim into "
            "logs/state-log-archive-20261031.md; window tokens %s")
    return head % (start, end, " ".join(sorted(tokens)) if tokens else "none")


def run(window, rows=None, execute=False):
    if not execute:
        state = json.loads(io.open(STATE, encoding="utf-8").read())
        text = canonical_text(state)
        count = len(state["log"])
        start, end = 1, min(int(window), count - 4)
        summary = summary_for(state["log"][start - 1:end], start, end)
        plan, _ = state_fold.plan_fold(text.encode("utf-8"), state, start,
                                       end, summary, reserve=9000)
        brief = {k: plan[k] for k in ("window_start", "window_end",
                                      "window_lines", "tokens_total",
                                      "predicted_bytes", "margin", "newline",
                                      "folded_log_len")}
        print("FOLD(dry-run) %s" % json.dumps(brief))
        return 0 if not plan["tokens_missing"] and plan["gate_ok"] else 2
    text = normalize()
    if text is None:
        return 3
    state = json.loads(text)
    count = len(state["log"])
    start, end = 1, min(int(window), count - 4)
    summary = summary_for(state["log"][start - 1:end], start, end)
    plan = state_fold.fold(ROOT, "R2271", 1, start, end, summary,
                           reserve=9000, execute=True)
    brief = {k: plan[k] for k in ("window_start", "window_end",
                                  "window_lines", "tokens_total",
                                  "predicted_bytes", "margin", "newline",
                                  "folded_log_len")}
    print("FOLD%s %s" % ("" if execute else "(dry-run)",
                         json.dumps(brief)))
    if not execute:
        return 0 if not plan["would_fail"] else 2
    if plan["would_fail"]:
        return 2
    raw = io.open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        print("ABORT layout after fold")
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
    new_lines = lines[:last + 1] + new_items + lines[last + 1:]
    folded = layout["newline"].join(new_lines)
    parsed = json.loads(folded)
    if parsed["log"] != state["log"] + list(rows):
        print("ABORT round-trip mismatch")
        return 3
    parsed["tick"] = TICK
    folded = folded.replace('"tick": %d' % state["tick"],
                            '"tick": %d' % TICK, 1)
    if json.loads(folded)["tick"] != TICK:
        print("ABORT tick not bumped")
        return 3
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(folded)
    print("APPEND rows=%d bytes=%d tick=%d log_lines=%d"
          % (len(rows), len(folded.encode("utf-8")), TICK,
             len(rows) + len(state["log"])))
    return 0


def main(argv):
    window = 22
    if "--window" in argv:
        window = int(argv[argv.index("--window") + 1])
    if "--plan" in argv:
        return run(window, execute=False)
    if "--execute" in argv:
        rows = json.loads(io.open(argv[argv.index("--rows") + 1],
                                  encoding="utf-8").read())
        return run(window, rows=rows, execute=True)
    print("usage: --plan [--window N] | --execute --window N --rows FILE")
    return 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))