"""One-off live leg for R2513: read the REAL tree, then one stale fixture.

Writes qa/probe-seam-registry-live-R2513.log through the shipped single
evidence writer so the census reads it as `tee`. Read-only on the real tree.
"""

import hashlib
import os
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
import evidence_writer as EW  # noqa: E402

RENDER = os.path.join(SANDBOX, "suite_matrix.py")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    before = [digest(RENDER), digest(DOC)]
    report = PSR.audit(BASE)
    after = [digest(RENDER), digest(DOC)]
    lines = [PSR.render(report)]
    seams = [seam["name"] for seam in report["seams"]]
    lines.append("  live read: seams=%d unchanged=%s"
                 % (len(seams), before == after))

    work = tempfile.mkdtemp(prefix="psmr-live-")
    try:
        kept = seams[:-1]
        path = os.path.join(work, "stale_probe.py")
        with open(path, "w", encoding="ascii", newline="\n") as handle:
            handle.write("QUIETED = (%s,)\n"
                         % ", ".join('"%s"' % name for name in kept))
        stale = PSR.audit(work)
        row = stale["probes"][0]
        lines.append("  stale fixture: verdict=%s missing=%s file=%s"
                     % (row["verdict"], ",".join(row["missing"]),
                        row["file"]))
        lines.append("  stale fixture tree verdict=%s (exit 2 by the tool)"
                     % (stale["verdict"],))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    lines.append("RESULT verdict=%s covered=%d missing=%d out_of_scope=%d "
                 "historical=%d"
                 % (report["verdict"], report["counts"][PSR.COVERED],
                    report["counts"][PSR.MISSING_SEAM],
                    report["counts"][PSR.OUT_OF_SCOPE],
                    report["counts"][PSR.HISTORICAL]))
    body = "\n".join(lines)
    path = os.path.join(REPO, "qa", "probe-seam-registry-live-R2513.log")
    EW.write_evidence(path, body)
    row = EW.check_file(path)
    print(body)
    print("WROTE %s bytes=%d class=%s"
          % (path, row["bytes"], row["class"]))
    return 0 if report["verdict"] == PSR.SEAMS_COVERED and before == after \
        else 1


if __name__ == "__main__":
    sys.exit(main())