"""R2229 evidence runner: double-run the new category-claim suite and
the adjacent claim/category regressions through ONE python writer
(never a shell redirection), ASCII/LF only.

Usage: python src/os/run_evidence_R2229.py
"""

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
QA = os.path.join(ROOT, "qa")

SUITE = "test_apimarket_categoryclaimmonths.py"
ADJACENT = [
    "test_apimarket_claimmonths.py",
    "test_apimarket_categoryquestionmonths.py",
    "test_apimarket_claims.py",
    "test_apimarket_claimlatency.py",
    "test_apimarket_categoryrefundmonths.py",
    "test_apimarket_buyerclaimmonths.py",
    "test_apimarket_categorydemand.py",
]


def run_one(name):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run(
        [sys.executable, name], cwd=LEDGER, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def write_log(path, body):
    with open(path, "wb") as handle:
        handle.write(body)
    strict = body.decode("utf-8")

    def norm(text):
        return text.replace("\r\n", "\n").replace("\r", "\n")

    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(norm(strict).rstrip("\n") + "\n")


def criteria(body):
    return [line for line in body.decode("utf-8").splitlines()
            if line.startswith("PASS ") or line.startswith("FAIL ")]


def main():
    if not os.path.isdir(QA):
        os.makedirs(QA)
    out = []
    rc_a, body_a = run_one(SUITE)
    write_log(os.path.join(
        QA, "apimarket-categoryclaimmonths-R2229-a.log"), body_a)
    rc_b, body_b = run_one(SUITE)
    write_log(os.path.join(
        QA, "apimarket-categoryclaimmonths-R2229-b.log"), body_b)
    crit_a = criteria(body_a)
    crit_b = criteria(body_b)
    same = crit_a == crit_b
    digest = hashlib.sha256(
        "\n".join(crit_a).encode("utf-8")).hexdigest()[:16].upper()
    out.append("SUITE-A rc=%d" % rc_a)
    out.append("SUITE-B rc=%d" % rc_b)
    out.append("CRITERIA_LINES=%d IDENTICAL=%r SHA16=%s"
               % (len(crit_a), same, digest))
    for line in crit_a:
        out.append("  " + line)
    body = []
    body.append("=== ADJACENT REGRESSIONS ===")
    for name in ADJACENT:
        rc, blob = run_one(name)
        lines = criteria(blob)
        verdict = [l for l in blob.decode("utf-8").splitlines()
                   if l.startswith("SUITE ")]
        body.append("%s rc=%d %s"
                    % (name, rc, verdict[-1] if verdict else "NO-VERDICT"))
    write_log(os.path.join(QA, "regression-R2229.log"),
              ("\n".join(body) + "\n").encode("utf-8"))
    out.extend(body)
    print("\n".join(out))
    return 0 if (rc_a == 0 and rc_b == 0 and same) else 1


if __name__ == "__main__":
    raise SystemExit(main())