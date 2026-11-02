"""evidence_R2371 - the live capture for the R2371 product window.

Writes ONE utf-8 LF file with the real tree's readings: the guard on the real
declarations list, the exempt_review argument path before and after that
guard exists (same command), and the declaration bytes before/after so the
read-only claim is measured rather than asserted. Never a shell redirection.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
OUT = os.path.join(REPO, "qa", "review-window-wire-argument-guard-live-R2371.log")
DECL = os.path.join(REPO, "state", "review_window.json")


def digest(path):
    if not os.path.exists(path):
        return "ABSENT"
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run(args):
    proc = subprocess.run([sys.executable] + args, capture_output=True,
                          cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").replace(
        "\r\n", "\n")


def main():
    before = digest(DECL)
    guard_code, guard_out = run(
        [os.path.join("src", "os", "review_window_wire_argument_guard.py"),
         "--check"])
    guard_json_code, guard_json = run(
        [os.path.join("src", "os", "review_window_wire_argument_guard.py"),
         "--check", "--json"])
    review_code, review_out = run(
        [os.path.join("src", "os", "exempt_review.py"),
         "--round", "R2371", "--window", "100"])
    review_decl_code, review_decl_out = run(
        [os.path.join("src", "os", "exempt_review.py"),
         "--round", "R2371", "--window-from-declaration"])
    after = digest(DECL)

    lines = [
        "R2371 review_window_wire_argument_guard live capture",
        "declaration state/review_window.json sha256 before=%s after=%s"
        % (before, after),
        "guard --check rc=%d" % guard_code,
    ]
    lines.extend("  " + line for line in guard_out.rstrip("\n").splitlines())
    lines.append("guard --check --json rc=%d" % guard_json_code)
    lines.extend("  " + line for line in guard_json.rstrip("\n").splitlines())
    lines.append("exempt_review --round R2371 --window 100 rc=%d" % review_code)
    lines.extend("  " + line
                 for line in review_out.rstrip("\n").splitlines())
    lines.append("exempt_review --round R2371 --window-from-declaration rc=%d"
                 % review_decl_code)
    lines.extend("  " + line
                 for line in review_decl_out.rstrip("\n").splitlines())
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(OUT, "r", encoding="utf-8", newline="") as handle:
        read_back = handle.read()
    print("WROTE %s bytes=%d readback_ok=%s unchanged=%s"
          % (os.path.relpath(OUT, REPO), len(body.encode("utf-8")),
             read_back == body, before == after))
    print(body)
    return 0 if read_back == body and before == after else 1


if __name__ == "__main__":
    sys.exit(main())