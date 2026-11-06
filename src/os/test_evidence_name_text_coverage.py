"""AC-EVNM1..AC-EVNM6 suite for the evidence-name text coverage face (R2509).

Criteria were pinned in state/queue/tech.md:547 at R2507 BEFORE this code
existed.

What this proves: the R2507 disk-text gate derives everything
src/sandbox/suite_matrix.py::render reads off DISK, but its coverage probe
hands the render a CONSTANT evidence path, so the evidence file NAME the
artifact prints sits outside that derived set. Measured at R2507, a copy of the
real evidence named with U+FFFD rendered into the CEO-visible artifact while
the shipped reading still returned publishable=True.

Every proof runs against the shipped modules; the shipped law is patched only
to prove the CALL-time ask, and every doctoring happens in memory or in a
private temporary directory. No shipped source file, no evidence log and no
document is written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import evidence_name_text_coverage as EVNM  # noqa: E402
import patterns_label_readability as PLR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "evidence_name_text_coverage.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
PLR_MODULE = os.path.join(BASE, "patterns_label_readability.py")
WIRED_LABEL = '"os-evidence-name-text-coverage",'
WIRED_SUITE = '"test_evidence_name_text_coverage.py"), 6),'
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


def call_main(argv):
    """Run the shipped generator in-process and capture what it printed."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SM.main(["suite_matrix.py"] + argv)
    return code, buffer.getvalue()


def ac_evnm1():
    """The refusal IS the shipped law, asked at CALL time, code carried."""
    real = PLR.gate

    def refusing(fields):
        return {"publishable": False, "code": "E_GATE_AS_ASKED",
                "label": EVNM.PIECE_BASENAME, "codepoints": ["U+FFFD"],
                "refusal": None, "labels": []}

    PLR.gate = refusing
    try:
        raised = None
        try:
            EVNM.guard(evidence(), patterns())
        except EVNM.EvidenceNameRefused as exc:
            raised = exc
    finally:
        PLR.gate = real
    ok = check(raised is not None,
               "AC-EVNM1 a patched gate makes the real reading refuse")
    ok = check(raised is not None and raised.code == "E_GATE_AS_ASKED",
               "AC-EVNM1 the refusal code is the gate own, carried verbatim "
               "(%r)" % (getattr(raised, "code", None),)) and ok
    ok = check(raised is not None
               and raised.piece == EVNM.PIECE_BASENAME
               and raised.evidence == evidence(),
               "AC-EVNM1 the refused PIECE and the evidence path travel with "
               "the refusal (%r)" % (getattr(raised, "piece", None),)) and ok
    source = read_text(MODULE)
    ok = check("unicodedata" not in source and "def gate" not in source,
               "AC-EVNM1 this face carries no second classifier") and ok
    return ok


def ac_evnm2():
    """A broken evidence NAME refuses publication and writes no byte."""
    doc_before = read_bytes(DOC)
    doctored = os.path.join(tempfile.mkdtemp(prefix="evnm-"),
                            "reconcile-all-R2506-retr" + BREAK + "y.log")
    with open(doctored, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("RUNNER PASS (1/1 suites green, reconcile controls 1/1,"
                     " 0.1s)\n")
    refused = None
    try:
        try:
            SM.render(patterns(), doctored, {}, None, "evnm-stamp")
            code, out = call_main(["--evidence", doctored])
        except EVNM.EvidenceNameRefused as exc:
            refused = exc
            code, out = call_main(["--evidence", doctored])
    finally:
        pass
    ok = check(refused is not None,
               "AC-EVNM2 the real render refuses a doctored evidence name")
    ok = check(refused is not None
               and refused.piece.startswith("evidence.")
               and BREAK in (refused.name or "")
               and "U+FFFD" in refused.codepoints,
               "AC-EVNM2 the refusal names the PIECE and the offending name "
               "(%r/%r)" % (getattr(refused, "piece", None),
                            EVNM.ascii_safe(getattr(refused, "name", None)))) \
        and ok
    ok = check(code == 4 and "FAIL evidence-name" in out,
               "AC-EVNM2 the shipped tool refuses at exit 4 naming "
               "evidence-name (rc=%r)" % (code,)) and ok
    ok = check(read_bytes(DOC) == doc_before,
               "AC-EVNM2 the artifact keeps every byte it had") and ok
    residue = [name for name in os.listdir(os.path.dirname(DOC))
               if "evnm" in name.lower() or name.endswith(".part")
               or name.endswith(".tmp")]
    ok = check(not residue,
               "AC-EVNM2 no residue beside the artifact (%r)" % (residue,)) and ok
    for name in os.listdir(os.path.dirname(doctored)):
        os.remove(os.path.join(os.path.dirname(doctored), name))
    os.rmdir(os.path.dirname(doctored))
    return ok


def ac_evnm3():
    """A clean tree renders byte-identically to the committed document."""
    text = read_text(DOC)
    document = patterns()
    stamp = SM.doc_stamp(text, document)
    recorded = SM.doc_evidence_face(text, document)
    if stamp is None or recorded is None:
        return check(False,
                     "AC-EVNM3 the committed doc carries a stamp and an "
                     "evidence path")
    rendered = SM.render(document, evidence(), *SM.parse_evidence(evidence()),
                         stamp,
                         stamp_from=SM.MSPL.recorded_source(text,
                                                            document["labels"]))
    ok = check(rendered == text,
               "AC-EVNM3 a clean tree renders byte-identically to the "
               "committed doc (%d bytes)" % len(text.encode("utf-8")))
    code, out = call_main(["--check"])
    ok = check(code == 0,
               "AC-EVNM3 --check keeps its today reading (rc=%r)" % (code,)) \
        and ok
    return ok


def ac_evnm4():
    """Coverage is DERIVED from what the render prints, never listed."""
    live = evidence()
    fields = EVNM.evidence_strings(live, patterns())
    ok = check(fields.get(EVNM.PIECE_BASENAME) == os.path.basename(live),
               "AC-EVNM4 the live evidence basename is in the derived set")
    ok = check(fields.get(EVNM.PIECE_RELPATH) == SM.rel(live),
               "AC-EVNM4 the relative path the command line prints is in the "
               "set (%r)" % (fields.get(EVNM.PIECE_RELPATH),)) and ok
    other = os.path.join(BASE, "some-other-R1234-evidence.log")
    other_fields = EVNM.evidence_strings(other, patterns())
    ok = check(other_fields.get(EVNM.PIECE_BASENAME)
               == "some-other-R1234-evidence.log"
               and other_fields.get(EVNM.PIECE_ROUND_TAG) == "R1234",
               "AC-EVNM4 a different path yields its own pieces, so nothing "
               "is canned (%r)" % (sorted(other_fields),)) and ok
    plain = EVNM.evidence_strings("no-round-tag.log", patterns())
    ok = check(EVNM.PIECE_ROUND_TAG not in plain,
               "AC-EVNM4 a name carrying no round tag claims no separate "
               "piece (%r)" % (sorted(plain),)) and ok
    source = read_text(MODULE)
    ok = check(os.path.basename(live) not in source
               and SM.rel(live) not in source,
               "AC-EVNM4 no literal evidence name or path lives in the "
               "module") and ok
    return ok


def ac_evnm5():
    """No source file and no evidence file is rewritten; digests unchanged."""
    live = evidence()
    faces = [PLR_MODULE, PATTERNS_PATH, live]
    before = [digest(path) for path in faces]
    EVNM.evidence_strings(live, patterns())
    EVNM.reading(live, patterns())
    ac_evnm4()
    after = [digest(path) for path in faces]
    ok = check(before == after,
               "AC-EVNM5 the law, patterns and evidence digests are unchanged")
    probe = os.path.join(SANDBOX, EVNM.PROBE_EVIDENCE)
    ok = check(not os.path.exists(probe),
               "AC-EVNM5 the coverage probe leaves no file behind") and ok
    source = read_text(MODULE)
    ok = check('"w"' not in source and "'w'" not in source
               and "os.replace" not in source and "os.remove" not in source
               and "shutil" not in source,
               "AC-EVNM5 the module holds no write primitive") and ok
    return ok


def ac_evnm6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source))
    ok = check(ascii_only, "AC-EVNM6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "hashlib", "json", "os", "sys",
                           "patterns_label_readability"},
               "AC-EVNM6 imports are stdlib plus the shipped law (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-EVNM6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-EVNM6 zero network imports") and ok
    ok = check(EVNM.LABEL == "os-evidence-name-text-coverage",
               "AC-EVNM6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-EVNM6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-EVNM6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("EVIDENCE NAME TEXT COVERAGE suite (R2509, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_evnm1(), ac_evnm2(), ac_evnm3(), ac_evnm4(), ac_evnm5(),
               ac_evnm6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())