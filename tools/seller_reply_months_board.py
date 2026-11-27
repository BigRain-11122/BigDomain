"""Seller monthly rating-reply cadence board (R3445).

WHY THIS PAGE EXISTS (measured at R3445, not assumed):
api_seller_reply_months shipped the monthly rating-reply cadence - a reply
books in the UTC month of its own immutable replied_utc, a cross-month
discharge counts as backlog, and a silent month is an honest zero row - but a
search over tools/, preview/ and src/os answered rc=1 for its name. The reply
family already had a LIFETIME latency scorecard (api_rating_reply_latency), so
a shop that answered every rating within an hour last quarter and then went
silent this month read exactly like one that never answered at all. This page
opens the time axis the face already carries; it adds no table, no reading and
no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-SRPM3, fixed in this round's window
before the first render; the src/os/backlog.md R3445 PIN row landed before any
code):
  - rating_count == replied_count + unreplied_count
  - reply_coverage == round(replied / rating, 4) iff rating > 0 else None
  - month_count == len(months), contiguous grid, first/last month match rows
  - per row backlog_count + same_month_count == replied_count
  - per row fastest <= mean <= slowest, zero-reply month has None latencies
  - running_replied monotone, last value == envelope replied_count
  - envelope replied/backlog/same_month each equal the row sums
  - peak month is the earliest maximum
  - seller scopes carry the market mean, the market scope carries None
  - per-seller rating/replied/unreplied sums equal the market envelope

Every number on the page comes from the shipped face. Chinese labels live in
preview/seller-reply-months-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-reply-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-reply-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-reply-months-board-copy.json")

FACE = "api_seller_reply_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "market", "sellers", "disclaimer",
    "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "dev_account", "scope", "owned_listing_count", "market_mean_seconds",
    "rating_count", "replied_count", "unreplied_count", "reply_coverage",
    "backlog_reply_count", "same_month_reply_count", "buyer_count",
    "listing_count", "month_count", "active_month_count", "peak_month",
    "peak_replied_count", "first_month", "last_month",
    "latest_month_replied_count", "fastest_seconds", "slowest_seconds",
    "mean_seconds", "oldest_unreplied_utc", "months", "disclaimer",
)

ROW_KEYS = (
    "month", "replied_count", "backlog_count", "same_month_count",
    "buyer_count", "listing_count", "fastest_seconds", "slowest_seconds",
    "mean_seconds", "running_replied",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_sellers", "sec_law", "sec_disc", "sec_rep",
    "scope_market", "scope_seller", "dash_scope",
    "kpi_ratings", "kpi_replied", "kpi_unreplied", "kpi_coverage",
    "kpi_backlog", "kpi_same_month", "kpi_months", "kpi_active", "kpi_peak",
    "kpi_latest", "kpi_fastest", "kpi_slowest", "kpi_mean", "kpi_oldest",
    "kpi_bench",
    "col_month", "col_replied", "col_backlog", "col_same", "col_buyers",
    "col_listings", "col_fastest", "col_slowest", "col_mean", "col_run",
    "col_state", "col_bar",
    "badge_same", "badge_backlog", "badge_silent", "badge_mixed",
    "empty", "none", "bar_caption", "peak_label", "oldest_label",
    "bench_label",
    "law_sum", "law_coverage", "law_grid", "law_split", "law_latency",
    "law_running", "law_peak", "law_scope", "law_bar", "law_empty",
    "law_notadvice",
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
.badge.off{border-color:#e4b9b9;background:#fdf1f1;color:#8a2323}
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
STAMP = {"value": "2026-09-05T00:00:00Z"}


class FaceError(Exception):
    code = "E_SRPM_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_SRPM_LAW"


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
    """One landed story across three months, every row through a shipped door.

    2026-09: dana answers carol's September rating inside September, so the
    month books one same-month reply at its true short wait.
    2026-11: dave buys frank's shelf and rates it, and nobody answers - the
    live debt grows with a real stamp.  In the same month dana discharges
    bob's September rating, so November books one backlog reply carrying the
    real cross-month wait.
    2026-10 is therefore an honest zero row in the middle of the grid.
    """
    board = am.api_board() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = row
    for key in ("risk-scan", "macro-feed", "chart-render"):
        if key not in by_key:
            raise FaceError("shipped board lost %s" % key)
    dana = str(by_key["risk-scan"]["dev_account"])
    frank = str(by_key["chart-render"]["dev_account"])
    dana_1 = int(by_key["risk-scan"]["listing_id"])
    dana_2 = int(by_key["macro-feed"]["listing_id"])
    frank_3 = int(by_key["chart-render"]["listing_id"])

    STAMP["value"] = "2026-09-30T00:00:00Z"
    am.reply_to_rating(dana, 1, "yes it covers the tools we ship")

    STAMP["value"] = "2026-11-10T08:00:00Z"
    am.purchase_api("usr:dave", frank_3, "r3445")
    am.rate_api("usr:dave", frank_3, 5)

    STAMP["value"] = "2026-11-20T00:00:00Z"
    am.reply_to_rating(dana, 2, "thanks, glad it helped")

    return sorted({dana, frank}), {"dana_1": dana_1, "dana_2": dana_2,
                                   "frank_3": frank_3}


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="srpm-")
    db = os.path.join(tmp_root, "srpm.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        sellers, _shelves = build_world(am)
        market = dict(am.api_seller_reply_months())
        scoped = [{"seller": name,
                   "envelope": dict(am.api_seller_reply_months(name))}
                  for name in sellers]
        empty_scope = dict(am.api_seller_reply_months("usr:ghost"))
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
    missing = [key for key in ENVELOPE_KEYS if key not in market]
    if missing:
        raise FaceError("envelope keys missing: %s" % ",".join(missing))
    return market, scoped, empty_scope


def _next_month(label):
    year, month = int(label[:4]), int(label[5:7])
    month += 1
    if month > 12:
        month = 1
        year += 1
    return "%04d-%02d" % (year, month)


def _envelope_problems(tag, envelope, problems, market_mean):
    rows = envelope.get("months") or []
    rating = int(envelope.get("rating_count", -1))
    replied = int(envelope.get("replied_count", -1))
    unreplied = int(envelope.get("unreplied_count", -1))
    if rating != replied + unreplied:
        problems.append("%s rating %d != replied %d + unreplied %d"
                        % (tag, rating, replied, unreplied))
    coverage = envelope.get("reply_coverage")
    if rating > 0:
        want = round(replied / float(rating), 4)
        if coverage is None or abs(float(coverage) - want) > 1e-9:
            problems.append("%s coverage %r != %r" % (tag, coverage, want))
    elif coverage is not None:
        problems.append("%s coverage %r on zero ratings" % (tag, coverage))
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("%s month_count %s != %d rows"
                        % (tag, envelope.get("month_count"), len(rows)))
    if rows:
        if envelope.get("first_month") != rows[0]["month"]:
            problems.append("%s first_month does not match the first row" % tag)
        if envelope.get("last_month") != rows[-1]["month"]:
            problems.append("%s last_month does not match the last row" % tag)
        expect = rows[0]["month"]
        for row in rows:
            if row["month"] != expect:
                problems.append("%s month grid broke at %s"
                                % (tag, row["month"]))
            expect = _next_month(expect)
    running = []
    sums = {"replied_count": 0, "backlog_count": 0, "same_month_count": 0}
    # The row names the split counts without the _reply infix; the envelope
    # carries the same sums as backlog_reply_count / same_month_reply_count.
    envelope_names = {"replied_count": "replied_count",
                      "backlog_count": "backlog_reply_count",
                      "same_month_count": "same_month_reply_count"}
    for row in rows:
        row_replied = int(row["replied_count"])
        if int(row["backlog_count"]) + int(row["same_month_count"]) != row_replied:
            problems.append("%s %s split does not sum to replies"
                            % (tag, row["month"]))
        for key in sums:
            sums[key] += int(row[key])
        if row_replied > 0:
            fast = row["fastest_seconds"]
            mean = row["mean_seconds"]
            slow = row["slowest_seconds"]
            if fast is None or mean is None or slow is None:
                problems.append("%s %s replied month lost a latency"
                                % (tag, row["month"]))
            elif not (int(fast) <= int(mean) <= int(slow)):
                problems.append("%s %s latency order broken"
                                % (tag, row["month"]))
        else:
            for key in ("fastest_seconds", "mean_seconds", "slowest_seconds"):
                if row[key] is not None:
                    problems.append("%s %s zero month fabricates %s"
                                    % (tag, row["month"], key))
        running.append(int(row["running_replied"]))
    if running != sorted(running):
        problems.append("%s running accumulator is not monotone" % tag)
    if running and running[-1] != replied:
        problems.append("%s running ends at %d not %d"
                        % (tag, running[-1], replied))
    for key in sums:
        want = envelope.get(envelope_names[key], -2)
        if sums[key] != int(want if want is not None else -2):
            problems.append("%s row %s sum %d != envelope %s"
                            % (tag, key, sums[key], want))
    peak_month = envelope.get("peak_month")
    peak_count = envelope.get("peak_replied_count")
    if rows:
        best = max(int(row["replied_count"]) for row in rows)
        earliest = None
        for row in rows:
            if int(row["replied_count"]) == best:
                earliest = row["month"]
                break
        if best <= 0:
            if peak_month is not None or peak_count is not None:
                problems.append("%s peaks on a silent world" % tag)
        else:
            if peak_month != earliest or int(peak_count or -1) != best:
                problems.append("%s peak %r/%r != %r/%d"
                                % (tag, peak_month, peak_count, earliest, best))
    if envelope.get("latest_month_replied_count") != (
            rows[-1]["replied_count"] if rows else 0):
        problems.append("%s latest month count does not match the last row"
                        % tag)
    if envelope.get("scope") == "seller":
        if envelope.get("market_mean_seconds") != market_mean:
            problems.append("%s seller scope lost the market benchmark" % tag)
    elif envelope.get("market_mean_seconds") is not None:
        problems.append("%s market scope benchmarks itself" % tag)
    return problems


def check_laws(market, scoped, empty_scope):
    """AC-SRPM3 read at the source: refuse rather than print."""
    problems = []
    if market.get("scope") != "market":
        problems.append("market envelope scope %r" % market.get("scope"))
    market_mean = market.get("mean_seconds")
    problems = _envelope_problems("market", market, problems, market_mean)
    totals = {"rating_count": 0, "replied_count": 0, "unreplied_count": 0,
              "backlog_reply_count": 0, "same_month_reply_count": 0}
    for item in scoped:
        tag = "seller %s" % item["seller"]
        envelope = item["envelope"]
        if envelope.get("scope") != "seller":
            problems.append("%s scope %r" % (tag, envelope.get("scope")))
        if envelope.get("dev_account") != item["seller"]:
            problems.append("%s dev_account %r"
                            % (tag, envelope.get("dev_account")))
        problems = _envelope_problems(tag, envelope, problems, market_mean)
        for key in totals:
            totals[key] += int(envelope.get(key, 0))
    for key in totals:
        if totals[key] != int(market.get(key, -2)):
            problems.append("seller %s %d != market %s"
                            % (key, totals[key], market.get(key)))
    if int(empty_scope.get("month_count", -1)) != 0:
        problems.append("empty scope answers %r months"
                        % empty_scope.get("month_count"))
    if empty_scope.get("reply_coverage") is not None:
        problems.append("empty scope fabricates a coverage")
    if empty_scope.get("market_mean_seconds") != market_mean:
        problems.append("empty scope lost the market benchmark")
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
        (labels["kpi_ratings"], envelope.get("rating_count")),
        (labels["kpi_replied"], envelope.get("replied_count")),
        (labels["kpi_unreplied"], envelope.get("unreplied_count")),
        (labels["kpi_coverage"], envelope.get("reply_coverage")),
        (labels["kpi_backlog"], envelope.get("backlog_reply_count")),
        (labels["kpi_same_month"], envelope.get("same_month_reply_count")),
        (labels["kpi_months"], envelope.get("month_count")),
        (labels["kpi_active"], envelope.get("active_month_count")),
        (labels["kpi_peak"], envelope.get("peak_month")),
        (labels["kpi_latest"], envelope.get("latest_month_replied_count")),
        (labels["kpi_fastest"], envelope.get("fastest_seconds")),
        (labels["kpi_slowest"], envelope.get("slowest_seconds")),
        (labels["kpi_mean"], envelope.get("mean_seconds")),
        (labels["kpi_oldest"], envelope.get("oldest_unreplied_utc")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def month_table(envelope, labels, e, dash):
    rows = envelope.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("peak_replied_count")
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_month"] else "",
                      e(name))
                   for name in (labels["col_month"], labels["col_replied"],
                                labels["col_backlog"], labels["col_same"],
                                labels["col_buyers"], labels["col_listings"],
                                labels["col_fastest"], labels["col_slowest"],
                                labels["col_mean"], labels["col_run"],
                                labels["col_state"], labels["col_bar"]))
    body = []
    for row in rows:
        replied = int(row["replied_count"])
        backlog = int(row["backlog_count"])
        same = int(row["same_month_count"])
        if replied <= 0:
            state = '<span class="badge">%s</span>' % e(labels["badge_silent"])
        elif backlog > 0 and same > 0:
            state = ('<span class="badge on">%s</span>'
                     '<span class="badge off">%s</span>'
                     % (e(labels["badge_same"]), e(labels["badge_backlog"])))
        elif backlog > 0:
            state = '<span class="badge off">%s</span>' % e(
                labels["badge_backlog"])
        else:
            state = '<span class="badge on">%s</span>' % e(
                labels["badge_same"])
        if not peak or replied <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, replied / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-month="%s"%s><td>%s</td>%s<td>%s</td><td>%s</td></tr>'
            % (e(str(row["month"])),
               ' class="quiet-row"' if replied <= 0 else "",
               e(str(row["month"])),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("replied_count", "backlog_count",
                                   "same_month_count", "buyer_count",
                                   "listing_count", "fastest_seconds",
                                   "slowest_seconds", "mean_seconds",
                                   "running_replied")),
               state, bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def scope_card(envelope, labels, e, dash, heading, tag):
    bench = envelope.get("market_mean_seconds")
    badge = ""
    if bench is not None:
        badge = ' <span class=badge>%s %s</span>' % (
            e(labels["bench_label"]), e(text(bench, dash)))
    peak = envelope.get("peak_month")
    peak_html = ""
    if peak:
        peak_html = ' <span class=badge>%s %s</span>' % (
            e(labels["peak_label"]), e(str(peak)))
    oldest = envelope.get("oldest_unreplied_utc")
    oldest_html = ""
    if oldest:
        oldest_html = ' <span class=badge off>%s %s</span>' % (
            e(labels["oldest_label"]), e(str(oldest)))
    return (
        '<div class=card data-scope="%s">\n<h3>%s%s%s%s</h3>\n'
        "<div class=kpi>%s</div>\n%s\n</div>\n"
        % (e(tag), e(heading), peak_html, oldest_html, badge,
           kpi_html(envelope, labels, e, dash),
           month_table(envelope, labels, e, dash))
    )


def build_html(market, scoped, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_sum"], labels["law_coverage"], labels["law_grid"],
            labels["law_split"], labels["law_latency"], labels["law_running"],
            labels["law_peak"], labels["law_scope"], labels["law_bar"],
            labels["law_empty"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    seller_cards = "".join(
        scope_card(item["envelope"], labels, e, dash,
                   "%s %s" % (labels["scope_seller"], item["seller"]),
                   item["seller"])
        for item in scoped)
    if not seller_cards:
        seller_cards = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]),
           scope_card(market, labels, e, dash, labels["scope_market"],
                      "market"),
           e(labels["sec_sellers"]), seller_cards,
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
    """AC-PWC71 (R3593): landing this pair and re-deriving the CEO face are ONE run.

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


def trim_envelope(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in ROW_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def payload_of(market, scoped, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "market": trim_envelope(market),
        "sellers": [{"seller": item["seller"],
                     "envelope": trim_envelope(item["envelope"])}
                    for item in scoped],
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
        print("REPLY-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        market, scoped, empty_scope = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(market, scoped, empty_scope)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = market.get("disclaimer")
    doc = build_html(market, scoped, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(market, scoped, args.out, disclaimer, now)
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

    print("REPLY-MONTHS %s bytes=%d months=%d ratings=%d replied=%d "
          "unreplied=%d coverage=%r sellers=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             market["month_count"], market["rating_count"],
             market["replied_count"], market["unreplied_count"],
             market["reply_coverage"], len(payload["sellers"])))
    print("REPLY-MONTHS face=%s" % face)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
