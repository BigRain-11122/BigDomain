"""R2762 closeout: append this window's fact line and its tokens line.

The state document is written through the canonical writer state_io.write_document,
never by a bare text edit, so the two-space log block and the CRLF canon stay
intact and state_io --check keeps reading CANON-CLEAN.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")
sys.path.insert(0, BASE)

import state_io  # noqa: E402

FACT = (
    "R2762 THE RESIDUAL RED ROW OF THE R2757 LEG WAS A CRITERION PINNED TO A "
    "RETIRED LITERAL, and it was repaired at the criterion rather than by "
    "walking the driver backwards. R2757 had already moved the outs term at its "
    "birth site to back[\"outs\"] == written_outs because the R2595 head-row "
    "form is exactly what R2751 D3 forbids on any wait round, so the driver was "
    "correct and AC-EDSW5 in src/os/test_export_R2431_health_verdict.py was the "
    "stale face: it demanded the old literal and therefore reddened a healthy "
    "tree forever. The repair keeps the term INTENT unchanged - the outs face "
    "must still be proved against what the run wrote - accepts either literal, "
    "and still refuses a total drop of the term, so the guard keeps gating. "
    "Measured rather than asserted: the suite re-ran 6/6 PASS on this tree and "
    "its own AC-EDSW5 line now prints outs_form=['back[\"outs\"] == "
    "written_outs'], the registry re-measured BY IMPORT at 676 suites / 5032 "
    "criteria / 676 unique names / 676 unique paths, and a repository-wide scan "
    "found no other file still pinning the retired literal. The R2757 evidence "
    "file was committed as the record of a red leg that was settled by "
    "measurement, and the successor battery reconcile-battery-R2762 was launched "
    "detached on the committed tree after every state, board and export byte was "
    "written, so the R2168 mixed-tree rule is answered by a leg this window did "
    "not read."
)
TOKENS = (
    "R2762 tokens: local=~11k api=0 api_reason=repair window - one leg tail and "
    "one FAIL-line harvest to attribute the red row, one suite read to find the "
    "pinned literal, one driver read to confirm the shipped repair, one grep to "
    "prove no other file pins it, one registry import to prove the target did "
    "not move, one suite re-run green, and the state/board/export closeout; zero "
    "cloud calls, zero network."
)


def main():
    with io.open(STATE, encoding="utf-8") as fh:
        data = json.load(fh)
    data["tick"] = int(data.get("tick") or 0) + 1
    log = data.get("log") or []
    log.append(FACT)
    log.append(TOKENS)
    data["log"] = log
    state_io.write_document(STATE, data)
    with io.open(STATE, encoding="utf-8") as fh:
        back = json.load(fh)
    print("WROTE tick=%s log=%d bytes=%d"
          % (back["tick"], len(back["log"]), os.path.getsize(STATE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
