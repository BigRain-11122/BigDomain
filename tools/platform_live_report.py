#!/usr/bin/env python3
"""P-47 platform face: every sandbox door proved live over a real socket, on one page.

The five business faces each have their own rendered page, and
src/sandbox/start_all.py already brings the whole sandbox up in one command -
but that command only prints JSON to a console, and nothing in the repository
records what it measured. A reader therefore has two choices: trust the
launcher's word, or run it himself. This driver closes that gap: it IMPORTS the
shipped launcher (plan/build_commands/start/verify/teardown) instead of
re-implementing it, boots every face the launcher publishes, speaks real HTTP to
every door, tears the whole thing down again, and only then renders one page
with the measured numbers.

Pre-registered criteria (pinned before any code, per the honesty law):
  AC-PLVR1  the shipped verifier reports ready with exactly the faces the
           launcher publishes, zero errors, and every port came from plan() as
           one distinct OS-assigned value per plan key.
  AC-PLVR2  every face URL answers a real HTTP GET with status 200 and a
           non-empty body; status, bytes and content-type recorded.
  AC-PLVR3  each answering door serves its own page: every body carries a
           non-empty <title>, and no two bodies are byte-identical.
  AC-PLVR4  the deep reads hold: GET city/snapshot answers 200 as parsable JSON
           carrying as_of, and the hub's own probe map reads every face live.
  AC-PLVR5  every face URL is loopback and its port equals the planned port for
           that face under the shipped FACE_PORT_KEY mapping - no external host.
  AC-PLVR6  teardown is clean: after it, every child process is kernel GONE and
           every planned port refuses a connection, so no orphan keeps a
           sandbox port.
  AC-PLVR7  zero external network: every host-bearing URL literal in this driver
           is loopback, and every shipped entry file is byte-identical before
           and after the run.
  AC-PLVR8  the report is self-consistent and carries the standing law: the
           embedded sizes equal the bytes on disk, the page prints one command
           a reader can paste to reproduce it, and the AIGC mark, the
           non-advisory notice and the msgSecCheck pre-gate are rendered as
           permanent faces while mock=true and chargeable=false are stated.
  AC-PLVR9  no hand-typed count survives in the criteria prose or the page: a
           count is either a digit this run measured or it is absent, so growth
           of the shipped launcher cannot leave the label undercounting. (Added
           at R3070 after the page read "six doors" above a row naming eight.)

R3071 - why this family is AC-PLVR, not AC-PLR. Measured before the change:
this module carried AC-PLR1..AC-PLR9 while src/os/patterns_label_readability.py
has carried AC-PLR1..AC-PLR6 since R2494 (it is the readability gate's family,
registry row os-patterns-label-readability). Two unrelated criteria families
shared one prefix, so a red line naming a bare AC-PLR id did not say WHICH
criterion had failed - the [GATES] face prints ids, not modules. The rename cost was
counted first: every occurrence lived in this one file, and outside the two
owners only historical seed rows and docs/copyright carried the token, so no
consumer moved. Three refusals, stated instead of implied: (1) the readability
family keeps its numbers - it is the older family and its seed row lives in
state/queue/tech.md, so renaming it would rewrite history to fix a newcomer;
(2) adding a comment while keeping the id was refused - the ambiguity lives in
the ID, not in the comment; (3) the guard suite this round ships is NOT named
AC-PLR*B, because "AC-PLRB1" still contains "AC-PLR" and a substring census
would keep reporting the collision. The battery row is the other half of the
same defect: this face had ZERO row in src/sandbox/reconcile_all.py, so its
criteria were graded only by the round-opening gate sweep.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SANDBOX = os.path.join(ROOT, "src", "sandbox")
PREVIEW = os.path.join(ROOT, "preview")
HTML_PATH = os.path.join(PREVIEW, "platform-live-report.html")
JSON_PATH = os.path.join(PREVIEW, "platform-live-report.json")

# The shipped launcher owns the entry vectors; nothing here restarts them.
SHIPPED = [
    os.path.join(SANDBOX, "start_all.py"),
    os.path.join(SANDBOX, "lobby", "server.py"),
    os.path.join(SANDBOX, "lobby", "checkout_demo.py"),
    os.path.join(SANDBOX, "ledger", "ledger_page.py"),
    os.path.join(SANDBOX, "ugc", "ugc_page.py"),
    os.path.join(SANDBOX, "lobby", "config.json"),
    os.path.join(SANDBOX, "pay", "config.json"),
]

REPRODUCE = "python tools/platform_live_report.py"
SERVE = "python src/sandbox/start_all.py"

CRITERIA = [
    ("AC-PLVR1", "shipped verifier ready with every shipped face, zero errors, one distinct port per plan key"),
    ("AC-PLVR2", "every shipped face URL answers a real HTTP 200 with a non-empty body"),
    ("AC-PLVR3", "each door serves its own page: non-empty title, no two bodies identical"),
    ("AC-PLVR4", "city/snapshot 200 parsable JSON with as_of; hub probe map reads every face live"),
    ("AC-PLVR5", "every face URL loopback and its port equal to the planned port for that face"),
    ("AC-PLVR6", "after teardown every child is kernel GONE and every planned port refuses"),
    ("AC-PLVR7", "no external host literal; every shipped entry file byte-identical before and after"),
    ("AC-PLVR8", "sizes self-consistent with the landed pair, one paste-ready command, AIGC/non-advisory/msgSecCheck faces, mock stated"),
    ("AC-PLVR9", "no typed count in the criteria prose or the page: every count is a digit measured this run, or absent"),
]

COMPLIANCE = [
    ("AIGC 生成标识面", "本沙箱一切生成内容在呈现面标注 AI 生成标识；服务端权威字段 ai_generated 不接受客户端伪造。"),
    ("非投顾常驻提示", "本平台不构成投资建议；风险提示随大厅连接第二帧常驻呈现，不折叠、不可关闭。"),
    ("msgSecCheck 前置闸", "内容安全未接线前大厅禁开门；真实 msgSecCheck 需小程序资质（CEO 物理件），现役为 shipped 词表 stub。"),
]


def _sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _title(body):
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
    return (match.group(1).strip() if match else "")


def _get(url, timeout=10.0):
    request = urllib.request.Request(url, headers={"User-Agent": "BigDomain-live/**"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as res:
            raw = res.read()
            return {
                "url": url,
                "status": int(res.status),
                "bytes": len(raw),
                "ctype": (res.headers.get("Content-Type") or "").split(";")[0].strip(),
                "body": raw,
            }
    except urllib.error.HTTPError as exc:  # a 4xx/5xx is still a measurement
        raw = exc.read()
        return {
            "url": url,
            "status": int(exc.code),
            "bytes": len(raw),
            "ctype": (exc.headers.get("Content-Type") or "").split(";")[0].strip(),
            "body": raw,
        }
    except (OSError, urllib.error.URLError) as exc:
        return {"url": url, "status": 0, "bytes": 0, "ctype": "", "body": b"", "error": str(exc)}


def _loopback_hosts(text):
    """Host-bearing literals only: a bare scheme inside prose is not a target."""
    found = sorted(set(re.findall(r"(?:wss?|https?)://[A-Za-z0-9._-]+", text)))
    return found, [tok for tok in found if "127.0.0.1" not in tok and "localhost" not in tok]


# R3070: this face was authored while the shipped launcher held six faces, and its
# title, its criteria prose and its closing line counted them by hand. The launcher
# then grew - eight faces, six children, ten planned ports - and every typed count
# stayed put, so the page published "six doors" directly above a measured row naming
# eight. A typed count is a claim nothing measures; tools/face_sweep.py already lives
# by this law (AC-FSW18 E_FSW_SCOPE_TYPED derives its sentence from the row table
# after R2901 deleted a hand-moved count literal), and this face is late to it. The
# criterion therefore refuses the word instead of grading it, so growth of the
# shipped launcher cannot make the label wrong again. Digits printed from this run's
# measurement are not typed counts.
TYPED_COUNTS_EN = ("three", "four", "five", "six", "seven", "eight", "nine", "ten")
TYPED_COUNTS_CJK = u"\u516d\u4e03\u516b\u4e5d\u5341"  # 6 7 8 9 10
_CNT_EN_RE = re.compile(r"\b(" + "|".join(TYPED_COUNTS_EN) + r")\b", re.I)
_CNT_CJK_RE = re.compile(u"[" + TYPED_COUNTS_CJK + u"](?:\u95e8|\u4e2a|\u6761|\u9879)")


def ac_plr9(doc, criteria):
    """Refuse a hand-typed count wherever this face publishes one."""
    hits = []
    for cid, intent in criteria:
        found = _CNT_EN_RE.findall(intent)
        if found:
            hits.append("%s:%s" % (cid, ",".join(found)))
    found = _CNT_EN_RE.findall(doc)
    if found:
        hits.append("page:" + ",".join(sorted(set(w.lower() for w in found))))
    match = _CNT_CJK_RE.search(doc)
    if match:
        hits.append("page:" + match.group(0))
    return {
        "pass": not hits,
        "measured": "typed_counts=%s" % (",".join(hits) if hits else "none"),
    }


def measure():
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import start_all  # noqa: PLC0415 - the shipped launcher, not a copy

    evidence = {}
    facts = {"shipped_files": [os.path.relpath(p, ROOT) for p in SHIPPED]}
    before = {os.path.relpath(p, ROOT): _sha(p) for p in SHIPPED}
    facts["shipped_before"] = before

    host = "127.0.0.1"
    ports = start_all.plan(host)
    children = start_all.start(start_all.build_commands(host, ports))
    try:
        ready, hub_url, faces, live, errors = start_all.verify(host, ports, 45.0)
        facts["host"] = host
        facts["hub_url"] = hub_url
        facts["ports"] = dict(ports)
        facts["faces"] = dict(faces)
        facts["live"] = dict(live)
        facts["errors"] = list(errors)

        # AC-PLVR1
        distinct = len(set(ports.values())) == len(start_all.PLAN_KEYS)
        evidence["AC-PLVR1"] = {
            "pass": bool(ready) and sorted(faces) == sorted(start_all.FACE_KEYS) and not errors and distinct,
            "measured": "ready=%s faces=%s errors=%s ports_keys=%d distinct=%s"
            % (ready, sorted(faces), errors or "none", len(ports), distinct),
        }

        # AC-PLVR2 / AC-PLVR3
        pages = {}
        for key in start_all.FACE_KEYS:
            url = faces.get(key) or ""
            got = _get(url) if url else {"status": 0, "bytes": 0, "ctype": "", "body": b""}
            body = got.pop("body")
            got["title"] = _title(body.decode("utf-8", "replace"))
            got["sha"] = hashlib.sha256(body).hexdigest()[:16]
            pages[key] = got
        facts["pages"] = pages
        ok2 = all(p["status"] == 200 and p["bytes"] > 0 for p in pages.values()) and len(pages) == len(start_all.FACE_KEYS)
        evidence["AC-PLVR2"] = {
            "pass": ok2,
            "measured": " ".join("%s=%d/%dB" % (k, pages[k]["status"], pages[k]["bytes"]) for k in start_all.FACE_KEYS),
        }
        titles = [pages[k]["title"] for k in start_all.FACE_KEYS]
        bodies = {pages[k]["sha"] for k in start_all.FACE_KEYS}
        evidence["AC-PLVR3"] = {
            "pass": all(titles) and len(bodies) == len(start_all.FACE_KEYS),
            "measured": "titles_nonempty=%d/%d distinct_bodies=%d/%d"
            % (len([t for t in titles if t]), len(titles), len(bodies), len(start_all.FACE_KEYS)),
        }

        # AC-PLVR4
        snap = _get(faces.get("city", "") + "snapshot") if faces.get("city") else {"status": 0, "body": b""}
        snap_body = snap.get("body", b"")
        snap_json = {}
        try:
            snap_json = json.loads(snap_body.decode("utf-8"))
        except ValueError:
            snap_json = {}
        hub_probe = _get(hub_url + "api/faces?probe=1")
        hub_payload = {}
        try:
            hub_payload = json.loads(hub_probe.get("body", b"").decode("utf-8"))
        except ValueError:
            hub_payload = {}
        hub_live = {k: bool((hub_payload.get("live") or {}).get(k)) for k in start_all.FACE_KEYS}
        facts["city_snapshot"] = {
            "status": snap.get("status", 0),
            "bytes": snap.get("bytes", 0),
            "keys": sorted(snap_json)[:12],
            "as_of": snap_json.get("as_of"),
        }
        facts["hub_live"] = hub_live
        evidence["AC-PLVR4"] = {
            "pass": snap.get("status") == 200 and bool(snap_json.get("as_of")) is not None
            and "as_of" in snap_json and all(hub_live.values()) and hub_live == dict(live),
            "measured": "snapshot=%d keys=%d as_of=%s hub_live_all=%s equals_verifier=%s"
            % (snap.get("status", 0), len(snap_json), snap_json.get("as_of"),
               all(hub_live.values()), hub_live == dict(live)),
        }

        # AC-PLVR5
        bad_host, bad_port = [], []
        for key in start_all.FACE_KEYS:
            url = faces.get(key) or ""
            host_part = url.split("//", 1)[1].split("/", 1)[0] if "//" in url else ""
            name, _, port_text = host_part.partition(":")
            if "127.0.0.1" not in name and "localhost" not in name:
                bad_host.append(key)
            want = ports[start_all.FACE_PORT_KEY[key]]
            if str(want) != port_text:
                bad_port.append("%s:%s!=%d" % (key, port_text, want))
        evidence["AC-PLVR5"] = {
            "pass": not bad_host and not bad_port,
            "measured": "external_hosts=%s port_mismatch=%s" % (bad_host or "none", bad_port or "none"),
        }

        # AC-PLVR7 source face (measured before teardown, it is file-only)
        here = open(os.path.abspath(__file__), encoding="utf-8").read()
        found, external = _loopback_hosts(here)
        facts["url_literals"] = found
        facts["external_literals"] = external
    finally:
        start_all.teardown(children)

    # AC-PLVR6 measured strictly after teardown
    gone = {name: (proc.poll() is not None) for name, proc in children}
    refusing = {}
    for key in start_all.PLAN_KEYS:
        refusing[key] = not start_all.can_connect(host, ports[key])
    facts["children_gone"] = gone
    facts["ports_refusing"] = refusing
    evidence["AC-PLVR6"] = {
        "pass": all(gone.values()) and all(refusing.values()),
        "measured": "children_gone=%d/%d ports_refusing=%d/%d"
        % (len([v for v in gone.values() if v]), len(gone), len([v for v in refusing.values() if v]), len(refusing)),
    }

    after = {os.path.relpath(p, ROOT): _sha(p) for p in SHIPPED}
    facts["shipped_after"] = after
    evidence["AC-PLVR7"] = {
        "pass": not external and before == after,
        "measured": "external_literals=%s shipped_identical=%s"
        % (external or "none", before == after),
    }
    return evidence, facts


def _fingerprint(evidence, facts):
    payload = json.dumps(
        {
            "evidence": {k: v["pass"] for k, v in sorted(evidence.items())},
            "face_keys": sorted(facts["faces"]),
            "titles": {k: facts["pages"][k]["title"] for k in sorted(facts["pages"])},
            "body_sha": {k: facts["pages"][k]["sha"] for k in sorted(facts["pages"])},
            "hub_live": facts["hub_live"],
            # the ephemeral ports change every run by design, so the fingerprint
            # pins what the run proved and never the port numbers
            "port_count": len(facts["ports"]),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def render(evidence, facts):
    passed = sum(1 for v in evidence.values() if v["pass"])
    total = len(CRITERIA)
    # R3070: two criteria can only be graded AFTER this page exists (the byte-pair
    # check needs the written bytes, the no-typed-count check needs the document).
    # The page used to print them as "bad" rows reading "-" and then announce
    # "7/8 PASS" beside a JSON verdict of PASS 8/8 - the face contradicted its own
    # evidence on the one line a reader trusts. A criterion this page cannot grade
    # now says so, and the score counts only what this page graded.
    def _row_class(cid):
        if cid not in evidence:
            return "later"
        return "ok" if evidence[cid]["pass"] else "bad"

    rows = "\n".join(
        '<tr class="%s"><td>%s</td><td>%s</td><td>%s</td></tr>'
        % (_row_class(cid), cid, intent,
           (str(evidence[cid]["measured"]).replace("<", "&lt;") if cid in evidence
            else "graded by --check against the landed pair"))
        for cid, intent in CRITERIA
    )
    later = len([cid for cid, _ in CRITERIA if cid not in evidence])
    score = "%d/%d PASS" % (passed, total - later)
    if later:
        later_note = (
            "%d \u6761\u53ea\u80fd\u5728\u672c\u9875\u5199\u6210\u4e4b\u540e\u6838\u5bf9"
            "\uff08\u5b57\u8282\u5bf9\u3001\u4e0d\u6253\u5b57\u8ba1\u6570\uff09\uff0c\u7531 "
            "<code>--check</code> \u5bf9\u843d\u5730\u4ef6\u9010\u6761\u9a8c\u8bc1\uff1a%s\u3002"
            % (later, ", ".join(cid for cid, _ in CRITERIA if cid not in evidence))
        )
    else:
        later_note = "\u672c\u9875\u4e0a\u7684\u5224\u636e\u5747\u5df2\u5728\u672c\u9875\u5185\u5b8c\u6210\u6838\u5bf9\u3002"


    door_rows = "\n".join(
        '<tr class="%s"><td>%s</td><td><code>%s</code></td><td>%d</td><td>%d B</td>'
        "<td>%s</td><td>%s</td></tr>"
        % ("ok" if facts["pages"][k]["status"] == 200 else "bad", k,
           facts["faces"].get(k, ""), facts["pages"][k]["status"],
           facts["pages"][k]["bytes"], facts["pages"][k]["ctype"] or "-",
           facts["pages"][k]["title"].replace("<", "&lt;") or "-")
        for k in sorted(facts["pages"])
    )
    port_rows = "\n".join(
        "<tr><td>%s</td><td>%d</td><td>%s</td></tr>"
        % (key, facts["ports"][key], "已拆台" if facts["ports_refusing"][key] else "仍在听")
        for key in sorted(facts["ports"])
    )
    compliance = "\n".join(
        '<li><b>%s</b> — %s</li>' % (name, text.replace("<", "&lt;"))
        for name, text in COMPLIANCE
    )
    snap = facts["city_snapshot"]
    doc = """<!DOCTYPE html>
<meta charset="utf-8">
<title>BigDomain 沙箱 · 全部门实测在线（一指令拉起）</title>
<style>
body{{font:15px/1.65 -apple-system,"Segoe UI",sans-serif;margin:0;background:#0f1115;color:#e8eaed}}
main{{max-width:1060px;margin:0 auto;padding:32px 24px 64px}}
h1{{font-size:24px;margin:0 0 6px}}
.sub{{color:#9aa0a6;margin:0 0 24px}}
.card{{background:#171a21;border:1px solid #262b36;border-radius:10px;padding:16px 18px;margin:0 0 16px}}
.card h2{{font-size:16px;margin:0 0 10px;color:#cfd4dc}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td,th{{text-align:left;padding:8px 6px;border-bottom:1px solid #262b36;vertical-align:top}}
tr.ok td:first-child{{color:#7ee787}} tr.bad td:first-child{{color:#ff7b72}}
tr.later td:first-child{{color:#d29922}}
pre{{background:#0b0d11;border:1px solid #262b36;border-radius:8px;padding:12px;overflow:auto;font-size:12.5px;color:#c9d1d9}}
.score{{font-size:28px;color:#7ee787}}
code{{color:#79c0ff}}
.note{{color:#9aa0a6;font-size:13px}}
</style>
<main>
<h1>BigDomain 沙箱 · 全部门实测在线</h1>
<p class="sub">本轮把「一个指令拉起全平台」变成一页可看的实物：导入 shipped 启动器 <code>src/sandbox/start_all.py</code>（不是复刻），
起全部面、逐面真实 HTTP 取回、再整体拆台，页面上的每个数字都是这一轮量出来的。</p>
<div class="card"><h2>判据结果</h2>
<p class="score">{score}</p>
<p class="note">{later_note}</p>
<table><tr><th>判据</th><th>意图（预注册）</th><th>实测</th></tr>
{rows}
</table></div>
<div class="card"><h2>各道门（真实 HTTP 取回）</h2>
<table><tr><th>门</th><th>地址</th><th>HTTP</th><th>字节</th><th>Content-Type</th><th>页面 title</th></tr>
{door_rows}
</table>
<p class="note">Hub 门：<code>{hub}</code>（hub 自报 live：{hub_live}）</p></div>
<div class="card"><h2>深读一例：city /city/snapshot</h2>
<p>HTTP {snap_status} · {snap_bytes} B · 顶层键 {snap_keys} 个 · <code>as_of</code> = <code>{snap_asof}</code></p></div>
<div class="card"><h2>计划端口与拆台后状态</h2>
<table><tr><th>端口键</th><th>端口</th><th>拆台后</th></tr>
{port_rows}
</table>
<p class="note">端口由操作系统临时分配（<code>plan()</code>），所以这里不承诺固定端口，只承诺「起得来、测得到、拆得净」。</p></div>
<div class="card"><h2>你自己跑（复制即可）</h2>
<pre>{reproduce}</pre>
<pre>{serve}</pre>
<p class="note">第一条点亮本页全部数字并重渲染；第二条把沙箱留着你手里，末尾会打印可直接打开的 hub 地址。</p></div>
<div class="card"><h2>合规常驻面（生死线，随件常驻）</h2>
<ul>{compliance}</ul>
<p class="note">本件 mock=true、chargeable=false：沙箱入城为模拟凭证，无任何真实扣费；19.9 真实收款要等 CEO 物理件（微信商户号）。</p></div>
<div class="card"><h2>边界（诚实披露）</h2>
<ul>
<li>本页证明的是「各门在真实套接字上起得来、答得出、拆得净」，不是上线许可。</li>
<li>生产面 wss/TLS/域名/ICP/1000 并发为 AC-P1..P5，预注册不预执行。</li>
<li>内容安全现役为 shipped 词表 stub；真实 msgSecCheck 未接线，按规格大厅禁开门。</li>
<li>沙箱数据为演示库，非真实用户数据；页面 title 取自各门真实返回，未手写。</li>
</ul></div>
</main>
""".format(
        passed=passed, total=total, rows=rows, door_rows=door_rows,
        score=score, later_note=later_note,
        hub=facts["hub_url"],
        hub_live=", ".join("%s=%s" % (k, v) for k, v in sorted(facts["hub_live"].items())),
        snap_status=snap["status"], snap_bytes=snap["bytes"],
        snap_keys=len(snap["keys"]), snap_asof=snap.get("as_of"),
        port_rows=port_rows, reproduce=REPRODUCE, serve=SERVE, compliance=compliance,
    )
    data = {
        "artifact": "platform-live-report",
        "face": "P-47 platform: every sandbox door proved live over real sockets",
        "verdict": "PASS" if passed == len(evidence) == total else "FAIL",
        "passed": passed,
        "total": total,
        "criteria": [
            {"id": cid, "intent": intent,
             "pass": bool(evidence.get(cid, {}).get("pass")),
             "measured": str(evidence.get(cid, {}).get("measured", "-"))}
            for cid, intent in CRITERIA
        ],
        "faces": facts["faces"],
        "pages": {k: {kk: vv for kk, vv in facts["pages"][k].items() if kk != "body"}
                  for k in facts["pages"]},
        "ports": facts["ports"],
        "ports_refusing_after_teardown": facts["ports_refusing"],
        "children_gone": facts["children_gone"],
        "city_snapshot": facts["city_snapshot"],
        "hub_live": facts["hub_live"],
        "shipped_sha256": {k: v[:16] for k, v in facts["shipped_before"].items()},
        "fingerprint": _fingerprint(evidence, facts),
        "reproduce": [REPRODUCE, SERVE],
        "compliance_faces": [name for name, _ in COMPLIANCE],
        "mock": True,
        "chargeable": False,
        "disclosures": [
            "ports are OS-assigned on every run, so the fingerprint pins what was proved and never the ports",
            "sandbox entrance is a mock; the real 19.9 receipt needs the CEO merchant id",
            "content gate is the shipped wordlist stub; msgSecCheck needs the mini-program credentials",
            "production criteria AC-P1..P5 are pre-registered and not executed",
        ],
    }
    return doc, data


def ac_plr8(doc, html_bytes, json_bytes):
    """The report face measured on the rendered document, not on intent.

    At the size fixed point the numbers embedded here equal the bytes on disk,
    so 'sizes_consistent' is a true statement about the landed pair rather than
    a promise; the markers prove a template edit cannot silently drop the
    standing compliance faces or the paste-ready commands.
    """
    faces = [name for name, _ in COMPLIANCE if name in doc]
    has_repro = REPRODUCE in doc and SERVE in doc
    mock_stated = "mock=true" in doc and "chargeable=false" in doc
    sane = html_bytes > 0 and json_bytes > 0
    return {
        "pass": len(faces) == len(COMPLIANCE) and has_repro and mock_stated and sane,
        "measured": "compliance_faces=%d/%d commands=%d mock_stated=%s sizes=(%dB,%dB)"
        % (len(faces), len(COMPLIANCE), 2 if has_repro else 0, mock_stated,
           html_bytes, json_bytes),
    }


def _sizes():
    return {
        "html": os.path.getsize(HTML_PATH) if os.path.exists(HTML_PATH) else 0,
        "json": os.path.getsize(JSON_PATH) if os.path.exists(JSON_PATH) else 0,
    }


def _write(text, path):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return os.path.getsize(path)


def _landing_is_default(html_path, json_path):
    """True only when both halves land under THIS root's own preview/.

    The wanted folder is computed from ROOT, not from any rebindable output
    constant, so a world that repoints its outputs cannot pose as the root.
    """
    want = os.path.realpath(os.path.join(ROOT, "preview"))
    for path in (html_path, json_path):
        if os.path.dirname(os.path.realpath(path)) != want:
            return False
    return True


def _refresh_face(html_path, json_path):
    """AC-PWC24 (R3546): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: both halves are
    already on disk when this runs, so the caller's exit code stays its own.
    """
    if not _landing_is_default(html_path, json_path):
        return "SKIPPED scratch"
    try:
        os_src = os.path.join(ROOT, "src", "os")
        if os_src not in sys.path:
            sys.path.insert(0, os_src)
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(ROOT)
        return "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # a private world may carry no shared writer
        return "SKIPPED %s" % type(exc).__name__


def main(argv):
    check = "--check" in argv
    evidence, facts = measure()
    doc, data = render(evidence, facts)
    if check:
        if not (os.path.exists(JSON_PATH) and os.path.exists(HTML_PATH)):
            print("VERDICT FAIL landed artifacts absent")
            return 2
        with open(JSON_PATH, encoding="utf-8") as handle:
            landed = json.load(handle)
        sizes = _sizes()
        fresh8 = ac_plr8(doc, sizes["html"], sizes["json"])
        evidence["AC-PLVR8"] = fresh8
        # R3070: graded on the document this run would publish, so the check reads
        # the same prose a reader would.
        evidence["AC-PLVR9"] = ac_plr9(doc, CRITERIA)
        for cid, intent in CRITERIA:
            item = evidence[cid]
            print(" | %s %s: %s" % ("PASS" if item["pass"] else "FAIL", cid, item["measured"]))
        passed = sum(1 for v in evidence.values() if v["pass"])
        total = len(CRITERIA)
        ok = (
            passed == total
            and landed.get("fingerprint") == data["fingerprint"]
            and landed.get("verdict") == "PASS"
            and landed.get("sizes") == sizes
            and sizes["html"] > 0
            and sizes["json"] > 0
        )
        print("VERDICT %s %d/%d fingerprint=%s landed=%s sizes=%s"
              % ("PASS" if ok else "FAIL", passed, total, data["fingerprint"],
                 landed.get("fingerprint"), sizes))
        return 0 if ok else 2
    os.makedirs(PREVIEW, exist_ok=True)
    evidence["AC-PLVR9"] = ac_plr9(doc, CRITERIA)
    # The document embeds its own byte sizes, so a one-pass render always
    # reports the size the file had before that line changed it. Iterate to a
    # fixed point and refuse to land if it does not converge.
    prev_json = 0
    converged = False
    for _ in range(12):
        html_bytes = _write(doc, HTML_PATH)
        data["sizes"] = {"html": html_bytes, "json": prev_json}
        row8 = ac_plr8(doc, html_bytes, prev_json)
        for row in data["criteria"]:
            if row["id"] == "AC-PLVR8":
                row["pass"] = row8["pass"]
                row["measured"] = row8["measured"]
            elif row["id"] == "AC-PLVR9":
                row["pass"] = evidence["AC-PLVR9"]["pass"]
                row["measured"] = evidence["AC-PLVR9"]["measured"]
        data["passed"] = sum(1 for c in data["criteria"] if c["pass"])
        data["verdict"] = "PASS" if data["passed"] == data["total"] else "FAIL"
        json_text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        json_bytes = _write(json_text, JSON_PATH)
        if prev_json == json_bytes:
            converged = True
            break
        prev_json = json_bytes
    # AC-PWC24: the face re-derivation belongs to the landed pair, not to a
    # schedule that can run apart from it; the fixed-point loop above writes
    # both halves up to twelve times, so the closure sits AFTER it.
    face = _refresh_face(HTML_PATH, JSON_PATH)
    for cid, intent in CRITERIA:
        row = [c for c in data["criteria"] if c["id"] == cid][0]
        print(" | %s %s: %s" % ("PASS" if row["pass"] else "FAIL", cid, row["measured"]))
    html_bytes = os.path.getsize(HTML_PATH)
    json_bytes = os.path.getsize(JSON_PATH)
    with open(JSON_PATH, encoding="utf-8") as handle:
        landed = json.load(handle)
    consistent = landed.get("sizes") == {"html": html_bytes, "json": json_bytes}
    passed = sum(1 for c in landed["criteria"] if c["pass"])
    total = len(CRITERIA)
    good = converged and consistent and passed == total
    print("VERDICT %s %d/%d fingerprint=%s html=%dB json=%dB self_consistent=%s converged=%s face=%s"
          % ("PASS" if good else "FAIL", passed, total, data["fingerprint"],
             html_bytes, json_bytes, consistent, converged, face))
    return 0 if good else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
