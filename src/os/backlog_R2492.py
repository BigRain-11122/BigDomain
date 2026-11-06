"""R2492 backlog: close the carried row and prepend the two next-round rows."""
import io

P = "src/os/backlog.md"
text = io.open(P, encoding="utf-8", newline="").read()

OLD_MARK = "- [x] [done 2026-11-06 R2491] R2491 TECH window"
assert text.startswith(OLD_MARK), text[:80]

DONE = (
    "- [x] [done 2026-11-06 R2492] R2492 TECH window on the carried product leader "
    "(product-face-R2491, tech head state/queue/tech.md:527 prefix AC-RMPP1, "
    "criteria AC-RMPP1..AC-RMPP6 pinned there at R2440 BEFORE any code; "
    "five-silence scan clean at HEAD f358685d, no index.lock, no unreplied "
    "@BigDomain ledger row, decisions diff new=0, orders tail unchanged, "
    "benchmarks 2026-11-03 inside the gate; debt_gate CLAIM-FIRST). CLAIM: neither "
    "the corpus-scope face nor the existence face asked whether the DECLARED "
    "package is carried by the read tree, so --package nosuchpkg joined every "
    "relative import onto a package that does not exist and a declaration typo was "
    "published as N broken imports. SHIPPED src/os/"
    "relative_package_presence_refusal.py + src/os/"
    "test_relative_package_presence_refusal.py: the declared package gets a "
    "presence decision on the parent own root-wide corpus (ABSENT / MARKER / "
    "PRESENT with a carrier count); ABSENT refuses ONCE as E_RMPP_NO_PACKAGE "
    "naming the declaration and the corpus searched with ZERO per-import rows; a "
    "carried declaration keeps the parent reading byte for byte (all 22 "
    "REPORT_KEYS compared equal); a package carried only by __init__.py reads "
    "MARKER not ABSENT; the corpus is the R2440 walk asked once, the parent "
    "reading being handed that same measurement behind a root equality guard "
    "restored in a finally block. PROOF: AC-RMPP1..AC-RMPP6 SUITE PASS 6/6 TWICE "
    "identical + three adjacent suites green (qa/"
    "relative-package-presence-refusal-R2492.log, legs=2 identical=True, fails=0). "
    "LIVE on one real tree (qa/relative-package-presence-refusal-live-R2492.log, "
    "utf-8 LF): declared=nosuchpkg rc=2 verdict=NO-PACKAGE presence=ABSENT "
    "missing_rows=0, and declared=mypkg rc=2 verdict=MISSING-MODULE "
    "presence=PRESENT missing_modules=mypkg.nosuchmodule - the refusal does not "
    "hide a real typo. REGISTRY 574/4420 -> 575/4426 by exactly one row "
    "os-relative-package-presence-refusal(6); matrix restamped stamp-aligned to "
    "55158B at 575/4426 with a byte-identical --check whose green line honestly "
    "reads 574/575; product-face-R2491 closed (line 214, open 2->1, done "
    "193->194) and product-face-R2492 opened first=yes through their shipped "
    "writers. HONEST: internal tech face, zero product points on the Executive "
    "Protocol scale; my own first live leg was wrong twice (a helper-only "
    "publisher read EMPTY, a second placement inside the package confused the "
    "scan) and only the R2440 fixture text reproduced the defect - the criteria "
    "were never loosened to fit; the one-walk substitution mutates a module "
    "attribute for one call and is a real limit for concurrent in-process "
    "callers; Docker absent so no containerised bring-up claimed; real 19.9 debit "
    "and real msgSecCheck still wait on CEO physical items; tasks.md untouched.\n"
)

CARRIED = (
    "- [ ] [carried 2026-11-06 R2492] R2493 first item: the BATTERY owed on the "
    "registry R2492 moved to 575 suites / 4426 criteria (product-face-R2492, "
    "first=yes), on the committed tree BEFORE any further product byte - the "
    "R2168 mixed-tree rule. Re-measure the target by importing "
    "reconcile_all.SUITES before launching rather than trusting this note, run it "
    "detached (pid file in logs/) because the runner tees a block-buffered stdout "
    "and the shell watchdog cancels five minutes of silence, then run the four "
    "follow-up sections (matrix dry-run FAIL then stamp-aligned regeneration from "
    "this round own evidence, fingerprint, profile, census) and close the row "
    "through debt_close. Only after that: a product face on the tech head "
    "state/queue/tech.md:528 prefix AC-MSFL1 (matrix_stamp_from_liveness, criteria "
    "AC-MSFL1..AC-MSFL6 pinned there at R2442 before any code) - a provenance line "
    "that names its source document never asks whether that source still exists. "
    "Also open and needing an ELEVATED shell: BigDomain-OSLoop exists but its "
    "Principal.LogonType is still InteractiveToken (carried as loop-s4u-reconcile).\n"
)

text = text.replace(OLD_MARK, DONE + CARRIED + OLD_MARK, 1)
OLD_CARRIED = "- [ ] [carried 2026-11-06 R2491] R2492 first item:"
assert text.count(OLD_CARRIED) == 1
text = text.replace(OLD_CARRIED,
                    "- [x] [done 2026-11-06 R2492] [carried 2026-11-06 R2491] "
                    "R2492 first item:", 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(text)
print("backlog updated")