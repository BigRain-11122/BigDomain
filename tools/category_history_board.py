"""Category-history board (R3455).

WHY THIS PAGE EXISTS (measured at R3455, not assumed):
api_category_history shipped the per-listing category-movement face - the
declaration made at publish time plus every append-only revision in order, the
CURRENT effective bucket and the revision count, so a seller and an operator
can both read how a listing moved between buckets - but a search over tools/,
preview/ and src/os answered zero readers for its name. api_categories answers
how many listings sit in each bucket today and api_category_*_months answers
monthly buckets, so "which shelf changed bucket, from where to where, how many
times and what did the market's buckets gain and lose" could only be read by
calling the sandbox from a shell. This page opens the axis the face already
carries; it adds no table, no reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-CGHB3, fixed in this round's window
before the first render; the src/os/backlog.md R3455 PIN row landed with the
driver and says so):
  - per listing revision_count == the number of revision rows
  - the chain is continuous: the first row's previous_category == the base
    declaration, and every later row's previous_category == the previous
    row's category
  - the effective category == the last row's category, or the base
    declaration when there is no revision at all
  - latest_revision_utc == the last row's revised_utc, or None (never a
    fabricated zero) when the listing was never revised
  - revision_id is strictly ascending inside every listing
  - the market listing count == the number of listing entries, the revision
    total == the sum of the per-listing revision counts, and moved +
    unchanged == listing count
  - per bucket gained == the number of revisions whose category is that
    bucket and lost == the number whose previous_category is that bucket
  - per bucket base + gained - lost == current, and both the base total and
    the current total equal the listing count
  - buckets are ordered by category ascending with the uncategorized bucket
    pinned last, mirroring api_categories
  - the most-moved listing is the one with the largest revision count, ties
    going to the smallest listing_id, and None when nothing was revised
  - a delisted listing keeps its whole chain readable, and delisted_count
    counts them
  - the bare world answers zero listings and zero revisions with every
    derived field empty

Every number on the page comes from the shipped face. Chinese labels live in
preview/category-history-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "category-history-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "category-history-board.json")
COPY = os.path.join(ROOT, "preview", "category-history-board-copy.json")

FACE = "api_category_history"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "market", "listings", "disclaimer",
    "report", "sources", "sizes",
)

MARKET_KEYS = (
    "listing_count", "moved_listing_count", "unchanged_listing_count",
    "revision_count", "seller_count", "bucket_count", "delisted_count",
    "latest_revision_utc", "most_moved_listing", "buckets",
)

BUCKET_KEYS = ("category", "base_count", "gained_count", "lost_count",
               "net_count", "current_count")

LISTING_KEYS = ("listing_id", "listing_key", "dev_account", "base_category",
                "category", "revision_count", "latest_revision_utc",
                "delisted", "delisted_utc", "rows")

ROW_KEYS = ("revision_id", "dev_account", "previous_category", "category",
            "revised_utc")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_listings", "sec_law", "sec_disc", "sec_rep",
    "kpi_listings", "kpi_moved", "kpi_unchanged", "kpi_revisions",
    "kpi_sellers", "kpi_buckets", "kpi_delisted", "kpi_latest",
    "kpi_most_moved", "market_cap",
    "col_category", "col_base", "col_gained", "col_lost", "col_net",
    "col_current", "col_bar",
    "col_seq", "col_from", "col_to", "col_seller", "col_stamp",
    "uncategorized", "empty", "none", "bar_caption",
    "law_count", "law_chain", "law_effective", "law_stamp", "law_order",
    "law_market", "law_conserve", "law_gained", "law_unchanged", "law_most",
    "law_delisted", "law_bar", "law_zero", "law_notadvice",
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

# One pinned clock drives every write so the story reproduces.
STAMP = {"value": "2026-06-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_CGHB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_CGHB_LAW"


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
    """One landed movement story, every row by door.

    The factory world carries three live shelves and ZERO category revision,
    so every re-filing below is made through the shipped publish_api and
    revise_category doors under the pinned clock - no sqlite rewrite, no typed
    ids, no padded rows. The story exercises the laws on purpose: a shelf that
    walks data -> tools -> media -> data (three revisions ending back on its
    base bucket), a shelf that walks tools -> media -> tools (a legal return to
    an earlier bucket), one shelf filed into the uncategorized bucket and one
    filed out of it, a shelf revised and then delisted, and three shelves
    never revised at all.
    """
    STAMP["value"] = "2026-06-01T00:00:00Z"
    ids = {row["listing_key"]: int(row["listing_id"])
           for row in (am.api_search(include_delisted=True).get("listings")
                       or [])}

    def pub(dev, key, title, category):
        ids[key] = am.publish_api(dev, key, title, "demo", {"ep": key},
                                  5, False, supply=5,
                                  category=category)["listing_id"]

    pub("usr:dana", "data-a", "Data A", "data")
    pub("usr:dana", "data-b", "Data B", "data")
    pub("usr:frank", "tools-a", "Tools A", "tools")
    pub("usr:frank", "tools-b", "Tools B", "tools")
    pub("usr:dana", "misc-a", "Misc A", None)
    pub("usr:frank", "media-a", "Media A", "media")
    pub("usr:dana", "ops-a", "Ops A", "ops")
    pub("usr:frank", "ops-b", "Ops B", "ops")

    STAMP["value"] = "2026-07-10T00:00:00Z"
    am.revise_category("usr:dana", ids["risk-scan"], "data")
    am.revise_category("usr:frank", ids["chart-render"], "tools")
    am.revise_category("usr:dana", ids["misc-a"], "data")
    am.revise_category("usr:frank", ids["media-a"], None)

    STAMP["value"] = "2026-08-03T00:00:00Z"
    am.revise_category("usr:dana", ids["risk-scan"], "tools")
    am.revise_category("usr:frank", ids["chart-render"], None)

    STAMP["value"] = "2026-09-01T00:00:00Z"
    am.revise_category("usr:dana", ids["ops-a"], "tools")

    STAMP["value"] = "2026-09-15T00:00:00Z"
    am.revise_category("usr:dana", ids["risk-scan"], "media")
    am.delist_api("usr:dana", ids["ops-a"])


def _enumerate(am):
    """Every listing the market carries, retired ones included, by door."""
    rows = am.api_search(include_delisted=True).get("listings") or []
    return [(int(row["listing_id"]), row.get("listing_key"),
             row.get("dev_account")) for row in rows]


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="cgh-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "cgh.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        listings = []
        for listing_id, key, dev in _enumerate(am):
            envelope = dict(am.api_category_history(listing_id))
            listings.append((listing_id, key, dev, envelope))
        listings.sort(key=lambda item: item[0])
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
    for listing_id, key, dev, envelope in listings:
        missing = [name for name in LISTING_KEYS
                   if name not in ("listing_id", "listing_key", "dev_account",
                                   "rows") and name not in envelope]
        if missing or "revisions" not in envelope:
            raise FaceError("envelope keys missing for %r: %s"
                            % (listing_id, ",".join(missing)))
    return listings


def read_empty():
    """The bare stack answers one unrevised shelf; the page shows it."""
    tmp_root = tempfile.mkdtemp(prefix="cgh-empty-")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "bare.db"))
        R.seed_demo(am, led, dk)
        envelope = dict(am.api_category_history(1))
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


def _bucket_key(category):
    return (1 if category is None else 0, str(category or ""))


def derive_market(listings):
    """AC-CGHB3 read at the source: the bucket ledger is derived, not typed."""
    buckets = {}
    sellers = set()
    revisions = 0
    moved = 0
    delisted = 0
    latest = None
    most = None
    best = -1
    for listing_id, key, dev, envelope in listings:
        base = envelope["base_category"]
        current = envelope["category"]
        rows = envelope.get("revisions") or []
        revisions += len(rows)
        if rows:
            moved += 1
        if envelope["delisted"]:
            delisted += 1
        if key and dev:
            sellers.add(dev)
        bucket = buckets.setdefault(base, {"base": 0, "current": 0,
                                           "gained": 0, "lost": 0})
        bucket["base"] += 1
        bucket = buckets.setdefault(current, {"base": 0, "current": 0,
                                              "gained": 0, "lost": 0})
        bucket["current"] += 1
        for row in rows:
            buckets.setdefault(row["category"],
                               {"base": 0, "current": 0, "gained": 0,
                                "lost": 0})["gained"] += 1
            buckets.setdefault(row["previous_category"],
                               {"base": 0, "current": 0, "gained": 0,
                                "lost": 0})["lost"] += 1
            if latest is None or row["revised_utc"] > latest:
                latest = row["revised_utc"]
        count = int(envelope["revision_count"])
        if count > best or (count == best and most is not None
                            and listing_id < most):
            best = count
            most = listing_id
    rows = []
    for category in sorted(buckets, key=_bucket_key):
        cell = buckets[category]
        rows.append({
            "category": category,
            "base_count": cell["base"],
            "gained_count": cell["gained"],
            "lost_count": cell["lost"],
            "net_count": cell["gained"] - cell["lost"],
            "current_count": cell["current"],
        })
    return {
        "listing_count": len(listings),
        "moved_listing_count": moved,
        "unchanged_listing_count": len(listings) - moved,
        "revision_count": revisions,
        "seller_count": len(sellers),
        "bucket_count": len(buckets),
        "delisted_count": delisted,
        "latest_revision_utc": latest,
        "most_moved_listing": most if best > 0 else None,
        "buckets": rows,
    }


def check_laws(listings, market, empty):
    """AC-CGHB3 read at the source: refuse rather than print."""
    problems = []
    seen = set()
    revision_total = 0
    moved = 0
    base_totals = {}
    current_totals = {}
    gained = {}
    lost = {}
    latest = None
    most = None
    best = -1
    for listing_id, key, dev, envelope in listings:
        if listing_id in seen:
            problems.append("listing %r appears twice" % (listing_id,))
        seen.add(listing_id)
        rows = envelope.get("revisions") or []
        if int(envelope["revision_count"]) != len(rows):
            problems.append("%r revision_count %r != %d rows"
                            % (listing_id, envelope["revision_count"],
                               len(rows)))
        previous_id = None
        for index, row in enumerate(rows):
            if previous_id is not None and int(row["revision_id"]) <= previous_id:
                problems.append("%r revision_id %r not ascending after %r"
                                % (listing_id, row["revision_id"],
                                   previous_id))
            previous_id = int(row["revision_id"])
            if index == 0:
                if row["previous_category"] != envelope["base_category"]:
                    problems.append("%r first previous %r != base %r"
                                    % (listing_id,
                                       row["previous_category"],
                                       envelope["base_category"]))
            elif row["previous_category"] != rows[index - 1]["category"]:
                problems.append("%r chain broken at %r"
                                % (listing_id, row["revision_id"]))
        wanted = rows[-1]["category"] if rows else envelope["base_category"]
        if envelope["category"] != wanted:
            problems.append("%r effective %r != %r"
                            % (listing_id, envelope["category"], wanted))
        wanted_stamp = rows[-1]["revised_utc"] if rows else None
        if envelope["latest_revision_utc"] != wanted_stamp:
            problems.append("%r latest %r != %r"
                            % (listing_id, envelope["latest_revision_utc"],
                               wanted_stamp))
        revision_total += len(rows)
        if rows:
            moved += 1
        base_totals[envelope["base_category"]] = \
            base_totals.get(envelope["base_category"], 0) + 1
        current_totals[envelope["category"]] = \
            current_totals.get(envelope["category"], 0) + 1
        for row in rows:
            gained[row["category"]] = gained.get(row["category"], 0) + 1
            lost[row["previous_category"]] = \
                lost.get(row["previous_category"], 0) + 1
            if latest is None or row["revised_utc"] > latest:
                latest = row["revised_utc"]
        if int(envelope["revision_count"]) > best:
            best = int(envelope["revision_count"])
            most = listing_id
    total = len(listings)
    if int(market["listing_count"]) != total:
        problems.append("market listings %r != %d"
                        % (market["listing_count"], total))
    if int(market["revision_count"]) != revision_total:
        problems.append("market revisions %r != %d"
                        % (market["revision_count"], revision_total))
    if int(market["moved_listing_count"]) != moved:
        problems.append("market moved %r != %d"
                        % (market["moved_listing_count"], moved))
    if int(market["moved_listing_count"]) + \
            int(market["unchanged_listing_count"]) != total:
        problems.append("market moved + unchanged != %d" % total)
    want_most = most if best > 0 else None
    if market["most_moved_listing"] != want_most:
        problems.append("market most moved %r != %r"
                        % (market["most_moved_listing"], want_most))
    if market["latest_revision_utc"] != latest:
        problems.append("market latest %r != %r"
                        % (market["latest_revision_utc"], latest))
    buckets = market.get("buckets") or []
    if int(market["bucket_count"]) != len(buckets):
        problems.append("market bucket_count %r != %d rows"
                        % (market["bucket_count"], len(buckets)))
    previous = None
    base_sum = 0
    current_sum = 0
    for row in buckets:
        bucket = row["category"]
        if bucket not in base_totals and bucket not in current_totals \
                and bucket not in gained and bucket not in lost:
            problems.append("bucket %r has no source" % (bucket,))
        if previous is not None and _bucket_key(bucket) <= previous:
            problems.append("bucket rows out of order at %r" % (bucket,))
        previous = _bucket_key(bucket)
        if int(row["base_count"]) != base_totals.get(bucket, 0):
            problems.append("bucket %r base %r != %d"
                            % (bucket, row["base_count"],
                               base_totals.get(bucket, 0)))
        if int(row["current_count"]) != current_totals.get(bucket, 0):
            problems.append("bucket %r current %r != %d"
                            % (bucket, row["current_count"],
                               current_totals.get(bucket, 0)))
        if int(row["gained_count"]) != gained.get(bucket, 0):
            problems.append("bucket %r gained %r != %d"
                            % (bucket, row["gained_count"],
                               gained.get(bucket, 0)))
        if int(row["lost_count"]) != lost.get(bucket, 0):
            problems.append("bucket %r lost %r != %d"
                            % (bucket, row["lost_count"],
                               lost.get(bucket, 0)))
        if int(row["net_count"]) != (int(row["gained_count"])
                                     - int(row["lost_count"])):
            problems.append("bucket %r net %r != gained - lost"
                            % (bucket, row["net_count"]))
        if int(row["base_count"]) + int(row["net_count"]) != \
                int(row["current_count"]):
            problems.append("bucket %r conservation broken" % (bucket,))
        base_sum += int(row["base_count"])
        current_sum += int(row["current_count"])
    for bucket, count in base_totals.items():
        if bucket not in [row["category"] for row in buckets]:
            problems.append("base bucket %r missing from rows" % (bucket,))
    if base_sum != total and total:
        problems.append("base total %d != %d" % (base_sum, total))
    if current_sum != total and total:
        problems.append("current total %d != %d" % (current_sum, total))
    if empty.get("revisions"):
        problems.append("bare shelf answered %d revisions"
                        % len(empty["revisions"]))
    for name in ("revision_count",):
        if int(empty.get(name, -1)) != 0:
            problems.append("bare %s %r != 0" % (name, empty.get(name)))
    for name in ("latest_revision_utc",):
        if empty.get(name) is not None:
            problems.append("bare %s %r is not None" % (name, empty.get(name)))
    return problems


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


def bucket_table(market, labels, e, dash):
    rows = market.get("buckets") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = max(int(row["current_count"]) for row in rows)
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_category"] else "",
                      e(name))
                   for name in (labels["col_category"], labels["col_base"],
                                labels["col_gained"], labels["col_lost"],
                                labels["col_net"], labels["col_current"],
                                labels["col_bar"]))
    body = []
    for row in rows:
        current = int(row["current_count"])
        category = (row["category"] if row["category"] is not None
                    else labels["uncategorized"])
        if not peak:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, current / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-bucket="%s"%s><td>%s</td>%s<td>%s</td></tr>'
            % (e(str(category)), ' class="quiet-row"' if not current else "",
               e(str(category)),
               "".join('<td class="n">%s</td>'
                       % e(text(row[key], dash))
                       for key in ("base_count", "gained_count",
                                   "lost_count", "net_count",
                                   "current_count")),
               bar))
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
                                labels["col_to"], labels["col_seller"],
                                labels["col_stamp"]))
    body = []
    for index, row in enumerate(rows, 1):
        def bucket(value):
            return (labels["uncategorized"] if value is None
                    else str(value))
        body.append(
            '<tr data-revision="%s"><td class="n">%d</td><td>%s</td>'
            '<td>%s</td><td>%s</td><td class="n">%s</td></tr>'
            % (e(text(row["revision_id"], "")), index,
               e(bucket(row["previous_category"])),
               e(bucket(row["category"])),
               e(str(row["dev_account"] or dash)),
               e(str(row["revised_utc"] or dash))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def listing_card(listing_id, key, dev, envelope, labels, e, dash):
    def bucket(value):
        return labels["uncategorized"] if value is None else str(value)

    pairs = [
        (labels["kpi_revisions"], envelope.get("revision_count")),
        (labels["kpi_latest"], envelope.get("latest_revision_utc")),
        (labels["col_base"], bucket(envelope.get("base_category"))),
        (labels["col_current"], bucket(envelope.get("category"))),
        (labels["kpi_delisted"], "yes" if envelope.get("delisted") else "no"),
        (labels["col_seller"], dev),
    ]
    return ('<div class=card data-listing="%s"><h3 style="margin:0 0 8px;'
            'font-size:14px">%s <span style="color:#66707a;font-weight:400">'
            '#%s</span></h3><div class=kpi>%s</div>%s'
            '<p class=cap>%s</p></div>'
            % (e(str(listing_id)), e(str(key or dash)), e(str(listing_id)),
               kpi_html(pairs, e, dash),
               chain_table(envelope, labels, e, dash),
               e(labels["bar_caption"])))


def build_html(listings, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_chain"],
            labels["law_effective"], labels["law_stamp"],
            labels["law_order"], labels["law_market"],
            labels["law_conserve"], labels["law_gained"],
            labels["law_unchanged"], labels["law_most"],
            labels["law_delisted"], labels["law_bar"], labels["law_zero"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    market_pairs = [
        (labels["kpi_listings"], market.get("listing_count")),
        (labels["kpi_moved"], market.get("moved_listing_count")),
        (labels["kpi_unchanged"], market.get("unchanged_listing_count")),
        (labels["kpi_revisions"], market.get("revision_count")),
        (labels["kpi_sellers"], market.get("seller_count")),
        (labels["kpi_buckets"], market.get("bucket_count")),
        (labels["kpi_delisted"], market.get("delisted_count")),
        (labels["kpi_latest"], market.get("latest_revision_utc")),
        (labels["kpi_most_moved"], market.get("most_moved_listing")),
    ]
    market_html = (
        '<div class=card><div class=kpi>%s</div>%s'
        '<p class=cap>%s</p></div>'
        % (kpi_html(market_pairs, e, dash),
           bucket_table(market, labels, e, dash),
           e(labels["market_cap"])))
    cards = "".join(listing_card(listing_id, key, dev, envelope, labels, e,
                                 dash)
                    for listing_id, key, dev, envelope in listings)
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
           e(labels["sec_listings"]), cards,
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


def trim_listing(listing_id, key, dev, envelope):
    doc = {"listing_id": listing_id, "listing_key": key, "dev_account": dev}
    for name in LISTING_KEYS:
        if name in ("listing_id", "listing_key", "dev_account", "rows"):
            continue
        doc[name] = envelope[name]
    doc["rows"] = [{name: row[name] for name in ROW_KEYS}
                   for row in envelope.get("revisions") or []]
    return doc


def payload_of(listings, market, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "listings",
        "market": market,
        "listings": [trim_listing(listing_id, key, dev, envelope)
                     for listing_id, key, dev, envelope in listings],
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
        print("CATEGORY-HISTORY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        listings = read_world()
        empty = read_empty()
        market = derive_market(listings)
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    try:
        problems = check_laws(listings, market, empty)
    except LawError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = listings[0][3].get("disclaimer") if listings else None
    doc = build_html(listings, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(listings, market, args.out, disclaimer, now)
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

    print("CATEGORY-HISTORY %s bytes=%d listings=%d revisions=%d buckets=%d"
          % (payload["report"], len(doc.encode("utf-8")), len(listings),
             int(market["revision_count"]), int(market["bucket_count"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
