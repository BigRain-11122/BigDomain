"""Market-wide monthly provider-identity redeclaration board (R3453).

WHY THIS PAGE EXISTS (measured at R3453, not assumed):
api_market_provider_months shipped the market's monthly real-name timeline - a
registration booked in the UTC month of its own registered_utc, a revision in
the month of its own revised_utc, a contiguous grid with honest zero rows, a
redeclaration rate that answers None in a month with no identity event, the
distinct-account split (one seller can carry several events) and one monotone
revision accumulator - but a search over tools/, preview/ and src/os answered
zero readers for its name. api_provider_identity answers one developer's
published pair, api_provider_history answers one developer's revision rows and
api_public_listings prints the identity per live shelf, so "how often is the
shop front being re-declared, and is it churning faster this quarter" could
only be read by walking every developer by hand. This page opens the axis the
face already carries; it adds no table, no reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-PMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3453 PIN row landed with the
driver and says so):
  - month_count == len(months) and the rows are one contiguous grid
  - per row: event_count == registration_count + revision_count and
    redeclaration_rate is revision / event rounded to four places, or None
    (never a fabricated zero) when the month carried no identity event
  - per row: seller_count <= event_count, redeclared_seller_count <=
    seller_count and redeclared_seller_count <= revision_count, because one
    developer that registers once and revises twice inside one month is ONE
    seller and THREE events
  - per row: running_revision replays monotonically from the first month and
    the last row equals the envelope revision total, so a later revision never
    rewrites the month a registration landed in
  - envelope registration and revision totals equal the row sums, event total
    is their sum, and avg_revisions_per_redeclared_seller is
    revision_total / redeclared_seller_count rounded to four places or None
    when nobody redeclared
  - the peak names the FIRST row carrying the maximum positive revision count
    and answers None when nothing was revised
  - first_month / last_month are the grid ends, and the bare (unseeded) world
    answers month_count 0 with every derived number None or zero

Every number on the page comes from the shipped face. Chinese labels live in
preview/market-provider-months-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "market-provider-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "market-provider-months-board.json")
COPY = os.path.join(ROOT, "preview", "market-provider-months-board-copy.json")

FACE = "api_market_provider_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
)

ENVELOPE_KEYS = (
    "month_count", "registration_count", "revision_count", "event_count",
    "seller_count", "redeclared_seller_count",
    "avg_revisions_per_redeclared_seller", "peak_revision_month",
    "peak_revision_count", "first_month", "last_month", "latest_event_utc",
    "months", "disclaimer",
)

MONTH_KEYS = ("month", "registration_count", "revision_count", "event_count",
              "seller_count", "redeclared_seller_count",
              "redeclaration_rate", "running_revision")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_months", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_first", "kpi_last", "kpi_reg", "kpi_rev",
    "kpi_events", "kpi_sellers", "kpi_redeclared", "kpi_avg",
    "kpi_peak_month", "kpi_peak_count", "kpi_latest",
    "col_month", "col_state", "col_reg", "col_rev", "col_events",
    "col_sellers", "col_redeclared", "col_rate", "col_running", "col_bar",
    "badge_zero", "badge_register", "badge_revision", "badge_mixed",
    "empty", "none", "bar_caption",
    "law_grid", "law_events", "law_rate", "law_subset", "law_carry",
    "law_sums", "law_avg", "law_peak", "law_ends", "law_distinct",
    "law_zero", "law_bar", "law_empty", "law_notadvice",
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
    code = "E_PMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_PMB_LAW"


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
    """One landed real-name timeline, every row by door.

    The factory world carries no provider registration at all, so every row
    below is made through the shipped register_provider and revise_provider
    doors under the pinned clock. The story exercises the laws on purpose: one
    developer registers in June (the pure registration month), July adds the
    second registration and TWO revisions by the first developer (the mixed
    month at a 0.6667 rate), August is one revision, September carries THREE
    revisions by ONE developer (the distinct-account law: three events, one
    seller), October is the honest zero row and November carries two revisions
    by two developers.
    """
    STAMP["value"] = "2026-06-05T00:00:00Z"
    am.register_provider("usr:dana", "DANA Studio", "91350100MA1111111A")
    STAMP["value"] = "2026-07-10T00:00:00Z"
    am.register_provider("usr:frank", "Frank Works", "91350100MA2222222B")
    STAMP["value"] = "2026-07-18T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="DANA Studio East")
    STAMP["value"] = "2026-07-26T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 2")
    STAMP["value"] = "2026-08-09T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="DANA Studio East 2")
    STAMP["value"] = "2026-09-04T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 3")
    STAMP["value"] = "2026-09-15T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 4")
    STAMP["value"] = "2026-09-27T00:00:00Z"
    am.revise_provider("usr:frank", credit_code="91350100MA2222222C")
    STAMP["value"] = "2026-11-06T00:00:00Z"
    am.revise_provider("usr:dana", credit_code="91350100MA1111111C")
    STAMP["value"] = "2026-11-21T00:00:00Z"
    am.revise_provider("usr:frank", provider_name="Frank Works 5")


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="pmb-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "pmb.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        envelope = dict(am.api_market_provider_months())
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
    tmp_root = tempfile.mkdtemp(prefix="pmb-empty-")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "bare.db"))
        envelope = dict(am.api_market_provider_months())
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


def _ratio(revision, events):
    return round(revision / float(events), 4) if events else None


def check_laws(envelope, empty):
    """AC-PMB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("month_count %r != %d rows"
                        % (envelope.get("month_count"), len(rows)))
    previous = None
    run_revision = 0
    sum_reg = 0
    sum_rev = 0
    for row in rows:
        month = row["month"]
        if previous is not None and \
                _month_index(month) - _month_index(previous) != 1:
            problems.append("rows not contiguous at %s" % month)
        previous = month
        reg = int(row["registration_count"])
        rev = int(row["revision_count"])
        events = int(row["event_count"])
        if events != reg + rev:
            problems.append("row %s events %r != %d + %d"
                            % (month, row["event_count"], reg, rev))
        if row["redeclaration_rate"] != _ratio(rev, events):
            problems.append("row %s rate %r != %r"
                            % (month, row["redeclaration_rate"],
                               _ratio(rev, events)))
        sellers = int(row["seller_count"])
        redeclared = int(row["redeclared_seller_count"])
        if sellers > events:
            problems.append("row %s sellers %r > events %d"
                            % (month, row["seller_count"], events))
        if redeclared > sellers:
            problems.append("row %s redeclared %r > sellers %d"
                            % (month, row["redeclared_seller_count"],
                               sellers))
        if redeclared > rev:
            problems.append("row %s redeclared %r > revisions %d"
                            % (month, row["redeclared_seller_count"], rev))
        run_revision += rev
        if int(row["running_revision"]) != run_revision:
            problems.append("row %s running_revision %r != %d"
                            % (month, row["running_revision"], run_revision))
        sum_reg += reg
        sum_rev += rev
    if int(envelope.get("registration_count", -1)) != sum_reg:
        problems.append("registration total %r != row sum %d"
                        % (envelope.get("registration_count"), sum_reg))
    if int(envelope.get("revision_count", -1)) != sum_rev:
        problems.append("revision total %r != row sum %d"
                        % (envelope.get("revision_count"), sum_rev))
    if int(envelope.get("event_count", -1)) != sum_reg + sum_rev:
        problems.append("event total %r != %d + %d"
                        % (envelope.get("event_count"), sum_reg, sum_rev))
    if rows:
        if int(rows[-1]["running_revision"]) != sum_rev:
            problems.append("last running_revision %r != %d"
                            % (rows[-1]["running_revision"], sum_rev))
    redeclared_total = int(envelope.get("redeclared_seller_count", 0))
    avg = envelope.get("avg_revisions_per_redeclared_seller")
    wanted_avg = (round(sum_rev / float(redeclared_total), 4)
                  if redeclared_total else None)
    if avg != wanted_avg:
        problems.append("avg %r != %r" % (avg, wanted_avg))
    if int(envelope.get("seller_count", 0)) > sum_reg + sum_rev:
        problems.append("seller total %r > events %d"
                        % (envelope.get("seller_count"), sum_reg + sum_rev))
    peak_month = None
    peak_count = None
    for row in rows:
        rev = int(row["revision_count"])
        if rev > 0 and (peak_count is None or rev > peak_count):
            peak_month = row["month"]
            peak_count = rev
    if envelope.get("peak_revision_month") != peak_month:
        problems.append("peak month %r != %r"
                        % (envelope.get("peak_revision_month"), peak_month))
    if envelope.get("peak_revision_count") != peak_count:
        problems.append("peak count %r != %r"
                        % (envelope.get("peak_revision_count"), peak_count))
    first = rows[0]["month"] if rows else None
    last = rows[-1]["month"] if rows else None
    if envelope.get("first_month") != first:
        problems.append("first month %r != %r"
                        % (envelope.get("first_month"), first))
    if envelope.get("last_month") != last:
        problems.append("last month %r != %r"
                        % (envelope.get("last_month"), last))
    if rows and not envelope.get("latest_event_utc"):
        problems.append("landed rows but latest_event_utc is empty")
    if not rows and envelope.get("latest_event_utc") is not None:
        problems.append("bare latest_event_utc %r is not None"
                        % (envelope.get("latest_event_utc"),))
    # The bare world must answer the honest empty envelope.
    if empty.get("months"):
        problems.append("bare world answered %d month rows"
                        % len(empty.get("months")))
    for key in ("month_count", "registration_count", "revision_count",
                "event_count", "seller_count", "redeclared_seller_count"):
        if int(empty.get(key, -1)) != 0:
            problems.append("bare %s %r != 0" % (key, empty.get(key)))
    for key in ("avg_revisions_per_redeclared_seller", "peak_revision_month",
                "peak_revision_count", "first_month", "last_month",
                "latest_event_utc"):
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
        (labels["kpi_reg"], envelope.get("registration_count")),
        (labels["kpi_rev"], envelope.get("revision_count")),
        (labels["kpi_events"], envelope.get("event_count")),
        (labels["kpi_sellers"], envelope.get("seller_count")),
        (labels["kpi_redeclared"],
         envelope.get("redeclared_seller_count")),
        (labels["kpi_avg"],
         envelope.get("avg_revisions_per_redeclared_seller")),
        (labels["kpi_peak_month"], envelope.get("peak_revision_month")),
        (labels["kpi_peak_count"], envelope.get("peak_revision_count")),
        (labels["kpi_latest"], envelope.get("latest_event_utc")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def badge_of(row, labels, e):
    reg = int(row["registration_count"])
    rev = int(row["revision_count"])
    if reg == 0 and rev == 0:
        return ('<span class="badge">%s</span>'
                % e(labels["badge_zero"]), True)
    if reg > 0 and rev == 0:
        return ('<span class="badge on">%s</span>'
                % e(labels["badge_register"]), False)
    if reg == 0 and rev > 0:
        return ('<span class="badge off">%s</span>'
                % e(labels["badge_revision"]), False)
    return ('<span class="badge warn">%s</span>'
            % e(labels["badge_mixed"]), False)


def month_table(envelope, labels, e, dash):
    rows = envelope.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("peak_revision_count") or 0
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name not in (labels["col_month"],
                                                   labels["col_state"])
                      else "", e(name))
                   for name in (labels["col_month"], labels["col_state"],
                                labels["col_reg"], labels["col_rev"],
                                labels["col_events"], labels["col_sellers"],
                                labels["col_redeclared"], labels["col_rate"],
                                labels["col_running"], labels["col_bar"]))
    body = []
    for row in rows:
        badge, quiet = badge_of(row, labels, e)
        rev = int(row["revision_count"])
        if not peak or rev <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, rev / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-month="%s"%s><td>%s</td><td>%s</td>%s<td>%s</td></tr>'
            % (e(str(row["month"])), ' class="quiet-row"' if quiet else "",
               e(str(row["month"])), badge,
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("registration_count", "revision_count",
                                   "event_count", "seller_count",
                                   "redeclared_seller_count",
                                   "redeclaration_rate", "running_revision")),
               bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_grid"], labels["law_events"], labels["law_rate"],
            labels["law_subset"], labels["law_carry"], labels["law_sums"],
            labels["law_avg"], labels["law_peak"], labels["law_ends"],
            labels["law_distinct"], labels["law_zero"], labels["law_bar"],
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
    """AC-PWC60 (R3582): landing this pair and re-deriving the CEO face are ONE run.

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
        print("MARKET-PROVIDER-MONTHS CHECK %s fails=%d html=%dB json=%dB"
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

    face = _refresh_face(args.out, args.json)
    print("MARKET-PROVIDER-MONTHS %s bytes=%d months=%d reg=%d rev=%d "
          "events=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             int(envelope["month_count"]), int(envelope["registration_count"]),
             int(envelope["revision_count"]), int(envelope["event_count"]),
             face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
