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

v0.5 (2026-10-02, R940b row of the R937 scope amendment, AC-W8):
mounts the minors guardian compliance card. The guard face runs live
in-process at render time with deterministic caller-supplied probe
inputs and the page shows its real readings (registered / guard
calls / refusals / day ledger), the WIRING_POINTS imported from the
guard module, and the compliance block: AIGC label, persistent
non-investment-advisory note, [needs-CEO] limit note, msgSecCheck
front-gate note, law citation. Pure composition: the guard module
is imported, never copied.

v0.6 (2026-10-02, R942 product round, AC-FD6a..f): mounts the M1
walkable-slice commerce-mount card -- the five visitor-journey
stations with their mount/consumer/judgement/gate rows and the three
first-launch hook copies (audit P-2026-10-02-02 M1 face, milestone
<=10-09). Every displayed string is loaded at render time from the
data file preview/m1-mount-nodes.json (extracted verbatim from the
preview page M1 sections, sync-gated by the wiring suite); this
source stays pure ASCII so no business copy can hide in code.

v0.7 (2026-10-02, R943 product round, AC-FD7a..f): mounts the
city-commerce-plan card -- the audit P-2026-10-02-02 L76 gap face
("BigCompute/BigDomain city commercial scheme = zero") answered by
the R849 spec docs/spec/city-commerce-plan-v0.md. Every displayed
string (four business layers, the 5-row audit-gap map, dual pricing
references with the [needs-CEO] verdict line, the M1..M4 milestone
bite-table, the compliance four-piece, the CEO-physicals blocked
notes) is loaded at render time from the data file
preview/city-commerce-plan-nodes.json extracted verbatim from that
spec, sync-gated by the wiring suite; source stays pure ASCII.

v0.8 (2026-10-02, R945 product round, AC-FD8a..f): mounts the
city-commerce dual-track SCENARIO card -- the runnable face of the
R850 model src/sandbox/citymodel/scenario.py (the v0.7 plan card
carries the canon; this card carries the computed numbers, closing
audit P-2026-10-02-02 L76 "pricing model = zero on file"). The REAL
model is imported and runs in-process at render time on the
caller-supplied probe params loaded from the data file
preview/citymodel-scenario-nodes.json: track A buyout+DLC monthly
projection, track B subscription-band decay/inflow, free-layer
funnel, buyout-price sensitivity grid, breakeven month, and the
deterministic ASCII report mounted byte-identical. Every displayed
number is computed by the model, never canned; scenario params are
labeled probe assumptions and the model computes without deciding
(fail-closed); pricing stays [needs-CEO] approval-only; Chinese
strings live only in the data file; source stays pure ASCII.
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
M1_JSON = os.path.join(ROOT, "preview", "m1-mount-nodes.json")
CC_JSON = os.path.join(ROOT, "preview", "city-commerce-plan-nodes.json")
CM_JSON = os.path.join(ROOT, "preview", "citymodel-scenario-nodes.json")
QA_DIR = os.path.join(ROOT, "qa")
WORLD = os.path.join(HERE, "lobby", "city_data", "world-public.json")
CITIZENS = os.path.join(HERE, "lobby", "city_data", "citizens-light.jsonl")
JOURNEY = os.path.join(HERE, "journey_demo.py")

MINORS_DIR = os.path.join(HERE, "minors")
if MINORS_DIR not in sys.path:
    sys.path.insert(0, MINORS_DIR)
import minors as minors_mod  # guard face module (reuse, no copy)

CITYMODEL_DIR = os.path.join(HERE, "citymodel")
if CITYMODEL_DIR not in sys.path:
    sys.path.insert(0, CITYMODEL_DIR)
import scenario as citymodel_mod  # dual-track model (reuse, no copy)

HOST, PORT = "127.0.0.1", 8093


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def esc(value):
    return html.escape(str(value), quote=True)


# Caller-supplied scenario probe params (single source: the data
# file). The card runs the REAL model on these; the model computes
# and never decides -- pricing stays a [needs-CEO] approval face.
CM_PROBE = load_json(CM_JSON)


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


# Deterministic probe fixtures for the minors guardian card. These
# are PROBE inputs (caller-supplied clock/limits, no wall time),
# not platform defaults: platform-side default limit VALUES stay
# [needs-CEO] and are never invented here (minors.py fail-closed).
PROBE = {
    "date": "2026-10-02",
    "window": (600, 900),
    "in_window_min": 700,
    "outside_min": 1200,
    "single_cent": 1990,
    "daily_cent": 4980,
    "buy_cent": 1990,
    "over_single_cent": 2990,
}


def minor_guard_probe():
    """Run the REAL MinorGuardFace in-process with the PROBE fixtures
    and return live readings (F3 law: every number below is computed
    by the guard at render time, never canned in this source)."""
    g = minors_mod.MinorGuardFace()
    g.register_resident("probe-adult", False)
    g.register_resident("probe-kid", True, guardian_id="probe-guardian")
    g.set_guardian_limits(
        "probe-guardian", "probe-kid",
        allowed_windows=[tuple(PROBE["window"])],
        single_cent=PROBE["single_cent"],
        daily_cent=PROBE["daily_cent"])
    readings = {"registered": len(g.residents_readout()), "calls": 0,
                "refusals": 0, "codes": [], "replays": 0}

    def call(fn, commit=False):
        readings["calls"] += 1
        try:
            out = fn()
            if commit and out.get("idempotent"):
                readings["replays"] += 1
        except minors_mod.GuardError as exc:
            readings["refusals"] += 1
            readings["codes"].append(exc.code)

    # sec.31 live ban + sec.24(3) marketing ban + sec.43 time windows
    call(lambda: g.check_live("probe-kid"))
    call(lambda: g.check_marketing("probe-kid"))
    call(lambda: g.check_time("probe-kid", PROBE["in_window_min"],
                              PROBE["date"]))
    call(lambda: g.check_time("probe-kid", PROBE["outside_min"],
                              PROBE["date"]))
    # sec.44 spend faces: one in-limit pass, one over-single refusal
    call(lambda: g.check_spend("probe-kid", PROBE["buy_cent"],
                               PROBE["date"]))
    call(lambda: g.check_spend("probe-kid", PROBE["over_single_cent"],
                               PROBE["date"]))
    # adults pass through the same gates (minors-only face law)
    call(lambda: g.check_live("probe-adult"))
    call(lambda: g.check_time("probe-adult", PROBE["outside_min"],
                              PROBE["date"]))
    call(lambda: g.check_spend("probe-adult", PROBE["buy_cent"],
                               PROBE["date"]))
    # commit face: same-ref replay records zero extra spend (AC-W7)
    for _ in range(2):
        call(lambda: g.record_spend("probe-kid", PROBE["buy_cent"],
                                    PROBE["date"], "probe-order-1"),
             commit=True)
    day = g.day_readout("probe-kid", PROBE["date"])
    readings["allowed"] = readings["calls"] - readings["refusals"]
    readings["spent_cent"] = day["spent_cent"]
    readings["events"] = len(day["events"])
    return readings


def citymodel_card():
    """Run the REAL dual-track scenario model in-process on the
    probe params (F3 law: every number below is computed by the
    model at render time, never canned in this source)."""
    d = CM_PROBE
    params, months = d["params"], int(d["months"])
    fa = citymodel_mod.project_track_a(params, months)
    fb = citymodel_mod.project_track_b(params, months)
    fu = citymodel_mod.funnel(params)
    grid = citymodel_mod.sensitivity_grid(params, months,
                                          d["price_steps"])
    be = citymodel_mod.breakeven_month(fa, d["fixed_cost"])
    report = citymodel_mod.render_report(params, months)
    return d, fa, fb, fu, grid, be, report


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

    mg = minor_guard_probe()
    mg_summary = esc(
        "probe summary: registered=%d calls=%d refusals=%d allowed=%d "
        "spent_cent=%d events=%d replays=%d"
        % (mg["registered"], mg["calls"], mg["refusals"], mg["allowed"],
           mg["spent_cent"], mg["events"], mg["replays"]))
    mg_codes = esc(", ".join(mg["codes"]) or "-")
    mg_limits = esc(
        "probe fixtures: window=%04d-%04d single_cent=%d daily_cent=%d "
        "(caller-supplied inputs; platform default limit VALUES stay "
        "[needs-CEO], unconfigured limits refuse billing)"
        % (PROBE["window"][0], PROBE["window"][1], PROBE["single_cent"],
           PROBE["daily_cent"]))
    mg_wp = esc(" ; ".join(minors_mod.WIRING_POINTS))
    mg_msgsec = ("CONTENT GATE: every UGC/text surface in this stack "
                 "keeps the msgSecCheck front gate (sandbox = wordlist "
                 "mock per P-47-3b; production wiring stays fail-closed "
                 "until the platform key arrives).")
    mg_compliance = esc(minors_mod.COMPLIANCE_HEADER.rstrip("\n"))

    m1 = load_json(M1_JSON)
    m1_rows = "".join(
        "<tr><td><b>%s</b><br><span class=kv>%s</span></td><td>%s</td>"
        "<td>%s</td><td>%s</td></tr>"
        % (esc(st["name"]), esc(st["role"]), esc(st["mount"]),
           esc(st["crit"]), esc(st["gate"]))
        for st in m1["stations"])
    m1_head = "".join("<th>%s</th>" % esc(h) for h in m1["table_headers"])
    m1_hooks = "".join(
        "<li><code>%s</code> &mdash; %s</li>"
        % (esc(h["code"]), esc(h["copy"])) for h in m1["hooks"])

    cc = load_json(CC_JSON)
    cc_lrows = "".join(
        "<tr><td><b>%s</b></td><td>%s</td></tr>"
        % (esc(l["name"]), esc(l["desc"])) for l in cc["layers"])
    cc_grows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (esc(g["gap"]), esc(g["answer"]), esc(g["status"]))
        for g in cc["gaps"])
    cc_ghead = "".join("<th>%s</th>" % esc(h)
                       for h in cc["gap_headers"])
    cc_prows = "".join(
        "<li><b>%s</b> &mdash; %s</li>"
        % (esc(p["ref"]), esc(p["note"])) for p in cc["pricing"])
    cc_mrows = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>"
        % (esc(m["m"]), esc(m["pre"]), esc(m["win"]))
        for m in cc["milestones"])
    cc_mhead = "".join("<th>%s</th>" % esc(h)
                       for h in cc["milestone_headers"])
    cc_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>"
        % (esc(c["name"]), esc(c["text"])) for c in cc["compliance"])
    cc_demo = "".join(
        "<p class=kv>%s</p>" % esc(b) for b in cc["demo_bullets"])
    cc_ws = "".join(
        "<p class=kv>%s</p>" % esc(b) for b in cc["workshop_bullets"])

    cmd, cm_fa, cm_fb, cm_fu, cm_grid, cm_be, cm_report = citymodel_card()
    cm_ta_rows = "".join(
        "<tr><td>%d</td><td>%d</td><td>%.2f</td><td>%.2f</td></tr>"
        % (r["month"], r["units"], r["gross"], r["cumulative"])
        for r in cm_fa["rows"])
    cm_tb_rows = "".join(
        "<tr><td>%d</td><td>%.2f</td><td>%.2f</td><td>%.2f</td></tr>"
        % (r["month"], r["subs_total"], r["mrr"], r["cumulative"])
        for r in cm_fb["rows"])
    cm_ta_head = "".join("<th>%s</th>" % esc(h)
                         for h in cmd["track_a_headers"])
    cm_tb_head = "".join("<th>%s</th>" % esc(h)
                         for h in cmd["track_b_headers"])
    cm_sens_rows = "".join(
        "<tr><td>%.2f</td><td>%.2f</td></tr>"
        % (g["buyout_price"], g["gross_total"]) for g in cm_grid)
    cm_sens_head = "".join("<th>%s</th>" % esc(h)
                           for h in cmd["sens_headers"])
    cm_be_txt = ("month %d" % cm_be) if cm_be else "none"
    cm_comb = round(cm_fa["gross_total"] + cm_fb["mrr_total"], 2)
    cm_funnel = esc(
        "funnel (probe): visitors=%(visitors).2f -> registered="
        "%(registered).2f -> paid=%(paid).2f" % cm_fu)
    cm_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>"
        % (esc(c["name"]), esc(c["text"])) for c in cmd["compliance"])

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
.mgcompliance{white-space:pre-wrap;background:#0d1117;border:1px
solid var(--line);border-radius:8px;padding:10px;font-size:12px;
color:var(--dim);margin:8px 0}
</style></head><body><div class="wrap">
<header><h1>BigDomain Sandbox Front Door</h1>
<span class="badge">AIGC: __AI__</span>
<span class="sub">XL-16 / D-20260930-06 &middot; pure composition of
existing sandbox faces &middot; no new business face &middot; v0.4
membership + quality cards &middot; v0.5 minors guardian card
(R940b) &middot; v0.6 M1 walk card (R942) &middot; v0.7 city
commerce plan card (R943) &middot; v0.8 city commerce scenario
card (R945)</span></header>

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

<div class="card"><h2>Minor Guardian Face (minor-protection wiring,
sandbox probe)</h2>
<div class="grid">
<div class="kpi"><b>__MG_REG__</b>residents probed</div>
<div class="kpi"><b>__MG_CALLS__</b>guard calls</div>
<div class="kpi"><b>__MG_REF__</b>refusals (fail-closed)</div></div>
<p class=kv>__MG_SUMMARY__</p>
<p class=kv>refusal codes seen: __MG_CODES__</p>
<p class=kv>__MG_LIMITS__</p>
<p class=kv>production wiring points (imported from the guard
module, single source): __MG_WP__</p>
<p class=kv>__MG_MSGSEC__</p>
<pre class=mgcompliance>__MG_COMPLIANCE__</pre>
<p class=kv>Readings above are executed at render time against the
REAL MinorGuardFace: R939 wired the three call sites (member / pay /
liveroom) opt-in fail-closed, R940 wired the pay grant commit face
(record_spend, exactly-once per order ref); this page mount closes
the R940b remainder of the declared row.</p></div>

<div class="card"><h2>__M1_TITLE__</h2>
<p class=kv>__M1_SOURCE__</p>
<div class="grid">
<div class="kpi"><b>__M1_N__</b>stations on the walk</div>
<div class="kpi"><b>__M1_NH__</b>first-launch hooks</div></div>
<table><tr>__M1_HEAD__</tr>__M1_ROWS__</table>
<h3 style="margin:14px 0 8px">__M1_HOOKTITLE__</h3><ul>__M1_HOOKS__</ul>
<p class=kv>__M1_HOOKNOTE__</p>
<p class=fail>__M1_GATE__</p>
<p class=kv>__M1_WALKNOTE__</p></div>

<div class="card"><h2>__CC_TITLE__</h2>
<p class=kv>__CC_SOURCE__</p>
<h3 style="margin:10px 0 8px">__CC_LTITLE__</h3>
<table>__CC_LROWS__</table>
<h3 style="margin:14px 0 8px">__CC_GTITLE__</h3>
<table><tr>__CC_GHEAD__</tr>__CC_GROWS__</table>
<h3 style="margin:14px 0 8px">__CC_PTITLE__</h3><ul>__CC_PROWS__</ul>
<p class=kv>__CC_PVERDICT__</p>
<h3 style="margin:14px 0 8px">__CC_DTITLE__</h3>__CC_DEMO__
<h3 style="margin:14px 0 8px">__CC_WTITLE__</h3>__CC_WS__
<h3 style="margin:14px 0 8px">__CC_MTITLE__</h3>
<table><tr>__CC_MHEAD__</tr>__CC_MROWS__</table>
<h3 style="margin:14px 0 8px">__CC_CTITLE__</h3><ul>__CC_COMPL__</ul>
<p class=fail>__CC_BLOCKED__</p>
<p class=kv>__CC_BLOCKED2__</p></div>

<div class="card"><h2>__CM_TITLE__</h2>
<p class=kv>__CM_SOURCE__</p>
<p class=kv>__CM_PROBENOTE__</p>
<div class="grid">
<div class="kpi"><b>__CM_A__</b>track A gross total CNY</div>
<div class="kpi"><b>__CM_B__</b>track B MRR total CNY</div>
<div class="kpi"><b>__CM_COMB__</b>combined gross CNY</div>
<div class="kpi"><b>__CM_BE__</b>track A breakeven</div></div>
<h3 style="margin:10px 0 8px">__CM_TA_TITLE__</h3>
<table><tr>__CM_TA_HEAD__</tr>__CM_TA_ROWS__</table>
<h3 style="margin:14px 0 8px">__CM_TB_TITLE__</h3>
<table><tr>__CM_TB_HEAD__</tr>__CM_TB_ROWS__</table>
<p class=kv>__CM_FUNNEL__</p>
<h3 style="margin:14px 0 8px">__CM_SENS_TITLE__</h3>
<table><tr>__CM_SENS_HEAD__</tr>__CM_SENS_ROWS__</table>
<h3 style="margin:14px 0 8px">__CM_REP_TITLE__</h3>
<pre class=proof>__CM_REPORT__</pre>
<h3 style="margin:14px 0 8px">__CM_COMPL_TITLE__</h3><ul>__CM_COMPL__</ul>
<p class=kv>__CM_TAIL__</p></div>

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
        "__MG_REG__": esc(mg["registered"]),
        "__MG_CALLS__": esc(mg["calls"]),
        "__MG_REF__": esc(mg["refusals"]),
        "__MG_SUMMARY__": mg_summary,
        "__MG_CODES__": mg_codes,
        "__MG_LIMITS__": mg_limits,
        "__MG_WP__": mg_wp,
        "__MG_MSGSEC__": mg_msgsec,
        "__MG_COMPLIANCE__": mg_compliance,
        "__M1_TITLE__": esc(m1["card_title"]),
        "__M1_SOURCE__": esc(m1["source_note"]),
        "__M1_N__": esc(len(m1["stations"])),
        "__M1_NH__": esc(len(m1["hooks"])),
        "__M1_HEAD__": m1_head,
        "__M1_ROWS__": m1_rows,
        "__M1_HOOKTITLE__": esc(m1["hooks_title"]),
        "__M1_HOOKS__": m1_hooks,
        "__M1_HOOKNOTE__": esc(m1["hooks_note"]),
        "__M1_GATE__": esc(m1["service_gate"]["note"]),
        "__M1_WALKNOTE__": esc(m1["walk_note"]),
        "__CC_TITLE__": esc(cc["card_title"]),
        "__CC_SOURCE__": esc(cc["source_note"]),
        "__CC_LTITLE__": esc(cc["layer_title"]),
        "__CC_LROWS__": cc_lrows,
        "__CC_GTITLE__": esc(cc["gap_title"]),
        "__CC_GHEAD__": cc_ghead,
        "__CC_GROWS__": cc_grows,
        "__CC_PTITLE__": esc(cc["pricing_title"]),
        "__CC_PROWS__": cc_prows,
        "__CC_PVERDICT__": esc(cc["pricing_verdict"]),
        "__CC_DTITLE__": esc(cc["demo_title"]),
        "__CC_DEMO__": cc_demo,
        "__CC_WTITLE__": esc(cc["workshop_title"]),
        "__CC_WS__": cc_ws,
        "__CC_MTITLE__": esc(cc["milestone_title"]),
        "__CC_MHEAD__": cc_mhead,
        "__CC_MROWS__": cc_mrows,
        "__CC_CTITLE__": esc(cc["compliance_title"]),
        "__CC_COMPL__": cc_compl,
        "__CC_BLOCKED__": esc(cc["blocked_note"]),
        "__CC_BLOCKED2__": esc(cc["blocked_note_2"]),
        "__CM_TITLE__": esc(cmd["card_title"]),
        "__CM_SOURCE__": esc(cmd["source_note"]),
        "__CM_PROBENOTE__": esc(cmd["probe_note"]),
        "__CM_A__": esc("%.2f" % cm_fa["gross_total"]),
        "__CM_B__": esc("%.2f" % cm_fb["mrr_total"]),
        "__CM_COMB__": esc("%.2f" % cm_comb),
        "__CM_BE__": esc(cm_be_txt),
        "__CM_TA_TITLE__": esc(cmd["track_a_title"]),
        "__CM_TA_HEAD__": cm_ta_head,
        "__CM_TA_ROWS__": cm_ta_rows,
        "__CM_TB_TITLE__": esc(cmd["track_b_title"]),
        "__CM_TB_HEAD__": cm_tb_head,
        "__CM_TB_ROWS__": cm_tb_rows,
        "__CM_FUNNEL__": cm_funnel,
        "__CM_SENS_TITLE__": esc(cmd["sens_title"]),
        "__CM_SENS_HEAD__": cm_sens_head,
        "__CM_SENS_ROWS__": cm_sens_rows,
        "__CM_REP_TITLE__": esc(cmd["report_title"]),
        "__CM_REPORT__": esc(cm_report.rstrip("\n")),
        "__CM_COMPL_TITLE__": esc(cmd["compliance_title"]),
        "__CM_COMPL__": cm_compl,
        "__CM_TAIL__": esc(cmd["tail_note"]),
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
