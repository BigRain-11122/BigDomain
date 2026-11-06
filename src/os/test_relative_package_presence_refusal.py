# test_relative_package_presence_refusal.py - the six criteria pinned in
# state/queue/tech.md for AC-RMPP1..AC-RMPP6, proved against the SHIPPED
# capture callable and the SHIPPED CLI, never against a copy.
# Pure ASCII, stdlib only, no clock, zero network, writes only under a temp
# root it creates itself.

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import relative_package_presence_refusal as RPPR
import relative_module_corpus_scope as RMCS

MODULE = os.path.join(HERE, "relative_package_presence_refusal.py")
SOURCE = os.path.join(HERE, "relative_package_presence_refusal.py")
PACKAGE = "mypkg"

HEAD = '''import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
'''

BODY = '''    return publish(".", EXPORT, text="{}")
'''

REL_PRESENT = ("from .wire import publish\n" + HEAD + BODY)
REL_MISSING = ("from .nosuchmodule import publish\n" + HEAD + BODY)

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
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    parent_dir = os.path.dirname(path)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def tree_digest(root):
    """sha256 over every file path and its bytes - the write-nothing proof."""
    digest = hashlib.sha256()
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(
                os.path.relpath(path, root).replace(os.sep, "/").encode("utf-8"))
            digest.update(b"\0")
            with io.open(path, "rb") as handle:
                digest.update(handle.read())
            digest.update(b"\0")
    return digest.hexdigest()


def world(scripts, package_files=("mypkg/__init__.py", "mypkg/wire.py")):
    """The same fixture shape the R2440 / R2491 suites use."""
    root = tempfile.mkdtemp(prefix="rmpp-")
    for name in package_files:
        write(os.path.join(root, name), "")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def main():
    worlds = []
    try:
        # AC-RMPP1: a declared package the tree carries NOTHING at or under
        # refuses ONCE, naming the declaration and the corpus it searched,
        # and no per-import MISSING-MODULE row is invented from it.
        root_absent = world([("rel_pub.py", REL_MISSING)])
        worlds.append(root_absent)
        corpus = RMCS.tree_corpus(root_absent)
        report, code = RPPR.check(root_absent, "nosuchpkg")
        absent = (code == 2
                  and report["verdict"] == RPPR.NO_PACKAGE
                  and report["presence"] == RPPR.ABSENT
                  and report["declaration"] == "nosuchpkg"
                  and report["refusal"] == RPPR.REFUSAL_CODE
                  and report["missing"] == []
                  and report["missing_modules"] == []
                  and report["detail"] == []
                  and report["presence_corpus"] == len(corpus)
                  and report["corpus"] == len(corpus))
        rc_txt, out_txt, err_txt = run(root_absent, ["--package", "nosuchpkg"])
        printed = ("declaration=nosuchpkg" in out_txt
                   and ("presence_corpus=%d" % len(corpus)) in out_txt
                   and "refusal=%s" % RPPR.REFUSAL_CODE in out_txt
                   and "missing_module=" not in out_txt)
        # the defect this criterion exists for: the SAME tree under the
        # carried package still reads the real missing import, so the
        # refusal names the declaration instead of hiding a real typo.
        real, real_code = RPPR.check(root_absent, PACKAGE)
        contrast = (real_code == 2
                    and real["verdict"] == RMCS.MISSING_MODULE
                    and real["presence"] == RPPR.PRESENT
                    and len(real["missing"]) == 1)
        check(absent and printed and not err_txt and contrast,
              "AC-RMPP1 absent declaration refuses once with no MISSING rows")

        # AC-RMPP2: a declared package the tree DOES carry keeps today's
        # reading byte for byte - every parent key holds the same value.
        root_present = world([("rel_pub.py", REL_PRESENT),
                              ("rel_miss.py", REL_MISSING)])
        worlds.append(root_present)
        mine, mine_code = RPPR.check(root_present, PACKAGE)
        theirs, their_code = RMCS.check(root_present, PACKAGE)
        same = (mine_code == their_code
                and sorted(mine[key] == theirs[key]
                           for key in RMCS.REPORT_KEYS) == [True] * len(
                               RMCS.REPORT_KEYS))
        still_reads = (mine["verdict"] == RMCS.MISSING_MODULE
                       and len(mine["missing"]) == len(theirs["missing"]) == 1
                       and mine["presence"] == RPPR.PRESENT)
        check(same and still_reads,
              "AC-RMPP2 a carried package keeps the parent reading byte for byte")

        # AC-RMPP3: a package carried ONLY by its own marker counts present.
        root_marker = world([("rel_pub.py", REL_PRESENT)],
                            package_files=("mypkg/__init__.py",))
        worlds.append(root_marker)
        marker, marker_code = RPPR.check(root_marker, "mypkg")
        carried = (marker["presence"] == RPPR.MARKER
                   and marker["presence_carriers"] == 1
                   and marker["verdict"] != RPPR.NO_PACKAGE
                   and marker_code in (0, 2))
        deep = RPPR.presence(set(["only", "only.mod"]), "only")
        marker_only = RPPR.presence(set(["only"]), "only")
        absent_pair = RPPR.presence(set(["other"]), "only")
        check(carried and deep[0] == RPPR.PRESENT
              and marker_only[0] == RPPR.MARKER
              and absent_pair[0] == RPPR.ABSENT,
              "AC-RMPP3 a package marker alone counts as present")

        # AC-RMPP4: the corpus is the R2440 measured walk asked at CALL time
        # and no walk of its own exists. Counted: this face asks the parent
        # walk exactly once, and in the refusal path it never reaches the
        # parent reading at all.
        text = read(SOURCE)
        no_own_walk = "os.walk" not in text and "tree_corpus(" in text
        calls = {"walk": 0, "check": 0}
        real_walk = RMCS.tree_corpus
        real_check = RMCS.check

        def counted_walk(root):
            calls["walk"] += 1
            return real_walk(root)

        def counted_check(*args, **kwargs):
            calls["check"] += 1
            return real_check(*args, **kwargs)

        RMCS.tree_corpus = counted_walk
        RMCS.check = counted_check
        try:
            RPPR.check(root_absent, "nosuchpkg")
            refusal_calls = dict(calls)
            calls["walk"] = 0
            calls["check"] = 0
            RPPR.check(root_present, PACKAGE)
            present_calls = dict(calls)
        finally:
            RMCS.tree_corpus = real_walk
            RMCS.check = real_check
        one_walk = (no_own_walk
                    and refusal_calls["walk"] == 1
                    and refusal_calls["check"] == 0
                    and present_calls["walk"] == 1
                    and present_calls["check"] == 1)
        check(one_walk,
              "AC-RMPP4 corpus is the parent walk asked once, no own walk")

        # AC-RMPP5: exit codes 0/2/3/5 and a byte-stable --json over the
        # extended pinned keys, while every parent key keeps its meaning.
        rc_ok, out_ok, err_ok = run(root_present, ["--package", PACKAGE,
                                                  "--json"])
        first = json.loads(out_ok)
        again = json.loads(run(root_present, ["--package", PACKAGE,
                                             "--json"])[1])
        keys_kept = all(key in first for key in RMCS.REPORT_KEYS)
        keys_new = all(key in first for key in RPPR.PRESENCE_KEYS)
        stable = (first == again
                  and out_ok == run(root_present, ["--package", PACKAGE,
                                                   "--json"])[1])
        rc_absent, out_absent, _ = run(root_absent, ["--package", "nosuchpkg",
                                                     "--json"])
        absent_json = json.loads(out_absent)
        rc_root, _, err_root = run(os.path.join(root_present, "nope"))
        rc_bad, _, err_bad = run(root_present, ["--package", "not a package"])
        rc_flags, _, err_flags = run(root_present, ["--bogus"])
        codes = (rc_ok == 2 and rc_absent == 2 and rc_root == 3
                 and rc_bad == 5 and rc_flags == 5)
        check(keys_kept and keys_new and stable and codes
              and absent_json["verdict"] == RPPR.NO_PACKAGE
              and bool(err_root) and bool(err_bad) and bool(err_flags),
              "AC-RMPP5 exits 0/2/3/5 with a byte-stable --json over pinned keys")

        # AC-RMPP6: pure ASCII, stdlib only, no clock, zero network,
        # read-only, own reconcile label and own suite name.
        raw = io.open(SOURCE, "rb").read()
        ascii_ok = all(byte < 128 for byte in raw)
        imported = sorted(set(re.findall(r"^import (\w+)", text, re.M)
                              + re.findall(r"^from (\w+)", text, re.M)))
        stdlib_ok = all(name in ("importlib", "json", "os", "sys")
                        for name in imported)
        quiet = (not re.search(r"^\s*(import|from)\s+(time|datetime|socket|"
                               r"urllib|http|requests)\b", text, re.M)
                 and "open(" not in text.replace("io.open", ""))
        labelled = (RPPR.LABEL == "os-relative-package-presence-refusal"
                    and os.path.basename(SOURCE) ==
                    "relative_package_presence_refusal.py")
        before = tree_digest(root_present)
        RPPR.check(root_present, PACKAGE)
        untouched = before == tree_digest(root_present)
        check(ascii_ok and stdlib_ok and quiet and labelled and untouched,
              "AC-RMPP6 ascii stdlib no clock no network read-only own label")

        if FAILS:
            print("SUITE FAIL (%d/%d criteria pass)" % (PASSES, PASSES + FAILS),
                  flush=True)
            return 1
        print("SUITE PASS (%d/%d criteria pass)" % (PASSES, PASSES + FAILS),
              flush=True)
        return 0
    finally:
        for root in worlds:
            shutil.rmtree(root, ignore_errors=True)


def capture():
    """The suite runner's callable: returns (passes, fails) for this suite."""
    global PASSES, FAILS
    PASSES = 0
    FAILS = 0
    main()
    return PASSES, FAILS


if __name__ == "__main__":
    sys.exit(main())