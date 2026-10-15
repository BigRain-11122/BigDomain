# takeover_verify_R1990.py - R1990 commit-debt takeover verification
# (R1988/R1949 takeover precedent: original round crashed after the
# full RUNNER log was preserved green 218/218 - qa/reconcile-all-
# R1990.log - so the taker re-verifies the chain WITHOUT re-running
# the full RUNNER: suite double-run byte-identity vs the claimed
# sha16 dca908c94dadfc5a, then the on-disk matrix --check, qa writer
# census --check, fingerprint sentinel --check, runner profile
# --check. Pure stdlib, zero network, pure ASCII source.)
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PY = sys.executable
SUITE = os.path.join("src", "sandbox", "ledger",
                     "test_showcase_statsdualpersist.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
FPRINT = os.path.join("src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join("src", "sandbox", "migration_chains.json")
PROFILE = os.path.join("src", "sandbox", "runner_profile.py")
OUT = os.path.join("qa", "takeover-verify-R1990-2.log")
CLAIMED_SHA16 = "dca908c94dadfc5a"

sections = []


def run(cmd):
    p = subprocess.run([PY, "-X", "utf8"] + cmd, cwd=ROOT,
                       capture_output=True)
    out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    return p.returncode, out


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main():
    print("[1] suite double-run ...", flush=True)
    rc1, o1 = run([SUITE])
    rc2, o2 = run([SUITE])
    identical = (o1 == o2) and rc1 == 0 and rc2 == 0
    s1 = sha16(o1)
    sha_match = (s1 == CLAIMED_SHA16)
    sections.append("--- [1] suite double-run (rc %s/%s) ---" % (rc1, rc2))
    sections.append("sha16 run1=%s run2=%s byte-identical=%s "
                   "matches-claimed=%s (%s)"
                   % (s1, sha16(o2), identical, sha_match, CLAIMED_SHA16))
    sections.append("suite tail: %s" % "\n".join(o1.splitlines()[-3:]))
    print("    rc=%s/%s identical=%s sha16=%s match=%s"
          % (rc1, rc2, identical, s1, sha_match), flush=True)

    print("[2] matrix --check ...", flush=True)
    rc3, o3 = run([MATRIX, "--check"])
    sections.append("--- [2] matrix --check (rc %s) ---\n%s"
                    % (rc3, o3[-500:]))
    print("    rc=%s" % rc3, flush=True)

    print("[3] census --check ...", flush=True)
    rc4, o4 = run([CENSUS, "--check"])
    sections.append("--- [3] census --check (rc %s) ---\n%s"
                    % (rc4, o4[-600:]))
    print("    rc=%s" % rc4, flush=True)

    print("[4] fingerprint --check ...", flush=True)
    rc5, o5 = run([FPRINT, "--chain", CHAIN, "--check"])
    sections.append("--- [4] fingerprint --check (rc %s) ---\n%s"
                    % (rc5, o5[-500:]))
    print("    rc=%s" % rc5, flush=True)

    print("[5] runner profile --check ...", flush=True)
    rc6, o6 = run([PROFILE, "--check"])
    sections.append("--- [5] profile --check (rc %s) ---\n%s"
                    % (rc6, o6[-400:]))
    print("    rc=%s" % rc6, flush=True)

    verdict = (identical and sha_match and rc3 == 0 and rc4 == 0
               and rc5 == 0 and rc6 == 0)
    body = "\n".join(sections) + "\n"
    body += "VERDICT %s\n" % ("PASS" if verdict else "FAIL")
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(body)
    print("VERDICT %s" % ("PASS" if verdict else "FAIL"), flush=True)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
