# closeout_R2014.py - R2014 full delivery battery: (1) lobby suite
# double-run byte-identity evidence -> qa/idem-budget-R2014.log,
# (2) full RUNNER battery -> qa/reconcile-all-R2014.log, (3)
# suite-matrix regen + --check byte-identical, (4) fingerprint
# regen --check, (5) runner profile --daily --check, (6) qa writer
# census --check. Environment note: the lobby venv python is
# currently denied writes to the system temp tree (drifted after
# the R2002 morning battery - venv temp denial observed live this
# round), so every subprocess gets TMP/TEMP pointed at a writable
# project-local work dir. Streams progress lines (keeps the 5-min
# zero-output kill away). ASCII only (encoding discipline).
import hashlib
import io
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

VENV_PY = os.path.join(ROOT, "src", "sandbox", "lobby", ".venv",
                       "Scripts", "python.exe")
LOBBY_TC = os.path.join(ROOT, "src", "sandbox", "lobby",
                        "test_client.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
WORK = os.path.join(ROOT, ".codely-cli", "tmp", "idem-bg-2014")

EV_SUITE = os.path.join("qa", "idem-budget-R2014.log")
EV_RUNNER = os.path.join("qa", "reconcile-all-R2014.log")
EV_MATRIX = os.path.join("docs", "sandbox-suite-matrix.md")


def env_with_workdir():
    env = dict(os.environ)
    env["TMP"] = WORK
    env["TEMP"] = WORK
    return env


def run_capture(cmd, env, cwd):
    p = subprocess.Popen(cmd, cwd=cwd, env=env,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    buf = []
    for raw in p.stdout:
        buf.append(raw.decode("utf-8", "replace"))
    rc = p.wait()
    return rc, "".join(buf)


def norm_lf(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def main():
    os.makedirs(WORK, exist_ok=True)
    t0 = time.time()
    results = []

    # (1) suite double run
    rc1, out1 = run_capture([VENV_PY, LOBBY_TC],
                            env_with_workdir(), WORK)
    print("step1 run1 rc=%d bytes=%d elapsed=%.0fs"
          % (rc1, len(out1.encode("utf-8")), time.time() - t0),
          flush=True)
    rc2, out2 = run_capture([VENV_PY, LOBBY_TC],
                            env_with_workdir(), WORK)
    a = norm_lf(out1)
    b = norm_lf(out2)
    ident = a == b
    sha16 = hashlib.sha256(b.encode("utf-8")).hexdigest()[:16]
    print("step1 run2 rc=%d bytes=%d byte-identical=%s"
          " sha16=%s elapsed=%.0fs"
          % (rc2, len(out2.encode("utf-8")), ident, sha16,
             time.time() - t0), flush=True)
    suite_ok = rc1 == 0 and rc2 == 0 and ident
    results.append(("suite-double-run", suite_ok))
    with io.open(os.path.join(ROOT, EV_SUITE), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("R2014 idem gate-order budget window - suite"
                " double-run\n")
        fh.write("=" * 61 + "\n")
        fh.write("run1 rc=%d bytes=%d\n" % (rc1,
                 len(out1.encode("utf-8"))))
        fh.write("run2 rc=%d bytes=%d\n" % (rc2,
                 len(out2.encode("utf-8"))))
        fh.write("byte-identical=%s sha16=%s (LF-normalized)\n"
                 % (ident, sha16))
        fh.write("note: criteria pre-registered R2013 in"
                " state/queue/explore.md claim row; implemented"
                " R2014; rate-reject pred first-run defect (sec."
                "reject-only) fixed in-round (AC-S9 face shows"
                " pre-mute violations answer err.rate_limit)\n")
        fh.write("\n--- run2 stdout ---\n")
        fh.write(b)

    # (2) full RUNNER battery
    rc3, out3 = run_capture(
        [sys.executable, RUNNER, EV_RUNNER],
        env_with_workdir(), ROOT)
    with io.open(os.path.join(ROOT, EV_RUNNER), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(norm_lf(out3))
    runner_ok = rc3 == 0 and "RUNNER PASS" in out3
    tail = [ln for ln in out3.splitlines()
            if ln.startswith("RUNNER")]
    print("step2 RUNNER rc=%d %s elapsed=%.0fs"
          % (rc3, tail[-1] if tail else "no-runner-line",
             time.time() - t0), flush=True)
    results.append(("runner-full-battery", runner_ok))

    # (3) suite matrix regen + --check
    m1_rc, m1 = run_capture(
        [sys.executable, os.path.join("src", "sandbox",
                                      "suite_matrix.py"),
         "--out", EV_MATRIX, "--evidence", EV_RUNNER],
        env_with_workdir(), ROOT)
    m2_rc, m2 = run_capture(
        [sys.executable, os.path.join("src", "sandbox",
                                      "suite_matrix.py"),
         "--out", EV_MATRIX, "--evidence", EV_RUNNER,
         "--check"],
        env_with_workdir(), ROOT)
    mtail = [ln for ln in (m1 + "\n" + m2).splitlines()
             if ln.startswith("PASS") or ln.startswith("FAIL")]
    matrix_ok = m1_rc == 0 and m2_rc == 0 and "FAIL" not in m2
    print("step3 matrix rc=%d/%d %s elapsed=%.0fs"
          % (m1_rc, m2_rc,
             (mtail[-1] if mtail else "no-line")[:100],
             time.time() - t0), flush=True)
    results.append(("suite-matrix-check", matrix_ok))

    # (4) fingerprint regen --check
    f_rc, f_out = run_capture(
        [sys.executable, os.path.join("src", "sandbox",
                                      "fingerprint_regen.py"),
         "--check"], env_with_workdir(), ROOT)
    fp_ok = f_rc == 0
    ftail = [ln for ln in f_out.splitlines() if ln][-1:]
    print("step4 fingerprint rc=%d %s elapsed=%.0fs"
          % (f_rc, (ftail[0][:100] if ftail else "no-line"),
             time.time() - t0), flush=True)
    results.append(("fingerprint-check", fp_ok))

    # (5) runner profile --daily --check
    p_rc, p_out = run_capture(
        [sys.executable, os.path.join("src", "sandbox",
                                      "runner_profile.py"),
         "--daily", "--check"], env_with_workdir(), ROOT)
    prof_ok = p_rc == 0
    ptail = [ln for ln in p_out.splitlines() if ln][-1:]
    print("step5 profile rc=%d %s elapsed=%.0fs"
          % (p_rc, (ptail[0][:100] if ptail else "no-line"),
             time.time() - t0), flush=True)
    results.append(("profile-daily-check", prof_ok))

    # (6) qa writer census --check
    c_rc, c_out = run_capture(
        [sys.executable, os.path.join("src", "sandbox",
                                      "qa_writer_census.py"),
         "--check"], env_with_workdir(), ROOT)
    census_ok = c_rc == 0
    ctail = [ln for ln in c_out.splitlines() if ln][-1:]
    print("step6 census rc=%d %s elapsed=%.0fs"
          % (c_rc, (ctail[0][:100] if ctail else "no-line"),
             time.time() - t0), flush=True)
    results.append(("writer-census-check", census_ok))

    print("-- battery verdicts --")
    for name, ok in results:
        print("%s %s" % ("PASS" if ok else "FAIL", name))
    all_ok = all(ok for _, ok in results)
    print("BATTERY %s elapsed=%.1fs" % ("PASS" if all_ok
                                        else "FAIL",
                                        time.time() - t0))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
