"""R2321 closeout repair: one bookkeeping defect this window's own fold
created, repaired at its birth site with a text splice so every existing byte
stays intact, a predicted byte delta, one atomic replace and a read-back proof.

state/residue_triage.json - this window's fold 619 moved the R2307 log block
into the archive, so R2307 became live residue with no triage entry (the known
fold-creates-residue law, first measured at R2311 and repaired the same way at
R2318 and R2320). R2307 reads DELIVERED off the live stamp table, so it is
carried forward by name rather than by regenerating the declaration, which
would absorb every other entry's reason.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
RESIDUE = os.path.join(ROOT, "state", "residue_triage.json")

CARRIED = {
    "round": 2307,
    "status": "DELIVERED",
    "declared_by": "R2321",
    "reason": "read at R2321 off the live stamp table: "
              "state/queue/tech.md:370 carries a CLOSED row for the "
              "stamp_exempt_append face this round shipped, and the "
              "round became residue only when the R2321 fold 619 "
              "moved its log block into the archive",
    "until": 2330,
}


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write_atomic(path, text, predicted_bytes):
    tmp = path + ".tmp-r2321"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    written = os.path.getsize(tmp)
    if written != predicted_bytes:
        os.remove(tmp)
        raise SystemExit("E_C2321_PREDICT %s wrote %d predicted %d"
                         % (path, written, predicted_bytes))
    os.replace(tmp, path)
    if os.path.exists(tmp):
        raise SystemExit("E_C2321_TEMP %s" % tmp)
    back = os.path.getsize(path)
    if back != predicted_bytes:
        raise SystemExit("E_C2321_READBACK %s %d != %d"
                         % (path, back, predicted_bytes))
    return back


def carry_residue():
    before = read_text(RESIDUE)
    data = json.loads(before)
    rounds = sorted(int(e["round"]) for e in data["entries"])
    if CARRIED["round"] in rounds:
        print("residue: R2307 already carried")
        return
    tail = "      \"until\": 2330\n    }\n  ]\n}\n"
    if not before.endswith(tail):
        raise SystemExit("E_C2321_RESIDUE_TAIL")
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
        raise SystemExit("E_C2321_RESIDUE_PARSE")
    if sorted(int(e["round"]) for e in parsed["entries"])[:-1] != rounds:
        raise SystemExit("E_C2321_RESIDUE_ORDER")
    predicted = len(after.encode("utf-8"))
    print("residue before=%dB after=%dB pred=%dB entries %d -> %d"
          % (len(before.encode("utf-8")), predicted, predicted,
             len(rounds), len(parsed["entries"])))
    write_atomic(RESIDUE, after, predicted)
    print("residue readback ok last rounds %s"
          % (sorted(e["round"] for e in parsed["entries"])[-3:],))


if __name__ == "__main__":
    carry_residue()