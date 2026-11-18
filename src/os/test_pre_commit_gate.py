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

sys.path.insert(0, os.path.join(SRC, "sandbox"))
import reconcile_all as RA  # SHELL_CAPTURE_LABEL, single source (AC-EVB3)

EXPECTED_CRITERIA = 15
HOOKS = os.path.join(ROOT, "tools", "hooks")
GATE = os.path.join(HOOKS, "pre_commit_gate.py")
ENABLE = os.path.join(HOOKS, "enable.py")
HOOK = os.path.join(HOOKS, "pre-commit")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
CENSUS = os.path.join(BASE, "qa_writer_census.py")
DIALECT = os.path.join(BASE, "evidence_dialect.py")
PROBE = os.path.join(BASE, "qa_decode_probe.py")
MATRIX = os.path.join(SRC, "sandbox", "suite_matrix.py")
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


def make_world(with_dialect=True):
    """A real git work tree holding only the gate, the laws and a baseline."""
    world = tempfile.mkdtemp(prefix="hk-world-")
    os.makedirs(os.path.join(world, "tools", "hooks"))
    for name in ("pre-commit", "pre_commit_gate.py", "enable.py"):
        shutil.copy2(os.path.join(HOOKS, name),
                     os.path.join(world, "tools", "hooks", name))
    os.makedirs(os.path.join(world, "src", "os"))
    shutil.copy2(os.path.join(BASE, "one_off_round_scripts.py"),
                 os.path.join(world, "src", "os", "one_off_round_scripts.py"))
    if with_dialect:
        # AC-EVB5: the dialect law travels with the gate. It is a LEAF
        # module by construction, so the world needs nothing else for it.
        shutil.copy2(DIALECT, os.path.join(world, "src", "os",
                                           "evidence_dialect.py"))
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


def write_bytes(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(payload)


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

    # AC-EVB1 - R2926: a staged evidence file in a non-tee dialect is refused
    # at the commit, named, and the commit count does not move.
    # (The AC-HK2 one-off is still staged after its own refusal - a refused
    # commit changes nothing - so clear it before the next commit is read.)
    run(["git", "reset", "-q"], world)
    os.unlink(os.path.join(world, "src", "os", "foo_R2838.py"))
    write_bytes(os.path.join(world, "qa", "utf16-evidence.log"),
                b"\xff\xfe" + "PASS row\n".encode("utf-16-le"))
    run(["git", "add", "-A"], world)
    before_e = commits(world)
    code_e, out_e, err_e = commit(world, "shell-captured evidence must not land")
    check(code_e != 0
          and "E_HOOK_EVIDENCE" in err_e
          and "qa/utf16-evidence.log(ps-utf16)" in err_e
          and commits(world) == before_e,
          "AC-EVB1 staged shell-captured evidence refused by a REAL commit, "
          "named with its class, count unchanged (%d)" % before_e)

    # AC-EVB2 - the gate is scoped to qa/, not to the dialect: the same bytes
    # filed under logs/ commit, and a deleted evidence file is never refused.
    run(["git", "reset", "-q"], world)
    os.unlink(os.path.join(world, "qa", "utf16-evidence.log"))
    write(os.path.join(world, "qa", "healthy.log"), "PASS healthy\n")
    run(["git", "add", "-A"], world)
    commit(world, "healthy tee evidence")
    before_s = commits(world)
    write_bytes(os.path.join(world, "logs", "archived-sample.log"),
                b"\xff\xfe" + "archived\n".encode("utf-16-le"))
    run(["git", "rm", "-q", "qa/healthy.log"], world)
    run(["git", "add", "-A"], world)
    code_s, out_s, err_s = commit(world, "archive sample plus evidence delete")
    check(code_s == 0 and "HOOK OK" in (out_s + err_s)
          and commits(world) == before_s + 1,
          "AC-EVB2 non-qa/ sample and an evidence deletion both commit "
          "(rc=%d %s)" % (code_s, (err_s + out_s).strip()[:160]))

    # AC-EVB3 - the label is not the law, measured both ways.
    write_bytes(os.path.join(world, "qa", "unlabeled-tee.log"),
                "PASS no label here\n".encode("utf-8"))
    run(["git", "add", "-A"], world)
    before_l = commits(world)
    code_l, out_l, err_l = commit(world, "unlabeled tee evidence")
    label_bytes = RA.SHELL_CAPTURE_LABEL.encode("ascii")
    write_bytes(os.path.join(world, "qa", "labeled-capture.log"),
                label_bytes + b"\r\nPASS row\r\n")
    run(["git", "add", "-A"], world)
    code_lc, out_lc, err_lc = commit(world, "labeled non-tee evidence")
    check(code_l == 0 and "HOOK OK" in (out_l + err_l)
          and commits(world) == before_l + 1
          and code_lc != 0 and "E_HOOK_EVIDENCE" in err_lc
          and "labeled-capture.log(pwsh-capture)" in err_lc,
          "AC-EVB3 label absent commits, label present in a bad dialect is "
          "refused (rc=%d/%d)" % (code_l, code_lc))

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

# AC-EVB4 - one dialect law: the census delegates instead of keeping a copy,
# and the baselined label split is published from that same module.
census_src = text(CENSUS)
dialect_src = text(DIALECT)
code_split = ("import sys\n"
              "sys.path.insert(0, %r)\n"
              "import evidence_dialect as ED\n"
              "rows = [('a.log', ED.classify_bytes(b'PASS\\n', b'LABEL')),"
              " ('b.log', ED.classify_bytes(b'LABEL\\nPASS\\n', b'LABEL'))]\n"
              "s = ED.label_coverage(rows)\n"
              "print('SPLIT', s['labeled'], s['unlabeled'],"
              " s['labeled_names'])\n" % BASE)
rc_sp, out_sp, err_sp = run([sys.executable, "-c", code_split], ROOT)
code_live, out_live, _ = run([sys.executable, CENSUS, "--check"], ROOT)
check("ED.classify_bytes" in census_src
      and "ED.label_coverage" in census_src
      and 'row["class"] = "nul-bytes"' not in census_src
      and 'row["class"] = "nul-bytes"' in dialect_src
      and "SPLIT 1 1 ['b.log']" in out_sp
      and ("labeled_baselined=" in out_live
           and "unlabeled_baselined=" in out_live),
      "AC-EVB4 one dialect law (census delegates, no branch copy), label "
      "split published (rc=%d, split rc=%d)" % (code_live, rc_sp))

# AC-EVB5 - a missing classifier is a NAMED refusal, never a clean commit.
world2 = make_world(with_dialect=False)
try:
    write(os.path.join(world2, "qa", "anything.log"), "PASS row\n")
    run(["git", "add", "-A"], world2)
    code_nl, out_nl, err_nl = run(
        [sys.executable, os.path.join(world2, "tools", "hooks",
                                      "pre_commit_gate.py")], world2)
    check(code_nl == 3 and "E_HOOK_NO_EVIDENCE_LAW" in err_nl,
          "AC-EVB5 missing dialect law refuses by name (rc=%d)" % code_nl)
finally:
    shutil.rmtree(world2, ignore_errors=True)

# AC-HK7 - registration (the count is the suite's own, not a second number).
runner_src = text(RUNNER)
check('"%s"' % LABEL in runner_src and ", %d)" % EXPECTED_CRITERIA in runner_src,
      "AC-HK7 %s registered with its criterion count (%d)"
      % (LABEL, EXPECTED_CRITERIA))

# AC-HK8 - the battery leg asks the law BEFORE any suite runs.
main_at = runner_src.find("def main(argv):")
law_row = runner_src.find("law_ok = phase_freeze_law()")
suite_at = runner_src.find("suites_ok = phase_suites()")
check("import one_off_round_scripts as _oor" in runner_src
      and main_at != -1 and law_row > main_at
      and suite_at != -1 and law_row < suite_at,
      "AC-HK8 the freeze law is asked before the first suite")

# AC-HK9 - R2842: asking the law before the suites was not enough - the runner
# still burned the whole leg and only said FAIL at the end. The refusal is now
# the battery's FIRST exit. Measured in a world that carries NO suite files at
# all, so any 'SUITE ' row would prove the runner walked past the law.
_world = tempfile.mkdtemp(prefix="hk9-world-")
try:
    os.makedirs(os.path.join(_world, "src", "sandbox"))
    os.makedirs(os.path.join(_world, "src", "os"))
    shutil.copy2(RUNNER, os.path.join(_world, "src", "sandbox",
                                     "reconcile_all.py"))
    shutil.copy2(os.path.join(BASE, "one_off_round_scripts.py"),
                 os.path.join(_world, "src", "os", "one_off_round_scripts.py"))
    with open(os.path.join(_world, "src", "os", "foo_R2838.py"), "w") as fh:
        fh.write("# deliberate one-off at the freeze round\n")
    rc_r, out_r, err_r = run(
        [sys.executable, os.path.join(_world, "src", "sandbox",
                                      "reconcile_all.py")], _world)
    rows = out_r.splitlines()
    suite_rows = [ln for ln in rows if ln.startswith("SUITE ")]
    rec_rows = [ln for ln in rows if "RECONCILE" in ln]
    check(rc_r == 1 and "FREEZE LAW REFUSE" in out_r
          and "foo_R2838.py" in out_r
          and "RUNNER FAIL (freeze law refused" in out_r
          and not suite_rows and not rec_rows,
          "AC-HK9 refused tree aborts before the first suite "
          "(rc=%d suites=%d reconcile=%d)" % (rc_r, len(suite_rows),
                                              len(rec_rows)))

    # AC-HK10 - the answer is read from the world, not from prose: the same
    # world's own runner module must return False, the live tree must not, and
    # the verdict branch must no longer re-judge a law that already returned.
    code = ("import sys\n"
            "sys.path.insert(0, %r)\n"
            "import reconcile_all as R\n"
            "print('LAW', R.phase_freeze_law())\n"
            % os.path.join(_world, "src", "sandbox"))
    rc_d, out_d, _ = run([sys.executable, "-c", code], _world)
    live_report, live_code = OOS.audit(ROOT)
    main_src = runner_src[runner_src.find("def main(argv):"):]
    check("LAW False" in out_d and rc_d == 0
          and live_code == 0 and not live_report["refused"]
          and main_src.count("freeze law refused") == 1
          and "if FAILS == 0 and suites_ok:" in main_src
          and "and law_ok" not in main_src,
          "AC-HK10 law read from the world (refused=False, live=clean), "
          "one refusal site, verdict independent")
finally:
    shutil.rmtree(_world, ignore_errors=True)

print("SUITE %s %d/%d criteria"
      % ("PASS" if FAILS == 0 else "FAIL", PASSES, EXPECTED_CRITERIA))
if PASSES + FAILS != EXPECTED_CRITERIA:
    print("SUITE COUNT MISMATCH ran=%d expected=%d"
          % (PASSES + FAILS, EXPECTED_CRITERIA))
    FAILS += 1
sys.exit(0 if FAILS == 0 else 1)
