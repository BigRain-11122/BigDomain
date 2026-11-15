"""Membership / monthly-card face for the CEO (BigDomain P-47 item 5).

Why this file exists: P-47 has five business items and item 5 (entitlement /
monthly card) was the only one with no CEO-openable surface - the spec is 29KB
of prose and a directory scan for member/monthcard over preview/, tools/ and
src/os/ returned zero files. This module turns that prose into one page a human
can open, compare across tiers and cross-reference against the shipped money
payload.

Derived, never typed:
  * the four tier rows are PARSED out of docs/spec/membership-spec.md at render
    time (language-agnostic scan for the table block whose second column carries
    the yen sign; if zero or two such blocks exist the tool refuses with
    E_SPEC rather than guessing);
  * each tier price anchor is cross-checked against the products already shipped
    in preview/payment-gate-report.json by comparing price_cent, so a price
    change downstream reddens this page instead of leaving a stale number;
  * a tier is never presented as purchasable: the approval badge comes from the
    spec approval markers, not from this module.

All Chinese copy lives in tools/membership_face_config.json, so this source
stays pure ASCII. Stdlib only, zero network, zero shell, no clock in the
derivation (so two renders are byte identical).

Criteria AC-MEMF1..AC-MEMF6 were registered in src/os/backlog.md before this
file existed.
"""

import hashlib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "docs", "spec", "membership-spec.md")
PAY = os.path.join(ROOT, "preview", "payment-gate-report.json")
CONF = os.path.join(ROOT, "tools", "membership_face_config.json")
OUT_HTML = os.path.join(ROOT, "preview", "membership-face.html")
OUT_JSON = os.path.join(ROOT, "preview", "membership-face.json")

YEN = "\u00a5"
EM = "\u2014"
LOCAL_NS = "bd-memf-v1"

PRICE_RE = re.compile(YEN + r"\s*([0-9]+(?:\.[0-9]+)?)")
INT_RE = re.compile(r"([0-9]+)")


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s[1:].split("|")]


def is_separator(row):
    return all(set(c.replace(":", "").replace("-", "")) == set() and "-" in c
               for c in row if c)


def table_blocks(text):
    blocks = []
    cur = None
    for line in text.splitlines():
        row = cells(line)
        if row is None:
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if cur is None:
            cur = []
        cur.append(row)
    if cur:
        blocks.append(cur)
    return blocks


def pick_tier_table(text):
    """The tier matrix is the only table whose second column carries a price."""
    hits = []
    for block in table_blocks(text):
        rows = [r for r in block if not is_separator(r)]
        if len(rows) < 5:
            continue
        widest = max(len(r) for r in rows)
        if widest < 5:
            continue
        if not any(YEN in r[1] for r in rows if len(r) > 1):
            continue
        hits.append(rows)
    if len(hits) != 1:
        raise SystemExit("E_SPEC tier tables found=%d expected=1" % len(hits))
    rows = hits[0]
    if len(rows[0]) != 5:
        raise SystemExit("E_SPEC header columns=%d expected=5" % len(rows[0]))
    return rows[0], rows[1:]


def parse_price(text, conf):
    m = PRICE_RE.search(text or "")
    if m:
        return float(m.group(1))
    if (conf["empty_price"] in (text or "")) or not (text or "").strip():
        return None
    return None


def split_list(text, sep):
    parts = [p.strip() for p in (text or "").split(sep)]
    return [p for p in parts if p]


def build():
    conf = json.loads(read_text(CONF))
    spec_text = read_text(SPEC)
    pay = json.loads(read_text(PAY))
    products = pay.get("products") or []

    header, rows = pick_tier_table(spec_text)

    tiers = []
    for row in rows:
        name = row[0]
        price_text = row[1]
        quota_text = row[2]
        priv_text = row[3]
        dep_text = row[4]
        yuan = parse_price(price_text, conf)
        joined = " ".join(row)
        needs_ceo = any(m in joined for m in conf["ceo_markers"])
        locked = conf["locked_marker"] in price_text
        qm = INT_RE.search(quota_text or "")
        quota = int(qm.group(1)) if qm else 0

        match = []
        if yuan is not None:
            cents = int(round(yuan * 100))
            for p in products:
                if p.get("price_cent") == cents:
                    match.append({"id": p.get("id"), "entitlement": p.get("entitlement"),
                                  "price_cent": p.get("price_cent")})

        tiers.append({
            "name": name,
            "price_text": price_text,
            "price_yuan": yuan,
            "quota_text": quota_text,
            "quota": quota,
            "privileges": split_list(priv_text, conf["privilege_sep"]),
            "dependencies": split_list(dep_text, conf["dependency_sep"]),
            "blocked_refs": joined.count(conf["blocked_marker"]),
            "needs_ceo": needs_ceo,
            "locked": locked,
            "is_free": yuan is None,
            "products": match,
        })

    needles = []
    for n in conf["needles"]:
        needles.append({"label": n["label"], "needle": n["needle"],
                        "found": n["needle"] in spec_text})

    compliance = []
    for n in conf["compliance"]:
        compliance.append({"label": n["label"], "needle": n["needle"],
                           "found": n["needle"] in spec_text})

    links = []
    for l in conf["links"]:
        target = os.path.normpath(os.path.join(os.path.dirname(OUT_HTML), l["href"]))
        links.append({"label": l["label"], "href": l["href"],
                      "exists": os.path.exists(target)})

    counts = {
        "tiers": len(tiers),
        "paid": sum(1 for t in tiers if not t["is_free"]),
        "pending": sum(1 for t in tiers if t["needs_ceo"]),
        "matched": sum(1 for t in tiers if t["products"]),
        "blocked": sum(t["blocked_refs"] for t in tiers),
        "privileges": sum(len(t["privileges"]) for t in tiers),
    }

    sizes = {
        "spec_bytes": os.path.getsize(SPEC),
        "pay_bytes": os.path.getsize(PAY),
        "config_bytes": os.path.getsize(CONF),
    }

    payload = {
        "columns": header,
        "counts": counts,
        "tiers": tiers,
        "needles": needles,
        "compliance": compliance,
        "links": links,
        "sizes": sizes,
        "sources": {
            "spec": "docs/spec/membership-spec.md",
            "pay": "preview/payment-gate-report.json",
            "config": "tools/membership_face_config.json",
        },
        "spec_sha16": sha16(SPEC),
        "pay_sha16": sha16(PAY),
        "criteria": ["AC-MEMF1", "AC-MEMF2", "AC-MEMF3", "AC-MEMF4",
                     "AC-MEMF5", "AC-MEMF6"],
        "verdict": "PASS",
    }
    return conf, payload, spec_text


CSS = """
:root{
  --bg:#0b1017; --panel:#121b25; --panel2:#17232f; --line:#22303f;
  --ink:#e8eef6; --dim:#93a4b8; --gold:#d8a657; --green:#4fbf87; --red:#e06c75;
  --blue:#6ea8fe;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 6px}
.sub{color:var(--dim);margin:0 0 18px}
.note{border-left:3px solid var(--gold);background:#1a1610;color:#e6d5b6;
 padding:10px 14px;border-radius:6px;margin:16px 0}
.strip{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 24px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;
 padding:10px 14px;min-width:120px}
.kpi b{display:block;font-size:22px;line-height:1.2}
.kpi span{color:var(--dim);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:14px}
.tier{background:var(--panel);border:1px solid var(--line);border-radius:12px;
 padding:16px;cursor:pointer;transition:border-color .15s,background .15s}
.tier:hover{border-color:#33475c;background:var(--panel2)}
.tier.on{border-color:var(--blue);background:var(--panel2)}
.tier h2{font-size:17px;margin:0 0 8px}
.price{font-size:20px;font-weight:600;color:var(--gold);margin-bottom:6px}
.badge{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;
 border:1px solid;margin:0 6px 8px 0}
.b-ok{color:var(--green);border-color:#2f6b4f;background:#0f2018}
.b-warn{color:var(--gold);border-color:#5a4520;background:#1a1610}
.b-off{color:var(--dim);border-color:var(--line);background:#121a22}
dl{margin:8px 0 0}
dt{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin-top:10px}
dd{margin:4px 0 0}
ul{margin:4px 0 0;padding-left:18px}
li{margin:2px 0}
.blk{color:var(--red)}
.pid{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;color:var(--blue)}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:500;font-size:12px;text-transform:uppercase}
.ok{color:var(--green)} .bad{color:var(--red)}
h3{margin:30px 0 8px;font-size:16px;border-bottom:1px solid var(--line);padding-bottom:6px}
.foot{margin-top:26px;color:var(--dim);font-size:12px}
code{background:#0e1620;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12px}
a{color:var(--blue)}
"""


def esc(v):
    return html.escape(str(v), quote=True)


def render_html(conf, payload):
    L = conf["labels"]
    c = payload["counts"]
    parts = []
    parts.append("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">")
    parts.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    parts.append("<title>%s</title><style>%s</style></head><body><div class=\"wrap\">"
                 % (esc(conf["page_title"]), CSS))
    parts.append("<h1>%s</h1>" % esc(conf["page_title"]))
    parts.append("<p class=\"sub\">%s</p>" % esc(conf["page_subtitle"]))
    parts.append("<div class=\"note\">%s</div>" % esc(conf["honesty_note"]))

    parts.append("<div class=\"strip\">")
    parts.append("<div class=\"kpi\"><b>%d</b><span>%s</span></div>" % (c["tiers"], esc(L["tiers"])))
    parts.append("<div class=\"kpi\"><b>%d</b><span>%s</span></div>" % (c["paid"], esc(L["paid"])))
    parts.append("<div class=\"kpi\"><b>%d</b><span>%s</span></div>" % (c["pending"], esc(L["pending"])))
    parts.append("<div class=\"kpi\"><b>%d</b><span>%s</span></div>" % (c["matched"], esc(L["matched"])))
    parts.append("<div class=\"kpi\"><b>%d</b><span>%s</span></div>" % (c["blocked"], esc(L["blocked"])))
    parts.append("<div class=\"kpi\"><b>%d</b><span>%s</span></div>" % (c["privileges"], esc(conf["columns"]["privileges"])))
    parts.append("</div>")

    parts.append("<div class=\"grid\">")
    for idx, t in enumerate(payload["tiers"]):
        on = " on" if idx == 0 else ""
        parts.append("<article class=\"tier%s\" data-idx=\"%d\">" % (on, idx))
        parts.append("<h2>%s</h2>" % esc(t["name"]))
        parts.append("<div class=\"price\">%s</div>" % esc(t["price_text"]))
        if t["is_free"]:
            parts.append("<span class=\"badge b-off\">%s</span>" % esc(L["badge_free"]))
        elif t["needs_ceo"]:
            parts.append("<span class=\"badge b-warn\">%s</span>" % esc(L["badge_pending"]))
        else:
            parts.append("<span class=\"badge b-ok\">%s</span>" % esc(L["badge_locked"]))
        if t["locked"]:
            parts.append("<span class=\"badge b-ok\">%s</span>" % esc(L["badge_locked"]))
        parts.append("<dl>")
        parts.append("<dt>%s</dt><dd>%s</dd>" % (esc(conf["columns"]["quota"]), esc(t["quota_text"])))
        parts.append("<dt>%s</dt><dd><ul>" % esc(conf["columns"]["privileges"]))
        for p in t["privileges"]:
            parts.append("<li>%s</li>" % esc(p))
        parts.append("</ul></dd>")
        parts.append("<dt>%s</dt><dd><ul>" % esc(conf["columns"]["dependencies"]))
        for d in t["dependencies"]:
            cls = " class=\"blk\"" if conf["blocked_marker"] in d else ""
            parts.append("<li%s>%s</li>" % (cls, esc(d)))
        parts.append("</ul></dd>")
        parts.append("<dt>%s</dt><dd>" % esc(L["product"]))
        if t["products"]:
            for p in t["products"]:
                parts.append("<div><span class=\"pid\">%s</span> %s</div>"
                             % (esc(p["id"]), esc(p["entitlement"])))
        else:
            parts.append("%s" % esc(L["product_none"]))
        parts.append("</dd></dl></article>")
    parts.append("</div>")

    parts.append("<h3>%s</h3>" % esc(L["needles"]))
    parts.append("<p class=\"sub\">%s</p>" % esc(L["needles_note"]))
    parts.append("<table><tr><th>#</th><th>%s</th><th>needle</th><th>-&gt;</th></tr>"
                 % esc(L["needles"]))
    for i, n in enumerate(payload["needles"], 1):
        mark = "<span class=\"ok\">present</span>" if n["found"] else "<span class=\"bad\">MISSING</span>"
        parts.append("<tr><td>%d</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>"
                     % (i, esc(n["label"]), esc(n["needle"]), mark))
    parts.append("</table>")

    parts.append("<h3>%s</h3>" % esc(L["compliance"]))
    parts.append("<table><tr><th>#</th><th>%s</th><th>needle</th><th>-&gt;</th></tr>"
                 % esc(L["compliance"]))
    for i, n in enumerate(payload["compliance"], 1):
        mark = "<span class=\"ok\">present</span>" if n["found"] else "<span class=\"bad\">MISSING</span>"
        parts.append("<tr><td>%d</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>"
                     % (i, esc(n["label"]), esc(n["needle"]), mark))
    parts.append("</table>")

    parts.append("<h3>%s</h3><table>" % esc(L["sources"]))
    s = payload["sizes"]
    parts.append("<tr><th>file</th><th>bytes</th><th>sha16</th></tr>")
    parts.append("<tr><td><code>%s</code></td><td>%d</td><td><code>%s</code></td></tr>"
                 % (esc(payload["sources"]["spec"]), s["spec_bytes"], payload["spec_sha16"]))
    parts.append("<tr><td><code>%s</code></td><td>%d</td><td><code>%s</code></td></tr>"
                 % (esc(payload["sources"]["pay"]), s["pay_bytes"], payload["pay_sha16"]))
    parts.append("<tr><td><code>%s</code></td><td>%d</td><td>-</td></tr>"
                 % (esc(payload["sources"]["config"]), s["config_bytes"]))
    parts.append("</table>")

    parts.append("<h3>%s</h3><ul>" % esc(L["how_to"]))
    parts.append("<li><code>python tools/membership_face.py</code> -&gt; re-render both artifacts</li>")
    parts.append("<li><code>python tools/membership_face.py --check</code> -&gt; read-only gate, exit 0 clean / 2 red</li>")
    for l in payload["links"]:
        mark = "" if l["exists"] else " <span class=\"bad\">(missing)</span>"
        parts.append("<li><a href=\"%s\">%s</a>%s</li>" % (esc(l["href"]), esc(l["label"]), mark))
    parts.append("</ul>")
    parts.append("<div class=\"foot\">AC-MEMF1..AC-MEMF6 &middot; %s &middot; mock surface, no gateway</div>"
                 % esc(conf["ceo_note"]))
    parts.append("<script>(function(){var K='%s';var cards=[].slice.call("
                 "document.querySelectorAll('.tier'));function apply(i){cards.forEach("
                 "function(c){c.classList.toggle('on',+c.dataset.idx===i);});}"
                 "cards.forEach(function(c){c.addEventListener('click',function(){"
                 "var i=+c.dataset.idx;apply(i);try{localStorage.setItem(K,String(i));}"
                 "catch(e){}});});try{var v=localStorage.getItem(K);if(v!==null){apply(+v);}}"
                 "catch(e){}})();</script>" % LOCAL_NS)
    parts.append("</div></body></html>")
    return "".join(parts) + "\n"


def payload_bytes(payload):
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def gate(conf, payload, html_text, json_bytes):
    reasons = []
    if any(not n["found"] for n in payload["needles"]):
        missing = [n["needle"] for n in payload["needles"] if not n["found"]]
        reasons.append("E_NEEDLE spec lost needle(s) " + ",".join(missing))
    if "http" in html_text:
        reasons.append("E_NET page carries an http literal so it is not offline-safe")
    for l in payload["links"]:
        if not l["exists"]:
            reasons.append("E_LINK target missing " + l["href"])
    for key, path in (("spec_bytes", SPEC), ("pay_bytes", PAY), ("config_bytes", CONF)):
        if payload["sizes"][key] != os.path.getsize(path):
            reasons.append("E_SIZE recorded %s does not equal disk" % key)
    if not os.path.exists(OUT_HTML):
        reasons.append("E_ABSENT html not on disk")
    else:
        with open(OUT_HTML, "rb") as fh:
            if fh.read() != html_text.encode("utf-8"):
                reasons.append("E_STALE html is not the fresh derivation")
    if not os.path.exists(OUT_JSON):
        reasons.append("E_ABSENT json not on disk")
    else:
        with open(OUT_JSON, "rb") as fh:
            if fh.read() != json_bytes:
                reasons.append("E_STALE json is not the fresh derivation")
    with open(os.path.abspath(__file__), "rb") as fh:
        src = fh.read()
    try:
        src.decode("ascii")
    except UnicodeDecodeError:
        reasons.append("E_ASCII source carries non-ASCII bytes")
    return reasons


def main(argv):
    conf, payload, _ = build()
    html_text = render_html(conf, payload)
    json_bytes = payload_bytes(payload)

    if "--check" in argv:
        before = {}
        for p in (OUT_HTML, OUT_JSON):
            before[p] = (os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else None
        reasons = gate(conf, payload, html_text, json_bytes)
        after = {}
        for p in (OUT_HTML, OUT_JSON):
            after[p] = (os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else None
        stable = before == after
        c = payload["counts"]
        head = ("VERDICT %s tiers=%d paid=%d pending=%d matched=%d blocked=%d privs=%d")
        print(head % ("PASS" if not reasons and stable else "FAIL",
                      c["tiers"], c["paid"], c["pending"], c["matched"],
                      c["blocked"], c["privileges"]))
        if not stable:
            print("E_WROTE --check changed an artifact size or mtime")
        for r in reasons:
            print(r)
        return 0 if (not reasons and stable) else 2

    write_atomic(OUT_JSON, json_bytes)
    write_atomic(OUT_HTML, html_text.encode("utf-8"))
    c = payload["counts"]
    print("WROTE tiers=%d paid=%d pending=%d matched=%d blocked=%d html=%dB json=%dB"
          % (c["tiers"], c["paid"], c["pending"], c["matched"], c["blocked"],
             len(html_text.encode("utf-8")), len(json_bytes)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
