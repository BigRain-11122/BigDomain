"""board_R2373 - stamp the claimed tech row and seed ONE measured gap row.

Same shape as the shipped per-round board writers: whole-file rewrite through
one write, with a predicted byte count, a read-back and a floor re-read.

What it does, and nothing else:
  1. the row the reader named (state/queue/tech.md:419, prefix AC-CUR1) is
     stamped [done 2026-11-02 R2373] - the bracket payload is 22 characters,
     inside the queue_done_stamp 60-character law, and no other bracket on
     that row changes;
  2. one REAL measured gap row is appended at the tail: a tool's OWN argument
     block still has no owner. runner_arg_guard.guard_usage() is a hand-written
     literal and battery_followup_help_wire builds its own flag line from
     strings inside usage_text, so while the CONTRACT block now has one owner,
     a third tool describing its own flags would copy one of those. The seed
     carries AC-OUB1..AC-OUB6 pre-registered before any code.

Usage: python src/os/board_R2373.py [--execute]
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
TECH = os.path.join(REPO, "state", "queue", "tech.md")

STAMP_FROM = "- [ ] P2 tech seed (R2366, from this window own measured seam):"
STAMP_TO = ("- [x] [done 2026-11-02 R2373] P2 tech seed (R2366, from this "
            "window own measured seam):")

SEED = (
    "- [ ] P2 tech seed (R2373, from this window own measured seam): "
    "`src/os/own_usage_block_renderer.py` - the CONTRACT block now has one "
    "owner, but a tool's OWN argument block still has none. Measured this "
    "window: `runner_arg_guard.guard_usage()` returns a hand-written literal "
    "(`usage: runner_arg_guard.py [--json] [--] <runner argv ...>` plus a "
    "prose paragraph), and `battery_followup_help_wire.usage_text` composes "
    "its own flag line from format strings inside the module, so a third tool "
    "describing ITS OWN flags must copy one of those two shapes - the same "
    "class this window collapsed one layer down for the imported contract. "
    "Product: one renderer for a tool's own arguments (name, value flags with "
    "derived metavars, boolean flags, and the honest `(none)`), imported by "
    "both CLIs so neither writes a format string for its own block. Criteria "
    "AC-OUB1..AC-OUB6 pre-registered HERE BEFORE any code: AC-OUB1 the "
    "renderer is imported by both CLIs and patching it moves both own-blocks "
    "byte for byte, with zero format strings left in either module; AC-OUB2 "
    "every already-published own-block line stays byte-identical to R2366 and "
    "R2373 (the guard `--guard-help` text and the wire `usage:` head), so the "
    "collapse adds no new wording; AC-OUB3 a value flag with no metavar and a "
    "table with no flags each render their honest form instead of a partial "
    "line; AC-OUB4 an empty own-flag set renders `(none)`; AC-OUB5 both CLIs "
    "keep their exit codes and a byte-stable `--json`; AC-OUB6 pure ASCII, "
    "stdlib only, no clock, no network, and the four follow-up sections still "
    "run. Anchors zero-occupancy at HEAD 2026-11-02: own_usage_block_renderer, "
    "AC-OUB, E_OUB, os-own-usage-block-renderer, "
    "test_own_usage_block_renderer.\n"
)


def read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def main(argv):
    execute = "--execute" in argv
    raw = read(TECH)
    before = len(raw.encode("utf-8"))
    if STAMP_TO in raw:
        print("BOARD already stamped")
        return 0
    if STAMP_FROM not in raw:
        print("BOARD refuse: the row to stamp was not found (E_B2373_NO_ROW)")
        return 2
    text = raw.replace(STAMP_FROM, STAMP_TO, 1)
    if not text.endswith("\n"):
        text += "\n"
    text = text + SEED
    after = len(text.encode("utf-8"))
    print("BOARD rows stamp=1 seed=1 predicted %dB -> %dB (+%d)"
          % (before, after, after - before))
    if not execute:
        print("BOARD dry run, wrote nothing")
        return 0
    back = write(TECH, text)
    ok = back == text
    print("BOARD execute readback=%s bytes=%d"
          % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))