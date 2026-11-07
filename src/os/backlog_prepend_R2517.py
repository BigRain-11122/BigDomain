"""R2517 backlog prepend: one done row, one carried row, one stale row closed.

Idempotent: refuses to prepend twice. Writes once and keeps the file LF.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

DONE = (
    "- [x] [done 2026-11-07 R2517] R2517 PRODUCT window on the tech head the "
    "register named (product-face-R2516, state/queue/tech.md:553 prefix "
    "AC-PSL1 probe_seam_lazy_scope, criteria AC-PSL1..AC-PSL6 pinned in that "
    "row at R2515 BEFORE any code). Five-silence scan clean at HEAD "
    "3c3a4e5f (git status empty, no index.lock, zero @BigDomain ledger rows, "
    "decisions diff new=0 over the stored 90-token baseline, group orders "
    "tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the "
    "gate); the gate named product-face-R2516 first=yes and no successor "
    "battery was owed because R2516 moved no product src byte. SHIPPED "
    "src/os/probe_seam_lazy_scope.py plus its suite: import resolution is "
    "DERIVED at CALL time from the probe own syntax tree at ANY nesting level "
    "(module body, function body, method body) on the same cycle-guarded "
    "same-root walk the forwarding face runs, so no helper list and no seam "
    "name is spelled in the module; each row names the helpers it was "
    "followed through AND the lazy imports it took. A probe that quiets "
    "nothing itself but lazily imports a helper that does reads COVERED, and "
    "the SAME fixture reads OUT-OF-SCOPE under the module-level forwarding "
    "face, so the closed gap is measured on one fixture in both readers; a "
    "lazy helper that omits a seam makes the probe MISSING-SEAM naming seam "
    "and file with the probe never imported or run; a module whose lazy "
    "imports quiet nothing stays OUT-OF-SCOPE; a lazily chained helper is "
    "followed so a partial middle helper cannot invent a missing seam; a "
    "lazy import cycle terminates; an unparseable source or helper reads "
    "UNREADABLE; a round-token file reads HISTORICAL. PROOF: AC-PSL1..AC-PSL6 "
    "SUITE PASS 6/6 TWICE with an identical digest plus two adjacent probe "
    "faces green (qa/probe-seam-lazy-scope-R2517.log 6504B legs=2 "
    "identical=True fails=0 adjacent=2) captured through the shipped single "
    "evidence writer, and a live leg on the REAL tree reading "
    "SEAMS-LAZY-COVERED over 3 covered probes, 168 out-of-scope modules and "
    "1208 historical one-shot scripts with a lazy fixture COVERED "
    "helpers=quiet_helper quieted=5 beside the same fixture OUT-OF-SCOPE "
    "quieted=0 on the module-level face and a stale lazy fixture "
    "MISSING-SEAM missing=STPT while render and artifact digests were "
    "unchanged (qa/probe-seam-lazy-scope-live-R2517.log 625B class=tee). "
    "REGISTRY 587/4498 -> 588/4504 by exactly one row "
    "os-probe-seam-lazy-scope(6), recounted by importing reconcile_all.SUITES; "
    "matrix regenerated stamp-aligned from qa/reconcile-all-R2516.log to "
    "56544B at 588 suites / 4504 criteria with --check byte-identical and "
    "green honestly 587/588. BOARD: row 553 closed through a per-round writer "
    "(predicted and measured 1679440B, readback ok) and ONE row seeded from "
    "this window own MEASURED limit - a probe that builds its import at RUN "
    "time (importlib.import_module with a literal, or __import__) reads "
    "OUT-OF-SCOPE quieted=0 in both shipped readers - as AC-PDI1..AC-PDI6; "
    "floor FLOOR-MET 5/5 10/10 10/10, head now line 555. DEBT: "
    "product-face-R2516 closed (150420B -> 150423B, readback ok), "
    "reconcile-battery-R2517 appended first=yes at 588/4504 (150423B -> "
    "150786B), product-face-R2517 appended first=no naming tech line 555 "
    "AC-PDI1 (150786B -> 151161B, after ONE refusal E_DEBTA_BAD_FIELD for an "
    "equals sign obeyed and rewritten in words). HONEST: one product point on "
    "a runnable reading, nothing a CEO could open newly built; the run-time "
    "import limit is named and seeded rather than hidden; the decisions file "
    "reads 116 rows against the stored 189 while its token set is unchanged "
    "at 90, so no new decision arrived and the row figure is recorded "
    "honestly; raw queue_row / queue_done_stamp checkers still read "
    "VIOLATION / UNSTAMPED on OLD rows that pre-date this window and were not "
    "touched; Docker absent; tasks.md untouched; the S4U lane reconcile still "
    "needs an ELEVATED shell."
)

CARRIED = (
    "- [ ] [carried 2026-11-07 R2517] R2518 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule), pre-registered at 588 suites / 4504 criteria - exactly what R2517 "
    "registered when it moved the registry by one row "
    "(os-probe-seam-lazy-scope(6), recounted by importing "
    "reconcile_all.SUITES) - and any larger delta must be named rather than "
    "swept. Run the full battery with an empty git status before the run, "
    "launch it detached and unfiltered through src/os/battery_stream.py (the "
    "filtering-pipe trap has cost earlier windows their whole run), keep the "
    "red leg if it goes red, then the four follow-up sections through "
    "src/os/battery_followup.py (its matrix section FAILS first on a stale "
    "doc by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py after, stamp-aligned from this round own "
    "green evidence). On green go back to the product face the register names "
    "next - re-read it with `python src/os/queue_head.py --head tech`, which "
    "R2517 left at state/queue/tech.md:555 prefix AC-PDI1 "
    "probe_seam_dynamic_import_scope (criteria pinned there THIS window before "
    "any code): a probe that builds its import at RUN time reads OUT-OF-SCOPE "
    "quieted=0 because only import statements are read, so a computed-name "
    "forwarding probe is invisible again. NOTE measured many times: a commit "
    "that moves the queue must also re-derive docs/status-export.json and land "
    "its queue block through queue_export_gate_wire --execute, otherwise the "
    "next battery reads the queue face STALE. Also open and needing an "
    "ELEVATED shell: BigDomain-OSLoop exists but its Principal.LogonType still "
    "reads InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task (carried as the stale row loop-s4u-reconcile)."
)

STALE_HEAD = "- [ ] [carried 2026-11-07 R2515] R2516 first item: THE BATTERY"
STALE_DONE = "- [x] [old carried row, discharged 2026-11-07 R2516] R2516 first item: THE BATTERY"


def main():
    raw = open(PATH, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    if "R2517 PRODUCT window" in text:
        print("NOOP already prepended")
        return 0
    if STALE_HEAD not in text:
        print("FAIL stale row not found")
        return 2
    text = text.replace(STALE_HEAD, STALE_DONE, 1)
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
          and back[0].startswith("- [x] [done 2026-11-07 R2517]")
          and back[1].startswith("- [ ] [carried 2026-11-07 R2517] R2518")
          and STALE_DONE in back_raw.decode("utf-8"))
    print("backlog %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())