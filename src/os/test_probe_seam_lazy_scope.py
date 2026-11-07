"""AC-PSL1..AC-PSL6 suite for the seam lazy scope face (R2517).

Criteria were pinned in state/queue/tech.md:553 at R2515 BEFORE this code
existed.

What this proves: MEASURED at R2515 in the previous window own live leg, a
probe that imports its quieting helper INSIDE a function body reads
OUT-OF-SCOPE with zero quieted seams under probe_seam_forwarding_scope, which
follows only module-level imports. This face follows the quieting through
function-level imports too, on the same cycle-guarded same-root walk, so a
lazy forwarding probe is answered on its own row instead of being skipped and
a chained lazy helper can never invent a missing seam.

Every proof runs against the shipped modules; every fixture lives in a
private temporary directory and no shipped source file is written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import ast
import contextlib
import hashlib
import io
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

import probe_seam_forwarding_scope as PSF  # noqa: E402
import probe_seam_lazy_scope as PSL  # noqa: E402
import probe_seam_registry as PSR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_lazy_scope.py")
FORWARDING = os.path.join(BASE, "probe_seam_forwarding_scope.py")
REGISTRY = os.path.join(BASE, "probe_seam_registry.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-lazy-scope",'
WIRED_SUITE = '"test_probe_seam_lazy_scope.py"), 6),'
REAL_PROBES = ("artifact_disk_text_readability.py",
               "evidence_name_text_coverage.py",
               "stamp_text_coverage.py")


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


def lazy_probe_text(helper, body="VALUE = 1"):
    """A probe that imports its helper INSIDE a function body only."""
    return ("def run():\n"
            "    import %s\n"
            "    return %s.QUIETED\n"
            "\n"
            "%s\n" % (helper, helper, body))


def row_of(report, name):
    for row in report["probes"]:
        if row["file"] == name:
            return row
    return {}


def call_main(argv, module=PSL):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = module.main(["module.py"] + argv)
    return code, buffer.getvalue()


def render_asks():
    """The globals the render body asks `.guard(` on, read from its SOURCE."""
    tree = ast.parse(read_text(RENDER_MODULE))
    names = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "render":
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            target = inner.func
            if (isinstance(target, ast.Attribute) and target.attr == "guard"
                    and isinstance(target.value, ast.Name)
                    and target.value.id not in names):
                names.append(target.value.id)
    return names


def ac_psl1():
    """A function-level import is resolved from the tree, never a list."""
    seams = PSL.seam_names(SM)
    independent = render_asks()
    ok = check(seams == independent and len(seams) >= 2,
               "AC-PSL1 the derived seams equal an independent AST reading of "
               "the render source (%r vs %r)" % (seams, independent))
    ok = check(all(callable(getattr(getattr(SM, name, None), "guard", None))
                   for name in seams),
               "AC-PSL1 every derived name really carries a callable guard") \
        and ok
    source_text = read_text(MODULE)
    ok = check(not [name for name in independent if name in source_text],
               "AC-PSL1 no seam name is spelled in the module source") and ok
    got = PSL.imports_anywhere(lazy_probe_text("quiet_helper"))
    ok = check(got is not None and got[0] == ["quiet_helper"]
               and got[1] == [] and got[2] == ["quiet_helper"],
               "AC-PSL1 a function-body import is read AND named lazy "
               "(%r)" % (got,)) and ok
    work = tempfile.mkdtemp(prefix="psl-")
    other = tempfile.mkdtemp(prefix="psl-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "lazy_probe.py"),
                    lazy_probe_text("quiet_helper"))
        row = row_of(PSL.audit(work, SM), "lazy_probe.py")
        ok = check(row.get("verdict") == PSL.COVERED
                   and row.get("direct") == []
                   and row.get("helpers") == ["quiet_helper"],
                   "AC-PSL1 a probe that only lazily imports its helper is "
                   "followed (%r direct=%r helpers=%r)"
                   % (row.get("verdict"), row.get("direct"),
                      row.get("helpers"))) and ok
        ok = check(row.get("lazy_imports") == ["quiet_helper"],
                   "AC-PSL1 the row names the lazy import it took (%r)"
                   % (row.get("lazy_imports"),)) and ok
        write_ascii(os.path.join(other, "helper_zz.py"), helper_text(seams))
        write_ascii(os.path.join(other, "lazy_probe.py"),
                    lazy_probe_text("helper_zz"))
        row = row_of(PSL.audit(other, SM), "lazy_probe.py")
        ok = check(row.get("verdict") == PSL.COVERED
                   and row.get("helpers") == ["helper_zz"],
                   "AC-PSL1 a differently named lazy helper is followed too, "
                   "so no helper list is hard-coded (%r)"
                   % (row.get("helpers"),)) and ok
        write_ascii(os.path.join(work, "mentioned_only.py"),
                    'def run():\n    MENTION = "quiet_helper"\n'
                    '    return MENTION\n')
        row = row_of(PSL.audit(work, SM), "mentioned_only.py")
        ok = check(row.get("verdict") == PSL.OUT_OF_SCOPE,
                   "AC-PSL1 a bare string naming a helper is not an import "
                   "(%r)" % (row.get("verdict"),)) and ok
        write_ascii(os.path.join(work, "quiet_helper.py"),
                    helper_text(seams, omit=(seams[-1],)))
        after = row_of(PSL.audit(work, SM), "lazy_probe.py").get("verdict")
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        now = row_of(PSL.audit(work, SM), "lazy_probe.py").get("verdict")
        ok = check(after == PSL.MISSING_SEAM and now == PSL.COVERED,
                   "AC-PSL1 the lazy hop is re-read at CALL time: editing "
                   "ONLY the helper moves the same probe %r -> %r"
                   % (after, now)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(other, ignore_errors=True)
    return ok


def ac_psl2():
    """A probe that lazily imports every seam through one helper is COVERED."""
    seams = PSL.seam_names(SM)
    work = tempfile.mkdtemp(prefix="psl-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "lazy_probe.py"),
                    lazy_probe_text("quiet_helper",
                                    body="def unused():\n    return 0"))
        report = PSL.audit(work, SM)
        row = row_of(report, "lazy_probe.py")
        ok = check(row.get("verdict") == PSL.COVERED,
                   "AC-PSL2 a lazy forwarding probe reads COVERED (%r)"
                   % (row.get("verdict"),))
        ok = check(row.get("helpers") == ["quiet_helper"],
                   "AC-PSL2 the helper it was followed through is named (%r)"
                   % (row.get("helpers"),)) and ok
        ok = check(set(row.get("required", [])) <= set(row.get("quieted", []))
                   and len(row.get("required", [])) == len(seams),
                   "AC-PSL2 the lazily forwarded seams cover every seam it "
                   "owes (quieted=%d required=%d)"
                   % (len(row.get("quieted", [])),
                      len(row.get("required", [])))) and ok
        gap = row_of(PSF.audit(work, SM), "lazy_probe.py")
        ok = check(gap.get("verdict") == PSF.OUT_OF_SCOPE,
                   "AC-PSL2 the same fixture is OUT-OF-SCOPE to the "
                   "module-level face, so the closed gap is measured (%r)"
                   % (gap.get("verdict"),)) and ok
        code, out = call_main(["--root", work])
        ok = check(code == 0 and "quiet_helper" in out
                   and PSL.SEAMS_LAZY_COVERED in out,
                   "AC-PSL2 the shipped tool accepts it at exit 0 naming the "
                   "helper (rc=%r)" % (code,)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psl3():
    """A lazy helper that omits a seam makes the probe MISSING-SEAM, never run."""
    seams = PSL.seam_names(SM)
    missing_seam = seams[-1]
    work = tempfile.mkdtemp(prefix="psl-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"),
                    helper_text(seams, omit=(missing_seam,)))
        write_ascii(os.path.join(work, "lazy_probe.py"),
                    'raise SystemExit("must not run")\n'
                    + lazy_probe_text("quiet_helper"))
        raised = None
        sys.modules.pop("lazy_probe", None)
        report = None
        try:
            report = PSL.audit(work, SM)
        except Exception as exc:  # noqa: BLE001 - the probe must not run
            raised = exc
        row = row_of(report, "lazy_probe.py") if raised is None else {}
        ok = check(raised is None and row.get("verdict") == PSL.MISSING_SEAM,
                   "AC-PSL3 a lazy forwarding probe behind its helper reads "
                   "MISSING-SEAM (%r)" % (row.get("verdict"),))
        ok = check(row.get("missing") == [missing_seam],
                   "AC-PSL3 the reading names the seam the lazy helper omits "
                   "(%r)" % (row.get("missing"),)) and ok
        ok = check("lazy_probe" not in sys.modules,
                   "AC-PSL3 the probe that carries a module-level exit is "
                   "named, never imported") and ok
        code, out = call_main(["--root", work])
        ok = check(code == 2 and PSL.MISSING_SEAM in out
                   and missing_seam in out and "lazy_probe.py" in out,
                   "AC-PSL3 the shipped tool refuses at exit 2 naming seam "
                   "and file (rc=%r)" % (code,)) and ok
        ok = check(report["verdict"] == PSL.SEAMS_LAZY_STALE,
                   "AC-PSL3 a stale lazy probe makes the tree STALE") and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psl4():
    """A module whose lazy imports quiet nothing is OUT-OF-SCOPE, never clean."""
    seams = PSL.seam_names(SM)
    work = tempfile.mkdtemp(prefix="psl-")
    chain = tempfile.mkdtemp(prefix="psl-")
    try:
        write_ascii(os.path.join(work, "silent_helper.py"), "VALUE = 1\n")
        write_ascii(os.path.join(work, "silent_probe.py"),
                    lazy_probe_text("silent_helper", body="VALUE = 2"))
        write_ascii(os.path.join(work, "plain_module.py"), "VALUE = 3\n")
        report = PSL.audit(work, SM)
        rows = dict((row["file"], row) for row in report["probes"])
        ok = check(rows["silent_probe.py"]["verdict"] == PSL.OUT_OF_SCOPE
                   and rows["silent_helper.py"]["verdict"] == PSL.OUT_OF_SCOPE,
                   "AC-PSL4 lazily importing a helper that quiets nothing "
                   "stays OUT-OF-SCOPE (%r/%r)"
                   % (rows["silent_probe.py"]["verdict"],
                      rows["silent_helper.py"]["verdict"]))
        ok = check(report["counts"][PSL.OUT_OF_SCOPE] == 3
                   and report["counts"][PSL.COVERED] == 0,
                   "AC-PSL4 nothing in that tree is counted as clean (%r)"
                   % (report["counts"],)) and ok
        ok = check(report["verdict"] == PSL.SEAMS_LAZY_COVERED,
                   "AC-PSL4 out-of-scope is a named bucket, not an alarm "
                   "(%r)" % (report["verdict"],)) and ok
        write_ascii(os.path.join(chain, "deep_helper.py"), helper_text(seams))
        write_ascii(os.path.join(chain, "middle_helper.py"),
                    "%s\n%s\n"
                    % (helper_text(seams, omit=seams[1:]).strip(),
                       lazy_probe_text("deep_helper")))
        write_ascii(os.path.join(chain, "two_hop_probe.py"),
                    lazy_probe_text("middle_helper"))
        row = row_of(PSL.audit(chain, SM), "two_hop_probe.py")
        ok = check(row.get("verdict") == PSL.COVERED
                   and "middle_helper" in row.get("helpers", []),
                   "AC-PSL4 a lazily chained helper is followed too, so a "
                   "partial helper cannot INVENT a missing seam (%r "
                   "helpers=%r)"
                   % (row.get("verdict"), row.get("helpers"))) and ok
        write_ascii(os.path.join(chain, "loop_a.py"),
                    "%s\n%s" % (helper_text(seams).strip(),
                                lazy_probe_text("loop_b")))
        write_ascii(os.path.join(chain, "loop_b.py"),
                    lazy_probe_text("loop_a"))
        row = row_of(PSL.audit(chain, SM), "loop_a.py")
        ok = check(row.get("verdict") == PSL.COVERED,
                   "AC-PSL4 a lazy import cycle terminates and reads COVERED "
                   "(%r)" % (row.get("verdict"),)) and ok
        live = PSL.audit(BASE, SM)
        live_rows = dict((row["file"], row["verdict"])
                         for row in live["probes"])
        ok = check(live_rows.get("queue_head.py") == PSL.OUT_OF_SCOPE,
                   "AC-PSL4 a real shipped module outside the protocol reads "
                   "OUT-OF-SCOPE (%r)" % (live_rows.get("queue_head.py"),)) \
            and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(chain, ignore_errors=True)
    return ok


def ac_psl5():
    """Read-only: every digest the reading touches is unchanged."""
    faces = [MODULE, FORWARDING, REGISTRY, RENDER_MODULE, PATTERNS_PATH]
    faces.extend(os.path.join(BASE, name) for name in REAL_PROBES)
    faces.extend(os.path.join(BASE, seam["owner"] + ".py")
                 for seam in PSL.audit(BASE, SM)["seams"])
    before = [digest(path) for path in faces]
    work = tempfile.mkdtemp(prefix="psl-")
    try:
        write_ascii(os.path.join(work, "plain_module.py"), "VALUE = 1\n")
        listing_before = sorted(os.listdir(work))
        PSL.audit(work, SM)
        PSL.reading(work, SM)
        listing_after = sorted(os.listdir(work))
        ok = check(listing_before == listing_after,
                   "AC-PSL5 the probed root gains no file")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    after = [digest(path) for path in faces]
    ok = check(before == after and len(faces) >= 9,
               "AC-PSL5 the render, the patterns file, both readers, every "
               "probe and every seam owner keep their bytes (%d files)"
               % len(faces)) and ok
    source_text = read_text(MODULE)
    ok = check('"w"' not in source_text and "'w'" not in source_text
               and "os.replace" not in source_text
               and "os.remove" not in source_text
               and "shutil" not in source_text
               and "subprocess" not in source_text,
               "AC-PSL5 the module holds no write primitive") and ok
    return ok


def ac_psl6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source_text = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source_text))
    ok = check(ascii_only, "AC-PSL6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "ast", "hashlib", "json", "os", "re",
                           "sys", "warnings"},
               "AC-PSL6 module-level imports are stdlib only (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PSL6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PSL6 zero network imports") and ok
    ok = check(PSL.LABEL == "os-probe-seam-lazy-scope",
               "AC-PSL6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-PSL6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PSL6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PROBE SEAM LAZY SCOPE suite (R2517, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_psl1(), ac_psl2(), ac_psl3(), ac_psl4(), ac_psl5(),
               ac_psl6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())