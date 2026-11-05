"""row_key_carrier_scope suite (R2486).

Criteria AC-PFKC1..AC-PFKC6 were pinned in the R2446 tech seed row of
state/queue/tech.md:522 BEFORE this code existed.

What this proves: comma_binding_face_row_drift (R2446) compares only the keys
EVERY publisher face carries, and MEASURED at R2446 the intersection of the
6/7/8 row shapes is module/receiver/state/text - so `kind` (from-import and
relative, 22 rows over 11 files) and `relative` (relative only, 11 rows) are
dropped in silence. The shipped module reads every published key across the
faces that actually carry it, names a disagreement between carriers as
ROWS-SPLIT including a two-of-three key the intersection never compared, and
reports a one-of-three key as SINGLE-FACE with its carrier count.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

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
import row_key_carrier_scope as PFKC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "row_key_carrier_scope.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-row-key-carrier-scope"
WIRED_EXPECT = '"test_row_key_carrier_scope.py"), 6),'

EXPORT = "status-export.json"
WIRE = "closeout_export_parity_wire"
OWNER = "queue_floor_export_face"
OWNER_LINE = "from queue_floor_export_face import EXPORT"
CALL = "\n\ndef go():\n    return CEPW.publish(PATH, EXPORT)\n"

PLAIN_WIRE = ("import closeout_export_parity_wire as CEPW\n"
              + OWNER_LINE + "\n" + CALL)

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
    root = tempfile.mkdtemp(prefix="pfkc-suite-")
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


def drifted_kind(root):
    """The R2446 probe: one from-import `kind` rewritten, verdict unchanged."""
    real = EPBW.audit(root, EXPORT, OWNER, WIRE)[0]
    detail = [dict(row) for row in real["detail"]]
    original = detail[0]["kind"]
    detail[0]["kind"] = "drifted_kind"

    def drifted(*args, **kwargs):
        copy = dict(real)
        copy["detail"] = detail
        return copy, 0

    return patch(EPBW, "audit", drifted), detail[0], original


def ac_pfkc1(root, source):
    """The carriers of a key are the faces that actually publish it."""
    report, code = PFKC.audit(root, EXPORT, OWNER, WIRE)
    faces = report["row_drift"]["parent"]["faces"]
    derived = {}
    for face in faces:
        for row in face["rows"]:
            for name in row.keys():
                if name in PFKC.JOIN_KEYS:
                    continue
                derived.setdefault(name, set()).add(face["face"])
    expected = dict((name, sorted(names)) for name, names in derived.items())
    ok = check(code == 0
               and dict((name, list(names))
                        for name, names in
                        PFKC.carriers_of(faces).items()) == expected
               and expected.get("kind") == ["from-import", "relative"]
               and expected.get("relative") == ["relative"],
               "AC-PFKC1 a key's carriers are the faces that publish it")

    real = EPWI.audit(root, EXPORT, OWNER, WIRE)[0]
    trimmed = [dict(row) for row in real["detail"]]
    for row in trimmed:
        row.pop("text", None)

    def without_text(*args, **kwargs):
        copy = dict(real)
        copy["detail"] = trimmed
        return copy, 0

    restore = patch(EPWI, "audit", without_text)
    try:
        moved, moved_code = PFKC.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    ok = check(moved_code == 0
               and moved["carrier_counts"].get("text") == 2
               and moved["carrier_counts"].get("state") == 3,
               "AC-PFKC1 dropping a key from one face narrows its own "
               "carrier set instead of a fixed list") and ok
    literal = ('"module", "receiver", "state", "text"')
    ok = check(literal not in source
               and '("module", "receiver"' not in source,
               "AC-PFKC1 no fixed key list in the source") and ok
    return ok


def ac_pfkc2(root):
    """A two-of-three key disagreement reads ROWS-SPLIT naming the key and
    both carrying faces, where the R2446 reading stays FACES-AGREE."""
    restore, row, original = drifted_kind(root)
    try:
        drift, drift_code = PFRD.audit(root, EXPORT, OWNER, WIRE)
        report, code = PFKC.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    latched = check(drift["verdict"] == PFRD.AGREE and drift_code == 0
                    and drift["splits"] == [],
                    "AC-PFKC2 the probe is invisible to the R2446 intersection "
                    "reading")
    splits = [item for item in report["splits"] if item["key"] == "kind"]
    ok = check(latched and code == 2 and report["verdict"] == PFKC.SPLIT
               and len(splits) == 1
               and splits[0]["line"] == row["line"]
               and sorted(item["face"] for item in splits[0]["faces"])
               == ["from-import", "relative"]
               and any("drifted_kind" in item["value"]
                       for item in splits[0]["faces"]),
               "AC-PFKC2 a two-of-three key disagreement reads ROWS-SPLIT "
               "naming the key and both carriers")
    ok = check(report["carrier_counts"].get("kind") == 2,
               "AC-PFKC2 the split key keeps its carrier count") and ok
    return ok


def ac_pfkc3(root):
    """A key only one face publishes reads SINGLE-FACE, never a split."""
    report, code = PFKC.audit(root, EXPORT, OWNER, WIRE)
    singles = dict((row["key"], row) for row in report["single_face"])
    ok = check(code == 0 and report["verdict"] == PFKC.AGREE
               and "relative" in singles
               and singles["relative"]["carriers"] == 1
               and singles["relative"]["faces"] == ["relative"],
               "AC-PFKC3 a one-of-three key is reported SINGLE-FACE with its "
               "carrier count")
    ok = check(all(item["key"] != "relative" for item in report["splits"]),
               "AC-PFKC3 a single-face key is never invented as a split") and ok
    ok = check(all(row["scope"] == PFKC.SUBSET for row in report["single_face"])
               and report["keys_all"] == ["module", "receiver", "state", "text"]
               and report["keys_subset"] == ["kind", "relative"],
               "AC-PFKC3 the scope rows separate all-face keys from a subset") \
        and ok
    return ok


def ac_pfkc4(root):
    """Every key's carrier count is published, and all-face keys keep the
    R2446 reading byte for byte - on a clean tree and on the drifted probe."""
    report, code = PFKC.audit(root, EXPORT, OWNER, WIRE)
    drift, _drift_code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    truth = dict((row["key"], row["carriers"]) for row in report["scopes"])
    ok = check(code == 0 and report["carrier_counts"] == truth
               and sorted(truth) == ["kind", "module", "receiver", "relative",
                                    "state", "text"],
               "AC-PFKC4 every published key carries its carrier count")
    ok = check(json.dumps(report["row_drift"], ensure_ascii=False)
               == json.dumps(drift, ensure_ascii=False),
               "AC-PFKC4 the shipped R2446 reading is kept unchanged inside "
               "this report") and ok
    mine = [item for item in report["splits"]
            if item["key"] in report["keys_all"]]
    ok = check(json.dumps(mine, ensure_ascii=False)
               == json.dumps(drift["splits"], ensure_ascii=False),
               "AC-PFKC4 agreeing all-face keys keep the R2446 split reading "
               "byte for byte") and ok

    restore, _row, _original = drifted_kind(root)
    try:
        moved, moved_code = PFKC.audit(root, EXPORT, OWNER, WIRE)
        moved_drift, _moved_drift_code = PFRD.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    moved_all = [item for item in moved["splits"]
                 if item["key"] in moved["keys_all"]]
    ok = check(moved_code == 2
               and json.dumps(moved_all, ensure_ascii=False)
               == json.dumps(moved_drift["splits"], ensure_ascii=False),
               "AC-PFKC4 a subset-key split does not disturb the all-face "
               "reading") and ok
    return ok


def ac_pfkc5(root):
    """Each split row keeps the R2446 carrier shape (face, label, module,
    value, seams), with the seams that actually fired.

    The from-import face is the one drifted here ON PURPOSE: relative runs for
    real, so its carrier row proves the seam travels with the row.
    """
    restore, _row, _original = drifted_kind(root)
    try:
        report, code = PFKC.audit(root, EXPORT, OWNER, WIRE)
    finally:
        restore()
    splits = [item for item in report["splits"] if item["key"] == "kind"]
    carriers = splits[0]["faces"] if splits else []
    expected = ("face", "label", "module", "seams", "value")
    ok = check(code == 2 and len(splits) == 1
               and tuple(sorted(splits[0].keys()))
               == ("faces", "key", "line", "path")
               and all(tuple(sorted(row.keys())) == expected
                       for row in carriers)
               and len(carriers) == 2,
               "AC-PFKC5 every carrier row carries the pinned split keys")
    relative = [item for item in carriers if item["face"] == "relative"]
    ok = check(bool(relative)
               and relative[0]["label"] == "os-publish-relative-package-identity"
               and any(row["calls"] > 0 for row in relative[0]["seams"]),
               "AC-PFKC5 the relative carrier records its own label and the "
               "seam that fired") and ok
    return ok


def ac_pfkc6(source):
    """Pure ASCII, stdlib only, no clock, zero network, read-only, own label
    and own suite wired into the runner."""
    ok = check(all(ord(char) < 128 for char in source),
               "AC-PFKC6 source is pure ASCII")
    imports = sorted(line.split()[1].split(".")[0]
                     for line in source.splitlines()
                     if line.startswith("import "))
    ok = check(imports == sorted(STDLIB_OK),
               "AC-PFKC6 stdlib only, no network, no clock") and ok
    ok = check("open(" not in source and "os.replace" not in source
               and "import time" not in source and "time.time" not in source
               and "socket" not in source and "urllib" not in source,
               "AC-PFKC6 the module writes nothing and reads no clock") and ok
    ok = check(PFKC.LABEL == LABEL and "LABEL" in source,
               "AC-PFKC6 own reconcile label") and ok
    runner = read(RUNNER)
    ok = check(WIRED_EXPECT in runner,
               "AC-PFKC6 own suite is wired into the reconcile runner") and ok
    return ok


def main():
    source = read(MODULE)
    root = world([("plain_pub.py", PLAIN_WIRE)])

    results = [
        ("AC-PFKC1", ac_pfkc1(root, source)),
        ("AC-PFKC2", ac_pfkc2(root)),
        ("AC-PFKC3", ac_pfkc3(root)),
        ("AC-PFKC4", ac_pfkc4(root)),
        ("AC-PFKC5", ac_pfkc5(root)),
        ("AC-PFKC6", ac_pfkc6(source)),
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