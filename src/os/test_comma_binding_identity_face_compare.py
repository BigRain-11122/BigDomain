"""comma_binding_identity_face_compare suite (R2444).

Criteria AC-PICIC1..AC-PICIC6 were pinned in the R2430 tech seed row of
state/queue/tech.md:510 BEFORE this code existed.

What this proves: comma_binding_sibling_faces (R2430) compared two faces and
comma_binding_consumer_wire (R2428) served the third, through a different
seam, so a regression on the identity path could move that verdict while both
sibling faces kept agreeing. The shipped module asks all three shipped faces
over one tree, measures which seam supplied each face's receiver table by
wrapping both seam providers for the duration of that face's own audit, and
publishes every disagreement with the face and the seam behind it.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import importlib
import io
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import comma_binding_identity_face_compare as PICIC  # noqa: E402
import comma_binding_sibling_faces as PICBS  # noqa: E402
import export_publish_from_import_law as EPBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import publish_relative_package_identity as PRPI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "comma_binding_identity_face_compare.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-comma-binding-identity-face-compare"
WIRED_EXPECT = '"test_comma_binding_identity_face_compare.py"), 6),'

EXPORT = "status-export.json"
WIRE = "closeout_export_parity_wire"
OWNER = "queue_floor_export_face"
OWNER_LINE = "from queue_floor_export_face import EXPORT"
CALL = "\n\ndef go():\n    return CEPW.publish(PATH, EXPORT)\n"

COMMA_WIRE = ("import os, closeout_export_parity_wire as CEPW\n"
              + OWNER_LINE + "\n" + CALL)
COMMA_FOREIGN = ("import os, some_other_wire as CEPW\n"
                 + OWNER_LINE + "\n" + CALL)
PLAIN_WIRE = ("import closeout_export_parity_wire as CEPW\n"
              + OWNER_LINE + "\n" + CALL)
UNBOUND = ("import os\n" + OWNER_LINE
           + "\n\ndef go():\n    return ghost.publish(PATH, EXPORT)\n")

STDLIB_OK = ("importlib", "json", "os", "sys")

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
    return ok


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
    root = tempfile.mkdtemp(prefix="picic-suite-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def cli(args):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    done = subprocess.run([sys.executable, MODULE] + args, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env)
    return (done.returncode, done.stdout.decode("utf-8", "replace"),
            done.stderr.decode("utf-8", "replace"))


def face_of(report, name):
    for row in report["faces"]:
        if row["face"] == name:
            return row
    raise SystemExit("FAIL setup: face %s missing" % name)


def ac_picic1(source):
    """All three faces are asked at CALL time and no table is restated."""
    seen = []
    law = importlib.import_module("export_publish_from_import_law")
    relative = importlib.import_module("publish_relative_package_identity")
    identity = importlib.import_module("export_publish_wire_identity")

    def stub(name):
        def call(*args, **kwargs):
            seen.append(name)
            return ({"label": "stub-" + name, "verdict": "WIRE",
                     "publishers": ["stub.py"], "wire": ["stub.py"],
                     "foreign": [], "unresolved": [], "no_publish": [],
                     "detail": []}, 0)
        return call

    saved = (law.audit, relative.audit, identity.audit)
    law.audit = stub("from-import")
    relative.audit = stub("relative")
    identity.audit = stub("identity")
    try:
        report, code = PICIC.audit(tempfile.gettempdir(), EXPORT, OWNER, WIRE)
    finally:
        law.audit, relative.audit, identity.audit = saved
    ok = check(sorted(seen) == ["from-import", "identity", "relative"]
               and code == 0
               and [row["label"] for row in report["faces"]]
               == ["stub-from-import", "stub-relative", "stub-identity"]
               and len(report["faces"]) == 3,
               "AC-PICIC1 all three faces are asked at call time")
    ok = check("comma_binding_wire" not in source
               and "def bindings" not in source
               and "FROM_PLAIN_RE" not in source
               and "import re" not in source,
               "AC-PICIC1 no receiver table or import grammar is restated") and ok
    return ok


def ac_picic2(comma_root, foreign_root):
    """One comma-list fixture reads WIRE on all three faces, and a face that
    differs is NAMED with its verdict and its seam."""
    report, code = PICIC.audit(comma_root, EXPORT, OWNER, WIRE)
    verdicts = [row["verdict"] for row in report["faces"]]
    ok = check(verdicts == ["WIRE", "WIRE", "WIRE"] and code == 0
               and report["verdict"] == PICIC.AGREE
               and report["differences"] == [],
               "AC-PICIC2 one comma-list fixture reads WIRE on all three faces")
    identity = importlib.import_module("export_publish_wire_identity")
    original = identity.audit

    def drifted(*args, **kwargs):
        return ({"label": "os-export-publish-wire-identity",
                 "verdict": "FOREIGN", "publishers": ["comma_pub.py"],
                 "wire": [], "foreign": ["comma_pub.py"], "unresolved": [],
                 "no_publish": [], "detail": []}, 2)

    identity.audit = drifted
    try:
        split, split_code = PICIC.audit(comma_root, EXPORT, OWNER, WIRE)
    finally:
        identity.audit = original
    named = [row["face"] for row in split["differences"]
             if row["kind"] == "verdict"]
    ok = check(split["verdict"] == PICIC.SPLIT and split_code == 2
               and named == ["identity"]
               and [row["face"] for row in split["split"]] == ["identity"],
               "AC-PICIC2 a differing face is named instead of inferred") and ok
    foreign, foreign_code = PICIC.audit(foreign_root, EXPORT, OWNER, WIRE)
    ok = check(foreign["verdict"] == PICIC.AGREE and foreign_code == 0
               and [row["verdict"] for row in foreign["faces"]]
               == ["FOREIGN", "FOREIGN", "FOREIGN"],
               "AC-PICIC2 the foreign fixture still reads FOREIGN everywhere") and ok
    return ok


def ac_picic3(plain_root):
    """A script with no comma list keeps every key of every row byte-identical
    on all three faces against the shipped faces' own readings."""
    report, code = PICIC.audit(plain_root, EXPORT, OWNER, WIRE)
    asked = (
        ("from-import", EPBW.audit(plain_root, EXPORT, OWNER, WIRE)[0]),
        ("relative", PRPI.audit(plain_root, None, EXPORT, OWNER, WIRE)[0]),
        ("identity", EPWI.audit(plain_root, EXPORT, OWNER, WIRE)[0]),
    )
    differing = []
    for name, own in asked:
        row = face_of(report, name)
        if row["rows"] != (own.get("detail") or []):
            differing.append("%s:rows" % name)
        if row["publishers"] != sorted(own.get("publishers") or []):
            differing.append("%s:publishers" % name)
        if row["verdict"] != own.get("verdict"):
            differing.append("%s:verdict" % name)
        mine = [tuple(sorted(item.keys())) for item in row["rows"]]
        theirs = [tuple(sorted(item.keys()))
                  for item in (own.get("detail") or [])]
        if mine != theirs:
            differing.append("%s:keys" % name)
    identity_keys = sorted(face_of(report, "identity")["rows"][0].keys())
    ok = check(code == 0 and report["verdict"] == PICIC.AGREE
               and not differing
               and identity_keys == ["line", "module", "path", "receiver",
                                    "state", "text"],
               "AC-PICIC3 a no-comma script keeps every key of every row on "
               "all three faces")
    return ok


def ac_picic4(unbound_root):
    """A receiver no import binds still reads UNRESOLVED on all three faces."""
    report, code = PICIC.audit(unbound_root, EXPORT, OWNER, WIRE)
    verdicts = [row["verdict"] for row in report["faces"]]
    modules = [item["module"] for row in report["faces"]
               for item in row["rows"]]
    ok = check(verdicts == ["UNRESOLVED", "UNRESOLVED", "UNRESOLVED"]
               and code == 0 and modules == ["", "", ""]
               and report["verdict"] == PICIC.AGREE,
               "AC-PICIC4 a receiver no import binds reads UNRESOLVED "
               "everywhere rather than being guessed")
    return ok


def ac_picic5(comma_root):
    """Each face row records the seam that actually supplied its table, and
    moving a seam moves that face's rows."""
    report, code = PICIC.audit(comma_root, EXPORT, OWNER, WIRE)
    law_face = face_of(report, "from-import")
    relative_face = face_of(report, "relative")
    identity_face = face_of(report, "identity")
    law_seams = [row["seam"] for row in law_face["seams"]]
    identity_seams = [row["seam"] for row in identity_face["seams"]]
    ok = check(code == 0
               and law_seams == [PICIC.SEAM_SIBLING]
               and [row["seam"] for row in relative_face["seams"]]
               == [PICIC.SEAM_SIBLING]
               and PICIC.SEAM_IDENTITY in identity_seams
               and all(row["calls"] > 0 for row in identity_face["seams"]),
               "AC-PICIC5 each face row records the seam that supplied it")

    consumer = importlib.import_module("comma_binding_consumer_wire")
    original = consumer.wire_audit_script

    def sentinel(lines, export_name=EXPORT, wire_module=WIRE):
        return [{"line": 1, "receiver": "CEPW", "module": "sentinel_wire",
                 "state": "WIRE", "text": "sentinel"}]

    consumer.wire_audit_script = sentinel
    try:
        drifted, _rc = PICIC.audit(comma_root, EXPORT, OWNER, WIRE)
    finally:
        consumer.wire_audit_script = original
    moved = [item["module"] for item in face_of(drifted, "identity")["rows"]]
    held = [item["module"] for item in face_of(drifted, "from-import")["rows"]]
    ok = check(moved == ["sentinel_wire"] and held == [WIRE],
               "AC-PICIC5 the recorded seam is the seam that fires") and ok
    return ok


def ac_picic6(source):
    """Pure ASCII, stdlib only, zero network, no clock, read-only, own label
    and own suite wired into the runner."""
    ok = check(all(ord(char) < 128 for char in source),
               "AC-PICIC6 source is pure ASCII")
    imports = sorted(line.split()[1].split(".")[0]
                     for line in source.splitlines()
                     if line.startswith("import "))
    ok = check(imports == sorted(STDLIB_OK),
               "AC-PICIC6 stdlib only, no network, no clock") and ok
    ok = check("open(" not in source and "os.replace" not in source
               and "import time" not in source and "time.time" not in source
               and "socket" not in source and "urllib" not in source,
               "AC-PICIC6 the module writes nothing and reads no clock") and ok
    ok = check(PICIC.LABEL == LABEL and "LABEL" in source,
               "AC-PICIC6 own reconcile label") and ok
    runner = read(RUNNER)
    ok = check(WIRED_EXPECT in runner,
               "AC-PICIC6 own suite is wired into the reconcile runner") and ok
    return ok


def main():
    source = read(MODULE)
    comma_root = world([("comma_pub.py", COMMA_WIRE)])
    plain_root = world([("plain_pub.py", PLAIN_WIRE)])
    foreign_root = world([("foreign_pub.py", COMMA_FOREIGN)])
    unbound_root = world([("ghost_pub.py", UNBOUND)])

    results = [
        ("AC-PICIC1", ac_picic1(source)),
        ("AC-PICIC2", ac_picic2(comma_root, foreign_root)),
        ("AC-PICIC3", ac_picic3(plain_root)),
        ("AC-PICIC4", ac_picic4(unbound_root)),
        ("AC-PICIC5", ac_picic5(comma_root)),
        ("AC-PICIC6", ac_picic6(source)),
    ]
    red = [name for name, good in results if not good]
    print("SUITE %s %d/%d criteria" % (
        "PASS" if not red and FAILS == 0 else "FAIL",
        len(results) - len(red), len(results)), flush=True)
    if not red and FAILS == 0:
        return 0
    print("FAILING %s" % ",".join(red), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())