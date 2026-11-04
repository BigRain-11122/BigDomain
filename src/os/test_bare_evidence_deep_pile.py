"""bare_evidence_deep_pile suite (R2432; criteria AC-BEDP1..AC-BEDP6 were

pre-registered inside the R2404 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the pile measurement walks a DECLARED depth asked at call
time, so a bare name filed at qa/rounds/<name> is resolved instead of being
reported absent; a name that is not found while the tree really continues
below the searched depth refuses with a code that NAMES that depth; a name
whose absence is proved keeps the shipped E_BEPR_NOT_FOUND spelling; two
copies inside the searched depth still refuse as ambiguous; and the CLI keeps
0/2/3/5 with a byte-stable --json.

Every world below is a stand-in root; nothing under the shipped tree is
written. Stdlib only, ASCII source, zero network, no clock. Exit 0 = green.
"""

import ast
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import bare_evidence_deep_pile as BEDP  # noqa: E402
import bare_evidence_pile_refusal as BEPR  # noqa: E402
import matrix_evidence_pile_consistency as MEPC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "bare_evidence_deep_pile.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-bare-evidence-deep-pile"
VOCAB = ("matrix", "fingerprint", "profile", "census")
BARE = "reconcile-all-R9101.log"

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


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def log_text(round_label="R9101"):
    lines = ["SECTION %s PASS detail" % name for name in VOCAB]
    lines.append("VERDICT %s PASS" % round_label)
    return "\n".join(lines) + "\n"


def make_world(rel_piles, bare=BARE, filler=True):
    """A stand-in root; every pile is a root-relative directory."""
    world = tempfile.mkdtemp(prefix="bigdomain-bedp-w-")
    for pile in rel_piles:
        write(os.path.join(world, pile, bare), log_text())
    if filler:
        write(os.path.join(world, "qa", "notes.log"), "no evidence here\n")
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode, proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def tree_snapshot(root):
    rows = []
    for folder, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(folder, name)
            rows.append((os.path.relpath(path, root),
                         os.path.getsize(path)))
    return rows


def ac_bedp1():
    """A bare name at depth 2 resolves and the tool argument names it."""
    world = make_world([os.path.join("qa", "rounds")])
    report = BEDP.reading(BARE, world)
    argument = MEPC.tool_argument(BARE, world)
    placed = MEPC.placement(BARE, world)
    shipped = BEPR.reading(BARE, world)
    rc, out, _ = run_cli(["--check", BARE, "--root", world])
    ok = (report["verdict"] == "RESOLVED"
          and report["pile"] == os.path.join("qa", "rounds")
          and report["depth"] == 2
          and argument == os.path.join("qa", "rounds", BARE)
          and placed["verdict"] == "PLACED"
          and placed["same_file"] is True
          and shipped["dir"].replace("\\", "/") == "qa/rounds"
          and rc == 0
          and "qa" in out.replace("\\", "/"))
    if not ok:
        print("  measured: report=%r argument=%r placed=%r shipped=%r rc=%r"
              % (report, argument, placed.get("verdict"),
                 shipped.get("dir"), rc))
    drop_world(world)
    check(ok, "AC-BEDP1 a bare name filed at depth 2 resolves, the matrix "
              "tool argument names that same path, and the shipped R2386 "
              "face reads the same pile")


def ac_bedp2():
    """The depth is asked of the law at CALL time, so a patch moves it."""
    deep = make_world([os.path.join("qa", "rounds", "inner")], filler=False)
    shallow_pick = None
    patched_deep = None
    with_depth_3 = None
    try:
        BEDP.MAX_DEPTH = 3
        with_depth_3 = BEDP.reading(BARE, deep)
        patched_deep = BEDP.resolve(BARE, deep)
        BEDP.MAX_DEPTH = 2
        shallow_pick = BEDP.reading(BARE, deep)
    finally:
        BEDP.MAX_DEPTH = 2
    two_level = make_world([os.path.join("qa", "rounds")])
    original = BEDP.MAX_DEPTH
    try:
        BEDP.MAX_DEPTH = 1
        one_level = BEDP.reading(BARE, two_level)
    finally:
        BEDP.MAX_DEPTH = original
    ok = (with_depth_3["verdict"] == "RESOLVED"
          and with_depth_3["pile"] == os.path.join("qa", "rounds", "inner")
          and with_depth_3["depth"] == 3
          and patched_deep == os.path.join("qa", "rounds", "inner")
          and shallow_pick["verdict"] == "REFUSED"
          and shallow_pick["code"] == BEDP.E_BEDP_BEYOND_DEPTH
          and one_level["verdict"] == "REFUSED"
          and one_level["depth"] == 1
          and one_level["code"] == BEDP.E_BEDP_BEYOND_DEPTH)
    if not ok:
        print("  measured: depth3=%r deep=%r depth2=%r depth1=%r"
              % (with_depth_3, patched_deep, shallow_pick, one_level))
    drop_world(deep)
    drop_world(two_level)
    check(ok, "AC-BEDP2 the declared depth is read at CALL time: patching it "
              "to 3 resolves a depth-3 name and putting it back to 2 refuses "
              "that same name naming depth 2")


def ac_bedp3():
    """Beyond the declared depth refuses naming the depth searched."""
    world = make_world([os.path.join("qa", "a", "b")], filler=False)
    beyond = BEDP.reading(BARE, world)
    rc, out, _ = run_cli(["--check", BARE, "--root", world])
    flat = make_world([])
    proved = BEDP.reading(BARE, flat)
    ok = (beyond["verdict"] == "REFUSED"
          and beyond["code"] == BEDP.E_BEDP_BEYOND_DEPTH
          and "depth 2" in beyond["detail"]
          and rc == 2
          and BEDP.E_BEDP_BEYOND_DEPTH in out
          and "depth 2" in out
          and proven_code_ok(proved))
    if not ok:
        print("  measured: beyond=%r rc=%r out=%r proved=%r"
              % (beyond, rc, out.strip(), proved))
    drop_world(world)
    drop_world(flat)
    check(ok, "AC-BEDP3 a name beyond the declared depth refuses with a code "
              "that names the depth searched, never E_BEPR_NOT_FOUND alone, "
              "while a proved absence keeps the shipped code")


def proven_code_ok(report):
    return (report["verdict"] == "REFUSED"
            and report["code"] == "E_BEPR_NOT_FOUND"
            and report["code"] == BEPR.E_BEPR_NOT_FOUND
            and "absence is proved" in report["detail"])


def ac_bedp4():
    """Two copies inside the searched depth refuse as ambiguous."""
    world = make_world(["qa", os.path.join("qa", "rounds")])
    twice = BEDP.reading(BARE, world)
    rc, out, _ = run_cli(["--check", BARE, "--root", world])
    shipped = BEPR.reading(BARE, world)
    flat_twice = make_world(["qa", "lab"])
    flat_report = BEPR.reading(BARE, flat_twice)
    ok = (twice["verdict"] == "REFUSED"
          and twice["code"] == BEDP.E_BEPR_AMBIGUOUS
          and twice["code"] == BEPR.E_BEPR_AMBIGUOUS
          and os.path.join("qa", "rounds") in twice["detail"]
          and "qa" in twice["detail"]
          and rc == 2
          and BEPR.E_BEPR_AMBIGUOUS in out
          and "qa/rounds" in out.replace("\\", "/")
          and shipped["code"] == BEPR.E_BEPR_AMBIGUOUS
          and flat_report["code"] == BEPR.E_BEPR_AMBIGUOUS)
    if not ok:
        print("  measured: twice=%r rc=%r shipped=%r flat=%r"
              % (twice, rc, shipped.get("code"), flat_report.get("code")))
    drop_world(world)
    drop_world(flat_twice)
    check(ok, "AC-BEDP4 two copies inside the searched depth refuse as "
              "ambiguous naming both piles, and the R2386 one-level "
              "ambiguity reading is unchanged")


def ac_bedp5():
    """CLI 0/2/3/5 with a byte-stable --json over the pinned keys."""
    world = make_world([os.path.join("qa", "rounds")])
    missing_root = os.path.join(world, "no-such-root")
    rc_clean, out_clean, _ = run_cli(["--check", BARE, "--root", world])
    rc_json_1, json_1, _ = run_cli(["--check", BARE, "--root", world,
                                    "--json"])
    rc_json_2, json_2, _ = run_cli(["--check", BARE, "--root", world,
                                    "--json"])
    rc_refuse, _, _ = run_cli(["--check", "no-such-R9102.log",
                               "--root", world])
    rc_unreadable, out_bad, _ = run_cli(["--check", BARE,
                                         "--root", missing_root])
    rc_flags, _, _ = run_cli(["--check", "--nope"])
    payload = json.loads(json_1)
    ok = (rc_clean == 0
          and "RESOLVED" in out_clean
          and rc_json_1 == 0
          and json_1 == json_2
          and list(payload.keys()) == list(BEDP.READING_KEYS)
          and json_1.endswith("\n")
          and json_1.isascii()
          and rc_refuse == 2
          and rc_unreadable == 3
          and BEDP.E_BEDP_BAD_ROOT in out_bad
          and rc_flags == 5)
    if not ok:
        print("  measured: rc=%r/%r/%r/%r/%r stable=%r keys=%r tail=%r"
              % (rc_clean, rc_json_1, rc_refuse, rc_unreadable, rc_flags,
                 json_1 == json_2, list(payload.keys()),
                 json_1[-1:]))
    drop_world(world)
    check(ok, "AC-BEDP5 the CLI answers 0/2/3/5 and its --json is byte-stable "
              "over the pinned keys, ASCII, one trailing newline")


def ac_bedp6():
    """Writes nothing, no clock, ASCII, stdlib only, own label and suite."""
    world = make_world([os.path.join("qa", "rounds")])
    before = tree_snapshot(world)
    BEDP.reading(BARE, world)
    run_cli(["--check", BARE, "--root", world])
    run_cli(["--check", BARE, "--root", world, "--json"])
    after = tree_snapshot(world)
    drop_world(world)
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = True
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
        text = raw.decode("ascii", "replace")
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    stdlib_only = imported <= {"json", "os", "sys"}
    no_clock = ("import time" not in text and "datetime" not in text
                and "time.time" not in text)
    with open(RUNNER, "rb") as handle:
        runner_text = handle.read().decode("ascii", "replace")
    wired = '"%s"' % LABEL in runner_text
    suite_exists = os.path.isfile(
        os.path.join(BASE, "test_bare_evidence_deep_pile.py"))
    ok = (before == after and ascii_ok and stdlib_only and no_clock
          and wired and suite_exists)
    if not ok:
        print("  measured: unchanged=%r ascii=%r imports=%r clock=%r "
              "wired=%r suite=%r"
              % (before == after, ascii_ok, sorted(imported), no_clock,
                 wired, suite_exists))
    check(ok, "AC-BEDP6 writes nothing, reads no clock, pure ASCII, stdlib "
              "only, plus its own reconcile label and its own suite file")


def main():
    print("bare_evidence_deep_pile suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_bedp1()
    ac_bedp2()
    ac_bedp3()
    ac_bedp4()
    ac_bedp5()
    ac_bedp6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())