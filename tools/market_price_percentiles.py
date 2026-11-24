#!/usr/bin/env python3
"""Render the market asking-price distribution into one browsable page.

Why this exists: api_market_price_percentiles shipped in R2160 with eight green
criteria of its own and answers the question a seller actually asks before
publishing - where does my asking price sit in this market - but git grep -F
over tools/ and preview/ finds ZERO readers, so the only way to read it was to
call the sandbox from a shell. Nothing else on the openable pages carries the
quartiles: api_market_stats holds a single average, api_categories a min/max
band per bucket, api_listing_position one listing's rank.

Nothing here re-implements a market rule. Every price on the page comes from
src/sandbox/ledger/apimarket.py api_market_price_percentiles() read over a
fresh throwaway demo world seeded through the shipped report helpers; the page
renders the quantiles it is handed and never recomputes one. The only
arithmetic added here is the visual position of a quantile on the min..max
ruler, which is stated on the page as a position, not as a price.

The real sandbox is never opened for writing.

Usage:
  python tools/market_price_percentiles.py
  python tools/market_price_percentiles.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face or the label copy is missing.

AC-MPQ1..AC-MPQ6 are pre-registered in src/os/backlog.md (R3400 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/market-price-percentiles-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "market-price-percentiles.html")
OUT_JSON = os.path.join(ROOT, "preview", "market-price-percentiles.json")
COPY = os.path.join(ROOT, "preview", "market-price-percentiles-copy.json")

FACE = "api_market_price_percentiles"

# Pinned envelope keys (AC-MPQ1). A missing one is a contract break rather
# than a silent blank on the page.
PINNED_KEYS = (
    "listing_count", "live_listing_count", "retired_listing_count",
    "min_price", "max_price", "p25_price", "p50_price", "p75_price",
    "p90_price", "mean_price", "spread", "category_count", "categories",
    "disclaimer",
)

# Pinned payload keys (AC-MPQ1): the envelope plus the ruler, the provenance
# block and the two blocks the --check gate reads.
PAYLOAD_KEYS = (
    "generated_utc", "face", "listing_count", "live_listing_count",
    "retired_listing_count", "min_price", "max_price", "p25_price",
    "p50_price", "p75_price", "p90_price", "mean_price", "spread",
    "category_count", "categories", "quantiles", "disclaimer", "report",
    "sources", "sizes",
)

# The ladder in printed order. mean_price rides along as a reference row and is
# excluded from the ordering criterion (a mean is not a quantile position).
LADDER = ("min_price", "p25_price", "p50_price", "p75_price", "p90_price",
          "max_price")
MEAN_KEY = "mean_price"

COPY_KEYS = (
    "title", "sub", "gen", "src", "kpi_listings", "kpi_live", "kpi_retired",
    "kpi_min", "kpi_p50", "kpi_mean", "kpi_p90", "kpi_spread", "sec_ruler",
    "sec_ladder", "sec_buckets", "sec_disc", "sec_rep", "col_quantile",
    "col_price", "col_position", "col_category", "col_listings", "col_live",
    "col_retired", "col_min", "col_p50", "col_mean", "col_max",
    "q_min_price", "q_p25_price", "q_p50_price", "q_p75_price",
    "q_p90_price", "q_max_price", "q_mean_price", "uncategorized", "aigc",
    "rep", "cmd", "none",
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
td.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 110px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.ruler{position:relative;height:62px;margin:26px 8px 8px}
.rail{position:absolute;top:22px;left:0;right:0;height:8px;border-radius:4px;
background:linear-gradient(90deg,#dfe4ea,#9fb3c8)}
.tick{position:absolute;top:0;transform:translateX(-50%);text-align:center;
font-size:11.5px;color:var(--muted);white-space:nowrap}
.tick i{display:block;width:2px;height:30px;margin:0 auto 2px;
background:#3d5a80}
.tick b{display:block;color:var(--ink);font-variant-numeric:tabular-nums}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""


DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face, or the label copy, is missing."""

    code = "E_MPQ_FACE"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_face():
    """Build the demo world in a private dir and read the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="market-price-percentiles-")
    db = os.path.join(tmp_root, "market-price-percentiles.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        env = getattr(am, FACE)()
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    missing = [key for key in PINNED_KEYS if key not in env]
    if missing:
        raise FaceError("pinned keys missing: %s" % ",".join(missing))
    return env


def quantiles(env):
    """The printed ladder plus the reference mean, with ruler positions.

    Positions are relative to the market's own min..max span; a zero span puts
    every tick at the left end rather than inventing a spread.
    """
    lo = env["min_price"]
    hi = env["max_price"]
    span = 0 if lo is None or hi is None else hi - lo
    rows = []
    for key in LADDER + (MEAN_KEY,):
        price = env[key]
        if price is None:
            pos = 0.0
        elif span <= 0:
            pos = 0.0
        else:
            pos = round((float(price) - float(lo)) * 100.0 / float(span), 1)
        rows.append({"key": key, "price": price, "pos": pos})
    return rows


def ordered(rows):
    """AC-MPQ3 read at the source: the ladder must be non-decreasing."""
    prices = [r["price"] for r in rows if r["key"] in LADDER]
    if any(p is None for p in prices):
        return False
    return prices == sorted(prices)


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def build_html(env, rows, labels, now):
    e = html.escape
    esc = labels
    kpi = [
        (labels["kpi_listings"], fmt(env["listing_count"], labels["none"])),
        (labels["kpi_live"], fmt(env["live_listing_count"], labels["none"])),
        (labels["kpi_retired"], fmt(env["retired_listing_count"],
                                   labels["none"])),
        (labels["kpi_min"], fmt(env["min_price"], labels["none"])),
        (labels["kpi_p50"], fmt(env["p50_price"], labels["none"])),
        (labels["kpi_mean"], fmt(env["mean_price"], labels["none"])),
        (labels["kpi_p90"], fmt(env["p90_price"], labels["none"])),
        (labels["kpi_spread"], fmt(env["spread"], labels["none"])),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>"
                       % (e(k), e(v)) for k, v in kpi)

    ticks = []
    for row in rows:
        if row["key"] == MEAN_KEY:
            continue
        ticks.append(
            '<div class=tick style="left:%.1f%%"><i></i><b>%s</b>%s</div>'
            % (row["pos"], e(fmt(row["price"], labels["none"])),
               e(labels["q_" + row["key"]])))
    ruler = ('<div class=ruler><div class=rail></div>%s</div>'
             % "".join(ticks))

    ladder_rows = []
    for row in rows:
        ladder_rows.append(
            "<tr><td>%s</td><td class=n>%s</td><td class=n>%.1f%%</td></tr>"
            % (e(labels["q_" + row["key"]]),
               e(fmt(row["price"], labels["none"])), row["pos"]))
    ladder = ("<table><tr><th>%s</th><th class=n>%s</th>"
              "<th class=n>%s</th></tr>%s</table>"
              % (e(labels["col_quantile"]), e(labels["col_price"]),
                 e(labels["col_position"]), "".join(ladder_rows)))

    bucket_rows = []
    for row in env["categories"]:
        cat = row["category"]
        bucket_rows.append(
            "<tr><td>%s</td><td class=n>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td class=n>%s</td></tr>"
            % (e(labels["uncategorized"] if cat is None else str(cat)),
               e(fmt(row["listing_count"], labels["none"])),
               e(fmt(row["live_listing_count"], labels["none"])),
               e(fmt(row["retired_listing_count"], labels["none"])),
               e(fmt(row["min_price"], labels["none"])),
               e(fmt(row["p50_price"], labels["none"])),
               e(fmt(row["mean_price"], labels["none"])),
               e(fmt(row["max_price"], labels["none"]))))
    buckets = ("<table><tr><th>%s</th><th class=n>%s</th><th class=n>%s</th>"
               "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
               "<th class=n>%s</th><th class=n>%s</th></tr>%s</table>"
               % (e(labels["col_category"]), e(labels["col_listings"]),
                  e(labels["col_live"]), e(labels["col_retired"]),
                  e(labels["col_min"]), e(labels["col_p50"]),
                  e(labels["col_mean"]), e(labels["col_max"]),
                  "".join(bucket_rows)))

    head = (
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
        "<p style=\"margin-top:10px\"><span class=badge>%s</span></p></div>\n"
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/market_price_percentiles.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_ruler"]), ruler,
           e(labels["sec_ladder"]), ladder,
           e(labels["sec_buckets"]), buckets,
           e(labels["sec_disc"]), DISCLAIMER_SLOT,
           e(labels["aigc"]), e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    # The disclaimer is the face's own sentence, injected after assembly so its
    # text is never retyped here.
    return head.replace(DISCLAIMER_SLOT, e(env["disclaimer"]))


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
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("PRICE CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json) else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        env = read_face()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    rows = quantiles(env)
    if not ordered(rows):
        sys.stderr.write("E_MPQ_ORDER: ladder out of order %s\n"
                         % [(r["key"], r["price"]) for r in rows])
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, rows, labels, now)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "listing_count": env["listing_count"],
        "live_listing_count": env["live_listing_count"],
        "retired_listing_count": env["retired_listing_count"],
        "min_price": env["min_price"],
        "max_price": env["max_price"],
        "p25_price": env["p25_price"],
        "p50_price": env["p50_price"],
        "p75_price": env["p75_price"],
        "p90_price": env["p90_price"],
        "mean_price": env["mean_price"],
        "spread": env["spread"],
        "category_count": env["category_count"],
        "categories": env["categories"],
        "quantiles": rows,
        "disclaimer": env["disclaimer"],
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

    print("PRICE %s bytes=%d listings=%d min=%s p50=%s p90=%s spread=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             env["listing_count"], fmt(env["min_price"], "-"),
             fmt(env["p50_price"], "-"), fmt(env["p90_price"], "-"),
             fmt(env["spread"], "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
