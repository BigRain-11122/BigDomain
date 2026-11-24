#!/usr/bin/env python3
"""Render the buyer star-giving tendency board into one browsable page.

Why this exists: api_buyer_rating_pattern answers a question no other face
answers - is this resident consistently harsh or generous, is it stricter than
the market, and how did its stars spread - with its own AC-BRP criteria, but
git grep -F over tools/ and preview/ found no reader at all, so the only way to
get that answer was to call the sandbox from a shell. The seller scorecard
grades sellers and the neighbour and position boards rank listings; none of
them speaks about the buyer side of a star.

Nothing here re-implements a market rule. Buyers are enumerated from the
shipped api_board() and api_ratings() faces and every number on the page comes
from the shipped api_buyer_rating_pattern() face read over a fresh throwaway
demo world seeded through the shipped report helpers. The page prints the
envelopes it is handed and never recomputes a bucket, an average or a ratio;
the only checks it runs are the face's own published laws, and a broken law
refuses the render instead of printing a plausible page.

The real sandbox is never opened for writing.

Usage:
  python tools/buyer_rating_pattern_board.py
  python tools/buyer_rating_pattern_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BRPB1..AC-BRPB6 are pre-registered in src/os/backlog.md (R3406 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/buyer-rating-pattern-board-copy.json and appear in the rendered
document only, never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "buyer-rating-pattern-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-rating-pattern-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-rating-pattern-board-copy.json")

FACE = "api_buyer_rating_pattern"
BOARD_FACE = "api_board"
RATINGS_FACE = "api_ratings"

# Pinned payload keys (AC-BRPB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "ratings_face", "buyer_count",
    "market_avg_stars", "buyers", "disclaimer", "report", "sources", "sizes",
)

BUCKETS = ("1", "2", "3", "4", "5")

# Pinned per-buyer key set (the shipped twenty-key envelope).
BUYER_KEYS = (
    "buyer_id", "rating_count", "listing_count", "revision_count",
    "revised_rating_count", "star_sum", "avg_stars", "min_stars", "max_stars",
    "harsh_count", "neutral_count", "generous_count", "harsh_ratio",
    "generous_ratio", "market_avg_stars", "tendency_delta", "purchase_count",
    "rating_coverage", "star_distribution", "disclaimer",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_kpi", "sec_buyers", "sec_shape",
    "sec_law", "sec_disc", "sec_rep", "col_buyer", "col_ratings", "col_avg",
    "col_delta", "col_min", "col_max", "col_harsh", "col_neutral",
    "col_generous", "col_harshratio", "col_generousratio", "col_coverage",
    "col_listings", "col_revisions", "col_star", "col_count", "kpi_marketavg",
    "kpi_buyers", "kpi_ratings", "kpi_harsh", "kpi_neutral", "kpi_generous",
    "none", "law_conservation", "law_sum", "law_ratio", "law_delta",
    "law_coverage", "law_effective", "law_none", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
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
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_BRPB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_BRPB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_buyers():
    """Enumerate buyers through the shipped board and ratings faces."""
    tmp_root = tempfile.mkdtemp(prefix="buyer-rating-pattern-board-")
    db = os.path.join(tmp_root, "buyer-rating-pattern-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        seen = set()
        for listing in board["listings"]:
            rated = getattr(am, RATINGS_FACE)(listing["listing_id"])
            for row in rated.get("ratings") or []:
                buyer = row.get("buyer_id")
                if buyer:
                    seen.add(str(buyer))
        buyers = [dict(getattr(am, FACE)(buyer)) for buyer in sorted(seen)]
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
    for block in buyers:
        miss = [key for key in BUYER_KEYS if key not in block]
        if miss:
            raise FaceError("buyer keys missing on %s: %s"
                            % (block.get("buyer_id"), ",".join(miss)))
        dist = block["star_distribution"]
        if not isinstance(dist, dict) or sorted(dist.keys()) != list(BUCKETS):
            raise FaceError("star_distribution shape on %s: %r"
                            % (block.get("buyer_id"), dist))
    return buyers, disclaimer


def check_laws(buyers):
    """AC-BRPB3 read at the source: refuse rather than print."""
    problems = []

    def one(block):
        name = block.get("buyer_id")
        count = int(block["rating_count"])
        dist = block["star_distribution"]
        buckets = [int(dist[b]) for b in BUCKETS]
        harsh = int(block["harsh_count"])
        neutral = int(block["neutral_count"])
        generous = int(block["generous_count"])
        if sum(buckets) != count:
            problems.append("%s buckets sum=%d ratings=%d"
                            % (name, sum(buckets), count))
        if harsh + neutral + generous != count:
            problems.append("%s harsh+neutral+generous=%d ratings=%d"
                            % (name, harsh + neutral + generous, count))
        if harsh != buckets[0] + buckets[1]:
            problems.append("%s harsh=%d buckets=%d"
                            % (name, harsh, buckets[0] + buckets[1]))
        if neutral != buckets[2]:
            problems.append("%s neutral=%d bucket3=%d"
                            % (name, neutral, buckets[2]))
        if generous != buckets[3] + buckets[4]:
            problems.append("%s generous=%d buckets=%d"
                            % (name, generous, buckets[3] + buckets[4]))
        want_sum = sum((i + 1) * n for i, n in enumerate(buckets))
        if int(block["star_sum"]) != want_sum:
            problems.append("%s star_sum=%r expected=%d"
                            % (name, block["star_sum"], want_sum))
        avg = block["avg_stars"]
        want_avg = (float(want_sum) / count) if count else None
        if avg != want_avg:
            problems.append("%s avg=%r expected=%r" % (name, avg, want_avg))
        live = [i + 1 for i, n in enumerate(buckets) if n]
        want_min = min(live) if live else None
        want_max = max(live) if live else None
        if block["min_stars"] != want_min:
            problems.append("%s min=%r expected=%r"
                            % (name, block["min_stars"], want_min))
        if block["max_stars"] != want_max:
            problems.append("%s max=%r expected=%r"
                            % (name, block["max_stars"], want_max))
        for key, part in (("harsh_ratio", harsh),
                          ("generous_ratio", generous)):
            want = (float(part) / count) if count else None
            if block[key] != want:
                problems.append("%s %s=%r expected=%r"
                                % (name, key, block[key], want))
        market = block["market_avg_stars"]
        want_delta = None
        if avg is not None and market is not None:
            want_delta = avg - market
        if block["tendency_delta"] != want_delta:
            problems.append("%s tendency_delta=%r expected=%r"
                            % (name, block["tendency_delta"], want_delta))
        bought = int(block["purchase_count"])
        want_cov = (float(count) / bought) if bought else None
        if block["rating_coverage"] != want_cov:
            problems.append("%s coverage=%r expected=%r"
                            % (name, block["rating_coverage"], want_cov))
        if int(block["listing_count"]) > count:
            problems.append("%s listing_count=%r ratings=%d"
                            % (name, block["listing_count"], count))

    for block in buyers:
        one(block)

    ids = [str(block["buyer_id"]) for block in buyers]
    if ids != sorted(ids):
        problems.append("buyer order=%r" % (ids,))
    markets = set(repr(block["market_avg_stars"]) for block in buyers)
    if len(markets) > 1:
        problems.append("market_avg_stars differs across buyers: %r"
                        % (sorted(markets),))
    return problems


def fmt(value, none_text, digits=4):
    if value is None:
        return none_text
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return ("%." + str(digits) + "f") % value
    return str(value)


def build_html(buyers, labels, now, disclaimer):
    e = html.escape
    none = labels["none"]
    market = buyers[0]["market_avg_stars"] if buyers else None
    total_ratings = sum(int(b["rating_count"]) for b in buyers)
    kpi = [
        (labels["kpi_marketavg"], fmt(market, none)),
        (labels["kpi_buyers"], str(len(buyers))),
        (labels["kpi_ratings"], str(total_ratings)),
        (labels["kpi_harsh"], str(sum(int(b["harsh_count"])
                                     for b in buyers))),
        (labels["kpi_neutral"], str(sum(int(b["neutral_count"])
                                       for b in buyers))),
        (labels["kpi_generous"], str(sum(int(b["generous_count"])
                                        for b in buyers))),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                       for k, v in kpi)

    buyer_head = (labels["col_buyer"], labels["col_ratings"], labels["col_avg"],
                  labels["col_delta"], labels["col_min"], labels["col_max"],
                  labels["col_harsh"], labels["col_neutral"],
                  labels["col_generous"], labels["col_harshratio"],
                  labels["col_generousratio"], labels["col_coverage"],
                  labels["col_listings"], labels["col_revisions"])
    buyer_head_html = ('<th>%s</th>' % e(buyer_head[0])) + "".join(
        '<th class=n>%s</th>' % e(cell) for cell in buyer_head[1:])

    buyer_rows = []
    for block in buyers:
        cells = (
            fmt(block["rating_count"], none),
            fmt(block["avg_stars"], none),
            fmt(block["tendency_delta"], none),
            fmt(block["min_stars"], none),
            fmt(block["max_stars"], none),
            fmt(block["harsh_count"], none),
            fmt(block["neutral_count"], none),
            fmt(block["generous_count"], none),
            fmt(block["harsh_ratio"], none),
            fmt(block["generous_ratio"], none),
            fmt(block["rating_coverage"], none),
            fmt(block["listing_count"], none),
            fmt(block["revision_count"], none),
        )
        buyer_rows.append('<tr class="buyer"><td>%s</td>%s</tr>'
                          % (e(str(block["buyer_id"])),
                             "".join("<td class=n>%s</td>" % e(v)
                                     for v in cells)))

    shape_head = "".join('<th class=n>%s</th>' % e(b) for b in BUCKETS)
    shape_rows = []
    for block in buyers:
        dist = block["star_distribution"]
        shape_rows.append('<tr class="shape"><td>%s</td>%s</tr>'
                          % (e(str(block["buyer_id"])),
                             "".join("<td class=n>%s</td>"
                                     % e(fmt(dist[b], none))
                                     for b in BUCKETS)))

    laws = [labels["law_conservation"], labels["law_sum"], labels["law_ratio"],
            labels["law_delta"], labels["law_coverage"],
            labels["law_effective"], labels["law_none"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n<div class=card><table><tr>%s</tr>%s</table></div>\n"
        "<h2>%s</h2>\n<div class=card><table><tr><th>%s</th>%s</tr>%s"
        "</table></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/buyer_rating_pattern_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_kpi"]), kpi_html,
           e(labels["sec_buyers"]), buyer_head_html, "".join(buyer_rows),
           e(labels["sec_shape"]), e(labels["col_buyer"]), shape_head,
           "".join(shape_rows),
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
        print("BUYER PATTERN CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        buyers, disclaimer = read_buyers()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(buyers)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(buyers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "ratings_face": RATINGS_FACE,
        "buyer_count": len(buyers),
        "market_avg_stars": (buyers[0]["market_avg_stars"] if buyers else None),
        "buyers": buyers,
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

    print("BUYER PATTERN %s bytes=%d buyers=%d market_avg=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"], payload["market_avg_stars"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
