"""Provider identity board (R3457).

WHY THIS PAGE EXISTS (measured at R3457, not assumed):
api_provider_identity shipped the per-developer real-name face - the
registration flag, the published provider name, the unified social credit code,
the registration stamp and whether disclosure is complete - but a search over
tools/, preview/ and src/os answered zero readers for its name. api_public_
listings carries the provider columns inside one shelf row and
api_market_provider_months carries the market's monthly registration churn,
so "who is behind each shelf, since when, and which developers are still
undisclosed" could only be read by calling the sandbox from a shell. This page
opens the axis the face already carries; it adds no table, no reading and no
business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-PIDB3, fixed in this round's window
before the first render; the src/os/backlog.md R3457 PIN row landed with the
driver and says so):
  - registered is true exactly when provider_name, credit_code and
    registered_utc are all non-None, and disclosure_ok equals registered
  - an undisclosed developer carries four None fields and disclosure_ok False;
    an empty string never stands in for a missing identity
  - the market developer count equals the number of developer entries, and
    registered + undisclosed == developer count
  - the disclosure rate is the registered share rounded to four places, and
    None (never a fabricated zero) when there are no developers
  - the earliest and latest registration stamps are the min and max of the
    non-None stamps, and None when nobody is registered
  - every registered credit code is distinct - one code names one provider -
    and every name and code is trimmed and non-empty, the code at most 64
    characters and the name at most 120
  - the oldest undisclosed developer is the undisclosed shelf owner with the
    earliest first-listing stamp, ties going to the smallest dev_account, and
    None when every developer is disclosed or no undisclosed developer has a
    shelf stamp
  - developer entries are ordered by dev_account ascending, and every entry
    comes from the shipped market search - the page never invents a developer
  - the bare world answers zero developers, a None rate and every stamp None

Every number on the page comes from the shipped faces. Chinese labels live in
preview/provider-identity-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "provider-identity-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "provider-identity-board.json")
COPY = os.path.join(ROOT, "preview", "provider-identity-board-copy.json")

FACE = "api_provider_identity"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "market", "developers",
    "disclaimer", "report", "sources", "sizes",
)

MARKET_KEYS = (
    "developer_count", "registered_count", "undisclosed_count",
    "disclosure_rate", "earliest_registered_utc", "latest_registered_utc",
    "oldest_undisclosed_dev", "oldest_undisclosed_listed_utc",
    "distinct_credit_code_count",
)

DEV_KEYS = ("dev_account", "registered", "provider_name", "credit_code",
            "registered_utc", "disclosure_ok", "listing_count",
            "earliest_listed_utc")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_devs", "sec_law", "sec_disc", "sec_rep",
    "kpi_devs", "kpi_registered", "kpi_undisclosed", "kpi_rate",
    "kpi_earliest", "kpi_latest", "kpi_oldest_dev", "kpi_oldest_listed",
    "kpi_codes",
    "col_dev", "col_state", "col_name", "col_code", "col_registered",
    "col_shelves", "col_earliest_listed",
    "badge_disclosed", "badge_undisclosed",
    "law_registered", "law_none", "law_counts", "law_rate", "law_stamps",
    "law_codes", "law_oldest", "law_order", "law_zero", "law_scope",
    "law_notadvice",
    "empty", "none", "clip_caption", "clip_mark",
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
STAMP = {"value": "2026-08-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_PIDB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_PIDB_LAW"


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


def build_world(am, dk):
    """One landed identity story, every row by door.

    The factory world carries two sellers (dana, frank) and ZERO provider
    registration, so both registrations, both extra shelves and the one
    identity revision below are made through the shipped issue_key,
    publish_api, register_provider and revise_provider doors under the pinned
    clock - no sqlite rewrite, no typed ids, no padded rows. The story
    exercises the laws on purpose: dana registers and later revises both name
    and credit code (the effective pair moves, the registration stamp does
    not), gina registers and never revises, frank and helen never register at
    all (the honest undisclosed branch), and helen's shelf predates frank's so
    the oldest-undisclosed tie-break has a real answer.
    """
    STAMP["value"] = "2026-08-01T00:00:00Z"
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    dk.issue_key("usr:helen", "helen-key", 10, ["backtest"], False)
    am.register_provider("usr:dana", "Dana Labs", "91310000MA1K3XYZ12")

    STAMP["value"] = "2026-08-05T00:00:00Z"
    am.register_provider("usr:gina", "Gina Studio", "91310000MA1K3ABC34")

    STAMP["value"] = "2026-08-10T00:00:00Z"
    am.publish_api("usr:gina", "gina-api", "Gina API", "demo",
                   {"ep": "gina"}, 6, False, supply=4)

    STAMP["value"] = "2026-08-12T00:00:00Z"
    am.publish_api("usr:helen", "helen-api", "Helen API", "demo",
                   {"ep": "helen"}, 4, False, supply=3)

    STAMP["value"] = "2026-09-10T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="Dana Labs Co., Ltd.",
                       credit_code="91310000MA1K3XYZ99")


def _shelf_stats(am):
    """Every shelf owner the market holds, retired shelves included.

    api_search publishes the owner but not the publication stamp, so each
    shelf is re-read through api_view - the shipped per-listing face that
    carries listed_utc for live and retired shelves alike.
    """
    stats = {}
    for row in am.api_search(include_delisted=True).get("listings") or []:
        dev = row.get("dev_account")
        if not dev:
            continue
        cell = stats.setdefault(
            dev, {"listing_count": 0, "earliest_listed_utc": None})
        cell["listing_count"] += 1
        stamp = am.api_view(int(row["listing_id"])).get("listed_utc")
        if stamp and (cell["earliest_listed_utc"] is None
                      or stamp < cell["earliest_listed_utc"]):
            cell["earliest_listed_utc"] = stamp
    return stats


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="pid-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "pid.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am, dk)
        stats = _shelf_stats(am)
        rows = []
        for dev in sorted(stats):
            envelope = dict(am.api_provider_identity(dev))
            if envelope.get("dev_account") != dev:
                raise FaceError("identity %r drifted to %r"
                                % (dev, envelope.get("dev_account")))
            row = {"dev_account": dev}
            for name in DEV_KEYS:
                if name == "dev_account":
                    continue
                if name in ("listing_count", "earliest_listed_utc"):
                    row[name] = stats[dev][name]
                else:
                    row[name] = envelope[name]
            rows.append(row)
        sellers = sorted(stats)
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
    for row in rows:
        missing = [name for name in DEV_KEYS if name not in row]
        if missing:
            raise FaceError("row keys missing for %r: %s"
                            % (row.get("dev_account"), ",".join(missing)))
    return rows, sellers


def read_empty():
    """One honest undisclosed envelope on the bare stack: four Nones, False."""
    tmp_root = tempfile.mkdtemp(prefix="pid-empty-")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "bare.db"))
        R.seed_demo(am, led, dk)
        envelope = dict(am.api_provider_identity("usr:dana"))
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


def derive_market(rows):
    """AC-PIDB3 read at the source: every market number is derived."""
    registered = [row for row in rows if row["registered"]]
    undisclosed = [row for row in rows if not row["registered"]]
    stamps = [row["registered_utc"] for row in registered
              if row["registered_utc"]]
    codes = {row["credit_code"] for row in registered
             if row["credit_code"]}
    oldest_dev = None
    oldest_stamp = None
    for row in sorted(undisclosed,
                      key=lambda item: (item["earliest_listed_utc"] or "",
                                        item["dev_account"])):
        if row["earliest_listed_utc"]:
            oldest_dev = row["dev_account"]
            oldest_stamp = row["earliest_listed_utc"]
            break
    return {
        "developer_count": len(rows),
        "registered_count": len(registered),
        "undisclosed_count": len(undisclosed),
        "disclosure_rate": (round(len(registered) / float(len(rows)), 4)
                            if rows else None),
        "earliest_registered_utc": min(stamps) if stamps else None,
        "latest_registered_utc": max(stamps) if stamps else None,
        "oldest_undisclosed_dev": oldest_dev,
        "oldest_undisclosed_listed_utc": oldest_stamp,
        "distinct_credit_code_count": len(codes),
    }


def check_laws(rows, market, empty):
    """AC-PIDB3 read at the source: refuse rather than print."""
    problems = []
    seen = set()
    registered = 0
    stamps = []
    codes = []
    undisclosed = []
    previous = None
    for row in rows:
        dev = row.get("dev_account")
        if not isinstance(dev, str) or not dev.startswith("usr:"):
            problems.append("bad dev_account %r" % (dev,))
            continue
        if dev in seen:
            problems.append("developer %r appears twice" % (dev,))
        seen.add(dev)
        if previous is not None and dev < previous:
            problems.append("developer %r out of ascending order" % (dev,))
        previous = dev
        fields = (row["provider_name"], row["credit_code"],
                  row["registered_utc"])
        complete = all(value is not None for value in fields)
        if bool(row["registered"]) != complete:
            problems.append("%r registered %r != complete %r"
                            % (dev, row["registered"], complete))
        if bool(row["disclosure_ok"]) != bool(row["registered"]):
            problems.append("%r disclosure_ok %r != registered %r"
                            % (dev, row["disclosure_ok"], row["registered"]))
        if not row["registered"]:
            if any(value is not None for value in fields):
                problems.append("%r undisclosed but carries identity" % (dev,))
            undisclosed.append(row)
        else:
            registered += 1
            stamps.append(row["registered_utc"])
            codes.append(row["credit_code"])
            name = row["provider_name"]
            code = row["credit_code"]
            if not isinstance(name, str) or not name.strip() or name != name.strip():
                problems.append("%r provider name %r not trimmed non-empty"
                                % (dev, name))
            if len(str(name or "")) > 120:
                problems.append("%r provider name too long" % (dev,))
            if not isinstance(code, str) or not code.strip() or code != code.strip():
                problems.append("%r credit code %r not trimmed non-empty"
                                % (dev, code))
            if len(str(code or "")) > 64:
                problems.append("%r credit code too long" % (dev,))
        count = int(row["listing_count"])
        if count < 1:
            problems.append("%r carries %r shelves, scope is shelf owners"
                            % (dev, row["listing_count"]))
        if row["earliest_listed_utc"] is None:
            problems.append("%r has shelves but no earliest stamp" % (dev,))
    if int(market["developer_count"]) != len(rows):
        problems.append("market developers %r != %d"
                        % (market["developer_count"], len(rows)))
    if int(market["registered_count"]) != registered:
        problems.append("market registered %r != %d"
                        % (market["registered_count"], registered))
    if int(market["undisclosed_count"]) != len(undisclosed):
        problems.append("market undisclosed %r != %d"
                        % (market["undisclosed_count"], len(undisclosed)))
    if int(market["registered_count"]) + \
            int(market["undisclosed_count"]) != len(rows):
        problems.append("market registered + undisclosed != %d" % len(rows))
    want_rate = (round(registered / float(len(rows)), 4) if rows else None)
    got_rate = market["disclosure_rate"]
    if want_rate is None:
        if got_rate is not None:
            problems.append("market rate %r should be None" % (got_rate,))
    elif got_rate is None or abs(float(got_rate) - want_rate) > 1e-9:
        problems.append("market rate %r != %r" % (got_rate, want_rate))
    if market["earliest_registered_utc"] != (min(stamps) if stamps else None):
        problems.append("market earliest %r != %r"
                        % (market["earliest_registered_utc"],
                           min(stamps) if stamps else None))
    if market["latest_registered_utc"] != (max(stamps) if stamps else None):
        problems.append("market latest %r != %r"
                        % (market["latest_registered_utc"],
                           max(stamps) if stamps else None))
    if len(set(codes)) != len(codes):
        problems.append("duplicate credit code across providers")
    if int(market["distinct_credit_code_count"]) != len(set(codes)):
        problems.append("market distinct codes %r != %d"
                        % (market["distinct_credit_code_count"],
                           len(set(codes))))
    want_dev = None
    want_stamp = None
    for row in sorted(undisclosed,
                      key=lambda item: (item["earliest_listed_utc"] or "",
                                        item["dev_account"])):
        if row["earliest_listed_utc"]:
            want_dev = row["dev_account"]
            want_stamp = row["earliest_listed_utc"]
            break
    if market["oldest_undisclosed_dev"] != want_dev:
        problems.append("market oldest undisclosed %r != %r"
                        % (market["oldest_undisclosed_dev"], want_dev))
    if market["oldest_undisclosed_listed_utc"] != want_stamp:
        problems.append("market oldest listed %r != %r"
                        % (market["oldest_undisclosed_listed_utc"],
                           want_stamp))
    if empty.get("registered") is not False:
        problems.append("bare envelope registered %r is not False"
                        % (empty.get("registered"),))
    if empty.get("disclosure_ok") is not False:
        problems.append("bare envelope disclosure_ok %r is not False"
                        % (empty.get("disclosure_ok"),))
    for name in ("provider_name", "credit_code", "registered_utc"):
        if empty.get(name) is not None:
            problems.append("bare %s %r is not None" % (name, empty.get(name)))
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
        return ("%.4f" % value).rstrip("0").rstrip(".")
    return str(value)


def rate_text(value, none_text):
    if value is None:
        return none_text
    return "%.1f%%" % (float(value) * 100.0)


def kpi_html(pairs, e, dash):
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(str(value)))
                   for name, value in pairs)


def dev_card(row, labels, e, dash):
    dev = row["dev_account"]
    badges = []
    if row["registered"]:
        badges.append('<span class="badge on">%s</span>'
                      % e(labels["badge_disclosed"]))
    else:
        badges.append('<span class="badge off">%s</span>'
                      % e(labels["badge_undisclosed"]))
    body = [
        "<tr><th>%s</th><td>%s</td></tr>" % (e(labels["col_name"]),
                                              e(text(row["provider_name"],
                                                     dash))),
        "<tr><th>%s</th><td>%s</td></tr>" % (e(labels["col_code"]),
                                              e(text(row["credit_code"],
                                                     dash))),
        "<tr><th>%s</th><td>%s</td></tr>" % (e(labels["col_registered"]),
                                              e(text(row["registered_utc"],
                                                     dash))),
        "<tr><th>%s</th><td>%s</td></tr>" % (e(labels["col_shelves"]),
                                              e(text(row["listing_count"],
                                                     dash))),
        "<tr><th>%s</th><td>%s</td></tr>"
        % (e(labels["col_earliest_listed"]),
           e(text(row["earliest_listed_utc"], dash))),
    ]
    quiet = "" if row["registered"] else "<p class=empty>%s</p>" % e(
        labels["empty"])
    return ('<div class=card data-dev="%s"><h3 style="margin:0 0 8px;'
            'font-size:14px">%s</h3><p class=qa>%s</p>%s'
            '<table><tbody>%s</tbody></table></div>'
            % (e(dev), e(dev), "".join(badges), quiet, "".join(body)))


def build_html(rows, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_registered"], labels["law_none"],
            labels["law_counts"], labels["law_rate"], labels["law_stamps"],
            labels["law_codes"], labels["law_oldest"], labels["law_order"],
            labels["law_zero"], labels["law_scope"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    market_pairs = [
        (labels["kpi_devs"], text(market.get("developer_count"), dash)),
        (labels["kpi_registered"], text(market.get("registered_count"), dash)),
        (labels["kpi_undisclosed"], text(market.get("undisclosed_count"),
                                          dash)),
        (labels["kpi_rate"], rate_text(market.get("disclosure_rate"), dash)),
        (labels["kpi_earliest"],
         text(market.get("earliest_registered_utc"), dash)),
        (labels["kpi_latest"], text(market.get("latest_registered_utc"),
                                     dash)),
        (labels["kpi_oldest_dev"],
         text(market.get("oldest_undisclosed_dev"), dash)),
        (labels["kpi_oldest_listed"],
         text(market.get("oldest_undisclosed_listed_utc"), dash)),
        (labels["kpi_codes"], text(market.get("distinct_credit_code_count"),
                                   dash)),
    ]
    market_html = ('<div class=card><div class=kpi>%s</div>'
                   '<p class=cap>%s</p></div>'
                   % (kpi_html(market_pairs, e, dash),
                      e(labels["clip_caption"])))
    cards = "".join(dev_card(row, labels, e, dash) for row in rows)
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
           e(labels["sec_devs"]), cards,
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


def payload_of(rows, market, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "developers",
        "market": market,
        "developers": rows,
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
    """AC-PWC34 (R3556): landing this pair and re-deriving the CEO face are ONE run.

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
        print("PROVIDER-IDENTITY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        rows, sellers = read_world()
        empty = read_empty()
        market = derive_market(rows)
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    try:
        problems = check_laws(rows, market, empty)
    except LawError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = empty.get("disclaimer")
    doc = build_html(rows, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(rows, market, args.out, disclaimer, now)
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

    print("PROVIDER-IDENTITY %s bytes=%d developers=%d registered=%d "
          "undisclosed=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             int(market["developer_count"]), int(market["registered_count"]),
             int(market["undisclosed_count"]), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
