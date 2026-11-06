"""artifact_disk_text_readability - the artifact's DISK-sourced text is readable too.

MEASURED at R2505 while wiring the non-label gate: patterns_label_readability
.gate covers every string src/sandbox/suite_matrix.py::render takes from the
PATTERNS DOCUMENT, while the same render also interpolates text that comes from
DISK:

  * the registry's own suite labels and suite paths, read live from
    reconcile_all.SUITES (imported, never copied), and
  * every string billable_faces pulls out of each product config.json - the
    node's keys, its list items, or the scalar itself.

A registry label carrying U+FFFD rendered straight into
docs/sandbox-suite-matrix.md while the shipped gate still read
publishable=True (qa/patterns-non-label-live-R2505.log), so the CEO-visible
artifact could still hold unreadable text that lives outside the patterns file.

This face closes that gap without growing a second classifier:

  disk_strings(patterns)
      the set of DISK-sourced strings the render actually reads, derived by
      composing the real render once against recording wrappers: the registry
      rows are handed to the render as recording strings addressed
      "registry[<index>].label" / "registry[<index>].path", and face_node is
      asked through a wrapper that hands back a recording view of the config
      node addressed "config.<dotted.path>[<key>]". Nothing here holds a
      hand-written source list, so a suite added to the registry or a key
      added to a config.json is covered the moment the render reads it.
  guard(patterns)
      asks src/os/patterns_label_readability.gate - the SHIPPED per-codepoint
      law - at CALL time over that derived set, and raises DiskTextRefused
      naming the SOURCE (registry or config) and the field path when the first
      suspect is found. The verdict is never re-derived here: patching
      PLR.gate moves this reading, which is how AC-ADTR1 is proved.
  publish(patterns, render)
      runs the caller's render only when the disk-sourced text is publishable.

No source file is rewritten: the registry module, the product config.json files
and the patterns file keep their digests across a full reading (AC-ADTR5).

Criteria AC-ADTR1..AC-ADTR6 were pinned in state/queue/tech.md as the R2507
claim row BEFORE this code existed.

LIMIT, stated rather than buried: deriving the read set means composing the
real render once, so the guard seams the render asks before it reads anything
are patched for the duration of that single probe (the registry SUITES list,
suite_matrix.face_node, and every guard module the render carries - the two
this probe shipped with and any seam added later, read off the module so a new
guard cannot revive a verdict the probe must read past), each replaced by a
quiet stand-in, and all of them are restored in a finally block. A concurrent
in-process caller could observe that window; the CLI and the shipped render
path are single-process, so the window is not reachable there.

SECOND LIMIT, stated as measured rather than assumed: the shipped law flags
a script bucket no OTHER label in the same set carries, so if this derived set
mixes scripts the law may name a legitimate label - the suite proves the
BROKEN-CODEPOINT refusal, which is what this face exists for.

Pure ASCII, stdlib only, no clock, no network, writes nothing but stdout.

CLI: --patterns JSON [--json]
  exit 0 = every disk-sourced string is publishable (verdict CLEAN)
  exit 2 = a disk-sourced string is SUSPECT, publication refused
  exit 3 = the patterns file is missing, unreadable or malformed
  exit 5 = bad arguments
"""

import argparse
import hashlib
import json
import os
import sys

import patterns_label_readability as PLR

LABEL = "os-artifact-disk-text-readability"
E_ARGS = "E_ADTR_ARGS"
E_PATTERNS = "E_ADTR_PATTERNS"
CLEAN = "CLEAN"
SUSPECT = "SUSPECT"
PROBE_STAMP = "ADTR-PROBE"
PROBE_STAMP_FROM = "adtr-probe-source.md"
PROBE_EVIDENCE = "adtr-probe-evidence.log"
REGISTRY_SOURCE = "registry"
CONFIG_SOURCE = "config"
UNKNOWN_SOURCE = "unknown"

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

_PROBE_DEPTH = 0


class DiskTextRefused(Exception):
    """A disk-sourced field stopped a publication; source and field travel."""

    def __init__(self, code, source, field, codepoints):
        Exception.__init__(self, "%s: %s %s" % (code, source, field))
        self.code = code
        self.source = source
        self.field = field
        self.codepoints = codepoints


class _Quiet(object):
    """Stand-in for a guard the probe must read PAST; restored in finally."""

    def guard(self, *args, **kwargs):
        return None


class _Recorded(str):
    """A string that records itself, addressed by the path that asked for it."""

    def __new__(cls, value, sink, path):
        text = str(value)
        obj = str.__new__(cls, text)
        sink[path] = text
        return obj


class _RecordedKeys(dict):
    """A config node whose KEYS the render copies with str() into the table."""

    def __init__(self, source, sink, prefix):
        dict.__init__(self, source)
        self._sink = sink
        self._prefix = prefix

    def __iter__(self):
        for key in dict.__iter__(self):
            yield _Recorded(key, self._sink,
                            "%s[%s]" % (self._prefix, key))


class _RecordedItems(list):
    """A config node whose ITEMS the render copies with str() into the table."""

    def __init__(self, source, sink, prefix):
        list.__init__(self, source)
        self._sink = sink
        self._prefix = prefix

    def __iter__(self):
        for index, item in enumerate(list.__iter__(self)):
            yield _Recorded(item, self._sink,
                            "%s[%d]" % (self._prefix, index))


def _wrap(node, sink, path):
    """A recording view of one config node, without changing what it holds."""
    if isinstance(node, dict):
        return _RecordedKeys(node, sink, path)
    if isinstance(node, list):
        return _RecordedItems(node, sink, path)
    return _Recorded(node, sink, path)


def suite_matrix_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def _recording_face_node(real, sink):
    """Ask the shipped reader, then hand back a view that records what it read."""

    def wrapper(cfg, dotted):
        node = real(cfg, dotted)
        return _wrap(node, sink, "%s.%s" % (CONFIG_SOURCE, dotted))

    return wrapper


def _recording_suites(suites, sink):
    """The live registry rows, each string recording the path that asked."""
    rows = []
    for index, (label, suite_path, crit) in enumerate(suites):
        rows.append((_Recorded(label, sink,
                               "%s[%d].label" % (REGISTRY_SOURCE, index)),
                     _Recorded(suite_path, sink,
                               "%s[%d].path" % (REGISTRY_SOURCE, index)),
                     crit))
    return rows


def disk_strings(patterns):
    """The DISK-sourced strings the real render reads, derived not listed."""
    global _PROBE_DEPTH
    module = suite_matrix_module()
    registry = module.RA
    sink = {}
    real_suites = registry.SUITES
    real_face_node = module.face_node
    real_plrc = module.PLRC
    real_pnlt = module.PNLT
    # R2509 birth-site repair: suite_matrix.render gained a FOURTH guard seam
    # (evidence_name_text_coverage) after this probe was written, and a probe
    # that asks a live guard recurses into it and inherits whatever verdict is
    # in flight. This seam must be quiet too, so it is read off the module
    # rather than frozen at the three names this probe shipped with.
    real_evnm = getattr(module, "EVNM", None)
    # R2511 birth-site repair: render gained a FIFTH guard seam
    # (stamp_text_coverage) after this probe was written; a probe that asks a
    # live guard recurses into it and pays for a second composition. Read the
    # seam off the module rather than freezing the names this probe shipped
    # with, exactly as the EVNM seam above is read.
    real_stpt = getattr(module, "STPT", None)
    _PROBE_DEPTH += 1
    try:
        registry.SUITES = _recording_suites(real_suites, sink)
        module.face_node = _recording_face_node(real_face_node, sink)
        module.PLRC = _Quiet()
        module.PNLT = _Quiet()
        if real_evnm is not None:
            module.EVNM = _Quiet()
        if real_stpt is not None:
            module.STPT = _Quiet()
        module.render(patterns, PROBE_EVIDENCE, {}, None, PROBE_STAMP,
                      stamp_from=PROBE_STAMP_FROM)
    finally:
        registry.SUITES = real_suites
        module.face_node = real_face_node
        module.PLRC = real_plrc
        module.PNLT = real_pnlt
        if real_evnm is not None:
            module.EVNM = real_evnm
        if real_stpt is not None:
            module.STPT = real_stpt
        _PROBE_DEPTH -= 1
    return sink


def source_of(field):
    """Which disk face a refused field came from, read off its own path."""
    name = str(field)
    if name.startswith(REGISTRY_SOURCE):
        return REGISTRY_SOURCE
    if name.startswith(CONFIG_SOURCE):
        return CONFIG_SOURCE
    return UNKNOWN_SOURCE


def guard(patterns):
    """Ask the shipped gate at CALL time over the artifact's disk-sourced text."""
    if _PROBE_DEPTH:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
                "publishable": True, "code": None,
                "refused_source": None, "refused_field": None,
                "refused_codepoints": [], "fields": []}
    strings = disk_strings(patterns)
    verdict = PLR.gate(strings)
    if not verdict["publishable"]:
        raise DiskTextRefused(verdict["code"], source_of(verdict["label"]),
                              verdict["label"], verdict["codepoints"])
    return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
            "publishable": True, "code": None, "refused_source": None,
            "refused_field": None, "refused_codepoints": [],
            "fields": sorted(strings)}


def reading(patterns):
    """What the render path would publish, as a report row (never raises)."""
    try:
        return guard(patterns)
    except DiskTextRefused as exc:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": SUSPECT,
                "publishable": False, "code": exc.code,
                "refused_source": exc.source,
                "refused_field": exc.field,
                "refused_codepoints": exc.codepoints,
                "fields": sorted(disk_strings(patterns))}


def publish(patterns, render):
    """Run render() only for a publishable document, keeping its bytes."""
    guard(patterns)
    return render()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def render(report_row):
    lines = ["ARTIFACT DISK TEXT READABILITY %s verdict=%s source=%s fields=%d"
             % (report_row["tool"], report_row["verdict"],
                report_row["source"], len(report_row["fields"]))]
    if not report_row["publishable"]:
        lines.append("  refused=%s source=%s field=%s codepoints=%s"
                     % (report_row["code"], report_row["refused_source"],
                        report_row["refused_field"],
                        ",".join(report_row["refused_codepoints"])))
    for field in report_row["fields"]:
        lines.append("  %s" % field)
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the render inputs)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        document = load(args.patterns)
        before = digest(args.patterns)
    except (OSError, ValueError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3
    try:
        row = reading(document)
    except (KeyError, TypeError, AttributeError) as exc:
        print("FAIL patterns: %s incomplete document: %s" % (E_PATTERNS, exc))
        return 3
    after = digest(args.patterns)
    if after != before:
        print("FAIL patterns: %s source changed under the reading" % E_PATTERNS)
        return 3
    if args.json:
        print(json.dumps(row, sort_keys=True))
    else:
        print(render(row))
    return 0 if row["publishable"] else 2


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