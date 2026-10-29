"""Single-writer evidence capture for the R2257 window.

Runs the state_seq suite twice and a batch of adjacent os suites once,
writing every body itself as utf-8 LF so no PowerShell redirection can land
UTF-16 (the R2228/R2233 dialect trap). Never transcodes and never relaxes
an assertion.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(ROOT, "qa")

SUITE = os.path.join(BASE, "test_state_seq.py")

ADJACENT = [
    "test_round_evidence.py",
    "test_queue_row.py",
    "test_queue_floor.py",
    "test_debt_register.py",
    "test_export_freshness.py",
]

PY = sys.executable


def _run(script):
    proc = subprocess.run([PY, script], cwd=BASE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, body


def _write(path, parts):
    text = "".join(parts)
    if not text.endswith("\n"):
        text += "\n"
    data = text.replace("\r\n", "\n").encode("utf-8")
    with open(path, "wb") as handle:
        handle.write(data)
    return len(data)


def _criteria(body):
    lines = []
    for line in body.splitlines():
        if line.startswith("PASS ") or line.startswith("FAIL "):
            lines.append(line)
    joined = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16].upper()


def main():
    legs = []
    for suffix in ("a", "b"):
        rc, body = _run(SUITE)
        path = os.path.join(QA, "state-seq-R2257-%s.log" % suffix)
        size = _write(path, ["RUN %s rc=%d suite=%s\n"
                             % (suffix.upper(), rc,
                                os.path.basename(SUITE)), body])
        print("LEG %s rc=%d bytes=%d sha16=%s"
              % (suffix.upper(), rc, size, _criteria(body)))
        legs.append((rc, body))
    print("CRITERIA identical=%r" % (legs[0][1] == legs[1][1],))

    parts = ["RUNNER R2257 adjacent os regressions\n"]
    fails = 0
    for name in ADJACENT:
        rc, body = _run(os.path.join(BASE, name))
        last = [ln for ln in body.splitlines() if ln.startswith("SUITE")]
        parts.append("== %s rc=%d %s\n"
                     % (name, rc, last[-1] if last else "NO SUITE LINE"))
        if rc != 0:
            fails += 1
    adj = os.path.join(QA, "regression-R2257.log")
    size = _write(adj, parts)
    print("ADJACENT fails=%d bytes=%d" % (fails, size))

    live = subprocess.run([PY, os.path.join(BASE, "state_seq.py"),
                           "--check"],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    live_body = live.stdout.decode("utf-8", "replace")
    head = [ln for ln in live_body.splitlines()
            if ln.startswith("STATE SEQUENCE")]
    print("LIVE rc=%d %s" % (live.returncode,
                             head[0][:200] if head else "NO GATE LINE"))

    identical = legs[0][1] == legs[1][1]
    ok = (legs[0][0] == 0 and legs[1][0] == 0 and fails == 0
          and identical)
    print("EVIDENCE identical=%r all_green=%r" % (identical, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())