"""R2795 closeout: append the window log rows and bump the tick.

The battery row R2794 owed for tools/ledger_reconcile_face.py landed this
window: src/os/test_ledger_reconcile_face.py carries AC-LRB1..AC-LRB8 and the
registry gained os-ledger-reconcile-face at eight criteria (686 suites /
5104 criteria). Writes through state_io.write_document, the canonical writer.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

STATE = os.path.join(HERE, "state.json")

ROWS = [
    "2026-11-15 R2795 PRODUCT + DEBT CLOSED: the R2794 carry (a face with no "
    "battery row) is gone - src/os/test_ledger_reconcile_face.py lands AC-LRB1..AC-LRB8 "
    "in a private world and drives the SHIPPED gate twice: clean (rc=0, zero findings, "
    "repo pair bytes AND mtime untouched) and against a PRIVATE copy whose first check "
    "name was altered (three findings, i.e. the gate is load-bearing rather than "
    "decorative). SUITE PASS 8/8 measured: rows=8 announced=8, real=PASS seeded=PASS "
    "fails=0, entries=0 empty=True disclosed=True, control_rc=2 flipped=2 named-in-rows=True, "
    "live ledger.db plus -wal/-shm byte- and mtime-identical before and after.",
    "2026-11-15 R2795 the criteria were pinned BEFORE the code, in this order: the "
    "AC-LRB1..AC-LRB8 row was written into src/os/backlog.md first, the suite file second, "
    "and the registry row third - so this window does not repeat R2780's same-window "
    "pin disclosure. One criterion was NARROWED before any failure: AC-LRB4 asserts the "
    "derived values and the tool's own exit-code mapping, NOT byte-identity between two "
    "renders, because R2794 measured that the shipped ledger API mints random tx ids; "
    "the narrowing is stated in the suite docstring and in the pinned row. Registry now "
    "reads 686 suites / 5104 criteria; docs/sandbox-suite-matrix.md regenerated 72428B "
    "and reads byte-identical under --check, suite_matrix_reconcile reads DOC-CURRENT, "
    "the face's own gate reads VERDICT PASS 6/6 checks=8 real=PASS empty=True seeded=PASS "
    "control=FAIL flipped=2, and preview/index.html re-rendered to 35359B with "
    "deliverable_index VERDICT PASS 14/14 fingerprint=5ef05abdfe2aee6e.",
    "2026-11-15 R2795 honest disclosures: (a) this window added a GUARD around an "
    "existing page, so the CEO-visible surface itself did not change - the product "
    "increment is engineering honesty (the eight green checks now have a battery row "
    "that can go red), not a new page; (b) the suite does not re-render the page and "
    "does not assert the page is current with the live book - that remains "
    "tools/ledger_reconcile_face.py --check own job, and it passes 6/6; (c) the full "
    "battery is STILL OWED and grew to 686 suites / 5104 criteria, no leg was launched "
    "in this 25-minute window; (d) the shipped sandbox book is still an EMPTY book "
    "(0 entries, 5 accounts) - this window did not seed it, so the green reconcile "
    "remains a vacuous green by content, exactly as R2794 disclosed; (e) state.json was "
    "already over the 78500B waterline before this append and the round-aligned fold is "
    "still owed; (f) tasks.md was not touched, it is the P-47 canonical board; (g) every "
    "P-47 business face still waits on CEO physical pieces (server / domain / filing+ICP / "
    "merchant id, plus the miniprogram appid+secret); (h) Docker is absent on this host; "
    "(i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for its "
    "S4U re-registration.",
    "R2795 tokens: local=~18k api=0 api_reason=one five-silence scan, one backlog head read "
    "for the carried debt, one template suite read to match the registry shape, one tool "
    "read for its gate entry points, the pin row written before any code, one suite file, "
    "one registry row, one suite run plus one matrix regeneration and check, one face-gate "
    "and one entry-page re-render with its 14-check gate, one evidence log through the "
    "birth-site writer, and the state/export closeout; zero cloud calls and zero external "
    "API touches",
]


def main():
    raw = state_io.read_raw(STATE)
    payload = state_io.parse(state_io.decode(raw))
    for row in ROWS:
        if row in payload["log"]:
            continue
        payload["log"].append(row)
    payload["tick"] = int(payload.get("tick", 0)) + 1
    result = state_io.write_document(STATE, payload)
    print("STATE tick=%d log=%d written=%dB" % (
        payload["tick"], len(payload["log"]), result["written"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
