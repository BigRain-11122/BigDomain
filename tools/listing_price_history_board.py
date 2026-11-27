"""Listing asking-price history board (R3482).

WHY THIS PAGE EXISTS (measured at R3482, not assumed):
api_price_history shipped ONE listing's asking-price history - the immutable
base price plus every append-only revision in order, the current price and the
revision count - but a search over tools/, preview/ and src/os answered rc=1
for its name, so a seller's whole repricing trail could only be read by calling
the sandbox from a shell. The seller cadence page (R3442) answers a different
question: that one is seller x month, this one is one shelf's complete trail
with who moved it, by how much, and in which direction.
This page opens the trail the face already carries; it adds no table, no
reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-LPHB1..AC-LPHB6, fixed in this
round's window before the first render; the src/os/backlog.md R3482 PIN row
landed before any driver code):
  - revision_count == len(revisions)
  - replay: start at base_price, each step's previous is the last step's new,
    and the last new equals current_price; with no revision current == base
  - every step token_price > 0 and differs from the price it replaced
  - revision_id strictly ascending and revised_utc never moves backwards
  - up + down == revision_count; the largest step is taken by absolute
    difference and the tie goes to the earliest revision
  - a shelf with no revision says so in words: no empty table, no invented row

Every number on the page comes from the shipped face. Chinese labels live in
preview/listing-price-history-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "listing-price-history-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "listing-price-history-board.json")
COPY = os.path.join(ROOT, "preview", "listing-price-history-board-copy.json")

FACE = "api_price_history"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "listings", "market", "disclaimer",
    "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "listing_id", "base_price", "current_price", "revision_count",
    "delisted", "delisted_utc", "revisions", "disclaimer",
)

REV_KEYS = ("revision_id", "dev_account", "token_price", "revised_utc")

MARKET_KEYS = (
    "listing_count", "revision_count", "up_count", "down_count",
    "max_step_delta", "max_step_listing", "max_step_revision",
    "max_step_pct", "peak_month", "peak_month_revisions", "busiest_listing",
    "busiest_revisions",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_boards", "sec_law", "sec_disc", "sec_rep",
    "m_listings", "m_revisions", "m_up", "m_down", "m_max_step",
    "m_max_pct", "m_peak_month", "m_busiest",
    "b_base", "b_current", "b_revisions", "b_net", "b_span", "b_status",
    "col_rev", "col_who", "col_prev", "col_new", "col_delta", "col_pct",
    "col_when",
    "badge_up", "badge_down", "badge_live", "badge_delisted", "badge_count",
    "empty", "empty_market", "none", "span_suffix",
    "law_count", "law_replay", "law_noop", "law_order", "law_direction",
    "law_quiet", "law_notadvice",
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
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:18px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.up{border-color:#9ad1a7;background:#eef9f1;color:#1f6b33}
.badge.down{border-color:#e4b9b9;background:#fdeff1;color:#8a2338}
.badge.off{border-color:#c9c9c9;background:#f2f2f2;color:#555}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"

# One pinned clock drives every write so the trail reproduces.
STAMP = {"value": "2026-11-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_LPHB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_LPHB_LAW"


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

    The factory world carries three listings and zero price revisions, so every
    revision here is made through the shipped revise_price door under the
    pinned clock. risk-scan walks down then up then up again (three steps, two
    up one down), macro-feed moves once, and chart-render is never repriced -
    which is the face's own honest quiet shape.
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

    STAMP["value"] = "2026-09-05T00:00:00Z"
    am.revise_price(owners["risk-scan"], risk, 12)
    STAMP["value"] = "2026-10-02T00:00:00Z"
    am.revise_price(owners["risk-scan"], risk, 9)
    STAMP["value"] = "2026-11-08T00:00:00Z"
    am.revise_price(owners["risk-scan"], risk, 15)
    STAMP["value"] = "2026-10-20T00:00:00Z"
    am.revise_price(owners["macro-feed"], macro, 4)
    shelf_by_id = {risk: "risk-scan", macro: "macro-feed",
                   chart: "chart-render"}
    return [risk, macro, chart], {"by_id": shelf_by_id}


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="lphb-")
    db = os.path.join(tmp_root, "lphb.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        ids, owners = build_world(am)
        envelopes = [dict(am.api_price_history(listing_id))
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
    return envelopes, owners


def _month(utc):
    return str(utc)[:7]


def _merge(owners, envelopes):
    """Attach the shelf name and owner the board carries, for the page only."""
    rows = []
    for envelope in envelopes:
        doc = dict(envelope)
        doc["shelf"] = owners["by_id"].get(int(envelope["listing_id"]), "")
        doc["owner"] = (envelope.get("revisions") or [{}])[0].get(
            "dev_account") or ""
        rows.append(doc)
    return rows


def _market(envelopes):
    up = down = 0
    revisions = 0
    best = None
    for envelope in envelopes:
        previous = int(envelope["base_price"])
        for rev in envelope.get("revisions") or []:
            price = int(rev["token_price"])
            delta = price - previous
            revisions += 1
            if delta > 0:
                up += 1
            elif delta < 0:
                down += 1
            if best is None or abs(delta) > abs(best["delta"]):
                best = {"delta": delta, "pct": round(delta * 100.0
                                                    / previous, 2),
                        "listing": int(envelope["listing_id"]),
                        "revision": int(rev["revision_id"]),
                        "month": _month(rev["revised_utc"])}
            previous = price
    counts = {}
    for envelope in envelopes:
        for rev in envelope.get("revisions") or []:
            key = _month(rev["revised_utc"])
            counts[key] = counts.get(key, 0) + 1
    peak_month = None
    peak_count = 0
    for key in sorted(counts):
        if counts[key] > peak_count:
            peak_month, peak_count = key, counts[key]
    busiest = None
    busiest_count = 0
    for envelope in sorted(envelopes, key=lambda e: int(e["listing_id"])):
        count = len(envelope.get("revisions") or [])
        if count > busiest_count:
            busiest, busiest_count = int(envelope["listing_id"]), count
    return {
        "listing_count": len(envelopes),
        "revision_count": revisions,
        "up_count": up,
        "down_count": down,
        "max_step_delta": best["delta"] if best else None,
        "max_step_listing": best["listing"] if best else None,
        "max_step_revision": best["revision"] if best else None,
        "max_step_pct": best["pct"] if best else None,
        "peak_month": peak_month,
        "peak_month_revisions": peak_count,
        "busiest_listing": busiest,
        "busiest_revisions": busiest_count,
    }


def check_laws(envelopes, market):
    problems = []
    up = down = 0
    revisions = 0
    for envelope in envelopes:
        tag = "listing %s" % envelope.get("listing_id")
        rows = envelope.get("revisions") or []
        if int(envelope.get("revision_count", -1)) != len(rows):
            problems.append("%s revision_count %r != %d rows"
                            % (tag, envelope.get("revision_count"),
                               len(rows)))
        previous = int(envelope["base_price"])
        last_id = None
        last_utc = None
        for rev in rows:
            price = int(rev["token_price"])
            if price <= 0:
                problems.append("%s revision %r carries price %d"
                                % (tag, rev["revision_id"], price))
            if price == previous:
                problems.append("%s revision %r repeats price %d"
                                % (tag, rev["revision_id"], price))
            if last_id is not None and int(rev["revision_id"]) <= last_id:
                problems.append("%s revision ids not ascending at %r"
                                % (tag, rev["revision_id"]))
            if last_utc is not None and str(rev["revised_utc"]) < last_utc:
                problems.append("%s revision time moved backwards at %r"
                                % (tag, rev["revision_id"]))
            last_id = int(rev["revision_id"])
            last_utc = str(rev["revised_utc"])
            if price > previous:
                up += 1
            elif price < previous:
                down += 1
            revisions += 1
            previous = price
        if int(envelope["current_price"]) != previous:
            problems.append("%s current %r != replayed %d"
                            % (tag, envelope["current_price"], previous))
        if not rows and int(envelope["current_price"]) != int(
                envelope["base_price"]):
            problems.append("%s quiet shelf current %r != base %r"
                            % (tag, envelope["current_price"],
                               envelope["base_price"]))
    if market["revision_count"] != revisions:
        problems.append("market revision_count %r != %d"
                        % (market["revision_count"], revisions))
    if market["up_count"] != up or market["down_count"] != down:
        problems.append("market up/down %r/%r != %d/%d"
                        % (market["up_count"], market["down_count"],
                           up, down))
    if up + down != revisions:
        problems.append("direction split %d + %d != %d" % (up, down,
                                                           revisions))
    if market["listing_count"] != len(envelopes):
        problems.append("market listing_count %r != %d"
                        % (market["listing_count"], len(envelopes)))
    return problems


def text(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def market_html(market, labels, e, none_text):
    cells = (
        ("m_listings", market["listing_count"]),
        ("m_revisions", market["revision_count"]),
        ("m_up", market["up_count"]),
        ("m_down", market["down_count"]),
        ("m_max_step", market["max_step_delta"]),
        ("m_max_pct", market["max_step_pct"]),
        ("m_peak_month", market["peak_month"]),
        ("m_busiest", market["busiest_listing"]),
    )
    out = []
    for key, value in cells:
        if key == "m_max_pct" and value is not None:
            shown = "%s%s" % (text(value, none_text), labels["span_suffix"])
        else:
            shown = text(value, none_text)
        out.append("<div><b>%s</b><span>%s</span></div>"
                   % (e(shown), e(labels[key])))
    return "<div class=kpi>%s</div>" % "".join(out)


def envelope_card(envelope, labels, e, none_text):
    rows = envelope.get("revisions") or []
    badge = '<span class="badge off">%s</span>' % e(
        labels["badge_delisted"] if envelope.get("delisted")
        else labels["badge_live"])
    counts = '<span class="badge">%s %s</span>' % (
        e(str(int(envelope["revision_count"]))), e(labels["badge_count"]))
    span = None
    if rows:
        low = min([int(envelope["base_price"])]
                  + [int(rev["token_price"]) for rev in rows])
        high = max([int(envelope["base_price"])]
                   + [int(rev["token_price"]) for rev in rows])
        span = "%d .. %d" % (low, high)
    cells = (
        ("b_base", envelope["base_price"]),
        ("b_current", envelope["current_price"]),
        ("b_revisions", envelope["revision_count"]),
        ("b_net", int(envelope["current_price"])
         - int(envelope["base_price"])),
        ("b_span", span),
    )
    kpi = "".join("<div><b>%s</b><span>%s</span></div>"
                  % (e(text(value, none_text)), e(labels[key]))
                  for key, value in cells)
    if not rows:
        table = '<p class=empty>%s</p>' % e(labels["empty"])
    else:
        head = "".join("<th%s>%s</th>" % (" class=n" if key != "col_who"
                                          and key != "col_when" else "",
                                          e(labels[key]))
                       for key in ("col_rev", "col_who", "col_prev",
                                   "col_new", "col_delta", "col_pct",
                                   "col_when"))
        previous = int(envelope["base_price"])
        body = []
        for rev in rows:
            price = int(rev["token_price"])
            delta = price - previous
            pct = round(delta * 100.0 / previous, 2)
            kind = "up" if delta > 0 else "down"
            body.append(
                "<tr><td class=n>%d</td><td>%s</td>"
                "<td class=n>%d</td><td class=n>%d</td>"
                '<td class=n><span class="badge %s">%+d</span></td>'
                "<td class=n>%+.2f%s</td><td>%s</td></tr>"
                % (int(rev["revision_id"]), e(str(rev["dev_account"])),
                   previous, price, kind, delta, pct,
                   e(labels["span_suffix"]), e(str(rev["revised_utc"]))))
            previous = price
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
    laws = [labels["law_count"], labels["law_replay"], labels["law_noop"],
            labels["law_order"], labels["law_direction"], labels["law_quiet"],
            labels["law_notadvice"]]
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
    """AC-PWC59 (R3581): landing this pair and re-deriving the CEO face are ONE run.

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
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "revisions"}
    doc["shelf"] = envelope.get("shelf") or ""
    doc["revisions"] = [{key: row[key] for key in REV_KEYS}
                        for row in envelope.get("revisions") or []]
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
        print("LISTING-PRICE-HISTORY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelopes, owners = read_world()
        envelopes = _merge(owners, envelopes)
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
    print("LISTING-PRICE-HISTORY %s bytes=%d listings=%d revisions=%d "
          "up=%d down=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             market["listing_count"], market["revision_count"],
             market["up_count"], market["down_count"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
