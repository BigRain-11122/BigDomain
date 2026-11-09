# -*- coding: utf-8 -*-
"""One-off R2595 board writer: repair row + successor seed row."""
import io

P = 'state/queue/tech.md'
text = io.open(P, encoding='utf-8').read()
lines = text.splitlines()
anchor = lines[628]
assert anchor.startswith('- [ ] P2 tech seed (R2594'), anchor[:60]

repair = (
    "- [x] [done 2026-11-09 R2595] BIRTH-SITE REPAIR of the round export driver health term "
    "`src/os/export_R2431.py` - MEASURED by the R2595 battery, not guessed: `os-export-driver-queue-face` read "
    "4/6 with AC-EDQF2 and AC-EDQF5 red, printing `queue=CURRENT queue_bytes=398052 ok=False` and exiting 2, because "
    "the health term demanded `log_lines_in_window == substantive_non_idle_mention_lines` (51 vs 50 on the live window). "
    "That equality can NEVER hold once one `tokens:` line sits in the window, since `check_export_consistency.recompute` "
    "counts a tokens line as a window line and never as substantive. The term now compares the document whole "
    "`self_drive` block against a FRESH recompute at call time. Criteria AC-EDSH1..AC-EDSH6 in "
    "`src/os/test_export_driver_self_drive_health.py` were authored AFTER the repair byte (disclosed, weaker evidence "
    "than a pre-registered suite): fresh-recompute term is live, the tokens-line window exits 0, a document doctored "
    "on disk after the write exits 2, a non-CURRENT gate word still reds the run, every earlier health term survives, "
    "hygiene plus registry wiring. PROOF: SUITE PASS 6/6 twice with identical output plus two adjacent export suites "
    "green (qa/export-driver-self-drive-health-R2595.log, 2322B, legs=2 identical=True adjacent=2 fails=0). "
    "REGISTRY 629/4750 -> 630/4756 recounted by import (630 unique names, 630 unique paths)."
)

seed = (
    "- [ ] P2 tech seed (R2595, from this window own measured limit): `src/os/export_R2431.py` health-term RACE and "
    "size agreement - MEASURED this window: the repaired term re-reads the document and recomputes `self_drive` a SECOND "
    "time, so any writer that appends one state log line between the write and the read-back would make a healthy "
    "refresh read `ok=False`; and the printed `queue_bytes` is never compared with `os.path.getsize(EXPORT)` although "
    "both appear in the same statement. Criteria AC-EDSW1..AC-EDSW6 pinned HERE BEFORE any code: AC-EDSW1 a "
    "`self_drive` block that moved because the LOG moved between write and read-back is reported as its own word "
    "(`DRIFT-UNDER-WRITE`), distinct from a document doctored after the write; AC-EDSW2 a document doctored after the "
    "write keeps the refusal it has today byte for byte; AC-EDSW3 the run asserts `queue_bytes` equals the size on disk "
    "and names the pair when it does not; AC-EDSW4 a caller whose log moves twice in one call still gets exactly one "
    "verdict word and no partial write; AC-EDSW5 every R2595 term survives beside the new ones (tick row, outs, three "
    "ceo fields, stamp, fresh self_drive, gate); AC-EDSW6 pure ASCII, stdlib only, no network, its own reconcile label "
    "and its own suite."
)

out = lines[:628] + [repair, seed] + lines[628:]
io.open(P, 'w', encoding='utf-8', newline='\n').write("\n".join(out) + "\n")
print('lines %d -> %d' % (len(lines), len(out)))