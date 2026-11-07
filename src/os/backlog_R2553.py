"""R2553 backlog ledger: close the carried line this window discharged and
open the next window's carried line at the top. ASCII source, UTF-8 data."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(BASE, "backlog.md")

DONE_PREFIX = "- [ ] [carried 2026-11-08 R2552] R2553 first item:"
DONE_REPLACEMENT = (
    "- [x] [done 2026-11-08 R2553] [was carried 2026-11-08 R2552] "
    "R2553 first item:")

NEW_LINE = (
    "- [ ] [carried 2026-11-08 R2553] R2554 first item: a VERIFICATION window "
    "on the battery the register now names first - reconcile-battery-R2553 at "
    "the pre-registered 606 suites / 4612 criteria, because this window moved "
    "the registry by one row and a shipped document (the R2168 mixed-tree "
    "rule). Re-measure the target by importing reconcile_all.SUITES before the "
    "launch, run the full battery on a CLEAN committed tree with git status "
    "empty, launch it detached through src/os/battery_stream.py with an "
    "explicit --evidence path and NEVER a shell redirection of its stdout into "
    "qa/ (the ps-utf16 trap), keep the red leg if it goes red and commit a "
    "birth-site repair ALONE before any retry, then run the four follow-up "
    "sections through src/os/battery_followup.py (its matrix section FAILS "
    "first by design and must not rewrite the doc; regenerate with "
    "src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after) and land the verdict. On green go "
    "back to the product face the queue head names - re-read it with "
    "`python src/os/queue_head.py --head tech`, which this window left at "
    "state/queue/tech.md:591 prefix AC-PNDR1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_chain (criteria "
    "AC-PNDR1..AC-PNDR6 pinned in that row THIS window before any code): a two "
    "hop module alias chain reads name-unbound, a constant bound inside a "
    "function body reads name-unbound, and a three-group arm with one "
    "disagreeing branch publishes both values without naming the offending "
    "group. NOTE measured many times: a commit that moves the queue must also "
    "re-derive docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute. Also open and misc: state.json stands "
    "at 229870B against the 78500B waterline so state_fold --check reads "
    "FOLD-DUE and this build ships only a --check face, so the fold stays an "
    "OWED obligation seeded as state_fold_run (AC-SFOLD1..6); residue_triage "
    "--check reads TRIAGED with two UNMATCHED entries (R2547, R2549 declared "
    "DELIVERED, live=-); the open rows product-face-R2511, R2513, R2515, "
    "R2517 and R2522 still overstate outstanding work and were disclosed "
    "rather than hand-closed; and BigDomain-OSLoop still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task (carried as the ceo-pending physical item loop-s4u-reconcile, needs "
    "an ELEVATED shell).\n"
)


def main():
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    if DONE_PREFIX not in text:
        print("REFUSED E_BL_NOMATCH: the carried line was not found")
        return 3
    if "R2554 first item:" in text:
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