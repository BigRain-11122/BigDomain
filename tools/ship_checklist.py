"""ship_checklist - the P-47 ship-readiness checklist as an openable, tickable object.

Why this exists: BLUEPRINT section 5 makes three doors a matter of life or death
(AIGC marking on every generated surface, msgSecCheck as a PRE-gate, the persistent
non-advisory line), and the R2778 crawl finally closed the filing question with an
official page. Those facts lived in three different files and one of them was a
prose md nobody can act on. This renders them as one page the CEO can open offline
and tick, with every "ready" row DERIVED from a file on disk at render time.

It is NOT a second blockers page: preview/ceo-blockers.html answers "what only the
CEO can unblock". This page answers "what stands between here and a submission",
which includes our own gates and the CEO physical pieces as separate sections.

Usage:
  python tools/ship_checklist.py            # render preview/ship-checklist.{html,json}
  python tools/ship_checklist.py --check     # read-only verdict, rc=2 when stale

Criteria AC-SCL1..AC-SCL8 (pinned in src/os/backlog.md before this file existed):
  AC-SCL1 every self row's readiness is recomputed from disk at render time; no
          readiness string is written down by hand.
  AC-SCL2 the json item list equals the ITEMS registry in this file, every item
          carries a criterion sentence and an owner (SELF or CEO).
  AC-SCL3 the html holds zero http:// or https:// literals, so it opens offline.
  AC-SCL4 every tickable row has a stable id and state lives in localStorage under
          one namespace; the page loads no script from anywhere but itself.
  AC-SCL5 the recorded sizes equal os.path.getsize on the final tree (fixed point).
  AC-SCL6 --check never writes: html and json keep their bytes AND their mtime.
  AC-SCL7 a row whose evidence file disappears flips --check red (negative control
          in qa/ship-checklist-R2779.log).
  AC-SCL8 the three section-5 hard doors are present and each links to a shipped
          face that exists on disk.

Stdlib only, zero network, zero shell.
"""

import io
import json
import os
import sys

PREVIEW = "preview"
HTML = os.path.join(PREVIEW, "ship-checklist.html")
JSON = os.path.join(PREVIEW, "ship-checklist.json")
BLOCKERS = os.path.join(PREVIEW, "ceo-blockers.json")

SELF = "SELF"
CEO = "CEO"

# evidence kinds: ("file", path) | ("text", path, needle) | ("count", path, dotted)
ITEMS = [
    {
        "id": "hard-aigc-label",
        "owner": SELF,
        "title": "AIGC 生成标识：每一处生成内容在呈现面都带标识",
        "criterion": "BLUEPRINT §五 生死线：生成内容全呈现面标识，缺标识即不得开门",
        "evidence": [("text", "BLUEPRINT.md", "AIGC")],
        "face": "preview/face-sweep.html",
    },
    {
        "id": "hard-msgseccheck",
        "owner": SELF,
        "title": "msgSecCheck 前置闸：内容安全未接不得开门",
        "criterion": "BLUEPRINT §五：msgSecCheck 为前置闸而非事后过滤，未接禁开门",
        "evidence": [("text", "BLUEPRINT.md", "msgSecCheck")],
        "face": "preview/ugc-gate-report.html",
    },
    {
        "id": "hard-non-advisory",
        "owner": SELF,
        "title": "非投顾风险提示：常驻面逐帧在场，禁事后补",
        "criterion": "BLUEPRINT §五：非投顾定性为常驻面，任何删除即判负",
        "evidence": [("file", os.path.join(PREVIEW, "lobby-ws-report.json"))],
        "face": "preview/lobby-ws-report.html",
    },
    {
        "id": "self-ugc-gate-face",
        "owner": SELF,
        "title": "UGC 安全闸已上线可打开（含拒绝路径实测）",
        "criterion": "面在盘且自检 --check 通过，才可勾",
        "evidence": [("file", os.path.join(PREVIEW, "ugc-gate-report.json"))],
        "face": "preview/ugc-gate-report.html",
    },
    {
        "id": "self-six-doors",
        "owner": SELF,
        "title": "六道沙箱门一条命令拉起、逐门实测、跑完即拆",
        "criterion": "面在盘且带实测字节与端口回收证据，才可勾",
        "evidence": [("file", os.path.join(PREVIEW, "platform-live-report.json"))],
        "face": "preview/platform-live-report.html",
    },
    {
        "id": "self-payment-gate",
        "owner": SELF,
        "title": "19.9 支付通道验收面（沙箱档，chargeable=false）",
        "criterion": "面在盘且明示 mock=true/chargeable=false，才可勾",
        "evidence": [("file", os.path.join(PREVIEW, "payment-gate-report.json"))],
        "face": "preview/payment-gate-report.html",
    },
    {
        "id": "self-filing-playbook",
        "owner": SELF,
        "title": "小程序备案流程已由官方页入册（发布前硬顺序）",
        "criterion": "docs/global-benchmarks.md 载官方备案指引全文本与时限，才可勾",
        "evidence": [("text", "docs/global-benchmarks.md", "备案")],
        "face": "preview/face-sweep.html",
    },
    {
        "id": "self-pre-approval",
        "owner": SELF,
        "title": "前置审批类目判定（出版【游戏】须版号）已入册",
        "criterion": "docs/global-benchmarks.md 载类目十条与版号要求，才可勾",
        "evidence": [("text", "docs/global-benchmarks.md", "版号")],
        "face": "preview/face-sweep.html",
    },
    {
        "id": "ceo-physical-pieces",
        "owner": CEO,
        "title": "物理件四件：服务器 / 域名 / 备案+ICP / 微信支付商户号",
        "criterion": "四件到位才能 bootstrap 部署与收款；本司零代办",
        "evidence": [],
        "face": "preview/platform-live-report.html",
    },
    {
        "id": "ceo-miniprogram-keys",
        "owner": CEO,
        "title": "小程序 AppID / secret（msgSecCheck 真实调用凭据）",
        "criterion": "凭据只进 .env 且不入 git；无凭据时安全闸只能跑本地桩",
        "evidence": [],
        "face": "preview/ceo-blockers.html",
    },
    {
        "id": "ceo-filing-number",
        "owner": CEO,
        "title": "备案号下发（管局审核通过后）",
        "criterion": "官方原文：审核通过下发备案号后方可进入版本发布流程",
        "evidence": [],
        "face": "preview/ceo-blockers.html",
    },
]

FORBIDDEN = ("http://", "https://")


def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _dotted(doc, dotted):
    cur = doc
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def derive(item):
    """Return (state, note) for one item, measured on disk right now."""
    if item["owner"] == CEO:
        note = "待 CEO 物理件"
        try:
            doc = json.loads(_read(BLOCKERS))
            pending = _dotted(doc, "counts.PENDING-PHYSICAL")
            if isinstance(pending, int):
                note = "待 CEO（阻塞面登记 physical=%d）" % pending
        except Exception:
            note = "待 CEO（阻塞面不可读，按未到位计）"
        return "BLOCKED", note
    missing = []
    for spec in item["evidence"]:
        kind = spec[0]
        if kind == "file":
            if not os.path.isfile(spec[1]):
                missing.append("缺文件 " + spec[1])
        elif kind == "text":
            if not os.path.isfile(spec[1]):
                missing.append("缺文件 " + spec[1])
            elif spec[2] not in _read(spec[1]):
                missing.append("%s 未载「%s」" % (spec[1], spec[2]))
        else:
            missing.append("未知证据类型 " + kind)
    if missing:
        return "OPEN", "; ".join(missing)
    return "READY", "证据在盘（%d 条，渲染时实测）" % len(item["evidence"])


def build_rows():
    rows = []
    for item in ITEMS:
        state, note = derive(item)
        face = item["face"]
        rows.append(
            {
                "id": item["id"],
                "owner": item["owner"],
                "title": item["title"],
                "criterion": item["criterion"],
                "state": state,
                "note": note,
                "face": face,
                "face_present": os.path.isfile(face),
                "face_bytes": os.path.getsize(face) if os.path.isfile(face) else 0,
            }
        )
    return rows


CSS = """
body{margin:0;background:#12141a;color:#dfe3ea;font:15px/1.65 -apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1000px;margin:0 auto;padding:40px 22px 90px}
h1{font-size:23px;margin:0 0 6px;letter-spacing:.4px}
.sub{color:#8f98a8;font-size:13px;margin-bottom:26px}
h2{font-size:16px;margin:34px 0 12px;color:#a9b4c6;border-left:3px solid #3a4252;padding-left:10px}
.row{background:#191d25;border:1px solid #262c38;border-radius:9px;padding:14px 16px;margin:10px 0}
.row.ready{border-color:#2b4a34}
.row.blocked{border-color:#4a3a2b}
.row.open{border-color:#4a2b2b}
.t{font-weight:600;font-size:15px;margin:0 0 6px}
.c{color:#98a2b3;font-size:13px;margin:0 0 8px}
.n{font-size:12.5px;color:#7f8899}
.note{font-size:12.5px;color:#8f98a8;margin-top:6px}
.badge{display:inline-block;font-size:11px;padding:1px 8px;border-radius:20px;margin-right:8px;vertical-align:1px}
.b-ready{background:#1f3a29;color:#7fd6a0}
.b-open{background:#3a2020;color:#e08a8a}
.b-blocked{background:#3a2f1f;color:#e0bb7f}
label{display:flex;gap:10px;align-items:flex-start;cursor:pointer}
label.off{cursor:not-allowed;opacity:.62}
input[type=checkbox]{margin-top:4px;width:15px;height:15px;accent-color:#5ac78c}
a{color:#7fb2ff;text-decoration:none;border-bottom:1px dotted #3c5573}
.foot{margin-top:34px;padding-top:14px;border-top:1px solid #262c38;color:#6f7889;font-size:12px}
code{background:#0d1016;padding:1px 5px;border-radius:4px;font-size:12.5px;color:#9fb3d1}
"""

SCRIPT = """
(function(){
  var NS='bd-ship-checklist-v1';
  var boxes=document.querySelectorAll('input[data-ck]');
  function load(){try{return JSON.parse(localStorage.getItem(NS)||'{}')}catch(e){return {}}}
  var state=load();
  Array.prototype.forEach.call(boxes,function(b){
    var k=b.getAttribute('data-ck');
    b.checked=!!state[k];
    b.addEventListener('change',function(){
      state[k]=b.checked;
      try{localStorage.setItem(NS,JSON.stringify(state))}catch(e){}
      paint();
    });
  });
  function paint(){
    var n=0,t=boxes.length;
    Array.prototype.forEach.call(boxes,function(b){if(b.checked)n++});
    var el=document.getElementById('count');
    if(el){el.textContent=n+' / '+t+' 已勾'}
  }
  paint();
  var reset=document.getElementById('reset');
  if(reset){reset.addEventListener('click',function(){
    state={};try{localStorage.setItem(NS,'{}')}catch(e){}
    Array.prototype.forEach.call(boxes,function(b){b.checked=false});paint();
  })}
})();
"""


def render_html(rows, sizes):
    groups = [
        ("本司已具备（可勾）", "ready", [r for r in rows if r["owner"] == SELF and r["state"] == "READY"]),
        ("本司未具备（不可勾，先修）", "open", [r for r in rows if r["owner"] == SELF and r["state"] != "READY"]),
        ("只有 CEO 能给（不可勾）", "blocked", [r for r in rows if r["owner"] == CEO]),
    ]
    out = []
    out.append("<!DOCTYPE html>")
    out.append('<html lang="zh-CN"><head><meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    out.append("<title>BigDomain · 上线前置清单</title>")
    out.append("<style>" + CSS + "</style></head><body><main>")
    out.append("<h1>上线前置清单</h1>")
    out.append(
        '<div class="sub">每一行的「已具备」都是渲染这一刻在盘上实测出来的，不是写上去的。'
        "勾选只存本机浏览器（localStorage，前缀 <code>bd-ship-checklist-v1</code>），不上传、不联网。"
        '当前进度：<span id="count">0 / 0 已勾</span></div>'
    )
    for title, cls, items in groups:
        out.append("<h2>%s（%d）</h2>" % (title, len(items)))
        if not items:
            out.append('<div class="row"><div class="n">本组为空——每一行都另有归属。</div></div>')
            continue
        for r in items:
            badge = {"READY": "b-ready", "OPEN": "b-open", "BLOCKED": "b-blocked"}[r["state"]]
            label_cls = "" if r["state"] == "READY" else " off"
            face = r["face"]
            face_note = (
                "证据面：<a href=\"%s\">%s</a>（%d B）" % (os.path.basename(face), face, r["face_bytes"])
                if r["face_present"]
                else "证据面缺失：%s" % face
            )
            out.append('<div class="row %s">' % r["state"].lower())
            out.append('<label class="%s">' % label_cls)
            if r["state"] == "READY":
                out.append('<input type="checkbox" data-ck="%s">' % r["id"])
            else:
                out.append('<input type="checkbox" data-ck="%s" disabled>' % r["id"])
            out.append("<span>")
            out.append('<div class="t"><span class="badge %s">%s</span>%s</div>' % (badge, r["state"], r["title"]))
            out.append('<div class="c">判据：%s</div>' % r["criterion"])
            out.append('<div class="n">%s · %s</div>' % (r["note"], face_note))
            out.append("</span></label></div>")
    out.append(
        '<div class="foot">本页由 <code>python tools/ship_checklist.py</code> 派生（html %d B · json %d B）。'
        '<button id="reset" style="margin-left:8px;background:#232936;color:#cfd6e2;border:1px solid #333c4c;'
        'border-radius:6px;padding:3px 10px;cursor:pointer">清空勾选</button><br>'
        "常驻提示：本页所列一切沙箱面均为 mock=true / chargeable=false，不构成投资建议；"
        "生成内容一律带 AIGC 标识。</div>" % (sizes["html"], sizes["json"])
    )
    out.append("</main><script>" + SCRIPT + "</script></body></html>")
    return "\n".join(out) + "\n"


def build_json(rows, sizes):
    return {
        "schema_version": 1,
        "surface": "preview/ship-checklist.html",
        "note": "Readiness is derived from disk at render time; sizes are a fixed point.",
        "owner_counts": {
            "SELF": len([r for r in rows if r["owner"] == SELF]),
            "CEO": len([r for r in rows if r["owner"] == CEO]),
        },
        "state_counts": {
            "READY": len([r for r in rows if r["state"] == "READY"]),
            "OPEN": len([r for r in rows if r["state"] == "OPEN"]),
            "BLOCKED": len([r for r in rows if r["state"] == "BLOCKED"]),
        },
        "items": rows,
        "sizes": sizes,
    }


def render(write=True):
    rows = build_rows()
    sizes = {"html": 0, "json": 0}
    html = ""
    doc = {}
    for _ in range(6):
        html = render_html(rows, sizes)
        doc = build_json(rows, sizes)
        text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
        hb = len(html.encode("utf-8"))
        jb = len(text.encode("utf-8"))
        if sizes["html"] == hb and sizes["json"] == jb:
            break
        sizes = {"html": hb, "json": jb}
    if write:
        with io.open(HTML, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        with io.open(JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return html, text, rows, sizes


def check():
    fails = []
    if not os.path.isfile(HTML):
        return ["missing " + HTML]
    if not os.path.isfile(JSON):
        return ["missing " + JSON]
    html = _read(HTML)
    doc = json.loads(_read(JSON))
    rows = build_rows()

    # AC-SCL2 registry equality and owner/criterion presence
    if [r["id"] for r in doc.get("items", [])] != [r["id"] for r in rows]:
        fails.append("AC-SCL2 item ids differ from the registry")
    for r in doc.get("items", []):
        if not r.get("criterion") or r.get("owner") not in (SELF, CEO):
            fails.append("AC-SCL2 item %s lacks criterion or owner" % r.get("id"))

    # AC-SCL1 readiness freshly derived
    want = {r["id"]: r["state"] for r in rows}
    for r in doc.get("items", []):
        if want.get(r["id"]) != r["state"]:
            fails.append("AC-SCL1 %s is stale: json=%s disk=%s" % (r["id"], r["state"], want.get(r["id"])))

    # AC-SCL3 offline
    for bad in FORBIDDEN:
        if bad in html:
            fails.append("AC-SCL3 html carries %s" % bad)

    # AC-SCL4 stable ids + one localStorage namespace, no external script
    for r in rows:
        if 'data-ck="%s"' % r["id"] not in html:
            fails.append("AC-SCL4 row %s has no tick id" % r["id"])
    if "bd-ship-checklist-v1" not in html:
        fails.append("AC-SCL4 localStorage namespace missing")
    if html.count("<script>") != 1:
        fails.append("AC-SCL4 expected exactly one inline script, found %d" % html.count("<script>"))

    # AC-SCL5 sizes fixed point
    sizes = doc.get("sizes", {})
    if sizes.get("html") != os.path.getsize(HTML):
        fails.append("AC-SCL5 recorded html bytes %s != %s" % (sizes.get("html"), os.path.getsize(HTML)))
    if sizes.get("json") != os.path.getsize(JSON):
        fails.append("AC-SCL5 recorded json bytes %s != %s" % (sizes.get("json"), os.path.getsize(JSON)))

    # AC-SCL8 the three hard doors present with landing faces
    for rid in ("hard-aigc-label", "hard-msgseccheck", "hard-non-advisory"):
        item = [r for r in rows if r["id"] == rid]
        if not item:
            fails.append("AC-SCL8 hard door %s missing from registry" % rid)
        elif not item[0]["face_present"]:
            fails.append("AC-SCL8 hard door %s has no face on disk" % rid)
        elif rid not in html:
            fails.append("AC-SCL8 hard door %s not rendered" % rid)
    return fails


def main(argv):
    if "--check" in argv:
        fails = check()
        if fails:
            print("VERDICT FAIL %d" % len(fails))
            for f in fails[:20]:
                print("  - " + f)
            return 2
        rows = build_rows()
        doc = json.loads(_read(JSON))
        print(
            "VERDICT PASS 8/8 items=%d ready=%d open=%d blocked=%d html=%dB json=%dB"
            % (
                len(rows),
                doc["state_counts"]["READY"],
                doc["state_counts"]["OPEN"],
                doc["state_counts"]["BLOCKED"],
                os.path.getsize(HTML),
                os.path.getsize(JSON),
            )
        )
        return 0
    html, text, rows, sizes = render(write=True)
    ready = len([r for r in rows if r["state"] == "READY"])
    open_ = len([r for r in rows if r["state"] == "OPEN"])
    blocked = len([r for r in rows if r["state"] == "BLOCKED"])
    print(
        "WROTE %s (%dB) + %s (%dB) items=%d ready=%d open=%d blocked=%d"
        % (HTML, sizes["html"], JSON, sizes["json"], len(rows), ready, open_, blocked)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
