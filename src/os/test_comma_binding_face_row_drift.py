"""comma_binding_face_row_drift suite (R2446).

Criteria AC-PFRD1..AC-PFRD6 were pinned in the R2444 tech seed row of
state/queue/tech.md:512 BEFORE this code existed.

What this proves: comma_binding_identity_face_compare (R2444) compares each
face's VERDICT and publisher SET, so a per-line disagreement under an agreeing
verdict is invisible - MEASURED at R2444, one identity detail row rewritten
from closeout_export_parity_wire to drifted_wire keeps verdict=FACES-AGREE
rc=0 differences=0. The shipped module compares the values the faces DO share
on every (path, line) a face publishes, names a disagreement with the file,
the line, the key and every face's own module/label/seam, and reports a face
that publishes nothing on a line the others publish as SILENT.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import importlib
import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import comma_binding_face_row_drift as PFRD  # noqa: E402
import comma_binding_identity_face_compare as PICIC  # noqa: E402
import export_publish_from_import_law as EPBW  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402
import publish_relative_package_identity as PRPI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "comma_binding_face_row_drift.py")
PARENT_MODULE = os.path.join(BASE, "comma_binding_identity_face_compare.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-comma-binding-face-row-drift"
WIRED_EXPECT = '"test_comma_binding_face_row_drift.py"), 6),'

EXPORT = "status-export.json"
WIRE = "closeout_export_parity_wire"
OWNER = "queue_floor_export_face"
OWNER_LINE = "from queue_floor_export_face import EXPORT"
CALL = "\n\ndef go():\n    return CEPW.publish(PATH, EXPORT)\n"

PLAIN_WIRE = ("import closeout_export_parity_wire as CEPW\n"
              + OWNER_LINE + "\n" + CALL)

STDLIB_OK = ("importlib", "io", "json", "os", "sys")

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
    root = tempfile.mkdtemp(prefix="pfrd-suite-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(module, args):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    done = subprocess.run([sys.executable, module] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env)
    return (done.returncode, done.stdout.decode("utf-8", "replace"),
            done.stderr.decode("utf-8", "replace"))


def patch(target, name, value):
    """Swap one callable and hand back a restore callback."""
    saved = getattr(target, name)
    setattr(target, name, value)

    def restore():
        setattr(target, name, saved)
    return restore


def ac_pfrd1(root, source):
    """The compared keys are the published rows' own intersection, never a
    fixed list."""
    report, code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    faces = report["parent"]["faces"]
    published = None
    for face in faces:
        for row in face["rows"]:
            keys = set(row.keys())
            published = keys if published is None else (published & keys)
    expected = sorted(published - set(PFRD.JOIN_KEYS))
    ok = check(code == 0
               and list(report["compared_keys"]) == expected
               and expected == ["module", "receiver", "state", "text"],
               "AC-PFRD1 the compared keys are the rows' own intersection")

    real = EPWI.audit(root, EXPORT, OWNER, WIRE)[0]
    trimmed = [dict(row) for row in real["detail"]]
    for row in trimmed:
        row.pop("receiver", None)

    def without_receiver(*args, **kwargs):
        copy = dict(real)
        copy["detail"] = trimmed
        return copy, 0

    restore = patch(EPWI, "audit", without_receiver)
    try:
        moved, moved_code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    ok = check(moved_code == 0
               and "receiver" not in moved["compared_keys"]
               and "module" in moved["compared_keys"],
               "AC-PFRD1 dropping a published key narrows the comparison "
               "instead of a fixed list") and ok
    literal = ('"module", "receiver", "state", "text"')
    ok = check(literal not in source
               and '("module", "state"' not in source,
               "AC-PFRD1 no fixed compared-key list in the source") and ok
    return ok


def ac_pfrd2(root):
    """The exact probe measured at R2444 reads ROWS-SPLIT naming the line and
    both modules."""
    real = EPWI.audit(root, EXPORT, OWNER, WIRE)[0]
    detail = [dict(row) for row in real["detail"]]
    original = detail[0]["module"]
    detail[0]["module"] = "drifted_wire"

    def drifted(*args, **kwargs):
        copy = dict(real)
        copy["detail"] = detail
        return copy, 0

    restore = patch(EPWI, "audit", drifted)
    try:
        parent, parent_code = PICIC.audit(root, EXPORT, OWNER, WIRE)
        report, code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    measured = check(parent["verdict"] == PICIC.AGREE and parent_code == 0
                     and parent["differences"] == [],
                     "AC-PFRD2 the probe keeps verdict=FACES-AGREE with no "
                     "difference at the verdict level")
    splits = [row for row in report["splits"] if row["key"] == "module"]
    modules = sorted(set(item["module"] for row in splits
                         for item in row["faces"]))
    ok = check(measured and code == 2 and report["verdict"] == PFRD.SPLIT
               and len(splits) == 1
               and splits[0]["line"] == detail[0]["line"]
               and modules == sorted([original, "drifted_wire"]),
               "AC-PFRD2 a rewritten module under an unchanged verdict reads "
               "ROWS-SPLIT naming the line and both modules")
    return ok


def ac_pfrd3(root):
    """Rows that agree keep today's FACES-AGREE report byte for byte."""
    report, code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    parent, parent_code = PICIC.audit(root, EXPORT, OWNER, WIRE)
    same_object = (json.dumps(report["parent"], ensure_ascii=False)
                   == json.dumps(parent, ensure_ascii=False))
    ours = run(MODULE, ["--check", "--root", root])
    theirs = run(PARENT_MODULE, ["--check", "--root", root])
    ok = check(code == 0 and report["verdict"] == PFRD.AGREE
               and report["splits"] == [] and report["silent"] == []
               and same_object and parent_code == 0,
               "AC-PFRD3 agreeing rows keep the shipped report unchanged")
    ok = check(ours[0] == 0 and ours[1] == theirs[1] and theirs[1].strip(),
               "AC-PFRD3 agreeing rows print the shipped text byte for byte") and ok
    return ok


def ac_pfrd4(root):
    """A face publishing nothing on a line the others publish reads SILENT
    naming that face rather than agreeing."""
    real = EPWI.audit(root, EXPORT, OWNER, WIRE)[0]

    def muted(*args, **kwargs):
        copy = dict(real)
        copy["detail"] = []
        return copy, 0

    restore = patch(EPWI, "audit", muted)
    try:
        parent, _parent_code = PICIC.audit(root, EXPORT, OWNER, WIRE)
        report, code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    measured = check(parent["verdict"] == PICIC.AGREE
                     and parent["differences"] == [],
                     "AC-PFRD4 the muted face still agrees at the verdict level")
    named = sorted(set(row["face"] for row in report["silent"]))
    ok = check(measured and code == 2
               and report["verdict"] == PFRD.SILENT
               and named == ["identity"]
               and all(row["published_by"] == ["from-import", "relative"]
                       for row in report["silent"]),
               "AC-PFRD4 a silent face is named instead of counted as "
               "agreement")
    return ok


def ac_pfrd5(root):
    """Every row-split row records the face label and the seam that supplied
    it.

    The from-import face is the one drifted here ON PURPOSE: the other two
    run for real, so the carrier rows still carry the seams that actually
    fired and the criterion can prove the seam travels with the row.
    """
    real = EPBW.audit(root, EXPORT, OWNER, WIRE)[0]
    detail = [dict(row) for row in real["detail"]]
    detail[0]["state"] = "FOREIGN"

    def drifted(*args, **kwargs):
        copy = dict(real)
        copy["detail"] = detail
        return copy, 0

    restore = patch(EPBW, "audit", drifted)
    try:
        report, code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    splits = [row for row in report["splits"] if row["key"] == "state"]
    carriers = splits[0]["faces"] if splits else []
    identity = [item for item in carriers if item["face"] == "identity"]
    expected = ("face", "label", "module", "seams", "value")
    ok = check(code == 2 and len(splits) == 1
               and tuple(sorted(splits[0].keys())) == tuple(sorted(PFRD.SPLIT_KEYS))
               and all(tuple(sorted(row.keys())) == expected
                       for row in carriers)
               and len(carriers) == 3,
               "AC-PFRD5 every carrier row carries the pinned split keys")
    ok = check(bool(identity)
               and identity[0]["label"] == "os-export-publish-wire-identity"
               and any(row["seam"] == PICIC.SEAM_IDENTITY
                       and row["calls"] > 0
                       for row in identity[0]["seams"]),
               "AC-PFRD5 the identity carrier records its own label and the "
               "seam that fired") and ok
    return ok


def ac_pfrd6(source):
    """Pure ASCII, stdlib only, zero network, no clock, read-only, own label
    and own suite wired into the runner."""
    ok = check(all(ord(char) < 128 for char in source),
               "AC-PFRD6 source is pure ASCII")
    imports = sorted(line.split()[1].split(".")[0]
                     for line in source.splitlines()
                     if line.startswith("import "))
    ok = check(imports == sorted(STDLIB_OK),
               "AC-PFRD6 stdlib only, no network, no clock") and ok
    ok = check("open(" not in source and "os.replace" not in source
               and "import time" not in source and "time.time" not in source
               and "socket" not in source and "urllib" not in source,
               "AC-PFRD6 the module writes nothing and reads no clock") and ok
    ok = check(PFRD.LABEL == LABEL and "LABEL" in source,
               "AC-PFRD6 own reconcile label") and ok
    runner = read(RUNNER)
    ok = check(WIRED_EXPECT in runner,
               "AC-PFRD6 own suite is wired into the reconcile runner") and ok
    return ok


def main():
    source = read(MODULE)
    root = world([("plain_pub.py", PLAIN_WIRE)])

    results = [
        ("AC-PFRD1", ac_pfrd1(root, source)),
        ("AC-PFRD2", ac_pfrd2(root)),
        ("AC-PFRD3", ac_pfrd3(root)),
        ("AC-PFRD4", ac_pfrd4(root)),
        ("AC-PFRD5", ac_pfrd5(root)),
        ("AC-PFRD6", ac_pfrd6(source)),
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