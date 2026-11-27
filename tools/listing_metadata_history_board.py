"""Listing metadata history board (R3483).

WHY THIS PAGE EXISTS (measured at R3483, not assumed):
api_metadata_history shipped ONE listing's title/description trail - the
immutable base pair plus every append-only revision in order, the current
effective pair and the revision count - but a search over tools/, preview/ and
src/os answered zero readers for its name, so a seller's whole copy-repair
trail could only be read by calling the sandbox from a shell. The price
history page (R3482) answers a different question: that one is money, this one
is words - which field moved, to what text, and when.
This page opens the trail the face already carries; it adds no table, no
reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-LMHB1..AC-LMHB6, fixed in this
round's window before the first render; the src/os/backlog.md R3483 PIN row
landed before any driver code):
  - revision_count == len(revisions)
  - replay: start at (base_title, base_description), each revision row stores
    the full effective pair, and the last pair equals the face's pair; with no
    revision both effective fields equal their base
  - every step carries two non-blank fields and differs from the pair it
    replaced in at least one field (the door refuses a same pair, so history
    must never show one)
  - revision_id strictly ascending and revised_utc never moves backwards
  - title_changes + description_changes == every changed field counted once
    per step; both_changes == the steps that moved both
  - a shelf with no revision says so in words: no empty table, no invented row

Every number on the page comes from the shipped face. Chinese labels live in
preview/listing-metadata-history-board-copy.json so this driver stays ASCII.
"""
import argparse
import datetime
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

OUT_HTML = os.path.join(ROOT, "preview", "listing-metadata-history-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "listing-metadata-history-board.json")
COPY = os.path.join(ROOT, "preview", "listing-metadata-history-board-copy.json")

FACE = "api_metadata_history"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "listings", "market", "disclaimer",
    "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "listing_id", "base_title", "base_description", "title", "description",
    "revision_count", "latest_revision_utc", "delisted", "delisted_utc",
    "revisions", "disclaimer",
)

REV_KEYS = ("revision_id", "dev_account", "title", "description",
            "revised_utc")

MARKET_KEYS = (
    "listing_count", "revision_count", "title_changes",
    "description_changes", "both_changes", "peak_month",
    "peak_month_revisions", "busiest_listing", "busiest_revisions",
    "latest_revision_utc", "unrevisioned_count",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_boards", "sec_law", "sec_disc", "sec_rep",
    "m_listings", "m_revisions", "m_title", "m_desc", "m_both",
    "m_peak", "m_busiest", "m_unrev",
    "b_base", "b_current", "b_revisions", "b_title_changes",
    "b_desc_changes", "b_latest",
    "col_rev", "col_who", "col_fields", "col_title", "col_desc", "col_when",
    "badge_title", "badge_desc", "badge_both", "badge_live", "badge_delisted",
    "badge_count",
    "empty", "empty_market", "none", "unrev_suffix",
    "law_count", "law_replay", "law_order", "law_change", "law_quiet",
    "law_notadvice", "law_notpolicy",
    "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:16px 0 8px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line);
vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 130px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:16px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.t{border-color:#a9c7e8;background:#eef5fd;color:#1c4e80}
.badge.d{border-color:#c9b6e0;background:#f5eefd;color:#4b2a75}
.badge.b{border-color:#9ad1a7;background:#eef9f1;color:#1f6b33}
.badge.off{border-color:#c9c9c9;background:#f2f2f2;color:#555}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"

# One pinned clock drives every write so the trail reproduces.
STAMP = {"value": "2026-11-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_LMHB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_LMHB_LAW"


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
    """One landed trail across the three shipped shelves, every row by door.

    The factory world carries three listings and zero metadata revisions, so
    every revision here is made through the shipped edit_listing door under
    the pinned clock: risk-scan moves the title, then the description, then
    both; macro-feed moves the title once; chart-render is never edited, which
    is the face's own honest quiet shape.
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
    owners = {key: str(by_key[key]["dev_account"])
              for key in ("risk-scan", "macro-feed", "chart-render")}

    STAMP["value"] = "2026-09-12T00:00:00Z"
    am.edit_listing(owners["risk-scan"], risk, title="Risk Scan API v2")
    STAMP["value"] = "2026-10-06T00:00:00Z"
    am.edit_listing(owners["risk-scan"], risk,
                    description="portfolio risk scan with sector drilldown")
    STAMP["value"] = "2026-11-14T00:00:00Z"
    am.edit_listing(owners["risk-scan"], risk, title="Risk Scan API Pro",
                    description="portfolio risk scan, exposure and drilldown")
    STAMP["value"] = "2026-10-23T00:00:00Z"
    am.edit_listing(owners["macro-feed"], macro, title="Macro Feed API v2")
    shelf_by_id = {risk: "risk-scan", macro: "macro-feed",
                   chart: "chart-render"}
    return [risk, macro, chart], {"by_id": shelf_by_id, "owners": owners}


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="lmhb-")
    db = os.path.join(tmp_root, "lmhb.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        ids, meta = build_world(am)
        envelopes = [dict(am.api_metadata_history(listing_id))
                     for listing_id in ids]
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
    for envelope in envelopes:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing for %s: %s"
                            % (envelope.get("listing_id"),
                               ",".join(missing)))
        for rev in envelope.get("revisions") or []:
            miss = [key for key in REV_KEYS if key not in rev]
            if miss:
                raise FaceError("revision keys missing: %s"
                                % ",".join(miss))
    return envelopes, meta


def _month(utc):
    return str(utc)[:7]


def _fields(previous, current):
    """Which of the two effective fields this step moved."""
    changed = []
    if str(previous[0]) != str(current[0]):
        changed.append("title")
    if str(previous[1]) != str(current[1]):
        changed.append("description")
    return changed


def _merge(meta, envelopes):
    """Attach the shelf name and owner the board carries, for the page only."""
    rows = []
    for envelope in envelopes:
        doc = dict(envelope)
        shelf = meta["by_id"].get(int(envelope["listing_id"]), "")
        doc["shelf"] = shelf
        doc["owner"] = meta["owners"].get(shelf, "")
        doc["steps"] = []
        previous = (envelope["base_title"], envelope["base_description"])
        for rev in envelope.get("revisions") or []:
            current = (rev["title"], rev["description"])
            doc["steps"].append({
                "revision_id": rev["revision_id"],
                "dev_account": rev["dev_account"],
                "title": rev["title"],
                "description": rev["description"],
                "revised_utc": rev["revised_utc"],
                "changed": _fields(previous, current),
            })
            previous = current
        rows.append(doc)
    return rows


def _market(envelopes):
    title_changes = desc_changes = both_changes = revisions = 0
    latest = None
    counts = {}
    busiest = (None, 0)
    for envelope in sorted(envelopes, key=lambda e: int(e["listing_id"])):
        for step in envelope.get("steps") or []:
            changed = step["changed"]
            revisions += 1
            if "title" in changed:
                title_changes += 1
            if "description" in changed:
                desc_changes += 1
            if len(changed) == 2:
                both_changes += 1
            key = _month(step["revised_utc"])
            counts[key] = counts.get(key, 0) + 1
            if latest is None or str(step["revised_utc"]) > latest:
                latest = str(step["revised_utc"])
        count = len(envelope.get("steps") or [])
        if count > busiest[1]:
            busiest = (int(envelope["listing_id"]), count)
    peak_month = None
    peak_count = 0
    for key in sorted(counts):
        if counts[key] > peak_count:
            peak_month, peak_count = key, counts[key]
    unrevisioned = sum(1 for envelope in envelopes
                       if not envelope.get("steps"))
    return {
        "listing_count": len(envelopes),
        "revision_count": revisions,
        "title_changes": title_changes,
        "description_changes": desc_changes,
        "both_changes": both_changes,
        "peak_month": peak_month,
        "peak_month_revisions": peak_count,
        "busiest_listing": busiest[0],
        "busiest_revisions": busiest[1],
        "latest_revision_utc": latest,
        "unrevisioned_count": unrevisioned,
    }


def check_laws(envelopes, market):
    problems = []
    title_changes = desc_changes = both_changes = revisions = 0
    for envelope in envelopes:
        tag = "listing %s" % envelope.get("listing_id")
        steps = envelope.get("steps") or []
        if int(envelope.get("revision_count", -1)) != len(steps):
            problems.append("%s revision_count %r != %d rows"
                            % (tag, envelope.get("revision_count"),
                               len(steps)))
        previous = (envelope["base_title"], envelope["base_description"])
        last_id = None
        last_utc = None
        for step in steps:
            current = (step["title"], step["description"])
            if not str(step["title"]).strip():
                problems.append("%s revision %r blank title"
                                % (tag, step["revision_id"]))
            if not str(step["description"]).strip():
                problems.append("%s revision %r blank description"
                                % (tag, step["revision_id"]))
            changed = _fields(previous, current)
            if not changed:
                problems.append("%s revision %r repeats the pair"
                                % (tag, step["revision_id"]))
            if str(step["dev_account"]) != str(envelope.get("owner")):
                problems.append("%s revision %r by %r not the owner %r"
                                % (tag, step["revision_id"],
                                   step["dev_account"],
                                   envelope.get("owner")))
            if last_id is not None and int(step["revision_id"]) <= last_id:
                problems.append("%s revision ids not ascending at %r"
                                % (tag, step["revision_id"]))
            if last_utc is not None and str(step["revised_utc"]) < last_utc:
                problems.append("%s revision time moved backwards at %r"
                                % (tag, step["revision_id"]))
            last_id = int(step["revision_id"])
            last_utc = str(step["revised_utc"])
            revisions += 1
            if "title" in changed:
                title_changes += 1
            if "description" in changed:
                desc_changes += 1
            if len(changed) == 2:
                both_changes += 1
            previous = current
        if str(previous[0]) != str(envelope["title"]) or str(
                previous[1]) != str(envelope["description"]):
            problems.append("%s replay pair %r/%r != face pair %r/%r"
                            % (tag, previous[0], previous[1],
                               envelope["title"], envelope["description"]))
        if not steps and (str(envelope["title"]) != str(
                envelope["base_title"]) or str(envelope["description"]) != str(
                    envelope["base_description"])):
            problems.append("%s quiet shelf pair differs from base" % tag)
    if market["revision_count"] != revisions:
        problems.append("market revision_count %r != %d"
                        % (market["revision_count"], revisions))
    if (market["title_changes"] != title_changes
            or market["description_changes"] != desc_changes
            or market["both_changes"] != both_changes):
        problems.append("market field split %r/%r/%r != %d/%d/%d"
                        % (market["title_changes"],
                           market["description_changes"],
                           market["both_changes"], title_changes,
                           desc_changes, both_changes))
    if market["listing_count"] != len(envelopes):
        problems.append("market listing_count %r != %d"
                        % (market["listing_count"], len(envelopes)))
    return problems


def text(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def badge_of(changed, labels, e):
    if len(changed) == 2:
        return '<span class="badge b">%s</span>' % e(labels["badge_both"])
    if changed and changed[0] == "title":
        return '<span class="badge t">%s</span>' % e(labels["badge_title"])
    return '<span class="badge d">%s</span>' % e(labels["badge_desc"])


def market_html(market, labels, e, none_text):
    cells = (
        ("m_listings", market["listing_count"]),
        ("m_revisions", market["revision_count"]),
        ("m_title", market["title_changes"]),
        ("m_desc", market["description_changes"]),
        ("m_both", market["both_changes"]),
        ("m_peak", market["peak_month"]),
        ("m_busiest", market["busiest_listing"]),
        ("m_unrev", "%d%s" % (market["unrevisioned_count"],
                              labels["unrev_suffix"])),
    )
    out = []
    for key, value in cells:
        out.append("<div><b>%s</b><span>%s</span></div>"
                   % (e(text(value, none_text)), e(labels[key])))
    return "<div class=kpi>%s</div>" % "".join(out)


def envelope_card(envelope, labels, e, none_text):
    steps = envelope.get("steps") or []
    badge = '<span class="badge off">%s</span>' % e(
        labels["badge_delisted"] if envelope.get("delisted")
        else labels["badge_live"])
    counts = '<span class="badge">%s %s</span>' % (
        e(str(int(envelope["revision_count"]))), e(labels["badge_count"]))
    title_moves = sum(1 for step in steps if "title" in step["changed"])
    desc_moves = sum(1 for step in steps
                     if "description" in step["changed"])
    cells = (
        ("b_base", envelope["base_title"]),
        ("b_current", envelope["title"]),
        ("b_revisions", envelope["revision_count"]),
        ("b_title_changes", title_moves),
        ("b_desc_changes", desc_moves),
        ("b_latest", envelope.get("latest_revision_utc")),
    )
    kpi = "".join("<div><b>%s</b><span>%s</span></div>"
                  % (e(text(value, none_text)), e(labels[key]))
                  for key, value in cells)
    if not steps:
        table = '<p class=empty>%s</p>' % e(labels["empty"])
    else:
        head = "".join(
            "<th%s>%s</th>"
            % (" class=n" if key == "col_rev" else "", e(labels[key]))
            for key in ("col_rev", "col_who", "col_fields", "col_title",
                        "col_desc", "col_when"))
        body = []
        for step in steps:
            body.append(
                "<tr><td class=n>%d</td><td>%s</td><td>%s</td>"
                "<td>%s</td><td>%s</td><td>%s</td></tr>"
                % (int(step["revision_id"]), e(str(step["dev_account"])),
                   badge_of(step["changed"], labels, e),
                   e(str(step["title"])), e(str(step["description"])),
                   e(str(step["revised_utc"]))))
        table = ("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                 % (head, "".join(body)))
    return (
        '<div class=card data-listing="%s">\n<h3>%s %s %s</h3>\n'
        "<div class=kpi>%s</div>\n%s\n</div>\n"
        % (e(str(envelope["listing_id"])), e(labels["b_current"]),
           e(str(envelope["shelf"] or envelope["listing_id"])), badge + counts,
           kpi, table)
    )


def build_html(envelopes, market, labels, now, disclaimer):
    e = html.escape
    none_text = labels["none"]
    laws = [labels["law_count"], labels["law_replay"], labels["law_order"],
            labels["law_change"], labels["law_quiet"],
            labels["law_notadvice"], labels["law_notpolicy"]]
    law_html = "".join("<p class=law>%s</p>" % e(line) for line in laws)
    cards = "".join(envelope_card(item, labels, e, none_text)
                    for item in envelopes)
    if not cards:
        cards = "<p class=empty>%s</p>" % e(labels["empty_market"])
    market_doc = market_html(market, labels, e, none_text)
    if not envelopes:
        market_doc += "<p class=empty>%s</p>" % e(labels["empty_market"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]), market_doc,
           e(labels["sec_boards"]), cards,
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
    market = payload.get("market") or {}
    extra = sorted(set(market) - set(MARKET_KEYS))
    missing = sorted(set(MARKET_KEYS) - set(market))
    if extra or missing:
        fails.append("market keys extra=%r missing=%r" % (extra, missing))
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
    doc = {key: envelope[key] for key in ENVELOPE_KEYS
           if key != "revisions"}
    doc["shelf"] = envelope.get("shelf") or ""
    doc["owner"] = envelope.get("owner") or ""
    doc["steps"] = []
    for step in envelope.get("steps") or []:
        item = {key: step[key] for key in REV_KEYS}
        item["changed"] = list(step.get("changed") or [])
        doc["steps"].append(item)
    doc.pop("revisions", None)
    return doc


def payload_of(envelopes, market, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "listing",
        "listings": [trim_envelope(item) for item in envelopes],
        "market": market,
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
    """AC-PWC52 (R3574): landing this pair and re-deriving the CEO face are ONE run.

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
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py "
                         "missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("LISTING-METADATA-HISTORY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelopes, meta = read_world()
        envelopes = _merge(meta, envelopes)
        market = _market(envelopes)
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(envelopes, market)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    disclaimer = (envelopes[0].get("disclaimer") if envelopes else "")
    doc = build_html(envelopes, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(envelopes, market, args.out, disclaimer, now)
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

    print("LISTING-METADATA-HISTORY %s bytes=%d listings=%d revisions=%d "
          "title=%d desc=%d both=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             market["listing_count"], market["revision_count"],
             market["title_changes"], market["description_changes"],
             market["both_changes"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
