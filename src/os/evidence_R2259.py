"""Single-writer evidence capture for the R2259 window.

Runs the seed_anchor suite twice and a batch of adjacent os suites once,
writing every body itself as utf-8 LF so no PowerShell redirection can land
UTF-16 (the R2228/R2233 dialect trap). Never transcodes and never relaxes an
assertion.

The live leg is deliberately two readings, because the tool's whole point is
that the two scopes disagree: a name already mentioned in the seed row text is
OCCUPIED at HEAD, while this window's own uncommitted wiring makes a fresh
name OCCUPIED in the working tree only.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(ROOT, "qa")

SUITE = os.path.join(BASE, "test_seed_anchor.py")

ADJACENT = [
    "test_state_seq.py",
    "test_round_evidence.py",
    "test_queue_row.py",
    "test_queue_floor.py",
    "test_debt_register.py",
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


def _live(needle, scope):
    proc = subprocess.run([PY, os.path.join(BASE, "seed_anchor.py"),
                           "--check", "--needle", needle,
                           "--root", ROOT, "--scope", scope],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace")
    head = [ln for ln in body.splitlines() if ln.startswith("SEED ANCHOR")]
    return proc.returncode, head[0] if head else "NO GATE LINE"


def main():
    legs = []
    for suffix in ("a", "b"):
        rc, body = _run(SUITE)
        path = os.path.join(QA, "seed-anchor-R2259-%s.log" % suffix)
        size = _write(path, ["RUN %s rc=%d suite=%s\n"
                             % (suffix.upper(), rc,
                                os.path.basename(SUITE)), body])
        print("LEG %s rc=%d bytes=%d sha16=%s"
              % (suffix.upper(), rc, size, _criteria(body)))
        legs.append((rc, body))
    print("CRITERIA identical=%r" % (legs[0][1] == legs[1][1],))

    parts = ["RUNNER R2259 adjacent os regressions\n"]
    fails = 0
    for name in ADJACENT:
        rc, body = _run(os.path.join(BASE, name))
        last = [ln for ln in body.splitlines() if ln.startswith("SUITE")]
        parts.append("== %s rc=%d %s\n"
                     % (name, rc, last[-1] if last else "NO SUITE LINE"))
        if rc != 0:
            fails += 1
    adj = os.path.join(QA, "regression-R2259.log")
    size = _write(adj, parts)
    print("ADJACENT fails=%d bytes=%d" % (fails, size))

    rc_text, line_text = _live("seed_anchor", "both")
    print("LIVE seed_anchor rc=%d %s" % (rc_text, line_text[:220]))
    rc_label, line_label = _live("os-seed-anchor", "head")
    print("LIVE os-seed-anchor head rc=%d %s"
          % (rc_label, line_label[:220]))

    identical = legs[0][1] == legs[1][1]
    ok = (legs[0][0] == 0 and legs[1][0] == 0 and fails == 0
          and identical)
    print("EVIDENCE identical=%r all_green=%r" % (identical, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())