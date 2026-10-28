"""Single-writer evidence capture for the R2236 window.

Runs the R2236 suite twice and the adjacent trust-family suite batch
once, writing every body itself as utf-8 LF so no PowerShell redirection
can land UTF-16 (the R2228/R2233 dialect trap). Never transcodes and
never relaxes an assertion.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
QA = os.path.join(ROOT, "qa")

SUITE = os.path.join(LEDGER,
                     "test_apimarket_sellerratingmonths.py")

ADJACENT = [
    "test_apimarket_ratingmonths.py",
    "test_apimarket_sellerquality.py",
    "test_apimarket_sellerinbox.py",
    "test_apimarket_ratingrev.py",
    "test_apimarket_ratingreply.py",
    "test_apimarket_ratingreplylatency.py",
]

PY = sys.executable


def _run(script):
    proc = subprocess.run([PY, script], cwd=LEDGER,
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


def main():
    legs = []
    for suffix in ("a", "b"):
        rc, body = _run(SUITE)
        path = os.path.join(
            QA, "apimarket-sellerratingmonths-R2236-%s.log" % suffix)
        size = _write(path, ["RUN %s rc=%d suite=%s\n"
                             % (suffix.upper(), rc,
                                os.path.basename(SUITE)), body])
        print("LEG %s rc=%d bytes=%d" % (suffix.upper(), rc, size))
        legs.append((rc, body))

    parts = ["RUNNER R2236 adjacent trust-family regressions\n"]
    fails = 0
    for name in ADJACENT:
        rc, body = _run(os.path.join(LEDGER, name))
        last = [ln for ln in body.splitlines() if ln.startswith("SUITE")]
        parts.append("== %s rc=%d %s\n"
                     % (name, rc, last[-1] if last else "NO SUITE LINE"))
        parts.append(body)
        if rc != 0:
            fails += 1
    adj = os.path.join(QA, "regression-R2236.log")
    size = _write(adj, parts)
    print("ADJACENT fails=%d bytes=%d" % (fails, size))

    ok = (legs[0][0] == 0 and legs[1][0] == 0 and fails == 0
          and legs[0][1] == legs[1][1])
    print("EVIDENCE identical=%r all_green=%r"
          % (legs[0][1] == legs[1][1], ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())