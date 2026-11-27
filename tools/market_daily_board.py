#!/usr/bin/env python3
"""Render the market daily settlement sheet into one browsable page.

Why this exists: api_market_daily shipped with its own AC-MDL1..AC-MDL8
criteria and answers the sheet an operator actually reads - what did the market
do on one calendar day, and which day was the busiest - but the R3408 census
re-measured the six faces the R3407 board named as candidates and found ZERO
readers under tools/ and preview/ for every one of them, api_market_daily
included. Every other time axis stops short of a date: api_market_months answers
one UTC month, api_market_hour_heatmap answers an hour-of-weekday slot
aggregated across all history, api_market_feed lists event rows. So the daily
sheet could only be read by calling the sandbox from a shell.

Nothing here re-implements a market rule. Every number on the page comes from
src/sandbox/ledger/apimarket.py api_market_daily() read over a fresh throwaway
demo world seeded through the shipped report helpers; the page prints the days
and totals it is handed and never recomputes one. The only arithmetic added
here is the visual width of the net bar (a day's absolute net over the page's
own largest absolute net), which is stated on the page as a width - not a share
and not a return.

The real sandbox is never opened for writing.

Usage:
  python tools/market_daily_board.py
  python tools/market_daily_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face or the label copy is missing.

AC-MDB1..AC-MDB6 are pre-registered in src/os/backlog.md (R3408 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/market-daily-copy.json and appear in the rendered document only, never
in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "market-daily.html")
OUT_JSON = os.path.join(ROOT, "preview", "market-daily.json")
COPY = os.path.join(ROOT, "preview", "market-daily-copy.json")

FACE = "api_market_daily"

# Pinned envelope keys (AC-MDB1). A missing one is a contract break rather than
# a silent blank on the page.
PINNED_KEYS = (
    "day_count", "active_day_count", "zero_day_count", "window_start",
    "window_end", "lifetime_sales_count", "lifetime_gross",
    "lifetime_refund_count", "lifetime_refunded", "lifetime_net",
    "lifetime_dev_revenue", "lifetime_platform_revenue", "busiest_day",
    "quietest_active_day", "avg_net_per_active_day", "days", "disclaimer",
)

ROW_KEYS = (
    "day", "sales_count", "gross", "refund_count", "refunded", "net",
    "dev_share", "platform_share", "dev_share_net", "platform_share_net",
    "buyer_count", "seller_count", "listing_count",
)

# Pinned payload keys (AC-MDB1): the envelope plus the provenance and the two
# blocks the --check gate reads.
PAYLOAD_KEYS = (
    "generated_utc", "face", "day_count", "active_day_count",
    "zero_day_count", "window_start", "window_end", "lifetime_sales_count",
    "lifetime_gross", "lifetime_refund_count", "lifetime_refunded",
    "lifetime_net", "lifetime_dev_revenue", "lifetime_platform_revenue",
    "busiest_day", "quietest_active_day", "avg_net_per_active_day", "days",
    "disclaimer", "report", "sources", "sizes",
)

COPY_KEYS = (
    "title", "sub", "gen", "src", "kpi_window", "kpi_days", "kpi_active",
    "kpi_zero", "kpi_gross", "kpi_refunded", "kpi_net", "kpi_dev",
    "kpi_platform", "kpi_avg", "sec_days", "sec_extremes", "sec_laws",
    "sec_disc", "sec_rep",
    "col_day", "col_sales", "col_gross", "col_refund", "col_refunded",
    "col_net", "col_devnet", "col_platnet", "col_buyers", "col_sellers",
    "col_listings", "col_bar",
    "law1", "law2", "law3", "law4", "law5", "law6", "law7",
    "busiest", "quietest", "avg", "zero_note", "none", "aigc", "cmd",
    "top_none",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tr.zero td{color:#96a0aa}
tr.refundday td.neg{color:#a33}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 120px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.track{background:#eef1f5;border-radius:4px;height:10px;min-width:70px}
.fill{background:#3d5a80;height:10px;border-radius:4px;min-width:0}
.fill.neg{background:#b5654a}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.weak{font-size:14px}
.weak b{font-variant-numeric:tabular-nums}
ol.laws{margin:0;padding-left:20px;font-size:13px;color:#2b3138}
ol.laws li{margin-bottom:4px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""


DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face, or the label copy, is missing."""

    code = "E_MDB_FACE"


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
    tmp_root = tempfile.mkdtemp(prefix="market-daily-")
    db = os.path.join(tmp_root, "market-daily.db")
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
    if not isinstance(env.get("days"), list):
        raise FaceError("days is not a list: %r" % (env.get("days"),))
    if int(env["day_count"]) != len(env["days"]):
        raise FaceError("day_count %r != %d rows"
                        % (env["day_count"], len(env["days"])))
    for row in env["days"]:
        row_missing = [key for key in ROW_KEYS if key not in row]
        if row_missing:
            raise FaceError("row keys missing: %s" % ",".join(row_missing))
    return env


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def bar_width(net, peak):
    """Visual width only: absolute net over the page's own largest absolute."""
    if not peak:
        return 0.0
    return round(abs(float(net)) * 100.0 / float(peak), 1)


def build_html(env, labels, now):
    e = html.escape
    none = labels["none"]
    window = "%s &rarr; %s" % (e(str(env["window_start"])),
                               e(str(env["window_end"])))
    kpi = [
        (labels["kpi_window"], window),
        (labels["kpi_days"], fmt(env["day_count"], none)),
        (labels["kpi_active"], fmt(env["active_day_count"], none)),
        (labels["kpi_zero"], fmt(env["zero_day_count"], none)),
        (labels["kpi_gross"], fmt(env["lifetime_gross"], none)),
        (labels["kpi_refunded"], fmt(env["lifetime_refunded"], none)),
        (labels["kpi_net"], fmt(env["lifetime_net"], none)),
        (labels["kpi_dev"], fmt(env["lifetime_dev_revenue"], none)),
        (labels["kpi_platform"], fmt(env["lifetime_platform_revenue"], none)),
        (labels["kpi_avg"], fmt(env["avg_net_per_active_day"], none)),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>"
                       % (e(k), v) for k, v in kpi)

    days = env["days"]
    peak = max([abs(int(row["net"])) for row in days] or [0])
    row_html = []
    for row in days:
        net = int(row["net"])
        is_zero = not (row["sales_count"] or row["refund_count"])
        is_refund_day = bool(row["refund_count"]) and not row["sales_count"]
        cls = "zero" if is_zero else ("refundday" if is_refund_day else "day")
        width = bar_width(net, peak)
        fill_cls = "fill neg" if net < 0 else "fill"
        net_cls = "n neg" if net < 0 else "n"
        row_html.append(
            '<tr class="%s"><td>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td>'
            '<td class="%s">%s</td>'
            '<td><div class=track><div class="%s" style="width:%.1f%%">'
            '</div></div></td>'
            '<td class=n>%s</td><td class=n>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>'
            % (cls, e(str(row["day"])),
               e(fmt(row["sales_count"], none)),
               e(fmt(row["gross"], none)),
               e(fmt(row["refund_count"], none)),
               e(fmt(row["refunded"], none)),
               net_cls, e(fmt(net, none)),
               fill_cls, width,
               e(fmt(row["dev_share_net"], none)),
               e(fmt(row["platform_share_net"], none)),
               e(fmt(row["buyer_count"], none)),
               e(fmt(row["seller_count"], none)),
               e(fmt(row["listing_count"], none))))
    rows = ("<table><tr><th>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th></tr>"
            "%s</table>"
            % (e(labels["col_day"]), e(labels["col_sales"]),
               e(labels["col_gross"]), e(labels["col_refund"]),
               e(labels["col_refunded"]), e(labels["col_net"]),
               e(labels["col_bar"]), e(labels["col_devnet"]),
               e(labels["col_platnet"]), e(labels["col_buyers"]),
               e(labels["col_sellers"]), e(labels["col_listings"]),
               "".join(row_html)))
    if not row_html:
        rows = "<p>%s</p>" % e(labels["top_none"])
    zero_note = labels["zero_note"] % fmt(env["zero_day_count"], none)

    extremes = [
        (labels["busiest"], fmt(env["busiest_day"], none)),
        (labels["quietest"], fmt(env["quietest_active_day"], none)),
        (labels["avg"], fmt(env["avg_net_per_active_day"], none)),
    ]
    extremes_html = "".join("<div><span>%s</span><b>%s</b></div>"
                            % (e(k), e(v)) for k, v in extremes)
    laws = "".join("<li>%s</li>" % e(labels["law%d" % (i + 1)])
                   for i in range(7))

    head = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n<div class=card>%s<p class=weak>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n<div class=card><ol class=laws>%s</ol></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        "<p style=\"margin-top:10px\"><span class=badge>%s</span></p></div>\n"
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/market_daily_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_days"]), rows, e(zero_note),
           e(labels["sec_extremes"]), extremes_html,
           e(labels["sec_laws"]), laws,
           e(labels["sec_disc"]), DISCLAIMER_SLOT,
           e(labels["aigc"]), e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    # The disclaimer is the face's own sentence, injected after assembly so its
    # text is never retyped here.
    return head.replace(DISCLAIMER_SLOT, e(env["disclaimer"] or ""))


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
    """AC-PWC54 (R3576): landing this pair and re-deriving the CEO face are ONE run.

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
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("MARKET-DAILY CHECK %s fails=%d html=%dB json=%dB"
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

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, labels, now)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "day_count": env["day_count"],
        "active_day_count": env["active_day_count"],
        "zero_day_count": env["zero_day_count"],
        "window_start": env["window_start"],
        "window_end": env["window_end"],
        "lifetime_sales_count": env["lifetime_sales_count"],
        "lifetime_gross": env["lifetime_gross"],
        "lifetime_refund_count": env["lifetime_refund_count"],
        "lifetime_refunded": env["lifetime_refunded"],
        "lifetime_net": env["lifetime_net"],
        "lifetime_dev_revenue": env["lifetime_dev_revenue"],
        "lifetime_platform_revenue": env["lifetime_platform_revenue"],
        "busiest_day": env["busiest_day"],
        "quietest_active_day": env["quietest_active_day"],
        "avg_net_per_active_day": env["avg_net_per_active_day"],
        "days": env["days"],
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
    face = _refresh_face(args.out, args.json)

    print("MARKET-DAILY %s bytes=%d days=%d active=%d zero=%d net=%s "
          "busiest=%s face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             env["day_count"], env["active_day_count"],
             env["zero_day_count"], fmt(env["lifetime_net"], "-"),
             env["busiest_day"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
