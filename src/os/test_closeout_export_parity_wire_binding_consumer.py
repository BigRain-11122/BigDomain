"""AC-CEPB1..AC-CEPB6 suite for the wire-binding consumer face (R2733).

Criteria were pinned in state/queue/tech.md:702 at R2501 BEFORE this code
existed. Every fixture is built in memory and landed under a scratch dir that
this suite removes before it exits; no shipped source file is written.
Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)

import closeout_export_parity_wire_binding_consumer as CEPB  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "closeout_export_parity_wire_binding_consumer.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-closeout-export-parity-wire-binding-consumer",'
WIRED_SUITE = '"test_closeout_export_parity_wire_binding_consumer.py"'
PREV_LABEL = '"os-closeout-export-parity-text-binding",'
WIRE_LABEL = '"os-closeout-export-parity-wire",'

SCRATCH = os.path.join(SRC, "..", "tmp", "cepb-R2733-%d" % os.getpid())
WORLD = os.path.join(SCRATCH, "world")
OSDIR = os.path.join(WORLD, "src", "os")
DOCS = os.path.join(WORLD, "docs")

FIXTURE_OWN = '''import json
import os
import closeout_export_parity_wire as CEPW

REPO = "."
EXPORT = os.path.join(REPO, "docs", "status-export.json")
MARKER = "marker_own.txt"


def read_text(path):
    handle = open(path, "r")
    try:
        return handle.read()
    finally:
        handle.close()


def run():
    handle = open(MARKER, "w")
    handle.write("ran")
    handle.close()
    data = json.loads(read_text(EXPORT))
    data["do"] = "changed"
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return CEPW.publish(REPO, EXPORT, text=text)
'''

FIXTURE_OTHER = '''import json
import os
import closeout_export_parity_wire as CEPW

REPO = "."
EXPORT = os.path.join(REPO, "docs", "status-export.json")
OTHER = os.path.join(REPO, "docs", "other.json")
MARKER = "marker_other.txt"


def read_text(path):
    handle = open(path, "r")
    try:
        return handle.read()
    finally:
        handle.close()


def run():
    handle = open(MARKER, "w")
    handle.write("ran")
    handle.close()
    data = json.loads(read_text(OTHER))
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return CEPW.publish(REPO, EXPORT, text=text)
'''

FIXTURE_PLAIN = '''PLAIN = 1
'''

FIXTURE_STRING = '''BODY = """
import closeout_export_parity_wire as CEPW
text = "{}"
CEPW.publish(".", "docs/status-export.json", text=text)
"""
'''

FIXTURE_IMPORT_ONLY = '''import closeout_export_parity_wire as CEPW

VALUE = 1
'''

FIXTURE_NEW = '''import json
import os
import closeout_export_parity_wire as CEPW

REPO = "."
EXPORT = os.path.join(REPO, "docs", "status-export.json")


def read_text(path):
    handle = open(path, "r")
    try:
        return handle.read()
    finally:
        handle.close()


def run():
    data = json.loads(read_text(EXPORT))
    data["do"] = "again"
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return CEPW.publish(REPO, EXPORT, text=text)
'''

EXPORT_DOC = {"do": "A", "latest_artifact": "L", "next": "N"}
OTHER_DOC = {"do": "B", "latest_artifact": "L", "next": "N"}

WAVE_ONE = (
    ("caller_own.py", FIXTURE_OWN),
    ("caller_other.py", FIXTURE_OTHER),
    ("plain.py", FIXTURE_PLAIN),
    ("string_only.py", FIXTURE_STRING),
    ("import_only.py", FIXTURE_IMPORT_ONLY),
)


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def write_text(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    handle = open(path, "w")
    try:
        handle.write(text)
    finally:
        handle.close()


def read_bytes(path):
    handle = open(path, "rb")
    try:
        return handle.read()
    finally:
        handle.close()


def sha256(path):
    return hashlib.sha256(read_bytes(path)).hexdigest().upper()


def tree_digest(folder):
    """One digest over every file name and byte under a folder, sorted."""
    parts = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            parts.append(name + ":" + sha256(path))
    return hashlib.sha256(("\n".join(parts)).encode("ascii")).hexdigest().upper()


def build_world():
    for name, text in WAVE_ONE:
        write_text(os.path.join(OSDIR, name), text)
    write_text(os.path.join(DOCS, "status-export.json"),
               '{"do": "A", "latest_artifact": "L", "next": "N"}\n')
    write_text(os.path.join(DOCS, "other.json"),
               '{"do": "B", "latest_artifact": "L", "next": "N"}\n')


def rows_by_file(report):
    out = {}
    for row in report["rows"]:
        out.setdefault(row["file"], []).append(row)
    return out


def ac_cepb1():
    """AC-CEPB1: the caller set is derived from the tree at CALL time."""
    first = CEPB.read(WORLD)
    write_text(os.path.join(OSDIR, "caller_new.py"), FIXTURE_NEW)
    second = CEPB.read(WORLD)
    names_one = set(rows_by_file(first))
    names_two = set(rows_by_file(second))
    ok = check(second["scanned"] == first["scanned"] + 1,
               "AC-CEPB1 a new file on disk MOVES the scan count (%d -> %d)"
               % (first["scanned"], second["scanned"]))
    ok = check(names_one < names_two and "caller_new.py" in names_two,
               "AC-CEPB1 the set grows with the tree (%d -> %d names)"
               % (len(names_one), len(names_two))) and ok
    ok = check(second["bound"] > first["bound"],
               "AC-CEPB1 the new caller moves the BOUND count (%d -> %d)"
               % (first["bound"], second["bound"])) and ok
    raw = read_bytes(MODULE).decode("ascii")
    planted = [name for name in ("caller_own", "caller_other", "caller_new",
                                 "string_only", "import_only")
               if name in raw]
    ok = check(not planted,
               "AC-CEPB1 no fixture name is planted in the face (%s)"
               % (planted,)) and ok
    ok = check("os.listdir" in raw,
               "AC-CEPB1 the face enumerates the folder it is given") and ok
    return ok


def ac_cepb2():
    """AC-CEPB2: a caller handing in its OWN composition reads BOUND."""
    before = sha256(os.path.join(OSDIR, "caller_own.py"))
    report = CEPB.read(WORLD)
    rows = rows_by_file(report).get("caller_own.py", [])
    ok = check(len(rows) == 1, "AC-CEPB2 caller_own.py carries one row (%d)"
               % (len(rows),))
    row = rows[0] if rows else {}
    ok = check(row.get("verdict") == CEPB.BOUND,
               "AC-CEPB2 its verdict is BOUND (%r)" % (row.get("verdict"),)
               ) and ok
    ok = check("status-export.json" in row.get("source", ""),
               "AC-CEPB2 the row names the document it composed (%r)"
               % (row.get("source"),)) and ok
    after = sha256(os.path.join(OSDIR, "caller_own.py"))
    ok = check(before == after,
               "AC-CEPB2 the caller bytes are unchanged (%s..)"
               % (after[:12],)) and ok
    ok = check(row.get("first_field") == "(unchanged)",
               "AC-CEPB2 a bound caller names no differing field (%r)"
               % (row.get("first_field"),)) and ok
    return ok


def ac_cepb3():
    """AC-CEPB3: another document's composition reads UNBOUND, never run."""
    rows = rows_by_file(CEPB.read(WORLD)).get("caller_other.py", [])
    ok = check(len(rows) == 1, "AC-CEPB3 caller_other.py carries one row (%d)"
               % (len(rows),))
    row = rows[0] if rows else {}
    ok = check(row.get("verdict") == CEPB.UNBOUND,
               "AC-CEPB3 its verdict is UNBOUND (%r)" % (row.get("verdict"),)
               ) and ok
    ok = check(row.get("file") == "caller_other.py",
               "AC-CEPB3 the row names the file (%r)" % (row.get("file"),)
               ) and ok
    ok = check(row.get("first_field") == "do",
               "AC-CEPB3 the first differing field is named (%r)"
               % (row.get("first_field"),)) and ok
    ok = check(row.get("other") == "other.json",
               "AC-CEPB3 the other document is named (%r)"
               % (row.get("other"),)) and ok
    ok = check(not os.path.exists(os.path.join(WORLD, "marker_other.txt")),
               "AC-CEPB3 the unbound caller was NOT run (no marker)") and ok
    ok = check(not os.path.exists(
        os.path.join(OSDIR, "marker_other.txt")),
        "AC-CEPB3 no marker landed beside the caller either") and ok
    return ok


def ac_cepb4():
    """AC-CEPB4: a file that never publishes reads OUT-OF-SCOPE, and is named."""
    report = CEPB.read(WORLD)
    rows = rows_by_file(report)
    wanted = ("plain.py", "string_only.py", "import_only.py")
    ok = check(report["out_of_scope"] == 3,
               "AC-CEPB4 three out-of-scope rows are counted (%d)"
               % (report["out_of_scope"],))
    for name in wanted:
        got = rows.get(name, [])
        ok = check(len(got) == 1 and got[0]["verdict"] == CEPB.OUT_OF_SCOPE,
                   "AC-CEPB4 %s reads OUT-OF-SCOPE rather than vanishing"
                   % (name,)) and ok
    ok = check(report["bound"] + report["unbound"] + report["out_of_scope"]
               == len(report["rows"]),
               "AC-CEPB4 every row carries one of the three verdicts (%d rows)"
               % (len(report["rows"]),)) and ok
    ok = check(report["scanned"] == len(rows),
               "AC-CEPB4 every scanned file is represented (%d/%d)"
               % (len(rows), report["scanned"])) and ok
    return ok


def ac_cepb5():
    """AC-CEPB5: the reading writes nothing and reads no clock."""
    before = tree_digest(OSDIR)
    CEPB.read(WORLD)
    after = tree_digest(OSDIR)
    ok = check(before == after,
               "AC-CEPB5 the scanned world is byte-identical (%s..)"
               % (after[:12],))
    real_before = tree_digest(BASE)
    live = CEPB.read(os.path.join(BASE, "..", ".."), "docs/status-export.json")
    real_after = tree_digest(BASE)
    ok = check(real_before == real_after,
               "AC-CEPB5 the live src/os tree is byte-identical (%s..)"
               % (real_after[:12],)) and ok
    ok = check(live["scanned"] > 100,
               "AC-CEPB5 the live reading scans the real tree (%d files)"
               % (live["scanned"],)) and ok
    print("LIVE %s scanned=%d bound=%d unbound=%d out_of_scope=%d"
          % (live["label"], live["scanned"], live["bound"], live["unbound"],
             live["out_of_scope"]))
    ok = check(live["label"] == CEPB.LABEL,
               "AC-CEPB5 the live reading carries its own label") and ok
    return ok


def import_names(text):
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            out.append(stripped.split()[1])
        elif stripped.startswith("from ") and " import " in stripped:
            out.append(stripped.split()[1])
    return out


def ac_cepb6():
    """AC-CEPB6: hygiene - ASCII, stdlib only, own label and own suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-CEPB6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "import subprocess",
                                "shell=True")
              if name in text]
    ok = check(not banned, "AC-CEPB6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    allowed = ("ast", "io", "json", "os", "sys", "warnings")
    bad = [name for name in import_names(text)
           if name.split(".")[0] not in allowed]
    ok = check(not bad and import_names(text),
               "AC-CEPB6 every import is stdlib (%s)" % (bad,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-CEPB6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-CEPB6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(PREV_LABEL) == 1,
               "AC-CEPB6 the R2501 binding row is untouched (%d)"
               % (registry.count(PREV_LABEL),)) and ok
    ok = check(registry.count(WIRE_LABEL) == 1,
               "AC-CEPB6 the R2377 wire row is untouched (%d)"
               % (registry.count(WIRE_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE), "AC-CEPB6 this suite exists on disk"
               ) and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-CEPB6 six criteria are declared") and ok
    ok = check(CEPB.LABEL == "os-closeout-export-parity-wire-binding-consumer",
               "AC-CEPB6 the face carries its own reconcile label (%r)"
               % (CEPB.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(OSDIR):
        os.makedirs(OSDIR)
    if not os.path.isdir(DOCS):
        os.makedirs(DOCS)
    build_world()
    checks = [ac_cepb1, ac_cepb2, ac_cepb3, ac_cepb4, ac_cepb5, ac_cepb6]
    try:
        results = [func() for func in checks]
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
        for stray in ("marker_own.txt", "marker_other.txt"):
            path = os.path.join(SRC, "..", "tmp", stray)
            if os.path.exists(path):
                os.remove(path)
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
