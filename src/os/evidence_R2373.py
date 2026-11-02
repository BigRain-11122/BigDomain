"""evidence_R2373 - the live leg, written by ONE utf-8 LF writer.

Nothing here is a shell redirection: the child CLIs are run through
subprocess and their console transport EOL is normalised (the R2373 birth-site
repair), then the file is opened once with newline="\\n". The run is
READ-ONLY: every CLI call is the help/asked path, which writes nothing.

What it proves live, on the real tree:
  - the guard's asked path and the wire's house line are rendered by the SAME
    module, and both are byte-identical to the lines R2366 published;
  - patching nothing, the two functions agree with the module they delegate to.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import battery_followup_help_wire as HW  # noqa: E402
import contract_usage_renderer as CUR  # noqa: E402
import runner_arg_guard as G  # noqa: E402

OUT = os.path.join(REPO, "qa", "contract-usage-renderer-live-R2373.log")
PUBLISHED_GUARD = "usage: reconcile_all.py [evidence_log_path]\n" \
                  "known flags: (none)"
PUBLISHED_HOUSE = \
    "house contract: reconcile_all.py [evidence_log_path] flags=(none)"


def run(module, args):
    proc = subprocess.run([sys.executable, module] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    out = proc.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    err = proc.stderr.decode("utf-8", "replace").replace("\r\n", "\n")
    return proc.returncode, out, err


def main():
    contract = G.load_contract()
    guard_help = run(os.path.join(BASE, "runner_arg_guard.py"),
                     ["--guard-help"])
    guard_asked = run(os.path.join(BASE, "runner_arg_guard.py"), ["--help"])
    wire_help = run(os.path.join(BASE, "battery_followup_help_wire.py"),
                    ["--help"])
    block_via_guard = G.usage_text(contract)
    block_via_module = CUR.block(contract)
    line_via_guard = G.contract_line(contract)
    line_via_module = CUR.inline(contract)
    house_line = HW.house_line(contract)
    lines = [
        "LIVE R2373 contract_usage_renderer (read-only help paths)",
        "guard --guard-help rc=%d bytes=%d"
        % (guard_help[0], len(guard_help[1])),
        "guard --help rc=%d" % guard_asked[0],
        "wire --help rc=%d" % wire_help[0],
        "block_guard_equals_module %s"
        % (block_via_guard == block_via_module),
        "line_guard_equals_module %s" % (line_via_guard == line_via_module),
        "guard_published_identical %s" % (block_via_guard == PUBLISHED_GUARD),
        "wire_house_identical %s" % (house_line == PUBLISHED_HOUSE),
        "wire_house_in_help %s" % (PUBLISHED_HOUSE in wire_help[1]),
        "guard_published_in_asked %s" % (PUBLISHED_GUARD in guard_asked[1]),
        "GUARD-BLOCK %s" % block_via_guard.replace("\n", " | "),
        "WIRE-HOUSE %s" % house_line,
        "verdict %s" % ("LIVE-COLLAPSED"
                        if block_via_guard == block_via_module
                        and line_via_guard == line_via_module
                        and block_via_guard == PUBLISHED_GUARD
                        and house_line == PUBLISHED_HOUSE
                        and PUBLISHED_HOUSE in wire_help[1]
                        and guard_asked[0] == 0 and wire_help[0] == 0
                        else "LIVE-MISMATCH"),
    ]
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    return 0 if lines[-1].endswith("LIVE-COLLAPSED") else 1


if __name__ == "__main__":
    sys.exit(main())