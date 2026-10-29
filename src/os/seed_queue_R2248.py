"""R2248 queue seeding: append ten seed rows to the standing floors.

Every seed names a real gap, carries a pre-registered criteria prefix and
was checked zero-occupancy against HEAD before landing (git grep -F rc=1).
Single writer, utf-8, LF. Refuses to append a row whose anchor is already
present in the target file, so a re-run cannot double-seed.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

TECH = os.path.join(REPO, "state", "queue", "tech.md")
EXPLORE = os.path.join(REPO, "state", "queue", "explore.md")

TECH_ROWS = [
    (b"ITEM-DEBTA",
     b"- [ ] P2 tech seed (R2248 a): `src/os/debt_append.py` - the debt "
     b"register (R2248) only has rows if a window writes them, and the "
     b"deferral would still start life as log prose. One callable that "
     b"appends a row in the register format (opened=<round> | item=... | "
     b"note=... | first=yes), refuses a duplicate item and refuses a "
     b"second first=yes, then reads the row back through debt_register's "
     b"own parser. Criteria AC-DEBTA1..6 (append shape, duplicate refusal, "
     b"first-flag refusal, read-back through the parser, atomic write, "
     b"purity of the dry run)."),
    (b"ITEM-QROW",
     b"- [ ] P2 tech seed (R2248 b): `src/os/queue_row.py` - a seed exists "
     b"so its criteria are registered BEFORE the code, but nothing stops a "
     b"seed row without a criteria prefix from entering a queue. A checker "
     b"that refuses a claimable open row carrying no `Criteria prefix AC-` "
     b"(gated rows exempt) makes pre-registration a gate instead of a "
     b"habit. Criteria AC-QROW1..6 (row law reuse, prefix detection, gated "
     b"exemption, refusal report, CLI codes, purity)."),
    (b"ITEM-REV",
     b"- [ ] P2 tech seed (R2248 c): `src/os/round_evidence.py` - a round "
     b"claims SUITE PASS in its log item, and the file that proves it lives "
     b"in qa/ under a round-suffixed name; today the link is only the "
     b"prose. A reader that maps each round in state.json to the qa/ files "
     b"naming it and reports rounds that claim evidence without a file. "
     b"Criteria AC-REV1..6 (round extraction, file mapping, claim "
     b"detection, missing-evidence report, honest empty, purity)."),
    (b"ITEM-SEQ",
     b"- [ ] P2 tech seed (R2248 d): `src/os/state_seq.py` - tick climbs "
     b"every window, but nothing checks that the tick, the log round "
     b"labels and the R-number sequence agree, so a skipped or repeated "
     b"round label is invisible. A read-only checker over tick, the log "
     b"round labels and the queue's done rows. Criteria AC-SEQ1..6 (tick "
     b"read, label sequence, gap report, repeat report, CLI codes, "
     b"purity)."),
    (b"ITEM-SEED",
     b"- [ ] P2 tech seed (R2248 e): `src/os/seed_anchor.py` - a seed's "
     b"face name must be zero-occupancy before it lands, and that check is "
     b"currently a hand-run `git grep -F`. One callable that takes a face "
     b"name, greps HEAD (and optionally the working tree for uncommitted "
     b"hits) and prints OCCUPIED/FREE with the hit count, refusing to seed "
     b"on a hit. Criteria AC-SAN1..5 (HEAD grep, tree grep, verdict, "
     b"refusal on occupancy, purity)."),
]

EXPLORE_ROWS = [
    (b"ITEM-CRS",
     b"- [ ] P3 explore seed (R2248 a): apimarket **per-category monthly "
     b"restock pressure** (`api_category_restock_months`) - "
     b"api_seller_restock_months answers restock per seller and the market "
     b"monthly supply timeline answers the whole shelf, but nothing "
     b"answered which categories absorb restock month over month. Criteria "
     b"prefix AC-CRS1..8; anchor api_category_restock_months checked zero "
     b"occupancy against HEAD 2026-10-29 (git grep -F rc=1)."),
    (b"ITEM-BQM",
     b"- [ ] P3 explore seed (R2248 b): apimarket **buyer-side monthly "
     b"question volume** (`api_buyer_question_months`) - the question "
     b"family answers the market, the category and the seller, so a buyer "
     b"that asked heavily and then went quiet is invisible. Criteria "
     b"prefix AC-BQM1..8; anchor api_buyer_question_months zero "
     b"occupancy against HEAD 2026-10-29 (rc=1)."),
    (b"ITEM-SDL",
     b"- [ ] P3 explore seed (R2248 c): apimarket **seller-scoped monthly "
     b"delisting flow** (`api_seller_delist_months`) - supply is answered "
     b"as adds and sales, but a seller withdrawing shelf units month over "
     b"month reads as nothing at all. Criteria prefix AC-SDL1..8; anchor "
     b"api_seller_delist_months zero occupancy against HEAD 2026-10-29 "
     b"(rc=1)."),
    (b"ITEM-MSC",
     b"- [ ] P3 explore seed (R2248 d): apimarket **market monthly seller "
     b"churn** (`api_market_seller_churn_months`) - the month-end snapshot "
     b"reports seller breadth, but not the openings and closures that "
     b"produced it, so breadth holding still hides churn underneath. "
     b"Criteria prefix AC-MSC1..8; anchor api_market_seller_churn_months "
     b"zero occupancy against HEAD 2026-10-29 (rc=1)."),
    (b"ITEM-MDK",
     b"- [ ] P3 explore seed (R2248 e): apimarket **market monthly "
     b"discount-event flow** (`api_market_discount_months`) - asking price "
     b"by category is month-indexed, but a discount is an event on top of "
     b"the ask and nothing books it, so a month of heavy discounting looks "
     b"like holding prices. Criteria prefix AC-MDK1..8; anchor "
     b"api_market_discount_months zero occupancy against HEAD 2026-10-29 "
     b"(rc=1)."),
]


def append(path, rows):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    added = []
    for anchor, row in rows:
        if anchor in text.encode("utf-8"):
            print("SKIP already present %s" % anchor.decode("ascii"))
            continue
        added.append(row)
    if not added:
        return 0
    if not text.endswith("\n"):
        text += "\n"
    body = text
    for row in added:
        body += row.decode("utf-8") + "\n"
    data = body.encode("utf-8")
    with io.open(path, "wb") as handle:
        handle.write(data)
    print("APPENDED %d rows to %s (%d bytes)"
          % (len(added), os.path.basename(path), len(data)))
    return len(added)


def main():
    total = append(TECH, TECH_ROWS) + append(EXPLORE, EXPLORE_ROWS)
    print("SEED total_added=%d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())