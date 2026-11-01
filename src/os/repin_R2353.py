# closeout_R2353.py - re-pin the triage declaration from ONE live reading.
#
# Why this exists: the R2331 head declared every entry until R2350, so at
# R2353 the whole set read EXPIRED and handed its rounds back to the debt,
# while the append channel refuses to add a round when any other round is
# untriaged. Rested order: retire the one entry whose round left the residue
# (through residue_triage_entry_retire), then re-read the live residue ONCE
# and accept every round at its reported status until R2363. Nothing here
# invents a status: the round list and every status come from
# residue_triage.live_residue, and the write is one atomic replace.
#
# Pure apart from that one replace; no clock, no network.

import json
import os
import sys

import residue_triage as RT

ROUND = 2353
UNTIL = 2363

REASON = ("re-pinned at R2353: the R2331 head expired at until R2350, so "
          "every live round was read once more from stamp_residue and "
          "accepted at its reported status until R2363")


def build(root):
    """Every live residue round at its live status, nothing invented."""
    rows = RT.live_residue(root)
    entries = []
    for row in sorted(rows, key=lambda item: int(item["round"])):
        entries.append({
            "round": int(row["round"]),
            "status": row["status"],
            "declared_by": ROUND,
            "reason": REASON,
            "until": UNTIL,
        })
    return {"declared_by": ROUND, "reason": REASON, "entries": entries}


def to_text(body):
    document = {
        "declared_by": "R%d" % body["declared_by"],
        "reason": body["reason"],
        "entries": [],
    }
    for entry in body["entries"]:
        document["entries"].append({
            "round": entry["round"],
            "status": entry["status"],
            "declared_by": "R%d" % entry["declared_by"],
            "reason": entry["reason"],
            "until": entry["until"],
        })
    return json.dumps(document, ensure_ascii=True, indent=2) + "\n"


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    for index, arg in enumerate(argv):
        if arg == "--root" and index + 1 < len(argv):
            root = argv[index + 1]
    body = build(root)
    text = to_text(body)
    payload = text.encode("utf-8")
    path = os.path.join(root, RT.DECLARATION_PATH)
    before = os.path.getsize(path) if os.path.exists(path) else 0
    temp = path + ".tmp-pin"
    with open(temp, "wb") as handle:
        handle.write(payload)
    os.replace(temp, path)
    size = os.path.getsize(path)
    if size != len(payload):
        sys.stdout.write("E_PIN_READBACK predicted %d measured %d\n"
                         % (len(payload), size))
        return 1
    report = RT.read(root, "R%d" % ROUND)
    sys.stdout.write("RESIDUE TRIAGE PINNED declared_by=R%d entries=%d "
                     "until=R%d bytes=%d->%d verdict=%s triaged=%d "
                     "untriaged=%d unmatched=%d\n"
                     % (ROUND, len(body["entries"]), UNTIL, before, size,
                        report["verdict"], report["triaged"],
                        report["untriaged"], report["unmatched"]))
    return 0 if report["verdict"] == "TRIAGED" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))