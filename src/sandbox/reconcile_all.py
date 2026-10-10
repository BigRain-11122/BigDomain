"""Product health-check runner (BigDomain explore-line item #9, R594;
pay/member standalone-reconcile extension, R595 follow-up row;
five-suite fan-out expansion, R1063 - benchgate/citymodel/compliance/
minors wiring, closing the drift between this runner's fan-out and the
shipped modules).

One command = the full sandbox regression fan-out (thirty-nine
acceptance suites, 420 pre-registered criteria in total) plus the
standalone reconcile product face for all three bookkeeping domains,
each with a clean/tamper dual control:

  ledger  demo built via the ledger public API  -> reconcile exit 0,
          tampered copy (materialized balance +1) -> exit 2
  pay     demo built via the pay public API (orders + mock-callback
          grant chain + ledger conversion bridge) -> reconcile exit 0,
          tampered copy (granted order amount_cent +1) -> exit 2
  member  demo built via the member public API (activate / consume /
          refund / voucher lifecycle on a real pay grant) ->
          reconcile exit 0, tampered copy (one credits audit row
          deleted) -> exit 2

Live-db passthrough evaluation (R595 AC-RA10, honest conclusion): all
three reconcile CLIs already accept external database paths (ledger
and pay via positional argv, member via argparse flags); the demo dual
controls below run them against throwaway tmp-dir databases, which is
the passthrough proof - production bootstrap passes real db paths
through the same arguments, no new CLI surface is needed now.

Suite scenario logic stays inside each acceptance suite - this
runner orchestrates, it does not duplicate (no-reinvent-wheel law).
Pre-registered criteria: AC-RA1..RA5 = src/os/backlog.md R594 row;
AC-RA6..RA10 = src/os/backlog.md R595 row.

Usage:
    python reconcile_all.py [evidence_log_path]
(the optional path makes this runner tee its own utf-8 evidence log
while still streaming to the console; pass e.g.
qa/reconcile-all-R595.log)

Interpreter: run under the full-assembly python (the system install
carrying cv2, cryptography, blind_watermark, numpy and websockets).
The lobby suite's minimal .venv (pip + websockets only) is a
single-suite assembly: it lacks the watermark / pay-v3-real
dependencies, and on this machine it is denied writes to the system
temp dir so tempfile.gettempdir() falls back to CWD (R684 triage
verdict; qa/runner-triage-R684.log).
"""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "ledger")
PAY = os.path.join(BASE, "pay")
MEMBER = os.path.join(BASE, "member")
LOBBY = os.path.join(BASE, "lobby")


def _wire_paths():
    """Put every product dir on sys.path (deterministic front order:
    lobby, member, pay, ledger). No module-name collisions among the
    in-process imports (store/sec_gate resolve to lobby only, catalog
    and member to member only, orders and adapters to pay only, ledger
    to ledger only); the per-domain reconcile scripts are never
    imported in-process - they run as child processes below."""
    for d in (LEDGER, PAY, MEMBER, LOBBY):
        if d not in sys.path:
            sys.path.insert(0, d)


def _load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)

SUITES = [
    # (label, suite path relative to the sandbox root, expected criteria)
    ("lobby", os.path.join("lobby", "test_client.py"), 16),
    ("ledger", os.path.join("ledger", "test_ledger.py"), 11),
    ("ledger-props", os.path.join("ledger", "test_props.py"), 7),
    ("ledger-incentive",
     os.path.join("ledger", "test_incentive.py"), 7),
    ("ledger-settlement",
     os.path.join("ledger", "test_settlement.py"), 7),
    ("ledger-venue", os.path.join("ledger", "test_venue.py"), 7),
    ("ledger-collectibles",
     os.path.join("ledger", "test_collectibles.py"), 7),
    ("ledger-expedite",
     os.path.join("ledger", "test_expedite.py"), 7),
    ("ledger-ads",
     os.path.join("ledger", "test_ads.py"), 7),
    ("ledger-observation",
     os.path.join("ledger", "test_observation.py"), 7),
    ("ledger-identity",
     os.path.join("ledger", "test_identity.py"), 7),
    ("ledger-studio",
     os.path.join("ledger", "test_studio.py"), 7),
    ("ledger-metered",
     os.path.join("ledger", "test_metered.py"), 7),
    ("ledger-reports",
     os.path.join("ledger", "test_reports.py"), 7),
    ("ledger-effects",
     os.path.join("ledger", "test_effects.py"), 7),
    ("ledger-growth-archive",
     os.path.join("ledger", "test_growth_archive.py"), 7),
    # R1689 resident AI companion subscription face: monthly pass
    # idempotency + msgSecCheck pre-gate (injected SecGate, reference
    # not copy) + structural AIGC label + append-only memory archive
    # (AC-CP1..CP7 pre-registered in state/queue/explore.md).
    ("ledger-companion",
     os.path.join("ledger", "test_companion.py"), 7),
    # R1691 UGC template marketplace face: listing idempotency +
    # msgSecCheck pre-gate (injected SecGate, reference not copy) +
    # integer-law revenue split (exactly one creator share tx per
    # purchase, floor+ordered-remainder zero loss, DB CHECK) +
    # purchaser-only immutable rating (AC-TM1..TM7 pre-registered
    # in state/queue/explore.md).
    ("ledger-tmarket",
     os.path.join("ledger", "test_tmarket.py"), 7),
    # R1693 solar-term / festival limited-event face: ads/venue
    # schedule-window convention (inclusive on both edges) +
    # per-account purchase-limit gate + event-wide edition cap (all
    # reject BEFORE the spend) + event-commemorative collectibles
    # linkage through the collectibles public API (AC-FE1..FE7
    # pre-registered in state/queue/explore.md).
    ("ledger-festival",
     os.path.join("ledger", "test_festival.py"), 7),
    # R1695 enterprise-showroom SaaS package face: the annual bundle
    # (storefront lease + giant-screen carousel rotation + visitor-
    # tour stop) granted through the venue/ads public APIs (two fee
    # rails, one spend each), replay/active-contract/subscriber-cap/
    # rotation-pre-read gates all before the first spend, platform-
    # side posture per Advertising-Law Article 56 (AC-SR1..SR7
    # pre-registered in state/queue/explore.md).
    ("ledger-showroom",
     os.path.join("ledger", "test_showroom.py"), 7),
    # R1696 sister-city cross-city visit face: twin-pair schedule
    # window registration + visit pass (one pass per resident per
    # pairing, window edges inclusive, replay/dup gates before the
    # spend) + merchant cross-city exposure with pair-wide slot cap +
    # window settlement through the SettlementFace public API
    # build/verify manifest reference (AC-SC1..SC7 pre-registered in
    # state/queue/explore.md).
    ("ledger-sistercity",
     os.path.join("ledger", "test_sistercity.py"), 7),
    # R1700 API open-platform developer-ecosystem face: the three
    # rings (per-developer deterministic key issuance through the
    # metered register_client public API, per-key UTC-month call
    # quota counted over immutable rows with zero UPDATE, billing
    # delegated wholesale to the metered public API) with every
    # reject firing before the charge (AC-DK1..DK7 pre-registered
    # in state/queue/explore.md).
    ("ledger-apidev",
     os.path.join("ledger", "test_apidev.py"), 7),
    # R1711 apidev key lifecycle: revocation fail-closed before the
    # billing ring, rotation with contract + balance carry-over
    # (same metered client) and anti-evasion window inheritance
    # over the full rotate_in ancestry, lifecycle events in a
    # separate sqlite file (zero ledger-schema touch)
    # (AC-KR1..KR8 pre-registered in state/queue/tech.md).
    ("ledger-apidev-lifecycle",
     os.path.join("ledger", "test_apidev_lifecycle.py"), 8),
    # R1712 apidev minute-window rate ring: per-key per-UTC-minute
    # cap (minute_cap, 0 = dark, legacy issue_key form unchanged),
    # rate gate between the kind gate and the monthly quota gate,
    # fired before the billing ring; minute/monthly readings stay
    # separate; ancestry (rotate_in chain) counted on the minute
    # ring too (rotation never resets it); rate gate precedes the
    # dup pre-check (AC-RT1..RT7 pre-registered in
    # state/queue/tech.md).
    ("ledger-apidev-rate",
     os.path.join("ledger", "test_apidev_rate.py"), 7),
    # R1728 apidev reject-tally read face: key-attributed call-chain
    # rejects (revoked/kind/rate/quota/dup gates + billing-ring
    # metered codes) land one immutable diagnostic event each in a
    # separate sqlite store (api_rejects.db, single writer, zero
    # ledger-schema touch); recording is best-effort (primary
    # reject contract sacred); tally read faces (reject_tally,
    # key_view, dev_board) aggregate at read time GROUP BY reason
    # over the current UTC month window; rotation attributes to
    # the exact key (AC-RJ1..RJ7 pre-registered in
    # state/queue/tech.md).
    ("ledger-apidev-reject",
     os.path.join("ledger", "test_apidev_reject.py"), 7),
    # R1729 apidev usage-log read cap: optional limit parameter
    # (0 = full-log behavior byte-stable); limit>0 bounds the
    # response to the most recent limit rows and adds the
    # overflow block (limit/total/returned/truncated); the
    # truncated window is the exact tail of the ascending
    # (called_utc, call_ref) order; key gate before argument
    # gate; dead keys stay readable (AC-UL1..UL7 pre-registered
    # in state/queue/tech.md).
    ("ledger-apidev-usagelog",
     os.path.join("ledger", "test_apidev_usagelog.py"), 7),
    # R1730 apidev reject-tally window-parameterized read: the
    # public reject_tally face takes an optional explicit
    # "YYYY-MM" window (None = current UTC month, byte-stable
    # with R1728); strict format gate fail-closed after the key
    # gate; historical/future windows are honest reads over the
    # immutable rows; embedded faces (key_view, dev_board) keep
    # the current-month default; dead keys stay readable
    # (AC-RJW1..RJW7 pre-registered in state/queue/tech.md).
    ("ledger-apidev-rejectwin",
     os.path.join("ledger", "test_apidev_rejectwin.py"), 7),
    # R1732 apidev usage-log window-filtered read: optional
    # explicit "YYYY-MM" window on the public usage_log face
    # (None = all-months behavior byte-stable with R1729); the
    # window filter applies before COUNT/LIMIT so the overflow
    # block total is the in-window row count; explicit-window
    # envelope adds an additive window key; strict format gate
    # fail-closed after the key gate and the limit gate; dead
    # keys stay readable (AC-UW1..UW7 pre-registered in
    # state/queue/tech.md).
    ("ledger-apidev-usagewin",
     os.path.join("ledger", "test_apidev_usagewin.py"), 7),
    # R1735 apidev usage by-kind window-count read: the read-face
    # family's third symmetric member (reject_tally counts by
    # reason, usage_log returns rows, this counts by API kind) --
    # the developer panel's "which kinds am I using this month"
    # face that quota_used's single total cannot answer; default
    # None reads the current UTC month through the same
    # _window_utc source as the quota ring, an explicit "YYYY-MM"
    # reads any month over the immutable rows; read-time GROUP BY
    # kind COUNT, zero new tables, zero UPDATE; exact-key
    # attribution (rotation does not inherit ancestor kinds);
    # embedded faces (key_view, dev_board) gain the current-month
    # profile additively and stay window-free (AC-RJW4 law)
    # (AC-UK1..UK7 pre-registered in state/queue/tech.md).
    ("ledger-apidev-usagekind",
     os.path.join("ledger", "test_apidev_usagekind.py"), 7),
    ("tourstate", os.path.join("tourstate", "test_tourstate.py"), 7),
    # R1702 ingest_lobby batched gate window: L1-first per row, one
    # check_batch call per (source, actor) group chunk, window-order
    # replay (AC-IL1..IL7 pre-registered in state/queue/tech.md)
    # R1703 ingest window watermark cap: max_ingest_window config
    # cap, beyond-cap rows stay unmarked and re-read next window
    # (AC-WC1..WC6 pre-registered in state/queue/tech.md)
    # R1704 window-order stabilization: explicit rowid tiebreak on the
    # intake reader, deterministic cap slicing under ts ties
    # (AC-OS1..OS5 pre-registered in state/queue/tech.md)
    ("ugc", os.path.join("ugc", "test_ugc.py"), 37),
    # R1681 sec-gate batch + degradation face: p95 profile, persistent
    # degraded banner queue (own sqlite file, R1254 precedent)
    ("ugc-sec-batch", os.path.join("ugc", "test_sec_batch.py"), 7),
    ("pay", os.path.join("pay", "test_pay.py"), 16),
    ("pay-v3", os.path.join("pay", "test_pay_v3.py"), 14),
    ("pay-v3-real", os.path.join("pay", "test_pay_v3_real.py"), 9),
    # R1678 V3 window boundary: inclusive delta==W both edges, one-past
    # rejects, per-channel parameterized boundary, in-window burned-
    # nonce replay gate, same boundary under verify_mode rsa
    # (AC-V3W1..W6 pre-registered in state/queue/tech.md).
    ("pay-v3-window", os.path.join("pay", "test_pay_v3_window.py"), 6),
    # R1706 payment-state notification face: W15/W10 channel consumption
    # (payment-success/refund dual timepoints, template-review gate
    # fail-closed pending CEO template ids, authorization budget,
    # daily cap, skipped_* banner queue; AC-PN1..PN7 pre-registered
    # in state/queue/tech.md)
    ("pay-notify", os.path.join("pay", "test_pay_notify.py"), 7),
    # R1718 orders.py notify wiring (R1706 successor): post-commit
    # payment-success + refund-close notice attempts, never-break
    # degradation with envelope evidence, close_refund face
    # (AC-NW1..NW7 pre-registered in state/queue/tech.md).
    ("pay-notify-wiring", os.path.join("pay", "test_pay_notify_wiring.py"), 7),
    # R1719 W15 authorization report face: closes the grant_authorization
    # zero-caller gap (pay-domain bearer; lobby forwarding rejected -
    # ephemeral lobby actors cannot key budget the pay send path
    # consumes). authorize.py wraps the notify face (single-writer
    # discipline unchanged); notify.py gains the additive budget_face
    # read + deterministic same-second grant-id disambiguation
    # (R1719 suite first-run discovery). End-to-end: authorized budget
    # is truly consumed by the R1718-wired send path (AC-AZ1..AZ7
    # pre-registered in state/queue/tech.md).
    ("pay-authorize", os.path.join("pay", "test_authorize.py"), 7),
    # R1723 refund conversion-share clawback (R1721 successor): the
    # token-side reverse of the pay_conversion forward entry on a
    # refund close - no overdraft ever (claw capped at min(forward,
    # current balance), the consumed portion stays pool-side via
    # spend->pool:reserve so the pool is net-whole), forward tx is the
    # amount authority (zero caller amounts), reverse books as
    # ref='refund:'+order_id / ref_type='order' / type='adjust' with
    # provenance memo, UNIQUE(ref,ref_type) = natural idempotency;
    # caller-built caller-owned wiring (conversion_clawback=None =
    # shipped byte-stable) + never-break post-commit + heal face
    # (AC-RC1..RC8 pre-registered in state/queue/tech.md).
    ("ledger-clawback", os.path.join("pay", "test_clawback_wiring.py"), 8),
    ("member", os.path.join("member", "test_member.py"), 16),
    ("member-entry", os.path.join("member", "test_entry_tier.py"), 7),
    # R1721 close_refund entitlement-recovery linkage (R1718 successor):
    # pay read-face refunded annotation (status-derived, zero schema
    # touch), member activation gate, revoke_refunded face (existing
    # active->expired legal edge + refund-recovery audit provenance),
    # birth-cert re-judge on non-refunded grants, caller-built recovery
    # wiring with never-break degradation + crash-window heal
    # (AC-RR1..RR7 pre-registered in state/queue/tech.md).
    ("member-refund-recovery",
     os.path.join("member", "test_refund_recovery.py"), 7),
    ("watermark", os.path.join("watermark", "test_watermark.py"), 5),
    ("watermark-robust",
     os.path.join("watermark", "test_watermark_robust.py"), 6),
    # R1680 DCT-domain parameter sweep: quantization-step (d1) x
    # repetition-factor (wm_size) grid, BER profile + PSNR cost +
    # near-survival band map (AC-DS1..DS6 pre-registered in
    # state/queue/tech.md; AC-DS7 = round-carried, AC-W4 precedent).
    ("watermark-sweep",
     os.path.join("watermark", "test_watermark_sweep.py"), 6),
    # R1707 scale-family template-alignment recovery experiment
    # (R1680 negative-verdict successor; verdicts recorded in suite)
    ("watermark-scale-recover",
     os.path.join("watermark", "test_scale_recover.py"), 7),
    # R1725 unknown-factor grid: four non-integer factors {0.7x/0.85x/
    # 1.1x/1.5x} through the full blind search domain (0.3, 2.2);
    # hit-rate reading, negative verdicts lawful (AC-UKF1..UKF7
    # pre-registered in state/queue/tech.md).
    ("watermark-scale-unknown",
     os.path.join("watermark", "test_scale_unknown.py"), 6),
    ("dual-track", os.path.join("watermark", "test_dual_track.py"), 7),
    ("opsreview", os.path.join("opsreview", "test_opsreview.py"), 7),
    ("liveroom", os.path.join("liveroom", "test_liveroom.py"), 10),
    # R1063 fan-out expansion: five suites shipped after R595 but never
    # wired into this runner (the fan-out had drifted behind the shipped
    # modules). Pure wiring - the suite files themselves are unchanged.
    # benchgate/compliance run unittest-style (exit 0 + "OK", zero
    # PASS-lines by design); their criteria counts are their test-method
    # counts. citymodel/minors/minors-wiring use the PASS-line convention.
    ("benchgate", os.path.join("benchgate", "test_bench_gate.py"), 11),
    ("citymodel", os.path.join("citymodel", "test_scenario.py"), 10),
    ("compliance",
     os.path.join("compliance", "test_sku_compliance_map.py"), 15),
    ("minors", os.path.join("minors", "test_minors.py"), 19),
    ("minors-wiring", os.path.join("minors", "test_wiring.py"), 70),
    # R1676 schema-migrate: sandbox-wide schema versioning migrator
    # (PRAGMA user_version chain, ALTER-free rebuild, dual-phase verify;
    # AC-LM1..LM11 pre-registered in state/queue/tech.md).
    ("schema-migrate", "test_schema_migrate.py", 21),
    # R1713 fingerprint-regen: baseline fingerprint regenerator for
    # migration_chains.json (live-constructor re-derivation, drift is
    # FAIL; AC-BF1..BF7 pre-registered in state/queue/tech.md).
    ("fingerprint-regen", "test_fingerprint_regen.py", 16),
    # R1714 reconcile-daily-sentinel: schema-drift sentinel wired into
    # the daily wrapper (fingerprint_regen --check appended to the dated
    # evidence log; daily exit aggregation; AC-FS1..FS6 pre-registered in
    # state/queue/tech.md). R1737 extends with the elapsed-tail checks
    # (fs7/fs8, AC-SN1) -> criteria 6->8.
    ("reconcile-daily-sentinel", "test_reconcile_daily_sentinel.py", 8),
    # R1708 suite-matrix default-evidence discovery-face fix (R1695
    # naming gap: old face globbed reconcile-all-R*.log only; new face
    # walks qa/*.log newest-first with four fail-closed eligibility
    # checks; AC-SM1..SM7 pre-registered in state/queue/tech.md).
    # R1709 AC-TIE1..TIE7: same-mtime tie-break coverage (+5 cases).
    ("suite-matrix-discovery", "test_suite_matrix.py", 15),
    # R1715 runner-profile daily variant: --daily face (discovery
    # restricted to reconcile-daily-*.log evidence, separate
    # runner-profile-daily-baseline.json; sentinel-section parser
    # inertia; AC-RD1..RD6 pre-registered in state/queue/tech.md).
    # R1737 extends with the sentinel-elapsed consumption checks
    # (sn1..sn4, AC-SN2..SN4) -> criteria 8->12.
    ("runner-profile-daily", "test_runner_profile_daily.py", 12),
    # R1733 reconcile-daily profile step: runner_profile --daily --check
    # appended to the dated evidence log after the sentinel; observation
    # window records the profile exit without gating the day (AC-PD1..PD7
    # pre-registered in state/queue/tech.md).
    ("reconcile-daily-profile", "test_reconcile_daily_profile.py", 7),
]

FAILS = 0


class Tee(object):
    """Stream to the console and mirror everything to a utf-8 log file."""

    def __init__(self, path):
        self.file = open(path, "w", encoding="utf-8", newline="\n")
        self.stdout = sys.stdout

    def write(self, data):
        self.file.write(data)
        try:
            self.stdout.write(data)
        except UnicodeEncodeError:
            # console is locale-encoded (cp936 here); never let an
            # echo kill the run - lossy for console only, file stays
            # full-fidelity utf-8
            enc = getattr(self.stdout, "encoding", None) or "ascii"
            self.stdout.write(
                data.encode(enc, "replace").decode(enc, "replace"))

    def flush(self):
        self.file.flush()
        self.stdout.flush()

    def close(self):
        self.file.close()


def note(ok, line):
    global FAILS
    if not ok:
        FAILS += 1
    print("%s %s" % ("PASS" if ok else "FAIL", line), flush=True)


def run_cmd(cmd, cwd):
    # child pythons emit pipe output in the machine locale (cp936 on
    # this zh-CN Windows) - decode with the same locale, not utf-8
    proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True,
                           errors="replace", cwd=cwd, timeout=300)
    return proc.returncode, proc.stdout or ""


def echo(out):
    for line in out.splitlines():
        print("  | %s" % line)


def phase_suites():
    green = 0
    total = 0
    for label, rel, crit in SUITES:
        path = os.path.join(BASE, rel)
        t0 = time.time()
        code, out = run_cmd([sys.executable, path], cwd=os.path.dirname(path))
        echo(out)
        passes = len(re.findall(r"(?m)^PASS\b", out))
        fails = len(re.findall(r"(?m)^FAIL\b", out))
        total += crit
        ok = code == 0
        if ok:
            green += 1
        note(ok, "suite %s exit=%d pass-lines=%d fail-lines=%d criteria=%d %.1fs"
             % (label, code, passes, fails, crit, time.time() - t0))
    note(green == len(SUITES),
         "suites %d/%d green, expected criteria total=%d"
         % (green, len(SUITES), total))
    return green == len(SUITES)


def build_demo_state(db_path):
    """Canonical ledger demo state via the public API only (reuse law)."""
    sys.path.insert(0, LEDGER)
    import ledger as L  # noqa: E402 (product module, reuse-not-copy)
    with open(os.path.join(LEDGER, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    led = L.Ledger(db_path, cfg)
    led.mint_to_pool("pool:reward", 500, "DEMO-MINT-1")
    led.mint_to_pool("pool:share", 300, "DEMO-MINT-2")
    led.ensure_account("usr:demo1", "AV-DEMO-1")
    led.ensure_account("usr:demo2", "AV-DEMO-2")
    led.grant_reward("usr:demo1", "login", "DEMO-EVT-1")
    led.record_gate_pass("DEMO-EVT-G1")
    led.grant_reward("usr:demo1", "cocreate", "DEMO-EVT-G1")
    led.share_from_pool("pool:share", "usr:demo2", 40, "DEMO-SHARE-1")
    led.spend("usr:demo2", 10, "DEMO-ORDER-1")
    led.close()


def phase_reconcile(tmp):
    db = os.path.join(tmp, "ledger.db")
    build_demo_state(db)
    code, out = run_cmd([sys.executable, os.path.join(LEDGER, "reconcile.py"),
                         db], cwd=LEDGER)
    echo(out)
    note(code == 0 and "RECONCILE PASS" in out,
         "reconcile ledger-demo exit=%d (expect 0, clean eight checks)" % code)
    tampered = os.path.join(tmp, "ledger-tampered.db")
    shutil.copyfile(db, tampered)
    conn = sqlite3.connect(tampered)
    conn.execute("UPDATE ledger_accounts SET balance = balance + 1"
                 " WHERE account_id = 'usr:demo1'")
    conn.commit()
    conn.close()
    code2, out2 = run_cmd([sys.executable, os.path.join(LEDGER, "reconcile.py"),
                           tampered], cwd=LEDGER)
    echo(out2)
    note(code2 == 2 and "RECONCILE FAIL" in out2,
         "reconcile tamper-control exit=%d (expect 2, FAIL detected)" % code2)


def _pay_grant_chain(pay, chans, product_id, avatar, nonce):
    """create -> place -> valid mock callback -> granted (public API
    only); returns the granted order_id (AC-RA6 happy leg)."""
    resp = pay.create_order(product_id, avatar)
    oid = resp["order_id"]
    pay.place_order(oid)
    amount = pay.order_detail(oid)["amount_cent"]
    cb = chans[resp["channel"]].make_callback(oid, amount, nonce)
    pay.handle_callback(cb)
    return oid


def build_pay_demo_state(tmp):
    """Canonical pay demo state via the pay/ledger/lobby public APIs
    only (AC-RA6): two granted orders (the share_observation order
    drives a real conversion-bridge share entry, pack_compute_19_9 a
    plain grant) plus one order left in 'created'."""
    _wire_paths()
    import orders as O                                  # pay product
    import adapters as A                                # pay product
    import store as lobby_store                         # lobby product
    from ledger import Ledger                           # ledger product
    cfg = _load_json(os.path.join(PAY, "config.json"))
    led_cfg = _load_json(os.path.join(LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "pay-events.db"))
    led = Ledger(os.path.join(tmp, "pay-ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-PAY-1", "settlement")
    pay = O.PayOrders(cfg, os.path.join(tmp, "pay.db"), events, led)
    chans = A.from_config(cfg)
    oid_share = _pay_grant_chain(pay, chans, "share_observation",
                                 "AV-PAY-DEMO-1", "n-pay-demo-1")
    oid_pack = _pay_grant_chain(pay, chans, "pack_compute_19_9",
                                "AV-PAY-DEMO-2", "n-pay-demo-2")
    pay.create_order("pack_compute_19_9", "AV-PAY-DEMO-3")  # stays created
    pay.close()
    led.close()
    return {"pay_db": os.path.join(tmp, "pay.db"),
            "ledger_db": os.path.join(tmp, "pay-ledger.db"),
            "config": os.path.join(PAY, "config.json"),
            "tamper_order": oid_pack}


def phase_pay_reconcile(tmp):
    world = build_pay_demo_state(tmp)
    code, out = run_cmd([sys.executable, os.path.join(PAY, "reconcile.py"),
                         world["pay_db"], world["config"], world["ledger_db"]],
                        cwd=PAY)
    echo(out)
    note(code == 0 and "reconcile: PASS checks=6/6" in out,
         "reconcile pay-demo exit=%d (expect 0, clean six checks)" % code)
    tampered = os.path.join(tmp, "pay-tampered.db")
    shutil.copyfile(world["pay_db"], tampered)
    conn = sqlite3.connect(tampered)
    # tamper posture per the suite's AC-Y12 amount family: the amount
    # lock trigger is dropped first (injection posture), then the
    # granted order's locked price is bumped
    conn.execute("DROP TRIGGER trg_order_amount_lock")
    conn.execute("UPDATE pay_orders SET amount_cent = amount_cent + 1"
                 " WHERE order_id = ?", (world["tamper_order"],))
    conn.commit()
    conn.close()
    code2, out2 = run_cmd([sys.executable, os.path.join(PAY, "reconcile.py"),
                           tampered, world["config"], world["ledger_db"]],
                          cwd=PAY)
    echo(out2)
    note(code2 == 2 and "reconcile: FAIL" in out2,
         "reconcile pay-tamper exit=%d (expect 2, FAIL detected)" % code2)


def _tier_products(pcfg):
    """Sandbox dock face (same three rows as the member suite): pay
    price rows whose entitlement keys are the member catalog product
    keys - real tier prices stay a [needs-CEO] approval face."""
    for key, cents in (("tier_experience", 1990), ("tier_mayor", 4990),
                       ("tier_cocreator", 9900)):
        pcfg["products"][key] = {
            "channel": "virtual", "price_cent": cents, "share_tokens": 0,
            "entitlement": "tier:" + key.split("_", 1)[1],
            "copy": "sandbox dock product: %s tier" % key}
    return pcfg


def build_member_demo_state(tmp):
    """Canonical member demo state via the member/pay/ledger public
    APIs only (AC-RA8): mayor-tier activation on a real pay grant,
    consume 7 + refund 5 (journal discipline), voucher text-set and
    use (voucher lifecycle + audit faces)."""
    _wire_paths()
    import member as MB                                # member product
    import orders as O                                 # pay product
    import adapters as A                               # pay product
    import store as lobby_store                        # lobby product
    from ledger import Ledger                          # ledger product
    mcfg = _load_json(os.path.join(MEMBER, "config.json"))
    pcfg = _tier_products(_load_json(os.path.join(PAY, "config.json")))
    led_cfg = _load_json(os.path.join(LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "member-events.db"))
    led = Ledger(os.path.join(tmp, "member-ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-MEMBER-1", "settlement")
    pay = O.PayOrders(pcfg, os.path.join(tmp, "member-pay.db"), events, led)
    chans = A.from_config(pcfg)
    store = MB.MemberStore(mcfg, os.path.join(tmp, "member.db"), pay)
    oid = _pay_grant_chain(pay, chans, "tier_mayor", "AV-MEMBER-DEMO-1",
                           "n-member-demo-1")
    gid = pay.grants_for("AV-MEMBER-DEMO-1")["items"][-1]["grant_id"]
    activated = store.activate(gid, "AV-MEMBER-DEMO-1")
    store.consume_credits("AV-MEMBER-DEMO-1", 7, ref="svc-1",
                          ref_type="service_ticket")
    store.refund_credits("AV-MEMBER-DEMO-1", 5,
                         activated["period_id"], ref="svc-1")
    store.set_voucher_text("AV-MEMBER-DEMO-1", "building_naming",
                           "harbor gate")
    store.use_voucher("AV-MEMBER-DEMO-1", "building_naming")
    store.close()
    pay.close()
    led.close()
    return {"member_db": os.path.join(tmp, "member.db"),
            "pay_db": os.path.join(tmp, "member-pay.db"),
            "ledger_db": os.path.join(tmp, "member-ledger.db"),
            "config": os.path.join(MEMBER, "config.json")}


def phase_member_reconcile(tmp):
    world = build_member_demo_state(tmp)
    args = ["--member-db", world["member_db"], "--pay-db", world["pay_db"],
            "--ledger-db", world["ledger_db"], "--config", world["config"]]
    code, out = run_cmd([sys.executable, os.path.join(MEMBER, "reconcile.py")]
                        + args, cwd=MEMBER)
    echo(out)
    note(code == 0 and "PASS: 6 checks clean" in out,
         "reconcile member-demo exit=%d (expect 0, clean six checks)" % code)
    tampered = os.path.join(tmp, "member-tampered.db")
    shutil.copyfile(world["member_db"], tampered)
    conn = sqlite3.connect(tampered)
    victim = conn.execute("SELECT audit_id FROM member_audit WHERE"
                          " kind = 'credits' LIMIT 1").fetchone()
    conn.execute("DELETE FROM member_audit WHERE audit_id = ?",
                 (victim[0],))
    conn.commit()
    conn.close()
    code2, out2 = run_cmd([sys.executable, os.path.join(MEMBER, "reconcile.py")]
                          + ["--member-db", tampered, "--pay-db",
                             world["pay_db"], "--ledger-db",
                             world["ledger_db"], "--config",
                             world["config"]], cwd=MEMBER)
    echo(out2)
    note(code2 == 2 and "FAIL:" in out2,
         "reconcile member-tamper exit=%d (expect 2, FAIL detected)" % code2)


def main(argv):
    tee = None
    if len(argv) > 1:
        tee = Tee(argv[1])
        sys.stdout = tee
    t0 = time.time()
    suites_ok = phase_suites()
    tmp = tempfile.mkdtemp(prefix="reconcile-all-")
    try:
        phase_reconcile(tmp)
        phase_pay_reconcile(tmp)
        phase_member_reconcile(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILS == 0 and suites_ok:
        print("RUNNER PASS (%d/%d suites green, reconcile controls 6/6, %.1fs)"
              % (len(SUITES), len(SUITES), time.time() - t0), flush=True)
        code = 0
    else:
        print("RUNNER FAIL (%d failed assertions)" % FAILS, flush=True)
        code = 1
    if tee is not None:
        sys.stdout = tee.stdout
        tee.close()
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
