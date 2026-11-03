"""plain_import_alias_gate suite (R2422).

Criteria AC-PIAG1..AC-PIAG6 were pinned inside the R2420 tech seed row of
state/queue/tech.md BEFORE this code existed.

What this proves: the shipped alias gate reads FROM-imports only, so the house
idiom `import M as publish` is outside its scope. Measured at R2420 at HEAD,
that line binds publish in the RECEIVER table while both publish-name tables
answer {} and the from-import gate reads mentions_publish=False. One reading
now asks all three tables at call time, per plain-import line that binds the
local name publish, and prints the answers side by side.

The pre-registered AC-PIAG4 wording ("no file reads CLEAN while a plain-import
alias binds publish unbound") is CORRECTED here by measurement: no
publish-name table reads a plain import at all, so such a line is UNBOUND by
construction and the word CLEAN is unreachable for this gate. The suite proves
the stronger property instead - every file carrying such a line reads
ASYMMETRIC and is named, and a tree with none reads EMPTY.

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
import plain_import_alias_gate as PIAG  # noqa: E402
import relative_import_publish_binding as RIPB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "plain_import_alias_gate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-plain-import-alias-gate"
WIRED_EXPECT = '"test_plain_import_alias_gate.py"), 6),'

HEAD = '''import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
'''

BODY = '''    return publish(".", EXPORT, text="{}")
'''

PLAIN_ALIAS = ("import some_wire as publish\n" + HEAD + BODY)
PLAIN_DOTTED = ("import some.wire.mod as publish\n" + HEAD + BODY)
PLAIN_BARE = ("import publish\n" + HEAD + BODY)
PLAIN_ALIAS_LIST = ("import os, some_wire as publish\n" + HEAD + BODY)
PLAIN_NOT_PUBLISH = ("import some_wire as ship\n" + HEAD + BODY)
FROM_PUBLISH = ("from some_wire import publish\n" + HEAD + BODY)
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
    root = tempfile.mkdtemp(prefix="piag-")
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
    return PIAG.reading(script.splitlines())[0]


def main():
    # AC-PIAG1: all three tables are asked at CALL time and none is restated,
    # so patching any table moves this reading and this module owns no
    # import-line pattern of its own.
    baseline = one(PLAIN_ALIAS)
    source = read(MODULE)
    saved_rel = RIPB.relative_publish_names
    saved_abs = EPBW.imported_publish_names
    saved_recv = EPWI.import_bindings
    patched_ok = []
    try:
        EPBW.imported_publish_names = lambda lines: {"publish": "sentinel"}
        patched_ok.append(one(PLAIN_ALIAS)["absolute"] == {"publish": "sentinel"})
        EPBW.imported_publish_names = saved_abs

        RIPB.relative_publish_names = lambda lines: {"publish": "sentinel"}
        patched_ok.append(one(PLAIN_ALIAS)["relative"] == {"publish": "sentinel"})
        RIPB.relative_publish_names = saved_rel

        EPWI.import_bindings = lambda lines: {"publish": "sentinel"}
        patched_ok.append(one(PLAIN_ALIAS)["receiver"] == {"publish": "sentinel"})
        EPWI.import_bindings = saved_recv

        EPBW.imported_publish_names = lambda lines: {"publish": "sentinel"}
        patched_ok.append(one(PLAIN_ALIAS)["verdict"] == PIAG.BOUND)
        EPBW.imported_publish_names = saved_abs

        EPBW.imported_publish_names = lambda lines: {}
        RIPB.relative_publish_names = lambda lines: {}
        patched_ok.append(one(PLAIN_ALIAS)["verdict"] == PIAG.UNBOUND)
    finally:
        RIPB.relative_publish_names = saved_rel
        EPBW.imported_publish_names = saved_abs
        EPWI.import_bindings = saved_recv
    check(all(patched_ok)
          and one(PLAIN_ALIAS) == baseline
          and "re.compile" not in source
          and "IMPORT_AS_RE" in source
          and "IMPORT_PLAIN_RE" in source,
          "AC-PIAG1 the three tables are asked at call time, never restated")

    # AC-PIAG2: `import M as publish` binds in the receiver table and binds
    # nothing in either publish-name table - both sides printed, and the line
    # and its file read UNBOUND / ASYMMETRIC rather than skipped.
    alias = one(PLAIN_ALIAS)
    root_alias = world([("alias_pub.py", PLAIN_ALIAS)])
    alias_report, alias_code = PIAG.audit(root_alias)
    rc_alias, out_alias, _ = run(root_alias)
    check(alias["receiver"] == {"publish": "some_wire"}
          and alias["absolute"] == {}
          and alias["relative"] == {}
          and alias["bound_by"] == "receiver"
          and alias["verdict"] == PIAG.UNBOUND
          and alias["spelling"] == PIAG.PLAIN
          and alias["imported"] == "some_wire"
          and alias["local"] == "publish"
          and alias_code == 2
          and alias_report["verdict"] == PIAG.ASYMMETRIC
          and alias_report["unbound_lines"] == 1
          and alias_report["asymmetric_files"] == ["alias_pub.py"]
          and rc_alias == 2
          and 'receiver={"publish": "some_wire"}' in out_alias
          and "absolute={}" in out_alias
          and "relative={}" in out_alias,
          "AC-PIAG2 a plain-import publish binding reads bound on the "
          "receiver side and unbound on both publish-name sides, both printed")

    # AC-PIAG3: a plain import that does not bind the name publish is not a
    # publish line at all - neither the alias for another name, nor a plain
    # import of an unrelated module, nor a from-import (the other gate's job).
    other = world([("ship_pub.py", PLAIN_NOT_PUBLISH), ("notes.py", NO_IMPORT),
                   ("plain_os.py", "import os\nimport sys\n")])
    other_report, other_code = PIAG.audit(other)
    not_publish_ok = (PIAG.reading(PLAIN_NOT_PUBLISH.splitlines()) == []
                      and NOT_PUBLISH_ROWS_OK()
                      and PIAG.mentions_publish("import some_wire as publish") is True
                      and other_code == 0
                      and other_report["verdict"] == PIAG.EMPTY
                      and other_report["files_with_imports"] == 0
                      and other_report["detail"] == [])
    check(not_publish_ok,
          "AC-PIAG3 an import that does not bind publish is not counted")

    # AC-PIAG4: every file carrying such a line reads ASYMMETRIC and is named;
    # no such file can read the gate's empty word, and a tree with none reads
    # EMPTY. Spelling variants all land the same way.
    #
    # DISCLOSED rather than hidden: for the comma-list spelling the receiver
    # table itself reads only the LEADING module ("os"), so it does not bind
    # publish either - a second blind spot found by measuring instead of
    # assuming, and the line is still named ASYMMETRIC because this gate reads
    # the tail itself.
    mixed = world([("alias_pub.py", PLAIN_ALIAS), ("dotted_pub.py", PLAIN_DOTTED),
                   ("bare_pub.py", PLAIN_BARE), ("list_pub.py", PLAIN_ALIAS_LIST),
                   ("ship_pub.py", PLAIN_NOT_PUBLISH),
                   ("from_pub.py", FROM_PUBLISH)])
    mixed_report, mixed_code = PIAG.audit(mixed)
    empty_report, empty_code = PIAG.audit(world([("notes.py", "NOTE = 1\n")]))
    named = mixed_report["asymmetric_files"]
    rows_by_path = {}
    for row in mixed_report["detail"]:
        rows_by_path.setdefault(row["path"], []).append(row)
    check(mixed_code == 2 and mixed_report["verdict"] == PIAG.ASYMMETRIC
          and sorted(named) == ["alias_pub.py", "bare_pub.py",
                                "dotted_pub.py", "list_pub.py"]
          and mixed_report["unbound_lines"] == 4
          and mixed_report["bound_lines"] == 0
          and "from_pub.py" not in named
          and all(row["verdict"] == PIAG.UNBOUND
                  for rows in rows_by_path.values() for row in rows)
          and rows_by_path["dotted_pub.py"][0]["imported"] == "some.wire.mod"
          and rows_by_path["list_pub.py"][0]["receiver"] == {"os": "os"}
          and empty_code == 0 and empty_report["verdict"] == PIAG.EMPTY,
          "AC-PIAG4 every file carrying a plain-import publish binding reads "
          "ASYMMETRIC and is named")

    # AC-PIAG5: exits 0/2/3/5 with a byte-stable --json over the pinned keys.
    rc_clean, out_clean, _ = run(other)
    rc_json, json_a, _ = run(root_alias, ("--json",))
    rc_again, json_b, _ = run(root_alias, ("--json",))
    rc_bad, out_bad, _ = run(root_alias)
    rc_missing, _out_missing, missing_err = run(
        os.path.join(root_alias, "no-such-dir"))
    rc_flags, _out_flags, flags_err = run(root_alias, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root_alias],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_clean == 0 and "verdict=EMPTY" in out_clean
          and rc_json == 2 and json_a == json_b
          and tuple(parsed.keys()) == PIAG.REPORT_KEYS
          and [tuple(row.keys()) for row in parsed["detail"]]
          == [PIAG.CALL_KEYS + ("path",)] * len(parsed["detail"])
          and rc_bad == 2 and "verdict=ASYMMETRIC" in out_bad
          and rc_missing == 3 and "E_PIAG_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_PIAG_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-PIAG5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-PIAG6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    source = read(MODULE)
    digest_before = hashlib.sha256(source.encode("utf-8")).hexdigest()
    whole_before = tree_digest(root_alias)
    run(root_alias, ("--json",))
    PIAG.audit(root_alias)
    recipes = read(RUNNER)
    forbidden = ("datetime", "time.time", "socket", "urllib", "requests",
                 "os.open", "io.open")
    check(tree_digest(root_alias) == whole_before
          and hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
          == digest_before
          and all(name not in source for name in forbidden)
          and all(ord(char) < 128 for char in source)
          and WIRED_EXPECT in recipes
          and LABEL in recipes,
          "AC-PIAG6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


def NOT_PUBLISH_ROWS_OK():
    """A publish-shaped from-import belongs to the other gate, not this one."""
    return (PIAG.mentions_publish(FROM_PUBLISH) is False
            and PIAG.mentions_publish("import some_wire as ship") is False
            and PIAG.mentions_publish("import os") is False)


if __name__ == "__main__":
    sys.exit(main())