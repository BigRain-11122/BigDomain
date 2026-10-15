"""Evidence assembly for R1990 (BigDomain OSLoop).

Runs the new stats_board_dual persist suite twice (byte-identity
check) and the full reconcile_all RUNNER once, writing
LF-normalized utf-8 evidence logs per the R1880 dialect law
(subprocess stdout must be normalized before it lands on disk).
Prints a machine-readable summary for the round log. Pure ASCII.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX = os.path.join(BASE, "sandbox")
QA = os.path.join(os.path.dirname(BASE), "qa")
SUITE = os.path.join(SANDBOX, "ledger",
                     "test_showcase_statsdualpersist.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
SUITE_LOG = os.path.join(QA, "showcase-statsdualpersist-R1990.log")
RUNNER_LOG = os.path.join(QA, "reconcile-all-R1990.log")

ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"


def run(cmd):
    proc = subprocess.run(
        [sys.executable] + cmd,
        cwd=SANDBOX, env=ENV,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    raw = proc.stdout
    text = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return proc.returncode, text


def sha16(data):
    digest = hashlib.sha256(data).hexdigest()
    return digest[:16]


def main():
    rc1, out1 = run([SUITE])
    rc2, out2 = run([SUITE])
    identical = out1 == out2
    body = []
    body.append(b"--- RUN1 (stats_board_dual persist suite) ---")
    body.append(out1 if out1.endswith(b"\n") else out1 + b"\n")
    body.append(b"--- RUN2 (byte-identity check) ---")
    body.append(b"run1_sha16=%s run2_sha16=%s identical=%s\n"
                % (sha16(out1).encode(), sha16(out2).encode(),
                   str(identical).lower().encode()))
    with open(SUITE_LOG, "wb") as handle:
        handle.write(b"".join(body))

    rc3, out3 = run([RUNNER])
    with open(RUNNER_LOG, "wb") as handle:
        handle.write(out3 if out3.endswith(b"\n") else out3 + b"\n")

    suite_last = out1.decode("utf-8", "replace").strip().splitlines()
    runner_last = out3.decode("utf-8", "replace").strip().splitlines()
    print("SUITE_RC=%s RUNNER_RC=%s" % (rc1, rc3))
    print("SUITE_LINE=" + (suite_last[-1] if suite_last else "?"))
    print("RUNNER_LINE=" + (runner_last[-1] if runner_last else "?"))
    print("DOUBLE_RUN_IDENTICAL=%s sha16=%s"
          % (identical, sha16(out1)))
    print("SUITE_LOG=" + SUITE_LOG)
    print("RUNNER_LOG=" + RUNNER_LOG)
    if rc1 != 0 or rc2 != 0 or not identical:
        sys.exit(2)
    if rc3 != 0:
        sys.exit(3)


if __name__ == "__main__":
    main()
