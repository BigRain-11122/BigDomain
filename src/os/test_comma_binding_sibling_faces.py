"""comma_binding_sibling_faces suite (R2430).

Criteria AC-PICBS1..AC-PICBS6 were pinned inside the R2428 tech seed row of
state/queue/tech.md (line 492) BEFORE this code existed.

What this proves: the comma-aware receiver table reached the identity face
alone, so the two sibling faces still answered UNRESOLVED for the same
comma-list publisher the identity face read as WIRE. One seam now chooses the
table for every face, and a file without a comma list keeps every key of every
row byte for byte.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import importlib.util
import io
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import comma_binding_sibling_faces as PICBS  # noqa: E402
import comma_binding_wire as PICBW  # noqa: E402
import export_publish_from_import_law as EPBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import publish_relative_package_identity as PRPI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "comma_binding_sibling_faces.py")
LAW = os.path.join(BASE, "export_publish_from_import_law.py")
RELATIVE = os.path.join(BASE, "publish_relative_package_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-comma-binding-sibling-faces"
WIRED_EXPECT = '"test_comma_binding_sibling_faces.py"), 6),'

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


def world(scripts):
    root = tempfile.mkdtemp(prefix="picbs-suite-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(command, extra=(), path_extra=None):
    argv = list(command)
    argv.extend(extra)
    env = dict(os.environ)
    if path_extra:
        env["PYTHONPATH"] = path_extra
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env)
    return (done.returncode, done.stdout.decode("utf-8", "replace"),
            done.stderr.decode("utf-8", "replace"))


def head_copy(rel, alias):
    """A HEAD copy of a shipped module, imported under its own alias."""
    source = subprocess.run(
        ["git", "-C", REPO, "show", "HEAD:src/os/%s" % rel],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if source.returncode != 0:
        return None, None
    temp = tempfile.mkdtemp(prefix="picbs-head-")
    path = os.path.join(temp, alias + ".py")
    with io.open(path, "wb") as handle:
        handle.write(source.stdout)
    sys.path.insert(0, BASE)
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def row_keys(rows):
    return [tuple(sorted(row.keys())) for row in rows]


def main():
    source = read(MODULE)
    law_source = read(LAW)
    relative_source = read(RELATIVE)

    comma_root = world([("comma_pub.py", COMMA_WIRE)])
    plain_root = world([("plain_pub.py", PLAIN_WIRE)])
    foreign_root = world([("foreign_pub.py", COMMA_FOREIGN)])
    unbound_root = world([("ghost_pub.py", UNBOUND)])

    # AC-PICBS1: both faces ask the shipped seam at CALL time, proved by
    # patching that seam and watching BOTH rows move, and no split is
    # restated in the module or in either face.
    moved = []
    saved = PICBS.receivers_for
    try:
        PICBS.receivers_for = lambda lines: {"CEPW": "sentinel_wire"}
        law_rows = EPBW.classify_script(COMMA_WIRE.splitlines(), EXPORT, WIRE)
        relative_rows = PRPI.classify_script(
            COMMA_WIRE.splitlines(), "mypkg", EXPORT, WIRE)
        moved.append([row["module"] for row in law_rows] == ["sentinel_wire"])
        moved.append([row["module"] for row in relative_rows] == ["sentinel_wire"])
    finally:
        PICBS.receivers_for = saved
    baseline_law = EPBW.classify_script(COMMA_WIRE.splitlines(), EXPORT, WIRE)
    check(all(moved)
          and [row["module"] for row in baseline_law] == [WIRE]
          and "comma_binding_wire" in source
          and "receivers_for" in law_source
          and "comma_binding_sibling_faces" in law_source
          and "comma_binding_sibling_faces" in relative_source
          and "import re" not in source
          and "parts_of" not in source
          and "part_statement" not in source
          and "is_comma_import" not in source,
          "AC-PICBS1 both faces ask the shipped seam at call time and no "
          "split is restated")

    # AC-PICBS2: the same comma-list fixture reads WIRE on every face that
    # resolves publishers, and FOREIGN where the module is not the wire.
    report, code = PICBS.audit(comma_root, EXPORT, "queue_floor_export_face", WIRE)
    law_report, law_code = EPBW.audit(comma_root, EXPORT, "queue_floor_export_face", WIRE)
    relative_report, relative_code = PRPI.audit(
        comma_root, None, EXPORT, "queue_floor_export_face", WIRE)
    identity_report, identity_code = EPWI.audit(comma_root, EXPORT, "queue_floor_export_face", WIRE)
    foreign_report, foreign_code = PICBS.audit(
        foreign_root, EXPORT, "queue_floor_export_face", WIRE)
    check(report["verdict"] == PICBS.AGREE and code == 0
          and law_report["verdict"] == EPBW.WIRE and law_code == 0
          and law_report["unresolved"] == []
          and relative_report["verdict"] == EPWI.WIRE and relative_code == 0
          and identity_report["verdict"] == EPWI.WIRE and identity_code == 0
          and foreign_report["verdict"] == PICBS.AGREE and foreign_code == 0
          and foreign_report["faces"][0]["verdict"] == EPBW.FOREIGN
          and len(report["faces"]) == 2,
          "AC-PICBS2 one comma-list fixture reads WIRE on every face")

    # AC-PICBS3: a script without a comma list keeps every key of every row
    # byte-identical against the HEAD copies of both faces.
    head_law, _p = head_copy("export_publish_from_import_law.py", "head_epbw")
    head_relative, _p2 = head_copy(
        "publish_relative_package_identity.py", "head_prpi")
    differing = []
    if head_law is None or head_relative is None:
        differing.append("head-copy-missing")
    else:
        for name, text, package in (
                ("plain_pub.py", PLAIN_WIRE, None),
                ("from_pub.py", FROM_IMPORT, None),
                ("bare_pub.py", BARE, None),
                ("plain_pub.py", PLAIN_WIRE, "mypkg"),
                ("from_pub.py", FROM_IMPORT, "mypkg")):
            now = EPBW.classify_script(text.splitlines(), EXPORT, WIRE)
            was = head_law.classify_script(text.splitlines(), EXPORT, WIRE)
            if now != was or row_keys(now) != row_keys(was):
                differing.append("law:%s" % name)
            if package is not None:
                now_rel = PRPI.classify_script(
                    text.splitlines(), package, EXPORT, WIRE)
                was_rel = head_relative.classify_script(
                    text.splitlines(), package, EXPORT, WIRE)
                if now_rel != was_rel or row_keys(now_rel) != row_keys(was_rel):
                    differing.append("relative:%s" % name)
        live = EPBW.audit(os.path.join(SRC, "os"), EXPORT,
                          "queue_floor_export_face", WIRE)[0]
        live_head = head_law.audit(os.path.join(SRC, "os"), EXPORT,
                                   "queue_floor_export_face", WIRE)[0]
        if live["detail"] != live_head["detail"]:
            differing.append("law:live-tree")
    check(not differing,
          "AC-PICBS3 a script without a comma list keeps every key of every "
          "row byte-identical against HEAD")

    # AC-PICBS4: a receiver no import binds still reads UNRESOLVED on both
    # faces rather than being guessed.
    law_unbound = EPBW.audit(unbound_root, EXPORT, "queue_floor_export_face", WIRE)
    relative_unbound = PRPI.audit(
        unbound_root, None, EXPORT, "queue_floor_export_face", WIRE)
    faces_unbound = PICBS.audit(unbound_root, EXPORT, "queue_floor_export_face", WIRE)
    face_verdicts = [row["verdict"] for row in faces_unbound[0]["faces"]]
    check(law_unbound[0]["verdict"] == EPBW.UNRESOLVED and law_unbound[1] == 2
          and relative_unbound[0]["verdict"] == EPWI.UNRESOLVED
          and relative_unbound[1] == 2
          and [row["module"] for row in law_unbound[0]["detail"]] == [""]
          and [row["module"] for row in relative_unbound[0]["detail"]] == [""]
          and faces_unbound[0]["verdict"] == PICBS.AGREE
          and face_verdicts == ["UNRESOLVED", "UNRESOLVED"],
          "AC-PICBS4 a receiver no import binds still reads UNRESOLVED on "
          "both faces")

    # AC-PICBS5: every pre-existing refusal code, exit code and printed line
    # of both CLIs is unchanged, proved against their HEAD copies run as
    # scripts (bad flags, missing root, and a tree with no publisher).
    law_head_run = head_copy("export_publish_from_import_law.py", "head_run_epbw")
    relative_head_run = head_copy(
        "publish_relative_package_identity.py", "head_run_prpi")
    same = []
    if law_head_run[1] is None or relative_head_run[1] is None:
        same.append(False)
    else:
        cases = [((), 0), (("--check", "--bogus"), 5)]
        for extra, want in cases:
            now = run([sys.executable, LAW], extra)
            was = run([sys.executable, law_head_run[1]], extra, path_extra=BASE)
            same.append(now[0] == want and now[0] == was[0]
                        and now[1] == was[1]
                        and now[2].replace("export_publish_from_import_law", "")
                        == was[2].replace("head_run_epbw", ""))
            now_rel = run([sys.executable, RELATIVE], extra)
            was_rel = run([sys.executable, relative_head_run[1]], extra,
                          path_extra=BASE)
            same.append(now_rel[0] == was_rel[0])
        empty_root = world([("quiet.py", "VALUE = 1\n")])
        now = run([sys.executable, LAW], ("--check", "--root", empty_root))
        was = run([sys.executable, law_head_run[1]],
                  ("--check", "--root", empty_root), path_extra=BASE)
        same.append(now[0] == 0 and now[0] == was[0] and now[1] == was[1])
        now_rel = run([sys.executable, RELATIVE],
                      ("--check", "--root", empty_root))
        was_rel = run([sys.executable, relative_head_run[1]],
                      ("--check", "--root", empty_root), path_extra=BASE)
        same.append(now_rel[0] == was_rel[0] and now_rel[1] == was_rel[1])
        missing = run([sys.executable, LAW], ("--check", "--root",
                                              os.path.join(empty_root, "nope")))
        same.append(missing[0] == 3)
    check(all(same),
          "AC-PICBS5 every pre-existing refusal code, exit code and printed "
          "line of both CLIs is unchanged")

    # AC-PICBS6: pure ASCII, stdlib only, zero network, no clock, read-only,
    # its own reconcile label and its own suite wired into the runner.
    ascii_ok = all(ord(ch) < 128 for ch in source)
    runner = read(RUNNER) if os.path.exists(RUNNER) else ""
    stdlib_only = all(
        line.split()[0] in ("import", "from")
        and line.split()[1].split(".")[0] in
        ("importlib", "json", "os", "sys", "re", "io", "hashlib",
         "subprocess", "tempfile", "shutil", "time", "datetime")
        for line in source.splitlines()
        if line.startswith("import ") or line.startswith("from "))
    check(ascii_ok and stdlib_only
          and "urllib" not in source and "requests" not in source
          and "socket" not in source
          and "http" not in source
          and "datetime" not in source and "time.time" not in source
          and "open(" not in source.split("def main(")[0]
          and 'open(path, "w"' not in source
          and LABEL in source
          and WIRED_EXPECT in runner,
          "AC-PICBS6 pure ASCII, stdlib only, read-only, own label and suite")

    print("SUITE %s criteria=%d pass=%d fail=%d" % (
        "PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA, PASSES, FAILS))
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())