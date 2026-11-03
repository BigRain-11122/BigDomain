"""comma_binding_wire suite (R2426).

Criteria AC-PICBW1..AC-PICBW6 were pinned inside the R2424 tech seed row of
state/queue/tech.md (line 490) BEFORE this code existed.

What this proves: the shipped receiver table matches a plain import with an
anchored single-module pattern, so on `import os, some_wire as wiremod` it
binds {"os": "os"} only, callee_of returns module "" for a call through
wiremod, and the identity reading reports UNRESOLVED for a publisher that a
plain alias would resolve. One wire now asks the SHIPPED splitter and the
SHIPPED composition for the parts and adds only what the table dropped.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
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

import comma_binding_wire as PICBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import plain_import_comma_binding as PICB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "comma_binding_wire.py")
IDENTITY = os.path.join(BASE, "export_publish_wire_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-comma-binding-wire"
WIRED_EXPECT = '"test_comma_binding_wire.py"), 6),'

CALL = "\n\ndef go():\n    return wiremod.publish(PATH, EXPORT)\n"

COMMA_ALIAS = "import os, some_wire as wiremod" + CALL
COMMA_FIRST = "import some_wire as wiremod, os" + CALL
COMMA_THREE = "import os, sys as sh, some.wire.mod as wiremod" + CALL
COMMA_NO_CALL = "import os, some_wire as wiremod\n\nNOTE = 1\n"
PLAIN_ALIAS = "import some_wire as wiremod" + CALL
UNBOUND = "\n\ndef go():\n    return ghost.publish(PATH, EXPORT)\n"

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
    root = tempfile.mkdtemp(prefix="picbw-suite-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def call_line(script):
    for number, line in enumerate(script.splitlines(), 1):
        if "publish(" in line:
            return number, line
    return 0, ""


def rows(script):
    return PICBW.script_rows(script.splitlines())


def main():
    source = read(MODULE)

    # AC-PICBW1: the split and the table are asked at CALL time through the
    # shipped modules and no import grammar is restated here.
    baseline = rows(COMMA_ALIAS)
    saved_split = PICB.parts_of
    saved_recv = EPWI.import_bindings
    patched = []
    try:
        PICB.parts_of = lambda line: [("zzz", "wiremod")]
        moved = rows(COMMA_ALIAS)
        patched.append(len(moved) == 1
                       and moved[0]["wire_module"] == "zzz"
                       and moved[0]["state"] == PICBW.BOUND)
        PICB.parts_of = saved_split

        EPWI.import_bindings = lambda lines: {"wiremod": "sentinel"}
        moved = rows(COMMA_ALIAS)
        patched.append(len(moved) == 1
                       and moved[0]["wire_module"] == "sentinel"
                       and moved[0]["table_module"] == "sentinel")
        EPWI.import_bindings = saved_recv
    finally:
        PICB.parts_of = saved_split
        EPWI.import_bindings = saved_recv
    check(all(patched)
          and rows(COMMA_ALIAS) == baseline
          and "import re" not in source
          and "re.compile" not in source
          and "parts_of" in source
          and "part_statement" in source
          and "import_bindings" in source
          and "callee_of" in source,
          "AC-PICBW1 the split and the receiver table are asked at call time "
          "and no import pattern is restated")

    # AC-PICBW2: callee_of reads the real module for a comma-list publisher
    # instead of module '', and the audit/CLI name it as BOUND.
    number, line = call_line(COMMA_ALIAS)
    code = EPWI.code_only(COMMA_ALIAS.splitlines())
    table_receiver, table_module = EPWI.callee_of(
        line, EPWI.import_bindings(code))
    wire = PICBW.resolve(line, PICBW.bindings(code), EPWI.import_bindings(code))
    root = world([("comma_pub.py", COMMA_ALIAS)])
    report, code_rc = PICBW.audit(root)
    rc, out, _ = run(root)
    first = rows(COMMA_FIRST)
    three = rows(COMMA_THREE)
    check(table_receiver == "wiremod" and table_module == ""
          and wire["module"] == "some_wire" and wire["state"] == PICBW.BOUND
          and len(baseline) == 1 and baseline[0]["table_module"] == ""
          and baseline[0]["wire_module"] == "some_wire"
          and baseline[0]["receiver"] == "wiremod"
          and code_rc == 0 and report["verdict"] == PICBW.RESOLVED
          and report["resolved_lines"] == 1 and report["unresolved_lines"] == 0
          and report["comma_files"] == 1 and report["comma_lines"] == 1
          and report["detail"][0]["path"] == "comma_pub.py"
          and rc == 0
          and "wire_module=some_wire" in out
          and "table_module=(unbound)" in out
          and len(first) == 1 and first[0]["wire_module"] == "some_wire"
          and len(three) == 1 and three[0]["wire_module"] == "some.wire.mod",
          "AC-PICBW2 a comma-list publisher reads its real module from "
          "callee_of instead of module ''")

    # AC-PICBW3: a statement with no comma still resolves exactly as today -
    # proved on a fixture AND on every real file that carries no comma list,
    # by comparing the two tables' answers for the same lines.
    plain_code = EPWI.code_only(PLAIN_ALIAS.splitlines())
    plain_number, plain_line = call_line(PLAIN_ALIAS)
    same = (PICBW.bindings(plain_code) == EPWI.import_bindings(plain_code)
            and PICBW.resolve(plain_line, PICBW.bindings(plain_code))
            == {"receiver": "wiremod", "module": "some_wire",
                "table_module": "", "state": PICBW.BOUND}
            and PICBW.resolve(plain_line, PICBW.bindings(plain_code),
                              EPWI.import_bindings(plain_code))["table_module"]
            == "some_wire")
    live_root = os.path.join(SRC, "os")
    mismatch = []
    live_compared = 0
    for path in PICBW.guard().scan_scripts(live_root):
        name = os.path.basename(path)
        if name in (PICBW.SELF_NAME, PICBW.SELF_TEST_NAME):
            continue
        try:
            lines = PICBW.guard().read_lines(path)
        except (IOError, OSError):
            continue
        live_code = EPWI.code_only(lines)
        if any(PICBW.comma_parts(line) for line in live_code):
            continue
        live_compared += 1
        if PICBW.bindings(live_code) != EPWI.import_bindings(live_code):
            mismatch.append(os.path.basename(path))
    live_report, _live_rc = PICBW.audit(live_root)
    check(same and not mismatch and live_compared > 900
          and live_report["parity_files"] == live_compared
          and live_report["parity_files"] + live_report["comma_files"]
          == live_report["files_compared"],
          "AC-PICBW3 a statement with no comma resolves exactly as today on "
          "every non-comma line")

    # AC-PICBW4: a receiver no import binds still reads UNRESOLVED - it is
    # never guessed from a neighbour, a sibling file or another module name.
    number, line = call_line(UNBOUND)
    unbound_code = EPWI.code_only(UNBOUND.splitlines())
    unbound = PICBW.resolve(line, PICBW.bindings(unbound_code))
    root = world([("ghost.py", UNBOUND),
                  ("bound.py", PLAIN_ALIAS),
                  ("comma.py", COMMA_ALIAS)])
    report, code_rc = PICBW.audit(root)
    check(unbound["module"] == "" and unbound["state"] == PICBW.UNRESOLVED
          and unbound["receiver"] == "ghost"
          and report["verdict"] == PICBW.RESOLVED
          and report["resolved_lines"] == 1
          and report["unresolved_lines"] == 0
          and report["comma_files"] == 1,
          "AC-PICBW4 a receiver no import binds still reads UNRESOLVED")

    # AC-PICBW5: the identity module is UNTOUCHED and its own refusals are
    # byte-identical to the HEAD copy's, captured by running both scripts.
    head_source = subprocess.run(
        ["git", "-C", REPO, "show", "HEAD:src/os/export_publish_wire_identity.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    head_temp = tempfile.mkdtemp(prefix="picbw-head-")
    head_path = os.path.join(head_temp, "export_publish_wire_identity.py")
    with io.open(head_path, "wb") as handle:
        handle.write(head_source.stdout)
    missing = os.path.join(head_temp, "no-such-dir")
    head_missing = subprocess.run(
        [sys.executable, head_path, "--check", "--root", missing],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    now_missing = subprocess.run(
        [sys.executable, IDENTITY, "--check", "--root", missing],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    head_flags = subprocess.run(
        [sys.executable, head_path, "--check", "--nope"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    now_flags = subprocess.run(
        [sys.executable, IDENTITY, "--check", "--nope"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    shutil.rmtree(head_temp, ignore_errors=True)
    check(head_source.returncode == 0
          and head_source.stdout == io.open(IDENTITY, "rb").read()
          and head_missing.returncode == 3 and now_missing.returncode == 3
          and head_missing.stderr == now_missing.stderr
          and "E_EPWI_NO_ROOT" in now_missing.stderr.decode("utf-8", "replace")
          and head_flags.returncode == 5 and now_flags.returncode == 5
          and head_flags.stderr == now_flags.stderr,
          "AC-PICBW5 the identity module is untouched and its refusal codes, "
          "exit codes and printed lines match the HEAD capture")

    # AC-PICBW6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    digest_before = hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
    whole_before = tree_digest(root)
    run(root, ("--json",))
    PICBW.audit(root)
    recipes = read(RUNNER)
    forbidden = ("datetime", "time.time", "socket", "urllib", "requests",
                 "os.open", "io.open")
    rc_json, json_a, _ = run(root, ("--json",))
    rc_again, json_b, _ = run(root, ("--json",))
    parsed = json.loads(json_a)
    check(tree_digest(root) == whole_before
          and hashlib.sha256(read(MODULE).encode("utf-8")).hexdigest()
          == digest_before
          and all(name not in source for name in forbidden)
          and all(ord(char) < 128 for char in source)
          and WIRED_EXPECT in recipes
          and LABEL in recipes
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == PICBW.REPORT_KEYS
          and all(tuple(item.keys()) == PICBW.CALL_KEYS + ("path",)
                  for item in parsed["detail"]),
          "AC-PICBW6 writes nothing, ASCII, stdlib only, wired")

    print("SUITE %s criteria=%d passes=%d fails=%d"
          % ("PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA,
             PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())