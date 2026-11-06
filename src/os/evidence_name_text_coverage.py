"""evidence_name_text_coverage - the EVIDENCE NAME the artifact prints is covered too.

MEASURED at R2507 while wiring the disk-text gate: artifact_disk_text_readability
derives everything the render reads off DISK through recording wrappers, but its
coverage probe hands the render a CONSTANT evidence path, so the evidence file
NAME that src/sandbox/suite_matrix.py::render interpolates into
docs/sandbox-suite-matrix.md sits outside that derived set. A copy of the real
evidence named "reconcile-all-R2506-retr<U+FFFD>y.log" rendered into the
document with the broken codepoint carried while the shipped reading still
returned publishable=True (qa/adtr-evidence-name-live-R2507.log).

The render takes three strings from the evidence path:

  * base = os.path.basename(evidence_path), printed on the evidence line and
    again on the provenance line,
  * rel(evidence_path), printed on the regeneration command line,
  * the round tag, which is "R<digits>" when the basename carries one and the
    basename itself otherwise.

This face closes that gap without growing a second classifier:

  evidence_strings(evidence_path, patterns)
      the evidence-derived strings the render actually prints, derived by
      composing the real render ONCE against a probe that records every string
      the render asks for from that path - os.path.basename answered by a
      recording os.path proxy and suite_matrix.rel answered by a recording
      wrapper, addressed as "evidence.basename" and "evidence.relpath". Both
      record only when the path asked about IS the evidence path, so an
      unrelated path is never claimed. The round tag is recorded as
      "evidence.round_tag" only when it is a DIFFERENT string from the
      basename - the render prints the basename verbatim otherwise, so claiming
      it twice would be dishonest bookkeeping. Nothing here holds a
      hand-written name or path: whatever evidence is handed in is what gets
      read.
  guard(evidence_path, patterns)
      asks src/os/patterns_label_readability.gate - the SHIPPED per-codepoint
      law - at CALL time over that derived set, and raises EvidenceNameRefused
      naming the PIECE and the offending NAME when the first suspect is found.
      The verdict is never re-derived here: patching PLR.gate moves this
      reading, which is how AC-EVNM1 is proved.
  publish(evidence_path, patterns, render)
      runs the caller's render only when the evidence name is publishable.

No source file and no evidence file is rewritten: the patterns file, the
evidence log and the artifact keep their digests across a full reading
(AC-EVNM5).

Criteria AC-EVNM1..AC-EVNM6 were pinned in state/queue/tech.md:547 as the R2507
seed row BEFORE this code existed.

LIMIT, stated rather than buried: deriving the set means composing the real
render once, so five suite_matrix module attributes are replaced for the
duration of that single probe - "os" (a proxy that only redirects
os.path.basename for the evidence path), "rel" (a recording wrapper), and the
three guard seams the render asks before it reads anything (each a quiet
stand-in) - and all five are restored in a finally block. Every other
attribute is the real module object. A concurrent in-process caller could
observe the window, which the single-process CLI and the shipped render path
never do.

SECOND LIMIT, stated as measured rather than assumed: suite_matrix.rel
resolves against the process CWD for a relative input, exactly as the render
does today, so the probe records what the render WOULD print rather than a
normalised path of this module's own choosing.

Pure ASCII, stdlib only, no clock, no network, writes nothing but stdout.

CLI: --patterns JSON --evidence PATH [--json]
  exit 0 = every evidence-derived string is publishable (verdict CLEAN)
  exit 2 = an evidence-derived string is SUSPECT, publication refused
  exit 3 = the patterns file is missing, unreadable or malformed
  exit 5 = bad arguments
"""

import argparse
import hashlib
import json
import os
import sys

import patterns_label_readability as PLR

LABEL = "os-evidence-name-text-coverage"
E_ARGS = "E_EVNM_ARGS"
E_PATTERNS = "E_EVNM_PATTERNS"
E_PROBE = "E_EVNM_PROBE"
CLEAN = "CLEAN"
SUSPECT = "SUSPECT"
PROBE_STAMP = "EVNM-PROBE"
PROBE_STAMP_FROM = "evnm-probe-source.md"
PROBE_EVIDENCE = "evnm-probe-evidence.log"
PIECE_BASENAME = "evidence.basename"
PIECE_RELPATH = "evidence.relpath"
PIECE_ROUND_TAG = "evidence.round_tag"

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

_PROBE_DEPTH = 0


class EvidenceNameRefused(Exception):
    """An evidence-derived name stopped a publication; piece and name travel."""

    def __init__(self, code, piece, name, evidence, codepoints):
        Exception.__init__(self, "%s: %s %s" % (code, piece, name))
        self.code = code
        self.piece = piece
        self.name = name
        self.evidence = evidence
        self.codepoints = codepoints


class _Quiet(object):
    """Stand-in for a guard the probe must read PAST; restored in finally."""

    def guard(self, *args, **kwargs):
        return None


class _PathShim(object):
    """os.path with basename recording what the render asked for.

    Only the evidence path is recorded: a basename of some other path is none
    of this face's business and is passed straight through.
    """

    def __init__(self, real, sink, target):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_sink", sink)
        object.__setattr__(self, "_target", str(target))

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)

    def basename(self, path):
        value = object.__getattribute__(self, "_real").basename(path)
        if str(path) == object.__getattribute__(self, "_target"):
            object.__getattribute__(self, "_sink")[PIECE_BASENAME] = str(value)
        return value

    def relpath(self, path, start=None):
        real = object.__getattribute__(self, "_real")
        return real.relpath(path, start) if start is not None \
            else real.relpath(path)


class _OsShim(object):
    """The real os module with os.path swapped for the recording proxy."""

    def __init__(self, real, sink, target):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_path", _PathShim(real.path, sink, target))

    def __getattr__(self, name):
        if name == "path":
            return object.__getattribute__(self, "_path")
        return getattr(object.__getattribute__(self, "_real"), name)


def _recording_rel(real, sink, target):
    """Record what the shipped rel() RETURNS - that is the string printed."""

    def wrapper(path):
        value = real(path)
        if str(path) == target:
            sink[PIECE_RELPATH] = str(value)
        return value

    return wrapper


def suite_matrix_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def round_tag(module, basename):
    """The tag the render prints in its summary row, computed by ITS law."""
    match = module.EVID_ROUND_RE.search(basename)
    return ("R" + match.group(1)) if match else basename


def evidence_strings(evidence_path, patterns):
    """The evidence-derived strings the real render prints, derived not listed."""
    global _PROBE_DEPTH
    module = suite_matrix_module()
    sink = {}
    target = str(evidence_path)
    real_os = module.os
    real_rel = module.rel
    real_plrc = module.PLRC
    real_pnlt = module.PNLT
    real_adtr = module.ADTR
    # R2511 birth-site repair: render gained a FIFTH guard seam
    # (stamp_text_coverage) after this probe was written, and a probe that asks
    # a live guard would pay for a second full composition. Read it off the
    # module so this probe keeps working when the seam set grows again.
    real_stpt = getattr(module, "STPT", None)
    _PROBE_DEPTH += 1
    try:
        module.os = _OsShim(real_os, sink, target)
        module.rel = _recording_rel(real_rel, sink, target)
        module.PLRC = _Quiet()
        module.PNLT = _Quiet()
        module.ADTR = _Quiet()
        if real_stpt is not None:
            module.STPT = _Quiet()
        module.render(patterns, evidence_path, {}, None, PROBE_STAMP,
                      stamp_from=PROBE_STAMP_FROM)
    finally:
        module.os = real_os
        module.rel = real_rel
        module.PLRC = real_plrc
        module.PNLT = real_pnlt
        module.ADTR = real_adtr
        if real_stpt is not None:
            module.STPT = real_stpt
        _PROBE_DEPTH -= 1
    base = sink.get(PIECE_BASENAME)
    if base is not None:
        tag = round_tag(module, base)
        if tag != base:
            sink[PIECE_ROUND_TAG] = tag
    if PIECE_BASENAME not in sink:
        raise RuntimeError("%s: the render asked for no evidence basename"
                           % E_PROBE)
    return sink


def guard(evidence_path, patterns):
    """Ask the shipped gate at CALL time over the evidence-derived names."""
    if _PROBE_DEPTH:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
                "publishable": True, "code": None, "refused_piece": None,
                "refused_name": None, "refused_evidence": None,
                "refused_codepoints": [], "fields": []}
    strings = evidence_strings(evidence_path, patterns)
    verdict = PLR.gate(strings)
    if not verdict["publishable"]:
        piece = verdict["label"]
        raise EvidenceNameRefused(verdict["code"], piece, strings.get(piece),
                                  str(evidence_path), verdict["codepoints"])
    return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
            "publishable": True, "code": None, "refused_piece": None,
            "refused_name": None, "refused_evidence": None,
            "refused_codepoints": [], "fields": sorted(strings)}


def reading(evidence_path, patterns):
    """What the render path would publish, as a report row (never raises)."""
    try:
        return guard(evidence_path, patterns)
    except EvidenceNameRefused as exc:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": SUSPECT,
                "publishable": False, "code": exc.code,
                "refused_piece": exc.piece, "refused_name": exc.name,
                "refused_evidence": exc.evidence,
                "refused_codepoints": exc.codepoints,
                "fields": sorted(evidence_strings(evidence_path, patterns))}


def publish(evidence_path, patterns, render):
    """Run render() only for a publishable evidence name, keeping its bytes."""
    guard(evidence_path, patterns)
    return render()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def ascii_safe(text):
    """A name carrying a broken codepoint must not crash the console that
    reports it (R2503 lesson: the console re-encodes what it prints)."""
    if text is None:
        return ""
    return str(text).encode("unicode_escape").decode("ascii")


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def render(report_row):
    lines = ["EVIDENCE NAME TEXT COVERAGE %s verdict=%s source=%s pieces=%d"
             % (report_row["tool"], report_row["verdict"],
                report_row["source"], len(report_row["fields"]))]
    if not report_row["publishable"]:
        lines.append("  refused=%s piece=%s name=%s evidence=%s codepoints=%s"
                     % (report_row["code"], report_row["refused_piece"],
                        ascii_safe(report_row["refused_name"]),
                        ascii_safe(report_row["refused_evidence"]),
                        ",".join(report_row["refused_codepoints"])))
    for field in report_row["fields"]:
        lines.append("  %s" % field)
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the render inputs)")
    parser.add_argument("--evidence", required=True, metavar="PATH",
                        help="the evidence log whose name the artifact prints")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        document = load(args.patterns)
        before = digest(args.patterns)
    except (OSError, ValueError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3
    try:
        row = reading(os.path.abspath(args.evidence), document)
    except (KeyError, TypeError, AttributeError) as exc:
        print("FAIL patterns: %s incomplete document: %s" % (E_PATTERNS, exc))
        return 3
    except RuntimeError as exc:
        print("FAIL probe: %s" % exc)
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