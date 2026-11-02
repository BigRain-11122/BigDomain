"""live_R2383: the own-block collapse measured on the real tree, not planned.

Written by one utf-8 LF writer. Read-only over the tree.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import battery_followup_help_wire as HW  # noqa: E402
import own_usage_block_renderer as OUB  # noqa: E402
import runner_arg_guard as G  # noqa: E402

OUT = os.path.join(REPO, "qa", "own-usage-block-renderer-live-R2383.log")

PUBLISHED_GUARD = (
    "usage: runner_arg_guard.py [--json] [--] <runner argv ...>\n"
    "       runner_arg_guard.py --guard-help\n"
    "answers whether reconcile_all.py would accept that argv; "
    "exit 0 allowed/asked, 2 refused, 3 unreadable runner, 5 bad guard "
    "flags. A bare --help is forwarded to the runner as a QUESTION "
    "(exit 0), never swallowed by the guard.")
PUBLISHED_WIRE_HEAD = (
    "usage: battery_followup.py --evidence EVIDENCE --label LABEL "
    "--root ROOT --round ROUND --dry-run --json [--help]")


def read(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def main():
    lines = ["LIVE own_usage_block_renderer R2383"]
    guard = G.guard_usage()
    wire = HW.usage_text()
    lines.append("STEP1 guard_block_matches_published=%s"
                 % (guard == PUBLISHED_GUARD))
    lines.append("STEP2 wire_head_matches_published=%s"
                 % (PUBLISHED_WIRE_HEAD in wire.splitlines()))
    lines.append("STEP3 wire_ends_with_one_newline=%s"
                 % wire.endswith("\n"))
    real = OUB.block
    try:
        OUB.block = lambda spec: "PATCHED"
        moved_guard = G.guard_usage()
        moved_wire = HW.usage_text()
    finally:
        OUB.block = real
    lines.append("STEP4 patched_guard=%r patched_wire=%r"
                 % (moved_guard, moved_wire))
    lines.append("STEP5 restored_guard_matches=%s"
                 % (G.guard_usage() == PUBLISHED_GUARD))
    guard_src = read(os.path.join(BASE, "runner_arg_guard.py"))
    wire_src = read(os.path.join(BASE, "battery_followup_help_wire.py"))
    lines.append("STEP6 guard_head_literal=(none)=%s wire_head_literal=(none)=%s"
                 % ('"usage: ' not in guard_src, '"usage: ' not in wire_src))
    verdict = ("LIVE-COLLAPSED" if all(
        (guard == PUBLISHED_GUARD,
         PUBLISHED_WIRE_HEAD in wire.splitlines(),
         moved_guard == "PATCHED", moved_wire == "PATCHED\n",
         '"usage: ' not in guard_src, '"usage: ' not in wire_src))
        else "LIVE-SPLIT")
    lines.append("VERDICT %s" % verdict)
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body.replace("\r\n", "\n"), end="")
    print("WROTE %s bytes=%d" % (OUT, len(body.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())