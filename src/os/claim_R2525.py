"""Prepend the R2525 claim row to src/os/backlog.md and stamp heartbeat.txt."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROW = (
    "- [x] [done 2026-11-07 R2525] R2525 PRODUCT window on the tech head the "
    "queue named (state/queue/tech.md:561 prefix AC-PLAC1, criteria "
    "AC-PLAC1..AC-PLAC6 pinned at R2523 BEFORE any code). Five-silence scan "
    "clean (git status empty, no index.lock, decisions diff new=0 over the "
    "160-token baseline, orders tail unchanged, benchmarks inside the gate); "
    "debt gate OPEN-NONE so no battery was owed; queue_head named line 561 "
    "claimable=11; all five pinned anchors re-checked at zero occupancy. "
    "SHIPPED src/os/probe_seam_annotated_constant_scope.py plus its suite: the "
    "SHIPPED constant tables are EXTENDED, not replaced - an annotated "
    "assignment whose annotation is a plain name, a walrus binding and a "
    "for-loop target of one str literal are read in the module body and in "
    "function bodies with the same ambiguity rule, the shipped resolution law "
    "is asked FIRST with the extended tables so every earlier answer stands, "
    "and only when it answers None is ONE more attribute hop taken on a "
    "module-level constant tree with the binding label carried on the row. An "
    "annotation that is not a plain name is refused rather than guessed; a "
    "call, a concatenation, a comprehension and an arithmetic expression are "
    "never evaluated and are named as unresolved. PROOF: AC-PLAC1..AC-PLAC6 "
    "SUITE PASS 6/6 TWICE with an identical digest plus three adjacent probe "
    "faces green (qa/probe-seam-annotated-constant-scope-R2525.log, 8335B, "
    "legs=2 identical=True fails=0 adjacent=3), landed with LF only and a byte "
    "read-back; a live leg on the REAL tree reads SEAMS-ANNOTATED-COVERED over "
    "1410 probes (3 covered, 172 out-of-scope, 1235 historical, missing=0) "
    "with the real probes showing their annotated local bindings, one annotated "
    "fixture reads MISSING-SEAM missing=PLRC dynamic=importlib.import_module:"
    "plac_live_helper@NAME, a missing root is refused E_PLAC_NO_ROOT, and the "
    "module and render digests are unchanged (qa/probe-seam-annotated-"
    "constant-scope-live-R2525.log, 1267B). REGISTRY 591/4522 -> 592/4528 by "
    "one row recounted by import; matrix regenerated stamp-aligned from the "
    "eligible battery leg qa/reconcile-all-R2524-retry.log to 57026B with "
    "--check byte-identical and green honestly 591/592. BIRTH SITE: the R2514 "
    "residue block had expired at until R2524, so the shipped idempotent repin "
    "re-read every live round and re-pinned it through R2535 (300 -> 301 "
    "entries, 83156B -> 83255B, readback PINNED) which also declared R2525 "
    "DELIVERED, and the batch appender then CORRECTLY refused a duplicate; "
    "residue_triage --check reads R2525 TRIAGED live=DELIVERED at exit 0. "
    "BOARD: row 561 closed with its DISCHARGED note (predicted and measured "
    "1698899B) and ONE row seeded from this window own measured limit "
    "(AC-PCAS1..AC-PCAS6: an annotated alias of a constant, a with-as binding, "
    "a multi-value for-loop target and a two-hop dict chain all still read "
    "unresolved), floor FLOOR-MET 5/5 10/10 10/10, head now line 563. DEBT: "
    "reconcile-battery-R2525 appended first=yes at 592/4528 (156539B -> "
    "156981B) and product-face-R2525 first=no (156981B -> 157320B), both "
    "readback ok, so the next window owes that battery before any product "
    "byte. HONEST: two product points on a runnable reading, nothing a CEO "
    "opens is new; the defect was measured at R2523 and re-measured here so it "
    "is a repair of a disclosed gap; the limits above are measured, not "
    "assumed; the walk shape is a third copy because parameterising a shipped "
    "face would owe a same-window battery, while tables, resolution law, shape "
    "detector and seam classifier all stay the shipped ones; the state_fold "
    "layout defect from R2524 is still open and the append used a proved "
    "load+dump round-trip instead; Docker absent; the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items; tasks.md untouched; the "
    "S4U lane reconcile still needs an ELEVATED shell."
)

LINE = ("2026-11-07 R2525 product window: annotated/walrus/for constant "
        "bindings read in the seam probe, registry 592/4528")


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if ROW[:60] in text:
        print("BACKLOG already carries this row")
    else:
        io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(
            ROW + "\n" + text)
        back = io.open(BACKLOG, encoding="utf-8").read()
        print("BACKLOG prepended ok=%s bytes=%d"
              % (back.startswith(ROW[:60]),
                 len(back.encode("utf-8"))))
    beat = io.open(HEARTBEAT, encoding="utf-8").read()
    if LINE in beat:
        print("HEARTBEAT already carries this line")
    else:
        if beat and not beat.endswith("\n"):
            beat += "\n"
        io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n").write(
            beat + LINE + "\n")
        print("HEARTBEAT appended lines=%d"
              % len(io.open(HEARTBEAT, encoding="utf-8").read().splitlines()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())