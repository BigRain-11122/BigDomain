"""R2248 backlog closeout plus one honest-disclosure log item.

Backlog edits (top of src/os/backlog.md, newest first):
  - the carried R2247 row ('R2248 first item: SEED FIRST') is closed;
  - a done row records the R2248 claim;
  - a carried row names the R2249 first item (battery + matrix).
State edit: one extra log item disclosing that the first layout repair
script overwrote three historical export labels, restored from HEAD.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_BACKLOG = os.path.join(BASE, "backlog.md")
P_STATE = os.path.join(BASE, "state.json")

CARRIED_OLD = "- [ ] [carried 2026-10-29 R2247] R2248 first item: SEED FIRST"

NEW_ROWS = [
    "- [ ] [carried 2026-10-29 R2248] R2249 first item: RUN THE BATTERY, do "
    "not open a new product face. This window changed src/os "
    "(debt_register.py, test_debt_register.py, evidence_R2248.py, "
    "seed_queue_R2248.py, closeout/fix helpers), src/sandbox/reconcile_all.py "
    "and both queue files, so the full reconcile battery plus the suite-matrix "
    "regeneration must run on the committed tree (R2168 mixed-tree rule). "
    "Expect the matrix to grow by one suite (os-debt-register, 8 criteria).",
    "- [x] [done 2026-10-29 R2248] P2 tech head claim (R2240-c seed; criteria "
    "AC-DEBT1..AC-DEBT6 pre-registered in state/queue/tech.md BEFORE the code, "
    "AC-DEBT7/AC-DEBT8 added in the same window and disclosed): carried debt "
    "becomes a register. Product: state/debt.md (column-0 rows, pipe-separated "
    "key=value, one first item, open/closed sections) plus "
    "src/os/debt_register.py (parse with unknown/duplicate/missing-key refusal, "
    "three-window staleness alarm with --round, honest empty and honest absent, "
    "CLI 0/2/3/4/5, byte-stable --json over eleven pinned keys). Evidence: "
    "SUITE PASS 8/8 double-run byte-identical criterion sha16 "
    "8230EE0683CCB6EB (qa/debt-register-R2248-a.log / -b.log, 800B each, "
    "single writer utf-8 LF by src/os/evidence_R2248.py); wired "
    "os-debt-register(8); five adjacent os suites green "
    "(qa/regression-R2248.log, fails=0). Live reading: DEBT REGISTER open=2 "
    "done=2 first=reconcile-battery-and-matrix stale=1 carried=17 "
    "verdict=DEBT-STALE. The first suite run read 7/8 on a real shape defect "
    "(done rows missing carried/stale) fixed in the implementation, not by "
    "widening the criterion.",
    "- [x] [done 2026-10-29 R2248] the R2247 seeding duty discharged: ten seed "
    "rows landed (five tech: debt_append, queue_row, round_evidence, state_seq, "
    "seed_anchor; five explore: api_category_restock_months, "
    "api_buyer_question_months, api_seller_delist_months, "
    "api_market_seller_churn_months, api_market_discount_months), every anchor "
    "zero-occupancy checked with git grep -F against HEAD (rc=1). The floor "
    "gauge now reads QUEUE FLOOR main=5/5 tech=10/10 explore=10/10 "
    "verdict=FLOOR-MET shortfall=0, up from FLOOR-DEBT shortfall=10.",
]

LOG_ITEM = (
    "R2248 honest disclosure: the first layout repair (src/os/fix_R2248.py) "
    "matched any export results row whose body merely mentions 'tick' and "
    "overwrote three historical round labels (R2167, R2149, R2212) with the "
    "live tick. The project's own check_export_consistency caught only the "
    "tick row, so the corruption was found by reading the patched rows back "
    "rather than by the checker. src/os/fix_R2248b.py restored all three "
    "labels from HEAD by row-body match, advanced exactly one row (the pinned "
    "tick-row label) and refuses unless exactly one match exists; the reading "
    "is now restored=3 tick_rows=1 and the checker returns 21 pass / 0 fail. "
    "The loose match was the defect, not the checker."
)


def main():
    with io.open(P_BACKLOG, "r", encoding="utf-8") as handle:
        text = handle.read()
    lines = text.split("\n")
    closed = 0
    for index, line in enumerate(lines):
        if line.startswith(CARRIED_OLD):
            lines[index] = line.replace(
                "- [ ] [carried 2026-10-29 R2247]",
                "- [x] [done 2026-10-29 R2248]", 1)
            closed += 1
            break
    if closed != 1:
        print("E_BL_NO_CARRIED_ROW")
        return 1
    body = "\n".join(NEW_ROWS) + "\n" + "\n".join(lines)
    data = body.encode("utf-8")
    with io.open(P_BACKLOG, "wb") as handle:
        handle.write(data)
    print("BACKLOG closed=%d appended=%d bytes=%d"
          % (closed, len(NEW_ROWS), len(data)))

    with io.open(P_STATE, "r", encoding="utf-8") as handle:
        state = json.loads(handle.read())
    if LOG_ITEM in state["log"]:
        print("STATE disclosure already present")
        return 0
    state["log"].append(LOG_ITEM)
    body = json.dumps(state, indent=2, ensure_ascii=False)
    if not body.endswith("\n"):
        body += "\n"
    # Canonical log item indent is 16 spaces (state_io ITEM_INDENT).
    out = []
    inside = False
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith('"log": ['):
            inside = True
            out.append(line)
            continue
        if inside and stripped == "]":
            inside = False
            out.append(line)
            continue
        if inside and (len(line) - len(line.lstrip(" "))) == 4:
            out.append(" " * 16 + stripped)
            continue
        out.append(line)
    body = "\n".join(out)
    data = body.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    with io.open(P_STATE, "wb") as handle:
        handle.write(data)
    print("STATE items=%d bytes=%d" % (len(state["log"]), len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())