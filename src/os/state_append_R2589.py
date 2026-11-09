"""state_append_R2589 - append this round log lines and advance the tick.

The layout is indent=1 with no trailing newline; the round-trip is proved
before any byte is written, so a refusal leaves the file untouched.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-09 R2589 VERIFICATION window on the battery the register named first "
    "(reconcile-battery-R2588, pre-registered 626 suites / 4732 criteria at R2588). "
    "Five-silence at open: git status carried exactly TWO untracked files from an "
    "INTERRUPTED ATTEMPT of this same round (qa/reconcile-all-R2588-retry.log and "
    "src/os/launch_battery_R2589_retry.py) with no battery process live, zero "
    "@BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions "
    "scan read 58 tokens against the stored baseline with new=1 (D-20261109-04), the "
    "group orders tail unchanged at 2026-11-09 00:59, benchmarks 2026-11-03 inside "
    "the seven-day gate. The debt gate read CLAIM-FIRST item=reconcile-battery-R2588 "
    "first=1 open=36, so the battery was owed on this committed tree BEFORE any "
    "product byte (the R2168 mixed-tree rule); queue_head named tech line 623 prefix "
    "AC-PNAD1 claimable=13 and queue_floor read FLOOR-MET at 5/5, 13/10, 10/10.",

    "2026-11-09 R2589 THE NEW DECISION WAS JUDGED AND ACKNOWLEDGED WITHOUT "
    "EXECUTION: D-20261109-04 records a group production-queue supply gap "
    "(PRODUCTION-QUEUE.jsonl OPEN=0 with 17 long-standing UNVERIFIED cards) and "
    "dispatches ONE real task to @bm-a to verify them with a 24h receipt window. It "
    "is a group fleet and dispatch face with no BigDomain execution surface, so it is "
    "recorded as knowledge and the token baseline advances by exactly that one token; "
    "no BigDomain task is dispatched from it.",

    "2026-11-09 R2589 A PRIOR ATTEMPT OF THIS ROUND HAD ALREADY RUN THE BATTERY GREEN "
    "AND IS ADOPTED, NOT RE-RUN: qa/reconcile-all-R2588-retry.log was on disk with no "
    "battery process live (no python process carried reconcile_all or battery_stream "
    "in its command line), so the leg was re-measured rather than restarted and the "
    "one-off launcher was DELETED before the commit instead of staged. MEASURED NOT "
    "QUOTED: 1059158B, utf-8 bom=False crlf=0 nul=0, 8215 lines, closing line RUNNER "
    "PASS (626/626 suites green, reconcile controls 7/7, 2022.2s), 626 PASS suite "
    "rows with 626 UNIQUE names, and an INDEPENDENT recount over their own criteria "
    "fields summing to EXACTLY 4732 - byte for byte the pre-registered number. The "
    "registry was re-read by importing reconcile_all.SUITES at 626 suites / 626 "
    "unique, matching on both axes. TMP RECLAIM candidates=932 removed=932 busy=0 "
    "failed=0 reclaimed=326.59 MiB.",

    "2026-11-09 R2589 FOLLOW-UP IN THE DESIGNED ORDER: the dry run read SECTION "
    "matrix FAIL first BY DESIGN at on-disk 63018B against regenerated 62998B with NO "
    "byte written while fingerprint read PASS CLEAN domains=5, profile read PASS "
    "byte-identical and census read PASS DRIFT-CLEAN, for VERDICT R2588 FAIL "
    "failing=matrix; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned "
    "from THIS round own green evidence through src/sandbox/suite_matrix.py "
    "--evidence qa/reconcile-all-R2588-retry.log --stamp-from the existing document to "
    "62998 bytes at 626 suites / 4732 criteria with its green line honestly reading "
    "626/626 self-describing, --check read byte-identical at rc=0, and the four "
    "sections re-ran to VERDICT R2588 PASS failing=none (APPENDED 1951B "
    "eol_ok=True).",

    "2026-11-09 R2589 DEBT AND BOARD: reconcile-battery-R2588 was closed through the "
    "shipped debtor at its predicted and measured 187667B -> 187670B (line 341, open "
    "36->35, done 287->288, readback ok). The gate then read verdict=OPEN-NONE with "
    "first_count=0, so product-face-R2589 was appended first=yes at its predicted and "
    "measured 187670B -> 188057B (readback ok) naming the next window a PRODUCT face "
    "on the queue head state/queue/tech.md:623 prefix AC-PNAD1, whose AC-PNAD1..AC-"
    "PNAD6 were pinned in that row at R2588 BEFORE any code. NO successor battery is "
    "owed: this window moved no product src byte and the registry is unmoved at 626 "
    "suites / 4732 criteria, which is exactly what the green leg measured. No queue "
    "row was opened or closed, because a verification window writes no board row; "
    "queue_head still reads line 623 claimable=13 and queue_floor FLOOR-MET at 5/5, "
    "13/10, 10/10.",

    "R2589 honest disclosures: (a) ZERO product points on the Executive Protocol "
    "scale - nothing a CEO could open was built this window and none is claimed; the "
    "deliverable is a green 626/4732 battery on disk, a matrix document whose "
    "evidence column names THIS round own green leg, and one closed debt row with one "
    "opened; (b) the window opened on an INTERRUPTED ATTEMPT of the same round whose "
    "battery had already finished green, so that leg is adopted and re-measured "
    "instead of authored here and the launcher was deleted rather than committed; (c) "
    "the leg went green so no red leg exists to keep and no repair was needed, which "
    "is a fact of this run and not a claim that the battery is safe in general; (d) "
    "state.json read 77220B against the 78500B waterline at open (FOLD-CLEAR margin "
    "1280) and this append was checked for the indent=1 no-trailing-newline "
    "round-trip before mutation; the append pushes the file past the gate, so a fold "
    "at a true round-block boundary is run in this window and its result is reported "
    "by the next line rather than assumed here; (e) last_decision_rows stands at 284 "
    "and the content-addressed token set advanced by exactly one judged token; (f) "
    "Docker is absent on this host so no containerised bring-up of the sandbox faces "
    "is claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items (merchant id, mini-program appid/secret); (h) tasks.md was not "
    "touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an ELEVATED shell (carried ceo-pending physical item "
    "loop-s4u-reconcile).",

    "R2589 tokens: local=~9k api=0 api_reason=verification window - one five-silence "
    "scan with the content-addressed decisions scan, the group orders tail and the "
    "ledger face actually read, one new decision token read and judged knowledge-only, "
    "one debt gate read naming the battery, one queue head and floor read, one "
    "626-suite target re-measured by import on both axes, one full 626-suite leg "
    "adopted from an interrupted attempt and re-measured on its runner, encoding, "
    "uniqueness and criteria faces with an independent recount to exactly 4732, one "
    "designed matrix FAIL with no byte written, one stamp-aligned regeneration from "
    "this round own green evidence checked byte-identical, one four-section follow-up "
    "to a PASS verdict, one debt row closed and one opened through their shipped "
    "writers, and the state/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    if json.dumps(doc, ensure_ascii=False, indent=1) != text:
        print("REFUSED layout round-trip mismatch")
        return 3
    doc["log"].extend(LINES)
    doc["tick"] = int(doc.get("tick", 0)) + 1
    tokens = doc.setdefault("last_dec_tokens", [])
    if "D-20261109-04" not in tokens:
        tokens.append("D-20261109-04")
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = back["tick"] == doc["tick"] and back["log"][-1] == LINES[-1]
    print("APPEND tick=%d log_rows=%d before=%dB after=%dB ok=%s"
          % (back["tick"], len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())