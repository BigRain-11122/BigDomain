#!/usr/bin/env python3
"""Render the market activity-by-time heatmap into one browsable page.

Why this exists: api_market_hour_heatmap shipped in R2165 with eight green
criteria and answers the coarsest operating question the market has - which
HOUR of the day and which WEEKDAY it actually trades in - but git grep finds
zero readers in tools/ and preview/, so the only way to read it was to call
the sandbox from a shell. A seller picking a publish or repricing moment, and
an operator sizing support cover, had no openable face at all.

Nothing here re-implements a market rule: every number on the page comes from
src/sandbox/ledger/apimarket.py api_market_hour_heatmap(), read over a fresh
throwaway demo world seeded through the shipped report helpers. The real
sandbox is never opened for writing.

Usage:
  python tools/market_hour_heatmap.py
  python tools/market_hour_heatmap.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face is missing.

AC-MHP1..AC-MHP6 are pre-registered in src/os/backlog.md (R3399 PIN) BEFORE
this file existed: page and json land with a pinned key set, every number is
the demo world's own, all 168 (weekday, hour) cells print exactly once, the
hour / weekday / cell totals agree with the envelope, the standing compliance
faces ride along with zero external links, and no older criterion is relaxed.

ASCII source, stdlib only, no network. Chinese only appears in the rendered
document, never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "market-hour-heatmap.html")
OUT_JSON = os.path.join(ROOT, "preview", "market-hour-heatmap.json")

FACE = "api_market_hour_heatmap"

# Pinned envelope keys (AC-MHP1). A missing one is a contract break, not a
# silent blank on the page.
PINNED_KEYS = (
    "hour_count", "weekday_count", "cell_count", "sales_count", "gross",
    "refund_count", "refunded", "net", "buyer_count", "seller_count",
    "busiest_hour", "busiest_weekday", "disclaimer", "hours", "weekdays",
    "cells",
)

L = {
    "title": "\u7845\u57fa\u57df \u00b7 \u5e02\u573a\u6d3b\u8dc3\u65f6\u6bb5\u70ed\u529b\u56fe",
    "sub": "BigDomain \u5e02\u573a \u00b7 \u54ea\u4e2a\u5c0f\u65f6\u3001\u661f\u671f\u51e0\u771f\u6b63\u5728\u6210\u4ea4",
    "gen": "\u751f\u6210\u65f6\u95f4",
    "src": "\u8bfb\u6570\u9762",
    "kpi_sales": "\u6210\u4ea4\u7b14\u6570",
    "kpi_gross": "\u6210\u4ea4\u603b\u989d",
    "kpi_refund": "\u9000\u6b3e\u7b14\u6570",
    "kpi_net": "\u51c0\u989d",
    "kpi_buyers": "\u4e70\u5bb6\u6570",
    "kpi_sellers": "\u5356\u5bb6\u6570",
    "kpi_hour": "\u6700\u5fd9\u5c0f\u65f6",
    "kpi_day": "\u6700\u5fd9\u661f\u671f",
    "heat": "\u4e00\u3001\u661f\u671f\u00d7\u5c0f\u65f6\u70ed\u529b\u683c\uff08168 \u683c\u5168\u91cf\u00b7\u7a7a\u683c\u4e5f\u7167\u5370\uff09",
    "hours": "\u4e8c\u3001\u5c0f\u65f6\u884c\uff0824 \u884c\uff09",
    "days": "\u4e09\u3001\u661f\u671f\u884c\uff087 \u884c\uff09",
    "disc": "\u56db\u3001\u5e38\u9a7b\u98ce\u9669\u63d0\u793a",
    "hour": "\u5c0f\u65f6",
    "day": "\u661f\u671f",
    "sales": "\u6210\u4ea4",
    "gross": "\u989d\u5ea6",
    "refund": "\u9000\u6b3e",
    "refunded": "\u9000\u6b3e\u989d",
    "net": "\u51c0\u989d",
    "buyers": "\u4e70\u5bb6",
    "sellers": "\u5356\u5bb6",
    "aigc": "AIGC \u751f\u6210\u5185\u5bb9",
    "rep": "\u590d\u73b0",
    "cmd": "\u590d\u73b0\u547d\u4ee4",
    "none": "-",
}

WEEKDAY_CN = ["\u5468\u4e00", "\u5468\u4e8c", "\u5468\u4e09", "\u5468\u56db",
              "\u5468\u4e94", "\u5468\u516d", "\u5468\u65e5"]


class FaceError(Exception):
    """Named refusal: the shipped face is missing or the world is bad."""

    code = "E_MHH_FACE"


def read_face():
    """Build the demo world in a private dir and read the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="market-hour-heatmap-")
    db = os.path.join(tmp_root, "market-hour-heatmap.db")
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


def fmt(value):
    if value is None:
        return L["none"]
    return str(value)


def heat_row(env):
    """167 grid cells in weekday-major order, looked up by (day, hour)."""
    cells = {(c["weekday"], c["hour"]): c for c in env["cells"]}
    peak = max([c["sales_count"] for c in env["cells"]] or [0])
    out = []
    for day in range(7):
        tds = []
        for hour in range(24):
            cell = cells[(day, hour)]
            n = cell["sales_count"]
            shade = 0 if peak == 0 else int(round(200 - 170.0 * n / peak))
            tds.append(
                '<td class=n title="%s %02d:00 \u00b7 %s=%d">'
                '<span class=h style="background:rgb(%d,%d,%d)">%d</span></td>'
                % (WEEKDAY_CN[day], hour, L["sales"], n, shade, shade,
                   230 if shade < 200 else shade, n))
        out.append("<tr><th>%s</th>%s</tr>" % (WEEKDAY_CN[day], "".join(tds)))
    head = "".join("<th class=n>%02d</th>" % h for h in range(24))
    return head, out


def build_html(env, now):
    e = html.escape
    head_cells, grid = heat_row(env)
    hour_rows = []
    for row in env["hours"]:
        hour_rows.append(
            "<tr><td class=n>%02d:00</td><td class=n>%d</td><td class=n>%d</td>"
            "<td class=n>%d</td><td class=n>%d</td><td class=n>%d</td>"
            "<td class=n>%d</td><td class=n>%d</td></tr>"
            % (row["hour"], row["sales_count"], row["gross"],
               row["refund_count"], row["refunded"], row["net"],
               row["buyer_count"], row["seller_count"]))
    day_rows = []
    for row in env["weekdays"]:
        day_rows.append(
            "<tr><td>%s</td><td class=n>%d</td><td class=n>%d</td>"
            "<td class=n>%d</td><td class=n>%d</td><td class=n>%d</td>"
            "<td class=n>%d</td><td class=n>%d</td></tr>"
            % (e(WEEKDAY_CN[row["weekday"]]), row["sales_count"],
               row["gross"], row["refund_count"], row["refunded"],
               row["net"], row["buyer_count"], row["seller_count"]))
    busiest_hour = (L["none"] if env["busiest_hour"] is None
                    else "%02d:00" % env["busiest_hour"])
    busiest_day = (L["none"] if env["busiest_weekday"] is None
                   else WEEKDAY_CN[env["busiest_weekday"]])

    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--ok:#1f7a4d;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line);vertical-align:middle}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.h{display:inline-block;min-width:26px;padding:2px 4px;border-radius:4px;color:#10141a}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 120px;border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;border:1px solid var(--line);
border-radius:999px;font-size:12px;color:var(--muted)}
foot,footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
</style></head><body><main>
<h1>%s</h1>
<div class=meta>%s \u00b7 %s %s \u00b7 <code>%s</code> \u00b7 <code>%s</code></div>

<div class=card><div class=kpi>
<div><span>%s</span><b>%d</b></div>
<div><span>%s</span><b>%d</b></div>
<div><span>%s</span><b>%d</b></div>
<div><span>%s</span><b>%d</b></div>
<div><span>%s</span><b>%d</b></div>
<div><span>%s</span><b>%d</b></div>
<div><span>%s</span><b>%s</b></div>
<div><span>%s</span><b>%s</b></div>
</div></div>

<h2>%s</h2>
<div class=card><table>
<tr><th>%s</th>%s</tr>
%s
</table></div>

<h2>%s</h2>
<div class=card><table>
<tr><th>%s</th><th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>
<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th><th class=n>%s</th></tr>
%s
</table></div>

<h2>%s</h2>
<div class=card><table>
<tr><th>%s</th><th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>
<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th><th class=n>%s</th></tr>
%s
</table></div>

<h2>%s</h2>
<div class=card><div class=disclaimer>%s</div>
<p style="margin-top:10px"><span class=badge>%s</span></p></div>

<h2>%s</h2>
<div class=card><code>%s</code></div>
<footer>BigDomain OSLoop \u00b7 %s \u00b7 \u672c\u9875\u7531 tools/market_hour_heatmap.py \u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>
</main></body></html>
""" % (
        e(L["title"]), e(L["title"]), e(L["sub"]), e(L["gen"]), e(now),
        e(L["src"]), e(FACE),
        e(L["kpi_sales"]), env["sales_count"],
        e(L["kpi_gross"]), env["gross"],
        e(L["kpi_refund"]), env["refund_count"],
        e(L["kpi_net"]), env["net"],
        e(L["kpi_buyers"]), env["buyer_count"],
        e(L["kpi_sellers"]), env["seller_count"],
        e(L["kpi_hour"]), e(busiest_hour),
        e(L["kpi_day"]), e(busiest_day),
        e(L["heat"]), e(L["day"]), head_cells, "\n".join(grid),
        e(L["hours"]), e(L["hour"]), e(L["sales"]), e(L["gross"]),
        e(L["refund"]), e(L["refunded"]), e(L["net"]), e(L["buyers"]),
        e(L["sellers"]), "\n".join(hour_rows),
        e(L["days"]), e(L["day"]), e(L["sales"]), e(L["gross"]),
        e(L["refund"]), e(L["refunded"]), e(L["net"]), e(L["buyers"]),
        e(L["sellers"]), "\n".join(day_rows),
        e(L["disc"]), e(env["disclaimer"]), e(L["aigc"]),
        e(L["rep"]), e(L["cmd"]), e(now),
    )


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def source_fingerprints():
    """AC-MHP1: the inputs this page's numbers are derived from."""
    return {
        "driver": sha16(os.path.abspath(__file__)),
        "apimarket": sha16(os.path.join(LEDGER_DIR, "apimarket.py")),
        "report": sha16(os.path.join(LEDGER_DIR, "apimarket_report.py")),
    }


def check_sizes(html_path, json_path):
    if not (os.path.exists(html_path) and os.path.exists(json_path)):
        return ["artifacts missing: %s / %s" % (html_path, json_path)]
    with open(json_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    sizes = doc.get("sizes") or {}
    fails = []
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
        print("HEATMAP CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json) else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        env = read_face()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, now)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "hour_count": env["hour_count"],
        "weekday_count": env["weekday_count"],
        "cell_count": env["cell_count"],
        "sales_count": env["sales_count"],
        "gross": env["gross"],
        "refund_count": env["refund_count"],
        "refunded": env["refunded"],
        "net": env["net"],
        "buyer_count": env["buyer_count"],
        "seller_count": env["seller_count"],
        "busiest_hour": env["busiest_hour"],
        "busiest_weekday": env["busiest_weekday"],
        "disclaimer": env["disclaimer"],
        "hours": env["hours"],
        "weekdays": env["weekdays"],
        "cells": env["cells"],
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

    print("HEATMAP %s bytes=%d cells=%d sales=%d gross=%d busiest=%s/%s"
          % (payload["report"], len(doc.encode("utf-8")),
             env["cell_count"], env["sales_count"], env["gross"],
             fmt(env["busiest_hour"]), fmt(env["busiest_weekday"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
