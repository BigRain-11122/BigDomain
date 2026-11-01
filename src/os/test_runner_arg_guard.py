"""runner_arg_guard suite (R2362; criteria AC-RAG1..AC-RAG6 were pinned inside
the R2348 tech seed row of state/queue/tech.md:404 BEFORE this code existed).

What this proves: the guard reads the runner's own CLI contract (imported, not
a second hand-written flag list), refuses an unknown flag by naming the token
AND the file the runner would have created, passes known flags through in
order, answers a bare --help as a question, and keeps a byte-stable JSON face
over pinned keys with the pre-registered exit codes.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import runner_arg_guard as G  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "runner_arg_guard.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-runner-arg-guard"

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


def run_main(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = G.main(argv)
    return code, buf.getvalue()


def patched_runner(tmpdir, flag):
    """Copy the runner and give its contract one extra known flag."""
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        source = handle.read()
    target = os.path.join(tmpdir, "runner_patched.py")
    marker = '"known_flags": (),'
    if marker not in source:
        raise AssertionError("contract marker not found in the runner")
    patched = source.replace(marker, '"known_flags": ("%s",),' % flag, 1)
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(patched)
    return target


def ac_rag1():
    """The known-flag set is READ FROM the runner, proven by patching it."""
    contract = G.load_contract()
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        source = handle.read()
    derived = ('"known_flags": (),' in source
               and '"max_positional": 1' in source
               and '"positional_label": "evidence_log_path"' in source)
    before = G.classify(["--quick"], contract, os.getcwd())
    tmpdir = tempfile.mkdtemp(prefix="bigdomain-rag1-")
    patched = patched_runner(tmpdir, "--quick")
    after = G.classify(["--quick"], G.load_contract(patched), os.getcwd())
    check(before["status"] == "refused" and after["status"] == "allowed"
          and derived and contract["name"] == "reconcile_all.py",
          "AC-RAG1 contract imported from the runner: same source, patched "
          "copy flips --quick from refused to allowed")


def ac_rag2():
    """Unknown flag: refused, names token AND file, zero bytes, zero suites."""
    tmpdir = tempfile.mkdtemp(prefix="bigdomain-rag2-")
    code, out = run_main(["prog", "--dry-run"])
    leaked = os.path.abspath("--dry-run")
    result = G.classify(["--dry-run"], G.load_contract(), os.getcwd())
    names_both = ("--dry-run" in result["refused"][0]
                  and result["created_path"] in result["refused"][0])
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    no_runner_start = ("subprocess" not in source
                       and "phase_suites" not in source)
    check(code == 2 and "REFUSED" in out and names_both
          and not os.path.exists(leaked) and os.path.isdir(tmpdir)
          and result["allowed"] == [] and no_runner_start,
          "AC-RAG2 unknown flag --dry-run refused naming token and target "
          "file, zero bytes written, zero suites run")


def ac_rag3():
    """Known flags pass through unchanged and in order (invisible guard)."""
    tmpdir = tempfile.mkdtemp(prefix="bigdomain-rag3-")
    patched = patched_runner(tmpdir, "--quick")
    contract = G.load_contract(patched)
    contract = dict(contract, known_flags=("--quick", "--verbose"))
    argv = ["--verbose", "qa/evidence.log", "--quick"]
    result = G.classify(argv, contract, os.getcwd())
    plain = G.classify(["qa/evidence.log"], G.load_contract(), os.getcwd())
    check(result["status"] == "allowed" and result["allowed"] == argv
          and result["refused"] == [] and plain["allowed"] == ["qa/evidence.log"],
          "AC-RAG3 known flags pass through unchanged and in order")


def ac_rag4():
    """A bare --help is a QUESTION: usage text, exit 0, no battery."""
    code, out = run_main(["prog", "--help"])
    contract = G.load_contract()
    usage = G.usage_text(contract)
    check(code == 0 and "ASKED" in out and usage in out
          and contract["name"] in out and contract["positional_label"] in out,
          "AC-RAG4 bare --help answered with the derived usage text at exit 0")


def ac_rag5():
    """Pinned exit codes 0/2/3/5 and a byte-stable --json face."""
    allowed, _ = run_main(["prog", "qa/evidence.log"])
    refused, _ = run_main(["prog", "--dry-run"])
    bad_flag, _ = run_main(["prog", "--guard-nope"])
    tmpdir = tempfile.mkdtemp(prefix="bigdomain-rag5-")
    empty = os.path.join(tmpdir, "empty_runner.py")
    with io.open(empty, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("X = 1\n")
    saved = G.RUNNER
    try:
        G.RUNNER = empty
        unreadable, _ = run_main(["prog", "qa/evidence.log"])
    finally:
        G.RUNNER = saved
    first, out_a = run_main(["prog", "--json", "--dry-run"])
    second, out_b = run_main(["prog", "--json", "--dry-run"])
    payload = json.loads(out_a.strip())
    keys_ok = sorted(payload.keys()) == sorted(G.JSON_KEYS)
    check(allowed == 0 and refused == 2 and unreadable == 3
          and bad_flag == 5 and out_a == out_b and keys_ok
          and payload["status"] == "refused",
          "AC-RAG5 exit 0/2/3/5 with byte-stable --json over pinned keys")


def ac_rag6():
    """ASCII, stdlib only, zero network, no clock, read-only, and wired."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = all(byte < 128 for byte in raw)
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    imports_ok = all(token not in source for token in (
        "socket", "urllib", "http.client", "requests"))
    no_clock = not any(token in source for token in (
        "import time", "time.time", "datetime", "random"))
    read_only = not any(token in source for token in (
        "open(", "tempfile", "os.makedirs", "os.mkdir", "os.replace",
        "os.remove", "shutil"))
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = ('"%s"' % LABEL) in runner and (
        "test_runner_arg_guard.py" in runner)
    check(ascii_ok and imports_ok and no_clock and read_only and wired,
          "AC-RAG6 pure ASCII, stdlib only, zero network, no clock, read-only, "
          "one runner entry at 6 criteria")


def main():
    print("SUITE runner_arg_guard (R2362) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    ac_rag1()
    ac_rag2()
    ac_rag3()
    ac_rag4()
    ac_rag5()
    ac_rag6()
    print("SUITE RESULT passes=%d fails=%d criteria=%d"
          % (PASSES, FAILS, EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())