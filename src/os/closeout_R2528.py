"""R2528 closeout: state append, backlog row and heartbeat, one write each.

The state file is appended through a PROVED load+dump round-trip (the shipped
state_fold layout reader still does not match this file, disclosed since R2522),
so the only bytes added are this round own rows.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

ROWS = [
    "2026-11-07 R2528 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2527, pre-registered 593 suites / 4534 criteria). "
    "Five-silence state at open: the tree was clean at HEAD beccc381 equal to "
    "origin/main with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read new=0 "
    "over the stored 160-token baseline at a measured 93 tokens, group orders "
    "tail unchanged at 2026-11-07 12:2x, benchmarks 2026-11-03 inside the "
    "seven-day gate. The debt gate read CLAIM-FIRST "
    "item=reconcile-battery-R2527 first=1, and the target was RE-MEASURED "
    "before anything ran by importing reconcile_all.SUITES: 593 suites and "
    "4534 criteria, byte for byte the registered number.",

    "2026-11-07 R2528 GREEN ON THE FIRST LEG, measured not quoted: "
    "qa/reconcile-all-R2528.log is 920698B as delivered (the follow-up block "
    "appended its own 1950B to the 918748B green leg - both numbers are true of "
    "their own moment), utf-8 bom=False crlf=0 lone_cr=0, closing RUNNER PASS "
    "(593/593 suites green, reconcile controls 7/7, 1112.6s), zero FAIL suite "
    "rows, and an independent recount over the 593 PASS rows sums to EXACTLY "
    "4534 criteria - the pre-registered total matched by measurement. Launched "
    "detached and unfiltered through src/os/battery_stream.py (pid in "
    "logs/battery-R2528.pid) so the filtering-pipe trap was not re-paid. FOUR "
    "FOLLOW-UP SECTIONS in the designed order: the dry run read SECTION matrix "
    "FAIL at on-disk 57113B against regenerated 57108B with NO byte written "
    "while fingerprint read CLEAN domains=5, profile byte-identical and census "
    "DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then regenerated "
    "stamp-aligned from THIS round own green evidence through "
    "src/sandbox/suite_matrix.py --stamp-from (57108 bytes, 593 suites / 4534 "
    "criteria, green=593/593 self-describing), --check read byte-identical at "
    "rc=0, and the re-run read all four PASS for VERDICT R2528 PASS "
    "failing=none (APPENDED 1950B, eol crlf=0 bare_cr=0 bom=False).",

    "2026-11-07 R2528 DEBT AND BOARD: reconcile-battery-R2527 was closed "
    "through the shipped debtor at its predicted 159687B -> 159690B (line 255, "
    "open 12->11, done 226->227, readback ok). NO successor battery is owed: "
    "this window moved no product src byte and the registry is unmoved at 593 "
    "suites / 4534 criteria, which is exactly what the green leg measured; the "
    "count was re-read by import rather than trusted. The gate then owed a "
    "leader, so product-face-R2528 was appended first=yes at its predicted "
    "159690B -> 160016B (readback ok) naming the next window a PRODUCT face on "
    "the queue head state/queue/tech.md:565 prefix AC-PCAE1 "
    "probe_seam_alias_expression_scope, whose AC-PCAE1..AC-PCAE6 were pinned in "
    "that row at R2527 BEFORE any code. queue_head read claimable=11 at line "
    "565 with the floor MET; no queue row was opened or closed this window, "
    "because a verification window writes no board row.",

    "2026-11-07 R2528 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 593/4534 battery and a "
    "matrix document whose evidence column names THIS round own green leg "
    "rather than a borrowed older one. (b) The window ran one full 1112.6s "
    "battery plus the follow-up pass and overshot its 25-minute budget, and it "
    "says so rather than hiding it. (c) My first follow-up invocation passed "
    "--round R2528 and was refused E_BFU_BAD_ARGS because that flag takes an "
    "INTEGER, reported rather than silently retried; the re-run used 2528. (d) "
    "The open rows product-face-R2511, product-face-R2513, product-face-R2515, "
    "product-face-R2517 and product-face-R2522 still name product windows whose "
    "suites demonstrably shipped, and the shipped readers still do not age "
    "them; this window declined to mass-close them by hand and did not invent a "
    "reading to hide them, so the register overstates outstanding work and says "
    "so here. (e) Docker is absent on this host so no containerised bring-up of "
    "the sandbox faces is claimed. (f) The real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret). (g) tasks.md was not touched, it is the P-47 canonical "
    "board. (h) MEASURED DEFECT STILL OPEN from R2522: the shipped state_fold "
    "layout reader no longer matches the state file written with json.dump, so "
    "this window appended through a proved load+dump round-trip instead of "
    "reformatting the file. (i) Both legs stay in the evidence file and the red "
    "leg does not exist for this window because none was produced, stated "
    "rather than implied.",

    "R2528 tokens: local=~9k api=0 api_reason=verification window - five-"
    "silence scan at the committed closeout tree, one content-addressed "
    "decisions scan reading new=0, one debt gate read naming the owed battery, "
    "one registry target re-measured by import, one full 593-suite battery "
    "green on the first leg at the pre-registered 4534 criteria, four follow-up "
    "sections plus one stamp-aligned matrix regeneration from this round own "
    "green evidence checked byte-identical, one debt row closed and one opened "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-07 R2528] R2528 VERIFICATION window on the battery the "
    "register owed (reconcile-battery-R2527, pre-registered 593 suites / 4534 "
    "criteria, and the target was re-measured by importing reconcile_all.SUITES "
    "before anything ran - byte for byte the registered number). Five-silence "
    "state at open: clean tree at HEAD beccc381 equal to origin/main, no "
    "index.lock, zero @BigDomain ledger rows, decisions diff new=0 over the "
    "stored baseline at a measured 93 tokens, group orders tail unchanged, "
    "benchmarks inside the seven-day gate; the debt gate read CLAIM-FIRST "
    "reconcile-battery-R2527 first=1. RESULT GREEN ON THE FIRST LEG, measured "
    "not quoted: qa/reconcile-all-R2528.log is 920698B as delivered (1950B "
    "follow-up block appended to a 918748B green leg), utf-8 bom=False crlf=0 "
    "lone_cr=0, closing RUNNER PASS (593/593 suites green, reconcile controls "
    "7/7, 1112.6s), zero FAIL suite rows, and an independent recount over the "
    "593 PASS rows summing to EXACTLY 4534 criteria; launched detached and "
    "unfiltered through battery_stream.py (pid in logs/battery-R2528.pid). FOUR "
    "FOLLOW-UP SECTIONS in the designed order: dry run read matrix FAIL at "
    "on-disk 57113B against regenerated 57108B with no byte written while "
    "fingerprint read CLEAN domains=5, profile byte-identical and census "
    "DRIFT-CLEAN; docs/sandbox-suite-matrix.md regenerated stamp-aligned from "
    "this round own green evidence through suite_matrix.py --stamp-from to "
    "57108B at 593 suites / 4534 criteria with green=593/593 self-describing, "
    "--check byte-identical, then all four PASS for VERDICT R2528 PASS "
    "failing=none (APPENDED 1950B). DEBT: reconcile-battery-R2527 closed through "
    "the shipped debtor at its predicted 159687B -> 159690B (line 255, open "
    "12->11, done 226->227, readback ok); NO successor battery owed because no "
    "product src byte moved and the registry is unmoved at 593/4534; "
    "product-face-R2528 appended first=yes at 159690B -> 160016B naming the next "
    "window a PRODUCT face on queue head state/queue/tech.md:565 prefix AC-PCAE1 "
    "probe_seam_alias_expression_scope (criteria pinned at R2527 BEFORE any "
    "code), queue_head claimable=11 with the floor MET. HONEST: zero product "
    "points, nothing a CEO could open was built, the window overshot its budget "
    "on a 1112.6s battery, my first follow-up call passed --round R2528 and was "
    "refused because that flag takes an integer, five stale product-face rows "
    "are disclosed rather than hand-closed, the state_fold layout defect from "
    "R2522 is still open, Docker absent, the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items, tasks.md untouched."
)


def main():
    raw = io.open(STATE, encoding="utf-8").read()
    obj = json.loads(raw)
    round_trip = json.dumps(obj, indent=4, ensure_ascii=False) + "\n"
    if round_trip != raw:
        print("FAIL round-trip: %d vs %d" % (len(round_trip), len(raw)))
        return 3
    before = len(raw.encode("utf-8"))
    obj["tick"] = 2528
    obj["log"].extend(ROWS)
    payload = json.dumps(obj, indent=4, ensure_ascii=False) + "\n"
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    ok = back["tick"] == 2528 and back["log"][-len(ROWS):] == ROWS
    print("state %s tick=%s rows=%d before=%d after=%d"
          % ("OK" if ok else "FAIL", back["tick"], len(ROWS), before,
             len(payload.encode("utf-8"))))

    text = io.open(BACKLOG, encoding="utf-8").read()
    rows = text.split("\n")
    if BACKLOG_ROW in text:
        print("backlog SKIP already present")
    else:
        rows.insert(0, BACKLOG_ROW)
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(rows))
        print("backlog OK prepended %d bytes"
              % (len(BACKLOG_ROW.encode("utf-8")),))

    hb = io.open(HEARTBEAT, encoding="utf-8").read()
    line = ("tick=2528 2026-11-07 R2528 verification window: reconcile battery "
            "green on the first leg 593/593 suites at exactly 4534 criteria, "
            "matrix regenerated self-describing, battery row closed and the "
            "next product face registered\n")
    if "tick=2528" in hb:
        print("heartbeat SKIP already present")
    else:
        with io.open(HEARTBEAT, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
        print("heartbeat OK %d bytes" % (len(line.encode("utf-8")),))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())