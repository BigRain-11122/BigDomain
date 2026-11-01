"""state_close_R2324.py - append the R2324 window items through state_io.

Fold 619 already ran BEFORE the append (78481B -> 71311B, margin 7189B), so
these four items are written to fit under the 78500B gate and the script
refuses to write over it. Dry run by default; --execute writes.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_io  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
GATE = 78500

NARRATIVE = (
    "2026-11-01 R2324 verification window (five-silence scan clean at open: "
    "empty git status --short and no index.lock; decisions.md carried 84 "
    "non-empty rows EQUAL to the stored baseline with the token diff reading "
    "ZERO new, so no decision row is owed; the group ledger carried the same "
    "three @BigDomain patrol rows already paid off, the last one "
    "P-20261026-0930 acked at R2311, with zero unreplied numbered handoffs; "
    "the group orders tail was unchanged at the 2026-11-01 10:4x baseline "
    "R2321 already acked by number as non-execution; benchmarks refreshed "
    "2026-11-01 inside the seven-day gate). The debt gate named "
    "product-face-R2323 and the board top named the battery the R2168 "
    "mixed-tree rule defers, so this window ran the VERIFICATION with ZERO "
    "product edits. FOLD FIRST because state.json stood at 78481B against the "
    "78500B gate (19B margin): fold 619 moved log lines 4..10 - the whole "
    "R2309 and R2310 round blocks - verbatim into logs/state-log-archive-"
    "2026-11.md (162788B -> 170132B, prefix intact, 7 window tokens covered, "
    "no token missing), predicted 71311B equal to measured 71311B, margin "
    "7189B, committed alone as 65862198. The fold created NO live residue "
    "(state/residue_triage.json still reads residue=192 triaged=192 "
    "untriaged=0 unmatched=0 verdict=TRIAGED), so the two speculative "
    "declaration entries this window had prepared were reverted rather than "
    "left as inert rows. BATTERY on the committed fold tree 65862198 with an "
    "empty git status before the run: RUNNER PASS 469/469 suites green plus "
    "controls 7/7 in 791.9s with birth-site TMP RECLAIM 932/932 worlds "
    "326.59 MiB busy zero failed zero (qa/reconcile-all-R2324.log, 786983B, "
    "single writer utf-8 LF through src/os/battery_stream.py, never a shell "
    "redirection), criteria total 3790 - EXACTLY the pre-registered target "
    "of +1 suite / +6 criteria against R2322 (468/3784) from the R2323 "
    "os-orphan-trace suite, so the prediction matched the measurement with no "
    "correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=44931B regenerated=45005B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 469 suites / 3790 criteria (45005B) and "
    "the re-run read all four sections PASS (matrix byte-identical 45005B, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing VERDICT R2324 PASS. The product face the "
    "row demanded was then read live: orphan_trace --trace reads rounds=1 "
    "legs=2 trace_exists=1 no_trace=0 verdict=TRACE-FOUND with R2136 standing "
    "in through reconcile-all-R2136c.log (RUNNER PASS) while the -b leg reads "
    "RUNNER FAIL, and queue_head --head tech reads line 380 prefix AC-FRH1 "
    "claimable=10 (followup_retry_history), so the product face carries to "
    "R2325. Battery evidence committed as 4909350f."
)

LEDGER = (
    "R2324 tokens: local=~11k api=0 api_reason=verification-only window - one "
    "waterline fold with its archive append and read-back proof, one full "
    "reconcile battery on the committed tree with its streamed evidence file, "
    "one four-section follow-up (the designed matrix FAIL) plus one matrix "
    "regeneration and a re-run that read all four PASS, one live product "
    "reading and one queue_head re-read, one debt close and one debt append, "
    "and the state/export/heartbeat/board closeout; zero cloud calls and zero "
    "external API touches; the product face resumes at R2325"
)

SELF_HEAL = (
    "R2324 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(eighty-sixth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2324 honest disclosures: (a) this window shipped NO product code and "
    "scores 0 product points; the work it did was the battery the register "
    "named plus the fold the waterline demanded. (b) The fold PREDICTION of "
    "new residue was WRONG and is disclosed as such: I expected R2309 and "
    "R2310 to become live residue once their blocks moved, wrote two "
    "declaration entries, and the measurement then read unmatched=2 because "
    "the residue law counts rounds stamped only on OPEN rows and neither round "
    "is one - the splice was reverted with git checkout and the declaration "
    "reads unmatched=0 again, so no inert row was left behind. (c) The matrix "
    "section failed first by design - it refuses to rewrite a stale doc - and "
    "both legs stay in the evidence file (1889B FAIL then 1950B PASS), so the "
    "round reads as one designed FAIL followed by one PASS rather than two "
    "rounds. (d) The battery measured the committed fold tree 65862198; this "
    "window's own closeout changes are bookkeeping only and are not battery "
    "subjects. (e) The export consistency checker read FAIL on "
    "self_drive.log_lines_in_window (stored 11, recomputed 10) BEFORE this "
    "closeout, which is the stale derived field the refresh fixes, not a "
    "defect this window introduced. (f) tasks.md was left untouched: it is "
    "the P-47 canonical board and carries no row for this tech slice, "
    "disclosed rather than silently skipped."
)


def build(raw):
    state = json.loads(raw.decode("utf-8"))
    before = len(state["log"])
    state["tick"] = 2324
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES])
    ascii_only = all(byte < 0x80 for byte in raw)
    body = json.dumps(state, ensure_ascii=ascii_only, indent=2)
    return before, state_io.canon(body).encode("utf-8")


def write(path, data, label):
    temp = os.path.join(os.path.dirname(path), ".%s.tmp" % label)
    with open(temp, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    if open(path, "rb").read() != data:
        raise SystemExit("E_READBACK %s" % label)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % label)


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    before_items, new = build(raw)
    print("LOG_ITEMS %d -> %d TICK 2324 BEFORE %dB AFTER %dB DELTA %+d "
          "GATE %d MARGIN %d"
          % (before_items, before_items + 4, len(raw), len(new),
             len(new) - len(raw), GATE, GATE - len(new)))
    if len(new) > GATE:
        raise SystemExit("E_C2324_OVER_GATE %d" % len(new))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    write(STATE, new, "state_close_R2324")
    parsed = json.loads(open(STATE, "rb").read().decode("utf-8"))
    if parsed["tick"] != 2324 or len(parsed["log"]) != before_items + 4:
        raise SystemExit("E_C2324_PARSE")
    print("WROTE %dB readback ok temp clean tick=%d log=%d"
          % (len(new), parsed["tick"], len(parsed["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))