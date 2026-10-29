# BigDomain debt register

Machine-readable carried-debt register. Row law: a row starts at column 0
with `- [ ]` (open) or `- [x]` (done), followed by pipe-separated
`key=value` segments. Known keys: `opened`, `item`, `note`, `first`,
`closed`. Open rows require `opened`, `item` and `first` (`yes`/`no`);
done rows require `opened`, `item` and `closed`. At most one open row may
carry `first=yes` - that is the item that leads the next window.

Checker: `python src/os/debt_register.py --check --round R<n>`
(exit 0 clean / 2 open / 3 missing or malformed / 4 stale / 5 bad flags),
where stale means carried `STALE_WINDOWS` (3) windows or more. Rows are
aged only when a round is supplied; without it the checker reports
`stale=unknown` rather than pretending.

Prose mentions of `- [ ]` inside a sentence are not rows; only a
column-0 checkbox starts one.

## Open

- [ ] opened=R2255 | item=reconcile-battery-R2256 | note=R2255 changed src/os (round_evidence.py, test_round_evidence.py, evidence_R2255.py), one runner entry and three queue/board files; the newest slice is only covered by its own six criteria plus five neighbours, so the next window runs the full battery and the suite-matrix regeneration on the committed tree with zero product code changed (the R2168 mixed-tree rule) | first=yes

- [ ] opened=R2231 | item=loop-s4u-reconcile | note=BigDomain-OSLoop principal reads InteractiveToken, which the 2026-09-29 machine law forbids for lane tasks; repair needs an elevated shell (twenty-third consecutive disclosure at R2254) | first=no
- [x] opened=R2254 | item=product-face-R2255 | note=discharged at R2255: the register named it first=yes, the floors read main 5/5 tech 9/10 explore 10/10 at open (tech was short by the one row this window consumed, so one real gap row was seeded in the same window and the gauge closed at FLOOR-MET 10/10), the P1 canonical rows stay blocked-on-CEO, so the window claimed the top real tech row (the R2248 c seed round_evidence) and shipped one product face with its criteria pinned in the row BEFORE the code; battery debt opened as its successor | closed=R2255

## Closed

- [x] opened=R2253 | item=reconcile-battery-R2254 | note=R2253 changed src/os (queue_row.py, test_queue_row.py, wire_R2253.py, evidence_R2253.py), one runner entry and two queue files; run on the committed tree at R2254 = RUNNER PASS 431/431 suites plus controls 7/7 in 881.2s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2254.log, 764782B at RUNNER close, single-writer utf-8 LF through battery_stream.py), expected criteria total=3564; four follow-up sections all PASS through src/os/battery_followup_R2254.py - matrix regenerated to 431 suites / 3564 criteria and read back byte-identical (docs/sandbox-suite-matrix.md, 41967B, green=431/431), fingerprint CLEAN over 5 domains, runner profile --daily --check PASS, writer census re-frozen then DRIFT-CLEAN files=2192 tee=1663 baselined=529 disappeared=0 flags=0; the +1 suite / +6 criteria against R2252 is exactly the R2253 os-queue-row suite joining the registry | closed=R2254

- [x] opened=R2248 | item=reconcile-battery-and-matrix | note=R2248 changed src/os (debt_register.py, test_debt_register.py, evidence/seed helpers), the battery runner and two queue files; run on the committed tree at R2249 = RUNNER PASS 428/428 plus controls 7/7 in 1165.7s, tmp reclaim 932/932 worlds 326.57 MiB, then matrix 428 suites / 3546 criteria byte-identical, fingerprint CLEAN, profile PASS, census DRIFT-CLEAN files=2181 | closed=R2249

- [x] opened=R2247 | item=queue-seeding | note=floors were short by 10 at the R2247 closeout (tech 5/10, explore 5/10 claimable); ten seed rows with pre-registered criteria landed here, every anchor checked zero-occupancy against HEAD, and the gauge now reads main 5/5 tech 10/10 explore 10/10 FLOOR-MET | closed=R2248

- [x] opened=R2244 | item=reconcile-battery-and-matrix | note=deferred by R2244/R2245/R2246, run to RUNNER PASS 427/427 plus the four follow-up sections at R2247 | closed=R2247

- [x] opened=R2250 | item=reconcile-battery-and-matrix | note=R2250 changed src/os (export_freshness.py, test_export_freshness.py, evidence_R2250.py) and R2251 added src/os/debt_append.py, test_debt_append.py and evidence_R2251.py plus one runner and two queue files; closed at R2252 on the committed tree = RUNNER PASS 430/430 suites plus controls 7/7 in 798.1s, tmp reclaim 932/932 worlds 326.57 MiB, then matrix 430 suites / 3558 criteria byte-identical, fingerprint CLEAN, profile PASS, census DRIFT-CLEAN files=2188 | closed=R2252
