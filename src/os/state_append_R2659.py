"""state_append_R2659 - the R2659 verification window narrative and tokens.

Every number below was measured off this tree in this window: the evidence
bytes on eight axes, the registry recount by import, the matrix byte counts on
both sides of the regeneration, the four follow-up verdicts, the debt register
byte counts across both writers, and the fold prediction against its result.
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
    "2026-11-12 R2659 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2657, pre-registered 652 suites / 4888"
    " criteria at R2657 because that window moved one product src file, one"
    " suite and one registry row). Five readings at open: git status carried"
    " ONLY this round own two untracked artifacts (the evidence file and its"
    " one-off launcher) at HEAD c6595f63 equal to origin/main with no"
    " index.lock; ZERO unreplied @BigDomain rows in cph4/evolution-ledger.md"
    " (atbd_lines=0 unreplied_groups=0); the content-addressed decisions scan"
    " read rows=117 tokens=62 with new=0; the group orders tail still carries"
    " the 2026-11-12 01:5x CEO-PROXY R40 row already recorded as last_order"
    " and judged knowledge-only for this company; benchmarks_refreshed"
    " 2026-11-10 sitting two days inside the seven-day gate. debt_gate read"
    " CLAIM-FIRST item=reconcile-battery-R2657 opened=R2657 carried=2 stale=no"
    " open=45 first=1; queue_head named tech line 665 prefix AC-EDXB1"
    " claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10, so"
    " the battery was claimed FIRST per the R2168 mixed-tree rule and no"
    " product byte moved.",
    "R2659 THE LEG AN EARLIER ATTEMPT OF THIS SAME ROUND LAUNCHED IS ADOPTED,"
    " NOT RESTARTED, AND IT IS GREEN BY MEASUREMENT: no reconcile writer was"
    " live by command line (a Get-CimInstance filter over reconcile_all,"
    " battery_stream and both launcher names returned nothing) and the"
    " evidence file was complete, so qa/reconcile-all-R2659.log was re-read on"
    " BYTES rather than quoted - 1101982 bytes at adoption, utf-8 True,"
    " bom=False, crlf=0, lone_cr=0, nul=0, 8648 lines, 652 PASS suite rows"
    " with 652 UNIQUE names and ZERO FAIL suite rows, ZERO non-zero exits, and"
    " an INDEPENDENT criteria recount over the per-row criteria fields summing"
    " to EXACTLY 4888; its closing line reads RUNNER PASS (652/652 suites"
    " green, reconcile controls 7/7, 2194.5s) with TMP RECLAIM 697/697 at"
    " 241.16 MiB, and the file landed through the single writer"
    " battery_stream.py as a utf-8 LF artifact rather than a shell"
    " redirection. THE TARGET WAS RE-MEASURED BY IMPORT BEFORE ANY JUDGEMENT:"
    " reconcile_all.SUITES read 652 suites / 4888 criteria / 652 unique names"
    " / 652 unique paths, byte for byte the registered number.",
    "R2659 R2614 DISCIPLINE CHECKED RATHER THAN ASSUMED: the leg own window"
    " was 09:42:02 to 10:18:37 by its stream length and duration, and the"
    " NEWEST commit on this tree is 09:35:00 (c6595f63), i.e. BEFORE the leg"
    " started, so no commit landed under it and no export-suite re-run was"
    " owed on that ground; the tree the leg measured is the tree this window"
    " closes on.",
    "R2659 FOUR FOLLOW-UP SECTIONS IN THE DESIGNED ORDER through"
    " src/os/battery_followup.py: the dry run read VERDICT FAIL failing=matrix"
    " at on-disk 66886B against regenerated 66872B with NO byte written while"
    " fingerprint read CLEAN domains=5, profile read byte-identical and census"
    " read DRIFT-CLEAN, and that designed refusal appended 1890B;"
    " docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from"
    " THIS round own green evidence through src/sandbox/suite_matrix.py"
    " --evidence qa/reconcile-all-R2659.log --stamp-from"
    " docs/sandbox-suite-matrix.md to 66872 bytes at 652 suites / 4888"
    " criteria with its green line honestly reading 652/652 self-describing,"
    " --check then read byte-identical at rc=0, and the four sections re-ran"
    " to VERDICT R2659 PASS failing=none (APPENDED 1951B eol_ok=True), so the"
    " closing evidence carries both verdicts and reads 1105823 bytes.",
    "R2659 BOARD AND DEBT: the backlog carried NO open adopt row for this"
    " round (the previous window named the battery in the register and the"
    " queue only), so no board row was closed and none was invented; DEBT"
    " through the shipped writers - reconcile-battery-R2657 closed at its"
    " predicted and measured 211177B -> 211180B (line 389, open 45->44, done"
    " 326->327, readback ok) and product-face-R2659 appended first=yes at the"
    " predicted 211180B -> 211483B (readback ok) naming the next window a"
    " PRODUCT face on the queue head state/queue/tech.md:665 prefix AC-EDXB1;"
    " the gate then re-read CLAIM-FIRST item=product-face-R2659 opened=R2659"
    " carried=0 stale=no open=45 first=1, and NO successor battery is owed"
    " because this window moved no product src byte and the registry is"
    " unmoved at 652 suites / 4888 criteria, re-measured by import.",
    "R2659 RESIDUE READ NOT ASSUMED: residue_triage --check --round R2659"
    " reads TRIAGED with residue=1 (the R2165 STAMP-ONLY-OPEN entry) and ONE"
    " inherited UNMATCHED entry (R2653 declared DELIVERED, live=-), the same"
    " shape carried since that round; no declaration was owed for this window"
    " and none was invented.",
    "R2659 FOLD, WITH ONE REFUSAL NAMED: state_fold --check read FOLD-CLEAR"
    " with only 484B of margin against the 78500B gate, so this window own log"
    " could not be appended without folding first; the first two dry runs over"
    " window 81..89 were REFUSED with token-missing (my summary omitted the"
    " fold predicate own token set and my first regex saw only one of them)"
    " and wrote nothing, after which the same window ran with all five tokens"
    " carried - AC-EDXA1 D-TOP O-PROXY R-MET T-CLEAN - as fold 698 at a true"
    " round-block boundary (the complete R2655 verification block ending on"
    " its second-half tokens line), 78016B -> 70119B with margin 8381,"
    " tokens=5 ok=True and archive VERIFIED.",
    "R2659 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - no product byte was written because the debt gate puts"
    " the owed battery before any further product work; (b) the green leg was"
    " AUTHORED BY THE EARLIER ATTEMPT OF THIS SAME ROUND and is adopted and"
    " re-measured here rather than re-run, and its one-off launcher"
    " src/os/launch_battery_R2659.py was DELETED before this commit rather"
    " than staged; (c) the matrix document green line reads 652/652"
    " self-describing from this round own leg, which is a smaller claim than"
    " anything about future suites; (d) residue still carries ONE inherited"
    " UNMATCHED entry and that number is reported rather than cleared; (e)"
    " the fold took three invocations because my first two summaries missed"
    " the predicate own tokens - the refusals are named above, not smoothed;"
    " (f) src/os/scan_five_still.py is still run under"
    " PYTHONIOENCODING=utf-8 because of its [ORD-TOP] GBK crash - WORKED"
    " AROUND, NOT REPAIRED; (g) Docker is absent on this host so no"
    " containerised bring-up of the sandbox faces is claimed; (h) the real"
    " 19.9 debit and the real msgSecCheck still wait on CEO physical items"
    " (merchant id, mini-program appid/secret); (i) tasks.md was not touched,"
    " it is the P-47 canonical board; (j) BigDomain-OSLoop still needs an"
    " ELEVATED shell for its S4U re-registration (carried ceo-pending"
    " physical item loop-s4u-reconcile).",
    "R2659 tokens: local=~9k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face read, one debt gate read naming the"
    " battery, one queue head plus floor read, one liveness check that found"
    " no writer and one byte-level re-measurement of the adopted evidence on"
    " eight axes plus an independent criteria recount, one commit-time check"
    " that no commit landed under the leg, one registry target re-measured by"
    " import on four axes, one designed matrix FAIL with no byte written, one"
    " stamp-aligned regeneration checked byte-identical, one four-section"
    " write leg to a PASS verdict, two debt rows moved through their shipped"
    " writers, one fold executed after two named refusals, and the"
    " state/export closeout; zero cloud calls and zero external API touches",
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
