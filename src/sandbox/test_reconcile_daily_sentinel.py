"""Reconcile-daily sentinel wiring suite (R1714; criteria AC-FS1..AC-FS6
pre-registered in state/queue/tech.md before this code existed - honesty
law). Exit 0 = all green. Stdlib only, ASCII source, zero network.

Checks:
  fs1-live-sentinel   real run_sentinel on the true tree (AC-FS4)
  fs2-aggregate-drift stub (runner=0, sentinel=2) -> daily exit 2 (AC-FS2)
  fs3-aggregate-runner-fail stub (3,0) -> exit 3, sentinel still logged
  fs4-sentinel-argv   captured argv == sentinel_command(), cwd=BASE (FS1)
  fs5-hygiene         ASCII + no-net imports + shipped files clean
  fs6-same-day-suffix two stub runs -> -2 suffix, no overwrite (AC-FS3)
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


def stub_world(qa_dir, runner_code, sentinel_code, sentinel_out):
    """Install subprocess stubs + QA sandbox; return captured dict."""
    captured = {}

    def fake_call(cmd, *a, **kw):
        captured["runner_cmd"] = cmd
        return runner_code

    def fake_run(cmd, **kw):
        captured["sentinel_cmd"] = cmd
        captured["sentinel_kwargs"] = kw
        return FakeProc(sentinel_code, sentinel_out)

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


def main():
    real_call, real_run, real_qa = subprocess.call, subprocess.run, RD.QA

    # fs1: live sentinel on the true tree (no stubs installed yet)
    tmp = tempfile.mkdtemp(prefix="sentinel-live-")
    try:
        log = os.path.join(tmp, "sentinel-live.log")
        code = RD.run_sentinel(log)
        with open(log, encoding="utf-8") as f:
            text = f.read()
        ok = (code == 0
              and RD.SENTINEL_MARKER in text
              and "verdict CLEAN" in text
              and "sentinel exit=0" in text
              and text.count(RD.SENTINEL_MARKER) == 1
              and len(re.findall(r"(?m)^PASS domain=", text)) == 5)
        check(ok, "fs1-live-sentinel exit=%d marker+CLEAN+5-domains" % code)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # fs2: runner clean, sentinel drift -> daily exit 2, verdict FAIL
    tmp = tempfile.mkdtemp(prefix="sentinel-drift-")
    try:
        cap = stub_world(tmp, 0, 2, "PASS domain=ledger\nFAIL domain=pay "
                                    "baseline drift\nverdict DRIFT domains=1")
        code, out = run_main_capture()
        with open(os.path.join(tmp, os.listdir(tmp)[0]),
                  encoding="utf-8") as f:
            text = f.read()
        ok = (code == 2
              and "verdict=FAIL" in out
              and "sentinel=drift(exit=2)" in out
              and "runner_exit=0" in out
              and RD.SENTINEL_MARKER in text
              and "baseline drift" in text
              and "sentinel exit=2" in text)
        check(ok, "fs2-aggregate-drift (0,2)->exit=%d FAIL drift" % code)
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # fs3: runner fails, sentinel clean -> runner exit propagates,
    # sentinel section still appended (failed day must not skip drift)
    tmp = tempfile.mkdtemp(prefix="sentinel-rfail-")
    try:
        cap = stub_world(tmp, 3, 0, "verdict CLEAN domains=5")
        code, out = run_main_capture()
        log = os.path.join(tmp, os.listdir(tmp)[0])
        with open(log, encoding="utf-8") as f:
            text = f.read()
        ok = (code == 3
              and "runner_exit=3" in out
              and "sentinel=ok" in out
              and RD.SENTINEL_MARKER in text
              and "sentinel exit=0" in text)
        check(ok, "fs3-aggregate-runner-fail (3,0)->exit=%d sentinel kept"
              % code)
        # fs4: argv wiring captured during fs3 stub world
        ok = (cap["sentinel_cmd"] == RD.sentinel_command()
              and cap["sentinel_kwargs"].get("cwd") == BASE
              and "--check" in cap["sentinel_cmd"]
              and cap["sentinel_cmd"][1].startswith(BASE)
              and cap["sentinel_cmd"][3].startswith(BASE))
        check(ok, "fs4-sentinel-argv BASE-derived chain+check cwd=BASE")
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    # fs5: hygiene - ASCII source, no network imports, shipped untouched
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
               os.path.join(BASE, "migration_chains.json")]
    shipped += sorted(glob.glob(os.path.join(BASE, "*", "config.json")))
    rel = [os.path.relpath(p, REPO).replace(os.sep, "/") for p in shipped]
    proc = subprocess.run([git_bin, "status", "--porcelain", "--"] + rel,
                           capture_output=True, text=True, cwd=REPO)
    clean = proc.returncode == 0 and not proc.stdout.strip()
    check(ascii_ok and not net_imports and clean,
          "fs5-hygiene ascii=%s net-imports=%d shipped-clean=%s"
          % (ascii_ok, len(net_imports), clean))

    # fs6: same-day rerun -> -2 suffix, earlier evidence never overwritten
    tmp = tempfile.mkdtemp(prefix="sentinel-suffix-")
    try:
        stub_world(tmp, 0, 0, "verdict CLEAN domains=5")
        code1, out1 = run_main_capture()
        log1 = re.search(r"log=(\S+)", out1).group(1)
        code2, out2 = run_main_capture()
        log2 = re.search(r"log=(\S+)", out2).group(1)
        ok = (code1 == 0 and code2 == 0
              and log1 != log2
              and os.path.exists(log1) and os.path.exists(log2)
              and log2.endswith("-2.log")
              and "sentinel=ok" in out1 and "sentinel=ok" in out2)
        check(ok, "fs6-same-day-suffix second=%s distinct no-overwrite"
              % os.path.basename(log2))
    finally:
        restore(real_call, real_run, real_qa)
        shutil.rmtree(tmp, ignore_errors=True)

    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, PASSES + FAILS), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
