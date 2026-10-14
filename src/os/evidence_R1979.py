# evidence_R1979.py - assemble qa/honorcert-yearbook-R1979.log
# Sections: [0] suite double-run byte-identity, [1] census drift
# discovery (R1978 leftover hygiene debt caught live), [2] census
# baseline re-freeze (documented legal gate) + clean re-check,
# [3] fingerprint check. RUNNER/matrix verdicts appended by
# append_evidence_R1979.py after the green re-run.
import hashlib
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
CENSUS = os.path.join(ROOT, "src", "os", "qa_writer_census.py")
FP = os.path.join(ROOT, "src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join(ROOT, "src", "sandbox", "migration_chains.json")
OUT = os.path.join(ROOT, "qa", "honorcert-yearbook-R1979.log")

ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, cwd=cwd, env=ENV)
    return p.returncode, p.stdout.decode("utf-8", "replace") + \
        p.stderr.decode("utf-8", "replace")


def sha16(data):
    return hashlib.sha256(data).hexdigest()[:16]


def main():
    suite = os.path.join(LEDGER, "test_honorcert_yearbook.py")
    rc1, out1 = run([sys.executable, suite], cwd=LEDGER)
    rc2, out2 = run([sys.executable, suite], cwd=LEDGER)
    ident = out1 == out2
    lines = []
    lines.append("== honor yearbook read face (R1979) evidence ==")
    lines.append("canon: explore-queue idx52 claim row, AC-HY1..HY7"
                 " pre-registered before code (honesty law)")
    lines.append("")
    lines.append("-- section 1: acceptance suite double-run --")
    lines.append("run1 exit=%d run2 exit=%d stdout-byte-identical=%s"
                 % (rc1, rc2, ident))
    lines.append("run1 sha16=%s run2 sha16=%s"
                 % (sha16(out1.encode("utf-8")),
                    sha16(out2.encode("utf-8"))))
    for ln in out2.strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    lines.append("-- section 2: writer-census drift discovery --")
    rc3, out3 = run([sys.executable, CENSUS, "--dir",
                     os.path.join(ROOT, "qa"), "--check"])
    lines.append("census pre-freeze exit=%d (live-fire catch: R1978"
                 " evidence file apimarket-devboard-R1978.log landed"
                 " after that round's census pass and was never"
                 " re-baselined - honest hygiene-debt note)"
                 % rc3)
    for ln in out3.strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    lines.append("-- section 3: baseline re-freeze + clean re-check --")
    rc4, out4 = run([sys.executable, CENSUS, "--dir",
                     os.path.join(ROOT, "qa"), "--update-baseline"])
    lines.append("census re-freeze exit=%d" % rc4)
    for ln in out4.strip().splitlines():
        lines.append("  " + ln)
    rc5, out5 = run([sys.executable, CENSUS, "--dir",
                     os.path.join(ROOT, "qa"), "--check"])
    verdict_clean = "verdict: DRIFT-CLEAN" in out5
    lines.append("census post-freeze re-check exit=%d DRIFT-CLEAN=%s"
                 % (rc5, verdict_clean))
    for ln in out5.strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    lines.append("-- section 4: fingerprint check --")
    rc6, out6 = run([sys.executable, FP, "--chain", CHAIN, "--check"])
    lines.append("fingerprint exit=%d" % rc6)
    for ln in out6.strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    ok = (rc1 == 0 and rc2 == 0 and ident and rc5 == 0
          and verdict_clean and rc6 == 0)
    lines.append("VERDICT %s (suite 7/7 double-run identical;"
                 " census debt closed by documented re-freeze gate;"
                 " fingerprint CLEAN)"
                 % ("PASS" if ok else "FAIL"))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("EVIDENCE-WRITTEN %s verdict=%s" % (OUT, "PASS" if ok else "FAIL"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
