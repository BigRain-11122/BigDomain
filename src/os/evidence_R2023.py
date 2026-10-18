"""R2023 evidence collector for the apimarket month-window
persist suite (ascii-only source, stdlib only, zero network).

Usage:
  python src/os/evidence_R2023.py suite    # double-run section
  python src/os/evidence_R2023.py collect   # battery + gates

All output is appended (utf-8) to
qa/apimarket-devboardmonthpersist-R2023.log."""

import hashlib
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LOG = os.path.join(ROOT, "qa", "apimarket-devboardmonthpersist"
                   "-R2023.log")
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_devboardmonthpersist.py")


def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    # LF-normalize child stdout (R2023 dialect law: children
    # that do not reconfigure their own stdout emit CRLF over
    # pipes on this host; the evidence log is LF-only)
    return proc.returncode, proc.stdout.replace(b"\r\n", b"\n")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "suite"
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as out:
        if mode == "suite":
            rc1, raw1 = run([sys.executable, SUITE])
            rc2, raw2 = run([sys.executable, SUITE])
            t1 = raw1.replace(b"\r\n", b"\n")
            t2 = raw2.replace(b"\r\n", b"\n")
            same = t1 == t2 and rc1 == 0 and rc2 == 0
            sha = hashlib.sha256(t1).hexdigest()[:16]
            out.write("=== R2023 apimarket dev_sales_board"
                      " month-window persist suite ===\n")
            out.write(t1.decode("utf-8", "replace"))
            out.write("\n--- second run (byte capture) ---\n")
            out.write("run1 rc=%d run2 rc=%d "
                      "byte-identical=%s sha16=%s bytes=%d\n"
                      % (rc1, rc2, same, sha, len(t1)))
            out.write("SUITE-DOUBLE-RUN %s sha16=%s\n"
                      % ("PASS" if same else "FAIL", sha))
        elif mode == "collect":
            battery = os.path.join(ROOT, "qa",
                                   "reconcile-all-R2023.log")
            with io.open(battery, "r", encoding="utf-8",
                         errors="replace") as fh:
                lines = fh.read().splitlines()
            out.write("\n=== battery tail (qa/reconcile-all"
                      "-R2023.log) ===\n")
            for line in lines[-8:]:
                out.write(line + "\n")
            out.write("\n=== matrix regen + check ===\n")
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox", "suite_matrix.py")])
            out.write(raw.decode("utf-8", "replace"))
            out.write("matrix regen exit=%d\n" % rc)
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox", "suite_matrix.py"),
                "--check"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("matrix check exit=%d\n" % rc)
            out.write("\n=== census update + check ===\n")
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "os", "qa_writer_census.py"),
                "--update-baseline", "--dir", "qa"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("census update exit=%d\n" % rc)
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "os", "qa_writer_census.py"),
                "--check", "--dir", "qa"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("census check exit=%d\n" % rc)
            out.write("\n=== fingerprint sentinel ===\n")
            # first attempt note: invoked with the bare
            # "migration_chains.json" relative path from the repo
            # root, which resolved nowhere (FileNotFoundError,
            # exit 1) - erratum kept visible below; the corrected
            # invocation uses the shipped chain file path.
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox",
                "fingerprint_regen.py"),
                "--chain", os.path.join("src", "sandbox",
                                        "migration_chains.json"),
                "--check"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("fingerprint exit=%d\n" % rc)
            out.write("\n=== runner profile daily check ===\n")
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox", "runner_profile.py"),
                "--daily", "--check"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("profile exit=%d\n" % rc)


if __name__ == "__main__":
    main()
