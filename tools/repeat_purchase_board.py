#!/usr/bin/env python3
"""Render the repeat-purchase retention board into one browsable page.

Why this exists: api_repeat_purchase answered the marketplace's most load-
bearing health question - does the same resident come back and buy a second
time - with its own AC-RPT criteria, but git grep -F over tools/ and preview/
found no reader at all, so the only way to get that answer was to call the
sandbox from a shell. The neighbour and position boards rank listings; none of
them counts buyers, and none of them can say whether retention exists.

Nothing here re-implements a market rule. Sellers are enumerated from the
shipped api_board() face and every number on the page comes from the shipped
api_repeat_purchase() face read over a fresh throwaway demo world seeded
through the shipped report helpers: once for the market and once per seller.
The page prints the envelopes it is handed and never recomputes a rate, an
average or a repeat count; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing.

Usage:
  python tools/repeat_purchase_board.py
  python tools/repeat_purchase_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-RPN1..AC-RPN6 are pre-registered in src/os/backlog.md (R3405 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/repeat-purchase-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "repeat-purchase-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "repeat-purchase-board.json")
COPY = os.path.join(ROOT, "preview", "repeat-purchase-board-copy.json")

FACE = "api_repeat_purchase"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-RPN1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope_count", "market", "scopes",
    "disclaimer", "report", "sources", "sizes",
)

SCOPE_KEYS = ("dev_account", "buyer_count", "repeat_buyer_count",
              "one_time_buyer_count", "repeat_rate", "purchase_count",
              "repeat_purchase_count", "avg_purchases_per_buyer",
              "max_purchases", "top_repeat_buyer", "categories", "disclaimer")

CAT_KEYS = ("category", "buyer_count", "repeat_buyer_count",
            "one_time_buyer_count", "repeat_rate", "purchase_count",
            "repeat_purchase_count", "avg_purchases_per_buyer")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_kpi", "sec_scopes",
    "sec_cats", "sec_law", "sec_disc", "sec_rep", "col_scope", "col_buyers",
    "col_repeat", "col_onetime", "col_purchases", "col_repeatpurch",
    "col_avg", "col_rate", "col_max", "col_top", "col_category",
    "kpi_buyers", "kpi_repeat", "kpi_onetime", "kpi_purchases",
    "kpi_repeatpurch", "kpi_avg", "kpi_max", "kpi_top", "none",
    "market_label", "cat_uncat", "law_net", "law_repeat", "law_count",
    "law_scope", "law_cat", "law_none", "law_sumbuyers", "rep", "cmd",
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
tr.market td{background:#f4f7fb;font-weight:600}
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

    code = "E_RPN_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_RPN_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_scopes():
    """Read the market scope, then one scope per seller the board enumerates."""
    tmp_root = tempfile.mkdtemp(prefix="repeat-purchase-board-")
    db = os.path.join(tmp_root, "repeat-purchase-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        market = dict(getattr(am, FACE)())
        sellers = sorted(set(str(row["dev_account"])
                             for row in board["listings"]))
        scopes = [dict(getattr(am, FACE)(seller)) for seller in sellers]
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
    for block, name in [(market, "market")] + [(s, str(s["dev_account"]))
                                              for s in scopes]:
        for key in SCOPE_KEYS:
            if key not in block:
                raise FaceError("scope keys missing on %s: %s" % (name, key))
        if not isinstance(block["categories"], list):
            raise FaceError("categories is not a list on %s" % name)
        for row in block["categories"]:
            miss = [k for k in CAT_KEYS if k not in row]
            if miss:
                raise FaceError("category keys missing: %s" % ",".join(miss))
    if market["dev_account"] is not None:
        raise FaceError("market scope carries a seller: %r"
                        % (market["dev_account"],))
    return market, scopes, disclaimer


def check_laws(market, scopes):
    """AC-RPN3 / AC-RPN4 read at the source: refuse rather than print."""
    problems = []

    def ident(block, name):
        buyers = int(block["buyer_count"])
        repeat = int(block["repeat_buyer_count"])
        onetime = int(block["one_time_buyer_count"])
        bought = int(block["purchase_count"])
        again = int(block["repeat_purchase_count"])
        if repeat + onetime != buyers:
            problems.append("%s repeat+onetime=%d buyers=%d"
                            % (name, repeat + onetime, buyers))
        if again != bought - buyers:
            problems.append("%s repeat_purchases=%d expected=%d"
                            % (name, again, bought - buyers))
        rate = block["repeat_rate"]
        want_rate = (float(repeat) / buyers) if buyers else None
        if rate != want_rate:
            problems.append("%s repeat_rate=%r expected=%r"
                            % (name, rate, want_rate))
        avg = block["avg_purchases_per_buyer"]
        want_avg = (float(bought) / buyers) if buyers else None
        if avg != want_avg:
            problems.append("%s avg=%r expected=%r" % (name, avg, want_avg))

    ident(market, "market")
    for scope in scopes:
        ident(scope, str(scope["dev_account"]))

    for block, name in [(market, "market")] + [(s, str(s["dev_account"]))
                                               for s in scopes]:
        cats = block["categories"]
        keyed = [(row["category"] is None, row["category"] or "") for row
                 in cats]
        if keyed != sorted(keyed):
            problems.append("%s category order=%r" % (name, keyed))
        if sum(int(row["purchase_count"]) for row in cats) != int(
                block["purchase_count"]):
            problems.append("%s category purchases do not sum to scope" % name)
        if sum(int(row["repeat_purchase_count"]) for row in cats) != int(
                block["repeat_purchase_count"]):
            problems.append("%s category repeats do not sum to scope" % name)
        for row in cats:
            ident(row, "%s/%r" % (name, row["category"]))
        top = block["top_repeat_buyer"]
        if top is not None and int(block["repeat_buyer_count"]) == 0:
            problems.append("%s names a top repeat buyer with no repeats"
                            % name)
    return problems


def fmt(value, none_text, digits=4):
    if value is None:
        return none_text
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return ("%." + str(digits) + "f") % value
    return str(value)


def cat_name(row, labels):
    if row["category"] is None:
        return labels["cat_uncat"]
    return str(row["category"])


def scope_cells(block, labels):
    return (fmt(block["buyer_count"], labels["none"]),
            fmt(block["repeat_buyer_count"], labels["none"]),
            fmt(block["one_time_buyer_count"], labels["none"]),
            fmt(block["purchase_count"], labels["none"]),
            fmt(block["repeat_purchase_count"], labels["none"]),
            fmt(block["avg_purchases_per_buyer"], labels["none"]),
            fmt(block["repeat_rate"], labels["none"]),
            fmt(block["max_purchases"], labels["none"]),
            fmt(block["top_repeat_buyer"], labels["none"]))


def build_html(market, scopes, labels, now, disclaimer):
    e = html.escape
    none = labels["none"]
    kpi = [
        (labels["kpi_buyers"], fmt(market["buyer_count"], none)),
        (labels["kpi_repeat"], fmt(market["repeat_buyer_count"], none)),
        (labels["kpi_onetime"], fmt(market["one_time_buyer_count"], none)),
        (labels["kpi_purchases"], fmt(market["purchase_count"], none)),
        (labels["kpi_repeatpurch"], fmt(market["repeat_purchase_count"],
                                         none)),
        (labels["kpi_avg"], fmt(market["avg_purchases_per_buyer"], none)),
        (labels["kpi_max"], fmt(market["max_purchases"], none)),
        (labels["kpi_top"], fmt(market["top_repeat_buyer"], none)),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                       for k, v in kpi)

    head_cells = (labels["col_scope"], labels["col_buyers"],
                  labels["col_repeat"], labels["col_onetime"],
                  labels["col_purchases"], labels["col_repeatpurch"],
                  labels["col_avg"], labels["col_rate"], labels["col_max"],
                  labels["col_top"])
    head_html = "".join(
        '<th class=n>%s</th>' % e(cell) for cell in head_cells[:1])
    head_html += "".join('<th class=n>%s</th>' % e(cell)
                         for cell in head_cells[1:])

    scope_rows = ['<tr class="scope market"><td>%s</td>%s</tr>'
                  % (e(labels["market_label"]),
                     "".join("<td class=n>%s</td>" % e(v) for v in
                             scope_cells(market, labels)))]
    for scope in scopes:
        scope_rows.append('<tr class="scope"><td>%s</td>%s</tr>'
                          % (e(str(scope["dev_account"])),
                             "".join("<td class=n>%s</td>" % e(v) for v in
                                     scope_cells(scope, labels))))

    cat_head = (labels["col_category"], labels["col_buyers"],
                labels["col_repeat"], labels["col_onetime"],
                labels["col_purchases"], labels["col_repeatpurch"],
                labels["col_avg"], labels["col_rate"])
    cat_rows = []
    for row in market["categories"]:
        cells = (cat_name(row, labels),
                 fmt(row["buyer_count"], none),
                 fmt(row["repeat_buyer_count"], none),
                 fmt(row["one_time_buyer_count"], none),
                 fmt(row["purchase_count"], none),
                 fmt(row["repeat_purchase_count"], none),
                 fmt(row["avg_purchases_per_buyer"], none),
                 fmt(row["repeat_rate"], none))
        cat_rows.append('<tr class="cat"><td>%s</td>%s</tr>'
                        % (e(cells[0]),
                           "".join("<td class=n>%s</td>" % e(v)
                                   for v in cells[1:])))

    laws = [labels["law_net"], labels["law_repeat"], labels["law_count"],
            labels["law_scope"], labels["law_cat"], labels["law_none"],
            labels["law_sumbuyers"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n<div class=card><table><tr>%s</tr>%s</table></div>\n"
        "<h2>%s</h2>\n<div class=card><table><tr>%s</tr>%s</table></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/repeat_purchase_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_kpi"]), kpi_html,
           e(labels["sec_scopes"]), head_html, "".join(scope_rows),
           e(labels["sec_cats"]),
           "".join('<th class=n>%s</th>' % e(cell) for cell in cat_head),
           "".join(cat_rows),
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
        print("REPEAT CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        market, scopes, disclaimer = read_scopes()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(market, scopes)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(market, scopes, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope_count": len(scopes),
        "market": market,
        "scopes": scopes,
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

    print("REPEAT %s bytes=%d scopes=%d market_buyers=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["scope_count"], payload["market"]["buyer_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
