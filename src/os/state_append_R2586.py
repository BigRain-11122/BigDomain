"""R2586 state append: tick + the round log block, layout proved before mutation.

This round ADOPTS the earlier attempt of the same round (the red leg, the
birth-site repair and the export refresh were already committed) and lands the
verification closeout on the tree those commits produced.
"""

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(ROOT)
STATE = os.path.join(ROOT, "src", "os", "state.json")

NEW_DEC = ["D-20261109-01", "D-20261109-02", "D-20261109-03"]

LINES = [
    "2026-11-09 R2586 VERIFICATION window on the battery the register named first "
    "(reconcile-battery-R2585, pre-registered 623 suites / 4714 criteria at R2585). "
    "Five-silence at open: git status carried exactly TWO untracked files from an "
    "INTERRUPTED ATTEMPT of this same round (qa/reconcile-all-R2586-retry.log and "
    "-retry2.log) with no battery process live, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed D-/C- decisions scan read 167 "
    "tokens over 392 rows against the stored 197-token baseline with new=3 "
    "(D-20261109-01, -02, -03), the group orders tail holding its newest real row at "
    "2026-11-09 00:59 (a BigStream TTS QC dispatch, knowledge-only here; the scanner "
    "max_ts 2026-11-09 12:00 is a DUE DATE inside the 2026-11-08 06:0x committee row "
    "and is named rather than smoothed), benchmarks 2026-11-03 inside the seven-day "
    "gate. The debt gate read CLAIM-FIRST item=reconcile-battery-R2585 first=1 "
    "open=36 with its own note naming the pre-registered target, so the battery ran "
    "BEFORE any product byte (the R2168 mixed-tree rule); queue_head named tech line "
    "619 prefix AC-PNAB1 claimable=13 and queue_floor read FLOOR-MET at 5/5, 13/10, "
    "10/10.",

    "2026-11-09 R2586 THE THREE NEW DECISIONS WERE JUDGED AND ACKNOWLEDGED WITHOUT "
    "EXECUTION: D-20261109-01 (the 52nd batch collection-face audit - seven faces, "
    "only BigCompute carrying same-day rows), D-20261109-02 (the BigCompute M176 "
    "'21 permanently lost group ledger rows' claim FALSIFIED with a REAL 47-row "
    "table drift handed to a mechanical escape repair) and D-20261109-03 (decision-"
    "round gap evidence for 11-07 and the 11-09 00:00 class). All three are group "
    "audit or BigCompute repair faces with no BigDomain execution surface, so each is "
    "recorded as knowledge and the baseline advances by exactly those three tokens; "
    "no BigDomain task is dispatched from them.",

    "2026-11-09 R2586 A PRIOR ATTEMPT OF THIS ROUND HAD ALREADY RUN THREE LEGS AND "
    "IS ADOPTED, NOT RESTARTED: qa/reconcile-all-R2586.log (the red leg) and the "
    "birth-site repair commit c98b67a9 came first - its ONE failing suite was "
    "os-seq-stamped-never-logged, reading a stamped-but-never-logged round against "
    "the LIVE log only, so the repair taught the guard to count a folded round's "
    "block in logs/state-log-archive-*.md through the same owning-label law; six "
    "criteria were pinned on the board BEFORE that code and its own suite read green "
    "6/6 twice plus four adjacent suites, and the registry moved 623/4714 -> "
    "624/4720 by exactly that one row. A SECOND red was then disclosed rather than "
    "hidden (qa/reconcile-all-R2586-retry.log: three export/queue faces reading stale "
    "documents at 621/624) and healed in the designed order by refreshing the export "
    "through src/os/export_R2586.py, committed as 98f62c19. Neither commit was "
    "authored in this window and neither is claimed as new work here; what this "
    "window adds is the measurement, the follow-up, the debt and the closeout.",

    "2026-11-09 R2586 GREEN LEG MEASURED NOT QUOTED: qa/reconcile-all-R2586-retry2.log "
    "1054406B, utf-8 bom=False crlf=0 lone_cr=0 nul=0, 8161 lines, closing line "
    "RUNNER PASS (624/624 suites green, reconcile controls 7/7, 2267.5s), ZERO "
    "non-zero-exit suite rows, 624 PASS suite rows with 624 UNIQUE names, and an "
    "INDEPENDENT recount over their own criteria fields summing to EXACTLY 4720. The "
    "registered target was 623/4714 and the delta is NAMED rather than swept: +1 "
    "suite and +6 criteria because the birth-site repair shipped its own six-criteria "
    "suite, with no unrelated row moving. The registry was re-measured by importing "
    "reconcile_all.SUITES after the leg and read 624 suites / 4720 criteria / 624 "
    "unique names / 624 unique paths - byte for byte the leg's own recount. TMP "
    "RECLAIM was not re-run in this window and is not claimed.",

    "2026-11-09 R2586 FOLLOW-UP in the designed order: the dry run read SECTION matrix "
    "FAIL first BY DESIGN at on-disk 62324B against regenerated 62352B with NO byte "
    "written while fingerprint read PASS verdict CLEAN domains=5, profile read PASS "
    "byte-identical and census read PASS DRIFT-CLEAN, for VERDICT R2586 FAIL "
    "failing=matrix; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned "
    "from THIS round own green evidence through src/sandbox/suite_matrix.py --evidence "
    "qa/reconcile-all-R2586-retry2.log --stamp-from the existing document to 62352 "
    "bytes at 624 suites / 4720 criteria with its green line honestly reading 624/624 "
    "self-describing, --check read byte-identical at rc=0, and the four sections "
    "re-ran to VERDICT R2586 PASS failing=none (APPENDED 1951B eol_ok=True).",

    "2026-11-09 R2586 DEBT AND BOARD: reconcile-battery-R2585 was closed through the "
    "shipped debtor at its predicted and measured 186734B -> 186737B (line 338, open "
    "36->35, done 285->286, readback ok). The gate then read verdict=OPEN-NONE with "
    "first_count=0, so product-face-R2586 was appended first=yes at its predicted and "
    "measured 186737B -> 187181B (readback ok) naming the next window a PRODUCT face "
    "on the queue head state/queue/tech.md:619 prefix AC-PNAB1, whose "
    "AC-PNAB1..AC-PNAB6 were pinned in that row at R2585 BEFORE any code. NO "
    "successor battery is owed: this window moved no product src byte and the "
    "registry is unmoved at 624 suites / 4720 criteria, which is exactly what the "
    "green leg measured. No queue row was opened or closed in this window, because a "
    "verification window writes no board row; the repair's P2 seed from the red it "
    "found is already on the board as its own open row.",

    "2026-11-09 R2586 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - nothing a CEO could open was built this window and none is "
    "claimed; the deliverable is a green 624/4720 battery on disk, a matrix document "
    "whose evidence column names THIS round own green leg, and one closed debt row "
    "with one opened; (b) THREE legs were already spent by an earlier attempt of this "
    "same round before this window opened, so the window is an adoption and a "
    "closeout rather than a fresh run, and the round as a whole ran far past its "
    "25-minute budget - stated plainly rather than dressed as progress; (c) the "
    "registry delta against the pre-registered number (+1 suite / +6 criteria) is "
    "named above with its cause; (d) TMP RECLAIM was not re-run this window and is "
    "not claimed; (e) last_decision_rows stays at its auxiliary value while the "
    "content-addressed token baseline is the authority and advanced by the three "
    "judged tokens; (f) Docker is absent on this host so no containerised bring-up of "
    "the sandbox faces is claimed; (g) the real 19.9 debit and the real msgSecCheck "
    "still wait on CEO physical items (merchant id, mini-program appid/secret); (h) "
    "tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop "
    "still reads InteractiveToken and needs an ELEVATED shell (carried ceo-pending "
    "physical item loop-s4u-reconcile).",

    "R2586 tokens: local=~11k api=0 api_reason=verification window - one five-silence "
    "scan with the decisions content-addressed scan, the three new tokens read and "
    "judged, the group orders tail and the ledger face actually read, one debt gate "
    "read naming the battery, one queue head and floor read, one registry target "
    "re-measured by import on both axes, one full 624-suite leg adopted from an "
    "interrupted attempt and measured on its runner, encoding, uniqueness and "
    "criteria faces with an independent recount to exactly 4720, one designed matrix "
    "FAIL with no byte written, one stamp-aligned regeneration from this round own "
    "green evidence checked byte-identical, one four-section follow-up to a PASS "
    "verdict, one debt row closed and one opened through their shipped writers, and "
    "the state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def main(argv):
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    layout = None
    for indent in (1, 2):
        for trail in ("", "\n"):
            if json.dumps(state, indent=indent, ensure_ascii=False) + trail == text:
                print("LAYOUT PROVED indent=%d trail=%r bytes=%d" % (indent, trail, len(raw)))
                layout = (indent, trail)
                break
        if layout:
            break
    if not layout:
        print("E_R2586_BAD_LAYOUT")
        return 3
    block = state.setdefault("log", [])
    start = len(block)
    block.extend(LINES)
    state["tick"] = int(state.get("tick", 0)) + 1
    tokens = list(state.get("last_dec_tokens", []))
    for tok in NEW_DEC:
        if tok not in tokens:
            tokens.append(tok)
    state["last_dec_tokens"] = tokens
    new_text = json.dumps(state, indent=layout[0], ensure_ascii=False) + layout[1]
    check = json.loads(new_text)
    if check["log"][start:] != LINES or len(check["log"]) != len(block):
        print("E_R2586_ROUNDTRIP")
        return 4
    if check.tick if False else check["tick"] != state["tick"]:
        print("E_R2586_TICK")
        return 5
    execute = "--execute" in argv
    print("APPEND tick=%s log %d -> %d lines, tokens %d -> %d, bytes %d -> %d, execute=%s"
          % (state["tick"], start, len(block), len(state["last_dec_tokens"]) - len(NEW_DEC),
             len(state["last_dec_tokens"]), len(raw), len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2586_")
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