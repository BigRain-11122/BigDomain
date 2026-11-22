#!/usr/bin/env python3
"""Shared onward-route block: where a face sends the reader next.

Why this exists: at R3283 the buyer chain stopped on the page where money
appears, so buyer-trial grew a footer route. R3284 measured the rest of the
tree and found two more faces with out-degree zero, one of them the landing
page of the live-room funnel (journey-19.9). Each face writing its own hand-
typed link list is how a page silently turns into a dead end again, so the hop
order lives in ONE closure here and the numbers are measured at render time.

R3286: the ORDER was one closure but the SENTENCE was still five copies - the
probe measured 20 hops over 7 hrefs with four hrefs carrying two to four
versions of their own label (buyer-trial 4, merchant-onboard 4, start-here 3,
money-path-demo 2), so one destination was described in five voices and
`check` never compared labels at all. The text now lives in LABELS keyed by
href; a face declares only the order. The entry page also gains an
`index` walk, because index.html listed every face flat and said nothing
about which page a first-time reader should open first.

Measurement is not duplicated: control counts and byte sizes come from
buyer_trial.measure_hop, the same definition AC-BT7 grades.

Criteria AC-JNY9 (journey-19.9), AC-MPD7 (money-path-demo), AC-MO7
(merchant-onboard) and AC-LPM7 (lobby-protocol-map) are pre-registered in
src/os/backlog.md (R3284/R3285 PIN lines) before this file existed:
  (a) printed hop count equals the declared count
  (b) every hop exists on disk and is linked with its exact href
  (c) every hop's bytes/controls equal a fresh measurement (typed values red)
  (d) at least one hop carries a control, else "next step" is an empty promise
  (e) the "furthest you can walk" sentence equals a fresh derivation, verbatim

AC-RLB (pinned R3286 before this code) adds the label arms:
  (f) every declared href has an entry in LABELS, else the face is named red
  (g) the landed json label equals the closure label, verbatim
  (h) the page prints that closure label, verbatim

AC-IDX1 (pinned R3286 before this code) grades the entry page's first-visit
walk in tools/deliverable_index.py, using the same state()/render_block().
"""
import html
import os
import re

import buyer_trial

PREVIEW = buyer_trial.PREVIEW

# One row of the entry walk, read back as (row number, target href).
ROW_RE = re.compile(r'data-hop="(\d+)">\s*\d+\.\s*<a href="([^"]+)"')

# One label per destination. A face that wants different wording adds a hop to
# this dict, it never retypes the sentence - that is how five voices happened.
LABELS = {
    "start-here.html": "回到起点：这台机器今天能亲手做什么（只读汇总）",
    "buyer-trial.html": "自己点一遍：MOCK 下单与两本账配平（可操作）",
    "merchant-onboard.html": "要真收钱还缺什么：商户号 / 服务器 / 域名 / 备案（可填）",
    "money-path-demo.html": "这笔钱在账本里怎么走（可操作）",
    "journey-19.9.html": "这单买的是哪八步（只读判定表）",
    "membership-face.html": "这条权益落在哪：会员面（只读）",
    "lobby-session-trace.html": "同一套大厅协议在一次会话里怎么走（只读）",
}

# One closure of ORDER. Each hop is a local html file that exists on disk; the
# order is the order a reader would actually walk, action pages before reading
# pages. `index` is the first-visit walk printed on the entry page.
ROUTES = {
    "index": [
        "start-here.html",
        "buyer-trial.html",
        "merchant-onboard.html",
        "money-path-demo.html",
    ],
    "journey-19.9": [
        "money-path-demo.html",
        "merchant-onboard.html",
        "buyer-trial.html",
        "start-here.html",
    ],
    "money-path-demo": [
        "merchant-onboard.html",
        "buyer-trial.html",
        "journey-19.9.html",
        "start-here.html",
    ],
    "buyer-trial": [
        "membership-face.html",
        "merchant-onboard.html",
        "money-path-demo.html",
        "start-here.html",
    ],
    "lobby-protocol-map": [
        "lobby-session-trace.html",
        "merchant-onboard.html",
        "buyer-trial.html",
        "start-here.html",
    ],
    "merchant-onboard": [
        "buyer-trial.html",
        "money-path-demo.html",
        "journey-19.9.html",
        "start-here.html",
    ],
}

# The entry page is not a face with a footer: its walk is the first thing a
# reader sees, so the block carries its own attribute name and heading.
FIRST_VISIT = "index"


def hop_state(href, preview=None):
    path = os.path.join(preview or PREVIEW, href)
    size, controls = buyer_trial.measure_hop(path)
    return {
        "href": href,
        "label": LABELS.get(href, ""),
        "labelled": href in LABELS,
        "bytes": size,
        "controls": controls,
        "readonly": controls == 0,
        "exists": size > 0,
    }


def state(face, preview=None):
    hops = [hop_state(href, preview) for href in ROUTES.get(face, [])]
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
    first = face == FIRST_VISIT
    attr = "data-first-visit-hops" if first else "data-onward-hops"
    if first:
        heading = ("第一次来先走这四步（%d 跳，尺寸与控件数在渲染时从盘上现读）" % doc["count"])
    else:
        heading = "下一步 · 本机还能走到哪（%d 跳，尺寸与控件数在渲染时从盘上现读）" % doc["count"]
    parts = [
        '<div class="route" %s="%d" style="border:1px solid rgba(128,128,128,.4);'
        "border-radius:10px;padding:12px 14px;margin:18px 0;font-size:13px;line-height:1.6\">"
        % (attr, doc["count"]),
        '<h2 style="font-size:14px;margin:0 0 8px">%s</h2>' % heading,
        '<ol style="padding-left:18px;margin:0">',
    ]
    for i, h in enumerate(doc["hops"]):
        kind = "只读" if h["readonly"] else "可操作"
        parts.append(
            '<li data-hop="%d">%d. <a href="%s">%s</a> '
            '<span data-hop-bytes="%d" data-hop-controls="%d" style="opacity:.7">'
            "&middot; %s · %d 个控件 · %dB</span> — %s</li>"
            % (
                i + 1,
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
    problems.extend(label_problems(face, page_text, kept, fresh))
    return problems


def label_problems(face, page_text, kept, fresh):
    """AC-RLB (R3286): the sentence is one closure, and no face may paraphrase it."""
    problems = []
    for now, was in zip(fresh["hops"], kept):
        name = now["href"]
        if not now["labelled"]:
            problems.append("%s: hop %s has no label in the closure" % (face, name))
            continue
        if was.get("label") != now["label"]:
            problems.append(
                "%s: hop label drifted %s json=%r closure=%r"
                % (face, name, was.get("label"), now["label"])
            )
        elif html.escape(now["label"]) not in page_text:
            problems.append("%s: page does not print the closure label of %s" % (face, name))
    return problems


def first_visit_problems(page_text):
    """AC-IDX1 (R3286): the entry page's walk, graded from the same closure.

    The arms are in tools/deliverable_index.py; this returns the problems so
    the block and its criterion read ONE derivation.

    The order arm grades the ROW'S HREF, not the row number: a first cut only
    checked that the data-hop positions ascended, and the negative control
    swapped two rows and renumbered them, which left every number ascending and
    the walk in the wrong order (measured, then fixed here).
    """
    fresh = state(FIRST_VISIT)
    problems = []
    attr = 'data-first-visit-hops="%d"' % fresh["count"]
    if attr not in page_text:
        problems.append("index: page does not print the first-visit hop count %d" % fresh["count"])
    for hop in fresh["hops"]:
        name = hop["href"]
        if not hop["labelled"]:
            problems.append("index: hop %s has no label in the closure" % name)
        if not hop["exists"]:
            problems.append("index: hop file missing %s" % name)
        if ('href="%s"' % name) not in page_text:
            problems.append("index: hop not linked %s" % name)
        elif hop["labelled"] and html.escape(hop["label"]) not in page_text:
            problems.append("index: page does not print the closure label of %s" % name)
    rows = [(int(n), href) for n, href in ROW_RE.findall(page_text)]
    declared = [(i, hop["href"]) for i, hop in enumerate(fresh["hops"], 1)]
    if rows != declared:
        problems.append("index: walk order printed=%s declared=%s" % (rows, declared))
    if not any(h["controls"] > 0 for h in fresh["hops"]):
        problems.append("index: every hop is read-only, so 'start here' promises nothing")
    return problems
