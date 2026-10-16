# evidence_R2008.py - R2008 suite double-run byte-identity
# evidence assembler (R1990/R2006/R2007 subprocess byte-capture
# precedent family: avoids the PS5.1 redirect UTF-16 dialect
# pitfall; captures raw stdout bytes of both runs, asserts
# byte-identity, then writes the qa/ evidence log).
# ASCII only (encoding discipline).
import hashlib
import subprocess
import sys

SUITE = ("src" + "\\" + "sandbox" + "\\" + "ledger" + "\\" +
         "test_datasub_coveragedual.py")
OUT = "qa" + "\\" + "datasub-coveragedual-R2008.log"


def run_once():
    proc = subprocess.run(
        [sys.executable, SUITE],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    same = out1 == out2
    sha = hashlib.sha256(out1).hexdigest()[:16]
    verdict = (rc1 == 0 and rc2 == 0 and same)
    lines = []
    lines.append("== R2008 suite double-run evidence ==")
    lines.append("suite: " + SUITE)
    lines.append("run1 exit=%d bytes=%d" % (rc1, len(out1)))
    lines.append("run2 exit=%d bytes=%d" % (rc2, len(out2)))
    lines.append("byte-identical: %s" % same)
    lines.append("stdout sha16: %s" % sha)
    lines.append("verdict: %s" % ("PASS" if verdict else "FAIL"))
    lines.append("")
    lines.append("-- run 1 stdout --")
    lines.append(out1.decode("ascii"))
    lines.append("-- run 2 stdout --")
    lines.append(out2.decode("ascii"))
    with open(OUT, "wb") as handle:
        handle.write("\n".join(lines).encode("ascii"))
    print("double-run identical=%s sha16=%s bytes=%d rc=%d/%d"
          % (same, sha, len(out1), rc1, rc2))
    print("verdict=%s" % ("PASS" if verdict else "FAIL"))
    sys.exit(0 if verdict else 1)


if __name__ == "__main__":
    main()
