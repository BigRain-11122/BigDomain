"""evidence_R2374 - the live leg for queue_floor_export_face.

Runs the shipped CLI three times on the REAL tree (dry run, --execute, dry run
again) and writes the normalised transcript as one utf-8 LF file through a
single writer, so the census dialect check reads one dialect. No shell
redirection is used: the console would otherwise put CRLF into the file.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
MODULE = os.path.join(BASE, "queue_floor_export_face.py")
EVIDENCE = os.path.join(REPO, "qa", "queue-floor-export-face-live-R2374.log")


def run(args):
    proc = subprocess.run([sys.executable, MODULE] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    out = proc.stdout.decode("utf-8", "replace").replace("\r\n", "\n").strip()
    err = proc.stderr.decode("utf-8", "replace").replace("\r\n", "\n").strip()
    return proc.returncode, out, err


def main():
    lines = ["R2374 live leg: queue_floor_export_face on the real tree",
             "step=before"]
    code, out, err = run(["--check", "--json"])
    lines.append("rc=%d out=%s" % (code, out))
    if err:
        lines.append("err=%s" % err)
    lines.append("step=execute")
    code, out, err = run(["--execute", "--json"])
    lines.append("rc=%d out=%s" % (code, out))
    if err:
        lines.append("err=%s" % err)
    lines.append("step=after")
    code, out, err = run(["--check", "--json"])
    lines.append("rc=%d out=%s" % (code, out))
    if err:
        lines.append("err=%s" % err)
    text = "\n".join(lines) + "\n"
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("EVIDENCE bytes=%d path=%s" % (len(text.encode("utf-8")), EVIDENCE))
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())