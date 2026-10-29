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

- [ ] opened=R2248 | item=reconcile-battery-and-matrix | note=R2248 changed src/os (debt_register.py, test_debt_register.py, evidence/seed helpers), the battery runner and two queue files; the full battery plus the suite-matrix regeneration must run on the committed tree before the next product edit (R2168 mixed-tree rule) | first=yes
- [ ] opened=R2231 | item=loop-s4u-reconcile | note=BigDomain-OSLoop principal reads InteractiveToken, which the 2026-09-29 machine law forbids for lane tasks; repair needs an elevated shell (seventeenth consecutive disclosure at R2247) | first=no

## Closed

- [x] opened=R2247 | item=queue-seeding | note=floors were short by 10 at the R2247 closeout (tech 5/10, explore 5/10 claimable); ten seed rows with pre-registered criteria landed here, every anchor checked zero-occupancy against HEAD, and the gauge now reads main 5/5 tech 10/10 explore 10/10 FLOOR-MET | closed=R2248

- [x] opened=R2244 | item=reconcile-battery-and-matrix | note=deferred by R2244/R2245/R2246, run to RUNNER PASS 427/427 plus the four follow-up sections at R2247 | closed=R2247