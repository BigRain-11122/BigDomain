#!/usr/bin/env python3
"""First-yuan money path face (BigDomain R2772).

Renders preview/first-yuan.html + preview/first-yuan.json from SIX shipped
business faces plus the debt register and the CEO-blocker face. No verdict is
typed into this file: every carrier state is read from the report that carries
it, every blocker count is read from the register that owns it, and the window
verdict is computed by the rule pinned below.

Criteria pinned BEFORE the code (state/queue/tech.md:1, row AC-FYP1..7):
  AC-FYP1 the page carries exactly the carrier rows a fresh parse of the six
          reports yields, in the same order, so a report that changes shape
          without a re-render reddens this face.
  AC-FYP2 every carrier state string equals a fresh read of that report field
          (verdict / reconcile_rc / hole_status); nothing is hand-typed.
  AC-FYP3 --check must not author the artifact it verifies (size+mtime control,
          AC-UGR10 precedent).
  AC-FYP4 the three standing compliance faces are present: AIGC marking,
          msgSecCheck front gate, non-advice disclaimer.
  AC-FYP5 zero http:// or https:// literals, so the page opens offline.
  AC-FYP6 recorded sizes equal disk bytes (self-referential fixpoint).
  AC-FYP7 the window verdict equals the pinned rule applied to the FRESH
          inputs, and when it is not READY the first blocking edge is named:
            READY iff every carrier is OK and physical == 0 and decisions == 0
            BLOCKED-PHYSICAL if physical > 0
            BLOCKED-DECISION elif decisions > 0
            BLOCKED-CODE elif some carrier is not OK

Read-only by default: without --write nothing on disk is touched.
"""
import argparse
import io
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_REL = "preview/first-yuan.html"
JSON_REL = "preview/first-yuan.json"

# (id, label, json path, field that carries the state)
CARRIERS = [
    ("C1", "大厅 WebSocket 握手面", "preview/lobby-ws-report.json", "verdict"),
    ("C2", "城市观测面", "preview/city-face-report.json", "verdict"),
    ("C3", "19.9 支付通道面", "preview/payment-gate-report.json", "verdict"),
    ("C4", "权益 / 月卡面", "preview/membership-benefit-report.json", "verdict"),
    ("C5", "代币双式账本面", "preview/ledger-business-report.json", "reconcile_rc"),
    ("C6", "UGC 安全闸面", "preview/ugc-gate-report.json", "hole_status"),
]


def _abs(rel):
    return os.path.join(BASE, rel.replace("/", os.sep))


def _read(rel):
    with io.open(_abs(rel), "r", encoding="utf-8") as fh:
        return fh.read()


def carrier_row(cid, label, rel, field):
    doc = json.loads(_read(rel))
    if field == "reconcile_rc":
        rc = doc.get("reconcile_rc")
        refused = len(doc.get("rejected") or [])
        state = "reconcile_rc=%s refused=%d tx=%s entries=%s" % (
            rc, refused, doc.get("tx_count"), doc.get("entry_count"))
        ok = rc == 0
    elif field == "hole_status":
        state = "hole_status=%s" % (doc.get("hole_status"),)
        # Hole LIVE means the front gate is not wired in this deployment; that
        # is a physical-item blocker, not a code defect, and it must not read OK.
        ok = doc.get("hole_status") != "LIVE"
    else:
        state = "verdict=%s" % (doc.get(field),)
        ok = doc.get(field) == "PASS"
    path = _abs(rel)
    return {
        "id": cid,
        "label": label,
        "source": rel,
        "field": field,
        "state": state,
        "ok": bool(ok),
        "bytes": os.path.getsize(path),
        "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(path))),
    }


def debt_open_rows():
    rows = []
    for line in _read("state/debt.md").split("\n"):
        if not line.startswith("- [ ]"):
            continue
        item = ""
        for seg in line.split("|"):
            seg = seg.strip().lstrip("-").strip().lstrip("[]").strip()
            if seg.startswith("item="):
                item = seg.split("=", 1)[1].strip()
        if item:
            rows.append(item)
    return rows


def blockers():
    ceo = json.loads(_read("preview/ceo-blockers.json"))
    counts = ceo.get("counts") or {}
    physical = [r for r in ceo.get("rows") or []
                if r.get("state") == "PENDING-PHYSICAL" or "PHYSICAL" in json.dumps(r.get("state"), ensure_ascii=False)]
    # The blocker face keeps its classification in counts; the row-level class is
    # carried by the same keys, so read both and never invent a number.
    physical_n = int(counts.get("PENDING-PHYSICAL", 0))
    decision_n = int(counts.get("PENDING-DECISION", 0))
    named_physical = [r.get("id") for r in physical][:4]
    code_rows = debt_open_rows()
    return {
        "physical": physical_n,
        "decisions": decision_n,
        "code_open": len(code_rows),
        "named_physical": named_physical,
        "code_items": code_rows,
    }


def derive():
    rows = [carrier_row(*c) for c in CARRIERS]
    blk = blockers()
    reasons = []
    if all(r["ok"] for r in rows) and blk["physical"] == 0 and blk["decisions"] == 0:
        verdict = "READY"
        top_edge = "无阻塞边：可直接进入真实收款链"
    elif blk["physical"] > 0:
        verdict = "BLOCKED-PHYSICAL"
        top_edge = "物理件未到位 %d 项（具名清单见 preview/ceo-blockers.html）；UGC 闸现读 %s" % (
            blk["physical"],
            [r["state"] for r in rows if r["id"] == "C6"][0],
        )
    elif blk["decisions"] > 0:
        verdict = "BLOCKED-DECISION"
        top_edge = "待 CEO 决策 %d 项" % blk["decisions"]
    else:
        verdict = "BLOCKED-CODE"
        bad = [r["id"] for r in rows if not r["ok"]]
        top_edge = "代码面未绿 %s" % (",".join(bad) or "?")
    for r in rows:
        reasons.append("%s %s %s" % (r["id"], r["state"], "OK" if r["ok"] else "NOT-OK"))
    return {
        "schema": "bigdomain-first-yuan-1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "carriers": rows,
        "blockers": blk,
        "verdict": verdict,
        "top_edge": top_edge,
        "reasons": reasons,
        "sizes": {"html": 0, "json": 0},
    }


COMPLIANCE = [
    "AI 生成内容全程显式标识 + 隐式水印双轨",
    "msgSecCheck 前置闸：未接入前 UGC 不开放",
    "非投顾定性：本平台不构成投资建议",
]


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_html(d):
    rows = []
    for r in d["carriers"]:
        rows.append(
            "<tr class=\"%s\"><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s B</td></tr>" % (
                "ok" if r["ok"] else "bad", esc(r["id"]), esc(r["label"]),
                esc(r["state"]), "PASS" if r["ok"] else "BLOCKED",
                esc(r["source"]), r["bytes"]))
    blk = d["blockers"]
    items = "".join("<li>%s</li>" % esc(x) for x in blk["code_items"])
    named = "%d 项待 CEO 交件" % blk["physical"]
    comp = "".join("<li>%s</li>" % esc(x) for x in COMPLIANCE)
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>BigDomain 第一笔收入路径</title>
<style>
body{font-family:-apple-system,"Segoe UI",sans-serif;margin:32px;color:#1b1f24;background:#fbfbfc}
h1{font-size:22px;margin:0 0 4px}
.sub{color:#5b6572;font-size:13px;margin-bottom:20px}
table{border-collapse:collapse;width:100%%;font-size:13px;background:#fff}
th,td{border:1px solid #e3e6ea;padding:7px 9px;text-align:left;vertical-align:top}
th{background:#f3f5f7}
tr.ok td:nth-child(5){color:#126b34;font-weight:600}
tr.bad td:nth-child(5){color:#a3231b;font-weight:600}
.banner{margin:18px 0;padding:14px 16px;border-radius:6px;background:#fff4e5;border:1px solid #f0c48a}
.banner.ready{background:#eaf7ee;border-color:#9ad3ae}
.banner h2{margin:0 0 6px;font-size:16px}
.cols{display:flex;gap:16px;margin-top:16px;flex-wrap:wrap}
.card{flex:1 1 260px;background:#fff;border:1px solid #e3e6ea;border-radius:6px;padding:12px 14px;font-size:13px}
.card h3{margin:0 0 8px;font-size:14px}
ul{margin:0;padding-left:18px}
code{background:#f3f5f7;padding:2px 5px;border-radius:3px;font-size:12px}
footer{margin-top:22px;font-size:12px;color:#5b6572}
</style></head><body>
<h1>BigDomain · 第一笔收入路径（19.9 元）</h1>
<div class="sub">六条承载面状态与阻塞边全部由盘上报告现读，结论按固定规则现算 · 生成时间 %s UTC · 派生自 %s</div>
<table><thead><tr><th>#</th><th>承载面</th><th>现读状态</th><th>判定</th><th>来源</th><th>字节</th></tr></thead>
<tbody>%s</tbody></table>
<div class="banner%s"><h2>窗口结论：%s</h2><div>首位阻塞边：%s</div></div>
<div class="cols">
<div class="card"><h3>物理件（CEO 保留面）%d 项</h3><ul><li>具名：%s</li><li>完整清单见 <code>preview/ceo-blockers.html</code></li></ul></div>
<div class="card"><h3>待决策 %d 项</h3><ul><li>定价与开闸按 P1 只呈批不执行</li></ul></div>
<div class="card"><h3>代码开放债 %d 行</h3><ul>%s</ul></div>
</div>
<div class="card" style="margin-top:16px"><h3>常驻合规面</h3><ul>%s</ul></div>
<footer>只读面：本页不含任何写路径，重渲染请显式执行 <code>python tools/first_yuan_path.py --write</code>。尺寸 %d B / %d B（自指记录）。</footer>
</body></html>
""" % (esc(d["generated_utc"]), esc(JSON_REL),
       "".join(rows), "" if d["verdict"] != "READY" else " ready",
       esc(d["verdict"]), esc(d["top_edge"]), blk["physical"], named,
       blk["decisions"], blk["code_open"], items, comp,
       d["sizes"]["html"], d["sizes"]["json"])


def build():
    """Iterate both artifacts to a fixed point: each embeds the OTHER size, so a
    single pass drifts whenever a byte count gains or loses a digit."""
    d = derive()
    html = text = ""
    for _ in range(30):
        html = render_html(d)
        text = json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        cur = {"html": len(html.encode("utf-8")), "json": len(text.encode("utf-8"))}
        if d["sizes"] == cur:
            return html, text, d
        d["sizes"] = cur
    html = render_html(d)
    text = json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return html, text, d


def _refresh_face():
    """AC-PWC8 (R3530): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second writer
    is kept here. BASE is passed explicitly, so a private world derives that
    world's face. Refusals are named, never raised: both halves are already on
    disk when this runs, so the caller's exit code stays its own.
    """
    try:
        os_src = os.path.join(BASE, "src", "os")
        if os_src not in sys.path:
            sys.path.insert(0, os_src)
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(BASE)
        return "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # a private world may carry no shared writer
        return "SKIPPED %s" % type(exc).__name__


def cmd_write():
    html, text, d = build()
    for rel, body in ((HTML_REL, html), (JSON_REL, text)):
        with io.open(_abs(rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    print("face export=" + _refresh_face())
    print("WROTE %s %dB %s %dB verdict=%s" % (
        HTML_REL, len(html.encode("utf-8")), JSON_REL, len(text.encode("utf-8")), d["verdict"]))
    return 0


def cmd_check():
    ok = True

    def say(cid, good, detail):
        nonlocal ok
        ok = ok and good
        print("%s %s %s" % ("PASS" if good else "FAIL", cid, detail))

    hp, jp = _abs(HTML_REL), _abs(JSON_REL)
    if not (os.path.exists(hp) and os.path.exists(jp)):
        print("FAIL AC-FYP1 artifact missing (%s / %s)" % (HTML_REL, JSON_REL))
        print("VERDICT FAIL fails=1")
        return 2
    h0, j0 = os.stat(hp), os.stat(jp)
    html = io.open(hp, encoding="utf-8").read()
    raw = io.open(jp, encoding="utf-8").read()
    doc = json.loads(raw)
    fresh = derive()

    have = [(r["id"], r["label"], r["source"]) for r in doc.get("carriers") or []]
    want = [(r["id"], r["label"], r["source"]) for r in fresh["carriers"]]
    say("AC-FYP1", have == want, "carriers=%d fresh=%d order_equal=%s" % (len(have), len(want), have == want))

    same = all(a["state"] == b["state"] and a["ok"] == b["ok"]
               for a, b in zip(doc.get("carriers") or [], fresh["carriers"]))
    say("AC-FYP2", same, "states=%s" % [r["state"] for r in fresh["carriers"]])

    h1, j1 = os.stat(hp), os.stat(jp)
    untouched = (h0.st_size, h0.st_mtime_ns) == (h1.st_size, h1.st_mtime_ns) and \
                (j0.st_size, j0.st_mtime_ns) == (j1.st_size, j1.st_mtime_ns)
    say("AC-FYP3", untouched, "--check left both artifacts byte- and mtime-identical")

    miss = [c for c in COMPLIANCE if c not in html]
    say("AC-FYP4", not miss, "compliance_missing=%d" % len(miss))

    external = [x for x in ("http://", "https://") if x in html]
    say("AC-FYP5", not external, "external_literals=%s" % (external or "none"))

    sizes = doc.get("sizes") or {}
    real = {"html": h1.st_size, "json": j1.st_size}
    say("AC-FYP6", sizes == real, "recorded=%s disk=%s" % (sizes, real))

    rule_ok = doc.get("verdict") == fresh["verdict"] and doc.get("top_edge") == fresh["top_edge"]
    say("AC-FYP7", rule_ok, "verdict=%s top_edge=%s" % (fresh["verdict"], fresh["top_edge"]))

    print("VERDICT %s fails=%d" % ("PASS" if ok else "FAIL", 0 if ok else 1))
    return 0 if ok else 2


def main(argv):
    ap = argparse.ArgumentParser(description="BigDomain first-yuan money path face")
    ap.add_argument("--write", action="store_true", help="render both artifacts")
    ap.add_argument("--check", action="store_true", help="verify without writing")
    a = ap.parse_args(argv)
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    print("\n".join("%s %s %s" % (r["id"], r["state"], "OK" if r["ok"] else "NOT-OK")
                    for r in derive()["carriers"]))
    print("verdict=%s" % derive()["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
