"""Closeout for the R2452 product window.

Writes the state log, the backlog row and the heartbeat row for the window
that shipped the export writer transport scope - and that scope named the one
writer which cannot keep the target dialect at all. Every number below was
measured this window.

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

TICK = 2452
DEC_ROWS = 186
ORDER_TS = "2026-11-05 00:36"
NEW_DEC_TOKENS = []

LOG = [
    "2026-11-05 R2452 product window (five-silence scan at open: git status "
    "empty at HEAD 05e6a47e with no .git/index.lock; the evolution ledger "
    "carries zero @BigDomain rows; the content-addressed decisions diff read "
    "123 tokens with new=0 and gone=0 against the stored baseline at 186 rows; "
    "the group orders tail max_ts is 2026-11-05 00:36 equal to the stored "
    "last_order; benchmarks were refreshed 2026-11-03 inside the seven-day "
    "gate; the queue head read state/queue/tech.md:518 prefix AC-SEWS1). The "
    "debt gate named CLAIM-FIRST item=product-face-R2452 carried from R2451, "
    "so this window is a PRODUCT window on that row.",

    "2026-11-05 R2452 board first, before any code: AC-SEWS1..AC-SEWS6 were "
    "re-read from the R2450 seed row at state/queue/tech.md:518 and used as "
    "written, and the five anchors were re-checked at HEAD with git grep -l: "
    "status_export_writer_transport_scope hit docs/status-export.json, "
    "src/os/backlog.md, src/os/closeout_R2450.py, src/os/export_R2450.py, "
    "src/os/export_R2451.py, src/os/stamp_queue_R2450.py, src/os/state.json "
    "and state/queue/tech.md; AC-SEWS hit those plus src/os/closeout_R2451.py "
    "and state/debt.md; and E_SEWS, "
    "os-status-export-writer-transport-scope and "
    "test_status_export_writer_transport_scope hit only "
    "src/os/stamp_queue_R2450.py and state/queue/tech.md - prose, state and "
    "prior closeouts only, i.e. zero executable occupancy on all five, and no "
    "file by either name existed.",

    "2026-11-05 R2452 SHIPPED src/os/status_export_writer_transport_scope.py "
    "plus src/os/test_status_export_writer_transport_scope.py. The proved set "
    "is the dialect wire own derived set read off the shipped audit at CALL "
    "time, so no writer name is written down in the module; each writer is "
    "asked through its OWN entry point discovered by surface (write, else "
    "publish) over an LF copy and a CRLF copy of the real document inside a "
    "private fixture world, and the two legs must agree on the same document. "
    "The base reading of the dialect wire is carried through with every key "
    "keeping its value, and the scope adds scope_verdict / scope / "
    "scope_proved / scope_unprovable / scope_target.",

    "2026-11-05 R2452 MEASURED on the real tree, not asserted: "
    "STATUS EXPORT WRITERS derived=3 routed=3 unrouted=0 audit=AUDIT-CLEAN "
    "verdict=WIRED scope=SCOPE-PARTIAL proved=2 "
    "unprovable=closeout_export_parity_wire.py, with "
    "queue_export_gate_wire PROVED (lf=102887B crlf=103292B lone-lf=0 "
    "agree=yes) and queue_floor_export_face PROVED (same bytes, same "
    "agreement) - the two writers the R2450 wire never proved - while the "
    "third writer is published as UNPROVABLE refusal=2/DISAGREES with its "
    "document left byte-identical. The refusal is transport-only: its LF leg "
    "writes normally (WRITTEN, agree=yes), so the row is a named reading "
    "about the CRLF dialect rather than a dropped writer.",

    "2026-11-05 R2452 a REAL birth-site defect was found by RUNNING, not by "
    "reading: the new suite read FAIL 5/6 the moment it was run from src/os "
    "(AC-SEWS3 proved=2 broken=[] today=102854 same=[]), because "
    "status_export_writer_dialect_wire.transport called QFE.compose(\".\") and "
    "QFE.write(\".\") with the queues root hardcoded to the process cwd - the "
    "R2451 repair had fixed the suite call sites only, so the shipped wire own "
    "transport proof had been reading the wrong queues for any caller outside "
    "the repository root. Repaired at the birth site: transport takes the root "
    "and check passes its own root through, after which both suites read SUITE "
    "PASS 6/6 from BOTH the repository root and src/os, and no criterion was "
    "widened.",

    "2026-11-05 R2452 evidence, measured rather than asserted: SUITE PASS 6/6 "
    "twice with an identical digest plus three adjacent suites green "
    "(EVIDENCE CAPTURE round=R2452 legs=2 identical=True adjacent=3 fails=0 "
    "offending=None, qa/status-export-writer-transport-scope-R2452.log, "
    "2076B, one utf-8 LF single writer through the shipped capture callable); "
    "the three adjacent suites were test_status_export_writer_dialect_wire, "
    "test_queue_floor_export_face and test_queue_export_gate_wire, and the "
    "three writer suites the scope asks by subprocess still read 6/6, 6/6 and "
    "16/16. Wired os-status-export-writer-transport-scope(6) so the registry "
    "reads 554 suites / 4300 criteria, exactly the +1 suite / +6 criteria this "
    "window owes; docs/sandbox-suite-matrix.md was regenerated from the newest "
    "eligible battery face (qa/reconcile-all-R2451-retry.log) through "
    "--stamp-from to 53568B at 554 suites / 4300 criteria with --check "
    "byte-identical, and its own green line honestly reads 553/554 because "
    "this window suite has no line in that battery log.",

    "2026-11-05 R2452 LIVE, not a plan: "
    "qa/status-export-writer-transport-scope-live-R2452.log (559B, one utf-8 "
    "LF body, zero CRLF, readback ok) is the shipped CLI read over the real "
    "document, exit 2 with scope=SCOPE-PARTIAL - exit 2 is the honest code for "
    "a partial scope, so the CLI cannot be mistaken for a clean bill.",

    "2026-11-05 R2452 board and register: row 518 was stamped through the "
    "shipped pattern with a DISCHARGED block and one REAL measured gap row "
    "seeded at line 520 (closeout_export_parity_dialect_wire, AC-CEPD1..AC-CEPD6 "
    "pre-registered BEFORE any code) because the closeout wire cannot publish "
    "a CRLF-dialect export at all - the exact dialect the R2450 wire exists to "
    "preserve. Board bytes 1615074B -> 1618464B, readback ok; the head "
    "advanced to state/queue/tech.md:520 prefix AC-CEPD1. Debt: "
    "product-face-R2452 closed at 116959B -> 116962B (line=188, open 2->1, "
    "done 167->168, readback=ok) and reconcile-battery-R2453 opened first=yes "
    "at 116962B -> 117670B through debt_append, because this window changed "
    "product src bytes AND moved the registry, so the R2168 mixed-tree rule "
    "owes the battery next at the pre-registered 554 suites / 4300 criteria. "
    "The gate now reads CLAIM-FIRST item=reconcile-battery-R2453. Remaining "
    "open: loop-s4u-reconcile and reconcile-battery-R2453.",

    "2026-11-05 R2452 honest disclosures: (a) this window claims two product "
    "points for a runnable reading that turned an untested writer into a named "
    "UNPROVABLE one and proved the other two in both transports, but it is "
    "still export-chain plumbing, not a P-47 business surface - no business "
    "surface was rebuilt and no P-47 item was touched, and that gap is stated "
    "rather than dressed up as progress on the product line; (b) repairing a "
    "shipped "
    "module inside another round product (the transport root) was necessary "
    "and is named here rather than folded into the new file; (c) the AC-SEWS3 "
    "criterion caught my own predecessor defect only because the suite was run "
    "from a second cwd - the same lesson R2451 paid for, restated as a habit "
    "rather than as new law; (d) READ-ONLY observation outside this repo: the "
    "group file FluxGroup/docs/orders.md still carries its leftover empty "
    "conflict markers (the tail reads '>>>>>>> origin/main') in the group "
    "worktree, which this station may not write; it is already reported in "
    "HQ-FEEDBACK.md; (e) heartbeat.txt last row is stamped "
    "2026-11-05T06:55:00+08:00 while this window measured 04:23 local, so the "
    "heartbeat stamps are not monotonic - it is appended, not rewritten, and "
    "named here so the next reader does not read it as a slow lane; (f) the "
    "window ran past its 25-minute budget on the dual-cwd suite runs and the "
    "evidence legs, named rather than hidden; (g) tasks.md was not touched, it "
    "is the P-47 canonical board.",

    "2026-11-05 R2452 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 needs an "
    "elevated shell while this session is unelevated, so the definition was "
    "left untouched again (two-hundred-and-seventeenth consecutive disclosure, "
    "carried as the stale row loop-s4u-reconcile).",
]

TOKENS = (
    "R2452 tokens: local=~21k api=0 api_reason=product window - one src/os "
    "scope whose proved set is derived from the shipped audit at CALL time, "
    "each writer asked through its own discovered entry point over an LF and a "
    "CRLF copy, with an UNPROVABLE writer published with its own refusal code; "
    "one six-criteria suite against criteria pinned at R2450 plus forty-two "
    "suite runs across the dual-cwd legs, the capture ritual and the CLI self "
    "check; one birth-site repair of the shipped dialect wire transport root; "
    "one dual-face evidence capture; one stamp-aligned matrix regeneration; "
    "one board row stamped and one real gap seeded, one debt row closed and "
    "one battery row opened through their shipped CLIs; and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches"
)

BACKLOG_ROW = (
    "- [x] [done 2026-11-05 R2452] R2452 product window on the debt gate "
    "first=yes item product-face-R2452 (tech head state/queue/tech.md:518 "
    "prefix AC-SEWS1, criteria pinned at R2450): shipped "
    "src/os/status_export_writer_transport_scope.py plus its six-criteria "
    "suite. The proved set is the dialect wire own derived set read off the "
    "shipped audit at CALL time (no writer name in the module), each writer is "
    "asked through its own entry point discovered by surface (write, else "
    "publish) over an LF copy and a CRLF copy in a private fixture world, and "
    "the two legs must carry the same document. MEASURED live: "
    "scope=SCOPE-PARTIAL proved=2 unprovable=closeout_export_parity_wire.py "
    "with queue_export_gate_wire and queue_floor_export_face PROVED "
    "(lf=102887B, crlf=103292B, lone-lf=0, agree=yes - the two writers the "
    "R2450 wire never proved) and the third published as UNPROVABLE "
    "refusal=2/DISAGREES with its document byte-identical, which is a named "
    "reading instead of a dropped writer. The base reading keeps every key it "
    "published before, and the scope keys are additional. A REAL birth-site "
    "defect surfaced by running the suite from src/os (FAIL 5/6, today=102854 "
    "against rows 102887): status_export_writer_dialect_wire.transport had the "
    "queues root hardcoded to '.' - the R2451 repair fixed the suite call "
    "sites only - now the root is passed through and both suites read 6/6 from "
    "BOTH cwds. Evidence: capture 2 legs identical + 3 adjacent suites green "
    "(qa/status-export-writer-transport-scope-R2452.log, 2076B) and a 559B "
    "single-writer LF live log (exit 2, SCOPE-PARTIAL, zero CRLF); registry "
    "554 suites / 4300 criteria with the matrix regenerated to 53568B and "
    "--check byte-identical (its green line honestly 553/554). Debt: "
    "product-face-R2452 closed (line=188, open 2->1, done 167->168, readback "
    "ok) and reconcile-battery-R2453 opened first=yes at the pre-registered "
    "554/4300; board row 518 stamped (1615074B->1618464B) with one real gap "
    "seeded at line 520 - closeout_export_parity_dialect_wire, AC-CEPD1.."
    "AC-CEPD6 pinned before any code - because the closeout wire cannot "
    "publish a CRLF export at all. Two product points claimed for the "
    "reading; no P-47 business surface was rebuilt, every P-47 item remains "
    "blocked on CEO physical pieces."
)

HEARTBEAT_ROW = (
    "2026-11-05T04:23:14+08:00 tick=2452 R2452 product window - the export "
    "writer transport scope landed and MEASURED the real tree: proved=2 "
    "(queue_export_gate_wire and queue_floor_export_face, both transports, "
    "lone-lf=0, agree=yes) with the third writer published as UNPROVABLE "
    "refusal=2/DISAGREES rather than dropped, and a real birth-site defect "
    "found by running the suite from src/os - the dialect wire transport had "
    "the queues root hardcoded to the cwd, now passed through, 6/6 from both "
    "cwds [via BigDomain-OSLoop]"
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
        raise SystemExit("E_R2452_BACK read-back does not match the write")
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
        raise SystemExit("E_R2452_TICK state reads %s, expected %d"
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
        raise SystemExit("E_R2452_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2452-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d tokens=%d layout_ok=%s crlf=%d "
          "bare_lf=%d" % (TICK, size, len(payload["log"]), len(tokens),
                          layout["layout_ok"], layout["crlf"],
                          layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2452] R2452 product window" in backlog:
        raise SystemExit("E_R2452_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2452-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2452 " in beat:
        raise SystemExit("E_R2452_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2452-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))