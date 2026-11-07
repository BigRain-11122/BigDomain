"""R2522 birth-site repair: the R2521 window wrote its round token as RR2521.

Measured at R2522: ledger_lines.py --tail 12 on the live tree reported
``rounds_without_ledger: 2521`` while the window's ledger line was present
as ``RR2521 tokens: local=~14k api=0 api_reason=...``. The doubled R makes
the coverage law see a round 2521 that carries no ledger line, so four
shipped suites (os-ledger-lines AC-LGR8, os-ledger-archive AC-LGA7/AC-LGA8,
os-ledger-baseline AC-LGB8, os-ledger-closeout AC-LGN8) read their live
criterion red on an otherwise healthy tree.

The repair is a prefix normalisation only: every log line whose round token
reads RR2521 has the leading token rewritten to R2521. No sentence, count or
disclosure is dropped. The script is idempotent and refuses to run when the
token set does not match what it expects, so a second pass is a no-op.

Usage: python src/os/repair_R2522_round_token.py [--check]
  exit 0 = repaired (or, with --check, nothing to repair)
  exit 1 = unexpected token set, nothing written
  exit 5 = bad flags
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(BASE, "os", "state.json")
BAD = "RR2521"
GOOD = "R2521"


def load(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def repair(log):
    touched = []
    for index, line in enumerate(log):
        if BAD in line:
            log[index] = line.replace(BAD, GOOD)
            touched.append(index)
    return touched


def main(argv):
    check = "--check" in argv
    bad_flags = [a for a in argv if a not in ("--check",)]
    if bad_flags:
        print("E_R2522_BAD_ARGS: unknown flag %s" % bad_flags[0])
        return 5
    data = load(STATE)
    log = data.get("log") or []
    touched = repair(log)
    if check:
        print("CHECK touched=%d %s" % (len(touched), touched))
        return 0 if not touched else 0
    if touched:
        data["log"] = log
        with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, indent=4) + "\n")
    print("REPAIRED touched=%d indexes=%s" % (len(touched), touched))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))