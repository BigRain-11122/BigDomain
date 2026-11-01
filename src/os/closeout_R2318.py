"""R2318 closeout repairs: two bookkeeping defects the R2318 battery
found, each repaired at its birth site with a text splice so every
existing byte stays intact, a predicted byte delta, one atomic
replace and a read-back proof.

(1) state/residue_triage.json - the R2317 fold 616 moved the R2302
    and R2303 log blocks into the archive, so both rounds became
    live residue with no triage entry (the known fold-creates-residue
    law, first measured at R2311). Both rounds read DELIVERED off the
    live stamp table, so they are carried forward by name.

(2) state/run_identity_baseline.json - qa/reconcile-all-R2316.log and
    its -run2.log form a correction-rerun pair whose bodies carry the
    per-suite byte claims, so the audit reads the pair as
    E_FALSE_BYTE_CLAIM. Disclosed rather than renamed, following the
    R2233/R2262 precedent.

Pure ASCII, stdlib only, no network, writes nothing else.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

RESIDUE = os.path.join(BASE, "state", "residue_triage.json")
BASELINE = os.path.join(BASE, "state", "run_identity_baseline.json")

CARRIED = [
    {"round": 2302,
     "status": "DELIVERED",
     "declared_by": "R2318",
     "reason": "read at R2318 off the live stamp table: "
               "state/queue/tech.md:367 carries a CLOSED row for the "
               "evidence_variants face this round shipped, and the "
               "round became residue only when the R2317 fold 616 "
               "moved its log block into the archive",
     "until": 2330},
    {"round": 2303,
     "status": "DELIVERED",
     "declared_by": "R2318",
     "reason": "read at R2318 off the live stamp table: "
               "state/queue/tech.md:368 carries a CLOSED row for the "
               "followup_retry_legs face this round shipped, and the "
               "round became residue only when the R2317 fold 616 "
               "moved its log block into the archive",
     "until": 2330},
]

BASELINE_ENTRY = {
    "base": "reconcile-all-R2316",
    "classes": ["E_FALSE_BYTE_CLAIM"],
    "why": "This stem is a BATTERY log, not one suite's double run. "
           "The primary leg is the RED first attempt on the R2315 "
           "tree and the -run2 leg is the post-repair rerun on the "
           "committed repair tree, so the two files legitimately "
           "differ. The byte claims the audit reads are the "
           "per-suite 'byte-identical' sentences inside the bodies, "
           "never this file pair. Disclosed here rather than renaming "
           "an archive that cannot be reproduced to the same bytes.",
}


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write_atomic(path, text, predicted_bytes):
    tmp = path + ".tmp-r2318"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    written = os.path.getsize(tmp)
    if written != predicted_bytes:
        os.remove(tmp)
        raise SystemExit("E_C2318_PREDICT %s wrote %d predicted %d"
                         % (path, written, predicted_bytes))
    os.replace(tmp, path)
    if os.path.exists(tmp):
        raise SystemExit("E_C2318_TEMP %s" % tmp)
    back = os.path.getsize(path)
    if back != predicted_bytes:
        raise SystemExit("E_C2318_READBACK %s %d != %d"
                         % (path, back, predicted_bytes))
    return back


def carry_residue():
    before = read_text(RESIDUE)
    data = json.loads(before)
    rounds = sorted(int(e["round"]) for e in data["entries"])
    if len(rounds) != 187:
        raise SystemExit("E_C2318_RESIDUE_COUNT %d" % len(rounds))
    for entry in CARRIED:
        if int(entry["round"]) in rounds:
            raise SystemExit("E_C2318_RESIDUE_DUP %d" % entry["round"])
    tail = "      \"until\": 2330\n    }\n  ]\n}\n"
    if not before.endswith(tail):
        raise SystemExit("E_C2318_RESIDUE_TAIL")
    body = before[:-len(tail) + len("      \"until\": 2330\n    }\n")]
    rendered = []
    for entry in CARRIED:
        block = ",\n    {\n"
        block += "      \"round\": %d,\n" % entry["round"]
        block += "      \"status\": \"%s\",\n" % entry["status"]
        block += "      \"declared_by\": \"%s\",\n" % entry["declared_by"]
        block += "      \"reason\": %s,\n" % json.dumps(entry["reason"])
        block += "      \"until\": %d\n    }" % entry["until"]
        rendered.append(block)
    after = body + "".join(rendered) + "\n  ]\n}\n"
    parsed = json.loads(after)
    if len(parsed["entries"]) != len(rounds) + len(CARRIED):
        raise SystemExit("E_C2318_RESIDUE_PARSE")
    predicted = len(after.encode("utf-8"))
    print("residue before=%dB after=%dB predicted=%dB entries %d -> %d"
          % (len(before.encode("utf-8")), predicted, predicted,
             len(rounds), len(parsed["entries"])))
    write_atomic(RESIDUE, after, predicted)
    print("residue readback ok rounds %s"
          % (sorted(e["round"] for e in parsed["entries"])[-3:],))


def disclose_baseline():
    before = read_text(BASELINE)
    data = json.loads(before)
    bases = [k["base"] for k in data["known"]]
    if BASELINE_ENTRY["base"] in bases:
        raise SystemExit("E_C2318_BASE_DUP")
    tail = "    }\n  ]\n}"
    if not before.endswith(tail):
        raise SystemExit("E_C2318_BASE_TAIL")
    body = before[:-len(tail) + len("    }\n")]
    block = ",\n    {\n"
    block += "      \"base\": %s,\n" % json.dumps(BASELINE_ENTRY["base"])
    block += "      \"classes\": %s,\n" % json.dumps(
        BASELINE_ENTRY["classes"])
    block += "      \"why\": %s\n    }" % json.dumps(
        BASELINE_ENTRY["why"])
    after = body + block + "\n  ]\n}"
    parsed = json.loads(after)
    if len(parsed["known"]) != len(bases) + 1:
        raise SystemExit("E_C2318_BASE_PARSE")
    predicted = len(after.encode("utf-8"))
    print("baseline before=%dB after=%dB known %d -> %d"
          % (len(before.encode("utf-8")), predicted, len(bases),
             len(parsed["known"])))
    write_atomic(BASELINE, after, predicted)
    print("baseline readback ok last base=%s"
          % parsed["known"][-1]["base"])


if __name__ == "__main__":
    carry_residue()
    disclose_baseline()