"""Buyer monthly watch-flow board (R3447).

WHY THIS PAGE EXISTS (measured at R3447, not assumed):
api_buyer_watch_months shipped ONE resident's attention timeline - how many
shelves they put on the watch list each month, how many they dropped, the
running live count at each month end, and how much of what they watched they
actually bought - but a search over tools/, preview/ and src/os answered rc=1
for its name. The market-wide and seller-wide watch axes already had pages, and
the buyer side carried a live snapshot and a lifetime funnel, so a resident
whose interest was heating up read exactly like one going cold.
This page opens the timeline the face already carries; it adds no table, no
reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-BWMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3447 PIN row landed before any
driver code):
  - month_count == len(months)
  - the month rows are one contiguous grid: each month is exactly one month
    after the previous one, so a month with no event carries an honest zero row
  - every row net_count == watch_count - unwatch_count and >= -watch_count
  - active_count is the running net over that grid and its last value is the
    envelope live_watch_count
  - envelope net_count == watch_count - unwatch_count == the sum of row nets
  - envelope converted_count == the sum of row conversions and no row ever
    converts more watches than it opened
  - every row listing_count and seller_count is a distinct-event count, so a
    row never reports more listings than it has watch + unwatch events
  - converted_month names the FIRST row carrying the maximum positive
    conversion, and is None when nothing converted
  - busiest_month names the FIRST row carrying the maximum positive watch
    count, and is None when nothing was watched
  - a buyer with no event answers month_count 0, an empty grid, zero totals
    and no named month

Every number on the page comes from the shipped face. Chinese labels live in
preview/buyer-watch-months-board-copy.json so this driver stays ASCII.
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

import apimarket as A  # noqa: E402
import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "buyer-watch-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-watch-months-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-watch-months-board-copy.json")

FACE = "api_buyer_watch_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "buyers", "disclaimer", "report",
    "sources", "sizes",
)

ENVELOPE_KEYS = (
    "scope", "buyer_id", "month_count", "watch_count", "unwatch_count",
    "net_count", "live_watch_count", "converted_count", "converted_month",
    "listing_count", "seller_count", "busiest_month", "busiest_watch_count",
    "months", "disclaimer",
)

MONTH_KEYS = ("month", "watch_count", "unwatch_count", "net_count",
              "active_count", "converted_count", "listing_count",
              "seller_count")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "scope_buyer", "kpi_months", "kpi_watches", "kpi_unwatch", "kpi_net",
    "kpi_live", "kpi_converted", "kpi_converted_month", "kpi_listings",
    "kpi_sellers", "kpi_busiest", "kpi_busiest_count",
    "col_month", "col_watch", "col_unwatch", "col_net", "col_active",
    "col_converted", "col_listings", "col_bar",
    "badge_live", "badge_closed", "badge_zero",
    "empty", "none", "bar_caption",
    "law_grid", "law_net", "law_running", "law_live", "law_sum",
    "law_conversion", "law_busiest", "law_converted_month", "law_zero",
    "law_bar", "law_notadvice",
    "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:16px 0 8px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 104px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:18px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.on{border-color:#9ad1a7;background:#eef9f1;color:#1f6b33}
.badge.off{border-color:#b9c7e4;background:#f1f4fd;color:#23388a}
.bar{position:relative;height:10px;min-width:120px;max-width:240px;
border:1px solid var(--line);border-radius:999px;background:#f2f4f7}
.bar i{position:absolute;top:-3px;width:3px;height:16px;background:#3c4653}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.quiet-row td{color:var(--muted)}
.cap{color:var(--muted);font-size:12px;margin:8px 0 0}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"

# One pinned clock drives every write so the month buckets reproduce.
STAMP = {"value": "2026-11-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_BWMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_BWMB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS
               if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def _clock():
    return STAMP["value"]


def build_world(am):
    """One landed attention timeline across four buyers, every row by door.

    The factory world carries zero watch rows, so every watch and unwatch here
    is made through the shipped watch_api / unwatch_api doors under the pinned
    clock. bob watches the macro-feed shelf in June and drops it in November,
    while his September purchase of that shelf converts the June watch. carol
    watches the chart-render shelf in October and buys it in November, then
    watches the risk-scan shelf; both watches stay live. dave watches and drops
    the risk-scan shelf inside November, so his net is an honest zero. erin
    keeps no watch at all, which is the face's own empty envelope.
    """
    board = am.api_board() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = row
    for key in ("risk-scan", "macro-feed", "chart-render"):
        if key not in by_key:
            raise FaceError("shipped board lost %s" % key)
    risk = int(by_key["risk-scan"]["listing_id"])
    macro = int(by_key["macro-feed"]["listing_id"])
    chart = int(by_key["chart-render"]["listing_id"])

    STAMP["value"] = "2026-06-10T00:00:00Z"
    am.watch_api("usr:bob", macro)
    STAMP["value"] = "2026-11-05T00:00:00Z"
    am.unwatch_api("usr:bob", macro)
    STAMP["value"] = "2026-10-05T00:00:00Z"
    am.watch_api("usr:carol", chart)
    STAMP["value"] = "2026-11-06T00:00:00Z"
    am.watch_api("usr:carol", risk)
    STAMP["value"] = "2026-11-07T00:00:00Z"
    am.purchase_api("usr:carol", chart, "r3447-a")
    STAMP["value"] = "2026-11-10T00:00:00Z"
    am.watch_api("usr:dave", risk)
    STAMP["value"] = "2026-11-11T00:00:00Z"
    am.unwatch_api("usr:dave", risk)

    return ["usr:bob", "usr:carol", "usr:dave", "usr:erin"], {
        "risk": risk, "macro": macro, "chart": chart}


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="bwmb-")
    db = os.path.join(tmp_root, "bwmb.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        buyers, _shelves = build_world(am)
        envelopes = [{"buyer": name,
                      "envelope": dict(am.api_buyer_watch_months(name))}
                     for name in buyers]
        empty_scope = dict(am.api_buyer_watch_months("usr:ghost"))
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    for item in envelopes:
        missing = [key for key in ENVELOPE_KEYS if key not in item["envelope"]]
        if missing:
            raise FaceError("envelope keys missing for %s: %s"
                            % (item["buyer"], ",".join(missing)))
    missing = [key for key in ENVELOPE_KEYS if key not in empty_scope]
    if missing:
        raise FaceError("empty envelope keys missing: %s" % ",".join(missing))
    return envelopes, empty_scope


def _month_index(label):
    return int(label[:4]) * 12 + int(label[5:7])


def _envelope_problems(tag, envelope, problems):
    rows = envelope.get("months") or []
    month_count = int(envelope.get("month_count", -1))
    if month_count != len(rows):
        problems.append("%s month_count %d != %d rows"
                        % (tag, month_count, len(rows)))
    previous = None
    running = 0
    row_watch = 0
    row_unwatch = 0
    row_converted = 0
    for row in rows:
        watch = int(row["watch_count"])
        unwatch = int(row["unwatch_count"])
        net = int(row["net_count"])
        if net != watch - unwatch:
            problems.append("%s row %s net %d != %d - %d"
                            % (tag, row["month"], net, watch, unwatch))
        if net > watch:
            problems.append("%s row %s nets more than it opened"
                            % (tag, row["month"]))
        running += net
        if running < 0:
            problems.append("%s row %s drives the live count negative"
                            % (tag, row["month"]))
        if int(row["active_count"]) != running:
            problems.append("%s row %s active %r != running %d"
                            % (tag, row["month"], row["active_count"],
                               running))
        if previous is not None and (
                _month_index(row["month"]) - _month_index(previous) != 1):
            problems.append("%s rows not contiguous at %s"
                            % (tag, row["month"]))
        previous = row["month"]
        if int(row["converted_count"]) > watch:
            problems.append("%s row %s converts more than it opened"
                            % (tag, row["month"]))
        if int(row["listing_count"]) > watch + unwatch:
            problems.append("%s row %s names more listings than events"
                            % (tag, row["month"]))
        if int(row["seller_count"]) > watch + unwatch:
            problems.append("%s row %s names more sellers than events"
                            % (tag, row["month"]))
        row_watch += watch
        row_unwatch += unwatch
        row_converted += int(row["converted_count"])
    if int(envelope.get("watch_count", -1)) != row_watch:
        problems.append("%s watch total %r != row sum %d"
                        % (tag, envelope.get("watch_count"), row_watch))
    if int(envelope.get("unwatch_count", -1)) != row_unwatch:
        problems.append("%s unwatch total %r != row sum %d"
                        % (tag, envelope.get("unwatch_count"), row_unwatch))
    if int(envelope.get("net_count", 0)) != row_watch - row_unwatch:
        problems.append("%s net %r != %d - %d"
                        % (tag, envelope.get("net_count"), row_watch,
                           row_unwatch))
    if int(envelope.get("live_watch_count", -1)) != running:
        problems.append("%s live %r != last running %d"
                        % (tag, envelope.get("live_watch_count"), running))
    if int(envelope.get("converted_count", -1)) != row_converted:
        problems.append("%s converted total %r != row sum %d"
                        % (tag, envelope.get("converted_count"),
                           row_converted))
    busiest = None
    busiest_count = None
    for row in rows:
        if int(row["watch_count"]) > 0 and (
                busiest_count is None
                or int(row["watch_count"]) > busiest_count):
            busiest = row["month"]
            busiest_count = int(row["watch_count"])
    if envelope.get("busiest_month") != busiest:
        problems.append("%s busiest %r != %r"
                        % (tag, envelope.get("busiest_month"), busiest))
    if envelope.get("busiest_watch_count") != busiest_count:
        problems.append("%s busiest count %r != %r"
                        % (tag, envelope.get("busiest_watch_count"),
                           busiest_count))
    converted = None
    converted_count = None
    for row in rows:
        if int(row["converted_count"]) > 0 and (
                converted_count is None
                or int(row["converted_count"]) > converted_count):
            converted = row["month"]
            converted_count = int(row["converted_count"])
    if envelope.get("converted_month") != converted:
        problems.append("%s converted month %r != %r"
                        % (tag, envelope.get("converted_month"), converted))
    if int(envelope.get("listing_count", -1)) < 0:
        problems.append("%s negative listing count" % tag)
    if int(envelope.get("seller_count", -1)) < 0:
        problems.append("%s negative seller count" % tag)
    if int(envelope.get("seller_count", -1)) > int(
            envelope.get("listing_count", -1)):
        problems.append("%s more sellers than listings" % tag)
    return problems


def check_laws(envelopes, empty_scope):
    """AC-BWMB3 read at the source: refuse rather than print."""
    problems = []
    for item in envelopes:
        problems = _envelope_problems("buyer %s" % item["buyer"],
                                      item["envelope"], problems)
    if int(empty_scope.get("month_count", -1)) != 0:
        problems.append("empty scope answers %r months"
                        % empty_scope.get("month_count"))
    if empty_scope.get("months"):
        problems.append("empty scope carries %d month rows"
                        % len(empty_scope.get("months") or []))
    for key in ("watch_count", "unwatch_count", "net_count",
                "live_watch_count", "converted_count"):
        if int(empty_scope.get(key, -1)) != 0:
            problems.append("empty scope fabricates %s=%r"
                            % (key, empty_scope.get(key)))
    for key in ("converted_month", "busiest_month"):
        if empty_scope.get(key) is not None:
            problems.append("empty scope names %s=%r"
                            % (key, empty_scope.get(key)))
    problems = _envelope_problems("empty scope", empty_scope, problems)
    return problems


def text(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return ("%.4f" % value).rstrip("0").rstrip(".")
    return str(value)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_months"], envelope.get("month_count")),
        (labels["kpi_watches"], envelope.get("watch_count")),
        (labels["kpi_unwatch"], envelope.get("unwatch_count")),
        (labels["kpi_net"], envelope.get("net_count")),
        (labels["kpi_live"], envelope.get("live_watch_count")),
        (labels["kpi_converted"], envelope.get("converted_count")),
        (labels["kpi_converted_month"], envelope.get("converted_month")),
        (labels["kpi_listings"], envelope.get("listing_count")),
        (labels["kpi_sellers"], envelope.get("seller_count")),
        (labels["kpi_busiest"], envelope.get("busiest_month")),
        (labels["kpi_busiest_count"], envelope.get("busiest_watch_count")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def month_table(envelope, labels, e, dash):
    rows = envelope.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("busiest_watch_count") or 0
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_month"] else "",
                      e(name))
                   for name in (labels["col_month"], labels["col_watch"],
                                labels["col_unwatch"], labels["col_net"],
                                labels["col_active"], labels["col_converted"],
                                labels["col_listings"], labels["col_bar"]))
    body = []
    for row in rows:
        watch = int(row["watch_count"])
        quiet = watch == 0 and int(row["unwatch_count"]) == 0
        if not peak or watch <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, watch / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        if int(row["active_count"]) > 0:
            badge = '<span class="badge on">%s</span>' % e(labels["badge_live"])
        elif quiet:
            badge = '<span class="badge">%s</span>' % e(labels["badge_zero"])
        else:
            badge = '<span class="badge off">%s</span>' % e(
                labels["badge_closed"])
        body.append(
            '<tr data-month="%s"%s><td>%s</td>%s<td>%s</td><td>%s</td></tr>'
            % (e(str(row["month"])), ' class="quiet-row"' if quiet else "",
               e(str(row["month"])),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("watch_count", "unwatch_count",
                                   "net_count", "active_count",
                                   "converted_count", "listing_count")),
               badge, bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def scope_card(envelope, labels, e, dash, heading, tag):
    live = envelope.get("live_watch_count")
    badge = ""
    if live is not None:
        badge = ' <span class=badge>%s %s</span>' % (
            e(labels["kpi_live"]), e(text(live, dash)))
    if int(envelope.get("month_count") or 0) == 0:
        quiet = "<p class=empty>%s</p>" % e(labels["empty"])
    else:
        quiet = ""
    return (
        '<div class=card data-buyer="%s">\n<h3>%s%s</h3>\n'
        "<div class=kpi>%s</div>\n%s\n%s</div>\n"
        % (e(tag), e(heading), badge,
           kpi_html(envelope, labels, e, dash),
           month_table(envelope, labels, e, dash), quiet)
    )


def build_html(envelopes, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_grid"], labels["law_net"], labels["law_running"],
            labels["law_live"], labels["law_sum"], labels["law_conversion"],
            labels["law_busiest"], labels["law_converted_month"],
            labels["law_zero"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    cards = "".join(
        scope_card(item["envelope"], labels, e, dash,
                   "%s %s" % (labels["scope_buyer"], item["buyer"]),
                   item["buyer"])
        for item in envelopes)
    if not cards:
        cards = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_buyers"]), cards,
           e(labels["sec_law"]), law_html, e(labels["bar_caption"]),
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
    if not os.path.exists(html_path):
        return ["html missing: %s" % html_path]
    if not os.path.exists(json_path):
        return ["json missing: %s" % json_path]
    with open(json_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    sizes = payload.get("sizes") or {}
    if sizes.get("html") != os.path.getsize(html_path):
        fails.append("json records html %r but disk answers %d"
                     % (sizes.get("html"), os.path.getsize(html_path)))
    if sizes.get("json") != os.path.getsize(json_path):
        fails.append("json records itself as %r but disk answers %d"
                     % (sizes.get("json"), os.path.getsize(json_path)))
    extra = sorted(set(payload) - set(PAYLOAD_KEYS))
    missing = sorted(set(PAYLOAD_KEYS) - set(payload))
    if extra or missing:
        fails.append("payload keys extra=%r missing=%r" % (extra, missing))
    return fails


def check_sources(json_path):
    fails = []
    if not os.path.exists(json_path):
        return ["json missing: %s" % json_path]
    with open(json_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    recorded = payload.get("sources") or {}
    if sorted(recorded) != ["apimarket", "copy", "driver", "report"]:
        fails.append("source keys %r" % sorted(recorded))
        return fails
    live = source_fingerprints()
    for key, value in live.items():
        if recorded.get(key) != value:
            fails.append("source %s moved: %r -> %r"
                         % (key, recorded.get(key), value))
    return fails


def trim_envelope(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in MONTH_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def payload_of(envelopes, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "buyer",
        "buyers": [{"buyer": item["buyer"],
                    "envelope": trim_envelope(item["envelope"])}
                   for item in envelopes],
        "disclaimer": disclaimer,
        "report": os.path.relpath(path, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }


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
        print("BUYER-WATCH-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelopes, empty_scope = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(envelopes, empty_scope)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = (envelopes[0]["envelope"].get("disclaimer")
                  if envelopes else empty_scope.get("disclaimer"))
    doc = build_html(envelopes, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(envelopes, args.out, disclaimer, now)
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

    print("BUYER-WATCH-MONTHS %s bytes=%d buyers=%d months=%d live=%d"
          % (payload["report"], len(doc.encode("utf-8")), len(envelopes),
             sum(int(item["envelope"]["month_count"]) for item in envelopes),
             sum(int(item["envelope"]["live_watch_count"])
                 for item in envelopes)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
