# verify_R2019.py - 36th-case takeover verification for the
# R2019 crashed round (statsmonth re-place bounce persist
# suite). Steps: (1) personal re-verification - re-run the
# crashed round's suite twice, LF-normalize stdout bytes,
# confirm byte-identity and sha16 anchor-match against the
# crashed round's own double run (8ec2106227a9816f); (2) the
# four post-RUNNER battery faces - census --update-baseline
# legal re-anchor for the two new qa logs first, then matrix
# regen + --check (evidence = qa/reconcile-all-R2019.log),
# fingerprint --check, runner profile --daily --check and
# main --check, census --check; (3) append all sections plus
# a takeover VERDICT line to qa/reconcile-all-R2019.log (the
# crashed round's log ends at RUNNER PASS; same append shape
# as battery_followup_R2017.py). Captured child output is
# LF-normalized before the append so the battery log stays
# pure-LF (tee class, never a one-generation-later census
# flag face - the R2016.log/R2017-3.log CRLF-tail lesson).
# Pure stdlib, pure ASCII source.
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PY = sys.executable
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_showcase_statsmonthreplacepersist.py")
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2019.log")
MATRIX_EVIDENCE = "qa/reconcile-all-R2019.log"
ANCHOR = "8ec2106227a9816f"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, cwd=ROOT)


def norm(text):
    return text.replace("\r\n", "\n")


def section(caption, proc):
    body = norm(proc.stdout.decode("utf-8", "replace"))
    if proc.stderr:
        err = norm(proc.stderr.decode("utf-8", "replace"))
        body += "--- stderr ---\n" + err
    return "%s\nexit=%d\n%s" % (
        caption, proc.returncode,
        body if body.endswith("\n") else body + "\n")


def suite_once():
    proc = subprocess.run([PY, SUITE], capture_output=True,
                          cwd=ROOT)
    out = proc.stdout.replace(b"\r\n", b"\n")
    return (proc.returncode, out,
            hashlib.sha256(out).hexdigest()[:16])


def main():
    chunks = []
    fails = []
    # 0. personal re-verification: suite double-run re-run
    rc1, out1, sha1 = suite_once()
    rc2, out2, sha2 = suite_once()
    anchor_ok = (sha1 == ANCHOR and sha2 == ANCHOR)
    ident = (out1 == out2)
    both_ok = (rc1 == 0 and rc2 == 0)
    lines = [
        "--- TAKEOVER personal re-verification: suite double"
        " run (LF-normalized) ---",
        "--- rerun 1 rc=%d sha16=%s ---" % (rc1, sha1),
        "--- rerun 2 rc=%d sha16=%s ---" % (rc2, sha2),
        "--- anchor-match vs crashed round sha16 %s: %s ---"
        % (ANCHOR, "PASS" if anchor_ok else "FAIL"),
        "--- byte-identity: %s (bytes=%d) ---"
        % ("PASS" if ident else "FAIL", len(out1)),
        "--- SUITE-REVERIFY %s ---" % (
            "PASS" if (anchor_ok and ident and both_ok)
            else "FAIL"),
    ]
    chunks.append("\n".join(lines) + "\n")
    if not (anchor_ok and ident and both_ok):
        fails.append("suite-reverify")
    print("suite rerun1 rc=%d sha16=%s" % (rc1, sha1))
    print("suite rerun2 rc=%d sha16=%s" % (rc2, sha2))
    print("anchor-match=%s identity=%s"
          % (anchor_ok, ident))

    # 1. census legal re-anchor first (two new qa logs from
    # the crashed round are un-baselined; R2010/R1996/R2018
    # attempt1 precedent family), then the drift check.
    up = run([PY, os.path.join(HERE, "qa_writer_census.py"),
              "--update-baseline"])
    chunks.append(section(
        "--- qa-writer-census: --update-baseline (legal"
        " re-anchor for the crashed round's two new qa logs,"
        " R2010/R1996/R2018 precedent) ---", up))
    if up.returncode != 0:
        fails.append("census-update")
    chk = run([PY, os.path.join(HERE, "qa_writer_census.py"),
               "--check"])
    chunks.append(section(
        "--- qa-writer-census: --check (post re-anchor drift"
        " face) ---", chk))
    if chk.returncode != 0:
        fails.append("census-check")

    # 2. matrix regen then --check (byte-identity face)
    regen = run([PY, os.path.join(ROOT, "src", "sandbox",
                                  "suite_matrix.py"),
                 "--evidence", MATRIX_EVIDENCE])
    chunks.append(section(
        "--- MATRIX regen: suite_matrix.py --evidence %s ---"
        % MATRIX_EVIDENCE, regen))
    if regen.returncode != 0:
        fails.append("matrix regen")
    check = run([PY, os.path.join(ROOT, "src", "sandbox",
                                  "suite_matrix.py"),
                 "--evidence", MATRIX_EVIDENCE, "--check"])
    chunks.append(section(
        "--- MATRIX --check: byte-identical face ---", check))
    if check.returncode != 0:
        fails.append("matrix check")

    # 3. fingerprint sentinel
    fp = run([PY, os.path.join(ROOT, "src", "sandbox",
                               "fingerprint_regen.py"),
              "--chain", "src/sandbox/migration_chains.json",
              "--check"])
    chunks.append(section(
        "--- FINGERPRINT: fingerprint_regen.py --chain"
        " src/sandbox/migration_chains.json --check ---", fp))
    if fp.returncode != 0:
        fails.append("fingerprint")

    # 4. runner wall-time profile: daily face and main face
    prof = run([PY, os.path.join(ROOT, "src", "sandbox",
                                "runner_profile.py"),
                "--daily", "--check"])
    chunks.append(section(
        "--- RUNNER_PROFILE: runner_profile.py --daily"
        " --check ---", prof))
    if prof.returncode != 0:
        # cross-day rollover face: the battery ran yesterday
        # (2026-10-17 22:45); if the daily check wants the
        # current day state, legally update then re-check.
        upd = run([PY, os.path.join(
            ROOT, "src", "sandbox", "runner_profile.py"),
            "--daily"])
        chunks.append(section(
            "--- RUNNER_PROFILE daily rollover update:"
            " runner_profile.py --daily ---", upd))
        prof2 = run([PY, os.path.join(
            ROOT, "src", "sandbox", "runner_profile.py"),
            "--daily", "--check"])
        chunks.append(section(
            "--- RUNNER_PROFILE recheck: --daily --check"
            " (post rollover update) ---", prof2))
        if prof2.returncode != 0:
            fails.append("profile-daily")
    prof_main = run([PY, os.path.join(ROOT, "src", "sandbox",
                                      "runner_profile.py"),
                     "--check"])
    chunks.append(section(
        "--- RUNNER_PROFILE main: runner_profile.py --check"
        " ---", prof_main))
    if prof_main.returncode != 0:
        fails.append("profile-main")

    verdict = ("VERDICT %s (R2019 36th-case takeover battery"
               " follow-up: suite double-run re-verify"
               " anchor-matched; census re-anchor + check;"
               " matrix regen + check; fingerprint; profile"
               " daily + main)"
               % ("PASS" if not fails else "FAIL"))
    chunks.append(verdict + "\n")
    with open(LOG, "ab") as h:
        for chunk in chunks:
            h.write(chunk.encode("utf-8"))
    print(verdict)
    for f in fails:
        print("FAILED SECTION: %s" % f)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
