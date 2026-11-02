"""relative_import_publish_binding suite (R2402).

Criteria AC-RIPB1..AC-RIPB6 were pinned inside the R2400 tech seed row of
state/queue/tech.md:465 BEFORE this code existed.

What this proves: the from-import spelling law matched `from M import publish`
through the identity module's dotted-module patterns, so a PACKAGE-RELATIVE
import (`from . import publish`, `from .wire import publish`) bound nothing and
the call read kind=bare state=UNRESOLVED - a real in-package publisher reported
as an unbound call. One added notion now binds the relative name, keeps the
module text exactly as the file wrote it, and asks the parent law for every
classification, so there is still exactly one publish classifier in the tree.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import export_publish_from_import_law as EPBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import relative_import_publish_binding as RIPB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "relative_import_publish_binding.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-relative-import-publish-binding"
WIRED_EXPECT = '"test_relative_import_publish_binding.py"), 6),'

WIRE = "closeout_export_parity_wire"
EXPORT = "status-export.json"

HEAD = '''import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
'''

BODY = '''    return publish(".", EXPORT, text="{}")
'''

REL_PACKAGE = ("from . import publish\n" + HEAD + BODY)
REL_MODULE = ("from .wire import publish\n" + HEAD + BODY)
REL_ALIAS = ("from .wire import publish as wire_it\n" + HEAD
             + BODY.replace("return publish(", "return wire_it("))
REL_RENAMED_IMPORT = ("from .wire import publish as ship\n" + HEAD + BODY)
REL_OTHER_NAME = ("from .wire import other as publish\n" + HEAD + BODY)
REL_DEEPER = ("from ..pkg.sub import publish\n" + HEAD + BODY)

ABS_WIRE = ("from closeout_export_parity_wire import publish\n" + HEAD + BODY)
ABS_ALIAS = ("from closeout_export_parity_wire import publish as wire_it\n"
             + HEAD + BODY.replace("return publish(", "return wire_it("))
ABS_FOREIGN = ("from some_other_wire import publish\n" + HEAD + BODY)
ABS_ATTR = ("import closeout_export_parity_wire as CEPW\n" + HEAD
            + BODY.replace("return publish(",
                           "return CEPW.publish("))
BARE_UNBOUND = HEAD + BODY

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
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
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


def world(scripts):
    root = tempfile.mkdtemp(prefix="ripb-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def rows(script):
    return RIPB.classify_script(script.splitlines(), EXPORT, WIRE)


def states(script):
    return [row["state"] for row in rows(script)]


def kinds(script):
    return [row["kind"] for row in rows(script)]


def main():
    # AC-RIPB1: `from . import publish` and `from .M import publish` are read
    # as from_import, naming the RELATIVE module text rather than an absolute
    # module this law invented.
    package_rows = rows(REL_PACKAGE)
    module_rows = rows(REL_MODULE)
    deeper_rows = rows(REL_DEEPER)
    check(len(package_rows) == 1 and package_rows[0]["kind"] == "from_import"
          and package_rows[0]["module"] == "."
          and package_rows[0]["state"] == "RELATIVE"
          and package_rows[0]["relative"] is True
          and len(module_rows) == 1
          and module_rows[0]["kind"] == "from_import"
          and module_rows[0]["module"] == ".wire"
          and module_rows[0]["state"] == "RELATIVE"
          and deeper_rows[0]["module"] == "..pkg.sub"
          and deeper_rows[0]["kind"] == "from_import",
          "AC-RIPB1 AC-RIPB1 a relative import reads as from_import")

    # The absolute table is the parent law's own, asked at call time: patching
    # that table moves this reading, so no second absolute parser lives here.
    original = EPBW.imported_publish_names
    try:
        EPBW.imported_publish_names = lambda lines: {}
        moved = RIPB.classify_script(ABS_WIRE.splitlines(), EXPORT, WIRE)
    finally:
        EPBW.imported_publish_names = original
    draft = read(MODULE)
    check([row["state"] for row in moved] == ["UNRESOLVED"]
          and "EPBW.FROM_PLAIN_RE" not in draft
          and "FROM_PLAIN_RE =" not in draft
          and "FROM_AS_RE =" not in draft,
          "AC-RIPB1b AC-RIPB1 the absolute table is asked, not restated")

    # AC-RIPB2: every absolute form keeps its reading byte for byte - the same
    # state and the same four published fields as the parent law's own face.
    def parent_view(script):
        calls = EPBW.classify_script(script.splitlines(), EXPORT, WIRE)
        return [{key: row[key] for key in ("kind", "receiver", "module",
                                           "state", "line", "text")}
                for row in calls]

    def my_view(script):
        calls = rows(script)
        return [{key: row[key] for key in ("kind", "receiver", "module",
                                           "state", "line", "text")}
                for row in calls]

    same = all(parent_view(script) == my_view(script)
               for script in (ABS_WIRE, ABS_ALIAS, ABS_FOREIGN, ABS_ATTR,
                              BARE_UNBOUND))
    check(same and states(ABS_WIRE) == ["WIRE"]
          and states(ABS_FOREIGN) == ["FOREIGN"]
          and states(ABS_ATTR) == ["WIRE"]
          and states(BARE_UNBOUND) == ["UNRESOLVED"]
          and all(row["relative"] is False for row in rows(ABS_WIRE)),
          "AC-RIPB2 AC-RIPB2 the absolute forms read exactly as before")

    # AC-RIPB3: a relative import that binds a DIFFERENT local name does not
    # make a bare publish resolve - the alias law holds in the relative case.
    renamed = rows(REL_RENAMED_IMPORT)
    other = rows(REL_OTHER_NAME)
    alias = rows(REL_ALIAS)
    check([row["kind"] for row in renamed] == ["bare"]
          and [row["state"] for row in renamed] == ["UNRESOLVED"]
          and [row["kind"] for row in other] == ["bare"]
          and [row["module"] for row in other] == [""]
          and [row["kind"] for row in alias] == ["from_import"]
          and [row["module"] for row in alias] == [".wire"]
          and [row["state"] for row in alias] == ["RELATIVE"],
          "AC-RIPB3 AC-RIPB3 the local name is the alias, as before")

    # AC-RIPB4: every refusal code, exit code and printed line of the parent
    # law and the identity module is unchanged - proved by running them on the
    # same fixtures and comparing their own readings, and by the parent's own
    # classification of a relative script still being bare/UNRESOLVED (this
    # module adds a reading, it does not rewrite the parent's).
    root = world([("rel_pub.py", REL_MODULE), ("abs_pub.py", ABS_WIRE),
                  ("foreign_pub.py", ABS_FOREIGN)])
    root_rel = world([("rel_pub.py", REL_MODULE)])
    parent_report, parent_code = EPBW.audit(root_rel)
    identity_report = EPWI.audit(root_rel)
    parent_rows = EPBW.classify_script(REL_MODULE.splitlines(), EXPORT, WIRE)
    done = subprocess.run(
        [sys.executable, os.path.join(BASE, "export_publish_from_import_law.py"),
         "--check", "--root", root_rel],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_parent = done.stdout.decode("utf-8", "replace")
    check(done.returncode == 2
          and [row["kind"] for row in parent_rows] == ["bare"]
          and [row["state"] for row in parent_rows] == ["UNRESOLVED"]
          and parent_report["verdict"] == "UNRESOLVED" and parent_code == 2
          and parent_report["unresolved"] == ["rel_pub.py"]
          and identity_report[0]["unresolved"] == ["rel_pub.py"]
          and identity_report[0]["foreign"] == []
          and out_parent.startswith("EXPORT PUBLISH FROM IMPORT LAW ")
          and "verdict=UNRESOLVED" in out_parent
          and "rel_pub.py:10 kind=bare" in out_parent
          and "receiver=publish module=(unbound)" in out_parent,
          "AC-RIPB4 AC-RIPB4 the parent law's own reading is untouched")

    # AC-RIPB5: exits 0/2/3/5 with a byte-stable --json over the pinned keys.
    root_wire = world([("wire_pub.py", ABS_WIRE)])
    root_relative = world([("rel_pub.py", REL_MODULE)])
    root_empty = world([("notes.py", "NOTE = 'nothing here'\n")])
    rc_wire, out_wire, _ = run(root_wire)
    rc_json, json_a, _ = run(root_wire, ("--json",))
    rc_again, json_b, _ = run(root_wire, ("--json",))
    rc_relative, out_relative, _ = run(root_relative)
    rc_empty, out_empty, _ = run(root_empty)
    rc_missing, _, missing_err = run(os.path.join(root_wire, "no-such-dir"))
    rc_flags, _, flags_err = run(root_wire, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root_wire],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_wire == 0 and "verdict=WIRE" in out_wire
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == RIPB.REPORT_KEYS
          and [tuple(row.keys()) for row in parsed["detail"]]
          == [RIPB.CALL_KEYS + ("path",)]
          and rc_relative == 2 and "verdict=RELATIVE" in out_relative
          and "module=.wire" in out_relative
          and "rel_pub.py:10" in out_relative
          and rc_empty == 0 and "verdict=EMPTY" in out_empty
          and rc_missing == 3 and "E_RIPB_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_RIPB_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-RIPB5 AC-RIPB5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-RIPB6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    source = read(MODULE)
    digest_before = hashlib.sha256(source.encode("utf-8")).hexdigest()
    whole_before = tree_digest(root_wire)
    run(root_wire, ("--json",))
    RIPB.audit(root_wire)
    recipes = read(RUNNER)
    forbidden = ("datetime", "time.time", "socket", "urllib", "requests",
                 "os.open", "io.open")
    check(tree_digest(root_wire) == whole_before
          and hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
          == digest_before
          and all(name not in source for name in forbidden)
          and all(ord(char) < 128 for char in source)
          and WIRED_EXPECT in recipes
          and LABEL in recipes,
          "AC-RIPB6 AC-RIPB6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())