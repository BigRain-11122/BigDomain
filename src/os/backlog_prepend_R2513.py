"""R2513 backlog prepend: one done row and one carried row, CRLF preserved."""
import io

P = "src/os/backlog.md"

DONE = (
    "- [x] [done 2026-11-07 R2513] R2513 PRODUCT window on the tech head the "
    "register named (product-face-R2512, state/queue/tech.md:551 prefix "
    "AC-PSMR1 probe_seam_registry, criteria AC-PSMR1..AC-PSMR6 pinned there at "
    "R2511 BEFORE any code). Five-silence scan clean at HEAD ef3eb183 (git "
    "status empty, no index.lock, zero @BigDomain ledger rows, decisions diff "
    "new=0 over the stored 90-token baseline at a measured 189 rows, group "
    "orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside "
    "the gate); debt_gate CLAIM-FIRST product-face-R2512 first=1 and no "
    "battery owed. CLAIM: R2511 disclosed that wiring the FIFTH guard seam cost "
    "TWO hand edits to already-shipped probes because each enumerated the seam "
    "names it quieted, and the repair still leaves the next seam to be "
    "remembered per probe. SHIPPED src/os/probe_seam_registry.py plus its "
    "suite: the seam set is DERIVED from the SHIPPED render at CALL time (every "
    "global the render own code object asks, kept only when it really carries a "
    "callable guard), so no seam name is spelled in the module; a module that "
    "quiets at least one seam is a PROBE and reads COVERED or MISSING-SEAM "
    "naming the seam and its file, a module naming no seam reads OUT-OF-SCOPE "
    "rather than clean, an unparseable source reads UNREADABLE rather than "
    "being skipped, and a round-token file reads HISTORICAL; no probe is ever "
    "imported, so a stale probe is NAMED rather than RUN; a probe is never "
    "asked to quiet its OWN seam. PROOF: AC-PSMR1..AC-PSMR6 SUITE PASS 6/6 "
    "TWICE identical plus three adjacent readability suites green "
    "(qa/probe-seam-registry-R2513.log 4885B legs=2 identical=True fails=0 "
    "adjacent=3), the CALL-time derivation proved both by an independent AST "
    "reading of the render source and by patching SM.render to ask a new guard "
    "global and watching the set move; a stale fixture refuses the shipped tool "
    "at exit 2 while carrying a module-level raise that would have fired had it "
    "been imported. LIVE: qa/probe-seam-registry-live-R2513.log (849B, "
    "class=tee) reads SEAMS-COVERED over 3 covered probes with the render and "
    "artifact digests unchanged, then a fixture stale probe as MISSING-SEAM "
    "missing=STPT. REGISTRY 585/4486 -> 586/4492 by exactly one row "
    "os-probe-seam-registry(6); matrix regenerated stamp-aligned to 56372B at "
    "586/4492 with --check byte-identical and green honestly 585/586. BOARD: "
    "row 551 closed through a per-round writer (predicted and measured "
    "1671421B, readback ok) and ONE row seeded from this window own MEASURED "
    "limit - a probe forwarding its quieting through a helper module reads "
    "OUT-OF-SCOPE while the helper reads COVERED, so that shape is invisible - "
    "as AC-PSF1..AC-PSF6; floor FLOOR-MET 5/5 10/10 10/10, head now line 552. "
    "DEBT: product-face-R2512 closed (line 234, open 3->2, done 213->214, "
    "146882B -> 146885B readback ok), reconcile-battery-R2513 appended "
    "first=yes at 586/4492 (146885B -> 147304B), product-face-R2513 appended "
    "first=no naming tech head 552 AC-PSF1 (147304B -> 147666B). HONEST: one "
    "product point on a runnable reading, nothing a CEO could open; the defect "
    "was measured at R2511; the forwarding gap is seeded rather than hidden; "
    "Docker absent; tasks.md untouched; the S4U lane reconcile still needs an "
    "ELEVATED shell; the fold ran at a true round-block boundary (window 1..78, "
    "80166B -> 12885B, predicted==actual, 386 tokens carried none missing).\r\n"
)

CARRIED = (
    "- [ ] [carried 2026-11-07 R2513] R2514 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule), pre-registered at 586 suites / 4492 criteria - exactly what R2513 "
    "registered when it moved the registry by one row - and any larger delta "
    "must be named rather than swept. Run the full battery with an empty git "
    "status before the run, launch it detached and unfiltered through "
    "src/os/battery_stream.py (the filtering-pipe trap has cost earlier windows "
    "their whole run), keep the red leg if it goes red, then the four follow-up "
    "sections through src/os/battery_followup.py (its matrix section FAILS "
    "first on a stale doc by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py after, stamp-aligned from this round own green "
    "evidence). On green go back to the product face the register names next - "
    "re-read it with `python src/os/queue_head.py --head tech`, which R2513 left "
    "at state/queue/tech.md:552 prefix AC-PSF1 probe_seam_forwarding_scope "
    "(criteria pinned there THIS window before any code): a probe that forwards "
    "its seam quieting through a shared helper module reads OUT-OF-SCOPE while "
    "the helper reads COVERED, so the forwarding shape is invisible today. NOTE "
    "measured many times: a commit that moves the queue must also re-derive "
    "docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute, otherwise the next battery reads the "
    "queue face STALE. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop exists but its Principal.LogonType still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task (carried as the stale row loop-s4u-reconcile).\r\n"
)

raw = io.open(P, "rb").read()
if raw.count(b"\n") != raw.count(b"\r\n"):
    print("FAIL backlog dialect: %d lf vs %d crlf"
          % (raw.count(b"\n"), raw.count(b"\r\n")))
    raise SystemExit(2)
head = (DONE + CARRIED).encode("utf-8")
with io.open(P, "wb") as handle:
    handle.write(head + raw)
after = io.open(P, "rb").read()
print("bytes before=%d after=%d crlf=%d lone_lf=%d"
      % (len(raw), len(after), after.count(b"\r\n"),
         after.count(b"\n") - after.count(b"\r\n")))