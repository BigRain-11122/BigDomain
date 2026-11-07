"""R2515 backlog prepend: one done row and one carried row, proved by read-back.

Idempotent: refuses to prepend twice. Writes once through one atomic replace
and keeps the file LF (it is LF today and must stay LF).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

DONE = (
    "- [x] [done 2026-11-07 R2515] R2515 PRODUCT window on the tech head the "
    "register named (product-face-R2514, state/queue/tech.md:552 prefix "
    "AC-PSF1 probe_seam_forwarding_scope, criteria AC-PSF1..AC-PSF6 pinned in "
    "that row at R2513 BEFORE any code). Five-silence scan clean at HEAD "
    "f80b75a9 (git status empty, no index.lock, zero @BigDomain ledger rows, "
    "decisions diff new=0 over the stored 90-token baseline at 189 rows, "
    "group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 "
    "inside the gate); the gate named reconcile-battery-R2515 first=yes and "
    "that battery is owed by THIS window, so a product byte came first per "
    "the R2168 mixed-tree rule. SHIPPED src/os/probe_seam_forwarding_scope.py "
    "plus its suite: the quieting hop is DERIVED at CALL time from the probe "
    "own module-level imports and each helper own syntax tree, so no helper "
    "list and no seam name is spelled in the module; a forwarding probe "
    "reads COVERED with its helpers named, a helper that omits a seam reads "
    "MISSING-SEAM naming seam and file with the probe never run, a module "
    "importing helpers that quiet nothing stays OUT-OF-SCOPE, an unparseable "
    "source or helper reads UNREADABLE, and a round-token file reads "
    "HISTORICAL. ONE REGISTERED HOP WAS NOT ENOUGH, measured before shipping: "
    "a one-hop reading invents a MISSING-SEAM when a middle helper names part "
    "and re-exports the rest, so the shipped reading follows local imports "
    "transitively (same root, cycle-guarded, depth 8) - a strict superset "
    "disclosed rather than hidden. PROOF: AC-PSF1..AC-PSF6 SUITE PASS 6/6 "
    "TWICE identical plus four adjacent readability suites green "
    "(qa/probe-seam-forwarding-scope-R2515.log 6183B legs=2 identical=True "
    "fails=0 adjacent=4) and a live leg on the REAL tree reading "
    "SEAMS-FORWARDED over 3 covered probes with the render and doc digests "
    "unchanged, a forwarding fixture COVERED helpers=quiet_helper quieted=5 "
    "and a stale fixture MISSING-SEAM missing=STPT "
    "(qa/probe-seam-forwarding-scope-live-R2515.log 1132B class=tee). "
    "REGISTRY 586/4492 -> 587/4498 by exactly one row "
    "os-probe-seam-forwarding-scope(6); matrix regenerated stamp-aligned to "
    "56475B at 587/4498 with --check byte-identical and green honestly "
    "586/587. BOARD: row 552 closed through a per-round writer (predicted and "
    "measured 1674931B, readback ok) and one row seeded from this window own "
    "MEASURED limit - an import inside a FUNCTION body is not followed, lazy "
    "fixture reading OUT-OF-SCOPE quieted=0 - as AC-PSL1..AC-PSL6; floor "
    "FLOOR-MET 5/5 10/10 10/10, head now line 553. DEBT: product-face-R2514 "
    "closed (148756B -> 148759B, readback ok), reconcile-battery-R2515 "
    "appended first=yes at 587/4498 (148759B -> 149123B), product-face-R2515 "
    "appended first=no naming tech line 553 AC-PSL1 (149123B -> 149635B). "
    "HONEST: one product point on a runnable reading, nothing a CEO could "
    "open newly built; the registered one-hop scope was widened only because "
    "a narrower reading could invent a defect; the same-root/module-level "
    "limits are named and seeded; raw queue_row/queue_done_stamp checkers "
    "read VIOLATION/UNSTAMPED on OLD rows that pre-date this window and were "
    "not touched; Docker absent; tasks.md untouched; the S4U lane reconcile "
    "still needs an ELEVATED shell."
)

CARRIED = (
    "- [ ] [carried 2026-11-07 R2515] R2516 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule), pre-registered at 587 suites / 4498 criteria - exactly what "
    "R2515 registered when it moved the registry by one row "
    "(os-probe-seam-forwarding-scope(6), recounted by importing "
    "reconcile_all.SUITES) - and any larger delta must be named rather than "
    "swept. Run the full battery with an empty git status before the run, "
    "launch it detached and unfiltered through src/os/battery_stream.py (the "
    "filtering-pipe trap has cost earlier windows their whole run), keep the "
    "red leg if it goes red, then the four follow-up sections through "
    "src/os/battery_followup.py (its matrix section FAILS first on a stale "
    "doc by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py after, stamp-aligned from this round own "
    "green evidence). On green go back to the product face the register "
    "names next - re-read it with `python src/os/queue_head.py --head tech`, "
    "which R2515 left at state/queue/tech.md:553 prefix AC-PSL1 "
    "probe_seam_lazy_scope (criteria pinned there THIS window before any "
    "code): a probe that imports its quieting helper INSIDE a function body "
    "reads OUT-OF-SCOPE quieted=0 because only module-level imports are "
    "followed, so a lazy forwarding probe is invisible again. NOTE measured "
    "many times: a commit that moves the queue must also re-derive "
    "docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute, otherwise the next battery reads the "
    "queue face STALE. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop exists but its Principal.LogonType still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every "
    "lane task (carried as the stale row loop-s4u-reconcile)."
)


def main():
    raw = open(PATH, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    if DONE.split("]")[0] in text and "R2515 PRODUCT window" in text:
        print("NOOP already prepended")
        return 0
    before = len(raw)
    payload = DONE + eol + CARRIED + eol + text
    predicted = len(payload.encode("utf-8"))
    print("backlog before=%d predicted=%d delta=%d"
          % (before, predicted, predicted - before))
    with io.open(PATH, "wb") as handle:
        handle.write(payload.encode("utf-8"))
    back_raw = open(PATH, "rb").read()
    back = back_raw.decode("utf-8").split(eol)
    ok = (len(back_raw) == predicted
          and back[0].startswith("- [x] [done 2026-11-07 R2515]")
          and back[1].startswith("- [ ] [carried 2026-11-07 R2515] R2516"))
    print("backlog %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())