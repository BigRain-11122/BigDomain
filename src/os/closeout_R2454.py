"""Closeout for the R2454 product window.

Writes the state log, the backlog row and the heartbeat row for the window
that shipped the closeout dialect wire. Every number below was measured this
window.

Run with --execute to write; the default is a dry run that prints the payload
and touches nothing. The export is refreshed by its own shipped writers AFTER
the state append.
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

TICK = 2454
DEC_ROWS = 186
ORDER_TS = "2026-11-05 00:36"
NEW_DEC_TOKENS = []

LOG = [
    "2026-11-05 R2454 product window on the debt gate first=yes item "
    "product-face-R2454 (tech head state/queue/tech.md:520 prefix AC-CEPD1 "
    "closeout_export_parity_dialect_wire, whose AC-CEPD1..AC-CEPD6 were "
    "pinned in that row at R2452 BEFORE any code; five-silence scan at open: "
    "git status empty at HEAD 7d6ee762 with no .git/index.lock, 24 ledger "
    "@BigDomain lines with no new number, the content-addressed decisions "
    "diff new=0 against the stored 123-token baseline, the group orders tail "
    "max_ts 2026-11-05 00:36 equal to the stored last_order, benchmarks "
    "refreshed 2026-11-03 inside the seven-day gate, queue head AC-CEPD1).",

    "2026-11-05 R2454 SHIPPED src/os/closeout_export_parity_dialect_wire.py "
    "plus src/os/test_closeout_export_parity_dialect_wire.py, and the cause "
    "of the R2452 measurement was repaired at its birth site instead of "
    "worked around: export_closeout_gate_parity.closeout_style appended a "
    "hardcoded LF while queue_export_gate_wire kept the target's own "
    "dialect, so the two recipes disagreed on line endings and the closeout "
    "refused every CRLF document at exit 2 with differs=bytes. The "
    "composition now renders through the shipped dialect law "
    "(general_writer_dialect_audit.payload_for) asked at CALL time, and the "
    "reading gains one transport key while every old key keeps its value.",

    "2026-11-05 R2454 evidence: SUITE PASS 20/20 twice with identical "
    "verdict lines (qa/closeout-export-parity-dialect-wire-R2454.log, "
    "legs=2 identical=True, fails=0) plus three adjacent suites green "
    "(export_closeout_gate_parity 6/6, closeout_export_parity_wire 16/16, "
    "status_export_writer_transport_scope 6/6) and the dialect audit still "
    "AUDIT-CLEAN keeps=10 routed=10 unrouted=0. The wire is wired as "
    "os-closeout-export-parity-dialect-wire(6) so the registry reads 555 "
    "suites / 4306 criteria, and docs/sandbox-suite-matrix.md was "
    "regenerated through --stamp-from to 53662B with --check byte-identical "
    "(its green line honestly reads 554/555 because this round produced no "
    "battery).",

    "2026-11-05 R2454 LIVE (qa/closeout-export-parity-dialect-wire-live-"
    "R2454.log): the repository export reads dialect=LF and the parity reads "
    "AGREES gate=WRITTEN differs=(none); a CRLF copy of that same real "
    "document publishes through the new wire with WRITTEN/AGREES, "
    "transport=CRLF, bytes=106468, lone_lf=0 and crlf=413, where at R2452 "
    "the same copy read REFUSED. The copy lived in a temp directory and the "
    "repository export was only read, so no live byte was rewritten by the "
    "proof.",

    "2026-11-05 R2454 debt register through its own writers: "
    "product-face-R2454 closed at 118555B -> 118558B (line=190, open 2->1, "
    "done 169->170, readback ok) and reconcile-battery-R2455 opened first=yes "
    "at 118558B -> 118758B (readback ok) because product src bytes changed "
    "and the registry moved 554->555 suites / 4300->4306 criteria; the gate "
    "now reads CLAIM-FIRST item=reconcile-battery-R2455. Remaining open: "
    "loop-s4u-reconcile and reconcile-battery-R2455.",

    "2026-11-05 R2454 honest disclosures: (a) the transport fix revealed a "
    "SECOND real limit, measured rather than guessed: publishing a "
    "composition made from document A over document B reads WRITTEN/AGREES "
    "and silently writes A's content into B (self_drive.tick 9 became 1), "
    "because the parity recomposes the STAGED bytes and never asks whether "
    "those bytes are what the document it replaces composes to - seeded as "
    "tech row 528 AC-CEPM1 closeout_export_parity_text_binding; (b) an "
    "unsupported --help probe of src/os/refresh_export_R2401.py ran the tool "
    "for real and moved export_ts by a few seconds with zero field change, "
    "which is why the export stamp in this round predates the content "
    "refresh; (c) no P-47 business surface was rebuilt and every P-47 item "
    "remains blocked on CEO physical pieces; (d) READ-ONLY observation "
    "outside this repo: FluxGroup/docs/orders.md still ends with its empty "
    "conflict markers, already reported in HQ-FEEDBACK.md; (e) the window "
    "ran past its 25-minute budget on the birth-site repair, the suite legs "
    "and the matrix regeneration.",

    "2026-11-05 R2454 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType still reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "needs an elevated shell while this session is unelevated, so the "
    "definition was left untouched again (carried as the stale row "
    "loop-s4u-reconcile).",
]

TOKENS = (
    "R2454 tokens: local=~12k api=0 api_reason=product window - one birth-site "
    "repair to the shipped parity, two new files, six criteria proved twice "
    "with identical verdicts plus three adjacent suites, one registry row, "
    "one stamp-aligned matrix regeneration with a byte-identical check, one "
    "live CRLF round trip on a temp copy, one debt row closed and one "
    "battery row opened, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches"
)

BACKLOG_ROW = (
    "- [x] [done 2026-11-05 R2454] R2454 product window on the debt gate "
    "first=yes item (product-face-R2454, tech head state/queue/tech.md:520 "
    "prefix AC-CEPD1, AC-CEPD1..AC-CEPD6 pinned there at R2452 BEFORE any "
    "code): SHIPPED src/os/closeout_export_parity_dialect_wire.py plus its "
    "six-criteria suite, and REPAIRED the cause at its birth site - "
    "export_closeout_gate_parity.closeout_style appended a hardcoded LF while "
    "the gate wire kept the target dialect, so a CRLF export refused at exit "
    "2 with differs=bytes; the composition now asks the shipped dialect law "
    "(general_writer_dialect_audit.payload_for) at CALL time, which the suite "
    "proves by patching that seam and moving the composed text. SUITE PASS "
    "20/20 twice with identical verdict lines plus three adjacent suites "
    "green (qa/closeout-export-parity-dialect-wire-R2454.log, legs=2 "
    "identical=True adjacent=3 fails=0), wired "
    "os-closeout-export-parity-dialect-wire(6) so the registry reads 555 "
    "suites / 4306 criteria, matrix regenerated stamp-aligned to 53662B with "
    "--check byte-identical (green honestly 554/555). LIVE: the repository "
    "export reads dialect=LF with the parity AGREES, and a CRLF copy of that "
    "real document publishes WRITTEN/AGREES transport=CRLF bytes=106468 "
    "lone_lf=0 crlf=413 where R2452 read REFUSED "
    "(qa/closeout-export-parity-dialect-wire-live-R2454.log). ONE real "
    "measured gap seeded as tech row 528 AC-CEPM1 "
    "closeout_export_parity_text_binding: a composition made from document A "
    "published over document B reads WRITTEN/AGREES and writes A's content "
    "into B (tick 9 became 1). Debt: product-face-R2454 closed at 118555B -> "
    "118558B (line=190, open 2->1, done 169->170, readback ok) and "
    "reconcile-battery-R2455 opened first=yes at 118558B -> 118758B because "
    "product src bytes and the registry count moved. Two product points for a "
    "runnable publisher; zero CEO-visible business surface and no P-47 "
    "business item unblocked, they all still wait on CEO physical pieces."
)

HEARTBEAT_ROW = (
    "2026-11-05T05:36:30+08:00 tick=2454 R2454 product window - the closeout "
    "parity now composes in the target's own transport, so a CRLF export "
    "publishes WRITTEN/AGREES with lone_lf=0 where R2452 refused; suite 20/20 "
    "twice plus three adjacent green, registry 555 suites / 4306 criteria, "
    "matrix 53662B --check byte-identical, debt row closed and "
    "reconcile-battery-R2455 opened [via BigDomain-OSLoop]"
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
        raise SystemExit("E_R2454_BACK read-back does not match the write")
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
        raise SystemExit("E_R2454_TICK state reads %s, expected %d"
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
        raise SystemExit("E_R2454_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2454-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d tokens=%d layout_ok=%s crlf=%d "
          "bare_lf=%d" % (TICK, size, len(payload["log"]), len(tokens),
                          layout["layout_ok"], layout["crlf"],
                          layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2454] R2454 product window" in backlog:
        raise SystemExit("E_R2454_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2454-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2454 " in beat:
        raise SystemExit("E_R2454_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2454-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))