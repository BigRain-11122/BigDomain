"""One-off fold for R2324: the R2309 and R2310 whole round blocks.

The open state.json stood at 78481B against the 78500B waterline (a 19B
margin), so the fold runs BEFORE any append through the shipped
state_fold law. The window is lines 4..10 on purpose: lines 1..3 are the
three existing fold markers and folding them would demand that their
whole token lists be re-named in a new summary. Whole round blocks only,
so the ledger gate cannot read a split.

After the fold the two moved rounds become live residue (the law first
measured at R2311), so they are spliced into state/residue_triage.json BY
NAME rather than by regenerating the declaration - a regeneration would
absorb every other entry's reason, which is exactly what the R2310 seed
names as the risk of the shortcut.

Pure ASCII, stdlib only, no network, no clock.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

WINDOW_START = 4
WINDOW_END = 10
FOLD_NO = 619
RESERVE = 7000

RESIDUE = os.path.join(ROOT, "state", "residue_triage.json")

CARRIED = [
    {
        "round": 2309,
        "declared_by": "R2324",
        "reason": "read at R2324 off the live stamp table: the R2309 round "
                  "ran the full reconcile battery (qa/reconcile-all-R2309.log) "
                  "and its log block moved into the archive under fold 619",
    },
    {
        "round": 2310,
        "declared_by": "R2324",
        "reason": "read at R2324 off the live stamp table: the R2310 round "
                  "shipped residue_triage plus its pinned declaration and its "
                  "log block moved into the archive under fold 619",
    },
]


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write_atomic(path, text, predicted_bytes):
    tmp = path + ".tmp-r2324"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    written = os.path.getsize(tmp)
    if written != predicted_bytes:
        os.remove(tmp)
        raise SystemExit("E_C2324_PREDICT %s wrote %d predicted %d"
                         % (path, written, predicted_bytes))
    os.replace(tmp, path)
    if os.path.exists(tmp):
        raise SystemExit("E_C2324_TEMP %s" % tmp)
    back = os.path.getsize(path)
    if back != predicted_bytes:
        raise SystemExit("E_C2324_READBACK %s %d != %d"
                         % (path, back, predicted_bytes))
    return back


def do_fold(execute):
    state = json.load(io.open(os.path.join(ROOT, "src", "os", "state.json"),
                              encoding="utf-8"))
    items = state["log"][WINDOW_START - 1:WINDOW_END]
    body = "\n".join(items)
    tokens = sorted(set(SF.PAT.findall(body)))
    summary = ("Fold R2324: log lines %d..%d (the R2309 and R2310 whole "
               "round blocks) moved verbatim to the archive; window tokens: %s"
               % (WINDOW_START, WINDOW_END, " ".join(tokens)))
    print("tokens=%d summary=%dB" % (len(tokens), len(summary)))
    report = SF.fold(ROOT, "R2324", FOLD_NO, WINDOW_START, WINDOW_END,
                     summary, reserve=RESERVE, execute=execute)
    for key in sorted(report):
        if key in ("post_text", "window_lines"):
            continue
        print("%s=%r" % (key, report[key]))
    return report


def carry_residue():
    before = read_text(RESIDUE)
    data = json.loads(before)
    rounds = sorted(int(e["round"]) for e in data["entries"])
    for item in CARRIED:
        if item["round"] in rounds:
            raise SystemExit("E_C2324_RESIDUE_DUP %d" % item["round"])
    tail = "      \"until\": 2330\n    }\n  ]\n}\n"
    if not before.endswith(tail):
        raise SystemExit("E_C2324_RESIDUE_TAIL")
    body = before[:-len(tail) + len("      \"until\": 2330\n    }\n")]
    blocks = []
    for item in CARRIED:
        b = ",\n    {\n"
        b += "      \"round\": %d,\n" % item["round"]
        b += "      \"status\": \"DELIVERED\",\n"
        b += "      \"declared_by\": \"%s\",\n" % item["declared_by"]
        b += "      \"reason\": %s,\n" % json.dumps(item["reason"])
        b += "      \"until\": 2330\n    }"
        blocks.append(b)
    after = body + "".join(blocks) + "\n  ]\n}\n"
    parsed = json.loads(after)
    if len(parsed["entries"]) != len(rounds) + len(CARRIED):
        raise SystemExit("E_C2324_RESIDUE_PARSE")
    if sorted(int(e["round"]) for e in parsed["entries"])[:-len(CARRIED)] != rounds:
        raise SystemExit("E_C2324_RESIDUE_ORDER")
    predicted = len(after.encode("utf-8"))
    print("residue before=%dB after=%dB entries %d -> %d"
          % (len(before.encode("utf-8")), predicted,
             len(rounds), len(parsed["entries"])))
    write_atomic(RESIDUE, after, predicted)
    print("residue readback ok last rounds %s"
          % (sorted(e["round"] for e in parsed["entries"])[-3:],))


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    do_fold(execute)
    if execute:
        carry_residue()