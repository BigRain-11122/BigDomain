"""state_append_R2663 - the R2663 verification window narrative and tokens.

Every number below was measured off this tree in this window: the five readings
at open, the registry target recounted by import, the first leg suite counters
read off its own stream, the census drift reproduced in-process twice (before
and after the repair), the repair byte counts, the fold prediction and result.
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

LINES = [
    "2026-11-12 R2663 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2661, pre-registered 653 suites / 4894"
    " criteria at R2661 because that window moved one product src file, one"
    " suite and one registry row). Five readings at open: git status EMPTY at"
    " HEAD 3f78e2cb equal to origin/main with no index.lock; ZERO unreplied"
    " @BigDomain rows in cph4/evolution-ledger.md (atbd_lines=0"
    " unreplied_groups=0); the content-addressed decisions scan read rows=117"
    " tokens=62 with new=0; the group orders tail still carries the"
    " 2026-11-12 01:5x CEO-PROXY R40 row already recorded as last_order and"
    " judged knowledge-only for this company; benchmarks_refreshed 2026-11-10"
    " sitting two days inside the seven-day gate. debt_gate read CLAIM-FIRST"
    " item=reconcile-battery-R2661 opened=R2661 carried=2 stale=no open=45"
    " first=1; queue_head named tech line 666 prefix AC-EDXC1 claimable=15 and"
    " queue_floor read FLOOR-MET at 5/5, 15/10, 10/10, so the battery was"
    " claimed FIRST per the R2168 mixed-tree rule and no product byte moved.",
    "R2663 TARGET RE-MEASURED BY IMPORT BEFORE THE LAUNCH:"
    " reconcile_all.SUITES read 653 suites / 4894 criteria / 653 unique names"
    " / 653 unique paths, byte for byte the registered number. One one-off"
    " launcher refused on a moved target, a non-unique name or path, or an"
    " existing evidence file, Popen-ed src/os/battery_stream.py with"
    " CREATE_NO_WINDOW|DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP, and put the"
    " stream and the pid in SEPARATE files under logs/"
    " (battery-R2663.stream, battery-R2663.pid, pid 107564 with its"
    " reconcile_all child 105876) so qa/ is written by the single writer and"
    " never by a shell redirection. MEASURED at open+45s the leg had closed"
    " six suites with the hub ledger face green.",
    "R2663 FIRST LEG IS RED AND IS KEPT AS EVIDENCE, NAMED NOT GLOSSED:"
    " reconcile-daily-census read SUITE FAIL 7/8 at exit=2 with"
    " cd7-live-real-tree label=drift(exit=2). The cause was MEASURED"
    " INDEPENDENTLY in-process rather than guessed: the shipped qa writer"
    " census read flags=2 new-dialect class=pwsh-capture on"
    " qa/limits-export-composed-landed-next-R2661.log and"
    " qa/limits-export-composed-landed-sixth-wave-after-R2661.log - two"
    " evidence logs landed by the PREVIOUS window carried CRLF (4 and 5 bare"
    " CRLF pairs) against the utf-8 bare-LF contract, with files=2873 tee=2342"
    " baselined=529.",
    "R2663 BIRTH-SITE REPAIR COMMITTED ALONE (6542ad6c) BEFORE ANY RETRY:"
    " src/os/repair_dialect_R2530.py rewrote exactly those two files through a"
    " temp file plus os.replace - 612B -> 608B and 755B -> 750B, bom=False,"
    " nul=0, crlf=0, bare_cr=0 on both - after which the census re-read"
    " flags=0 DRIFT-CLEAN at files=2873 tee=2344 baselined=529 with the"
    " 529-entry baseline untouched and disappeared=0, and the red suite re-read"
    " SUITE PASS 8/8 alone. Nothing was loosened and no criterion was widened:"
    " the repaired bytes carry the same text in the contract dialect.",
    "R2663 ONE CLEANUP NAMED RATHER THAN LEFT LYING: a bounded attempt to read"
    " the drift detail through 'reconcile_daily.py --check' produced no output"
    " inside the shell five-minute silence window and was cancelled, and its"
    " qa/reconcile-daily-20261112.log artifact was DELETED rather than kept or"
    " quoted (the R2493 precedent), so the census it fed still reads"
    " DRIFT-CLEAN at flags=0.",
    "R2663 RETRY OWED AND NOT LAUNCHED HERE, with the reason stated: the first"
    " leg is STILL LIVE at closeout (pid 107564, 330 PASS suite rows and 1 FAIL"
    " row on its stream) and two battery writers must never share one tree, so"
    " a fresh leg was NOT started beside it. The row"
    " reconcile-battery-R2661 STAYS OPEN at its unmoved 653 suites / 4894"
    " criteria, which is correct because this window changed two evidence files"
    " and no product src byte and no registry row; the next window ADOPTS the"
    " running leg as the red evidence, confirms the repair is on the committed"
    " tree, and relaunches one leg there (the R2609/R2647 precedent).",
    "R2663 FOLD 699 AT A TRUE ROUND-BLOCK BOUNDARY: the check read FOLD-CLEAR"
    " with only 213B of margin against the 78500B gate, so this window own log"
    " could not be appended without folding first. The dry run REFUSED with"
    " token-missing until the summary carried all EIGHT tokens the predicate"
    " asks for (AC-EDXA1 AC-EDXB1 D-CLEAR D-TOP O-PROXY O-visible R-MET"
    " T-CLEAN), then agreed exactly and the execute ran over log items 83..92"
    " (the complete R2659 verification block ending on its push and export"
    " receipt): 78287B -> 70070B with margin 8430, tokens=8 ok=True and archive"
    " VERIFIED.",
    "R2663 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - no product byte was written because the debt gate puts"
    " the owed battery before any further product work and that leg is still"
    " live at closeout; (b) the battery is NOT green and is NOT claimed green -"
    " its first leg carries one FAIL row and the green retry has not run, so"
    " reconcile-battery-R2661 stays OPEN at 653 suites / 4894 criteria; (c) the"
    " red was born in the PREVIOUS window own evidence transport (the fifth"
    " recorded instance of that trap in this repository) and it was repaired at"
    " its birth site rather than at the detector; (d) the repair was committed"
    " while the first leg was still running, which is disclosed rather than"
    " hidden - it cannot launder that leg into a verdict, because the leg"
    " already recorded its FAIL row and is reported as red; (e)"
    " src/os/scan_five_still.py still crashes at its final [ORD-TOP] print on"
    " the GBK console, so the scan was run under PYTHONIOENCODING=utf-8 -"
    " WORKED AROUND, NOT REPAIRED; (f) Docker is absent on this host so no"
    " containerised bring-up of the sandbox faces is claimed; (g) the real 19.9"
    " debit and the real msgSecCheck still wait on CEO physical items (merchant"
    " id, mini-program appid/secret); (h) tasks.md was not touched, it is the"
    " P-47 canonical board; (i) BigDomain-OSLoop still reads InteractiveToken"
    " and needs an ELEVATED shell for its S4U re-registration (carried"
    " ceo-pending physical item loop-s4u-reconcile).",
    "R2663 tokens: local=~11k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face read, one debt gate read naming the"
    " battery, one queue head plus floor read on all three lines, one registry"
    " target re-measured by import on four axes, one refusing one-off launcher"
    " written and one detached leg launched with its stream and pid in separate"
    " files, one red suite reproduced in-process twice with its cause read off"
    " the shipped census, one birth-site repair through the shipped rewrite"
    " face with byte-level readback, one commit carrying that repair alone, one"
    " cancelled bounded probe whose artifact was deleted, one fold executed"
    " after one named token-missing refusal, and the state/export closeout;"
    " zero cloud calls and zero external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["tick"] = int(state.get("tick", 0)) + 1
    for line in LINES:
        state["log"].append(line)
    state["last_order"] = "2026-11-12 01:5x"
    state["last_decision_rows"] = 117
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"])
    print("APPEND tick=%d lines=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
