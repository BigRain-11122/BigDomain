# heartbeat_and_backlog_R2368.py - append the round heartbeat line and the
# backlog top row, both with read-back proof.
import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

LINE = (
    "R2368 (tick 2368): verification then product - the carried battery ran "
    "first on the committed dffdd007 tree and read RUNNER PASS 494/494 suites "
    "plus controls 7/7 in 914.6s with criteria total 3940 EXACTLY as "
    "pre-registered, TMP RECLAIM 932/932 worlds 326.59 MiB; four follow-up "
    "sections PASS after the designed matrix FAIL and its regeneration to "
    "494/3940 (47273B), committed alone as cee549f7 before any product byte "
    "changed. Then the row the reader named: state/queue/tech.md:413 AC-QFR1 "
    "queue_floor_reading_wire shipped, criteria pinned in that row at R2365 "
    "BEFORE the code and all five anchors zero-occupancy at HEAD. The wire "
    "publishes ONE floor reading whose claimable IS the discounted number with "
    "the discount count and the discounted rows (line+prefix) beside it, so "
    "gross reconciles; the report is queue_floor_delivered_wire.gauge itself "
    "and every row law stays with queue_floor, so a queue with nothing "
    "delivered publishes queue_floor's row byte for byte on every shared key; "
    "pure read, no clock, no writes, no network. SUITE PASS 6/6 twice "
    "identical plus four adjacent suites green "
    "(qa/queue-floor-reading-wire-R2368.log, 1723B), wired "
    "os-queue-floor-reading-wire(6). LIVE: published tech=9/10-1 FLOOR-DEBT "
    "with the discounted row named as line 413 AC-QFR1 itself, while "
    "queue_floor alone still read tech=10/10 FLOOR-MET on the same tree at the "
    "same instant - the undiscounted answer was the published one, which is "
    "the defect the seed described. Row 413 stamped and one REAL measured gap "
    "row seeded (queue_floor_export_face, AC-QFE1..6, from the measurement "
    "that git grep -F for claimable/floor/FLOOR over docs/status-export.json "
    "and check_export_consistency.py returns ZERO hits), gauge FLOOR-MET "
    "5/5 10/10 10/10, debt register closed reconcile-battery-R2367 and opened "
    "reconcile-battery-R2368 at 495 suites / 3946 criteria. Disclosed: the "
    "first battery invocation was piped through a filtering selector and died "
    "to the five-minute no-output rule with zero survivors and zero evidence "
    "before the direct-stream rerun. Two product points."
)

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2368] verification-then-product-R2368: the "
    "carried battery ran first on the committed dffdd007 tree with an empty "
    "git status and read RUNNER PASS 494/494 suites green plus controls 7/7 "
    "in 914.6s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB "
    "busy=0 failed=0 (qa/reconcile-all-R2368.log, 802737B, single writer "
    "utf-8 LF through src/os/battery_stream.py) and criteria total 3940 "
    "EXACTLY as pre-registered, so the prediction matched the measurement "
    "with nothing to name; the four follow-up sections ran through "
    "src/os/battery_followup.py, the matrix section FAILED first on the stale "
    "doc and did NOT rewrite it (on-disk=47070B regenerated=47273B), "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md to "
    "494 suites / 3940 criteria and the re-run read all four PASS for VERDICT "
    "R2368 PASS; evidence and matrix committed alone as cee549f7 before any "
    "product byte changed (the R2168 mixed-tree rule). PRODUCT: claimed "
    "state/queue/tech.md:413 prefix AC-QFR1 (queue_floor_reading_wire), whose "
    "AC-QFR1..AC-QFR6 were pinned inside that row at R2365 BEFORE any code, "
    "after a fresh zero-occupancy anchor check at HEAD (all five anchors hit "
    "only prose and state files). SHIPPED src/os/"
    "queue_floor_reading_wire.py plus "
    "src/os/test_queue_floor_reading_wire.py: ONE published floor reading "
    "whose claimable IS the discounted number, with the discount count and "
    "the discounted rows (line+prefix, exactly as queue_occupancy reported "
    "them) travelling beside it so gross reconciles as claimable + "
    "discounted; the report is queue_floor_delivered_wire.gauge itself "
    "(AC-QFR1 proven by patching that gauge and watching the published number "
    "move) and every row law, count, floor and status stays with queue_floor, "
    "so a queue with nothing delivered publishes queue_floor's row byte for "
    "byte on every shared key; pure read of a root, no write, no clock, no "
    "network. SUITE PASS 6/6 twice with an identical criterion digest plus "
    "four adjacent suites green (qa/queue-floor-reading-wire-R2368.log, "
    "1723B, legs=2 identical=True adjacent=4 fails=0), wired "
    "os-queue-floor-reading-wire(6). LIVE, not a plan: published "
    "main=5/5 tech=9/10-1 explore=10/10 FLOOR-DEBT shortfall=1 delivered=1 "
    "with the discounted row named as line 413 AC-QFR1, while queue_floor "
    "--check on the same tree at the same instant still read tech=10/10 "
    "FLOOR-MET (qa/queue-floor-reading-wire-live-R2368.log, 1134B, single "
    "utf-8 LF writer). Row stamped and one REAL measured gap row seeded "
    "(queue_floor_export_face, AC-QFE1..AC-QFE6 pre-registered, five anchors "
    "zero-occupancy) because the CEO-visible export publishes no queue line "
    "at all; gauge FLOOR-MET main 5/5 tech 10/10 explore 10/10; debt register "
    "closed reconcile-battery-R2367 (open 3->2, done 96->97, readback ok) and "
    "opened reconcile-battery-R2368 first=yes at 495 suites / 3946 criteria. "
    "Disclosed: the first battery invocation was piped through a filtering "
    "selector and cancelled by the five-minute no-output rule (zero "
    "survivors, zero evidence, clean tree before the rerun); AC-QFR2's first "
    "red was this window own fixture asserting a hand-written prefix while "
    "queue_occupancy legitimately reports the whole token, so the assertion "
    "now compares against queue_occupancy's own reported list and no "
    "criterion was widened; tasks.md untouched because it is the P-47 board "
    "and carries no row for this tech slice. Two product points.\n"
)


def append_line(path, line):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    text += line + "\n"
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    return back.rstrip("\n").split("\n")[-1]


def prepend_row(path, row):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    text = row + text
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    first = back.split("\n")[0]
    return first.startswith("- [x] [done 2026-11-02 R2368]")


def main():
    last = append_line(HEARTBEAT, LINE)
    has_tick = "tick 2368" in last
    ok_backlog = prepend_row(BACKLOG, BACKLOG_ROW)
    print("HEARTBEAT ok=%s bytes=%d" % (has_tick, os.path.getsize(HEARTBEAT)))
    print("BACKLOG ok=%s bytes=%d" % (ok_backlog, os.path.getsize(BACKLOG)))
    return 0 if (has_tick and ok_backlog) else 2


if __name__ == "__main__":
    raise SystemExit(main())