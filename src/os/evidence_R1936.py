# -*- coding: utf-8 -*-
"""R1936 evidence driver: observation cross-restart persist suite
(strategy paid-observation face, R1886 family seat).
Sections (LF-normalized single writer, R1880/R1884 dialect law):
  [1] suite double-run (byte-identical stdout proof)
  [2] RUNNER regression evidence from the day's sanctioned tee
      carrier qa/reconcile-daily-20261014.log (R1883 precedent:
      the daily log doubles as the suite full-regression carrier;
      no second full RUNNER burn)
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
SUITE = os.path.join("src", "sandbox", "ledger",
                     "test_observation_persist.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
DAILY = os.path.join("qa", "reconcile-daily-20261014.log")
OUT = os.path.join("qa", "observation-persist-R1936.log")

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


def read_lf(path):
    with open(path, encoding="utf-8", errors="replace") as h:
        return h.read().replace("\r\n", "\n")


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

    print("[2] RUNNER evidence from daily tee carrier ...")
    daily = read_lf(DAILY)
    keep = []
    for ln in daily.splitlines():
        if ("ledger-observation-persist" in ln
                or ln.startswith("RUNNER PASS")
                or ln.startswith("census exit=")
                or ln.startswith("sentinel exit=")
                or ln.startswith("profile exit=")):
            keep.append(ln)
    obs_line = [ln for ln in keep
                if "ledger-observation-persist" in ln
                and ln.startswith("PASS suite")]
    runner_line = [ln for ln in keep if ln.startswith("RUNNER PASS")]
    ok2 = (len(obs_line) == 1 and len(runner_line) == 1)
    sections.append("--- [2] daily carrier extract "
                    "(reconcile-daily-20261014.log) ---\n%s"
                    % "\n".join(keep))
    print("    obs_line=%s runner_line=%s" % (bool(ok2),
                                              runner_line[:1]))

    print("[3] suite matrix regen + --check ...")
    # default discovery face: the mtime-newest eligible RUNNER
    # carrier is the daily tee log written by the sanctioned
    # writer (this evidence log is written last and carries
    # only extracts, so discovery falls through it safely).
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

    verdict = (identical and ok2 and rc4 == 0 and rc5 == 0
               and rc6 == 0)
    body = "\n".join(sections)
    body += "\nVERDICT %s\n" % ("PASS" if verdict else "FAIL")
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(body)
    print("VERDICT %s" % ("PASS" if verdict else "FAIL"))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
