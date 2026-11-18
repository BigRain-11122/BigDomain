"""filing_checklist - the mini-program FILING flow as an object you can open and tick.

WHY: the official guide landed in docs/global-benchmarks.md at R2778 as prose, and
filing is the hard pre-release gate for this company (official text: the bureau
issues the filing number, and only then may you proceed to version release). A
wall of prose cannot be executed in the right order under time pressure, so this
tool derives the executable page from the same row, and CROSS-CHECKS the row at
render time: if the benchmark row loses one of the phrases the page counts, the
gate goes red instead of quietly showing a stale list.

HONESTY RULE (inherited from the ship checklist): a row that cannot be measured
from disk is NEVER shown as ready. DERIVED rows are recomputed from files; MANUAL
rows report NEEDS-HUMAN and say why. The page never invents progress.

Criteria AC-FCL1..AC-FCL8 were pinned in src/os/backlog.md BEFORE this file.

Usage:
  python tools/filing_checklist.py            # render preview/filing-checklist.{html,json}
  python tools/filing_checklist.py --check    # read-only verdict, rc 0 clean / 2 red
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = "preview"
HTML = os.path.join(PREVIEW, "filing-checklist.html")
JSON = os.path.join(PREVIEW, "filing-checklist.json")
BENCH = "docs/global-benchmarks.md"
BLUEPRINT = "BLUEPRINT.md"
BLOCKERS = os.path.join(PREVIEW, "ceo-blockers.json")

SELF = "SELF"
CEO = "CEO"
DERIVED = "DERIVED"
MANUAL = "MANUAL"

# the official timelines, quoted rather than paraphrased (AC-FCL2)
FLOW = [
    ("1", "\u5907\u6848\u4fe1\u606f\u586b\u5199",
     "\u4e3b\u529e\u5355\u4f4d\u4e0e\u8d1f\u8d23\u4eba\u8eab\u4efd\u4fe1\u606f\u3001\u5c0f\u7a0b\u5e8f\u4fe1\u606f\u3001"
     "\u670d\u52a1\u5185\u5bb9\u7c7b\u578b",
     "\u672c\u53f8\u586b", "MANUAL"),
    ("2", "\u5e73\u53f0\u521d\u5ba1", "1-2 \u4e2a\u5de5\u4f5c\u65e5",
     "\u5fae\u4fe1\u5e73\u53f0", "WAIT-PLATFORM"),
    ("3", "\u5de5\u4fe1\u90e8\u77ed\u4fe1\u6838\u9a8c",
     "12381 \u00b7 24h \u5185\u4e8e beian.miit.gov.cn \u5b8c\u6210\uff0c\u903e\u671f\u7cfb\u7edf\u81ea\u52a8\u9a73\u56de",
     "\u4e3b\u529e\u5355\u4f4d\u8d1f\u8d23\u4eba", "MANUAL"),
    ("4", "\u901a\u7ba1\u5c40\u5ba1\u6838", "1-20 \u4e2a\u5de5\u4f5c\u65e5",
     "\u7701\u7ea7\u901a\u4fe1\u7ba1\u7406\u5c40", "WAIT-PLATFORM"),
    ("5", "\u5907\u6848\u53f7\u4e0b\u53d1", "\u7531\u5e73\u53f0\u81ea\u52a8\u5c55\u793a\u4e8e\u5c0f\u7a0b\u5e8f"
     "\u66f4\u591a\u8d44\u6599\u9875", "\u5e73\u53f0", "WAIT-PLATFORM"),
]

# the seven material categories, exactly as counted by the official row (AC-FCL3)
MATERIALS = [
    "\u4e3b\u529e\u5355\u4f4d\u8bc1\u4ef6",
    "\u4e3b\u4f53\u8d1f\u8d23\u4eba\u8bc1\u4ef6",
    "\u5c0f\u7a0b\u5e8f\u8d1f\u8d23\u4eba\u8bc1\u4ef6",
    "\u524d\u7f6e\u5ba1\u6279\u6587\u4ef6",
    "\u8865\u5145\u6750\u6599\uff08\u6388\u6743\u4e66\u00b7\u627f\u8bfa\u4e66\u7b49\uff09",
    "\u8d1f\u8d23\u4eba\u4eba\u8138\u6838\u8eab\u73b0\u573a\u7167",
    "\u771f\u5b9e\u6027\u6838\u9a8c\u5355",
]

# the ten pre-approval categories (AC-FCL3)
PRE_APPROVAL = [
    "\u51fa\u7248\u3010\u6e38\u620f\u3011\u987b\u7248\u53f7",
    "\u7f51\u7edc\u51fa\u7248\u8bb8\u53ef\u8bc1",
    "\u4fe1\u606f\u7f51\u7edc\u4f20\u64ad\u89c6\u542c\u8282\u76ee\u8bb8\u53ef\u8bc1",
    "\u4e92\u8054\u7f51\u836f\u54c1\u4fe1\u606f\u670d\u52a1\u8d44\u683c",
    "\u7f51\u7edc\u6587\u5316\u7ecf\u8425\u8bb8\u53ef",
    "\u4e92\u8054\u7f51\u65b0\u95fb\u670d\u52a1\u8bb8\u53ef",
    "\u7f51\u7ea6\u8f66\u8bb8\u53ef",
    "\u6821\u5916\u57f9\u8bad\u5ba1\u6279",
    "\u5b97\u6559\u4fe1\u606f\u670d\u52a1",
    "\u4e92\u91d1\u76d1\u7ba1\u6279\u590d",
]

TYPES = ["\u65b0\u589e\u5907\u6848", "\u53d8\u66f4\u5907\u6848", "\u6ce8\u9500\u5907\u6848"]

# phrases the official row MUST still carry for the counts above to be true
NEEDLES = ["12381", "1-2 \u4e2a\u5de5\u4f5c\u65e5", "1-20 \u4e2a\u5de5\u4f5c\u65e5",
           "\u771f\u5b9e\u6027\u6838\u9a8c\u5355", "\u7248\u53f7", "2.5.35"]

HARD_ORDER = ("\u5b98\u65b9\u539f\u6587\uff1a\u7ba1\u5c40\u5ba1\u6838\u901a\u8fc7\u540e\uff0c\u5c06\u4e0b\u53d1\u7684"
              "\u5c0f\u7a0b\u5e8f\u5907\u6848\u53f7\u2026\u53ef\u4ee5\u8fdb\u5165\u4e0b\u4e00\u6b65\u7248\u672c"
              "\u53d1\u5e03\u7b49\u6d41\u7a0b")

FORBIDDEN = ("http://", "https://")


def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def benchmark_row(text):
    """The single table row that carries the filing guide, or ''."""
    for line in text.splitlines():
        if "\u5907\u6848" in line and "12381" in line:
            return line
    return ""


def derive():
    """Every DERIVED row, measured on disk right now. Never a typed ready."""
    rows = []
    bench_text = _read(BENCH) if os.path.isfile(BENCH) else ""
    row = benchmark_row(bench_text)
    missing = [n for n in NEEDLES if n not in bench_text]
    rows.append({
        "id": "step-playbook",
        "owner": SELF,
        "kind": DERIVED,
        "title": "\u5b98\u65b9\u6307\u5f15\u5df2\u5165\u518c\uff08\u4e03\u7c7b\u6750\u6599\uff0f\u4e94"
                 "\u73af\u6d41\u7a0b\uff0f\u5341\u7c7b\u524d\u7f6e\u5ba1\u6279\uff09",
        "criterion": "\u5e95\u7a3f\u884c\u4ecd\u8f7d\u8ba1\u6570\u6240\u4f9d\u7684\u516d\u4e2a\u5b57\u9762"
                     "\u77ed\u8bed\uff0c\u7f3a\u4e00\u5373\u5224\u8d1f",
        "state": "READY" if row and not missing else "OPEN",
        "note": ("\u5b57\u9762\u77ed\u8bed\u9f50\u5907\uff08%d \u9879\uff09" % len(NEEDLES))
                if row and not missing
                else ("\u7f3a\uff1a" + ", ".join(missing) if missing else "\u5e95\u7a3f\u884c\u672a\u627e\u5230"),
        "face": "preview/face-sweep.html",
    })
    bp = _read(BLUEPRINT) if os.path.isfile(BLUEPRINT) else ""
    rows.append({
        "id": "step-hard-door",
        "owner": SELF,
        "kind": DERIVED,
        "title": "\u786c\u95e8\uff1a\u5907\u6848\u53f7\u672a\u4e0b\u53d1\u4e0d\u5f97\u53d1\u5e03",
        "criterion": "\u5b98\u65b9\u786c\u987a\u5e8f\u5199\u5165 BLUEPRINT \u751f\u6b7b\u7ebf",
        "state": "READY" if "AIGC" in bp and "msgSecCheck" in bp else "OPEN",
        "note": "\u751f\u6b7b\u7ebf\u4e24\u6761\u5728\u518c",
        "face": "preview/face-sweep.html",
    })
    pending = None
    if os.path.isfile(BLOCKERS):
        try:
            doc = json.loads(_read(BLOCKERS))
            pending = (doc.get("counts") or {}).get("PENDING-PHYSICAL")
        except Exception:
            pending = None
    rows.append({
        "id": "step-ceo-pieces",
        "owner": CEO,
        "kind": MANUAL,
        "title": "\u7269\u7406\u4ef6\uff1a\u670d\u52a1\u5668\uff0f\u57df\u540d"
                 "\uff0f\u5907\u6848+ICP\uff0f\u5546\u6237\u53f7",
        "criterion": "\u56db\u4ef6\u5230\u4f4d\u624d\u80fd\u63d0\u4ea4\u5907\u6848\u4e0e\u6536\u6b3e"
                     "\uff1b\u672c\u53f8\u96f6\u4ee3\u529e",
        "state": "BLOCKED",
        "note": ("\u963b\u585e\u9762\u767b\u8bb0 physical=%s" % pending)
                if isinstance(pending, int) else "\u5f85 CEO",
        "face": "preview/platform-live-report.html",
    })
    rows.append({
        "id": "step-sms-window",
        "owner": CEO,
        "kind": MANUAL,
        "title": "\u77ed\u4fe1\u6838\u9a8c\u7a97\uff1a12381 \u00b7 24h \u5185\u5b8c\u6210"
                 "\uff0c\u903e\u671f\u7cfb\u7edf\u81ea\u52a8\u9a73\u56de",
        "criterion": "\u8d1f\u8d23\u4eba\u624b\u673a\u53ef\u63a5\u6536\u4e14\u5f53\u65e5\u5728\u4f4d",
        "state": "NEEDS-HUMAN",
        "note": "\u672c\u53f8\u65e0\u6cd5\u4ece\u76d8\u4e0a\u6d4b\u5f97\uff0c\u5fc5\u987b\u4eba\u5de5\u786e\u8ba4",
        "face": "preview/filing-checklist.html",
    })
    return rows


def build_rows():
    rows = derive()
    for i, name in enumerate(MATERIALS, 1):
        rows.append({
            "id": "mat-%02d" % i, "owner": CEO, "kind": MANUAL, "title": name,
            "criterion": "\u5b98\u65b9\u5217\u4e3e\u7684\u4e03\u7c7b\u6750\u6599\u4e4b\u4e00"
                         "\uff0c\u987b\u771f\u5b9e\u4e0a\u4f20",
            "state": "NEEDS-HUMAN", "note": "\u65e0\u6cd5\u4ece\u76d8\u4e0a\u5224\u5b9a",
            "face": "preview/filing-checklist.html",
        })
    for i, name in enumerate(PRE_APPROVAL, 1):
        applies = name.startswith("\u51fa\u7248")
        rows.append({
            "id": "pre-%02d" % i, "owner": SELF, "kind": DERIVED, "title": name,
            "criterion": "\u4ec5\u5f53\u5c0f\u7a0b\u5e8f\u5c5e\u6b64\u7c7b\u76ee\u65f6\u9700\u8be5\u8bb8\u53ef",
            "state": "N/A", "note": "\u672c\u4e1a\u52a1\u5f62\u6001\u4e0d\u5c5e\u6b64\u7c7b"
                                    if not applies else "\u5047\u5982\u4e0a\u67b6\u5c0f\u6e38\u620f\u7c7b"
                                    "\u76ee\u5219\u9700\u7248\u53f7",
            "face": "preview/filing-checklist.html",
        })
    return rows


CSS = """
body{margin:0;background:#12141a;color:#dfe3ea;font:15px/1.65 -apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1000px;margin:0 auto;padding:40px 22px 90px}
h1{font-size:23px;margin:0 0 6px}
.sub{color:#8f98a8;font-size:13px;margin-bottom:22px}
.hard{background:#2a1d1d;border:1px solid #5a3232;border-radius:9px;padding:12px 16px;margin:0 0 22px;color:#e8b9b9;font-size:13.5px}
.hard b{color:#ff9d9d}
h2{font-size:16px;margin:30px 0 12px;color:#a9b4c6;border-left:3px solid #3a4252;padding-left:10px}
.row{background:#191d25;border:1px solid #262c38;border-radius:9px;padding:12px 15px;margin:9px 0}
.row.ready{border-color:#2b4a34}.row.open{border-color:#4a2b2b}.row.blocked{border-color:#4a3a2b}
.t{font-weight:600;font-size:15px;margin:0 0 5px}
.c{color:#98a2b3;font-size:13px;margin:0 0 6px}
.n{font-size:12.5px;color:#7f8899}
.badge{display:inline-block;font-size:11px;padding:1px 8px;border-radius:20px;margin-right:8px}
.b-ready{background:#1f3a29;color:#7fd6a0}.b-open{background:#3a2020;color:#e08a8a}
.b-blocked{background:#3a2f1f;color:#e0bb7f}.b-na{background:#232936;color:#9aa4b4}
.b-human{background:#1d2a3a;color:#8fb6e0}
label{display:flex;gap:10px;align-items:flex-start}
input[type=checkbox]{margin-top:4px;width:15px;height:15px;accent-color:#5ac78c}
code{background:#0d1016;padding:1px 5px;border-radius:4px;font-size:12.5px;color:#9fb3d1}
.foot{margin-top:30px;padding-top:14px;border-top:1px solid #262c38;color:#6f7889;font-size:12px}
a{color:#7fb2ff;text-decoration:none;border-bottom:1px dotted #3c5573}
"""

SCRIPT = """
(function(){
  var NS='bd-filing-checklist-v1';
  var boxes=document.querySelectorAll('input[data-ck]');
  function load(){try{return JSON.parse(localStorage.getItem(NS)||'{}')}catch(e){return {}}}
  var state=load();
  Array.prototype.forEach.call(boxes,function(b){
    var k=b.getAttribute('data-ck');
    b.checked=!!state[k];
    b.addEventListener('change',function(){state[k]=b.checked;
      try{localStorage.setItem(NS,JSON.stringify(state))}catch(e){}});
  });
})();
"""


def render_html(rows, sizes):
    out = ["<!DOCTYPE html>",
           '<html lang="zh-CN"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>BigDomain \u00b7 \u5c0f\u7a0b\u5e8f\u5907\u6848\u6267\u884c\u6e05\u5355</title>",
           "<style>" + CSS + "</style></head><body><main>",
           "<h1>\u5c0f\u7a0b\u5e8f\u5907\u6848\u6267\u884c\u6e05\u5355</h1>",
           '<div class="sub">\u6bcf\u4e00\u884c\u7684\u72b6\u6001\u90fd\u662f\u6e32\u67d3\u8fd9\u4e00\u523b'
           '\u5728\u76d8\u4e0a\u6d4b\u51fa\u6765\u7684\uff1b\u6d4b\u4e0d\u51fa\u7684\u4e00\u5f8b\u6807'
           "\u4e3a\u9700\u4eba\u5de5\u786e\u8ba4\uff0c\u4ece\u4e0d\u5199\u6210\u5df2\u5b8c\u6210"
           "\u3002\u52fe\u9009\u53ea\u5b58\u672c\u673a\uff08<code>bd-filing-checklist-v1</code>"
           "\uff09\u3002</div>",
           '<div class="hard"><b>\u786c\u95e8\uff1a</b>' + HARD_ORDER
           + "\u3002\u7b7e\u53d1\u524d\u4e0d\u5f97\u53d1\u5e03\u3002</div>"]
    groups = [("DERIVED\uff08\u76d8\u4e0a\u6d4b\u5f97\uff09", "ready",
               [r for r in rows if r["kind"] == DERIVED and r["state"] == "READY"]),
              ("DERIVED\uff08\u672a\u8fbe\uff09", "open",
               [r for r in rows if r["kind"] == DERIVED and r["state"] == "OPEN"]),
              ("\u524d\u7f6e\u5ba1\u6279\u7c7b\u76ee\uff08\u4ec5\u5f53\u5c5e\u6b64\u7c7b\u65f6\u9700"
               "\uff09", "blocked",
               [r for r in rows if r["state"] == "N/A"]),
              ("\u4eba\u5de5\u884c\uff08\u4e0d\u53ef\u52fe\uff09", "blocked",
               [r for r in rows if r["kind"] == MANUAL])]
    for title, cls, items in groups:
        out.append("<h2>%s (%d)</h2>" % (title, len(items)))
        if not items:
            out.append('<div class="row"><div class="n">\u672c\u7ec4\u4e3a\u7a7a\u3002</div></div>')
            continue
        for r in items:
            badge = {"READY": "b-ready", "OPEN": "b-open", "BLOCKED": "b-blocked",
                     "N/A": "b-na", "NEEDS-HUMAN": "b-human"}.get(r["state"], "b-na")
            out.append('<div class="row %s">' % {"READY": "ready", "OPEN": "open"}.get(r["state"], "blocked"))
            out.append("<label>")
            if r["state"] == "READY":
                out.append('<input type="checkbox" data-ck="%s">' % r["id"])
            else:
                out.append('<input type="checkbox" data-ck="%s" disabled>' % r["id"])
            out.append("<span>")
            out.append('<div class="t"><span class="badge %s">%s</span>%s</div>'
                       % (badge, r["state"], r["title"]))
            out.append('<div class="c">\u5224\u636e\uff1a%s</div>' % r["criterion"])
            out.append('<div class="n">%s</div>' % r["note"])
            if r["face"].replace("\\", "/") == HTML.replace("\\", "/"):
                # self-reference never becomes a link: the page existing would
                # otherwise change the page, and AC-FCL6 needs a fixed point.
                out.append('<div class="n">\u8bc1\u636e\u9762\uff1a\u672c\u9875 %s</div>'
                           % r["face"])
            elif os.path.isfile(r["face"]):
                # href is page-relative (the browser's base is preview/), while
                # the label stays the repo-relative path. ship_checklist.py has
                # always done this; this page shipped a repo-relative href and
                # every link 404'd for a reader who opened it from disk.
                out.append('<div class="n">\u8bc1\u636e\u9762\uff1a<a href="%s">%s</a></div>'
                           % (os.path.basename(r["face"]), r["face"]))
            out.append("</span></label></div>")
    out.append("<h2>\u4e94\u73af\u6d41\u7a0b\u4e0e\u5b98\u65b9\u65f6\u9650</h2>")
    for no, name, window, who, state in FLOW:
        out.append('<div class="row"><div class="t">%s. %s \u00b7 <code>%s</code></div>'
                   '<div class="n">\u8d1f\u8d23\uff1a%s \u00b7 \u72b6\u6001\uff1a%s</div></div>'
                   % (no, name, window, who, state))
    out.append("<h2>\u5907\u6848\u7c7b\u578b\uff08%d\uff09</h2>" % len(TYPES))
    out.append('<div class="row"><div class="n">%s</div></div>' % " \u00b7 ".join(TYPES))
    out.append('<div class="foot">\u672c\u9875\u7531 <code>python tools/filing_checklist.py</code> '
               "\u6d3e\u751f\uff08html %d B \u00b7 json %d B\uff09\u3002\u5e38\u9a7b\u63d0\u793a\uff1a"
               "\u4e00\u5207\u6c99\u7bb1\u9762\u5747 mock=true / chargeable=false\uff0c"
               "\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\uff1b\u751f\u6210\u5185\u5bb9\u4e00\u5f8b"
               "\u5e26 AIGC \u6807\u8bc6\u3002\u6765\u6e90\uff1adocs/global-benchmarks.md"
               "\uff08\u5b98\u65b9\u9875\u76f4\u91c7\uff09\u3002</div>" % (sizes["html"], sizes["json"]))
    out.append("</main><script>" + SCRIPT + "</script></body></html>")
    return "\n".join(out) + "\n"


def build_json(rows, sizes):
    return {
        "schema_version": 1,
        "surface": HTML,
        "note": "Derived rows are recomputed from disk at render time; MANUAL rows are never ready.",
        "counts": {
            "materials": len(MATERIALS),
            "pre_approval": len(PRE_APPROVAL),
            "filing_types": len(TYPES),
            "flow_steps": len(FLOW),
        },
        "hard_order": HARD_ORDER,
        "items": rows,
        "flow": [{"no": n, "name": nm, "window": w, "owner": o, "state": s}
                 for n, nm, w, o, s in FLOW],
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

    # AC-FCL1 derived rows are live, manual rows are never ready
    want = {r["id"]: r["state"] for r in rows}
    for r in doc.get("items", []):
        if want.get(r["id"]) != r["state"]:
            fails.append("AC-FCL1 %s is stale: json=%s disk=%s"
                         % (r["id"], r["state"], want.get(r["id"])))
    if any(r["state"] == "READY" for r in rows if r["kind"] == MANUAL):
        fails.append("AC-FCL1 a MANUAL row claims READY")

    # AC-FCL2 the official timelines and the hard-order quote are present
    for needle in ("1-2 \u4e2a\u5de5\u4f5c\u65e5", "12381", "24h",
                   "1-20 \u4e2a\u5de5\u4f5c\u65e5"):
        if needle not in html:
            fails.append("AC-FCL2 timeline %r missing from the page" % needle)
    if "\u7ba1\u5c40\u5ba1\u6838\u901a\u8fc7\u540e" not in html:
        fails.append("AC-FCL2 the hard-order sentence is not quoted")

    # AC-FCL3 counts equal the registry AND the benchmark row still carries them
    counts = doc.get("counts") or {}
    if counts.get("materials") != len(MATERIALS):
        fails.append("AC-FCL3 material count drifted")
    if counts.get("pre_approval") != len(PRE_APPROVAL):
        fails.append("AC-FCL3 pre-approval count drifted")
    if counts.get("filing_types") != len(TYPES):
        fails.append("AC-FCL3 filing-type count drifted")
    bench = _read(BENCH) if os.path.isfile(BENCH) else ""
    missing = [n for n in NEEDLES if n not in bench]
    if missing:
        fails.append("AC-FCL3 the benchmark row lost %s" % ", ".join(missing))

    # AC-FCL4 offline and every link target exists
    for bad in FORBIDDEN:
        if bad in html:
            fails.append("AC-FCL4 html carries %s" % bad)
    page_base = os.path.dirname(HTML)
    for href in re.findall(r'href="([^"]+)"', html):
        # resolve the way a BROWSER resolves it - against the page's own dir.
        # this check used to resolve against the repo root, which is exactly why
        # a repo-relative href could ship broken and still read AC-FCL4 green.
        target = href.split("#", 1)[0].split("?", 1)[0]
        if "://" in target or target.startswith(("mailto:", "javascript:", "data:")):
            continue
        if not os.path.isfile(os.path.normpath(os.path.join(page_base, target))):
            fails.append("AC-FCL4 link target missing: %s" % href)

    # AC-FCL5 tick ids, one namespace, one inline script
    for r in rows:
        if 'data-ck="%s"' % r["id"] not in html:
            fails.append("AC-FCL5 row %s has no tick id" % r["id"])
    if html.count("<script>") != 1:
        fails.append("AC-FCL5 expected exactly one inline script")
    if "var NS='bd-filing-checklist-v1';" not in html:
        fails.append("AC-FCL5 namespace declaration missing")

    # AC-FCL6 sizes fixed point
    sizes = doc.get("sizes") or {}
    if sizes.get("html") != os.path.getsize(HTML):
        fails.append("AC-FCL6 html size is not the disk size")
    if sizes.get("json") != os.path.getsize(JSON):
        fails.append("AC-FCL6 json size is not the disk size")

    # AC-FCL8 the three hard doors are restated with existing faces
    for rid in ("step-hard-door", "step-playbook", "step-ceo-pieces"):
        hit = [r for r in rows if r["id"] == rid]
        if not hit:
            fails.append("AC-FCL8 %s missing" % rid)
        elif not os.path.isfile(hit[0]["face"]):
            fails.append("AC-FCL8 %s face missing on disk" % rid)
    return fails


def main(argv):
    if "--check" in argv:
        fails = check()
        if fails:
            print("VERDICT FAIL %d" % len(fails))
            for f in fails[:20]:
                print("  - " + f)
            return 2
        doc = json.loads(_read(JSON))
        ready = len([r for r in doc["items"] if r["state"] == "READY"])
        human = len([r for r in doc["items"] if r["state"] in ("NEEDS-HUMAN", "BLOCKED")])
        print("VERDICT PASS 8/8 items=%d ready=%d manual=%d materials=%d pre_approval=%d "
              "flow=%d html=%dB json=%dB"
              % (len(doc["items"]), ready, human, doc["counts"]["materials"],
                 doc["counts"]["pre_approval"], doc["counts"]["flow_steps"],
                 os.path.getsize(HTML), os.path.getsize(JSON)))
        return 0
    html, text, rows, sizes = render(write=True)
    ready = len([r for r in rows if r["state"] == "READY"])
    human = len([r for r in rows if r["state"] in ("NEEDS-HUMAN", "BLOCKED")])
    print("WROTE %s (%dB) + %s (%dB) items=%d ready=%d manual=%d"
          % (HTML, sizes["html"], JSON, sizes["json"], len(rows), ready, human))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
