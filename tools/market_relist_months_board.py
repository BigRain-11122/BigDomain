"""Market-wide monthly retirement / re-listing board (R3452).

WHY THIS PAGE EXISTS (measured at R3452, not assumed):
api_market_relist_months shipped the market's monthly retirement and return
timeline - a delisting booked in the UTC month of its own delisted_utc, a
re-listing in the month of its own relisted_utc, a contiguous grid with honest
zero rows, a same-month flow ratio that answers None in a pure-return month and
two monotone accumulators - but a search over tools/, preview/ and src/os
answered zero readers for its name. api_relist_gap answers one shelf's
retirement-to-return interval, api_listing_lifecycle answers raw event rows and
api_market_months answers cash, so a return-heavy delisting wave read exactly
like a normal seasonal rotation once the per-shelf lines were added up by hand.
This page opens the axis the face already carries; it adds no table, no reading
and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-MRMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3452 PIN row landed with the
driver and says so):
  - month_count == len(months) and the rows are one contiguous grid
  - per row: net_count == delist_count - relist_count and relist_rate is
    relist / delist rounded to four places, or None (never a fabricated zero)
    when the month retired nothing
  - per row: running_delist and running_relist replay monotonically from the
    first month, so a later return never rewrites the month a shelf left in
  - envelope totals equal the row sums, net_count is the difference of the two
    totals, relist_rate follows the same quotient law on the totals, and the
    last row accumulators equal those totals
  - active_month_count is not a face field here, so the page never invents it;
    peaks name the FIRST row carrying the maximum positive count and answer
    None when nothing happened, so an empty world reports None instead of
    inventing a month
  - first_month / last_month are the grid ends, and the bare (unseeded) world
    answers month_count 0 with every derived number None or zero

Every number on the page comes from the shipped face. Chinese labels live in
preview/market-relist-months-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "market-relist-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "market-relist-months-board.json")
COPY = os.path.join(ROOT, "preview", "market-relist-months-board-copy.json")

FACE = "api_market_relist_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
)

ENVELOPE_KEYS = (
    "month_count", "delist_count", "relist_count", "net_count", "relist_rate",
    "seller_count", "listing_count", "peak_delist_month",
    "peak_delist_count", "peak_relist_month", "peak_relist_count",
    "first_month", "last_month", "months", "disclaimer",
)

MONTH_KEYS = ("month", "delist_count", "relist_count", "net_count",
              "relist_rate", "seller_count", "listing_count",
              "running_delist", "running_relist")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_months", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_first", "kpi_last", "kpi_delist", "kpi_relist",
    "kpi_net", "kpi_rate", "kpi_sellers", "kpi_listings",
    "kpi_peak_delist", "kpi_peak_delist_count",
    "kpi_peak_relist", "kpi_peak_relist_count",
    "col_month", "col_delist", "col_relist", "col_net", "col_rate",
    "col_sellers", "col_listings", "col_running_delist",
    "col_running_relist", "col_bar", "col_state",
    "badge_zero", "badge_pure_return", "badge_net_down", "badge_mixed",
    "empty", "none", "bar_caption",
    "law_grid", "law_net", "law_rate", "law_carry", "law_sums",
    "law_peak", "law_ends", "law_zero", "law_bar", "law_empty",
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
.badge.warn{border-color:#e4c9b9;background:#fdf1ea;color:#8a4623}
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
    code = "E_MRMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_MRMB_LAW"


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
    """One landed retirement / return timeline, every row by door.

    The factory world carries three live shelves and no delisting at all, so
    every event below is made through the shipped delist_api and relist_api
    doors under the pinned clock. The story exercises the laws on purpose: one
    shelf retires and returns inside June (a same-month return, ratio 1.0),
    another retires in August and never returns, two shelves retire in
    September and both come back in November (a pure-return month whose ratio
    answers None), while July and October carry no event at all and therefore
    carry the honest zero rows.
    """
    board = am.api_board() or {}
    ids = {}
    owners = {}
    for row in board.get("listings") or []:
        key = str(row["listing_key"])
        ids[key] = int(row["listing_id"])
        owners[key] = str(row.get("dev_account"))
    for key in ("macro-feed", "chart-render", "risk-scan"):
        if key not in ids:
            raise FaceError("shipped board lost %s" % key)

    STAMP["value"] = "2026-06-08T00:00:00Z"
    am.delist_api(owners["macro-feed"], ids["macro-feed"])
    STAMP["value"] = "2026-06-20T00:00:00Z"
    am.relist_api(owners["macro-feed"], ids["macro-feed"])

    STAMP["value"] = "2026-08-05T00:00:00Z"
    am.delist_api(owners["chart-render"], ids["chart-render"])

    STAMP["value"] = "2026-09-12T00:00:00Z"
    am.delist_api(owners["macro-feed"], ids["macro-feed"])
    STAMP["value"] = "2026-09-25T00:00:00Z"
    am.delist_api(owners["risk-scan"], ids["risk-scan"])

    STAMP["value"] = "2026-11-03T00:00:00Z"
    am.relist_api(owners["macro-feed"], ids["macro-feed"])
    STAMP["value"] = "2026-11-18T00:00:00Z"
    am.relist_api(owners["risk-scan"], ids["risk-scan"])


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="mrmb-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "mrmb.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        envelope = dict(am.api_market_relist_months())
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
    missing = [key for key in ENVELOPE_KEYS if key not in envelope]
    if missing:
        raise FaceError("envelope keys missing: %s" % ",".join(missing))
    return envelope


def read_empty():
    """The bare stack answers the honest empty envelope; the page shows it."""
    tmp_root = tempfile.mkdtemp(prefix="mrmb-empty-")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "bare.db"))
        envelope = dict(am.api_market_relist_months())
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelope


def _month_index(label):
    return int(label[:4]) * 12 + int(label[5:7])


def _ratio(relist, delist):
    return round(relist / float(delist), 4) if delist else None


def check_laws(envelope, empty):
    """AC-MRMB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("month_count %r != %d rows"
                        % (envelope.get("month_count"), len(rows)))
    previous = None
    run_delist = 0
    run_relist = 0
    sum_delist = 0
    sum_relist = 0
    for row in rows:
        month = row["month"]
        if previous is not None and \
                _month_index(month) - _month_index(previous) != 1:
            problems.append("rows not contiguous at %s" % month)
        previous = month
        delist = int(row["delist_count"])
        relist = int(row["relist_count"])
        if int(row["net_count"]) != delist - relist:
            problems.append("row %s net %r != %d - %d"
                            % (month, row["net_count"], delist, relist))
        if row["relist_rate"] != _ratio(relist, delist):
            problems.append("row %s rate %r != %r"
                            % (month, row["relist_rate"],
                               _ratio(relist, delist)))
        if int(row["seller_count"]) < 0 or int(row["listing_count"]) < 0:
            problems.append("row %s negative participants" % month)
        if int(row["listing_count"]) > delist + relist:
            problems.append("row %s listings %r > events %d"
                            % (month, row["listing_count"], delist + relist))
        run_delist += delist
        run_relist += relist
        if int(row["running_delist"]) != run_delist:
            problems.append("row %s running_delist %r != %d"
                            % (month, row["running_delist"], run_delist))
        if int(row["running_relist"]) != run_relist:
            problems.append("row %s running_relist %r != %d"
                            % (month, row["running_relist"], run_relist))
        sum_delist += delist
        sum_relist += relist
    if int(envelope.get("delist_count", -1)) != sum_delist:
        problems.append("delist total %r != row sum %d"
                        % (envelope.get("delist_count"), sum_delist))
    if int(envelope.get("relist_count", -1)) != sum_relist:
        problems.append("relist total %r != row sum %d"
                        % (envelope.get("relist_count"), sum_relist))
    if int(envelope.get("net_count", 0)) != sum_delist - sum_relist:
        problems.append("net total %r != %d - %d"
                        % (envelope.get("net_count"), sum_delist,
                           sum_relist))
    if envelope.get("relist_rate") != _ratio(sum_relist, sum_delist):
        problems.append("envelope rate %r != %r"
                        % (envelope.get("relist_rate"),
                           _ratio(sum_relist, sum_delist)))
    if rows:
        if int(rows[-1]["running_delist"]) != sum_delist:
            problems.append("last running_delist %r != %d"
                            % (rows[-1]["running_delist"], sum_delist))
        if int(rows[-1]["running_relist"]) != sum_relist:
            problems.append("last running_relist %r != %d"
                            % (rows[-1]["running_relist"], sum_relist))
    peak_delist_month = None
    peak_delist_count = None
    peak_relist_month = None
    peak_relist_count = None
    for row in rows:
        delist = int(row["delist_count"])
        relist = int(row["relist_count"])
        if delist > 0 and (peak_delist_count is None
                           or delist > peak_delist_count):
            peak_delist_month = row["month"]
            peak_delist_count = delist
        if relist > 0 and (peak_relist_count is None
                           or relist > peak_relist_count):
            peak_relist_month = row["month"]
            peak_relist_count = relist
    if envelope.get("peak_delist_month") != peak_delist_month:
        problems.append("peak delist month %r != %r"
                        % (envelope.get("peak_delist_month"),
                           peak_delist_month))
    if envelope.get("peak_delist_count") != peak_delist_count:
        problems.append("peak delist count %r != %r"
                        % (envelope.get("peak_delist_count"),
                           peak_delist_count))
    if envelope.get("peak_relist_month") != peak_relist_month:
        problems.append("peak relist month %r != %r"
                        % (envelope.get("peak_relist_month"),
                           peak_relist_month))
    if envelope.get("peak_relist_count") != peak_relist_count:
        problems.append("peak relist count %r != %r"
                        % (envelope.get("peak_relist_count"),
                           peak_relist_count))
    first = rows[0]["month"] if rows else None
    last = rows[-1]["month"] if rows else None
    if envelope.get("first_month") != first:
        problems.append("first month %r != %r"
                        % (envelope.get("first_month"), first))
    if envelope.get("last_month") != last:
        problems.append("last month %r != %r"
                        % (envelope.get("last_month"), last))
    # The bare world must answer the honest empty envelope.
    if empty.get("months"):
        problems.append("bare world answered %d month rows"
                        % len(empty.get("months")))
    for key in ("month_count", "delist_count", "relist_count", "net_count",
                "seller_count", "listing_count"):
        if int(empty.get(key, -1)) != 0:
            problems.append("bare %s %r != 0" % (key, empty.get(key)))
    for key in ("relist_rate", "peak_delist_month", "peak_delist_count",
                "peak_relist_month", "peak_relist_count", "first_month",
                "last_month"):
        if empty.get(key) is not None:
            problems.append("bare %s %r is not None" % (key, empty.get(key)))
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
        (labels["kpi_first"], envelope.get("first_month")),
        (labels["kpi_last"], envelope.get("last_month")),
        (labels["kpi_delist"], envelope.get("delist_count")),
        (labels["kpi_relist"], envelope.get("relist_count")),
        (labels["kpi_net"], envelope.get("net_count")),
        (labels["kpi_rate"], envelope.get("relist_rate")),
        (labels["kpi_sellers"], envelope.get("seller_count")),
        (labels["kpi_listings"], envelope.get("listing_count")),
        (labels["kpi_peak_delist"], envelope.get("peak_delist_month")),
        (labels["kpi_peak_delist_count"],
         envelope.get("peak_delist_count")),
        (labels["kpi_peak_relist"], envelope.get("peak_relist_month")),
        (labels["kpi_peak_relist_count"],
         envelope.get("peak_relist_count")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def badge_of(row, labels, e):
    delist = int(row["delist_count"])
    relist = int(row["relist_count"])
    if delist == 0 and relist == 0:
        return ('<span class="badge">%s</span>'
                % e(labels["badge_zero"]), True)
    if delist == 0 and relist > 0:
        return ('<span class="badge on">%s</span>'
                % e(labels["badge_pure_return"]), False)
    if relist == 0 and delist > 0:
        return ('<span class="badge warn">%s</span>'
                % e(labels["badge_net_down"]), False)
    return '<span class="badge off">%s</span>' % e(labels["badge_mixed"]), \
        False


def month_table(envelope, labels, e, dash):
    rows = envelope.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("peak_delist_count") or 0
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_month"]
                      and name != labels["col_state"] else "", e(name))
                   for name in (labels["col_month"], labels["col_state"],
                                labels["col_delist"], labels["col_relist"],
                                labels["col_net"], labels["col_rate"],
                                labels["col_sellers"], labels["col_listings"],
                                labels["col_running_delist"],
                                labels["col_running_relist"],
                                labels["col_bar"]))
    body = []
    for row in rows:
        badge, quiet = badge_of(row, labels, e)
        delist = int(row["delist_count"])
        if not peak or delist <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, delist / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-month="%s"%s><td>%s</td><td>%s</td>%s<td>%s</td></tr>'
            % (e(str(row["month"])), ' class="quiet-row"' if quiet else "",
               e(str(row["month"])), badge,
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("delist_count", "relist_count",
                                   "net_count", "relist_rate",
                                   "seller_count", "listing_count",
                                   "running_delist", "running_relist")),
               bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_grid"], labels["law_net"], labels["law_rate"],
            labels["law_carry"], labels["law_sums"], labels["law_peak"],
            labels["law_ends"], labels["law_zero"], labels["law_bar"],
            labels["law_empty"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]), kpi_html(envelope, labels, e, dash),
           e(labels["sec_months"]),
           month_table(envelope, labels, e, dash),
           e(labels["bar_caption"]),
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


def payload_of(envelope, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "envelope": trim_envelope(envelope),
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
        print("MARKET-RELIST-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelope = read_world()
        empty = read_empty()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(envelope, empty)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = envelope.get("disclaimer")
    doc = build_html(envelope, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(envelope, args.out, disclaimer, now)
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

    print("MARKET-RELIST-MONTHS %s bytes=%d months=%d delist=%d relist=%d "
          "net=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             int(envelope["month_count"]), int(envelope["delist_count"]),
             int(envelope["relist_count"]), int(envelope["net_count"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
