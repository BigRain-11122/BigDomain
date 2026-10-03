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

v0.9 (2026-10-02, R946 product round, AC-FD9a..f): mounts the
publishing-research card -- the remaining three faces of audit
P-2026-10-02-02 P2-9 ("Steam store page / demo strategy / workshop
ecosystem = zero on file" after the v0.7 plan card and the v0.8
scenario card closed the other two). The canon is the same-window
research piece docs/research/R-20261002-publishing-face-research.md;
every displayed string is loaded at render time from the data file
preview/publishing-face-nodes.json extracted verbatim from it
(sync-gated by the wiring suite); structural baseline research only
-- no invented price numbers, no web fetch this round; publish /
listing / gate decisions stay [needs-CEO] approval-only; source stays
pure ASCII.

v0.10 (2026-10-03, R965 product-first round, AC-FD10a..f): mounts the
token-ledger core face card -- the P-47-2 dual-entry ledger is the
company's economic core (15 ledger-domain suites, 100+ pre-registered
criteria) and until now the only core product with zero front-door
card. The REAL ledger product (src/sandbox/ledger/ledger.py) and the
REAL reconcile engine (reconcile.py check_lines) are imported, never
copied; the card runs an in-process probe ledger at render time:
census-bound onboarding, three-pool authorized mint (equity:auth
counterparty), fiat-side stand-in funding, the AC-L8 content-gate
reward face (unrecorded event refused / gate-passed event granted),
one spend closing the token loop back into pool:reserve (BLUEPRINT
5.4), live balances for all six accounts, and the eight-check
reconcile verdict computed on the probe database -- plus a tamper
control: a copy of the database with one entry amount bumped by +1
re-run through the same engine shows its FAIL lines honestly. Every
number is computed by the ledger at render time, never canned; the
sandbox keeps mock keys until CEO physical items arrive; pricing and
gate decisions stay [needs-CEO] approval-only.

v0.11 (2026-10-03, R968 product-first round, AC-FD11a..f): mounts the
UGC + msgSecCheck pipeline core face card -- the P-47-3 intake product
was the last of the five P-47 core faces with zero front-door presence
(lobby / ledger / pay / membership cards were already mounted). The
REAL pipeline (src/sandbox/ugc/pipeline.py, SecGate referenced from the
lobby product, L1 local wordlist per OH-20261002 adoption) is imported,
never copied; the card runs an in-process probe pipeline at render time
on a throwaway database: fail-closed entrance, the two-layer content
gate (L1 real local wordlist hit with the quota counter, then the L2
wordlist-mock gate incl. the non-advisory ban), gray-word human review
re-entry, six-line routing, honest noise triage, content-addressed
replay refusal plus the cross-actor duplicate_of marker, the
rule-template draft (zero LLM on server faces), the small-idea L0
self-decide adoption, and the landfall needs_ceo_review path where
adoption is refused without the CEO receipt and granted after it. The
export face is shown as its config contract only: the probe never
writes the product export dir (AC-U11) with throwaway rows. Probe
fixtures live in preview/ugc-pipeline-nodes.json; compliance strings
are loaded from the ugc config at runtime; this source stays ASCII.
"""

import contextlib
import glob
import html
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import reconcile_all  # suite inventory single source (reuse, no copy)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOBBY_CFG = os.path.join(HERE, "lobby", "config.json")
PAY_CFG = os.path.join(HERE, "pay", "config.json")
MEMBER_CFG = os.path.join(HERE, "member", "config.json")
LEDGER_CFG = os.path.join(HERE, "ledger", "config.json")
M1_JSON = os.path.join(ROOT, "preview", "m1-mount-nodes.json")
CC_JSON = os.path.join(ROOT, "preview", "city-commerce-plan-nodes.json")
CM_JSON = os.path.join(ROOT, "preview", "citymodel-scenario-nodes.json")
PB_JSON = os.path.join(ROOT, "preview", "publishing-face-nodes.json")
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

LEDGER_DIR = os.path.join(HERE, "ledger")
if LEDGER_DIR not in sys.path:
    sys.path.insert(0, LEDGER_DIR)
import ledger as ledger_mod       # token ledger product (reuse, no copy)
import reconcile as recon_mod     # ledger reconcile engine (reuse, no copy)
import props as props_mod         # city props/cosmetics face (reuse, no copy)
import incentive as incentive_mod  # creator incentive face (reuse, no copy)
import observation as observation_mod  # paid strategy observation (reuse, no copy)
import venue as venue_mod         # venue occupancy engine (reuse, no copy)
import studio as studio_mod       # studio onboarding annual-fee face (reuse, no copy)
import ads as ads_mod             # virtual-exhibition ad-slot face (reuse, no copy)

UGC_DIR = os.path.join(HERE, "ugc")
if UGC_DIR not in sys.path:
    sys.path.insert(0, UGC_DIR)
import pipeline as ugc_mod        # UGC intake pipeline product (reuse, no copy)

UGC_CFG = os.path.join(HERE, "ugc", "config.json")
UGC_JSON = os.path.join(ROOT, "preview", "ugc-pipeline-nodes.json")
WM_DIR = os.path.join(HERE, "watermark")
WM_DOC = os.path.join(ROOT, "docs", "spec",
                      "implicit-watermark-verify.md")
WM_PIPE = os.path.join(HERE, "ugc", "pipeline.py")

LIVEROOM_DIR = os.path.join(HERE, "liveroom")
LOBBY_DIR = os.path.join(HERE, "lobby")
for _d in (LIVEROOM_DIR, LOBBY_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)
import liveroom as liveroom_mod  # slow-live cart face (reuse, no copy)
import sec_gate as secgate_mod   # lobby wordlist gate (reuse family law)

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


def ledger_probe():
    """Run the REAL dual-entry token ledger in-process on caller-supplied
    probe fixtures and return live readings (F3 law: every number below
    is computed by the ledger at render time, never canned in this
    source). The probe walks the P-47-2 core face end to end: census-
    bound onboarding, authorized three-pool mint with the equity:auth
    counterparty, fiat-side stand-in funding, the AC-L8 content-gate
    reward face (unrecorded event refused, gate-passed event granted),
    and one spend closing the token loop back into pool:reserve
    (BLUEPRINT 5.4). The reconcile engine then runs its eight checks
    against the live probe database; a tamper control (database copy
    with one entry amount bumped +1) re-runs the same engine and its
    FAIL lines are reported honestly -- detection is computed, not
    claimed."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-ledger-")
    db = os.path.join(tmp, "ledger.db")
    led = ledger_mod.Ledger(db, cfg)
    score = int(cfg["actions"]["cocreate"]["score"])
    led.ensure_account("usr:probe-a", census_avatar_id="probe-a")
    led.ensure_account("usr:probe-b", census_avatar_id="probe-b")
    led.mint_to_pool("pool:reserve", 1000, "probe:mint:reserve")
    led.mint_to_pool("pool:share", 500, "probe:mint:share")
    led.mint_to_pool("pool:reward", 500, "probe:mint:reward")
    led.adjust([("pool:reserve", "debit", 120),
                ("usr:probe-a", "credit", 120)],
               "probe:fund:a",
               "frontdoor probe fiat-side stand-in funding")
    refused = None
    try:
        led.grant_reward("usr:probe-b", "cocreate",
                         "evt:probe:not-recorded", "event")
    except ledger_mod.LedgerError as exc:
        refused = exc.code
    led.record_gate_pass("evt:probe:gate:1")
    led.grant_reward("usr:probe-b", "cocreate",
                     "evt:probe:gate:1", "event")
    spend_tx = led.spend("usr:probe-a", 30, "probe:spend:1", "order",
                         memo="frontdoor probe privilege spend")
    led.close()
    accounts = ["usr:probe-a", "usr:probe-b", "pool:reserve",
                "pool:share", "pool:reward", "equity:auth"]
    conn = sqlite3.connect(db)
    balances = {a: int(conn.execute(
        "SELECT balance FROM ledger_accounts WHERE account_id = ?",
        (a,)).fetchone()[0]) for a in accounts}
    tx_n = int(conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    entry_n = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_entries").fetchone()[0])
    conn.close()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        recon_fails = recon_mod.check_lines(sqlite3.connect(db), cfg)
    recon_lines = [ln.strip() for ln in buf.getvalue().splitlines()
                   if ln.strip()]
    tampered = os.path.join(tmp, "tampered.db")
    shutil.copyfile(db, tampered)
    conn = sqlite3.connect(tampered)
    entry_id = conn.execute(
        "SELECT entry_id FROM ledger_entries WHERE direction = 'debit'"
        " ORDER BY entry_id LIMIT 1").fetchone()[0]
    conn.execute("UPDATE ledger_entries SET amount = amount + 1"
                 " WHERE entry_id = ?", (entry_id,))
    conn.commit()
    conn.close()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tamper_fails = recon_mod.check_lines(
            sqlite3.connect(tampered), cfg)
    tamper_lines = [ln.strip() for ln in buf.getvalue().splitlines()
                    if "FAIL" in ln]
    return {
        "balances": balances, "tx": tx_n, "entries": entry_n,
        "score": score, "refused": refused,
        "spend_tx": spend_tx, "recon_lines": recon_lines,
        "recon_fails": recon_fails, "tamper_fails": tamper_fails,
        "tamper_lines": tamper_lines,
        "issued": -balances["equity:auth"],
    }


def ugc_probe():
    """Run the REAL UGC + msgSecCheck intake pipeline (P-47-3 face)
    in-process on caller-supplied probe fixtures loaded from the data
    file (F3 law: every outcome below is computed by the pipeline at
    render time, never canned in this source). The probe walks the
    intake chain end to end on a throwaway database: fail-closed
    entrance, the two-layer content gate (L1 real local wordlist hit
    with the quota counter, then the L2 wordlist-mock gate incl. the
    non-advisory ban), gray-word human review re-entry, six-line
    routing, honest noise triage, the content-addressed replay refusal
    plus the cross-actor duplicate_of marker, the rule-template draft
    (zero LLM on server faces), the small-idea L0 self-decide
    adoption, and the landfall needs_ceo_review path where adoption
    is refused without the CEO receipt and granted after it. The
    export face is NOT executed: the probe database is throwaway and
    writing its rows into the product export dir (AC-U11 in-repo path)
    would pollute the product face -- the card shows the export
    contract from config instead."""
    cfg = load_json(UGC_CFG)
    fx = load_json(UGC_JSON)["probe"]
    a_main, a_gray, a_later = (fx["actor_main"], fx["actor_gray"],
                               fx["actor_later"])
    tmp = tempfile.mkdtemp(prefix="frontdoor-ugc-")
    pipe = ugc_mod.UGCPipeline(cfg, os.path.join(tmp, "ugc.db"))
    legs = []
    refusals = []

    def ok(action, outcome):
        legs.append({"n": len(legs) + 1, "action": action,
                     "outcome": outcome})

    def refuse_leg(action, fn):
        try:
            out = fn()  # design says refuse; accepted = honest display
            ok(action, "unexpectedly accepted: %s" % out)
        except ugc_mod.UGC.PipelineError as exc:
            refusals.append(str(exc.code))
            ok(action, "refused: %s" % exc)

    def submit(actor, content):
        return lambda: pipe.submit("direct", actor, content)

    refuse_leg("submit before any entrance grant (fail-closed)",
               submit(a_main, fx["content_pre_entrance"]))
    grant = pipe.grant_entrance_sandbox(a_main)
    pipe.grant_entrance_sandbox(a_gray)
    pipe.grant_entrance_sandbox(a_later)
    ok("grant sandbox entrance for the three probe residents",
       "entrance granted (mock=%s, ttl=%ss; production = P-47-4 payment"
       " receipt, account domain never self-served)"
       % (grant.get("mock"), grant.get("ttl_seconds")))
    refuse_leg("submit the L1 fixture (real local wordlist)",
               submit(a_main, fx["content_l1_wordlist"]))
    ok("read the L1 local-hit counter (msgSecCheck quota saved)",
       "local L1 hits = %d (caught locally before any platform call)"
       % pipe.local_hit_count)
    refuse_leg("submit the L2 fixture (advisory-ban wording the L1 dict"
               " does not carry)",
               submit(a_main, fx["content_l2_advisory"]))
    out_gray = pipe.submit("direct", a_gray, fx["content_gray"])
    ok("submit the gray-word fixture",
       "received evt=%s, gate=review, suspended (human desk; AC-U3 no"
       " verdict = suspended forever)" % out_gray.get("evt_id"))
    rev = pipe.review_verdict(out_gray["evt_id"], "pass",
                              reviewer="probe-reviewer")
    ok("review verdict: pass (the only exit from review)",
       "re-entered the flow: pooled=%s, line=%s (AC-U3)"
       % (rev.get("pooled"), rev.get("line")))
    clean = pipe.submit("direct", a_gray, fx["content_clean"])
    ok("submit the clean route fixture",
       "pooled=%s, line=%s (six-line router, config-driven)"
       % (clean.get("pooled"), clean.get("line")))
    noise = pipe.submit("direct", a_later, fx["content_noise"])
    ok("submit the noise fixture (too short)",
       "kept but never pooled: noise_reason=%s, pooled=%s (AC-U5 honest"
       " triage, the row survives)" % (noise.get("noise_reason"),
                                       noise.get("pooled")))
    refuse_leg("replay the same source + actor + content",
               submit(a_gray, fx["content_clean"]))
    dup = pipe.submit("direct", a_later, fx["content_clean"])
    ok("submit the same content from another resident",
       "pooled=%s, duplicate_of marker set=%s (AC-U6 cross-actor dedup)"
       % (dup.get("pooled"), bool(dup.get("duplicate_of"))))
    draft = pipe.draft(clean["evt_id"])
    ok("draft the clean item (rule template)",
       "producer=%s, ai_generated=%s (zero LLM on any server face)"
       % (draft.get("producer"), draft.get("ai_generated")))
    fr = pipe.final_review(clean["evt_id"])
    ok("final review the small idea",
       "state=%s, needs_ceo=%s (L0 self-decide path)"
       % (fr.get("state"), fr.get("needs_ceo")))
    ad = pipe.final_decide(clean["evt_id"], "adopt")
    ok("decide: adopt the small idea",
       "state=%s (L0 self-decide, AC-U9)" % ad.get("state"))
    land = pipe.submit("direct", a_later, fx["content_landfall"])
    ok("submit the landfall-scale fixture (over the length threshold)",
       "pooled=%s, line=%s" % (land.get("pooled"), land.get("line")))
    pipe.draft(land["evt_id"])
    fr2 = pipe.final_review(land["evt_id"])
    ok("draft + final review the landfall-scale item",
       "state=%s, needs_ceo=%s (CEO approval only, never auto-adopted)"
       % (fr2.get("state"), fr2.get("needs_ceo")))
    refuse_leg("decide: adopt the landfall item WITHOUT the CEO receipt",
               lambda: pipe.final_decide(land["evt_id"], "adopt"))
    pipe.record_ceo_decision(land["evt_id"], "approved")
    fin = pipe.final_decide(land["evt_id"], "adopt")
    ok("record the CEO receipt, then adopt",
       "state=%s with receipt (AC-U10 receipt at adoption)"
       % fin.get("state"))
    chron = pipe.chronicle_query()
    chron_states = {}
    for row in chron.get("items", []):
        key = str(row.get("state"))
        chron_states[key] = chron_states.get(key, 0) + 1
    ok("read the city chronicle",
       "terminal rows: %d (%s) -- every terminal state lands (AC-U12)"
       % (len(chron.get("items", [])),
          ", ".join("%s x%d" % kv
                    for kv in sorted(chron_states.items())) or "none"))
    pool = pipe.pool_query()
    pool_lines = {}
    for item in pool.get("items", []):
        key = str(item.get("line"))
        pool_lines[key] = pool_lines.get(key, 0) + 1
    ok("read the live pool",
       "pooled/drafted items: %d (%s); disclaimer persistent=%s"
       % (len(pool.get("items", [])),
          ", ".join("%s x%d" % kv
                    for kv in sorted(pool_lines.items())) or "none",
          pool.get("persistent")))
    readings = {
        "legs": legs, "refusals": refusals,
        "local_hits": pipe.local_hit_count,
        "pooled": len(pool.get("items", [])),
        "chronicle": len(chron.get("items", [])),
        "pool_lines": pool_lines, "chron_states": chron_states,
    }
    pipe.close()
    return readings


def liveroom_probe():
    """Run the REAL slow-live room conversion-piece face (P-47 cart
    face, R608 product, BLUEPRINT sec.4 "the live room carries the
    cart") in-process at render time on a throwaway database (F3 law:
    every reading below is computed by the product modules, never
    canned). Division of labor (D-20260924-08): the live account is a
    BigStream asset face and broadcast ops belong to BigCompute risk
    control -- this card shows only this company's in-room conversion
    supply face. Chain: the unattended open form is platform-banned
    and refused before any row exists (patrol-4 E2-3 hard law, coded
    fail-closed); an attended session opens only with a non-empty
    risk-control citation; anonymous cohort entry moves zero tokens;
    the danmaku front gate (SecGate wordlist, msgSecCheck-style
    fail-closed) rejects banned and advisory wording before any row
    lands and refuses anonymous viewers outright; a clean AI-flagged
    danmaku lands with the label; cart_convert books exactly ONE token
    spend for a census-registered viewer and binds the spend tx; a
    second conversion for the same viewer is rejected with zero
    charge; after close_session every writer face refuses; funnel
    counts match an independent SQL recount; the transcript keeps the
    config disclaimer first and last; the conversion audit binds a
    real debit entry per conversion. Raw tx ids contain timestamps
    and are never rendered (determinism); the audit face shows the
    bound-debit verification instead. Prices are caller-supplied probe
    values only -- 19.9-style pricing stays a [needs-CEO] approval
    face."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-liveroom-")
    led = None
    lf = None
    try:
        db = os.path.join(tmp, "ledger.db")
        led = ledger_mod.Ledger(db, cfg)
        gate = secgate_mod.SecGate(cfg["gate"]["forbidden_words"],
                                   cfg["gate"]["advisory_ban_words"])
        disc = str(cfg["token"]["disclaimer"])
        ai_label = str(cfg["token"]["ai_label_text"])
        lf = liveroom_mod.LiveRoomFace(led, gate, disc, ai_label)
        legs = []
        refusals = []

        def ok(action, outcome):
            legs.append({"n": len(legs) + 1, "action": action,
                         "outcome": outcome})

        def refuse_leg(action, fn):
            try:
                out = fn()  # design says refuse; accepted = honest show
                ok(action, "unexpectedly accepted: %s" % out)
            except secgate_mod.ContentRejectedError as exc:
                refusals.append("gate%d" % exc.gate)
                ok(action, "refused at gate %d (wordlist hit, row never"
                   " landed)" % exc.gate)
            except liveroom_mod.LiveRoomError as exc:
                refusals.append(str(exc.code))
                ok(action, "refused: %s" % exc.code)

        def spend_n():
            conn = sqlite3.connect(db)
            n = conn.execute("SELECT COUNT(*) FROM ledger_tx"
                             " WHERE type = 'spend'").fetchone()[0]
            conn.close()
            return int(n)

        # setup: authorize a reserve mint + fiat-side stand-in funding
        led.mint_to_pool("pool:reserve", 100000, "probe:mint:reserve")
        for avatar, amount in (("amy", 3000), ("ben", 2000), ("cyd", 1000)):
            led.ensure_account("usr:" + avatar, census_avatar_id=avatar)
            led.adjust([("pool:reserve", "debit", amount),
                        ("usr:" + avatar, "credit", amount)],
                       "probe:fund:" + avatar,
                       "frontdoor probe fiat-side stand-in funding")

        # -- hard law + attended open ---------------------------------
        refuse_leg("open session with attended=False (unattended"
                   " streaming form)",
                   lambda: lf.open_session("s-ghost", "room-cart", False,
                                           "bigcompute-risk-control-ref"))
        refuse_leg("open attended session with an EMPTY risk-control"
                   " citation",
                   lambda: lf.open_session("s-noref", "room-cart", True,
                                          "  "))
        conn = sqlite3.connect(db)
        sess0 = conn.execute("SELECT COUNT(*) FROM"
                             " live_sessions").fetchone()[0]
        conn.close()
        ok("count session rows after both refusals",
           "rows=%d (fail-closed: the banned form and the uncited"
           " form leave nothing behind)" % sess0)
        s = lf.open_session("s-front", "room-cart", True,
                            "bigcompute-risk-control-ref")
        ok("open attended session with the BigCompute risk-control"
           " citation",
           "attended=%s risk_control=%s (broadcast strategy belongs"
           " to BigCompute risk control, cited here, never decided"
           " here)" % (s["attended"], s["risk_control_ref"]))

        # -- anonymous cohort: zero token touch ------------------------
        tx0 = spend_n()
        for i in range(4):
            lf.viewer_enter("s-front", "anon-%d" % i)
        f0 = lf.funnel("s-front")
        tx1 = spend_n()
        ok("four anonymous viewers enter the cohort",
           "funnel entered=%d registered=%d converted=%d; spend-tx"
           " count %d==%d (watching is free, zero token touch)"
           % (f0["entered"], f0["registered"], f0["converted"], tx0, tx1))
        for viewer, avatar in (("anon-0", "amy"), ("anon-1", "ben"),
                               ("anon-2", "cyd")):
            lf.viewer_register("s-front", viewer, avatar)
        f1 = lf.funnel("s-front")
        ok("register three viewers to census avatars (city identity"
           " gate)",
           "funnel entered=%d registered=%d (census binding is the"
           " interaction + conversion gate)" % (f1["entered"],
                                                f1["registered"]))

        # -- danmaku front gate ----------------------------------------
        bad_word = str(cfg["gate"]["forbidden_words"][0])
        advisory_word = str(cfg["gate"]["advisory_ban_words"][0])
        refuse_leg("post danmaku with a banned word (gate 1)",
                   lambda: lf.post_danmaku("s-front", "anon-0",
                                           "hello " + bad_word))
        refuse_leg("post danmaku with an advisory-ban word (gate 2,"
                   " non-advisory law)",
                   lambda: lf.post_danmaku("s-front", "anon-0",
                                           "hello " + advisory_word))
        conn = sqlite3.connect(db)
        dm0 = conn.execute("SELECT COUNT(*) FROM"
                           " live_danmaku").fetchone()[0]
        conn.close()
        ok("count danmaku rows after both gate rejections",
           "rows=%d (both rejections landed nothing)" % dm0)
        refuse_leg("post danmaku as an anonymous (unregistered) viewer",
                   lambda: lf.post_danmaku("s-front", "anon-3",
                                           "clean hello"))
        dm_ok = lf.post_danmaku("s-front", "anon-0",
                                "clean hello city cart",
                                ai_generated=True)
        conn = sqlite3.connect(db)
        dm1 = conn.execute("SELECT COUNT(*) FROM"
                           " live_danmaku").fetchone()[0]
        conn.close()
        ok("post a clean AI-generated danmaku from a registered viewer",
           "ai_generated=%s, rows %d==%d+1 (the row lands with the"
           " label)" % (dm_ok["ai_generated"], dm1, dm0))

        # -- the conversion piece: exactly one spend -------------------
        bal0 = led.balance("usr:amy")["balance"]
        tx2 = spend_n()
        c1 = lf.cart_convert("s-front", "anon-0", 1990,
                             "order:cart-amy")
        bal1 = led.balance("usr:amy")["balance"]
        tx3 = spend_n()
        conn = sqlite3.connect(db)
        head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id ="
                            " ?", (c1["spend_tx_id"],)).fetchone()
        leg_row = conn.execute(
            "SELECT direction, amount FROM ledger_entries"
            " WHERE tx_id = ? AND account_id = ?",
            (c1["spend_tx_id"], "usr:amy")).fetchone()
        conn.close()
        ok("cart_convert for the registered viewer at the probe price"
           " 1990",
           "account=%s balance %d->%d (exact -1990); spend-tx %d->%d"
           " (+1); the bound tx is a real %s with a %s %d for the"
           " account" % (c1["account_id"], bal0, bal1, tx2, tx3,
                         head[0], leg_row[0], leg_row[1]))
        bal2 = led.balance("usr:amy")["balance"]
        refuse_leg("cart_convert the SAME viewer a second time in the"
                   " same session",
                   lambda: lf.cart_convert("s-front", "anon-0", 990,
                                           "order:cart-amy-2"))
        bal3 = led.balance("usr:amy")["balance"]
        ok("re-read the balance after the duplicate refusal",
           "%d==%d (the dup is rejected BEFORE the spend, a rejection"
           " never charges)" % (bal3, bal2))
        c2 = lf.cart_convert("s-front", "anon-1", 990, "order:cart-ben")
        ok("cart_convert a second REGISTERED viewer at probe price 990"
           " (one per viewer per session)",
           "account=%s price=%d (a different viewer may convert once)"
           % (c2["account_id"], c2["price"]))

        # -- close + post-close refuses ---------------------------------
        lf.close_session("s-front")
        refuse_leg("cart_convert after close_session",
                   lambda: lf.cart_convert("s-front", "anon-2", 500,
                                           "order:late-cart"))
        refuse_leg("post danmaku after close_session",
                   lambda: lf.post_danmaku("s-front", "anon-0",
                                          "after close"))

        # -- funnel vs independent recount ------------------------------
        f = lf.funnel("s-front")
        conn = sqlite3.connect(db)
        ent = conn.execute("SELECT COUNT(*) FROM live_cohort WHERE"
                           " session_id = 's-front'").fetchone()[0]
        reg = conn.execute("SELECT COUNT(*) FROM live_cohort WHERE"
                           " session_id = 's-front' AND"
                           " census_avatar_id IS NOT NULL").fetchone()[0]
        conv = conn.execute("SELECT COUNT(*), COALESCE(SUM(price), 0)"
                            " FROM live_conversions WHERE session_id ="
                            " 's-front'").fetchone()
        conn.close()
        ok("read the funnel vs an independent SQL recount",
           "entered=%d/%d registered=%d/%d converted=%d/%d"
           " conversion_total=%d/%d (derived from real rows, zero"
           " fabricated numbers)"
           % (f["entered"], ent, f["registered"], reg,
              f["converted"], conv[0], f["conversion_total"],
              int(conv[1])))

        # -- transcript compliance spine ---------------------------------
        lines = lf.transcript("s-front")
        ai_rows = [ln for ln in lines if "clean hello city cart" in ln]
        ok("read the session transcript (compliance spine)",
           "%d lines; first+last are the config disclaimer verbatim"
           " (%s); the AI danmaku row carries [%s]"
           % (len(lines),
             "yes" if (lines[0] == disc and lines[-1] == disc) else
             "NO", ai_label if ai_rows and
             ("[" + ai_label + "]") in ai_rows[0] else "-"))

        # -- conversion audit + isolation --------------------------------
        audit = lf.conversion_ledger("s-front")
        conn = sqlite3.connect(db)
        debit_sum = 0
        bound_ok = len(audit) == 2
        for row in audit:
            leg = conn.execute(
                "SELECT direction, amount FROM ledger_entries"
                " WHERE tx_id = ? AND account_id = ?",
                (row["bound_spend_tx"], row["account_id"])).fetchone()
            bound_ok = bound_ok and leg is not None \
                and leg[0] == "debit"
            debit_sum += leg[1] if leg else 0
        tx_all = spend_n()
        conn.close()
        ok("conversion audit + isolation law",
           "audit rows=%d each binding a real spend debit=%s; bound"
           " debit sum=%d == conversion_total=%d; whole-probe"
           " spend-tx=%d == conversion rows=%d (enter/register/"
           "danmaku/close moved zero tokens; the cart spend is the"
           " ONLY token touch)"
           % (len(audit), bound_ok, debit_sum, f["conversion_total"],
              tx_all, f["converted"]))
        lf.close()
        led.close()
        return {
            "legs": legs, "refusals": refusals,
            "entered": f["entered"], "registered": f["registered"],
            "converted": f["converted"],
            "conversion_total": f["conversion_total"],
            "transcript": lines, "audit_ok": bound_ok,
            "debit_sum": debit_sum, "spend_tx": tx_all,
            "disclaimer": disc, "ai_label": ai_label,
        }
    finally:
        if lf is not None:
            with contextlib.suppress(Exception):
                lf.close()
        if led is not None:
            with contextlib.suppress(Exception):
                led.close()
        shutil.rmtree(tmp, ignore_errors=True)


def props_probe():
    """Run the REAL city props/cosmetics inventory face (R599 product,
    BLUEPRINT sec.4.5 metaverse identity/props price lines) in-process
    at render time on a throwaway database (F3 law: every reading
    below is computed by the product modules, never canned). The
    counts-vs-tokens isolation law: a purchase touches the token
    ledger exactly once (one spend booking bound into the grant row);
    consuming credits and every refusal move zero tokens, and no verb
    anywhere in the module converts credits back into tokens or moves
    inventory between accounts (any such face is a P1 CEO approval
    item). Chain: a cosmetic buys as a permanent entitlement with
    exactly one spend; re-buying the held cosmetic is refused BEFORE
    the spend (a rejected buy never charges); prop credits buy and
    stack on re-purchase; consuming credits leaves the spend-tx count
    untouched; over-hold, cosmetic-consume, unknown-item, non-resident,
    kind-drift, empty-ref and zero-count faces are all refused
    fail-closed; a second resident holds his own entitlement (no
    cross-account verb exists); the inventory read shows entitlements,
    credit balances and the purchase provenance binding; the audit
    face verifies every inventory row against a real debit entry and
    the exact balance arithmetic. Raw tx ids are never rendered
    (determinism). Prices are caller-supplied probe values; catalog
    pricing stays a [needs-CEO] approval face."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-props-")
    led = None
    pf = None
    try:
        db = os.path.join(tmp, "ledger.db")
        led = ledger_mod.Ledger(db, cfg)
        pf = props_mod.PropsFace(led)
        legs = []
        refusals = []

        def ok(action, outcome):
            legs.append({"n": len(legs) + 1, "action": action,
                         "outcome": outcome})

        def refuse_leg(action, fn):
            try:
                out = fn()  # design says refuse; accepted = honest show
                ok(action, "unexpectedly accepted: %s" % out)
            except props_mod.PropError as exc:
                refusals.append(str(exc.code))
                ok(action, "refused: %s" % exc.code)

        def spend_n():
            conn = sqlite3.connect(db)
            n = conn.execute("SELECT COUNT(*) FROM ledger_tx"
                             " WHERE type = 'spend'").fetchone()[0]
            conn.close()
            return int(n)

        # setup: authorized reserve mint + fiat-side stand-in funding
        led.mint_to_pool("pool:reserve", 200000, "probe:mint:reserve")
        for avatar in ("amy", "ben"):
            led.ensure_account("usr:" + avatar, census_avatar_id=avatar)
            led.adjust([("pool:reserve", "debit", 5000),
                        ("usr:" + avatar, "credit", 5000)],
                       "probe:fund:" + avatar,
                       "frontdoor probe fiat-side stand-in funding")
        ok("authorize the reserve mint + fund two probe residents",
           "cosmetic probe price 2990, prop refills 500/300, credits"
           " 5+3 -- all caller-supplied probe values, never pricing"
           " decisions")

        # -- cosmetic: permanent entitlement, one spend, dup refused --
        tx0 = spend_n()
        bal0 = led.balance("usr:amy")["balance"]
        pf.buy_prop("usr:amy", "skin-neon", "cosmetic", 2990,
                    "order:skin-amy")
        bal1 = led.balance("usr:amy")["balance"]
        tx1 = spend_n()
        ok("resident amy buys the cosmetic (permanent entitlement)",
           "balance %d->%d (exact -2990); spend-tx %d->%d (+1); the"
           " grant row binds that spend as its purchase provenance"
           % (bal0, bal1, tx0, tx1))
        refuse_leg("amy re-buys the SAME cosmetic",
                   lambda: pf.buy_prop("usr:amy", "skin-neon",
                                       "cosmetic", 2990,
                                       "order:skin-amy-2"))
        bal2 = led.balance("usr:amy")["balance"]
        tx2 = spend_n()
        ok("re-read balance + spend count after the duplicate refusal",
           "%d==%d and %d==%d (the dup is rejected BEFORE the spend;"
           " a rejected buy never charges)" % (bal2, bal1, tx2, tx1))

        # -- prop credits: buy, stack, consume (zero token touch) -----
        p1 = pf.buy_prop("usr:amy", "boost-charge", "prop", 500,
                         "order:boost-amy", count=5)
        p2 = pf.buy_prop("usr:amy", "boost-charge", "prop", 300,
                         "order:boost-amy-2", count=3)
        ok("amy buys prop credits 5 then re-buys 3 (re-purchasable)",
           "credits %d then %d (stack on re-purchase; two spends"
           " booked, one per purchase)"
           % (p1["count_credits"], p2["count_credits"]))
        tx3 = spend_n()
        cu = pf.consume_prop("usr:amy", "boost-charge", 2)
        tx4 = spend_n()
        ok("amy consumes 2 credits",
           "credits %d->%d; spend-tx %d==%d (consuming credits never"
           " books a token tx -- the counts-vs-tokens isolation law)"
           % (cu["count_credits"] + 2, cu["count_credits"], tx4, tx3))
        refuse_leg("amy consumes more credits than held",
                   lambda: pf.consume_prop("usr:amy", "boost-charge",
                                           10))
        refuse_leg("amy consumes the cosmetic (permanent, not"
                   " consumable)",
                   lambda: pf.consume_prop("usr:amy", "skin-neon", 1))
        refuse_leg("amy consumes an item never purchased",
                   lambda: pf.consume_prop("usr:amy", "ghost-item", 1))

        # -- fail-closed purchase refusals ----------------------------
        refuse_leg("a pool account tries to buy (non-resident)",
                   lambda: pf.buy_prop("pool:reserve", "skin-neon",
                                       "cosmetic", 2990, "order:pool"))
        refuse_leg("kind drift: buy the held cosmetic as a prop",
                   lambda: pf.buy_prop("usr:amy", "skin-neon", "prop",
                                       300, "order:drift", count=1))
        refuse_leg("buy with an empty purchase ref",
                   lambda: pf.buy_prop("usr:amy", "boost-charge",
                                       "prop", 300, "   ", count=1))
        refuse_leg("buy prop credits with count=0",
                   lambda: pf.buy_prop("usr:amy", "boost-charge",
                                       "prop", 300, "order:zero",
                                       count=0))

        # -- second resident: own entitlement, no cross-account verb --
        pf.buy_prop("usr:ben", "skin-neon", "cosmetic", 2990,
                    "order:skin-ben")
        inv_b = pf.inventory("usr:ben")
        ok("resident ben buys the same cosmetic for himself",
           "ben holds his own entitlement (cosmetics=%s) --"
           " entitlements bind to the purchasing account and no verb"
           " moves inventory between accounts (any such face is a P1"
           " CEO approval item)" % inv_b["cosmetics"])

        # -- inventory read + audit + isolation ----------------------
        inv = pf.inventory("usr:amy")
        ok("read amy's inventory (entitlements + balances +"
           " provenance)",
           "cosmetics=%s; props=%s; every row carries its bound"
           " origin-purchase spend tx"
           % (inv["cosmetics"],
              ", ".join("%s x%d" % (p["item_id"], p["count_credits"])
                        for p in inv["props"])))
        conn = sqlite3.connect(db)
        spend_all = spend_n()
        landed_buys = 4
        bound_ok = True
        for _item, tx in inv["bound_spend_tx"].items():
            leg = conn.execute(
                "SELECT direction FROM ledger_entries"
                " WHERE tx_id = ? AND account_id = ?",
                (tx, "usr:amy")).fetchone()
            bound_ok = bound_ok and leg is not None \
                and leg[0] == "debit"
        total_debit = int(conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM ledger_entries"
            " WHERE account_id = ? AND direction = 'debit'",
            ("usr:amy",)).fetchone()[0])
        conn.close()
        bal_final = led.balance("usr:amy")["balance"]
        ok("inventory audit + isolation law",
           "amy rows=%d each binding a real origin-purchase spend"
           " debit=%s; amy total debits=%d; balance 5000 - %d = %d"
           " exact; whole-probe spend-tx=%d == landed purchases=%d"
           " (consume/refusal legs moved zero tokens; the buy spend"
           " is the ONLY token touch)"
           % (len(inv["bound_spend_tx"]), bound_ok, total_debit,
              total_debit, bal_final, spend_all, landed_buys))
        pf.close()
        led.close()
        return {
            "legs": legs, "refusals": refusals,
            "cosmetics": inv["cosmetics"], "props": inv["props"],
            "bound_ok": bound_ok, "total_debit": total_debit,
            "spend_tx": spend_all, "landed_buys": landed_buys,
        }
    finally:
        if pf is not None:
            with contextlib.suppress(Exception):
                pf.close()
        if led is not None:
            with contextlib.suppress(Exception):
                led.close()
        shutil.rmtree(tmp, ignore_errors=True)


def incentive_probe():
    """Run the REAL UGC creator incentive gradient allocator (R600
    product, BLUEPRINT sec.4 co-creation revenue-share ecosystem
    layer; design source docs/spec/incentive-agent-spec.md) in-process
    at render time on a throwaway database (F3 law: every reading
    below is computed by the product modules, never canned). The
    one-way share law: a settled window books each payout as exactly
    one share tx out of pool:share via the ledger public API; payouts
    are one-way grants and no reverse-conversion verb exists anywhere
    in the module. Chain: a pure decreasing-marginal gradient walk
    (anti-farm bands) -> a budget-binding window where the raw total
    overshoots the window budget and the deterministic pro-rata
    integer scaling lands the payout sum on the budget exactly with
    zero rounding loss -> a collar-binding window where a huge single
    contribution is capped by the per-creator collar -> the ledger
    join verifies every credit entry binds its settlement ref ->
    re-settling the same window is refused (idempotence) with zero
    ledger movement -> empty contributions, non-resident accounts,
    non-positive units and duplicate creators are all refused
    fail-closed. Gradient/collar/budget VALUES are sandbox-only
    probe params; real parameter adoption stays a P1 CEO
    approval-only item (AC-IG7: no incentive key ships in any
    config). Raw tx ids are never rendered (determinism)."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-incentive-")
    led = None
    face = None
    try:
        db = os.path.join(tmp, "ledger.db")
        led = ledger_mod.Ledger(db, cfg)
        face = incentive_mod.IncentiveFace(led)
        legs = []
        refusals = []

        def ok(action, outcome):
            legs.append({"n": len(legs) + 1, "action": action,
                         "outcome": outcome})

        def refuse_leg(action, fn):
            try:
                out = fn()  # design says refuse; accepted = honest show
                ok(action, "unexpectedly accepted: %s" % out)
            except incentive_mod.IncentiveError as exc:
                refusals.append(str(exc.code))
                ok(action, "refused: %s" % exc.code)

        def share_n():
            conn = sqlite3.connect(db)
            n = conn.execute(
                "SELECT COUNT(*) FROM ledger_tx WHERE type = 'share'"
            ).fetchone()[0]
            conn.close()
            return int(n)

        # setup: settlement-window funding mint + creator accounts
        led.mint_to_pool("pool:share", 2000, "probe:mint:share",
                         "settlement")
        for name in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + name, census_avatar_id=name)
        pool_before = led.balance("pool:share")["balance"]
        ok("authorize the settlement-window funding mint + register"
           " four probe creators",
           "pool:share seeded %d; gradient bands %s, collar %d,"
           " budget %d -- all sandbox-only probe params, real values"
           " stay a [needs-CEO] approval face"
           % (pool_before,
              incentive_mod.SANDBOX_PARAMS["bands"],
              incentive_mod.SANDBOX_PARAMS["collar"],
              incentive_mod.SANDBOX_PARAMS["budget"]))

        # -- pure gradient law (AC-IG1 face, decreasing marginal) ---
        seq_u = (0, 1, 3, 5, 6, 15, 16, 40, 100)
        seq_p = [incentive_mod.payout_for(u) for u in seq_u]
        marg = [incentive_mod.payout_for(u + 1)
                - incentive_mod.payout_for(u) for u in (2, 6, 20)]
        ok("walk the pure gradient function over probe units %s"
           % (seq_u,),
           "payouts %s -- monotone non-decreasing with the per-unit"
           " marginal falling band over band (%d -> %d -> %d): the"
           " anti-farm shape rewards early contribution and flattens"
           " farming" % (seq_p, marg[0], marg[1], marg[2]))

        # -- W1: budget-binding window, exact pro-rata landing --
        tx0 = share_n()
        paid_w1 = face.settle_window("W1", [
            ("usr:alice", 100),   # raw 270 -> collar 150
            ("usr:bob", 30),      # raw 130
            ("usr:carol", 30),    # raw 130
        ])
        pool_w1 = led.balance("pool:share")["balance"]
        ok("settle window W1 (raw 410 overshoots the budget 400)",
           "collar first, then deterministic pro-rata integer scaling"
           " lands %s (sum %d == budget exactly, zero rounding loss;"
           " remainder walks input order)" % (paid_w1, sum(
               a for _, a in paid_w1)))

        # -- W2: collar-binding window (budget not binding) ---------
        paid_w2 = face.settle_window("W2", [("usr:dave", 10 ** 6)])
        ok("settle window W2 with one 1,000,000-unit contribution",
           "payout %s -- the per-creator window collar caps the"
           " giant farm attempt at %d; a whale cannot drain the"
           " window" % (paid_w2,
                        incentive_mod.SANDBOX_PARAMS["collar"]))

        # -- ledger booking join (AC-IG4 face) ----------------------
        tx1 = share_n()
        total_all = sum(a for _, a in paid_w1) + sum(
            a for _, a in paid_w2)
        pool_after = led.balance("pool:share")["balance"]
        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT e.account_id, e.amount, t.ref FROM"
            " ledger_entries e JOIN ledger_tx t ON t.tx_id = e.tx_id"
            " WHERE t.ref LIKE 'incentive:%' AND e.direction ="
            " 'credit' ORDER BY t.ref").fetchall()
        conn.close()
        join_ok = (len(rows) == 4
                   and sum(r[1] for r in rows) == total_all
                   and all(r[2] == "incentive:%s:%s"
                           % (r[2].split(":")[1], r[0]) for r in rows))
        ok("audit the ledger booking join",
           "share-tx %d->%d (+4, one per payout); pool:share"
           " %d - %d = %d exact; %d credit rows each binding its"
           " settlement ref=%s (every payout is exactly one share"
           " booking -- the ledger owns all token arithmetic)"
           % (tx0, tx1, pool_before, total_all, pool_after,
              len(rows), join_ok))

        # -- idempotence (AC-IG5 face) + fail-closed refusals ------
        snap = {n: led.balance("usr:" + n)["balance"] for n in
                ("alice", "bob", "carol", "dave")}
        snap_pool = led.balance("pool:share")["balance"]
        refuse_leg("re-settle the SAME window W1",
                   lambda: face.settle_window(
                       "W1", [("usr:alice", 100)]))
        snap_ok = (all(led.balance("usr:" + n)["balance"] == snap[n]
                       for n in ("alice", "bob", "carol", "dave"))
                   and led.balance("pool:share")["balance"]
                   == snap_pool)
        ok("re-read all balances after the replay refusal",
           "unchanged=%s -- a settled window is idempotent, the"
           " replay moved zero tokens" % snap_ok)
        refuse_leg("settle a window with EMPTY contributions",
                   lambda: face.settle_window("W3", []))
        refuse_leg("a pool account tries to collect",
                   lambda: face.settle_window("W4", [
                       ("pool:reserve", 10)]))
        refuse_leg("contribute zero units",
                   lambda: face.settle_window("W5", [
                       ("usr:alice", 0)]))
        refuse_leg("the same creator twice in one window",
                   lambda: face.settle_window("W6", [
                       ("usr:alice", 5), ("usr:alice", 5)]))

        # -- one-way share law + zero-config face -------------------
        with open(os.path.join(HERE, "ledger", "incentive.py"),
                  "rb") as handle:
            src_bytes = handle.read()
        src = src_bytes.decode("ascii", errors="strict")
        banned = ("sell", "refund", "exchange", "withdraw",
                  "transfer", "mint")
        hits = [w for w in banned if w in src.lower()]
        with open(LEDGER_CFG, encoding="utf-8") as handle:
            shipped = json.load(handle)
        cfg_has_key = any("incentive" in str(k).lower()
                          for k in shipped)
        ok("isolation law + shipped-config check",
           "banned-verb hits in the module=%s (share is one-way, no"
           " reverse-conversion verb); incentive param keys in the"
           " shipped config=%s -- the sandbox defaults ship only in"
           " the module, real parameter adoption stays P1"
           " CEO-only" % (hits, cfg_has_key))
        face.close()
        led.close()
        return {
            "legs": legs, "refusals": refusals,
            "paid_w1": paid_w1, "paid_w2": paid_w2,
            "gradient": seq_p, "marginals": marg,
            "share_tx": tx1, "total_paid": total_all,
            "pool_before": pool_before, "pool_after": pool_after,
            "join_rows": len(rows), "join_ok": join_ok,
            "banned_hits": hits, "cfg_has_key": cfg_has_key,
        }
    finally:
        if face is not None:
            with contextlib.suppress(Exception):
                face.close()
        if led is not None:
            with contextlib.suppress(Exception):
                led.close()
        shutil.rmtree(tmp, ignore_errors=True)


def obs_probe():
    """Run the REAL paid strategy-observation face (R623 product,
    BLUEPRINT sec.4 C-end line 4: strategy co-creation paid
    observation, a core revenue line assigned to this company by
    D-20260924-10) in-process at render time on a throwaway database
    (F3 law: every reading below is computed by the product modules,
    never canned). The results-only boundary is structural: the
    registry has no source column and the register face has no
    source parameter at all, so no source code can ever leak.
    Chain: an unregistered strategy id is refused with zero charge
    -> a strategy is registered with a results summary only -> one
    single-strategy purchase books exactly one spend and the grant
    row binds it -> re-buying the same strategy is refused BEFORE
    the spend (a rejected buy never charges) -> observing without an
    entitlement is refused fail-closed -> a monthly pass buys one
    window and observes every registered strategy inside it ->
    re-buying the same month is refused -> the single grant is
    permanent across months while the pass covers exactly its own
    month -> pure reads move zero tokens and the observe view keys
    are exactly {strategy_id, summary, kind, tx}. Raw tx ids are
    never rendered (determinism). Prices are caller-supplied probe
    values mirroring the canon anchors (9.9 yuan single / 19.9 yuan
    monthly pass); real pricing stays a P1 CEO approval-only
    face."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-obs-")
    led = None
    face = None
    try:
        db = os.path.join(tmp, "ledger.db")
        led = ledger_mod.Ledger(db, cfg)
        face = observation_mod.ObservationFace(led)
        legs = []
        refusals = []

        def ok(action, outcome):
            legs.append({"n": len(legs) + 1, "action": action,
                         "outcome": outcome})

        def refuse_leg(action, fn):
            try:
                out = fn()  # design says refuse; accepted = honest show
                ok(action, "unexpectedly accepted: %s" % out)
            except observation_mod.ObservationError as exc:
                refusals.append(str(exc.code))
                ok(action, "refused: %s" % exc.code)

        def spend_n():
            conn = sqlite3.connect(db)
            n = conn.execute("SELECT COUNT(*) FROM ledger_tx"
                             " WHERE type = 'spend'").fetchone()[0]
            conn.close()
            return int(n)

        # setup: authorized reserve mint + fiat-side stand-in funding
        led.mint_to_pool("pool:reserve", 20000, "probe:mint:reserve")
        for avatar in ("amy", "ben", "carol"):
            led.ensure_account("usr:" + avatar, census_avatar_id=avatar)
            led.adjust([("pool:reserve", "debit", 3000),
                        ("usr:" + avatar, "credit", 3000)],
                       "probe:fund:" + avatar,
                       "frontdoor probe fiat-side stand-in funding")
        ok("authorize the reserve mint + fund three probe residents",
           "single-strategy observation probe price 990, monthly-pass"
           " probe price 1990 (canon anchors 9.9 / 19.9 CNY) --"
           " caller-supplied probe values, never pricing decisions")

        # -- results-only registration (structural, no source column) --
        reg = face.register_strategy(
            "strat-alpha", "usr:carol",
            {"backtest": "PASS", "sharpe": 1.8, "drawdown": "-7.2%"})
        conn = sqlite3.connect(db)
        cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(obs_strategies)").fetchall()]
        conn.close()
        ok("carol registers strat-alpha with a RESULTS summary",
           "registered=%s; obs_strategies columns=%s -- no source"
           " column and no source parameter exist anywhere on the"
           " register face, the results-only boundary is structural"
           % (reg["registered"], cols))

        # -- registration gate: unknown id refused, zero charge -------
        bal0 = led.balance("usr:amy")["balance"]
        refuse_leg("amy tries to buy an UNREGISTERED strategy id",
                   lambda: face.buy_single(
                       "usr:amy", "strat-ghost", 990, "order:ghost"))
        ok("re-read amy's balance after the unknown-id refusal",
           "%d==%d (an unregistered strategy is never purchasable;"
           " the refusal charged nothing)"
           % (led.balance("usr:amy")["balance"], bal0))

        # -- single purchase: one spend, bound into the grant row ----
        tx0 = spend_n()
        bal1 = led.balance("usr:amy")["balance"]
        face.buy_single("usr:amy", "strat-alpha", 990, "order:obs-amy")
        bal2 = led.balance("usr:amy")["balance"]
        tx1 = spend_n()
        ent1 = face.entitlements_view("usr:amy")
        ok("amy buys single observation of strat-alpha (permanent)",
           "balance %d->%d (exact -990); spend-tx %d->%d (+1); grant"
           " row binds that spend as its purchase provenance=%s"
           % (bal1, bal2, tx0, tx1,
              bool(ent1["grants"])
              and ent1["grants"][0]["spend_tx"] is not None))
        refuse_leg("amy re-buys the SAME strategy",
                   lambda: face.buy_single(
                       "usr:amy", "strat-alpha", 990, "order:obs-amy-2"))
        ok("re-read balance + spend count after the duplicate refusal",
           "%d==%d and %d==%d (the dup is rejected BEFORE the spend;"
           " a rejected buy never charges)"
           % (led.balance("usr:amy")["balance"], bal2, spend_n(), tx1))

        # -- fail-closed access gate ---------------------------------
        bal_b0 = led.balance("usr:ben")["balance"]
        refuse_leg("ben observes WITHOUT any entitlement",
                   lambda: face.observe(
                       "usr:ben", "strat-alpha", "2026-10"))
        ok("re-read ben's balance after the access refusal",
           "%d==%d (the access gate is fail-closed; a refused"
           " observation charges nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0))

        # -- monthly pass: one window, every registered strategy ------
        tx2 = spend_n()
        face.buy_pass("usr:ben", "2026-10", 1990, "order:pass-ben")
        tx3 = spend_n()
        view = face.observe("usr:ben", "strat-alpha", "2026-10")
        ok("ben buys the 2026-10 monthly pass and observes strat-alpha",
           "spend-tx %d->%d (+1); observe view keys=%s; kind=%s;"
           " summary=%s (results only, no source key can exist)"
           % (tx2, tx3, sorted(view.keys()), view["kind"],
              view["summary"]))
        refuse_leg("ben re-buys the SAME month pass",
                   lambda: face.buy_pass(
                       "usr:ben", "2026-10", 1990, "order:pass-ben-2"))

        # -- permanence vs window scope --------------------------------
        perm = face.can_observe("usr:amy", "strat-alpha", "2026-11")
        nxt = face.can_observe("usr:ben", "strat-alpha", "2026-11")
        ok("next month 2026-11 scope check",
           "amy single grant allowed=%s kind=%s (permanent, survives"
           " months); ben pass allowed=%s (a pass covers exactly its"
           " own month window)"
           % (perm["allowed"], perm["kind"], nxt["allowed"]))

        # -- pure reads move zero tokens --------------------------------
        tx4 = spend_n()
        face.can_observe("usr:ben", "strat-alpha", "2026-10")
        face.observe("usr:ben", "strat-alpha", "2026-10")
        face.entitlements_view("usr:ben")
        face.strategy_view("strat-alpha")
        tx5 = spend_n()
        ok("pure-read audit: can_observe/observe/views",
           "spend-tx %d==%d unchanged -- observe and can_observe are"
           " pure reads, zero token movement" % (tx4, tx5))

        # -- non-resident refusal + grant/debit audit ------------------
        refuse_leg("a pool account tries to buy observation",
                   lambda: face.buy_single(
                       "pool:reserve", "strat-alpha", 990,
                       "order:pool-buy"))
        ent_a = face.entitlements_view("usr:amy")
        ent_b = face.entitlements_view("usr:ben")
        sv = face.strategy_view("strat-alpha")
        grants_n = len(ent_a["grants"]) + len(ent_b["grants"])
        amy_final = led.balance("usr:amy")["balance"]
        ben_final = led.balance("usr:ben")["balance"]
        ok("audit the grant table against real debit entries",
           "%d grant rows (amy single + ben pass); spend-tx total"
           " %d; every grant row binds a real spend debit as its"
           " provenance; balances exact amy 3000-990=%d and ben"
           " 3000-1990=%d; strategy_view keys=%s (registry read"
           " face carries results only)"
           % (grants_n, tx5, amy_final, ben_final, sorted(sv.keys())))
        face.close()
        led.close()
        return {
            "legs": legs, "refusals": refusals,
            "spend_total": tx5, "grants": grants_n,
            "amy_bal": amy_final, "ben_bal": ben_final,
            "view_keys": sorted(view.keys()),
            "perm_allowed": perm["allowed"], "perm_kind": perm["kind"],
            "pass_next_allowed": nxt["allowed"],
            "cols": cols,
            "no_source_col": "source" not in [c.lower() for c in cols],
            "audit_ok": grants_n == tx5,
        }
    finally:
        if face is not None:
            with contextlib.suppress(Exception):
                face.close()
        if led is not None:
            with contextlib.suppress(Exception):
                led.close()
        shutil.rmtree(tmp, ignore_errors=True)


def st_probe():
    """Run the REAL studio-onboarding annual-fee face (R625 product,
    BLUEPRINT sec.4 B-side rows B1 game-studio 9,800 CNY/year + B2
    quant-studio / researcher 19,800 CNY/year, joint delivery in one
    registry) in-process at render time on a throwaway database
    (F3 law: every reading below is computed by the product modules,
    never canned). The seat rides the venue storefront exclusivity
    gate (venue = the R605 occupancy engine, referenced never
    rebuilt); every onboarding books exactly one token spend bound
    into the occupancy row, and the registry is immutable once
    written. Chain: mechanism registration is idempotent and refuses
    kind drift -> onboarding an unregistered studio is refused with
    zero charge -> one onboarding = one spend, window [year, year]
    -> the same studio-year replays as a refusal BEFORE the spend
    -> another account on the same studio-year is refused by the
    venue exclusivity gate -> renewal = onboarding a later year
    window (advance booking) -> two kinds are independent products
    and parallel same-kind studios are legal -> bad-args family
    refused -> canon three-benefit bundles -> profile reads bind the
    purchase spend and move zero tokens -> audit: spends equal
    onboardings, balances exact, pool conservation -> isolation law:
    zero banned verbs and zero row-mutation surface in the module
    source. Prices are caller-supplied probe values mirroring the
    canon anchors (9,800 / 19,800 CNY per year); real pricing stays
    a P1 CEO approval-only face."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-st-")
    led = None
    ven = None
    face = None
    try:
        db = os.path.join(tmp, "ledger.db")
        led = ledger_mod.Ledger(db, cfg)
        ven = venue_mod.VenueFace(led)
        face = studio_mod.StudioFace(led, ven)
        legs = []
        refusals = []

        def ok(action, outcome):
            legs.append({"n": len(legs) + 1, "action": action,
                         "outcome": outcome})

        def refuse_leg(action, fn):
            try:
                out = fn()  # design says refuse; accepted = honest show
                ok(action, "unexpectedly accepted: %s" % out)
            except studio_mod.StudioError as exc:
                refusals.append(str(exc.code))
                ok(action, "refused: %s" % exc.code)

        def spend_n():
            conn = sqlite3.connect(db)
            n = conn.execute("SELECT COUNT(*) FROM ledger_tx"
                             " WHERE type = 'spend'").fetchone()[0]
            conn.close()
            return int(n)

        # setup: authorized reserve mint + fiat-side stand-in funding
        led.mint_to_pool("pool:reserve", 200000, "probe:mint:reserve",
                         "settlement")
        for avatar in ("amy", "ben", "carol"):
            led.ensure_account("usr:" + avatar, census_avatar_id=avatar)
            led.adjust([("pool:reserve", "debit", 50000),
                        ("usr:" + avatar, "credit", 50000)],
                       "probe:fund:" + avatar,
                       "frontdoor probe fiat-side stand-in funding")
        ok("authorize the reserve mint + fund three probe residents",
           "game-studio probe price 9800, quant-studio probe price"
           " 19800 per year window (canon anchors B1 9,800 / B2"
           " 19,800 CNY per year) -- caller-supplied probe values,"
           " never pricing decisions")

        # -- mechanism registration: idempotent + kind-drift gate ---
        reg_g = face.register_studio("studio:pixelforge",
                                     "game_studio")
        reg_i = face.register_studio("studio:pixelforge",
                                     "game_studio")
        refuse_leg("re-register pixelforge under a DIFFERENT kind",
                   lambda: face.register_studio(
                       "studio:pixelforge", "quant_studio"))
        reg_q = face.register_studio("studio:quantworks",
                                     "quant_studio")
        with open(studio_mod.__file__, encoding="utf-8") as fh:
            st_src = fh.read()
        conn = sqlite3.connect(db)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name LIKE 'studio%'").fetchall()]
        conn.close()
        ok("register the two studios under their kinds",
           "first=%s idempotent=%s quant=%s; registry tables=%s --"
           " one small registry only, the module source has zero"
           " direct INSERT INTO venue_occupancy (the venue stays the"
           " engine, this face is the API)"
           % (reg_g["idempotent"] is False,
              reg_i["idempotent"] is True,
              reg_q["idempotent"] is False, tables))

        # -- registry gate: unknown studio, zero charge -------------
        bal_b0 = led.balance("usr:ben")["balance"]
        refuse_leg("ben tries to onboard an UNREGISTERED studio",
                   lambda: face.onboard_studio(
                       "usr:ben", "studio:ghostworks", 26, 9800,
                       "order:st-ghost"))
        ok("re-read ben's balance after the unknown-studio refusal",
           "%d==%d (an unregistered studio is never onboardable; the"
           " refusal charged nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0))

        # -- one onboarding: one spend bound into the occupancy row --
        tx0 = spend_n()
        bal_a1 = led.balance("usr:amy")["balance"]
        r1 = face.onboard_studio("usr:amy", "studio:pixelforge", 26,
                                 9800, "order:st-amy-26")
        bal_a2 = led.balance("usr:amy")["balance"]
        tx1 = spend_n()
        occ = ven.occupancy_ledger("studio:pixelforge")
        ok("amy onboards pixelforge for year-window 26",
           "balance %d->%d (exact -9800); spend-tx %d->%d (+1);"
           " window=%s; occupancy rows=%d, bound spend provenance=%s"
           % (bal_a1, bal_a2, tx0, tx1, r1["window"], len(occ),
              bool(occ) and occ[0]["bound_spend_tx"] is not None))

        # -- same studio-year replay refused BEFORE the spend --------
        refuse_leg("amy replays the SAME studio-year window",
                   lambda: face.onboard_studio(
                       "usr:amy", "studio:pixelforge", 26, 9800,
                       "order:st-amy-26-again"))
        ok("re-read balance + spend count after the replay refusal",
           "%d==%d and %d==%d (the replay is rejected BEFORE the"
           " spend; a rejected onboarding never charges)"
           % (led.balance("usr:amy")["balance"], bal_a2,
              spend_n(), tx1))

        # -- venue exclusivity: another account, same studio-year ----
        refuse_leg("ben hits the SAME studio-year held by amy",
                   lambda: face.onboard_studio(
                       "usr:ben", "studio:pixelforge", 26, 9800,
                       "order:st-ben-26"))
        ok("re-read ben's balance after the exclusivity refusal",
           "%d==%d (the venue storefront gate is single-tenant per"
           " window; the refusal charged nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0))

        # -- renewal = a later year window (advance booking) ---------
        tx2 = spend_n()
        bal_a3 = led.balance("usr:amy")["balance"]
        r2 = face.onboard_studio("usr:amy", "studio:pixelforge", 27,
                                 9800, "order:st-amy-27")
        tx3 = spend_n()
        tenant26 = face.studio_tenant("studio:pixelforge", 26)
        tenant27 = face.studio_tenant("studio:pixelforge", 27)
        tenant28 = face.studio_tenant("studio:pixelforge", 28)
        ok("amy renews pixelforge for year-window 27 in advance",
           "balance %d->%d (exact -9800); spend-tx %d->%d (+1);"
           " window=%s; tenants year26=%s year27=%s year28=%s (each"
           " year window is its own seat, 28 is open)"
           % (bal_a3, led.balance("usr:amy")["balance"], tx2, tx3,
              r2["window"], tenant26, tenant27, tenant28))

        # -- two kinds independent + parallel same-kind studio -------
        tx4 = spend_n()
        bal_a4 = led.balance("usr:amy")["balance"]
        rq = face.onboard_studio("usr:amy", "studio:quantworks", 26,
                                 19800, "order:st-amy-q26")
        tx5 = spend_n()
        face.register_studio("studio:indienest", "game_studio")
        tx6 = spend_n()
        bal_c1 = led.balance("usr:carol")["balance"]
        rc = face.onboard_studio("usr:carol", "studio:indienest", 26,
                                 9800, "order:st-carol-26")
        tx7 = spend_n()
        ok("kinds are independent: amy holds game + quant seats the"
           " same year, carol onboards a parallel game studio",
           "amy balance %d->%d (exact -19800, quant seat legal next"
           " to the game seat); carol balance %d->%d (exact -9800,"
           " second game studio legal); spend-tx %d->%d->%d (one per"
           " seat); kinds=%s/%s"
           % (bal_a4, led.balance("usr:amy")["balance"], bal_c1,
              led.balance("usr:carol")["balance"], tx4, tx5, tx7,
              rq["st_kind"], rc["st_kind"]))

        # -- bad-args family, all zero side effects ------------------
        refuse_leg("a corp: account tries to onboard",
                   lambda: face.onboard_studio(
                       "corp:acme", "studio:pixelforge", 26, 9800,
                       "order:st-corp"))
        refuse_leg("zero-price onboarding is refused",
                   lambda: face.onboard_studio(
                       "usr:ben", "studio:pixelforge", 28, 0,
                       "order:st-zero"))
        refuse_leg("a negative year window is refused",
                   lambda: face.onboard_studio(
                       "usr:ben", "studio:pixelforge", -1, 9800,
                       "order:st-neg"))
        refuse_leg("an empty onboarding ref is refused",
                   lambda: face.onboard_studio(
                       "usr:ben", "studio:pixelforge", 28, 9800,
                       "   "))
        ok("bad-args audit: four refusals, ben's balance flat",
           "%d==%d (owners are usr:* only, price must be int > 0,"
           " year must be int >= 0, ref required -- every rejected"
           " onboarding charges nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0))

        # -- canon benefit bundles, read at runtime -------------------
        ben_g = face.studio_benefits("studio:pixelforge")
        ben_q = face.studio_benefits("studio:quantworks")
        ok("read the canon three-benefit bundles B1 / B2",
           "B1 game bundle=%s; B2 quant bundle=%s (BLUEPRINT sec.4"
           " B1/B2 rows, static per kind, derived at runtime)"
           % (ben_g["benefits"], ben_q["benefits"]))

        # -- profile read faces: bound spends, zero token movement ---
        tx8 = spend_n()
        prof_a = face.studio_profile("usr:amy", 26)
        prof_b = face.studio_profile("usr:ben", 26)
        prof_a28 = face.studio_profile("usr:amy", 28)
        face.studio_tenant("studio:pixelforge", 26)
        tx9 = spend_n()
        a_ids = sorted(s["studio_id"] for s in prof_a["subscriptions"])
        ok("profile reads are pure and bind the purchase spends",
           "spend-tx %d==%d unchanged -- profile/tenant reads move"
           " zero tokens; amy@26 subscriptions=%s (every row carries"
           " spend_tx=%s and year=26); ben@26=%s (no seat, no"
           " leak); amy@28=%s (window scope only)"
           % (tx8, tx9, a_ids,
              all(s["spend_tx"] for s in prof_a["subscriptions"]),
              [s["studio_id"] for s in prof_b["subscriptions"]],
              [s["studio_id"] for s in prof_a28["subscriptions"]]))

        # -- audit: spends equal onboardings, balances exact ---------
        tx_total = spend_n()
        onboardings = 4
        amy_final = led.balance("usr:amy")["balance"]
        ben_final = led.balance("usr:ben")["balance"]
        carol_final = led.balance("usr:carol")["balance"]
        pool_final = led.balance("pool:reserve")["balance"]
        conn = sqlite3.connect(db)
        reg_rows = conn.execute(
            "SELECT COUNT(*) FROM studio_products").fetchone()[0]
        occ_bound = conn.execute(
            "SELECT COUNT(*) FROM venue_occupancy WHERE"
            " bound_spend_tx IS NOT NULL").fetchone()[0]
        conn.close()
        ok("audit the seats against real debit entries",
           "spend-tx total %d == onboardings %d; every one of the"
           " %d occupancy rows binds a real spend debit as its"
           " provenance; balances exact: amy 50000-9800-9800-19800"
           "=%d, ben 50000==%d untouched, carol 50000-9800=%d;"
           " pool:reserve %d (conservation); registry rows=%d"
           % (tx_total, onboardings, occ_bound, amy_final,
              ben_final, carol_final, pool_final, reg_rows))

        # -- isolation law: module source, structural -----------------
        banned = [w for w in ("refund", "withdraw", "convert",
                              "transfer") if w in st_src]
        no_direct_write = ("INSERT INTO venue_occupancy" not in st_src
                           and "UPDATE" not in st_src)
        ok("isolation law audit on the REAL module source",
           "banned verbs found=%s; zero direct INSERT INTO"
           " venue_occupancy and zero UPDATE surface=%s (the registry"
           " is immutable once written, cancellation or fee reversal"
           " of any kind stays a P1 [needs-CEO] approval face, and"
           " no verb turns a subscription back into tokens)"
           % (banned or "none", no_direct_write))
        face.close()
        ven.close()
        led.close()
        return {
            "legs": legs, "refusals": refusals,
            "spend_total": tx_total, "onboards": onboardings,
            "ben_g": ben_g["benefits"], "ben_q": ben_q["benefits"],
            "amy_bal": amy_final, "ben_bal": ben_final,
            "carol_bal": carol_final, "reg_rows": reg_rows,
            "occ_bound": occ_bound,
            "banned": banned, "no_mutation": no_direct_write,
            "tenant26": tenant26, "tenant27": tenant27,
            "audit_ok": tx_total == onboardings
            and ben_final == 50000 and amy_final == 10600
            and carol_final == 40200,
        }
    finally:
        if face is not None:
            with contextlib.suppress(Exception):
                face.close()
        if ven is not None:
            with contextlib.suppress(Exception):
                ven.close()
        if led is not None:
            with contextlib.suppress(Exception):
                led.close()
        shutil.rmtree(tmp, ignore_errors=True)


def ads_probe():
    """Run the REAL virtual-exhibition ad-slot schedule face (R622
    product, BLUEPRINT sec.4 B3 ad-slot price row: QUANT giant-screen
    carousel 2000 CNY/week, building naming rights 10000 CNY/year
    for street or metro names, lobby splash ad 5000 CNY/week)
    in-process at render time on a throwaway database (F3 law: every
    reading below is computed by the product modules, never canned).
    The venue stays the occupancy engine (R605, referenced never
    rebuilt): this face owns one small ad_units registry and every
    booking goes through the VenueFace public API, landing as an
    occupancy row bound to exactly one token spend. Chain: mechanism
    registration under the three product kinds is idempotent and
    refuses kind drift -> an unregistered unit is refused with zero
    charge -> one naming booking = one spend -> the same unit-window
    replay is refused BEFORE the spend -> another account on the
    same exclusive unit-window is refused by the venue exclusivity
    gate -> the splash books a two-window span -> the carousel
    capacity gate fills its three rotation slots then refuses the
    fourth -> an off-peak carousel span books legally -> an advance
    naming booking at a future window -> bad-args family refused ->
    lineup / holder / board read faces move zero tokens -> audit:
    spends equal bookings, balances exact, pool conservation ->
    isolation law: zero banned verbs and zero row-mutation surface
    in the module source. Prices are caller-supplied probe values
    mirroring the canon anchors (2000 / 10000 / 5000 CNY per
    window); real pricing stays a P1 CEO approval-only face."""
    cfg = load_json(LEDGER_CFG)
    tmp = tempfile.mkdtemp(prefix="frontdoor-ad-")
    led = None
    ven = None
    face = None
    try:
        db = os.path.join(tmp, "ledger.db")
        led = ledger_mod.Ledger(db, cfg)
        ven = venue_mod.VenueFace(led)
        face = ads_mod.AdsFace(led, ven)
        legs = []
        refusals = []

        def ok(action, outcome):
            legs.append({"n": len(legs) + 1, "action": action,
                         "outcome": outcome})

        def refuse_leg(action, fn):
            try:
                out = fn()  # design says refuse; accepted = honest show
                ok(action, "unexpectedly accepted: %s" % out)
            except ads_mod.AdsError as exc:
                refusals.append(str(exc.code))
                ok(action, "refused: %s" % exc.code)

        def spend_n():
            conn = sqlite3.connect(db)
            n = conn.execute("SELECT COUNT(*) FROM ledger_tx"
                             " WHERE type = 'spend'").fetchone()[0]
            conn.close()
            return int(n)

        # setup: authorized reserve mint + fiat-side stand-in funding
        led.mint_to_pool("pool:reserve", 240000, "probe:mint:reserve",
                         "settlement")
        for avatar in ("amy", "ben", "carol", "dave"):
            led.ensure_account("usr:" + avatar, census_avatar_id=avatar)
            led.adjust([("pool:reserve", "debit", 50000),
                        ("usr:" + avatar, "credit", 50000)],
                       "probe:fund:" + avatar,
                       "frontdoor probe fiat-side stand-in funding")
        ok("authorize the reserve mint + fund four probe residents",
           "probe per-window prices mirror the B3 canon anchors:"
           " carousel 2000 / naming 10000 / splash 5000 CNY per"
           " window -- caller-supplied probe values, never pricing"
           " decisions")

        # -- mechanism registration: three kinds, idempotent, drift --
        reg_s = face.register_ad_unit("screen:quant-main",
                                      "quant_screen_carousel",
                                      rotation_slots=3)
        reg_s2 = face.register_ad_unit("screen:quant-main",
                                        "quant_screen_carousel",
                                        rotation_slots=3)
        refuse_leg("re-register the screen under a DIFFERENT kind",
                   lambda: face.register_ad_unit(
                       "screen:quant-main", "lobby_splash"))
        reg_n = face.register_ad_unit("naming:harbor-gate",
                                      "building_naming")
        reg_n2 = face.register_ad_unit("naming:metro-l4",
                                       "building_naming")
        reg_l = face.register_ad_unit("splash:lobby", "lobby_splash")
        with open(ads_mod.__file__, encoding="utf-8") as fh:
            ad_src = fh.read()
        conn = sqlite3.connect(db)
        ad_tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name LIKE 'ad_%'").fetchall()]
        conn.close()
        ok("register four ad units under the three product kinds",
           "screen first=%s idempotent=%s; naming=%s/%s splash=%s;"
           " ads-owned tables=%s -- one small registry only, the"
           " module source has zero direct INSERT INTO"
           " venue_occupancy (the venue stays the engine, this"
           " face is the API)"
           % (reg_s["idempotent"] is False,
              reg_s2["idempotent"] is True,
              reg_n["idempotent"] is False,
              reg_n2["idempotent"] is False,
              reg_l["idempotent"] is False, ad_tables))

        # -- registry gate: unknown unit, zero charge ---------------
        bal_b0 = led.balance("usr:ben")["balance"]
        refuse_leg("ben tries to book an UNREGISTERED ad unit",
                   lambda: face.book("usr:ben", "screen:ghost", 50, 1,
                                     2000, "order:ad-ghost"))
        ok("re-read ben's balance after the unknown-unit refusal",
           "%d==%d (an unregistered unit is never bookable; the"
           " refusal charged nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0))

        # -- one naming booking: one spend bound into the occupancy --
        tx0 = spend_n()
        bal_a1 = led.balance("usr:amy")["balance"]
        r1 = face.book("usr:amy", "naming:harbor-gate", 26, 1, 10000,
                       "order:ad-amy-26")
        bal_a2 = led.balance("usr:amy")["balance"]
        tx1 = spend_n()
        ok("amy buys the harbor-gate naming right for year-window 26",
           "balance %d->%d (exact -10000); spend-tx %d->%d (+1);"
           " span=%d..%d; occ row #%d bound to that spend as its"
           " provenance; kind=%s"
           % (bal_a1, bal_a2, tx0, tx1, r1["start_window"],
              r1["end_window"], r1["occ_id"], r1["ad_kind"]))

        # -- same unit-window replay refused BEFORE the spend ---------
        refuse_leg("amy replays the SAME naming unit-window",
                   lambda: face.book(
                       "usr:amy", "naming:harbor-gate", 26, 1, 10000,
                       "order:ad-amy-26-again"))
        ok("re-read balance + spend count after the replay refusal",
           "%d==%d and %d==%d (the replay is rejected BEFORE the"
           " spend; a rejected booking never charges)"
           % (led.balance("usr:amy")["balance"], bal_a2,
              spend_n(), tx1))

        # -- venue exclusivity: another account, same unit-window -----
        refuse_leg("ben hits the SAME naming window held by amy",
                   lambda: face.book(
                       "usr:ben", "naming:harbor-gate", 26, 1, 10000,
                       "order:ad-ben-26"))
        ok("re-read ben's balance after the exclusivity refusal",
           "%d==%d (naming and splash are exclusive units, at most"
           " one holder per window; the refusal charged nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0))

        # -- splash: a two-window span, exact fee --------------------
        tx2 = spend_n()
        bal_c1 = led.balance("usr:carol")["balance"]
        r2 = face.book("usr:carol", "splash:lobby", 40, 2, 5000,
                       "order:ad-carol-splash")
        bal_c2 = led.balance("usr:carol")["balance"]
        tx3 = spend_n()
        own40 = face.splash_owner("splash:lobby", 40)
        own41 = face.splash_owner("splash:lobby", 41)
        own42 = face.splash_owner("splash:lobby", 42)
        ok("carol buys the lobby splash for the two-week span"
           " 40..41",
           "balance %d->%d (exact -10000 = 2 windows x 5000);"
           " spend-tx %d->%d (+1); span=%d..%d; splash owner"
           " week40=%s week41=%s week42=%s (span scope only)"
           % (bal_c1, bal_c2, tx2, tx3, r2["start_window"],
              r2["end_window"], own40, own41, own42))

        # -- carousel capacity gate: three slots, then FULL ----------
        tx4 = spend_n()
        bal_a3 = led.balance("usr:amy")["balance"]
        ra = face.book("usr:amy", "screen:quant-main", 50, 4, 2000,
                       "order:ad-amy-screen")
        rb = face.book("usr:ben", "screen:quant-main", 50, 2, 2000,
                       "order:ad-ben-screen")
        rc = face.book("usr:carol", "screen:quant-main", 50, 1, 2000,
                       "order:ad-carol-screen")
        tx5 = spend_n()
        bal_d1 = led.balance("usr:dave")["balance"]
        refuse_leg("dave tries a FOURTH concurrent carousel slot at"
                   " week 50", lambda: face.book(
                       "usr:dave", "screen:quant-main", 50, 1, 2000,
                       "order:ad-dave-screen"))
        ok("three rotation slots fill, the fourth is refused",
           "amy/ben/carol booked %d->%d (+3 spends); fees"
           " 8000/4000/2000 = windows x 2000; dave refused with his"
           " balance %d==%d untouched (capacity 3 = rotation_slots,"
           " the refusal charged nothing)"
           % (tx4, tx5, led.balance("usr:dave")["balance"], bal_d1))

        # -- off-peak carousel span legal + advance naming booking ---
        tx6 = spend_n()
        r_d = face.book("usr:dave", "screen:quant-main", 52, 3, 2000,
                        "order:ad-dave-offpeak")
        r_adv = face.book("usr:carol", "naming:metro-l4", 100, 1,
                          10000, "order:ad-carol-metro100")
        tx7 = spend_n()
        h99 = face.naming_holder("naming:metro-l4", 99)
        h100 = face.naming_holder("naming:metro-l4", 100)
        h101 = face.naming_holder("naming:metro-l4", 101)
        ok("dave books an off-peak span and carol advance-books the"
           " metro-l4 naming at window 100",
           "dave span=%d..%d fee=%d (only amy overlaps at 52..53,"
           " inside capacity); carol advance span=%d..%d fee=%d"
           " charged today for a future window; holder"
           " 99=%s / 100=%s / 101=%s (advance window scope)"
           % (r_d["start_window"], r_d["end_window"], r_d["fee"],
              r_adv["start_window"], r_adv["end_window"],
              r_adv["fee"], h99, h100, h101))

        # -- bad-args family, all zero side effects -------------------
        refuse_leg("a corp: account tries to book",
                   lambda: face.book(
                       "corp:acme", "splash:lobby", 60, 1, 5000,
                       "order:ad-corp"))
        refuse_leg("a zero price is refused",
                   lambda: face.book(
                       "usr:ben", "splash:lobby", 60, 1, 0,
                       "order:ad-zero"))
        refuse_leg("a zero window count is refused",
                   lambda: face.book(
                       "usr:ben", "splash:lobby", 60, 0, 5000,
                       "order:ad-zerow"))
        refuse_leg("a negative start window is refused",
                   lambda: face.book(
                       "usr:ben", "splash:lobby", -1, 1, 5000,
                       "order:ad-neg"))
        refuse_leg("an empty booking ref is refused",
                   lambda: face.book(
                       "usr:ben", "splash:lobby", 60, 1, 5000, "  "))
        ok("bad-args audit: five refusals, ben's balance flat",
           "%d==%d (advertisers are usr:* only, price must be int >"
           " 0, windows int >= 1, start_window int >= 0, ref"
           " required -- every rejected booking charges nothing)"
           % (led.balance("usr:ben")["balance"], bal_b0 - 4000))

        # -- pure read faces: lineup order, zero token movement -------
        tx8 = spend_n()
        line50 = face.carousel_lineup("screen:quant-main", 50)
        line53 = face.carousel_lineup("screen:quant-main", 53)
        holders = [face.naming_holder("naming:harbor-gate", 26),
                   face.naming_holder("naming:harbor-gate", 27)]
        board = face.schedule_board("naming:harbor-gate")
        tx9 = spend_n()
        pos50 = [(a["position"], a["account_id"])
                 for a in line50["advertisers"]]
        pos53 = [(a["position"], a["account_id"])
                 for a in line53["advertisers"]]
        ok("lineup / holder / board reads are pure and ordered",
           "spend-tx %d==%d unchanged -- reads move zero tokens;"
           " lineup at week 50 (full) = %s in booking order with"
           " rotation_slots=%d; at week 53 = %s (ben and carol"
           " expired, 2/3); naming holder 26=%s 27=%s; board rows"
           "=%s each carrying its bound spend tx"
           % (tx8, tx9, pos50, line50["rotation_slots"], pos53,
              holders[0], holders[1],
              len(board["bookings"])))

        # -- audit: spends equal bookings, balances exact ------------
        tx_total = spend_n()
        bookings = 7
        amy_final = led.balance("usr:amy")["balance"]
        ben_final = led.balance("usr:ben")["balance"]
        carol_final = led.balance("usr:carol")["balance"]
        dave_final = led.balance("usr:dave")["balance"]
        pool_final = led.balance("pool:reserve")["balance"]
        conn = sqlite3.connect(db)
        ad_rows = conn.execute(
            "SELECT COUNT(*) FROM ad_units").fetchone()[0]
        occ_bound = conn.execute(
            "SELECT COUNT(*) FROM venue_occupancy WHERE"
            " bound_spend_tx IS NOT NULL").fetchone()[0]
        bad_kind = conn.execute(
            "SELECT COUNT(*) FROM venue_occupancy v LEFT JOIN"
            " ad_units a ON a.unit_id = v.unit_id WHERE"
            " a.unit_id IS NULL").fetchone()[0]
        conn.close()
        ok("audit the bookings against real debit entries",
           "spend-tx total %d == bookings %d; every one of the %d"
           " occupancy rows binds a real spend debit as its"
           " provenance and %d of them live outside the ad registry;"
           " balances exact: amy 50000-10000-8000=%d, ben"
           " 50000-4000=%d, carol 50000-10000-2000-10000=%d, dave"
           " 50000-6000=%d; pool:reserve %d (240000 mint, spent"
           " tokens loop back in, conservation holds); ad_units"
           " registry rows=%d"
           % (tx_total, bookings, occ_bound, bad_kind, amy_final,
              ben_final, carol_final, dave_final, pool_final,
              ad_rows))

        # -- isolation law: module source, structural ---------------
        banned_sql = [p for p in ("INSERT INTO venue_occupancy",
                                  "UPDATE ad_units",
                                  "UPDATE venue_occupancy")
                      if p in ad_src]
        led_touches = ad_src.count("self.led")
        no_mutation = (not banned_sql) and led_touches == 1
        ok("isolation law audit on the REAL module source",
           "zero direct INSERT INTO venue_occupancy and zero UPDATE"
           " surface on registry or occupancy rows (banned SQL"
           " found=%s, the suite AC-AD7 pattern); the face holds the"
           " token ledger only to share its DB file -- self.led"
           " appears exactly %d time (the reference store), every"
           " spend is booked by the venue engine, and no verb turns"
           " a booking back into tokens (cancellation or fee"
           " reversal of any kind stays a P1 [needs-CEO] approval"
           " face)"
           % (banned_sql or "none", led_touches))
        face.close()
        ven.close()
        led.close()
        return {
            "legs": legs, "refusals": refusals,
            "spend_total": tx_total, "bookings": bookings,
            "amy_bal": amy_final, "ben_bal": ben_final,
            "carol_bal": carol_final, "dave_bal": dave_final,
            "pool_bal": pool_final, "ad_rows": ad_rows,
            "occ_bound": occ_bound, "banned_sql": banned_sql,
            "led_touches": led_touches,
            "no_mutation": no_mutation,
            "line50": pos50, "line53": pos53,
            "holder26": holders[0], "holder27": holders[1],
            "audit_ok": tx_total == bookings
            and amy_final == 32000 and ben_final == 46000
            and carol_final == 28000 and dave_final == 44000
            and pool_final == 90000,
        }
    finally:
        if face is not None:
            with contextlib.suppress(Exception):
                face.close()
        if ven is not None:
            with contextlib.suppress(Exception):
                ven.close()
        if led is not None:
            with contextlib.suppress(Exception):
                led.close()
        shutil.rmtree(tmp, ignore_errors=True)


def wm_probe():
    """Run the REAL AIGC implicit-watermark capability (P-47-3c face)
    in-process on a deterministic throwaway image (F3 law: every
    verdict below is computed by the local pip blind_watermark library
    at probe time, never canned in this source). The probe composes
    the adopted library directly and reuses the watermark suite
    calibration fixtures (make_img / label_bits) by import -- the
    suite files themselves stay untouched. Chain: 256-bit label embed
    > clean extract > JPEG re-save extract > honest negative (85%
    central crop degrades the direct extract) > library recover
    locate + canvas rebuild > extract exact."""
    import cv2
    import numpy as np
    from blind_watermark import WaterMark
    from blind_watermark.recover import (estimate_crop_parameters,
                                         recover_crop)
    if WM_DIR not in sys.path:
        sys.path.insert(0, WM_DIR)
    import test_watermark as wm_suite  # calibration fixtures (reuse)

    jpeg_q = 90       # robustness case 1, locked at suite calibration
    keep = 0.85       # robustness case 2, locked at suite calibration
    legs = []

    def ok(leg, outcome):
        legs.append({"n": len(legs) + 1, "leg": leg,
                     "outcome": outcome})

    tmp = tempfile.mkdtemp(prefix="frontdoor-wm-")
    try:
        bits = wm_suite.label_bits().astype(int)
        nbits = int(bits.size)
        orig = os.path.join(tmp, "orig.png")
        emb = os.path.join(tmp, "embedded.png")
        cv2.imwrite(orig, wm_suite.make_img())
        bwm = WaterMark(password_wm=1, password_img=1, mode="common")
        bwm.read_img(orig)
        bwm.read_wm(bits, mode="bit")
        bwm.embed(emb)
        emb_ok = os.path.exists(emb) and os.path.getsize(emb) > 0
        ok("import the capability + embed the 256-bit label (SHA-256 "
           "of the fixed label string) into a deterministic 640x480 "
           "throwaway image",
           "local pip blind_watermark imported in-process; embedded "
           "ok=%s bits=%d (suite calibration fixtures imported, zero "
           "suite file touched)" % (emb_ok, nbits))

        def extract(path):
            w = WaterMark(password_wm=1, password_img=1, mode="common")
            got = w.extract(filename=path, wm_shape=[nbits],
                            mode="bit")
            return np.asarray(got).astype(int).clip(0, 1)

        got_clean = extract(emb)
        clean_exact = bool(np.array_equal(got_clean, bits))
        ok("clean extract roundtrip",
           "bit-exact=%s (ber=%.4f vs the embedded label)"
           % (clean_exact, float(np.mean(got_clean != bits))))

        img_e = cv2.imread(emb, cv2.IMREAD_COLOR)
        jpg = os.path.join(tmp, "embedded_q%d.jpg" % jpeg_q)
        ok_write = img_e is not None and cv2.imwrite(
            jpg, img_e, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_q])
        got_jpg = extract(jpg) if ok_write else None
        jpg_exact = ok_write and bool(np.array_equal(got_jpg, bits))
        ok("robustness case 1: JPEG re-save q=%d, then extract"
           % jpeg_q,
           "write=%s bit-exact=%s (ber=%.4f)"
           % (bool(ok_write), jpg_exact,
              float(np.mean(got_jpg != bits))
              if got_jpg is not None else 1.0))

        h, w = img_e.shape[:2]
        ch, cw = int(h * keep), int(w * keep)
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        crop = os.path.join(tmp, "crop_%d.png" % int(keep * 100))
        cv2.imwrite(crop, img_e[y0:y0 + ch, x0:x0 + cw])
        got_direct = extract(crop)
        direct_degrades = not np.array_equal(got_direct, bits)
        ok("robustness case 2: %d%% central crop, direct extract "
           "(honest negative)" % int(keep * 100),
           "direct extract degrades=%s (ber=%.4f, honest negative "
           "displayed -- the library needs the canvas rebuilt first)"
           % (direct_degrades, float(np.mean(got_direct != bits))))

        loc, shape, score, _scale = estimate_crop_parameters(
            original_file=emb, template_file=crop, scale=(1, 1),
            search_num=1)
        rec = os.path.join(tmp, "recovered.png")
        recover_crop(template_file=crop, output_file_name=rec,
                     loc=loc, image_o_shape=shape)
        got_rec = extract(rec)
        rec_exact = bool(np.array_equal(got_rec, bits))
        ok("recover.py template-match locate + canvas rebuild, then "
           "extract",
           "locate score=%.3f loc=%s recovered bit-exact=%s"
           % (float(score), tuple(int(v) for v in loc), rec_exact))

        # dual-track anchors: the explicit track is read live from the
        # ugc product files; the implicit spec presence shows honestly
        with open(UGC_CFG, encoding="utf-8") as fh:
            cfg_text = fh.read()
        explicit = str((json.loads(cfg_text).get("compliance") or {})
                       .get("ai_label_text", ""))
        cfg_line = next((i + 1 for i, ln in enumerate(cfg_text
                                                     .splitlines())
                         if '"ai_label_text"' in ln), -1)
        with open(WM_PIPE, encoding="utf-8") as fh:
            pipe_text = fh.read()
        pipe_line = next((i + 1 for i, ln in enumerate(pipe_text
                                                       .splitlines())
                          if '"ai_label"' in ln), -1)
        ok("dual-track anchor read (explicit track live from the ugc "
           "product files)",
           "explicit label set=%s (ugc config.json L%d); pipeline.py "
           "L%d ai_label draft field; implicit spec on disk=%s"
           % (explicit != "", cfg_line, pipe_line,
              os.path.exists(WM_DOC)))

        return {
            "legs": legs, "nbits": nbits, "clean": clean_exact,
            "jpeg": jpg_exact, "crop_degrades": direct_degrades,
            "recovered": rec_exact, "explicit": explicit,
            "cfg_line": cfg_line, "pipe_line": pipe_line,
            "doc_on_disk": os.path.exists(WM_DOC),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_wm_probe_once():
    """Server-start isomorph of the journey pattern: run the
    watermark probe once and keep the transcript; a restart re-runs
    it. Honest failure face on any probe error, never a fake PASS."""
    try:
        return wm_probe(), ""
    except Exception as exc:  # honest failure face, never fake PASS
        return None, str(exc)[:300]


WM_RES, WM_ERR = run_wm_probe_once()


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

    pb = load_json(PB_JSON)
    pb_face_html = "".join(
        "<h3 style=\"margin:14px 0 8px\">%s</h3>%s"
        % (esc(f["name"]),
           "".join("<p class=kv>%s</p>" % esc(b) for b in f["blocks"]))
        for f in pb["faces"])
    pb_dec_head = "".join("<th>%s</th>" % esc(h)
                          for h in pb["decision_headers"])
    pb_dec_rows = "".join(
        "<tr><td><b>%s</b></td><td>%s</td></tr>"
        % (esc(d["m"]), esc(d["status"])) for d in pb["decisions"])
    pb_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>"
        % (esc(c["name"]), esc(c["text"])) for c in pb["compliance"])

    # -- token ledger core face card (v0.10): REAL probe at render time --
    lcfg = load_json(LEDGER_CFG)
    try:
        lp = ledger_probe()
        lp_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        lp, lp_err = None, str(exc)[:300]
    tl_label = esc(str(lcfg.get("token", {}).get("ai_label_text", "")))
    tl_disc = esc(str(lcfg.get("token", {}).get("disclaimer", "")))
    if lp is not None:
        tl_roles = [("usr:probe-a", "resident account (census-bound, funded, spent)"),
                    ("usr:probe-b", "resident account (census-bound, gated reward)"),
                    ("pool:reserve", "platform reserve pool (fiat stand-in source, spend sink)"),
                    ("pool:share", "platform share pool (co-create reward source)"),
                    ("pool:reward", "platform reward pool"),
                    ("equity:auth", "mint counterparty (negative by construction, AC-L6)")]
        tl_rows = "".join(
            "<tr><td><b>%s</b></td><td>%d</td><td>%s</td></tr>"
            % (esc(a), lp["balances"][a], esc(r)) for a, r in tl_roles)
        tl_sum = esc("zero-sum identity (AC-L6): sum of the six balances = %d"
                     % sum(lp["balances"].values()))
        tl_gate = esc(
            "content-gate reward face (AC-L8): unrecorded event refused (%s),"
            " gate-passed event granted +%d booked from the %s pool"
            % (lp["refused"], lp["score"],
               str(lcfg["actions"]["cocreate"]["pool"])))
        tl_spend = esc(
            "spend loop closure (BLUEPRINT 5.4): one spend tx %s booked,"
            " 30 debited from usr:probe-a and credited back into"
            " pool:reserve -- tokens never leave the loop"
            % str(lp["spend_tx"])[:16])
        verdict = ("VERDICT: RECONCILE PASS (8/8 checks)"
                   if lp["recon_fails"] == 0 else
                   "VERDICT: RECONCILE FAIL (%d/8 checks failed)"
                   % lp["recon_fails"])
        tl_recls = "qok" if lp["recon_fails"] == 0 else "qfail"
        tl_recon_html = ("<pre class=\"proof %s\">%s\n%s</pre>"
                         % (tl_recls, esc("\n".join(lp["recon_lines"])),
                            esc(verdict)))
        tl_tamper_html = ("<pre class=\"proof qfail\">%s\n%s</pre>"
                          % (esc("\n".join(lp["tamper_lines"])),
                             esc("VERDICT: RECONCILE FAIL (%d/8 checks"
                                 " failed)" % lp["tamper_fails"])))
        tl_kpis = ("<div class=\"grid\">"
                   "<div class=\"kpi\"><b>%d</b>probe tx booked</div>"
                   "<div class=\"kpi\"><b>%d</b>double entries</div>"
                   "<div class=\"kpi\"><b>%d</b>issued = -equity:auth</div>"
                   "<div class=\"kpi\"><b>%s</b>gate refusal code</div>"
                   "</div>"
                   % (lp["tx"], lp["entries"], lp["issued"], lp["refused"]))
    else:
        tl_rows = ""
        tl_sum = tl_gate = tl_spend = ""
        tl_recon_html = tl_tamper_html = tl_kpis = ""
    if lp_err:
        tl_kpis = ("<p class=fail>LEDGER PROBE FAILED (honest failure,"
                   " no fake PASS): %s</p>" % esc(lp_err))
    tl_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", tl_label),
            ("disclaimer", tl_disc),
            ("[needs-CEO]", "sandbox keeps mock keys; real channel keys"
             " and platform credentials are CEO physical items and never"
             " enter git; pricing/gate decisions stay approval-only"),
            ("msgSecCheck front gate", "content rewards only book behind"
             " a recorded gate pass (AC-L8); the sandbox gate is the"
             " wordlist mock, production stays fail-closed until the"
             " platform key arrives"),
        ])

    # -- ugc pipeline core face card (v0.11): REAL probe at render time --
    ucfg = load_json(UGC_CFG)
    unodes = load_json(UGC_JSON)
    try:
        up = ugc_probe()
        up_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        up, up_err = None, str(exc)[:300]
    if up is not None:
        ug_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in up["legs"])
        ug_kpis = ("<div class=\"grid\">"
                   "<div class=\"kpi\"><b>%d</b>gate refusals"
                   " (fail-closed)</div>"
                   "<div class=\"kpi\"><b>%d</b>local L1 hits (quota"
                   " saved)</div>"
                   "<div class=\"kpi\"><b>%d</b>items pooled live</div>"
                   "<div class=\"kpi\"><b>%d</b>chronicle rows</div>"
                   "</div>"
                   % (len(up["refusals"]), up["local_hits"],
                      up["pooled"], up["chronicle"]))
        ug_pool = esc(
            "live pool: %d pooled/drafted items (%s); chronicle terminal"
            " states: %s"
            % (up["pooled"],
               ", ".join("%s x%d" % kv
                         for kv in sorted(up["pool_lines"].items()))
               or "none",
               ", ".join("%s x%d" % kv
                         for kv in sorted(up["chron_states"].items()))
               or "none"))
        ug_export = ("<p class=kv>%s</p><p class=kv>%s</p>"
                     % (esc(str(ucfg.get("export", {}).get("note", ""))),
                        esc(str(unodes.get("export_note", "")))))
    else:
        ug_rows = ug_kpis = ug_pool = ug_export = ""
    if up_err:
        ug_kpis = ("<p class=fail>UGC PROBE FAILED (honest failure, no"
                   " fake PASS): %s</p>" % esc(up_err))
    ug_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(ucfg.get("compliance", {}).get(
                "ai_label_text", ""))),
            ("disclaimer", str(ucfg.get("compliance", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", str(ucfg.get("params_status", ""))),
            ("msgSecCheck front gate", str(ucfg.get("gate", {}).get(
                "note", ""))),
        ])
    ug_prov = esc(
        "L1 local pre-filter source (from config, verbatim): %s"
        % str(ucfg.get("gate", {}).get("pre_filter", {}).get(
            "source", "")))

    # -- live room conversion face card (v0.13): REAL probe at
    # render time; honest failure face --
    try:
        lr = liveroom_probe()
        lr_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        lr, lr_err = None, str(exc)[:300]
    if lr is not None:
        lrv_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in lr["legs"])
        lrv_kpis = ("<div class=\"grid\">"
                    "<div class=\"kpi\"><b>%d</b>gate/policy refusals"
                    " (fail-closed)</div>"
                    "<div class=\"kpi\"><b>%d</b>conversions booked"
                    "</div>"
                    "<div class=\"kpi\"><b>%d</b>probe conversion_total"
                    " (cents)</div>"
                    "<div class=\"kpi\"><b>%d==%d</b>spend-tx =="
                    " conversions (isolation)</div>"
                    "</div>"
                    % (len(lr["refusals"]), lr["converted"],
                       lr["conversion_total"], lr["spend_tx"],
                       lr["converted"]))
        lrv_funnel = esc(
            "funnel (live tables): entered=%d -> registered=%d ->"
            " converted=%d, conversion_total=%d cents; session runs"
            " attended with the BigCompute risk-control citation"
            % (lr["entered"], lr["registered"], lr["converted"],
               lr["conversion_total"]))
        lrv_trans = ("<pre class=\"proof qok\">%s</pre>"
                     % esc("\n".join(lr["transcript"])))
    else:
        lrv_rows = lrv_kpis = lrv_funnel = lrv_trans = ""
    if lr_err:
        lrv_kpis = ("<p class=fail>LIVE ROOM PROBE FAILED (honest"
                    " failure, no fake PASS): %s</p>" % esc(lr_err))
    lrv_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(lcfg.get("token", {}).get("ai_label_text",
                                                   ""))),
            ("disclaimer", str(lcfg.get("token", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", "prices are caller-supplied probe values"
             " only; 19.9-style pricing stays a CEO approval face;"
             " broadcast strategy belongs to BigCompute risk control"
             " (cited, never decided here)"),
            ("msgSecCheck front gate", "danmaku runs the wordlist gate"
             " BEFORE any row lands (sandbox = wordlist mock per"
             " P-47-3b; production wiring stays fail-closed until the"
             " platform key arrives)"),
        ])
    lrv_hard = esc(
        "platform hard law: unattended streaming is banned outright"
        " (patrol-4 E2-3 + BigCompute risk-register E1) --"
        " open_session with attended=False is refused before any row"
        " exists; the room only ever opens attended, with a non-empty"
        " risk-control citation")

    # -- city props face card (v0.14): REAL probe at render time;
    # honest failure face --
    try:
        pp = props_probe()
        pp_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        pp, pp_err = None, str(exc)[:300]
    if pp is not None:
        ppv_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in pp["legs"])
        ppv_credits = (pp["props"][0]["count_credits"]
                       if pp["props"] else 0)
        ppv_kpis = ("<div class=\"grid\">"
                    "<div class=\"kpi\"><b>%d</b>fail-closed refusals"
                    "</div>"
                    "<div class=\"kpi\"><b>%d</b>landed purchases (one"
                    " spend each)</div>"
                    "<div class=\"kpi\"><b>%d</b>credit balance after"
                    " consume</div>"
                    "<div class=\"kpi\"><b>%d==%d</b>spend-tx =="
                    " purchases (isolation)</div>"
                    "</div>"
                    % (len(pp["refusals"]), pp["landed_buys"],
                       ppv_credits, pp["spend_tx"], pp["landed_buys"]))
        ppv_inv = esc(
            "amy's live inventory: cosmetics=%s; props=%s --"
            " entitlements and credits bind to the purchasing"
            " account; every row carries its origin-purchase spend"
            % (",".join(pp["cosmetics"]) or "none",
               ", ".join("%s x%d" % (p["item_id"], p["count_credits"])
                         for p in pp["props"]) or "none"))
        ppv_audit = esc(
            "audit: every inventory row binds a real origin-purchase"
            " spend debit=%s; balance arithmetic exact (5000 - %d"
            " debits); raw tx ids are never rendered (determinism)"
            % (pp["bound_ok"], pp["total_debit"]))
    else:
        ppv_rows = ppv_kpis = ppv_inv = ppv_audit = ""
    if pp_err:
        ppv_kpis = ("<p class=fail>PROPS PROBE FAILED (honest"
                    " failure, no fake PASS): %s</p>" % esc(pp_err))
    ppv_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(lcfg.get("token", {}).get("ai_label_text",
                                                   ""))),
            ("disclaimer", str(lcfg.get("token", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", "probe prices (2990/500/300) are"
             " caller-supplied sandbox values; catalog pricing stays"
             " a CEO approval face; no verb converts credits back"
             " into tokens and none moves inventory between accounts"
             " -- any such face is P1 CEO approval-only"),
            ("msgSecCheck front gate", "this card has no free-text"
             " face; item copy and purchase refs stay config/probe"
             " driven; every UGC/text surface in the stack keeps the"
             " msgSecCheck front gate (wordlist mock in sandbox,"
             " fail-closed in production)"),
        ])
    ppv_hard = esc(
        "structural law (counts-vs-tokens two-domain rule): the"
        " token ledger is touched exactly once per purchase by one"
        " spend booking; credits are never tokens, consume never"
        " books a token tx, and no reverse-conversion or transfer"
        " verb exists in the module (BLUEPRINT 5.4 posture extended"
        " to the counts domain)")

    # -- creator incentive face card (v0.15): REAL probe at render
    # time; honest failure face --
    try:
        ic = incentive_probe()
        ic_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        ic, ic_err = None, str(exc)[:300]
    if ic is not None:
        icv_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in ic["legs"])
        icv_kpis = ("<div class=\"grid\">"
                    "<div class=\"kpi\"><b>%d==%d</b>share tx =="
                    " payout rows (one-way)</div>"
                    "<div class=\"kpi\"><b>%d</b>window budget landed"
                    " exact</div>"
                    "<div class=\"kpi\"><b>%d</b>fail-closed refusals"
                    "</div>"
                    "<div class=\"kpi\"><b>%d</b>ref-bound credit rows"
                    "</div>"
                    "</div>"
                    % (ic["share_tx"], len(ic["paid_w1"])
                       + len(ic["paid_w2"]),
                       sum(a for _, a in ic["paid_w1"]),
                       len(ic["refusals"]), ic["join_rows"]))
        icv_grad = esc(
            "pure gradient walk: units (0, 1, 3, 5, 6, 15, 16, 40,"
            " 100) -> payouts %s; marginal per unit falls band over"
            " band (%d -> %d -> %d) -- the anti-farm shape that"
            " rewards early contribution and flattens farming"
            % (ic["gradient"], ic["marginals"][0], ic["marginals"][1],
               ic["marginals"][2]))
        icv_join = esc(
            "booking join: pool:share %d - %d = %d exact; %d credit"
            " rows each binding its incentive:window:creator ref=%s;"
            " W1 landed %s (sum == budget) and W2 capped the whale at"
            " %s (collar)"
            % (ic["pool_before"], ic["total_paid"], ic["pool_after"],
               ic["join_rows"], ic["join_ok"], ic["paid_w1"],
               ic["paid_w2"]))
    else:
        icv_rows = icv_kpis = icv_grad = icv_join = ""
    if ic_err:
        icv_kpis = ("<p class=fail>INCENTIVE PROBE FAILED (honest"
                    " failure, no fake PASS): %s</p>" % esc(ic_err))
    icv_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(lcfg.get("token", {}).get("ai_label_text",
                                                   ""))),
            ("disclaimer", str(lcfg.get("token", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", "gradient bands / collar / budget are"
             " sandbox-only probe params; real share ratios,"
             " settlement period and redemption threshold stay a P1"
             " CEO approval face and no incentive key ships in any"
             " config file"),
            ("msgSecCheck front gate", "payouts only settle against"
             " contribution units booked by the UGC pipeline behind"
             " its gate passes; every UGC/text surface in the stack"
             " keeps the msgSecCheck front gate (wordlist mock in"
             " sandbox, fail-closed in production)"),
        ])
    icv_hard = esc(
        "structural law (one-way share rule): a settled window books"
        " each payout as exactly one share tx out of pool:share via"
        " the ledger public API; the allocator owns no token"
        " arithmetic of its own, a settled window replays as a"
        " refusal with zero ledger movement, and no"
        " reverse-conversion verb exists anywhere in the module"
        " (tokens never leave the loop, BLUEPRINT 5.4)")

    # -- strategy observation face card (v0.16): REAL probe at render
    # time; honest failure face --
    try:
        ob = obs_probe()
        ob_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        ob, ob_err = None, str(exc)[:300]
    if ob is not None:
        ob_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in ob["legs"])
        ob_kpis = ("<div class=\"grid\">"
                   "<div class=\"kpi\"><b>%d==%d</b>spend tx == grant"
                   " rows (one per purchase)</div>"
                   "<div class=\"kpi\"><b>%d</b>fail-closed refusals"
                   "</div>"
                   "<div class=\"kpi\"><b>%d</b>observe view keys"
                   " (results only)</div>"
                   "<div class=\"kpi\"><b>%s</b>registry source"
                   " column</div>"
                   "</div>"
                   % (ob["spend_total"], ob["grants"],
                      len(ob["refusals"]), len(ob["view_keys"]),
                      "none" if ob["no_source_col"] else "LEAK"))
        ob_scope = esc(
            "permanence vs window scope: the single grant survives"
            " months (amy 2026-11 allowed=%s, kind=%s) while the pass"
            " covers exactly its own month (ben 2026-11 allowed=%s)"
            % (ob["perm_allowed"], ob["perm_kind"],
               ob["pass_next_allowed"]))
        ob_audit = esc(
            "purchase audit: %d grant rows, spend-tx total %d"
            " (every purchase books exactly one spend and every grant"
            " row binds that debit as its provenance); balances exact:"
            " amy 3000-990=%d, ben 3000-1990=%d"
            % (ob["grants"], ob["spend_total"], ob["amy_bal"],
               ob["ben_bal"]))
    else:
        ob_rows = ob_kpis = ob_scope = ob_audit = ""
    if ob_err:
        ob_kpis = ("<p class=fail>OBSERVATION PROBE FAILED (honest"
                   " failure, no fake PASS): %s</p>" % esc(ob_err))
    ob_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(lcfg.get("token", {}).get("ai_label_text",
                                                   ""))),
            ("disclaimer", str(lcfg.get("token", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", "the 9.9 yuan single / 19.9 yuan"
             " monthly-pass canon anchors are caller-supplied probe"
             " prices; real pricing and any launch gating stay a P1"
             " CEO approval face"),
            ("msgSecCheck front gate", "strategy results summaries"
             " and every UGC/text surface in the stack keep the"
             " msgSecCheck front gate (wordlist mock in sandbox,"
             " fail-closed in production)"),
        ])
    ob_hard = esc(
        "structural law (results-only paywall): the registry has no"
        " source column and the register face has no source"
        " parameter at all, so the results-only boundary cannot leak"
        " source code; every purchase touches the token ledger"
        " exactly once through one spend booking bound into an"
        " immutable grant row, pure reads move zero tokens, and the"
        " access gate is fail-closed (BLUEPRINT sec.4 C-end line 4)")

    # -- studio onboarding face card (v0.17): REAL probe at render
    # time; honest failure face --
    try:
        st = st_probe()
        st_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        st, st_err = None, str(exc)[:300]
    if st is not None:
        st_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in st["legs"])
        st_kpis = ("<div class=\"grid\">"
                   "<div class=\"kpi\"><b>%d==%d</b>spend tx =="
                   " onboarded seats</div>"
                   "<div class=\"kpi\"><b>%d</b>fail-closed"
                   " refusals</div>"
                   "<div class=\"kpi\"><b>%d+%d</b>canon benefits"
                   " B1 + B2</div>"
                   "<div class=\"kpi\"><b>%s</b>registry row-mutation"
                   " surface</div>"
                   "</div>"
                   % (st["spend_total"], st["onboards"],
                      len(st["refusals"]), len(st["ben_g"]),
                      len(st["ben_q"]),
                      "none" if st["no_mutation"] else "LEAK"))
        st_scope = esc(
            "window semantics: each year index is its own seat --"
            " year 26 held by %s, the year-27 renewal books in"
            " advance as its own seat (%s), year 28 stays open;"
            " two kinds are independent products (one account may"
            " hold a game seat and a quant seat the same year) and"
            " parallel same-kind studios are legal"
            % (st["tenant26"], st["tenant27"]))
        st_audit = esc(
            "purchase audit: %d onboarding spends, every one of the"
            " %d occupancy rows binds its spend debit as provenance;"
            " balances exact: amy 50000-9800-9800-19800=%d, ben"
            " 50000==%d untouched, carol 50000-9800=%d; registry"
            " rows=%d immutable"
            % (st["spend_total"], st["occ_bound"], st["amy_bal"],
               st["ben_bal"], st["carol_bal"], st["reg_rows"]))
    else:
        st_rows = st_kpis = st_scope = st_audit = ""
    if st_err:
        st_kpis = ("<p class=fail>STUDIO PROBE FAILED (honest"
                   " failure, no fake PASS): %s</p>" % esc(st_err))
    st_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(lcfg.get("token", {}).get("ai_label_text",
                                                   ""))),
            ("disclaimer", str(lcfg.get("token", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", "the B1 9,800 / B2 19,800 CNY-per-year"
             " canon anchors are caller-supplied probe prices; real"
             " pricing, launch gating, cancellation and any fee"
             " reversal stay a P1 CEO approval face"),
            ("msgSecCheck front gate", "studio storefront branding"
             " and every UGC/text surface in the stack keep the"
             " msgSecCheck front gate (wordlist mock in sandbox,"
             " fail-closed in production)"),
        ])
    st_hard = esc(
        "structural law (onboarding-is-not-tokens): each onboarding"
        " is exactly one token spend and nothing else in the module"
        " ever touches the token domain -- profile, benefit and"
        " tenant faces move zero tokens, no verb turns a"
        " subscription back into tokens or moves it between"
        " accounts, and the registry is immutable once written; the"
        " occupancy engine stays the venue (referenced, never"
        " rebuilt, BLUEPRINT sec.4 B1/B2)")

    # -- virtual-exhibition ad-slot face card (v0.18): REAL probe at
    # render time; honest failure face --
    try:
        ad = ads_probe()
        ad_err = ""
    except Exception as exc:  # honest failure face, never fake PASS
        ad, ad_err = None, str(exc)[:300]
    if ad is not None:
        ad_rows_html = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["action"]), esc(lg["outcome"]))
            for lg in ad["legs"])
        ad_kpis = ("<div class=\"grid\">"
                   "<div class=\"kpi\"><b>%d==%d</b>spend tx =="
                   " booked ads</div>"
                   "<div class=\"kpi\"><b>%d</b>fail-closed"
                   " refusals</div>"
                   "<div class=\"kpi\"><b>%s</b>carousel lineup"
                   " wk50 + wk53</div>"
                   "<div class=\"kpi\"><b>%s</b>registry row-mutation"
                   " surface</div>"
                   "</div>"
                   % (ad["spend_total"], ad["bookings"],
                      len(ad["refusals"]),
                      esc("%s+%s" % (ad["line50"], ad["line53"])),
                      "none" if ad["no_mutation"] else "LEAK"))
        ad_scope = esc(
            "window semantics: naming rides a year window (holder"
            " 26=%s, 27=%s free), the splash and the carousel ride"
            " week windows (splash owner span 40..41 only), and any"
            " future window books in advance charged today"
            % (ad["holder26"], ad["holder27"]))
        ad_audit = esc(
            "purchase audit: %d booking spends, every one of the %d"
            " occupancy rows binds its spend debit as provenance;"
            " balances exact: amy 50000-10000-8000=%d, ben"
            " 50000-4000=%d, carol 50000-10000-2000-10000=%d, dave"
            " 50000-6000=%d; pool:reserve %d (spent tokens loop"
            " back in, conservation holds)"
            % (ad["spend_total"], ad["occ_bound"], ad["amy_bal"],
               ad["ben_bal"], ad["carol_bal"], ad["dave_bal"],
               ad["pool_bal"]))
    else:
        ad_rows_html = ad_kpis = ad_scope = ad_audit = ""
    if ad_err:
        ad_kpis = ("<p class=fail>AD PROBE FAILED (honest"
                   " failure, no fake PASS): %s</p>" % esc(ad_err))
    ad_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(lcfg.get("token", {}).get("ai_label_text",
                                                   ""))),
            ("disclaimer", str(lcfg.get("token", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", "the B3 canon anchors (giant-screen"
             " carousel 2,000 CNY/week, building naming right"
             " 10,000 CNY/year, lobby splash 5,000 CNY/week) are"
             " caller-supplied probe prices; real pricing, launch"
             " gating, cancellation and any fee reversal stay a P1"
             " CEO approval face"),
            ("msgSecCheck front gate", "ad creative text and every"
             " UGC/text surface in the stack keep the msgSecCheck"
             " front gate (wordlist mock in sandbox, fail-closed"
             " in production)"),
        ])
    ad_hard = esc(
        "structural law (occupancy-is-not-tokens): each booking is"
        " exactly one token spend and nothing else in the module"
        " ever touches the token domain -- lineup, holder and"
        " board faces move zero tokens, no verb converts a booking"
        " back into tokens or moves it between accounts, and"
        " booking rows are immutable once written; the occupancy"
        " engine stays the venue and this face owns exactly one"
        " small ad_units registry (referenced, never rebuilt,"
        " BLUEPRINT sec.4 B3)")

    # -- AIGC implicit watermark face card (v0.12): REAL probe run
    # once at server start (journey isomorph); honest failure face --
    if WM_RES is not None:
        wm_rows = "".join(
            "<tr><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (lg["n"], esc(lg["leg"]), esc(lg["outcome"]))
            for lg in WM_RES["legs"])
        wm_kpis = ("<div class=\"grid\">"
                   "<div class=\"kpi\"><b>%d</b>label bits embedded"
                   "</div>"
                   "<div class=\"kpi\"><b>%s</b>clean roundtrip exact"
                   "</div>"
                   "<div class=\"kpi\"><b>%s</b>exact after JPEG q90"
                   "</div>"
                   "<div class=\"kpi\"><b>%s</b>exact after crop "
                   "recover</div>"
                   "</div>"
                   % (WM_RES["nbits"], WM_RES["clean"], WM_RES["jpeg"],
                      WM_RES["recovered"]))
    else:
        wm_rows = wm_kpis = ""
    if WM_ERR:
        wm_kpis = ("<p class=fail>WATERMARK PROBE FAILED (honest "
                   "failure, no fake PASS): %s</p>" % esc(WM_ERR))
    wm_dual = esc(
        "dual-track AIGC labeling: explicit track = ugc config.json "
        "L%d ai_label_text (rendered verbatim below) + pipeline.py "
        "L%d ai_label draft field; implicit track = this card's "
        "embedded 256-bit label, spec on disk = %s "
        "(docs/spec/implicit-watermark-verify.md)"
        % ((WM_RES or {}).get("cfg_line", -1),
           (WM_RES or {}).get("pipe_line", -1),
           bool((WM_RES or {}).get("doc_on_disk"))))
    wm_compl = "".join(
        "<li><b>%s</b>&#65306;%s</li>" % (esc(n), esc(t))
        for n, t in [
            ("AIGC", str(ucfg.get("compliance", {}).get(
                "ai_label_text", ""))),
            ("disclaimer", str(ucfg.get("compliance", {}).get(
                "disclaimer", ""))),
            ("[needs-CEO]", str(ucfg.get("params_status", ""))),
            ("msgSecCheck front gate", str(ucfg.get("gate", {}).get(
                "note", ""))),
        ])
    wm_defer = esc(
        "production wiring stays deferred to the bootstrap window "
        "(R321 AC-W2 note): the implicit track is proven here in the "
        "sandbox; wiring generated-content surfaces to the embed call "
        "starts only when the CEO physical items (server / platform "
        "credentials) arrive -- the account domain is never "
        "self-served.")

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
card (R945) &middot; v0.9 publishing research card (R946) &middot;
v0.10 token ledger core card (R965) &middot; v0.11 UGC pipeline core
card (R968) &middot; v0.12 AIGC implicit watermark card
(R975) &middot; v0.13 live room conversion card
(R977) &middot; v0.14 city props card
(R978) &middot; v0.15 creator incentive card
(R980) &middot; v0.16 strategy observation card
(R984) &middot; v0.17 studio onboarding card
(R986) &middot; v0.18 ad slot card
(R987)</span></header>

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

<div class="card"><h2>Token Ledger Core Face (P-47-2 dual-entry, live
probe)</h2>
<p class=kv>The REAL ledger product and reconcile engine are imported
from src/sandbox/ledger/ and run in-process at render time on a
throwaway probe database -- every number below is computed by the
ledger, never canned.</p>
__TL_KPIS__
<table><tr><th>account</th><th>balance</th><th>role in the probe</th></tr>
__TL_ROWS__</table>
<p class=kv>__TL_SUM__</p>
<p class=kv>__TL_GATE__</p>
<p class=kv>__TL_SPEND__</p>
<h3 style="margin:14px 0 8px">Reconcile engine verdict (eight checks on
the probe database)</h3>
__TL_RECON__
<h3 style="margin:14px 0 8px">Tamper control (database copy, one entry
amount +1, same engine re-run)</h3>
__TL_TAMPER__
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__TL_COMPL__</ul>
<p class=kv>Probe chain: census-bound onboarding &gt; authorized
three-pool mint (equity:auth counterparty) &gt; fiat-side stand-in
funding &gt; gated reward (refused then granted) &gt; spend closing
the loop into pool:reserve &gt; reconcile &gt; tamper control.</p></div>

<div class="card"><h2>UGC + msgSecCheck Pipeline Core Face (P-47-3
intake, live probe)</h2>
<p class=kv>The REAL intake pipeline (src/sandbox/ugc/pipeline.py;
SecGate referenced from the lobby product; L1 local wordlist per the
OH-20261002 adoption) is imported and run in-process at render time on
a throwaway database -- every outcome below is computed by the
pipeline, never canned.</p>
__UG_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__UG_ROWS__</table>
<p class=kv>state machine (constitutional order): intake &gt; gate 1
(pass | review | risky) &gt; gate 2 (non-advisory) &gt; routing &gt;
noise triage &gt; pooled &gt; drafted (rule template, zero LLM) &gt;
final_review (small ideas: L0 self-decide; landfall scale:
needs_ceo_review, CEO approval only) &gt; adopted | rejected &gt;
chronicle.</p>
<p class=kv>__UG_POOL__</p>
__UG_EXPORT__
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__UG_COMPL__</ul>
<p class=kv>__UG_PROV__</p>
<p class=kv>Probe fixtures: preview/ugc-pipeline-nodes.json
(caller-supplied, single source); the sandbox keeps the wordlist-mock
gate until the platform credentials (CEO physical items) arrive -- the
production door stays closed until then (AC-UP1).</p></div>

<div class="card"><h2>AIGC Implicit Watermark Face (P-47-3c, live
probe)</h2>
<p class=kv>The REAL implicit-labeling capability (local pip
guofei9987/blind_watermark, MIT, OH-20260926 five-gate adoption) runs
once in-process at server start on a deterministic throwaway image --
every verdict below is computed by the library, never canned; a
server restart re-runs the probe. The watermark suite files stay
untouched (suite calibration fixtures are imported, not copied).</p>
__WM_KPIS__
<table><tr><th>#</th><th>probe leg</th><th>computed outcome</th></tr>
__WM_ROWS__</table>
<p class=kv>__WM_DUAL__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__WM_COMPL__</ul>
<p class=kv>__WM_DEFER__</p></div>

<div class="card"><h2>Live Room Conversion Face (slow-live cart,
live probe)</h2>
<p class=kv>The REAL conversion-piece product (src/sandbox/liveroom/
liveroom.py over the P-47-2 ledger + the lobby SecGate wordlist gate,
all imported, never copied) runs in-process at render time on a
throwaway probe database -- every reading below is computed by the
product modules, never canned. Division of labor: the live account is
a BigStream asset face and broadcast ops belong to BigCompute risk
control; this card shows only this company's in-room conversion
supply face (BLUEPRINT sec.4: the live room carries the cart).</p>
__LR_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__LR_ROWS__</table>
<p class=kv>__LR_FUNNEL__</p>
<h3 style="margin:14px 0 8px">Session transcript (compliance spine:
config disclaimer first and last, AI rows labeled)</h3>
__LR_TRANS__
<p class=kv>__LR_HARD__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__LR_COMPL__</ul>
<p class=kv>Probe prices (1990 / 990 cents) are caller-supplied
sandbox values, not pricing decisions; raw spend tx ids contain
timestamps and are never rendered -- the audit face shows the
bound-debit verification instead.</p></div>

<div class="card"><h2>City Props Face (cosmetic + consumable inventory,
live probe)</h2>
<p class=kv>The REAL city props/cosmetics product (src/sandbox/ledger/
props.py over the P-47-2 token ledger, both imported, never copied)
runs in-process at render time on a throwaway probe database --
every reading below is computed by the product modules, never canned.
This is the in-city economy face behind the BLUEPRINT sec.4.5 price
lines: a cosmetic buys as a permanent entitlement (one per account),
a prop buys as consumable credits (re-purchasable).</p>
__PP_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__PP_ROWS__</table>
<p class=kv>__PP_INV__</p>
<p class=kv>__PP_AUDIT__</p>
<p class=kv>__PP_HARD__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__PP_COMPL__</ul>
<p class=kv>Probe prices are caller-supplied sandbox values, not
pricing decisions; raw spend tx ids contain timestamps and are never
rendered -- the audit face shows the bound-debit verification
instead.</p></div>

<div class="card"><h2>Creator Incentive Face (co-create revenue
share, live probe)</h2>
<p class=kv>The REAL UGC creator incentive gradient allocator
(src/sandbox/ledger/incentive.py over the P-47-2 token ledger, both
imported, never copied) runs in-process at render time on a
throwaway probe database -- every reading below is computed by the
product modules, never canned. This is the ecosystem layer of the
BLUEPRINT sec.4 co-creation revenue-share mechanism: adopted
co-creations earn window payouts out of the share pool through a
decreasing-marginal anti-farm gradient, a per-creator collar and a
window budget cap with zero-rounding-loss integer landing.</p>
__IC_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__IC_ROWS__</table>
<p class=kv>__IC_GRAD__</p>
<p class=kv>__IC_JOIN__</p>
<p class=kv>__IC_HARD__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__IC_COMPL__</ul>
<p class=kv>Gradient bands, collar and budget are sandbox-only probe
params; real parameter adoption (share ratios, settlement period,
redemption threshold) stays a [needs-CEO] P1 approval face and no
incentive key ships in any config file. Raw tx ids are never
rendered (determinism) -- the audit face shows the ref-bound join
verification instead.</p></div>

<div class="card"><h2>Strategy Observation Face (co-create paywall,
live probe)</h2>
<p class=kv>The REAL paid strategy-observation face
(src/sandbox/ledger/observation.py over the P-47-2 token ledger, both
imported, never copied) runs in-process at render time on a
throwaway probe database -- every reading below is computed by the
product modules, never canned. This is the BLUEPRINT sec.4 C-end
line-4 strategy co-creation paid-observation canon (a core revenue
line assigned to this company by D-20260924-10): results-only
viewing of registered co-created strategies, no source code, one
permanent single-strategy grant and one monthly unlimited pass,
each purchase bound to exactly one token spend.</p>
__OB_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__OB_ROWS__</table>
<p class=kv>__OB_SCOPE__</p>
<p class=kv>__OB_AUDIT__</p>
<p class=kv>__OB_HARD__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__OB_COMPL__</ul>
<p class=kv>Probe prices (990 / 1990 tokens) mirror the 9.9 / 19.9
CNY canon anchors and are caller-supplied sandbox values, not
pricing decisions; raw tx ids are never rendered (determinism) --
the audit face shows the bound-debit verification instead.</p></div>

<div class="card"><h2>Studio Onboarding Face (B1/B2 annual fee,
live probe)</h2>
<p class=kv>The REAL studio-onboarding annual-fee face
(src/sandbox/ledger/studio.py over the venue occupancy engine and
the P-47-2 token ledger, all imported, never copied) runs
in-process at render time on a throwaway probe database -- every
reading below is computed by the product modules, never canned.
This is the BLUEPRINT sec.4 B-side onboarding canon: B1 game-studio
9,800 CNY/year and B2 quant-studio / researcher 19,800 CNY/year,
joint delivery in one registry -- each onboarding books exactly one
token spend and the seat rides the venue storefront exclusivity
gate.</p>
__ST_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__ST_ROWS__</table>
<p class=kv>__ST_SCOPE__</p>
<p class=kv>__ST_AUDIT__</p>
<p class=kv>__ST_HARD__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__ST_COMPL__</ul>
<p class=kv>Probe prices (9800 / 19800 tokens) mirror the B1 / B2
canon anchors and are caller-supplied sandbox values, not pricing
decisions; raw tx ids are never rendered (determinism) -- the audit
face shows the bound-debit verification instead.</p></div>

<div class="card"><h2>Ad Slot Face (B3 virtual exhibition, live
probe)</h2>
<p class=kv>The REAL virtual-exhibition ad-slot face
(src/sandbox/ledger/ads.py over the venue occupancy engine and the
P-47-2 token ledger, all imported, never copied) runs in-process at
render time on a throwaway probe database -- every reading below is
computed by the product modules, never canned. This is the
BLUEPRINT sec.4 B-side ad-slot canon: the QUANT giant-screen
carousel (capacity-bounded rotation, booking order = lineup order),
the building naming right (exclusive, one holder per window) and
the lobby splash (exclusive) -- every booking books exactly one
token spend and rides the venue gates.</p>
__AD_KPIS__
<table><tr><th>#</th><th>probe action</th><th>live outcome</th></tr>
__AD_ROWS__</table>
<p class=kv>__AD_SCOPE__</p>
<p class=kv>__AD_AUDIT__</p>
<p class=kv>__AD_HARD__</p>
<h3 style="margin:14px 0 8px">Compliance (persistent, from config)</h3>
<ul>__AD_COMPL__</ul>
<p class=kv>Probe prices (2000 / 10000 / 5000 tokens) mirror the
B3 canon anchors and are caller-supplied sandbox values, not
pricing decisions; raw tx ids are never rendered (determinism) --
the audit face shows the bound-debit verification instead.</p></div>

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

<div class="card"><h2>__PB_TITLE__</h2>
<p class=kv>__PB_SOURCE__</p>
<p class=kv>__PB_HONEST__</p>
__PB_FACES__
<h3 style="margin:14px 0 8px">__PB_DTITLE__</h3>
<table><tr>__PB_DHEAD__</tr>__PB_DROWS__</table>
<p class=fail>__PB_BLOCKED__</p>
<h3 style="margin:14px 0 8px">__PB_CTITLE__</h3><ul>__PB_COMPL__</ul>
<p class=kv>audit P-2026-10-02-02 P2-9 residual three faces answered
[needs-CEO]; structural baseline research, zero invented numbers,
zero execution; sync-gated verbatim from the research canon.</p></div>

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
        "__TL_KPIS__": tl_kpis,
        "__TL_ROWS__": tl_rows,
        "__TL_SUM__": tl_sum,
        "__TL_GATE__": tl_gate,
        "__TL_SPEND__": tl_spend,
        "__TL_RECON__": tl_recon_html,
        "__TL_TAMPER__": tl_tamper_html,
        "__TL_COMPL__": tl_compl,
        "__UG_KPIS__": ug_kpis,
        "__UG_ROWS__": ug_rows,
        "__UG_POOL__": ug_pool,
        "__UG_EXPORT__": ug_export,
        "__UG_COMPL__": ug_compl,
        "__UG_PROV__": ug_prov,
        "__WM_KPIS__": wm_kpis,
        "__WM_ROWS__": wm_rows,
        "__WM_DUAL__": wm_dual,
        "__WM_COMPL__": wm_compl,
        "__WM_DEFER__": wm_defer,
        "__LR_KPIS__": lrv_kpis,
        "__LR_ROWS__": lrv_rows,
        "__LR_FUNNEL__": lrv_funnel,
        "__LR_TRANS__": lrv_trans,
        "__LR_HARD__": lrv_hard,
        "__LR_COMPL__": lrv_compl,
        "__PP_KPIS__": ppv_kpis,
        "__PP_ROWS__": ppv_rows,
        "__PP_INV__": ppv_inv,
        "__PP_AUDIT__": ppv_audit,
        "__PP_HARD__": ppv_hard,
        "__PP_COMPL__": ppv_compl,
        "__IC_KPIS__": icv_kpis,
        "__IC_ROWS__": icv_rows,
        "__IC_GRAD__": icv_grad,
        "__IC_JOIN__": icv_join,
        "__IC_HARD__": icv_hard,
        "__IC_COMPL__": icv_compl,
        "__OB_KPIS__": ob_kpis,
        "__OB_ROWS__": ob_rows,
        "__OB_SCOPE__": ob_scope,
        "__OB_AUDIT__": ob_audit,
        "__OB_HARD__": ob_hard,
        "__OB_COMPL__": ob_compl,
        "__ST_KPIS__": st_kpis,
        "__ST_ROWS__": st_rows,
        "__ST_SCOPE__": st_scope,
        "__ST_AUDIT__": st_audit,
        "__ST_HARD__": st_hard,
        "__ST_COMPL__": st_compl,
        "__AD_KPIS__": ad_kpis,
        "__AD_ROWS__": ad_rows_html,
        "__AD_SCOPE__": ad_scope,
        "__AD_AUDIT__": ad_audit,
        "__AD_HARD__": ad_hard,
        "__AD_COMPL__": ad_compl,
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
        "__PB_TITLE__": esc(pb["card_title"]),
        "__PB_SOURCE__": esc(pb["source_note"]),
        "__PB_HONEST__": esc(pb["honest_note"]),
        "__PB_FACES__": pb_face_html,
        "__PB_DTITLE__": esc(pb["decision_title"]),
        "__PB_DHEAD__": pb_dec_head,
        "__PB_DROWS__": pb_dec_rows,
        "__PB_BLOCKED__": esc(pb["blocked_note"]),
        "__PB_CTITLE__": esc(pb["compliance_title"]),
        "__PB_COMPL__": pb_compl,
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
