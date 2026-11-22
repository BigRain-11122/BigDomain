#!/usr/bin/env python3
"""Shared onward-route block: where a face sends the reader next.

Why this exists: at R3283 the buyer chain stopped on the page where money
appears, so buyer-trial grew a footer route. R3284 measured the rest of the
tree and found two more faces with out-degree zero, one of them the landing
page of the live-room funnel (journey-19.9). Each face writing its own hand-
typed link list is how a page silently turns into a dead end again, so the hop
order lives in ONE closure here and the numbers are measured at render time.

Measurement is not duplicated: control counts and byte sizes come from
buyer_trial.measure_hop, the same definition AC-BT7 grades.

Criteria AC-JNY9 (journey-19.9) and AC-MPD7 (money-path-demo) are pre-
registered in src/os/backlog.md (R3284 PIN line) before this file existed:
  (a) printed hop count equals the declared count
  (b) every hop exists on disk and is linked with its exact href
  (c) every hop's bytes/controls equal a fresh measurement (typed values red)
  (d) at least one hop carries a control, else "next step" is an empty promise
  (e) the "furthest you can walk" sentence equals a fresh derivation, verbatim
"""
import html
import os

import buyer_trial

PREVIEW = buyer_trial.PREVIEW

# One closure. Each hop is a local html file that exists on disk; the order is
# the order a reader would actually walk, action pages before reading pages.
ROUTES = {
    "journey-19.9": [
        ("money-path-demo.html", "这单的钱在账本里怎么走（可操作）"),
        ("merchant-onboard.html", "要真收钱还缺什么：商户号 / 服务器 / 域名 / 备案（可填）"),
        ("buyer-trial.html", "自己点一遍：选商品、MOCK 付款、看两本账配平（可操作）"),
        ("start-here.html", "回到起点：这台机器今天能亲手做什么（只读汇总）"),
    ],
    "money-path-demo": [
        ("merchant-onboard.html", "真收钱还缺什么：商户号 / 服务器 / 域名 / 备案（可填）"),
        ("buyer-trial.html", "自己点一遍 MOCK 下单与入账（可操作）"),
        ("journey-19.9.html", "这单买的是哪八步（只读判定表）"),
        ("start-here.html", "回到起点：本机能亲手做什么（只读汇总）"),
    ],
    "buyer-trial": [
        ("membership-face.html", "这条权益落在哪：会员面（只读）"),
        ("merchant-onboard.html", "要真收钱还缺什么（可填）"),
        ("money-path-demo.html", "这笔钱在账本里怎么走（可操作）"),
        ("start-here.html", "回到起点：本机今天能亲手做什么（只读）"),
    ],
}


def hop_state(href, label, preview=None):
    path = os.path.join(preview or PREVIEW, href)
    size, controls = buyer_trial.measure_hop(path)
    return {
        "href": href,
        "label": label,
        "bytes": size,
        "controls": controls,
        "readonly": controls == 0,
        "exists": size > 0,
    }


def state(face, preview=None):
    hops = [hop_state(href, label, preview) for href, label in ROUTES.get(face, [])]
    actionable = [i for i, h in enumerate(hops) if not h["readonly"]]
    last = actionable[-1] + 1 if actionable else 0
    if last:
        sentence = (
            "本机不接服务器时，这条路最远走到第 %d 跳（%s，%d 个控件）；"
            "再往后只有读数，没有可操作控件。" % (last, hops[last - 1]["href"], hops[last - 1]["controls"])
        )
    else:
        sentence = "这条路本机一页可操作的都没有：下面全部是只读读数。"
    return {
        "face": face,
        "hops": hops,
        "count": len(hops),
        "last_actionable": last,
        "last_sentence": sentence,
    }


def render_block(face, preview=None):
    doc = state(face, preview)
    parts = [
        '<div class="route" data-onward-hops="%d" style="border:1px solid rgba(128,128,128,.4);'
        "border-radius:10px;padding:12px 14px;margin:18px 0;font-size:13px;line-height:1.6\">"
        % doc["count"],
        '<h2 style="font-size:14px;margin:0 0 8px">下一步 · 本机还能走到哪（%d 跳，尺寸与控件数在渲染时从盘上现读）</h2>'
        % doc["count"],
        '<ol style="padding-left:18px;margin:0">',
    ]
    for i, h in enumerate(doc["hops"]):
        kind = "只读" if h["readonly"] else "可操作"
        parts.append(
            '<li>%d. <a href="%s">%s</a> '
            '<span data-hop-bytes="%d" data-hop-controls="%d" style="opacity:.7">'
            "&middot; %s · %d 个控件 · %dB</span> — %s</li>"
            % (
                i + 1,
                html.escape(h["href"], quote=True),
                html.escape(h["href"]),
                h["bytes"],
                h["controls"],
                kind,
                h["controls"],
                h["bytes"],
                html.escape(h["label"]),
            )
        )
    parts.append("</ol>")
    parts.append(
        '<p class="small" data-onward-last="%s" style="margin:8px 0 0;opacity:.75">%s</p>'
        % (html.escape(doc["last_sentence"], quote=True), html.escape(doc["last_sentence"]))
    )
    parts.append("</div>")
    return "\n".join(parts)


def check(face, page_text, landed, preview=None):
    """Return problem strings; empty means the route is intact."""
    fresh = state(face, preview)
    problems = []
    if not landed:
        return ["%s: route block absent from json" % face]
    if landed.get("count") != fresh["count"]:
        problems.append("%s: hop count json=%s fresh=%d" % (face, landed.get("count"), fresh["count"]))
    if ('data-onward-hops="%d"' % fresh["count"]) not in page_text:
        problems.append("%s: page does not print hop count %d" % (face, fresh["count"]))
    kept = landed.get("hops") or []
    if len(kept) != len(fresh["hops"]):
        problems.append("%s: json hops=%d fresh=%d" % (face, len(kept), len(fresh["hops"])))
    for now, was in zip(fresh["hops"], kept):
        name = now["href"]
        if not now["exists"]:
            problems.append("%s: hop file missing %s" % (face, name))
        if ('href="%s"' % name) not in page_text:
            problems.append("%s: hop not linked %s" % (face, name))
        if was.get("bytes") != now["bytes"] or was.get("controls") != now["controls"]:
            problems.append(
                "%s: hop measure drifted %s json=%s/%s disk=%s/%s"
                % (face, name, was.get("bytes"), was.get("controls"), now["bytes"], now["controls"])
            )
    if not any(h["controls"] > 0 for h in fresh["hops"]):
        problems.append("%s: every hop is read-only, so 'next step' promises nothing" % face)
    if landed.get("last_sentence") != fresh["last_sentence"]:
        problems.append("%s: last-actionable sentence stale" % face)
    if ('data-onward-last="%s"' % html.escape(fresh["last_sentence"], quote=True)) not in page_text:
        problems.append("%s: page does not carry the fresh last-actionable sentence" % face)
    return problems
