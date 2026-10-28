"""R2212 evidence writer: run the new apimarket feed-months suite twice
and write both transcripts with an in-process utf-8 LF single writer
(never a shell redirection, the R2171/R2177 census dialect trap), then
report the byte identity and the criterion digest."""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_feedmonths.py")
QA = os.path.join(ROOT, "qa")


def run_once():
    proc = subprocess.run([sys.executable, SUITE], cwd=os.path.join(
        ROOT, "src", "sandbox", "ledger"), capture_output=True)
    body = proc.stdout + proc.stderr
    return proc.returncode, body.replace(b"\r\n", b"\n")


def write(path, body):
    with open(path, "wb") as handle:
        handle.write(body)
    return os.path.getsize(path)


def main():
    if not os.path.isdir(QA):
        os.makedirs(QA)
    runs = []
    bodies = []
    for tag in ("a", "b"):
        rc, body = run_once()
        path = os.path.join(QA, "apimarket-feedmonths-R2212-%s.log" % tag)
        size = write(path, body)
        bodies.append(body)
        runs.append((tag, rc, path, size, hashlib.sha256(body).hexdigest()))
        print("run %s rc=%d size=%d sha256=%s"
              % (tag, rc, size, runs[-1][4]))
    same = runs[0][4] == runs[1][4]
    crit = [line.strip() for line in bodies[0].decode("utf-8").splitlines()
            if line.startswith("PASS ") or line.startswith("FAIL ")]
    sha16 = hashlib.sha256("\n".join(crit).encode("utf-8")).hexdigest()[:16]
    print("byte_identical=%r criteria=%d criterion_sha16=%s"
          % (same, len(crit), sha16))
    bad = [r for r in runs if r[1] != 0]
    return 0 if (same and not bad and len(crit) == 8) else 1


if __name__ == "__main__":
    sys.exit(main())