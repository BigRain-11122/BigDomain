"""Closeout for the R2453 verification window.

Writes the state log, the backlog row and the heartbeat row for the window
that discharged the battery the R2452 product edit owed. Every number below
was measured this window.

Run with --execute to write; the default is a dry run that prints the payload
and touches nothing. The export is refreshed by its own shipped writer AFTER
every state append (the R2449 ordering law), never from inside this script.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                         "heartbeat.txt")

TICK = 2453
DEC_ROWS = 186
ORDER_TS = "2026-11-05 00:36"
NEW_DEC_TOKENS = []

LOG = [
    "2026-11-05 R2453 verification window (five-silence scan at open: git "
    "status empty at HEAD 4e2d8535 with no .git/index.lock; the evolution "
    "ledger carries zero @BigDomain rows; the content-addressed decisions "
    "diff read 186 rows with new=0 and gone=0 against the stored 123-token "
    "baseline; the group orders tail max_ts is 2026-11-05 00:36 equal to the "
    "stored last_order; benchmarks were refreshed 2026-11-03 inside the "
    "seven-day gate; the queue head read state/queue/tech.md:520 prefix "
    "AC-CEPD1). The debt gate named CLAIM-FIRST item=reconcile-battery-R2453 "
    "carried from R2452, so this window is a VERIFICATION window: zero "
    "product edits until green, the R2168 mixed-tree rule.",

    "2026-11-05 R2453 the first launch never reached the battery and the "
    "cause is named rather than swept: the command was piped through a "
    "filtering selector, the pipe buffered every line, the shell cancelled it "
    "at the five-minute no-output gate, and src/os/battery_stream.py writes "
    "evidence only at close - so the process died with NO evidence file and "
    "the tree stayed clean (zero survivors checked by command line, no "
    "qa/reconcile-all-R2453.log on disk). The battery was then launched "
    "UNFILTERED so every line streams, which is the same trap R2211, R2268, "
    "R2289 and R2348 paid for and is restated here as a habit rather than as "
    "new law.",

    "2026-11-05 R2453 BATTERY GREEN on the committed tree 4e2d8535 with an "
    "empty git status: RUNNER PASS 554/554 suites green, reconcile controls "
    "7/7, 1255.0s, criteria total 4300 EXACTLY as pre-registered at R2452, "
    "birth-site TMP RECLAIM 932/932 removed=932 busy=0 failed=0 reclaimed "
    "326.59 MiB. Evidence qa/reconcile-all-R2453.log written by ONE utf-8 LF "
    "single writer through src/os/battery_stream.py, never a shell "
    "redirection: crlf=0 bare_cr=0 bom=False. No red leg exists for this "
    "round because none was produced, stated rather than implied.",

    "2026-11-05 R2453 the four follow-up sections produced the designed "
    "order: SECTION matrix FAIL at on-disk=53568B against regenerated=53539B "
    "with no byte written, then src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md from THIS round own eligible green evidence "
    "through --stamp-from to 53539B at 554 suites / 4300 criteria, --check "
    "read byte-identical, and the re-run read matrix byte-identical 53539B, "
    "fingerprint CLEAN domains=5, profile byte-identical PASS, census "
    "DRIFT-CLEAN - VERDICT R2453 PASS failing=none. Both legs stay in the "
    "evidence tail (1889B FAIL then 1950B PASS) and the whole file measures "
    "858125B. The matrix is self-describing this round: its own green line "
    "reads 554/554 because it names this round own battery rather than a "
    "borrowed older leg.",

    "2026-11-05 R2453 debt register closed through its own writers: "
    "reconcile-battery-R2453 closed at 117670B -> 117673B (line=189, open "
    "2->1, done 168->169, readback=ok). NO successor battery was registered "
    "because this window changed no product src byte and the registry is "
    "unmoved at 554 suites and 4300 criteria, so the gate owed a leader: "
    "product-face-R2454 was appended first=yes at 117673B -> 118555B "
    "(readback=ok) naming the tech head state/queue/tech.md:520 prefix "
    "AC-CEPD1 closeout_export_parity_dialect_wire, whose AC-CEPD1..AC-CEPD6 "
    "were pinned in that row at R2452 BEFORE any code. The gate now reads "
    "CLAIM-FIRST item=product-face-R2454. Remaining open: loop-s4u-reconcile "
    "and product-face-R2454.",

    "2026-11-05 R2453 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt, no P-47 "
    "business surface was touched, and every P-47 item remains blocked on CEO "
    "physical pieces; what the window bought is a proven registry (554 "
    "suites, 4300 criteria) rather than a smaller story about it; (b) the "
    "first launch was killed by the filtering-pipe trap and left no evidence, "
    "disclosed above rather than counted as a leg; (c) the window ran well "
    "past its 25-minute budget on a 1255.0s battery plus the follow-up legs, "
    "named rather than hidden; (d) READ-ONLY observation outside this repo: "
    "the group file FluxGroup/docs/orders.md still carries its leftover empty "
    "conflict markers (the tail reads '>>>>>>> origin/main') in the group "
    "worktree, which this station may not write; it is already reported in "
    "HQ-FEEDBACK.md; (e) tasks.md was not touched, it is the P-47 canonical "
    "board; (f) no fold was due: state.json measured 30353B before the "
    "closeout against the 78500B waterline.",

    "2026-11-05 R2453 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 needs an "
    "elevated shell while this session is unelevated, so the definition was "
    "left untouched again (two-hundred-and-eighteenth consecutive disclosure, "
    "carried as the stale row loop-s4u-reconcile).",
]

TOKENS = (
    "R2453 tokens: local=~9k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (554/554 suites, controls 7/7, "
    "4300 criteria exactly as pre-registered, 1255.0s), one designed matrix "
    "FAIL followed by a stamp-aligned regeneration from this round own green "
    "evidence and a byte-identical --check, four follow-up sections PASS for "
    "VERDICT R2453 PASS, one battery row closed and one product row opened "
    "through their shipped CLIs, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches"
)

BACKLOG_ROW = (
    "- [x] [done 2026-11-05 R2453] R2453 verification window on the debt gate "
    "first=yes item (reconcile-battery-R2453, carried from R2452 at the "
    "pre-registered 554 suites / 4300 criteria): zero product code changed, "
    "the R2168 mixed-tree rule honoured. The first launch was killed by the "
    "filtering-pipe trap before the battery started (no evidence file, zero "
    "survivors, disclosed), so it was relaunched unfiltered and the battery "
    "ran on the committed 4e2d8535 tree with an empty git status: RUNNER PASS "
    "554/554 suites green plus reconcile controls 7/7 in 1255.0s at criteria "
    "total 4300 EXACTLY as pre-registered, TMP RECLAIM 932/932 busy=0 "
    "failed=0 reclaimed 326.59 MiB (qa/reconcile-all-R2453.log, 858125B with "
    "both legs, one utf-8 LF single writer through src/os/battery_stream.py, "
    "crlf=0 bare_cr=0 bom=False). Four follow-up sections produced the "
    "designed order: matrix FAILED first on the stale doc (on-disk=53568B "
    "against regenerated=53539B) with no byte written, "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md "
    "from THIS round own eligible green evidence through --stamp-from to "
    "53539B at 554 suites / 4300 criteria, --check read byte-identical, and "
    "the re-run read matrix byte-identical, fingerprint CLEAN domains=5, "
    "profile byte-identical, census DRIFT-CLEAN for VERDICT R2453 PASS "
    "failing=none; the matrix is self-describing this round at green=554/554. "
    "Debt: reconcile-battery-R2453 closed at 117670B -> 117673B (line=189, "
    "open 2->1, done 168->169, readback ok); NO successor battery owed "
    "because no product src byte changed and the registry is unmoved at "
    "554/4300, so product-face-R2454 was opened first=yes at 117673B -> "
    "118555B naming the tech head state/queue/tech.md:520 prefix AC-CEPD1 "
    "(closeout_export_parity_dialect_wire, criteria pinned at R2452 before any "
    "code). Zero product points claimed; no P-47 business surface was rebuilt "
    "and every P-47 item remains blocked on CEO physical pieces."
)

HEARTBEAT_ROW = (
    "2026-11-05T05:16:01+08:00 tick=2453 R2453 verification window - the "
    "battery the R2452 product edit owed read RUNNER PASS 554/554 suites plus "
    "controls 7/7 in 1255.0s at criteria 4300 exactly as pre-registered, the "
    "matrix was regenerated from THIS round own green evidence to 53539B with "
    "--check byte-identical, and all four follow-up sections PASS for VERDICT "
    "R2453 PASS; debt row closed and product-face-R2454 opened on the tech "
    "head AC-CEPD1 [via BigDomain-OSLoop]"
)


def write_bytes_atomic(path, data, prefix):
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2453_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d new_dec=%d"
              % (TICK, len(LOG) + 1, len(NEW_DEC_TOKENS)))
        for line in LOG:
            print("  LOG %s" % line[:110])
        print("  TOKENS %s" % TOKENS[:110])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2453_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["last_order"] = ORDER_TS
    tokens = sorted(set(list(payload["last_dec_tokens"]) + NEW_DEC_TOKENS))
    payload["last_dec_tokens"] = tokens
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2453_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2453-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d tokens=%d layout_ok=%s crlf=%d "
          "bare_lf=%d" % (TICK, size, len(payload["log"]), len(tokens),
                          layout["layout_ok"], layout["crlf"],
                          layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2453] R2453 verification window" in backlog:
        raise SystemExit("E_R2453_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2453-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2453 " in beat:
        raise SystemExit("E_R2453_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2453-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))