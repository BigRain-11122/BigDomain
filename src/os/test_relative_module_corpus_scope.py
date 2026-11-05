"""relative_module_corpus_scope suite (R2491).

Criteria AC-RMSC1..AC-RMSC6 were pinned inside the R2440 tech seed row of
state/queue/tech.md:525 BEFORE this code existed.

What this proves: the R2440 existence face measures its module corpus by
walking the ROOT it is handed, so a join whose module is importable but lives
outside that root reads MISSING-MODULE exactly like a broken import - a scope
limit and a typo were indistinguishable. This face keeps the same parent audit
and the same words, and adds (a) the search scope published on every
MISSING-MODULE row - the root as given and the corpus size it was judged
against - and (b) caller-declared extra module names merged ON TOP of the
measured tree, never replacing it.

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
import relative_module_corpus_scope as RMCS  # noqa: E402
import relative_module_existence_face as RMEF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "relative_module_corpus_scope.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-relative-module-corpus-scope"
WIRED_EXPECT = '"test_relative_module_corpus_scope.py"), 6),'

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
    root = tempfile.mkdtemp(prefix="rmsc-")
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
    # AC-RMSC1: every MISSING-MODULE row publishes the scope it was judged in
    # - the root AS GIVEN and the corpus size - in the object and on screen.
    root_missing = world([("rel_pub.py", REL_MISSING)])
    report_missing, code_missing = RMCS.check(root_missing, PACKAGE,
                                              wire_module="mypkg.wire")
    rows = report_missing["missing"]
    scoped = (code_missing == 2
              and report_missing["verdict"] == RMCS.MISSING_MODULE
              and len(rows) == 1
              and rows[0]["scope_root"] == root_missing
              and rows[0]["scope_corpus"] == report_missing["corpus"]
              and rows[0]["scope_corpus"] == len(
                  RMCS.tree_corpus(root_missing)))
    rc_txt, out_txt, err_txt = run(root_missing, ["--package", PACKAGE,
                                                  "--wire", "mypkg.wire"])
    printed = ("scope_root=%s" % root_missing) in out_txt \
        and ("scope_corpus=%d" % report_missing["corpus"]) in out_txt
    check(scoped and rc_txt == 2 and printed and not err_txt,
          "AC-RMSC1 every MISSING-MODULE row prints root as given + corpus size")

    # AC-RMSC2: the corpus is ROOT-WIDE, so a module the tree carries under
    # another top-level package is present. The publisher lives in
    # `scripts/` while the package sits in `mypkg/` - a sibling top-level
    # directory - and the join onto mypkg.wire is still found.
    root_sibling = world([("scripts/rel_pub.py", REL_PRESENT)])
    corpus_wide = RMCS.tree_corpus(root_sibling)
    wide, wide_code = RMCS.check(root_sibling, PACKAGE, wire_module="mypkg.wire")
    real_corpus = RMCS.tree_corpus

    def narrow(root):
        """The bug this criterion exists for: walk only the scripts dir."""
        return real_corpus(os.path.join(root, "scripts"))

    narrowed = []
    try:
        RMCS.tree_corpus = narrow
        narrow_report, narrow_code = RMCS.check(root_sibling, PACKAGE,
                                                wire_module="mypkg.wire")
        narrowed.append(narrow_code == 2
                        and narrow_report["verdict"] == RMCS.MISSING_MODULE
                        and narrow_report["missing_modules"] == ["mypkg.wire"])
    finally:
        RMCS.tree_corpus = real_corpus
    check("mypkg.wire" in corpus_wide
          and wide_code == 0
          and wide["verdict"] == "WIRE"
          and all(narrowed),
          "AC-RMSC2 a module carried in another top-level package is present")

    # AC-RMSC3: caller-declared extras are MERGED on top of the measured tree
    # and a patched tree reading still moves the verdict.
    merged_report, merged_code = RMCS.check(
        root_missing, PACKAGE, wire_module="mypkg.wire",
        extra=["mypkg.nosuchmodule"])
    # The extras only make a module PRESENT; the WIRE/FOREIGN word stays the
    # parent's own, so an extra cannot invent a wire (AC-RMSC4's split).
    plain_report, plain_code = RMCS.check(root_missing, PACKAGE,
                                          wire_module="mypkg.wire")
    parent_only, parent_only_code = PRPI.audit(root_missing, PACKAGE, EXPORT,
                                               PRPI.DEFAULT_OWNER,
                                               "mypkg.wire")
    extras = (merged_code == parent_only_code
              and merged_report["verdict"] == parent_only["verdict"]
              and merged_report["missing"] == []
              and merged_report["missing_modules"] == []
              and merged_report["scope"] == RMCS.SCOPE_TREE_EXTRA
              and merged_report["scope_corpus"]
              == len(real_corpus(root_missing)) + 1
              and merged_report["extra"] == ["mypkg.nosuchmodule"])
    # A patched TREE reading still moves the verdict: the corpus is measured,
    # never hard-coded, so adding the name to the measured tree clears the
    # absence exactly as declaring it does.
    widened = RMCS.tree_corpus

    def patched_tree(root):
        return widened(root) | set(["mypkg.nosuchmodule"])

    patched_move = []
    try:
        RMCS.tree_corpus = patched_tree
        patched_plain, patched_plain_code = RMCS.check(
            root_missing, PACKAGE, wire_module="mypkg.wire")
        patched_move.append(patched_plain["missing"] == []
                            and patched_plain_code == parent_only_code
                            and patched_plain["verdict"]
                            == parent_only["verdict"])
    finally:
        RMCS.tree_corpus = widened
    tree_only, _ = RMCS.check(root_missing, PACKAGE, wire_module="mypkg.wire")
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
        patched, patched_code = RMCS.check(root_missing, PACKAGE, extra=[
            "mypkg.nosuchmodule"])
        moved.append(patched_code == 2
                     and patched["missing_modules"] == ["mypkg.ghost"]
                     and patched["extra"] == ["mypkg.nosuchmodule"])
    finally:
        PRPI.audit = real_audit
    check(extras and all(patched_move)
          and tree_only["missing_modules"] == ["mypkg.nosuchmodule"]
          and tree_only["scope"] == RMCS.SCOPE_TREE and all(moved),
          "AC-RMSC3 extras merged on top of the tree, patched reading still moves")

    # AC-RMSC4: the join and the parent reading are publish_relative_package_
    # identity's own, asked at CALL time, with ONE corpus walk and no second.
    walks = []
    real_tree_corpus = RMCS.tree_corpus

    def counting(root):
        walks.append(root)
        return real_tree_corpus(root)

    called = []
    try:
        RMCS.tree_corpus = counting
        parented, parented_code = RMCS.check(root_missing, PACKAGE,
                                             wire_module="mypkg.wire")
        called.append(len(walks))
        source = read(MODULE)
        # The dependency law, not a prose ban: this face asks the PARENT
        # (publish_relative_package_identity) and never the R2440 face, so the
        # join and the classifier keep exactly one owner.
        called.append("import relative_module_existence_face" not in source)
        called.append(parented_code == 2)
    finally:
        RMCS.tree_corpus = real_tree_corpus
    root_none = world([("rel_pub.py", REL_PRESENT)])
    no_package, no_package_code = RMCS.check(root_none, None)
    parent_none, parent_none_code = PRPI.audit(root_none, None, EXPORT,
                                               PRPI.DEFAULT_OWNER,
                                               PRPI.DEFAULT_WIRE)
    check(called == [1, True, True]
          and no_package_code == parent_none_code
          and no_package["verdict"] == parent_none["verdict"]
          and no_package["scope"] == RMCS.SCOPE_NONE
          and no_package["corpus"] == RMCS.NO_CORPUS,
          "AC-RMSC4 parent audit asked at call time, exactly one corpus walk")

    # AC-RMSC5: CLI exits 0/2/3/5 with a byte-stable --json over extended
    # pinned keys, while every R2440 key keeps its name and its meaning.
    root_ok = world([("rel_pub.py", REL_PRESENT)])
    rc_ok, out_ok, _ = run(root_ok, ["--package", PACKAGE, "--wire",
                                     "mypkg.wire", "--json"])
    rc_missing, out_1, _ = run(root_missing, ["--package", PACKAGE, "--wire",
                                              "mypkg.wire", "--json"])
    rc_twice, out_2, _ = run(root_missing, ["--package", PACKAGE, "--wire",
                                            "mypkg.wire", "--json"])
    rc_root, _, err_root = run(os.path.join(root_ok, "nosuch"), ["--check"])
    rc_bad, _, err_bad = run(root_ok, ["--check", "--nope"])
    rc_extra, _, err_extra = run(root_ok, ["--check", "--package", PACKAGE,
                                           "--extra", "9bad"])
    mine, _ = RMCS.check(root_ok, PACKAGE, wire_module="mypkg.wire")
    theirs, _ = RMEF.check(root_ok, PACKAGE, wire_module="mypkg.wire")
    shared = [key for key in RMEF.REPORT_KEYS
              if key not in ("label", "missing", "missing_modules")]
    kept = all(mine[key] == theirs[key] for key in shared)
    keys_kept = set(RMEF.REPORT_KEYS).issubset(set(RMCS.REPORT_KEYS))
    parsed = json.loads(out_1)
    json_kept = set(RMEF.REPORT_KEYS).issubset(set(parsed))
    check(rc_ok == 0 and rc_missing == rc_twice == 2
          and out_1 == out_2 and parsed["scope_root"] == root_missing
          and rc_root == 3 and "E_RMSC_NO_ROOT" in err_root
          and rc_bad == 5 and "E_RMSC_BAD_FLAGS" in err_bad
          and rc_extra == 5 and "E_RMSC_BAD_EXTRA" in err_extra
          and keys_kept and json_kept and kept
          and parsed["label"] == LABEL,
          "AC-RMSC5 exits 0/2/3/5, byte-stable json, R2440 keys kept")

    # AC-RMSC6: pure ASCII, stdlib only, no clock, read-only, own label and
    # own suite wired into the runner registry.
    source = read(MODULE)
    ascii_ok = all(ord(ch) < 128 for ch in source)
    banned = [word for word in ("time.", "datetime", "socket", "urllib",
                                "requests", "http.client")
              if word in source]
    digest = tree_digest(root_ok)
    RMCS.check(root_ok, PACKAGE, wire_module="mypkg.wire",
               extra=["mypkg.extra"])
    runner = read(RUNNER)
    check(ascii_ok and not banned and digest == tree_digest(root_ok)
          and RMCS.LABEL == LABEL and LABEL in runner
          and WIRED_EXPECT in runner,
          "AC-RMSC6 ascii, stdlib, no clock, read-only, own label + suite wired")

    total = PASSES + FAILS
    print("SUITE %s (%d/%d criteria pass)" % (
        "PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL",
        PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())