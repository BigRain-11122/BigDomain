#!/usr/bin/env python3
"""Render the shelf detail face into one page a human can open.

Why this exists: api_view answers "what exactly is this shelf - the price it
carries now against the price it was published at, how many times its price,
category and metadata were revised, how many buyers took it, how they rated
it, how many refunds it paid, and whether it is still on the shelf" with its
own AC-AMV criteria, but a search over tools/, preview/ and src/os answered
rc=1 with zero hits, so the discovery page could print a listing id and
nothing could open it. Nobody could see on one page that a shelf sold twice,
paid one refund and averaged five stars.

Nothing here re-implements a market rule. Every number comes from the shipped
api_view() face read over a fresh throwaway demo world seeded through the
shipped report helpers, and the listing ids come from the shipped board face
instead of being typed by hand. The page prints what the face hands it and
recomputes only its own market strip, which the page says out loud is a sum of
the printed envelopes and not a shipped field. A broken identity refuses the
render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/listing_view_board.py
  python tools/listing_view_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-LVWB1..AC-LVWB6 are pre-registered in src/os/backlog.md (R3438 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/listing-view-board-copy.json and appear in the rendered document only,
never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "listing-view-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "listing-view-board.json")
COPY = os.path.join(ROOT, "preview", "listing-view-board-copy.json")

FACE = "api_view"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-LVWB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "listing_count",
    "listings", "market", "disclaimer", "report", "sources", "sizes",
)

# The shipped detail envelope, 28 keys.
ENVELOPE_KEYS = (
    "listing_id", "dev_account", "listing_key", "title", "description",
    "token_price", "base_token_price", "base_title", "base_description",
    "metadata_revision_count", "latest_metadata_revision_utc",
    "revision_count", "latest_revision_utc", "ai_label", "listed_utc",
    "category", "base_category", "category_revision_count",
    "latest_category_revision_utc", "purchase_count", "rating_count",
    "rating_avg", "refund_count", "refunded_total", "net_purchase_count",
    "delisted", "delisted_utc", "disclaimer",
)

# The market strip is this page's sum over the printed envelopes.
MARKET_KEYS = (
    "listing_count", "purchase_count", "rating_count", "refund_count",
    "refunded_total", "net_purchase_count", "revision_count",
    "metadata_revision_count", "category_revision_count", "ai_label_count",
    "delisted_count", "price_total", "top_price",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_listings", "sec_law", "sec_disc", "sec_rep",
    "kpi_listings", "kpi_purchases", "kpi_ratings", "kpi_refunds",
    "kpi_refunded", "kpi_net", "kpi_revisions", "kpi_labeled",
    "kpi_delisted", "kpi_price_total", "kpi_top",
    "badge_live", "badge_delisted", "badge_labeled", "badge_unlabeled",
    "lbl_price", "lbl_base_price", "lbl_category", "lbl_base_category",
    "lbl_purchases", "lbl_ratings", "lbl_avg", "lbl_refunds",
    "lbl_refunded", "lbl_net", "lbl_revisions", "lbl_meta_rev",
    "lbl_cat_rev", "lbl_listed", "lbl_rev_at", "lbl_meta_at",
    "lbl_cat_at", "lbl_delisted_at", "lbl_seller", "lbl_key", "lbl_desc",
    "empty", "none", "yes", "no",
    "law_count", "law_net", "law_refund", "law_rating", "law_avg",
    "law_stamp", "law_delist", "law_label", "law_order", "law_market",
    "law_notadvice", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:18px 0 6px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.warn{border-color:#e7c1bb;background:#fdf1ef;color:#b42318}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.desc{color:var(--muted);font-size:13px;margin:6px 0 10px}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_LVWB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_LVWB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_world():
    """One shipped detail envelope per listing on the shipped board face."""
    tmp_root = tempfile.mkdtemp(prefix="listing-view-board-")
    db = os.path.join(tmp_root, "listing-view-board.db")
    led = mtr = dk = am = None
    listings = []
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        ids = sorted(int(row["listing_id"]) for row in board["listings"])
        for listing_id in ids:
            listings.append(dict(getattr(am, FACE)(listing_id)))
        disclaimer = listings[0]["disclaimer"] if listings else None
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    for envelope in listings:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("listing_id"), ",".join(missing)))
    return listings, disclaimer


def derived(listings):
    """The market strip this page states out loud, recomputed from the rows."""
    prices = [int(row["token_price"]) for row in listings]
    return {
        "listing_count": len(listings),
        "purchase_count": sum(int(row["purchase_count"]) for row in listings),
        "rating_count": sum(int(row["rating_count"]) for row in listings),
        "refund_count": sum(int(row["refund_count"]) for row in listings),
        "refunded_total": sum(int(row["refunded_total"]) for row in listings),
        "net_purchase_count": sum(int(row["net_purchase_count"])
                                  for row in listings),
        "revision_count": sum(int(row["revision_count"]) for row in listings),
        "metadata_revision_count": sum(
            int(row["metadata_revision_count"]) for row in listings),
        "category_revision_count": sum(
            int(row["category_revision_count"]) for row in listings),
        "ai_label_count": sum(1 for row in listings
                              if int(row["ai_label"]) == 1),
        "delisted_count": sum(1 for row in listings if bool(row["delisted"])),
        "price_total": sum(prices),
        "top_price": max(prices) if prices else None,
    }


def check_laws(listings, disclaimer):
    """AC-LVWB3 read at the source: refuse rather than print."""
    problems = []
    previous = None
    for row in listings:
        tag = "listing %s" % row.get("listing_id")
        lid = int(row["listing_id"])
        if previous is not None and lid <= previous:
            problems.append("%s listing_id not strictly ascending" % tag)
        previous = lid
        purchases = int(row["purchase_count"])
        refunds = int(row["refund_count"])
        ratings = int(row["rating_count"])
        if refunds > purchases:
            problems.append("%s refund_count %d > purchase_count %d"
                            % (tag, refunds, purchases))
        if ratings > purchases:
            problems.append("%s rating_count %d > purchase_count %d"
                            % (tag, ratings, purchases))
        if int(row["net_purchase_count"]) != purchases - refunds:
            problems.append("%s net_purchase_count %s != %d-%d"
                            % (tag, row["net_purchase_count"], purchases,
                               refunds))
        avg = row["rating_avg"]
        if ratings == 0:
            # Measured on the shipped face: with no rating at all the face
            # answers 0.0, not null. This page prints the dash for that zero
            # instead of passing it off as a real score.
            if avg is not None and float(avg) != 0.0:
                problems.append("%s rating_avg %r with zero ratings"
                                % (tag, avg))
        elif avg is None or not (1 <= float(avg) <= 5):
            problems.append("%s rating_avg %r over %d ratings"
                            % (tag, avg, ratings))
        for count_key, stamp_key in (
                ("revision_count", "latest_revision_utc"),
                ("metadata_revision_count", "latest_metadata_revision_utc"),
                ("category_revision_count",
                 "latest_category_revision_utc")):
            if int(row[count_key]) < 0:
                problems.append("%s %s negative" % (tag, count_key))
            if int(row[count_key]) == 0 and row[stamp_key] is not None:
                problems.append("%s %s on a zero count"
                                % (tag, stamp_key))
        if bool(row["delisted"]) and row["delisted_utc"] is None:
            problems.append("%s delisted without a stamp" % tag)
        if int(row["ai_label"]) not in (0, 1):
            problems.append("%s ai_label %r" % (tag, row["ai_label"]))
        if row["disclaimer"] != disclaimer:
            problems.append("%s disclaimer differs from the first envelope"
                            % tag)
    return problems


def text(value, none_text):
    return none_text if value is None else str(value)


def number(value, none_text):
    return none_text if value is None else str(value)


def badge_row(row, labels, e):
    items = []
    if bool(row["delisted"]):
        items.append('<span class="badge warn">%s</span>'
                     % e(labels["badge_delisted"]))
    else:
        items.append('<span class="badge">%s</span>' % e(labels["badge_live"]))
    if int(row["ai_label"]) == 1:
        items.append('<span class="badge">%s</span>'
                     % e(labels["badge_labeled"]))
    else:
        items.append('<span class="badge warn">%s</span>'
                     % e(labels["badge_unlabeled"]))
    return "".join(items)


def kpi_html(block, labels, e, dash, prefix):
    if int(block["rating_count"]) == 0:
        avg_text = dash
    else:
        avg_text = number(block.get("rating_avg"), dash)
    items = [
        (labels[prefix + "purchases"], block["purchase_count"]),
        (labels[prefix + "ratings"], block["rating_count"]),
        (labels[prefix + "avg"], avg_text),
        (labels[prefix + "refunds"], block["refund_count"]),
        (labels[prefix + "refunded"], block["refunded_total"]),
        (labels[prefix + "net"], block["net_purchase_count"]),
        (labels[prefix + "revisions"], block["revision_count"]),
        (labels[prefix + "meta_rev"], block["metadata_revision_count"]),
        (labels[prefix + "cat_rev"], block["category_revision_count"]),
        (labels[prefix + "price"], block["token_price"]),
        (labels[prefix + "base_price"], block["base_token_price"]),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(k)), e(str(v))) for k, v in items)


def stamps_table(row, labels, e, dash):
    pairs = [
        (labels["lbl_seller"], str(row["dev_account"])),
        (labels["lbl_key"], str(row["listing_key"])),
        (labels["lbl_category"], text(row["category"], dash)),
        (labels["lbl_base_category"], text(row["base_category"], dash)),
        (labels["lbl_listed"], text(row["listed_utc"], dash)),
        (labels["lbl_rev_at"], text(row["latest_revision_utc"], dash)),
        (labels["lbl_meta_at"], text(row["latest_metadata_revision_utc"], dash)),
        (labels["lbl_cat_at"], text(row["latest_category_revision_utc"], dash)),
        (labels["lbl_delisted_at"], text(row["delisted_utc"], dash)),
    ]
    body = "".join("<tr><td>%s</td><td>%s</td></tr>"
                   % (e(name), e(value)) for name, value in pairs)
    return "<table>%s</table>" % body


def listing_section(row, labels, e, dash):
    return (
        '<div class=card data-listing="%s">\n'
        "<h3>%s &middot; %s</h3>\n"
        "<div>%s</div>\n"
        '<p class=desc>%s</p>\n'
        "<div class=kpi>%s</div>\n"
        "%s\n</div>\n"
        % (e(str(row["listing_id"])), e(str(row["listing_id"])),
           e(str(row["title"])), badge_row(row, labels, e),
           e(str(row["description"] or dash)),
           kpi_html(row, labels, e, dash, "lbl_"),
           stamps_table(row, labels, e, dash))
    )


def build_html(listings, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_net"], labels["law_refund"],
            labels["law_rating"], labels["law_avg"], labels["law_stamp"],
            labels["law_delist"], labels["law_label"], labels["law_order"],
            labels["law_market"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    market_kpi = "".join(
        "<div><span>%s</span><b>%s</b></div>"
        % (e(labels[key]),
           e(dash if market[field] is None else str(market[field])))
        for key, field in (
            ("kpi_listings", "listing_count"),
            ("kpi_purchases", "purchase_count"),
            ("kpi_ratings", "rating_count"),
            ("kpi_refunds", "refund_count"),
            ("kpi_refunded", "refunded_total"),
            ("kpi_net", "net_purchase_count"),
            ("kpi_revisions", "revision_count"),
            ("kpi_labeled", "ai_label_count"),
            ("kpi_delisted", "delisted_count"),
            ("kpi_price_total", "price_total"),
            ("kpi_top", "top_price"),
        ))
    if listings:
        sections = "".join(listing_section(row, labels, e, dash)
                           for row in listings)
    else:
        sections = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card data-market="1"><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), market_kpi,
           e(labels["sec_listings"]), sections,
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["rep"]), e(now), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(str(disclaimer or "")))


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
        print("LISTING-VIEW CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        listings, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(listings, disclaimer)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    market = derived(listings)
    doc = build_html(listings, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "market",
        "listing_count": len(listings),
        "listings": [{key: row[key] for key in ENVELOPE_KEYS}
                     for row in listings],
        "market": {key: market[key] for key in MARKET_KEYS},
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

    print("LISTING-VIEW %s bytes=%d listings=%d purchases=%d refunds=%d"
          % (payload["report"], len(doc.encode("utf-8")), len(listings),
             market["purchase_count"], market["refund_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))