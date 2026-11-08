"""R2584 state append: tick + the round log block, layout proved before mutation."""

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(ROOT)
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-09 R2584 VERIFICATION window on the battery the register named first "
    "(reconcile-battery-R2583, pre-registered 622 suites / 4708 criteria). Five-silence "
    "at open: git status carried exactly TWO untracked files from an INTERRUPTED "
    "ATTEMPT of this same round (qa/reconcile-all-R2584.log and "
    "src/os/launch_battery_R2584.py), zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions scan read 161 tokens "
    "against the 197-token stored baseline with new=0 over 379 rows, the group orders "
    "tail max_ts read 2026-11-09 12:00 which is a DUE DATE INSIDE the 2026-11-08 06:0x "
    "committee row rather than a new order (named rather than smoothed), so last_order "
    "stays at the 2026-11-09 00:59 BigStream row, benchmarks 2026-11-03 inside the "
    "seven-day gate. The debt gate read CLAIM-FIRST item=reconcile-battery-R2583 "
    "first=1 open=35, and queue_head named tech line 617 prefix AC-PNAA1 claimable=12 "
    "with queue_floor FLOOR-MET at 5/5, 12/10, 10/10.",

    "2026-11-09 R2584 A PRIOR ATTEMPT OF THIS ROUND HAD ALREADY RUN THE BATTERY GREEN "
    "AND IS ADOPTED, NOT RE-RUN: qa/reconcile-all-R2584.log was left on disk by that "
    "attempt and no battery process was live at open (no python process on the host "
    "carried reconcile_all or battery_stream in its command line), so the leg was "
    "re-measured rather than restarted and the launcher was DELETED before the commit "
    "instead of staged. MEASURED NOT QUOTED: 1051551B, utf-8 bom=False crlf=0 "
    "lone_cr=0 nul=0, 8124 lines, closing line RUNNER PASS (622/622 suites green, "
    "reconcile controls 7/7, 1964.5s), ZERO non-zero-exit suite rows, 622 PASS suite "
    "rows with 622 UNIQUE names, and an INDEPENDENT recount over their own criteria "
    "fields summing to EXACTLY 4708; the target was re-measured by importing "
    "reconcile_all.SUITES BEFORE any follow-up ran and read 622 suites, 4708 criteria, "
    "622 unique names, 622 unique paths, byte for byte the registered number. TMP "
    "RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB. ONE "
    "DIALECT FACT IS NAMED RATHER THAN ASSERTED AWAY: 22 of those rows carry "
    "pass-lines=0 with a non-zero criteria count, i.e. the runner fell back to the "
    "registry criteria number for suites that print no AC- lines, which is the shipped "
    "dialect and not a green claim invented here.",

    "2026-11-09 R2584 FOLLOW-UP in the designed order: the dry run read SECTION matrix "
    "FAIL first BY DESIGN at on-disk 61934B against regenerated 61928B with NO byte "
    "written while fingerprint read PASS CLEAN domains=5, profile read PASS "
    "byte-identical and census read PASS DRIFT-CLEAN, for VERDICT R2584 FAIL "
    "failing=matrix; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned "
    "from THIS round own green evidence through src/sandbox/suite_matrix.py --evidence "
    "qa/reconcile-all-R2584.log --stamp-from the existing document to 61928 bytes at "
    "622 suites / 4708 criteria with its green line honestly reading 622/622 "
    "self-describing, --check read byte-identical at rc=0, and the four sections re-ran "
    "to VERDICT R2584 PASS failing=none (APPENDED 1951B eol_ok=True).",

    "2026-11-09 R2584 DEBT AND BOARD: reconcile-battery-R2583 was closed through the "
    "shipped debtor at its predicted and measured 185898B -> 185901B (line 335, "
    "open 35->34, done 283->284, readback ok), and product-face-R2584 was appended "
    "first=yes through the shipped appender at its predicted 185901B -> 186278B "
    "(readback ok) naming the next window a PRODUCT face on the queue head "
    "state/queue/tech.md:617 prefix AC-PNAA1, whose AC-PNAA1..AC-PNAA6 were pinned in "
    "that row at R2583 BEFORE any code. NO successor battery is owed: this window moved "
    "no product src byte and the registry is unmoved at 622 suites / 4708 criteria, "
    "re-read by import rather than trusted. queue_head re-read line 617 claimable=12 and "
    "queue_floor read FLOOR-MET at 5/5, 12/10, 10/10; no queue row was opened or closed, "
    "because a verification window writes no board row.",

    "2026-11-09 R2584 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - nothing a CEO could open was built this window and none is "
    "claimed; the deliverable is a green 622/4708 battery on disk, a matrix document "
    "whose evidence column names THIS round own green leg, and one closed debt row with "
    "one opened; (b) the window opened on an INTERRUPTED ATTEMPT of the same round whose "
    "battery had already finished green, so that leg is adopted and re-measured instead "
    "of authored here and the launcher was deleted rather than committed; (c) the leg "
    "went green so no red leg exists to keep and no repair was needed, which is a fact "
    "of this run and not a claim that the battery is safe in general; (d) 22 suite rows "
    "carry pass-lines=0 against a non-zero criteria count, named above; (e) state.json "
    "read 77795B against the 78500B waterline at open so state_fold --check read "
    "FOLD-CLEAR and no fold ran, and this append used a PROVED indent=1 "
    "no-trailing-newline round-trip checked byte for byte before mutation; (f) "
    "last_decision_rows stands at 284 while the file now reads 379 rows - that field is "
    "the auxiliary row count and the content-addressed token set is the authority with "
    "new=0, which is why it is not advanced here; (g) Docker is absent on this host so "
    "no containerised sandbox bring-up is claimed; (h) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (i) tasks.md was not touched, it is the P-47 canonical board; (j) "
    "BigDomain-OSLoop still needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile).",

    "R2584 tokens: local=~9k api=0 api_reason=verification window - five-silence scan "
    "with the decisions token scan, the group orders tail and the ledger face actually "
    "read, one debt gate read naming the battery, one queue head and floor read, one "
    "registry target re-measured by import on both axes, one full 622-suite leg adopted "
    "from an interrupted attempt and re-measured on its runner, encoding, uniqueness and "
    "criteria faces with an independent recount to exactly 4708, one designed matrix "
    "FAIL with no byte written, one stamp-aligned regeneration from this round own green "
    "evidence checked byte-identical, one four-section follow-up to a PASS verdict, one "
    "debt row closed and one opened through their shipped writers, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main(argv):
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    for indent in (1, 2):
        for trail in ("", "\n"):
            if json.dumps(state, indent=indent, ensure_ascii=False) + trail == text:
                print("LAYOUT PROVED indent=%d trail=%r bytes=%d" % (indent, trail, len(raw)))
                layout = (indent, trail)
                break
        else:
            continue
        break
    else:
        print("E_R2584_BAD_LAYOUT")
        return 3
    block = state.setdefault("log", [])
    start = len(block)
    block.extend(LINES)
    state["tick"] = int(state.get("tick", 0)) + 1
    new_text = json.dumps(state, indent=layout[0], ensure_ascii=False) + layout[1]
    check = json.loads(new_text)
    if check["log"][start:] != LINES or len(check["log"]) != len(block):
        print("E_R2584_ROUNDTRIP")
        return 4
    execute = "--execute" in argv
    print("APPEND tick=%s log %d -> %d lines, bytes %d -> %d, execute=%s"
          % (state["tick"], start, len(block), len(raw), len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2584_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(new_text.encode("utf-8"))
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = json.load(open(STATE, encoding="utf-8"))
    print("READBACK tick=%s log_lines=%d ok=%s"
          % (back["tick"], len(back["log"]), back["log"][start:] == LINES))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))