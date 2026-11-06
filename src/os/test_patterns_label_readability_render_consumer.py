"""AC-PLRC1..AC-PLRC6 suite for the render-path readability consumer (R2503).

Criteria were pinned in state/queue/tech.md:540 at R2502, the seed row, BEFORE
this code existed.

What this proves: the R2502 readability face protected only callers that chose
publish(); the shipped generator read suite_matrix_patterns.json with json.load
and interpolated every label straight into docs/sandbox-suite-matrix.md, so a
mis-encoded label still reached the CEO-visible artifact when the operator ran
`python src/sandbox/suite_matrix.py` directly. The render path now asks that
ONE gate at CALL time and refuses before composing a byte.

Every proof runs against the shipped modules (no stub of the law under test):
the gate is patched only to prove the CALL-time ask, and the doctorings happen
in a private copy of the real patterns file. The shipped patterns file is read
and hashed, never written.

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
import patterns_label_readability_render_consumer as PLRC  # noqa: E402
import matrix_stamp_provenance_line as MSPL  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "patterns_label_readability_render_consumer.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_EXPECT = ('"os-patterns-label-readability-render-consumer",')
WIRED_SUITE = ('"test_patterns_label_readability_render_consumer.py"), 6),')
MOJIBAKE = "\u04e1\ufffd\ufffd"


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


def doctored(path, key="title"):
    """A real copy of the shipped patterns file with ONE label mis-encoded."""
    document = patterns()
    document["labels"][key] = MOJIBAKE
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, ensure_ascii=False, indent=2))
    return path


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


def ac_plrc1():
    """The refusal IS the shipped gate, asked at CALL time, code carried."""
    real = PLR.gate

    def refusing(labels):
        return {"publishable": False, "code": "E_GATE_AS_ASKED",
                "label": "title", "codepoints": ["U+FFFD"],
                "refusal": None, "labels": []}

    PLR.gate = refusing
    try:
        raised = None
        try:
            SM.render(patterns(), evidence(), {}, None, "stamp")
        except PLRC.RenderRefused as exc:
            raised = exc
    finally:
        PLR.gate = real
    ok = check(raised is not None,
               "AC-PLRC1 a patched gate makes the real render refuse")
    ok = check(raised is not None and raised.code == "E_GATE_AS_ASKED",
               "AC-PLRC1 the refusal code is the gate own, carried verbatim "
               "(%r)" % (getattr(raised, "code", None),)) and ok
    ok = check(raised is not None and raised.label == "title",
               "AC-PLRC1 the refused label key travels with the refusal") and ok
    source = read_text(MODULE)
    ok = check("unicodedata" not in source and "def gate" not in source,
               "AC-PLRC1 the consumer carries no second classifier") and ok
    return ok


def ac_plrc2(world):
    """A suspect patterns file refuses the shipped tool and writes no byte."""
    copy = doctored(os.path.join(world, "patterns-suspect.json"))
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
    ok = check(code == 4, "AC-PLRC2 the shipped tool refuses at exit 4 "
                          "(got %d)" % code)
    ok = check("E_PLR_SUSPECT" in out and "title" in out,
               "AC-PLRC2 the refusal names the gate code and the label key") \
        and ok
    ok = check(read_bytes(target) == before,
               "AC-PLRC2 the target keeps every byte it had") and ok
    residue = [name for name in os.listdir(world)
               if name.endswith((".tmp", ".part", ".parity-stage"))]
    ok = check(residue == [],
               "AC-PLRC2 no residue is left beside the target (%r)"
               % residue) and ok
    ok = check(PLRC.main(["x", "--patterns", copy]) == 2,
               "AC-PLRC2 the consumer CLI refuses the same file at exit 2") \
        and ok
    return ok


def ac_plrc3():
    """A clean patterns file renders byte-identically to the shipped doc."""
    with open(DOC, encoding="utf-8") as handle:
        current = handle.read()
    base = patterns()
    stamp = SM.doc_stamp(current, base)
    status, run = SM.parse_evidence(evidence())
    fresh = SM.render(base, evidence(), status, run, stamp,
                      stamp_from=MSPL.recorded_source(current,
                                                      base["labels"]))
    ok = check(stamp is not None, "AC-PLRC3 the shipped doc carries a stamp")
    ok = check(fresh == current,
               "AC-PLRC3 a clean render is byte-identical to %s (%d bytes)"
               % (SM.rel(DOC), len(fresh.encode("utf-8")))) and ok
    ok = check(PLRC.reading(base["labels"])["publishable"] is True,
               "AC-PLRC3 the shipped labels read publishable") and ok
    return ok


def ac_plrc4(world):
    """--check keeps today semantics on a clean tree, refuses distinctly on one."""
    clean = call_main(["--check", "--out", DOC, "--evidence", evidence()])
    ok = check(clean[0] == 0 and "PASS check" in clean[1],
               "--check on the clean tree keeps its today reading "
               "(exit %d)" % clean[0])
    copy = doctored(os.path.join(world, "patterns-check.json"))
    real = SM.PATTERNS
    SM.PATTERNS = copy
    try:
        suspect = call_main(["--check", "--out", DOC, "--evidence", evidence()])
    finally:
        SM.PATTERNS = real
    ok = check(suspect[0] == 4,
               "AC-PLRC4 --check refuses a suspect file at exit 4 (got %d, "
               "not drift exit 2)" % suspect[0]) and ok
    ok = check("FAIL readability" in suspect[1]
               and "stale" not in suspect[1],
               "AC-PLRC4 the refusal reads as readability, never as drift") \
        and ok
    return ok


def ac_plrc5(world):
    """Labels are never rewritten and the patterns digest never moves."""
    before = digest(PATTERNS_PATH)
    before_labels = json.loads(json.dumps(patterns()["labels"]))
    ac_plrc2(world)
    ac_plrc3()
    after = digest(PATTERNS_PATH)
    ok = check(before == after,
               "AC-PLRC5 the shipped patterns digest is unchanged (%s)"
               % before[:16])
    ok = check(patterns()["labels"] == before_labels,
               "AC-PLRC5 every shipped label is still exactly as it was read") \
        and ok
    source = read_text(MODULE)
    ok = check('"w"' not in source and "'w'" not in source
               and "os.replace" not in source and "os.remove" not in source
               and "shutil" not in source,
               "AC-PLRC5 the consumer holds no write primitive") and ok
    return ok


def ac_plrc6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source))
    ok = check(ascii_only, "AC-PLRC6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "json", "sys",
                           "patterns_label_readability"},
               "AC-PLRC6 imports are stdlib plus the shipped gate (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PLRC6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PLRC6 zero network imports") and ok
    ok = check(PLRC.LABEL == "os-patterns-label-readability-render-consumer",
               "AC-PLRC6 the module carries its own reconcile label") and ok
    ok = check(WIRED_EXPECT in read_text(RUNNER)
               and WIRED_SUITE in read_text(RUNNER),
               "AC-PLRC6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PLRC6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PATTERNS RENDER CONSUMER suite (R2503, %d criteria)"
          % EXPECTED_CRITERIA)
    world = tempfile.mkdtemp(prefix="plrc-suite-")
    try:
        results = [ac_plrc1(), ac_plrc2(world), ac_plrc3(), ac_plrc4(world),
                   ac_plrc5(world), ac_plrc6()]
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