"""backlog_R2562 - mark the R2562 item done and prepend the R2563 first item."""

import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(BASE, "src", "os", "backlog.md")

DONE_MARK = "[x] [done 2026-11-08 R2562] [was carried 2026-11-08 R2561]"
NEW = (
    "- [ ] [carried 2026-11-08 R2562] R2563 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:599 prefix "
    "AC-PNDC1 (criteria AC-PNDC1..AC-PNDC6 pinned in that row at R2561 BEFORE "
    "any code). Re-read it with `python src/os/queue_head.py --head tech` "
    "rather than trusting this line (claimable=12, floor FLOOR-MET 5/5 12/10 "
    "10/10), run a fresh zero-occupancy anchor check at HEAD before any code, "
    "ship ONE face with its pre-registered suite, prove it twice through the "
    "shipped capture callable with an identical digest, run the adjacent "
    "probe suites, and add a bounded live leg with the same fixtures measured "
    "on BOTH readers. Commit BEFORE any battery - NO successor battery is "
    "owed at open because R2562 moved no product src byte and the registry is "
    "unmoved at 610 suites / 4636 criteria, re-read by import. NOTE measured "
    "many times: a commit that moves the queue must also re-derive "
    "docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute. Also open and misc: state.json reads "
    "296983B against the 78500B waterline so state_fold --check reads "
    "FOLD-DUE and this build ships only a --check face, so the fold stays an "
    "OWED obligation seeded as state_fold_run (AC-SFOLD1..6); the open rows "
    "product-face-R2511, R2513, R2515, R2517 and R2522 still overstate "
    "outstanding work and were disclosed rather than hand-closed; "
    "queue_row --check still reads pre-existing VIOLATIONS on rows that "
    "predate this window; and BigDomain-OSLoop still reads InteractiveToken, "
    "which the 2026-09-29 machine law forbids for every lane task (carried as "
    "the ceo-pending physical item loop-s4u-reconcile, needs an ELEVATED "
    "shell)."
)


def main():
    with open(P, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    target = lines[1]
    if not target.startswith("- [ ] [carried 2026-11-08 R2561] R2562 first item"):
        raise SystemExit("unexpected backlog head: " + target[:80])
    lines[1] = target.replace("- [ ] [carried 2026-11-08 R2561]",
                              DONE_MARK, 1)
    lines.insert(0, NEW)
    out = "\n".join(lines).encode("utf-8")
    tmp = P + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, P)
    with open(P, "rb") as fh:
        back = fh.read()
    print("backlog bytes", len(back), "lines", back.count(b"\n") + 1,
          "crlf", back.count(b"\r\n"))


if __name__ == "__main__":
    main()