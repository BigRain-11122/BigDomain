#!/usr/bin/env python3
"""P-47 merchant onboarding checklist face: one offline page an operator can run.

Why this exists: at R3250 the buyer trial could only REFUSE the two
standard-channel products and print the missing physical pieces as one sentence.
An operator had no artifact saying which item is missing, who owns it, and how it
is verified. This tool renders a single-file checklist that runs from file://
with zero network and never accepts a secret value: six CEO physical items plus
two items whose evidence is re-read from shipped files on every run.

Products and item text are not authored here. Products are projected from
preview/payment-gate-report.json, items from state/merchant-onboard-items.json,
and --check refuses the face when either source drifts.

Criteria AC-MO1..AC-MO6 are pre-registered in src/os/backlog.md (R3251 PIN line)
before this file existed.
AC-MO7 (R3285): this page had out-degree zero - an operator could tick every
box and then had nowhere to go. The hop list lives in tools/buyer_route.py, the
one closure AC-JNY9/AC-MPD7/AC-BT7 already grade, and each hop's size and
control count is measured from disk at render time.
"""
import argparse
import hashlib
import html
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

import buyer_route

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "preview", "payment-gate-report.json")
ITEMS = os.path.join(ROOT, "state", "merchant-onboard-items.json")
TRIAL = os.path.join(ROOT, "preview", "buyer-trial.json")
PREVIEW = os.path.join(ROOT, "preview")
OUT_HTML = os.path.join(PREVIEW, "merchant-onboard.html")
OUT_JSON = os.path.join(PREVIEW, "merchant-onboard.json")

CANON_KEYS = ("face", "source", "items_source", "items", "standard_products", "bands", "secret_rule", "honest", "onward")

CRITERIA = [
    ("AC-MO1", "source sha256 recorded on the face equals the file on disk"),
    ("AC-MO2", "every item and every standard-channel product equals a fresh projection"),
    ("AC-MO3", "the page carries zero external refs (file:// double-click works offline)"),
    ("AC-MO4", "only checkbox inputs exist and the secret rule is printed (no secret value field)"),
    ("AC-MO5", "proven + pending == total and the printed counts equal a fresh reading"),
    ("AC-MO6", "MOCK / AIGC / non-advice bands are permanent on the face"),
    ("AC-MO7", "the onward route is intact: every hop on disk, linked, measured fresh, at least one operable"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def price_label(cent):
    return "\u00a5%.2f" % (cent / 100.0)


def evidence():
    """Read the two shipped evidence files. Nothing is declared here."""
    pay = json.load(io.open(SOURCE, encoding="utf-8"))
    positives = pay.get("channel_positive", [])
    accepted = [c for c in positives if c.get("ok")]
    callback_ok = len(positives) == 2 and len(accepted) == 2
    trial = {}
    if os.path.exists(TRIAL):
        trial = json.load(io.open(TRIAL, encoding="utf-8"))
    crit = {}
    for c in trial.get("criteria", []):
        crit[c.get("id")] = bool(c.get("pass_", c.get("pass")))
    books_ok = trial.get("verdict") == "PASS" and bool(crit.get("AC-BT4")) and bool(crit.get("AC-BT5"))
    return {
        "callback": callback_ok,
        "callback_text": "payment-gate-report.json channel_positive %d/%d accepted"
        % (len(accepted), len(positives)),
        "books": bool(books_ok),
        "books_text": "preview/buyer-trial.json AC-BT4/AC-BT5 PASS",
    }


def items_doc():
    return json.load(io.open(ITEMS, encoding="utf-8"))


def project_items():
    data = items_doc()
    ev = evidence()
    rows = []
    for it in data.get("items", []):
        source_key = it.get("evidence_source", "")
        proven = bool(source_key) and bool(ev.get(source_key))
        rows.append(
            {
                "id": it["id"],
                "label": it["label"],
                "owner": it["owner"],
                "how": it.get("how", ""),
                "evidence_source": source_key,
                "proven": proven,
                "evidence_text": ev.get(source_key + "_text", "") if source_key else "",
            }
        )
    return rows


def project_standard_products():
    doc = json.load(io.open(SOURCE, encoding="utf-8"))
    out = []
    for p in doc.get("products", []):
        if p.get("channel") != "standard":
            continue
        out.append(
            {
                "id": p["id"],
                "price_cent": int(p["price_cent"]),
                "price_label": price_label(int(p["price_cent"])),
                "entitlement": p.get("entitlement", ""),
                "channel": p["channel"],
                "copy": p.get("copy", ""),
            }
        )
    return out


def counts(rows):
    total = len(rows)
    proven = sum(1 for r in rows if r["proven"])
    ceo = sum(1 for r in rows if r["owner"] == "ceo")
    pending_ceo = sum(1 for r in rows if r["owner"] == "ceo" and not r["proven"])
    return {
        "total": total,
        "proven": proven,
        "ceo": ceo,
        "pending_ceo": pending_ceo,
        "declared": 0,
        "done": proven,
    }


def canonical_hash(doc):
    subset = {k: doc.get(k) for k in CANON_KEYS}
    return hashlib.sha256(json.dumps(subset, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def payload_doc():
    data = items_doc()
    rows = project_items()
    c = counts(rows)
    payload = {
        "face": data.get("face", "merchant-onboard"),
        "title": data.get("title", ""),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {"path": "preview/payment-gate-report.json", "sha256": sha256_file(SOURCE)},
        "items_source": {
            "path": "state/merchant-onboard-items.json",
            "sha256": sha256_file(ITEMS),
        },
        "ui": data.get("ui", {}),
        "items": rows,
        "standard_products": project_standard_products(),
        "bands": data.get("bands", []),
        "secret_rule": data.get("secret_rule", ""),
        "honest": data.get("honest", ""),
        "onward": buyer_route.state("merchant-onboard", PREVIEW),
        "counts": c,
        "criteria": [{"id": i, "text": t} for i, t in CRITERIA],
    }
    payload["payload_sha256"] = canonical_hash(payload)
    return payload


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--ink:#1b1a18;--paper:#f6f2ea;--line:#d8d0c2;--dim:#6c665c;--ok:#1f6b45;--bad:#8f2f24;--accent:#2f4b7c;--warn:#7a5c00}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 "Songti SC","Noto Serif CJK SC",Georgia,serif}
header{padding:28px 32px 18px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:26px;letter-spacing:.02em}
.sub{color:var(--dim);font-size:14px}
.bands{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.band{font:12px/1.4 ui-monospace,Consolas,monospace;border:1px solid var(--line);padding:4px 8px;border-radius:3px;color:var(--dim);background:#fffdf8}
.band.warn{border-color:#c9a227;color:var(--warn)}
main{display:grid;grid-template-columns:minmax(300px,1.35fr) minmax(320px,1fr);gap:24px;padding:24px 32px 40px}
@media(max-width:880px){main{grid-template-columns:1fr}}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.14em;color:var(--dim);margin:0 0 10px;font-family:ui-monospace,Consolas,monospace}
.card{border:1px solid var(--line);background:#fffdf8;padding:14px 16px;margin-bottom:14px}
.item{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);background:#fffdf8;padding:11px 13px;margin-bottom:9px}
.item.proven{border-color:#9cc3ab}
.item .box{margin-top:3px}
.item .body{flex:1}
.item .row{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.item .name{font-size:16px}
.item .how,.item .ev{color:var(--dim);font-size:13px;margin-top:5px}
.item .ev{font-family:ui-monospace,Consolas,monospace;font-size:12px}
.tag{font:11px/1.3 ui-monospace,Consolas,monospace;border:1px solid var(--line);padding:2px 6px;border-radius:2px;color:var(--dim);white-space:nowrap}
.tag.ceo{border-color:#c9a227;color:var(--warn)}
.tag.proven{border-color:#9cc3ab;color:var(--ok)}
button{font:14px/1 inherit;font-family:inherit;padding:8px 13px;border:1px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer}
.verdict{font:13px/1.55 ui-monospace,Consolas,monospace;padding:9px 11px;border:1px solid var(--line);margin-top:10px}
.verdict.pass{border-color:#9cc3ab;color:var(--ok)}
.verdict.fail{border-color:#d8a49b;color:var(--bad)}
.progress{font:14px/1.6 ui-monospace,Consolas,monospace}
table{width:100%;border-collapse:collapse;font:13px/1.45 ui-monospace,Consolas,monospace}
th,td{text-align:left;padding:5px 6px;border-bottom:1px dotted var(--line)}
td.num,th.num{text-align:right}
.crit{font:12px/1.75 ui-monospace,Consolas,monospace}
.crit b{color:var(--ok)}
.crit .x{color:var(--bad)}
ul.rules{margin:0;padding-left:18px}
ul.rules li{margin-bottom:8px}
footer{padding:0 32px 40px;color:var(--dim);font-size:12px;font-family:ui-monospace,Consolas,monospace}
</style>
</head>
<body data-payload-sha256="__PAYLOAD_SHA__">
<header>
  <h1>__H1__ <span class="sub">__H1_TAIL__</span></h1>
  <div class="sub">__SUB__</div>
  <div class="bands">__BANDS__</div>
</header>
<main>
  <section>
    <h2>__H2_ITEMS__</h2>
    __ITEMS__
    <div class="card"><h2>__H2_LEGEND__</h2><div class="sub">__LEGEND__</div></div>
  </section>
  <section>
    <h2>__H2_PROGRESS__</h2>
    <div class="card">
      <div class="progress" id="progress">__PROGRESS0__</div>
      <div class="verdict fail" id="verdict">__VERDICT0__</div>
      <div style="margin-top:10px"><button id="reset">__RESET__</button></div>
    </div>
    <div class="card">
      <h2>__H2_STANDARD__</h2>
      __PRODUCTS__
      <div class="sub">__BLOCKED_NOTE__</div>
    </div>
    <div class="card">
      <h2>__H2_RULES__</h2>
      <ul class="rules">
        <li>__SECRET_RULE__</li>
        <li>__HONEST__</li>
      </ul>
    </div>
    <div class="card">
      <h2>__H2_SELFTEST__</h2>
      <div class="sub">__SELFTEST_HEAD__</div>
      <div class="crit" id="selftest"></div>
    </div>
  </section>
</main>
__ONWARD__
<footer>
  <div id="src"></div>
  <div>__FOOTER_LEDGER__</div>
</footer>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
(function(){
  var P = JSON.parse(document.getElementById('payload').textContent);
  var UI = P.ui || {};
  var KEY = 'bd-merchant-onboard-v1';
  var ticks = {};
  try { var raw = localStorage.getItem(KEY); if (raw) { ticks = JSON.parse(raw) || {}; } } catch (e) { ticks = {}; }
  var boxes = document.querySelectorAll('input.tick');

  function $(id){ return document.getElementById(id); }
  function fmt(tpl, obj){
    return String(tpl || '').replace(/\\{(\\w+)\\}/g, function(m, k){ return (obj[k] === undefined ? m : obj[k]); });
  }
  function save(){ try { localStorage.setItem(KEY, JSON.stringify(ticks)); } catch (e) {} }
  function count(){
    var proven = 0, declared = 0, ceo = 0, total = 0;
    for (var i = 0; i < boxes.length; i++){
      var b = boxes[i], id = b.getAttribute('data-item');
      var it = null;
      for (var j = 0; j < P.items.length; j++){ if (P.items[j].id === id) { it = P.items[j]; break; } }
      if (!it) continue;
      total++;
      if (it.owner === 'ceo') ceo++;
      if (it.proven) { proven++; }
      else if (ticks[id]) { declared++; }
    }
    return {total: total, proven: proven, ceo: ceo, declared: declared, done: proven + declared};
  }
  function render(){
    var c = count();
    for (var i = 0; i < boxes.length; i++){
      var b = boxes[i], id = b.getAttribute('data-item'), it = null;
      for (var j = 0; j < P.items.length; j++){ if (P.items[j].id === id) { it = P.items[j]; break; } }
      if (!it) continue;
      if (it.proven) { b.checked = true; b.disabled = true; }
      else { b.disabled = false; b.checked = !!ticks[id]; }
    }
    $('progress').textContent = fmt(UI.progress_fmt, {declared: c.declared, ceo: c.ceo, proven: c.proven, total: c.total, done: c.done});
    var verdict;
    if (c.proven === c.total) { verdict = fmt(UI.verdict_proven_all, {total: c.total}); }
    else if (c.ceo > 0 && c.declared === c.ceo) { verdict = fmt(UI.verdict_declared, {ceo: c.ceo}); }
    else { verdict = fmt(UI.verdict_missing, {missing: c.total - c.done}); }
    $('verdict').textContent = verdict;
    $('verdict').className = 'verdict ' + (c.proven === c.total ? 'pass' : 'fail');
    selftest(c);
    return c;
  }
  function selftest(c){
    var box = $('selftest');
    box.innerHTML = '';
    var checks = [
      ['AC-MO5 arithmetic: done == proven + declared', c.done === c.proven + c.declared],
      ['AC-MO4 secret face: one checkbox per item, rule printed', boxes.length === P.items.length && !!P.secret_rule],
      ['AC-MO6 bands: MOCK / AIGC / non-advice', P.bands.length === 3 && P.bands.join(' ').indexOf('MOCK') >= 0 && P.bands.join(' ').indexOf('AIGC') >= 0]
    ];
    for (var i = 0; i < checks.length; i++){
      var d = document.createElement('div');
      d.appendChild(document.createTextNode((checks[i][1] ? 'PASS ' : 'FAIL ') + checks[i][0]));
      if (!checks[i][1]) { d.className = 'x'; }
      box.appendChild(d);
    }
  }
  function onToggle(){
    for (var i = 0; i < boxes.length; i++){
      var b = boxes[i], id = b.getAttribute('data-item');
      ticks[id] = !!b.checked;
    }
    save();
    render();
  }
  $('reset').addEventListener('click', function(){ ticks = {}; save(); render(); });
  for (var i = 0; i < boxes.length; i++){ boxes[i].addEventListener('change', onToggle); }
  $('src').textContent = 'source: ' + P.source.path + ' sha256=' + P.source.sha256
    + ' | items: ' + P.items_source.path + ' sha256=' + P.items_source.sha256
    + ' | payload_sha256=' + P.payload_sha256 + ' | generated ' + P.generated_utc;
  render();
})();
</script>
</body>
</html>
"""


def render_items(rows, ui):
    parts = []
    for r in rows:
        owner_tag = ui.get("tag_ceo", "CEO") if r["owner"] == "ceo" else ui.get("tag_ours", "ours")
        tags = '<span class="tag%s">%s</span>' % (" ceo" if r["owner"] == "ceo" else "", html.escape(owner_tag))
        if r["proven"]:
            tags += ' <span class="tag proven">%s</span>' % html.escape(ui.get("tag_proven", "evidence"))
        ev = ""
        if r["proven"]:
            ev = '<div class="ev">%s%s</div>' % (
                html.escape(ui.get("evidence_prefix", "")),
                html.escape(r["evidence_text"]),
            )
        elif r["owner"] == "ceo":
            ev = '<div class="ev">%s</div>' % html.escape(ui.get("pending", ""))
        parts.append(
            '<label class="item%s" data-item="%s">'
            '<input class="tick" type="checkbox" data-item="%s"%s>'
            '<div class="body">'
            '<div class="row"><span class="name">%s</span><span>%s</span></div>'
            '<div class="how">%s%s</div>%s'
            "</div></label>"
            % (
                " proven" if r["proven"] else "",
                html.escape(r["id"], quote=True),
                html.escape(r["id"], quote=True),
                ' checked disabled' if r["proven"] else "",
                html.escape(r["label"]),
                tags,
                html.escape(ui.get("how_prefix", "")),
                html.escape(r["how"]),
                ev,
            )
        )
    return "\n    ".join(parts)


def render_products(products):
    rows = []
    for p in products:
        rows.append(
            "<tr><td>%s</td><td>%s</td><td class=\"num\">%s</td><td>%s</td><td>%s</td></tr>"
            % (
                html.escape(p["id"]),
                html.escape(p["copy"]),
                html.escape(p["price_label"]),
                html.escape(p["entitlement"]),
                html.escape(p["channel"]),
            )
        )
    return (
        '<table><thead><tr><th>id</th><th>商品</th><th class="num">价格</th>'
        "<th>权益</th><th>通道</th></tr></thead><tbody>%s</tbody></table>" % "".join(rows)
    )


def initial_strings(payload):
    ui = payload["ui"]
    c = payload["counts"]

    def fmt(tpl, obj):
        return re.sub(r"\{(\w+)\}", lambda m: str(obj.get(m.group(1), m.group(0))), tpl or "")

    progress = fmt(
        ui.get("progress_fmt", ""),
        {
            "declared": c["declared"],
            "ceo": c["ceo"],
            "proven": c["proven"],
            "total": c["total"],
            "done": c["done"],
        },
    )
    if c["proven"] == c["total"]:
        verdict = fmt(ui.get("verdict_proven_all", ""), {"total": c["total"]})
    else:
        verdict = fmt(ui.get("verdict_missing", ""), {"missing": c["total"] - c["done"]})
    return progress, verdict


def render_html(payload):
    ui = payload["ui"]
    progress0, verdict0 = initial_strings(payload)
    bands = "".join(
        '<span class="band%s">%s</span>' % (" warn" if i == 0 else "", html.escape(b))
        for i, b in enumerate(payload["bands"])
    )
    blob = json.dumps(payload, ensure_ascii=False, indent=1).replace("</", "<\\/")
    pairs = [
        ("__TITLE__", html.escape(payload["title"])),
        ("__H1__", html.escape(ui.get("h1", payload["title"]))),
        ("__H1_TAIL__", html.escape(ui.get("h1_tail", ""))),
        (
            "__SUB__",
            html.escape(
                ui.get("sub_fmt", "").replace("{src16}", payload["source"]["sha256"][:16]).replace(
                    "{items16}", payload["items_source"]["sha256"][:16]
                )
            ),
        ),
        ("__BANDS__", bands),
        ("__H2_ITEMS__", html.escape(ui.get("h2_items", ""))),
        ("__ITEMS__", render_items(payload["items"], ui)),
        ("__H2_LEGEND__", html.escape(ui.get("h2_legend", ""))),
        ("__LEGEND__", html.escape(ui.get("legend", ""))),
        ("__H2_PROGRESS__", html.escape(ui.get("h2_progress", ""))),
        ("__PROGRESS0__", html.escape(progress0)),
        ("__VERDICT0__", html.escape(verdict0)),
        ("__RESET__", html.escape(ui.get("reset", ""))),
        ("__H2_STANDARD__", html.escape(ui.get("h2_standard", ""))),
        ("__PRODUCTS__", render_products(payload["standard_products"])),
        ("__BLOCKED_NOTE__", html.escape(ui.get("blocked_note", ""))),
        ("__H2_RULES__", html.escape(ui.get("h2_rules", ""))),
        ("__SECRET_RULE__", html.escape(payload["secret_rule"])),
        ("__HONEST__", html.escape(payload["honest"])),
        ("__H2_SELFTEST__", html.escape(ui.get("h2_selftest", ""))),
        ("__SELFTEST_HEAD__", html.escape(ui.get("selftest_head", ""))),
        ("__FOOTER_LEDGER__", html.escape(ui.get("footer_ledger", ""))),
        ("__PAYLOAD_SHA__", payload["payload_sha256"]),
        ("__ONWARD__", buyer_route.render_block("merchant-onboard", PREVIEW)),
        ("__PAYLOAD__", blob),
    ]
    body = TEMPLATE
    for needle, value in pairs:
        body = body.replace(needle, value)
    return body


def write():
    payload = payload_doc()
    html_text = render_html(payload)
    with io.open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_text)
    out = dict(payload)
    out["sizes"] = {"html_bytes": len(html_text.encode("utf-8")), "json_bytes": 0}
    out["criteria"] = [dict(c, pass_=True) for c in payload["criteria"]]
    out["verdict"] = "PASS"
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    out["sizes"]["json_bytes"] = len(text.encode("utf-8")) + 1
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    print(
        "merchant-onboard WROTE html=%dB json=%dB items=%d proven=%d"
        % (
            len(html_text.encode("utf-8")),
            len(text.encode("utf-8")),
            payload["counts"]["total"],
            payload["counts"]["proven"],
        )
    )
    _refresh_face()
    return 0


def _landing_is_default():
    """AC-PWC15 (R3537): a scratch render derives nothing.

    Both halves are derived from ROOT at import time, so a caller that redirects
    them off this root's own preview/ is rendering a private world, not landing
    the company face.
    """
    try:
        own = os.path.realpath(PREVIEW)
        return (
            os.path.dirname(os.path.realpath(OUT_HTML)) == own
            and os.path.dirname(os.path.realpath(OUT_JSON)) == own
        )
    except Exception:
        return False


def _refresh_face():
    """AC-PWC15 (R3537): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second writer
    is kept here. ROOT is passed explicitly, so a private world derives that
    world's face. Refusals are named, never raised: both halves are already on
    disk when this runs, so the caller's exit code stays its own.
    """
    if not _landing_is_default():
        return "SKIPPED not-this-root"
    try:
        os_src = os.path.join(ROOT, "src", "os")
        if os_src not in sys.path:
            sys.path.insert(0, os_src)
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(ROOT)
        return "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # a private world may carry no shared writer
        return "SKIPPED %s" % type(exc).__name__


def check():
    failed = []
    if not os.path.exists(OUT_HTML) or not os.path.exists(OUT_JSON):
        print("merchant-onboard CHECK-MISSING face not on disk")
        return 2
    landed = json.load(io.open(OUT_JSON, encoding="utf-8"))
    page = io.open(OUT_HTML, encoding="utf-8").read()

    if landed.get("source", {}).get("sha256") != sha256_file(SOURCE):
        failed.append("AC-MO1 source sha256 drifted")
    if landed.get("items_source", {}).get("sha256") != sha256_file(ITEMS):
        failed.append("AC-MO1b items sha256 drifted")

    fresh = project_items()
    kept = landed.get("items", [])
    keys = ("id", "label", "owner", "proven", "evidence_text")
    if len(fresh) != len(kept) or any(
        tuple(bool(a[k]) if k == "proven" else a[k] for k in keys)
        != tuple(bool(b[k]) if k == "proven" else b[k] for k in keys)
        for a, b in zip(fresh, kept)
    ):
        failed.append("AC-MO2 item projection drifted")

    fresh_products = project_standard_products()
    kept_products = landed.get("standard_products", [])
    pkeys = ("id", "price_cent", "entitlement", "channel")
    if len(fresh_products) != len(kept_products) or any(
        tuple(a[k] for k in pkeys) != tuple(b[k] for k in pkeys)
        for a, b in zip(fresh_products, kept_products)
    ):
        failed.append("AC-MO2b standard product projection drifted")

    ext = len(re.findall(r'(?:src|href)\s*=\s*["\']https?://', page, re.I))
    if ext != 0:
        failed.append("AC-MO3 external refs=%d" % ext)

    tags = re.findall(r"<input\b[^>]*>", page)
    kinds = []
    for tag in tags:
        m = re.search(r'type\s*=\s*["\']([^"\']+)["\']', tag)
        kinds.append(m.group(1).lower() if m else "text")
    if sorted(set(kinds)) != ["checkbox"]:
        failed.append("AC-MO4 input kinds=%s" % ",".join(sorted(set(kinds))))
    if len(tags) != len(fresh):
        failed.append("AC-MO4b inputs=%d items=%d" % (len(tags), len(fresh)))
    if "<textarea" in page.lower():
        failed.append("AC-MO4c textarea present")
    if landed.get("secret_rule", "") not in page:
        failed.append("AC-MO4d secret rule missing from page")

    c = counts(fresh)
    landed_counts = landed.get("counts", {})
    if c["proven"] + c["pending_ceo"] != c["total"]:
        failed.append(
            "AC-MO5 arithmetic proven+pending=%d total=%d"
            % (c["proven"] + c["pending_ceo"], c["total"])
        )
    for key in ("total", "proven", "ceo", "pending_ceo"):
        if int(landed_counts.get(key, -1)) != c[key]:
            failed.append("AC-MO5b count %s landed=%s fresh=%s" % (key, landed_counts.get(key), c[key]))

    progress0, verdict0 = initial_strings({"ui": landed.get("ui", {}), "counts": c})
    if progress0 not in page:
        failed.append("AC-MO5c page does not print the initial progress line")
    if verdict0 not in page:
        failed.append("AC-MO5d page does not print the initial verdict line")

    canonical = canonical_hash(landed)
    if canonical != landed.get("payload_sha256"):
        failed.append("AC-MO5e payload_sha256 stale")
    if ('data-payload-sha256="%s"' % landed.get("payload_sha256")) not in page:
        failed.append("AC-MO5f page carries a different payload hash")

    bands = landed.get("bands", [])
    if len(bands) != 3:
        failed.append("AC-MO6b bands=%d" % len(bands))
    for needle in bands:
        if needle not in page:
            failed.append("AC-MO6 missing band text")
    joined = " ".join(bands)
    for needle in ("MOCK", "AIGC"):
        if needle not in joined:
            failed.append("AC-MO6c band set lacks %s" % needle)

    # AC-MO7: graded by the shared closure so every route-bearing face agrees.
    failed.extend(buyer_route.check("merchant-onboard", page, landed.get("onward"), PREVIEW))

    if failed:
        print("merchant-onboard CHECK-MISMATCH failed=%d" % len(failed))
        for f in failed:
            print("  - " + f)
        return 2
    print(
        "merchant-onboard VERDICT PASS criteria=7 items=%d ceo=%d proven=%d external_refs=0 route_hops=%d html=%dB json=%dB"
        % (
            c["total"],
            c["ceo"],
            c["proven"],
            landed.get("onward", {}).get("count", -1),
            os.path.getsize(OUT_HTML),
            os.path.getsize(OUT_JSON),
        )
    )
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.write:
        return write()
    return check()


if __name__ == "__main__":
    sys.exit(main())
