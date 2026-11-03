"""relative_import_alias_gate suite (R2420).

Criteria AC-RIAG1..AC-RIAG6 were pinned inside the R2402 tech seed row of
state/queue/tech.md:486 BEFORE this code existed.

What this proves: three shipped tables answer three different alias questions
and nothing said which one a reader meant, so one line could read bound or
unbound depending on which face looked at it. One reading now asks all three
at call time, per from-import line that mentions publish, and prints the
answers side by side; a line no publish-name table binds reads UNBOUND and a
file with any such line reads ASYMMETRIC, so a file can never read CLEAN while
the tables disagree.

The seed row's own premise was CORRECTED by measurement, and the correction
is proved here rather than repeated: it claimed the absolute table binds the
alias of ANY imported name. Measured at HEAD, `from some_wire import other as
publish` binds nothing in the absolute PUBLISH-NAME table - it is the receiver
table that binds it - and both publish-name tables require the imported name
to be publish, so a renamed relative publish import is invisible to every
publish-name table. AC-RIAG2 therefore reads the receiver face as the bound
absolute side and the relative table as unbound, with both printed.

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

import export_publish_from_import_law as EPBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import relative_import_alias_gate as RIAG  # noqa: E402
import relative_import_publish_binding as RIPB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "relative_import_alias_gate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-relative-import-alias-gate"
WIRED_EXPECT = '"test_relative_import_alias_gate.py"), 6),'

EXPORT = "status-export.json"

HEAD = '''import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
'''

BODY = '''    return publish(".", EXPORT, text="{}")
'''

RENAMED_ABS = ("from some_wire import other as publish\n" + HEAD + BODY)
RENAMED_REL = ("from .wire import other as publish\n" + HEAD + BODY)
PLAIN_ABS = ("from some_wire import publish\n" + HEAD + BODY)
PLAIN_REL = ("from .wire import publish\n" + HEAD + BODY)
ALIAS_ABS = ("from some_wire import publish as ship\n" + HEAD + BODY)
ALIAS_REL = ("from .wire import publish as ship\n" + HEAD + BODY)
NO_IMPORT = HEAD + BODY

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
    root = tempfile.mkdtemp(prefix="riag-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def one(script):
    return RIAG.reading(script.splitlines())[0]


def main():
    # AC-RIAG1: all three tables are asked at CALL time and none is restated,
    # so patching any table moves this reading and this module owns no
    # import-line pattern of its own.
    baseline = one(PLAIN_REL)
    source = read(MODULE)
    saved_rel = RIPB.relative_publish_names
    saved_abs = EPBW.imported_publish_names
    saved_recv = EPWI.import_bindings
    patched_ok = []
    try:
        RIPB.relative_publish_names = lambda lines: {}
        patched_ok.append(one(PLAIN_REL)["verdict"] == RIAG.UNBOUND)
        RIPB.relative_publish_names = saved_rel

        EPBW.imported_publish_names = lambda lines: {"publish": "sentinel"}
        patched_ok.append(one(PLAIN_ABS)["absolute"] == {"publish": "sentinel"})
        EPBW.imported_publish_names = saved_abs

        EPWI.import_bindings = lambda lines: {"publish": "sentinel"}
        patched_ok.append(one(PLAIN_ABS)["receiver"] == {"publish": "sentinel"})
        EPWI.import_bindings = saved_recv
    finally:
        RIPB.relative_publish_names = saved_rel
        EPBW.imported_publish_names = saved_abs
        EPWI.import_bindings = saved_recv
    check(all(patched_ok)
          and one(PLAIN_REL) == baseline
          and "re.compile" not in source
          and "FROM_PLAIN_RE" not in source.split("def ")[0]
          and "REL_PLAIN_RE" in source,
          "AC-RIAG1 the three tables are asked at call time, never restated")

    # AC-RIAG2: the renamed absolute import binds in the receiver table and
    # binds nothing in either publish-name table - both sides printed, and the
    # line and its file read UNBOUND / ASYMMETRIC rather than clean.
    renamed = one(RENAMED_ABS)
    root_renamed = world([("renamed_pub.py", RENAMED_ABS)])
    renamed_report, renamed_code = RIAG.audit(root_renamed)
    rc_renamed, out_renamed, _ = run(root_renamed)
    check(renamed["receiver"] == {"publish": "some_wire"}
          and renamed["absolute"] == {}
          and renamed["relative"] == {}
          and renamed["bound_by"] == "receiver"
          and renamed["verdict"] == RIAG.UNBOUND
          and renamed["spelling"] == RIAG.ABSOLUTE
          and renamed["imported"] == "other"
          and renamed["local"] == "publish"
          and renamed_code == 2
          and renamed_report["verdict"] == RIAG.ASYMMETRIC
          and renamed_report["unbound_lines"] == 1
          and renamed_report["asymmetric_files"] == ["renamed_pub.py"]
          and rc_renamed == 2
          and 'receiver={"publish": "some_wire"}' in out_renamed
          and "absolute={}" in out_renamed
          and "relative={}" in out_renamed,
          "AC-RIAG2 a renamed import reads bound on the receiver side and "
          "unbound on both publish-name sides, both printed")

    # AC-RIAG3: the matching import reads BOUND on both spellings - the
    # absolute line through the absolute and receiver tables, the relative
    # line through the relative table - with the local name it binds.
    abs_row = one(PLAIN_ABS)
    rel_row = one(PLAIN_REL)
    alias_abs_row = one(ALIAS_ABS)
    alias_rel_row = one(ALIAS_REL)
    root_bound = world([("abs_pub.py", PLAIN_ABS), ("rel_pub.py", PLAIN_REL),
                        ("alias_abs_pub.py", ALIAS_ABS),
                        ("alias_rel_pub.py", ALIAS_REL)])
    bound_report, bound_code = RIAG.audit(root_bound)
    rc_bound, out_bound, _ = run(root_bound)
    check(abs_row["verdict"] == rel_row["verdict"] == RIAG.BOUND
          and abs_row["bound_by"] == "receiver,absolute"
          and abs_row["absolute"] == {"publish": "some_wire"}
          and rel_row["bound_by"] == "relative"
          and rel_row["relative"] == {"publish": ".wire"}
          and alias_abs_row["local"] == "ship"
          and alias_abs_row["absolute"] == {"ship": "some_wire"}
          and alias_rel_row["local"] == "ship"
          and alias_rel_row["relative"] == {"ship": ".wire"}
          and bound_code == 0
          and bound_report["verdict"] == RIAG.CLEAN
          and bound_report["bound_lines"] == 4
          and bound_report["unbound_lines"] == 0
          and rc_bound == 0 and "verdict=CLEAN" in out_bound,
          "AC-RIAG3 a matching import reads bound on both spellings")

    # AC-RIAG4: no file reads CLEAN while the tables disagree - the verdict is
    # computed from the same rows, so CLEAN implies zero UNBOUND rows and any
    # disagreeing file is named in asymmetric_files.
    mixed_report, mixed_code = RIAG.audit(
        world([("renamed_pub.py", RENAMED_ABS), ("rel_renamed.py", RENAMED_REL),
               ("clean_pub.py", PLAIN_ABS)]))
    clean_only, clean_code = RIAG.audit(world([("clean_pub.py", PLAIN_ABS)]))
    empty_report, empty_code = RIAG.audit(world([("notes.py", "NOTE = 1\n")]))
    clean_rows = [row for row in mixed_report["detail"]
                  if row["path"] == "clean_pub.py"]
    check(mixed_code == 2 and mixed_report["verdict"] == RIAG.ASYMMETRIC
          and sorted(mixed_report["asymmetric_files"])
          == ["rel_renamed.py", "renamed_pub.py"]
          and mixed_report["unbound_lines"] == 2
          and mixed_report["bound_lines"] == 1
          and clean_rows and all(row["verdict"] == RIAG.BOUND
                                 for row in clean_rows)
          and clean_code == 0 and clean_only["verdict"] == RIAG.CLEAN
          and empty_code == 0 and empty_report["verdict"] == RIAG.EMPTY,
          "AC-RIAG4 no file reads CLEAN while the tables disagree")

    # AC-RIAG5: exits 0/2/3/5 with a byte-stable --json over the pinned keys.
    rc_clean, out_clean, _ = run(root_bound)
    rc_json, json_a, _ = run(root_bound, ("--json",))
    rc_again, json_b, _ = run(root_bound, ("--json",))
    rc_bad, out_bad, _ = run(root_renamed)
    rc_missing, _, missing_err = run(os.path.join(root_bound, "no-such-dir"))
    rc_flags, _, flags_err = run(root_bound, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root_bound],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_clean == 0 and "verdict=CLEAN" in out_clean
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == RIAG.REPORT_KEYS
          and [tuple(row.keys()) for row in parsed["detail"]]
          == [RIAG.CALL_KEYS + ("path",)] * len(parsed["detail"])
          and rc_bad == 2 and "verdict=ASYMMETRIC" in out_bad
          and rc_missing == 3 and "E_RIAG_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_RIAG_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-RIAG5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-RIAG6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    source = read(MODULE)
    digest_before = hashlib.sha256(source.encode("utf-8")).hexdigest()
    whole_before = tree_digest(root_bound)
    run(root_bound, ("--json",))
    RIAG.audit(root_bound)
    recipes = read(RUNNER)
    forbidden = ("datetime", "time.time", "socket", "urllib", "requests",
                 "os.open", "io.open")
    check(tree_digest(root_bound) == whole_before
          and hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
          == digest_before
          and all(name not in source for name in forbidden)
          and all(ord(char) < 128 for char in source)
          and WIRED_EXPECT in recipes
          and LABEL in recipes,
          "AC-RIAG6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())