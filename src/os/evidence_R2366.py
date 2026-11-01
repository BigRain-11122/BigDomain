"""evidence_R2366.py - the R2366 window's evidence capture.

One-off for this round (the house convention): two identical suite legs, a
digest over the PASS/FAIL lines only, one live reading of the shipped CLI and
ONE utf-8 LF writer for both files. Never a shell redirection - the R2362
census trap (a PowerShell capture lands as utf-16 with a BOM, and the census
detector exists to catch exactly that).

Usage: python src/os/evidence_R2366.py
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
PY = sys.executable

SUITE = os.path.join(BASE, "test_battery_followup_help_wire.py")
CLI = os.path.join(BASE, "battery_followup.py")
EVIDENCE = os.path.join(REPO, "qa", "battery-followup-help-wire-R2366.log")
LIVE = os.path.join(REPO, "qa", "battery-followup-help-wire-live-R2366.log")


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    return proc.returncode, text.replace("\r\n", "\n").replace("\r", "\n")


def criterion_lines(text):
    return [line for line in text.split("\n")
            if line.startswith("PASS ") or line.startswith("FAIL ")]


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]


def main():
    rc_a, out_a = run([PY, SUITE])
    rc_b, out_b = run([PY, SUITE])
    lines_a = criterion_lines(out_a)
    lines_b = criterion_lines(out_b)
    same = lines_a == lines_b
    sha = digest(lines_a)
    live_rc, live_out = run([PY, CLI, "--help"])

    body = []
    body.append("--- LEG A rc=%d criteria=%d ---" % (rc_a, len(lines_a)))
    body.append(out_a.rstrip("\n"))
    body.append("--- LEG B rc=%d criteria=%d ---" % (rc_b, len(lines_b)))
    body.append(out_b.rstrip("\n"))
    body.append("--- EVIDENCE legs=2 identical=%s criterion_sha16=%s ---"
                % (same, sha))
    body.append("--- LIVE battery_followup.py --help rc=%d ---" % live_rc)
    body.append(live_out.rstrip("\n"))
    text = "\n".join(body) + "\n"

    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(live_out)

    print("EVIDENCE %s bytes=%d legs=2 identical=%s sha16=%s"
          % (os.path.relpath(EVIDENCE, REPO).replace(os.sep, "/"),
             len(text.encode("utf-8")), same, sha))
    print("LIVE %s rc=%d bytes=%d"
          % (os.path.relpath(LIVE, REPO).replace(os.sep, "/"), live_rc,
             len(live_out.encode("utf-8"))))
    return 0 if (rc_a == 0 and rc_b == 0 and same and live_rc == 0) else 1


if __name__ == "__main__":
    sys.exit(main())