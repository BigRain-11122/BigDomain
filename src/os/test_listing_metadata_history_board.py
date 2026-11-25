"""Battery suite for tools/listing_metadata_history_board.py - AC-LMHB1..6.

WHY THIS SUITE EXISTS (measured at R3483, not assumed):
api_metadata_history shipped one listing's title/description trail - the
immutable base pair, every append-only revision in order, the current
effective pair and the revision count - but a search over tools/, preview/ and
src/os answered zero readers for its name, so a shelf's whole copy-repair trail
could only be read from a shell. R3483 renders the shipped envelopes on one
page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in the R3483 backlog PIN row before the
first render):
  AC-LMHB1 the chain replays: revision_count equals the step count, replaying
          from the base pair reaches the face's pair, a quiet shelf's pair
          equals its base pair, and every step is signed by the shelf owner.
  AC-LMHB2 the order law: revision ids strictly ascending, revised_utc never
          backwards, both fields non-blank, and no step repeats its pair.
  AC-LMHB3 the change law: title plus description moves equal every changed
          field, both_changes counts only two-field steps, the peak month takes
          the earliest tie, the busiest shelf takes the lowest id and the
          latest stamp is the maximum.
  AC-LMHB4 the page reads honestly: the unedited shelf prints the named
          sentence and draws no table, every other card's rows equal its count,
          and each card prints its base title and its current title.
  AC-LMHB5 the driver is ASCII, bare-LF, BOM-free, the label copy is complete,
          the suite is registered with its declared count and the edit door it
          exercises is still on disk.
  AC-LMHB6 the page agrees with its json (base title, current title, revision
          count, market totals) and the landed pair answers its own --check
          without writing.

Read-only over the repository: the driver builds its world in a temp dir, and
the suite only reads the landed pair.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "listing_metadata_history_board.py")
HTML = os.path.join(ROOT, "preview", "listing-metadata-history-board.html")
JSONF = os.path.join(ROOT, "preview", "listing-metadata-history-board.json")
COPY = os.path.join(ROOT, "preview", "listing-metadata-history-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
APIMARKET = os.path.join(ROOT, "src", "sandbox", "ledger", "apimarket.py")

ROW = "os-listing-metadata-history-board"
DECLARED = 6

CHECKS = []
FAILS = []


def ok(name, good, detail):
    CHECKS.append(name)
    if not good:
        FAILS.append(name)
    print("%-9s %s %s" % (name, "PASS" if good else "FAIL", detail))


def read(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def stamp(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    payload = json.loads(read(JSONF))
    doc = read(HTML)
    labels = json.loads(read(COPY))
    listings = payload.get("listings") or []
    market = payload.get("market") or {}

    # ---- AC-LMHB1 the chain replays ---------------------------------------
    replay_bad = []
    for item in listings:
        steps = item.get("steps") or []
        if int(item["revision_count"]) != len(steps):
            replay_bad.append("%s count" % item["listing_id"])
        pair = (item["base_title"], item["base_description"])
        for step in steps:
            pair = (step["title"], step["description"])
            if str(step["dev_account"]) != str(item.get("owner")):
                replay_bad.append("%s owner" % item["listing_id"])
        if pair != (item["title"], item["description"]):
            replay_bad.append("%s replay" % item["listing_id"])
        if not steps and pair != (item["base_title"],
                                  item["base_description"]):
            replay_bad.append("%s quiet" % item["listing_id"])
    ok("AC-LMHB1", not replay_bad and len(listings) == 3,
       "listings=%d bad=%r" % (len(listings), replay_bad))

    # ---- AC-LMHB2 the order law -------------------------------------------
    order_bad = []
    for item in listings:
        previous = (item["base_title"], item["base_description"])
        last_id = None
        last_utc = None
        for step in item.get("steps") or []:
            pair = (step["title"], step["description"])
            if not str(step["title"]).strip() or not str(
                    step["description"]).strip():
                order_bad.append("%s blank" % item["listing_id"])
            if pair == previous:
                order_bad.append("%s repeat" % item["listing_id"])
            if last_id is not None and int(step["revision_id"]) <= last_id:
                order_bad.append("%s ids" % item["listing_id"])
            if last_utc is not None and str(step["revised_utc"]) < last_utc:
                order_bad.append("%s time" % item["listing_id"])
            last_id = int(step["revision_id"])
            last_utc = str(step["revised_utc"])
            previous = pair
    ok("AC-LMHB2", not order_bad, "bad=%r" % (order_bad,))

    # ---- AC-LMHB3 the change law ------------------------------------------
    title_moves = desc_moves = both = total = 0
    months = {}
    latest = None
    busiest = (None, 0)
    field_bad = []
    for item in sorted(listings, key=lambda x: int(x["listing_id"])):
        previous = (item["base_title"], item["base_description"])
        for step in item.get("steps") or []:
            changed = step.get("changed") or []
            pair = (step["title"], step["description"])
            expect = []
            if pair[0] != previous[0]:
                expect.append("title")
            if pair[1] != previous[1]:
                expect.append("description")
            if changed != expect:
                field_bad.append("%s %r %r != %r"
                                 % (item["listing_id"],
                                    step["revision_id"], changed, expect))
            total += 1
            if "title" in changed:
                title_moves += 1
            if "description" in changed:
                desc_moves += 1
            if len(changed) == 2:
                both += 1
            key = str(step["revised_utc"])[:7]
            months[key] = months.get(key, 0) + 1
            if latest is None or str(step["revised_utc"]) > latest:
                latest = str(step["revised_utc"])
            previous = pair
        count = len(item.get("steps") or [])
        if count > busiest[1]:
            busiest = (int(item["listing_id"]), count)
    peak_m = peak_c = None
    for key in sorted(months):
        if peak_c is None or months[key] > peak_c:
            peak_m, peak_c = key, months[key]
    good = (not field_bad
            and market.get("title_changes") == title_moves
            and market.get("description_changes") == desc_moves
            and market.get("both_changes") == both
            and market.get("revision_count") == total
            and market.get("peak_month") == peak_m
            and market.get("peak_month_revisions") == peak_c
            and market.get("busiest_listing") == busiest[0]
            and market.get("busiest_revisions") == busiest[1]
            and market.get("latest_revision_utc") == latest
            and market.get("unrevisioned_count")
            == sum(1 for i in listings if not i.get("steps")))
    ok("AC-LMHB3", good,
       "title=%d desc=%d both=%d total=%d peak=%r busiest=%r bad=%r market=%r"
       % (title_moves, desc_moves, both, total, peak_m, busiest[0],
          field_bad,
          [market.get("title_changes"), market.get("description_changes"),
           market.get("both_changes"), market.get("revision_count"),
           market.get("peak_month"), market.get("busiest_listing")]))

    # ---- AC-LMHB4 the page reads honestly ---------------------------------
    cards = {}
    for chunk in doc.split('<div class=card data-listing="')[1:]:
        lid, _, rest = chunk.partition('">')
        cards[lid] = rest.split('<div class=card data-listing="')[0]
    quiet_ok = rows_ok = pair_ok = 0
    for item in listings:
        lid = str(item["listing_id"])
        block = cards.get(lid) or ""
        count = len(item.get("steps") or [])
        drawn = block.count("<tr>") - 1 if "<tr>" in block else 0
        if count == 0:
            if labels["empty"] in block and "<table>" not in block:
                quiet_ok += 1
        elif drawn == count:
            rows_ok += 1
        if str(item["base_title"]) in block and str(item["title"]) in block:
            pair_ok += 1
    quiet_shelves = sum(1 for item in listings if not item.get("steps"))
    ok("AC-LMHB4",
       quiet_ok == quiet_shelves and rows_ok == len(listings) - quiet_shelves
       and pair_ok == len(listings) and quiet_shelves >= 1,
       "cards=%d quiet=%d quiet_ok=%d rows_ok=%d pair_ok=%d"
       % (len(cards), quiet_shelves, quiet_ok, rows_ok, pair_ok))

    # ---- AC-LMHB5 the driver and the registry -----------------------------
    raw = open(TOOL, "rb").read()
    ascii_ok = all(byte < 128 for byte in raw)
    bare_lf = b"\r" not in raw
    no_bom = not raw.startswith(b"\xef\xbb\xbf")
    copy_ok = all(str(labels.get(key, "")).strip()
                  for key in json.loads(read(COPY)))
    registry = read(REGISTRY)
    registered = ('"%s"' % ROW) in registry
    row_block = registry.split('"%s"' % ROW, 1)[-1][:200]
    declared = (", %d)" % DECLARED) in row_block
    door = "def edit_listing" in read(APIMARKET)
    ok("AC-LMHB5",
       ascii_ok and bare_lf and no_bom and copy_ok and registered
       and declared and door,
       "ascii=%r bare_lf=%r no_bom=%r copy=%r registered=%r declared=%r "
       "door=%r" % (ascii_ok, bare_lf, no_bom, copy_ok, registered,
                    declared, door))

    # ---- AC-LMHB6 the page agrees with its json ---------------------------
    market_start = doc.find("<h2>" + labels["sec_market"] + "</h2>")
    market_end = doc.find("<h2>" + labels["sec_boards"] + "</h2>")
    market_block = (doc[market_start:market_end]
                    if market_start >= 0 and market_end > market_start else "")

    def kpi_value(block, label):
        marker = "<span>%s</span>" % label
        at = block.find(marker)
        if at < 0:
            return None
        head = block.rfind("<b>", 0, at)
        tail = block.rfind("</b>", 0, at)
        if head < 0 or tail < 0:
            return None
        return block[head + 3:tail]

    pair_bad = []
    for item in listings:
        block = cards.get(str(item["listing_id"])) or ""
        if kpi_value(block, labels["b_base"]) != str(item["base_title"]):
            pair_bad.append("%s base" % item["listing_id"])
        if kpi_value(block, labels["b_current"]) != str(item["title"]):
            pair_bad.append("%s current" % item["listing_id"])
        if kpi_value(block, labels["b_revisions"]) != str(
                item["revision_count"]):
            pair_bad.append("%s count" % item["listing_id"])
    market_ok = (str(market.get("revision_count")) in market_block
                 and str(market.get("listing_count")) in market_block
                 and str(market.get("title_changes")) in market_block
                 and str(market.get("description_changes")) in market_block)
    before = (stamp(HTML), stamp(JSONF), stamp(COPY))
    proc = subprocess.run([sys.executable, TOOL, "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    after = (stamp(HTML), stamp(JSONF), stamp(COPY))
    ok("AC-LMHB6",
       not pair_bad and market_ok and proc.returncode == 0
       and "CHECK PASS" in proc.stdout and before == after,
       "pair_bad=%r market=%r readonly=%r rc=%d"
       % (pair_bad, market_ok, before == after, proc.returncode))

    print("SUITE %s %d/%d declared=%d row=%s"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED, ROW))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
