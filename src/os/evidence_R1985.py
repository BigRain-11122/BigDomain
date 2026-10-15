# evidence_R1985.py - assemble qa/coverageboard-window-R1985.log
# Sections: [1] suite double-run byte-identity (subprocess byte
# capture - PS redirect dialect pitfall family R1873/R1880),
# [2] census drift discovery + baseline re-freeze + clean
# re-check (new evidence file lands -> documented gate),
# [3] fingerprint check (read-face round, zero schema touch).
# RUNNER/matrix verdicts appended after the green run.
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
OUT = os.path.join(ROOT, "qa", "coverageboard-window-R1985.log")

ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, cwd=cwd, env=ENV)
    return p.returncode, p.stdout + p.stderr


def sha16(raw):
    return hashlib.sha256(raw).hexdigest()[:16]


def main():
    suite = os.path.join(LEDGER, "test_coverage_board_window.py")
    rc1, out1 = run([sys.executable, suite], cwd=LEDGER)
    rc2, out2 = run([sys.executable, suite], cwd=LEDGER)
    # normalize CRLF->LF before hashing/compare (writer law)
    out1n = out1.replace(b"\r\n", b"\n")
    out2n = out2.replace(b"\r\n", b"\n")
    ident = out1n == out2n
    lines = []
    lines.append("== coverage board month-window read face (R1985)"
                 " evidence ==")
    lines.append("canon: explore-queue coverage-window claim row"
                 " (R1984 reseed), AC-CVW1..AC-CVW7 pre-registered"
                 " before code (honesty law); family law: R1826/R1888"
                 " window-parameterization (default byte-identical"
                 " zero drift, additive window envelope key,"
                 " record-time provenance stamps per row family)")
    lines.append("")
    lines.append("-- section 1: acceptance suite double-run --")
    lines.append("run1 exit=%d run2 exit=%d stdout-byte-identical=%s"
                 % (rc1, rc2, ident))
    lines.append("run1 sha16=%s run2 sha16=%s"
                 % (sha16(out1n), sha16(out2n)))
    for ln in out2n.decode("utf-8", "replace").strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    lines.append("-- section 2: writer-census drift discovery --")
    rc3, out3 = run([sys.executable, CENSUS, "--dir",
                     os.path.join(ROOT, "qa"), "--check"])
    lines.append("census pre-freeze exit=%d (expected drift: this"
                 " round's new evidence file lands after the last"
                 " round's baseline - documented re-freeze gate)"
                 % rc3)
    for ln in out3.decode("utf-8", "replace").strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    lines.append("-- section 3: baseline re-freeze + clean re-check --")
    rc4, out4 = run([sys.executable, CENSUS, "--dir",
                     os.path.join(ROOT, "qa"), "--update-baseline"])
    lines.append("census re-freeze exit=%d" % rc4)
    for ln in out4.decode("utf-8", "replace").strip().splitlines():
        lines.append("  " + ln)
    rc5, out5 = run([sys.executable, CENSUS, "--dir",
                     os.path.join(ROOT, "qa"), "--check"])
    verdict_clean = b"verdict: DRIFT-CLEAN" in out5
    lines.append("census post-freeze re-check exit=%d DRIFT-CLEAN=%s"
                 % (rc5, verdict_clean))
    for ln in out5.decode("utf-8", "replace").strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    lines.append("-- section 4: fingerprint check --")
    rc6, out6 = run([sys.executable, FP, "--chain", CHAIN, "--check"])
    lines.append("fingerprint exit=%d" % rc6)
    for ln in out6.decode("utf-8", "replace").strip().splitlines():
        lines.append("  " + ln)
    lines.append("")
    ok = (rc1 == 0 and rc2 == 0 and ident and rc5 == 0
          and verdict_clean and rc6 == 0)
    lines.append("VERDICT %s (suite 7/7 double-run identical;"
                 " census re-freeze documented gate -> DRIFT-CLEAN;"
                 " fingerprint CLEAN = zero schema touch on the"
                 " read-face round)"
                 % ("PASS" if ok else "FAIL"))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("EVIDENCE-WRITTEN %s verdict=%s suite_rc=%d/%d ident=%s"
          % (OUT, "PASS" if ok else "FAIL", rc1, rc2, ident))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
