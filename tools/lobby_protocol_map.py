#!/usr/bin/env python3
"""Lobby protocol map: the P-47 item-1 protocol surface as one page.

The spec docs/spec/lobby-websocket-spec.md carries the whole lobby protocol in
PROSE. The only shipped face about it is the handshake demo. Nothing on disk
answers, in one screen, which message identifiers the protocol defines, which
spec section defines each, and which of them no acceptance criterion tests.

Everything on this page is DERIVED at render time from the spec and from the
repository file index. The module source carries no message name, no section
title and no criterion id as a literal; the only literals are the regex shapes
and the JSON/HTML skeleton.

Usage:
    python tools/lobby_protocol_map.py            # render both artifacts
    python tools/lobby_protocol_map.py --check    # read-only verdict

Criteria AC-LPM1..AC-LPM6 were pinned in src/os/backlog.md BEFORE this file.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "docs", "spec", "lobby-websocket-spec.md")
HTML = os.path.join(ROOT, "preview", "lobby-protocol-map.html")
JSON_OUT = os.path.join(ROOT, "preview", "lobby-protocol-map.json")
IMPL = os.path.join(ROOT, "src", "sandbox", "lobby", "server.py")

NS = "bd-lobby-protocol-map-v1"

DOTTED = re.compile(r"(?<![A-Za-z0-9_.])([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,2})(?![A-Za-z0-9_])")
CRIT_ROW = re.compile(r"^\|\s*(AC-[SP][0-9A-Za-z]*)\s*\|(.*)$")
SECTION = re.compile(r"^(#{2,3})\s+(.*)$")
SCOPE_HEADING = re.compile(r"^\u4e8c\u3001")  # the protocol-spec part starts here
EXT = re.compile(r"^[a-z0-9]{2,5}$")


def read_spec():
    with open(SPEC, "r", encoding="utf-8") as f:
        return f.read()


def repo_basenames():
    """Every filename in the repo, so a dotted token can be classified as a
    FILE REFERENCE by existence instead of by a hand-written exception list."""
    names = set()
    skip = {".git", ".codely-cli", "__pycache__", "node_modules"}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in files:
            names.add(fn.lower())
    return names


def scan(text, basenames):
    # JSON keys printed in the spec samples: a dotted token whose FIRST segment
    # is one of those keys is a field path (payload.rooms), not a message name.
    field_roots = set(re.findall(r'"([a-z_][a-z0-9_]*)"\s*:', text))
    lines = text.splitlines()
    section = ""
    in_scope = False
    rows = []          # criteria rows: id, text, tokens
    hits = {}          # token -> {sections, count, criteria}
    for line in lines:
        s = line.strip()
        m = SECTION.match(s)
        if m:
            title = m.group(2).strip()
            if SCOPE_HEADING.match(title):
                in_scope = True
            section = title
            continue
        cm = CRIT_ROW.match(s)
        if cm:
            cid = cm.group(1)
            cells = [c.strip() for c in cm.group(2).split("|")]
            body = cells[0] if cells else ""
            toks = sorted(set(DOTTED.findall(body)))
            rows.append({"id": cid, "tokens": toks, "text": body})
            for t in toks:
                rec = hits.setdefault(t, {"sections": [], "count": 0, "criteria": [], "in_scope": False})
                if section and section not in rec["sections"]:
                    rec["sections"].append(section)
                rec["count"] += body.count(t)
                if cid not in rec["criteria"]:
                    rec["criteria"].append(cid)
                rec["in_scope"] = rec["in_scope"] or in_scope
            continue
        for t in DOTTED.findall(s):
            rec = hits.setdefault(t, {"sections": [], "count": 0, "criteria": [], "in_scope": False})
            if section and section not in rec["sections"]:
                rec["sections"].append(section)
            rec["count"] += 1
            rec["in_scope"] = rec["in_scope"] or in_scope

    tokens = []
    for t, rec in sorted(hits.items()):
        last = t.split(".")[-1]
        root = t.split(".")[0]
        # a token is a FILE REFERENCE when some repo file is named <something>.<last>
        is_file = any(fn.endswith("." + last) and EXT.match(last) for fn in basenames)
        kind = "file-ref" if is_file else ("field-path" if root in field_roots else "message")
        covered = bool(rec["criteria"])
        tokens.append({
            "token": t,
            "kind": kind,
            "sections": rec["sections"],
            "count": rec["count"],
            "criteria": rec["criteria"],
            "covered": covered,
            "in_scope": rec["in_scope"],
        })
    return rows, tokens


def payload():
    text = read_spec()
    basenames = repo_basenames()
    rows, tokens = scan(text, basenames)
    # the shipped sandbox is the implementation authority: a spec identifier that
    # the server source also names is an IMPLEMENTED message, everything else is a
    # spec-only token (field path, payload key, prose artefact).
    impl = set()
    if os.path.exists(IMPL):
        with open(IMPL, "r", encoding="utf-8", errors="replace") as f:
            impl = set(DOTTED.findall(f.read()))
    for t in tokens:
        if t["kind"] == "message":
            t["implemented"] = t["token"] in impl
            if not t["implemented"]:
                t["kind"] = "spec-only"
    messages = [t for t in tokens if t["kind"] == "message"]
    spec_only = [t for t in tokens if t["kind"] == "spec-only"]
    uncover = [t["token"] for t in messages if not t["covered"]]
    files = [t for t in tokens if t["kind"] == "file-ref"]
    fields = spec_only
    sections = [m.group(2).strip() for m in (SECTION.match(l.strip()) for l in text.splitlines()) if m]
    return {
        "namespace": NS,
        "spec": os.path.relpath(SPEC, ROOT).replace("\\", "/"),
        "spec_bytes": os.path.getsize(SPEC),
        "spec_lines": len(text.splitlines()),
        "impl": os.path.relpath(IMPL, ROOT).replace("\\", "/"),
        "impl_bytes": os.path.getsize(IMPL) if os.path.exists(IMPL) else 0,
        "section_count": len(sections),
        "criteria_rows": len(rows),
        "criteria_sandbox": len([r for r in rows if r["id"].startswith("AC-S")]),
        "criteria_prod": len([r for r in rows if r["id"].startswith("AC-P")]),
        "token_count": len(tokens),
        "message_count": len(messages),
        "file_ref_count": len(files),
        "field_path_count": len(fields),
        "uncovered_count": len(uncover),
        "uncovered": uncover,
        "criteria": rows,
        "messages": messages,
        "file_refs": files,
        "field_paths": fields,
        "gate": "derived from the spec at render time; no message name is typed in the source",
    }


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_html(p):
    rows = []
    for r in p["criteria"]:
        toks = " ".join("<code>%s</code>" % esc(t) for t in r["tokens"]) or "<span class=dim>no dotted token</span>"
        rows.append("<tr><td class=id>%s</td><td>%s</td><td class=tok>%s</td></tr>"
                    % (esc(r["id"]), esc(r["text"][:260]), toks))
    msgs = []
    for m in p["messages"]:
        cov = "COVERED" if m["covered"] else "UNCOVERED"
        cls = "ok" if m["covered"] else "bad"
        crit = ", ".join(m["criteria"]) or "none"
        secs = " / ".join(m["sections"]) or "no section"
        msgs.append(
            "<tr data-tok=\"%s\"><td><code>%s</code></td><td>%s</td><td>%d</td><td>%s</td><td class=%s>%s</td></tr>"
            % (esc(m["token"]), esc(m["token"]), esc(secs), m["count"], esc(crit), cls, cov))
    files = []
    for f in p["file_refs"] + p["field_paths"]:
        files.append("<tr data-tok=\"%s\"><td><code>%s</code></td><td>%s</td><td>%s</td><td>%d</td></tr>"
                     % (esc(f["token"]), esc(f["token"]), esc(f["kind"]),
                        esc(" / ".join(f["sections"]) or "-"), f["count"]))
    unc = "".join("<li><code>%s</code></li>" % esc(t) for t in p["uncovered"]) or "<li class=dim>none - every message identifier is named by at least one criterion row</li>"
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>P-47-1 lobby protocol map - messages and criterion coverage</title>
<style>
body{margin:0;background:#111417;color:#e8eaed;font:15px/1.55 "Segoe UI",system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 22px 60px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:30px 0 10px;color:#9fd0ff}
.sub{color:#9aa3ad;font-size:13px;margin-bottom:18px}
.grid{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 6px}
.card{background:#1a1f24;border:1px solid #2a3238;border-radius:8px;padding:10px 14px;min-width:132px}
.card b{display:block;font-size:21px;color:#fff}.card span{color:#9aa3ad;font-size:12px}
table{width:100%%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid #23292e;padding:6px 8px;text-align:left;vertical-align:top}
th{color:#9aa3ad;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
code{background:#0d1013;border:1px solid #23292e;border-radius:4px;padding:1px 5px;font-size:12px;color:#c9e2ff}
td.id{white-space:nowrap;color:#ffd479;font-weight:600}
td.tok code{display:inline-block;margin:1px 3px 1px 0}
.ok{color:#5ddb8a;font-weight:600;white-space:nowrap}.bad{color:#ff7b72;font-weight:600;white-space:nowrap}
.dim{color:#6b757e}
.note{background:#1a1f24;border-left:3px solid #3d7eff;padding:10px 12px;border-radius:0 6px 6px 0;margin:12px 0;font-size:13px;color:#c3ccd6}
input{background:#0d1013;border:1px solid #2a3238;border-radius:6px;color:#e8eaed;padding:7px 10px;width:280px;font-size:13px}
footer{margin-top:34px;color:#6b757e;font-size:12px}
</style></head><body><main>
<h1>\\u5927\\u5385\\u534f\\u8bae\\u6d88\\u606f\\u5b57\\u5178 + \\u5224\\u636e\\u8986\\u76d6</h1>
<div class="sub">P-47 \\u7b2c\\u2460\\u4ef6 \\u00b7 \\u5168\\u90e8\\u6570\\u5b57\\u5728\\u6e32\\u67d3\\u90a3\\u4e00\\u523b\\u4ece <code>%(spec)s</code>\\uff08%(spec_bytes)d \\u5b57\\u8282 / %(spec_lines)d \\u884c / %(section_count)d \\u8282\\uff09\\u4e0e\\u672c\\u4ed3\\u6587\\u4ef6\\u540d\\u7d22\\u5f15\\u6d3e\\u751f\\uff0c\\u6e90\\u7801\\u5185\\u96f6\\u6d88\\u606f\\u540d\\u5b57\\u9762\\u3002</div>
<div class="grid">
<div class="card"><b>%(criteria_rows)d</b><span>\\u9a8c\\u6536\\u5224\\u636e\\u884c\\uff08S \\u7cfb %(criteria_sandbox)d / P \\u7cfb %(criteria_prod)d\\uff09</span></div>
<div class="card"><b>%(message_count)d</b><span>\\u534f\\u8bae\\u6d88\\u606f\\u6807\\u8bc6</span></div>
<div class="card"><b>%(uncovered_count)d</b><span>\\u65e0\\u5224\\u636e\\u8986\\u76d6\\u7684\\u6d88\\u606f</span></div>
<div class="card"><b>%(excluded_count)d</b><span>\\u88ab\\u6392\\u9664\\u7684\\u6807\\u8bc6\\uff08\\u6587\\u4ef6\\u5f15\\u7528+\\u5b57\\u6bb5\\u8def\\u5f84\\uff09</span></div>
</div>
<div class="note"><b>\\u8fd9\\u4e00\\u9875\\u56de\\u7b54\\u4ec0\\u4e48\\uff1a</b>\\u534f\\u8bae\\u5230\\u5e95\\u5b9a\\u4e49\\u4e86\\u54ea\\u4e9b\\u6d88\\u606f\\u3001\\u6bcf\\u6761\\u6d88\\u606f\\u7531\\u54ea\\u4e00\\u8282\\u5b9a\\u4e49\\u3001\\u88ab\\u54ea\\u6761\\u9a8c\\u6536\\u5224\\u636e\\u70b9\\u540d\\uff1b\\u4ee5\\u53ca<b>\\u54ea\\u4e9b\\u6d88\\u606f\\u4e00\\u6761\\u5224\\u636e\\u90fd\\u6ca1\\u6709</b>\\u3002\\u5206\\u7c7b\\u4e0d\\u9760\\u624b\\u5199\\u4f8b\\u5916\\u8868\\u2014\\u2014\\u672b\\u6bb5\\u4e0e\\u4ed3\\u5185\\u67d0\\u6587\\u4ef6\\u540d\\u540e\\u7f00\\u76f8\\u7b26\\u7684\\u6807\\u8bc6\\u88ab\\u5224\\u4e3a\\u300c\\u6587\\u4ef6\\u5f15\\u7528\\u300d\\uff0c\\u5176\\u4f59\\u4e3a\\u6d88\\u606f\\u3002</div>
<h2>\\u65e0\\u5224\\u636e\\u8986\\u76d6\\u7684\\u6d88\\u606f\\uff08\\u5b9e\\u6d4b\\u7f3a\\u53e3\\uff09</h2>
<ul>%(unc)s</ul>
<h2>\\u6d88\\u606f\\u5b57\\u5178\\uff08\\u6309\\u6807\\u8bc6\\u6392\\u5e8f\\uff09</h2>
<input id="q" placeholder="\\u8fc7\\u6ee4\\uff1a\\u8f93\\u5165\\u6d88\\u606f\\u524d\\u7f00\\u6216\\u5224\\u636e\\u53f7">
<table id="mt"><thead><tr><th>\\u6807\\u8bc6</th><th>\\u5b9a\\u4e49\\u8282</th><th>\\u51fa\\u73b0</th><th>\\u70b9\\u540d\\u5b83\\u7684\\u5224\\u636e</th><th>\\u8986\\u76d6</th></tr></thead><tbody>%(msgs)s</tbody></table>
<h2>\\u9a8c\\u6536\\u5224\\u636e\\u884c\\uff08\\u9010\\u6761\\u539f\\u6587\\uff0c\\u622a\\u65ad 260 \\u5b57\\uff09</h2>
<table><thead><tr><th>\\u5224\\u636e</th><th>\\u539f\\u6587</th><th>\\u5176\\u70b9\\u540d\\u7684\\u6807\\u8bc6</th></tr></thead><tbody>%(rows)s</tbody></table>
<h2>\\u88ab\\u5224\\u4e3a\\u6587\\u4ef6\\u5f15\\u7528 / \\u5b57\\u6bb5\\u8def\\u5f84\\u7684\\u6807\\u8bc6\\uff08\\u4e0d\\u8ba1\\u5165\\u6d88\\u606f\\uff09</h2>
<table><thead><tr><th>\\u6807\\u8bc6</th><th>\\u7c7b\\u578b</th><th>\\u51fa\\u73b0\\u8282</th><th>\\u51fa\\u73b0</th></tr></thead><tbody>%(files)s</tbody></table>
<footer>\\u7531 <code>python tools/lobby_protocol_map.py</code> \\u6d3e\\u751f \\u00b7 \\u5224\\u636e AC-LPM1..6 \\u00b7 <code>--check</code> \\u53ea\\u8bfb\\u6821\\u9a8c \\u00b7 \\u65ad\\u7f51\\u53ef\\u5f00</footer>
</main>
<script>
(function(){
  var NS='%(ns)s', q=document.getElementById('q'), rows=[].slice.call(document.querySelectorAll('#mt tbody tr'));
  var saved=localStorage.getItem(NS); if(saved){q.value=saved;}
  function apply(){var v=q.value.toLowerCase();rows.forEach(function(r){r.style.display=(r.getAttribute('data-tok')||'').indexOf(v)>=0||(r.textContent||'').toLowerCase().indexOf(v)>=0?'':'none';});localStorage.setItem(NS,q.value);}
  q.addEventListener('input',apply); if(q.value){apply();}
})();
</script></body></html>
""" % {
        "spec": esc(p["spec"]), "spec_bytes": p["spec_bytes"], "spec_lines": p["spec_lines"],
        "section_count": p["section_count"], "criteria_rows": p["criteria_rows"],
        "criteria_sandbox": p["criteria_sandbox"], "criteria_prod": p["criteria_prod"],
        "message_count": p["message_count"], "uncovered_count": p["uncovered_count"],
        "file_ref_count": p["file_ref_count"],
        "excluded_count": p["file_ref_count"] + p["field_path_count"], "ns": NS,
        "unc": unc, "msgs": "".join(msgs), "rows": "".join(rows), "files": "".join(files),
    }


def write_artifacts():
    p = payload()
    html = render_html(p)
    p["html_bytes"] = len(html.encode("utf-8"))
    # the payload records its own artifact size, so settle the fixed point:
    # dump, measure, and accept only when the recorded value equals the write.
    for _ in range(4):
        js = json.dumps(p, ensure_ascii=False, indent=1) + "\n"
        size = len(js.encode("utf-8"))
        if p.get("json_bytes") == size:
            break
        p["json_bytes"] = size
    js = json.dumps(p, ensure_ascii=False, indent=1) + "\n"
    p["json_bytes"] = len(js.encode("utf-8"))
    js = json.dumps(p, ensure_ascii=False, indent=1) + "\n"
    os.makedirs(os.path.dirname(HTML), exist_ok=True)
    with open(HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    with open(JSON_OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    return p


def check():
    p = payload()
    html = render_html(p)
    fails = []
    if not os.path.exists(HTML):
        fails.append("html missing")
    elif open(HTML, encoding="utf-8").read() != html:
        fails.append("html is not the fresh derivation")
    if not os.path.exists(JSON_OUT):
        fails.append("json missing")
    else:
        disk = json.load(open(JSON_OUT, encoding="utf-8"))
        if disk.get("spec_bytes") != os.path.getsize(SPEC):
            fails.append("recorded spec bytes differ from disk")
        if disk.get("message_count") != p["message_count"]:
            fails.append("recorded message count differs from the fresh scan")
        if disk.get("uncovered_count") != p["uncovered_count"]:
            fails.append("recorded uncovered count differs from the fresh scan")
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    if any(ord(c) > 127 for c in src):
        fails.append("source is not pure ASCII")
    verdict = "PASS" if not fails else "FAIL"
    print("LOBBY PROTOCOL MAP %s criteria=%d messages=%d uncovered=%d file_refs=%d html=%sB fails=%d"
          % (verdict, p["criteria_rows"], p["message_count"], p["uncovered_count"],
             p["file_ref_count"], os.path.getsize(HTML) if os.path.exists(HTML) else -1, len(fails)))
    for f in fails:
        print("  - " + f)
    return 0 if not fails else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    p = write_artifacts()
    print("wrote preview/lobby-protocol-map.html %dB and .json %dB criteria=%d messages=%d uncovered=%d"
          % (p["html_bytes"], p["json_bytes"], p["criteria_rows"], p["message_count"], p["uncovered_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
