"""queue_R2378 - stamp the claimed tech row and seed the next measured gap.

Line 424 is the R2377 seed row whose AC-CEPW1..AC-CEPW6 this window delivered,
so it closes with a bracket inside the 60-character stamp law. The successor
row is the seam this window MEASURED while rerouting the closeout: of the three
closeout scripts that publish docs/status-export.json, only closeout_R2377.py
asks the parity wire; closeout_R2375.py and closeout_R2376.py still call
QFE.apply and write the document themselves.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
TECH = os.path.join(REPO, "state", "queue", "tech.md")

TARGET_LINE = 424
STAMP = "[done 2026-11-02 R2378]"

GAP_ROW = (
    "- [ ] P2 tech seed (R2378, from this window own measured gap): "
    "`src/os/export_publish_path_guard.py` - the parity wire now proves the "
    "closeout it serves, but only one closeout asks it: of the three scripts "
    "that publish docs/status-export.json, closeout_R2377.py routes through "
    "closeout_export_parity_wire.publish while closeout_R2375.py and "
    "closeout_R2376.py still call QFE.apply and write the document "
    "themselves, and nothing reads that. Product: one guard that names every "
    "script publishing the export WITHOUT the wire, so the bypass is a "
    "reading rather than a habit. Criteria AC-EPPG1..AC-EPPG6 "
    "pre-registered HERE BEFORE any code: AC-EPPG1 the guard reads the "
    "publishing scripts from the tree it is given and names each offender "
    "with its file and the line that publishes; AC-EPPG2 a script that routes "
    "through the wire is CLEAN, so the reading is a property of the code and "
    "not of a whitelist; AC-EPPG3 the guard writes nothing and reads no "
    "clock; AC-EPPG4 a tree with no publishing script reads EMPTY at exit 0 "
    "rather than CLEAN by accident; AC-EPPG5 exit 0 = CLEAN, 2 = BYPASS "
    "naming every offender, 3 = missing root, 5 = bad flags, with a "
    "byte-stable --json over pinned keys; AC-EPPG6 pure ASCII, stdlib only, "
    "zero network, plus its own reconcile label. Five anchors zero-occupancy "
    "at HEAD 2026-11-02: export_publish_path_guard, AC-EPPG, E_EPPG, "
    "os-export-publish-path-guard, test_export_publish_path_guard."
)


def main():
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")
    row = lines[TARGET_LINE - 1]
    if not row.startswith("- [ ]"):
        raise SystemExit("E_QR2378_NOT_OPEN %s" % row[:60])
    if "AC-CEPW1" not in row:
        raise SystemExit("E_QR2378_WRONG_ROW %s" % row[:60])
    lines[TARGET_LINE - 1] = row.replace("- [ ]", "- [x] " + STAMP, 1)
    if not lines[-1] == "":
        lines.append("")
    lines.append(GAP_ROW)
    if lines[-1] != "":
        lines.append("")
    new_text = "\n".join(lines)
    predicted = len(text.encode("utf-8")) + len(STAMP) + 1 + len(GAP_ROW) + 1
    tmp = TECH + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)
    os.replace(tmp, TECH)
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    if back != new_text:
        raise SystemExit("E_QR2378_READBACK")
    if os.path.exists(tmp):
        raise SystemExit("E_QR2378_RESIDUE")
    print("QUEUE R2378 stamped line %d predicted=%d actual=%d gap_row=%d"
          % (TARGET_LINE, predicted, len(back.encode("utf-8")), len(GAP_ROW)))


if __name__ == "__main__":
    main()