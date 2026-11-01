"""R2322 closeout repair: one bookkeeping defect this window's fold
created, repaired at its birth site with a text splice so every existing
entry stays byte-intact, a predicted byte delta, one atomic replace and
a read-back proof.

state/residue_triage.json - fold 620 this window ran moved the last live
lines of the R2308 block into the archive (its round line had already
been archived at R2315), so R2308 became live residue with no triage
entry (the known fold-creates-residue law, first measured at R2311 and
repaired the same way at R2318 and R2320). R2308 reads DELIVERED off the
live stamp table: state/queue/tech.md:371 carries
[done 2026-11-01 R2308] for the evidence_output_audit face that round
shipped. It is carried forward BY NAME rather than by regenerating the
whole declaration, because a regeneration would absorb every other
entry's reason - the risk the R2310 seed already names.

Pure ASCII, stdlib only, no network, no clock, writes nothing else.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

RESIDUE = os.path.join(BASE, "state", "residue_triage.json")

CARRIED = {
    "round": 2308,
    "status": "DELIVERED",
    "declared_by": "R2322",
    "reason": "read at R2322 off the live stamp table: "
              "state/queue/tech.md:371 carries a CLOSED row "
              "([done 2026-11-01 R2308]) for the evidence_output_audit face "
              "this round shipped, and the round became residue when the "
              "R2322 fold 620 moved its last live log lines into the "
              "archive after the R2315 fold 615 had already archived its "
              "round line",
    "until": 2330,
}


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write_atomic(path, text, predicted_bytes):
    tmp = path + ".tmp-r2322"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    written = os.path.getsize(tmp)
    if written != predicted_bytes:
        os.remove(tmp)
        raise SystemExit("E_C2322_PREDICT %s wrote %d predicted %d"
                         % (path, written, predicted_bytes))
    os.replace(tmp, path)
    if os.path.exists(tmp):
        raise SystemExit("E_C2322_TEMP %s" % tmp)
    back = os.path.getsize(path)
    if back != predicted_bytes:
        raise SystemExit("E_C2322_READBACK %s %d != %d"
                         % (path, back, predicted_bytes))
    return back


def carry_residue():
    before = read_text(RESIDUE)
    data = json.loads(before)
    rounds = sorted(int(e["round"]) for e in data["entries"])
    if CARRIED["round"] in rounds:
        raise SystemExit("E_C2322_RESIDUE_DUP %d" % CARRIED["round"])
    tail = "      \"until\": 2330\n    }\n  ]\n}\n"
    if not before.endswith(tail):
        raise SystemExit("E_C2322_RESIDUE_TAIL")
    body = before[:-len(tail) + len("      \"until\": 2330\n    }\n")]
    block = ",\n    {\n"
    block += "      \"round\": %d,\n" % CARRIED["round"]
    block += "      \"status\": \"%s\",\n" % CARRIED["status"]
    block += "      \"declared_by\": \"%s\",\n" % CARRIED["declared_by"]
    block += "      \"reason\": %s,\n" % json.dumps(CARRIED["reason"])
    block += "      \"until\": %d\n    }" % CARRIED["until"]
    after = body + block + "\n  ]\n}\n"
    parsed = json.loads(after)
    if len(parsed["entries"]) != len(rounds) + 1:
        raise SystemExit("E_C2322_RESIDUE_PARSE")
    if sorted(int(e["round"]) for e in parsed["entries"])[:-1] != rounds:
        raise SystemExit("E_C2322_RESIDUE_ORDER")
    predicted = len(after.encode("utf-8"))
    print("residue before=%dB after=%dB pred=%dB entries %d -> %d"
          % (len(before.encode("utf-8")), predicted, predicted,
             len(rounds), len(parsed["entries"])))
    write_atomic(RESIDUE, after, predicted)
    print("residue readback ok last rounds %s"
          % (sorted(e["round"] for e in parsed["entries"])[-3:],))


if __name__ == "__main__":
    carry_residue()