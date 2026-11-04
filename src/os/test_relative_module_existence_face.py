"""relative_module_existence_face suite (R2440).

Criteria AC-RMEF1..AC-RMEF6 were pinned inside the R2415 tech seed row of
state/queue/tech.md:504 BEFORE this code existed.

What this proves: publish_relative_package_identity joins a relative module
text onto a declared package, so `from .nosuchmodule import publish` with
--package mypkg used to read FOREIGN at exit 2 even though no such module
exists in the tree - a typo and a genuinely foreign wire read identically.
One added notion - the module corpus measured off the read tree's own .py
files - turns that join into MISSING-MODULE, while a join with a file behind
it keeps today's reading and a run with NO package keeps the parent's own
reading byte for byte.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import publish_relative_package_identity as PRPI  # noqa: E402
import relative_module_existence_face as RMEF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "relative_module_existence_face.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-relative-module-existence-face"
WIRED_EXPECT = '"test_relative_module_existence_face.py"), 6),'

WIRE = "closeout_export_parity_wire"
EXPORT = "status-export.json"
PACKAGE = "mypkg"

HEAD = '''import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
'''

BODY = '''    return publish(".", EXPORT, text="{}")
'''

REL_MODULE = ("from .wire import publish\n" + HEAD + BODY)
REL_MISSING = ("from .nosuchmodule import publish\n" + HEAD + BODY)
ABS_WIRE = ("from closeout_export_parity_wire import publish\n" + HEAD + BODY)

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
    root = tempfile.mkdtemp(prefix="rmef-")
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
    # AC-RMEF1: the WIRE/FOREIGN law is the parent's own audit asked at CALL
    # time, and the module corpus is MEASURED off the tree, never hard-coded.
    real_audit = PRPI.audit
    synthetic = {
        "label": PRPI.LABEL, "verdict": "WIRE", "root": ".", "package": PACKAGE,
        "scanned": 1, "publishers": ["rel_pub.py"], "wire": ["rel_pub.py"],
        "foreign": [], "unresolved": [], "relative": 1, "no_publish": [],
        "from_import": 1, "bare": 0, "refused": [], "detail": [{
            "kind": "from_import", "receiver": "", "module": "mypkg.ghost",
            "state": "WIRE", "line": 1, "relative": True, "path": "rel_pub.py",
            "text": "from .ghost import publish"}],
    }
    moved = []
    try:
        PRPI.audit = lambda *a, **k: (dict(synthetic), 0)
        report_patched, code_patched = RMEF.check(".", PACKAGE)
        moved.append(report_patched["verdict"] == RMEF.MISSING_MODULE
                     and code_patched == 2
                     and report_patched["missing_modules"] == ["mypkg.ghost"])
        PRPI.audit = real_audit
        root_one = world([("rel_pub.py", ABS_WIRE)])
        report_real, code_real = RMEF.check(root_one, None)
        moved.append(code_real == 0
                     and report_real["verdict"] == "WIRE"
                     and report_real["corpus"] == RMEF.NO_CORPUS)
    finally:
        PRPI.audit = real_audit
    corpus_short = RMEF.corpus(world([]))
    grown = world([])
    write(os.path.join(grown, "mypkg", "extra.py"), "")
    corpus_grown = RMEF.corpus(grown)
    check(all(moved) and "mypkg.wire" in corpus_short
          and "mypkg.extra" in corpus_grown
          and "mypkg.extra" not in corpus_short,
          "AC-RMEF1 parent audit asked at call time, corpus measured off the tree")

    # AC-RMEF2: a joined module with a file behind it keeps today's reading -
    # verdict, every row and every count identical to the parent's own audit.
    root_ok = world([("rel_pub.py", REL_MODULE)])
    mine, my_code = RMEF.check(root_ok, PACKAGE, wire_module="mypkg.wire")
    theirs, their_code = PRPI.audit(root_ok, PACKAGE, EXPORT,
                                    PRPI.DEFAULT_OWNER, "mypkg.wire")
    same = (my_code == their_code == 0
            and mine["verdict"] == theirs["verdict"] == "WIRE"
            and mine["detail"] == theirs["detail"]
            and mine["publishers"] == theirs["publishers"]
            and mine["wire"] == theirs["wire"]
            and mine["foreign"] == theirs["foreign"]
            and mine["relative"] == theirs["relative"] == 1
            and mine["missing"] == []
            and mine["corpus"] == len(RMEF.corpus(root_ok)))
    check(same, "AC-RMEF2 a join with a file behind it keeps today's reading")

    # AC-RMEF3: a join with NOTHING behind it reads MISSING-MODULE at exit 2,
    # naming the joined text and the declared package.
    root_gap = world([("rel_pub.py", REL_MISSING)])
    gap, gap_code = RMEF.check(root_gap, PACKAGE)
    rc_gap, out_gap, _ = run(root_gap, ("--package", PACKAGE))
    check(gap_code == 2 and gap["verdict"] == RMEF.MISSING_MODULE
          and gap["missing_modules"] == ["mypkg.nosuchmodule"]
          and len(gap["missing"]) == 1
          and gap["missing"][0]["package"] == PACKAGE
          and gap["missing"][0]["path"] == "rel_pub.py"
          and rc_gap == 2
          and "verdict=MISSING-MODULE" in out_gap
          and "module=mypkg.nosuchmodule" in out_gap
          and "package=mypkg" in out_gap,
          "AC-RMEF3 a join with nothing behind it reads MISSING-MODULE")

    # AC-RMEF4: with NO package the parent's reading is kept byte for byte and
    # no corpus is measured at all.
    root_none = world([("rel_pub.py", REL_MODULE),
                       ("abs_pub.py", ABS_WIRE)])
    plain, plain_code = RMEF.check(root_none, None)
    base, base_code = PRPI.audit(root_none, None)
    shared = dict((key, plain[key]) for key in base)
    shared["label"] = base["label"]
    never = []
    real_corpus = RMEF.corpus
    try:
        RMEF.corpus = lambda root: never.append(root) or set()
        nopkg, nopkg_code = RMEF.check(root_none, None)
        never_ran = not never
    finally:
        RMEF.corpus = real_corpus
    check(shared == base and plain_code == base_code == 2
          and plain["corpus"] == RMEF.NO_CORPUS
          and plain["missing"] == []
          and never_ran and nopkg["corpus"] == RMEF.NO_CORPUS
          and nopkg_code == base_code,
          "AC-RMEF4 no package keeps the parent reading and measures no corpus")

    # AC-RMEF5: exits 0/2/3/5 and a byte-stable --json over the pinned keys.
    rc_wire, out_wire, _ = run(root_ok, ("--package", PACKAGE,
                                         "--wire", "mypkg.wire"))
    rc_json, json_a, _ = run(root_ok, ("--package", PACKAGE,
                                       "--wire", "mypkg.wire", "--json"))
    rc_again, json_b, _ = run(root_ok, ("--package", PACKAGE,
                                        "--wire", "mypkg.wire", "--json"))
    rc_missing, _, _ = run(os.path.join(root_ok, "no-such-dir"))
    rc_flags, _, flags_err = run(root_ok, ("--nope",))
    rc_package, _, package_err = run(root_ok, ("--package", "bad/name"))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root_ok],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_wire == 0 and "verdict=WIRE" in out_wire
          and "package=mypkg" in out_wire
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == RMEF.REPORT_KEYS
          and rc_missing == 3
          and rc_flags == 5 and "E_RMEF_BAD_FLAGS" in flags_err
          and rc_package == 5 and "E_PRPI_BAD_PACKAGE" in package_err
          and rc_no_check == 5
          and rc_gap == 2,
          "AC-RMEF5 exits 0/2/3/5 with byte-stable --json over pinned keys")

    # AC-RMEF6: writes nothing, reads no clock, ASCII, stdlib only, its own
    # reconcile label and its own suite wired into the runner.
    before = tree_digest(root_gap)
    run(root_gap, ("--package", PACKAGE))
    after = tree_digest(root_gap)
    source = read(MODULE)
    ascii_ok = all(ord(ch) < 128 for ch in source)
    clock_free = ("import time" not in source
                  and "import datetime" not in source
                  and "time.time(" not in source)
    if os.path.isfile(RUNNER):
        text = read(RUNNER)
        wired = ('("' + LABEL + '",') in text and WIRED_EXPECT in text
        suite_present = os.path.isfile(os.path.join(
            BASE, "test_relative_module_existence_face.py"))
    else:
        wired = suite_present = False
    check(before == after and ascii_ok and clock_free and wired
          and suite_present,
          "AC-RMEF6 writes nothing, no clock, ASCII, its own label and suite")

    print("SUMMARY pass=%d fail=%d criteria=%d" % (PASSES, FAILS,
                                                   EXPECTED_CRITERIA),
          flush=True)
    if FAILS or PASSES + FAILS != EXPECTED_CRITERIA:
        print("SUITE FAIL", flush=True)
        return 2
    print("SUITE PASS", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())