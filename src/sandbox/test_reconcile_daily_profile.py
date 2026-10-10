"""Reconcile-daily profile-step wiring suite (R1733; criteria
AC-PD1..AC-PD7 pre-registered in state/queue/tech.md before this code
existed - honesty law). Exit 0 = all green. Stdlib only, ASCII source,
zero network.

Checks:
  pd1-step-append     stubbed run_profile_step -> marker + output +
                      observation tail; earlier section preserved;
                      argv == profile_command(), cwd=BASE (AC-PD1)
  pd2-observation     stub (0,0,2) -> daily exit 0, PASS,
                      profile=flag(exit=2) recorded not gating (PD2/3)
  pd3-sentinel-gate   stub (0,2,0) -> exit 2 (sentinel gating intact)
  pd4-runner-fail     stub (3,0,2) -> exit 3, profile section still
                      appended (failed day must not skip checks)
  pd5-live-step       real subprocess --daily --check on a temp copy of
                      the newest real daily log; real exit recorded
                      (expected 0 = daily baseline byte-consistent)
  pd6-hygiene         ASCII + no-net imports + shipped files clean
  pd7-registration    reconcile_all SUITES row present (source scan)
"""

import contextlib
import glob
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import reconcile_daily as RD  # noqa: E402

REPO = os.path.normpath(os.path.join(BASE, "..", ".."))
QA_REAL = os.path.normpath(os.path.join(REPO, "qa"))
REAL_GIT = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                        "Git", "cmd", "git.exe")

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


class FakeProc(object):
    def __init__(self, code, out, err=""):
        self.returncode = code
        self.stdout = out
        self.stderr = err


def stub_world(qa_dir, runner_code, sentinel_code, sentinel_out,
               profile_code, profile_out):
    captured = {}

    def fake_call(cmd, *a, **kw):
        captured["runner_cmd"] = cmd
        return runner_code

    def fake_run(cmd, **kw):
        if "fingerprint_regen.py" in cmd[1]:
            captured["sentinel_cmd"] = cmd
            return FakeProc(sentinel_code, sentinel_out)
        captured["profile_cmd"] = cmd
        captured["profile_kwargs"] = kw
        return FakeProc(profile_code, profile_out)

    subprocess.call = fake_call
    subprocess.run = fake_run
    RD.QA = qa_dir
    return captured


def restore(real_call, real_run, real_qa):
    subprocess.call = real_call
    subprocess.run = real_run
    RD.QA = real_qa


def run_main_capture():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = RD.main()
    return code, buf.getvalue().strip()


def only_log(tmp):
    return os.path.join(tmp, sorted(os.listdir(tmp))[0])


def main():
    real_call, real_run, real_qa = subprocess.call, subprocess.run, RD.QA

    # pd1: stubbed step -> marker + output + observation tail,
    # earlier section preserved, argv wiring == profile_command()
    tmp = tempfile.mkdtemp(prefix="pd1-step-")
    try:
        log = os.path.join(tmp, "pre.log")
        with open(log, "w", encoding="utf-8", newline="\n") as f:
            f.write("RUNNER PASS (1/1 suites green, reconcile controls "
                    "6/6, 1.0s)\n")
        captured = {}
        real_run_ref = subprocess.run

        def fake_run(cmd, **kw):
            captured["cmd"] = cmd
            captured["kw"] = kw
            return FakeProc(0, "baseline source: qa/x.log\ncheck: "
                               "byte-identical PASS")

        subprocess.run = fake_run
        code = RD.run_profile_step(log)
        subprocess.run = real_run_ref
        with open(log, encoding="utf-8") as f:
            text = f.read()
        ok = (code == 0
              and text.startswith("RUNNER PASS")
              and text.count(RD.PROFILE_MARKER) == 1
              and "byte-identical PASS" in text
              and "profile exit=0 (observation-window: recorded, "
                   "not gating)" in text
              and captured["cmd"] == RD.profile_command()
              and captured["kw"].get("cwd") == BASE
              and "--daily" in captured["cmd"]
              and "--check" in captured["cmd"])
        check(ok, "pd1-step-append exit=%d marker+tail+preserve argv"
              % code)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # pd2: runner clean + sentinel clean + profile flag -> day still
    # PASS, profile=flag(exit=2) recorded (observation window)
    tmp = tempfile.mkdtemp(prefix="pd2-obs-")
    try:
        stub_world(tmp, 0, 0, "verdict CLEAN domains=5",
                   2, "== stale-baseline check ==\ncheck: STALE/DIVERGED")
        code, out = run_main_capture()
        with open(only_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 0
              and "verdict=PASS" in out
              and "runner_exit=0" in out
              and "sentinel=ok" in out
              and "profile=flag(exit=2)" in out
              and RD.PROFILE_MARKER in text
              and "STALE/DIVERGED" in text
              and "profile exit=2 (observation-window: recorded, "
                   "not gating)" in text)
        check(ok, "pd2-observation (0,0,2)->exit=%d PASS flag recorded"
              % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # pd3: sentinel drift still gates the day (aggregation regression)
    tmp = tempfile.mkdtemp(prefix="pd3-gate-")
    try:
        stub_world(tmp, 0, 2, "verdict DRIFT domains=1", 0, "check: ok")
        code, out = run_main_capture()
        ok = (code == 2 and "verdict=FAIL" in out
              and "sentinel=drift(exit=2)" in out
              and "profile=ok" in out)
        check(ok, "pd3-sentinel-gate (0,2,0)->exit=%d gating intact" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # pd4: runner fail propagates; profile section still appended
    tmp = tempfile.mkdtemp(prefix="pd4-rfail-")
    try:
        stub_world(tmp, 3, 0, "verdict CLEAN domains=5",
                   2, "check: STALE/DIVERGED")
        code, out = run_main_capture()
        with open(only_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 3
              and "runner_exit=3" in out
              and "profile=flag(exit=2)" in out
              and RD.PROFILE_MARKER in text
              and "profile exit=2 (observation-window" in text)
        check(ok, "pd4-runner-fail (3,0,2)->exit=%d profile kept" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # pd5: live real-subprocess step on a temp copy of the newest real
    # daily evidence log (closed originals never touched - append lands
    # on the copy only); real exit recorded, expected 0 (daily baseline
    # byte-consistent since R1715).
    dailies = sorted(glob.glob(os.path.join(QA_REAL,
                                             "reconcile-daily-20*.log")),
                     key=os.path.getmtime, reverse=True)
    if not dailies:
        check(False, "pd5-live-step no real daily log found under qa/")
    else:
        tmp = tempfile.mkdtemp(prefix="pd5-live-")
        try:
            copy = os.path.join(tmp, os.path.basename(dailies[0]))
            shutil.copyfile(dailies[0], copy)
            code = RD.run_profile_step(copy)
            with open(copy, encoding="utf-8") as f:
                text = f.read()
            m = re.search(r"(?m)^profile exit=(\d+) "
                          r"\(observation-window", text)
            ok = (m is not None
                  and int(m.group(1)) == code
                  and text.count(RD.PROFILE_MARKER) == 1
                  and "runner wall-time profile" not in text)
            print("pd5 live exit=%d (newest daily: %s)"
                  % (code, os.path.basename(dailies[0])), flush=True)
            check(ok and code == 0,
                  "pd5-live-step real --daily --check exit=%d "
                  "(expected 0)" % code)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # pd6: hygiene - ASCII source, no network imports, shipped clean
    src_path = os.path.join(BASE, "reconcile_daily.py")
    with open(src_path, "rb") as f:
        raw = f.read()
    ascii_ok = all(b < 128 for b in raw)
    net_imports = []
    for line in raw.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            if re.search(r"\b(urllib|requests|socket|http)\b", stripped):
                net_imports.append(stripped)
    git_bin = REAL_GIT if os.path.exists(REAL_GIT) else shutil.which("git")
    shipped = [os.path.join(BASE, "fingerprint_regen.py"),
               os.path.join(BASE, "runner_profile.py"),
               os.path.join(BASE, "migration_chains.json")]
    shipped += sorted(glob.glob(os.path.join(BASE, "*", "config.json")))
    rel = [os.path.relpath(p, REPO).replace(os.sep, "/") for p in shipped]
    proc = subprocess.run([git_bin, "status", "--porcelain", "--"] + rel,
                          capture_output=True, text=True, cwd=REPO)
    clean = proc.returncode == 0 and not proc.stdout.strip()
    obs = ("PROFILE_OBSERVATION_WINDOW = True" in
           raw.decode("ascii"))
    check(ascii_ok and not net_imports and clean and obs,
          "pd6-hygiene ascii=%s net-imports=%d shipped-clean=%s obs=%s"
          % (ascii_ok, len(net_imports), clean, obs))

    # pd7: SUITES registration face (source scan; delivery chain)
    with open(os.path.join(BASE, "reconcile_all.py"), encoding="utf-8") \
            as f:
        reg = f.read()
    ok = ('("reconcile-daily-profile", "test_reconcile_daily_profile.py",'
          " 7)") in reg
    check(ok, "pd7-registration SUITES row reconcile-daily-profile=7")

    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, PASSES + FAILS), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
