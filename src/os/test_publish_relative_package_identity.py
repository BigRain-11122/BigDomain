"""publish_relative_package_identity suite (R2415).

Criteria AC-PRPI1..AC-PRPI6 were pinned inside the R2402 tech seed row of
state/queue/tech.md:482 BEFORE this code existed.

What this proves: the relative binding law names the relative module text but
reads one file on its own, so a real in-package publisher spelled
`from .wire import publish` reads RELATIVE and cannot be told from a foreign
one. One added notion - a caller-DECLARED package - joins the relative text
and the call is then classified like an absolute one by the parent law's own
classifier, asked at call time. A join that climbs past the package refuses
naming both sides instead of inventing a module, and with no package declared
every reading is the parent's own byte for byte.

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

import export_publish_wire_identity as EPWI  # noqa: E402
import publish_relative_package_identity as PRPI  # noqa: E402
import relative_import_publish_binding as RIPB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "publish_relative_package_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-publish-relative-package-identity"
WIRED_EXPECT = '"test_publish_relative_package_identity.py"), 6),'

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
REL_UP = ("from ..wire import publish\n" + HEAD + BODY)
ABS_WIRE = ("from closeout_export_parity_wire import publish\n" + HEAD + BODY)
ABS_FOREIGN = ("from some_other_wire import publish\n" + HEAD + BODY)
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
    root = tempfile.mkdtemp(prefix="prpi-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def rows(script, package=None, wire=WIRE, refusals=None):
    return PRPI.classify_script(script.splitlines(), package, EXPORT, wire,
                                refusals)


def states(script, package=None, wire=WIRE):
    return [row["state"] for row in rows(script, package, wire)]


def main():
    # AC-PRPI1: a declared package joins `.M` onto it and the joined module is
    # then classified exactly like an absolute one - WIRE when it is the wire
    # module, FOREIGN when it is not.
    wire_rows = rows(REL_MODULE, "mypkg", "mypkg.wire")
    foreign_rows = rows(REL_MODULE, "mypkg", WIRE)
    check(len(wire_rows) == 1
          and wire_rows[0]["kind"] == "from_import"
          and wire_rows[0]["module"] == "mypkg.wire"
          and wire_rows[0]["state"] == "WIRE"
          and wire_rows[0]["relative"] is True
          and len(foreign_rows) == 1
          and foreign_rows[0]["module"] == "mypkg.wire"
          and foreign_rows[0]["state"] == "FOREIGN"
          and PRPI.join_package("a.b", ".c.d") == "a.b.c.d",
          "AC-PRPI1 a declared package resolves .M to package.M")

    # AC-PRPI2: `.` is the package itself, and `..` drops one package segment
    # before the tail is appended.
    package_rows = rows(REL_PACKAGE, "mypkg", "mypkg")
    up_rows = rows(REL_UP, "mypkg.sub", "mypkg.wire")
    check(len(package_rows) == 1
          and package_rows[0]["module"] == "mypkg"
          and package_rows[0]["state"] == "WIRE"
          and len(up_rows) == 1
          and up_rows[0]["module"] == "mypkg.wire"
          and up_rows[0]["state"] == "WIRE"
          and PRPI.join_package("a.b", ".") == "a.b"
          and PRPI.join_package("a.b", "..") == "a",
          "AC-PRPI2 . resolves to the package and .. climbs it")

    # AC-PRPI3: with NO package every reading is the parent's own - the rows
    # are the same objects' content, and the audit counts are identical.
    same_rows = all(
        rows(script, None) == RIPB.classify_script(script.splitlines(),
                                                   EXPORT, WIRE)
        for script in (REL_PACKAGE, REL_MODULE, REL_UP, ABS_WIRE,
                       ABS_FOREIGN, BARE_UNBOUND))
    root = world([("rel_pub.py", REL_MODULE), ("abs_pub.py", ABS_WIRE),
                  ("foreign_pub.py", ABS_FOREIGN),
                  ("bare_pub.py", BARE_UNBOUND)])
    mine, my_code = PRPI.audit(root, None)
    theirs, their_code = RIPB.audit(root)
    same_audit = (my_code == their_code
                  and my_code == 2
                  and mine["verdict"] == theirs["verdict"] == "UNRESOLVED"
                  and mine["detail"] == theirs["detail"]
                  and mine["publishers"] == theirs["publishers"]
                  and mine["wire"] == theirs["wire"]
                  and mine["foreign"] == theirs["foreign"]
                  and mine["unresolved"] == theirs["unresolved"]
                  and mine["relative"] == theirs["relative"] == 1
                  and mine["no_publish"] == theirs["no_publish"])
    rc_rel, out_rel, _ = run(world([("rel_pub.py", REL_MODULE)]))
    check(same_rows and same_audit
          and rc_rel == 2 and "verdict=RELATIVE" in out_rel
          and "package=(none)" in out_rel
          and "module=.wire" in out_rel,
          "AC-PRPI3 no package keeps today's RELATIVE reading byte for byte")

    # AC-PRPI4: a declaration that cannot be joined refuses naming it, never
    # guessing an absolute module - both the bad-package and the over-climb
    # cases, with the written text preserved on the refused row.
    refused_at = []
    try:
        PRPI.check_package("bad/name")
    except PRPI.PublishRelativePackageIdentityError as exc:
        refused_at.append(exc.code == "E_PRPI_BAD_PACKAGE"
                          and "bad/name" in str(exc))
    try:
        PRPI.check_package("")
    except PRPI.PublishRelativePackageIdentityError as exc:
        refused_at.append(exc.code == "E_PRPI_BAD_PACKAGE")
    try:
        PRPI.check_package("1bad")
    except PRPI.PublishRelativePackageIdentityError as exc:
        refused_at.append(exc.code == "E_PRPI_BAD_PACKAGE")
    try:
        PRPI.join_package("mypkg", "..")
        refused_at.append(False)
    except PRPI.CannotJoinError as exc:
        refused_at.append(exc.code == "E_PRPI_CANNOT_JOIN"
                          and exc.package == "mypkg" and exc.text == "..")
    root_climb = world([("up_pub.py", REL_UP)])
    climb, climb_code = PRPI.audit(root_climb, "mypkg")
    rc_climb, out_climb, _ = run(root_climb, ("--package", "mypkg"))
    refused_row = [row for row in climb["detail"] if row["state"] == "REFUSED"]
    check(all(refused_at) and climb_code == 2
          and climb["verdict"] == "REFUSED"
          and climb["refused"] == ["up_pub.py:10"]
          and len(refused_row) == 1
          and refused_row[0]["module"] == "..wire"
          and "mypkg.wire" not in json.dumps(climb)
          and rc_climb == 2 and "verdict=REFUSED" in out_climb
          and "E_PRPI_CANNOT_JOIN package=mypkg" in out_climb,
          "AC-PRPI4 an unjoinable declaration refuses naming it")

    # AC-PRPI5: exits 0/2/3/5 with a byte-stable --json over the pinned keys.
    root_wire = world([("rel_pub.py", REL_MODULE)])
    root_foreign = world([("rel_pub.py", REL_MODULE)])
    root_empty = world([("notes.py", "NOTE = 'nothing here'\n")])
    rc_wire, out_wire, _ = run(root_wire,
                               ("--package", "mypkg", "--wire", "mypkg.wire"))
    rc_json, json_a, _ = run(root_wire,
                             ("--package", "mypkg", "--wire", "mypkg.wire",
                              "--json"))
    rc_again, json_b, _ = run(root_wire,
                              ("--package", "mypkg", "--wire", "mypkg.wire",
                               "--json"))
    rc_foreign, out_foreign, _ = run(root_foreign, ("--package", "mypkg"))
    rc_empty, out_empty, _ = run(root_empty, ("--package", "mypkg"))
    rc_missing, _, missing_err = run(os.path.join(root_wire, "no-such-dir"))
    rc_flags, _, flags_err = run(root_wire, ("--nope",))
    rc_bad_package, _, package_err = run(root_wire, ("--package", "bad/name"))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root_wire],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_wire == 0 and "verdict=WIRE" in out_wire
          and "package=mypkg" in out_wire
          and "kind=from_import" not in out_wire
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == PRPI.REPORT_KEYS
          and [tuple(row.keys()) for row in parsed["detail"]]
          == [PRPI.CALL_KEYS + ("path",)]
          and rc_foreign == 2 and "verdict=FOREIGN" in out_foreign
          and "mypkg.wire" in out_foreign
          and rc_empty == 0 and "verdict=EMPTY" in out_empty
          and rc_missing == 3 and "E_PRPI_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_PRPI_BAD_FLAGS" in flags_err
          and rc_bad_package == 5 and "E_PRPI_BAD_PACKAGE" in package_err
          and "bad/name" in package_err
          and rc_no_check == 5,
          "AC-PRPI5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-PRPI6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    source = read(MODULE)
    digest_before = hashlib.sha256(source.encode("utf-8")).hexdigest()
    whole_before = tree_digest(root_wire)
    run(root_wire, ("--package", "mypkg", "--json"))
    PRPI.audit(root_wire, "mypkg")
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
          "AC-PRPI6 AC-PRPI6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())