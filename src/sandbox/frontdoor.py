"""XL-16 front door: one openable URL composing the REAL sandbox faces.

Group dispatch D-20260930-06 (XL-16, window 10-07): assemble one
openable URL from the existing lobby/pay sandbox. Pure composition --
zero new business faces, zero schema changes, zero modification of any
existing sandbox file. Everything rendered is loaded at runtime from
the real config/data artifacts:

  city face   <- lobby/city_data/world-public.json + citizens jsonl
  journey     <- src/sandbox/journey_demo.py run once at startup
  lobby face  <- lobby/config.json (rooms, limits, persistent warning)
  pay face    <- pay/config.json (SKUs, channels, persistent disclaimer)

Compliance (BLUEPRINT sec.5): AIGC label + persistent non-advisory
risk warnings are rendered non-collapsible from config, never
hardcoded in this source. Chinese text lives only in data files.

Usage: python src/sandbox/frontdoor.py   (serves http://127.0.0.1:8093/)
One-click relaunch: frontdoor_start.bat

v0.4 (2026-10-02, product-first self-driven round): adds two more
composed cards -- the membership tier face (member/config.json) and
the quality face (suite inventory imported from reconcile_all.py plus
the newest qa/reconcile-all-*.log verdict read from disk at render
time). Still pure composition: every displayed string is loaded at
runtime from real config/data/evidence artifacts, never hardcoded.
"""

import glob
import html
import json
import os
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import reconcile_all  # suite inventory single source (reuse, no copy)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOBBY_CFG = os.path.join(HERE, "lobby", "config.json")
PAY_CFG = os.path.join(HERE, "pay", "config.json")
MEMBER_CFG = os.path.join(HERE, "member", "config.json")
QA_DIR = os.path.join(ROOT, "qa")
WORLD = os.path.join(HERE, "lobby", "city_data", "world-public.json")
CITIZENS = os.path.join(HERE, "lobby", "city_data", "citizens-light.jsonl")
JOURNEY = os.path.join(HERE, "journey_demo.py")

HOST, PORT = "127.0.0.1", 8093


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def esc(value):
    return html.escape(str(value), quote=True)


def run_journey_once():
    """Run the real J1..J9 business-day journey once, keep transcript."""
    try:
        proc = subprocess.run(
            [sys.executable, JOURNEY], capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=ROOT, timeout=60)
        lines = [ln.strip() for ln in (proc.stdout or "").splitlines()
                 if ln.strip()]
        ok = proc.returncode == 0
        return ok, lines, (proc.stderr or "").strip()
    except Exception as exc:  # honest failure face, never fake PASS
        return False, [], "journey subprocess failed: %s" % exc


JOURNEY_OK, JOURNEY_LINES, JOURNEY_ERR = run_journey_once()


def latest_regression_evidence():
    """Newest full-regression log in qa/ (rendered from disk, F3 law:
    no canned numbers; honest empty face when no evidence exists)."""
    best = None
    for path in glob.glob(os.path.join(QA_DIR, "reconcile-all-*.log")):
        if best is None or os.path.getmtime(path) > os.path.getmtime(best):
            best = path
    if best is None:
        return None, "", ""
    verdict = ""
    with open(best, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("RUNNER "):
                verdict = line  # last RUNNER line wins
    stamp = datetime.fromtimestamp(os.path.getmtime(best))
    return best, verdict, stamp.strftime("%Y-%m-%d %H:%M")


def suite_groups():
    """Group the real suite inventory by product dir (reuse law:
    imported from reconcile_all.SUITES, never duplicated here)."""
    groups = {}
    for _label, rel, crit in reconcile_all.SUITES:
        key = os.path.dirname(rel)
        cnt, total = groups.get(key, (0, 0))
        groups[key] = (cnt + 1, total + crit)
    return groups


def render():
    lobby = load_json(LOBBY_CFG)
    pay = load_json(PAY_CFG)
    member = load_json(MEMBER_CFG)
    world = load_json(WORLD)
    citizens = []
    if os.path.exists(CITIZENS):
        with open(CITIZENS, encoding="utf-8") as fh:
            citizens = [json.loads(ln) for ln in fh if ln.strip()]
    white = lobby["city"]["census_whitelist"]
    ai_label = esc(lobby.get("ai_label_text", ""))
    warn = esc(lobby["risk_warning"]["text"])
    pay_warn = esc(pay["compliance"]["disclaimer"])
    city = world["city"]
    events = world.get("events_tail", [])

    cit_rows = "".join(
        "<tr>%s</tr>" % "".join(
            "<td>%s</td>" % esc(c.get(k, "")) for k in white)
        for c in citizens[:5])

    evt_rows = "".join(
        "<li><span class=ts>%s</span> <b>%s</b> - %s</li>"
        % (esc(e.get("ts_utc", "")), esc(e.get("zone", "")),
           esc(e.get("summary", ""))) for e in events)

    journey_html = ""
    if JOURNEY_OK:
        journey_html = "<ul class=proof>%s</ul>" % "".join(
            "<li>%s</li>" % esc(ln) for ln in JOURNEY_LINES)
    else:
        journey_html = ("<p class=fail>JOURNEY RUN FAILED (honest "
                        "failure, no fake PASS). stderr: %s</p>"
                        % esc(JOURNEY_ERR[:500]))

    sku_rows = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%.2f CNY</td><td>%s</td>"
        "</tr>" % (esc(key), esc(val.get("channel", "")),
                   val.get("price_cent", 0) / 100.0,
                   esc(val.get("copy", "")))
        for key, val in pay.get("products", {}).items())

    rl = lobby["rate_limit"]
    hb = lobby["heartbeat"]

    tier_rows = ""
    for key in ("experience", "patron", "mayor", "cocreator"):
        tier = member.get("tiers", {}).get(key)
        if not tier:
            continue
        tier_rows += (
            "<tr><td><b>%s</b></td><td>%s / %sd</td><td>%s</td>"
            "<td>%s</td></tr>"
            % (esc(key), esc(tier.get("monthly_credits", "-")),
               esc(tier.get("period_days", "-")),
               esc(", ".join(tier.get("privileges", []))),
               esc(tier.get("copy", ""))))
    member_disclaimer = esc(member["compliance"]["disclaimer"])

    groups = suite_groups()
    total_suites = len(reconcile_all.SUITES)
    total_crit = sum(c for _l, _r, c in reconcile_all.SUITES)
    qual_rows = "".join(
        "<tr><td><b>%s</b></td><td>%d</td><td>%d</td></tr>"
        % (esc(name), cnt, crit)
        for name, (cnt, crit) in sorted(groups.items()))
    ev_path, ev_verdict, ev_stamp = latest_regression_evidence()
    if ev_verdict:
        ev_cls = "qok" if "RUNNER PASS" in ev_verdict else "qfail"
        ev_html = ("<p class=\"%s\">%s</p>"
                   "<p class=kv>last full run finished %s &middot; "
                   "evidence: qa/%s</p>"
                   % (ev_cls, esc(ev_verdict), esc(ev_stamp),
                      esc(os.path.basename(ev_path))))
    else:
        ev_html = ("<p class=fail>no reconcile-all evidence log on "
                   "disk (honest empty face, no fake PASS)</p>")

    page = """<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1">
<title>BigDomain Sandbox Front Door</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;
--dim:#8b949e;--acc:#58a6ff;--ok:#3fb950;--warn:#d29922}
*{box-sizing:border-box}body{margin:0;background:var(--bg);
color:var(--fg);font:15px/1.6 "Microsoft YaHei",system-ui,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:24px 16px 140px}
header{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
padding:8px 0 16px}
h1{font-size:22px;margin:0}h2{font-size:16px;margin:0 0 10px}
.badge{background:#1f6feb;color:#fff;font-size:12px;padding:2px 10px;
border-radius:10px} .sub{color:var(--dim);font-size:12px}
.card{background:var(--card);border:1px solid var(--line);
border-radius:10px;padding:16px 18px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,
1fr));gap:10px;margin-bottom:10px}
.kpi{background:#0d1117;border:1px solid var(--line);border-radius:8px;
padding:10px}.kpi b{display:block;font-size:24px;color:var(--acc)}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{border-top:1px solid var(--line);padding:6px 8px;text-align:left;
vertical-align:top}th{color:var(--dim);font-weight:600}
ul{margin:0;padding-left:18px}.proof{font-family:Consolas,monospace;
font-size:12.5px;max-height:340px;overflow:auto}
.ts{color:var(--dim);font-size:12px}
.fail{color:#f85149}
.qok{color:var(--ok);font-family:Consolas,monospace;font-size:13px}
.qfail{color:#f85149;font-family:Consolas,monospace;font-size:13px}
footer{position:fixed;bottom:0;left:0;right:0;background:#1a1f26;
border-top:2px solid var(--warn);padding:10px 16px;font-size:12.5px;
line-height:1.55;color:#e6edf3;z-index:9}
footer .badge{margin-right:8px}
.kv{color:var(--dim);font-size:13px;margin:4px 0}
</style></head><body><div class="wrap">
<header><h1>BigDomain Sandbox Front Door</h1>
<span class="badge">AIGC: __AI__</span>
<span class="sub">XL-16 / D-20260930-06 &middot; pure composition of
existing sandbox faces &middot; no new business face &middot; v0.4 adds
membership + quality cards</span></header>

<div class="card"><h2>City Live (read-only census snapshot)</h2>
<div class="grid">
<div class="kpi"><b>__POP__</b>residents</div>
<div class="kpi"><b>__DIST__</b>districts open</div>
<div class="kpi"><b>__VIS__</b>visitors today</div></div>
<p>__AMBIENT__</p><p class="kv">__TREND__</p>
<table><tr>__CITHEAD__</tr>__CITROWS__</table>
<h2 style="margin-top:14px">Recent city events</h2><ul>__EVENTS__</ul>
<p class="kv">snapshot as_of __ASOF__ &middot; source: world-public
sandbox stand-in (production = FluxVerse tick export, &le;20min
delay)</p></div>

<div class="card"><h2>Business-day Journey Proof (real ledger run)</h2>
__JOURNEY__
<p class="kv">Executed once at server start against the REAL dual-entry
ledger, content gate, props, venue and incentive faces. Exit code
verified; no canned output.</p></div>

<div class="card"><h2>Lobby Face (WebSocket sandbox)</h2>
<p class="kv">rooms: __ROOMS__ &middot; ws port __WSPORT__ &middot;
rate limit __RL__ msgs/__RLW__s (mute after __MUTE__ violations,
__MUTEW__s) &middot; heartbeat ping __PING__s / timeout __PTIME__s
&middot; text cap __MAXT__ chars &middot; sandbox entrance mock
(with real entrance gate in production)</p></div>

<div class="card"><h2>Pay Face (19.9 line, mock channels)</h2>
<table><tr><th>SKU</th><th>channel</th><th>price</th><th>copy</th></tr>
__SKUS__</table>
<p class="kv">Both channels run on explicit mock keys until CEO
physical items (merchant IDs) arrive; keys never enter git.
Conversion is one-way fiat-&gt;token into pool:share.</p></div>

<div class="card"><h2>Membership Face (tier table sandbox)</h2>
<table><tr><th>tier</th><th>credits / period</th><th>privileges</th>
<th>copy (real config text, [needs-CEO] notes included)</th></tr>
__TIERS__</table>
<p class=kv>__MEMDIS__</p>
<p class="kv">numbers are sandbox placeholders; all tier pricing stays
a [needs-CEO] approval face until the gate order arrives.</p></div>

<div class="card"><h2>Quality Face (suite inventory + last full
regression)</h2>
<div class="grid">
<div class="kpi"><b>__NSUITE__</b>suites</div>
<div class="kpi"><b>__NCRIT__</b>pre-registered criteria</div></div>
<table><tr><th>product dir</th><th>suites</th><th>criteria</th></tr>
__QUALROWS__</table>
__EVIDENCE__
<p class="kv">inventory imported at render time from
reconcile_all.SUITES; verdict read from the newest evidence log in
qa/ -- nothing canned.</p></div>

</div>
<footer><span class="badge">AIGC: __AI__</span>__WARN__<br>
__PAYWARN__</footer>
</body></html>"""

    cit_head = "".join("<th>%s</th>" % esc(k) for k in white)
    repl = {
        "__AI__": ai_label,
        "__POP__": esc(city.get("population", "-")),
        "__DIST__": esc(city.get("districts_open", "-")),
        "__VIS__": esc(city.get("visitors_today", "-")),
        "__AMBIENT__": esc(city.get("ambient", "")),
        "__TREND__": esc(city.get("trend_hint", "")),
        "__ASOF__": esc(world.get("as_of", "")),
        "__CITHEAD__": cit_head,
        "__CITROWS__": cit_rows,
        "__EVENTS__": evt_rows or "<li>-</li>",
        "__JOURNEY__": journey_html,
        "__ROOMS__": esc(", ".join(lobby.get("rooms", []))),
        "__WSPORT__": esc(lobby.get("default_port", "-")),
        "__RL__": esc(rl.get("max_messages", "-")),
        "__RLW__": esc(rl.get("window_seconds", "-")),
        "__MUTE__": esc(rl.get("mute_trigger_violations", "-")),
        "__MUTEW__": esc(rl.get("mute_seconds", "-")),
        "__PING__": esc(hb.get("ping_interval", "-")),
        "__PTIME__": esc(hb.get("ping_timeout", "-")),
        "__MAXT__": esc(lobby.get("max_text_len", "-")),
        "__SKUS__": sku_rows,
        "__TIERS__": tier_rows,
        "__MEMDIS__": member_disclaimer,
        "__NSUITE__": esc(total_suites),
        "__NCRIT__": esc(total_crit),
        "__QUALROWS__": qual_rows,
        "__EVIDENCE__": ev_html,
        "__WARN__": warn,
        "__PAYWARN__": pay_warn,
    }
    for key, val in repl.items():
        page = page.replace(key, val)
    return page.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = render()
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/healthz":
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"404 not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print("frontdoor serving http://%s:%d/ (journey_ok=%s)"
          % (HOST, PORT, JOURNEY_OK), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
