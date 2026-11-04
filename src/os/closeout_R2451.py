"""Closeout for the R2451 verification window.

Writes the state log, the board row and the heartbeat row for a window that
discharged the carried battery - and that battery earned its keep by naming
three real birth-site defects.  Every number below was measured this window.

Run with --execute to write; the default is a dry run that prints the payload
and touches nothing.  The export is refreshed by its own shipped writer AFTER
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

TICK = 2451
DEC_ROWS = 186
ORDER_TS = "2026-11-05 00:36"
NEW_DEC_TOKENS = []

LOG = [
    "2026-11-05 R2451 verification window on the debt gate first=yes item "
    "(reconcile-battery-R2451, carried from R2450 at the pre-registered 553 "
    "suites / 4294 criteria): zero product edits until green, the R2168 "
    "mixed-tree rule honoured. The battery ran FIRST on the committed R2450 "
    "tree dc2355c9 with an empty git status and came back RED - RUNNER FAIL "
    "550/553 suites, 4 failed assertions, 1350.5s, kept verbatim as the red "
    "leg qa/reconcile-all-R2451.log (854416B) - and all three reds were real "
    "birth-site defects of the R2450 window rather than stale expectations.",

    "2026-11-05 R2451 defect one, measured: os-status-export-writer-dialect-"
    "wire read exit=1 with 4 of its 6 criteria printed and no FAIL line, and "
    "re-running it by hand from the repository root read SUITE PASS 6/6 - so "
    "the suite was cwd-dependent. src/sandbox/reconcile_all.py:5606 runs each "
    "suite with cwd=os.path.dirname(path), i.e. src/os, while the suite asked "
    "the shipped readers with a cwd-relative root (GWDA.report(\".\") and "
    "SEWD.check(\".\", None)), so inside the battery the audit resolved "
    "src/os/src/os and raised E_GWDA_UNREADABLE: no such directory. Repaired "
    "at the birth site by passing REPO (already defined from __file__) at "
    "three call sites; the suite now reads SUITE PASS 6/6 from BOTH the "
    "repository root and src/os, and no criterion was widened.",

    "2026-11-05 R2451 defect two, measured: reconcile-daily-census read "
    "DRIFT-FLAG and named the row itself - qa/status-export-writer-dialect-"
    "wire-live-R2450.log was class=pwsh-capture, a 414B body carrying five "
    "CRLF lines because the R2450 live capture went through a PowerShell "
    "redirect. Repaired at the birth site by src/os/repair_R2451.py, which "
    "proves the line set identical on both sides of run_identity.normalize "
    "BEFORE writing, lands one atomic replace and reads the bytes back: 414B "
    "-> 409B, crlf 5 -> 0, readback=ok, and the census baseline was NOT "
    "opened, let alone widened. Census then reads DRIFT-CLEAN files=2526 "
    "tee=1997 baselined=529 flags=0.",

    "2026-11-05 R2451 defect three, measured: os-residue-triage read 5/6 with "
    "AC-RTR6 RESIDUE - residue=280 triaged=275 untriaged=5, the five being "
    "R2440, R2442, R2444, R2446 and R2448, all of them rounds this station "
    "delivered. Each round live status was read from ONE call of the shipped "
    "face (all five DELIVERED), then all five were spliced through the shipped "
    "batch channel residue_triage_append_batch: dry run predicted 275 -> 280 "
    "entries and 77117B -> 78117B and --execute measured exactly that, after "
    "which residue_triage --check --round R2451 reads triaged=280 "
    "untriaged=0 verdict=TRIAGED and the suite reads 6/6.",

    "2026-11-05 R2451 the three repairs were committed ALONE before any "
    "further run (0e0d5a9a style: one commit carrying the suite fix, the "
    "repair script, the normalised evidence, the declaration and the red "
    "leg), so the retry battery measured a committed tree. RETRY: RUNNER PASS "
    "553/553 suites green plus reconcile controls 7/7 in 1259.7s with criteria "
    "total 4294 EXACTLY as pre-registered (qa/reconcile-all-R2451-retry.log, "
    "853328B, one utf-8 LF single writer through src/os/battery_stream.py), "
    "TMP RECLAIM 932/932 busy=0 failed=0. Four follow-up sections produced the "
    "designed order: matrix FAILED first on the stale doc (on-disk=53423B "
    "against regenerated=53443B) with no byte written, suite_matrix "
    "regenerated docs/sandbox-suite-matrix.md from THIS round own eligible "
    "green evidence through --stamp-from to 53443B at 553 suites / 4294 "
    "criteria, --check read byte-identical, and the re-run read VERDICT R2451 "
    "PASS failing=none (matrix byte-identical, fingerprint CLEAN domains=5, "
    "profile byte-identical, census DRIFT-CLEAN); both legs stay in the "
    "evidence tail (1889B FAIL then 1950B PASS).",

    "2026-11-05 R2451 debt register closed through its own writers: "
    "reconcile-battery-R2451 closed at 116580B -> 116583B (line=187, open "
    "2->1, done 166->167, readback=ok) and product-face-R2452 opened first=yes "
    "at 116583B -> 116959B naming the tech head state/queue/tech.md:518 prefix "
    "AC-SEWS1, whose AC-SEWS1..AC-SEWS6 were pinned in that row at R2450 "
    "BEFORE any code. NO successor battery was registered because this window "
    "changed no product module and the registry is unmoved at 553 suites and "
    "4294 criteria. The gate now reads CLAIM-FIRST item=product-face-R2452.",

    "2026-11-05 R2451 honest disclosures: (a) this is a zero-product-point "
    "verification window - the battery bought back three real repairs, not a "
    "CEO-visible business surface; (b) the known --help trap bit once more and "
    "is recorded rather than swept: probing reconcile_all.py with --help "
    "started a real battery whose stream was cut by a truncating pipe, leaving "
    "a 13859B file literally named --help in the repo root, deleted before any "
    "commit, and no surviving process; the runner was then driven through "
    "src/os/battery_stream.py as the house law requires; (c) the residue "
    "repair used the BATCH channel rather than five single appends, so the "
    "declaration saw one atomic splice; (d) READ-ONLY observation outside this "
    "repo: the group file FluxGroup/docs/orders.md carries three leftover "
    "empty conflict markers at lines 324-326 (<<<<<<< HEAD, =======, "
    ">>>>>>> origin/main) and reads M in the group worktree, which is a group-"
    "layer condition this station may not write - one line was appended to "
    "HQ-FEEDBACK.md under the P-32 daily-report duty and nothing in that file "
    "was touched; (e) the window ran far past its 25-minute budget on two "
    "batteries (1350.5s then 1259.7s) plus three repairs, named rather than "
    "hidden; (f) tasks.md was not touched, it is the P-47 canonical board.",
]

TOKENS = (
    "R2451 tokens: local=~26k api=0 api_reason=verification window - two full "
    "reconcile batteries (one RED then one GREEN on the committed repair "
    "tree), three birth-site repairs with their own measurement, one "
    "normalised evidence body, one five-round declaration splice through the "
    "shipped batch channel, one stamp-aligned matrix regeneration, one battery "
    "row closed and one product row opened through their shipped CLIs, and "
    "the state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches"
)

BACKLOG_ROW = (
    "- [x] [done 2026-11-05 R2451] R2451 verification window on the debt gate "
    "first=yes item (reconcile-battery-R2451, carried from R2450 at the "
    "pre-registered 553 suites / 4294 criteria): zero product edits until "
    "green, and the first battery came back RED - 550/553 suites, 4 failed "
    "assertions, 1350.5s, red leg kept as qa/reconcile-all-R2451.log - with "
    "all three reds real birth-site defects. (1) The R2450 wire suite asked "
    "the shipped readers with a cwd-relative root while the runner runs suites "
    "at cwd=src/os, so inside the battery the audit resolved src/os/src/os and "
    "raised E_GWDA_UNREADABLE; repaired by passing REPO at three call sites "
    "and proved 6/6 from BOTH cwds. (2) The R2450 live capture was a "
    "PowerShell redirect (414B, five CRLF), normalised by repair_R2451.py "
    "through run_identity.normalize with the line set proved identical before "
    "the write (414B->409B, crlf 5->0, readback ok, baseline untouched). (3) "
    "Five delivered rounds R2440..R2448 sat untriaged in the residue "
    "declaration and were spliced through the shipped batch channel at their "
    "MEASURED DELIVERED status (dry run 275->280 entries, 77117B->78117B, "
    "measured exactly), after which the reading is TRIAGED 280/280. Repairs "
    "committed alone, then RETRY: RUNNER PASS 553/553 suites plus controls 7/7 "
    "in 1259.7s, criteria 4294 exactly as pre-registered; four follow-up "
    "sections PASS after the designed matrix FAIL and its stamp-aligned "
    "regeneration to 53443B (553/4294, --check byte-identical), VERDICT R2451 "
    "PASS failing=none. Debt: battery row closed (open 2->1, done 166->167, "
    "readback ok) and product-face-R2452 opened first=yes on tech head "
    "state/queue/tech.md:518 prefix AC-SEWS1 status_export_writer_transport_"
    "scope (AC-SEWS1..AC-SEWS6 pinned there at R2450 before any code); no "
    "successor battery owed because no product module changed and the registry "
    "is unmoved at 553/4294. Zero product points claimed."
)

HEARTBEAT_ROW = (
    "2026-11-05T06:55:00+08:00 tick=2451 R2451 verification window - the "
    "carried battery went RED first (550/553) and named three real R2450 "
    "defects, all repaired at their birth sites and committed alone: the wire "
    "suite no longer asks a cwd-relative root (6/6 from both cwds), the "
    "pwsh-captured live evidence was normalised with its line set proved "
    "identical (414B->409B, crlf 5->0), and five delivered rounds were spliced "
    "through the shipped batch channel at their measured status so the "
    "declaration reads TRIAGED 280/280; the retry battery then read RUNNER "
    "PASS 553/553 suites plus controls 7/7 at criteria 4294 exactly as "
    "pre-registered, with the matrix regenerated from this round own evidence "
    "[via BigDomain-OSLoop]"
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
        raise SystemExit("E_R2451_BACK read-back does not match the write")
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
        raise SystemExit("E_R2451_TICK state reads %s, expected %d"
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
        raise SystemExit("E_R2451_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2451-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d tokens=%d layout_ok=%s crlf=%d "
          "bare_lf=%d" % (TICK, size, len(payload["log"]), len(tokens),
                          layout["layout_ok"], layout["crlf"],
                          layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2451] R2451 verification window" in backlog:
        raise SystemExit("E_R2451_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2451-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2451 " in beat:
        raise SystemExit("E_R2451_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2451-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))