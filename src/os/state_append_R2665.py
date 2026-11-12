"""state_append_R2665 - the R2665 verification window narrative and tokens.

Every number below was measured off this tree in this window: the five
readings at open, the registry target recounted by import, the mixed-tree leg
snapshot read off its own stream byte for byte, the census reread on the
committed tree, and the launcher contract this window ships.
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

NEW_TOKENS = ["D-20261112-13", "D-20261112-14", "D-20261112-15"]

LINES = [
    "2026-11-12 R2665 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2661, pre-registered 653 suites / 4894"
    " criteria because R2661 moved one product src file, one suite and one"
    " registry row). Five readings at open: git status EMPTY at HEAD 0603916a"
    " equal to origin/main with no index.lock; ZERO unreplied @BigDomain rows"
    " in cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed decisions scan read rows=125 tokens=65 with new=3"
    " (D-20261112-13, D-20261112-14, D-20261112-15); the group orders tail"
    " still carries the 2026-11-12 01:5x CEO-PROXY R40 row already recorded as"
    " last_order and judged knowledge-only for this company;"
    " benchmarks_refreshed 2026-11-10 sitting two days inside the seven-day"
    " gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2661"
    " opened=R2661 carried=4 stale=yes open=45 first=1, so the battery was"
    " claimed FIRST per the R2168 mixed-tree rule and no product byte moved in"
    " this window.",
    "R2665 THE THREE NEW DECISIONS WERE JUDGED KNOWLEDGE-ONLY and named:"
    " D-20261112-13 is the batch-59 collection review plus a BigLife erratum"
    " read over eight faces, D-20261112-14 is the cloud-gate wiring executed"
    " inside that window through Tools/cloud-off-gate.ps1 with its three-state"
    " negative controls, and D-20261112-15 is the bm-c claim-executor busy-skip"
    " judgement with its manual poke recorded. None carries a BigDomain"
    " execution face and none was executed here; the baseline advanced by"
    " exactly those three tokens.",
    "R2665 TARGET RE-MEASURED BY IMPORT BEFORE ANY LAUNCH:"
    " reconcile_all.SUITES read 653 suites / 4894 criteria / 653 unique names"
    " / 653 unique paths, byte for byte the registered number, and the registry"
    " stays there because this window adds no suite row.",
    "R2665 THE LEG R2663 LEFT RUNNING WAS ADOPTED, MEASURED AND THEN TERMINATED"
    " AT 647 OF 653 SUITES, AND THE REASON IS NAMED RATHER THAN SMOOTHED: its"
    " stream logs/battery-R2663.stream read 1089780 bytes with 647 suite rows -"
    " 646 PASS and 1 FAIL, the FAIL being reconcile-daily-census exit=2"
    " pass-lines=7 fail-lines=1 criteria=8 12.7s, exactly the pwsh-capture"
    " drift R2663 had already repaired at its birth site - 647 unique names, an"
    " independent criteria recount over those rows summing to 4858 of the 4894"
    " registered, crlf=8405, lone_cr=0 and nul=0. It could never be a verdict"
    " on this tree because the repair commit 6542ad6c landed UNDER it (the"
    " R2168 one-tree law), it was still six suites short after 2000s with one"
    " probe-seam suite measured at roughly 480s on its own, and a second leg"
    " must never share one tree, so the leg was stopped by pid (107564 and its"
    " reconcile_all child 105876, both confirmed gone by command line) and its"
    " stream is kept as the red evidence rather than quoted as green.",
    "R2665 THE RED CAUSE WAS RE-READ ON THE COMMITTED TREE and the census reads"
    " DRIFT-CLEAN, so the repair really holds: src/os/qa_writer_census.py"
    " --check read files=2872 tee=2343 baselined=529 with disappeared=0 and"
    " flags=0, the 529-entry baseline untouched.",
    "R2665 THE JUDGEABLE LEG IS LAUNCHED ON THE TREE THIS COMMIT NAMES, NOT"
    " BEFORE IT: src/os/launch_battery_R2665.py refuses on a moved target, a"
    " non-unique name or path, or an existing evidence file, and Popen-s"
    " src/os/battery_stream.py detached with"
    " CREATE_NO_WINDOW|DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP, keeping the"
    " stream and the pid in SEPARATE files (logs/battery-R2665.stream,"
    " logs/battery-R2665.pid) so qa/reconcile-all-R2665.log is written by the"
    " single writer and never by a shell redirection. The launch runs AFTER"
    " this closeout precisely so the tree cannot move under the leg a second"
    " time - that is the one thing this window refuses to repeat from R2663.",
    "R2665 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - no product byte was written, because the debt gate puts"
    " the owed battery before any further product work and the judgeable leg"
    " has not finished; (b) the battery is NOT green and is NOT claimed green -"
    " reconcile-battery-R2661 stays OPEN at its unmoved 653 suites / 4894"
    " criteria, and the next window ADOPTS the R2665 leg and, if it is red,"
    " keeps it and repairs the birth site alone before any retry; (c) the"
    " mixed-tree leg was TERMINATED rather than run to completion, disclosed"
    " above with its measured counters, because it could never be a verdict and"
    " a second writer must not share the tree; (d) six suites remained and five"
    " of them are the long probe-seam family, one of which measured roughly"
    " 480s alone - a NAMED scheduling fact for the next window rather than a"
    " hang claim; (e) src/os/scan_five_still.py still crashes at its final"
    " [ORD-TOP] print on the GBK console, so the scan was run under"
    " PYTHONIOENCODING=utf-8 - WORKED AROUND, NOT REPAIRED; (f) Docker is"
    " absent on this host so no containerised bring-up of the sandbox faces is"
    " claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on"
    " CEO physical items (merchant id, mini-program appid/secret); (h)"
    " tasks.md was not touched, it is the P-47 canonical board; (i)"
    " BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell"
    " for its S4U re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",
    "R2665 tokens: local=~13k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face read, three new decision tokens judged,"
    " one debt gate read naming the battery, one queue head plus floor read, one"
    " registry target re-measured by import on four axes, one mixed-tree leg"
    " snapshot measured byte for byte on seven axes off its own stream, that leg"
    " stopped by pid with both processes confirmed gone, one census reread on"
    " the committed tree, one refusing launcher written, and the"
    " state/export/board closeout; zero cloud calls and zero external API"
    " touches",
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
    state["last_decision_rows"] = 125
    tokens = list(state.get("last_dec_tokens") or [])
    for tok in NEW_TOKENS:
        if tok not in tokens:
            tokens.append(tok)
    state["last_dec_tokens"] = tokens
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"]
          and len(reread["last_dec_tokens"]) == len(tokens))
    print("APPEND tick=%d lines=%d tokens=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), len(tokens), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
