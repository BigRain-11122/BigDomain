"""probe_seam_lazy_scope - follow the quieting through function-level imports.

MEASURED at R2515 in that window own live leg (lazy fixture in
qa/probe-seam-forwarding-scope-live-R2515.log): a probe that imports its
quieting helper INSIDE a function body reads OUT-OF-SCOPE with zero quieted
seams, because probe_seam_forwarding_scope follows only MODULE-LEVEL import
statements. A lazy forwarding probe is therefore invisible again, and a stale
one is never named - the exact gap the forwarding face closed, moved one
level down.

This face closes that gap with ONE reading and no second seam classifier:

  imports_anywhere(text)
      every local module stem a source imports at ANY nesting level, read off
      its own syntax tree, split into the module-level stems and the ones that
      only appear inside a function or method body. A name that merely appears
      in a string or a comment is NOT an import.
  helper_quieted(path, seams, stack, memo)
      the seams a helper - and the helpers IT imports at any level in the same
      root - quiets, read off syntax trees with a cycle guard and a depth cap.
  forwarded(text, seams, root)
      direct seams a probe names, UNION the seams its imported helpers in the
      SAME root quiet, whether the import sits at module level or inside a
      function, so a lazy forwarding probe reads on its own row.
  audit(root=None, module=None)
      every module that quiets at least one seam directly or through local
      imports is a PROBE and reads COVERED, or MISSING-SEAM naming the first
      seam it fails to quiet and the probe file, with the helpers it was
      followed through and the lazy imports it took named on the row. A module
      that quiets nothing - including one whose function-level imports quiet
      nothing - reads OUT-OF-SCOPE rather than being counted as clean. A
      source or a helper that will not parse reads UNREADABLE rather than
      being skipped. A probe is responsible for every seam except its OWN, the
      same rule the registry uses. A file whose name carries a round token is
      HISTORICAL. No probe and no helper is ever imported or run: this reads
      TEXT only, which is why a stale probe is NAMED rather than paid for.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PSL5).

Criteria AC-PSL1..AC-PSL6 were pinned in state/queue/tech.md:553 at R2515 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only local modules in the SAME root are
followed, at most MAX_HOPS links with a cycle guard, and an import built at
RUN time (importlib, __import__ with a computed name, or a module resolved
from another directory) is not seen. Those shapes can UNDER-report a stale
probe but can no longer invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for (verdict SEAMS-LAZY-COVERED)
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

LABEL = "os-probe-seam-lazy-scope"
E_ARGS = "E_PSL_ARGS"
E_NO_ROOT = "E_PSL_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_LAZY_COVERED = "SEAMS-LAZY-COVERED"
SEAMS_LAZY_STALE = "SEAMS-LAZY-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
MAX_HOPS = 8

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")


class LazyScopeError(Exception):
    """The shipped render or the probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _registry():
    """The shipped seam reader, imported once (one reader, no copy)."""
    import probe_seam_registry
    return probe_seam_registry


def render_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    module = render_module() if module is None else module
    return _registry().seam_names(module)


def seam_owners(module=None):
    """Which module owns each seam, read off the seam object, never guessed."""
    module = render_module() if module is None else module
    registry = _registry()
    return dict((name, registry.seam_owner(name, module))
                for name in seam_names(module))


def _stems_of(node):
    """Local module stems one import statement names, in source order."""
    stems = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            stem = alias.name.split(".")[0]
            if stem not in stems:
                stems.append(stem)
    elif isinstance(node, ast.ImportFrom):
        if node.level or not node.module:
            return stems
        stem = node.module.split(".")[0]
        if stem not in stems:
            stems.append(stem)
    return stems


def imports_anywhere(text):
    """Every local module stem a source imports, at ANY nesting level.

    Returns (every, module_level, lazy) or None when the source will not parse.
    A stem imported at module level is never counted as lazy, even when it is
    imported again inside a function.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(text)
    except SyntaxError:
        return None
    top = []
    for node in tree.body:
        for stem in _stems_of(node):
            if stem not in top:
                top.append(stem)
    every = []
    for node in ast.walk(tree):
        for stem in _stems_of(node):
            if stem not in every:
                every.append(stem)
    lazy = [stem for stem in every if stem not in top]
    return every, top, lazy


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def helper_quieted(path, seams, stack, memo):
    """Seams one helper quiets, plus the helpers it imports at any level.

    Returns (quieted, helpers, unreadable, parsed, lazy). Cycles contribute
    nothing new to the union (the stack breaks them), a helper that will not
    parse is named rather than skipped, and results are memoised per audit.
    """
    key = os.path.abspath(path)
    if key in memo:
        return memo[key]
    if key in stack:
        return [], [], [], True, []
    stack.add(key)
    try:
        text = _read(path)
    except OSError:
        result = (None, [], [os.path.basename(path)], False, [])
        memo[key] = result
        stack.discard(key)
        return result
    registry = _registry()
    direct = registry.quiets(text, seams)
    got = imports_anywhere(text)
    if direct is None or got is None:
        result = (None, [], [os.path.basename(path)], False, [])
        memo[key] = result
        stack.discard(key)
        return result
    every, _, lazy = got
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(lazy)
    if len(stack) <= MAX_HOPS:
        for stem in every:
            sub = os.path.join(os.path.dirname(path), stem + SUFFIX)
            if not os.path.isfile(sub):
                continue
            sub_q, sub_h, sub_bad, sub_ok, sub_lazy = helper_quieted(
                sub, seams, stack, memo)
            if not sub_ok:
                unreadable.extend(sub_bad)
                continue
            if sub_q:
                helpers.append(os.path.basename(sub)[:-len(SUFFIX)])
                for name in sub_q:
                    if name not in quieted:
                        quieted.append(name)
                for name in sub_lazy:
                    if name not in lazy_seen:
                        lazy_seen.append(name)
    result = (quieted, helpers, unreadable, True, lazy_seen)
    memo[key] = result
    stack.discard(key)
    return result


def forwarded(text, seams, root):
    """The seams a probe really quiets: its own names plus local imports."""
    registry = _registry()
    direct = registry.quiets(text, seams)
    if direct is None:
        return None
    got = imports_anywhere(text)
    if got is None:
        return None
    every, _, lazy = got
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(lazy)
    stack = set()
    memo = {}
    for stem in every:
        path = os.path.join(root, stem + SUFFIX)
        if not os.path.isfile(path):
            continue
        scope, sub_h, sub_bad, parsed, sub_lazy = helper_quieted(
            path, seams, stack, memo)
        if not parsed:
            unreadable.extend(sub_bad)
            continue
        if scope:
            helpers.append(os.path.basename(path)[:-len(SUFFIX)])
            for name in scope:
                if name not in quieted:
                    quieted.append(name)
            for name in sub_lazy:
                if name not in lazy_seen:
                    lazy_seen.append(name)
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, directly or through local imports."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise LazyScopeError(E_NO_ROOT, "not a directory: %s" % root)
    seams = seam_names(module)
    owners = seam_owners(module)
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
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [], "lazy_imports": [],
                         "unreadable_helpers": []})
            counts[HISTORICAL] += 1
            continue
        try:
            text = _read(path)
        except OSError:
            rows.append({"file": entry, "verdict": UNREADABLE,
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [], "lazy_imports": [],
                         "unreadable_helpers": []})
            counts[UNREADABLE] += 1
            continue
        scope = forwarded(text, seams, root)
        if scope is None or scope["unreadable"]:
            rows.append({"file": entry, "verdict": UNREADABLE,
                         "missing": [], "quieted": [],
                         "required": [], "helpers": [],
                         "direct": [],
                         "lazy_imports":
                             scope["lazy_imports"] if scope else [],
                         "unreadable_helpers":
                             scope["unreadable"] if scope else []})
            counts[UNREADABLE] += 1
            continue
        if not scope["quieted"]:
            rows.append({"file": entry, "verdict": OUT_OF_SCOPE,
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [],
                         "lazy_imports": scope["lazy_imports"],
                         "unreadable_helpers": []})
            counts[OUT_OF_SCOPE] += 1
            continue
        me = stem
        required = [name for name in seams if owners.get(name) != me]
        missing = [name for name in required if name not in scope["quieted"]]
        verdict = MISSING_SEAM if missing else COVERED
        rows.append({"file": entry, "verdict": verdict,
                     "missing": missing, "quieted": scope["quieted"],
                     "required": required, "helpers": scope["helpers"],
                     "direct": scope["direct"],
                     "lazy_imports": scope["lazy_imports"],
                     "unreadable_helpers": []})
        counts[verdict] += 1
    stale = counts[MISSING_SEAM] + counts[UNREADABLE]
    return {"tool": LABEL,
            "verdict": SEAMS_LAZY_STALE if stale else SEAMS_LAZY_COVERED,
            "seams": [{"name": name, "owner": owners.get(name)}
                      for name in seams],
            "probes": rows, "counts": counts}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except LazyScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_LAZY_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_LAZY_COVERED:
        raise LazyScopeError(
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
    lines = ["PROBE SEAM LAZY SCOPE %s verdict=%s seams=%d probes=%d "
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
        lines.append("  PROBE %s %s quieted=%d required=%d direct=%d"
                     " helpers=%s lazy=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["lazy_imports"]) or "-",
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
    except LazyScopeError as exc:
        print("FAIL root: %s %s" % (exc.code, exc.detail))
        return 3
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(render(report))
    return 0 if report["verdict"] == SEAMS_LAZY_COVERED else 2


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