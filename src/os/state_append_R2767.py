"""R2767 closeout: append this window's fact line and its tokens line.

Written through the canonical writer state_io.write_document so the two-space
log block and the CRLF canon survive, and state_io --check keeps reading
CANON-CLEAN.
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

FACT_A = (
    "R2767 PRODUCT SLICE: two of the three faces that still rendered without a "
    "size note now carry one, and the note is gated rather than decorative. "
    "BD-PROP-010 coverage moved 5 of 8 -> 7 of 8: preview/ugc-gate-report.json "
    "and preview/ledger-business-report.json now carry a sizes block naming the "
    "byte count of BOTH artifacts they belong to, iterated to a fixed point the "
    "way tools/payment_gate_report.py already does, so neither number can be a "
    "typed literal. Criteria were pre-registered on the board before the code: "
    "AC-UGR9 for the UGC face (--check refuses when either number disagrees with "
    "disk) and AC-LBR9 for the ledger face (a new read-only --check mode that "
    "needs no seeding). Measured: tools/ugc_gate_report.py --check reads VERDICT "
    "PASS 9/9 with json_sizes={'html': 9079, 'json': 6326} equal to disk, and "
    "tools/ledger_business_report.py --check reads PASS fails=0 against "
    "5276B/1061B."
)
FACT_B = (
    "R2767 THE NEGATIVE CONTROL CAUGHT MY OWN BIRTH-SITE DEFECT instead of "
    "confirming the repair, and that is the window's most useful measurement. "
    "The first AC-UGR9 read the sizes block out of the IN-MEMORY data dict, so a "
    "run that writes agreed with itself and a --no-write --check read an empty "
    "block and reddened a healthy document - measured as FAIL AC-UGR9 "
    "json_sizes={} disk=9079/6326 on the restored tree. Repaired at the birth "
    "site: the criterion now parses the LANDED json (json_text already in hand) "
    "and compares that against os.path.getsize, so the gate reads the document "
    "rather than its own memory. Six-check negative control landed as evidence "
    "(qa/BD-PROP-010-R2767.log, driver tmp/negctl_bdprop010.py, kept out of src/ "
    "so the corpus probe suites never see it): a tampered sizes block makes the "
    "real CLI exit 2 with FAIL AC-UGR9; a re-render restores 9/9; a private clean "
    "ledger copy fails 0; a missing block fails 2 with both numbers None; a "
    "ONE-BYTE stale json size fails 1 (the self-referential case, 1014 vs 1061); "
    "and an absent artifact fails with E-listing. VERDICT PASS 6/6 rc=0."
)
FACT_C = (
    "R2767 THE THIRD FACE IS BLOCKED FOR A MEASURED REASON AND THE REPAIR RECIPE "
    "IS NAMED, not deferred vaguely. The API-market face is rendered by "
    "src/sandbox/ledger/apimarket_report.py whose eight pinned suites include "
    "src/sandbox/ledger/test_apimarket_report_json.py:124 asserting "
    "sorted(doc) == [\"attention\", \"report\", \"schema_version\"], so adding a "
    "sizes key there reddens a suite on purpose. That change therefore has to "
    "move the assertion in the same commit and be followed by a full battery, "
    "which this window does not have the budget to answer; the two tools/ faces "
    "carried no such pin. Carried on the board with the line number so the next "
    "window does not re-derive it."
)
FACT_D = (
    "R2767 honest disclosures: (a) ONE product point by the Executive Protocol "
    "scale - two landed artifacts changed and both now carry a gated size note, "
    "but this is metadata on pages that already existed, not a new thing a CEO "
    "can open, and every P-47 business face still waits on CEO physical pieces "
    "(merchant id, mini-program appid/secret); (b) ZERO battery verdict is "
    "claimed - the debt row reconcile-battery-R2762 stays open and the successor "
    "leg is launched detached only after this closeout commits, so the R2168 "
    "mixed-tree rule is answered by a leg this window did not read; (c) "
    "src/os/state.json reads 129344B against the 78500B waterline, so the "
    "waterline stays RED and declared; (d) the dead per-round export hook in "
    "src/os/export_R2431.py is STILL OWED; (e) tmp/negctl_bdprop010.py is a "
    "throwaway driver left in tmp/ rather than added to the already bloated "
    "src/os, and this window added two scripts there (state_append, export) as "
    "every closeout does; (f) tasks.md was not touched, it is the P-47 canonical "
    "board; (g) Docker is absent on this host; (h) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile)."
)
TOKENS = (
    "R2767 tokens: local=~12k api=0 api_reason=product slice on a claimed debt "
    "row - one five-silence scan with the debt gate, the queue head and the "
    "queue floor, one criteria pre-registration, two tool reads, two edits to "
    "tools/ugc_gate_report.py and tools/ledger_business_report.py, two re-renders "
    "and two green --check runs, one six-check negative-control driver with one "
    "birth-site repair and one green re-run, one apimarket blocker read, and the "
    "state/board/export closeout; zero cloud calls and zero external API touches"
)


def main():
    with io.open(STATE, encoding="utf-8") as fh:
        data = json.load(fh)
    data["tick"] = int(data.get("tick") or 0) + 1
    log = data.get("log") or []
    for line in (FACT_A, FACT_B, FACT_C, FACT_D, TOKENS):
        log.append(line)
    data["log"] = log
    state_io.write_document(STATE, data)
    with io.open(STATE, encoding="utf-8") as fh:
        back = json.load(fh)
    print("WROTE tick=%s log=%d bytes=%d"
          % (back["tick"], len(back["log"]), os.path.getsize(STATE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
