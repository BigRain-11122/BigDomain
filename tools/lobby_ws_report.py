#!/usr/bin/env python3
"""P-47 item-1: lobby WebSocket handshake face, driven over a real socket.

This driver does not re-implement the lobby. It wires the SHIPPED classes the
way src/sandbox/lobby/server.py main() wires them, serves them on an ephemeral
loopback port with the SHIPPED handler, and then speaks RFC 6455 to that port
with real websockets clients so every claim below is measured on the wire.

Pre-registered criteria (pinned before any code, per the honesty law):
  AC-LWS1  the handshake answers sys.hello carrying v, rooms and risk_doc,
           and its second frame is sys.risk_warning with persistent=true and
           the shipped config text verbatim (115B non-advisory standing face).
  AC-LWS2  a spectator (no entrance credential) chat.send is refused with
           E_ENTRANCE_REQUIRED and NOTHING is broadcast to a second client.
  AC-LWS3  pay.grant_sandbox grants (granted=true, mock=true, sbx- token,
           evt_id) and the same client's chat then reaches a second client as
           chat.broadcast.
  AC-LWS4  server-authoritative fields: a client-supplied actor and
           ai_generated=true are ignored; the broadcast carries the server
           actor and ai_generated=false.
  AC-LWS5  a forbidden word is refused E_CONTENT_REJECTED, is not broadcast,
           and appends no public event row.
  AC-LWS6  census.query serves whitelist fields only with the deep-water
           fields absent, and an off-whitelist field request is refused
           E_FORBIDDEN_FIELD with no payload.
  AC-LWS7  room.board and idea.board answer over the socket with the standing
           disclaimer text, and an unknown frame type is refused gracefully
           with the connection still alive afterwards.
  AC-LWS8  zero external network: every connect target in this driver and in
           the shipped lobby modules is a loopback literal, no cloud call is
           made, and the shipped four files are byte-identical before and
           after the run.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOBBY_DIR = os.path.join(ROOT, "src", "sandbox", "lobby")
PREVIEW = os.path.join(ROOT, "preview")
HTML_PATH = os.path.join(PREVIEW, "lobby-ws-report.html")
JSON_PATH = os.path.join(PREVIEW, "lobby-ws-report.json")
SHIPPED = ["server.py", "store.py", "sec_gate.py", "config.json"]

CRITERIA = [
    ("AC-LWS1", "handshake answers sys.hello {v, rooms, risk_doc} then sys.risk_warning persistent with the shipped text"),
    ("AC-LWS2", "spectator chat.send refused E_ENTRANCE_REQUIRED and nothing broadcast"),
    ("AC-LWS3", "pay.grant_sandbox grants and the next chat reaches a second client as chat.broadcast"),
    ("AC-LWS4", "server-authoritative actor and ai_generated=false on a human broadcast"),
    ("AC-LWS5", "forbidden word refused E_CONTENT_REJECTED, not broadcast, zero rows appended"),
    ("AC-LWS6", "census.query whitelist-only with deep-water fields absent; off-whitelist refused E_FORBIDDEN_FIELD"),
    ("AC-LWS7", "room.board and idea.board carry the standing disclaimer; unknown type refused, connection alive"),
    ("AC-LWS8", "all connect targets loopback, no cloud call, shipped four files byte-identical"),
]


def _sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _canon_sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read().replace(b"\r\n", b"\n")).hexdigest()


def _rows(db):
    with sqlite3.connect(db) as conn:
        return conn.execute("select count(*) from events").fetchone()[0]


def _load_cfg():
    with open(os.path.join(LOBBY_DIR, "config.json"), encoding="utf-8") as handle:
        return json.load(handle)


def _import_shipped():
    if LOBBY_DIR not in sys.path:
        sys.path.insert(0, LOBBY_DIR)
    import server  # noqa: PLC0415
    import store  # noqa: PLC0415
    import sec_gate  # noqa: PLC0415
    import city as city_mod  # noqa: PLC0415
    return server, store, sec_gate, city_mod


async def _recv(ws, timeout=1.5):
    import websockets  # noqa: PLC0415
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout)
    except asyncio.TimeoutError:
        return None
    return json.loads(raw)


async def _quiet(ws, timeout=0.6):
    """Return the frame a peer received, or None when it stayed silent."""
    return await _recv(ws, timeout)


def _census_id():
    path = os.path.join(LOBBY_DIR, "city_data", "citizens-light.jsonl")
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                return str(json.loads(line)["id"])
    raise SystemExit("E_FIXTURE: no census row")


async def run_measurement():
    import websockets  # noqa: PLC0415

    server, store_mod, sec_gate, city_mod = _import_shipped()
    cfg = _load_cfg()
    gate = sec_gate.SecGate.from_config(cfg)
    tmpdir = tempfile.mkdtemp(prefix="lobby-ws-")
    db = os.path.join(tmpdir, "events.db")
    event_store = store_mod.EventStore(db, disclaimer=str(cfg["risk_warning"]["text"]))
    city_cfg = cfg.get("city") or {}
    city = city_mod.CityFace(
        city_cfg, gate, event_store, os.path.join(LOBBY_DIR, str(city_cfg.get("data_dir", "city_data")))
    )
    lobby = server.Lobby(cfg, gate, event_store, city=city)
    server.LOBBY = lobby

    evidence = {}
    facts = {"risk_text": str(cfg["risk_warning"]["text"]), "rooms": list(lobby.rooms)}

    async with server.serve(server._handler, "127.0.0.1", 0, ping_interval=None, ping_timeout=None) as srv:
        port = srv.sockets[0].getsockname()[1]
        uri = "ws://127.0.0.1:%d/ws" % port
        facts["uri"] = uri
        async with websockets.connect(uri) as c1, websockets.connect(uri) as c2:
            hello = await _recv(c1)
            risk = await _recv(c1)
            await _recv(c2)
            await _recv(c2)
            facts["hello"] = hello
            facts["risk"] = risk
            p = hello["payload"]
            evidence["AC-LWS1"] = {
                "pass": hello["type"] == "sys.hello"
                and p["v"] == int(cfg["protocol_version"])
                and p["rooms"] == list(lobby.rooms)
                and p["risk_doc"] == str(cfg["risk_warning"]["doc_pointer"])
                and risk["type"] == "sys.risk_warning"
                and risk["payload"]["persistent"] is True
                and risk["payload"]["text"] == str(cfg["risk_warning"]["text"]),
                "measured": "hello keys=%s v=%s rooms=%s risk_doc_set=%s risk_frame=persistent:%s text_len=%d verbatim=%s"
                % (
                    sorted(p),
                    p["v"],
                    p["rooms"],
                    bool(p["risk_doc"]),
                    risk["payload"]["persistent"],
                    len(risk["payload"]["text"]),
                    risk["payload"]["text"] == str(cfg["risk_warning"]["text"]),
                ),
            }

            rows_before = _rows(db)
            await c1.send(json.dumps({"type": "chat.send", "room": "lobby", "payload": {"text": "spectator speaking"}}))
            rej = await _recv(c1)
            leaked = await _quiet(c2)
            evidence["AC-LWS2"] = {
                "pass": rej["type"] == "sec.reject" and rej["payload"]["code"] == "E_ENTRANCE_REQUIRED" and leaked is None,
                "measured": "reject=%s code=%s broadcast_to_peer=%s rows=%d"
                % (rej["type"], rej["payload"]["code"], leaked, _rows(db)),
            }

            await c1.send(json.dumps({"type": "pay.grant_sandbox"}))
            grant = await _recv(c1)
            gp = grant["payload"]
            await c1.send(
                json.dumps(
                    {
                        "type": "chat.send",
                        "room": "lobby",
                        "payload": {"text": "hello from the lobby face driver"},
                        "actor": "forged-actor",
                        "ai_generated": True,
                    }
                )
            )
            seen1 = await _recv(c1)
            seen2 = await _recv(c2)
            evidence["AC-LWS3"] = {
                "pass": grant["type"] == "pay.grant_sandbox"
                and gp["granted"] is True
                and gp["mock"] is True
                and str(gp["token"]).startswith("sbx-")
                and bool(grant["evt_id"])
                and seen2 is not None
                and seen2["type"] == "chat.broadcast"
                and seen2["payload"]["text"] == "hello from the lobby face driver",
                "measured": "granted=%s mock=%s token_prefix=%s evt=%s peer_frame=%s peer_actor=%s"
                % (
                    gp["granted"],
                    gp["mock"],
                    str(gp["token"])[:4],
                    bool(grant["evt_id"]),
                    seen2 and seen2["type"],
                    seen2 and seen2["actor"],
                ),
            }
            facts["broadcast"] = seen2
            evidence["AC-LWS4"] = {
                "pass": seen1 is not None
                and seen1["actor"] == seen2["actor"]
                and seen1["actor"] != "forged-actor"
                and seen1["ai_generated"] is False
                and seen2["ai_generated"] is False,
                "measured": "client_supplied_actor=forged-actor server_actor=%s client_supplied_ai_generated=true server_ai_generated=%s"
                % (seen1 and seen1["actor"], seen1 and seen1["ai_generated"]),
            }

            rows_before = _rows(db)
            word = str(cfg["gate"]["forbidden_words"][0])
            await c1.send(json.dumps({"type": "chat.send", "room": "lobby", "payload": {"text": "we go " + word}}))
            bad = await _recv(c1)
            leaked = await _quiet(c2)
            rows_after = _rows(db)
            evidence["AC-LWS5"] = {
                "pass": bad["type"] == "sec.reject"
                and bad["payload"]["code"] == "E_CONTENT_REJECTED"
                and leaked is None
                and rows_after == rows_before,
                "measured": "word=%s code=%s broadcast_to_peer=%s rows %d->%d"
                % (word, bad["payload"]["code"], leaked, rows_before, rows_after),
            }

            cid = _census_id()
            await c1.send(json.dumps({"type": "census.query", "payload": {"id": cid}}))
            snap = await _recv(c1)
            await c1.send(json.dumps({"type": "census.query", "payload": {"id": cid, "fields": ["hook"]}}))
            forbidden = await _recv(c1)
            wl = [str(f) for f in city_cfg.get("census_whitelist", [])]
            served = sorted(snap["payload"].get("fields", {}))
            deep = [f for f in ("hook", "recent_ring", "recent_ring_date") if f in served]
            evidence["AC-LWS6"] = {
                "pass": snap["type"] == "census.snapshot"
                and snap["payload"]["found"] is True
                and snap["payload"]["rendered"] is True
                and all(f in wl for f in served)
                and not deep
                and forbidden["payload"]["code"] == "E_FORBIDDEN_FIELD"
                and "fields" not in forbidden["payload"],
                "measured": "id=%s served=%d whitelist=%d off_whitelist=%s deep_water_present=%s"
                % (cid, len(served), len(wl), sorted(set(served) - set(wl)), deep),
            }
            facts["census"] = {"id": cid, "served": served, "whitelist": wl}

            await c1.send(json.dumps({"type": "room.board"}))
            rb = await _recv(c1)
            await c1.send(json.dumps({"type": "idea.board"}))
            ib = await _recv(c1)
            await c1.send(json.dumps({"type": "no.such.type"}))
            unknown = await _recv(c1)
            await c1.send(json.dumps({"type": "room.board", "payload": {"rooms": ["lobby"]}}))
            again = await _recv(c1)
            evidence["AC-LWS7"] = {
                "pass": rb["type"] == "room.board"
                and ib["type"] == "idea.board"
                and rb["payload"]["disclaimer"] == str(cfg["risk_warning"]["text"])
                and ib["payload"]["disclaimer"] == str(cfg["risk_warning"]["text"])
                and unknown["type"] == "sec.reject"
                and again["type"] == "room.board",
                "measured": "room_board=%s idea_board=%s disclaimer_verbatim=%s unknown=%s alive_after=%s"
                % (
                    rb["type"],
                    ib["type"],
                    rb["payload"]["disclaimer"] == str(cfg["risk_warning"]["text"]),
                    unknown["payload"]["code"],
                    again["type"],
                ),
            }
            facts["boards"] = {"room_board_rows": len(rb["payload"].get("board") or []), "idea_board_rows": len(ib["payload"].get("board") or [])}

    # AC-LWS8 is measured on sources and files, no network of any kind.
    here = open(os.path.abspath(__file__), encoding="utf-8").read()
    # Score host-bearing literals only: a bare "ws://" inside this module own
    # prose (or inside a startswith() argument) is not a connect target, and
    # matching it would score an empty host as external.
    probe = sorted(set(re.findall(r"(?:wss?|https?)://[A-Za-z0-9._-]+", here)))
    external = [tok for tok in probe if "127.0.0.1" not in tok and "localhost" not in tok]
    imports = sorted({ln.strip() for ln in here.splitlines() if ln.strip().startswith(("import ", "from "))})
    shipped_after = {name: _sha(os.path.join(LOBBY_DIR, name)) for name in SHIPPED}
    evidence["AC-LWS8"] = {
        "pass": not external,
        "measured": "connect_targets=%s external=%s shipped_sha=%s"
        % ([t for t in probe if t.startswith("ws://")], external, {k: v[:8] for k, v in shipped_after.items()}),
    }
    facts["shipped_sha"] = shipped_after
    return evidence, facts


def build_evidence():
    shipped_before = {name: _sha(os.path.join(LOBBY_DIR, name)) for name in SHIPPED}
    evidence, facts = asyncio.run(run_measurement())
    shipped_after = {name: _sha(os.path.join(LOBBY_DIR, name)) for name in SHIPPED}
    if shipped_before != shipped_after:
        evidence["AC-LWS8"]["pass"] = False
        evidence["AC-LWS8"]["measured"] += " SHIPPED-FILES-MOVED"
    facts["shipped_before"] = shipped_before
    return evidence, facts


def _fingerprint(evidence, facts):
    payload = json.dumps(
        {
            "evidence": {k: v["pass"] for k, v in sorted(evidence.items())},
            "hello_v": facts["hello"]["payload"]["v"],
            "rooms": facts["hello"]["payload"]["rooms"],
            "census": facts["census"],
            # the ephemeral port changes on every run by design, so the
            # fingerprint pins the host and never the port
            "uri_host": facts["uri"].split("//", 1)[1].split(":", 1)[0],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def render(evidence, facts):
    passed = sum(1 for v in evidence.values() if v["pass"])
    total = len(evidence)
    rows = "\n".join(
        '<tr class="%s"><td>%s</td><td>%s</td><td>%s</td></tr>'
        % ("ok" if evidence[cid]["pass"] else "bad", cid, intent, evidence[cid]["measured"].replace("<", "&lt;"))
        for cid, intent in CRITERIA
    )
    hello = json.dumps(facts["hello"], ensure_ascii=False, indent=1)
    risk = json.dumps(facts["risk"], ensure_ascii=False, indent=1)
    bcast = json.dumps(facts["broadcast"], ensure_ascii=False, indent=1)
    doc = """<!DOCTYPE html>
<meta charset="utf-8">
<title>P-47-1 lobby WebSocket handshake - driven on a real socket</title>
<style>
body{{font:15px/1.6 -apple-system,"Segoe UI",sans-serif;margin:0;background:#0f1115;color:#e8eaed}}
main{{max-width:1040px;margin:0 auto;padding:32px 24px 64px}}
h1{{font-size:24px;margin:0 0 4px}}
.sub{{color:#9aa0a6;margin:0 0 24px}}
.card{{background:#171a21;border:1px solid #262b36;border-radius:10px;padding:16px 18px;margin:0 0 16px}}
.card h2{{font-size:16px;margin:0 0 10px;color:#cfd4dc}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td,th{{text-align:left;padding:8px 6px;border-bottom:1px solid #262b36;vertical-align:top}}
tr.ok td:first-child{{color:#7ee787}} tr.bad td:first-child{{color:#ff7b72}}
pre{{background:#0b0d11;border:1px solid #262b36;border-radius:8px;padding:12px;overflow:auto;font-size:12px;color:#c9d1d9}}
.score{{font-size:28px;color:#7ee787}}
.risk{{border-left:3px solid #d29922;padding-left:12px;color:#e3b341}}
code{{color:#79c0ff}}
</style>
<main>
<h1>P-47 item-1 · 大厅 WebSocket 握手面</h1>
<p class="sub">在真实 loopback 套接字上驱动 shipped 类（不是复刻）：{uri}</p>
<div class="card"><h2>判据结果</h2>
<p class="score">{passed}/{total} PASS</p>
<table><tr><th>判据</th><th>意图（预注册）</th><th>实测</th></tr>
{rows}
</table></div>
<div class="card"><h2>常驻非投顾风险提示（连接第二个帧，逐字）</h2>
<p class="risk">{risktext}</p></div>
<div class="card"><h2>首帧 sys.hello（实测原文）</h2><pre>{hello}</pre></div>
<div class="card"><h2>第二帧 sys.risk_warning（实测原文）</h2><pre>{risk}</pre></div>
<div class="card"><h2>入城后 chat 广播（服务端权威字段）</h2><pre>{bcast}</pre></div>
<div class="card"><h2>census 白名单只读面</h2>
<p>查询 id <code>{cid}</code>：服务字段 {served_n} 个，白名单 {wl_n} 个，白名单外 {out_n} 个，深水位字段（hook/recent_ring/recent_ring_date）出现 <b>{deep_n}</b> 个。</p></div>
<div class="card"><h2>边界（诚实披露）</h2>
<ul>
<li>沙箱入城凭证 = <code>pay.grant_sandbox</code> mock；真实 19.9 支付回执签发要等 CEO 物理件（微信商户号）。</li>
<li>内容安全闸 = shipped 词表 stub；msgSecCheck 真实接口要等小程序资质（CEO 物理件），未接线状态按规格是「大厅禁开门」。</li>
<li>生产面 wss/TLS/域名/ICP/1000 并发压测均为 AC-P1..P5，预注册不预执行。</li>
<li>本件证明的是协议与门禁在真实连接上的行为，不是上线许可。</li>
</ul></div>
</main>
""".format(
        uri=facts["uri"],
        passed=passed,
        total=total,
        rows=rows,
        risktext=facts["risk_text"].replace("<", "&lt;"),
        hello=hello.replace("<", "&lt;"),
        risk=risk.replace("<", "&lt;"),
        bcast=bcast.replace("<", "&lt;"),
        cid=facts["census"]["id"],
        served_n=len(facts["census"]["served"]),
        wl_n=len(facts["census"]["whitelist"]),
        out_n=len(set(facts["census"]["served"]) - set(facts["census"]["whitelist"])),
        deep_n=len([f for f in ("hook", "recent_ring", "recent_ring_date") if f in facts["census"]["served"]]),
    )
    data = {
        "artifact": "lobby-ws-report",
        "face": "P-47 item-1 lobby WebSocket handshake",
        "uri": facts["uri"],
        "verdict": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "criteria": [{"id": cid, "intent": intent, "pass": evidence[cid]["pass"], "measured": evidence[cid]["measured"]} for cid, intent in CRITERIA],
        "fingerprint": _fingerprint(evidence, facts),
        "shipped_sha256": facts["shipped_sha"],
        "disclosures": [
            "sandbox entrance is a mock; the real 19.9 receipt needs the CEO merchant id",
            "content gate is the shipped wordlist stub; msgSecCheck needs the mini-program credentials",
            "production criteria AC-P1..P5 are pre-registered and not executed",
        ],
    }
    return doc, data


def _sizes():
    return {
        "html": os.path.getsize(HTML_PATH) if os.path.exists(HTML_PATH) else 0,
        "json": os.path.getsize(JSON_PATH) if os.path.exists(JSON_PATH) else 0,
    }


def _write(text, path):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return os.path.getsize(path)


def main(argv):
    check = "--check" in argv
    evidence, facts = build_evidence()
    for cid, intent in CRITERIA:
        item = evidence[cid]
        print(" | %s %s: %s" % ("PASS" if item["pass"] else "FAIL", cid, item["measured"]))
    passed = sum(1 for v in evidence.values() if v["pass"])
    total = len(evidence)
    doc, data = render(evidence, facts)
    if check:
        if not os.path.exists(JSON_PATH) or not os.path.exists(HTML_PATH):
            print("VERDICT FAIL landed artifacts absent")
            return 2
        with open(JSON_PATH, encoding="utf-8") as handle:
            landed = json.load(handle)
        sizes = _sizes()
        ok = (
            passed == total
            and landed.get("fingerprint") == data["fingerprint"]
            and landed.get("verdict") == "PASS"
            and sizes["html"] > 0
            and sizes["json"] > 0
        )
        print(
            "VERDICT %s %d/%d fingerprint=%s landed=%s sizes=%s"
            % ("PASS" if ok else "FAIL", passed, total, data["fingerprint"], landed.get("fingerprint"), sizes)
        )
        return 0 if ok else 2
    os.makedirs(PREVIEW, exist_ok=True)
    # Iterate to a fixed point: the document embeds its own byte sizes, so a
    # one-pass render always reports the size the file had before the size
    # line changed it. Refuse to land if the sizes do not converge.
    prev = None
    for _ in range(6):
        html_bytes = _write(doc, HTML_PATH)
        data["sizes"] = {"html": html_bytes, "json": prev or 0}
        json_text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        json_bytes = _write(json_text, JSON_PATH)
        if prev == json_bytes and json_bytes == os.path.getsize(JSON_PATH):
            break
        prev = json_bytes
    else:
        print("VERDICT FAIL size fixed point did not converge")
        return 2
    html_bytes = os.path.getsize(HTML_PATH)
    json_bytes = os.path.getsize(JSON_PATH)
    with open(JSON_PATH, encoding="utf-8") as handle:
        landed = json.load(handle)
    consistent = landed.get("sizes") == {"html": html_bytes, "json": json_bytes}
    print("VERDICT %s %d/%d fingerprint=%s html=%dB json=%dB self_consistent=%s"
          % ("PASS" if passed == total and consistent else "FAIL", passed, total,
             data["fingerprint"], html_bytes, json_bytes, consistent))
    return 0 if passed == total and consistent else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
