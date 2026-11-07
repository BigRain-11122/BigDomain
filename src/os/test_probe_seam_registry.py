"""AC-PSMR1..AC-PSMR6 suite for the probe seam registry face (R2513).

Criteria were pinned in state/queue/tech.md:551 at R2511 BEFORE this code
existed.

What this proves: src/sandbox/suite_matrix.py::render asks several guard seams
before it reads anything, and MEASURED at R2511 wiring one more seam cost two
hand edits to probes that had already shipped, because each probe enumerated
the seam names it quieted. This face derives the seam set from the shipped
render at CALL time and names every probe that has fallen behind rather than
running it.

Every proof runs against the shipped modules; the shipped render is patched
only to prove the CALL-time derivation, and every fixture lives in a private
temporary directory. No shipped source file is written.

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
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_registry as PSR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_registry.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-registry",'
WIRED_SUITE = '"test_probe_seam_registry.py"), 6),'
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


def guard_asks():
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


def call_main(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = PSR.main(["probe_seam_registry.py"] + argv)
    return code, buffer.getvalue()


def ac_psmr1():
    """The seam set is derived from the shipped render, never a list."""
    derived = PSR.seam_names(SM)
    independent = guard_asks()
    ok = check(derived == independent and len(derived) >= 2,
               "AC-PSMR1 the derived seams equal an independent AST reading of "
               "the render source (%r vs %r)" % (derived, independent))
    ok = check(all(callable(getattr(getattr(SM, name, None), "guard", None))
                   for name in derived),
               "AC-PSMR1 every derived name really carries a callable guard")
    real_render = SM.render
    SM.ZZ = _StandIn()

    def stand_in(*args, **kwargs):
        return SM.ZZ.guard()

    SM.render = stand_in
    try:
        moved = PSR.seam_names(SM)
    finally:
        SM.render = real_render
        del SM.ZZ
    ok = check(moved == ["ZZ"],
               "AC-PSMR1 patching the RENDER moves the set at CALL time (%r)"
               % (moved,)) and ok
    ok = check(PSR.seam_names(SM) == independent,
               "AC-PSMR1 restoring the render restores the set") and ok
    source_text = read_text(MODULE)
    ok = check(not [name for name in independent if name in source_text],
               "AC-PSMR1 no seam name is spelled in the module source") and ok
    return ok


def ac_psmr2():
    """A probe that quiets every seam is COVERED, and its bytes are unchanged."""
    faces = [os.path.join(BASE, name) for name in REAL_PROBES]
    before = [digest(path) for path in faces]
    report = PSR.audit(BASE, SM)
    after = [digest(path) for path in faces]
    rows = dict((row["file"], row) for row in report["probes"])
    ok = check(before == after,
               "AC-PSMR2 every shipped probe file keeps its bytes")
    covered = [name for name in REAL_PROBES
               if rows.get(name, {}).get("verdict") == PSR.COVERED]
    ok = check(len(covered) == len(REAL_PROBES),
               "AC-PSMR2 every shipped probe reads COVERED (%r)"
               % (report["counts"],)) and ok
    ok = check(all(set(rows[name]["required"]) <= set(rows[name]["quieted"])
                   for name in covered),
               "AC-PSMR2 a COVERED probe really quiets every seam it owes")
    own = dict((seam["owner"], seam["name"]) for seam in report["seams"])
    ok = check(all(own.get(name[:-3]) not in rows[name]["required"]
                   for name in covered if own.get(name[:-3])),
               "AC-PSMR2 a probe is not asked to quiet its OWN seam") and ok
    return ok


def ac_psmr3():
    """A probe that omits a seam is NAMED, and it is never run."""
    seams = PSR.seam_names(SM)
    missing_seam = seams[-1]
    kept = [name for name in seams if name != missing_seam]
    work = tempfile.mkdtemp(prefix="psmr-")
    try:
        stale = os.path.join(work, "stale_probe.py")
        with open(stale, "w", encoding="ascii", newline="\n") as handle:
            handle.write('raise SystemExit("must not run")\n'
                         'QUIETED = (%s,)\n'
                         % ", ".join('"%s"' % name for name in kept))
        plain = os.path.join(work, "plain_probe.py")
        with open(plain, "w", encoding="ascii", newline="\n") as handle:
            handle.write('VALUE = 1\n')
        raised = None
        sys.modules.pop("stale_probe", None)
        try:
            report = PSR.audit(work, SM)
        except Exception as exc:  # noqa: BLE001 - the probe must not run
            raised = exc
        rows = dict((row["file"], row) for row in report["probes"]) \
            if raised is None else {}
        row = rows.get("stale_probe.py", {})
        ok = check(raised is None and row.get("verdict") == PSR.MISSING_SEAM,
                   "AC-PSMR3 a stale probe reads MISSING-SEAM (%r)"
                   % (row.get("verdict"),))
        ok = check(row.get("missing") == [missing_seam],
                   "AC-PSMR3 the reading names the seam it forgets (%r)"
                   % (row.get("missing"),)) and ok
        ok = check("stale_probe" not in sys.modules,
                   "AC-PSMR3 the stale probe is named, never imported") and ok
        code, out = call_main(["--root", work])
        ok = check(code == 2 and PSR.MISSING_SEAM in out
                   and missing_seam in out and "stale_probe.py" in out,
                   "AC-PSMR3 the shipped tool refuses at exit 2 naming seam "
                   "and file (rc=%r)" % (code,)) and ok
        ok = check(report["verdict"] == PSR.SEAMS_STALE,
                   "AC-PSMR3 a stale probe makes the whole tree STALE") and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psmr4():
    """A module that takes no part is OUT-OF-SCOPE, never counted as clean."""
    work = tempfile.mkdtemp(prefix="psmr-")
    try:
        silent = os.path.join(work, "silent_module.py")
        with open(silent, "w", encoding="ascii", newline="\n") as handle:
            handle.write('"""A helper that never touches the render."""\n'
                         'VALUE = 1\n')
        report = PSR.audit(work, SM)
        rows = dict((row["file"], row) for row in report["probes"])
        ok = check(rows.get("silent_module.py", {}).get("verdict")
                   == PSR.OUT_OF_SCOPE,
                   "AC-PSMR4 a module that names no seam reads OUT-OF-SCOPE "
                   "(%r)" % (rows.get("silent_module.py", {}).get("verdict"),))
        ok = check(report["counts"][PSR.OUT_OF_SCOPE] == 1
                   and report["counts"][PSR.COVERED] == 0,
                   "AC-PSMR4 it is not counted as clean (%r)"
                   % (report["counts"],)) and ok
        ok = check(report["verdict"] == PSR.SEAMS_COVERED,
                   "AC-PSMR4 out-of-scope is a named bucket, not an alarm "
                   "(%r)" % (report["verdict"],)) and ok
        real = PSR.audit(BASE, SM)
        live = dict((row["file"], row["verdict"]) for row in real["probes"])
        ok = check(live.get("queue_head.py") == PSR.OUT_OF_SCOPE,
                   "AC-PSMR4 a real shipped module outside the protocol reads "
                   "OUT-OF-SCOPE (%r)" % (live.get("queue_head.py"),)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psmr5():
    """Read-only: every digest the reading touches is unchanged."""
    faces = [MODULE, RENDER_MODULE, PATTERNS_PATH]
    faces.extend(os.path.join(BASE, name) for name in REAL_PROBES)
    faces.extend(os.path.join(BASE, seam["owner"] + ".py")
                 for seam in PSR.audit(BASE, SM)["seams"])
    before = [digest(path) for path in faces]
    work = tempfile.mkdtemp(prefix="psmr-")
    try:
        with open(os.path.join(work, "silent_module.py"), "w",
                  encoding="ascii", newline="\n") as handle:
            handle.write("VALUE = 1\n")
        listing_before = sorted(os.listdir(work))
        PSR.audit(work, SM)
        PSR.reading(work, SM)
        listing_after = sorted(os.listdir(work))
        ok = check(listing_before == listing_after,
                   "AC-PSMR5 the probed root gains no file")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    after = [digest(path) for path in faces]
    ok = check(before == after and len(faces) >= 6,
               "AC-PSMR5 the render, the patterns file, every probe and every "
               "seam owner keep their bytes (%d files)" % len(faces)) and ok
    source_text = read_text(MODULE)
    ok = check('"w"' not in source_text and "'w'" not in source_text
               and "os.replace" not in source_text
               and "os.remove" not in source_text
               and "shutil" not in source_text
               and "subprocess" not in source_text,
               "AC-PSMR5 the module holds no write primitive") and ok
    return ok


def ac_psmr6():
    """Hygiene: ASCII source, stdlib only, no clock, own label, wired suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source_text = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source_text))
    ok = check(ascii_only, "AC-PSMR6 the module source is pure ASCII")
    ok = check(imports == {"argparse", "ast", "hashlib", "json", "os", "re",
                           "sys", "warnings"},
               "AC-PSMR6 imports are stdlib only (%r)" % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PSMR6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PSMR6 zero network imports") and ok
    ok = check(PSR.LABEL == "os-probe-seam-registry",
               "AC-PSMR6 the module carries its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-PSMR6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PSMR6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PROBE SEAM REGISTRY suite (R2513, %d criteria)"
          % EXPECTED_CRITERIA)
    results = [ac_psmr1(), ac_psmr2(), ac_psmr3(), ac_psmr4(), ac_psmr5(),
               ac_psmr6()]
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())