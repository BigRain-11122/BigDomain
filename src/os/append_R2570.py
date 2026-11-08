"""R2570 closeout append: prove the byte-exact round-trip, then mutate."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2570 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2569, pre-registered 614 suites / 4660 criteria at "
    "R2569 because that window moved the registry by one row and shipped a "
    "document). Five-silence at open: git status EMPTY at HEAD 448804c4 with "
    "no index.lock and no live reconcile process, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, and the debt gate read CLAIM-FIRST "
    "item=reconcile-battery-R2569 first=1 with open=28. The target was "
    "RE-MEASURED by importing reconcile_all.SUITES BEFORE the launch: 614 "
    "suites and 4660 criteria, byte for byte the registered number. GREEN ON "
    "THE FIRST LEG, measured not quoted (qa/reconcile-all-R2569.log, "
    "1032567B): RUNNER PASS, 614/614 suites green, reconcile controls 7/7, "
    "1363.4s, ZERO FAIL suite rows, 614 PASS suite rows, and an INDEPENDENT "
    "recount over their own criteria fields summing to EXACTLY 4660. "
    "Launched detached through src/os/battery_stream.py with its stream and "
    "pid in separate files and no shell redirection ever touching qa/. The "
    "leg went green so no red leg exists to keep and no repair was needed, "
    "which is a fact of this run and not a claim that the battery is safe in "
    "general.",
    "2026-11-08 R2570 FOLLOW-UP in the designed order: the dry run read "
    "SECTION matrix FAIL BY DESIGN at on-disk 60266B against regenerated "
    "60236B with NO byte written while fingerprint read CLEAN domains=5, "
    "profile read byte-identical and census read DRIFT-CLEAN for VERDICT R2570 "
    "FAIL failing=matrix; docs/sandbox-suite-matrix.md was then regenerated "
    "stamp-aligned from THIS round own green evidence through "
    "src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2569.log "
    "--stamp-from docs/sandbox-suite-matrix.md to 60236 bytes at 614 suites / "
    "4660 criteria with its green line honestly reading 614/614 "
    "self-describing, --check read byte-identical at rc=0, and the write leg "
    "read all four sections PASS for VERDICT R2570 PASS failing=none "
    "(APPENDED 1951B eol_ok=True). DEBT through the shipped writers: "
    "reconcile-battery-R2569 closed at its predicted and measured 178457B -> "
    "178460B (line 314, open 28->27, done 269->270, readback ok). NO "
    "successor battery is owed because this window moved no product src byte "
    "and the registry is unmoved at 614 suites / 4660 criteria, which is "
    "exactly what the green leg measured; the gate then owed a leader, so "
    "product-face-R2570 was appended first=yes at its predicted 178460B -> "
    "178793B (readback ok) naming the next window a PRODUCT face on the queue "
    "head state/queue/tech.md:605 prefix AC-PNDCG1, whose AC-PNDCG1..AC-PNDCG6 "
    "were pinned in that row at R2569 BEFORE any code. queue_head re-read line "
    "605 claimable=11 and queue_floor read FLOOR-MET main=5/5 tech=11/10 "
    "explore=10/10; no queue row was opened or closed, because a verification "
    "window writes no board row.",
    "R2570 tokens: local=~4k api=0 api_reason=verification window - one "
    "five-silence scan, one debt gate read naming the owed battery, one "
    "registry target re-measured by import on both axes, one full 614-suite "
    "battery green on the first leg at the pre-registered 4660 criteria with "
    "an independent criteria recount, one designed matrix FAIL with no byte "
    "written, one stamp-aligned regeneration from this round own green "
    "evidence checked byte-identical, one four-section follow-up to a PASS "
    "verdict, one debt row closed and one opened through their shipped "
    "writers, and the state/export/backlog/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]


def dump(state):
    return json.dumps(state, ensure_ascii=False, indent=1)


def main():
    raw = open(PATH, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    proved = dump(state)
    if proved.encode("utf-8") != raw:
        raise SystemExit("E_ROUNDTRIP: dump differs from disk (%d vs %d bytes)"
                         % (len(proved.encode("utf-8")), len(raw)))
    before = len(state["log"])
    state["tick"] = int(state["tick"]) + 1
    state["log"].extend(LINES)
    out = dump(state).encode("utf-8")
    with open(PATH, "wb") as handle:
        handle.write(out)
    print("ROUNDTRIP-OK bytes=%d tick=%d log=%d->%d after=%d"
          % (len(raw), state["tick"], before, len(state["log"]), len(out)))


if __name__ == "__main__":
    main()