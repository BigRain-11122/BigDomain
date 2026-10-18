"""R2036 evidence collector for the showcase_view_window
bad-window gate family cross-restart same-code suite (ascii-only
source, stdlib only, zero network).

Usage:
  python src/os/evidence_R2036.py suite    # double-run section
  python src/os/evidence_R2036.py battery  # full RUNNER + log
  python src/os/evidence_R2036.py collect  # gates + battery tail

Output is appended (utf-8) to
qa/showcase-viewwindow-gatepersist-R2036.log; the battery log
lands in qa/reconcile-all-R2036.log. Same shape as
evidence_R2035.py (python single-writer utf-8 LF, R1880 dialect
law)."""

import hashlib
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LOG = os.path.join(ROOT, "qa",
                   "showcase-viewwindow-gatepersist-R2036.log")
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_showcase_viewwindow_gatepersist.py")


def battery_path(suffix=""):
    return os.path.join(
        ROOT, "qa", "reconcile-all-R2036-%s.log" % suffix
        if suffix else "reconcile-all-R2036.log")


def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    # LF-normalize child stdout (R2023 dialect law: children
    # that do not reconfigure their own stdout emit CRLF over
    # pipes on this host; the evidence logs are LF-only)
    return proc.returncode, proc.stdout.replace(b"\r\n", b"\n")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "suite"
    if mode == "suite":
        rc1, raw1 = run([sys.executable, SUITE])
        rc2, raw2 = run([sys.executable, SUITE])
        same = raw1 == raw2 and rc1 == 0 and rc2 == 0
        sha = hashlib.sha256(raw1).hexdigest()[:16]
        with io.open(LOG, "a", encoding="utf-8",
                     newline="\n") as out:
            out.write("=== R2036 showcase_view_window bad-window"
                      " gate family cross-restart same-code suite"
                      " ===\n")
            out.write(raw1.decode("utf-8", "replace"))
            out.write("\n--- second run (byte capture) ---\n")
            out.write("run1 rc=%d run2 rc=%d "
                      "byte-identical=%s sha16=%s bytes=%d\n"
                      % (rc1, rc2, same, sha, len(raw1)))
            out.write("SUITE-DOUBLE-RUN %s sha16=%s\n"
                      % ("PASS" if same else "FAIL", sha))
            out.write("EVIDENCE-WRITER python single-writer"
                      " utf-8 LF (R1880 dialect law)\n")
        print("SUITE-DOUBLE-RUN %s sha16=%s"
              % ("PASS" if same else "FAIL", sha))
        return 0 if same else 2
    if mode == "battery":
        suffix = sys.argv[2] if len(sys.argv) > 2 else ""
        rc, raw = run([sys.executable, os.path.join(
            ROOT, "src", "sandbox", "reconcile_all.py")])
        with io.open(battery_path(suffix), "w", encoding="utf-8",
                     newline="\n") as out:
            out.write(raw.decode("utf-8", "replace"))
        print("battery rc=%d bytes=%d" % (rc, len(raw)))
        return rc
    if mode == "collect":
        suffix = sys.argv[2] if len(sys.argv) > 2 else ""
        battery = battery_path(suffix)
        with io.open(LOG, "a", encoding="utf-8",
                     newline="\n") as out:
            with io.open(battery, "r", encoding="utf-8",
                         errors="replace") as fh:
                lines = fh.read().splitlines()
            out.write("\n=== battery tail (qa/reconcile-all"
                      "-R2036%s.log) ===\n" % suffix)
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
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox",
                "fingerprint_regen.py"),
                "--chain", os.path.join("src", "sandbox",
                                        "migration_chains.json"),
                "--check"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("fingerprint exit=%d\n" % rc)
            out.write("\n=== runner profile compare + check ===\n")
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox", "runner_profile.py")])
            out.write(raw.decode("utf-8", "replace"))
            out.write("profile compare exit=%d\n" % rc)
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox", "runner_profile.py"),
                "--check"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("profile check exit=%d\n" % rc)
            out.write("\n=== runner profile daily check ===\n")
            rc, raw = run([sys.executable, os.path.join(
                ROOT, "src", "sandbox", "runner_profile.py"),
                "--daily", "--check"])
            out.write(raw.decode("utf-8", "replace"))
            out.write("profile daily exit=%d\n" % rc)
        print("collect done")
        return 0
    print("unknown mode")
    return 2


if __name__ == "__main__":
    sys.exit(main())
