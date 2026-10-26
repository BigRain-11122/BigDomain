"""R2153 export patch: advance the OSLoop tick row and prepend the round's
results and outs rows. ASCII source, stdlib only, atomic replace.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(REPO, "docs", "status-export.json")
PATTERNS = os.path.join(BASE, "export_consistency_patterns.json")

ROUND = "2153"
RESULT = (
    "R2153: five-silence scan at open (79 bare-LF state lines repaired "
    "first; three ledger patrol rows already paid; 358 decision rows / 212 "
    "content-addressed tokens with zero new; group orders tail advanced to "
    "the 2026-10-27 00:40 bm-b model-slot row on another seat execution "
    "face; benchmarks refreshed today; tree clean) - the P2 tech head was "
    "claimable, so AC-RID1..AC-RID8 were registered in the queue line "
    "BEFORE the code: the double-run identity dialect. src/os/run_identity.py "
    "gives the question one dialect (bytes or conclusions, explicit and "
    "one-directional), reads evidence-pair claims from the body only (a "
    "criterion detail asserts the product, not the pair), verifies a byte "
    "claim and every declared digest against the files, pairs only "
    "-a/-b, -verifya/-verifyb and -run2 (the ambiguous battery -2 re-run "
    "shape is deliberately excluded) and audits qa/ read-only with a "
    "class-level known-defect baseline. Live audit: 63 pairs, 62 clean, "
    "zero conclusion drift, zero false digests, one historical byte-claim "
    "artifact baselined (apimarket-buyermonths-R2100). Suite 8/8 "
    "double-run byte-identical sha16 1155d8b16494c313, wired as "
    "os-run-identity(8); adjacent os-ledger-lines 8/8 and "
    "ledger-census-negative 12/12 green. Full battery and matrix regen NOT "
    "run this window (budget) and are the next round's first item."
)
OUT = [
    "double-run identity dialect helper + qa/ evidence audit "
    "(AC-RID1..AC-RID8)",
    "on",
    "R2153: two incompatible dialects for 'did run two agree with run one' "
    "collapse into one explicit, verified dialect - bytes or conclusions, "
    "never silently upgraded; claims are read from the body only so a "
    "product assertion is not mistaken for an evidence claim; a byte claim "
    "that does not hold is E_FALSE_BYTE_CLAIM and a declared digest is "
    "accepted against either disclosed form (whole file or payload view "
    "without the driver RUN line); a read-only audit of qa/ finds 63 pairs "
    "with zero conclusion drift and one historical artifact baselined "
    "class-wise. Deliverable: src/os/run_identity.py, "
    "state/run_identity_baseline.json, src/os/test_run_identity.py."
]


def main():
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(PATTERNS, "r", encoding="utf-8") as handle:
        label = json.load(handle)["tick_row_label"]

    rows = [r for r in export["results"]
            if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    if len(rows) != 1:
        sys.stderr.write("E_TICKROW: found %d\n" % len(rows))
        return 2
    rows[0][0] = ROUND
    if not (export["results"] and export["results"][0][0] == "R" + ROUND):
        export["results"].insert(0, ["R" + ROUND, RESULT])
    if not (export["outs"] and export["outs"][0][0] == OUT[0]):
        export["outs"].insert(0, OUT)

    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    tmp = EXPORT + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, EXPORT)
    print("tick_row=%s results=%d outs=%d"
          % (ROUND, len(export["results"]), len(export["outs"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())