#!/usr/bin/env python3
"""test_os_retry_naming.py - the correction-rerun naming seam.

AC-RTN1..AC-RTN6 (pre-registered in state/queue/tech.md R2238 claim
line BEFORE this code): the retry suffix, the refusal of the legacy
rerun suffixes, the auditor never pairing a retry leg, a genuine false
byte claim still turning red, the read-only directory census, and the
CLI plus wiring. ASCII only, stdlib only, zero network, no wall clock.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import retry_naming as RN
import run_identity as RI

TOOL = os.path.join(HERE, "retry_naming.py")
RECONCILE = os.path.join(HERE, "..", "sandbox", "reconcile_all.py")
CHECKS = 0


def ok(cond, label):
    global CHECKS
    assert cond, "FAIL: " + label
    CHECKS += 1
    print("PASS " + label)


def write(path, text):
    with open(path, "wb") as handle:
        handle.write(text.encode("utf-8"))


def snapshot(root):
    snap = {}
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isfile(path):
            with open(path, "rb") as handle:
                snap[name] = handle.read()
    return snap


def run(*args):
    proc = subprocess.run([sys.executable, TOOL] + list(args),
                          capture_output=True)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def failure(call, *args):
    try:
        call(*args)
    except RN.RetryNamingError as exc:
        return exc.code
    return None


def main():
    root = tempfile.mkdtemp(prefix="bd-retry-")
    try:
        world = os.path.join(root, "qa")
        os.makedirs(world)

        # AC-RTN1: the retry suffix sequence, base preserved
        write(os.path.join(world, "x-R100.log"), "SUITE FAIL 1/8\n")
        first = RN.retry_name("x-R100.log", world)
        ok(first == "x-R100-retry.log"
           and RN.is_retry(first)
           and RN.base_stem(first) == "x-R100",
           "AC-RTN1 first retry leg is -retry with the base intact")
        write(os.path.join(world, first), "SUITE PASS 8/8\n")
        second = RN.retry_name("x-R100.log", world)
        ok(second == "x-R100-retry2.log"
           and RN.retry_name("x-R100-retry.log", world) == second,
           "AC-RTN1 later retries count up from one base stem")

        # AC-RTN2: the legacy rerun suffixes are refused, zero writes
        before = snapshot(world)
        codes = (failure(RN.check_name, "x-R100-run2.log"),
                 failure(RN.check_name, "x-R100-2.log"),
                 failure(RN.check_name, "notes.txt"),
                 failure(RN.check_name, "x-R100-retry.log"))
        ok(codes == ("E_RETRY_BAD_SUFFIX", "E_RETRY_BAD_SUFFIX",
                     "E_RETRY_BAD_NAME", "E_RETRY_BAD_NAME")
           and snapshot(world) == before,
           "AC-RTN2 -run2/-2 fail closed with codes and write nothing")

        # AC-RTN3: the auditor never pairs a retry leg
        write(os.path.join(world, "p-a.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "p-b.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "q.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "q-retry.log"), "SUITE PASS 8/8\nq-only\n")
        pairs = RI.find_pairs(world)
        names = sorted(row["a"] + "|" + row["b"] for row in pairs)
        ok(names == ["p-a.log|p-b.log"]
           and RI.is_retry_name("q-retry.log")
           and not RI.is_retry_name("p-a.log"),
           "AC-RTN3 only the real identity pair is paired")

        # AC-RTN3b: a genuine false byte claim still turns red
        claim = ("SUITE PASS 8/8\nRUN1 rc=0 sha16=0123456789ABCDEF\n"
                 "byte-identical\n")
        write(os.path.join(world, "s-a.log"), claim)
        write(os.path.join(world, "s-b.log"), claim + "s-b only line\n")
        report = RI.audit_pairs(world)
        bad = [row for row in report["records"]
               if row["base"] == "s" and not row["ok"]]
        ok(len(bad) == 1
           and bad[0]["problems"]
           and report["summary"]["pairs"] == 2,
           "AC-RTN3b a lying identity pair still fails, retry not counted")

        # AC-RTN4: the census classes every leg and surfaces the legacy name
        write(os.path.join(world, second), "SUITE PASS 8/8\n")
        write(os.path.join(world, "u.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "u-run2.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "v-a.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "v-b.log"), "SUITE PASS 8/8\n")
        write(os.path.join(world, "w.log"), "SUITE PASS 8/8\n")
        envelope = RN.audit_dir(world)
        classes = {row["name"]: row["class"] for row in envelope["rows"]}
        ok(sorted(envelope.keys()) == sorted(
               ["dir", "file_count", "retry_count", "legacy_rerun_count",
                "pair_count", "rows"])
           and classes["q-retry.log"] == "retry"
           and classes["x-R100-retry2.log"] == "retry"
           and classes["u-run2.log"] == "legacy-rerun"
           and classes["v-a.log"] == "identity-leg"
           and classes["w.log"] == "first"
           and envelope["retry_count"] == 3
           and envelope["legacy_rerun_count"] == 1,
           "AC-RTN4 census classes retry, legacy and identity apart")

        # AC-RTN5: resolve_rerun names the rerun and reads the verdict move
        first_run = RN.resolve_rerun("z-R9.log", world)
        moved = RN.resolve_rerun("x-R100.log", world,
                                 "SUITE PASS 8/8\n")
        pair_code = failure(RN.resolve_rerun, "v-a.log", world)
        ok(first_run["class"] == "first"
           and first_run["name"] == "z-R9.log"
           and moved["class"] == "retry"
           and moved["name"] == "x-R100-retry3.log"
           and moved["verdict_before"] == "FAIL"
           and moved["verdict_after"] == "PASS"
           and moved["verdict_changed"] is True
           and pair_code == "E_RETRY_IDENTITY_SUFFIX",
           "AC-RTN5 resolve_rerun: retry for a moved verdict, pair refused")

        # AC-RTN6: the CLI contract
        clean = os.path.join(root, "clean")
        os.makedirs(clean)
        write(os.path.join(clean, "c.log"), "SUITE PASS 8/8\n")
        write(os.path.join(clean, "c-retry.log"), "SUITE PASS 8/8\n")
        rc_ok, out_ok, _err = run("--check-dir", clean)
        rc_legacy, out_legacy, _err2 = run("--check-dir", world)
        rc_missing, _out3, err_missing = run(
            "--check-dir", os.path.join(root, "nope"))
        rc_next, out_next, _err4 = run("--next", "x-R100.log", "--dir", world)
        ok(rc_ok == 0
           and out_ok.strip().splitlines()[-1] == "dir files=2 retry=1 legacy=0 pairs=0"
           and rc_legacy == 2
           and "class=legacy-rerun" in out_legacy
           and rc_missing == 3
           and err_missing.startswith("E_RETRY_NO_DIR:")
           and rc_next == 0
           and out_next.strip() == "next name=x-R100-retry3.log",
           "AC-RTN6 CLI exit codes, census line and next-name face")

        # AC-RTN6b: purity and the reconcile wiring
        source = open(TOOL, encoding="utf-8").read()
        source.encode("ascii")
        reg = open(RECONCILE, encoding="utf-8").read()
        ok("import time" not in source
           and "datetime" not in source
           and not any(mod in source for mod in RI.NET_IMPORTS)
           and reg.count('"os-retry-naming",') == 1
           and 'test_os_retry_naming.py' in reg,
           "AC-RTN6b source is pure ASCII and the suite is registered")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("SUITE PASS %d/8" % (CHECKS,))
    return 0


if __name__ == "__main__":
    sys.exit(main())