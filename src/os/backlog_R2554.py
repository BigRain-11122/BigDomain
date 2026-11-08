"""R2554 backlog ledger: close the carried line this window discharged and
open the next window's carried line at the top. ASCII source, UTF-8 data."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(BASE, "backlog.md")

DONE_PREFIX = "- [ ] [carried 2026-11-08 R2553] R2554 first item:"
DONE_REPLACEMENT = (
    "- [x] [done 2026-11-08 R2554] [was carried 2026-11-08 R2553] "
    "R2554 first item:")

NEW_LINE = (
    "- [ ] [carried 2026-11-08 R2554] R2555 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:591 prefix "
    "AC-PNDR1 probe_seam_name_binding_arm_mixed_residual_alias_chain, criteria "
    "AC-PNDR1..AC-PNDR6 pinned in that row at R2553 BEFORE any code. The "
    "measured limits, taken from the shipped residual-naming face own reader: "
    "(1) a TWO HOP module alias chain reads name-unbound, so a constant that "
    "reaches its literal through another module constant is invisible; (2) a "
    "constant declared inside a FUNCTION BODY reads name-unbound when the "
    "reading needs it as a module-level value; (3) a three-group arm chain "
    "with one disagreeing branch publishes BOTH values by full path but names "
    "no group, so the caller cannot see which group disagreed. Re-read the row "
    "with `python src/os/queue_head.py --head tech` rather than trusting this "
    "line (claimable=12, floor FLOOR-MET 5/5 12/10 10/10), run a fresh "
    "zero-occupancy anchor check at HEAD before any code, ship ONE face with "
    "its pre-registered suite, prove it twice through the shipped capture "
    "callable, run the adjacent probe suites, and add a live leg with the same "
    "fixtures measured on BOTH readers. Commit BEFORE any battery - NO "
    "successor battery is owed at open because R2554 moved no product src byte "
    "and the registry is unmoved at 606 suites / 4612 criteria, re-read by "
    "import. NOTE measured many times: a commit that moves the queue must also "
    "re-derive docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute. Also open and misc: state.json stands "
    "at 236570B against the 78500B waterline so state_fold --check reads "
    "FOLD-DUE and this build ships only a --check face, so the fold stays an "
    "OWED obligation seeded as state_fold_run (AC-SFOLD1..6); residue_triage "
    "--check reads TRIAGED with THREE UNMATCHED entries (R2547, R2549 and "
    "R2553 declared DELIVERED, live=-); the open rows product-face-R2511, "
    "R2513, R2515, R2517 and R2522 still overstate outstanding work and were "
    "disclosed rather than hand-closed; queue_row --check still reads "
    "pre-existing VIOLATIONS on rows that predate this window; and "
    "BigDomain-OSLoop still reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task (carried as the ceo-pending "
    "physical item loop-s4u-reconcile, needs an ELEVATED shell).\n"
)


def main():
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    if DONE_PREFIX not in text:
        print("REFUSED E_BL_NOMATCH: the carried line was not found")
        return 3
    if "R2555 first item:" in text:
        print("REFUSED E_BL_DUPLICATE: the next carried line already exists")
        return 2
    before = len(text.encode("utf-8"))
    text = text.replace(DONE_PREFIX, DONE_REPLACEMENT, 1)
    text = NEW_LINE + text
    out = text.encode("utf-8")
    tmp = BACKLOG + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, BACKLOG)
    back = open(BACKLOG, "rb").read()
    print("BACKLOG before=%dB after=%dB crlf=%d readback=%s"
          % (before, len(back), back.count(b"\r\n"),
             "ok" if back == out else "MISMATCH"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())