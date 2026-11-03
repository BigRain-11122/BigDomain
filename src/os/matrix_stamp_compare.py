"""matrix_stamp_compare - the matrix section's compare, made content-only
(R2418; criteria AC-MSC1..AC-MSC6 were pinned at R2414 inside the seed row of
state/queue/tech.md line 493 BEFORE this code existed).

What was measured, not assumed: battery_followup.matrix_core regenerated the
matrix into a private temp copy and byte-compared it with the shipped doc,
but the generator stamps every render with the CURRENT minute, so a doc
regenerated in a different minute read a mismatch of EQUAL byte length
(R2414 leg2: on-disk 51414B against regenerated 51414B FAIL) while
suite_matrix --check - which reuses the doc's own stamp - read PASS
byte-identical. The section therefore manufactured a FAIL on the one volatile
line and hid every real one behind it.

What this module adds: ONE question, "which stamp does this document carry",
asked of suite_matrix.doc_stamp at CALL time (the same law --check uses), plus
an aligned render of that document through `suite_matrix --stamp-from DOC`.
The byte compare that follows is then content-only by construction, so the
stamp line is neither parsed here nor stripped by a second reader. A document
with no stamp line refuses E_MSC_NO_STAMP; it never reads as a pass.

Read-only: no path is written except the private temp copy the render lands
in, and --check remains the single authority for the shipped doc.

Usage:
    python src/os/matrix_stamp_compare.py --check --doc docs/x.md \
        --evidence qa/reconcile-all-R<round>.log [--json]

Exit 0 = PASS byte-identical after the stamp is aligned, 2 = FAIL content
differs, 3 = missing doc / no stamp / missing tool / unreadable evidence,
5 = bad flags. Pure stdlib, pure-ASCII source, zero network, no clock.
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")

DEFAULT_DOC = "docs/sandbox-suite-matrix.md"
DEFAULT_EVIDENCE = "qa/reconcile-all.log"

E_MSC_BAD_ARGS = "E_MSC_BAD_ARGS"
E_MSC_NO_DOC = "E_MSC_NO_DOC"
E_MSC_NO_STAMP = "E_MSC_NO_STAMP"
E_MSC_NO_TOOL = "E_MSC_NO_TOOL"
E_MSC_REGEN = "E_MSC_REGEN"

PASS = "PASS"
FAIL = "FAIL"
MISSING_DOC = "MISSING-DOC"
NO_STAMP = "NO-STAMP"
NO_TOOL = "NO-TOOL"
REGEN_FAILED = "REGEN-FAILED"

SUITE_LABEL = "os-matrix-stamp-compare"
REPORT_KEYS = ("doc", "stamp", "verdict", "code", "on_disk_bytes",
               "fresh_bytes", "detail")

TAKES = {"--doc": "doc", "--evidence": "evidence", "--root": "root"}
FLAGS = {"--check": "check", "--json": "json"}


def law():
    """suite_matrix itself, imported at CALL time (one stamp law in the tree)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def run(cmd, root):
    proc = subprocess.run(cmd, capture_output=True, cwd=root)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace")
            + proc.stderr.decode("utf-8", "replace"))


def first_line(text):
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.strip():
            return line.strip()
    return "-"


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def stamp_of(doc_path):
    """(verdict, code, stamp, detail): the doc's stamp, asked of the law."""
    try:
        with io.open(doc_path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError):
        return MISSING_DOC, E_MSC_NO_DOC, None, "doc unreadable"
    reader = law()
    stamp = reader.doc_stamp(text, reader.load_patterns())
    if stamp is None:
        return NO_STAMP, E_MSC_NO_STAMP, None, "no stamp line in doc"
    return PASS, None, stamp, "stamp=%s" % stamp


def render(root, doc_path, evidence_path, call=None):
    """Render the doc's content with ITS OWN stamp into a private temp copy.

    Returns (verdict, code, fresh_bytes, detail). The shipped doc is never
    touched: the only write is the temp file this render lands in.
    """
    if call is None:
        call = lambda cmd: run(cmd, root)  # noqa: E731
    tool = os.path.join(root, "src", "sandbox", "suite_matrix.py")
    if not os.path.isfile(tool):
        return NO_TOOL, E_MSC_NO_TOOL, None, "src/sandbox/suite_matrix.py"
    work = tempfile.mkdtemp(prefix="bigdomain-msc-")
    try:
        copy = os.path.join(work, "matrix.md")
        rc, out = call([sys.executable, tool, "--out", copy,
                        "--evidence", evidence_path,
                        "--stamp-from", doc_path])
        if rc != 0 or not os.path.isfile(copy):
            return (REGEN_FAILED, E_MSC_REGEN, None,
                    "rc=%d %s" % (rc, first_line(out)))
        return PASS, None, read_bytes(copy), "rendered"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def compare(root, doc_path, evidence_path, call=None):
    """One row: is the shipped doc content-identical after the stamp aligns?"""
    verdict, code, stamp, detail = stamp_of(doc_path)
    if verdict != PASS:
        return {"doc": doc_path, "stamp": None, "verdict": verdict,
                "code": code, "on_disk_bytes": None, "fresh_bytes": None,
                "detail": detail}
    verdict, code, fresh, detail = render(root, doc_path, evidence_path, call)
    if verdict != PASS:
        return {"doc": doc_path, "stamp": stamp, "verdict": verdict,
                "code": code, "on_disk_bytes": None, "fresh_bytes": None,
                "detail": detail}
    try:
        disk = read_bytes(doc_path)
    except (IOError, OSError):
        return {"doc": doc_path, "stamp": stamp, "verdict": MISSING_DOC,
                "code": E_MSC_NO_DOC, "on_disk_bytes": None,
                "fresh_bytes": len(fresh), "detail": "doc unreadable"}
    row = {"doc": doc_path, "stamp": stamp, "on_disk_bytes": len(disk),
           "fresh_bytes": len(fresh)}
    if disk == fresh:
        row.update({"verdict": PASS, "code": 0,
                    "detail": "matrix byte-identical %dB stamp-aligned"
                              % len(fresh)})
        return row
    row.update({"verdict": FAIL, "code": 2,
                "detail": "matrix content mismatch on-disk=%dB"
                          " regenerated=%dB (no rewrite)"
                          % (len(disk), len(fresh))})
    return row


def render_row(row):
    """Human line: the verdict, the stamp, both byte counts and the code a
    refusal carries (a refusal that hid its code behind the JSON face would
    make an operator read NO-STAMP and grep for it)."""
    return ("%s%s stamp=%s on-disk=%s regenerated=%s %s"
            % (row["verdict"],
               "" if row["verdict"] == PASS else " %s" % row["code"],
               row["stamp"], row["on_disk_bytes"], row["fresh_bytes"],
               row["detail"]))


def parse(argv):
    """The flag table this tree keeps once; bad flags refuse BAD-ARGS."""
    opts = {"doc": DEFAULT_DOC, "evidence": DEFAULT_EVIDENCE,
            "root": REPO, "check": False, "json": False}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in TAKES:
            if index + 1 >= len(argv):
                return opts, E_MSC_BAD_ARGS
            opts[TAKES[token]] = argv[index + 1]
            index += 2
            continue
        if token in FLAGS:
            opts[FLAGS[token]] = True
            index += 1
            continue
        return opts, E_MSC_BAD_ARGS
    return opts, None


def main(argv):
    import json
    opts, bad = parse(argv[1:])
    if bad is not None:
        print("%s unknown or incomplete flag" % E_MSC_BAD_ARGS)
        return 5
    if not opts["check"]:
        print("%s --check is required" % E_MSC_BAD_ARGS)
        return 5
    root = os.path.abspath(opts["root"])
    doc = os.path.join(root, opts["doc"].replace("/", os.sep))
    evidence = os.path.join(root, opts["evidence"].replace("/", os.sep))
    row = compare(root, doc, evidence)
    payload = {"doc": opts["doc"], "stamp": row["stamp"],
               "verdict": row["verdict"], "code": row["code"],
               "on_disk_bytes": row["on_disk_bytes"],
               "fresh_bytes": row["fresh_bytes"], "detail": row["detail"]}
    if opts["json"]:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(render_row(row))
    return 0 if row["verdict"] == PASS else (2 if row["code"] == 2 else 3)


if __name__ == "__main__":
    sys.exit(main(sys.argv))