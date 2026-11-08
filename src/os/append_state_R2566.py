"""R2566 state append (tick 2566, log rows, baselines) with a proved round-trip.

The shipped state_fold layout reader still refuses a json.dump layout (open
since R2522), so this writer PROVES a load+dump round-trip is byte-identical
before it mutates anything, and refuses when it is not.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LOG = [
    "2026-11-08 R2566 VERIFICATION window on the battery the register named "
    "first (reconcile-battery-R2565, pre-registered 612 suites / 4648 "
    "criteria because R2565 moved the registry by one row and shipped a "
    "document, the R2168 mixed-tree rule). Five-silence scan at open: git "
    "status EMPTY at HEAD ebf0820c committed 2026-11-08 15:11:04 with no "
    "index.lock; the ledger scan read unreplied_groups=0 over 0 atbd lines; "
    "the content-addressed decisions diff read new=0 over the stored "
    "baseline at a measured 273 rows / 164 tokens; the group orders tail "
    "read last_tok=2026-11-08 12:06 which is exactly the stored last_order, "
    "so no new order arrived (the scanner also printed max_ts=2026-11-09 on "
    "a row whose own token is the 12:06 one - named here rather than "
    "smoothed); benchmarks 2026-11-03 inside the seven-day gate. The debt "
    "gate read CLAIM-FIRST item=reconcile-battery-R2565 opened=R2565 "
    "carried=1 stale=no open=27 first=1, and the target was RE-MEASURED "
    "before anything ran by importing reconcile_all.SUITES from "
    "src/sandbox: 612 suites and 4648 criteria with 612 unique names and 612 "
    "unique paths, byte for byte the registered number. NOTE DISCLOSED: my "
    "first gate probe passed --round 2566 and was refused E_DGT_BAD_ARGS "
    "because the flag takes the R-prefixed form; both readings are named "
    "rather than only the good one.",

    "2026-11-08 R2566 GREEN ON THE FIRST LEG, measured not quoted: "
    "qa/reconcile-all-R2566.log read 1028863B as delivered before the "
    "follow-up block, utf-8 bom=False crlf=0 lone_cr=0 nul=0, closing line "
    "RUNNER PASS (612/612 suites green, reconcile controls 7/7, 1426.0s), "
    "ZERO FAIL suite rows, zero PASS suite rows with a non-zero exit, and an "
    "INDEPENDENT recount over the 612 PASS suite rows - each carrying its "
    "own criteria= field - summing to EXACTLY 4648 with 612 unique names and "
    "zero duplicates, so the pre-registered total matched by measurement on "
    "both axes. Launched detached through src/os/launch_battery_R2558.py "
    "with its stream and its pid in SEPARATE files and no shell redirection "
    "ever touching qa/ (the ps-utf16 trap). TWO FAIL lines inside the log "
    "are FIXTURE expectations that PASS at exit=2 with the failure detected "
    "and named (member-demo check5 audit row missing, member-tamper FAIL "
    "detected), not suite failures. The leg went green so no red leg exists "
    "to keep and no repair was needed, which is a fact of this run and not a "
    "claim that the battery is safe in general. COST DISCLOSED: the "
    "runner 1426.0s plus the follow-up pair put this window past its "
    "25-minute budget, and my own polling shape repeated three times before "
    "it was replaced by ONE blocking wait - a cost even when each poll "
    "returned a new number.",

    "2026-11-08 R2566 FOLLOW-UP in the designed order: the dry run read "
    "SECTION matrix FAIL first by design at on-disk 59929B against "
    "regenerated 59921B with NO byte written while fingerprint read CLEAN "
    "domains=5, profile read byte-identical and census read DRIFT-CLEAN for "
    "VERDICT R2566 FAIL failing=matrix; docs/sandbox-suite-matrix.md was "
    "then regenerated stamp-aligned from THIS round own green evidence "
    "through src/sandbox/suite_matrix.py --evidence qa/"
    "reconcile-all-R2566.log --stamp-from docs/sandbox-suite-matrix.md to "
    "59921 bytes at 612 suites / 4648 criteria with its green line honestly "
    "reading 612/612 self-describing, --check read byte-identical at rc=0, "
    "and the write leg read all four sections PASS (matrix byte-identical "
    "59921B, fingerprint CLEAN domains=5, profile byte-identical, census "
    "DRIFT-CLEAN) for VERDICT R2566 PASS failing=none (APPENDED 1951B "
    "eol_ok=True).",

    "2026-11-08 R2566 DEBT AND BOARD: reconcile-battery-R2565 was closed "
    "through the shipped debtor at its predicted 176975B -> 176978B (line "
    "309, open 27->26, done 265->266, readback ok). NO successor battery is "
    "owed because this window moved no product src byte and the registry is "
    "unmoved at 612 suites / 4648 criteria, which is exactly what the green "
    "leg measured; the count was re-read by import rather than trusted. The "
    "gate then owed a leader, so product-face-R2566 was appended first=yes "
    "through the shipped appender at its predicted 176978B -> 177292B "
    "(readback ok) naming the next window a PRODUCT face on the queue head "
    "state/queue/tech.md:603 prefix AC-PNDCF1, whose AC-PNDCF1..AC-PNDCF6 "
    "were pinned in that row at R2565 BEFORE any code. queue_head read "
    "claimable=12 at line 603 with the floor MET; no queue row was opened or "
    "closed this window, because a verification window writes no board row. "
    "RESIDUE: residue_triage --check --round R2566 read verdict=TRIAGED "
    "declaration=PINNED declared_by=R2557 residue=300 triaged=300 "
    "untriaged=0 disagrees=0 expired=0 with FIVE UNMATCHED entries named "
    "here rather than hidden.",

    "2026-11-08 R2566 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this "
    "window and none is claimed; the deliverable is a green 612/4648 "
    "battery and a matrix document whose evidence column names THIS round "
    "own green leg with green=612/612 self-describing. (b) The leg was green "
    "so no red leg exists to keep and no repair was needed, which is a fact "
    "of this run. (c) MEASURED DEFECT STILL OPEN from R2522: state.json "
    "stands far above the 78500B waterline so state_fold --check reads "
    "FOLD-DUE and this tool still ships only a --check face, so this append "
    "used a PROVED load+dump round-trip compared byte for byte before any "
    "mutation and the fold stays an OWED obligation seeded as state_fold_run "
    "(AC-SFOLD1..AC-SFOLD6). (d) The decisions baseline and the orders tail "
    "were compared content-addressed rather than by line count, and the "
    "scanner own max_ts=2026-11-09 reading against last_tok=2026-11-08 12:06 "
    "is reported as measured rather than explained away. (e) The residue "
    "reading still carries five UNMATCHED entries and this window declined "
    "to hand-close them. (f) The open rows product-face-R2511, R2513, R2515, "
    "R2517 and R2522 still name product windows whose suites demonstrably "
    "shipped, and the shipped readers still do not age them; this window "
    "declined to mass-close them by hand and did not invent a reading to "
    "hide them. (g) Docker is absent on this host so no containerised "
    "bring-up of the sandbox faces is claimed. (h) The real 19.9 debit and "
    "the real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret). (i) tasks.md was not touched, it is the "
    "P-47 canonical board. (j) The S4U lane re-registration still needs an "
    "ELEVATED shell and D-20261107-14 has classified it as a ceo-pending "
    "physical item with zero chase.",

    "R2566 tokens: local=~8k api=0 api_reason=verification window - five-"
    "silence scan with a content-addressed decisions diff reading new=0, one "
    "debt gate read naming the owed battery, one registry target re-measured "
    "by import after correcting my own flag form, one full 612-suite battery "
    "green on the first leg at the pre-registered 4648 criteria with an "
    "independent criteria recount and a duplicate check, one designed matrix "
    "FAIL with no byte written, one stamp-aligned matrix regeneration from "
    "this round own green evidence checked byte-identical, one four-section "
    "follow-up re-run to a PASS verdict, one debt row closed and one opened "
    "through their shipped writers, one residue check, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    trial = json.dumps(data, indent=1, ensure_ascii=False)
    if trial != text:
        print("REFUSED E_SA_RT_LAYOUT: load+dump is not byte-identical "
              "(on-disk %dB, round-trip %dB)"
              % (len(raw), len(trial.encode("utf-8"))))
        return 3
    before = len(raw)
    data["tick"] = 2566
    for line in LOG:
        data["log"].append(line)
    data["last_decision_rows"] = 273
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    after = os.path.getsize(STATE)
    ok = (back["tick"] == 2566 and len(back["log"]) == len(data["log"]))
    print("STATE tick=2566 log=%d before=%dB after=%dB wrote=%s"
          % (len(back["log"]), before, after, "yes" if ok else "no"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())