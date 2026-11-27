"""Buyer repurchase-rhythm and dormancy board (R3446).

WHY THIS PAGE EXISTS (measured at R3446, not assumed):
api_buyer_gap_months shipped the rhythm of ONE resident - how many months
passed between two net purchases of the same account, how long the longest
silence ran, and how many months sit dormant inside the observed extent - but a
search over tools/, preview/ and src/os answered rc=1 for its name. The market
already had monthly spend (api_buyer_months), repeat purchase
(api_repeat_purchase) and a retention curve (api_market_buyer_retention), so a
loyal repurchaser and a sleeping account read the same on every live face.
This page opens the rhythm the face already carries; it adds no table, no
reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-BGMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3446 PIN row landed before any
driver code):
  - gap_count == len(gaps) == max(0, activity_month_count - 1)
  - every row span_months == gap_months + 1 and gap_months >= 0
  - rows join head to tail; first from == first_activity_month and the last
    to == last_activity_month
  - dormant_months_total == the gap sum
  - avg_gap_months == sum / count within 1e-9
  - median_gap_months == the sorted median within 1e-9
  - max_gap_months == the largest gap, longest_from/to name the first row
    reaching it
  - trailing_dormant_months == month_index(as_of) - month_index(last activity)
    whenever activity exists
  - a zero-activity buyer answers empty derived fields and no rows; a
    single-month buyer answers gap_count 0 while its trailing dormancy may
    still be non-zero

Every number on the page comes from the shipped face. Chinese labels live in
preview/buyer-gap-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "buyer-gap-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-gap-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-gap-board-copy.json")

FACE = "api_buyer_gap_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "as_of_month", "buyers", "disclaimer",
    "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "buyer_id", "activity_month_count", "purchase_count",
    "first_activity_month", "last_activity_month", "gap_count",
    "dormant_months_total", "avg_gap_months", "median_gap_months",
    "max_gap_months", "longest_from_month", "longest_to_month", "as_of_month",
    "trailing_dormant_months", "disclaimer", "gaps",
)

GAP_KEYS = ("from_month", "to_month", "span_months", "gap_months")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "scope_buyer", "as_of_label", "kpi_activity", "kpi_purchases",
    "kpi_gaps", "kpi_dormant", "kpi_avg", "kpi_median", "kpi_max",
    "kpi_longest_from", "kpi_longest_to", "kpi_first", "kpi_last",
    "kpi_trailing",
    "col_from", "col_to", "col_span", "col_gap", "col_bar",
    "badge_zero", "badge_unbroken", "badge_gap",
    "empty", "none", "single", "bar_caption", "trailing_label",
    "law_gapcount", "law_span", "law_chain", "law_sum", "law_avg",
    "law_median", "law_max", "law_trailing", "law_net", "law_bar",
    "law_empty", "law_notadvice",
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

AS_OF = "2026-12"

# One pinned clock drives every write so the month buckets reproduce.
STAMP = {"value": "2026-09-05T00:00:00Z"}


class FaceError(Exception):
    code = "E_BGMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_BGMB_LAW"


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
    """One landed rhythm across four buyers, every row through a shipped door.

    The factory world already carries bob's September macro-feed purchase,
    carol's September risk-scan purchase and erin's fully refunded chart-render
    purchase, so only the additional months are written here: bob buys the
    chart-render shelf in June (one three-month span, gap 2), carol buys in
    October and November (back-to-back months, gap 0), dave buys once in
    November (no gap at all) and erin keeps only a refunded purchase, which is
    not an activity month. as_of is pinned at 2026-12, after every last
    activity, so carol and dave carry a real trailing dormancy while bob reads
    0.
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
    am.purchase_api("usr:bob", chart, "r3446-a")
    STAMP["value"] = "2026-10-05T00:00:00Z"
    am.purchase_api("usr:carol", macro, "r3446-b")
    STAMP["value"] = "2026-11-05T00:00:00Z"
    am.purchase_api("usr:carol", chart, "r3446-c")
    STAMP["value"] = "2026-11-12T00:00:00Z"
    am.purchase_api("usr:dave", macro, "r3446-d")

    return ["usr:bob", "usr:carol", "usr:dave", "usr:erin"], {
        "risk": risk, "macro": macro, "chart": chart}


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="bgmb-")
    db = os.path.join(tmp_root, "bgmb.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        buyers, _shelves = build_world(am)
        envelopes = [{"buyer": name,
                      "envelope": dict(am.api_buyer_gap_months(name, AS_OF))}
                     for name in buyers]
        empty_scope = dict(am.api_buyer_gap_months("usr:ghost", AS_OF))
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


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _envelope_problems(tag, envelope, problems):
    rows = envelope.get("gaps") or []
    activity = int(envelope.get("activity_month_count", -1))
    gap_count = int(envelope.get("gap_count", -1))
    if gap_count != len(rows):
        problems.append("%s gap_count %d != %d rows"
                        % (tag, gap_count, len(rows)))
    if gap_count != max(0, activity - 1):
        problems.append("%s gap_count %d != activity %d - 1"
                        % (tag, gap_count, activity))
    values = []
    previous = None
    for row in rows:
        span = int(row["span_months"])
        gap = int(row["gap_months"])
        if span != gap + 1 or gap < 0:
            problems.append("%s row %s->%s span %d gap %d"
                            % (tag, row["from_month"], row["to_month"],
                               span, gap))
        if previous is not None and row["from_month"] != previous:
            problems.append("%s rows do not join at %s"
                            % (tag, row["from_month"]))
        previous = row["to_month"]
        values.append(gap)
    if rows:
        if rows[0]["from_month"] != envelope.get("first_activity_month"):
            problems.append("%s first row does not start the extent" % tag)
        if rows[-1]["to_month"] != envelope.get("last_activity_month"):
            problems.append("%s last row does not end the extent" % tag)
    if int(envelope.get("dormant_months_total", -1)) != sum(values):
        problems.append("%s dormant total %r != gap sum %d"
                        % (tag, envelope.get("dormant_months_total"),
                           sum(values)))
    if values:
        want_avg = sum(values) / float(len(values))
        got_avg = envelope.get("avg_gap_months")
        if got_avg is None or abs(float(got_avg) - want_avg) > 1e-9:
            problems.append("%s avg %r != %r" % (tag, got_avg, want_avg))
        want_median = _median(values)
        got_median = envelope.get("median_gap_months")
        if got_median is None or abs(float(got_median) - want_median) > 1e-9:
            problems.append("%s median %r != %r"
                            % (tag, got_median, want_median))
        want_max = max(values)
        if int(envelope.get("max_gap_months", -2)) != want_max:
            problems.append("%s max %r != %d"
                            % (tag, envelope.get("max_gap_months"), want_max))
        first_max = None
        for row in rows:
            if int(row["gap_months"]) == want_max:
                first_max = row
                break
        if first_max is not None and (
                envelope.get("longest_from_month") != first_max["from_month"]
                or envelope.get("longest_to_month") != first_max["to_month"]):
            problems.append("%s longest pair does not name the first max row"
                            % tag)
    else:
        for key in ("avg_gap_months", "median_gap_months", "max_gap_months",
                    "longest_from_month", "longest_to_month"):
            if envelope.get(key) is not None:
                problems.append("%s no-gap buyer fabricates %s" % (tag, key))
    last = envelope.get("last_activity_month")
    as_of = envelope.get("as_of_month")
    if last and as_of:
        want = _month_index(as_of) - _month_index(last)
        if want < 0:
            problems.append("%s as_of precedes last activity" % tag)
        elif envelope.get("trailing_dormant_months") != want:
            problems.append("%s trailing %r != %d"
                            % (tag, envelope.get("trailing_dormant_months"),
                               want))
    elif not last and envelope.get("trailing_dormant_months") is not None:
        problems.append("%s zero-activity buyer fabricates a trailing dormancy"
                        % tag)
    if not last:
        for key in ("first_activity_month", "first_activity_month"):
            if envelope.get(key) is not None:
                problems.append("%s zero-activity buyer names %s"
                                % (tag, key))
    return problems


def check_laws(envelopes, empty_scope):
    """AC-BGMB3 read at the source: refuse rather than print."""
    problems = []
    for item in envelopes:
        problems = _envelope_problems("buyer %s" % item["buyer"],
                                      item["envelope"], problems)
    if int(empty_scope.get("activity_month_count", -1)) != 0:
        problems.append("empty scope answers %r activity months"
                        % empty_scope.get("activity_month_count"))
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
        (labels["kpi_activity"], envelope.get("activity_month_count")),
        (labels["kpi_purchases"], envelope.get("purchase_count")),
        (labels["kpi_gaps"], envelope.get("gap_count")),
        (labels["kpi_dormant"], envelope.get("dormant_months_total")),
        (labels["kpi_avg"], envelope.get("avg_gap_months")),
        (labels["kpi_median"], envelope.get("median_gap_months")),
        (labels["kpi_max"], envelope.get("max_gap_months")),
        (labels["kpi_longest_from"], envelope.get("longest_from_month")),
        (labels["kpi_longest_to"], envelope.get("longest_to_month")),
        (labels["kpi_first"], envelope.get("first_activity_month")),
        (labels["kpi_last"], envelope.get("last_activity_month")),
        (labels["kpi_trailing"], envelope.get("trailing_dormant_months")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def gap_table(envelope, labels, e, dash):
    rows = envelope.get("gaps") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("max_gap_months")
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_from"] else "",
                      e(name))
                   for name in (labels["col_from"], labels["col_to"],
                                labels["col_span"], labels["col_gap"],
                                labels["col_bar"]))
    body = []
    for row in rows:
        gap = int(row["gap_months"])
        if gap <= 0:
            badge = '<span class="badge on">%s</span>' % e(
                labels["badge_unbroken"])
        else:
            badge = '<span class="badge off">%s</span>' % e(
                labels["badge_gap"])
        if not peak or gap <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, gap / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-gap="%s..%s"%s><td>%s</td>%s<td>%s</td><td>%s</td></tr>'
            % (e(str(row["from_month"])), e(str(row["to_month"])),
               ' class="quiet-row"' if gap <= 0 else "",
               e(str(row["from_month"])),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("from_month", "to_month", "span_months",
                                   "gap_months")),
               badge, bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def scope_card(envelope, labels, e, dash, heading, tag):
    trailing = envelope.get("trailing_dormant_months")
    badge = ""
    if trailing is not None:
        badge = ' <span class=badge>%s %s</span>' % (
            e(labels["trailing_label"]), e(text(trailing, dash)))
    if int(envelope.get("activity_month_count") or 0) == 0:
        quiet = "<p class=empty>%s</p>" % e(labels["empty"])
    elif int(envelope.get("gap_count") or 0) == 0:
        quiet = "<p class=cap>%s</p>" % e(labels["single"])
    else:
        quiet = ""
    return (
        '<div class=card data-buyer="%s">\n<h3>%s%s</h3>\n'
        "<div class=kpi>%s</div>\n%s\n%s</div>\n"
        % (e(tag), e(heading), badge,
           kpi_html(envelope, labels, e, dash),
           gap_table(envelope, labels, e, dash), quiet)
    )


def build_html(envelopes, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_gapcount"], labels["law_span"], labels["law_chain"],
            labels["law_sum"], labels["law_avg"], labels["law_median"],
            labels["law_max"], labels["law_trailing"], labels["law_net"],
            labels["law_bar"], labels["law_empty"], labels["law_notadvice"]]
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
        '<div class=meta>%s &middot; %s %s &middot; %s %s &middot; '
        "<code>%s</code></div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(labels["as_of_label"]), e(AS_OF),
           FACE,
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
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "gaps"}
    doc["gaps"] = [{key: row[key] for key in GAP_KEYS}
                   for row in envelope.get("gaps") or []]
    return doc


def payload_of(envelopes, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "buyer",
        "as_of_month": AS_OF,
        "buyers": [{"buyer": item["buyer"],
                    "envelope": trim_envelope(item["envelope"])}
                   for item in envelopes],
        "disclaimer": disclaimer,
        "report": os.path.relpath(path, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }


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
    """AC-PWC39 (R3561): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: both halves are
    already on disk when this runs, so the caller's exit code stays its own.
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
        print("BUYER-GAP CHECK %s fails=%d html=%dB json=%dB"
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

    face = _refresh_face(args.out, args.json)

    print("BUYER-GAP %s bytes=%d buyers=%d gaps=%d dormant=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")), len(envelopes),
             sum(int(item["envelope"]["gap_count"]) for item in envelopes),
             sum(int(item["envelope"]["dormant_months_total"])
                 for item in envelopes), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
