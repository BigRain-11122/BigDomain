"""plain_import_comma_binding suite (R2424).

Criteria AC-PICB1..AC-PICB6 were pinned inside the R2422 tech seed row of
state/queue/tech.md (line 489) BEFORE this code existed.

What this proves: the receiver table matches a plain import with an anchored
single-module pattern, so at HEAD `import os, some_wire as publish` binds
{"os": "os"} and silently says nothing about the second module - a bare
`publish(` call on that line can never resolve, and even the receiver side of
the alias asymmetry cannot see it. One reading now splits the statement with
the SHIPPED splitter, asks the SHIPPED table once for the whole statement and
once per part, and prints both answers beside the two publish-name tables.

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
import plain_import_comma_binding as PICB  # noqa: E402
import relative_import_publish_binding as RIPB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "plain_import_comma_binding.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-plain-import-comma-binding"
WIRED_EXPECT = '"test_plain_import_comma_binding.py"), 6),'

BODY = '''

def go():
    return publish(".", "x")
'''

COMMA_SECOND = "import os, some_wire as publish" + BODY
COMMA_FIRST = "import some_wire as publish, os" + BODY
COMMA_THREE = "import os, some_wire as publish, sys as sh" + BODY
COMMA_DOTTED = "import os, some.wire.mod as publish" + BODY
COMMA_NO_PUBLISH = "import os, sys" + BODY
COMMA_OTHER_NAME = "import os, some_wire as ship" + BODY
FROM_PUBLISH = "from some_wire import publish" + BODY
PLAIN_ALIAS = "import some_wire as publish" + BODY

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
    root = tempfile.mkdtemp(prefix="picb-suite-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def one(script, number=1):
    rows = PICB.reading(script.splitlines())
    return rows[0] if rows else None


def main():
    source = read(MODULE)

    # AC-PICB1: the splitter and the receiver table are asked at CALL time and
    # no import pattern is restated, so patching either moves this reading.
    baseline = one(COMMA_SECOND)
    saved_split = PIAG.plain_parts
    saved_recv = EPWI.import_bindings
    patched = []
    try:
        PIAG.plain_parts = lambda line: [("zzz", "publish")]
        moved = one(COMMA_SECOND)
        patched.append(moved["part_count"] == 1
                       and moved["publish_parts"] == "zzz"
                       and moved["receiver_parts"] == {"publish": "zzz"})
        PIAG.plain_parts = saved_split

        EPWI.import_bindings = lambda lines: {"publish": "sentinel"}
        moved = one(COMMA_SECOND)
        patched.append(moved["receiver"] == {"publish": "sentinel"}
                       and moved["receiver_parts"] == {"publish": "sentinel"}
                       and moved["dropped"] == "(none)")
        EPWI.import_bindings = saved_recv
    finally:
        PIAG.plain_parts = saved_split
        EPWI.import_bindings = saved_recv
    check(all(patched)
          and one(COMMA_SECOND) == baseline
          and "import re" not in source
          and "re.compile" not in source
          and "plain_parts" in source
          and "import_bindings" in source,
          "AC-PICB1 the splitter and the receiver table are asked at call "
          "time and no import pattern is restated")

    # AC-PICB2: the comma list binds publish on the receiver side while both
    # publish-name tables still answer {}, so the line reads UNBOUND and its
    # file is named instead of silently skipped - and the whole-statement
    # answer is printed beside the per-part one.
    row = one(COMMA_SECOND)
    root = world([("list_pub.py", COMMA_SECOND)])
    report, code = PICB.audit(root)
    rc, out, _ = run(root)
    check(row["receiver"] == {"os": "os"}
          and row["receiver_parts"] == {"os": "os", "publish": "some_wire"}
          and row["dropped"] == "publish"
          and row["absolute"] == {}
          and row["relative"] == {}
          and row["verdict"] == PICB.UNBOUND
          and row["part_count"] == 2
          and row["publish_parts"] == "some_wire"
          and code == 2 and report["verdict"] == PICB.ASYMMETRIC
          and report["comma_lines"] == 1 and report["unbound_lines"] == 1
          and report["dropped_parts"] == 1
          and report["asymmetric_files"] == ["list_pub.py"]
          and rc == 2
          and 'receiver={"os": "os"}' in out
          and 'receiver_parts={"os": "os", "publish": "some_wire"}' in out
          and "dropped=publish" in out
          and "absolute={}" in out,
          "AC-PICB2 the comma list binds publish on the receiver side and "
          "reads UNBOUND with both receiver answers printed")

    # AC-PICB3: exactly the parts that bind publish are counted - a comma list
    # without one is not a row, and a three-part list counts one.
    three = one(COMMA_THREE)
    other = one(COMMA_OTHER_NAME)
    no_publish = one(COMMA_NO_PUBLISH)
    first = one(COMMA_FIRST)
    check(no_publish is None
          and other is None
          and PICB.reading(FROM_PUBLISH.splitlines()) == []
          and three["part_count"] == 3
          and three["publish_parts"] == "some_wire"
          and first["publish_parts"] == "some_wire"
          and first["part_count"] == 2
          and PICB.is_comma_import(COMMA_SECOND) is True
          and PICB.is_comma_import("import some_wire as publish") is False
          and PICB.is_comma_import(FROM_PUBLISH) is False,
          "AC-PICB3 exactly the comma parts that bind publish are counted")

    # AC-PICB4: no file reads the empty word while any comma-list line binds
    # publish unbound; every such spelling is named, and a clean tree reads
    # EMPTY at exit 0.
    mixed = world([("second_pub.py", COMMA_SECOND),
                   ("first_pub.py", COMMA_FIRST),
                   ("three_pub.py", COMMA_THREE),
                   ("dotted_pub.py", COMMA_DOTTED),
                   ("plain_pub.py", PLAIN_ALIAS),
                   ("no_publish.py", COMMA_NO_PUBLISH),
                   ("ship_pub.py", COMMA_OTHER_NAME),
                   ("notes.py", "NOTE = 1\n")])
    mixed_report, mixed_code = PICB.audit(mixed)
    empty_report, empty_code = PICB.audit(world([("notes.py", "NOTE = 1\n")]))
    named = mixed_report["asymmetric_files"]
    rows_by_path = {}
    for item in mixed_report["detail"]:
        rows_by_path.setdefault(item["path"], []).append(item)
    check(mixed_code == 2 and mixed_report["verdict"] == PICB.ASYMMETRIC
          and sorted(named) == ["dotted_pub.py", "first_pub.py",
                                "second_pub.py", "three_pub.py"]
          and mixed_report["comma_lines"] == 4
          and mixed_report["unbound_lines"] == 4
          and mixed_report["bound_lines"] == 0
          # MEASURED, not assumed: five bindings are dropped across the four
          # lines, not four - the three-part list drops BOTH its alias parts
          # (publish and sh), because the anchored table reads one module per
          # statement. This window's first draft of this assertion said four
          # and the measurement corrected it; the pinned AC-PICB4 wording
          # ("no file reads the empty word") is untouched.
          and mixed_report["dropped_parts"] == 5
          and "plain_pub.py" not in named
          and "no_publish.py" not in named
          and "ship_pub.py" not in named
          and rows_by_path["dotted_pub.py"][0]["receiver_parts"]
          == {"os": "os", "publish": "some.wire.mod"}
          and all(item["verdict"] == PICB.UNBOUND
                  for rows in rows_by_path.values() for item in rows)
          and empty_code == 0 and empty_report["verdict"] == PICB.EMPTY,
          "AC-PICB4 no file reads EMPTY while a comma-list line binds "
          "publish unbound")

    # AC-PICB5: exits 0/2/3/5 with a byte-stable --json over the pinned keys.
    rc_clean, out_clean, _ = run(world([("notes.py", "NOTE = 1\n")]))
    rc_json, json_a, _ = run(root, ("--json",))
    rc_again, json_b, _ = run(root, ("--json",))
    rc_bad, out_bad, _ = run(root)
    rc_missing, _o, missing_err = run(os.path.join(root, "no-such-dir"))
    rc_flags, _o2, flags_err = run(root, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_clean == 0 and "verdict=EMPTY" in out_clean
          and rc_json == 2 and json_a == json_b
          and tuple(parsed.keys()) == PICB.REPORT_KEYS
          and [tuple(item.keys()) for item in parsed["detail"]]
          == [PICB.CALL_KEYS + ("path",)] * len(parsed["detail"])
          and rc_bad == 2 and "verdict=ASYMMETRIC" in out_bad
          and rc_missing == 3 and "E_PICB_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_PICB_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-PICB5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-PICB6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    digest_before = hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
    whole_before = tree_digest(root)
    run(root, ("--json",))
    PICB.audit(root)
    recipes = read(RUNNER)
    forbidden = ("datetime", "time.time", "socket", "urllib", "requests",
                 "os.open", "io.open")
    check(tree_digest(root) == whole_before
          and hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
          == digest_before
          and all(name not in source for name in forbidden)
          and all(ord(char) < 128 for char in source)
          and WIRED_EXPECT in recipes
          and LABEL in recipes,
          "AC-PICB6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())