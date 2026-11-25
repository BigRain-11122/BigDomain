"""Answer-revision board (R3456).

WHY THIS PAGE EXISTS (measured at R3456, not assumed):
api_answer_history shipped the per-answer revision face - the immutable base
wording, every append-only revision in order, the EFFECTIVE text and the
revision count, alongside the question the answer belongs to - but a search
over tools/, preview/ and src/os answered zero readers for its name.
api_seller_answers shows the current effective wording only and
api_listing_qna shows the effective text inside a thread, so "which answer was
rewritten, what did it say before, what does it say now and how often did it
change" could only be read by calling the sandbox from a shell. This page opens
the axis the face already carries; it adds no table, no reading and no business
semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-ARHB3, fixed in this round's window
before the first render; the src/os/backlog.md R3456 PIN row landed with the
driver and says so):
  - per answer revision_count == the number of revision rows
  - the chain is continuous: the first row's previous_text == the base answer,
    and every later row's previous_text == the previous row's answer_text
  - the effective text == the last row's answer_text, or the base answer when
    there is no revision at all
  - latest_revised_utc == the last row's revised_utc, or None (never a
    fabricated zero) when the answer was never revised
  - revision_id is strictly ascending inside every answer
  - an answer counts as reverted when it carries revisions and its effective
    text equals its base text (a legal revise-back, never a zero-row call)
  - the market answer count == the sum of the per-seller answered counts == the
    number of answer entries, and revised + unrevised == answer count
  - the market revision total == the sum of the per-answer revision counts
  - the most-revised answer is the one with the largest revision count, ties
    going to the smallest answer_id, and None when nothing was revised
  - a retired listing keeps its whole answer chain readable, and it still
    counts towards its seller
  - the bare world answers zero answers and zero revisions with every derived
    field empty, and a landed unrevised answer answers count 0 and a None
    stamp

Every number on the page comes from the shipped face. Chinese labels live in
preview/answer-revision-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "answer-revision-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "answer-revision-board.json")
COPY = os.path.join(ROOT, "preview", "answer-revision-board-copy.json")

FACE = "api_answer_history"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "market", "sellers", "answers",
    "disclaimer", "report", "sources", "sizes",
)

MARKET_KEYS = (
    "answer_count", "revised_answer_count", "unrevised_answer_count",
    "revision_count", "reverted_answer_count", "seller_count",
    "listing_count", "buyer_count", "latest_revised_utc",
    "most_revised_answer", "longest_chain",
)

SELLER_KEYS = ("dev_account", "answered_count", "revised_count",
               "revision_count", "latest_revised_utc")

ANSWER_KEYS = ("answer_id", "question_id", "listing_id", "listing_key",
               "dev_account", "buyer_id", "question_text", "base_text",
               "effective_text", "revision_count", "latest_revised_utc",
               "reverted", "retired", "rows")

ROW_KEYS = ("revision_id", "previous_text", "answer_text", "revised_utc")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_answers", "sec_law", "sec_disc", "sec_rep",
    "kpi_answers", "kpi_revised", "kpi_unrevised", "kpi_revisions",
    "kpi_reverted", "kpi_sellers", "kpi_listings", "kpi_buyers",
    "kpi_latest", "kpi_most", "kpi_longest",
    "col_seller", "col_answered", "col_revised", "col_revisions",
    "col_latest",
    "col_seq", "col_from", "col_to", "col_stamp",
    "kpi_chain", "badge_reverted", "badge_plain", "badge_retired",
    "base_label", "eff_label", "q_label",
    "empty", "none", "clip_caption", "clip_mark",
    "law_count", "law_chain", "law_effective", "law_stamp", "law_order",
    "law_reverted", "law_market", "law_most", "law_retired", "law_zero",
    "law_unrevised", "law_notadvice",
    "rep", "cmd",
)

CLIP = 80

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
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line);
vertical-align:top}
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
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.quiet-row td{color:var(--muted)}
.cap{color:var(--muted);font-size:12px;margin:8px 0 0}
.qa{font-size:12.5px;color:var(--muted);margin:0 0 6px}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"

# One pinned clock drives every write so the story reproduces.
STAMP = {"value": "2026-06-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_ARHB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_ARHB_LAW"


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
    """One landed revision story, every row by door.

    The factory world carries two published sellers and ZERO question, so every
    question, answer and revision below is made through the shipped ask_question,
    answer_question and revise_answer doors under the pinned clock - no sqlite
    rewrite, no typed ids, no padded rows. The story exercises the laws on
    purpose: an answer revised twice ending back on its base wording (a legal
    revise-back), an answer revised once and never returned, an answer on a
    shelf that is retired BEFORE its revision (retirement freezes the shelf, not
    the duty to answer), one answer never revised at all, and one question left
    open on purpose.
    """
    STAMP["value"] = "2026-06-01T00:00:00Z"
    ids = {row["listing_key"]: int(row["listing_id"])
           for row in (am.api_search(include_delisted=True).get("listings")
                       or [])}

    def pub(dev, key, title):
        ids[key] = am.publish_api(dev, key, title, "demo", {"ep": key},
                                  5, False, supply=5)["listing_id"]

    pub("usr:dana", "data-a", "Data A")
    pub("usr:dana", "data-b", "Data B")
    pub("usr:frank", "tools-a", "Tools A")
    pub("usr:dana", "ops-a", "Ops A")

    STAMP["value"] = "2026-07-01T00:00:00Z"
    q1 = am.ask_question("usr:bob", ids["data-a"],
                         "How many days does the first bundle take to ship?")
    q2 = am.ask_question("usr:carol", ids["data-a"],
                         "Is the export bundle shipped on a fixed weekday?")
    q3 = am.ask_question("usr:dave", ids["tools-a"],
                         "Which licence does the toolkit ship under?")
    q4 = am.ask_question("usr:dave", ids["ops-a"],
                         "How often are the nightly batches refreshed?")
    am.ask_question("usr:bob", ids["data-b"],
                    "Is there a cheaper tier for a single seat?")

    STAMP["value"] = "2026-07-02T00:00:00Z"
    a1 = am.answer_question("usr:dana", q1["question_id"],
                            "It ships in three working days.")
    a2 = am.answer_question("usr:dana", q2["question_id"],
                            "It ships every Monday.")
    a3 = am.answer_question("usr:frank", q3["question_id"],
                            "The toolkit ships under the MIT licence.")
    a4 = am.answer_question("usr:dana", q4["question_id"],
                            "Batches refresh once a week.")

    STAMP["value"] = "2026-08-10T00:00:00Z"
    am.revise_answer("usr:dana", a1["answer_id"],
                     "It ships in two working days.")
    am.revise_answer("usr:frank", a3["answer_id"],
                     "The toolkit ships under the Apache-2.0 licence.")

    STAMP["value"] = "2026-09-05T00:00:00Z"
    am.delist_api("usr:dana", ids["ops-a"])
    am.revise_answer("usr:dana", a4["answer_id"],
                     "Batches refresh every night.")

    STAMP["value"] = "2026-09-20T00:00:00Z"
    am.revise_answer("usr:dana", a1["answer_id"],
                     "It ships in three working days.")


def _sellers(am):
    """Every published seller, retired shelves included, by door."""
    rows = am.api_search(include_delisted=True).get("listings") or []
    return sorted({row["dev_account"] for row in rows if row.get("dev_account")})


def _enumerate(am):
    """Every answered question of every seller, by door."""
    retired = {int(row["listing_id"]): bool(row.get("delisted"))
               for row in (am.api_search(include_delisted=True).get("listings")
                           or [])}
    out = []
    for dev in _sellers(am):
        for row in am.api_seller_answers(dev).get("rows") or []:
            listing_id = int(row["listing_id"])
            out.append({"answer_id": int(row["answer_id"]),
                        "dev_account": dev,
                        "listing_key": row.get("listing_key"),
                        "listing_id": listing_id,
                        "buyer_id": row.get("buyer_id"),
                        "retired": retired.get(listing_id, False)})
    out.sort(key=lambda item: item["answer_id"])
    return out


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="arh-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "arh.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        answers = []
        for item in _enumerate(am):
            envelope = dict(am.api_answer_history(item["answer_id"]))
            # The retirement badge is derived from api_search, not invented:
            # the answer face does not publish a retired flag.
            envelope["retired"] = bool(item["retired"])
            # A revert is derived, never typed: the answer carries revisions
            # and the effective wording is the base wording again.
            envelope["reverted"] = bool(
                envelope.get("revisions")
                and envelope["effective_text"] == envelope["base_text"])
            if int(envelope["listing_id"]) != item["listing_id"]:
                raise FaceError("answer %r listing drift" % (item["answer_id"],))
            answers.append((item["answer_id"], item["dev_account"],
                            item["listing_key"], item["buyer_id"],
                            envelope))
        sellers = _sellers(am)
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
    for answer_id, dev, key, buyer, envelope in answers:
        missing = [name for name in ANSWER_KEYS
                   if name not in ("answer_id", "listing_key", "dev_account",
                                   "buyer_id", "rows") and name not in envelope]
        if missing or "revisions" not in envelope:
            raise FaceError("envelope keys missing for %r: %s"
                            % (answer_id, ",".join(missing)))
        if envelope["dev_account"] != dev:
            raise FaceError("answer %r answered by %r not %r"
                            % (answer_id, envelope["dev_account"], dev))
    return answers, sellers


def read_empty():
    """One landed unrevised answer on the bare stack: count 0, stamp None."""
    tmp_root = tempfile.mkdtemp(prefix="arh-empty-")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "bare.db"))
        R.seed_demo(am, led, dk)
        rows = am.api_search(include_delisted=True).get("listings") or []
        listing_id = int(rows[0]["listing_id"])
        question = am.ask_question("usr:bob", listing_id,
                                   "Is the sample shelf empty of revisions?")
        answer = am.answer_question("usr:dana", question["question_id"],
                                    "Yes, this answer has never been revised.")
        envelope = dict(am.api_answer_history(answer["answer_id"]))
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


def derive_market(answers, sellers):
    """AC-ARHB3 read at the source: every market number is derived."""
    revised = 0
    revisions = 0
    reverted = 0
    latest = None
    most = None
    best = -1
    seen_sellers = set()
    listings = set()
    buyers = set()
    for answer_id, dev, key, buyer, envelope in answers:
        rows = envelope.get("revisions") or []
        revisions += len(rows)
        if rows:
            revised += 1
        if rows and envelope["effective_text"] == envelope["base_text"]:
            reverted += 1
        for row in rows:
            if latest is None or row["revised_utc"] > latest:
                latest = row["revised_utc"]
        count = int(envelope["revision_count"])
        if count > best or (count == best and most is not None
                            and answer_id < most):
            best = count
            most = answer_id
        seen_sellers.add(dev)
        listings.add(int(envelope["listing_id"]))
        if buyer:
            buyers.add(buyer)
    return {
        "answer_count": len(answers),
        "revised_answer_count": revised,
        "unrevised_answer_count": len(answers) - revised,
        "revision_count": revisions,
        "reverted_answer_count": reverted,
        "seller_count": len(seen_sellers),
        "listing_count": len(listings),
        "buyer_count": len(buyers),
        "latest_revised_utc": latest,
        "most_revised_answer": most if best > 0 else None,
        "longest_chain": best if best > 0 else 0,
    }


def derive_sellers(answers, sellers):
    rows = []
    for dev in sellers:
        mine = [item for item in answers if item[1] == dev]
        revised = sum(1 for item in mine if item[4].get("revisions"))
        revisions = sum(len(item[4].get("revisions") or []) for item in mine)
        latest = None
        for item in mine:
            for row in item[4].get("revisions") or []:
                if latest is None or row["revised_utc"] > latest:
                    latest = row["revised_utc"]
        rows.append({"dev_account": dev, "answered_count": len(mine),
                     "revised_count": revised, "revision_count": revisions,
                     "latest_revised_utc": latest})
    return rows


def check_laws(answers, sellers, market, empty):
    """AC-ARHB3 read at the source: refuse rather than print."""
    problems = []
    seen = set()
    revision_total = 0
    revised = 0
    reverted = 0
    latest = None
    most = None
    best = -1
    per_seller = {}
    listings = set()
    buyers = set()
    for answer_id, dev, key, buyer, envelope in answers:
        if answer_id != int(envelope["answer_id"]):
            problems.append("%r answer_id %r" % (answer_id,
                                                 envelope["answer_id"]))
        if answer_id in seen:
            problems.append("answer %r appears twice" % (answer_id,))
        seen.add(answer_id)
        rows = envelope.get("revisions") or []
        if int(envelope["revision_count"]) != len(rows):
            problems.append("%r revision_count %r != %d rows"
                            % (answer_id, envelope["revision_count"],
                               len(rows)))
        previous_id = None
        for index, row in enumerate(rows):
            if previous_id is not None and \
                    int(row["revision_id"]) <= previous_id:
                problems.append("%r revision_id %r not ascending after %r"
                                % (answer_id, row["revision_id"],
                                   previous_id))
            previous_id = int(row["revision_id"])
            if index == 0:
                if row["previous_text"] != envelope["base_text"]:
                    problems.append("%r first previous != base"
                                    % (answer_id,))
            elif row["previous_text"] != rows[index - 1]["answer_text"]:
                problems.append("%r chain broken at %r"
                                % (answer_id, row["revision_id"]))
        wanted = (rows[-1]["answer_text"] if rows
                  else envelope["base_text"])
        if envelope["effective_text"] != wanted:
            problems.append("%r effective text drifted" % (answer_id,))
        wanted_stamp = rows[-1]["revised_utc"] if rows else None
        if envelope["latest_revised_utc"] != wanted_stamp:
            problems.append("%r latest %r != %r"
                            % (answer_id, envelope["latest_revised_utc"],
                               wanted_stamp))
        revision_total += len(rows)
        cell = per_seller.setdefault(dev, {"answered": 0, "revised": 0,
                                           "revisions": 0})
        cell["answered"] += 1
        if rows:
            revised += 1
            cell["revised"] += 1
            if envelope["effective_text"] == envelope["base_text"]:
                reverted += 1
        cell["revisions"] += len(rows)
        for row in rows:
            if latest is None or row["revised_utc"] > latest:
                latest = row["revised_utc"]
        count = int(envelope["revision_count"])
        if count > best:
            best = count
            most = answer_id
        listings.add(int(envelope["listing_id"]))
        if buyer:
            buyers.add(buyer)
    total = len(answers)
    if int(market["answer_count"]) != total:
        problems.append("market answers %r != %d"
                        % (market["answer_count"], total))
    if int(market["revision_count"]) != revision_total:
        problems.append("market revisions %r != %d"
                        % (market["revision_count"], revision_total))
    if int(market["revised_answer_count"]) != revised:
        problems.append("market revised %r != %d"
                        % (market["revised_answer_count"], revised))
    if int(market["revised_answer_count"]) + \
            int(market["unrevised_answer_count"]) != total:
        problems.append("market revised + unrevised != %d" % total)
    if int(market["reverted_answer_count"]) != reverted:
        problems.append("market reverted %r != %d"
                        % (market["reverted_answer_count"], reverted))
    if int(market["longest_chain"]) != (best if best > 0 else 0):
        problems.append("market longest %r != %d"
                        % (market["longest_chain"], max(best, 0)))
    want_most = most if best > 0 else None
    if market["most_revised_answer"] != want_most:
        problems.append("market most %r != %r"
                        % (market["most_revised_answer"], want_most))
    if market["latest_revised_utc"] != latest:
        problems.append("market latest %r != %r"
                        % (market["latest_revised_utc"], latest))
    if int(market["seller_count"]) != len(per_seller):
        problems.append("market sellers %r != %d"
                        % (market["seller_count"], len(per_seller)))
    if int(market["listing_count"]) != len(listings):
        problems.append("market listings %r != %d"
                        % (market["listing_count"], len(listings)))
    if int(market["buyer_count"]) != len(buyers):
        problems.append("market buyers %r != %d"
                        % (market["buyer_count"], len(buyers)))
    for dev in sellers:
        cell = per_seller.get(dev, {"answered": 0, "revised": 0,
                                    "revisions": 0})
        if cell["answered"] == 0:
            problems.append("seller %r has no answer entry" % (dev,))
    if empty.get("revisions"):
        problems.append("bare answer answered %d revisions"
                        % len(empty["revisions"]))
    if int(empty.get("revision_count", -1)) != 0:
        problems.append("bare revision_count %r != 0"
                        % (empty.get("revision_count"),))
    if empty.get("latest_revised_utc") is not None:
        problems.append("bare latest %r is not None"
                        % (empty.get("latest_revised_utc"),))
    if empty.get("effective_text") != empty.get("base_text"):
        problems.append("bare effective != base")
    return problems


def clip(value):
    text = str(value or "")
    return text if len(text) <= CLIP else text[:CLIP] + "\u2026"


def text(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return ("%.6f" % value).rstrip("0").rstrip(".")
    return str(value)


def kpi_html(pairs, e, dash):
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in pairs)


def seller_table(rows, labels, e, dash):
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_seller"] else "",
                      e(name))
                   for name in (labels["col_seller"], labels["col_answered"],
                                labels["col_revised"], labels["col_revisions"],
                                labels["col_latest"]))
    body = []
    for row in rows:
        body.append(
            '<tr data-seller="%s"><td>%s</td>%s</tr>'
            % (e(str(row["dev_account"])), e(str(row["dev_account"])),
               "".join('<td class="n">%s</td>'
                       % e(text(row[key], dash))
                       for key in ("answered_count", "revised_count",
                                   "revision_count", "latest_revised_utc"))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def chain_table(envelope, labels, e, dash):
    rows = envelope.get("revisions") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name in (labels["col_seq"],
                                               labels["col_stamp"]) else "",
                      e(name))
                   for name in (labels["col_seq"], labels["col_from"],
                                labels["col_to"], labels["col_stamp"]))
    body = []
    for index, row in enumerate(rows, 1):
        body.append(
            '<tr data-revision="%s"><td class="n">%d</td><td>%s</td>'
            '<td>%s</td><td class="n">%s</td></tr>'
            % (e(text(row["revision_id"], "")), index,
               e(clip(row["previous_text"])), e(clip(row["answer_text"])),
               e(str(row["revised_utc"] or dash))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def answer_card(item, labels, e, dash):
    answer_id, dev, key, buyer, envelope = item
    rows = envelope.get("revisions") or []
    badges = []
    if rows and envelope["effective_text"] == envelope["base_text"]:
        badges.append('<span class="badge off">%s</span>'
                      % e(labels["badge_reverted"]))
    if not rows:
        badges.append('<span class="badge off">%s</span>'
                      % e(labels["badge_plain"]))
    if envelope.get("retired"):
        badges.append('<span class="badge">%s</span>'
                      % e(labels["badge_retired"]))
    pairs = [(labels["kpi_chain"], envelope.get("revision_count")),
             (labels["col_latest"], envelope.get("latest_revised_utc")),
             (labels["col_seller"], dev),
             (labels["kpi_listings"], "#%s %s" % (envelope["listing_id"],
                                                  key or dash))]
    return ('<div class=card data-answer="%s"><h3 style="margin:0 0 8px;'
            'font-size:14px">%s #%s</h3><p class=qa>%s %s</p>'
            '<div class=kpi>%s</div>'
            '<p class=qa>%s %s</p><p class=qa>%s %s</p>%s%s</div>'
            % (e(str(answer_id)), e(labels["sec_answers"]), e(str(answer_id)),
               e(labels["q_label"]), e(clip(envelope.get("question_text"))),
               kpi_html(pairs, e, dash),
               e(labels["base_label"]), e(clip(envelope.get("base_text"))),
               e(labels["eff_label"]),
               e(clip(envelope.get("effective_text"))),
               "".join(badges), chain_table(envelope, labels, e, dash)))


def build_html(sellers_rows, answers, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_chain"],
            labels["law_effective"], labels["law_stamp"],
            labels["law_order"], labels["law_reverted"],
            labels["law_market"], labels["law_most"],
            labels["law_retired"], labels["law_unrevised"],
            labels["law_zero"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    market_pairs = [
        (labels["kpi_answers"], market.get("answer_count")),
        (labels["kpi_revised"], market.get("revised_answer_count")),
        (labels["kpi_unrevised"], market.get("unrevised_answer_count")),
        (labels["kpi_revisions"], market.get("revision_count")),
        (labels["kpi_reverted"], market.get("reverted_answer_count")),
        (labels["kpi_sellers"], market.get("seller_count")),
        (labels["kpi_listings"], market.get("listing_count")),
        (labels["kpi_buyers"], market.get("buyer_count")),
        (labels["kpi_latest"], market.get("latest_revised_utc")),
        (labels["kpi_most"], market.get("most_revised_answer")),
        (labels["kpi_longest"], market.get("longest_chain")),
    ]
    market_html = (
        '<div class=card><div class=kpi>%s</div>%s'
        '<p class=cap>%s</p></div>'
        % (kpi_html(market_pairs, e, dash),
           seller_table(sellers_rows, labels, e, dash),
           e(labels["clip_caption"])))
    cards = "".join(answer_card(item, labels, e, dash) for item in answers)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]), market_html,
           e(labels["sec_answers"]), cards,
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


def trim_answer(item):
    answer_id, dev, key, buyer, envelope = item
    doc = {"answer_id": answer_id, "dev_account": dev,
           "listing_key": key, "buyer_id": buyer}
    for name in ANSWER_KEYS:
        if name in ("answer_id", "listing_key", "dev_account", "buyer_id",
                    "rows"):
            continue
        doc[name] = envelope[name]
    doc["rows"] = [{name: row[name] for name in ROW_KEYS}
                   for row in envelope.get("revisions") or []]
    return doc


def payload_of(sellers_rows, answers, market, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "answers",
        "market": market,
        "sellers": sellers_rows,
        "answers": [trim_answer(item) for item in answers],
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
        print("ANSWER-REVISION CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        answers, sellers = read_world()
        empty = read_empty()
        market = derive_market(answers, sellers)
        sellers_rows = derive_sellers(answers, sellers)
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    try:
        problems = check_laws(answers, sellers, market, empty)
    except LawError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = answers[0][4].get("disclaimer") if answers else None
    doc = build_html(sellers_rows, answers, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(sellers_rows, answers, market, args.out, disclaimer,
                         now)
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

    print("ANSWER-REVISION %s bytes=%d answers=%d revisions=%d sellers=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             int(market["answer_count"]), int(market["revision_count"]),
             int(market["seller_count"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
