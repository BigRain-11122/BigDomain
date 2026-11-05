"""export_R2477 - refresh docs/status-export.json for the R2477 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2477 BUSINESS window: one command now brings the whole sandbox up "
           "- python src/sandbox/start_all.py starts all six faces on "
           "OS-assigned ports, proves each socket really accepts and that the "
           "hub's own probe map reads it live, prints the single door URL, "
           "and takes the whole thing down cleanly; proved twice 6/6 plus a "
           "live run where all six faces answered 200")

base.LATEST = ("src/sandbox/start_all.py (one-command launcher, pure ASCII, "
               "stdlib only, no shell) + src/sandbox/test_start_all.py "
               "(AC-STL1..AC-STL6) + qa/start-all-R2477-leg1.log & leg2.log "
               "(SUITE PASS 6/6 twice, identical verdict bodies) + "
               "qa/start-all-live-R2477.log (hub page 200 at 7104B, zero "
               "external references, six faces 200, launcher_exit=0, "
               "ports_still_open_after_stop=0)")

base.NEXT = ("2026-11-06 the next window owes the reconcile battery first "
             "(reconcile-battery-R2477, pre-registered 566 suites / 4372 "
             "criteria) on the committed tree before any product byte; after "
             "that the named business increment stays the half of the R2475 "
             "candidate this window did not reach - letting the hub page "
             "START a face from the browser instead of only from a terminal")

base.RESULT = (
    "2026-11-05 R2477 BUSINESS window delivered (CEO standing order "
    "OB-20261105-003656-879, real output only; it supersedes the carried "
    "audit row product-face-R2456 by name, which stays open and claimable). "
    "Five-silence scan at open was clean at HEAD 92e5e494 with an empty git "
    "status and no index.lock, zero unreplied @BigDomain ledger rows, the "
    "content-addressed decisions diff naming ZERO new tokens against the "
    "baseline, the group orders tail unchanged at 2026-11-05 20:22, benchmarks "
    "refreshed 2026-11-03 inside the seven-day gate, and tech head AC-PFKC1 "
    "with claimable=11 so no idle declaration was available. SHIPPED a launcher "
    "that closes the last step the hub could not: the hub is read-only, so "
    "every card it publishes ended in 'start this yourself', and a person "
    "needed five commands for six faces. start_all.py picks OS-assigned ports "
    "for eight sockets, starts the four shipped entry modules unchanged via "
    "argument vectors led by sys.executable (no shell, CREATE_NO_WINDOW so no "
    "console flashes), waits until every socket accepts, then asks the hub's "
    "own probe map what it publishes, so the URL printed is the hub's answer "
    "rather than a literal. Modes: serve (until a stop file appears) and "
    "--check (start, prove, tear down, report, exit). AC-STL1..AC-STL6 were "
    "pinned in src/os/backlog.md BEFORE the module, suite or registry row "
    "existed and read SUITE PASS 6/6 twice with identical verdict bodies; the "
    "live leg read hub 200 at 7104B with zero external references and all six "
    "faces 200 through the published URLs (checkout 8051B, city 6653B, gate "
    "7157B, ledger 7977B, lobby 10077B, ugc 8816B), launcher_exit=0 and "
    "ports_still_open_after_stop=0. Two real defects were found by running and "
    "repaired at their birth sites rather than by loosening a criterion: the "
    "suite read a report left by the previous leg before this run rewrote it, "
    "and a face name was used as a plan key (lobby's socket is planned as web, "
    "now published as face_ports through FACE_PORT_KEY). Registry moved 565 -> "
    "566 suites and 4366 -> 4372 criteria; the matrix was regenerated "
    "stamp-aligned to 54461B with --check byte-identical and its green line "
    "honestly reading 565/566; reconcile-battery-R2477 was appended first=no "
    "at its predicted 123180B -> 123363B with readback ok. Honest: half of the "
    "named candidate is met (a terminal command brings everything up) and half "
    "is not (the page still cannot start a face from the browser) and that is "
    "stated as half met; Docker is absent so a containerised bring-up stays "
    "unproved; the real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items; tasks.md was not touched."
)

base.OUTS = (
    "src/sandbox/start_all.py + src/sandbox/test_start_all.py + "
    "src/sandbox/reconcile_all.py + qa/start-all-R2477-leg1.log + "
    "qa/start-all-R2477-leg2.log + qa/start-all-live-R2477.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/state.json + "
    "src/os/backlog.md + src/os/state_append_R2477.py + src/os/export_R2477.py "
    "+ docs/status-export.json + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())