"""Evidence for R2261, produced by the new callable itself.

The whole point of this window is that the per-round evidence ritual no longer
has to be hand-typed, so this window's own evidence is captured by
`evidence_capture.capture` rather than by a fourth copy of the ritual. The two
live lines are appended afterwards by this single writer (utf-8 LF), because
the callable owns the suite legs and the adjacent batch, not the ad-hoc gates.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import evidence_capture as EC  # noqa: E402

ADJACENT = [
    "test_seed_anchor.py",
    "test_state_seq.py",
    "test_round_evidence.py",
    "test_queue_row.py",
    "test_queue_floor.py",
]


def append(path, lines):
    data = "".join(line if line.endswith("\n") else line + "\n"
                   for line in lines).replace("\r\n", "\n")
    with io.open(path, "ab") as handle:
        handle.write(data.encode("utf-8"))


def live_cli():
    """The callable used the way a window will use it: one CLI run, green."""
    target = os.path.join(ROOT, "qa", "evidence-cli-R2261.log")
    if os.path.exists(target):
        os.unlink(target)
    proc = subprocess.run([sys.executable,
                           os.path.join(BASE, "evidence_capture.py"),
                           "--round", "R2261",
                           "--suite", "test_queue_floor.py",
                           "--evidence", target,
                           "--root", BASE],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace").strip()
    return proc.returncode, body, os.path.exists(target)


def main():
    report = EC.capture(BASE, "R2261",
                        "test_evidence_capture.py",
                        adjacent=ADJACENT,
                        evidence=os.path.join(ROOT, "qa",
                                              "evidence-capture-R2261.log"))
    print(EC.render(report))

    code, line, made = live_cli()
    print("LIVE cli rc=%d file=%r %s" % (code, made, line[:200]))

    path = report["evidence"]
    append(path, ["",
                  "EVIDENCE CAPTURE round=R2261 legs=%d identical=%r "
                  "adjacent=%d digest=%s"
                  % (report["legs"], report["identical"],
                     len(report["adjacent"]), report["digest"]),
                  "LIVE cli rc=%d file=%r %s" % (code, made, line),
                  "LIVE note: this window evidence was written by the new "
                  "callable, not by a fresh copy of the ritual"])
    with io.open(path, "rb") as handle:
        size = len(handle.read())
    print("EVIDENCE file=%s bytes=%d" % (report["evidence"], size))
    return 0 if (code == 0 and made and report["identical"]) else 1


if __name__ == "__main__":
    sys.exit(main())