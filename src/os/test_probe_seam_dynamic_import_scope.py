"""AC-PDI1..AC-PDI6 suite for the seam dynamic import scope face (R2519).

Criteria were pinned in state/queue/tech.md:555 at R2517 BEFORE this code
existed.

What this proves: MEASURED at R2517, a probe that builds its import at RUN
time reads OUT-OF-SCOPE with zero quieted seams under every shipped reader,
because they resolve import STATEMENTS off a syntax tree. This face follows a
COMPUTED import whose module name is a string constant visible in the probe
own tree - importlib.import_module, __import__, a from-import of
import_module and a module-level binding of any of those callables - on the
same cycle-guarded same-root walk, so such a probe is answered on its own row
instead of being skipped. A module name that is NOT a constant is never
guessed at.

Every proof runs against the shipped modules; every fixture lives in a
private temporary directory and no shipped source file is written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import contextlib
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import probe_seam_lazy_scope as PSL  # noqa: E402
import probe_seam_registry as PSR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_dynamic_import_scope.py")
LAZY = os.path.join(BASE, "probe_seam_lazy_scope.py")
FORWARDING = os.path.join(BASE, "probe_seam_forwarding_scope.py")
REGISTRY = os.path.join(BASE, "probe_seam_registry.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-dynamic-import-scope",'
WIRED_SUITE = '"test_probe_seam_dynamic_import_scope.py"), 6),'
REAL_PROBES = ("artifact_disk_text_readability.py",
               "evidence_name_text_coverage.py",
               "stamp_text_coverage.py")

ATTR_FIXTURE = ('import importlib\n'
                '\n'
                'def run():\n'
                '    return importlib.import_module("%s").QUIETED\n')


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


def write_ascii(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def helper_text(seams, omit=()):
    kept = [name for name in seams if name not in omit]
    return "QUIETED = (%s,)\n" % ", ".join('"%s"' % name for name in kept)


def row_of(report, name):
    for row in report["probes"]:
        if row["file"] == name:
            return row
    return {}


def call_main(argv, module=PDI):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = module.main(["module.py"] + argv)
    return code, buffer.getvalue()


def ac_pdi1():
    """The dynamic call and its literal name are read off the tree at CALL."""
    seams = PDI.seam_names(SM)
    source_text = read_text(MODULE)
    ok = check(not [name for name in seams if name in source_text],
               "AC-PDI1 no seam name is spelled in the module source")
    ok = check(not [name for name in ("pdi_dyn_helper", "pdi_other_helper")
                    if name in source_text],
               "AC-PDI1 no helper name is written into the module") and ok
    got = PDI.dynamic_imports(ATTR_FIXTURE % "quiet_helper")
    ok = check(got is not None and got["resolved"] == [
        (PDI.SHAPE_IMPORTLIB, "quiet_helper")] and got["unresolved"] == [],
        "AC-PDI1 an importlib attribute call with a literal name is resolved "
        "(%r)" % (got,)) and ok
    got = PDI.dynamic_imports('def run():\n'
                              '    return __import__("quiet_helper").QUIETED\n')
    ok = check(got is not None and got["resolved"] == [
        (PDI.SHAPE_BUILTIN, "quiet_helper")],
        "AC-PDI1 __import__ with a literal name is resolved (%r)"
        % (got,)) and ok
    got = PDI.dynamic_imports('from importlib import import_module as im\n'
                              'def run():\n    return im("quiet_helper")\n')
    ok = check(got is not None and got["resolved"] == [
        (PDI.SHAPE_FROM, "quiet_helper")],
        "AC-PDI1 a from-import alias is resolved at call time (%r)"
        % (got,)) and ok
    got = PDI.dynamic_imports('import importlib\n'
                              'loader = importlib.import_module\n'
                              'def run():\n    return loader("quiet_helper")\n')
    ok = check(got is not None and got["resolved"] == [
        (PDI.SHAPE_IMPORTLIB, "quiet_helper")],
        "AC-PDI1 a module-level binding of the callable is resolved (%r)"
        % (got,)) and ok
    got = PDI.dynamic_imports('import importlib\n'
                              'name = "quiet_helper"\n'
                              'def run():\n'
                              '    return importlib.import_module(name)\n')
    ok = check(got is not None and got["resolved"] == []
               and len(got["unresolved"]) == 1
               and got["unresolved"][0].startswith(PDI.SHAPE_IMPORTLIB),
               "AC-PDI1 a name that is not a literal constant is NOT "
               "resolved (%r)" % (got,)) and ok
    ok = check(PDI.dynamic_imports("def broken(:\n") is None,
               "AC-PDI1 a source that will not parse reads None") and ok
    work = tempfile.mkdtemp(prefix="pdi-")
    try:
        write_ascii(os.path.join(work, "pdi_dyn_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "dyn_probe.py"),
                    ATTR_FIXTURE % "pdi_dyn_helper")
        row = row_of(PDI.audit(work, SM), "dyn_probe.py")
        ok = check(row.get("verdict") == PDI.COVERED
                   and row.get("direct") == []
                   and row.get("helpers") == ["pdi_dyn_helper"],
                   "AC-PDI1 a probe whose only import is dynamic is followed "
                   "(%r direct=%r helpers=%r)"
                   % (row.get("verdict"), row.get("direct"),
                      row.get("helpers"))) and ok
        write_ascii(os.path.join(work, "pdi_dyn_helper.py"),
                    helper_text(seams, omit=(seams[-1],)))
        after = row_of(PDI.audit(work, SM), "dyn_probe.py").get("verdict")
        write_ascii(os.path.join(work, "pdi_dyn_helper.py"),
                    helper_text(seams))
        now = row_of(PDI.audit(work, SM), "dyn_probe.py").get("verdict")
        ok = check(after == PDI.MISSING_SEAM and now == PDI.COVERED,
                   "AC-PDI1 the hop is re-read at CALL time: editing ONLY the "
                   "helper moves the same probe %r -> %r" % (after, now)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_pdi2():
    """A literal dynamic import that quiets every seam reads COVERED."""
    seams = PDI.seam_names(SM)
    work = tempfile.mkdtemp(prefix="pdi-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "dyn_probe.py"),
                    ATTR_FIXTURE % "quiet_helper")
        report = PDI.audit(work, SM)
        row = row_of(report, "dyn_probe.py")
        ok = check(row.get("verdict") == PDI.COVERED,
                   "AC-PDI2 a dynamically forwarding probe reads COVERED (%r)"
                   % (row.get("verdict"),))
        ok = check(row.get("helpers") == ["quiet_helper"],
                   "AC-PDI2 the helper it was followed through is named (%r)"
                   % (row.get("helpers"),)) and ok
        ok = check(row.get("dynamic") == ["%s:quiet_helper"
                                         % PDI.SHAPE_IMPORTLIB],
                   "AC-PDI2 the dynamic shape it took is named on the row (%r)"
                   % (row.get("dynamic"),)) and ok
        ok = check(set(row.get("required", [])) <= set(row.get("quieted", []))
                   and len(row.get("required", [])) == len(seams),
                   "AC-PDI2 the dynamic seams cover every seam it owes "
                   "(quieted=%d required=%d)"
                   % (len(row.get("quieted", [])),
                      len(row.get("required", [])))) and ok
        gap = row_of(PSL.audit(work, SM), "dyn_probe.py")
        ok = check(gap.get("verdict") == PSL.OUT_OF_SCOPE,
                   "AC-PDI2 the same fixture is OUT-OF-SCOPE to the lazy "
                   "face, so the closed gap is measured (%r)"
                   % (gap.get("verdict"),)) and ok
        builtin_probe = ('def run():\n'
                         '    return __import__("quiet_helper").QUIETED\n')
        write_ascii(os.path.join(work, "dyn_probe.py"), builtin_probe)
        row = row_of(PDI.audit(work, SM), "dyn_probe.py")
        ok = check(row.get("verdict") == PDI.COVERED
                   and row.get("dynamic") == ["%s:quiet_helper"
                                              % PDI.SHAPE_BUILTIN],
                   "AC-PDI2 the __import__ shape is followed too (%r dynamic="
                   "%r)" % (row.get("verdict"), row.get("dynamic"))) and ok
        write_ascii(os.path.join(work, "dyn_probe.py"),
                    ATTR_FIXTURE % "quiet_helper")
        code, out = call_main(["--root", work])
        ok = check(code == 0 and "quiet_helper" in out
                   and PDI.SEAMS_DYNAMIC_COVERED in out,
                   "AC-PDI2 the shipped tool accepts it at exit 0 naming the "
                   "helper (rc=%r)" % (code,)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_pdi3():
    """A dynamic helper that omits a seam makes the probe MISSING-SEAM."""
    seams = PDI.seam_names(SM)
    missing_seam = seams[-1]
    work = tempfile.mkdtemp(prefix="pdi-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"),
                    helper_text(seams, omit=(missing_seam,)))
        write_ascii(os.path.join(work, "dyn_probe.py"),
                    'raise SystemExit("must not run")\n'
                    + ATTR_FIXTURE % "quiet_helper")
        raised = None
        report = None
        try:
            report = PDI.audit(work, SM)
        except Exception as exc:  # noqa: BLE001 - the probe must not run
            raised = exc
        row = row_of(report, "dyn_probe.py") if raised is None else {}
        ok = check(raised is None and row.get("verdict") == PDI.MISSING_SEAM,
                   "AC-PDI3 a dynamic forwarding probe behind its helper reads "
                   "MISSING-SEAM (%r)" % (row.get("verdict"),))
        ok = check(row.get("missing") == [missing_seam],
                   "AC-PDI3 the reading names the seam the helper omits (%r)"
                   % (row.get("missing"),)) and ok
        ok = check("dyn_probe" not in sys.modules,
                   "AC-PDI3 the probe that carries a module-level exit is "
                   "named, never imported") and ok
        code, out = call_main(["--root", work])
        ok = check(code == 2 and PDI.MISSING_SEAM in out
                   and missing_seam in out and "dyn_probe.py" in out,
                   "AC-PDI3 the shipped tool refuses at exit 2 naming seam "
                   "and file (rc=%r)" % (code,)) and ok
        ok = check(report["verdict"] == PDI.SEAMS_DYNAMIC_STALE,
                   "AC-PDI3 a stale dynamic probe makes the tree STALE") and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_pdi4():
    """A computed module name is named, never guessed at nor counted clean."""
    seams = PDI.seam_names(SM)
    work = tempfile.mkdtemp(prefix="pdi-")
    chain = tempfile.mkdtemp(prefix="pdi-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "computed_probe.py"),
                    'import importlib\n'
                    'NAME = "quiet" + "_helper"\n'
                    'def run():\n'
                    '    return importlib.import_module(NAME).QUIETED\n')
        write_ascii(os.path.join(work, "mentioned_only.py"),
                    'def run():\n'
                    '    MENTION = "quiet_helper"\n'
                    '    return MENTION\n')
        report = PDI.audit(work, SM)
        rows = dict((row["file"], row) for row in report["probes"])
        ok = check(rows["computed_probe.py"]["verdict"] == PDI.OUT_OF_SCOPE,
                   "AC-PDI4 a computed module name reads OUT-OF-SCOPE (%r)"
                   % (rows["computed_probe.py"]["verdict"],))
        ok = check(len(rows["computed_probe.py"]["unresolved"]) == 1
                   and rows["computed_probe.py"]["unresolved"][0].startswith(
                       PDI.SHAPE_IMPORTLIB + ":NAME"),
                   "AC-PDI4 the unresolved call is named on the row (%r)"
                   % (rows["computed_probe.py"]["unresolved"],)) and ok
        ok = check(rows["computed_probe.py"]["quieted"] == []
                   and rows["mentioned_only.py"]["verdict"]
                   == PDI.OUT_OF_SCOPE,
                   "AC-PDI4 neither the computed call nor a bare string is "
                   "counted as clean (%r/%r)"
                   % (rows["computed_probe.py"]["quieted"],
                      rows["mentioned_only.py"]["verdict"])) and ok
        ok = check(report["verdict"] == PDI.SEAMS_DYNAMIC_COVERED,
                   "AC-PDI4 out-of-scope is a named bucket, not an alarm (%r)"
                   % (report["verdict"],)) and ok
        write_ascii(os.path.join(chain, "deep_helper.py"), helper_text(seams))
        write_ascii(os.path.join(chain, "middle_helper.py"),
                    "%s\n%s\n"
                    % (helper_text(seams, omit=seams[1:]).strip(),
                       ATTR_FIXTURE % "deep_helper"))
        write_ascii(os.path.join(chain, "two_hop_probe.py"),
                    ATTR_FIXTURE % "middle_helper")
        row = row_of(PDI.audit(chain, SM), "two_hop_probe.py")
        ok = check(row.get("verdict") == PDI.COVERED
                   and "middle_helper" in row.get("helpers", []),
                   "AC-PDI4 a dynamically chained helper is followed, so a "
                   "partial helper cannot INVENT a missing seam (%r "
                   "helpers=%r)"
                   % (row.get("verdict"), row.get("helpers"))) and ok
        write_ascii(os.path.join(chain, "loop_a.py"),
                    "%s\n%s" % (helper_text(seams).strip(),
                                ATTR_FIXTURE % "loop_b"))
        write_ascii(os.path.join(chain, "loop_b.py"),
                    ATTR_FIXTURE % "loop_a")
        row = row_of(PDI.audit(chain, SM), "loop_a.py")
        ok = check(row.get("verdict") == PDI.COVERED,
                   "AC-PDI4 a dynamic import cycle terminates and reads "
                   "COVERED (%r)" % (row.get("verdict"),)) and ok
        live_rows = dict((row["file"], row["verdict"])
                         for row in PDI.audit(BASE, SM)["probes"])
        ok = check(live_rows.get("queue_head.py") == PDI.OUT_OF_SCOPE,
                   "AC-PDI4 a real shipped module outside the protocol reads "
                   "OUT-OF-SCOPE (%r)"
                   % (live_rows.get("queue_head.py"),)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(chain, ignore_errors=True)
    return ok


def ac_pdi5():
    """Read-only: every digest the reading touches is unchanged."""
    faces = [MODULE, LAZY, FORWARDING, REGISTRY, RENDER_MODULE, PATTERNS_PATH]
    faces.extend(os.path.join(BASE, name) for name in REAL_PROBES)
    faces.extend(os.path.join(BASE, seam["owner"] + ".py")
                 for seam in PDI.audit(BASE, SM)["seams"])
    before = [digest(path) for path in faces]
    work = tempfile.mkdtemp(prefix="pdi-")
    try:
        write_ascii(os.path.join(work, "plain_module.py"), "VALUE = 1\n")
        listing_before = sorted(os.listdir(work))
        PDI.audit(work, SM)
        PDI.reading(work, SM)
        listing_after = sorted(os.listdir(work))
        ok = check(listing_before == listing_after,
                   "AC-PDI5 the probed root gains no file")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    after = [digest(path) for path in faces]
    ok = check(before == after and len(faces) >= 10,
               "AC-PDI5 the render, the patterns file, all three readers, "
               "every probe and every seam owner keep their bytes (%d files)"
               % len(faces)) and ok
    source_text = read_text(MODULE)
    ok = check('"w"' not in source_text and "'w'" not in source_text
               and "os.replace" not in source_text
               and "os.remove" not in source_text
               and "shutil" not in source_text
               and "subprocess" not in source_text,
               "AC-PDI5 the module holds no write primitive") and ok
    return ok


def ac_pdi6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source_text = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source_text))
    ok = check(ascii_only, "AC-PDI6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "ast", "hashlib", "json", "os", "re",
                           "sys", "warnings"},
               "AC-PDI6 module-level imports are stdlib only (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PDI6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PDI6 zero network imports") and ok
    ok = check(PDI.LABEL == "os-probe-seam-dynamic-import-scope",
               "AC-PDI6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-PDI6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PDI6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PROBE SEAM DYNAMIC IMPORT SCOPE suite (R2519, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_pdi1(), ac_pdi2(), ac_pdi3(), ac_pdi4(), ac_pdi5(),
               ac_pdi6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())