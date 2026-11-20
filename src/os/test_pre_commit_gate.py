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

R2933 adds the tree face (AC-CGH1..AC-CGH5): the same shipped writer census,
asked over the WORKING TREE, refuses an unstaged shell capture and a file whose
INDEX bytes are healthy while its DISK bytes are not - neither of which the
staged face can see. All five criteria are pinned in src/os/backlog.md BEFORE
the code and measured here on real git worlds: two refusals fire in one run
without masking each other, a missing census law or baseline is a NAMED
refusal, reader_refused stays informational exactly as R2932 decided, and the
live tree's file count agrees with the closeout gate because both ask one law.
Honest boundary: the world carries the census's whole import chain by hand, so
a new import inside that chain reddens this suite loudly instead of silently
grading a census that is not the shipped one.

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

EXPECTED_CRITERIA = 21
EXPECTED_CHECKS = 32
HOOKS = os.path.join(ROOT, "tools", "hooks")
GATE = os.path.join(HOOKS, "pre_commit_gate.py")
ENABLE = os.path.join(HOOKS, "enable.py")
HOOK = os.path.join(HOOKS, "pre-commit")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
RECONCILE = RUNNER
CENSUS = os.path.join(BASE, "qa_writer_census.py")
DIALECT = os.path.join(BASE, "evidence_dialect.py")
PROBE = os.path.join(BASE, "qa_decode_probe.py")
MATRIX = os.path.join(SRC, "sandbox", "suite_matrix.py")
LABEL = "os-pre-commit-gate"

# R2933 AC-CGH3: the tree face asks the shipped census, so a fixture world must
# ship that law and the modules it asks - never a stub, because a stub would
# grade the suite's idea of the census instead of the census.
CHAIN_OS = ("qa_writer_census.py", "qa_decode_probe.py",
            "matrix_stamp_provenance_line.py", "stamp_text_coverage.py",
            "patterns_label_readability.py",
            "patterns_label_readability_render_consumer.py",
            "patterns_non_label_text_readability.py",
            "artifact_disk_text_readability.py",
            "evidence_name_text_coverage.py")
CHAIN_SANDBOX = ("suite_matrix.py", "reconcile_all.py")
FREEZE_CODE = (
    "import os, sys\n"
    "sys.path.insert(0, os.path.join('src', 'os'))\n"
    "import qa_writer_census as C\n"
    "lines, code, _base = C.write_baseline('qa', os.path.join('qa', "
    "C.BASELINE_NAME))\n"
    "print(lines[0])\n"
    "sys.exit(code)\n"
)

PASSES = 0
FAILS = 0
LABELS = []


def check(ok, label):
    global PASSES, FAILS
    LABELS.append(label)
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
    os.makedirs(os.path.join(world, "src", "sandbox"))
    shutil.copy2(os.path.join(BASE, "one_off_round_scripts.py"),
                 os.path.join(world, "src", "os", "one_off_round_scripts.py"))
    # R2933: the tree face reads the SHIPPED census, so the world carries it
    # and the modules it asks. Measured chain (not guessed): the census asks
    # qa_decode_probe, which asks suite_matrix, which asks the stamp/readability
    # cluster - the same shape R2926 met on the dialect face. It is enumerated
    # by hand on purpose: if the chain grows, the freeze below fails LOUDLY
    # instead of letting the suite grade a census that is not the shipped one.
    for name in CHAIN_OS:
        shutil.copy2(os.path.join(BASE, name),
                     os.path.join(world, "src", "os", name))
    for name in CHAIN_SANDBOX:
        shutil.copy2(os.path.join(SRC, "sandbox", name),
                     os.path.join(world, "src", "sandbox", name))
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
    # A frozen world: one healthy tee evidence file and the baseline the census
    # derives from it, so the tree face is graded against a real baseline rather
    # than an empty promise. Freezing in a subprocess keeps the world's law out
    # of this suite's own imports.
    write(os.path.join(world, "qa", "seed.log"), "PASS seed row\n")
    if with_dialect:
        code_f, out_f, err_f = run([sys.executable, "-c", FREEZE_CODE], world)
        if code_f != 0:
            raise RuntimeError("fixture baseline freeze failed rc=%d %s"
                               % (code_f, (err_f or out_f).strip()[:200]))
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


def snapshot(folder):
    """Bytes and mtime per file: the read-only face measured, not asserted."""
    rows = {}
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        with open(path, "rb") as fh:
            rows[name] = (fh.read(), os.stat(path).st_mtime_ns)
    return rows


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

world = None
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
    if world:
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

# AC-CGH1 - R2933: an UNSTAGED shell-capture file is refused by a REAL commit.
# The staged face reads the index, so this file never reaches it - which is the
# window R2926 could not see and the reason the tree face exists.
world3 = make_world()
try:
    run(["git", "add", "-A"], world3)
    code_b3, out_b3, err_b3 = commit(world3, "baseline")
    base_n = commits(world3)
    write_bytes(os.path.join(world3, "qa", "leak-R2933.log"),
                u"AI \u5224\u5b9a".encode("utf-8") + b"\r\nPASS row\r\n")
    write(os.path.join(world3, "src", "os", "state_append.py"), "# unrelated\n")
    run(["git", "add", "src/os/state_append.py"], world3)
    code_l1, out_l1, err_l1 = commit(world3, "a leak that was never staged")
    check(code_b3 == 0 and code_l1 != 0
          and "E_HOOK_TREE" in err_l1
          and "leak-R2933.log" in err_l1
          and "E_HOOK_EVIDENCE" not in err_l1
          and commits(world3) == base_n,
          "AC-CGH1 an UNSTAGED shell-capture file refuses the commit by name, "
          "count unchanged (%d)" % base_n)
    os.unlink(os.path.join(world3, "qa", "leak-R2933.log"))
    run(["git", "add", "-A"], world3)
    code_l2, out_l2, err_l2 = commit(world3, "the same world without the leak")
    check(code_l2 == 0 and "HOOK OK" in (out_l2 + err_l2)
          and commits(world3) == base_n + 1,
          "AC-CGH1 removing the file returns the SAME world to a commit "
          "(rc=%d count=%d)" % (code_l2, commits(world3)))
finally:
    shutil.rmtree(world3, ignore_errors=True)

# AC-CGH2 - the two faces are independent and each names its own refusal, so
# neither can mask the other in one run; and a healthy INDEX with a rewritten
# disk file refuses on the tree face ALONE (the faces are not mirrors).
world4 = make_world()
try:
    run(["git", "add", "-A"], world4)
    commit(world4, "baseline")
    write_bytes(os.path.join(world4, "qa", "staged-bad.log"),
                u"AI \u5224\u5b9a".encode("gbk") + b"\r\nPASS row\r\n")
    write_bytes(os.path.join(world4, "qa", "tree-bad.log"),
                u"AI \u5224\u5b9a".encode("utf-8") + b"\r\nPASS row\r\n")
    run(["git", "add", "qa/staged-bad.log"], world4)
    before_t = commits(world4)
    code_t, out_t, err_t = commit(world4, "both faces in one run")
    check(code_t != 0
          and "E_HOOK_EVIDENCE" in err_t and "E_HOOK_TREE" in err_t
          and "staged-bad.log" in err_t and "tree-bad.log" in err_t
          and commits(world4) == before_t,
          "AC-CGH2 both faces fire in ONE run, each naming its own file "
          "(count unchanged at %d)" % before_t)
    run(["git", "reset", "-q"], world4)
    os.unlink(os.path.join(world4, "qa", "staged-bad.log"))
    os.unlink(os.path.join(world4, "qa", "tree-bad.log"))
    write(os.path.join(world4, "qa", "rewritten.log"), "PASS healthy bytes\n")
    run(["git", "add", "qa/rewritten.log"], world4)
    write_bytes(os.path.join(world4, "qa", "rewritten.log"),
                u"AI \u5224\u5b9a".encode("utf-8") + b"\r\nPASS row\r\n")
    before_r = commits(world4)
    code_r, out_r, err_r = commit(world4, "healthy index, unhealthy disk")
    check(code_r != 0 and "E_HOOK_TREE" in err_r
          and "E_HOOK_EVIDENCE" not in err_r
          and "rewritten.log" in err_r
          and commits(world4) == before_r,
          "AC-CGH2 healthy INDEX bytes with a rewritten disk file refuse on "
          "the tree face ALONE (rc=%d)" % code_r)
finally:
    shutil.rmtree(world4, ignore_errors=True)

# AC-CGH3 - the tree face cannot pass blind (missing law, missing baseline) and
# writes nothing. A world with no evidence dir is a NAMED skip, not a silent
# pass, because the verdict is scoped to qa/ (AC-EVB2 law).
world5 = make_world()
try:
    run(["git", "add", "-A"], world5)
    commit(world5, "baseline")
    gate5 = os.path.join(world5, "tools", "hooks", "pre_commit_gate.py")
    qa5 = os.path.join(world5, "qa")
    before_snap = snapshot(qa5)
    code_p, out_p, err_p = run([sys.executable, gate5], world5)
    after_snap = snapshot(qa5)
    check(code_p == 0 and "HOOK TREE PASS" in out_p
          and before_snap == after_snap,
          "AC-CGH3 a clean frozen world passes and the tree face writes "
          "nothing (rc=%d files=%d)" % (code_p, len(before_snap)))
    os.unlink(os.path.join(world5, "src", "os", "qa_writer_census.py"))
    code_law, out_law, err_law = run([sys.executable, gate5], world5)
    check(code_law == 3 and "E_HOOK_NO_CENSUS_LAW" in err_law,
          "AC-CGH3 a tree without the census law is a NAMED refusal (rc=%d)"
          % code_law)
    shutil.copy2(CENSUS, os.path.join(world5, "src", "os",
                                     "qa_writer_census.py"))
    os.unlink(os.path.join(qa5, "writer-census-baseline.json"))
    code_base, out_base, err_base = run([sys.executable, gate5], world5)
    check(code_base == 3 and "E_HOOK_NO_CENSUS_BASELINE" in err_base,
          "AC-CGH3 a missing baseline is a NAMED refusal (rc=%d)" % code_base)
    shutil.rmtree(qa5)
    code_skip, out_skip, err_skip = run([sys.executable, gate5], world5)
    check(code_skip == 0
          and "HOOK TREE SKIP reason=no-evidence-dir" in out_skip,
          "AC-CGH3 no evidence dir reads a NAMED skip, never a silent pass "
          "(rc=%d)" % code_skip)
finally:
    shutil.rmtree(world5, ignore_errors=True)

# AC-CGH4 - the R2932 decision holds on this face too: a baselined file no
# writer family decodes is PUBLISHED, never gated. The blob is on disk and
# baselined but NOT staged, because the STAGED face refuses any non-tee evidence
# whatever the baseline says (that disagreement is measured under AC-CGH2 and is
# why this criterion is about the tree face, not about the pair).
world6 = make_world()
try:
    write_bytes(os.path.join(world6, "qa", "unreadable.log"),
                b"\xef\xbb\xbf\xff\xff")
    code_f, out_f, err_f = run([sys.executable, "-c", FREEZE_CODE], world6)
    write(os.path.join(world6, "src", "os", "state_append.py"), "# unrelated\n")
    run(["git", "add", "src/os/state_append.py"], world6)
    code_u, out_u, err_u = commit(world6, "an unrelated file, blob untouched")
    check(code_f == 0 and code_u == 0 and "HOOK OK" in (out_u + err_u)
          and commits(world6) == 1,
          "AC-CGH4 a baselined undecodable file does not refuse the round "
          "(rc=%d count=%d)" % (code_u, commits(world6)))
    gate6 = os.path.join(world6, "tools", "hooks", "pre_commit_gate.py")
    code_g, out_g, err_g = run([sys.executable, gate6], world6)
    check(code_g == 0 and "reader_refused=1" in out_g
          and "gating=flags" in out_g
          and "[refuse-read] unreadable.log" in out_g,
          "AC-CGH4 the tree row PUBLISHES reader_refused=1 and gates on flags "
          "only (rc=%d)" % code_g)
finally:
    shutil.rmtree(world6, ignore_errors=True)

# AC-CGH6 - R3096: the DERIVED suite-matrix document is asked at the commit
# site. Five arms, one criterion; the gate delegates to closeout_gate so this
# measures the CALL SITE, not a second copy of the law.
# a) a world that builds no document reads a NAMED skip and still commits.
world7 = make_world()
try:
    write(os.path.join(world7, "notes.txt"), "healthy\n")
    run(["git", "add", "notes.txt"], world7)
    gate7 = os.path.join(world7, "tools", "hooks", "pre_commit_gate.py")
    code_a, out_a, err_a = run([sys.executable, gate7], world7)
    code_ac, _oc, _ec = commit(world7, "AC-CGH6a")
    check(code_a == 0
          and ("HOOK MATRIX SKIP reason=no-derived-doc "
               "doc=docs/sandbox-suite-matrix.md") in out_a
          and "matrix=SKIP" in out_a
          and code_ac == 0 and commits(world7) == 1,
          "AC-CGH6a a world with no derived document prints its SKIP reason "
          "and commits (rc=%d commit=%d)" % (code_a, code_ac))
finally:
    shutil.rmtree(world7, ignore_errors=True)

# b) a world that carries a document but not the law that judges it is a
# NAMED refusal, never a pass (the same rule AC-CGH3 applies to the census).
world8 = make_world()
try:
    write(os.path.join(world8, "docs", "sandbox-suite-matrix.md"),
          "# a document no law in this world judges\n")
    gate8 = os.path.join(world8, "tools", "hooks", "pre_commit_gate.py")
    code_b, out_b, err_b = run([sys.executable, gate8], world8)
    check(code_b == 3 and "E_HOOK_NO_MATRIX_LAW" in (out_b + err_b),
          "AC-CGH6b a document with no judging law is a NAMED refusal "
          "(rc=%d)" % code_b)
finally:
    shutil.rmtree(world8, ignore_errors=True)

# c) the live tree reads DOC-CURRENT, and the face is READ-ONLY: the document's
# bytes and mtime are measured before and after the run.
doc_live = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
before = (read(doc_live), os.stat(doc_live).st_mtime_ns)
code_c, out_c, err_c = run([sys.executable, GATE], ROOT)
after = (read(doc_live), os.stat(doc_live).st_mtime_ns)
check(code_c == 0 and "HOOK MATRIX PASS DOC-CURRENT" in out_c
      and "matrix=PASS" in out_c and before == after,
      "AC-CGH6c the live tree reads HOOK MATRIX PASS DOC-CURRENT and the "
      "document's bytes/mtime do not move")

# d) face order: a red tree prints no matrix row at all, so one face's silence
# can never be read as its verdict.
world9 = make_world()
try:
    write(os.path.join(world9, "docs", "sandbox-suite-matrix.md"),
          "# present, but the byte-drift face refuses first\n")
    write(os.path.join(world9, "qa", "unstaged_shell_capture.log"),
          "ROW\r\nsecond line\r\n")
    gate9 = os.path.join(world9, "tools", "hooks", "pre_commit_gate.py")
    code_d, out_d, err_d = run([sys.executable, gate9], world9)
    check(code_d == 1 and "E_HOOK_TREE" in (out_d + err_d)
          and "HOOK MATRIX" not in (out_d + err_d),
          "AC-CGH6d a red byte-drift face prints no matrix row (rc=%d)"
          % code_d)
finally:
    shutil.rmtree(world9, ignore_errors=True)

# e) the face owns no second law: a red answer from closeout_gate.check_matrix
# becomes E_HOOK_MATRIX with the law's own line carried through verbatim.
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("gate_under_test_R3096", GATE)
_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gate)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import closeout_gate as CG6  # noqa: E402
_original = CG6.check_matrix
CG6.check_matrix = lambda root, doc=None: (False, "RED-LEG rows=3/4")
try:
    kind_e, lines_e = _gate.matrix_face(ROOT)
finally:
    CG6.check_matrix = _original
check(kind_e == "REFUSED" and lines_e
      and lines_e[0].startswith("E_HOOK_MATRIX ")
      and "RED-LEG rows=3/4" in lines_e[0],
      "AC-CGH6e a red law becomes E_HOOK_MATRIX carrying the law's own line")

# AC-CGH5 - the live tree: the face is measured on the shipped repo, and its
# file count agrees with the closeout gate because both ask one law.
code_g5, out_g5, err_g5 = run([sys.executable, GATE], ROOT)
qa_live = os.path.join(ROOT, "qa")
disk_logs = len([n for n in os.listdir(qa_live) if n.endswith(".log")])
check(code_g5 == 0
      and ("HOOK TREE PASS files=%d flags=0 reader_refused=0 gating=flags"
           % disk_logs) in out_g5,
      "AC-CGH5 the live tree reads HOOK TREE PASS with a DERIVED count (%d)"
      % disk_logs)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import closeout_gate as CG  # noqa: E402
import qa_writer_census as CW  # noqa: E402
_lines_cg, rc_cg, verdict_cg = CG.evaluate(
    qa_live, CW.default_baseline_path(qa_live))
check(rc_cg == 0 and verdict_cg.get("files") == disk_logs,
      "AC-CGH5 the closeout gate and the commit tree face read the SAME count "
      "(%s)" % verdict_cg.get("files"))

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

total = PASSES + FAILS
criteria = set()
for name in LABELS:
    token = name.split(" ", 1)[0]
    for cut in range(len(token), 0, -1):
        if token[cut - 1].isdigit():
            criteria.add(token[:cut])
            break
print("suite: %d assertions over %d criteria" % (total, len(criteria)))
# The pair states ASSERTIONS (what actually ran); the declared criteria count
# above is what the battery compares against the registry, so the two numbers
# never have to be the same number.
print("SUITE %s %d/%d checks"
      % ("PASS" if FAILS == 0 else "FAIL", total, total))
if total != EXPECTED_CHECKS or len(criteria) != EXPECTED_CRITERIA:
    print("SUITE COUNT MISMATCH ran=%d expected=%d criteria=%d expected=%d"
          % (total, EXPECTED_CHECKS, len(criteria), EXPECTED_CRITERIA))
    FAILS += 1
sys.exit(0 if FAILS == 0 else 1)
