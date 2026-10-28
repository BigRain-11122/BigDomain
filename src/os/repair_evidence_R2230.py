"""R2230 evidence repair: the R2228 seller-repeat-month evidence was
written through a shell redirection, so both files landed as UTF-16LE
with a BOM and the qa writer census flagged them as new-dialect
(class=ps-utf16). This runner re-executes the very same suite twice and
rewrites the two evidence files through ONE python writer, ASCII/LF.

Nothing about the product, the suite or the criteria is changed: the
files are regenerated from a fresh double run, not transcoded.

Usage: python src/os/repair_evidence_R2230.py
"""

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
QA = os.path.join(ROOT, "qa")

SUITE = "test_apimarket_sellerrepeatmonths.py"
TARGETS = [
    ("apimarket-sellerrepeatmonths-R2228-a.log", "SUITE-A"),
    ("apimarket-sellerrepeatmonths-R2228-b.log", "SUITE-B"),
]


def run_one(name):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run(
        [sys.executable, name], cwd=LEDGER, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def write_log(path, body):
    text = body.decode("utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip("\n") + "\n")


def criteria(body):
    return [line for line in body.decode("utf-8").splitlines()
            if line.startswith("PASS ") or line.startswith("FAIL ")]


def main():
    out = []
    bodies = []
    rcs = []
    for name, label in TARGETS:
        rc, body = run_one(SUITE)
        rcs.append(rc)
        bodies.append(criteria(body))
        write_log(os.path.join(QA, name), body)
        out.append("%s rc=%d criteria=%d" % (label, rc, len(bodies[-1])))
    same = bodies[0] == bodies[1]
    digest = hashlib.sha256(
        "\n".join(bodies[0]).encode("utf-8")).hexdigest()[:16].upper()
    out.append("CRITERIA_LINES=%d IDENTICAL=%r SHA16=%s"
               % (len(bodies[0]), same, digest))
    for path, _ in TARGETS:
        full = os.path.join(QA, path)
        with open(full, "rb") as handle:
            raw = handle.read()
        out.append("%s bytes=%d bom=%r crlf=%d"
                   % (path, len(raw), raw[:3] == b"\xef\xbb\xbf",
                      raw.count(b"\r\n")))
    print("\n".join(out))
    return 0 if (all(rc == 0 for rc in rcs) and same) else 1


if __name__ == "__main__":
    raise SystemExit(main())