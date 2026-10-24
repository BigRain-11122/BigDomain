#!/usr/bin/env python3
"""evidence_census_R2072.py - historical dialect census reading.

Deliverable face 2 of the R2072 tech-queue row: a read-only census of
every qa/ evidence log (never rewrites history bytes), written through
the new single-writer helper so the census evidence itself is tee.

Proves AC-EVD7 at production scale: a (name, size, mtime_ns)
fingerprint of the whole directory is taken before and after the
census and the run fails honestly if any byte or mtime moved.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
for path in (BASE, SANDBOX):
    if path not in sys.path:
        sys.path.insert(0, path)

import evidence_writer as EW
import qa_writer_census as CENSUS

QA_DIR = os.path.join(ROOT, "qa")
OUT = os.path.join(QA_DIR, "evidence-writer-census-R2072.log")


def fingerprint(target):
    rows = []
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        if not os.path.isfile(path):
            continue
        st = os.stat(path)
        rows.append("%s %d %d" % (name, st.st_size, st.st_mtime_ns))
    return rows


def main():
    if not os.path.isdir(QA_DIR):
        print("REFUSED qa dir missing")
        return 3
    before = fingerprint(QA_DIR)
    lines, code, summary = CENSUS.probe_dir(QA_DIR)
    after = fingerprint(QA_DIR)
    stable = before == after
    counts = summary["counts"]
    total = summary["file_count"]
    lines.append("fingerprint stable=%s files=%d" % (stable, len(after)))
    lines.append("verdict CENSUS-READ-ONLY %s"
                 % ("PASS" if stable else "FAIL"))
    text = "\n".join(lines) + "\n"
    row = EW.write_evidence(OUT, text)
    print("read-only=%s class=%s files=%d total=%d" % (stable, row["class"],
                                                       total, total))
    print("counts tee=%d cmd-raw=%d pwsh-capture=%d ps-utf16=%d other=%d"
          % (counts["tee"], counts["cmd-raw"], counts["pwsh-capture"],
             counts["ps-utf16"], counts["other"]))
    print("evidence %s" % OUT)
    return 0 if stable and code == 0 else 2


if __name__ == "__main__":
    sys.exit(main())