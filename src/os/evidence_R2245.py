"""Single-writer evidence capture for the R2245 window.

Runs the R2245 state-fold suite twice plus a batch of adjacent os/ suites
once, writing every body itself as utf-8 LF so no PowerShell redirection can
land UTF-16 (the R2228/R2233 dialect trap). Never transcodes and never
relaxes an assertion. Also records the live --check reading so the waterline
verdict on the real tree is on the record.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(ROOT, "qa")

SUITE = os.path.join(BASE, "test_state_fold.py")

ADJACENT = [
    "test_queue_floor.py",
    "test_logs_inventory.py",
    "test_ledger_lines.py",
    "test_ledger_archive.py",
    "test_os_retry_naming.py",
    "test_ledger_closeout.py",
]

PY = sys.executable


def _run(script, args=None):
    proc = subprocess.run([PY, script] + list(args or []), cwd=BASE,
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
        path = os.path.join(QA, "state-fold-R2245-%s.log" % suffix)
        size = _write(path, ["RUN %s rc=%d suite=%s\n"
                             % (suffix.upper(), rc,
                                os.path.basename(SUITE)), body])
        print("LEG %s rc=%d bytes=%d sha16=%s"
              % (suffix.upper(), rc, size, _criteria(body)))
        legs.append((rc, body))

    parts = ["RUNNER R2245 adjacent os regressions\n"]
    fails = 0
    for name in ADJACENT:
        rc, body = _run(os.path.join(BASE, name))
        last = [ln for ln in body.splitlines() if ln.startswith("SUITE")]
        parts.append("== %s rc=%d %s\n"
                     % (name, rc, last[-1] if last else "NO SUITE LINE"))
        parts.append(body)
        if rc != 0:
            fails += 1
    check_rc, check_body = _run(os.path.join(BASE, "state_fold.py"),
                                ["--check"])
    parts.append("== live state_fold.py --check rc=%d\n" % check_rc)
    parts.append(check_body)
    adj = os.path.join(QA, "regression-R2245.log")
    size = _write(adj, parts)
    print("ADJACENT fails=%d bytes=%d live_check_rc=%d"
          % (fails, size, check_rc))

    identical = legs[0][1] == legs[1][1]
    ok = (legs[0][0] == 0 and legs[1][0] == 0 and fails == 0
          and identical)
    print("EVIDENCE identical=%r all_green=%r" % (identical, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())