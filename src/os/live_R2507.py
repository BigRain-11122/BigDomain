"""R2507 live leg: the real tree reads CLEAN, and a doctored registry refuses.

Run from src/os. Writes ONE utf-8 LF evidence file through the shipped single
writer. Reads the shipped modules; doctors only an in-memory registry list and
restores it in a finally block, so no shipped byte changes.

ASCII source, stdlib only, no clock, no network.
"""

import hashlib
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import artifact_disk_text_readability as ADTR  # noqa: E402
import evidence_writer as EW  # noqa: E402
import suite_matrix as SM  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
PATTERNS = os.path.join(SANDBOX, "suite_matrix_patterns.json")
OUT = os.path.join(REPO, "qa", "artifact-disk-text-readability-live-R2507.log")
BREAK = "\ufffd"


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    document = SM.load_patterns()
    doc_before = digest(DOC)
    doc_text = read_text(DOC)
    recorded = SM.doc_evidence_face(doc_text, document)
    if recorded is None:
        print("FAIL setup: shipped doc records no evidence path")
        return 2
    evidence_path = os.path.join(REPO, recorded)
    row = ADTR.reading(document)
    lines = [
        "ARTIFACT DISK TEXT READABILITY live R2507",
        "live verdict=%s publishable=%s fields=%d source=%s"
        % (row["verdict"], str(row["publishable"]).lower(),
           len(row["fields"]), row["source"]),
        "registry_labels=%d config_strings=%d"
        % (len([n for n in row["fields"] if n.startswith("registry")]),
           len([n for n in row["fields"] if n.startswith("config")])),
        "doc_digest_before=%s" % doc_before[:16],
    ]
    rows = list(SM.RA.SUITES)
    label, suite_path, crit = rows[0]
    rows[0] = (label + BREAK, suite_path, crit)
    real = SM.RA.SUITES
    refused = None
    try:
        SM.RA.SUITES = rows
        try:
            SM.render(document, evidence_path, {}, None, "adtr-live-stamp")
        except ADTR.DiskTextRefused as exc:
            refused = exc
    finally:
        SM.RA.SUITES = real
    lines.append("doctored_registry refused=%r code=%s source=%s field=%s"
                 % (refused is not None,
                    getattr(refused, "code", "-"),
                    getattr(refused, "source", "-"),
                    getattr(refused, "field", "-")))
    doc_after = digest(DOC)
    lines.append("doc_digest_after=%s unchanged=%r"
                 % (doc_after[:16], doc_after == doc_before))
    lines.append("patterns_digest=%s" % digest(PATTERNS)[:16])
    body = "\n".join(lines) + "\n"
    size = EW.write_evidence(OUT, body)
    sys.stdout.write(body)
    measured = size["bytes"] if isinstance(size, dict) else size
    print("LIVE evidence=%s bytes=%r" % (os.path.relpath(OUT, REPO), measured))
    clean = row["publishable"] is True
    return 0 if (clean and refused is not None and doc_after == doc_before) else 1


if __name__ == "__main__":
    sys.exit(main())