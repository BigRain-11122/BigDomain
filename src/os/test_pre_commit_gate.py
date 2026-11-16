"""pre_commit_gate suite (R2840; AC-HK1..AC-HK8 were pinned in the R2840 row of
src/os/backlog.md BEFORE this file existed - the pin row was committed ahead of
the code, at 50474a48).

What this proves: until R2839 the freeze-round law only ran at closeout, so a
window that wrote `foo_R<N>.py` and died, or a hand `git commit`, still put the
one-off on disk and in history. R2840 gives the law a commit-side call site:

  - the gate owns no shape regex and no tree walk; it asks the law;
  - a staged one-off at or above the freeze is refused by a REAL git commit,
    named, with the commit count unchanged;
  - a permanent module and a sub-freeze one-off still commit;
  - enablement is measured: unset reads DISABLED, --apply is read back;
  - a missing interpreter is a named refusal, never a silent pass;
  - the real tree reads clean and the readings never depend on this host
    having hooks enabled (a fresh clone must not redden).

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import one_off_round_scripts as OOS  # noqa: E402

EXPECTED_CRITERIA = 8
HOOKS = os.path.join(ROOT, "tools", "hooks")
GATE = os.path.join(HOOKS, "pre_commit_gate.py")
ENABLE = os.path.join(HOOKS, "enable.py")
HOOK = os.path.join(HOOKS, "pre-commit")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-pre-commit-gate"

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


def read(path):
    with open(path, "rb") as fh:
        return fh.read()


def text(path):
    return read(path).decode("utf-8", "replace")


def run(cmd, cwd):
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def make_world():
    """A real git work tree holding only the gate, the law and a baseline."""
    world = tempfile.mkdtemp(prefix="hk-world-")
    os.makedirs(os.path.join(world, "tools", "hooks"))
    for name in ("pre-commit", "pre_commit_gate.py", "enable.py"):
        shutil.copy2(os.path.join(HOOKS, name),
                     os.path.join(world, "tools", "hooks", name))
    os.makedirs(os.path.join(world, "src", "os"))
    shutil.copy2(os.path.join(BASE, "one_off_round_scripts.py"),
                 os.path.join(world, "src", "os", "one_off_round_scripts.py"))
    run(["git", "init", "-q"], world)
    for key, value in (("user.email", "hook@example.invalid"),
                       ("user.name", "Hook World"),
                       ("core.autocrlf", "false"),
                       ("core.hooksPath", "tools/hooks")):
        run(["git", "config", key, value], world)
    return world


def write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


def commit(world, message):
    return run(["git", "commit", "-q", "-m", message], world)


def commits(world):
    code, out, _ = run(["git", "rev-list", "--count", "HEAD"], world)
    return int(out.strip()) if code == 0 and out.strip().isdigit() else 0


# AC-HK1 - one shape owner: the law's regex, never a second one here.
gate_src = text(GATE)
raw_gate = read(GATE)
check("import one_off_round_scripts" in gate_src
      and "round_of(" in gate_src
      and "FREEZE_ROUND" in gate_src
      and "import re" not in gate_src
      and "re.compile" not in gate_src
      and "os.walk" not in gate_src
      and all(byte < 128 for byte in raw_gate),
      "AC-HK1 gate asks the law for shape and round, owns no regex or walk, ASCII")

try:
    world = make_world()
    write(os.path.join(world, "src", "os", "state_append.py"), "# baseline\n")
    run(["git", "add", "-A"], world)
    base_code, base_out, base_err = commit(world, "baseline")
    base_count = commits(world)

    # AC-HK3 - no false positive. git forwards hook stdout to stderr, so the
    # reading is taken from either stream rather than assumed.
    write(os.path.join(world, "src", "os", "old_R2431.py"), "# sub-freeze\n")
    run(["git", "add", "-A"], world)
    code_sub, out_sub, err_sub = commit(world, "sub-freeze one-off")
    check(base_code == 0 and "HOOK OK" in (base_out + base_err)
          and base_count == 1
          and code_sub == 0 and "HOOK OK" in (out_sub + err_sub)
          and commits(world) == 2,
          "AC-HK3 permanent module and a sub-freeze one-off both commit "
          "(baseline rc=%d, R2431 rc=%d)" % (base_code, code_sub))

    # AC-HK2 - birth-site refusal by a REAL commit, count unchanged.
    write(os.path.join(world, "src", "os", "foo_R2838.py"), "# one-off\n")
    run(["git", "add", "-A"], world)
    before = commits(world)
    code_off, out_off, err_off = commit(world, "one-off must not land")
    check(code_off != 0
          and "E_HOOK_REFUSE" in err_off
          and "src/os/foo_R2838.py" in err_off
          and commits(world) == before,
          "AC-HK2 a staged one-off is refused, named, count unchanged (%d)"
          % before)

    # AC-HK5 - the hook is LF-only and a missing interpreter is a named refusal.
    hook_raw = read(HOOK)
    hook_src = hook_raw.decode("utf-8", "replace")
    check(b"\r" not in hook_raw
          and "E_HOOK_NO_PYTHON" in hook_src
          and "--no-verify" in hook_src,
          "AC-HK5 hook is LF-only, names E_HOOK_NO_PYTHON and the bypass")

    # AC-HK4 - measured enablement: unset reads DISABLED, --apply is read back.
    run(["git", "config", "--unset", "core.hooksPath"], world)
    enable_world = os.path.join(world, "tools", "hooks", "enable.py")
    code_chk, out_chk, err_chk = run([sys.executable, enable_world, "--check"],
                                     world)
    code_app, out_app, _ = run([sys.executable, enable_world, "--apply"], world)
    code_after, out_after, _ = run([sys.executable, enable_world, "--check"],
                                   world)
    check(code_chk == 2 and "E_HK_NOT_ENABLED" in err_chk
          and "DISABLED" in out_chk
          and code_app == 0 and "APPLIED" in out_app
          and code_after == 0 and "ENABLED" in out_after,
          "AC-HK4 enablement measured: DISABLED rc=2, APPLIED, ENABLED rc=0")
finally:
    shutil.rmtree(world, ignore_errors=True)

# AC-HK6 - real-tree readings a fresh clone can reproduce (never "enabled").
report, law_code = OOS.audit(ROOT)
code_rt, out_rt, _ = run([sys.executable, ENABLE, "--check"], ROOT)
code_rt2, out_rt2, _ = run([sys.executable, GATE], ROOT)
check(law_code == 0 and report["verdict"] in ("OK", "NONE")
      and not report["refused"]
      and code_rt in (0, 2) and "hook_present=yes" in out_rt
      and "freeze=" in out_rt
      and code_rt2 == 0 and "HOOK OK" in out_rt2,
      "AC-HK6 real tree: law clean, enable --check honest (rc=%d), gate clean"
      % code_rt)

# AC-HK7 - registration.
runner_src = text(RUNNER)
check('"%s"' % LABEL in runner_src and ", 8)" in runner_src,
      "AC-HK7 %s registered with its criterion count" % LABEL)

# AC-HK8 - the battery leg asks the law BEFORE any suite runs.
main_at = runner_src.find("def main(argv):")
law_row = runner_src.find("law_ok = phase_freeze_law()")
suite_at = runner_src.find("suites_ok = phase_suites()")
check("import one_off_round_scripts as _oor" in runner_src
      and main_at != -1 and law_row > main_at
      and suite_at != -1 and law_row < suite_at,
      "AC-HK8 the freeze law is asked before the first suite")

print("SUITE %s %d/%d criteria"
      % ("PASS" if FAILS == 0 else "FAIL", PASSES, EXPECTED_CRITERIA))
if PASSES + FAILS != EXPECTED_CRITERIA:
    print("SUITE COUNT MISMATCH ran=%d expected=%d"
          % (PASSES + FAILS, EXPECTED_CRITERIA))
    FAILS += 1
sys.exit(0 if FAILS == 0 else 1)
