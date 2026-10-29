import io

PATH = r"state/debt.md"
text = io.open(PATH, encoding="utf-8").read()
sep = chr(10)
lines = text.splitlines()
new_done = (
    "- [x] opened=R2266 | item=product-face-R2267 | closed=R2267 | "
    "note=discharged at R2267: the register named it first=yes and this window "
    "shipped the product half FIRST so the battery could measure a committed "
    "tree, the order R2266 proved - src/os/debt_gate.py plus "
    "src/os/test_debt_gate.py answer one question before any work starts: does "
    "the register carry an open first=yes row, and which one. CLAIM-FIRST names "
    "item/opened/note/carried; OPEN-NONE covers both an empty register and an "
    "all-first=no register because both mean this window owes its own row; a "
    "missing, unreadable or malformed register is REFUSED with the register own "
    "code family because an absent file must not read as nothing owed. Row law "
    "imported from debt_register, zero writes, no clock read, byte-stable JSON. "
    "Criteria AC-DGT1..AC-DGT5 were already pinned in the R2248 f seed row "
    "before the code; SUITE PASS 5/5 double-run identical digest through the "
    "R2261 capture callable (qa/debt-gate-R2267.log), five adjacent os suites "
    "green, wired os-debt-gate(5), LIVE DEBT GATE verdict=CLAIM-FIRST "
    "item=product-face-R2267 carried=1 open=2 first=1. Disclosed divergence: "
    "the row own note proposed the queue_only_floor_wire seed, but it also said "
    "the TOP DELIVERABLE queue row, and the R2248 f debt_gate seed sits above "
    "that seed; queue_only_floor_wire stays open and claimable. The claim "
    "dropped tech claimable to 9 against its floor of 10, so one real gap row "
    "(queue_head, AC-QHD1..AC-QHD6 pre-registered, three anchors "
    "zero-occupancy rc=1) was seeded in the same window and the gauge closed "
    "main 5/5 tech 10/10 explore 10/10 FLOOR-MET. The battery is the successor "
    "row opened here"
)
new_open = (
    "- [ ] opened=R2267 | item=reconcile-battery-R2268 | note=this window "
    "changed src/os (debt_gate.py, test_debt_gate.py) and added one runner "
    "entry, so the R2168 mixed-tree rule applies: run the full reconcile "
    "battery on the committed tree at R2268 with ZERO product edits until it is "
    "green, expect +1 suite / +5 criteria against R2266 (438 suites / 3605 "
    "criteria) from the os-debt-gate suite, then the four follow-up sections. "
    "Second open row loop-s4u-reconcile still needs an elevated shell "
    "(thirty-third consecutive disclosure) | first=yes"
)

replaced = False
out = []
for line in lines:
    if line.startswith("- [ ] opened=R2266 | item=product-face-R2267"):
        out.append(new_done)
        replaced = True
    elif line.startswith("- [ ] opened=R2231 | item=loop-s4u-reconcile"):
        out.append(new_open)
        out.append(line)
    else:
        out.append(line)

if not replaced:
    raise SystemExit("E_TARGET_ROW_NOT_FOUND")

body = sep.join(out)
if not body.endswith(sep):
    body += sep
io.open(PATH, "w", encoding="utf-8", newline=sep).write(body)
print("debt register rewritten, rows=%d" % len(out))