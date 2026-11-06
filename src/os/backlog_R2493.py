"""R2493 backlog: close the carried battery row and prepend the next row."""
import io

P = "src/os/backlog.md"
text = io.open(P, encoding="utf-8", newline="").read()
lines = text.split("\n")

MARK = "- [ ] [carried 2026-11-06 R2492] R2493 first item: the BATTERY owed"
idx = [i for i, line in enumerate(lines) if line.startswith(MARK)]
assert len(idx) == 1, idx

DONE = (
    "- [x] [done 2026-11-06 R2493] R2493 VERIFICATION window on the battery the "
    "register owed (product-face-R2492, pre-registered 575 suites / 4426 "
    "criteria, target re-measured by importing reconcile_all.SUITES before the "
    "run; five-silence scan clean at HEAD f358685d, no index.lock, no unreplied "
    "@BigDomain ledger row, decisions diff new=0, orders tail unchanged, "
    "benchmarks 2026-11-03 inside the gate). The FIRST leg was RED at 573/575 "
    "with three failed assertions, both causes real birth-site defects: the R2492 "
    "evidence file was pwsh-capture (17 CRLF) and the shipped matrix doc carried "
    "no stamp-source provenance line, so --check passed at 55158B while the live "
    "stamp leg re-rendered 55216B. Both repaired at the birth site and committed "
    "ALONE as e3d9c7c1 before the retry (evidence re-taken through the shipped "
    "src/os/evidence_capture.py at 1342B legs=2 identical adjacent=3 fails=0, "
    "census then DRIFT-CLEAN flags=0; matrix regenerated stamp-aligned at "
    "55216B). RETRY GREEN: qa/reconcile-all-R2493-retry.log 868897B utf-8 LF "
    "bom=False crlf=0, RUNNER PASS (575/575 suites green, reconcile controls 7/7, "
    "1164.3s), zero FAIL rows, independent recount of the 575 PASS rows summing "
    "to exactly 4426 criteria. Four follow-up sections PASS (matrix dry-run FAIL "
    "then stamp-aligned regeneration at green=575/575 55212B with --check "
    "byte-identical, fingerprint CLEAN domains=5, profile byte-identical, census "
    "DRIFT-CLEAN) for VERDICT R2493 PASS. DEBT: product-face-R2492 closed (line "
    "215, open 2->1, done 194->195) and product-face-R2493 opened first=yes "
    "naming the next product face. STATE: the append read FOLD-DUE at 81949B and "
    "the fold ran in this window at the round-block boundary over log items 1..89 "
    "(336 tokens carried, post_bytes 12452, FOLD-CLEAR margin 66048). HONEST: "
    "zero product points; both red causes were mine and are named; my aborted "
    "reconcile_daily --check left a truncated qa/reconcile-daily-20261106.log "
    "which was DELETED rather than kept; Docker absent so no containerised "
    "bring-up is claimed; the real 19.9 debit and the real msgSecCheck still wait "
    "on CEO physical items; tasks.md untouched."
)

NEXT = (
    "- [ ] [carried 2026-11-06 R2493] R2494 first item: a PRODUCT face on the "
    "tech head state/queue/tech.md:528 prefix AC-MSFL1 (matrix_stamp_from_"
    "liveness, criteria AC-MSFL1..AC-MSFL6 pinned there at R2442 BEFORE any "
    "code) - a provenance line that names its source document never asks whether "
    "that source still exists. Re-read the row with `python src/os/queue_head.py "
    "--head tech` rather than trusting this line, run a fresh zero-occupancy "
    "anchor check at HEAD before writing anything, ship ONE face with its "
    "pre-registered suite, refill the tech floor if claiming drops claimable "
    "below 10, and commit BEFORE any battery (the R2168 mixed-tree rule). NOTE "
    "(measured twice now): a product commit that moves the queue must also "
    "re-derive docs/status-export.json and land its queue block through the "
    "shipped gate wire, otherwise the next battery reads the queue face STALE. "
    "Also open and needing an ELEVATED shell: BigDomain-OSLoop exists but its "
    "Principal.LogonType still reads InteractiveToken (carried as "
    "loop-s4u-reconcile)."
)

lines[idx[0]] = DONE + "\n" + NEXT
io.open(P, "w", encoding="utf-8", newline="").write("\n".join(lines))
print("replaced line %d; bytes=%d" % (idx[0] + 1,
                                      len(io.open(P, encoding="utf-8",
                                                  newline="").read().encode(
                                          "utf-8"))))