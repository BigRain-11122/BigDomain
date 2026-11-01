"""heartbeat_R2366.py - append this round's one-line heartbeat entry.

One-off for the round: the heartbeat is a rolling one-line-per-round file, so
the append is a single text write with a read-back proof.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(ROOT, "heartbeat.txt")

LINE = (
    "R2366: product window - the follow-up CLI now answers a bare --help at "
    "exit 0 (it used to call the operator wrong with exit 5) and answers from "
    "TWO imported contracts (reconcile_all.CLI_CONTRACT through the guard own "
    "importer, plus its own parser flag tables), so no second flag table "
    "exists; SUITE PASS 6/6 twice at criterion digest 7e6881b726a46311 with "
    "os-battery-followup and os-run-argument-guard still 6/6 unchanged and the "
    "live --help captured at exit 0. The debt gate pointed at FINISHED work "
    "(product-face-R2365, shipped at R2365) and that row was verified by "
    "measurement then closed through debt_close rather than re-run; seven new "
    "group decision rows D-20261102-07..13 read in full and none dispatches "
    "this company; tech row 412 stamped and one REAL gap seeded "
    "(contract_usage_renderer). Disclosed and repaired at the birth site: the "
    "first closeout fold picked a tokens LINE as its boundary and archived this "
    "round own narrative, the second picked one inside the R2365 block and read "
    "rounds_without_ledger=2365, so the archive section was trimmed, the state "
    "restored byte-exact from the fold backup and refolded at line 69 "
    "(predicted=measured 16702B, 771 tokens, ledger CLEAN), after which the "
    "nine fold-created residue rounds were spliced in ONE atomic replace "
    "(213->222 entries, TRIAGED 222/222). Two product points.\n"
)


def main():
    with io.open(PATH, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    if "R2366:" in text:
        print("REFUSE already present")
        return 2
    body = text if text.endswith("\n") else text + "\n"
    body += LINE
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(PATH, "r", encoding="utf-8", errors="replace") as handle:
        back = handle.read()
    ok = back.endswith(LINE)
    print("HEARTBEAT appended=%s bars=%d" % (ok, len(back.splitlines())))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())