"""R2152 closeout: advance the tick, append the round narrative and the
machine-readable ledger line, and re-anchor the decision/order baselines
measured in this window. Writes through a temp file plus os.replace.

ASCII source, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

ROUND = 2152
LAST_DECISION_ROWS = 290
LAST_ORDER = "2026-10-26 22:36"
DEC_ADDED = ["D-20261027-%02d" % n for n in range(1, 8)]
TOKENS_LINE = (
    "R2152 tokens: local=~105k api=0 api_reason=five-silence scan + "
    "ledger-line product change (parser + coverage audit + baseline + "
    "CLI gate) + suite 8/8 double-run + wiring + battery + matrix "
    "regen/check + state/export closeout, zero cloud calls")


def build_narrative(battery, matrix, extra):
    return (
        "2026-10-27 R2152 (five-silence scan clean at open: 67 log lines / "
        "30 ledger lines, the three @BigDomain patrol rows in the group "
        "ledger already paid off with zero unreplied, decisions.md 290 "
        "non-empty rows carrying seven new content-addressed tokens "
        "D-20261027-01..07 - the bigmoney bm-a task resume, the BigStream "
        "delivery-gap ruling, two ledger item closures, the docs boundary, "
        "the orders/decisions carriage and the external-audit absence, all "
        "other seats' faces so acknowledged with zero action and the "
        "baseline advanced - group orders baseline unchanged at the "
        "2026-10-26 22:36 dispatch-deck row, benchmarks refreshed "
        "2026-10-27 inside the seven-day gate, tree clean, no index.lock; "
        "the tech head was claimable, so this window claimed it and "
        "registered AC-LGR1..AC-LGR8 in the queue line BEFORE the code: "
        "the round-ledger line machine check). Product: "
        "src/os/ledger_lines.py - the shape the F3 law and the "
        "status-export self_drive face derive from now has a parser "
        "(round/local/api/reason with a pinned gate order), a coverage "
        "audit that cross-checks round narratives against ledger lines, a "
        "tail window, a shipped known-gap baseline (state/ledger_gaps.json) "
        "so only NEW drift turns red, and a CLI gate with exit 0/2/3. New "
        "suite src/os/test_ledger_lines.py covers the canonical parse, nine "
        "bad forms, the coverage law, the tail window, the other line "
        "families, the api discipline, the CLI contract and a live gate "
        "over state.json; SUITE PASS 8/8 double-run byte-identical sha16 "
        "4d26f94c05f5b51e (qa/ledger-lines-R2152-a.log and -b.log, "
        "single-writer UTF-8 LF), wired as os-ledger-lines(8). Battery: "
        + battery + "; matrix " + matrix + ". " + extra + ")")


def main(argv):
    battery = "NOT RUN this window"
    matrix = "not regenerated this window"
    extra = ""
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--battery" and index + 1 < len(argv):
            battery = argv[index + 1]
            index += 2
        elif arg == "--matrix" and index + 1 < len(argv):
            matrix = argv[index + 1]
            index += 2
        elif arg == "--extra" and index + 1 < len(argv):
            extra = argv[index + 1]
            index += 2
        else:
            raise SystemExit("bad argument %r" % arg)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data["tick"] = int(data.get("tick", 0)) + 1
    if data["tick"] != ROUND:
        raise SystemExit("tick %d is not the expected round %d"
                         % (data["tick"], ROUND))
    data["last_decision_rows"] = LAST_DECISION_ROWS
    data["last_order"] = LAST_ORDER
    tokens = [t for t in data.get("last_dec_tokens", "").split(",") if t]
    for token in DEC_ADDED:
        if token not in tokens:
            tokens.append(token)
    data["last_dec_tokens"] = ",".join(tokens)
    data["log"].append(build_narrative(battery, matrix, extra))
    data["log"].append(TOKENS_LINE)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temp = STATE + ".tmp-r2152"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    os.replace(temp, STATE)
    print("tick=%d log_lines=%d tokens=%d"
          % (data["tick"], len(data["log"]), len(tokens)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))