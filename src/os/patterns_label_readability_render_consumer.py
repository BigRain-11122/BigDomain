"""patterns_label_readability_render_consumer - the render path asks the gate.

MEASURED at R2502 while shipping the readability face: src/sandbox/
suite_matrix.py::load_patterns reads suite_matrix_patterns.json with json.load
and render() interpolates every label straight into
docs/sandbox-suite-matrix.md, so the operator's own render command never asked
whether a label is readable text - the R2502 gate only protected callers that
chose to route through publish(). A patterns file with one mis-encoded label
therefore still rendered into the CEO-visible artifact when the shipped tool
was run directly.

This module is the CONSUMER seam. It holds no classifier of its own: guard()
asks src/os/patterns_label_readability.gate at CALL time and carries that
verdict and that refusal code verbatim, so the render path cannot grow a
second opinion about what a readable label is. A clean file is handed back
untouched; a suspect file raises RenderRefused naming the label key and the
codepoints the shipped gate named.

Criteria AC-PLRC1..AC-PLRC6 were pinned in state/queue/tech.md:540 at R2502,
the seed row, BEFORE this code existed.

Pure ASCII, stdlib only, no clock, no network, writes nothing.

CLI: --patterns JSON [--json]
  exit 0 = the render path is publishable (the gate reads CLEAN)
  exit 2 = a label is SUSPECT, publication refused (the gate own code)
  exit 3 = the patterns file is missing, unreadable or malformed
  exit 5 = bad arguments
"""

import argparse
import json
import sys

import patterns_label_readability as PLR

LABEL = "os-patterns-label-readability-render-consumer"
E_ARGS = "E_PLRC_ARGS"
E_PATTERNS = "E_PLRC_PATTERNS"
CLEAN = "CLEAN"
SUSPECT = "SUSPECT"


class RenderRefused(Exception):
    """The shipped gate refused this patterns file before any render began."""

    def __init__(self, code, label, codepoints):
        Exception.__init__(self, "%s: %s" % (code, label))
        self.code = code
        self.label = label
        self.codepoints = codepoints


def guard(labels):
    """Ask the shipped gate at CALL time and refuse publication if it says so.

    The gate is looked up on the module object here, never copied and never
    re-implemented, so a patched gate moves this reading and a new label law
    needs no second call site.
    """
    verdict = PLR.gate(labels)
    if not verdict["publishable"]:
        raise RenderRefused(verdict["code"], verdict["label"],
                            verdict["codepoints"])
    return verdict


def reading(labels):
    """What the render path would do with this patterns file, derived."""
    try:
        verdict = guard(labels)
    except RenderRefused as exc:
        return {"tool": LABEL, "source": PLR.LABEL, "verdict": SUSPECT,
                "publishable": False, "code": exc.code,
                "refused_label": exc.label,
                "refused_codepoints": exc.codepoints}
    return {"tool": LABEL, "source": PLR.LABEL, "verdict": CLEAN,
            "publishable": True, "code": None, "refused_label": None,
            "refused_codepoints": []}


def render(report_row):
    lines = ["PATTERNS RENDER CONSUMER %s verdict=%s source=%s"
             % (report_row["tool"], report_row["verdict"],
                report_row["source"])]
    if not report_row["publishable"]:
        lines.append("  refused=%s label=%s codepoints=%s"
                     % (report_row["code"], report_row["refused_label"],
                        ",".join(report_row["refused_codepoints"])))
    return "\n".join(lines)


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patterns", required=True, metavar="JSON",
                        help="suite_matrix_patterns.json (the label owner)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    try:
        document = load(args.patterns)
        labels = document["labels"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("FAIL patterns: %s %s" % (E_PATTERNS, exc))
        return 3

    row = reading(labels)
    print(json.dumps(row, sort_keys=True, indent=2)
          if args.json else render(row))
    return 0 if row["publishable"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))