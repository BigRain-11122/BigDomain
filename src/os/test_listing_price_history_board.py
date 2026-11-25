"""Battery suite for tools/listing_price_history_board.py - AC-LPHB1..6.

WHY THIS SUITE EXISTS (measured at R3482, not assumed):
api_price_history shipped one listing's asking-price history - base price,
every append-only revision in order, the current price and the revision count -
but a search over tools/, preview/ and src/os answered zero readers for its
name, so a shelf's whole repricing trail could only be read from a shell.
R3482 renders the shipped envelopes on one page; this suite grades the page,
not the face.

WHAT IS PROVED HERE (criteria fixed in the R3482 backlog PIN row before the
first render):
  AC-LPHB1 the chain replays: revision_count equals the row count, replaying
          from the base price reaches the current price, and a quiet shelf's
          current price equals its base price.
  AC-LPHB2 the order law: revision ids strictly ascending, revised_utc never
          backwards, every step positive and never a no-op repeat.
  AC-LPHB3 the direction law: up plus down equals the revision count, the
          largest step is taken by absolute difference, the peak month takes
          the earliest on a tie and the busiest shelf takes the lowest id.
  AC-LPHB4 the page reads honestly: the quiet shelf prints the named sentence
          and draws no table, and every other card's rows equal its count.
  AC-LPHB5 the driver is ASCII, bare-LF, BOM-free, the label copy is complete
          and the suite is registered with its declared count.
  AC-LPHB6 the landed pair answers its own --check, --check writes nothing,
          and the face is still exercised by its shipped suite on disk.

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
TOOL = os.path.join(ROOT, "tools", "listing_price_history_board.py")
HTML = os.path.join(ROOT, "preview", "listing-price-history-board.html")
JSONF = os.path.join(ROOT, "preview", "listing-price-history-board.json")
COPY = os.path.join(ROOT, "preview", "listing-price-history-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_pricerev.py")

ROW = "os-listing-price-history-board"
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

    # ---- AC-LPHB1 the chain replays ---------------------------------------
    replay_bad = []
    for item in listings:
        rights = item.get("revisions") or []
        if int(item["revision_count"]) != len(rights):
            replay_bad.append("%s count" % item["listing_id"])
        price = int(item["base_price"])
        for rev in rights:
            price = int(rev["token_price"])
        if price != int(item["current_price"]):
            replay_bad.append("%s replay %d != %r"
                              % (item["listing_id"], price,
                                 item["current_price"]))
        if not rights and int(item["current_price"]) != int(
                item["base_price"]):
            replay_bad.append("%s quiet" % item["listing_id"])
    ok("AC-LPHB1", not replay_bad and len(listings) == 3,
       "listings=%d bad=%r" % (len(listings), replay_bad))

    # ---- AC-LPHB2 the order law -------------------------------------------
    order_bad = []
    for item in listings:
        previous = int(item["base_price"])
        last_id = None
        last_utc = None
        for rev in item.get("revisions") or []:
            price = int(rev["token_price"])
            if price <= 0 or price == previous:
                order_bad.append("%s %r price" % (item["listing_id"],
                                                  rev["revision_id"]))
            if last_id is not None and int(rev["revision_id"]) <= last_id:
                order_bad.append("%s ids" % item["listing_id"])
            if last_utc is not None and str(rev["revised_utc"]) < last_utc:
                order_bad.append("%s time" % item["listing_id"])
            last_id = int(rev["revision_id"])
            last_utc = str(rev["revised_utc"])
            previous = price
    ok("AC-LPHB2", not order_bad, "bad=%r" % (order_bad,))

    # ---- AC-LPHB3 the direction law ---------------------------------------
    up = down = total = 0
    best = None
    months = {}
    busiest = (None, 0)
    for item in sorted(listings, key=lambda x: int(x["listing_id"])):
        previous = int(item["base_price"])
        for rev in item.get("revisions") or []:
            price = int(rev["token_price"])
            delta = price - previous
            total += 1
            if delta > 0:
                up += 1
            elif delta < 0:
                down += 1
            if best is None or abs(delta) > abs(best):
                best = delta
            key = str(rev["revised_utc"])[:7]
            months[key] = months.get(key, 0) + 1
            previous = price
        count = len(item.get("revisions") or [])
        if count > busiest[1]:
            busiest = (int(item["listing_id"]), count)
    peak_m = peak_c = None
    for key in sorted(months):
        if peak_c is None or months[key] > peak_c:
            peak_m, peak_c = key, months[key]
    good = (market.get("up_count") == up and market.get("down_count") == down
            and market.get("revision_count") == total
            and up + down == total
            and market.get("max_step_delta") == best
            and market.get("peak_month") == peak_m
            and market.get("busiest_listing") == busiest[0]
            and market.get("busiest_revisions") == busiest[1])
    ok("AC-LPHB3", good,
       "up=%d down=%d total=%d best=%r peak=%r busiest=%r market=%r"
       % (up, down, total, best, peak_m, busiest[0],
          [market.get("up_count"), market.get("down_count"),
           market.get("revision_count"), market.get("max_step_delta"),
           market.get("peak_month"), market.get("busiest_listing")]))

    # ---- AC-LPHB4 the page reads honestly ---------------------------------
    cards = {}
    for chunk in doc.split('<div class=card data-listing="')[1:]:
        lid, _, rest = chunk.partition('">')
        cards[lid] = rest.split('<div class=card data-listing="')[0]
    quiet_ok = 0
    rows_ok = 0
    for item in listings:
        lid = str(item["listing_id"])
        block = cards.get(lid) or ""
        count = len(item.get("revisions") or [])
        drawn = block.count("<tr>") - 1 if "<tr>" in block else 0
        if count == 0:
            if labels["empty"] in block and "<table>" not in block:
                quiet_ok += 1
        elif drawn == count:
            rows_ok += 1
    quiet_shelves = sum(1 for item in listings
                        if not item.get("revisions"))
    ok("AC-LPHB4",
       quiet_ok == quiet_shelves and rows_ok == len(listings) - quiet_shelves
       and quiet_shelves >= 1,
       "cards=%d quiet_shelves=%d quiet_ok=%d rows_ok=%d"
       % (len(cards), quiet_shelves, quiet_ok, rows_ok))

    # ---- AC-LPHB5 the driver and the registry -----------------------------
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
    face_suite = os.path.exists(FACE_SUITE)
    face_ac = "AC-AMPR" in read(FACE_SUITE) if face_suite else False
    ok("AC-LPHB5",
       ascii_ok and bare_lf and no_bom and copy_ok and registered
       and declared and face_suite and face_ac,
       "ascii=%r bare_lf=%r no_bom=%r copy=%r registered=%r declared=%r "
       "face_suite=%r" % (ascii_ok, bare_lf, no_bom, copy_ok, registered,
                          declared, face_suite))

    # ---- AC-LPHB6 the landed pair and no relaxed read ---------------------
    before = (stamp(HTML), stamp(JSONF), stamp(COPY))
    proc = subprocess.run([sys.executable, TOOL, "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    after = (stamp(HTML), stamp(JSONF), stamp(COPY))
    ok("AC-LPHB6",
       proc.returncode == 0 and "CHECK PASS" in proc.stdout
       and before == after,
       "readonly=%r rc=%d out=%r"
       % (before == after, proc.returncode,
          (proc.stdout or "").strip().splitlines()[:1]))

    print("SUITE %s %d/%d declared=%d row=%s"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED, ROW))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
