"""R2703 verification window closeout: measured log lines and one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-13 R2703 VERIFICATION adoption window CLOSING reconcile-battery-R2701 "
    "GREEN at the pre-registered 663 suites / 4954 criteria. Five readings at open: "
    "git status carried exactly ONE untracked entry, qa/reconcile-all-R2702.log, the "
    "evidence of the leg this window was opened to adopt, at HEAD 86aaeb2b equal to "
    "origin/main with no index.lock; ZERO @BigDomain rows in the group ledger "
    "(atbd_lines=0, unreplied_groups=0); the content-addressed decisions face read "
    "rows=120 tokens=64 new=0 against the stored union baseline; the group orders tail "
    "max timestamp is still 2026-11-12 12:45, the bm-a station ONBOARD row already "
    "carried as last_order and judged knowledge-only for this company; "
    "benchmarks_refreshed 2026-11-13 inside the seven-day gate. debt_gate read "
    "CLAIM-FIRST item=reconcile-battery-R2701 opened=R2701 first=1 open=45, queue_head "
    "read tech line=684 prefix=AC-PNAS1 claimable=14, queue_floor --check read "
    "FLOOR-MET 5/5, 14/10, 10/10, state_fold --check read FOLD-CLEAR at 77881B against "
    "the 78500B gate with margin 619 and 66 live log lines, so a fold WAS owed before "
    "any append, and ledger_lines --check read VERDICT CLEAN.",

    "R2703 FOLD 717 RAN BEFORE THE APPEND AND ITS FIRST WINDOW WAS REFUSED FOR A REAL "
    "REASON: the first candidate (items 5..53, the complete R2694 through R2700 blocks "
    "ending on the R2700 push line) measured tokens=16 ok=True but was REFUSED by the "
    "predicate on live-floor, because 66 - 49 + 5 = 18 live lines sits under the "
    "stated 30-line minimum; the window was re-derived rather than the gate forced to "
    "items 5..39 (the complete R2694, R2695, R2696, R2697 and R2698 blocks ending on "
    "the R2698 push line). A DRY RUN CAME FIRST AND WAS PROVED TO WRITE NOTHING (sha256 "
    "of the state file unchanged before and after) and then the execute pass read "
    "verdict=CLEAR 77881B -> 41253B leaving margin 37247 with 13 tokens carried "
    "verbatim, 66 -> 32 live log lines, archive VERIFIED and layout AGREE; state_fold "
    "--check now reads FOLD-CLEAR at 41253B with margin 37247.",

    "R2703 THE LEG WAS ADOPTED BY ITS EVIDENCE PATH AND MEASURED, NEVER RELAUNCHED: no "
    "battery_stream and no reconcile_all process survived by command line before any "
    "byte was read, logs/battery-R2702.stream closed on 'RUNNER PASS (663/663 suites "
    "green, reconcile controls 7/7, 3800.1s)' and 'BATTERY rc=0 3800.8s', and "
    "qa/reconcile-all-R2702.log read 1164504B at adoption - utf-8, bom=False, crlf=0, "
    "lone_cr=0, nul=0, 9315 lines, 663 suite rows carrying 663 UNIQUE names with ZERO "
    "FAIL rows and ZERO non-zero exits, and an INDEPENDENT criteria recount over their "
    "declared criteria fields summing to EXACTLY 4954, byte for byte the number the "
    "debt gate pre-registered; the registry was re-measured through the shipped matrix "
    "face at registry-rows=663 (4954 criteria).",

    "R2703 R2614 DISCIPLINE WAS OWED AND HONOURED: logs/battery-R2702.pid records the "
    "leg window 19:12:22-20:15:42 and TWO commits landed under it - e1462efd at "
    "19:19:47 and 86aaeb2b at 19:21:02 - so the write-sensitive set was re-run on the "
    "FINAL committed tree HEAD 86aaeb2b over fifteen suites and read rc-failures=0 "
    "with every suite printing its own SUITE PASS line (qa/write-sensitive-R2703.log, "
    "utf-8 LF, single writer, with the leg window and both commits named in its own "
    "header). The DESIGNED matrix-FAIL-first step was measured BEFORE that write and "
    "before any other byte: suite_matrix_reconcile --check answered EVIDENCE-FACE "
    "recorded-evidence=qa/reconcile-all-R2699.log named-evidence="
    "qa/reconcile-all-R2702.log at registry-rows=663 (4954 criteria) with NO byte "
    "written, after which the document was regenerated STAMP-ALIGNED from THIS round "
    "own green leg via suite_matrix_reconcile --write --evidence "
    "qa/reconcile-all-R2702.log to 70077 bytes at 663 rows, and --check then read "
    "DOC-CURRENT at rc=0. battery_followup then ran the four pinned sections - matrix "
    "PASS byte-identical 70077B, fingerprint CLEAN domains=5, profile byte-identical, "
    "census DRIFT-CLEAN - for VERDICT R2703 PASS failing=none (APPENDED 1951B "
    "eol_ok=True).",

    "R2703 DEBT THROUGH THE SHIPPED WRITERS: reconcile-battery-R2701 was closed at its "
    "predicted and measured 221021B -> 221024B (line 411, open 45->44, done 348->349, "
    "readback ok) and product-face-R2703 was appended first=yes at 221024B -> 221641B "
    "naming the next window a PRODUCT face on queue head state/queue/tech.md line 684 "
    "prefix AC-PNAS1 with claimable 14 and the criteria AC-PNAS1..AC-PNAS6 pinned in "
    "that row at R2701 BEFORE any code; NO successor battery is owed because this "
    "window moved no product src byte, no registry row and no code, and the registry "
    "is unmoved at 663 suites / 4954 criteria.",

    "R2703 honest disclosures: (a) ZERO product points - a green battery, a restamped "
    "matrix and a write-sensitive pass are evidence, not something a CEO can newly "
    "open, and every P-47 business face still waits on CEO physical pieces (merchant "
    "id, mini-program appid/secret); (b) the fold first window was refused on "
    "live-floor with no byte written and is named above rather than retried silently; "
    "(c) the only tracked changes this window makes are docs/sandbox-suite-matrix.md "
    "(restamped from this round own green leg), the debt register and this file plus "
    "qa evidence, so no product src byte moved; (d) the one-off write-sensitive runner "
    "and this appender in tmp/ are DELETED before the commit rather than staged; (e) "
    "Docker is absent on this host; (f) tasks.md was not touched, it is the P-47 "
    "canonical board; (g) BigDomain-OSLoop still reads InteractiveToken and needs an "
    "ELEVATED shell for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",

    "R2703 tokens: local=~6k api=0 api_reason=verification adoption window - one "
    "five-silence scan with the content-addressed decisions face, the group orders tail "
    "and the ledger face read, one debt gate read, one queue head plus one queue floor "
    "plus one fold gate plus one ledger gate read, one fold refused on a real floor then "
    "re-derived at a true block boundary with a proved no-write dry run, one process-"
    "liveness read and one stream tail before any byte, one evidence measurement on "
    "bytes with an independent criteria recount, one registry read through the shipped "
    "matrix face, one fifteen-suite write-sensitive re-run on the final committed tree, "
    "one designed matrix FAIL-first measurement with no byte written then one "
    "stamp-aligned regeneration checked DOC-CURRENT, one follow-up run in the designed "
    "order landing VERDICT R2703 PASS, one debt close and one debt append with readback, "
    "and the state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES
    expected["tick"] = tick + 1

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    bumped = []
    old_tick = '"tick": %d,' % tick
    new_tick = '"tick": %d,' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip() == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + inserted + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2703_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d" %
          (tick + 1, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
