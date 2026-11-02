"""export_publish_wire_identity suite (R2391).

Criteria AC-EPWI1..AC-EPWI6 were pinned inside the R2384 tech seed row of
state/queue/tech.md:447 BEFORE this code existed.

What this proves: R2384's guard reads any `.publish(..., EXPORT, ...)` as the
proven route without asking WHICH module the call resolves to, so a script can
hand the export to some other module's publish and still read CLEAN while never
touching the wire that proves the bytes. One reading now resolves the callee
through the file's own import lines and answers WIRE, FOREIGN, UNRESOLVED or
NO-PUBLISH - and the routed-publish test itself is the guard's law asked at
call time, so there is exactly one owner of that half.

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

import export_publish_path_guard as EPPG  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_publish_wire_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-publish-wire-identity"
WIRED_EXPECT = '"test_export_publish_wire_identity.py"), 6),'

WIRE_SCRIPT = '''"""A current publisher that hands the bytes to the proven wire."""

import closeout_export_parity_wire as CEPW
import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    return CEPW.publish(".", EXPORT, text="{}")
'''

FOREIGN_SCRIPT = '''"""A current publisher that hands the export to some OTHER module."""

import queue_floor_export_face as QFE
import some_other_wire as SOW
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    return SOW.publish(".", EXPORT, text="{}")
'''

STALE_IMPORT_SCRIPT = '''"""The import was renamed and the call was not."""

import closeout_export_parity_wire as PROVEN
import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    return CEPW.publish(".", EXPORT, text="{}")
'''

PLAIN_IMPORT_SCRIPT = '''"""The callee is spelled by the module's own full name."""

import closeout_export_parity_wire
import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def flush(data):
    QFE.apply(data, ".")
    return closeout_export_parity_wire.publish(".", EXPORT, text="{}")
'''

NO_PUBLISH_SCRIPT = '''"""On the current path, but it writes the export itself."""

import os

import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    text = "{}"
    with io.open(EXPORT, "w", encoding="utf-8") as handle:
        handle.write(text)
'''

OFF_PATH_SCRIPT = '''"""A one-off from an old round: never asks the owner."""

import closeout_export_parity_wire as CEPW
import os

EXPORT = os.path.join("docs", "status-export.json")


def flush():
    return CEPW.publish(".", EXPORT, text="{}")
'''

PROSE_SCRIPT = '''"""A round script whose prose SPELLS a publish call."""

import os

import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")

NOTE = "any `.publish(..., EXPORT, ...)` is the proven path"

FIXTURE = """
def publish(data):
    return some_other_module.publish(".", EXPORT, text="{}")
"""


def flush(data):
    QFE.apply(data, ".")
'''

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
    root = tempfile.mkdtemp(prefix="epwi-")
    for name, text in scripts:
        write(os.path.join(root, name), text)
    return root


def run(root, extra=()):
    argv = [sys.executable, MODULE, "--check", "--root", root]
    argv.extend(extra)
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return done.returncode, done.stdout.decode("utf-8", "replace"), \
        done.stderr.decode("utf-8", "replace")


def main():
    # AC-EPWI1: the reading names, per routed script, the module its publish
    # call resolves to - and the routed-publish test is the GUARD's law asked
    # at call time, proven by patching that law and watching the reading move.
    root = world([("wire_pub.py", WIRE_SCRIPT),
                  ("off_path.py", OFF_PATH_SCRIPT)])
    report, code = EPWI.audit(root)
    detail = report["detail"]
    check(report["wire"] == ["wire_pub.py"]
          and [row["module"] for row in detail] == ["closeout_export_parity_wire"]
          and [row["receiver"] for row in detail] == ["CEPW"]
          and code == 0,
          "AC-EPWI1 AC-EPWI1 the routed publish names its callee module")

    original = EPPG.routed_publish
    try:
        EPPG.routed_publish = lambda line, export_name=None: False
        patched, _ = EPWI.audit(root)
        EPPG.routed_publish = lambda line, export_name=None: True
        widened, _ = EPWI.audit(root)
    finally:
        EPPG.routed_publish = original
    # The per-file reading resolves a publish whatever the script is: on-path
    # is the audit() layer's question, not the file law's, and the CALL-time
    # guard import is what makes the patched legs above move.
    patched_line = EPWI.audit_script(
        OFF_PATH_SCRIPT.splitlines(), "status-export.json",
        "closeout_export_parity_wire")
    check(patched["verdict"] == "EMPTY" and patched["publishers"] == []
          and len(widened["detail"]) > len(detail)
          and [row["state"] for row in patched_line] == ["WIRE"]
          and patched_line[0]["receiver"] == "CEPW",
          "AC-EPWI1b AC-EPWI1 the guard law is asked at call time, not restated")

    # AC-EPWI2: WIRE for the wire, FOREIGN for any other module, both named.
    root2 = world([("wire_pub.py", WIRE_SCRIPT),
                   ("foreign_pub.py", FOREIGN_SCRIPT)])
    report2, code2 = EPWI.audit(root2)
    foreign_row = [row for row in report2["detail"]
                   if row["state"] == "FOREIGN"]
    check(report2["verdict"] == "FOREIGN" and code2 == 2
          and report2["wire"] == ["wire_pub.py"]
          and report2["foreign"] == ["foreign_pub.py"]
          and len(foreign_row) == 1
          and foreign_row[0]["module"] == "some_other_wire"
          and foreign_row[0]["line"] == 12,
          "AC-EPWI2 AC-EPWI2 the wire reads WIRE, another module reads FOREIGN")

    # A plain import spells the callee by its module's full name and still
    # resolves to the wire - the resolution is the import's, not a prefix test.
    root3 = world([("plain_pub.py", PLAIN_IMPORT_SCRIPT)])
    report3, code3 = EPWI.audit(root3)
    check(report3["verdict"] == "WIRE" and code3 == 0
          and report3["detail"][0]["receiver"] == "closeout_export_parity_wire"
          and report3["detail"][0]["module"] == "closeout_export_parity_wire",
          "AC-EPWI2b AC-EPWI2 a plain import of the wire resolves to the wire")

    # AC-EPWI3: a script on the path that publishes nothing reads NO-PUBLISH,
    # is NOT counted among the publishers, and never reads WIRE by accident.
    root4 = world([("writes_itself.py", NO_PUBLISH_SCRIPT)])
    report4, code4 = EPWI.audit(root4)
    check(report4["verdict"] == "EMPTY" and code4 == 0
          and report4["no_publish"] == ["writes_itself.py"]
          and report4["publishers"] == []
          and report4["wire"] == [],
          "AC-EPWI3 AC-EPWI3 nothing published reads NO-PUBLISH, not WIRE")

    # A publish spelling inside prose or a fixture literal is not a call: the
    # token mask blanks string and comment spans before the reading. Measured
    # live this window - one round script's docstring paragraph and its
    # embedded fixture script both read UNRESOLVED until the mask went in.
    prose_world = world([("round_notes.py", PROSE_SCRIPT)])
    report_prose, code_prose = EPWI.audit(prose_world)
    check(report_prose["verdict"] == "EMPTY" and code_prose == 0
          and report_prose["publishers"] == []
          and report_prose["no_publish"] == ["round_notes.py"],
          "AC-EPWI3b AC-EPWI3 a publish spelled in prose is not a call")

    # AC-EPWI4: the import renamed and the call not (and the reverse) reads
    # UNRESOLVED instead of borrowing the name it used to have.
    root5 = world([("stale_import.py", STALE_IMPORT_SCRIPT)])
    report5, code5 = EPWI.audit(root5)
    both = EPWI.audit_script(WIRE_SCRIPT.replace(
        "import closeout_export_parity_wire as CEPW",
        "import closeout_export_parity_wire as PROVEN").splitlines(),
        "status-export.json", "closeout_export_parity_wire")
    check(report5["verdict"] == "UNRESOLVED" and code5 == 2
          and report5["unresolved"] == ["stale_import.py"]
          and report5["detail"][0]["module"] == ""
          and report5["detail"][0]["receiver"] == "CEPW"
          and [row["state"] for row in both] == ["UNRESOLVED"],
          "AC-EPWI4 AC-EPWI4 import and call must agree, else UNRESOLVED")

    # AC-EPWI5: exit codes and a byte-stable --json over the pinned key set.
    root6 = world([("wire_pub.py", WIRE_SCRIPT)])
    rc_wire, out_wire, _ = run(root6)
    rc_json, json_a, _ = run(root6, ("--json",))
    rc_again, json_b, _ = run(root6, ("--json",))
    rc_empty, empty_out, _ = run(root4)
    rc_foreign, foreign_out, _ = run(root2)
    rc_unres, unres_out, _ = run(root5)
    rc_missing, _, missing_err = run(os.path.join(root6, "no-such-dir"))
    rc_flags, _, flags_err = run(root6, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root6],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_wire == 0 and "verdict=WIRE" in out_wire
          and rc_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == EPWI.REPORT_KEYS
          and rc_empty == 0 and "verdict=EMPTY" in empty_out
          and rc_foreign == 2 and "verdict=FOREIGN" in foreign_out
          and "foreign_pub.py:12" in foreign_out
          and "some_other_wire" in foreign_out
          and rc_unres == 2 and "verdict=UNRESOLVED" in unres_out
          and "stale_import.py" in unres_out
          and rc_missing == 3 and "E_EPWI_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_EPWI_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-EPWI5 AC-EPWI5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-EPWI6: writes nothing, reads no clock, ASCII, stdlib only, wired.
    root7 = world([("wire_pub.py", WIRE_SCRIPT),
                   ("foreign_pub.py", FOREIGN_SCRIPT),
                   ("stale_import.py", STALE_IMPORT_SCRIPT)])
    before = tree_digest(root7)
    EPWI.audit(root7)
    EPWI.audit(root7)
    after = tree_digest(root7)
    source = read(MODULE)
    not_console = source.replace("sys.stdout.write", "").replace(
        "sys.stderr.write", "")
    banned = ("import requests", "import urllib", "import socket",
              "import http", "import time", "import datetime", "import random")
    ascii_ok = True
    try:
        source.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    wired = read(RUNNER)
    check(before == after
          and not_console.count(".write(") == 0
          and '"w"' not in source and "'w'" not in source
          and ascii_ok
          and not any(token in source for token in banned)
          and 'LABEL = "%s"' % LABEL in source
          and WIRED_EXPECT in wired
          and '("%s",' % LABEL in wired,
          "AC-EPWI6 AC-EPWI6 writes nothing, no clock, ascii, wired")

    print("CRITERIA EXPECTED %d OBSERVED %d PASS %d FAIL %d"
          % (EXPECTED_CRITERIA, PASSES + FAILS, PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())