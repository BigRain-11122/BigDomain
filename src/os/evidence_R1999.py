# evidence_R1999.py - R1999 evidence driver: suite double-run
# byte-identity capture (subprocess byte capture + CRLF->LF
# normalization before anything lands on disk, the R1880/R1884
# dialect-prevention law; single python writer, utf-8 LF output).
# Pure stdlib, pure ASCII source.
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_civic_competition_monthwindow.py")
OUT = os.path.join(ROOT, "qa", "civic-compmonth-R1999.log")


def run_once():
    proc = subprocess.run([sys.executable, SUITE],
                          capture_output=True)
    out = proc.stdout.replace(b"\r\n", b"\n")
    return proc.returncode, out


def main():
    rc1, out1 = run_once()
    rc2, out2 = run_once()
    ident = out1 == out2
    sha = hashlib.sha256(out1).hexdigest()
    ok = rc1 == 0 and rc2 == 0 and ident
    with open(OUT, "wb") as h:
        h.write(b"--- RUN 1: test_civic_competition_monthwindow.py"
                b" (subprocess byte capture, LF-normalized) ---\n")
        h.write(("exit=%d\n" % rc1).encode("ascii"))
        h.write(out1 if out1.endswith(b"\n") else out1 + b"\n")
        h.write(b"--- RUN 2: same suite, deterministic double-run"
                b" ---\n")
        h.write(("exit=%d\n" % rc2).encode("ascii"))
        h.write(out2 if out2.endswith(b"\n") else out2 + b"\n")
        h.write(("--- byte-identity: %s "
                 "(normalized-LF sha256=%s bytes=%d) ---\n"
                 % ("byte-identical" if ok else "DIFFER",
                    sha, len(out1))).encode("ascii"))
    print("RUN1 exit=%d RUN2 exit=%d identical=%s sha=%s bytes=%d"
          % (rc1, rc2, ident, sha, len(out1)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
