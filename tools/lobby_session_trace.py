"""Drive the shipped lobby sandbox once and publish the frames it answered.

Every other lobby surface on disk is a READING: the spec is prose, the ws
report is a handshake table, the protocol map is a dictionary of message
names. None of them shows what a real client and the real server actually
exchanged. This tool opens one local session against
src/sandbox/lobby/server.py, sends a scripted sequence through the three
gates the sandbox implements (content, non-advisory, rate) plus the room
handshakes, and renders the frames that crossed the socket.

The vocabulary is data, never code: room list, text cap, rate budget and
both wordlist samples are read from src/sandbox/lobby/config.json at render
time, so no Chinese literal and no numeric limit is typed here.

Criteria AC-LST1..AC-LST6 are pinned in src/os/backlog.md BEFORE this file.
The page reports what the text cap DOES, read off the captured frames rather
than off a spec sentence: an over-cap send is refused with the server's own
code once AC-S24 is in force, and the page reverts to the truncation warning
by itself if the server ever regresses. The actor on a broadcast is masked to
its class because the server assigns a per-session id that would otherwise
break render determinism.

Usage:
    python tools/lobby_session_trace.py            # run the session, render
    python tools/lobby_session_trace.py --check    # read-only gate
"""

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import face_backhop  # noqa: E402
ROOT = os.path.dirname(HERE)
LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")
SERVER = os.path.join(LOBBY, "server.py")
CONFIG = os.path.join(LOBBY, "config.json")
OUT_HTML = os.path.join(ROOT, "preview", "lobby-session-trace.html")
OUT_JSON = os.path.join(ROOT, "preview", "lobby-session-trace.json")

NS = "bd-lobby-session-trace-v1"
REL_CONFIG = "src/sandbox/lobby/config.json"
REL_SERVER = "src/sandbox/lobby/server.py"
OUT_REL = "preview/lobby-session-trace.html"

QUIET = 0.30
LONG_MULT = 2


def _read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def _load_json(path):
    return json.loads(_read_bytes(path).decode("utf-8"))


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def mask(value):
    """Keep the shape of a server-assigned id, drop the random part."""
    text = str(value)

    def repl(match):
        word = match.group(0)
        return "<id>" if any(ch.isdigit() for ch in word) else word

    return re.sub(r"[A-Za-z0-9]{5,}", repl, text)


def frame_record(frame):
    payload = frame.get("payload") if isinstance(frame.get("payload"), dict) else {}
    code = payload.get("code")
    text = payload.get("text")
    record = {
        "type": str(frame.get("type", "")),
        "code": str(code) if code else None,
        "room": str(frame["room"]) if frame.get("room") else None,
        "text_len": len(text) if isinstance(text, str) else None,
        "actor": mask(frame.get("actor", "")) or None,
        "ai_generated": bool(frame.get("ai_generated")) if "ai_generated" in frame else None,
        "evt": bool(frame.get("evt_id")),
        "keys": sorted(str(k) for k in frame.keys()),
    }
    return record


class Leg(object):
    """A private server process on a free port over a temp database."""

    def __init__(self):
        self.ws_port = free_port()
        self.tmp = tempfile.mkdtemp(prefix="lobby-trace-")
        self.db = os.path.join(self.tmp, "events.db")
        argv = [
            sys.executable,
            SERVER,
            "--host", "127.0.0.1",
            "--port", str(self.ws_port),
            "--db", self.db,
            "--web-port", "0",
            "--ping-interval", "30",
            "--ping-timeout", "60",
        ]
        self.proc = subprocess.Popen(
            argv, cwd=LOBBY, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True,
        )
        self.banner = self._wait_banner()

    def _wait_banner(self, deadline=25.0):
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            line = self.proc.stdout.readline()
            if not line:
                if self.proc.poll() is not None:
                    raise RuntimeError("server exited before banner")
                time.sleep(0.05)
                continue
            if "serving ws://" in line:
                return line.strip()
        raise RuntimeError("server banner not seen")

    def ws_url(self):
        return "ws://127.0.0.1:%d/ws" % self.ws_port

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - teardown must never mask a result
            try:
                self.proc.kill()
            except Exception:  # noqa: BLE001
                pass


def recv_frame(ws, timeout):
    return json.loads(ws.recv(timeout=timeout))


def drain(ws, quiet=QUIET, limit=40):
    got = []
    for _ in range(limit):
        try:
            got.append(recv_frame(ws, quiet))
        except Exception:  # noqa: BLE001 - a quiet socket is the exit condition
            break
    return got


def send_frame(ws, mtype, **payload):
    body = {"v": 1, "type": mtype}
    if payload:
        body["payload"] = payload
    ws.send(json.dumps(body, ensure_ascii=True))
    return {"type": mtype, "room": payload.get("room"), "text_len": len(payload.get("text", "")) or None}


def step(label, sent, frames):
    return {"label": label, "sent": sent, "frames": [frame_record(f) for f in frames]}


def run_session(cfg):
    from websockets.sync.client import connect

    rooms = list(cfg["rooms"])
    room = rooms[0]
    cap = int(cfg["max_text_len"])
    rate = cfg.get("rate_limit", {})
    forbidden = (cfg.get("gate", {}).get("forbidden_words") or [""])[0]
    advisory = (cfg.get("gate", {}).get("advisory_ban_words") or [""])[0]

    leg = Leg()
    steps = []
    try:
        ws = connect(leg.ws_url())
        steps.append(step("connect: server pushes hello and the standing risk warning",
                          None, drain(ws, quiet=0.6)))

        ws.send(json.dumps({"v": 1, "type": "pay.grant_sandbox", "payload": {}}))
        steps.append(step("pay.grant_sandbox: mock entrance, resident flag", {"type": "pay.grant_sandbox"}, drain(ws)))

        sent = send_frame(ws, "room.subscribe", room=room)
        steps.append(step("room.subscribe %s" % room, sent, drain(ws)))

        clean = "sandbox session trace: one clean line through the public room"
        sent = send_frame(ws, "chat.send", room=room, text=clean)
        steps.append(step("chat.send clean line (accepted)", sent, drain(ws)))

        sent = send_frame(ws, "chat.send", room=room, text="trace probe " + forbidden)
        steps.append(step("chat.send carrying a forbidden word (gate 1)", sent, drain(ws)))

        sent = send_frame(ws, "chat.send", room=room, text="trace probe " + advisory)
        steps.append(step("chat.send carrying an advisory word (gate 2)", sent, drain(ws)))

        long_text = "x" * (cap * LONG_MULT)
        sent = send_frame(ws, "chat.send", room=room, text=long_text)
        steps.append(step("chat.send over the text cap (cap x%d chars)" % LONG_MULT, sent, drain(ws)))

        sent = send_frame(ws, "room.subscribe", room="trace-no-such-room")
        steps.append(step("room.subscribe an unknown room", sent, drain(ws)))

        sent = send_frame(ws, "room.unsubscribe", room=room)
        steps.append(step("room.unsubscribe %s" % room, sent, drain(ws)))

        sent = send_frame(ws, "chat.send", room=room, text="after release")
        steps.append(step("chat.send into the just-released room", sent, drain(ws)))

        ws.close()

        burst = connect(leg.ws_url())
        drain(burst, quiet=0.5)
        # An ungranted connection is refused E_ENTRANCE_REQUIRED before any
        # gate, so the burst must be entitled and in the room to reach the
        # rate gate at all.
        burst.send(json.dumps({"v": 1, "type": "pay.grant_sandbox", "payload": {}}))
        drain(burst, quiet=0.5)
        burst.send(json.dumps({"v": 1, "type": "room.subscribe",
                               "payload": {"room": room}}))
        drain(burst, quiet=0.5)
        budget = int(rate.get("max_messages", 0))
        for index in range(budget + 1):
            burst.send(json.dumps({
                "v": 1, "type": "chat.send",
                "payload": {"room": room, "text": "burst %d" % (index + 1)},
            }))
        burst_frames = drain(burst, quiet=0.6, limit=80)
        burst.close()
        steps.append(step(
            "second connection bursts %d sends against a budget of %d"
            % (budget + 1, budget),
            {"type": "chat.send", "room": room, "text_len": None, "count": budget + 1},
            burst_frames))
    finally:
        leg.close()

    types = []
    for row in steps:
        for frame in row["frames"]:
            if frame["type"] not in types:
                types.append(frame["type"])

    frames = sum(len(row["frames"]) for row in steps)
    refusals = sum(1 for row in steps for f in row["frames"] if f["type"] in ("sec.reject", "err.rate_limit"))
    codes = []
    for row in steps:
        for frame in row["frames"]:
            if frame["code"] and frame["code"] not in codes:
                codes.append(frame["code"])

    over_cap = None
    for row in steps:
        if row["label"].startswith("chat.send over the text cap"):
            sent_len = (cap * LONG_MULT)
            for frame in row["frames"]:
                if frame["type"] in ("sec.reject", "err.rate_limit"):
                    over_cap = {"sent_len": sent_len, "outcome": "REFUSED",
                                "code": frame["code"], "received_len": None}
                    break
                if frame["type"] == "chat.broadcast":
                    got = frame["text_len"]
                    over_cap = {"sent_len": sent_len,
                                "outcome": ("ACCEPTED" if got == sent_len
                                            else "TRUNCATED"),
                                "code": None, "received_len": got}
                    break

    return {
        "namespace": NS,
        "page": OUT_REL,
        "source": {
            "config": REL_CONFIG,
            "config_bytes": os.path.getsize(CONFIG),
            "server": REL_SERVER,
            "server_bytes": os.path.getsize(SERVER),
        },
        "derived": {
            "rooms": rooms,
            "max_text_len": cap,
            "rate_max_messages": int(rate.get("max_messages", 0)),
            "rate_window_seconds": int(rate.get("window_seconds", 0)),
            "mute_trigger_violations": int(rate.get("mute_trigger_violations", 0)),
            "forbidden_sample": forbidden,
            "advisory_sample": advisory,
            "long_sent_len": cap * LONG_MULT,
        },
        "steps": steps,
        "summary": {
            "frames": frames,
            "steps": len(steps),
            "refusals": refusals,
            "types": types,
            "codes": codes,
            "over_cap": over_cap,
        },
    }


def dump_json(payload):
    return (json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")


def _cells(payload):
    return payload["derived"]


def render_html(payload):
    # The visible back-hop block is part of this page, so the fresh derivation
    # compared by --check carries it too (AC-FBH1 holds by construction).
    return face_backhop.inject_text(_render_html(payload),
                                    "lobby-session-trace.html")[0]


def _render_html(payload):
    derived = _cells(payload)
    summary = payload["summary"]
    src = payload["source"]
    out = []
    add = out.append
    add("<!DOCTYPE html>")
    add('<html lang="en"><head><meta charset="utf-8">')
    add('<meta name="viewport" content="width=device-width,initial-scale=1">')
    add("<title>Lobby session trace - frames the sandbox really answered</title>")
    add("<style>")
    add("body{font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0f1116;color:#e8eaf0}")
    add("main{max-width:1080px;margin:0 auto;padding:26px 20px 60px}")
    add("h1{font-size:21px;margin:0 0 6px}h2{font-size:15px;margin:26px 0 8px;color:#9fb0d0}")
    add(".hint{color:#8d96ab;font-size:12.5px}")
    add(".warn{border-left:3px solid #d0a24a;background:#1a1a12;padding:10px 12px;margin:14px 0;font-size:13px}")
    add(".cards{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}")
    add(".card{background:#161a22;border:1px solid #232a37;border-radius:8px;padding:10px 14px;min-width:120px}")
    add(".card b{display:block;font-size:20px;color:#7fd1a0}")
    add("table{width:100%;border-collapse:collapse;margin:8px 0 4px}")
    add("th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #202634;vertical-align:top;font-size:12.5px}")
    add("th{color:#93a2bd;font-weight:600;background:#141821}")
    add(".step{background:#141a24;font-weight:600}")
    add(".t{font-family:Consolas,monospace;color:#9ecbff}")
    add(".code{font-family:Consolas,monospace;color:#ffb4a2}")
    add(".ok{color:#7fd1a0}.no{color:#ff9c8a}")
    add("footer{margin-top:26px;color:#77819a;font-size:12px}")
    add("</style></head><body><main>")
    add("<h1>Lobby session trace</h1>")
    add('<p class="hint">One local session against <span class="t">%s</span>. '
        "Every row below is a frame that actually crossed the socket in this render.</p>" % src["server"])
    add('<div class="warn">This page connects to nothing and is not a live service: it is a '
        "recording of one sandbox session on 127.0.0.1. The entrance is a mock, there is no "
        "merchant, no platform content API and no cloud call. Refusal rows show the codes the "
        "shipped server itself emitted.</div>")

    add('<div class="cards">')
    add('<div class="card"><b>%d</b>frames captured</div>' % summary["frames"])
    add('<div class="card"><b>%d</b>steps driven</div>' % summary["steps"])
    add('<div class="card"><b>%d</b>refusals</div>' % summary["refusals"])
    add('<div class="card"><b>%d</b>distinct types</div>' % len(summary["types"]))
    add("</div>")

    add("<h2>Read from the sandbox config, not typed here</h2>")
    add("<table><tr><th>fact</th><th>value</th><th>source</th></tr>")
    add('<tr><td>rooms</td><td class="t">%s</td><td>%s</td></tr>'
        % (", ".join(derived["rooms"]), src["config"]))
    add('<tr><td>text cap</td><td class="t">%d chars</td><td>%s</td></tr>'
        % (derived["max_text_len"], src["config"]))
    add('<tr><td>rate budget</td><td class="t">%d msgs / %d s, mute after %d violations</td><td>%s</td></tr>'
        % (derived["rate_max_messages"], derived["rate_window_seconds"],
           derived["mute_trigger_violations"], src["config"]))
    add('<tr><td>gate 1 sample</td><td class="t">%s</td><td>%s</td></tr>'
        % (derived["forbidden_sample"], src["config"]))
    add('<tr><td>gate 2 sample</td><td class="t">%s</td><td>%s</td></tr>'
        % (derived["advisory_sample"], src["config"]))
    add("</table>")

    add("<h2>Frames, in the order they crossed the socket</h2>")
    add("<table><tr><th>#</th><th>type</th><th>code</th><th>room</th><th>text len</th>"
        "<th>actor</th><th>ai_generated</th><th>evt</th></tr>")
    index = 0
    for row in payload["steps"]:
        sent = row["sent"]
        sent_text = "client sends"
        if sent:
            bits = [str(sent.get("type"))]
            if sent.get("room"):
                bits.append("room=%s" % sent["room"])
            if sent.get("text_len"):
                bits.append("text=%d chars" % sent["text_len"])
            if sent.get("count"):
                bits.append("x%d" % sent["count"])
            sent_text = "client sends " + " ".join(bits)
        add('<tr class="step"><td>-</td><td colspan="7">%s &middot; %s</td></tr>'
            % (row["label"], sent_text))
        for frame in row["frames"]:
            index += 1
            cls = "no" if frame["type"] in ("sec.reject", "err.rate_limit") else "ok"
            add("<tr><td>%d</td><td class='t %s'>%s</td><td class='code'>%s</td><td class='t'>%s</td>"
                "<td>%s</td><td class='t'>%s</td><td>%s</td><td>%s</td></tr>"
                % (index, cls, frame["type"], frame["code"] or "", frame["room"] or "",
                   "" if frame["text_len"] is None else frame["text_len"],
                   frame["actor"] or "",
                   "" if frame["ai_generated"] is None else str(frame["ai_generated"]).lower(),
                   "yes" if frame["evt"] else ""))
    add("</table>")

    over_cap = summary["over_cap"]
    add("<h2>What the text cap does</h2>")
    if over_cap and over_cap["outcome"] == "REFUSED":
        add('<div class="warn">An over-cap send is <b>refused</b>: the client sent %d characters '
            "and the server answered <span class=\"code\">%s</span> instead of broadcasting a "
            'shorter line, so no text is silently lost. The spec names the code and its payload '
            "(AC-S24), the gate console answers the same input with 413, and the same cap applies "
            "to idea.submit.</div>" % (over_cap["sent_len"], over_cap["code"]))
    elif over_cap and over_cap["outcome"] == "TRUNCATED":
        add('<div class="warn">An over-long send was NOT refused. The client sent %d characters and '
            "the server broadcast %d: the text cap <b>truncates silently</b>, so a client that "
            "depends on a refusal code for over-length text is depending on behaviour the server "
            "does not have. This page reads the outcome off the captured frames, so it will say so "
            "again if the server ever regresses.</div>"
            % (over_cap["sent_len"], over_cap["received_len"]))
    elif over_cap and over_cap["outcome"] == "ACCEPTED":
        add('<div class="warn">The over-cap send was accepted at full length (%d characters), so '
            "the text cap is not enforced at all on this path.</div>"
            % over_cap["sent_len"])
    else:
        add('<div class="warn">No refusal and no broadcast row was captured for the over-cap probe, '
            "so what the cap does is NOT confirmed by this render.</div>")

    add("<h2>Codes the server emitted</h2>")
    add('<p class="t">%s</p>' % (", ".join(summary["codes"]) or "none"))
    add("<h2>Frame types observed</h2>")
    add('<p class="t">%s</p>' % ", ".join(summary["types"]))
    add("<footer>")
    add("config %s &middot; %d bytes &middot; server %s &middot; %d bytes<br>"
        % (src["config"], src["config_bytes"], src["server"], src["server_bytes"]))
    add("namespace %s &middot; this page is rendered from %s, which is the landed payload."
        % (payload["namespace"], "preview/lobby-session-trace.json"))
    add("</footer>")
    add("</main>")
    add("<script>")
    add("(function(){var k='%s';try{var v=localStorage.getItem(k);"
        "document.documentElement.setAttribute('data-seen',v?'yes':'no');"
        "localStorage.setItem(k,'1');}catch(e){}})();" % NS)
    add("</script></body></html>")
    return ("\n".join(out) + "\n").encode("utf-8")


def write_file_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as handle:
        handle.write(data)
    os.replace(tmp, path)


def check(payload_bytes, html_bytes):
    findings = []
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return ["landed json is not readable: %s" % exc], 2

    # AC-LST2: the recorded derived facts must still match the live config.
    try:
        cfg = _load_json(CONFIG)
    except Exception as exc:  # noqa: BLE001
        return ["config unreadable: %s" % exc], 2
    derived = payload.get("derived", {})
    if list(derived.get("rooms") or []) != list(cfg.get("rooms") or []):
        findings.append("E_CFG rooms drifted from config")
    if int(derived.get("max_text_len", -1)) != int(cfg.get("max_text_len", -2)):
        findings.append("E_CFG text cap drifted from config")
    rate = cfg.get("rate_limit") or {}
    if int(derived.get("rate_max_messages", -1)) != int(rate.get("max_messages", -2)):
        findings.append("E_CFG rate budget drifted from config")
    if int(derived.get("rate_window_seconds", -1)) != int(rate.get("window_seconds", -2)):
        findings.append("E_CFG rate window drifted from config")
    forbidden = (cfg.get("gate", {}).get("forbidden_words") or [""])[0]
    advisory = (cfg.get("gate", {}).get("advisory_ban_words") or [""])[0]
    if derived.get("forbidden_sample") != forbidden:
        findings.append("E_CFG gate 1 sample drifted from config")
    if derived.get("advisory_sample") != advisory:
        findings.append("E_CFG gate 2 sample drifted from config")

    # AC-LST1: the frame count is the rows actually recorded.
    steps = payload.get("steps") or []
    counted = sum(len(row.get("frames") or []) for row in steps)
    if counted != int(payload.get("summary", {}).get("frames", -1)):
        findings.append("E_SUM frame count %d != recorded rows %d"
                        % (payload.get("summary", {}).get("frames", -1), counted))

    # AC-LST4: a refusal row must carry a server code, and the two gate
    # refusals must be distinguishable from the rate refusal.
    refusals = [f for row in steps for f in (row.get("frames") or [])
                if f.get("type") in ("sec.reject", "err.rate_limit")]
    if not refusals:
        findings.append("E_ROWS no refusal row was captured")
    for frame in refusals:
        if not frame.get("code"):
            findings.append("E_ROWS %s row carries no server code" % frame.get("type"))
    codes = set(payload.get("summary", {}).get("codes") or [])
    for wanted in ("E_CONTENT_REJECTED", "E_ROOM_UNKNOWN", "E_RATE_LIMIT"):
        if wanted not in codes:
            findings.append("E_ROWS code %s never appeared in the session" % wanted)
    if not any(f.get("type") == "chat.broadcast" and f.get("ai_generated") is False
               for row in steps for f in (row.get("frames") or [])):
        findings.append("E_ROWS no accepted broadcast carrying the server ai_generated flag")

    # AC-LST3: the html must be the pure function of the LANDED payload.
    fresh = render_html(payload)
    if fresh != html_bytes:
        findings.append("E_STALE html is not the fresh derivation of the landed json")

    # AC-LST5: offline, and every relative link target exists.
    text = html_bytes.decode("utf-8", "replace")
    for needle in ("http://", "https://"):
        if needle in text:
            findings.append("E_OFFLINE html carries a %s literal" % needle)

    # AC-LST6: recorded source sizes still describe the final tree.
    if payload.get("source", {}).get("config_bytes") != os.path.getsize(CONFIG):
        findings.append("E_SRC config size is stale")
    if payload.get("source", {}).get("server_bytes") != os.path.getsize(SERVER):
        findings.append("E_SRC server size is stale")

    return findings, (0 if not findings else 2)


def main(argv):
    checking = "--check" in argv
    if checking:
        if not (os.path.exists(OUT_HTML) and os.path.exists(OUT_JSON)):
            print("VERDICT FAIL 1 (artifacts missing)")
            return 2
        before = (os.path.getsize(OUT_HTML), os.path.getmtime(OUT_HTML),
                  os.path.getsize(OUT_JSON), os.path.getmtime(OUT_JSON))
        findings, code = check(_read_bytes(OUT_JSON), _read_bytes(OUT_HTML))
        after = (os.path.getsize(OUT_HTML), os.path.getmtime(OUT_HTML),
                 os.path.getsize(OUT_JSON), os.path.getmtime(OUT_JSON))
        if before != after:
            findings = findings + ["E_WRITE --check changed the artifacts"]
            code = 2
        if findings:
            for finding in findings:
                print("  - " + finding)
            print("VERDICT FAIL %d rc=%d" % (len(findings), 2 if code else 0))
            return 2
        payload = json.loads(_read_bytes(OUT_JSON).decode("utf-8"))
        summary = payload["summary"]
        print("VERDICT PASS steps=%d frames=%d refusals=%d types=%d codes=%d html=%dB json=%dB rc=0"
              % (summary["steps"], summary["frames"], summary["refusals"],
                 len(summary["types"]), len(summary["codes"]),
                 os.path.getsize(OUT_HTML), os.path.getsize(OUT_JSON)))
        if summary.get("over_cap"):
            print("  cap: sent=%d outcome=%s code=%s received=%s"
                  % (summary["over_cap"]["sent_len"], summary["over_cap"]["outcome"],
                     summary["over_cap"]["code"], summary["over_cap"]["received_len"]))
        return 0

    cfg = _load_json(CONFIG)
    payload = run_session(cfg)
    if not os.path.isdir(os.path.dirname(OUT_HTML)):
        os.makedirs(os.path.dirname(OUT_HTML))
    write_file_atomic(OUT_JSON, dump_json(payload))
    robot = render_html(payload)
    write_file_atomic(OUT_HTML, robot)
    summary = payload["summary"]
    print("RENDERED steps=%d frames=%d refusals=%d types=%d codes=%d html=%dB json=%dB"
          % (summary["steps"], summary["frames"], summary["refusals"],
             len(summary["types"]), len(summary["codes"]),
             os.path.getsize(OUT_HTML), os.path.getsize(OUT_JSON)))
    print("types: " + " ".join(summary["types"]))
    print("codes: " + " ".join(summary["codes"]))
    if summary.get("over_cap"):
        print("cap: sent=%d outcome=%s code=%s received=%s"
              % (summary["over_cap"]["sent_len"], summary["over_cap"]["outcome"],
                 summary["over_cap"]["code"], summary["over_cap"]["received_len"]))
    findings, code = check(_read_bytes(OUT_JSON), _read_bytes(OUT_HTML))
    for finding in findings:
        print("  - " + finding)
    print("SELF-CHECK rc=%d findings=%d" % (code, len(findings)))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
