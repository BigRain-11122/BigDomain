"""AC-STPT1..AC-STPT6 suite for the stamp text coverage face (R2511).

Criteria were pinned in state/queue/tech.md:549 at R2509 BEFORE this code
existed.

What this proves: every gate shipped before R2511 reads text the render takes
from the patterns document, from DISK or from the evidence path, while
src/sandbox/suite_matrix.py::render also prints two CALLER-SUPPLIED strings -
the generation stamp and the --stamp-from provenance source. Measured at
R2509, a stamp and a stamp_from carrying U+FFFD printed both codepoints into
the CEO-visible artifact while every shipped reading still returned
publishable=True.

Every proof runs against the shipped modules; the shipped law is patched only
to prove the CALL-time ask, and every doctoring happens in memory or in a
private temporary directory. No shipped source file, no stamp source document
and no evidence log is written.

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

import stamp_text_coverage as STPT  # noqa: E402
import patterns_label_readability as PLR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_text_coverage.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
PLR_MODULE = os.path.join(BASE, "patterns_label_readability.py")
WIRED_LABEL = '"os-stamp-text-coverage",'
WIRED_SUITE = '"test_stamp_text_coverage.py"), 6),'
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


def evidence():
    """The evidence the SHIPPED doc was built from, asked of the shipped law."""
    recorded = SM.doc_evidence_face(read_text(DOC), patterns())
    if recorded is None:
        raise SystemExit("FAIL setup: shipped doc records no evidence path")
    return os.path.abspath(os.path.join(REPO, recorded))


def doc_faces():
    """The stamp and the borrow the SHIPPED doc records, asked of its laws."""
    text = read_text(DOC)
    document = patterns()
    stamp = SM.doc_stamp(text, document)
    source = SM.MSPL.recorded_source(text, document["labels"])
    if stamp is None:
        raise SystemExit("FAIL setup: shipped doc carries no stamp line")
    return stamp, source


def call_main(argv):
    """Run the shipped generator in-process and capture what it printed."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SM.main(["suite_matrix.py"] + argv)
    return code, buffer.getvalue()


def ac_stpt1():
    """The refusal IS the shipped law, asked at CALL time, code carried."""
    real = PLR.gate

    def refusing(fields):
        return {"publishable": False, "code": "E_GATE_AS_ASKED",
                "label": STPT.PIECE_STAMP, "codepoints": ["U+FFFD"],
                "refusal": None, "labels": []}

    stamp, source = doc_faces()
    PLR.gate = refusing
    try:
        raised = None
        try:
            STPT.guard(patterns(), stamp, source)
        except STPT.StampTextRefused as exc:
            raised = exc
    finally:
        PLR.gate = real
    ok = check(raised is not None,
               "AC-STPT1 a patched gate makes the real reading refuse")
    ok = check(raised is not None and raised.code == "E_GATE_AS_ASKED",
               "AC-STPT1 the refusal code is the gate own, carried verbatim "
               "(%r)" % (getattr(raised, "code", None),)) and ok
    ok = check(raised is not None and raised.piece == STPT.PIECE_STAMP
               and raised.value == stamp,
               "AC-STPT1 the refused PIECE and VALUE travel with the refusal "
               "(%r)" % (getattr(raised, "piece", None),)) and ok
    source_text = read_text(MODULE)
    ok = check("unicodedata" not in source_text
               and "def gate" not in source_text,
               "AC-STPT1 this face carries no second classifier") and ok
    return ok


def ac_stpt2():
    """A broken stamp or stamp_from refuses, naming the piece, writing none."""
    doc_before = read_bytes(DOC)
    work = tempfile.mkdtemp(prefix="stpt-")
    try:
        text = read_text(DOC)
        stamp, source = doc_faces()
        prefix = "- %s: %s" % (patterns()["labels"]["stamp"],
                               patterns()["labels"]["stamp_prefix"])
        broken_stamp_doc = os.path.join(work, "doc-broken-stamp.md")
        with open(broken_stamp_doc, "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(text.replace(prefix + stamp,
                                      prefix + stamp[:4] + BREAK + stamp[4:]))
        broken_source_doc = os.path.join(work, "doc-broken-source.md")
        with open(broken_source_doc, "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(text.replace(str(source),
                                      str(source)[:-4] + BREAK + ".log"))

        raised = None
        direct = None
        try:
            SM.render(patterns(), evidence(), {}, None,
                      stamp[:4] + BREAK + stamp[4:], stamp_from=source)
        except STPT.StampTextRefused as exc:
            raised = exc
        try:
            SM.render(patterns(), evidence(), {}, None, stamp,
                      stamp_from=str(source)[:-4] + BREAK + ".log")
        except STPT.StampTextRefused as exc:
            direct = exc
        ok = check(raised is not None, "AC-STPT2 the real render refuses a "
                                       "doctored stamp")
        ok = check(raised is not None
                   and raised.piece == STPT.PIECE_STAMP
                   and BREAK in (raised.value or "")
                   and "U+FFFD" in raised.codepoints,
                   "AC-STPT2 the stamp refusal names the PIECE and the value "
                   "(%r/%r)" % (getattr(raised, "piece", None),
                                STPT.ascii_safe(getattr(raised, "value",
                                                        None)))) and ok
        ok = check(direct is not None
                   and direct.piece == STPT.PIECE_STAMP_FROM
                   and BREAK in (direct.value or ""),
                   "AC-STPT2 a doctored stamp_from refuses the same way, "
                   "naming %s (%r)" % (STPT.PIECE_STAMP_FROM,
                                       getattr(direct, "piece", None))) and ok

        code, out = call_main(["--check", "--out", broken_stamp_doc,
                               "--evidence", evidence()])
        ok = check(code == 4 and "FAIL stamp-text" in out
                   and STPT.PIECE_STAMP in out,
                   "AC-STPT2 the shipped tool refuses at exit 4 naming "
                   "stamp-text and the piece (rc=%r)" % (code,)) and ok
        code2, out2 = call_main(["--check", "--out", broken_source_doc,
                                 "--evidence", evidence()])
        ok = check(code2 == 4 and "FAIL stamp-text" in out2
                   and STPT.PIECE_STAMP_FROM in out2,
                   "AC-STPT2 the same refusal covers stamp_from (rc=%r)"
                   % (code2,)) and ok
        ok = check(read_bytes(DOC) == doc_before,
                   "AC-STPT2 the artifact keeps every byte it had") and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_stpt3():
    """A clean tree renders byte-identically to the committed document."""
    text = read_text(DOC)
    document = patterns()
    stamp, source = doc_faces()
    rendered = SM.render(document, evidence(), *SM.parse_evidence(evidence()),
                         stamp, stamp_from=source)
    ok = check(rendered == text,
               "AC-STPT3 a clean tree renders byte-identically to the "
               "committed doc (%d bytes)" % len(text.encode("utf-8")))
    code, out = call_main(["--check"])
    ok = check(code == 0,
               "AC-STPT3 --check keeps its today reading (rc=%r)"
               % (code,)) and ok
    return ok


def ac_stpt4():
    """Coverage is DERIVED from what the render prints, never listed."""
    stamp, source = doc_faces()
    fields = STPT.printed_strings(patterns(), stamp, source)
    ok = check(fields.get(STPT.PIECE_STAMP) == stamp,
               "AC-STPT4 the live stamp the render prints is in the derived "
               "set")
    ok = check(fields.get(STPT.PIECE_STAMP_FROM) == source,
               "AC-STPT4 the borrow the render prints is in the set (%r)"
               % (fields.get(STPT.PIECE_STAMP_FROM),)) and ok
    plain = STPT.printed_strings(patterns(), stamp)
    ok = check(STPT.PIECE_STAMP_FROM not in plain,
               "AC-STPT4 a render given no stamp_from claims no such piece "
               "(%r)" % (sorted(plain),)) and ok
    other = STPT.printed_strings(patterns(), "another-R1234-stamp",
                                 "qa/another-R1234-source.md")
    ok = check(other.get(STPT.PIECE_STAMP) == "another-R1234-stamp"
               and other.get(STPT.PIECE_STAMP_FROM)
               == "qa/another-R1234-source.md",
               "AC-STPT4 different values yield their own pieces, so nothing "
               "is canned (%r)" % (sorted(other),)) and ok
    source_text = read_text(MODULE)
    ok = check(stamp not in source_text and str(source) not in source_text,
               "AC-STPT4 no literal stamp or borrow lives in the module") and ok
    return ok


def ac_stpt5():
    """No source file, stamp source document or evidence file is rewritten."""
    stamp, source = doc_faces()
    faces = [PLR_MODULE, PATTERNS_PATH, evidence(), DOC]
    before = [digest(path) for path in faces]
    STPT.printed_strings(patterns(), stamp, source)
    STPT.reading(patterns(), stamp, source)
    ac_stpt4()
    after = [digest(path) for path in faces]
    ok = check(before == after,
               "AC-STPT5 the law, patterns, evidence and stamp source digests "
               "are unchanged")
    probe = os.path.join(SANDBOX, STPT.PROBE_EVIDENCE)
    ok = check(not os.path.exists(probe),
               "AC-STPT5 the coverage probe leaves no file behind") and ok
    source_text = read_text(MODULE)
    ok = check('"w"' not in source_text and "'w'" not in source_text
               and "os.replace" not in source_text
               and "os.remove" not in source_text
               and "shutil" not in source_text,
               "AC-STPT5 the module holds no write primitive") and ok
    return ok


def ac_stpt6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source_text = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source_text))
    ok = check(ascii_only, "AC-STPT6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "hashlib", "json", "os", "sys",
                           "patterns_label_readability"},
               "AC-STPT6 imports are stdlib plus the shipped law (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-STPT6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-STPT6 zero network imports") and ok
    ok = check(STPT.LABEL == "os-stamp-text-coverage",
               "AC-STPT6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-STPT6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-STPT6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("STAMP TEXT COVERAGE suite (R2511, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_stpt1(), ac_stpt2(), ac_stpt3(), ac_stpt4(), ac_stpt5(),
               ac_stpt6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())