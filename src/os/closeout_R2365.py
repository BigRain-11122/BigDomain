"""R2365 state closeout: append this window's log entries and bump the tick.

Single writer: the file is read as bytes, the log items are inserted at the
canonical 16-space indent, CRLF is preserved, and the JSON payload is
re-parsed before the write so a broken splice can never land.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

ENTRIES = [
    "2026-11-02 R2365 product window (five- silence scan at open: empty git "
    "status --short at 88305647, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=112 tokens=74 new=0 so "
    "no decision row was owed, ORD max_ts=2026-11-01 with the 10:4x "
    "model-policy baseline already acknowledged as non-execution, BENCH "
    "refreshed=2026-11-01 inside the seven-day gate). THE DEBT GATE NAMED THIS "
    "WINDOW FACE AND NOT A BATTERY: CLAIM-FIRST item=product-face-R2365 "
    "opened=R2364 carried=1, with the queue head named at "
    "state/queue/tech.md:411 prefix AC-FDW1, whose AC-FDW1..AC-FDW6 were "
    "pinned INSIDE that row at R2354 BEFORE any code. The anchor check was "
    "re-run at HEAD and all five names were git grep -F zero-occupancy. "
    "SHIPPED src/os/queue_floor_delivered_wire.py plus "
    "src/os/test_queue_floor_delivered_wire.py.",
    "R2365 the wire asks queue_occupancy for the reading rather than scanning "
    "again - the suite patches queue_occupancy.audit_text and the gauge moves "
    "- and it discounts a DELIVERED open row from standing supply while every "
    "count queue_floor publishes stays byte-identical for the same file, "
    "because the discount is its own key (claimable stays gross, "
    "claimable_effective carries the reading). An all-delivered queue "
    "therefore reads FLOOR-DEBT with the shortfall equal to the whole floor "
    "and the discounted rows named by line and prefix, and a queue with no "
    "prefixed row reads exactly the queue_floor row. SUITE PASS 6/6 twice "
    "with an identical criterion digest through evidence_capture "
    "(qa/queue-floor-delivered-wire-R2365.log, 1552B, legs=2 identical=True) "
    "plus three adjacent suites green (queue-floor 8/8, queue-occupancy 6/6, "
    "queue-head-delivered 6/6), wired os-queue-floor-delivered-wire(6).",
    "R2365 live action, not a plan: the real queue was read at the instant the "
    "module and suite landed and the wire reported main=5/5 tech=8/10-1 "
    "explore=10/10 verdict=FLOOR-DEBT shortfall=2 delivered=1 with the "
    "discounted row named as line 411 prefix AC-FDW1 - i.e. the very defect "
    "the seed described, reproduced live - while queue_floor alone still read "
    "tech=9/10 at that same instant "
    "(qa/queue-floor-delivered-wire-live-R2365.log). The row was then stamped "
    "done (bracket payload 22 chars, well inside the queue_done_stamp 60-char "
    "law) and two REAL measured gaps were seeded: battery_followup_help_wire "
    "(AC-BFH1..6, from the R2364 measured --help contract divergence) and "
    "queue_floor_reading_wire (AC-QFR1..6, from this window own "
    "two-readers-two-answers reading). Tech claimable went 9 to 8 on the stamp "
    "and 8 to 10 on the two seeds, so the floor reads 10/10 with no filler "
    "row: both seeds name a gap measured in a round, not invented to make a "
    "number.",
    "R2365 tokens: local=~24k api=0 api_reason=product window - one product "
    "module and its six-criteria suite written to criteria pinned two rounds "
    "earlier, one evidence capture with two identical legs and three adjacent "
    "suites, one live reading that caught the defect it was built for, one "
    "queue row stamped, two measured gap rows seeded, one runner wiring line, "
    "and the state/export/backlog closeout; zero cloud calls and zero "
    "external API touches.",
    "R2365 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-first consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2365 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read new=0 over 112 "
    "rows and 74 tokens, and the evolution ledger carries no @BigDomain row, "
    "so nothing was executed, rejected or acknowledged this window and the "
    "baseline was left unchanged rather than widened without cause.",
    "R2365 honest disclosures: (a) NO reconcile battery ran and no battery row "
    "was opened, because the gate named the product face rather than a carried "
    "battery (open=3 first=1 item=product-face-R2365) and the test floor this "
    "window rises by exactly one suite / six criteria for the next battery to "
    "confirm - it must read 493 suites / 3934 criteria against the R2364 "
    "committed reading of 492/3928, and any larger delta must be named rather "
    "than swept. (b) The live capture was first written through a PowerShell "
    "redirect and landed as utf-16 with a BOM - exactly the R2362 census trap "
    "- so it was transcoded to utf-8 LF (900B to 444B, content identical, no "
    "baseline widened) and qa_writer_census then read flags=0 DRIFT-CLEAN; the "
    "incident is reported instead of overwritten. (c) The AC-FDW3 fixture "
    "initially counted a row delivered merely because its module and suite "
    "both existed in the world, which made it a second copy of AC-FDW2; it was "
    "rebuilt around an all-delivered queue so it tests the floor verdict, not "
    "the discount. (d) The suffix AC-QFW was already occupied by "
    "queue_only_floor_wire (R2269), so the second seed uses AC-QFR after a "
    "git grep -F check; no prefix was reused. (e) tasks.md was left untouched: "
    "it is the P-47 canonical board and carries no row for this tech slice, "
    "disclosed rather than silently skipped.",
]


def main():
    raw = open(PATH, "rb").read()
    text = raw.decode("utf-8")
    assert "\r\n" in text and text.count("\n") == text.count("\r\n")
    lines = text.split("\r\n")
    end = None
    for index in range(len(lines) - 1, -1, -1):
        if lines[index] == "  ]":
            end = index
            break
    assert end is not None and lines[end + 1] == "}"
    last = end - 1
    assert lines[last].rstrip().endswith('"'), repr(lines[last][-40:])
    lines[last] = lines[last] + ","
    new = []
    for entry in ENTRIES:
        new.append(" " * 16 + json.dumps(entry, ensure_ascii=False) + ",")
    new[-1] = new[-1][:-1]
    lines[end:end] = new
    out = "\r\n".join(lines)
    out = out.replace('"tick": 2364', '"tick": 2365', 1)
    data = json.loads(out)
    before = json.loads(text)
    assert data["tick"] == 2365
    assert len(data["log"]) == len(before["log"]) + len(ENTRIES)
    io.open(PATH, "w", encoding="utf-8", newline="").write(out)
    print("state tick", data["tick"], "log", len(data["log"]),
          "bytes", len(out.encode("utf-8")))


if __name__ == "__main__":
    main()