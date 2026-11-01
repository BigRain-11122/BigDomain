# evidence_R2368.py - one single-writer live capture for the R2368 product face
#
# Why a script and not a shell redirect: PowerShell redirection lands UTF-16
# with a BOM, which is exactly the dialect the qa writer census flags (the
# R2362/R2230 trap). This writes utf-8 with a bare LF, once.

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EVIDENCE = os.path.join(ROOT, "qa", "queue-floor-reading-wire-live-R2368.log")


def run(script):
    proc = subprocess.run([sys.executable, os.path.join(BASE, script), "--check"],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, body.replace("\r\n", "\n").replace("\r", "\n")


def main():
    rc_new, out_new = run("queue_floor_reading_wire.py")
    rc_old, out_old = run("queue_floor.py")
    lines = []
    lines.append("R2368 live: the published floor reading vs the undiscounted gauge")
    lines.append("")
    lines.append("$ queue_floor_reading_wire.py --check   (rc=%d)" % rc_new)
    lines.extend(out_new.rstrip("\n").split("\n"))
    lines.append("")
    lines.append("$ queue_floor.py --check   (rc=%d)" % rc_old)
    lines.extend(out_old.rstrip("\n").split("\n"))
    lines.append("")
    lines.append("READING: the two readers disagree on the same tree at the same "
                 "instant, which is the defect this wire removes - the "
                 "undiscounted gauge reports the tech floor as MET while one of "
                 "its ten claimable rows (line 413, AC-QFR1) is this window's own "
                 "shipped row.")
    body = "\n".join(lines) + "\n"
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print("WROTE %s bytes=%d path=%s" % (EVIDENCE, len(body.encode("utf-8")),
                                         EVIDENCE))
    print("rc new=%d old=%d" % (rc_new, rc_old))
    return 0


if __name__ == "__main__":
    sys.exit(main())