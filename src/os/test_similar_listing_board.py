"""Battery suite for tools/similar_listing_board.py - criteria AC-SNB1..6.

WHY THIS SUITE EXISTS (measured at R3404, not assumed):
api_similar_listings has shipped with eight green criteria of its own
(test_apimarket_similar.py, AC-AMSI), but git grep -F over tools/ and preview/
found no reader at all, so the face that answers the buyer's most natural
follow-up after opening one listing could not be opened by anyone. R3404
renders it onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3404 PIN
BEFORE the driver existed, with one in-place correction recorded there: the
neighbour rows carry no category of their own, so bucket scope is graded
through api_listing_position on each neighbour):
  AC-SNB1  the page and its json land, and the json carries exactly the pinned
           payload key set including the sizes and sources blocks.
  AC-SNB2  the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates ids through the shipped api_board()
           face, reads api_similar_listings() for each id there, and requires
           the page json heads to equal those readings item for item, plus the
           board's own disclaimer verbatim - no typed fixture, no synthesized
           neighbour.
  AC-SNB3  the order is the face's own published total order: no head appears
           in its own neighbour list, every row's price_delta equals its price
           minus the head's, abs_price_delta is the absolute of that, the
           sequence is sorted by (abs delta, price, id) with no repeat, and
           returned/total/truncated agree with the rows.
  AC-SNB4  the face reads honestly: each neighbour's own bucket (read through
           api_listing_position) equals the head's category, an unrated
           neighbour prints the no-value mark instead of the 0.0 stand-in,
           live status is printed per row, and the page carries exactly one
           section per head and one data row per neighbour.
  AC-SNB5  the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-SNB6  no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py, and the shipped face's own suite is
           still on disk with its AC-AMSI criteria.

Read-only over the repository: the provenance world is built in a temp dir and
every re-render writes into a temp dir, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "similar_listing_board.py")
HTML = os.path.join(ROOT, "preview", "similar-listing-board.html")
JSONF = os.path.join(ROOT, "preview", "similar-listing-board.json")
COPY = os.path.join(ROOT, "preview", "similar-listing-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_similar.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "listing_count", "pair_count",
    "heads", "disclaimer", "report", "sources", "sizes",
}
ENV_KEYS = ("listing_id", "category", "live", "delisted_utc", "current_price",
            "include_delisted", "limit", "total", "returned", "truncated",
            "rows")
ROW_KEYS = {"listing_id", "dev_account", "listing_key", "title",
            "current_price", "price_delta", "abs_price_delta", "rating_count",
            "rating_avg", "net_sales", "live", "delisted_utc"}

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def stamp(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def run_tool(args, cwd=ROOT):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def board_reading():
    """Enumerate ids from the shipped board, then their neighbours, in our world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="snb-suite-")
    db = os.path.join(tmp_root, "snb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        heads = []
        buckets = {}
        for row in board["listings"]:
            listing_id = int(row["listing_id"])
            head = dict(am.api_similar_listings(listing_id))
            head["title"] = row["title"]
            heads.append(head)
            for rival in head["rows"]:
                neighbour = int(rival["listing_id"])
                buckets[neighbour] = am.api_listing_position(neighbour)[
                    "category"]
        return heads, board["disclaimer"], buckets
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    heads = doc.get("heads") or []

    # ---- AC-SNB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    head_keys_ok = all(
        all(key in head for key in ENV_KEYS) and "title" in head
        for head in heads) if heads else False
    ok("AC-SNB1", landed and keys == PAYLOAD_KEYS and head_keys_ok,
       "landed=%s keys=%d missing=%s extra=%s head_keys=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), head_keys_ok))

    # ---- AC-SNB2: every printed number is the shipped face's own.
    readings, disclaimer, buckets = board_reading()
    same_len = len(heads) == len(readings)
    diffs = []
    if same_len:
        for landed_head, live_head in zip(heads, readings):
            for key in ENV_KEYS + ("title",):
                if landed_head.get(key) != live_head.get(key):
                    diffs.append((landed_head.get("listing_id"), key))
    disc_same = doc.get("disclaimer") == disclaimer
    ok("AC-SNB2", same_len and not diffs and disc_same,
       "heads=%d/%d diffs=%s disclaimer_same=%s"
       % (len(heads), len(readings), diffs[:3], disc_same))

    # ---- AC-SNB3: the face's published total order holds on the page.
    order_problems = []
    for head in heads:
        head_id = int(head["listing_id"])
        head_price = int(head["current_price"])
        rows = head["rows"]
        if int(head["returned"]) != len(rows):
            order_problems.append("%s returned" % head_id)
        if int(head["total"]) < int(head["returned"]):
            order_problems.append("%s total<returned" % head_id)
        if bool(head["truncated"]) != (int(head["returned"])
                                       < int(head["total"])):
            order_problems.append("%s truncated" % head_id)
        seq = []
        for rival in rows:
            if int(rival["listing_id"]) == head_id:
                order_problems.append("%s self" % head_id)
            delta = int(rival["current_price"]) - head_price
            if int(rival["price_delta"]) != delta:
                order_problems.append("%s delta" % rival["listing_id"])
            if int(rival["abs_price_delta"]) != abs(delta):
                order_problems.append("%s abs" % rival["listing_id"])
            seq.append((abs(int(rival["price_delta"])),
                        int(rival["current_price"]),
                        int(rival["listing_id"])))
        if seq != sorted(seq) or len(seq) != len(set(seq)):
            order_problems.append("%s order" % head_id)
    ok("AC-SNB3", not order_problems, "problems=%s" % order_problems[:3])

    # ---- AC-SNB4: bucket scope through the shipped position face, no 0.0.
    scope_problems = []
    for head in heads:
        for rival in head["rows"]:
            neighbour = int(rival["listing_id"])
            if buckets.get(neighbour) != head["category"]:
                scope_problems.append("%s->%s" % (head["listing_id"],
                                                  neighbour))
    unrated = [rival for head in heads for rival in head["rows"]
               if int(rival.get("rating_count") or 0) == 0]
    stand_in = ">0.0<" in page
    mark = ">%s<" % labels.get("none", "-")
    sections = page.count("<h3>")
    data_rows = page.count("<tr><td>")
    pairs = sum(len(head["rows"]) for head in heads)
    live_marks = (page.count(labels.get("live_yes", ""))
                  if labels.get("live_yes") else 0)
    ok("AC-SNB4", not scope_problems and not stand_in
       and (not unrated or mark in page) and sections == len(heads)
       and data_rows == pairs and live_marks >= pairs,
       "scope_problems=%s unrated=%d stand_in_0.0=%s mark=%s sections=%d/%d"
       " data_rows=%d/%d live_marks=%d"
       % (scope_problems[:3], len(unrated), stand_in, mark in page, sections,
          len(heads), data_rows, pairs, live_marks))

    # ---- AC-SNB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-SNB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-SNB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    wired = "similar_listing_board" in read(REGISTRY)
    face_ok = (os.path.exists(FACE_SUITE) and "AC-AMSI" in read(FACE_SUITE))
    ok("AC-SNB6", rc == 0 and "PASS" in out and before == after and wired
       and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%s face_suite=%s"
       % (rc, before == after, wired, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
