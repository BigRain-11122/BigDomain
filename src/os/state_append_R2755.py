"""state_append_R2755 - settle the R2742 leg RED and pre-register its successor.

Every claim in these lines is measured by src/os/settle_battery_R2742.py,
whose output is qa/battery-R2742-settlement.log: the evidence file, the
registry by import, and the five red suites re-run one by one on this
tree. Nothing is adopted; nothing is relaunched over.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2755

LINES = [
    (
        "R2755 THE R2742 LEG SETTLED RED ON MEASURED BYTES, NOT ADOPTED: "
        "qa/reconcile-all-R2742.log 1252699B, utf-8, bom=False, crlf=0, "
        "lone_cr=0, nul=0, 676 suite rows over 676 unique names, criteria "
        "recount EXACTLY 5032, pass_rows=671, fail_rows=5, closing line "
        "RUNNER FAIL (6 failed assertions) with no BATTERY rc= row, pid 64528 "
        "GONE by kernel probe. Per-suite times are in the evidence; the leg "
        "kept its own bytes and was not relaunched over."
    ),
    (
        "R2755 THE FIVE RED ROWS ARE ONE CALIBER AND THEY REHEAL 5/5 ON THIS "
        "TREE: os-ledger-lines (AC-LGR8), os-ledger-archive (AC-LGA7 AC-LGA8), "
        "os-ledger-baseline (AC-LGB8), os-ledger-fold-kind (AC-FCLS6) and "
        "os-ledger-fold-kind-dateprefix (AC-LKND6) are all live-gate-clean "
        "assertions, and re-run individually on the committed tree they read "
        "8/8 8/8 8/8 6/6 6/6 with zero fail-lines. Birth site is therefore "
        "named twice over: the R2742 closeout omitted its own round ledger "
        "line (restored at R2745) and the log it measured was the pre-fold "
        "98-item file (folded at R2754, commit 3fa9b49f). Evidence "
        "qa/battery-R2742-settlement.log written by the shipped measurement."
    ),
    (
        "R2755 THE MIXED-TREE OBLIGATION IS NOT DISCHARGED BY THAT REHEAL: "
        "product src moved under the leg (src/os/logs_toolkit.py, "
        "src/os/test_logs_toolkit.py, src/os/export_R2431.py since 022f916f), "
        "so no full battery has run on the tree that will carry the next "
        "product byte. reconcile-battery-R2742 was closed through the shipped "
        "debtor at R2755 and reconcile-battery-R2755 opened first=yes with the "
        "successor pre-registered BEFORE its launch: target re-measured by "
        "import at 676 suites / 5032 criteria / 676 unique names / 676 unique "
        "paths, evidence qa/reconcile-all-R2755.log, stream and pid in "
        "separate files under logs/, and every export and state write "
        "committed first so no export byte moves inside the leg reading window "
        "(the R2752 order lesson)."
    ),
    (
        "R2755 tokens: local=~7k api=0 api_reason=debt settlement window - one "
        "five-silence scan on tokens and tails, one kernel liveness probe on "
        "the leg pid, one evidence measure plus one registry import plus five "
        "single-suite re-runs shipped as one settlement artifact, two debt "
        "register writes with readback, one state append, one board rewrite; "
        "zero cloud calls and zero external API touches"
    ),
]


def main():
    data = state_io.parse(state_io.decode(state_io.read_raw(STATE)))
    log = data["log"]
    if any(l.startswith("R2755 THE R2742 LEG SETTLED RED") for l in log):
        sys.stdout.write("NOOP\n")
        return 0
    for line in LINES:
        log.append(line)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    sys.stdout.write("APPENDED %d lines tick=%d\n" % (len(LINES), TICK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
