"""state_append_R2665_push - the R2665 push, fold and export receipt.

Landed BEFORE the judgeable battery leg is launched, so that the leg runs on
a tree nothing moves under (the R2168 one-tree law, and the exact thing this
window refused to repeat from R2663).
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

LINE = (
    "R2665 push, fold and export: git push origin main SUCCEEDED"
    " (0603916a..bcf85c6b main -> main) and git rev-parse read HEAD equal to"
    " origin/main at bcf85c6b with an EMPTY git status, so the mixed-tree leg"
    " measurement, the census reread, the launcher and the board row are"
    " delivered; this receipt line lands in the follow-up commit it describes."
    " FOLD 700 ran at a true round-block boundary over log items 84..92 (the"
    " complete R2661 product-round block) after a dry run that agreed exactly,"
    " 83697B -> 75092B with 18 tokens carried, archive VERIFIED - and the"
    " summary was then REWORDED IN PLACE because ledger_lines read"
    " new_missing=2661: the summary opened 'R2661 product-round block folded"
    " into the archive', which FOLD_SUMMARY_RE cannot classify and"
    " NARRATIVE_RE reads as a round with no ledger line, so it was rewritten to"
    " the shipped 'R2661 fold of log items 84..92 ... all 18 tokens preserved"
    " verbatim' form, 75092B -> 75133B, the same 18 tokens and no value"
    " changed, after which ledger_lines read VERDICT CLEAN with new_missing"
    " none and new_orphan none and state_fold --check read FOLD-CLEAR at 75133B"
    " against the 78500B gate with margin 3367. The export was refreshed AFTER"
    " the state append (the R2449/R2433 ordering law) through"
    " src/os/export_R2635.py to 404654 bytes at tick 2658 with queue=CURRENT"
    " and queue_drifted=(none), and check_export_consistency read pass=21"
    " fail=0 VERDICT PASS with the three CEO lines derived rather than typed."
    " THE JUDGEABLE LEG IS LAUNCHED AFTER THIS COMMIT rather than before it,"
    " which is the one scheduling law this window refuses to break: nothing"
    " lands under it once it starts. The debt row reconcile-battery-R2661 stays"
    " OPEN at its unmoved 653 suites / 4894 criteria, and the queue head this"
    " window leaves behind is state/queue/tech.md:666 prefix AC-EDXC1."
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["log"].append(LINE)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = reread["log"][-1] == LINE and reread["tick"] == state["tick"]
    print("APPEND-RECEIPT tick=%d bytes %d -> %d readback=%s"
          % (reread["tick"], before, len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
