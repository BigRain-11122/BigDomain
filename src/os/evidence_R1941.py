# -*- coding: utf-8 -*-
"""R1941 evidence driver: ledger companion cross-restart persist
suite (the companion seat of the R1886 persist family). Sections
(LF-normalized single writer, R1880/R1884 dialect law):
  [1] suite double-run (byte-identical stdout proof)
  [2] RUNNER full regression (reconcile_all.py)
  [3] suite matrix regen + --check (byte-identical)
  [4] qa writer census --check
  [5] fingerprint sentinel (five-domain baseline; suite-only round
      with zero product bytes: zero schema touch must stay CLEAN)
  [6] git status hygiene face
Pure stdlib, zero network, pure ASCII source."""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PY = sys.executable
SUITE = os.path.join("src", "sandbox", "ledger",
                     "test_companion_persist.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
FPRINT = os.path.join("src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join("src", "sandbox", "migration_chains.json")
OUT = os.path.join("qa", "companion-persist-R1941.log")

sections = []


def run(cmd, cwd=ROOT):
    p = subprocess.run([PY, "-X", "utf8"] + cmd, cwd=cwd,
                       capture_output=True)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace")
            .replace("\r\n", "\n"),
            p.stderr.decode("utf-8", "replace")
            .replace("\r\n", "\n"))


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main():
    print("[1] suite double-run ...", flush=True)
    rc1, o1, e1 = run([SUITE])
    rc2, o2, e2 = run([SUITE])
    identical = o1 == o2 and rc1 == rc2 == 0
    sections.append("--- [1] suite double-run (rc %s/%s) ---\n%s"
                    % (rc1, rc2, o1))
    sections.append("sha16 run1=%s run2=%s byte-identical=%s"
                    % (sha16(o1), sha16(o2), identical))
    print("    rc=%s/%s identical=%s sha16=%s"
          % (rc1, rc2, identical, sha16(o1)), flush=True)

    print("[2] RUNNER full regression ...", flush=True)
    rc3, o3, e3 = run([RUNNER])
    # full-output carrier for the matrix default discovery face
    # (four-condition eligibility: RUNNER PASS + SUITE lines +
    # unique labels + count==RUNNER total need the whole output)
    with open(os.path.join(ROOT, "qa",
                           "reconcile-all-R1941.log"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(o3)
        if o3 and not o3.endswith("\n"):
            fh.write("\n")
    tail3 = "\n".join(o3.splitlines()[-40:])
    sections.append("--- [2] RUNNER (rc %s) tail ---\n%s" % (rc3, tail3))
    print("    rc=%s" % rc3, flush=True)

    print("[3] suite matrix regen + --check ...", flush=True)
    # default discovery face: the mtime-newest eligible RUNNER
    # carrier is the reconcile-all log written by step 2.
    rc4, o4, _ = run([MATRIX])
    sections.append("--- [3] matrix regen (rc %s) ---\n%s"
                    % (rc4, o4[-800:]))
    rc5, o5, _ = run([MATRIX, "--check"])
    sections.append("--- [3b] matrix --check (rc %s) ---\n%s"
                    % (rc5, o5[-400:]))
    print("    regen rc=%s check rc=%s" % (rc4, rc5), flush=True)

    print("[4] qa writer census --check ...", flush=True)
    rc6, o6, _ = run([CENSUS, "--check"])
    sections.append("--- [4] census --check (rc %s) ---\n%s"
                    % (rc6, o6[-600:]))
    print("    rc=%s" % rc6, flush=True)

    print("[5] fingerprint sentinel --check ...", flush=True)
    rc7, o7, _ = run([FPRINT, "--chain", CHAIN, "--check"])
    sections.append("--- [5] fingerprint --check (rc %s) ---\n%s"
                    % (rc7, o7[-600:]))
    print("    rc=%s" % rc7, flush=True)

    print("[6] git status hygiene ...", flush=True)
    p = subprocess.run(["git", "status", "--short"], cwd=ROOT,
                       capture_output=True)
    tree = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    sections.append("--- [6] git status --short ---\n%s" % tree)
    print("    dirty lines=%d" % len(tree.splitlines()), flush=True)

    verdict = (identical and rc3 == 0 and rc5 == 0 and rc6 == 0
               and rc7 == 0)
    body = "\n".join(sections)
    body += "\nVERDICT %s\n" % ("PASS" if verdict else "FAIL")
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(body)
    print("VERDICT %s" % ("PASS" if verdict else "FAIL"), flush=True)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
