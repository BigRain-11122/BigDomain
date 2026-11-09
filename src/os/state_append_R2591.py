"""state_append_R2591 - append this round log lines and advance the tick.

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
    "2026-11-09 R2591 VERIFICATION window on the battery the register named first "
    "(reconcile-battery-R2590, pre-registered 627 suites / 4738 criteria at R2590). "
    "Five-silence at open: git status carried exactly ONE untracked file from the "
    "INTERRUPTED ATTEMPT of the previous round (src/os/launch_battery_R2590.py) and a "
    "LIVE BATTERY was already running on the committed tree f41231c2 (pids 49316 "
    "battery_stream + 50340 reconcile_all, started 15:32:20, twenty-one seconds after "
    "the R2590 commit at 15:31:40), zero @BigDomain rows in cph4/evolution-ledger.md, "
    "the content-addressed decisions scan read 61 tokens against the stored 205-token "
    "baseline with new=0 over 162 rows, the group orders tail had moved to 2026-11-09 "
    "15:2x with TWO fleet rows (the CEO self-drive saturation law and the order-to-"
    "whole-fleet law, both registered by bm-a for the machine lanes) which were read "
    "and judged KNOWLEDGE-ONLY for this company with no BigDomain execution face, "
    "benchmarks 2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST "
    "item=reconcile-battery-R2590 first=1 open=37 with the pre-registered 627 suites / "
    "4738 criteria, so the battery was owed on this committed tree BEFORE any product "
    "byte (the R2168 mixed-tree rule); queue_head named tech line 625 prefix AC-PNAE1 "
    "claimable=13 and queue_floor read FLOOR-MET at 5/5, 13/10, 10/10.",

    "2026-11-09 R2591 THE BATTERY WAS ALREADY RUNNING AND IS ADOPTED RATHER THAN "
    "RESTARTED: the R2590 window launched it on the committed tree and did not live to "
    "record the result, so this window waited it out instead of starting a second "
    "writer on the same evidence path. IT FINISHED GREEN, measured not quoted: "
    "logs/battery-R2590.stream.log closed on `RUNNER PASS (627/627 suites green, "
    "reconcile controls 7/7, 3526.5s)` and `BATTERY rc=0 3526.9s`, and the delivered "
    "evidence qa/reconcile-all-R2590.log was then measured byte for byte - 1062246B, "
    "utf-8 with bom=False, crlf=0, lone_cr=0, nul=0, 8248 lines, 627 `PASS suite` rows "
    "carrying 627 UNIQUE suite names, ZERO non-zero-exit suite rows, and an INDEPENDENT "
    "recount over those rows own criteria fields summing to EXACTLY 4738, byte for byte "
    "the pre-registered number. TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 "
    "reclaimed 326.59 MiB. The target was re-measured by importing reconcile_all.SUITES "
    "BEFORE the follow-up ran and read 627 suites / 627 unique names / 627 unique paths "
    "on both axes.",

    "2026-11-09 R2591 FOLLOW-UP IN THE DESIGNED ORDER: the dry run read SECTION matrix "
    "FAIL first BY DESIGN at on-disk 63365B against regenerated 63354B with NO byte "
    "written while fingerprint read PASS CLEAN domains=5, profile read PASS "
    "byte-identical and census read PASS DRIFT-CLEAN, for VERDICT R2590 FAIL "
    "failing=matrix; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned "
    "from THIS round own green evidence through src/sandbox/suite_matrix.py --evidence "
    "qa/reconcile-all-R2590.log --stamp-from the existing document to 63354 bytes at "
    "627 suites / 4738 criteria with its green line now reading 627/627 self-describing "
    "instead of the previous window honest 626/627, --check read byte-identical at rc=0, "
    "and the four sections re-ran to VERDICT R2590 PASS failing=none (APPENDED 1951B "
    "eol_ok=True).",

    "2026-11-09 R2591 DEBT AND BOARD: reconcile-battery-R2590 was closed through the "
    "shipped debtor at its predicted and measured 188702B -> 188705B (line 343, open "
    "37->36, done 289->290, readback ok). The gate then read verdict=OPEN-NONE with "
    "first_count=0, so product-face-R2591 was appended first=yes at its predicted and "
    "measured 188705B -> 189099B (readback ok) naming the next window a PRODUCT face on "
    "the queue head state/queue/tech.md:625 prefix AC-PNAE1, whose AC-PNAE1..AC-PNAE6 "
    "were pinned in that row at R2590 BEFORE any code. NO successor battery is owed: "
    "this window moved no product src byte and the registry is unmoved at 627 suites / "
    "4738 criteria, which is exactly what the green leg measured. No queue row was "
    "opened or closed, because a verification window writes no board row; queue_head "
    "still reads line 625 claimable=13 and queue_floor FLOOR-MET at 5/5, 13/10, 10/10.",

    "R2591 honest disclosures: (a) ZERO product points on the Executive Protocol scale - "
    "nothing a CEO could newly open was built this window and none is claimed; the "
    "deliverable is a green 627/4738 battery on disk, a matrix document whose evidence "
    "column names THIS round own green leg and whose green line is now honestly "
    "627/627, and one closed debt row with one opened; (b) the battery was STARTED BY "
    "THE PREVIOUS ROUND and this window only waited it out and measured it - that is "
    "disclosed rather than presented as work authored here; (c) the leg went green so no "
    "red leg exists to keep and no repair was needed, which is a fact of this run and "
    "not a claim that the battery is safe in general; (d) this window ran far past its "
    "budget because the awaited battery alone took 3526.5s, stated plainly rather than "
    "dressed as progress; (e) the group orders tail rows at 15:1x and 15:2x are fleet "
    "self-drive and order-broadcast laws for the machine lanes with no BigDomain "
    "execution face, recorded as knowledge and last_order advanced to 2026-11-09 15:2x; "
    "(f) the leftover one-off launcher src/os/launch_battery_R2590.py was DELETED rather "
    "than committed, since it is a single-use file; (g) Docker is absent on this host so "
    "no containerised bring-up of the sandbox faces is claimed; (h) the real 19.9 debit "
    "and the real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret); (i) tasks.md was not touched, it is the P-47 canonical "
    "board; (j) BigDomain-OSLoop still needs an ELEVATED shell for its S4U "
    "re-registration (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2591 tokens: local=~7k api=0 api_reason=verification window - one five-silence "
    "scan with the content-addressed decisions scan, the group orders tail and the "
    "ledger face actually read, two fleet-only order rows judged knowledge-only, one "
    "debt gate read naming the battery, one queue head and floor read, one live battery "
    "detected by command line and WAITED rather than duplicated, one delivered evidence "
    "file measured on size, encoding, line count, suite uniqueness and an independent "
    "criteria recount to exactly 4738, one registry target re-measured by import on both "
    "axes, one designed matrix FAIL with no byte written, one stamp-aligned regeneration "
    "from this round own green evidence checked byte-identical, one four-section "
    "follow-up to a PASS verdict, one debt row closed and one opened through their "
    "shipped writers, one leftover launcher deleted, and the state/export/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
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
    doc["last_order"] = "2026-11-09 15:2x"
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = back["tick"] == doc["tick"] and back["log"][-1] == LINES[-1]
    print("APPEND tick=%d log_rows=%d before=%dB after=%dB ok=%s"
          % (back["tick"], len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())