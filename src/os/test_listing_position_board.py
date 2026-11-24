"""Battery suite for tools/listing_position_board.py - criteria AC-LPB1..6.

WHY THIS SUITE EXISTS (measured at R3403, not assumed):
api_listing_position has shipped with eight green criteria of its own
(test_apimarket_listingposition.py, AC-AMPOS), but git grep -F over tools/
and preview/ found no reader at all - one docstring sentence in
market_price_percentiles.py mentions the name and reads nothing - so the face
that answers "where do I stand inside my own category" could not be opened by
anyone. R3403 renders it onto one page; this suite grades the page, not the
face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3403 PIN
BEFORE the driver existed, with one in-place correction recorded there: the
face's rivals slice is the WHOLE bucket including the head, not the others):
  AC-LPB1  the page and its json land, and the json carries exactly the pinned
           payload key set including the sizes and sources blocks.
  AC-LPB2  the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates listing ids through the shipped
           api_board() face, reads api_listing_position() for each id there,
           and requires the page json rows to equal those readings item for
           item, plus the board's own disclaimer verbatim - no typed fixture,
           no synthesized rank.
  AC-LPB3  the ranks are positions, not dense ranks: each axis reads exactly
           1..category_size with no repeat, cheaper + pricier == size - 1, and
           the published slice holds `size` rows of which exactly one is the
           head itself.
  AC-LPB4  the bucket face is honest: live + retired == size, the printed band
           equals the extremes of the published slice prices, every listing
           gets its own row on the page, and an unrated listing prints the
           no-value mark instead of the envelope's 0.0 stand-in.
  AC-LPB5  the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-LPB6  no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py, and the shipped face's own suite is
           still on disk with its AC-AMPOS criteria.

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
TOOL = os.path.join(ROOT, "tools", "listing_position_board.py")
HTML = os.path.join(ROOT, "preview", "listing-position-board.html")
JSONF = os.path.join(ROOT, "preview", "listing-position-board.json")
COPY = os.path.join(ROOT, "preview", "listing-position-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_listingposition.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "listing_count", "bucket_count",
    "buckets", "disclaimer", "report", "sources", "sizes",
}
BUCKET_KEYS = {
    "category", "category_size", "category_live_count",
    "category_retired_count", "category_min_price", "category_max_price",
    "rows",
}
AXES = (("current_price", "price_rank"), ("net_sales", "sales_rank"),
        ("rating_avg", "rating_rank"))

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
    """Enumerate ids from the shipped board, then rank each one, in our world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="lpb-suite-")
    db = os.path.join(tmp_root, "lpb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = am.api_board()
        rows = [am.api_listing_position(row["listing_id"])
                for row in board["listings"]]
        return rows, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def num(value):
    if value is None:
        return "-"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    buckets = doc.get("buckets") or []

    # ---- AC-LPB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    bucket_keys_ok = all(set(bucket.keys()) == BUCKET_KEYS
                         for bucket in buckets)
    ok("AC-LPB1", landed and keys == PAYLOAD_KEYS and bucket_keys_ok,
       "landed=%s keys=%d missing=%s extra=%s bucket_keys=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), bucket_keys_ok))

    # ---- AC-LPB2: every printed number is the shipped face's own.
    rows, disclaimer = board_reading()
    landed_rows = [row for bucket in buckets for row in bucket["rows"]]
    same_len = len(landed_rows) == len(rows)
    diffs = []
    if same_len:
        for left, right in zip(landed_rows, rows):
            if left != right:
                diffs.append((left.get("listing_id"), right.get("listing_id")))
    disc_same = doc.get("disclaimer") == disclaimer
    ok("AC-LPB2", same_len and not diffs and disc_same,
       "rows=%d/%d diffs=%s disclaimer_same=%s"
       % (len(landed_rows), len(rows), diffs[:3], disc_same))

    # ---- AC-LPB3: positions in a total order over the whole bucket.
    rank_problems = []
    for bucket in buckets:
        size = int(bucket["category_size"])
        bucket_rows = bucket["rows"]
        for value_key, rank_key in AXES:
            ranks = sorted(int(r[rank_key]) for r in bucket_rows)
            if ranks != list(range(1, size + 1)):
                rank_problems.append("%s ranks=%r size=%d"
                                     % (rank_key, ranks, size))
        for row in bucket_rows:
            if (int(row["cheaper_count"]) + int(row["pricier_count"])
                    != size - 1):
                rank_problems.append("%s cheaper+pricier" % row["listing_id"])
            if len(row["rivals"]) != size:
                rank_problems.append("%s slice=%d"
                                     % (row["listing_id"], len(row["rivals"])))
            heads = [rival for rival in row["rivals"]
                     if int(rival["listing_id"]) == int(row["listing_id"])]
            if len(heads) != 1:
                rank_problems.append("%s heads=%d"
                                     % (row["listing_id"], len(heads)))
    ok("AC-LPB3", not rank_problems, "problems=%s" % rank_problems[:3])

    # ---- AC-LPB4: the bucket face is honest, and no 0.0 stand-in is printed.
    bucket_problems = []
    printed_missing = []
    for bucket in buckets:
        size = int(bucket["category_size"])
        live = int(bucket["category_live_count"])
        retired = int(bucket["category_retired_count"])
        if live + retired != size:
            bucket_problems.append("live+retired=%d size=%d" % (live + retired,
                                                               size))
        prices = [int(rival["current_price"])
                  for rival in bucket["rows"][0]["rivals"]]
        if bucket["category_min_price"] != min(prices):
            bucket_problems.append("min=%s slice_min=%d"
                                   % (bucket["category_min_price"],
                                      min(prices)))
        if bucket["category_max_price"] != max(prices):
            bucket_problems.append("max=%s slice_max=%d"
                                   % (bucket["category_max_price"],
                                      max(prices)))
        for row in bucket["rows"]:
            cell = "%s &middot; %s" % (row["listing_id"], row["title"])
            if cell not in page:
                printed_missing.append(row["listing_id"])
    unrated = [row for row in landed_rows
               if int(row.get("rating_count") or 0) == 0]
    stand_in = ">0.0<" in page
    has_mark = ">%s<" % labels.get("none", "-") in page
    ok("AC-LPB4", not bucket_problems and not printed_missing
       and not stand_in and (not unrated or has_mark),
       "bucket_problems=%s printed_missing=%s unrated=%d stand_in_0.0=%s mark=%s"
       % (bucket_problems[:3], printed_missing[:3], len(unrated), stand_in,
          has_mark))

    # ---- AC-LPB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-LPB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-LPB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    wired = "listing_position_board" in read(REGISTRY)
    face_ok = (os.path.exists(FACE_SUITE) and "AC-AMPOS" in read(FACE_SUITE))
    ok("AC-LPB6", rc == 0 and "PASS" in out and before == after and wired
       and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%s face_suite=%s"
       % (rc, before == after, wired, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
