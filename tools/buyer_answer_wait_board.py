"""Buyer monthly answer-wait board (R3449).

WHY THIS PAGE EXISTS (measured at R3449, not assumed):
api_buyer_answer_wait shipped ONE buyer's answer timeline - how many
pre-purchase questions were answered each month, how many of those discharged
an older month's backlog, the running lifetime count and the per-month fastest,
mean and slowest wait - but a search over tools/, preview/ and src/os answered
rc=1 for its name. api_buyer_questions merges every question of one buyer into
a lifetime timeline, api_seller_answer_months covers the SELLER side of the
same Q&A and the rating-reply cadence page covers POST-purchase ratings, so a
buyer answered within minutes all spring and ignored all summer read exactly
like one that never got an answer. This page opens the timeline the face
already carries; it adds no table, no reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-BAWB3, fixed in this round's window
before the first render; the src/os/backlog.md R3449 PIN row states plainly
that it landed in the same window as the driver):
  - month_count == len(months)
  - the month rows are one contiguous grid: each month is exactly one month
    after the previous one, so a month with no answer carries an honest zero row
  - every row backlog_count + same_month_count == answered_count
  - every row seller_count and listing_count is a distinct count, so a row
    never names more sellers or listings than it has answers
  - an active row carries fastest <= mean <= slowest and a zero row carries no
    latency at all (None, never a fabricated 0)
  - running_answered rises by exactly the row's answered_count and its last
    value is the envelope answered_count
  - envelope answered_count and backlog_answered_count equal the row sums
  - active_month_count is the number of rows with an answer, first_month and
    last_month are the grid ends, latest_month_answered_count is the last row
  - peak_month is the FIRST row carrying the maximum positive count and is None
    when nothing was answered
  - envelope fastest / slowest are the row extremes, the envelope mean sits
    inside that band, and a single active month reads its own mean
  - a buyer with no question answers month_count 0, an empty grid, zero totals,
    no named month and three empty latencies, while the asked-side envelope
    counts every question including still-open ones

Every number on the page comes from the shipped face. Chinese labels live in
preview/buyer-answer-wait-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "buyer-answer-wait-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-answer-wait-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-answer-wait-copy.json")

FACE = "api_buyer_answer_wait"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "buyers", "disclaimer", "report",
    "sources", "sizes",
)

ENVELOPE_KEYS = (
    "buyer_id", "scope", "question_count", "answered_count",
    "unanswered_count", "answer_rate", "seller_count", "listing_count",
    "backlog_answered_count", "month_count", "active_month_count",
    "peak_month", "peak_answered_count", "first_month", "last_month",
    "latest_month_answered_count", "fastest_seconds", "slowest_seconds",
    "mean_seconds", "disclaimer", "months",
)

MONTH_KEYS = ("month", "answered_count", "backlog_count", "same_month_count",
              "seller_count", "listing_count", "fastest_seconds",
              "slowest_seconds", "mean_seconds", "running_answered")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "scope_buyer",
    "kpi_months", "kpi_asked", "kpi_answered", "kpi_unanswered", "kpi_rate",
    "kpi_backlog", "kpi_same", "kpi_sellers", "kpi_listings", "kpi_active",
    "kpi_peak", "kpi_peak_count", "kpi_latest", "kpi_fastest", "kpi_mean",
    "kpi_slowest",
    "col_month", "col_answered", "col_backlog", "col_same", "col_sellers",
    "col_listings", "col_fastest", "col_mean", "col_slowest", "col_running",
    "col_bar",
    "badge_active", "badge_zero",
    "empty", "none", "bar_caption",
    "law_grid", "law_booking", "law_split", "law_latency", "law_running",
    "law_sum", "law_peak", "law_void", "law_scope", "law_bar",
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
    code = "E_BAWB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_BAWB_LAW"


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
    """One landed answer timeline across two buyers, every row by door.

    The factory world carries no question and no answer, so every row here is
    made through the shipped ask_question / answer_question doors under the
    pinned clock. bob gets one same-month answer in September, goes silent
    through the whole of October (the honest zero row) while an older question
    waits, then has two questions discharged in November - one of them a
    September question, so November is pure backlog. cy is a second buyer whose
    single October question is answered inside October, and ghost never asks,
    which is the face's own empty envelope.
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

    STAMP["value"] = "2026-09-03T00:00:00Z"
    q1 = am.ask_question("usr:bob", risk, "does the scan cover A-share")[
        "question_id"]
    STAMP["value"] = "2026-09-03T06:00:07Z"
    am.answer_question("usr:dana", q1, "yes, A-share and ETF")
    STAMP["value"] = "2026-09-05T00:00:00Z"
    q2 = am.ask_question("usr:bob", macro,
                         "how fresh is the daily feed")["question_id"]
    STAMP["value"] = "2026-09-09T00:00:00Z"
    q3 = am.ask_question("usr:bob", risk,
                         "is there a rate limit")["question_id"]
    STAMP["value"] = "2026-10-04T00:00:00Z"
    q4 = am.ask_question("usr:bob", chart,
                         "is the render 4k")["question_id"]
    STAMP["value"] = "2026-10-04T01:00:00Z"
    q_cy = am.ask_question("usr:cy", macro,
                           "which feed powers the macro shelf")["question_id"]
    STAMP["value"] = "2026-10-04T02:00:00Z"
    am.answer_question("usr:dana", q_cy, "an in-house settlement feed")
    STAMP["value"] = "2026-11-10T00:00:00Z"
    am.answer_question("usr:dana", q2, "published at 06:00 UTC daily")
    STAMP["value"] = "2026-11-12T00:00:00Z"
    am.answer_question("usr:frank", q4, "yes, 4k on request")
    STAMP["value"] = "2026-11-15T00:00:00Z"
    am.ask_question("usr:bob", chart, "can I get a sample render")

    return ["usr:bob", "usr:cy"]


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="bawb-")
    db = os.path.join(tmp_root, "bawb.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        buyers = build_world(am)
        envelopes = [{"buyer": name,
                      "envelope": dict(am.api_buyer_answer_wait(name))}
                     for name in buyers]
        empty_scope = dict(am.api_buyer_answer_wait("usr:ghost"))
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
    row_answered = 0
    row_backlog = 0
    active = 0
    row_fastest = []
    row_slowest = []
    row_means = []
    for row in rows:
        answered = int(row["answered_count"])
        backlog = int(row["backlog_count"])
        same = int(row["same_month_count"])
        if backlog + same != answered:
            problems.append("%s row %s split %d + %d != %d"
                            % (tag, row["month"], backlog, same, answered))
        if int(row["seller_count"]) > answered:
            problems.append("%s row %s names more sellers than answers"
                            % (tag, row["month"]))
        if int(row["listing_count"]) > answered:
            problems.append("%s row %s names more listings than answers"
                            % (tag, row["month"]))
        running += answered
        if int(row["running_answered"]) != running:
            problems.append("%s row %s running %r != %d"
                            % (tag, row["month"], row["running_answered"],
                               running))
        if previous is not None and (
                _month_index(row["month"]) - _month_index(previous) != 1):
            problems.append("%s rows not contiguous at %s"
                            % (tag, row["month"]))
        previous = row["month"]
        if answered > 0:
            active += 1
            fast = row["fastest_seconds"]
            mean = row["mean_seconds"]
            slow = row["slowest_seconds"]
            if fast is None or mean is None or slow is None:
                problems.append("%s row %s answers but hides a latency"
                                % (tag, row["month"]))
            else:
                if not (int(fast) <= int(mean) <= int(slow)):
                    problems.append("%s row %s latency order %r/%r/%r"
                                    % (tag, row["month"], fast, mean, slow))
                row_fastest.append(int(fast))
                row_slowest.append(int(slow))
                row_means.append(int(mean))
        else:
            for key in ("fastest_seconds", "mean_seconds", "slowest_seconds"):
                if row[key] is not None:
                    problems.append("%s row %s zero answers but %s=%r"
                                    % (tag, row["month"], key, row[key]))
        row_answered += answered
        row_backlog += backlog
    if int(envelope.get("answered_count", -1)) != row_answered:
        problems.append("%s answered total %r != row sum %d"
                        % (tag, envelope.get("answered_count"), row_answered))
    if int(envelope.get("backlog_answered_count", -1)) != row_backlog:
        problems.append("%s backlog total %r != row sum %d"
                        % (tag, envelope.get("backlog_answered_count"),
                           row_backlog))
    if int(envelope.get("active_month_count", -1)) != active:
        problems.append("%s active months %r != %d"
                        % (tag, envelope.get("active_month_count"), active))
    if running != int(envelope.get("answered_count", -1)):
        problems.append("%s running %d != answered total %r"
                        % (tag, running, envelope.get("answered_count")))
    first = rows[0]["month"] if rows else None
    last = rows[-1]["month"] if rows else None
    if envelope.get("first_month") != first:
        problems.append("%s first %r != %r"
                        % (tag, envelope.get("first_month"), first))
    if envelope.get("last_month") != last:
        problems.append("%s last %r != %r"
                        % (tag, envelope.get("last_month"), last))
    latest = int(rows[-1]["answered_count"]) if rows else 0
    if int(envelope.get("latest_month_answered_count", -1)) != latest:
        problems.append("%s latest %r != %d"
                        % (tag, envelope.get("latest_month_answered_count"),
                           latest))
    peak = None
    peak_count = None
    for row in rows:
        if int(row["answered_count"]) > 0 and (
                peak_count is None
                or int(row["answered_count"]) > peak_count):
            peak = row["month"]
            peak_count = int(row["answered_count"])
    if envelope.get("peak_month") != peak:
        problems.append("%s peak %r != %r"
                        % (tag, envelope.get("peak_month"), peak))
    if envelope.get("peak_answered_count") != peak_count:
        problems.append("%s peak count %r != %r"
                        % (tag, envelope.get("peak_answered_count"),
                           peak_count))
    fastest = min(row_fastest) if row_fastest else None
    slowest = max(row_slowest) if row_slowest else None
    if envelope.get("fastest_seconds") != fastest:
        problems.append("%s fastest %r != %r"
                        % (tag, envelope.get("fastest_seconds"), fastest))
    if envelope.get("slowest_seconds") != slowest:
        problems.append("%s slowest %r != %r"
                        % (tag, envelope.get("slowest_seconds"), slowest))
    mean = envelope.get("mean_seconds")
    if fastest is None:
        if mean is not None:
            problems.append("%s empty latencies but mean %r" % (tag, mean))
    else:
        if mean is None or not (fastest <= int(mean) <= slowest):
            problems.append("%s mean %r outside %d..%d"
                            % (tag, mean, fastest, slowest))
        elif len(row_means) == 1 and int(mean) != row_means[0]:
            problems.append("%s single month mean %r != %d"
                            % (tag, mean, row_means[0]))
    asked = int(envelope.get("question_count", -1))
    answered = int(envelope.get("answered_count", -1))
    unanswered = int(envelope.get("unanswered_count", -1))
    if answered + unanswered != asked:
        problems.append("%s answered %d + unanswered %d != asked %d"
                        % (tag, answered, unanswered, asked))
    rate = envelope.get("answer_rate")
    if asked > 0:
        if rate is None or abs(float(rate) - round(
                answered / float(asked), 4)) > 1e-9:
            problems.append("%s answer rate %r != %d/%d"
                            % (tag, rate, answered, asked))
    elif rate is not None:
        problems.append("%s no question but rate %r" % (tag, rate))
    if row_answered == 0:
        for key in ("answered_count", "backlog_answered_count", "seller_count",
                    "listing_count", "active_month_count", "question_count"):
            if int(envelope.get(key, -1)) != 0:
                problems.append("%s no answers but %s=%r"
                                % (tag, key, envelope.get(key)))
        for key in ("peak_month", "first_month", "last_month",
                    "fastest_seconds", "slowest_seconds", "mean_seconds"):
            if envelope.get(key) is not None:
                problems.append("%s no answers but names %s=%r"
                                % (tag, key, envelope.get(key)))
    return problems


def check_laws(envelopes, empty_scope):
    """AC-BAWB3 read at the source: refuse rather than print."""
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
    answered = int(envelope.get("answered_count") or 0)
    backlog = int(envelope.get("backlog_answered_count") or 0)
    items = [
        (labels["kpi_months"], envelope.get("month_count")),
        (labels["kpi_asked"], envelope.get("question_count")),
        (labels["kpi_answered"], envelope.get("answered_count")),
        (labels["kpi_unanswered"], envelope.get("unanswered_count")),
        (labels["kpi_rate"], envelope.get("answer_rate")),
        (labels["kpi_backlog"], envelope.get("backlog_answered_count")),
        (labels["kpi_same"], answered - backlog),
        (labels["kpi_sellers"], envelope.get("seller_count")),
        (labels["kpi_listings"], envelope.get("listing_count")),
        (labels["kpi_active"], envelope.get("active_month_count")),
        (labels["kpi_peak"], envelope.get("peak_month")),
        (labels["kpi_peak_count"], envelope.get("peak_answered_count")),
        (labels["kpi_latest"],
         envelope.get("latest_month_answered_count")),
        (labels["kpi_fastest"], envelope.get("fastest_seconds")),
        (labels["kpi_mean"], envelope.get("mean_seconds")),
        (labels["kpi_slowest"], envelope.get("slowest_seconds")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def month_table(envelope, labels, e, dash):
    rows = envelope.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("peak_answered_count") or 0
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_month"] else "",
                      e(name))
                   for name in (labels["col_month"], labels["col_answered"],
                                labels["col_backlog"], labels["col_same"],
                                labels["col_sellers"], labels["col_listings"],
                                labels["col_fastest"], labels["col_mean"],
                                labels["col_slowest"], labels["col_running"],
                                labels["col_bar"]))
    body = []
    for row in rows:
        answered = int(row["answered_count"])
        quiet = answered == 0
        if not peak or answered <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, answered / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        if quiet:
            badge = '<span class="badge">%s</span>' % e(labels["badge_zero"])
        else:
            badge = '<span class="badge on">%s</span>' % e(
                labels["badge_active"])
        body.append(
            '<tr data-month="%s"%s><td>%s</td>%s<td>%s</td><td>%s</td></tr>'
            % (e(str(row["month"])), ' class="quiet-row"' if quiet else "",
               e(str(row["month"])),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("answered_count", "backlog_count",
                                   "same_month_count", "seller_count",
                                   "listing_count", "fastest_seconds",
                                   "mean_seconds", "slowest_seconds",
                                   "running_answered")),
               badge, bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def scope_card(envelope, labels, e, dash, heading, tag):
    answered = envelope.get("answered_count")
    badge = ""
    if answered is not None:
        badge = ' <span class=badge>%s %s</span>' % (
            e(labels["kpi_answered"]), e(text(answered, dash)))
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
    laws = [labels["law_grid"], labels["law_booking"], labels["law_split"],
            labels["law_latency"], labels["law_running"], labels["law_sum"],
            labels["law_peak"], labels["law_void"], labels["law_scope"],
            labels["law_bar"], labels["law_notadvice"]]
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
        print("BUYER-ANSWER-WAIT CHECK %s fails=%d html=%dB json=%dB"
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

    print("BUYER-ANSWER-WAIT %s bytes=%d buyers=%d months=%d answered=%d"
          % (payload["report"], len(doc.encode("utf-8")), len(envelopes),
             sum(int(item["envelope"]["month_count"]) for item in envelopes),
             sum(int(item["envelope"]["answered_count"])
                 for item in envelopes)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
