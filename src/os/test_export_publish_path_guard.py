"""export_publish_path_guard suite (R2384).

Criteria AC-EPPG1..AC-EPPG6 were pinned inside the R2378 tech seed row of
state/queue/tech.md:431 BEFORE this code existed.

What this proves: the export has more writers than the one closeout that asks
the parity wire, and nothing read the difference. One guard now reads every
script in a tree, decides whether it belongs to the CURRENT publishing path
(does it ask the module that owns the current export shape?) and names every
current publisher that writes the document itself. A routed script reads CLEAN
whatever it is called; a bypassing one reads BYPASS whatever it is called. Old
one-off scripts are reported as historical and are never called offenders,
which is what keeps the gauge meaningful instead of permanently red.

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
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import export_publish_path_guard as EPPG  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_publish_path_guard.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-publish-path-guard"
WIRED_EXPECT = '"test_export_publish_path_guard.py"), 6),'

BYPASS_SCRIPT = '''"""A current publisher that writes the export itself."""

import json
import os

import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")


def write_text(path, text):
    return None


def publish(data):
    QFE.apply(data, ".")
    text = json.dumps(data) + "\\n"
    write_text(EXPORT, text)
'''

ROUTED_SCRIPT = '''"""A current publisher that hands the bytes to the proven wire."""

import os

import closeout_export_parity_wire as CEPW
import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    text = "{}"
    return CEPW.publish(".", EXPORT, text=text)
'''

HANDLE_SCRIPT = '''"""A current publisher that opens the export for writing in two steps."""

import os

import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    handle = open(EXPORT, "w", encoding="utf-8")
    handle.write("{}")
    handle.close()
'''

READER_SCRIPT = '''"""A script that only reads the export."""

import os

EXPORT = os.path.join("docs", "status-export.json")


def read_all():
    with open(EXPORT, "r", encoding="utf-8") as handle:
        return handle.read()
'''

HISTORICAL_SCRIPT = '''"""A one-off from an old round: writes an old shape, asks no owner."""

import io
import os

EXPORT = os.path.join("docs", "status-export.json")


def flush(text):
    with io.open(EXPORT, "w", encoding="utf-8", newline="\\n") as handle:
        handle.write(text)
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
    root = tempfile.mkdtemp(prefix="eppg-")
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
    # AC-EPPG1: every publisher is read from the GIVEN tree, and each offender
    # carries the file AND the line that publishes it.
    root = world([("direct_writer.py", BYPASS_SCRIPT),
                  ("reader.py", READER_SCRIPT)])
    report, code = EPPG.audit(root)
    detail = report["detail"]
    check(report["offenders"] == ["direct_writer.py"] and code == 2
          and len(detail) == 1
          and detail[0]["path"] == "direct_writer.py"
          and detail[0]["line"] == 18
          and detail[0]["kind"] == "write"
          and detail[0]["current"] is True
          and "reader.py" not in report["publishers"]
          and report["scanned"] == 2,
          "AC-EPPG1 AC-EPPG1 offender named with file and publishing line")

    # The line is measured, not assumed: the same script shifted by two lines
    # reports the shifted number, so the number comes from the file it names.
    shifted = world([("direct_writer.py", "\n\n" + BYPASS_SCRIPT)])
    report2, _ = EPPG.audit(shifted)
    check(report2["detail"][0]["line"] == 20,
          "AC-EPPG1b AC-EPPG1 the reported line follows the file it was read from")

    # AC-EPPG2: routing through the wire is CLEAN, and that is a property of the
    # code - the filename has no vote either way. An old one-off that asks no
    # owner is historical, not an offender.
    root2 = world([("closeout_blessed.py", BYPASS_SCRIPT),
                   ("not_a_closeout_name.py", ROUTED_SCRIPT),
                   ("flush_export_R1999.py", HISTORICAL_SCRIPT)])
    report3, code3 = EPPG.audit(root2)
    check(report3["verdict"] == "BYPASS"
          and report3["offenders"] == ["closeout_blessed.py"]
          and report3["clean"] == ["not_a_closeout_name.py"]
          and report3["historical"] == ["flush_export_R1999.py"]
          and "flush_export_R1999.py" not in report3["offenders"]
          and "flush_export_R1999.py" not in report3["clean"]
          and report3["publishers"] == ["closeout_blessed.py",
                                        "flush_export_R1999.py",
                                        "not_a_closeout_name.py"]
          and code3 == 2,
          "AC-EPPG2 AC-EPPG2 routed reads CLEAN, blessed name does not, "
          "fossils are historical")

    # The two-step handle write is caught at the open() call that names it.
    handle_world = world([("handle_writer.py", HANDLE_SCRIPT)])
    report4, _ = EPPG.audit(handle_world)
    check(report4["offenders"] == ["handle_writer.py"]
          and report4["detail"][0]["kind"] == "open"
          and 'open(EXPORT, "w"' in report4["detail"][0]["text"],
          "AC-EPPG2b AC-EPPG2 a two-step write is caught at its open() line")

    # AC-EPPG3: the guard writes nothing (whole-tree digest before and after)
    # and reads no clock.
    root3 = world([("direct_writer.py", BYPASS_SCRIPT),
                   ("routed.py", ROUTED_SCRIPT),
                   ("flush_export_R1999.py", HISTORICAL_SCRIPT)])
    before = tree_digest(root3)
    EPPG.audit(root3)
    EPPG.audit(root3)
    after = tree_digest(root3)
    source = read(MODULE)
    # The CLI prints, so stdout/stderr writes are not file writes: the law is
    # that no OTHER write call exists and no file is ever opened for writing.
    not_console = source.replace("sys.stdout.write", "").replace(
        "sys.stderr.write", "")
    check(before == after
          and "import time" not in source
          and "import datetime" not in source
          and "time." not in source
          and ".write(" not in not_console
          and '"w"' not in source
          and "'w'" not in source,
          "AC-EPPG3 AC-EPPG3 writes nothing and reads no clock")

    # AC-EPPG4: no current publisher at all reads EMPTY at exit 0 - never CLEAN,
    # and a historical one-off alone is still EMPTY because it is not the live
    # path.
    root4 = world([("reader.py", READER_SCRIPT), ("notes.py", "VALUE = 1\n"),
                   ("flush_export_R1999.py", HISTORICAL_SCRIPT)])
    report5, code5 = EPPG.audit(root4)
    check(report5["verdict"] == "EMPTY" and code5 == 0
          and report5["offenders"] == [] and report5["clean"] == []
          and report5["historical"] == ["flush_export_R1999.py"]
          and report5["scanned"] == 3,
          "AC-EPPG4 AC-EPPG4 no current publisher reads EMPTY at exit 0")

    # AC-EPPG5: exit codes and a byte-stable --json over the pinned key set.
    clean_world = world([("routed.py", ROUTED_SCRIPT)])
    rc_clean, out_clean, _ = run(clean_world)
    rc_clean_json, json_a, _ = run(clean_world, ("--json",))
    rc_again, json_b, _ = run(clean_world, ("--json",))
    rc_empty, empty_out, _ = run(root4)
    rc_bypass, bypass_out, _ = run(root3)
    rc_missing, _, missing_err = run(os.path.join(root3, "no-such-dir"))
    rc_flags, _, flags_err = run(root3, ("--nope",))
    rc_no_check = subprocess.run(
        [sys.executable, MODULE, "--root", root3],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    parsed = json.loads(json_a)
    check(rc_clean == 0 and "verdict=CLEAN" in out_clean
          and rc_clean_json == 0 and json_a == json_b
          and tuple(parsed.keys()) == EPPG.REPORT_KEYS
          and rc_empty == 0 and "verdict=EMPTY" in empty_out
          and rc_bypass == 2 and "verdict=BYPASS" in bypass_out
          and "direct_writer.py:18" in bypass_out
          and rc_missing == 3 and "E_EPPG_NO_ROOT" in missing_err
          and rc_flags == 5 and "E_EPPG_BAD_FLAGS" in flags_err
          and rc_no_check == 5,
          "AC-EPPG5 AC-EPPG5 exit codes 0/2/3/5 plus a byte-stable --json")

    # AC-EPPG6: pure ASCII, stdlib only, zero network, own reconcile label.
    banned = ("import requests", "import urllib", "import socket",
              "import http", "import urllib3", "import time", "import datetime",
              "import random")
    ascii_ok = True
    try:
        source.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    wired = read(RUNNER)
    check(ascii_ok
          and not any(token in source for token in banned)
          and 'LABEL = "%s"' % LABEL in source
          and WIRED_EXPECT in wired
          and '("%s",' % LABEL in wired,
          "AC-EPPG6 AC-EPPG6 ascii, stdlib only, no network, wired to the runner")

    print("CRITERIA EXPECTED %d OBSERVED %d PASS %d FAIL %d"
          % (EXPECTED_CRITERIA, PASSES + FAILS, PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())