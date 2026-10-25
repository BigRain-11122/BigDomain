"""Battery runner with streaming, single-writer evidence.

The interactive shell tool cancels a command that produces no output for
five minutes, and the window may not spawn a console child. This helper
runs the full reconcile battery with unbuffered output, echoes every line
as it arrives (so the caller sees progress) and writes the same bytes to
the evidence log with a bare LF UTF-8 single writer - never a shell
redirection, whose UTF-16 dialect trips the evidence census.

Usage: python src/os/battery_stream.py [--evidence PATH] [--runner PATH]
"""

import argparse
import io
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RUNNER = os.path.join(BASE, "sandbox", "reconcile_all.py")
DEFAULT_EVIDENCE = os.path.join(BASE, "qa", "reconcile-all.log")


def run(runner, evidence):
    started = time.time()
    proc = subprocess.Popen(
        [sys.executable, "-u", runner],
        cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1)
    lines = []
    assert proc.stdout is not None
    for line in proc.stdout:
        lines.append(line)
        sys.stdout.write(line)
        sys.stdout.flush()
    code = proc.wait()
    with io.open(evidence, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(lines))
    print("BATTERY rc=%d %.1fs" % (code, time.time() - started), flush=True)
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the reconcile battery "
                                                 "with streamed evidence.")
    parser.add_argument("--evidence", default=DEFAULT_EVIDENCE)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    args = parser.parse_args(argv)
    return run(args.runner, args.evidence)


if __name__ == "__main__":
    sys.exit(main())