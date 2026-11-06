"""AC-PNLT1..AC-PNLT6 suite for the non-label text readability face (R2505).

Criteria were pinned in state/queue/tech.md:542 at R2503, the seed row, BEFORE
this code existed.

What this proves: the R2502/R2503 gate is asked with patterns["labels"] ONLY,
while src/sandbox/suite_matrix.py::render interpolates header_note,
response_text, every caption and every face label into the CEO-visible artifact,
so a doctored header_note carrying U+FFFD read publishable=True and the composed
document really carried the broken codepoint. The render path now asks ONE
reading over every string the render actually reads, through the same shipped
per-codepoint law.

Every proof runs against the shipped modules (the law is patched only to prove
the CALL-time ask), and every doctoring happens in a private copy of the real
patterns file. The shipped patterns file is read and hashed, never written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import patterns_label_readability as PLR  # noqa: E402
import patterns_non_label_text_readability as PNLT  # noqa: E402
import matrix_stamp_provenance_line as MSPL  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "patterns_non_label_text_readability.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_EXPECT = ('"os-patterns-non-label-text-readability",')
WIRED_SUITE = ('"test_patterns_non_label_text_readability.py"), 6),')
BREAK = "\ufffd"


def check(ok, label):
    if ok:
        print("  PASS %s" % label)
    else:
        print("  FAIL %s" % label)
    return ok


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def patterns():
    return json.loads(read_text(PATTERNS_PATH))


def write_copy(path, document):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, ensure_ascii=False, indent=2))
    return path


def doctor_top(path, key):
    """A real copy with ONE broken codepoint appended to a top-level field."""
    document = patterns()
    document[key] = document[key] + BREAK
    return write_copy(path, document)


def doctor_label(path, key):
    """A real copy with ONE broken codepoint appended to a LABEL value."""
    document = patterns()
    document["labels"][key] = document["labels"][key] + BREAK
    return write_copy(path, document)


def evidence():
    """The evidence the SHIPPED doc was built from, asked of the shipped law."""
    recorded = SM.doc_evidence_face(read_text(DOC), patterns())
    if recorded is None:
        raise SystemExit("FAIL setup: shipped doc records no evidence path")
    return os.path.abspath(os.path.join(REPO, recorded))


def call_main(argv):
    """Run the shipped generator in-process and capture what it printed."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SM.main(["suite_matrix.py"] + argv)
    return code, buffer.getvalue()


def ac_pnlt1():
    """The refusal IS the shipped gate, asked at CALL time, code carried."""
    real = PLR.gate

    def refusing(fields):
        return {"publishable": False, "code": "E_GATE_AS_ASKED",
                "label": "header_note", "codepoints": ["U+FFFD"],
                "refusal": None, "labels": []}

    PLR.gate = refusing
    try:
        raised = None
        try:
            PNLT.guard(patterns())
        except PNLT.NonLabelRefused as exc:
            raised = exc
    finally:
        PLR.gate = real
    ok = check(raised is not None,
               "AC-PNLT1 a patched gate makes the real render refuse")
    ok = check(raised is not None and raised.code == "E_GATE_AS_ASKED",
               "AC-PNLT1 the refusal code is the gate own, carried verbatim "
               "(%r)" % (getattr(raised, "code", None),)) and ok
    ok = check(raised is not None and raised.field == "header_note",
               "AC-PNLT1 the refused FIELD travels with the refusal") and ok
    source = read_text(MODULE)
    ok = check("unicodedata" not in source and "def gate" not in source,
               "AC-PNLT1 this face carries no second classifier") and ok
    doctored = patterns()
    doctored["header_note"] = doctored["header_note"] + BREAK
    wiring = None
    try:
        SM.render(doctored, evidence(), {}, None, "stamp")
    except PNLT.NonLabelRefused as exc:
        wiring = exc
    ok = check(wiring is not None and wiring.field == "header_note",
               "AC-PNLT1 the REAL render path asks this face for a non-label "
               "defect the label gate cannot see") and ok
    return ok


def ac_pnlt2(world):
    """A suspect non-label field refuses the shipped tool, no byte written."""
    copy = doctor_top(os.path.join(world, "patterns-suspect.json"),
                      "header_note")
    target = os.path.join(world, "suspect-target.md")
    sentinel = "SENTINEL - must survive the refusal\n"
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(sentinel)
    before = read_bytes(target)
    real = SM.PATTERNS
    SM.PATTERNS = copy
    try:
        code, out = call_main(["--out", target, "--evidence", evidence()])
    finally:
        SM.PATTERNS = real
    ok = check(code == 4, "AC-PNLT2 the shipped tool refuses at exit 4 "
                          "(got %d)" % code)
    ok = check("field=header_note" in out and "non-label" in out,
               "AC-PNLT2 the refusal names the FIELD, not a label key: %r"
               % out.strip().splitlines()[:1]) and ok
    ok = check("E_PLR_SUSPECT" in out,
               "AC-PNLT2 the gate own code is carried into the refusal") \
        and ok
    ok = check(read_bytes(target) == before,
               "AC-PNLT2 the target keeps every byte it had") and ok
    residue = [name for name in os.listdir(world)
               if name.endswith((".tmp", ".part", ".parity-stage"))]
    ok = check(residue == [],
               "AC-PNLT2 no residue is left beside the target (%r)"
               % residue) and ok
    row = PNLT.reading(json.loads(read_text(copy)))
    ok = check(row["publishable"] is False and row["refused_field"]
               == "header_note" and row["refused_codepoints"] == ["U+FFFD"],
               "AC-PNLT2 the CLI reading names header_note and U+FFFD") and ok
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = PNLT.main(["patterns_non_label_text_readability.py",
                          "--patterns", copy])
    ok = check(code == 2,
               "AC-PNLT2 the face CLI refuses the same file at exit 2") and ok
    ok = check("field=header_note" in buffer.getvalue(),
               "AC-PNLT2 the CLI names the field too") and ok
    return ok


def ac_pnlt3():
    """A clean patterns file renders byte-identically to the shipped doc."""
    current = read_text(DOC)
    base = patterns()
    stamp = SM.doc_stamp(current, base)
    status, run = SM.parse_evidence(evidence())
    fresh = SM.render(base, evidence(), status, run, stamp,
                      stamp_from=MSPL.recorded_source(current,
                                                      base["labels"]))
    ok = check(stamp is not None, "AC-PNLT3 the shipped doc carries a stamp")
    ok = check(fresh == current,
               "AC-PNLT3 a clean render is byte-identical to %s (%d bytes)"
               % (SM.rel(DOC), len(fresh.encode("utf-8")))) and ok
    ok = check(PNLT.reading(base)["publishable"] is True,
               "AC-PNLT3 the shipped document reads publishable") and ok
    clean = call_main(["--check", "--out", DOC, "--evidence", evidence()])
    ok = check(clean[0] == 0 and "PASS check" in clean[1],
               "AC-PNLT3 --check keeps its today reading on the clean tree "
               "(exit %d)" % clean[0]) and ok
    return ok


def ac_pnlt4(world):
    """Coverage is derived from what the render READS, not a field list."""
    base = patterns()
    fields = PNLT.interpolated_strings(base)
    ok = check("header_note" in fields,
               "AC-PNLT4 the non-label header_note is covered (the measured "
               "gap)")
    ok = check("labels.response_text" in fields
               and "labels.provenance_note" in fields,
               "AC-PNLT4 the other interpolated label values are covered") \
        and ok
    ok = check("labels.summary_cols[0]" in fields
               and "labels.matrix_cols[5]" in fields,
               "AC-PNLT4 list items are covered one by one, not as a blob") \
        and ok
    ok = check("domains[0].faces[0].label" in fields
               and "domains[4].key" in fields,
               "AC-PNLT4 nested face labels and domain keys are covered") \
        and ok
    ok = check("labels.stamp_from" in fields,
               "AC-PNLT4 a field read through .get is covered too") and ok
    # The mirror: a key the render never reads is honestly NOT covered, so the
    # set is a derivation of the reads, not a blanket scan of the document.
    unread = patterns()
    unread["unread_note"] = "broken" + BREAK
    row = PNLT.reading(unread)
    ok = check(row["publishable"] is True
               and not [name for name in row["fields"]
                        if name.startswith("unread_note")],
               "AC-PNLT4 a key the render never reads is not claimed as "
               "covered") and ok
    # And a field the render really does read is refused, at the depth it sits.
    deep = patterns()
    deep["domains"][0]["faces"][0]["label"] = (
        deep["domains"][0]["faces"][0]["label"] + BREAK)
    row = PNLT.reading(deep)
    ok = check(row["publishable"] is False
               and row["refused_field"] == "domains[0].faces[0].label",
               "AC-PNLT4 a doctored nested face label is refused by its path "
               "(%r)" % (row["refused_field"],)) and ok
    return ok


def ac_pnlt5(world):
    """The patterns file is never rewritten and its digest never moves."""
    before = digest(PATTERNS_PATH)
    before_document = json.loads(json.dumps(patterns()))
    ac_pnlt2(world)
    ac_pnlt3()
    ac_pnlt4(world)
    after = digest(PATTERNS_PATH)
    ok = check(before == after,
               "AC-PNLT5 the shipped patterns digest is unchanged (%s)"
               % before[:16])
    ok = check(patterns() == before_document,
               "AC-PNLT5 every shipped value is still exactly as it was read") \
        and ok
    probe_absent = not os.path.exists(os.path.join(BASE, PNLT.PROBE_EVIDENCE))
    ok = check(probe_absent,
               "AC-PNLT5 the coverage probe leaves no file behind") and ok
    source = read_text(MODULE)
    ok = check('"w"' not in source and "'w'" not in source
               and "os.replace" not in source and "os.remove" not in source
               and "shutil" not in source,
               "AC-PNLT5 the module holds no write primitive") and ok
    return ok


def ac_pnlt6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source))
    ok = check(ascii_only, "AC-PNLT6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "hashlib", "json", "os", "sys",
                           "patterns_label_readability"},
               "AC-PNLT6 imports are stdlib plus the shipped gate (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PNLT6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PNLT6 zero network imports") and ok
    ok = check(PNLT.LABEL == "os-patterns-non-label-text-readability",
               "AC-PNLT6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_EXPECT in runner and WIRED_SUITE in runner,
               "AC-PNLT6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNLT6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PATTERNS NON-LABEL READABILITY suite (R2505, %d criteria)"
          % EXPECTED_CRITERIA)
    world = tempfile.mkdtemp(prefix="pnlt-suite-")
    try:
        results = [ac_pnlt1(), ac_pnlt2(world), ac_pnlt3(), ac_pnlt4(world),
                   ac_pnlt5(world), ac_pnlt6()]
    finally:
        shutil.rmtree(world, ignore_errors=True)
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())