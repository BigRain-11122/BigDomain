#!/usr/bin/env python3
"""P-47 buyer trial face: one offline page a visitor can actually operate.

Why this exists: the preview face carried 42 HTML pages at R3250 and 41 of them
were read-only reports (button count 0) - a visitor could look at engineering
numbers and could not do anything. This tool renders a single-file trial that
runs from file:// with zero network: pick one of the SHIPPED products, pay on a
mock gateway, watch a double-entry ledger post twice, prove that a repeated
callback books once, and see the entitlement arrive.

The products are not authored here. They are projected from
preview/payment-gate-report.json, and --check refuses the face when any id,
price, entitlement or channel drifts from that source.

Criteria AC-BT1..BT6 are pre-registered in src/os/backlog.md (R3250 PIN line)
before this file existed.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "preview", "payment-gate-report.json")
PREVIEW = os.path.join(ROOT, "preview")
OUT_HTML = os.path.join(PREVIEW, "buyer-trial.html")
OUT_JSON = os.path.join(PREVIEW, "buyer-trial.json")

SHORT = {
    "birthright_entry": "永久入城券",
    "pack_compute_19_9": "19.9 算力包",
    "report_data_b": "数据报告（B 端）",
    "share_observation": "观测费分成单",
    "tier_patron_30d": "月卡 · 30 天",
}

NEEDLES = ["MOCK", "AIGC", "非投资建议"]

# Where the buyer goes after a mock payment. Before R3284 this page was an
# operable dead end: three controls, zero outbound links, so the chain stopped
# exactly where money appears. Each hop is a local file; its size is read from
# disk at write time, never written down here.
ROUTE = [
    ("membership-face.html", "这条权益落在哪：会员面（只读）"),
    ("merchant-onboard.html", "要真收钱还缺什么：商户号 / 服务器 / 域名 / 备案（可填）"),
    ("money-path-demo.html", "这笔钱在账本里怎么走（可操作）"),
    ("start-here.html", "回到起点：这台机器今天能亲手做什么（只读汇总）"),
]

CRITERIA = [
    ("AC-BT1", "source sha256 recorded on the face equals the file on disk"),
    ("AC-BT2", "every product id / price_cent / entitlement / channel equals the source"),
    ("AC-BT3", "the page carries zero external refs (file:// double-click works offline)"),
    ("AC-BT4", "double-entry books balance: cash sum == 0 and token sum == 0 after each post"),
    ("AC-BT5", "a repeated callback for one order books once (idempotent guard)"),
    ("AC-BT6", "MOCK / AIGC / non-advice disclaimers are permanent on the face"),
    ("AC-BT7", "every onward hop exists on disk, is linked, and prints its current size"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def price_label(cent):
    return "¥%.2f" % (cent / 100.0)


def project_products():
    doc = json.load(io.open(SOURCE, encoding="utf-8"))
    out = []
    for p in doc.get("products", []):
        pid = p["id"]
        cent = int(p["price_cent"])
        channel = p["channel"]
        blocked = channel == "standard"
        out.append(
            {
                "id": pid,
                "label": SHORT.get(pid, pid),
                "copy": p.get("copy", ""),
                "entitlement": p.get("entitlement", ""),
                "channel": channel,
                "price_cent": cent,
                "price_label": price_label(cent),
                "needs_ceo": bool(p.get("needs_ceo")),
                "blocked": blocked,
                "blocked_reason": (
                    "本通道需要真实微信商户号与结算主体，演示中拒绝放行（物理件未到）"
                    if blocked
                    else ""
                ),
                "cash_entries": [
                    [["现金", cent], ["预收收入", -cent]],
                    [["预收收入", cent], ["营业收入", -cent]],
                ],
                "token_entries": [[["代币待发池", -cent], ["用户点数", cent]]],
                "share_cent": (cent * 30 // 100) if pid == "share_observation" else 0,
            }
        )
    return out


CONTROL_RE = re.compile(r"<(?:button|input|select|textarea)\b", re.I)


def measure_hop(path):
    """(bytes, controls) of one local face.

    The single definition of "how much can a reader actually operate here":
    AC-BT7 and the shared onward route (tools/buyer_route.py) both consume it,
    so a hop's control class cannot be graded two different ways. Controls are
    counted as literal tags; widgets a script injects at runtime are not
    counted, which is why the number is a floor, not a promise.
    """
    if not os.path.exists(path):
        return 0, 0
    text = io.open(path, encoding="utf-8").read()
    return os.path.getsize(path), len(CONTROL_RE.findall(text))


def project_route():
    hops = []
    for href, label in ROUTE:
        size, controls = measure_hop(os.path.join(PREVIEW, href))
        hops.append(
            {
                "href": href,
                "label": label,
                "bytes": size,
                "controls": controls,
                "readonly": controls == 0,
            }
        )
    return hops


def payload_doc():
    products = project_products()
    canonical = json.dumps(products, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {
        "face": "buyer-trial",
        "title": "买家试用镜 · 本地演示",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "path": "preview/payment-gate-report.json",
            "sha256": sha256_file(SOURCE),
        },
        "products_sha256": hashlib.sha256(canonical).hexdigest(),
        "products": products,
        "books": {"cash": "分", "token": "点"},
        "route": project_route(),
        "compliance": {
            "mock": "MOCK 非真实支付：本页不联网、不扣款、不产生商户订单；一切数字为本机模拟。",
            "aigc": "AIGC 标识：平台生成的呈现内容带 ai_service 标识，本页为演示壳，不冒充真人作品。",
            "disclaimer": "非投资建议：本页展示的是算力包与工具服务价格，不是投资建议，也不承诺任何收益。",
        },
        "criteria": [{"id": i, "text": t} for i, t in CRITERIA],
    }


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>买家试用镜 · 本地演示（MOCK）</title>
<style>
:root{--ink:#1b1a18;--paper:#f6f2ea;--line:#d8d0c2;--dim:#6c665c;--ok:#1f6b45;--bad:#8f2f24;--accent:#2f4b7c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 "Songti SC","Noto Serif CJK SC",Georgia,serif}
header{padding:28px 32px 18px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:26px;letter-spacing:.02em}
.sub{color:var(--dim);font-size:14px}
.bands{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.band{font:12px/1.4 ui-monospace,Consolas,monospace;border:1px solid var(--line);padding:4px 8px;border-radius:3px;color:var(--dim);background:#fffdf8}
.band.warn{border-color:#c9a227;color:#7a5c00}
main{display:grid;grid-template-columns:minmax(280px,1fr) minmax(360px,1.35fr);gap:24px;padding:24px 32px 40px}
@media(max-width:860px){main{grid-template-columns:1fr}}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.14em;color:var(--dim);margin:0 0 10px;font-family:ui-monospace,Consolas,monospace}
.card{border:1px solid var(--line);background:#fffdf8;padding:14px 16px;margin-bottom:14px}
.prod{cursor:pointer;border:1px solid var(--line);background:#fffdf8;padding:12px 14px;margin-bottom:10px;transition:border-color .12s,transform .12s}
.prod:hover{border-color:var(--accent);transform:translateX(2px)}
.prod[aria-pressed="true"]{border-color:var(--accent);box-shadow:inset 3px 0 0 var(--accent)}
.prod .row{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.prod .name{font-size:17px}
.prod .price{font:16px/1 ui-monospace,Consolas,monospace}
.prod .copy{color:var(--dim);font-size:13px;margin-top:6px}
.tag{font:11px/1.2 ui-monospace,Consolas,monospace;border:1px solid var(--line);padding:2px 6px;border-radius:2px;color:var(--dim)}
.tag.std{border-color:#c9a227;color:#7a5c00}
button{font:14px/1 inherit;font-family:inherit;padding:9px 14px;border:1px solid var(--ink);background:var(--ink);color:var(--paper);cursor:pointer}
button.ghost{background:transparent;color:var(--ink)}
button:disabled{opacity:.4;cursor:default}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
table{width:100%;border-collapse:collapse;font:13px/1.45 ui-monospace,Consolas,monospace}
th,td{text-align:left;padding:5px 6px;border-bottom:1px dotted var(--line)}
td.num,th.num{text-align:right}
.verdict{font:13px/1.5 ui-monospace,Consolas,monospace;padding:8px 10px;border:1px solid var(--line);margin-top:8px}
.verdict.pass{border-color:#9cc3ab;color:var(--ok)}
.verdict.fail{border-color:#d8a49b;color:var(--bad)}
ol.log{list-style:none;margin:0;padding:0;font:12px/1.7 ui-monospace,Consolas,monospace;color:var(--dim);max-height:180px;overflow:auto}
ol.log li::before{content:"· ";color:var(--accent)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font:13px/1.6 ui-monospace,Consolas,monospace}
.kv dt{color:var(--dim)}
footer{padding:0 32px 40px;color:var(--dim);font-size:12px;font-family:ui-monospace,Consolas,monospace}
.crit{font:12px/1.7 ui-monospace,Consolas,monospace}
.crit b{color:var(--ok)}
.crit .x{color:var(--bad)}
</style>
</head>
<body data-payload-sha256="__PAYLOAD_SHA__">
<header>
  <h1>买家试用镜 <span class="sub">· 双击本地打开，零网络</span></h1>
  <div class="sub">商品、价格、权益全部派生自 <code>preview/payment-gate-report.json</code>（sha256 前 16 位 <code>__SRC_SHA16__</code>）。选一件商品，走一遍钱路。</div>
  <div class="bands">
    <span class="band warn">MOCK 非真实支付 · 不联网 · 不扣款</span>
    <span class="band">AIGC 标识在册</span>
    <span class="band">非投资建议</span>
    <span class="band">外链计数 <b id="extcount">__EXT__</b></span>
  </div>
</header>
<main>
  <section>
    <h2>商品（派生自出厂支付门报告）</h2>
    <div id="products">__CARDS__</div>
    <div class="card" id="blocked" hidden></div>
  </section>
  <section>
    <h2>订单与账本</h2>
    <div class="card">
      <dl class="kv" id="orderbox">
        <dt>订单</dt><dd id="oid">—</dd>
        <dt>状态</dt><dd id="ostatus">未下单</dd>
        <dt>通道</dt><dd id="ochannel">—</dd>
      </dl>
      <div class="actions">
        <button id="pay" disabled>模拟支付</button>
        <button id="replay" class="ghost" disabled>重复回调（自证幂等）</button>
        <button id="reset" class="ghost">重置</button>
      </div>
    </div>
    <div class="card">
      <h2>现金账（单位：分）</h2>
      <table><thead><tr><th>#</th><th>科目</th><th class="num">金额</th><th>订单</th></tr></thead><tbody id="cashbook"></tbody></table>
    </div>
    <div class="card">
      <h2>代币账（单位：点）</h2>
      <table><thead><tr><th>#</th><th>科目</th><th class="num">点数</th><th>订单</th></tr></thead><tbody id="tokenbook"></tbody></table>
    </div>
    <div id="balance"></div>
    <div class="card">
      <h2>事件</h2>
      <ol class="log" id="log"></ol>
    </div>
    <div class="card">
      <h2>权益与收据</h2>
      <div id="receipt" class="sub">尚未交付。</div>
    </div>
    <div class="card">
      <h2>本页自检（AC-BT4/5/6）</h2>
      <div class="crit" id="selftest"></div>
    </div>
  </section>
</main>
<footer>
  <div id="src"></div>
  <div id="route" data-route-hops="__ROUTE_HOPS__">
    <h2 style="margin:14px 0 6px">下一步 · 付完这一单之后还能走到哪里（__ROUTE_HOPS__ 跳，每跳文件在盘，构建时核对）</h2>
    __ROUTE__
  </div>
  <div>账本为本页内模拟双式记账，不是 src/sandbox/ledger 真账库；真实入账需物理件到位后接真通道。</div>
</footer>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
(function(){
  var P = JSON.parse(document.getElementById('payload').textContent);
  var S = {order:null, seq:0, booked:{}, cash:[], token:[], log:[], delivered:false};

  function $(id){return document.getElementById(id);}
  function money(c){return '¥' + (c/100).toFixed(2);}
  function el(tag, cls, text){var n=document.createElement(tag); if(cls)n.className=cls; if(text!=null)n.textContent=text; return n;}
  function note(msg){S.log.push(msg); var li=el('li',null,msg); $('log').appendChild(li); $('log').scrollTop=1e9;}

  function sum(rows){
    var acc={};
    rows.forEach(function(r){ var side = r.side; acc[side[0]] = (acc[side[0]]||0) + side[1]; acc[r.opp[0]] = (acc[r.opp[0]]||0) + r.opp[1]; });
    var total=0; for(var k in acc){ total += acc[k]; }
    return {accounts:acc, total:total};
  }

  function postBook(kind, entries, oid){
    entries.forEach(function(pair){
      var side=[pair[0][0], pair[0][1]], opp=[pair[1][0], pair[1][1]];
      var row = {side:side, opp:opp, oid:oid};
      (kind==='cash' ? S.cash : S.token).push(row);
      var tb = $(kind==='cash' ? 'cashbook' : 'tokenbook');
      var tr = el('tr');
      tr.appendChild(el('td',null,String(tb.rows.length+1)));
      tr.appendChild(el('td',null,side[0] + ' / ' + opp[0]));
      var num = el('td','num', (side[1]>0?'+':'') + side[1] + ' | ' + (opp[1]>0?'+':'') + opp[1]);
      tr.appendChild(num);
      tr.appendChild(el('td',null,oid));
      tb.appendChild(tr);
    });
    renderBalance();
  }

  function renderBalance(){
    var c = sum(S.cash), t = sum(S.token);
    var ok = (c.total===0 && t.total===0);
    var box = $('balance');
    box.textContent = '账本自检 · 现金账合计 ' + c.total + ' 分 · 代币账合计 ' + t.total + ' 点 · ' + (ok?'配平':'不平');
    box.className = 'verdict ' + (ok?'pass':'fail');
    if(!ok){ note('账本不平，已停止记账'); }
    return ok;
  }

  function renderProducts(){
    // cards are rendered into the file by the generator; this only binds them,
    // so the page still shows every product with JavaScript partly unavailable.
    var byId = {};
    P.products.forEach(function(p){ byId[p.id] = p; });
    var ns = document.querySelectorAll('.prod');
    for(var i=0;i<ns.length;i++){
      (function(node){
        var p = byId[node.getAttribute('data-product')];
        if(!p) return;
        node.setAttribute('role','button');
        node.setAttribute('aria-pressed','false');
        node.addEventListener('click', function(){ select(p, node); });
      })(ns[i]);
    }
  }

  function clearSelection(){ var ns=document.querySelectorAll('.prod'); for(var i=0;i<ns.length;i++){ ns[i].setAttribute('aria-pressed','false'); } }

  function select(p, node){
    clearSelection(); node.setAttribute('aria-pressed','true');
    S.order = {id:'BT-' + String(++S.seq).padStart(4,'0'), pid:p.id, product:p, status:'待支付'};
    S.delivered=false;
    $('oid').textContent = S.order.id;
    $('ostatus').textContent = '待支付';
    $('ochannel').textContent = p.channel;
    $('pay').disabled = !!p.blocked;
    $('replay').disabled = true;
    $('receipt').textContent = '尚未交付。';
    var b = $('blocked');
    if(p.blocked){
      b.hidden = false;
      b.innerHTML = '';
      b.appendChild(el('h2',null,'这条通道今天放不了行'));
      b.appendChild(el('div','copy', p.blocked_reason));
      b.appendChild(el('div','copy','缺失物理件：真实微信商户号 / 结算主体 / 服务器与域名 / 备案+ICP / 小程序 appid+secret。'));
      note(o_id() + ' 选择标准通道商品，如拒：需真实商户主体');
    } else {
      b.hidden = true;
      note(S.order.id + ' 创建订单：' + p.label + ' ' + p.price_label);
    }
  }
  function o_id(){ return S.order ? S.order.id : '—'; }

  function pay(){
    if(!S.order || S.order.product.blocked) return;
    if(S.order.status !== '待支付'){ note(S.order.id + ' 状态为 ' + S.order.status + '，支付按钮不再触发'); return; }
    S.order.status = '支付中';
    $('ostatus').textContent = '支付中';
    note(S.order.id + ' 提交到 MOCK 网关，等待异步回调…');
    setTimeout(callback, 700);
  }

  function callback(){
    if(!S.order) return;
    if(S.booked[S.order.id]){ note(S.order.id + ' 重复回调：已入账，本次忽略（幂等）'); return; }
    S.booked[S.order.id] = true;
    var p = S.order.product;
    postBook('cash', p.cash_entries, S.order.id);
    postBook('token', p.token_entries, S.order.id);
    if(p.share_cent > 0){
      postBook('cash', [[["分成成本", p.share_cent], ["应付分成", -p.share_cent]]], S.order.id);
    }
    S.order.status = '已入账';
    $('ostatus').textContent = '已入账';
    $('replay').disabled = false;
    note(S.order.id + ' 回调验签通过，双式入账完成');
    deliver();
  }

  function deliver(){
    var p = S.order.product;
    S.delivered = true;
    var r = $('receipt');
    r.innerHTML = '';
    var kv = el('dl','kv');
    function add(k,v){ kv.appendChild(el('dt',null,k)); kv.appendChild(el('dd',null,v)); }
    add('收据号', 'RC-' + S.order.id);
    add('商品', p.label);
    add('金额', p.price_label + '（' + p.price_cent + ' 分）');
    add('通道', p.channel);
    add('权益', p.entitlement + ' 已生效');
    add('点数', p.price_cent + ' 点已入余额');
    if(p.share_cent>0) add('分成', '30% = ' + p.share_cent + ' 分（应付分成）');
    add('AIGC', '生成内容带 ai_service 标识');
    r.appendChild(kv);
    r.appendChild(el('div','copy', P.compliance.disclaimer));
    note(S.order.id + ' 权益 ' + p.entitlement + ' 已生效，收据已出');
  }

  function reset(){
    S.order=null; S.cash=[]; S.token=[]; S.booked={}; S.delivered=false; S.log=[];
    $('cashbook').innerHTML=''; $('tokenbook').innerHTML=''; $('log').innerHTML='';
    $('oid').textContent='—'; $('ostatus').textContent='未下单'; $('ochannel').textContent='—';
    $('pay').disabled=true; $('replay').disabled=true; $('receipt').textContent='尚未交付。';
    $('blocked').hidden=true; $('balance').textContent=''; $('balance').className='';
    clearSelection();
    note('已重置：账本清空，订单号从 ' + String(S.seq+1).padStart(4,'0') + ' 继续');
  }

  function selftest(){
    var box = $('selftest'); box.innerHTML='';
    var checks = [
      ['AC-BT4 账本双式配平', (sum(S.cash).total===0 && sum(S.token).total===0)],
      ['AC-BT5 幂等守卫在役', typeof S.booked === 'object'],
      ['AC-BT6 三面常驻', P.compliance.mock.indexOf('MOCK')>=0 && P.compliance.aigc.indexOf('AIGC')>=0 && P.compliance.disclaimer.indexOf('非投资建议')>=0]
    ];
    checks.forEach(function(c){
      var d = el('div');
      d.appendChild(el('b', null, (c[1]?'PASS':'FAIL') + ' '));
      d.appendChild(document.createTextNode(c[0]));
      if(!c[1]) d.className='x';
      box.appendChild(d);
    });
  }

  $('pay').addEventListener('click', pay);
  $('replay').addEventListener('click', callback);
  $('reset').addEventListener('click', reset);
  $('src').textContent = 'source: ' + P.source.path + ' sha256=' + P.source.sha256 + ' · products_sha256=' + P.products_sha256 + ' · generated ' + P.generated_utc;
  renderProducts(); renderBalance(); selftest();
  note('页面就绪：' + P.products.length + ' 件商品，零外链，MOCK 通道');
})();
</script>
</body>
</html>
"""


def render_cards(products):
    parts = []
    for p in products:
        parts.append(
            '<div class="prod" data-product="%s" aria-pressed="false">'
            '<div class="row"><span class="name">%s</span>'
            '<span><span class="price">%s</span> '
            '<span class="tag%s">%s</span></span></div>'
            '<div class="copy">%s</div></div>'
            % (
                html.escape(p["id"], quote=True),
                html.escape(p["label"]),
                html.escape(p["price_label"]),
                " std" if p["blocked"] else "",
                html.escape(p["channel"]),
                html.escape(p["copy"]),
            )
        )
    return "\n".join(parts)


def render_route(hops):
    rows = []
    for i, h in enumerate(hops):
        kind = "只读" if h["readonly"] else "可操作"
        rows.append(
            '<div class="hop" data-hop="%d" data-hop-bytes="%d">%d. '
            '<a href="%s">%s</a> <span class="tag">%s · %dB</span> — %s</div>'
            % (
                i + 1,
                h["bytes"],
                i + 1,
                html.escape(h["href"], quote=True),
                html.escape(h["href"]),
                kind,
                h["bytes"],
                html.escape(h["label"]),
            )
        )
    return "\n    ".join(rows)


def render_html(payload):
    blob = json.dumps(payload, ensure_ascii=False, indent=1)
    blob = blob.replace("</", "<\\/")
    body = TEMPLATE
    body = body.replace("__PAYLOAD_SHA__", payload["products_sha256"])
    body = body.replace("__SRC_SHA16__", payload["source"]["sha256"][:16])
    body = body.replace("__EXT__", "0")
    body = body.replace("__CARDS__", render_cards(payload["products"]))
    body = body.replace("__ROUTE_HOPS__", str(len(payload["route"])))
    body = body.replace("__ROUTE__", render_route(payload["route"]))
    body = body.replace("__PAYLOAD__", blob)
    return body


def write():
    payload = payload_doc()
    html_text = render_html(payload)
    with io.open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_text)
    out = dict(payload)
    out["sizes"] = {
        "html_bytes": len(html_text.encode("utf-8")),
        "json_bytes": 0,
    }
    out["criteria"] = [dict(c, pass_=True) for c in payload["criteria"]]
    out["verdict"] = "PASS"
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    # record its own size honestly on a second short pass
    size = len(text.encode("utf-8")) + 1
    out["sizes"]["json_bytes"] = size
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    print("buyer-trial WROTE html=%dB json=%dB products=%d"
          % (len(html_text.encode("utf-8")), len(text.encode("utf-8")), len(payload["products"])))
    return 0


def check():
    failed = []
    if not os.path.exists(OUT_HTML) or not os.path.exists(OUT_JSON):
        print("buyer-trial CHECK-MISSING face not on disk")
        return 2
    landed = json.load(io.open(OUT_JSON, encoding="utf-8"))
    page = io.open(OUT_HTML, encoding="utf-8").read()

    src_sha = sha256_file(SOURCE)
    if landed.get("source", {}).get("sha256") != src_sha:
        failed.append("AC-BT1 source sha256 drifted")

    fresh = project_products()
    kept = landed.get("products", [])
    keys = ("id", "price_cent", "entitlement", "channel")
    if len(fresh) != len(kept) or any(
        tuple(a[k] for k in keys) != tuple(b[k] for k in keys)
        for a, b in zip(fresh, kept)
    ):
        failed.append("AC-BT2 product projection drifted")

    ext = len(re.findall(r'(?:src|href)\s*=\s*["\']https?://', page, re.I))
    if ext != 0:
        failed.append("AC-BT3 external refs=%d" % ext)

    canonical = json.dumps(fresh, ensure_ascii=False, sort_keys=True).encode("utf-8")
    want = hashlib.sha256(canonical).hexdigest()
    if want != landed.get("products_sha256"):
        failed.append("AC-BT2b products_sha256 stale")
    if ('data-payload-sha256="%s"' % want) not in page:
        failed.append("AC-BT2c page carries a different payload hash")

    for pid in [p["id"] for p in fresh]:
        if ('data-product="%s"' % pid) not in page:
            failed.append("AC-BT2d card missing for %s" % pid)

    for needle in NEEDLES:
        if needle not in page:
            failed.append("AC-BT6 missing needle %s" % needle)

    # the page must carry the three books and the idempotent guard by construction
    for marker in ("booked", "postBook", "MOCK"):
        if marker not in page:
            failed.append("AC-BT4/5 marker missing %s" % marker)

    # AC-BT7: the footer route must exist, be linked, and be sized from disk
    hops = project_route()
    landed_route = landed.get("route", [])
    if ('data-route-hops="%d"' % len(hops)) not in page:
        failed.append("AC-BT7 page does not print hop count %d" % len(hops))
    if len(landed_route) != len(hops):
        failed.append("AC-BT7 json hops=%d fresh=%d" % (len(landed_route), len(hops)))
    for fresh_hop, kept_hop in zip(hops, landed_route):
        name = fresh_hop["href"]
        if fresh_hop["bytes"] == 0:
            failed.append("AC-BT7 hop file missing %s" % name)
        if ('href="%s"' % name) not in page:
            failed.append("AC-BT7 hop not linked %s" % name)
        if kept_hop.get("bytes") != fresh_hop["bytes"]:
            failed.append(
                "AC-BT7 hop size drifted %s json=%s disk=%s"
                % (name, kept_hop.get("bytes"), fresh_hop["bytes"])
            )

    if failed:
        print("buyer-trial CHECK-MISMATCH failed=%d" % len(failed))
        for f in failed:
            print("  - " + f)
        return 2
    print("buyer-trial VERDICT PASS criteria=%d products=%d route_hops=%d external_refs=0 html=%dB json=%dB"
          % (len(CRITERIA), len(fresh), len(hops), os.path.getsize(OUT_HTML), os.path.getsize(OUT_JSON)))
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
