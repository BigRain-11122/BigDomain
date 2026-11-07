"""AC-PSF1..AC-PSF6 suite for the seam forwarding scope face (R2515).

Criteria were pinned in state/queue/tech.md:552 at R2513 BEFORE this code
existed.

What this proves: MEASURED at R2513, a probe that quiets the render guard
seams through a shared helper module names no seam itself, so
probe_seam_registry reads it OUT-OF-SCOPE while the helper reads COVERED and
the forwarding shape is invisible. This face follows the quieting through
the local modules the probe imports at call time (cycle-guarded, depth
capped), so a forwarding probe is answered on its own row instead of being
skipped and a chained helper can never invent a missing seam.

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
import probe_seam_registry as PSR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_forwarding_scope.py")
REGISTRY = os.path.join(BASE, "probe_seam_registry.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-forwarding-scope",'
WIRED_SUITE = '"test_probe_seam_forwarding_scope.py"), 6),'
REAL_PROBES = ("artifact_disk_text_readability.py",
               "evidence_name_text_coverage.py",
               "stamp_text_coverage.py")


class _StandIn(object):
    """A seam stand-in that is asked the same way the real one is."""

    def guard(self, *args, **kwargs):
        return None


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


def call_main(argv, module=PSF):
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


def ac_psf1():
    """The hop is derived from imports and helper trees, never a list."""
    seams = PSF.seam_names(SM)
    independent = render_asks()
    ok = check(seams == independent and len(seams) >= 2,
               "AC-PSF1 the derived seams equal an independent AST reading of "
               "the render source (%r vs %r)" % (seams, independent))
    ok = check(all(callable(getattr(getattr(SM, name, None), "guard", None))
                   for name in seams),
               "AC-PSF1 every derived name really carries a callable guard") \
        and ok
    source_text = read_text(MODULE)
    ok = check(not [name for name in independent if name in source_text],
               "AC-PSF1 no seam name is spelled in the module source") and ok
    work = tempfile.mkdtemp(prefix="psf-")
    other = tempfile.mkdtemp(prefix="psf-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "forwarding_probe.py"),
                    "import quiet_helper\nVALUE = 1\n")
        row = row_of(PSF.audit(work, SM), "forwarding_probe.py")
        ok = check(row.get("verdict") == PSF.COVERED
                   and row.get("direct") == []
                   and row.get("helpers") == ["quiet_helper"],
                   "AC-PSF1 a probe that only imports its helper is followed "
                   "(%r direct=%r helpers=%r)"
                   % (row.get("verdict"), row.get("direct"),
                      row.get("helpers"))) and ok
        write_ascii(os.path.join(other, "quiet_helper_zz.py"), helper_text(seams))
        write_ascii(os.path.join(other, "forwarding_probe.py"),
                    "from quiet_helper_zz import QUIETED\nVALUE = 1\n")
        row = row_of(PSF.audit(other, SM), "forwarding_probe.py")
        ok = check(row.get("verdict") == PSF.COVERED
                   and row.get("helpers") == ["quiet_helper_zz"],
                   "AC-PSF1 a differently named helper is followed too, so no "
                   "helper list is hard-coded (%r)"
                   % (row.get("helpers"),)) and ok
        write_ascii(os.path.join(work, "mentioned_only.py"),
                    'MENTION = "quiet_helper"\nVALUE = 1\n')
        row = row_of(PSF.audit(work, SM), "mentioned_only.py")
        ok = check(row.get("verdict") == PSF.OUT_OF_SCOPE,
                   "AC-PSF1 a bare string naming a helper is not an import "
                   "(%r)" % (row.get("verdict"),)) and ok
        write_ascii(os.path.join(work, "quiet_helper.py"),
                    helper_text(seams, omit=(seams[-1],)))
        row = row_of(PSF.audit(work, SM), "forwarding_probe.py")
        after = row.get("verdict")
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        row = row_of(PSF.audit(work, SM), "forwarding_probe.py")
        ok = check(after == PSF.MISSING_SEAM
                   and row.get("verdict") == PSF.COVERED,
                   "AC-PSF1 the hop is re-read at CALL time: editing ONLY the "
                   "helper moves the same probe %r -> %r"
                   % (after, row.get("verdict"))) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(other, ignore_errors=True)
    return ok


def ac_psf2():
    """A probe forwarding every seam through one helper reads COVERED."""
    seams = PSF.seam_names(SM)
    work = tempfile.mkdtemp(prefix="psf-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"), helper_text(seams))
        write_ascii(os.path.join(work, "forwarding_probe.py"),
                    "import quiet_helper\n"
                    "def noop():\n    return quiet_helper.QUIETED\n")
        report = PSF.audit(work, SM)
        row = row_of(report, "forwarding_probe.py")
        ok = check(row.get("verdict") == PSF.COVERED,
                   "AC-PSF2 a forwarding probe reads COVERED (%r)"
                   % (row.get("verdict"),))
        ok = check(row.get("helpers") == ["quiet_helper"],
                   "AC-PSF2 the helper it was followed through is named (%r)"
                   % (row.get("helpers"),)) and ok
        ok = check(set(row.get("required", [])) <= set(row.get("quieted", []))
                   and len(row.get("required", [])) == len(seams) - 0,
                   "AC-PSF2 the forwarded seams cover every seam it owes "
                   "(quieted=%d required=%d)"
                   % (len(row.get("quieted", [])),
                      len(row.get("required", [])))) and ok
        code, out = call_main(["--root", work])
        ok = check(code == 0 and "quiet_helper" in out
                   and PSF.SEAMS_FORWARDED in out,
                   "AC-PSF2 the shipped tool accepts it at exit 0 naming the "
                   "helper (rc=%r)" % (code,)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psf3():
    """A helper that omits a seam makes the probe MISSING-SEAM, never run."""
    seams = PSF.seam_names(SM)
    missing_seam = seams[-1]
    work = tempfile.mkdtemp(prefix="psf-")
    try:
        write_ascii(os.path.join(work, "quiet_helper.py"),
                    helper_text(seams, omit=(missing_seam,)))
        write_ascii(os.path.join(work, "forwarding_probe.py"),
                    'raise SystemExit("must not run")\n'
                    "import quiet_helper\nVALUE = 1\n")
        raised = None
        sys.modules.pop("forwarding_probe", None)
        try:
            report = PSF.audit(work, SM)
        except Exception as exc:  # noqa: BLE001 - the probe must not run
            raised = exc
        row = row_of(report, "forwarding_probe.py") if raised is None else {}
        ok = check(raised is None and row.get("verdict") == PSF.MISSING_SEAM,
                   "AC-PSF3 a forwarding probe behind its helper reads "
                   "MISSING-SEAM (%r)" % (row.get("verdict"),))
        ok = check(row.get("missing") == [missing_seam],
                   "AC-PSF3 the reading names the seam the helper omits (%r)"
                   % (row.get("missing"),)) and ok
        ok = check("forwarding_probe" not in sys.modules,
                   "AC-PSF3 the probe that carries a module-level exit is "
                   "named, never imported") and ok
        code, out = call_main(["--root", work])
        ok = check(code == 2 and PSF.MISSING_SEAM in out
                   and missing_seam in out and "forwarding_probe.py" in out,
                   "AC-PSF3 the shipped tool refuses at exit 2 naming seam "
                   "and file (rc=%r)" % (code,)) and ok
        ok = check(report["verdict"] == PSF.SEAMS_FORWARD_STALE,
                   "AC-PSF3 a stale forwarding probe makes the tree STALE") \
            and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psf4():
    """A module whose imports quiet nothing is OUT-OF-SCOPE, never clean."""
    seams = PSF.seam_names(SM)
    work = tempfile.mkdtemp(prefix="psf-")
    chain = tempfile.mkdtemp(prefix="psf-")
    try:
        write_ascii(os.path.join(work, "silent_helper.py"), "VALUE = 1\n")
        write_ascii(os.path.join(work, "silent_probe.py"),
                    "import silent_helper\nVALUE = 2\n")
        write_ascii(os.path.join(work, "plain_module.py"), "VALUE = 3\n")
        report = PSF.audit(work, SM)
        rows = dict((row["file"], row) for row in report["probes"])
        ok = check(rows["silent_probe.py"]["verdict"] == PSF.OUT_OF_SCOPE
                   and rows["silent_helper.py"]["verdict"] == PSF.OUT_OF_SCOPE,
                   "AC-PSF4 importing a helper that quiets nothing stays "
                   "OUT-OF-SCOPE (%r/%r)"
                   % (rows["silent_probe.py"]["verdict"],
                      rows["silent_helper.py"]["verdict"]))
        ok = check(report["counts"][PSF.OUT_OF_SCOPE] == 3
                   and report["counts"][PSF.COVERED] == 0,
                   "AC-PSF4 nothing in that tree is counted as clean (%r)"
                   % (report["counts"],)) and ok
        ok = check(report["verdict"] == PSF.SEAMS_FORWARDED,
                   "AC-PSF4 out-of-scope is a named bucket, not an alarm "
                   "(%r)" % (report["verdict"],)) and ok
        write_ascii(os.path.join(chain, "deep_helper.py"), helper_text(seams))
        write_ascii(os.path.join(chain, "middle_helper.py"),
                    "import deep_helper\n%s\nVALUE = 1\n"
                    % helper_text(seams, omit=seams[1:]).strip())
        write_ascii(os.path.join(chain, "two_hop_probe.py"),
                    "import middle_helper\nVALUE = 2\n")
        row = row_of(PSF.audit(chain, SM), "two_hop_probe.py")
        ok = check(row.get("verdict") == PSF.COVERED
                   and "middle_helper" in row.get("helpers", []),
                   "AC-PSF4 a chained helper is followed too, so a partial "
                   "helper cannot INVENT a missing seam (%r helpers=%r)"
                   % (row.get("verdict"), row.get("helpers"))) and ok
        write_ascii(os.path.join(chain, "loop_a.py"),
                    "%s\nimport loop_b\n" % helper_text(seams))
        write_ascii(os.path.join(chain, "loop_b.py"), "import loop_a\nVALUE = 1\n")
        row = row_of(PSF.audit(chain, SM), "loop_a.py")
        ok = check(row.get("verdict") == PSF.COVERED,
                   "AC-PSF4 an import cycle terminates and reads COVERED "
                   "(%r)" % (row.get("verdict"),)) and ok
        live = PSF.audit(BASE, SM)
        live_rows = dict((row["file"], row["verdict"])
                         for row in live["probes"])
        ok = check(live_rows.get("queue_head.py") == PSF.OUT_OF_SCOPE,
                   "AC-PSF4 a real shipped module outside the protocol reads "
                   "OUT-OF-SCOPE (%r)" % (live_rows.get("queue_head.py"),)) \
            and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(chain, ignore_errors=True)
    return ok


def ac_psf5():
    """Read-only: every digest the reading touches is unchanged."""
    faces = [MODULE, REGISTRY, RENDER_MODULE, PATTERNS_PATH]
    faces.extend(os.path.join(BASE, name) for name in REAL_PROBES)
    faces.extend(os.path.join(BASE, seam["owner"] + ".py")
                 for seam in PSF.audit(BASE, SM)["seams"])
    before = [digest(path) for path in faces]
    work = tempfile.mkdtemp(prefix="psf-")
    try:
        write_ascii(os.path.join(work, "plain_module.py"), "VALUE = 1\n")
        listing_before = sorted(os.listdir(work))
        PSF.audit(work, SM)
        PSF.reading(work, SM)
        listing_after = sorted(os.listdir(work))
        ok = check(listing_before == listing_after,
                   "AC-PSF5 the probed root gains no file")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    after = [digest(path) for path in faces]
    ok = check(before == after and len(faces) >= 8,
               "AC-PSF5 the render, the patterns file, the registry, every "
               "probe and every seam owner keep their bytes (%d files)"
               % len(faces)) and ok
    source_text = read_text(MODULE)
    ok = check('"w"' not in source_text and "'w'" not in source_text
               and "os.replace" not in source_text
               and "os.remove" not in source_text
               and "shutil" not in source_text
               and "subprocess" not in source_text,
               "AC-PSF5 the module holds no write primitive") and ok
    return ok


def ac_psf6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source_text = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source_text))
    ok = check(ascii_only, "AC-PSF6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "ast", "hashlib", "json", "os", "re",
                           "sys", "warnings"},
               "AC-PSF6 module-level imports are stdlib only (%r)"
               % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PSF6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PSF6 zero network imports") and ok
    ok = check(PSF.LABEL == "os-probe-seam-forwarding-scope",
               "AC-PSF6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-PSF6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PSF6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PROBE SEAM FORWARDING SCOPE suite (R2515, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_psf1(), ac_psf2(), ac_psf3(), ac_psf4(), ac_psf5(),
               ac_psf6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())