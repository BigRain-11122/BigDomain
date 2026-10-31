"""battery follow-up as one callable (R2272; criteria AC-BFU1..AC-BFU6 were
pinned inside the R2250 seed row of state/queue/tech.md BEFORE this code).

The four post-battery sections - suite-matrix regeneration and read-back,
fingerprint chain check, runner profile daily check, writer census re-freeze
and check - lived in one per-round script each (battery_followup_R1999.._R2271,
42 copies) that re-implemented the same sequence and differed only by evidence
path and label, so a defect fixed in one round's copy stayed broken in the next.

sections(root, evidence, label, call=...) runs the four pinned sections in the
pinned order and returns (report, bodies). It is a READER-ORCHESTRATOR: it
writes nothing itself. write_sections(path, report, bodies) is the single
writer and appends only to the evidence path it is given (utf-8, LF, bodies
CRLF-normalised - the R2262 lesson).

The matrix section regenerates into a private temp copy and byte-compares it
with the shipped doc: a mismatch is a FAIL carrying BOTH byte counts and the
doc is left untouched, never silently rewritten (AC-BFU2). Absent tools or an
unreadable matrix FAIL with their own codes; nothing fails open (AC-BFU4).

Disclosed boundary (AC-BFU3): the census section invokes qa_writer_census.py
--update-baseline, so that TOOL owns a baseline file under qa/; this module
never writes it, and no other path is written by this module at all.

Pure stdlib, pure-ASCII source, zero network.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

SECTIONS = ("matrix", "fingerprint", "profile", "census")
REPORT_KEYS = ("evidence", "label", "round", "sections", "verdict", "failing")

PY = sys.executable
MATRIX_DOC = "docs/sandbox-suite-matrix.md"
CHAIN = "src/sandbox/migration_chains.json"
TOOLS = {"matrix": "src/sandbox/suite_matrix.py",
         "fingerprint": "src/sandbox/fingerprint_regen.py",
         "profile": "src/sandbox/runner_profile.py",
         "census": "src/os/qa_writer_census.py"}

E_BFU_BAD_ARGS = "E_BFU_BAD_ARGS"
E_BFU_NO_TOOL = "E_BFU_NO_TOOL"
E_BFU_NO_MATRIX = "E_BFU_NO_MATRIX"
E_BFU_REGEN = "E_BFU_REGEN"

DEFAULTS = {"evidence": "qa/reconcile-all.log", "label": "R0", "round": None,
            "sections": [], "verdict": "FAIL", "failing": []}


def clean(text):
    """No captured body reaches the evidence file with a CR in it."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def first_line(text):
    for line in clean(text).split("\n"):
        if line.strip():
            return line.strip()
    return "-"


def last_line(text):
    """The verdict-bearing line: these tools end on their own verdict."""
    for line in reversed(clean(text).split("\n")):
        if line.strip():
            return line.strip()
    return "-"


def tool(root, name):
    """Resolve one tool under root; None when it is not on disk."""
    path = os.path.join(root, TOOLS[name].replace("/", os.sep))
    return path if os.path.isfile(path) else None


def run(cmd, root):
    proc = subprocess.run(cmd, capture_output=True, cwd=root)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace")
            + proc.stderr.decode("utf-8", "replace"))


def _ok(name, detail):
    return {"section": name, "verdict": "PASS", "detail": detail}


def _fail(name, detail):
    return {"section": name, "verdict": "FAIL", "detail": detail}


def section_matrix(root, evidence, call):
    """AC-BFU2: regenerate into a temp copy, compare, never rewrite the doc."""
    path = tool(root, "matrix")
    if path is None:
        return _fail("matrix", "%s %s" % (E_BFU_NO_TOOL, TOOLS["matrix"])), ""
    doc = os.path.join(root, MATRIX_DOC.replace("/", os.sep))
    work = tempfile.mkdtemp(prefix="bigdomain-bfu-")
    try:
        copy = os.path.join(work, "matrix.md")
        rc, out = call([PY, path, "--out", copy, "--evidence", evidence])
        if rc != 0 or not os.path.isfile(copy):
            return _fail("matrix", "%s rc=%d %s"
                         % (E_BFU_REGEN, rc, first_line(out))), clean(out)
        with open(copy, "rb") as handle:
            fresh = handle.read()
        try:
            with open(doc, "rb") as handle:
                disk = handle.read()
        except (IOError, OSError):
            return _fail("matrix", "%s %s" % (E_BFU_NO_MATRIX, MATRIX_DOC)), ""
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if fresh != disk:
        return _fail("matrix", "matrix mismatch on-disk=%dB regenerated=%dB"
                     " (no rewrite)" % (len(disk), len(fresh))), ""
    rc, out = call([PY, path, "--check"])
    if rc != 0:
        return _fail("matrix", "matrix check rc=%d on-disk=%dB"
                     " regenerated=%dB %s"
                     % (rc, len(disk), len(fresh), first_line(out))), clean(out)
    return _ok("matrix", "matrix byte-identical %dB" % len(fresh)), clean(out)


def section_tool(name, root, argv, call):
    """AC-BFU4: a missing tool is a FAIL with its code, never a silent PASS."""
    path = tool(root, name)
    if path is None:
        return _fail(name, "%s %s" % (E_BFU_NO_TOOL, TOOLS[name])), ""
    rc, out = call([PY, path] + argv)
    detail = last_line(out)
    if rc != 0:
        return _fail(name, "rc=%d %s" % (rc, detail)), clean(out)
    return _ok(name, detail), clean(out)


def section_census(root, call):
    """Re-freeze, then check LAST so the log it measures is already complete."""
    path = tool(root, "census")
    if path is None:
        return _fail("census", "%s %s" % (E_BFU_NO_TOOL, TOOLS["census"])), ""
    upd_rc, upd = call([PY, path, "--update-baseline"])
    chk_rc, chk = call([PY, path, "--check"])
    detail = last_line(chk)
    if upd_rc != 0 or chk_rc != 0:
        return _fail("census", "rc=%d/%d %s"
                     % (upd_rc, chk_rc, detail)), clean(upd + chk)
    return _ok("census", detail), clean(upd + chk)


def sections(root, evidence, label, round_no=None, call=None):
    """AC-BFU1: the four pinned sections, in order, PASS/FAIL + one-line detail."""
    if call is None:
        call = lambda cmd: run(cmd, root)  # noqa: E731
    report = {"evidence": evidence, "label": label, "round": round_no,
              "sections": [], "verdict": "PASS", "failing": []}
    bodies = []
    runner = {"matrix": lambda: section_matrix(root, evidence, call),
              "fingerprint": lambda: section_tool(
                  "fingerprint", root,
                  ["--chain", CHAIN, "--check"], call),
              "profile": lambda: section_tool(
                  "profile", root, ["--daily", "--check"], call),
              "census": lambda: section_census(root, call)}
    for name in SECTIONS:
        entry, body = runner[name]()
        entry["detail"] = clean(entry["detail"]).split("\n")[0]
        report["sections"].append(entry)
        if entry["verdict"] != "PASS":
            report["failing"].append(name)
        bodies.append("--- %s ---\n%s\n%s\n"
                      % (name.upper(), entry["verdict"], body))
    report["verdict"] = "PASS" if not report["failing"] else "FAIL"
    return report, bodies


def eol_state(path):
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8", "replace")
    crlf = text.count("\r\n")
    bare = text.count("\r") - crlf
    return crlf, bare, raw.startswith(b"\xef\xbb\xbf"), len(raw)


def render(report, tail=None):
    lines = ["SECTION %s %s %s" % (entry["section"], entry["verdict"],
                                   entry["detail"])
             for entry in report["sections"]]
    lines.append("VERDICT %s %s failing=%s"
                 % (report["label"], report["verdict"],
                    ",".join(report["failing"]) if report["failing"] else "none"))
    if tail:
        lines.append(tail)
    return "\n".join(lines) + "\n"


def write_sections(path, report, bodies):
    """The single writer: the evidence path is the only file this module writes."""
    crlf, bare, bom, size = eol_state(path)
    eol_ok = crlf == 0 and bare == 0 and not bom
    tail = ("--- VERDICT %s: %s eol crlf=%d bare_cr=%d bom=%s bytes=%d ---"
            % (report["label"], report["verdict"], crlf, bare, bom, size))
    text = "".join(bodies) + render(report, tail)
    with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return len(text.encode("utf-8")), eol_ok


def parse_args(argv):
    """AC-BFU5: pinned flags; anything else is bad flags (exit 5)."""
    opts = {"root": None, "evidence": None, "label": None, "round": None,
            "json": False, "dry_run": False}
    takes = {"--root": "root", "--evidence": "evidence", "--label": "label",
             "--round": "round"}
    flags = {"--json": "json", "--dry-run": "dry_run"}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in flags:
            opts[flags[arg]] = True
            index += 1
        elif arg in takes:
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise ValueError(E_BFU_BAD_ARGS + " " + arg + " needs a value")
            opts[takes[arg]] = argv[index + 1]
            index += 2
        else:
            raise ValueError(E_BFU_BAD_ARGS + " " + arg)
    if not opts["evidence"]:
        raise ValueError(E_BFU_BAD_ARGS + " --evidence is required")
    if opts["root"] is None:
        opts["root"] = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", ".."))
    if not os.path.isdir(opts["root"]):
        raise ValueError(E_BFU_BAD_ARGS + " --root is not a directory")
    if opts["label"] is None:
        stem = os.path.basename(opts["evidence"]).replace(".log", "")
        opts["label"] = stem.split("-")[-1] or "R0"
    if opts["round"] is None:
        digits = "".join(ch for ch in opts["label"] if ch.isdigit())
        opts["round"] = int(digits) if digits else None
    else:
        try:
            opts["round"] = int(opts["round"])
        except (TypeError, ValueError):
            raise ValueError(E_BFU_BAD_ARGS + " --round must be an integer")
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except ValueError as exc:
        print(str(exc))
        return 5
    evidence = os.path.join(opts["root"], opts["evidence"].replace("/", os.sep))
    if not os.path.isfile(evidence):
        print("MISSING EVIDENCE %s" % opts["evidence"])
        return 3
    report, bodies = sections(opts["root"], opts["evidence"], opts["label"],
                              opts["round"])
    if opts["dry_run"]:
        print(render(report), end="")
    else:
        written, eol_ok = write_sections(evidence, report, bodies)
        print(render(report), end="")
        print("APPENDED %dB eol_ok=%s" % (written, eol_ok))
    if opts["json"]:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))