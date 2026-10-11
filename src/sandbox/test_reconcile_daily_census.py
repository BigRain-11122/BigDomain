"""Reconcile-daily writer-census sentinel wiring suite (R1848;
criteria AC-WCD1..AC-WCD7 pre-registered in state/queue/tech.md
before this code existed - honesty law). Exit 0 = all green.
Stdlib only, ASCII source, zero network.

Checks (8):
  cd1-missing-baseline-info  no baseline -> zero subprocess, INFO
                            section, census=not-deployed, exit 0
                            (AC-WCD2)
  cd2-argv-wiring           baseline world: census argv ==
                            census_command(), --check/--dir/cwd=BASE;
                            section + elapsed tail in log (AC-WCD1)
  cd3-aggregate-census-drift (0,0,census=2) -> daily exit 2 FAIL
                            census=drift(exit=2) (AC-WCD3)
  cd4-aggregate-runner-fail  (3,0,census=2) -> runner code propagates,
                            census section still logged (AC-WCD3)
  cd5-sentinel-precedence    (0,2,census=0) -> sentinel gates first,
                            census section still logged (AC-WCD3)
  cd6-refusal-fail           (0,0,census=3) -> exit 3 refusal FAIL
                            census=refusal(exit=3) (AC-WCD4)
  cd7-live-real-tree         real run_census on the true tree + the
                            R1841 baseline -> exit recorded (expected
                            0 = DRIFT-CLEAN); temp log only, the
                            closed daily evidence untouched (AC-WCD5)
  cd8-hygiene                ASCII + no-net imports + shipped clean
                            + criteria-count self-check == 8 (AC-WCD7)
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
REAL_GIT = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                        "Git", "cmd", "git.exe")

EXPECTED_CRITERIA = 8
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
               profile_code, profile_out, census_code, census_out,
               with_baseline):
    """Install three-way subprocess stubs + QA sandbox (R1733 AC-PD4
    routing precedent extended: fingerprint_regen.py -> sentinel stub,
    qa_writer_census.py -> census stub, everything else -> profile
    stub). Creates the writer-census baseline file inside qa_dir when
    with_baseline is True."""
    captured = {}
    if with_baseline:
        with open(os.path.join(qa_dir, RD.CENSUS_BASELINE), "w",
                  encoding="utf-8") as fh:
            fh.write('{"cmd-raw": [], "other": [], '
                     '"ps-utf16": [], "pwsh-capture": []}\n')

    def fake_call(cmd, *a, **kw):
        captured["runner_cmd"] = cmd
        return runner_code

    def fake_run(cmd, **kw):
        joined = " ".join(cmd)
        if "fingerprint_regen.py" in joined:
            captured["sentinel_cmd"] = cmd
            captured["sentinel_kwargs"] = kw
            return FakeProc(sentinel_code, sentinel_out)
        if "qa_writer_census.py" in joined:
            captured["census_cmd"] = cmd
            captured["census_kwargs"] = kw
            return FakeProc(census_code, census_out)
        captured["profile_cmd"] = cmd
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


def one_log(qa_dir):
    return os.path.join(qa_dir, os.listdir(qa_dir)[0])


def main():
    global PASSES, FAILS
    real_call, real_run, real_qa = subprocess.call, subprocess.run, RD.QA

    # cd1: missing baseline -> INFO face, zero census subprocess
    tmp = tempfile.mkdtemp(prefix="census-nobaseline-")
    try:
        cap = stub_world(tmp, 0, 0, "verdict CLEAN domains=5",
                         0, "check: ok", 2,
                         "[flag] never-reached", False)
        code, out = run_main_capture()
        with open(one_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 0
              and "census_cmd" not in cap
              and "profile_cmd" in cap
              and RD.CENSUS_MARKER in text
              and "census baseline missing" in text
              and "probe not deployed" in text
              and "census not-deployed (recorded, not gating)" in text
              and "census=not-deployed" in out
              and "verdict=PASS" in out)
        check(ok, "cd1-missing-baseline-info zero-subproc+INFO+"
              "not-gating exit=%d" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # cd2: argv wiring + section/tail shape in a baseline world
    tmp = tempfile.mkdtemp(prefix="census-argv-")
    try:
        cap = stub_world(tmp, 0, 0, "verdict CLEAN domains=5",
                         0, "check: ok", 0,
                         "mode: check\nverdict: DRIFT-CLEAN\nflags=0",
                         True)
        code, out = run_main_capture()
        with open(one_log(tmp), encoding="utf-8") as f:
            text = f.read()
        cmd = cap.get("census_cmd")
        ok = (code == 0
              and cmd == RD.census_command()
              and "--check" in cmd
              and "--dir" in cmd
              and cmd[1].endswith(os.path.join("os",
                                               "qa_writer_census.py"))
              and cmd[1].startswith(os.path.dirname(BASE))
              and cap["census_kwargs"].get("cwd") == BASE
              and RD.CENSUS_MARKER in text
              and "verdict: DRIFT-CLEAN" in text
              and re.search(r"(?m)^census exit=0 elapsed=[0-9.]+s$",
                            text) is not None
              and "census=ok" in out
              and text.count(RD.CENSUS_MARKER) == 1)
        check(ok, "cd2-argv-wiring src/os-path+--check/--dir+cwd=BASE "
              "+section+elapsed-tail exit=%d" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # cd3: runner+sentinel clean, census drift -> day FAIL exit 2
    tmp = tempfile.mkdtemp(prefix="census-drift-")
    try:
        stub_world(tmp, 0, 0, "verdict CLEAN domains=5",
                   0, "check: ok", 2,
                   "[flag] new-dialect: rogue.log (class=cmd-raw)\n"
                   "flags=1\nverdict: DRIFT-FLAG", True)
        code, out = run_main_capture()
        with open(one_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 2
              and "verdict=FAIL" in out
              and "census=drift(exit=2)" in out
              and "sentinel=ok" in out
              and "[flag] new-dialect: rogue.log" in text
              and re.search(r"(?m)^census exit=2 elapsed=[0-9.]+s$",
                            text) is not None)
        check(ok, "cd3-aggregate-census-drift (0,0,2)->exit=%d FAIL"
              % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # cd4: runner fails, census drift -> runner code propagates, the
    # census section still logged (failed day must not skip the check)
    tmp = tempfile.mkdtemp(prefix="census-rfail-")
    try:
        stub_world(tmp, 3, 0, "verdict CLEAN domains=5",
                   0, "check: ok", 2,
                   "[flag] new-dialect: rogue.log\nverdict: DRIFT-FLAG",
                   True)
        code, out = run_main_capture()
        with open(one_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 3
              and "runner_exit=3" in out
              and "census=drift(exit=2)" in out
              and RD.CENSUS_MARKER in text
              and re.search(r"(?m)^census exit=2 elapsed=[0-9.]+s$",
                            text) is not None)
        check(ok, "cd4-aggregate-runner-fail (3,0,2)->exit=%d census "
              "kept" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # cd5: sentinel drift gates first; census still runs and logs clean
    tmp = tempfile.mkdtemp(prefix="census-sentinel-")
    try:
        stub_world(tmp, 0, 2, "verdict DRIFT domains=1",
                   0, "check: ok", 0,
                   "verdict: DRIFT-CLEAN\nflags=0", True)
        code, out = run_main_capture()
        with open(one_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 2
              and "sentinel=drift(exit=2)" in out
              and "census=ok" in out
              and RD.CENSUS_MARKER in text
              and re.search(r"(?m)^census exit=0 elapsed=[0-9.]+s$",
                            text) is not None)
        check(ok, "cd5-sentinel-precedence (0,2,0)->exit=%d census "
              "still logged" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # cd6: census refusal (empty evidence dir) -> day FAIL exit 3
    tmp = tempfile.mkdtemp(prefix="census-refusal-")
    try:
        stub_world(tmp, 0, 0, "verdict CLEAN domains=5",
                   0, "check: ok", 3,
                   "no *.log candidates under target dir (refusal)",
                   True)
        code, out = run_main_capture()
        with open(one_log(tmp), encoding="utf-8") as f:
            text = f.read()
        ok = (code == 3
              and "verdict=FAIL" in out
              and "census=refusal(exit=3)" in out
              and "no *.log candidates" in text
              and re.search(r"(?m)^census exit=3 elapsed=[0-9.]+s$",
                            text) is not None)
        check(ok, "cd6-refusal-fail (0,0,3)->exit=%d refusal FAIL"
              % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # cd7: live real-tree run (no stubs) - true qa/ + R1841 baseline
    tmp = tempfile.mkdtemp(prefix="census-live-")
    try:
        log = os.path.join(tmp, "census-live.log")
        code, label = RD.run_census(log)
        with open(log, encoding="utf-8") as f:
            text = f.read()
        ok = (code == 0
              and label == "ok"
              and RD.CENSUS_MARKER in text
              and "verdict: DRIFT-CLEAN" in text
              and re.search(r"(?m)^census exit=0 elapsed=[0-9.]+s$",
                            text) is not None
              and "baseline missing" not in text)
        check(ok, "cd7-live-real-tree exit=%d label=%s DRIFT-CLEAN "
              "(closed daily evidence untouched)" % (code, label))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # cd8: hygiene - ASCII sources, no network imports, shipped clean
    src_paths = [os.path.join(BASE, "reconcile_daily.py"),
                 os.path.abspath(__file__)]
    ascii_ok = True
    for sp in src_paths:
        with open(sp, "rb") as f:
            raw = f.read()
        if any(b >= 128 for b in raw):
            ascii_ok = False
    net_imports = []
    with open(src_paths[0], "rb") as f:
        for line in f.read().decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or \
                    stripped.startswith("from "):
                if re.search(r"\b(urllib|requests|socket|http)\b",
                             stripped):
                    net_imports.append(stripped)
    git_bin = REAL_GIT if os.path.exists(REAL_GIT) else \
        shutil.which("git")
    shipped = [os.path.join(os.path.dirname(BASE), "os",
                            "qa_writer_census.py")]
    shipped += sorted(glob.glob(os.path.join(BASE, "*", "config.json")))
    rel = [os.path.relpath(p, REPO).replace(os.sep, "/") for p in shipped]
    proc = subprocess.run([git_bin, "status", "--porcelain", "--"] + rel,
                          capture_output=True, text=True, cwd=REPO)
    clean = proc.returncode == 0 and not proc.stdout.strip()
    check(ascii_ok and not net_imports and clean,
          "cd8-hygiene ascii=%s net-imports=%d shipped-clean=%s"
          % (ascii_ok, len(net_imports), clean))

    total = PASSES + FAILS
    if total != EXPECTED_CRITERIA:
        print("FAIL criteria-count-drift actual=%d expected=%d"
              % (total, EXPECTED_CRITERIA), flush=True)
        FAILS += 1
    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, PASSES + FAILS), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
