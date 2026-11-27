#!/usr/bin/env python3
"""Render the category competitive-standing board into one browsable page.

Why this exists: api_listing_position shipped with its own AC-AMPOS criteria and
answers the seller's own question - "where do I stand against the people I am
actually competing with" - but git grep -F over tools/ and preview/ finds no
reader at all (one docstring sentence in market_price_percentiles.py mentions
the name and reads nothing), so the only way to get that answer was to call the
sandbox from a shell. api_categories describes what a bucket is made of,
api_category_demand asks whether it sells and api_market_price_percentiles
describes the market's asking prices; none of them ranks one listing inside its
own bucket on the three axes a buyer weighs.

Nothing here re-implements a market rule. The ids come from the shipped
api_board() face and every number on the page comes from the shipped
api_listing_position() face read over a fresh throwaway demo world seeded
through the shipped report helpers. The page prints the envelopes it is handed
and never recomputes a rank, a count or a price band; the only checks it runs
are the face's own published laws, and a broken law refuses the render instead
of printing a plausible page.

The real sandbox is never opened for writing.

Usage:
  python tools/listing_position_board.py
  python tools/listing_position_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-LPB1..AC-LPB6 are pre-registered in src/os/backlog.md (R3403 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/listing-position-board-copy.json and appear in the rendered document
only, never in this file.
"""
import argparse
import hashlib
import html
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
sys.path.insert(0, LEDGER_DIR)

import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "listing-position-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "listing-position-board.json")
COPY = os.path.join(ROOT, "preview", "listing-position-board-copy.json")

FACE = "api_listing_position"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-LPB1). A missing one is a contract break rather than
# a silent blank on the page.
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "listing_count", "bucket_count",
    "buckets", "disclaimer", "report", "sources", "sizes",
)

BUCKET_KEYS = (
    "category", "category_size", "category_live_count",
    "category_retired_count", "category_min_price", "category_max_price",
    "rows",
)

# The three axes a buyer weighs (AC-LPB3). Each carries the value it ranks and
# the position the face published for it.
AXES = (
    ("current_price", "price_rank"),
    ("net_sales", "sales_rank"),
    ("rating_avg", "rating_rank"),
)

RIVAL_KEYS = ("listing_id", "title", "current_price", "net_sales",
              "rating_count", "rating_avg", "live")

COPY_KEYS = (
    "title", "sub", "gen", "src", "kpi_listings", "kpi_buckets", "kpi_size",
    "kpi_live", "kpi_retired", "kpi_min", "kpi_max", "sec_board",
    "sec_rivals", "sec_law", "sec_disc", "sec_rep", "col_listing",
    "col_price", "col_pricerank", "col_sales", "col_salesrank",
    "col_rating", "col_ratingrank", "col_cheaper", "col_pricier",
    "col_rival", "col_netsales", "col_status", "cat_uncat", "live_yes",
    "live_no", "self_mark", "none", "aigc", "law_total", "law_span",
    "law_band", "law_unrated", "rivals_for", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:14px 0 6px;font-weight:600;color:var(--muted)}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 110px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face, a law, or the label copy refused."""

    code = "E_LPB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_LPB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_board():
    """Enumerate listing ids from the shipped board, then rank each one."""
    tmp_root = tempfile.mkdtemp(prefix="listing-position-board-")
    db = os.path.join(tmp_root, "listing-position-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        ids = [int(row["listing_id"]) for row in board["listings"]]
        envs = [getattr(am, FACE)(listing_id) for listing_id in ids]
        disclaimer = board["disclaimer"]
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    if not envs:
        raise FaceError("board enumerated zero listings")
    for env in envs:
        for key in ("listing_id", "current_price", "net_sales",
                    "rating_count", "rating_avg", "category", "category_size",
                    "category_live_count", "category_retired_count",
                    "category_min_price", "category_max_price", "rivals"):
            if key not in env:
                raise FaceError("position keys missing: %s" % key)
        if not isinstance(env["rivals"], list):
            raise FaceError("rivals is not a list on listing %s"
                            % env["listing_id"])
        for rival in env["rivals"]:
            miss = [k for k in RIVAL_KEYS if k not in rival]
            if miss:
                raise FaceError("rival keys missing: %s" % ",".join(miss))
    return envs, disclaimer


def buckets_of(envs):
    """Group the position envelopes by the bucket the face itself reports."""
    order = []
    groups = {}
    for env in envs:
        key = env["category"]
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(env)
    named = sorted([k for k in order if k is not None])
    ordered_keys = named + ([None] if None in groups else [])
    out = []
    for key in ordered_keys:
        rows = sorted(groups[key], key=lambda r: int(r["listing_id"]))
        first = rows[0]
        out.append({
            "category": key,
            "category_size": first["category_size"],
            "category_live_count": first["category_live_count"],
            "category_retired_count": first["category_retired_count"],
            "category_min_price": first["category_min_price"],
            "category_max_price": first["category_max_price"],
            "rows": rows,
        })
    return out


def check_laws(buckets):
    """AC-LPB3 / AC-LPB4 read at the source: refuse rather than print."""
    problems = []
    for bucket in buckets:
        rows = bucket["rows"]
        size = int(bucket["category_size"])
        live = int(bucket["category_live_count"])
        retired = int(bucket["category_retired_count"])
        label = bucket["category"]
        if live + retired != size:
            problems.append("bucket %r live+retired=%d size=%d"
                            % (label, live + retired, size))
        if len(rows) != size:
            problems.append("bucket %r rows=%d size=%d"
                            % (label, len(rows), size))
        # Ranks are positions in a total order over the whole bucket. The page
        # renders the ids the board handed it, so a bucket larger than the
        # board slice cannot be graded here and says so by name.
        for value_key, rank_key in AXES:
            ranks = sorted(int(row[rank_key]) for row in rows)
            if ranks != list(range(1, len(rows) + 1)):
                problems.append("bucket %r axis %s ranks=%r over %d rows"
                                % (label, rank_key, ranks, len(rows)))
        prices = [int(rival["current_price"]) for rival in rows[0]["rivals"]]
        band_lo = bucket["category_min_price"]
        band_hi = bucket["category_max_price"]
        if band_lo is not None and band_hi is not None:
            if int(band_lo) != min(prices):
                problems.append("bucket %r min %s != %d"
                                % (label, band_lo, min(prices)))
            if int(band_hi) != max(prices):
                problems.append("bucket %r max %s != %d"
                                % (label, band_hi, max(prices)))
        for row in rows:
            cheaper = int(row["cheaper_count"])
            pricier = int(row["pricier_count"])
            if cheaper + pricier != size - 1:
                problems.append("listing %s cheaper+pricier=%d size-1=%d"
                                % (row["listing_id"], cheaper + pricier,
                                   size - 1))
            # The face publishes the bucket slice itself, so the slice holds
            # the head and every other row exactly once.
            if len(row["rivals"]) != size:
                problems.append("listing %s rivals=%d size=%d"
                                % (row["listing_id"], len(row["rivals"]),
                                   size))
            heads = [rival for rival in row["rivals"]
                     if int(rival["listing_id"]) == int(row["listing_id"])]
            if len(heads) != 1:
                problems.append("listing %s appears %d times in its own slice"
                                % (row["listing_id"], len(heads)))
    return problems


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def rating_text(row, none_text):
    """An unrated listing prints the no-value mark, never the 0.0 stand-in."""
    if int(row.get("rating_count") or 0) == 0:
        return none_text
    return fmt(row.get("rating_avg"), none_text)


def cat_name(bucket, labels):
    if bucket["category"] is None:
        return labels["cat_uncat"]
    return str(bucket["category"])


def build_html(buckets, labels, now, disclaimer):
    e = html.escape
    none = labels["none"]
    total = sum(len(bucket["rows"]) for bucket in buckets)
    head = buckets[0] if buckets else {"category_size": 0,
                                       "category_live_count": 0,
                                       "category_retired_count": 0,
                                       "category_min_price": None,
                                       "category_max_price": None}
    kpi = [
        (labels["kpi_listings"], fmt(total, none)),
        (labels["kpi_buckets"], fmt(len(buckets), none)),
        (labels["kpi_size"], fmt(head["category_size"], none)),
        (labels["kpi_live"], fmt(head["category_live_count"], none)),
        (labels["kpi_retired"], fmt(head["category_retired_count"], none)),
        (labels["kpi_min"], fmt(head["category_min_price"], none)),
        (labels["kpi_max"], fmt(head["category_max_price"], none)),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                       for k, v in kpi)

    board_blocks = []
    rival_blocks = []
    for bucket in buckets:
        rows_html = []
        for row in bucket["rows"]:
            rows_html.append(
                '<tr><td>%s &middot; %s</td><td class=n>%s</td>'
                '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
                '<td class=n>%s</td><td class=n>%s</td>'
                '<td class=n>%s</td><td class=n>%s</td></tr>'
                % (e(str(row["listing_id"])), e(str(row["title"])),
                   e(fmt(row["current_price"], none)),
                   e(fmt(row["price_rank"], none)),
                   e(fmt(row["net_sales"], none)),
                   e(fmt(row["sales_rank"], none)),
                   e(rating_text(row, none)),
                   e(fmt(row["rating_rank"], none)) if
                   int(row.get("rating_count") or 0) else e(none),
                   e(fmt(row["cheaper_count"], none)),
                   e(fmt(row["pricier_count"], none))))
        board_blocks.append(
            "<h3>%s &middot; %s %s</h3><table><tr><th>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th></tr>%s</table>"
            % (e(cat_name(bucket, labels)), e(labels["kpi_size"]),
               e(fmt(bucket["category_size"], none)),
               e(labels["col_listing"]), e(labels["col_price"]),
               e(labels["col_pricerank"]), e(labels["col_sales"]),
               e(labels["col_salesrank"]), e(labels["col_rating"]),
               e(labels["col_ratingrank"]), e(labels["col_cheaper"]),
               e(labels["col_pricier"]), "".join(rows_html)))

        for row in bucket["rows"]:
            rival_rows = []
            for rival in row["rivals"]:
                is_head = int(rival["listing_id"]) == int(row["listing_id"])
                status = labels["live_yes"] if rival["live"] \
                    else labels["live_no"]
                if is_head:
                    status = "%s / %s" % (labels["self_mark"], status)
                rival_rows.append(
                    '<tr><td>%s &middot; %s</td><td class=n>%s</td>'
                    '<td class=n>%s</td><td class=n>%s</td>'
                    "<td class=n>%s</td></tr>"
                    % (e(str(rival["listing_id"])), e(str(rival["title"])),
                       e(fmt(rival["current_price"], none)),
                       e(fmt(rival["net_sales"], none)),
                       e(rating_text(rival, none)), e(status)))
            rival_blocks.append(
                "<h3>%s %s &middot; %s</h3><table><tr><th>%s</th>"
                "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
                "<th class=n>%s</th></tr>%s</table>"
                % (e(labels["rivals_for"]), e(str(row["listing_id"])),
                   e(str(row["title"])), e(labels["col_rival"]),
                   e(labels["col_price"]), e(labels["col_netsales"]),
                   e(labels["col_rating"]), e(labels["col_status"]),
                   "".join(rival_rows)))

    laws = [labels["law_total"], labels["law_span"], labels["law_band"],
            labels["law_unrated"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/listing_position_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_board"]), "".join(board_blocks),
           e(labels["sec_rivals"]), "".join(rival_blocks),
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    # The disclaimer is the face's own sentence, injected after assembly so its
    # text is never retyped here.
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer))


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def source_fingerprints():
    return {
        "driver": sha16(os.path.abspath(__file__)),
        "copy": sha16(COPY),
        "apimarket": sha16(os.path.join(LEDGER_DIR, "apimarket.py")),
        "report": sha16(os.path.join(LEDGER_DIR, "apimarket_report.py")),
    }


def check_sizes(html_path, json_path):
    fails = []
    if not (os.path.exists(html_path) and os.path.exists(json_path)):
        return ["artifacts missing: %s / %s" % (html_path, json_path)]
    with open(json_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    sizes = doc.get("sizes") or {}
    if sizes.get("html") != os.path.getsize(html_path):
        fails.append("sizes html %s != %d on disk"
                     % (sizes.get("html"), os.path.getsize(html_path)))
    if sizes.get("json") != os.path.getsize(json_path):
        fails.append("sizes json %s != %d on disk"
                     % (sizes.get("json"), os.path.getsize(json_path)))
    return fails


def check_sources(json_path):
    if not os.path.exists(json_path):
        return ["artifacts missing: %s" % json_path]
    with open(json_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    recorded = doc.get("sources") or {}
    live = source_fingerprints()
    fails = []
    for key in sorted(live):
        if recorded.get(key) != live[key]:
            fails.append("E_SOURCE_STALE %s recorded %s current %s"
                         % (key, recorded.get(key), live[key]))
    return fails


def _landing_is_default(html_path, json_path):
    """True only when both halves land under THIS root's own preview/.

    The wanted folder is computed from ROOT, not from the rebindable --out and
    --json flags, so a run that redirects its outputs cannot pose as the root.
    """
    want = os.path.realpath(os.path.join(ROOT, "preview"))
    for path in (html_path, json_path):
        if os.path.dirname(os.path.realpath(path)) != want:
            return False
    return True


def _refresh_face(html_path, json_path):
    """AC-PWC53 (R3575): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: the landing already
    happened, so a refusal must not turn a good page into a traceback.
    """
    if not _landing_is_default(html_path, json_path):
        return "SKIPPED scratch"
    try:
        os_src = os.path.join(ROOT, "src", "os")
        if os_src not in sys.path:
            sys.path.insert(0, os_src)
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(ROOT)
        return "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # the landing already happened; name the refusal
        return "SKIPPED %s" % type(exc).__name__


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--out", default=OUT_HTML)
    ap.add_argument("--json", default=OUT_JSON)
    ap.add_argument("--check", action="store_true",
                    help="verify landed sizes and that no recorded input moved")
    try:
        args = ap.parse_args(argv[1:])
    except SystemExit:
        return 5
    if not os.path.exists(os.path.join(LEDGER_DIR, "apimarket.py")):
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py "
                         "missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("POSITION CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envs, disclaimer = read_board()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    buckets = buckets_of(envs)
    problems = check_laws(buckets)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(buckets, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "listing_count": sum(len(bucket["rows"]) for bucket in buckets),
        "bucket_count": len(buckets),
        "buckets": [dict((key, bucket[key]) for key in BUCKET_KEYS)
                    for bucket in buckets],
        "disclaimer": disclaimer,
        "report": os.path.relpath(args.out, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    # The json states both artifact sizes; only its own byte count is
    # self-referential, so iterate to the fixed point.
    for _ in range(6):
        payload["sizes"] = {
            "html": os.path.getsize(args.out),
            "json": (os.path.getsize(args.json)
                     if os.path.exists(args.json) else 0),
        }
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        if payload["sizes"]["json"] == os.path.getsize(args.json):
            break
    face = _refresh_face(args.out, args.json)

    print("POSITION %s bytes=%d listings=%d buckets=%d size=%s band=%s..%s "
          "face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["listing_count"], payload["bucket_count"],
             fmt(buckets[0]["category_size"], "-"),
             fmt(buckets[0]["category_min_price"], "-"),
             fmt(buckets[0]["category_max_price"], "-"), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
