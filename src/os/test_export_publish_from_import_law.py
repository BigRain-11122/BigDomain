"""export_publish_from_import_law suite (R2400).

Criteria AC-EPBW1..AC-EPBW6 were pinned inside the R2391 tech seed row of
state/queue/tech.md:463 BEFORE this code existed.

What this proves: the routed-publish law was the guard's `.publish(` attribute
call, so a file that did `from closeout_export_parity_wire import publish` and
then called a BARE `publish(".", EXPORT, ...)` was not a routed publish at all
and the script read NO-PUBLISH - a current publisher reported as publishing
nothing. One spelling law now reads three spellings (attribute, from_import,
bare), asks the guard for the attribute half and the identity module for the
binding table and the prose mask at CALL time, and hands the identity module
back exactly the row it published before.

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

import export_publish_path_guard as EPPG  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import export_publish_from_import_law as EPBW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_publish_from_import_law.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-publish-from-import-law"
WIRED_EXPECT = '"test_export_publish_from_import_law.py"), 6),'

HEAD = '''import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
'''

ATTR_SCRIPT = HEAD + '''    return CEPW.publish(".", EXPORT, text="{}")
'''
ATTR_SCRIPT = ('import closeout_export_parity_wire as CEPW\n'
               + ATTR_SCRIPT)

FROM_WIRE_SCRIPT = ('from closeout_export_parity_wire import publish\n'
                    + ATTR_SCRIPT.replace("    return CEPW.publish(",
                                          "    return publish("))

FROM_FOREIGN_SCRIPT = ('from some_other_wire import publish\n'
                       + ATTR_SCRIPT.replace("    return CEPW.publish(",
                                             "    return publish("))

FROM_ALIAS_SCRIPT = ('from closeout_export_parity_wire import publish as wire_it\n'
                     + ATTR_SCRIPT.replace("    return CEPW.publish(",
                                           "    return wire_it("))

UNBOUND_SCRIPT = ATTR_SCRIPT.replace("    return CEPW.publish(",
                                     "    return publish(")

RENAMED_IMPORT_SCRIPT = ('from closeout_export_parity_wire import publish as ship\n'
                         + ATTR_SCRIPT.replace("    return CEPW.publish(",
                                               "    return publish("))

RENAMED_CALL_SCRIPT = ('from closeout_export_parity_wire import publish\n'
                       + ATTR_SCRIPT.replace("    return CEPW.publish(",
                                             "    return ship("))

PROSE_SCRIPT = '''"""Prose and a fixture, not calls."""

import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")

NOTE = "a bare `publish(..., EXPORT, ...)` used to read NO-PUBLISH"

FIXTURE = """
def publish(data):
    return publish(".", EXPORT, text="{}")
"""


def flush(data):
    QFE.apply(data, ".")
'''

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
    root = tempfile.mkdtemp(prefix="epbw-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def states(script):
    return [row["state"] for row in EPBW.classify_script(
        script.splitlines(), "status-export.json", "closeout_export_parity_wire")]


def kinds(script):
    return [row["kind"] for row in EPBW.classify_script(
        script.splitlines(), "status-export.json", "closeout_export_parity_wire")]


def main():
    # AC-EPBW1: a name imported by `from M import publish` and called bare IS a
    # routed publish, and it names the module the import binds - the module
    # table is the identity module's own, asked at call time.
    wire_rows = EPBW.classify_script(
        FROM_WIRE_SCRIPT.splitlines(), "status-export.json",
        "closeout_export_parity_wire")
    check(len(wire_rows) == 1 and wire_rows[0]["kind"] == "from_import"
          and wire_rows[0]["module"] == "closeout_export_parity_wire"
          and wire_rows[0]["state"] == "WIRE"
          and wire_rows[0]["line"] == 11,
          "AC-EPBW1 AC-EPBW1 a from-import publish is read and names its module")

    # The binding table is the identity module's, so patching it moves this
    # reading and there is no second import parser in this file.
    original = EPWI.FROM_PLAIN_RE
    try:
        EPWI.FROM_PLAIN_RE = re.compile(r"(?!)")
        moved = EPBW.classify_script(
            FROM_WIRE_SCRIPT.splitlines(), "status-export.json",
            "closeout_export_parity_wire")
    finally:
        EPWI.FROM_PLAIN_RE = original
    draft = read(MODULE)
    check([row["state"] for row in moved] == ["UNRESOLVED"]
          and "FROM_AS_RE" in draft and "FROM_PLAIN_RE" in draft
          and "IMPORT_AS_RE" not in draft,
          "AC-EPBW1b AC-EPBW1 the binding table is asked, not restated")

    # AC-EPBW2: the attribute form keeps its reading byte for byte - same
    # receiver, same module, same state, same row keys from the identity module.
    before = [{"line": 10, "receiver": "CEPW",
               "module": "closeout_export_parity_wire", "state": "WIRE"}]
    after = EPWI.audit_script(ATTR_SCRIPT.splitlines(), "status-export.json",
                              "closeout_export_parity_wire")
    check([{key: row[key] for key in ("line", "receiver", "module", "state")}
           for row in after] == before
          and [row["kind"] for row in EPBW.classify_script(
              ATTR_SCRIPT.splitlines(), "status-export.json",
              "closeout_export_parity_wire")] == ["attribute"],
          "AC-EPBW2 AC-EPBW2 the attribute spelling reads exactly as before")

    # AC-EPBW3: a bare call no import binds reads UNRESOLVED, never NO-PUBLISH,
    # so the script is still counted as a publisher that must be looked at.
    unbound = world([("unbound.py", UNBOUND_SCRIPT)])
    report_unbound, code_unbound = EPBW.audit(unbound)
    identity_view = EPWI.audit(unbound)
    check(states(UNBOUND_SCRIPT) == ["UNRESOLVED"]
          and kinds(UNBOUND_SCRIPT) == ["bare"]
          and report_unbound["verdict"] == "UNRESOLVED" and code_unbound == 2
          and report_unbound["unresolved"] == ["unbound.py"]
          and report_unbound["no_publish"] == []
          and report_unbound["bare"] == 1
          and identity_view[0]["unresolved"] == ["unbound.py"]
          and "unbound.py" not in identity_view[0]["no_publish"],
          "AC-EPBW3 AC-EPBW3 an unbound bare publish reads UNRESOLVED")

    # AC-EPBW4: the binding is read from the file's OWN import lines in both
    # directions - a renamed import without its call, and a renamed call
    # without its import, each read UNRESOLVED rather than borrowing a name.
    renamed_view = world([("renamed.py", RENAMED_IMPORT_SCRIPT)])
    report_renamed, code_renamed = EPBW.audit(renamed_view)
    check(states(RENAMED_IMPORT_SCRIPT) == ["UNRESOLVED"]
          and report_renamed["verdict"] == "UNRESOLVED" and code_renamed == 2
          and states(RENAMED_CALL_SCRIPT) == []
          and states(FROM_ALIAS_SCRIPT) == ["WIRE"]
          and kinds(FROM_ALIAS_SCRIPT) == ["from_import"]
          and states(FROM_FOREIGN_SCRIPT) == ["FOREIGN"],
          "AC-EPBW4 AC-EPBW4 import and call must agree, aliases included")

    # A publish spelled inside prose or a fixture literal is not a call: the
    # mask is the identity module's code_only, still asked at call time.
    prose = world([("notes.py", PROSE_SCRIPT)])
    report_prose, code_prose = EPBW.audit(prose)
    check(report_prose["verdict"] == "EMPTY" and code_prose == 0
          and report_prose["publishers"] == []
          and report_prose["no_publish"] == ["notes.py"],
          "AC-EPBW4b AC-EPBW4 a publish spelled in prose is not a call")

    # AC-EPBW5: exit codes 0/2/3/5 and a byte-stable --json over pinned keys.
    root_wire = world([("wire_pub.py", FROM_WIRE_SCRIPT)])
    root_foreign = world([("foreign_pub.py", FROM_FOREIGN_SCRIPT)])
    root_empty = world([("notes.py", PROSE_SCRIPT)])
    rc_wire, out_wire, _ = run(root_wire)
    rc_json, json_a, _ = run(root_wire, ("--json",))
    rc_again, json_b, _ = run(root_wire, ("--json",))
    rc_foreign, out_foreign, _ = run(root_foreign)
    rc_unbound, out_unbound, _ = run(unbound)
    rc_empty, out_empty, _ = run(root_empty)
    rc_missing, _, missing_err = run(os.path.join(root_wire, "no-such-dir"))
    rc_flags, _, flags_err = run(root_wire, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root_wire],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_wire == 0 and "verdict=WIRE" in out_wire
          and "from_import=1 bare=0" in out_wire
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == EPBW.REPORT_KEYS
          and [tuple(row.keys()) for row in parsed["detail"]]
          == [EPBW.CALL_KEYS + ("path",)]
          and rc_foreign == 2 and "verdict=FOREIGN" in out_foreign
          and "foreign_pub.py:11" in out_foreign
          and "some_other_wire" in out_foreign
          and rc_unbound == 2 and "kind=bare" in out_unbound
          and rc_empty == 0 and "verdict=EMPTY" in out_empty
          and rc_missing == 3 and "E_EPBW_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_EPBW_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-EPBW5 AC-EPBW5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-EPBW6: writes nothing, reads no clock, ASCII, stdlib only, and the
    # suite is wired into the runner with its own label.
    source = read(MODULE)
    digest_before = hashlib.sha256(source.encode("utf-8")).hexdigest()
    whole_before = tree_digest(root_wire)
    run(root_wire, ("--json",))
    EPBW.audit(root_wire)
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
          "AC-EPBW6 AC-EPBW6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())