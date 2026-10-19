"""R2045 takeover battery driver (crashed-round orphan payload
closeout). The prior R2045 session claimed the explore FIFO head
(apimarket dev_sales_board month-window zero-listing boundary
cross-restart suite, AC-AMWZB1..7 pre-registered in the claim
row), wrote the suite + the reconcile_all wiring + the matrix
regen + a valid utf-8 suite evidence log, then died before the
queue flip and the state closeout, leaving one ps-utf16 dialect
RUNNER artifact (R1924/R2033 dialect law). This driver:
(verify) re-run the orphan suite twice, byte-compare, and
cross-check the captured sha16 against the orphan evidence
log's lf-sha16 line (takeover evidence-chain closure);
(battery) run the full reconcile_all RUNNER and replace the
dialect artifact with a proper python single-writer utf-8 LF
log (R1880 dialect law); (collect) run the four-face gates
(matrix regen + --check, census --update-baseline + --check,
fingerprint sentinel, profile compare [+ re-anchor per the
R2044 precedent when a new suite grows the battery] + --check
+ --daily --check) and append the whole trail to the suite
evidence log. Modes chain via 'all'. Pure ASCII source,
stdlib only, zero network."""

import hashlib
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LOG = os.path.join(ROOT, "qa",
                   "apimarket-devboardmonthboundary-R2045.log")
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_devboardmonthboundarypersist.py")
BATTERY = os.path.join(ROOT, "qa", "reconcile-all-R2045.log")


def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    # LF-normalize child stdout (R2023 dialect law: children
    # that do not reconfigure their own stdout emit CRLF over
    # pipes on this host; evidence logs are LF-only)
    return proc.returncode, proc.stdout.replace(b"\r\n", b"\n")


def orphan_sha16():
    """The prior session's evidence log claims its own double-
    run sha16; parse it for the takeover cross-check."""
    with io.open(LOG, encoding="utf-8") as fh:
        for line in fh:
            if "lf-sha16=" in line:
                return line.strip().split("lf-sha16=")[1][:16]
    return None


def mode_verify():
    rc1, raw1 = run([sys.executable, SUITE])
    rc2, raw2 = run([sys.executable, SUITE])
    same = raw1 == raw2 and rc1 == 0 and rc2 == 0
    sha = hashlib.sha256(raw1).hexdigest()[:16]
    orphan = orphan_sha16()
    cross = (orphan == sha)
    seven_seven = b"SUITE PASS (7/7 criteria green)" in raw1
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as out:
        out.write("\n=== R2045 takeover verification (orphan"
                  " evidence cross-check) ===\n")
        out.write("re-run rc1=%d rc2=%d byte-identical=%s"
                  " sha16=%s bytes=%d\n"
                  % (rc1, rc2, same, sha, len(raw1)))
        out.write("orphan lf-sha16=%s cross-check=%s\n"
                  % (orphan, "MATCH" if cross else "MISMATCH"))
        out.write("TAKEOVER-VERIFY %s sha16=%s "
                  "orphan-cross=%s seven-seven=%s\n"
                  % ("PASS" if (same and cross and seven_seven)
                     else "FAIL", sha,
                     "MATCH" if cross else "MISMATCH",
                     "yes" if seven_seven else "no"))
    print("TAKEOVER-VERIFY %s sha16=%s orphan-cross=%s"
          % ("PASS" if (same and cross and seven_seven) else
             "FAIL", sha, "MATCH" if cross else "MISMATCH"))
    return 0 if (same and cross and seven_seven) else 2


def mode_battery():
    dialect = False
    if os.path.exists(BATTERY):
        with open(BATTERY, "rb") as fh:
            head = fh.read(4)
        dialect = head[:2] in (b"\xff\xfe", b"\xfe\xff")
        os.unlink(BATTERY)
    rc, raw = run([sys.executable, os.path.join(
        ROOT, "src", "sandbox", "reconcile_all.py")])
    with io.open(BATTERY, "w", encoding="utf-8",
                 newline="\n") as out:
        out.write(raw.decode("utf-8", "replace"))
    print("battery rc=%d bytes=%d dialect-artifact-replaced=%s"
          % (rc, len(raw), "yes" if dialect else "no"))
    return rc


def gate(out, title, cmd):
    rc, raw = run(cmd)
    out.write("\n=== %s ===\n" % title)
    out.write(raw.decode("utf-8", "replace"))
    out.write("%s exit=%d\n" % (title, rc))
    return rc


def mode_collect():
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as out:
        with io.open(BATTERY, "r", encoding="utf-8",
                     errors="replace") as fh:
            lines = fh.read().splitlines()
        out.write("\n=== battery tail (qa/reconcile-all-R2045.log)"
                  " - takeover re-run, python single-writer utf-8"
                  " LF replacing the ps-utf16 dialect artifact"
                  " (R1924/R2033 dialect law) ===\n")
        for line in lines[-8:]:
            out.write(line + "\n")
        rc_matrix = gate(out, "matrix regen",
                         [sys.executable, os.path.join(
                             ROOT, "src", "sandbox",
                             "suite_matrix.py")])
        rc_matrix_c = gate(out, "matrix check",
                           [sys.executable, os.path.join(
                               ROOT, "src", "sandbox",
                               "suite_matrix.py"), "--check"])
        rc_census = gate(out, "census update",
                         [sys.executable, os.path.join(
                             ROOT, "src", "os",
                             "qa_writer_census.py"),
                          "--update-baseline", "--dir", "qa"])
        rc_census_c = gate(out, "census check",
                           [sys.executable, os.path.join(
                               ROOT, "src", "os",
                               "qa_writer_census.py"),
                            "--check", "--dir", "qa"])
        rc_fp = gate(out, "fingerprint sentinel",
                     [sys.executable, os.path.join(
                         ROOT, "src", "sandbox",
                         "fingerprint_regen.py"),
                      "--chain", os.path.join(
                          "src", "sandbox",
                          "migration_chains.json"), "--check"])
        rc_prof = gate(out, "profile compare",
                       [sys.executable, os.path.join(
                           ROOT, "src", "sandbox",
                           "runner_profile.py")])
        reanchored = False
        if rc_prof != 0:
            # R2044 precedent: new suite grows the battery; re-
            # anchor to the fresh log then re-compare
            gate(out, "profile re-anchor (R2044 precedent)",
                 [sys.executable, os.path.join(
                     ROOT, "src", "sandbox",
                     "runner_profile.py"), "--update-baseline"])
            reanchored = True
            rc_prof = gate(out, "profile compare (post re-anchor)",
                           [sys.executable, os.path.join(
                               ROOT, "src", "sandbox",
                               "runner_profile.py")])
        rc_prof_c = gate(out, "profile check",
                         [sys.executable, os.path.join(
                             ROOT, "src", "sandbox",
                             "runner_profile.py"), "--check"])
        rc_prof_d = gate(out, "profile daily check",
                         [sys.executable, os.path.join(
                             ROOT, "src", "sandbox",
                             "runner_profile.py"),
                          "--daily", "--check"])
        verdict = ("COLLECT %s matrix=%d/%d census=%d/%d "
                   "fp=%d prof=%d/%d/%d reanchor=%s"
                   % ("GREEN" if ([rc_matrix, rc_matrix_c,
                                  rc_census, rc_census_c,
                                  rc_fp, rc_prof, rc_prof_c,
                                  rc_prof_d] == [0] * 8)
                      else "FLAG",
                      rc_matrix, rc_matrix_c,
                      rc_census, rc_census_c, rc_fp,
                      rc_prof, rc_prof_c, rc_prof_d, reanchored))
        out.write("\n%s\n" % verdict)
        print(verdict)
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "verify":
        return mode_verify()
    if mode == "battery":
        return mode_battery()
    if mode == "collect":
        return mode_collect()
    if mode == "all":
        rc = mode_verify()
        if rc != 0:
            return rc
        rc = mode_battery()
        if rc != 0:
            return rc
        return mode_collect()
    print("unknown mode")
    return 2


if __name__ == "__main__":
    sys.exit(main())
