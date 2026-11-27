"""Per-category monthly pre-sale question board (R3451).

WHY THIS PAGE EXISTS (measured at R3451, not assumed):
api_category_question_months shipped the market's pre-sale pressure BY CATEGORY
on a monthly axis - a question booked in the UTC month it was asked and in the
category in force at that instant, the answered leg credited back to the ASKING
month and bucket, a contiguous month grid with honest zero rows and a monotone
per-category accumulator - but a search over tools/, preview/ and src/os
answered zero readers for its name. The whole-market, per-seller, per-buyer and
per-shelf question faces all had pages, so a bucket drowning in questions read
exactly like a quiet one once the per-row lines were added up by hand.
This page opens the axis the face already carries; it adds no table, no reading
and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-CQMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3451 PIN row landed with the
driver and says so):
  - month_count == len(months) and the rows are one contiguous grid
  - cells are ordered by category ascending with the uncategorized bucket last
  - per row: the cell question counts sum to question_count, the cell answered
    counts sum to answered_count, unanswered_count == question_count minus
    answered_count and answer_rate is answered / question rounded to four
    places, or None when the month asked nothing
  - per cell: unanswered_count == question_count - answered_count, answer_rate
    follows the same law, and running_question is the monotone per-category
    lifetime accumulator, so an answer never rewrites an earlier month
  - the row running_question is the monotone lifetime total and the last row
    equals the envelope question_count
  - envelope totals equal the row sums, active_month_count counts the rows that
    asked something, category_count is the distinct categories in the window,
    peak_month names the FIRST row carrying the maximum positive question count
    and is None when nothing was asked
  - include_uncategorized=False drops the bucket from every cell and recomputes
    every aggregate without it, so the same book reads honestly under both
    scopes

Every number on the page comes from the shipped face. Chinese labels live in
preview/category-question-months-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "category-question-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "category-question-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-question-months-board-copy.json")

FACE = "api_category_question_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
)

ENVELOPE_KEYS = (
    "question_count", "answered_count", "unanswered_count", "answer_rate",
    "buyer_count", "seller_count", "listing_count", "category_count",
    "month_count", "active_month_count", "peak_month", "peak_question_count",
    "first_month", "last_month", "latest_month_question_count", "disclaimer",
    "months",
)

MONTH_KEYS = ("month", "question_count", "answered_count", "unanswered_count",
              "answer_rate", "category_count", "buyer_count", "seller_count",
              "listing_count", "running_question", "categories")

CELL_KEYS = ("category", "question_count", "answered_count",
             "unanswered_count", "answer_rate", "buyer_count", "seller_count",
             "listing_count", "running_question")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_months", "sec_cats", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_first", "kpi_last", "kpi_questions", "kpi_answered",
    "kpi_unanswered", "kpi_rate", "kpi_buyers", "kpi_sellers", "kpi_listings",
    "kpi_cats", "kpi_active", "kpi_peak", "kpi_peak_count", "kpi_latest",
    "kpi_running",
    "col_month", "col_questions", "col_answered", "col_unanswered",
    "col_rate", "col_cats", "col_buyers", "col_sellers", "col_listings",
    "col_running", "col_bar", "col_category", "col_scope",
    "badge_zero", "badge_full", "badge_open", "uncategorized",
    "empty", "none", "bar_caption",
    "law_grid", "law_cells", "law_carry", "law_order", "law_sums",
    "law_rate", "law_cats", "law_peak", "law_latest", "law_zero",
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
    code = "E_CQMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_CQMB_LAW"


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


def _qid(result):
    if isinstance(result, dict):
        return result["question_id"]
    return result


def build_world(am):
    """One landed pre-sale question timeline, every row by door.

    The factory world carries three listings and no question at all, so four
    categorized listings are published through the shipped publish_api door
    under the pinned clock, every question below is asked through the shipped
    ask_question door and every answer through the shipped answer_question door.
    The answering law is exercised on purpose: two questions asked in June are
    answered in July and September and both stay booked in the June row, a July
    question waits until November and still raises July, and August asks nothing
    at all so it carries the honest zero row.
    """
    STAMP["value"] = "2026-06-01T00:00:00Z"
    am.publish_api("usr:dana", "data-lens", "Data Lens",
                   "row counts for one table",
                   {"endpoint": "/rows/count", "rows": 1200}, 12, True,
                   category="data")
    am.publish_api("usr:dana", "data-digest", "Data Digest",
                   "weekly digest of new rows",
                   {"endpoint": "/rows/digest", "rows": 40}, 9, True,
                   category="data")
    am.publish_api("usr:frank", "tools-forge", "Tools Forge",
                   "batch rename helper",
                   {"endpoint": "/tools/rename", "batch": 200}, 7, True,
                   category="tools")
    am.publish_api("usr:frank", "tools-mint", "Tools Mint",
                   "csv to json converter",
                   {"endpoint": "/tools/mint", "batch": 100}, 5, True,
                   category="tools")

    board = am.api_board() or {}
    ids = {}
    owners = {}
    for row in board.get("listings") or []:
        key = str(row["listing_key"])
        ids[key] = int(row["listing_id"])
        owners[key] = str(row.get("dev_account"))
    for key in ("data-lens", "data-digest", "tools-forge", "tools-mint",
                "risk-scan"):
        if key not in ids:
            raise FaceError("shipped board lost %s" % key)

    STAMP["value"] = "2026-06-10T00:00:00Z"
    bob_june = _qid(am.ask_question("usr:bob", ids["data-lens"],
                                    "does this count one table only?"))
    carol_june = _qid(am.ask_question("usr:carol", ids["data-lens"],
                                      "is the count cached?"))
    STAMP["value"] = "2026-07-05T00:00:00Z"
    dave_july = _qid(am.ask_question("usr:dave", ids["tools-forge"],
                                     "does it keep file names?"))
    _qid(am.ask_question("usr:erin", ids["risk-scan"],
                         "which exchange does this read?"))
    STAMP["value"] = "2026-09-09T00:00:00Z"
    bob_sept = _qid(am.ask_question("usr:bob", ids["data-digest"],
                                    "how many rows per digest?"))
    carol_sept = _qid(am.ask_question("usr:carol", ids["tools-mint"],
                                      "can it read utf-8 csv?"))
    STAMP["value"] = "2026-10-12T00:00:00Z"
    _qid(am.ask_question("usr:dave", ids["data-lens"],
                         "does it follow schema changes?"))
    erin_oct = _qid(am.ask_question("usr:erin", ids["risk-scan"],
                                    "is the feed delayed?"))
    STAMP["value"] = "2026-11-06T00:00:00Z"
    _qid(am.ask_question("usr:bob", ids["tools-forge"],
                         "does it batch 500 files?"))

    # Answers land later than the asking month on purpose.
    STAMP["value"] = "2026-07-02T00:00:00Z"
    am.answer_question(owners["data-lens"], bob_june, "one table, yes")
    STAMP["value"] = "2026-07-06T00:00:00Z"
    am.answer_question(owners["tools-forge"], dave_july, "names are kept")
    STAMP["value"] = "2026-09-30T00:00:00Z"
    am.answer_question(owners["data-lens"], carol_june, "not cached")
    STAMP["value"] = "2026-10-01T00:00:00Z"
    am.answer_question(owners["data-digest"], bob_sept, "forty rows")
    STAMP["value"] = "2026-11-02T00:00:00Z"
    am.answer_question(owners["tools-mint"], carol_sept, "utf-8 only")
    STAMP["value"] = "2026-11-20T00:00:00Z"
    am.answer_question(owners["risk-scan"], erin_oct, "ten minute delay")


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="cqmb-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "cqmb.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        envelope = dict(am.api_category_question_months())
        empty = dict(am.api_category_question_months(
            include_uncategorized=False))
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
    return envelope, empty


def _month_index(label):
    return int(label[:4]) * 12 + int(label[5:7])


def _category_order(cells):
    names = [cell["category"] for cell in cells]
    keyed = sorted([name for name in names if name is not None])
    expected = keyed + ([None] if None in names else [])
    return names == expected


def _rate(answered, asked):
    return round(answered / float(asked), 4) if asked else None


def check_laws(envelope, no_uncat):
    """AC-CQMB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("month_count %r != %d rows"
                        % (envelope.get("month_count"), len(rows)))
    previous = None
    row_asked = 0
    row_answered = 0
    categories = set()
    running = {}
    running_total = 0
    active_rows = 0
    for row in rows:
        month = row["month"]
        if previous is not None and _month_index(month) - \
                _month_index(previous) != 1:
            problems.append("rows not contiguous at %s" % month)
        previous = month
        cells = row.get("categories") or []
        if not _category_order(cells):
            problems.append("row %s cells not ordered" % month)
        if int(row.get("category_count", -1)) != len(cells):
            problems.append("row %s category_count %r != %d cells"
                            % (month, row.get("category_count"), len(cells)))
        cell_asked = 0
        cell_answered = 0
        for cell in cells:
            category = cell["category"]
            categories.add(category)
            asked = int(cell["question_count"])
            answered = int(cell["answered_count"])
            if int(cell["unanswered_count"]) != asked - answered:
                problems.append("cell %s/%s unanswered %r != %d - %d"
                                % (month, category,
                                   cell["unanswered_count"], asked, answered))
            if cell["answer_rate"] != _rate(answered, asked):
                problems.append("cell %s/%s rate %r != %r"
                                % (month, category, cell["answer_rate"],
                                   _rate(answered, asked)))
            running[category] = running.get(category, 0) + asked
            if int(cell["running_question"]) != running[category]:
                problems.append("cell %s/%s running %r != replay %d"
                                % (month, category,
                                   cell["running_question"],
                                   running[category]))
            if int(cell["buyer_count"]) < 0 or int(cell["seller_count"]) < 0 \
                    or int(cell["listing_count"]) < 0:
                problems.append("cell %s/%s negative count"
                                % (month, category))
            cell_asked += asked
            cell_answered += answered
        if cell_asked != int(row["question_count"]):
            problems.append("row %s questions %r != cell sum %d"
                            % (month, row["question_count"], cell_asked))
        if cell_answered != int(row["answered_count"]):
            problems.append("row %s answered %r != cell sum %d"
                            % (month, row["answered_count"], cell_answered))
        if int(row["unanswered_count"]) != cell_asked - cell_answered:
            problems.append("row %s unanswered %r != %d - %d"
                            % (month, row["unanswered_count"], cell_asked,
                               cell_answered))
        if row["answer_rate"] != _rate(cell_answered, cell_asked):
            problems.append("row %s rate %r != %r"
                            % (month, row["answer_rate"],
                               _rate(cell_answered, cell_asked)))
        running_total += cell_asked
        if int(row["running_question"]) != running_total:
            problems.append("row %s running %r != %d"
                            % (month, row["running_question"], running_total))
        if cell_asked > 0:
            active_rows += 1
        row_asked += cell_asked
        row_answered += cell_answered
    if int(envelope.get("question_count", -1)) != row_asked:
        problems.append("question total %r != row sum %d"
                        % (envelope.get("question_count"), row_asked))
    if int(envelope.get("answered_count", -1)) != row_answered:
        problems.append("answered total %r != row sum %d"
                        % (envelope.get("answered_count"), row_answered))
    if int(envelope.get("unanswered_count", 0)) != row_asked - row_answered:
        problems.append("unanswered %r != %d - %d"
                        % (envelope.get("unanswered_count"), row_asked,
                           row_answered))
    if envelope.get("answer_rate") != _rate(row_answered, row_asked):
        problems.append("envelope rate %r != %r"
                        % (envelope.get("answer_rate"),
                           _rate(row_answered, row_asked)))
    if int(envelope.get("category_count", -1)) != len(categories):
        problems.append("category total %r != %d distinct"
                        % (envelope.get("category_count"), len(categories)))
    if int(envelope.get("active_month_count", -1)) != active_rows:
        problems.append("active months %r != %d"
                        % (envelope.get("active_month_count"), active_rows))
    peak_month = None
    peak_count = None
    for row in rows:
        asked = int(row["question_count"])
        if asked <= 0:
            continue
        if peak_count is None or asked > peak_count:
            peak_month = row["month"]
            peak_count = asked
    if envelope.get("peak_month") != peak_month:
        problems.append("peak month %r != %r"
                        % (envelope.get("peak_month"), peak_month))
    if envelope.get("peak_question_count") != peak_count:
        problems.append("peak count %r != %r"
                        % (envelope.get("peak_question_count"), peak_count))
    first = rows[0]["month"] if rows else None
    last = rows[-1]["month"] if rows else None
    if envelope.get("first_month") != first:
        problems.append("first month %r != %r"
                        % (envelope.get("first_month"), first))
    if envelope.get("last_month") != last:
        problems.append("last month %r != %r" % (envelope.get("last_month"),
                                                 last))
    latest = int(rows[-1]["question_count"]) if rows else 0
    if int(envelope.get("latest_month_question_count", -1)) != latest:
        problems.append("latest month questions %r != %d"
                        % (envelope.get("latest_month_question_count"),
                           latest))
    if int(envelope.get("buyer_count", -1)) < 0 \
            or int(envelope.get("seller_count", -1)) < 0 \
            or int(envelope.get("listing_count", -1)) < 0:
        problems.append("negative envelope count")
    uncat_asked = 0
    uncat_answered = 0
    for row in rows:
        for cell in row.get("categories") or []:
            if cell["category"] is None:
                uncat_asked += int(cell["question_count"])
                uncat_answered += int(cell["answered_count"])
    for row in no_uncat.get("months") or []:
        for cell in row.get("categories") or []:
            if cell["category"] is None:
                problems.append("flag-off probe still carries the bucket at %s"
                                % row["month"])
    if int(no_uncat.get("question_count", -1)) != row_asked - uncat_asked:
        problems.append("flag-off questions %r != %d - %d"
                        % (no_uncat.get("question_count"), row_asked,
                           uncat_asked))
    if int(no_uncat.get("answered_count", -1)) != \
            row_answered - uncat_answered:
        problems.append("flag-off answered %r != %d - %d"
                        % (no_uncat.get("answered_count"), row_answered,
                           uncat_answered))
    if int(no_uncat.get("category_count", -1)) != \
            len([name for name in categories if name is not None]):
        problems.append("flag-off categories %r"
                        % (no_uncat.get("category_count"),))
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
        (labels["kpi_questions"], envelope.get("question_count")),
        (labels["kpi_answered"], envelope.get("answered_count")),
        (labels["kpi_unanswered"], envelope.get("unanswered_count")),
        (labels["kpi_rate"], envelope.get("answer_rate")),
        (labels["kpi_buyers"], envelope.get("buyer_count")),
        (labels["kpi_sellers"], envelope.get("seller_count")),
        (labels["kpi_listings"], envelope.get("listing_count")),
        (labels["kpi_cats"], envelope.get("category_count")),
        (labels["kpi_active"], envelope.get("active_month_count")),
        (labels["kpi_peak"], envelope.get("peak_month")),
        (labels["kpi_peak_count"], envelope.get("peak_question_count")),
        (labels["kpi_latest"], envelope.get("latest_month_question_count")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def category_name(value, labels, e):
    if value is None:
        return e(labels["uncategorized"])
    return e(str(value))


def cell_token(value):
    """A stable attribute token, so an absent category never prints None."""
    return "uncategorized" if value is None else str(value)


def cell_table(row, labels, e, dash, peak):
    cells = row.get("categories") or []
    if not cells:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name not in (labels["col_category"],)
                      else "", e(name))
                   for name in (labels["col_category"], labels["col_questions"],
                                labels["col_answered"],
                                labels["col_unanswered"], labels["col_rate"],
                                labels["col_buyers"], labels["col_sellers"],
                                labels["col_listings"], labels["col_bar"]))
    body = []
    for cell in cells:
        asked = int(cell["question_count"])
        if not peak or asked <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, asked / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-category="%s"><td>%s</td>%s<td>%s</td></tr>'
            % (e(cell_token(cell["category"])),
               category_name(cell["category"], labels, e),
               "".join('<td class="n">%s</td>' % e(text(cell[key], dash))
                       for key in ("question_count", "answered_count",
                                   "unanswered_count", "answer_rate",
                                   "buyer_count", "seller_count",
                                   "listing_count")),
               bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def month_card(row, labels, e, dash, peak):
    asked = int(row["question_count"])
    if asked == 0:
        badge = '<span class="badge">%s</span>' % e(labels["badge_zero"])
        quiet = True
    elif int(row["unanswered_count"]) == 0:
        badge = '<span class="badge on">%s</span>' % e(labels["badge_full"])
        quiet = False
    else:
        badge = '<span class="badge off">%s</span>' % e(labels["badge_open"])
        quiet = False
    cells = row.get("categories") or []
    table = cell_table(row, labels, e, dash, peak)
    return (
        '<div class=card data-month="%s"%s>\n<h3>%s %s</h3>\n'
        "<div class=kpi>"
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        "</div>\n%s\n</div>\n"
        % (e(str(row["month"])), ' class="quiet-row"' if quiet else "",
           e(str(row["month"])), badge,
           e(labels["col_questions"]), e(text(row["question_count"], dash)),
           e(labels["col_answered"]), e(text(row["answered_count"], dash)),
           e(labels["col_unanswered"]), e(text(row["unanswered_count"], dash)),
           e(labels["col_rate"]), e(text(row["answer_rate"], dash)),
           e(labels["col_cats"]), e(text(len(cells), dash)),
           e(labels["kpi_running"]),
           e(text(row["running_question"], dash)),
           table))


def category_summary(envelope, labels, e, dash):
    """Sums of the face's own cells, never a new reading."""
    totals = {}
    for row in envelope.get("months") or []:
        for cell in row.get("categories") or []:
            slot = totals.setdefault(cell["category"], {
                "asked": 0, "answered": 0, "running": 0})
            slot["asked"] += int(cell["question_count"])
            slot["answered"] += int(cell["answered_count"])
            slot["running"] = int(cell["running_question"])
    if not totals:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    names = sorted([name for name in totals if name is not None])
    if None in totals:
        names.append(None)
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_scope"] else "",
                      e(name))
                   for name in (labels["col_scope"], labels["col_questions"],
                                labels["col_answered"],
                                labels["col_unanswered"], labels["col_rate"],
                                labels["col_running"]))
    body = []
    for name in names:
        slot = totals[name]
        unanswered = slot["asked"] - slot["answered"]
        body.append('<tr data-category="%s"><td>%s</td>%s</tr>'
                    % (e(cell_token(name)), category_name(name, labels, e),
                       "".join('<td class="n">%s</td>'
                               % e(text(value, dash))
                               for value in (slot["asked"],
                                             slot["answered"], unanswered,
                                             _rate(slot["answered"],
                                                   slot["asked"]),
                                             slot["running"]))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_grid"], labels["law_cells"], labels["law_carry"],
            labels["law_order"], labels["law_sums"], labels["law_rate"],
            labels["law_cats"], labels["law_peak"], labels["law_latest"],
            labels["law_zero"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    peak = envelope.get("peak_question_count") or 0
    months = "".join(month_card(row, labels, e, dash, peak)
                     for row in envelope.get("months") or [])
    if not months:
        months = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n%s\n"
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
           e(labels["sec_months"]), months,
           e(labels["sec_cats"]),
           category_summary(envelope, labels, e, dash),
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
    months = []
    for row in envelope.get("months") or []:
        item = {key: row[key] for key in MONTH_KEYS if key != "categories"}
        item["categories"] = [{key: cell[key] for key in CELL_KEYS}
                              for cell in row.get("categories") or []]
        months.append(item)
    doc["months"] = months
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
    """AC-PWC47 (R3569): landing this pair and re-deriving the CEO face are ONE run.

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
        print("CATEGORY-QUESTION-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelope, empty = read_world()
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

    print("CATEGORY-QUESTION-MONTHS %s bytes=%d months=%d asked=%d answered=%d "
          "cats=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             int(envelope["month_count"]), int(envelope["question_count"]),
             int(envelope["answered_count"]),
             int(envelope["category_count"]), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
