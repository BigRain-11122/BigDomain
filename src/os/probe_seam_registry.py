"""probe_seam_registry - the guard seam set is DERIVED, and every probe is named.

MEASURED at R2511: wiring a fifth guard seam into src/sandbox/suite_matrix.py
::render cost TWO hand edits to probes that had already shipped, because each
probe enumerated the seam NAMES it quiets and the list it shipped with could
not see a seam that landed later. Each probe was repaired with a getattr read,
which fixes today and still leaves the next seam to be remembered per probe -
a probe written before a seam landed silently pays a second full composition,
and a probe that forgets the quieting inherits whatever verdict is in flight.

This face closes that gap with ONE reading and no second classifier:

  seam_names(module=None)
      the seam set is read off the SHIPPED render at CALL time: every global
      name the render own code object asks, kept only when that global really
      carries a callable guard. Nothing here holds a list of seam names - the
      module source does not spell any of them - so a seam added to the render
      appears here the moment it is asked, and a seam whose object stops
      carrying a guard leaves the set.
  owner_of(name, module)
      a seam own owner, read off the seam object itself, so the reading never
      guesses which probe is responsible for which seam.
  quiets(probe_text, seams)
      the seams a probe source QUIETS, derived by walking its AST for the seam
      tokens it names (attribute targets, string literals handed to getattr or
      setattr); a token that only appears inside a docstring is not a quieting.
  audit(root=None, module=None)
      every module in the root that quiets at least one seam is a PROBE and is
      answered COVERED, or MISSING-SEAM naming the first seam it fails to quiet
      and the probe file. A module that names no seam reads OUT-OF-SCOPE rather
      than being counted as clean, and a source that will not parse reads
      UNREADABLE rather than being skipped. A probe is responsible for every
      seam except its OWN: the owner answers its own seam through its own depth
      flag, so demanding it quiet itself would be an invented defect. A file
      whose name carries a round token is a one-off script of that round, not a
      shipped probe, and reads HISTORICAL - named in the counts rather than
      counted against the tree, the same rule the library dialect sweep uses.
      No probe is ever imported or run by this reading - it reads TEXT only,
      which is why a stale probe can be named without paying its composition.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PSMR5).

Criteria AC-PSMR1..AC-PSMR6 were pinned in state/queue/tech.md:551 as the
R2511 seed row BEFORE this code existed.

LIMIT, stated rather than buried: "quiets a seam" is decided by the seam token
appearing in the probe own syntax tree, so a probe that quietly forwards the
seam name through a shared helper in another module would read OUT-OF-SCOPE
rather than COVERED. That is a named, measurable gap and it is seeded rather
than hidden - it can only ever UNDER-report a stale probe, never invent one.

Pure ASCII, stdlib only, no clock, no network, writes nothing but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for (verdict SEAMS-COVERED)
  exit 2 = a probe is MISSING-SEAM or a source will not parse
  exit 3 = the root is missing or unreadable
  exit 5 = bad arguments
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import warnings

LABEL = "os-probe-seam-registry"
E_ARGS = "E_PSMR_ARGS"
E_NO_ROOT = "E_PSMR_NO_ROOT"
E_NO_RENDER = "E_PSMR_NO_RENDER"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-COVERED"
SEAMS_STALE = "SEAMS-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")


class SeamRegistryError(Exception):
    """The shipped render could not be read; the code travels with it."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def render_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    module = render_module() if module is None else module
    render = getattr(module, "render", None)
    code = getattr(render, "__code__", None)
    if code is None:
        raise SeamRegistryError(E_NO_RENDER,
                                "render carries no code object to read")
    names = []
    for name in code.co_names:
        value = getattr(module, name, None)
        if value is None:
            continue
        if not callable(getattr(value, "guard", None)):
            continue
        if name not in names:
            names.append(name)
    return names


def seam_owner(name, module=None):
    """Which module owns a seam, read off the seam object, never guessed."""
    module = render_module() if module is None else module
    value = getattr(module, name, None)
    return getattr(value, "__name__", None)


def _seam_tokens(text):
    """Every identifier and exact string literal a source names (AST walk)."""
    names = set()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.add(node.value)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    return names


def quiets(probe_text, seams):
    """The seams a probe source quiets, derived from its own syntax tree."""
    tokens = _seam_tokens(probe_text)
    if tokens is None:
        return None
    return [name for name in seams if name in tokens]


def audit(root=None, module=None):
    """Name every probe that quiets a seam, and every seam it forgets."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise SeamRegistryError(E_NO_ROOT, "not a directory: %s" % root)
    seams = seam_names(module)
    owners = dict((name, seam_owner(name, module)) for name in seams)
    rows = []
    counts = {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0, UNREADABLE: 0,
              HISTORICAL: 0}
    for entry in sorted(os.listdir(root)):
        if not entry.endswith(SUFFIX) or entry.startswith(TEST_PREFIX):
            continue
        path = os.path.join(root, entry)
        if not os.path.isfile(path):
            continue
        stem = entry[:-len(SUFFIX)]
        if ROUND_RE.search(stem):
            rows.append({"file": entry, "verdict": HISTORICAL,
                         "missing": [], "quieted": [], "required": []})
            counts[HISTORICAL] += 1
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            rows.append({"file": entry, "verdict": UNREADABLE,
                         "missing": [], "quieted": [], "required": []})
            counts[UNREADABLE] += 1
            continue
        quieted = quiets(text, seams)
        if quieted is None:
            rows.append({"file": entry, "verdict": UNREADABLE,
                         "missing": [], "quieted": [], "required": []})
            counts[UNREADABLE] += 1
            continue
        if not quieted:
            rows.append({"file": entry, "verdict": OUT_OF_SCOPE,
                         "missing": [], "quieted": [], "required": []})
            counts[OUT_OF_SCOPE] += 1
            continue
        me = entry[:-len(SUFFIX)]
        required = [name for name in seams if owners.get(name) != me]
        missing = [name for name in required if name not in quieted]
        verdict = MISSING_SEAM if missing else COVERED
        rows.append({"file": entry, "verdict": verdict,
                     "missing": missing, "quieted": quieted,
                     "required": required})
        counts[verdict] += 1
    stale = counts[MISSING_SEAM] + counts[UNREADABLE]
    return {"tool": LABEL, "verdict": SEAMS_STALE if stale else SEAMS_COVERED,
            "seams": [{"name": name, "owner": owners.get(name)}
                      for name in seams],
            "probes": rows, "counts": counts}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except SeamRegistryError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [], "counts": {COVERED: 0, MISSING_SEAM: 0,
                                         OUT_OF_SCOPE: 0, UNREADABLE: 0,
                                         HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the registry and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise SeamRegistryError(
            report["verdict"],
            ", ".join("%s:%s" % (row["file"],
                                 "/".join(row["missing"]) or row["verdict"])
                      for row in report["probes"]
                      if row["verdict"] in (MISSING_SEAM, UNREADABLE)))
    return report


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def render(report):
    lines = ["PROBE SEAM REGISTRY %s verdict=%s seams=%d probes=%d "
             "covered=%d missing=%d out_of_scope=%d unreadable=%d "
             "historical=%d"
             % (report["tool"], report["verdict"], len(report["seams"]),
                len(report["probes"]), report["counts"][COVERED],
                report["counts"][MISSING_SEAM],
                report["counts"][OUT_OF_SCOPE],
                report["counts"][UNREADABLE], report["counts"][HISTORICAL])]
    if report.get("refusal"):
        lines.append("  refused=%s detail=%s"
                     % (report["refusal"], report["detail"]))
    for seam in report["seams"]:
        lines.append("  SEAM %s owner=%s" % (seam["name"], seam["owner"]))
    for row in report["probes"]:
        if row["verdict"] in (OUT_OF_SCOPE, HISTORICAL):
            continue
        lines.append("  PROBE %s %s quieted=%d required=%d%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]),
                        (" missing=%s" % ",".join(row["missing"]))
                        if row["missing"] else ""))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=None, metavar="DIR",
                        help="the directory probed for seam-quieting modules")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])
    try:
        report = audit(args.root)
    except SeamRegistryError as exc:
        print("FAIL root: %s %s" % (exc.code, exc.detail))
        return 3
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(render(report))
    return 0 if report["verdict"] == SEAMS_COVERED else 2


def main_entry():
    argv = sys.argv
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 5


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - CLI guard
        sys.stderr.write("%s %s\n" % (E_ARGS, exc))
        sys.exit(5)