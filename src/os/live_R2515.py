"""One-off live leg for R2515: read the REAL tree, then two forwarding fixtures.

Writes qa/probe-seam-forwarding-scope-live-R2515.log through the shipped
single evidence writer so the census reads it as `tee`. Read-only on the real
tree; both fixtures live in private temporary directories.
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

import probe_seam_forwarding_scope as PSF  # noqa: E402
import evidence_writer as EW  # noqa: E402

RENDER = os.path.join(SANDBOX, "suite_matrix.py")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def write(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def helper_text(seams, omit=()):
    kept = [name for name in seams if name not in omit]
    return "QUIETED = (%s,)\n" % ", ".join('"%s"' % name for name in kept)


def main():
    before = [digest(RENDER), digest(DOC)]
    report = PSF.audit(BASE)
    after = [digest(RENDER), digest(DOC)]
    lines = [PSF.render(report)]
    seams = [seam["name"] for seam in report["seams"]]
    lines.append("  live read: seams=%d unchanged=%s"
                 % (len(seams), before == after))

    good = tempfile.mkdtemp(prefix="psf-live-")
    stale = tempfile.mkdtemp(prefix="psf-live-")
    try:
        write(os.path.join(good, "quiet_helper.py"), helper_text(seams))
        write(os.path.join(good, "forwarding_probe.py"),
              "import quiet_helper\nVALUE = 1\n")
        rows = PSF.audit(good)["probes"]
        row = [r for r in rows if r["file"] == "forwarding_probe.py"][0]
        lines.append("  forwarding fixture: verdict=%s helpers=%s quieted=%d"
                     % (row["verdict"], ",".join(row["helpers"]),
                        len(row["quieted"])))

        write(os.path.join(stale, "quiet_helper.py"),
              helper_text(seams, omit=(seams[-1],)))
        write(os.path.join(stale, "forwarding_probe.py"),
              'raise SystemExit("must not run")\n'
              "import quiet_helper\nVALUE = 1\n")
        stale_report = PSF.audit(stale)
        row = [r for r in stale_report["probes"]
               if r["file"] == "forwarding_probe.py"][0]
        lines.append("  stale forwarding fixture: verdict=%s missing=%s "
                     "file=%s"
                     % (row["verdict"], ",".join(row["missing"]),
                        row["file"]))
        lines.append("  stale fixture tree verdict=%s (exit 2 by the tool)"
                     % (stale_report["verdict"],))

        lazy = tempfile.mkdtemp(prefix="psf-live-")
        try:
            write(os.path.join(lazy, "quiet_helper.py"), helper_text(seams))
            write(os.path.join(lazy, "lazy_probe.py"),
                  "def load():\n"
                  "    import quiet_helper\n"
                  "    return quiet_helper.QUIETED\n")
            row = [r for r in PSF.audit(lazy)["probes"]
                   if r["file"] == "lazy_probe.py"][0]
            lines.append("  MEASURED LIMIT lazy fixture: verdict=%s quieted=%d "
                         "(an import inside a function body is not followed)"
                         % (row["verdict"], len(row["quieted"])))
        finally:
            shutil.rmtree(lazy, ignore_errors=True)
    finally:
        shutil.rmtree(good, ignore_errors=True)
        shutil.rmtree(stale, ignore_errors=True)

    lines.append("RESULT verdict=%s covered=%d missing=%d out_of_scope=%d "
                 "historical=%d"
                 % (report["verdict"], report["counts"][PSF.COVERED],
                    report["counts"][PSF.MISSING_SEAM],
                    report["counts"][PSF.OUT_OF_SCOPE],
                    report["counts"][PSF.HISTORICAL]))
    body = "\n".join(lines)
    path = os.path.join(REPO, "qa",
                        "probe-seam-forwarding-scope-live-R2515.log")
    EW.write_evidence(path, body)
    row = EW.check_file(path)
    print(body)
    print("WROTE %s bytes=%d class=%s"
          % (path, row["bytes"], row["class"]))
    return 0 if report["verdict"] == PSF.SEAMS_FORWARDED \
        and before == after else 1


if __name__ == "__main__":
    sys.exit(main())