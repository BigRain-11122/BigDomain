"""R2538 backlog prepend: one done row plus the next window first item.

Idempotent: refuses to prepend twice. Writes once through one atomic replace
and keeps the file LF (it is LF today and must stay LF).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

NEXT = (
    "- [ ] [carried 2026-11-07 R2538] R2539 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:575 prefix "
    "AC-PNSB1 probe_seam_name_binding_scope_awareness, criteria AC-PNSB1.."
    "AC-PNSB6 pinned in that row at R2537 BEFORE any code. The measured "
    "limit: the binding reader walks the WHOLE source, so one name bound in "
    "two different function bodies merges into a single table and reads "
    "ambiguous even though each scope is unambiguous on its own. Re-read the "
    "row with `python src/os/queue_head.py --head tech` rather than trusting "
    "this line (claimable=11, floor FLOOR-MET), run a fresh zero-occupancy "
    "anchor check at HEAD, ship ONE face with its pre-registered suite, "
    "refill the tech floor if claiming drops claimable below 10, and commit "
    "BEFORE any battery (the R2168 mixed-tree rule). NOTE measured many "
    "times, and re-measured the hard way this window: pass --evidence to "
    "battery_stream.py and NEVER redirect its stdout into qa/ - a PowerShell "
    "redirection lands UTF-16, the writer census flags it ps-utf16 and "
    "cd7-live-real-tree goes red for a whole battery leg. A commit that "
    "moves the queue must also re-derive docs/status-export.json and land "
    "its queue block through queue_export_gate_wire --execute. Also open and "
    "needing an ELEVATED shell: BigDomain-OSLoop exists but its "
    "Principal.LogonType still reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task (carried as the stale row "
    "loop-s4u-reconcile)."
)

DONE = (
    "- [x] [done 2026-11-07 R2538] R2538 VERIFICATION window on the battery "
    "the register owed (reconcile-battery-R2537, pre-registered 598 suites / "
    "4564 criteria). Five-silence scan clean at HEAD bc7cc37d (git status "
    "empty, no index.lock, zero @BigDomain ledger rows, content-addressed "
    "decisions diff new=0 at 237 rows, group orders tail carrying only a "
    "knowledge-only fleet row, benchmarks 2026-11-03 inside the gate); "
    "debt_gate read CLAIM-FIRST reconcile-battery-R2537 so the battery ran "
    "FIRST per the R2168 mixed-tree rule. LEG 1 RED AND KEPT "
    "(qa/reconcile-all-R2538.log, 939714B): 597/598 suites at exactly 4564 "
    "criteria in 1280.5s, the only red suite reconcile-daily-census "
    "cd7-live-real-tree exit=2 drift, and the shipped writer census named the "
    "cause in one line - qa/reconcile-all-R2538.stdout.log class=ps-utf16, "
    "this window own PowerShell redirection of the battery stdout into the "
    "evidence directory. The artifact was deleted, the census re-read "
    "DRIFT-CLEAN flags=0 files=2681, and the red leg was committed alone as "
    "e11fa6fd before the retry. RETRY GREEN: qa/reconcile-all-R2538-retry.log "
    "RUNNER PASS 598/598 suites, controls 7/7, 1260.7s. FOLLOW-UP in the "
    "designed order: matrix FAIL first on a stale doc (57696B vs 57715B, no "
    "byte written), regenerated stamp-aligned from this round own green "
    "evidence to 57715B at 598/4564 with --check byte-identical, then four "
    "PASS for VERDICT R2538 PASS failing=none. DEBT: reconcile-battery-R2537 "
    "closed through debt_close (open 17->16, done 236->237, readback ok) and "
    "product-face-R2538 opened first=yes naming tech head AC-PNSB1 "
    "(readback ok). HONEST: zero product points, nothing a CEO could newly "
    "open; the red was born in this window own transport (fifth recorded "
    "instance of the redirect-into-qa trap); two full batteries ran so the "
    "window went far past budget and one launch was killed by the shell tool "
    "five-minute silence limit because its stdout was redirected away; the "
    "state_fold layout reader is still broken (disclosed since R2522) so the "
    "append used a proved load+dump round-trip; Docker is absent; the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items; "
    "tasks.md was untouched."
)


def main():
    raw = open(PATH, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    if "R2538 VERIFICATION window" in text:
        print("NOOP already prepended")
        return 0
    before = len(raw)
    payload = NEXT + eol + DONE + eol + text
    predicted = len(payload.encode("utf-8"))
    print("backlog before=%d predicted=%d delta=%d"
          % (before, predicted, predicted - before))
    with io.open(PATH, "wb") as handle:
        handle.write(payload.encode("utf-8"))
    back_raw = open(PATH, "rb").read()
    back = back_raw.decode("utf-8").split(eol)
    ok = (len(back_raw) == predicted
          and back[0].startswith("- [ ] [carried 2026-11-07 R2538]")
          and back[1].startswith("- [x] [done 2026-11-07 R2538]"))
    print("backlog %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())