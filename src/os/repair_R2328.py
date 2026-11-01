"""R2328 closeout repair: fold 620 moved the R2314 and R2315 round blocks
into the archive, and the R2312 block had already moved at fold 617, so both
R2312 and R2314 read as live residue with no triage entry (the known
fold-creates-residue law, first measured at R2311 and repaired by hand at
R2318, R2320). Both read DELIVERED off the live stamp table:

  state/queue/tech.md:374  [x] [done 2026-11-01 R2312] closed=yes
  state/queue/tech.md:375  [x] [done 2026-11-01 R2314] closed=yes

Carried by name with a text splice so every existing byte stays intact, one
atomic replace, a predicted byte delta and a read-back proof. A regeneration
through closeout_R2310.py would absorb every other entry's own reason.

Pure ASCII, stdlib only, no network, no clock, writes nothing else.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

RESIDUE = os.path.join(BASE, "state", "residue_triage.json")

CARRIED = [
    {
        "round": 2312,
        "status": "DELIVERED",
        "declared_by": "R2328",
        "reason": "read at R2328 off the live stamp table: "
                  "state/queue/tech.md:374 carries a CLOSED row for the "
                  "gate_decl_append face this round shipped, and the round "
                  "became residue when fold 617 moved its log block into "
                  "the archive",
        "until": 2330,
    },
    {
        "round": 2314,
        "status": "DELIVERED",
        "declared_by": "R2328",
        "reason": "read at R2328 off the live stamp table: "
                  "state/queue/tech.md:375 carries a CLOSED row for the "
                  "gate_decl_identity face this round shipped, and the round "
                  "became residue when fold 620 of this window moved its log "
                  "block into the archive",
        "until": 2330,
    },
]


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write_atomic(path, text, predicted_bytes):
    tmp = path + ".tmp-r2328"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    written = os.path.getsize(tmp)
    if written != predicted_bytes:
        os.remove(tmp)
        raise SystemExit("E_C2328_PREDICT %s wrote %d predicted %d"
                         % (path, written, predicted_bytes))
    os.replace(tmp, path)
    if os.path.exists(tmp):
        raise SystemExit("E_C2328_TEMP %s" % tmp)
    back = os.path.getsize(path)
    if back != predicted_bytes:
        raise SystemExit("E_C2328_READBACK %s %d != %d"
                         % (path, back, predicted_bytes))
    return back


def carry_residue():
    before = read_text(RESIDUE)
    data = json.loads(before)
    rounds = sorted(int(e["round"]) for e in data["entries"])
    for entry in CARRIED:
        if entry["round"] in rounds:
            raise SystemExit("E_C2328_RESIDUE_DUP %d" % entry["round"])
    tail = "\n  ]\n}\n"
    if not before.endswith(tail):
        raise SystemExit("E_C2328_RESIDUE_TAIL")
    body = before[:-len(tail)]
    for entry in CARRIED:
        block = ",\n    {\n"
        block += "      \"round\": %d,\n" % entry["round"]
        block += "      \"status\": \"%s\",\n" % entry["status"]
        block += "      \"declared_by\": \"%s\",\n" % entry["declared_by"]
        block += "      \"reason\": %s,\n" % json.dumps(entry["reason"])
        block += "      \"until\": %d\n    }" % entry["until"]
        body += block
    after = body + "\n  ]\n}\n"
    parsed = json.loads(after)
    if len(parsed["entries"]) != len(rounds) + len(CARRIED):
        raise SystemExit("E_C2328_RESIDUE_PARSE")
    if sorted(int(e["round"]) for e in parsed["entries"])[:len(rounds)] != rounds:
        raise SystemExit("E_C2328_RESIDUE_ORDER")
    predicted = len(after.encode("utf-8"))
    print("residue before=%dB after=%dB entries %d -> %d"
          % (len(before.encode("utf-8")), predicted,
             len(rounds), len(parsed["entries"])))
    write_atomic(RESIDUE, after, predicted)
    print("residue readback ok last rounds %s"
          % (sorted(e["round"] for e in parsed["entries"])[-4:],))


if __name__ == "__main__":
    carry_residue()