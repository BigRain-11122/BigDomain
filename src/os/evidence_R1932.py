# -*- coding: utf-8 -*-
"""R1932 evidence driver: member entry-tier persist suite
(entry_tier activation-receipt family cross-restart).
Sections (LF-normalized single writer, R1880/R1884 dialect law):
  [1] suite double-run (byte-identical stdout proof)
  [2] RUNNER full regression (reconcile_all.py)
  [3] suite matrix regen + --check (byte-identical)
  [4] qa writer census --check
  [5] git status hygiene face
Pure stdlib, zero network, pure ASCII source."""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PY = sys.executable
SUITE = os.path.join("src", "sandbox", "member",
                     "test_entry_tier_persist.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
OUT = os.path.join("qa", "entrytier-persist-R1932.log")

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
    print("[1] suite double-run ...")
    rc1, o1, e1 = run([SUITE])
    rc2, o2, e2 = run([SUITE])
    identical = o1 == o2 and rc1 == rc2 == 0
    sections.append("--- [1] suite double-run (rc %s/%s) ---\n%s"
                    % (rc1, rc2, o1))
    sections.append("sha16 run1=%s run2=%s byte-identical=%s"
                    % (sha16(o1), sha16(o2), identical))
    print("    rc=%s/%s identical=%s sha16=%s"
          % (rc1, rc2, identical, sha16(o1)))

    print("[2] RUNNER full regression ...")
    rc3, o3, e3 = run([RUNNER])
    # full-output carrier for the matrix default discovery face
    # (four-condition eligibility: RUNNER PASS + SUITE lines +
    # unique labels + count==RUNNER total need the whole output)
    with open(os.path.join(ROOT, "qa",
                           "reconcile-all-R1932.log"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(o3)
        if o3 and not o3.endswith("\n"):
            fh.write("\n")
    tail3 = "\n".join(o3.splitlines()[-40:])
    sections.append("--- [2] RUNNER (rc %s) tail ---\n%s" % (rc3, tail3))
    print("    rc=%s" % rc3)

    print("[3] suite matrix regen + --check ...")
    # default discovery face: the mtime-newest eligible RUNNER
    # carrier is the reconcile-all log written by step 2.
    rc4, o4, _ = run([MATRIX])
    sections.append("--- [3] matrix regen (rc %s) ---\n%s"
                    % (rc4, o4[-800:]))
    rc5, o5, _ = run([MATRIX, "--check"])
    sections.append("--- [3b] matrix --check (rc %s) ---\n%s"
                    % (rc5, o5[-400:]))
    print("    regen rc=%s check rc=%s" % (rc4, rc5))

    print("[4] qa writer census --check ...")
    rc6, o6, _ = run([CENSUS, "--check"])
    sections.append("--- [4] census --check (rc %s) ---\n%s"
                    % (rc6, o6[-600:]))
    print("    rc=%s" % rc6)

    print("[5] git status hygiene ...")
    p = subprocess.run(["git", "status", "--short"], cwd=ROOT,
                       capture_output=True)
    tree = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    sections.append("--- [5] git status --short ---\n%s" % tree)
    print("    dirty lines=%d" % len(tree.splitlines()))

    verdict = (identical and rc3 == 0 and rc5 == 0 and rc6 == 0)
    body = "\n".join(sections)
    body += "\nVERDICT %s\n" % ("PASS" if verdict else "FAIL")
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(body)
    print("VERDICT %s" % ("PASS" if verdict else "FAIL"))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
