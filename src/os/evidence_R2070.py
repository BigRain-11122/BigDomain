"""R2070 evidence assembler: single-writer ASCII/LF evidence log.

Runs the new suite twice, captures the battery summary lines from
qa/reconcile-all-R2070.log, the matrix --check verdict and the live
census verdict, then writes qa/lobby-chat-mute-idem-R2070.log.
"""

import hashlib
import io
import os
import re
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
SUITE = os.path.join("src", "sandbox", "lobby", "test_chatmute_idem.py")
BATTERY = os.path.join("qa", "reconcile-all-R2070.log")
OUT = os.path.join("qa", "lobby-chat-mute-idem-R2070.log")


def run(argv):
    proc = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    code1, out1 = run([sys.executable, SUITE])
    code2, out2 = run([sys.executable, SUITE])
    sha1 = hashlib.sha256(out1.encode("utf-8")).hexdigest()[:16]
    sha2 = hashlib.sha256(out2.encode("utf-8")).hexdigest()[:16]

    mcode, mout = run([sys.executable, os.path.join("src", "sandbox",
                                                    "suite_matrix.py"),
                       "--check", "--evidence", BATTERY])
    with io.open(os.path.join(ROOT, BATTERY), encoding="utf-8",
                 errors="replace") as handle:
        battery_lines = [l for l in handle.read().splitlines()
                         if l.startswith("RUNNER ")
                         or l.startswith("FAIL suites")
                         or "lobby-chat-mute-idem" in l]

    lines = []
    lines.append("or: lobby chat mute/idempotency boundary suite (R2070)")
    lines.append("suite: %s" % SUITE.replace(os.sep, "/"))
    lines.append("")
    lines.append("== section 1: suite run one ==")
    lines.extend(out1.rstrip().splitlines())
    lines.append("exit=%d stdout sha16=%s" % (code1, sha1))
    lines.append("")
    lines.append("== section 2: suite run two (determinism) ==")
    lines.extend(out2.rstrip().splitlines())
    lines.append("exit=%d stdout sha16=%s" % (code2, sha2))
    lines.append("double-run identical=%s" % (sha1 == sha2))
    lines.append("")
    lines.append("== section 3: full battery summary (%s) =="
                 % BATTERY.replace(os.sep, "/"))
    lines.extend(battery_lines)
    lines.append("")
    lines.append("== section 4: suite-matrix check ==")
    lines.extend([l for l in mout.splitlines() if l.startswith("PASS")
                  or l.startswith("FAIL")])
    lines.append("matrix check exit=%d" % mcode)
    lines.append("")
    payload = "\n".join(lines) + "\n"
    if any(ord(ch) > 127 for ch in payload):
        payload = payload.encode("ascii", "replace").decode("ascii")
    with io.open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(payload)
    print("wrote %s bytes=%d suite_exit=%d matrix_exit=%d identical=%s"
          % (OUT, len(payload), code1, mcode, sha1 == sha2))
    return 0 if (code1 == 0 and code2 == 0 and mcode == 0) else 1


if __name__ == "__main__":
    sys.exit(main())