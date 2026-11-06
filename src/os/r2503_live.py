"""R2503 live reading + one measured limit of the shipped readability gate.

Two readings, both against the real modules and the real files:

  LIVE      the shipped patterns file, asked through the new consumer seam,
            reads publishable - the render path's guard is live on this tree.
  MEASURED  patterns_label_readability.gate() is asked with patterns["labels"]
            ONLY, while suite_matrix.render() interpolates header_note,
            response_text and every table caption straight into the artifact.
            So a mis-encoded header_note publishes into the CEO-visible doc
            while the gate reads CLEAN. This is measured here, not asserted
            from prose: a doctored copy carries U+FFFD in header_note, the
            gate still answers publishable=True, and the composed document
            text really contains the broken codepoint.

Writes one utf-8 LF log (never a pwsh capture: the R2486 lesson).
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import patterns_label_readability as PLR  # noqa: E402
import patterns_label_readability_render_consumer as PLRC  # noqa: E402
import suite_matrix as SM  # noqa: E402

PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(REPO, "qa", "patterns-render-consumer-live-R2503.log")


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    document = json.loads(read_text(PATTERNS_PATH))
    live = PLRC.reading(document["labels"])

    doctored = json.loads(json.dumps(document))
    doctored["header_note"] = doctored["header_note"] + " \u04e1\ufffd"
    verdict = PLR.gate(doctored["labels"])
    current = read_text(DOC)
    stamp = SM.doc_stamp(current, document)
    recorded = SM.doc_evidence_face(current, document)
    evidence_path = os.path.abspath(os.path.join(REPO, recorded))
    status, run = SM.parse_evidence(evidence_path)
    composed = SM.render(doctored, evidence_path, status, run, stamp,
                         stamp_from=recorded)
    carries = "\ufffd" in composed

    lines = [
        "PATTERNS RENDER CONSUMER live reading (R2503)",
        "LIVE   source=%s verdict=%s publishable=%s exit=0"
        % (live["source"], live["verdict"], live["publishable"]),
        "MEASURED gate-on-doctored-header publishable=%s code=%s "
        "artifact_carries_broken_codepoint=%s"
        % (verdict["publishable"], verdict["code"], carries),
        "NOTE   the gate is asked with patterns[labels] only, so header_note,"
        " response_text and every caption reach the artifact unasked",
        "ARTIFACT %s bytes=%d" % (SM.rel(DOC),
                                  len(composed.encode("utf-8"))),
    ]
    payload = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    print(payload.rstrip("\n"))
    print("bytes=%d" % len(payload.encode("utf-8")))
    return 0 if (live["publishable"] and carries
                 and verdict["publishable"]) else 1


if __name__ == "__main__":
    sys.exit(main())