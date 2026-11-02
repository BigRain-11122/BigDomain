"""R2376 live capture: the export write path proves its block on the real tree.

One writer, utf-8 LF, no shell redirection. Every number printed here is read
from the real repository; nothing is asserted from memory.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
OUT = os.path.join(REPO, "qa", "queue-export-gate-wire-live-R2376.log")
EXPORT = os.path.join(REPO, "docs", "status-export.json")

LINES = []


def emit(line):
    LINES.append(line)


def run(argv):
    proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace").strip(),
            proc.stderr.decode("utf-8", "replace").strip())


def main():
    python = sys.executable
    gate = os.path.join(REPO, "src", "os", "queue_export_freshness_gate.py")
    wire = os.path.join(REPO, "src", "os", "queue_export_gate_wire.py")

    before_bytes = len(io.open(EXPORT, "rb").read())

    rc1, out1, err1 = run([python, gate, "--check", "--root", REPO])
    emit("STEP1 gate-before rc=%d %s%s" % (rc1, out1, err1))

    rc2, out2, err2 = run([python, wire, "--execute", "--root", REPO,
                           "--export", EXPORT, "--json"])
    emit("STEP2 wire-execute rc=%d %s%s" % (rc2, out2, err2))

    rc3, out3, err3 = run([python, gate, "--check", "--root", REPO])
    emit("STEP3 gate-after rc=%d %s%s" % (rc3, out3, err3))

    after_bytes = len(io.open(EXPORT, "rb").read())
    emit("STEP4 export bytes %d -> %d" % (before_bytes, after_bytes))

    staging = [name for name in os.listdir(os.path.dirname(EXPORT))
               if name.endswith(".gate-stage")]
    emit("STEP5 staged residue=%r" % (staging,))

    directory = tempfile.mkdtemp(prefix="qeg-live-")
    try:
        doctored = os.path.join(directory, "doctored.json")
        with io.open(EXPORT, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        for row in data.get("queue", {}).get("queues") or ():
            if row.get("queue") == "tech":
                row["claimable"] = 999
        with io.open(doctored, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        rc4, out4, err4 = run([python, wire, "--execute", "--root", REPO,
                               "--export", doctored, "--json"])
        emit("STEP6 doctored-copy repaired rc=%d %s%s" % (rc4, out4, err4))
        rc5, out5, err5 = run([python, gate, "--check", "--root", REPO,
                               "--export", doctored])
        emit("STEP7 doctored-after rc=%d %s%s" % (rc5, out5, err5))

        broken = os.path.join(directory, "broken.json")
        with io.open(broken, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("{not json\n")
        rc6, out6, err6 = run([python, wire, "--execute", "--root", REPO,
                               "--export", broken])
        emit("STEP8 not-json rc=%d %s%s" % (rc6, out6, err6))

        rc7, out7, err7 = run([python, wire, "--execute", "--root", REPO,
                               "--export", os.path.join(directory, "none.json")])
        emit("STEP9 absent rc=%d %s%s" % (rc7, out7, err7))

        rc8, out8, err8 = run([python, wire, "--bogus"])
        emit("STEP10 bad-flags rc=%d %s%s" % (rc8, out8, err8))
    finally:
        shutil.rmtree(directory, ignore_errors=True)

    emit("VERDICT live=%s refusal_leg=fixtures-only (a refusal needs the tree "
         "to move between compose and check, which the suite proves by "
         "patching the gate)" % ("WRITTEN" if rc2 == 0 else "NOT-WRITTEN"))

    text = "\n".join(LINES) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(OUT, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    print("wrote %s bytes=%d readback=%s" % (OUT, len(text.encode("utf-8")),
                                             back == text))
    return 0


if __name__ == "__main__":
    sys.exit(main())