"""R2537 live leg: read the REAL src/os tree through the shipped face.

Lands one UTF-8 LF evidence file through the shipped single writer and prints
the measured counters plus the digests it did NOT move.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(os.path.dirname(BASE), "sandbox"))

import probe_seam_nested_key_binding_scope as P  # noqa: E402
import evidence_writer as EW  # noqa: E402


def main():
    module_before = P.digest(os.path.join(
        BASE, "probe_seam_nested_key_binding_scope.py"))
    base_before = P.digest(os.path.join(
        BASE, "probe_seam_nested_subscript_scope.py"))
    render_before = P.digest(os.path.join(
        os.path.dirname(BASE), "sandbox", "suite_matrix.py"))
    report = P.audit(BASE)
    module_after = P.digest(os.path.join(
        BASE, "probe_seam_nested_key_binding_scope.py"))
    base_after = P.digest(os.path.join(
        BASE, "probe_seam_nested_subscript_scope.py"))
    render_after = P.digest(os.path.join(
        os.path.dirname(BASE), "sandbox", "suite_matrix.py"))
    counts = report["counts"]
    lines = ["R2537 LIVE LEG probe_seam_nested_key_binding_scope on src/os",
             "verdict=%s probes=%d covered=%d out_of_scope=%d historical=%d"
             " missing=%d unreadable=%d"
             % (report["verdict"], len(report["probes"]), counts["COVERED"],
                counts["OUT-OF-SCOPE"], counts["HISTORICAL"],
                counts["MISSING-SEAM"], counts["UNREADABLE"]),
             "digests unchanged=%s module=%s base=%s render=%s"
             % (module_before == module_after
                and base_before == base_after
                and render_before == render_after,
                module_after[:16], base_after[:16], render_after[:16])]
    for row in report["probes"]:
        if row["verdict"] in ("COVERED", "MISSING-SEAM", "UNREADABLE"):
            lines.append("  PROBE %s %s keys=%s refused=%s"
                         % (row["file"], row["verdict"],
                            ",".join(row["containers"]) or "-",
                            ",".join(row["container_refusals"]) or "-"))
    text = "\n".join(lines) + "\n"
    path = os.path.join(os.path.dirname(os.path.dirname(BASE)), "qa",
                        "probe-seam-nested-key-binding-scope-live-R2537.log")
    census = EW.write_evidence(path, text)
    sys.stdout.write(text)
    sys.stdout.write("wrote %s bytes=%d class=%s\n"
                     % (path, os.path.getsize(path), census.get("class")))
    return 0 if report["verdict"] == P.SEAMS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())