"""one-off live capture for R2501 (the text-binding face on the REAL tree).

Reads the shipped docs/status-export.json, hands it to the shipped wire on a
private copy, then hands it a composition made from a DIFFERENT document and
records what the binding answers. Writes one utf-8 LF evidence file through the
shipped single writer. No repository byte other than that log is touched.
"""

import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import closeout_export_parity_text_binding as CEPTB  # noqa: E402
import closeout_export_parity_wire as CEPW  # noqa: E402
import evidence_writer  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")
LOG = os.path.join(REPO, "qa", "closeout-export-parity-text-binding-live-R2501.log")


def read_text(path):
    with io.open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def main():
    lines = []
    own = CEPTB.compose(REPO, EXPORT)
    difference, _composed = CEPTB.bind(REPO, EXPORT, own)
    lines.append("REAL BINDING path=%s difference=%s bytes=%d"
                 % (EXPORT, difference or "(none)", len(own.encode("utf-8"))))

    tmpdir = tempfile.mkdtemp(prefix="ceptb-live-")
    try:
        same = os.path.join(tmpdir, "same.json")
        with io.open(same, "w", encoding="utf-8", newline="") as handle:
            handle.write(read_text(EXPORT))
        result, code = CEPTB.publish(REPO, same, own)
        published = read_bytes(same)
        lines.append("SAME DOCUMENT verdict=%s binding=%s rc=%d bytes=%d crlf=%d"
                     % (result["verdict"], result["binding"], code,
                        result["bytes"], published.count(b"\r\n")))

        data = json.loads(read_text(EXPORT))
        data["self_drive"]["window_days"] = 999
        other = os.path.join(tmpdir, "other.json")
        with io.open(other, "w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        target = os.path.join(tmpdir, "target.json")
        with io.open(target, "w", encoding="utf-8", newline="") as handle:
            handle.write(read_text(EXPORT))
        before = read_bytes(target)
        result, code = CEPTB.publish(REPO, target, CEPW.compose(REPO, other))
        lines.append("FOREIGN TEXT verdict=%s binding=%s rc=%d differs=%s "
                     "unchanged=%s residue=%s"
                     % (result["verdict"], result["binding"], code,
                        result["differs"], read_bytes(target) == before,
                        os.path.exists(target + ".parity-stage")))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    text = "\n".join(lines) + "\n"
    evidence_writer.write_evidence(LOG, text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()