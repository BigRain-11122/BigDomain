"""Money-path demo face: the 19.9 money path as a MOCK surface a human can click.

Every number, product, price and journey verdict on the page is DERIVED at
render time from three shipped preview payloads; nothing is typed in.

Sources (read-only):
  preview/payment-gate-report.json  products / channels / blocked_on
  preview/journey-19.9.json         steps / verdicts / gates
  preview/ceo-blockers.json         blocker counts

Outputs: preview/money-path-demo.html + preview/money-path-demo.json

Criteria AC-MPD1..AC-MPD6 were pinned in src/os/backlog.md before this file
existed. This module is a MOCK surface: it connects to no merchant, signs no
order and writes no ledger entry.

CLI: python tools/money_path_demo.py           render both artifacts
     python tools/money_path_demo.py --check   read-only verification
"""

import json
import os
import sys

# D-20261116-13: value-domain assertion imported from the one shared module.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# The catalog is the REPO's shipped config, not the render target. A test world
# repoints ROOT/PREVIEW at a temp dir; reading the catalog through ROOT then
# emptied it and every product read "not in the catalog" (R2826). CATALOG_ROOT
# is computed from this file's location, so repointing ROOT cannot move it.
CATALOG_ROOT = os.path.dirname(HERE)
# R2826: the sibling import must survive every loader (the battery loads this
# file by path with no tools/ on sys.path), so the directory is added first.
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import value_domain as VD  # noqa: E402
PREVIEW = os.path.join(ROOT, "preview")

SOURCE_NAMES = {
    "payment": "payment-gate-report.json",
    "journey": "journey-19.9.json",
    "blockers": "ceo-blockers.json",
}
HTML_NAME = "money-path-demo.html"
JSON_NAME = "money-path-demo.json"
NS = "bd-money-path-demo-v1"

T_TITLE = "\u6536\u6b3e\u6f14\u7ec3\uff08MOCK\uff09"
T_MOCK = "\u672c\u9875\u4e3a\u6f14\u793a\u9762\uff1a\u672a\u63a5\u5165\u771f\u5546\u6237\u53f7\uff0c\u4ed8\u6b3e\u4e0e\u8d26\u672c\u5747\u4e3a MOCK\u3002"
T_PRODUCTS = "\u5546\u54c1\uff08\u6d3e\u751f\u81ea payment-gate-report.json\uff09"
T_STEPS = "\u65c5\u7a0b\u6b65\u9aa4\uff08\u6d3e\u751f\u81ea journey-19.9.json\uff09"
T_CEO_YES = "\u9700\u8981 CEO \u7269\u7406\u4ef6"
T_CEO_NO = "\u65e0\u9700\u7269\u7406\u4ef6"
T_ENT = "\u6743\u76ca\u6807\u8bc6"
T_CHAN = "\u901a\u9053"
T_PRICE = "\u4ef7\u76ee"
T_TICKS = "\u5ba1\u6838\u52fe\u9009\uff08\u672c\u673a\u4fdd\u5b58\uff09"
T_TICK1 = "\u5546\u54c1\u6587\u6848\u4e0e\u4ef7\u76ee\u5df2\u6838\u5bf9"
T_TICK2 = "\u95f8\u95e8\u6587\u6848\u5df2\u6838\u5bf9"
T_TICK3 = "\u963b\u585e\u9879\u5df2\u6838\u5bf9"
T_BLOCKED = "\u963b\u585e\u9879\uff08\u6d3e\u751f\u81ea ceo-blockers.json\uff09"
T_SIZES = "\u6e90\u6587\u4ef6\u5927\u5c0f\uff08\u6e32\u67d3\u65f6\u5b9e\u6d4b\uff09"
T_PHYS = "\u7269\u7406\u4ef6"
T_DEC = "\u5f85\u51b3\u7b56"
T_PICK = "\u9009\u4e2d\u67e5\u770b"


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def derive():
    """Read the three shipped payloads and return everything the face prints."""
    pay = _read_json(os.path.join(PREVIEW, SOURCE_NAMES["payment"]))
    jny = _read_json(os.path.join(PREVIEW, SOURCE_NAMES["journey"]))
    blk = _read_json(os.path.join(PREVIEW, SOURCE_NAMES["blockers"]))

    products = []
    for item in pay.get("products", []):
        cent = int(item.get("price_cent", 0))
        products.append(
            {
                "id": item.get("id"),
                "price_yuan": "%.2f" % (cent / 100.0),
                "price_cent": cent,
                "channel": item.get("channel"),
                "entitlement": item.get("entitlement"),
                "copy": item.get("copy"),
                "needs_ceo": bool(item.get("needs_ceo")),
            }
        )

    steps = []
    for item in jny.get("steps", []):
        steps.append(
            {
                "id": item.get("id"),
                "touchpoint": item.get("touchpoint"),
                "verdict": item.get("verdict"),
                "ok": bool(item.get("ok")),
                "gate": item.get("gate"),
                "carrier": item.get("carrier"),
            }
        )

    counts = blk.get("counts", {}) or {}
    sizes = {}
    for key, name in SOURCE_NAMES.items():
        sizes[key] = os.path.getsize(os.path.join(PREVIEW, name))

    return {
        "face": "money-path-demo",
        "generated_by": "tools/money_path_demo.py",
        "kind": "MOCK",
        "products": products,
        "steps": steps,
        "blocked_on": pay.get("blocked_on") or jny.get("blocked_on") or "",
        "counts": {
            "physical": int(counts.get("PENDING-PHYSICAL", 0)),
            "decision": int(counts.get("PENDING-DECISION", 0)),
            "products": len(products),
            "steps": len(steps),
            "steps_pass": len([s for s in steps if s["ok"]]),
        },
        "sources": {k: {"path": "preview/" + v, "bytes": sizes[k]} for k, v in SOURCE_NAMES.items()},
        "criteria": [
            "AC-MPD1 derived numbers only",
            "AC-MPD2 product list equals source, CEO gate badged",
            "AC-MPD3 MOCK statement, offline",
            "AC-MPD4 selection carries copy/entitlement/channel, verdicts unaltered",
            "AC-MPD5 recorded source sizes, byte-identical rerender",
            "AC-MPD6 read-only --check, one script, one namespace, ASCII source",
        ],
    }


CSS = """
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;padding:24px 28px;
background:#f6f6f4;color:#1d1d1f;line-height:1.55}
h1{font-size:22px;margin:0 0 6px}
h2{font-size:15px;margin:26px 0 10px;letter-spacing:.02em;color:#3a3a3c}
.mock{background:#fff3cd;border-left:4px solid #e0a800;padding:10px 12px;margin:12px 0;
font-size:14px}
.counts{font-size:13px;color:#48484a;margin:6px 0 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.card{background:#fff;border:1px solid #dcdcd8;border-radius:10px;padding:12px 14px;
cursor:pointer;text-align:left;font:inherit;color:inherit}
.card:hover{border-color:#8e8e93}
.card.on{border-color:#0a7cff;box-shadow:0 0 0 2px rgba(10,124,255,.15)}
.price{font-size:20px;font-weight:600}
.meta{font-size:12px;color:#636366;margin-top:4px}
.badge{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;
margin-top:8px;background:#ffe5e5;color:#b3261e;border:1px solid #ffb4ab}
.badge.ok{background:#e6f4ea;color:#137333;border-color:#a8d5b5}
#detail{background:#fff;border:1px solid #dcdcd8;border-radius:10px;padding:14px;
margin-top:12px;font-size:14px;min-height:78px}
#detail dt{font-size:12px;color:#636366;margin-top:8px}
#detail dd{margin:0;font-size:14px}
ol{padding-left:20px;margin:0}
ol li{margin:6px 0;font-size:14px}
.v{font-size:11px;padding:1px 6px;border-radius:6px;margin-left:6px;
background:#eef1f4;color:#3a3a3c}
.v.pass{background:#e6f4ea;color:#137333}
.gate{font-size:12px;color:#8a6d3b;margin-top:2px}
.ticks label{display:block;font-size:14px;margin:4px 0;cursor:pointer}
.small{font-size:12px;color:#636366}
"""


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(payload, script):
    data = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    counts = payload["counts"]
    sizes = "".join(
        '<li>%s &mdash; %d bytes</li>' % (_esc(v["path"]), v["bytes"])
        for _, v in sorted(payload["sources"].items())
    )
    ticks = "".join(
        '<label><input type="checkbox" data-ck="t%d"> %s</label>' % (i + 1, lab)
        for i, lab in enumerate([T_TICK1, T_TICK2, T_TICK3])
    )
    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n"
        "<h1>%s</h1>\n<p class=\"mock\">%s</p>\n"
        "<p class=\"counts\">%s <b>%d</b> &middot; %s <b>%d</b> &middot; "
        "products <b>%d</b> &middot; steps <b>%d</b> (pass %d)</p>\n"
        "<h2>%s</h2>\n<div class=\"grid\" id=\"products\"></div>\n"
        "<div id=\"detail\">%s</div>\n"
        "<h2>%s</h2>\n<ol id=\"steps\"></ol>\n"
        "<h2>%s</h2>\n<p class=\"small\" id=\"blocked\"></p>\n<ul class=\"small\" id=\"sizes\">%s</ul>\n"
        "<h2>%s</h2>\n<div class=\"ticks\" id=\"ticks\">%s</div>\n"
        "<script>var NS='%s';var DATA=%s;%s</script>\n</body>\n</html>\n"
    ) % (
        T_TITLE,
        CSS,
        T_TITLE,
        T_MOCK,
        T_PHYS,
        counts["physical"],
        T_DEC,
        counts["decision"],
        counts["products"],
        counts["steps"],
        counts["steps_pass"],
        T_PRODUCTS,
        T_PICK,
        T_STEPS,
        T_BLOCKED,
        sizes,
        T_TICKS,
        ticks,
        NS,
        data,
        script,
    )


JS = """
(function(){
  var P=DATA.products, S=DATA.steps, box=document.getElementById('products'),
      det=document.getElementById('detail'), ol=document.getElementById('steps');
  function esc(t){return String(t==null?'':t).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
  function show(p){
    var rows=document.querySelectorAll('.card');
    for(var i=0;i<rows.length;i++){rows[i].className='card'+(rows[i].getAttribute('data-id')===p.id?' on':'');}
    det.innerHTML='<div class="price">&yen;'+esc(p.price_yuan)+'</div><div class="small">'+esc(p.copy)+'</div>'+
      '<dl><dt>'+esc(LBL.ent)+'</dt><dd>'+esc(p.entitlement)+'</dd>'+
      '<dt>'+esc(LBL.chan)+'</dt><dd>'+esc(p.channel)+'</dd>'+
      '<dt>'+esc(LBL.price)+'</dt><dd>'+p.price_cent+' cents</dd></dl>'+
      '<div class="badge'+(p.needs_ceo?'':' ok')+'">'+esc(p.needs_ceo?LBL.ceoYes:LBL.ceoNo)+'</div>';
  }
  for(var i=0;i<P.length;i++){
    var b=document.createElement('button');
    b.className='card';b.setAttribute('data-id',P[i].id);
    b.innerHTML='<div class="price">&yen;'+esc(P[i].price_yuan)+'</div>'+
      '<div class="meta">'+esc(P[i].id)+' &middot; '+esc(P[i].channel)+'</div>'+
      '<div class="badge'+(P[i].needs_ceo?'':' ok')+'">'+esc(P[i].needs_ceo?LBL.ceoYes:LBL.ceoNo)+'</div>';
    b.onclick=(function(p){return function(){show(p);};})(P[i]);
    box.appendChild(b);
  }
  for(var k=0;k<S.length;k++){
    var li=document.createElement('li');
    li.innerHTML='<span class="v'+(S[k].ok?' pass':'')+'">'+esc(S[k].id+' '+S[k].verdict)+'</span> '+
      esc(S[k].touchpoint)+'<div class="gate">'+esc(S[k].gate||'')+'</div>';
    ol.appendChild(li);
  }
  document.getElementById('blocked').textContent=DATA.blocked_on||'';
  var sel=null;
  for(var m=0;m<P.length;m++){if(P[m].id==='pack_compute_19_9'){sel=P[m];}}
  show(sel||P[0]||{id:'',price_yuan:'0.00',copy:'',entitlement:'',channel:'',price_cent:0,needs_ceo:true});
  var T=document.querySelectorAll('[data-ck]');
  for(var n=0;n<T.length;n++){
    var kk=T[n].getAttribute('data-ck');
    T[n].checked=(localStorage.getItem(NS+':'+kk)==='1');
    T[n].onchange=function(){localStorage.setItem(NS+':'+this.getAttribute('data-ck'),this.checked?'1':'0');};
  }
})();
"""

LBL_JS = (
    "var LBL={ent:'%s',chan:'%s',price:'%s',ceoYes:'%s',ceoNo:'%s'};"
    % (T_ENT, T_CHAN, T_PRICE, T_CEO_YES, T_CEO_NO)
)


def _html(payload):
    return render_html(payload, LBL_JS + JS)


def write_all():
    payload = derive()
    html = _html(payload)
    html_path = os.path.join(PREVIEW, HTML_NAME)
    json_path = os.path.join(PREVIEW, JSON_NAME)
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    with open(html_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    return html_path, json_path, len(html.encode("utf-8")), os.path.getsize(json_path)


def check(diag=None):
    problems = []
    html_path = os.path.join(PREVIEW, HTML_NAME)
    json_path = os.path.join(PREVIEW, JSON_NAME)
    for path in (html_path, json_path):
        if not os.path.exists(path):
            return ["missing artifact: " + os.path.basename(path)]

    with open(html_path, "r", encoding="utf-8") as fh:
        landed_html = fh.read()
    with open(json_path, "r", encoding="utf-8") as fh:
        landed_json = json.load(fh)

    payload = derive()
    expected_html = _html(payload)

    if landed_html != expected_html:
        problems.append("html is not the fresh derivation")
    if landed_json != payload:
        problems.append("json is not the fresh derivation")

    if "http://" in landed_html or "https://" in landed_html:
        problems.append("html carries an absolute url")
    if landed_html.count("<script") != 1:
        problems.append("html script blocks = %d" % landed_html.count("<script"))
    if landed_html.count("var NS='%s'" % NS) != 1:
        problems.append("namespace declaration is not exactly one")
    if landed_html.count("localStorage.") != 2:
        problems.append("storage call count = %d" % landed_html.count("localStorage."))
    if landed_html.count("localStorage.getItem('") or landed_html.count('localStorage.setItem(\''):
        problems.append("storage addressed by literal key, not through NS")

    for key, meta in sorted(payload["sources"].items()):
        real = os.path.getsize(os.path.join(ROOT, meta["path"].replace("/", os.sep)))
        if real != meta["bytes"]:
            problems.append("source size drift on %s: %d != %d" % (key, meta["bytes"], real))

    ids = [p["id"] for p in landed_json["products"]]
    if len(ids) != len(payload["products"]) or sorted(ids) != sorted([p["id"] for p in payload["products"]]):
        problems.append("product list diverges from source")
    # AC-VD2/AC-VD5 (D-20261116-13): a fresh derivation is not a value-domain
    # assertion by itself - the landed price rows are compared to the catalog.
    cat = VD.catalog(CATALOG_ROOT)
    stats = {}
    problems.extend(VD.product_failures(landed_json["products"], cat,
                                       ("price_cent",), stats=stats))
    if any(("price" in k and "cent" not in k and isinstance(v, str) and "." in v and k != "price_yuan") for k, v in payload.items()):
        problems.append("unexpected price field")
    if landed_json["counts"]["products"] != len(landed_json["products"]):
        problems.append("product count is not derived")
    if landed_json["counts"]["steps"] != len(landed_json["steps"]):
        problems.append("step count is not derived")
    # AC-VD9/AC-VD11 (R2826): printed line and exit code read ONE list.
    problems = VD.teeth(stats.get("products", 0), stats.get("tiers", 0), problems)
    if diag is not None:
        diag["line"] = VD.line(stats.get("products", 0), stats.get("tiers", 0),
                               problems)
    return problems


def main(argv):
    if "--check" in argv:
        diag = {}
        problems = check(diag)
        print(diag.get("line", ""))
        if problems:
            print("VERDICT FAIL %d" % len(problems))
            for item in problems:
                print("  - " + item)
            return 2
        payload = derive()
        print(
            "VERDICT PASS products=%d steps=%d physical=%d decision=%d html=%dB json=%dB"
            % (
                payload["counts"]["products"],
                payload["counts"]["steps"],
                payload["counts"]["physical"],
                payload["counts"]["decision"],
                os.path.getsize(os.path.join(PREVIEW, HTML_NAME)),
                os.path.getsize(os.path.join(PREVIEW, JSON_NAME)),
            )
        )
        return 0
    html_path, json_path, html_bytes, json_bytes = write_all()
    print("WROTE %s %dB" % (os.path.basename(html_path), html_bytes))
    print("WROTE %s %dB" % (os.path.basename(json_path), json_bytes))
    diag = {}
    problems = check(diag)
    print(diag.get("line", ""))
    if problems:
        print("VERDICT FAIL %d" % len(problems))
        for item in problems:
            print("  - " + item)
        return 2
    print("VERDICT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
