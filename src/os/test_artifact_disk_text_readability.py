"""AC-ADTR1..AC-ADTR6 suite for the artifact disk-text readability face (R2507).

Criteria were pinned in state/queue/tech.md as the R2507 claim row BEFORE this
code existed.

What this proves: the R2502/R2503/R2505 gates read the PATTERNS DOCUMENT only,
while src/sandbox/suite_matrix.py::render also interpolates DISK-sourced text -
the registry labels and paths read live from reconcile_all.SUITES, and every
string billable_faces pulls out of each product config.json. Measured at R2505,
a registry label carrying U+FFFD rendered straight into the CEO-visible
artifact while the shipped gate still read publishable=True.

Every proof runs against the shipped modules; the shipped law is patched only
to prove the CALL-time ask, and every doctoring happens in memory or in a
private fixture. No shipped source file, config file or document is written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import artifact_disk_text_readability as ADTR  # noqa: E402
import patterns_label_readability as PLR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "artifact_disk_text_readability.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
REGISTRY_MODULE = os.path.join(SANDBOX, "reconcile_all.py")
CONFIG = os.path.join(SANDBOX, "ledger", "config.json")
WIRED_EXPECT = '"os-artifact-disk-text-readability",'
WIRED_SUITE = '"test_artifact_disk_text_readability.py"), 6),'
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


def doctored_patterns():
    """A private copy with one key the render never reads, carrying U+FFFD."""
    document = patterns()
    document["adtr_probe_unread_note"] = "broken" + BREAK
    return document


def doctored_registry():
    """The live registry with ONE label carrying a broken codepoint."""
    rows = list(SM.RA.SUITES)
    label, suite_path, crit = rows[0]
    rows[0] = (label + BREAK, suite_path, crit)
    return rows


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


def ac_adtr1():
    """The refusal IS the shipped law, asked at CALL time, code carried."""
    real = PLR.gate

    def refusing(fields):
        return {"publishable": False, "code": "E_GATE_AS_ASKED",
                "label": "registry[0].label", "codepoints": ["U+FFFD"],
                "refusal": None, "labels": []}

    PLR.gate = refusing
    try:
        raised = None
        try:
            ADTR.guard(patterns())
        except ADTR.DiskTextRefused as exc:
            raised = exc
    finally:
        PLR.gate = real
    ok = check(raised is not None,
               "AC-ADTR1 a patched gate makes the real reading refuse")
    ok = check(raised is not None and raised.code == "E_GATE_AS_ASKED",
               "AC-ADTR1 the refusal code is the gate own, carried verbatim "
               "(%r)" % (getattr(raised, "code", None),)) and ok
    ok = check(raised is not None
               and raised.source == ADTR.REGISTRY_SOURCE
               and raised.field == "registry[0].label",
               "AC-ADTR1 the refused SOURCE and field travel with the refusal "
               "(%r)" % (getattr(raised, "field", None),)) and ok
    source = read_text(MODULE)
    ok = check("unicodedata" not in source and "def gate" not in source,
               "AC-ADTR1 this face carries no second classifier") and ok
    return ok


def ac_adtr2():
    """A broken registry label refuses publication and writes no byte."""
    doc_before = read_bytes(DOC)
    real_suites = SM.RA.SUITES
    SM.RA.SUITES = doctored_registry()
    refused = None
    code = None
    try:
        try:
            SM.render(patterns(), evidence(), {}, None, "adtr-stamp")
        except ADTR.DiskTextRefused as exc:
            refused = exc
        code, out = call_main(["--evidence", evidence()])
    finally:
        SM.RA.SUITES = real_suites
    ok = check(refused is not None,
               "AC-ADTR2 the real render refuses a doctored registry label")
    ok = check(refused is not None
               and refused.source == ADTR.REGISTRY_SOURCE
               and refused.field.startswith("registry[0].label")
               and "U+FFFD" in refused.codepoints,
               "AC-ADTR2 the refusal names the SOURCE registry, the label and "
               "U+FFFD (%r/%r)"
               % (getattr(refused, "source", None),
                  getattr(refused, "field", None))) and ok
    ok = check(code == 4 and "FAIL disk-text" in out,
               "AC-ADTR2 the shipped tool refuses at exit 4 naming disk-text "
               "(rc=%r)" % (code,)) and ok
    ok = check(read_bytes(DOC) == doc_before,
               "AC-ADTR2 the artifact keeps every byte it had") and ok
    residue = [name for name in os.listdir(os.path.dirname(DOC))
               if "adtr" in name.lower() or name.endswith(".part")
               or name.endswith(".tmp")]
    ok = check(not residue,
               "AC-ADTR2 no residue beside the artifact (%r)" % (residue,)) and ok
    return ok


def ac_adtr3():
    """A clean tree renders byte-identically to the committed document."""
    text = read_text(DOC)
    document = patterns()
    stamp = SM.doc_stamp(text, document)
    recorded = SM.doc_evidence_face(text, document)
    if stamp is None or recorded is None:
        return check(False,
                     "AC-ADTR3 the committed doc carries a stamp and an "
                     "evidence path")
    rendered = SM.render(document, evidence(), *SM.parse_evidence(
        evidence()), stamp,
        stamp_from=SM.MSPL.recorded_source(text, document["labels"]))
    ok = check(rendered == text,
               "AC-ADTR3 a clean tree renders byte-identically to the "
               "committed doc (%d bytes)" % len(text.encode("utf-8")))
    code, out = call_main(["--check"])
    ok = check(code == 0,
               "AC-ADTR3 --check keeps its today reading (rc=%r)" % (code,)) \
        and ok
    return ok


def ac_adtr4():
    """Coverage is DERIVED from what the render reads off disk, never listed."""
    fields = ADTR.disk_strings(patterns())
    ok = check("registry[0].label" in fields
               and fields["registry[0].label"] == SM.RA.SUITES[0][0],
               "AC-ADTR4 the live registry label is in the derived set")
    ok = check(any(name.startswith("config.") for name in fields),
               "AC-ADTR4 the config-sourced strings are in the derived set") \
        and ok
    ok = check(len(fields) > 100,
               "AC-ADTR4 the set is measured over the whole tree (%d strings)"
               % len(fields)) and ok
    unread = ADTR.reading(doctored_patterns())
    ok = check(unread["publishable"] is True
               and not [name for name in unread["fields"]
                        if name.startswith("adtr_probe_unread_note")],
               "AC-ADTR4 a key the render never reads is not claimed") and ok
    source = read_text(MODULE)
    literal_registry_label = SM.RA.SUITES[0][0] in source
    literal_config_key = "active_day" in source
    ok = check(not literal_registry_label and not literal_config_key,
               "AC-ADTR4 no literal registry label or config key lives in the "
               "module") and ok
    return ok


def ac_adtr5():
    """No source file on disk is rewritten and every digest is unchanged."""
    faces = [REGISTRY_MODULE, PATTERNS_PATH, CONFIG]
    before = [digest(path) for path in faces]
    ADTR.disk_strings(patterns())
    ADTR.reading(patterns())
    ac_adtr4()
    after = [digest(path) for path in faces]
    ok = check(before == after,
               "AC-ADTR5 the registry, patterns and config digests are "
               "unchanged")
    probe = os.path.join(SANDBOX, ADTR.PROBE_EVIDENCE)
    ok = check(not os.path.exists(probe),
               "AC-ADTR5 the coverage probe leaves no file behind") and ok
    source = read_text(MODULE)
    ok = check('"w"' not in source and "'w'" not in source
               and "os.replace" not in source and "os.remove" not in source
               and "shutil" not in source,
               "AC-ADTR5 the module holds no write primitive") and ok
    return ok


def ac_adtr6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source))
    ok = check(ascii_only, "AC-ADTR6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "hashlib", "json", "os", "sys",
                           "patterns_label_readability"},
               "AC-ADTR6 imports are stdlib plus the shipped law (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-ADTR6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-ADTR6 zero network imports") and ok
    ok = check(ADTR.LABEL == "os-artifact-disk-text-readability",
               "AC-ADTR6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_EXPECT in runner and WIRED_SUITE in runner,
               "AC-ADTR6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-ADTR6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("ARTIFACT DISK TEXT READABILITY suite (R2507, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_adtr1(), ac_adtr2(), ac_adtr3(), ac_adtr4(), ac_adtr5(),
               ac_adtr6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())