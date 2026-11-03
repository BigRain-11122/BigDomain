"""comma_binding_consumer_wire suite (R2428).

Criteria AC-PICBC1..AC-PICBC6 were pinned inside the R2426 tech seed row of
state/queue/tech.md (line 491) BEFORE this code existed.

What this proves: comma_binding_wire resolved a comma-list publisher, but no
shipped reading asked it - the identity face still answered UNRESOLVED (or
EMPTY) for exactly the spelling the house uses. One consumer now puts that
table on the identity path, and every file without a comma list keeps its rows
byte for byte.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import comma_binding_consumer_wire as PICBC  # noqa: E402
import comma_binding_wire as PICBW  # noqa: E402
import export_publish_from_import_law as EPBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "comma_binding_consumer_wire.py")
IDENTITY = os.path.join(BASE, "export_publish_wire_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-comma-binding-consumer-wire"
WIRED_EXPECT = '"test_comma_binding_consumer_wire.py"), 6),'

EXPORT = "status-export.json"
WIRE = "closeout_export_parity_wire"
OWNER_LINE = "from queue_floor_export_face import EXPORT"

CALL = "\n\ndef go():\n    return CEPW.publish(PATH, EXPORT)\n"
COMMA_WIRE = ("import os, closeout_export_parity_wire as CEPW\n"
              + OWNER_LINE + "\n" + CALL)
COMMA_FOREIGN = ("import os, some_other_wire as CEPW\n"
                 + OWNER_LINE + "\n" + CALL)
PLAIN_WIRE = ("import closeout_export_parity_wire as CEPW\n"
              + OWNER_LINE + "\n" + CALL)
FROM_IMPORT = ("from closeout_export_parity_wire import publish\n"
               + OWNER_LINE + "\n\ndef go():\n    return publish(PATH, EXPORT)\n")
BARE = (OWNER_LINE + "\n\ndef go():\n    return publish(PATH, EXPORT)\n")
UNBOUND = ("import os\n" + OWNER_LINE
           + "\n\ndef go():\n    return ghost.publish(PATH, EXPORT)\n")

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
    root = tempfile.mkdtemp(prefix="picbc-suite-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(command, extra=()):
    argv = list(command)
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def head_identity():
    """The HEAD copy of the identity module, imported under its own name."""
    source = subprocess.run(
        ["git", "-C", REPO, "show", "HEAD:src/os/export_publish_wire_identity.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if source.returncode != 0:
        return None
    temp = tempfile.mkdtemp(prefix="picbc-head-")
    path = os.path.join(temp, "head_export_publish_wire_identity.py")
    with io.open(path, "wb") as handle:
        handle.write(source.stdout)
    spec = importlib.util.spec_from_file_location("head_epwi", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    shutil.rmtree(temp, ignore_errors=True)
    return module


def rows(text, export_name=EXPORT, wire_module=WIRE):
    return PICBC.classify_script(text.splitlines(), export_name, wire_module)


def main():
    source = read(MODULE)

    # AC-PICBC1: the table is comma_binding_wire.bindings asked at CALL time,
    # proved by patching that table and watching the identity row move - and
    # no split is restated here (no splitter, no pattern, no regex).
    fixture = world([("comma_pub.py", COMMA_WIRE)])
    baseline, _code = EPWI.audit(fixture)
    moved_rows = []
    saved = PICBW.bindings
    try:
        PICBW.bindings = lambda lines: {"CEPW": "sentinel_wire"}
        patched, _code2 = EPWI.audit(fixture)
        moved_rows.append(
            patched["detail"][0]["module"] == "sentinel_wire"
            and patched["detail"][0]["state"] == EPWI.FOREIGN)
        PICBW.bindings = saved
    finally:
        PICBW.bindings = saved
    check(all(moved_rows)
          and baseline["verdict"] == EPWI.WIRE
          and baseline["detail"][0]["module"] == WIRE
          and "bindings" in source
          and "parts_of" not in source
          and "part_statement" not in source
          and "import re" not in source
          and "re.compile" not in source
          and "classify_line" in source
          and "classify_script" in source,
          "AC-PICBC1 the comma-aware table is asked at call time and no "
          "split is restated")

    # AC-PICBC2: a comma-list publisher on the identity path reads WIRE with
    # its module named - not UNRESOLVED and not NO-PUBLISH - and FOREIGN when
    # the resolved module is not the wire.
    report, code = EPWI.audit(fixture)
    foreign_root = world([("foreign_pub.py", COMMA_FOREIGN)])
    foreign, foreign_code = EPWI.audit(foreign_root)
    own, own_code = PICBC.audit(fixture)
    head = EPWI.audit_script(COMMA_WIRE.splitlines(), EXPORT, WIRE)
    check(report["verdict"] == EPWI.WIRE and code == 0
          and report["publishers"] == ["comma_pub.py"]
          and report["wire"] == ["comma_pub.py"]
          and report["unresolved"] == []
          and report["no_publish"] == []
          and report["detail"][0]["receiver"] == "CEPW"
          and report["detail"][0]["module"] == WIRE
          and foreign["verdict"] == EPWI.FOREIGN and foreign_code == 2
          and foreign["detail"][0]["module"] == "some_other_wire"
          and own["verdict"] == PICBC.WIRE and own_code == 0
          and own["comma_files"] == 1 and own["comma_lines"] == 1
          and [row["state"] for row in head] == [EPWI.WIRE],
          "AC-PICBC2 a comma-list publisher reads WIRE (or FOREIGN) with its "
          "module instead of UNRESOLVED")

    # AC-PICBC3: a script with no comma list keeps every key of every row
    # byte-identical - proved against the HEAD identity module on fixtures and
    # against the shipped from-import law over every real non-comma file.
    head_module = head_identity()
    fixtures = [("plain_pub.py", PLAIN_WIRE), ("from_pub.py", FROM_IMPORT),
                ("bare_pub.py", BARE)]
    fixture_root = world(fixtures)
    differing = []
    head_missing = head_module is None
    if not head_missing:
        for name, text in fixtures:
            now_rows = EPWI.audit_script(text.splitlines(), EXPORT, WIRE)
            head_rows = head_module.audit_script(text.splitlines(), EXPORT, WIRE)
            if now_rows != head_rows or list(map(tuple, [r.keys() for r in now_rows])) \
                    != list(map(tuple, [r.keys() for r in head_rows])):
                differing.append(name)
    live_root = os.path.join(SRC, "os")
    live_compared = 0
    live_differing = []
    for path in EPWI.guard().scan_scripts(live_root):
        name = os.path.basename(path)
        if name in (PICBC.SELF_NAME, PICBC.SELF_TEST_NAME):
            continue
        try:
            lines = EPWI.guard().read_lines(path)
        except (IOError, OSError):
            continue
        code = EPWI.code_only(lines)
        if PICBC.has_comma(code):
            continue
        live_compared += 1
        if PICBC.classify_script(lines, EXPORT, WIRE) != EPBW.classify_script(
                lines, EXPORT, WIRE):
            live_differing.append(name)
    report3, code3 = EPWI.audit(fixture_root)
    # plain and from-import resolve to the wire; the bare spelling has no
    # binding at all, so the fixture pile honestly reads UNRESOLVED at exit 2
    # while every one of its rows still matches the HEAD module's.
    check(not head_missing and not differing and not live_differing
          and live_compared > 900
          and report3["verdict"] == EPWI.UNRESOLVED and code3 == 2
          and report3["wire"] == ["from_pub.py", "plain_pub.py"]
          and report3["unresolved"] == ["bare_pub.py"]
          and len(report3["detail"]) == 3,
          "AC-PICBC3 a script with no comma list keeps every row key of its "
          "identity reading byte-identical")

    # AC-PICBC4: a receiver no import binds still reads UNRESOLVED - the
    # comma table never invents a module for it.
    unbound_rows = rows(UNBOUND)
    unbound_root = world([("ghost.py", UNBOUND),
                          ("comma_pub.py", COMMA_WIRE)])
    report4, code4 = EPWI.audit(unbound_root)
    check([row["state"] for row in unbound_rows] == [EPWI.UNRESOLVED]
          and unbound_rows[0]["module"] == ""
          and unbound_rows[0]["receiver"] == "ghost"
          and report4["verdict"] == EPWI.UNRESOLVED and code4 == 2
          and report4["unresolved"] == ["ghost.py"]
          and report4["wire"] == ["comma_pub.py"],
          "AC-PICBC4 a receiver no import binds still reads UNRESOLVED")

    # AC-PICBC5: every pre-existing refusal code, exit code and printed line
    # of the identity CLI is unchanged, proved against the HEAD module's own
    # captured refusal (the module is edited on purpose this window, so the
    # comparison is behaviour, exactly as the criterion words it).
    head_source = subprocess.run(
        ["git", "-C", REPO, "show", "HEAD:src/os/export_publish_wire_identity.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    head_temp = tempfile.mkdtemp(prefix="picbc-refuse-")
    head_path = os.path.join(head_temp, "export_publish_wire_identity.py")
    with io.open(head_path, "wb") as handle:
        handle.write(head_source.stdout)
    missing = os.path.join(head_temp, "no-such-dir")
    head_missing_rc, _o, head_missing_err = run(
        [sys.executable, head_path, "--check", "--root", missing])
    now_missing_rc, _o2, now_missing_err = run(
        [sys.executable, IDENTITY, "--check", "--root", missing])
    head_flags_rc, _o3, head_flags_err = run(
        [sys.executable, head_path, "--check", "--nope"])
    now_flags_rc, _o4, now_flags_err = run(
        [sys.executable, IDENTITY, "--check", "--nope"])
    head_nocheck = run([sys.executable, head_path, "--root", missing])
    now_nocheck = run([sys.executable, IDENTITY, "--root", missing])
    shutil.rmtree(head_temp, ignore_errors=True)
    check(head_source.returncode == 0
          and head_missing_rc == 3 and now_missing_rc == 3
          and head_missing_err == now_missing_err
          and "E_EPWI_NO_ROOT" in now_missing_err
          and head_flags_rc == 5 and now_flags_rc == 5
          and head_flags_err == now_flags_err
          and head_nocheck[0] == 5 and now_nocheck[0] == 5
          and head_nocheck[2] == now_nocheck[2],
          "AC-PICBC5 the identity CLI refusal codes, exit codes and printed "
          "lines match the HEAD capture")

    # AC-PICBC6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    digest_before = hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
    whole_before = tree_digest(fixture)
    run([sys.executable, MODULE, "--check", "--root", fixture])
    run([sys.executable, MODULE, "--check", "--root", fixture, "--json"])
    PICBC.audit(fixture)
    recipes = read(RUNNER)
    forbidden = ("datetime", "time.time", "socket", "urllib", "requests",
                 "os.open", "io.open")
    rc_json, json_a, _e = run([sys.executable, MODULE, "--check",
                               "--root", fixture, "--json"])
    rc_again, json_b, _e2 = run([sys.executable, MODULE, "--check",
                                 "--root", fixture, "--json"])
    parsed = json.loads(json_a)
    check(tree_digest(fixture) == whole_before
          and hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
          == digest_before
          and all(name not in source for name in forbidden)
          and all(ord(char) < 128 for char in source)
          and WIRED_EXPECT in recipes
          and LABEL in recipes
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == PICBC.REPORT_KEYS
          and all(tuple(item.keys()) == PICBC.CALL_KEYS + ("path",)
                  for item in parsed["detail"]),
          "AC-PICBC6 writes nothing, no clock, ascii, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA, PASSES, FAILS),
          flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())