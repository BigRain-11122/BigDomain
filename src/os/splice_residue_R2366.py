"""splice_residue_R2366 - one-off splice of the rounds fold 642 created.

DISCLOSED AS A ONE-OFF, same shape as splice_residue_R2355.py. The shipped
residue_triage_append refuses a multi-round splice by design (its plan()
requires the file to re-read TRIAGED after the single entry it adds), so a
fold that leaves several residue rounds cannot go through its CLI. This script
does NOT re-implement the splice: it asks the shipped modules for the
declaration reader, the live reading, the entry shape, the composer and the
judge, declares EVERY round the live reading currently reports untriaged (so
the set is measured, not listed by hand), proves the judge leaves no residue,
and performs ONE atomic replace with a size prediction and a read-back.

The batch capability inside residue_triage_append stays a seeded gap row
(residue_triage_append_batch, AC-RTAB1..AC-RTAB6).

Usage: python src/os/splice_residue_R2366.py [--execute]
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import residue_triage as RT  # noqa: E402
import residue_triage_append as RTA  # noqa: E402

DECLARED_BY = 2366
UNTIL = 2376
REASON = ("fold 642 moved this round's log block into the monthly archive; "
          "its ledger line and its done row are on disk, and stamp_residue "
          "reads DELIVERED on a closed row")

execute = "--execute" in sys.argv

declaration = RTA._declaration(ROOT)
live = RTA._live(ROOT)
declared = set()
for item in declaration["entries"]:
    declared.add(int(item["round"]))
pending = sorted(number for number in live if number not in declared)
print("before entries=%d live=%d pending=%r"
      % (len(declaration["entries"]), len(live), pending))
if not pending:
    print("NOTHING-TO-SPLICE: the live reading reports no untriaged round")
    sys.exit(0)

raw_entries = []
for item in declaration["entries"]:
    raw_entries.append({
        "round": "R%d" % item["round"],
        "status": item["status"],
        "declared_by": "R%d" % item["declared_by"],
        "reason": item["reason"],
        "until": "R%d" % item["until"],
    })
new_entries = []
for number in pending:
    status = live.get(number)
    if status is None:
        raise SystemExit("E_SPLICE_NOT_RESIDUE R%d" % number)
    entry = {"round": number, "status": status,
             "declared_by": DECLARED_BY, "reason": REASON, "until": UNTIL}
    new_entries.append(entry)
    raw_entries.append({
        "round": "R%d" % number, "status": status,
        "declared_by": "R%d" % DECLARED_BY, "reason": REASON,
        "until": "R%d" % UNTIL,
    })
    print("entry R%d status=%s" % (number, status))

candidate = RT.shape({
    "declared_by": "R%d" % declaration["declared_by"],
    "reason": declaration["reason"],
    "entries": raw_entries,
}, "candidate declaration")
live_rows = [{"round": key, "status": live[key]} for key in sorted(live)]
judged = RT.judge(candidate["entries"], live_rows, DECLARED_BY)
print("judged residue=%r disagrees=%d unmatched=%d"
      % (judged["residue"], judged["disagrees"], judged["unmatched"]))
if judged["residue"] or judged["disagrees"]:
    raise SystemExit("E_SPLICE_STILL_OPEN")

path = os.path.join(ROOT, "state", "residue_triage.json")
before = io.open(path, "rb").read()
before_text = before.decode("utf-8")
after_text = before_text
for entry in new_entries:
    after_text = RTA.compose(after_text, entry)
after = after_text.encode("utf-8")
print("bytes before=%d after=%d delta=%d entries %d->%d"
      % (len(before), len(after), len(after) - len(before),
         len(declaration["entries"]), len(candidate["entries"])))

if not execute:
    print("DRY RUN: wrote nothing")
    raise SystemExit(0)

temp = path + ".tmp-splice2366"
with open(temp, "wb") as handle:
    handle.write(after)
os.replace(temp, path)
size = os.path.getsize(path)
if size != len(after):
    raise SystemExit("E_SPLICE_SIZE predicted %d measured %d"
                     % (len(after), size))
report = RT.read(ROOT, "R%d" % DECLARED_BY)
print("READBACK entries=%d verdict=%s untriaged=%d"
      % (report["residue_count"], report["verdict"], report["untriaged"]))
raise SystemExit(0 if report["verdict"] == "TRIAGED" else 2)