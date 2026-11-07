"""R2517 one-off: live leg on the REAL tree plus a lazy fixture contrast."""

import hashlib
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(REPO, "qa")
SANDBOX = os.path.join(REPO, "src", "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import evidence_writer  # noqa: E402
import probe_seam_forwarding_scope as PSF  # noqa: E402
import probe_seam_lazy_scope as PSL  # noqa: E402
import suite_matrix as SM  # noqa: E402

RENDER = os.path.join(SANDBOX, "suite_matrix.py")
ARTIFACT = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def write(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def helper(seams, omit=()):
    kept = [n for n in seams if n not in omit]
    return "QUIETED = (%s,)\n" % ", ".join('"%s"' % n for n in kept)


def lazy(helper_name):
    return ("def run():\n    import %s\n    return %s.QUIETED\n\nVALUE = 1\n"
            % (helper_name, helper_name))


def main():
    lines = []
    before = [digest(RENDER), digest(ARTIFACT)]
    report = PSL.audit(BASE, SM)
    lines.append("LIVE REAL TREE verdict=%s seams=%d probes=%d covered=%d "
                 "missing=%d out_of_scope=%d unreadable=%d historical=%d"
                 % (report["verdict"], len(report["seams"]),
                    len(report["probes"]), report["counts"][PSL.COVERED],
                    report["counts"][PSL.MISSING_SEAM],
                    report["counts"][PSL.OUT_OF_SCOPE],
                    report["counts"][PSL.UNREADABLE],
                    report["counts"][PSL.HISTORICAL]))
    for row in report["probes"]:
        if row["verdict"] == PSL.COVERED:
            lines.append("  COVERED %s helpers=%s lazy=%s"
                         % (row["file"], ",".join(row["helpers"]) or "-",
                            ",".join(row["lazy_imports"]) or "-"))
    seams = PSL.seam_names(SM)
    work = tempfile.mkdtemp(prefix="psl-live-")
    try:
        write(os.path.join(work, "quiet_helper.py"), helper(seams))
        write(os.path.join(work, "lazy_probe.py"), lazy("quiet_helper"))
        row = [r for r in PSL.audit(work, SM)["probes"]
               if r["file"] == "lazy_probe.py"][0]
        lines.append("  FIXTURE lazy_probe.py lazy-face=%s helpers=%s "
                     "quieted=%d"
                     % (row["verdict"], ",".join(row["helpers"]),
                        len(row["quieted"])))
        old = [r for r in PSF.audit(work, SM)["probes"]
               if r["file"] == "lazy_probe.py"][0]
        lines.append("  FIXTURE lazy_probe.py module-level-face=%s quieted=%d"
                     % (old["verdict"], len(old["quieted"])))
        write(os.path.join(work, "stale_helper.py"), helper(seams, omit=(seams[-1],)))
        write(os.path.join(work, "stale_probe.py"), lazy("stale_helper"))
        stale = [r for r in PSL.audit(work, SM)["probes"]
                 if r["file"] == "stale_probe.py"][0]
        lines.append("  FIXTURE stale_probe.py lazy-face=%s missing=%s"
                     % (stale["verdict"], ",".join(stale["missing"])))
        lines.append("  FIXTURE tree verdict=%s"
                     % (PSL.audit(work, SM)["verdict"],))
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    after = [digest(RENDER), digest(ARTIFACT)]
    lines.append("  DIGESTS render_unchanged=%s artifact_unchanged=%s"
                 % (before[0] == after[0], before[1] == after[1]))
    target = os.path.join(QA, "probe-seam-lazy-scope-live-R2517.log")
    row = evidence_writer.write_evidence(target, "\n".join(lines) + "\n")
    print("\n".join(lines))
    print("EVIDENCE %s class=%s bytes=%d"
          % (os.path.basename(target), row.get("class"), row.get("bytes")))
    return 0 if (before == after and report["verdict"] ==
                 PSL.SEAMS_LAZY_COVERED) else 1


if __name__ == "__main__":
    sys.exit(main())