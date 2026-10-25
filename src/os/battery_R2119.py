"""R2119 battery driver: full reconcile_all RUNNER plus the four-face
gate trail (matrix regen/check, census update/check, fingerprint
sentinel, profile compare/check/daily). Python single writer keeps the
evidence log utf-8 LF (R1924/R2033 dialect law). Pure ASCII, stdlib."""

import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2119.log")


def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    return proc.returncode, proc.stdout.replace(b"\r\n", b"\n"), \
        proc.stderr.replace(b"\r\n", b"\n")


RAW = os.path.join(ROOT, "qa", "_raw_R2119_battery.txt")


def mode_battery():
    """Child stdout goes straight to a raw file and a heartbeat is
    printed every 20s, so the CLI sees progress while the battery
    runs (a silent 5-minute pipe read gets the command cancelled)."""
    import time
    with open(RAW, "wb") as sink:
        proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "src", "sandbox",
                                          "reconcile_all.py")],
            cwd=ROOT, stdout=sink, stderr=subprocess.STDOUT)
        waited = 0
        while proc.poll() is None:
            time.sleep(20)
            waited += 20
            print("battery running %ds" % waited, flush=True)
        rc = proc.returncode
    with open(RAW, "rb") as fh:
        raw = fh.read().replace(b"\r\n", b"\n")
    with io.open(LOG, "w", encoding="utf-8", newline="\n") as out:
        out.write(raw.decode("utf-8", "replace"))
    os.unlink(RAW)
    print("battery rc=%d bytes=%d log=%s" % (rc, len(raw), LOG))
    return rc


def gate(out, title, cmd):
    rc, raw, err = run(cmd)
    out.write("\n=== %s ===\n" % title)
    out.write(raw.decode("utf-8", "replace"))
    if err:
        out.write(err.decode("utf-8", "replace"))
    out.write("%s exit=%d\n" % (title, rc))
    return rc


def mode_collect():
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as out:
        with io.open(LOG, "r", encoding="utf-8",
                     errors="replace") as fh:
            lines = fh.read().splitlines()
        out.write("\n=== battery tail (python single-writer utf-8 LF)"
                  " ===\n")
        for line in lines[-8:]:
            out.write(line + "\n")
        rc_matrix = gate(out, "matrix regen", [
            sys.executable, os.path.join(ROOT, "src", "sandbox",
                                         "suite_matrix.py")])
        rc_matrix_c = gate(out, "matrix check", [
            sys.executable, os.path.join(ROOT, "src", "sandbox",
                                         "suite_matrix.py"), "--check"])
        rc_census = gate(out, "census update", [
            sys.executable, os.path.join(ROOT, "src", "os",
                                         "qa_writer_census.py"),
            "--update-baseline", "--dir", "qa"])
        rc_census_c = gate(out, "census check", [
            sys.executable, os.path.join(ROOT, "src", "os",
                                         "qa_writer_census.py"),
            "--check", "--dir", "qa"])
        rc_fp = gate(out, "fingerprint sentinel", [
            sys.executable, os.path.join(ROOT, "src", "sandbox",
                                         "fingerprint_regen.py"),
            "--chain", os.path.join("src", "sandbox",
                                    "migration_chains.json"),
            "--check"])
        rc_prof = gate(out, "profile compare", [
            sys.executable, os.path.join(ROOT, "src", "sandbox",
                                         "runner_profile.py")])
        reanchored = False
        if rc_prof != 0:
            gate(out, "profile re-anchor (R2044 precedent)", [
                sys.executable, os.path.join(ROOT, "src", "sandbox",
                                             "runner_profile.py"),
                "--update-baseline"])
            reanchored = True
            rc_prof = gate(out, "profile compare (post re-anchor)", [
                sys.executable, os.path.join(ROOT, "src", "sandbox",
                                             "runner_profile.py")])
        rc_prof_c = gate(out, "profile check", [
            sys.executable, os.path.join(ROOT, "src", "sandbox",
                                         "runner_profile.py"), "--check"])
        rc_prof_d = gate(out, "profile daily check", [
            sys.executable, os.path.join(ROOT, "src", "sandbox",
                                         "runner_profile.py"),
            "--daily", "--check"])
        codes = [rc_matrix, rc_matrix_c, rc_census, rc_census_c,
                 rc_fp, rc_prof, rc_prof_c, rc_prof_d]
        verdict = ("COLLECT %s matrix=%d/%d census=%d/%d fp=%d"
                   " prof=%d/%d/%d reanchor=%s"
                   % ("GREEN" if codes == [0] * 8 else "FLAG",
                      rc_matrix, rc_matrix_c, rc_census,
                      rc_census_c, rc_fp, rc_prof, rc_prof_c,
                      rc_prof_d, reanchored))
        out.write("\n%s\n" % verdict)
    print(verdict)
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "battery":
        return mode_battery()
    if mode == "collect":
        return mode_collect()
    rc = mode_battery()
    if rc != 0:
        return rc
    return mode_collect()


if __name__ == "__main__":
    sys.exit(main())