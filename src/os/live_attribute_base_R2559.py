"""Bounded live leg for the alias attribute-base face (R2559).

Reads the REAL src/os probe modules through the shipped reading, then measures
ONE fixture on BOTH readers so the closed gap is a fact rather than a claim.
Writes one utf-8 LF evidence file by a single writer (never a shell redirect).

Usage: python src/os/live_attribute_base_R2559.py [evidence_path]
"""

import glob
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as A  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_position as P  # noqa

ROOT = os.path.join(REPO, "src", "os")
DEFAULT_EVIDENCE = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-base-"
    "live-R2559.log")

LOCAL_FIXTURE = (
    'def probe(node):\n'
    '    B = node.value\n'
    '    D = {"a": {"b": ("x",)}}\n'
    '    if q:\n'
    '        KEY = B\n'
    '    else:\n'
    '        KEY = B\n'
    '    for n in D["a"][KEY]:\n'
    '        pass\n')

DOTTED_FIXTURE = (
    'import pkg.mod\n'
    'D = {"a": {"b": ("x",)}}\n'
    'B = pkg.mod.ATTR\n'
    'if q:\n'
    '    KEY = B\n'
    'else:\n'
    '    KEY = B\n'
    'for n in D["a"][KEY]:\n'
    '    pass\n')


def both(fixture, name, root=None):
    """The same name measured on this face and on the shipped position face."""
    rows = A.attribute_report(fixture, root)["loops"]
    mine = A.attribute_entry(name, fixture, rows[-1]["scope"],
                             rows[-1]["line"], root=root)
    prows = P.position_report(fixture, root)["loops"]
    theirs = P.position_entry(name, fixture, prows[-1]["scope"],
                              prows[-1]["line"], root=root)
    return mine, theirs


def dotted_world():
    """A private same-root world carrying pkg/mod.py so the hop has a file."""
    root = tempfile.mkdtemp(prefix="pnda-live-")
    package = os.path.join(root, "pkg")
    os.makedirs(package)
    with io.open(os.path.join(package, "mod.py"), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write('ATTR = "b"\n')
    return root


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    evidence = args[0] if args else DEFAULT_EVIDENCE
    lines = []
    lines.append("LABEL %s" % A.LABEL)
    lines.append("base_tool %s" % P.LABEL)
    modules = sorted(glob.glob(os.path.join(ROOT, "probe_seam_*.py")))[:8]
    lines.append("bounded_modules=%d" % len(modules))
    covered = 0
    loops_seen = 0
    resolved = 0
    named = 0
    for path in modules:
        name = os.path.basename(path)[:-3]
        report = A.reading(ROOT, name)
        row = None
        for probe in report.get("probes") or []:
            if probe.get("file", "").endswith(name + ".py"):
                row = probe
                break
        verdict = (row or {}).get("verdict") or report.get("verdict")
        if verdict != A.COVERED:
            continue
        covered += 1
        loops = (row or {}).get("attribute_loops") or []
        loops_seen += len(loops)
        resolved += sum(len(loop["attr_resolved"]) for loop in loops)
        named += sum(len(loop["attr_refused"]) for loop in loops)
        lines.append("  covered %s attribute_loops=%d attr_resolved=%d "
                     "attr_named=%d"
                     % (name, len(loops),
                        sum(len(loop["attr_resolved"]) for loop in loops),
                        sum(len(loop["attr_refused"]) for loop in loops)))
    lines.append("covered_probes=%d attribute_loops=%d attr_resolved=%d "
                 "attr_named=%d"
                 % (covered, loops_seen, resolved, named))
    mine, theirs = both(LOCAL_FIXTURE, "KEY")
    lines.append("local_fixture attr_face=%s reason=%s"
                 % (mine.get("attr_state"), mine.get("attr_reason")))
    lines.append("local_fixture position_face=%s reason=%s"
                 % (theirs.get("position_state"), theirs.get("position_reason")))
    mine2, theirs2 = both(DOTTED_FIXTURE, "KEY", dotted_world())
    lines.append("dotted_fixture attr_face=%s reason=%s value=%s"
                 % (mine2.get("attr_state"), mine2.get("attr_reason"),
                    mine2.get("attr_value")))
    lines.append("dotted_fixture position_face=%s reason=%s"
                 % (theirs2.get("position_state"), theirs2.get("position_reason")))
    body = "\n".join(lines) + "\n"
    with io.open(evidence, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    raw = open(evidence, "rb").read()
    sys.stdout.write(body)
    sys.stdout.write("BYTES %d crlf %d bom %s\n"
                     % (len(raw), raw.count(b"\r\n"),
                        raw[:3] == b"\xef\xbb\xbf"))
    ok = (mine.get("attr_reason") == "attr-base-local:node"
          and (theirs.get("position_reason") or "").startswith(
              "attr-not-imported:"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())