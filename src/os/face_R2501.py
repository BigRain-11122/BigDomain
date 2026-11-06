"""R2501 heartbeat row and the backlog line this round records (one write each)."""
import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
HEART = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(BASE, "backlog.md")

ROW = "2026-11-07T03:3x R2501 tick 2501 product face\n"

ENTRY = (
    "- [x] [done 2026-11-07 R2501] " +
    json.dumps(
        "R2501 PRODUCT window on the tech head the register named (product-face-R2500, "
        "state/queue/tech.md:535 prefix AC-CEPM1 closeout_export_parity_text_binding, "
        "criteria AC-CEPM1..AC-CEPM6 pinned in that row at R2454 BEFORE any code). Five-silence "
        "scan at open was clean at HEAD 3e84d40f (git status empty, no index.lock, zero "
        "@BigDomain rows in cph4/evolution-ledger.md, group orders tail unchanged at 2026-11-06 "
        "23:46, benchmarks 2026-11-03 inside the seven-day gate); the decisions diff read 2 new "
        "tokens, the known prose artifact D-20261105-0 and D-20261107-07 (HQ PROBE A escalation "
        "dispatching @CPH4 by 12:00, no BigDomain face), both acknowledged with the baseline "
        "advanced; debt_gate read CLAIM-FIRST product-face-R2500 first=1 and no battery owed. "
        "CLAIM: closeout_export_parity_wire.publish proves the bytes it is handed against the "
        "parity, but the parity recomposes the STAGED bytes, so nothing asked whether those "
        "bytes are what the document being replaced composes to - MEASURED at R2454 a "
        "composition made from document A published over document B read WRITTEN/AGREES and "
        "wrote A content into B. SHIPPED src/os/closeout_export_parity_text_binding.py plus its "
        "suite: the binding is asked through the SHIPPED composition at CALL time, line endings "
        "are normalised only (transport stays the target own business and GWDA.payload_for still "
        "renders it on the write path), and text carrying another document content is refused "
        "with E_CEPM_BINDING naming the first differing field from the shipped difference law "
        "BEFORE any byte is staged, leaving the target byte-identical with no residue; the wire "
        "seven reading keys keep names, positions and values and binding/differs are strictly "
        "additional. PROOF: AC-CEPM1..AC-CEPM6 SUITE PASS 21/21 TWICE identical plus three "
        "adjacent suites green (qa/closeout-export-parity-text-binding-R2501.log, 2898B, "
        "legs=2 identical=True adjacent=3 fails=0). LIVE on the real tree: the shipped export "
        "composes to itself with difference=(none) at 215518 bytes, publishing that same "
        "composition reads WRITTEN/BOUND, and a composition from a doctored copy reads REFUSED "
        "with differs=self_drive.window_days while the target stays byte-identical (302B utf-8 "
        "LF live log). REGISTRY 578/4444 -> 579/4450 by one row, recounted by import; matrix "
        "regenerated stamp-aligned to 55613B with --check byte-identical and green honestly "
        "578/579. BOARD: row 535 closed with its DISCHARGED note through a per-round writer "
        "(predicted 1639200B -> 1643892B, measured exactly, readback ok) and TWO measured gaps "
        "seeded so the floor reads FLOOR-MET 5/5 10/10 10/10 - AC-CEPB1 (TWELVE closeout scripts "
        "call CEPW.publish directly and none asks the binding) and AC-DFOB1 (first_difference "
        "answers the shape word 'bytes' for an order-only difference while a value difference "
        "names 'y'). DEBT: product-face-R2500 closed (135564B -> 135567B, readback ok) and "
        "reconcile-battery-R2501 opened first=no (135567B -> 136171B, readback ok) at the "
        "measured 579 suites / 4450 criteria. HONEST: two product points for a real shipped "
        "write path, nothing a CEO opens is new; the defect was measured by R2454 and repaired "
        "here; both seeds are measurements taken this window and neither is claimed as fixed; "
        "Docker absent; the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
        "items; tasks.md untouched.", ensure_ascii=False)
    + "\n"
)

with io.open(HEART, "rb") as handle:
    raw = handle.read()
if raw.startswith(b"\xff\xfe"):
    heart = raw.decode("utf-16")
    encoding = "utf-16"
else:
    heart = raw.decode("utf-8")
    encoding = "utf-8"
if not heart.endswith("\n"):
    heart += "\n"
heart += ROW
with io.open(HEART, "w", encoding=encoding, newline="") as handle:
    handle.write(heart)

with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
    current = handle.read()
if "R2501 PRODUCT window" in current.split("\n")[0]:
    raise SystemExit("E_R2501_BACKLOG already carries this round")
with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
    handle.write(ENTRY + current)

print("heartbeat bytes=%d rows=%d"
      % (len(heart.encode("utf-8")), len(heart.splitlines())))
print("backlog bytes=%d" % os.path.getsize(BACKLOG))