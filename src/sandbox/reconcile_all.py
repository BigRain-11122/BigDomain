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
    # R1773 lobby room-level message read face: per-room chat counts +
    # distinct active-actor aggregation, pure-read derivation on the
    # EventStore (zero UPDATE, standing disclaimer envelope,
    # fail-closed without a wired disclaimer) - AC-S14/S15.
    # R1790 room.board protocol wiring face - AC-S16 (18 -> 19).
    # R1791 room.board optional payload.rooms subscription filter -
    # default absent/None keeps the full board, Python-side
    # order-preserving row filter after the store read face (zero
    # second SQL engine), bad forms fail closed E_BAD_FRAME,
    # explicit [] is an honest empty interest set - AC-S17 (19 -> 20).
    # R1792 event-derived idea pool face: idea_pool_board pure-read
    # derivation over type='idea.submit' rows (restart-surviving
    # replacement for the read reliance on the in-memory
    # proposal_pool stub) + idea.board wire face with the same
    # optional rooms filter law - AC-S18/S19 (20 -> 22).
    # R1869 month-window parameter on both lobby board read faces:
    # window=None keeps the full-history read byte-stable; an
    # explicit "YYYY-MM" window slices the row set by each event's
    # own record-time month (substr(ts_utc,1,7)) before the
    # per-zone aggregation, zone order and envelope untouched; 14
    # bad-window forms reject the dedicated E_LS_BAD_WINDOW
    # fail-closed after the disclaimer gate; pure-read law,
    # determinism and the live-db manual-SQL cross kept -
    # AC-S20/S21/S22 (22 -> 25).
    # R1876 cross-month roll preservation on both lobby board
    # faces: explicit-ts data-driven roll (no frozen clock), the
    # new-month grid is born inside the November window, the
    # October window keeps the pre-roll snapshot byte-identical
    # with bidirectional non-penetration, the default read stays
    # the full-window semantics (both months merged, the two
    # windows partition it exactly) and the immutable events
    # total is kept with the cross-board non-counted rows
    # isolated - AC-S23/S24/S25 (25 -> 28).
    # R1882 read-cap limit parameter on both lobby board read
    # faces: limit=0 sole default sentinel (full read
    # byte-identical), positive int caps to the zone-ascending
    # tail window with the four-key overflow block {limit, total,
    # returned, truncated} (total = windowed full count, never
    # post-truncation), five bad forms fail-closed E_LS_BAD_LIMIT
    # before the window gate, honest-empty four keys, pure-read +
    # live-db cross - AC-S26..S31 (28 -> 34).
    # R1891 board persist example window on both lobby board read
    # faces: close + same-db reopen reproduces every read face
    # (default / cap / window x cap) byte-for-byte (derived-face
    # zero in-memory drift), post-restart new data drifts the
    # default face while old explicit windows stay frozen, a
    # second restart keeps the guarantee, pure-read law across
    # restarts - AC-S32..S38 (34 -> 41).
    # R1892 idem_seen restart semantics window on chat.send: in-TTL
    # replay absorption re-acks the original evt_id, cross-restart
    # replay re-enters the event flow (the in-memory TTL+FIFO cache
    # dies with the process - honest boundary), TTL expiry admits a
    # legitimate resend, FIFO cap eviction is honest - AC-S39..S43
    # (41 -> 46).
    # R1899 idem key binding semantics window on chat.send: the dedup
    # key binds the client id to the exact text (same id + different
    # text = fresh event with both keys coexisting), the cache is
    # server-instance scoped (cross-connection replay absorbs), id
    # and text domains are independent, and the strip/truncate
    # normalization happens before the key digest - AC-S44..S48
    # (46 -> 51).
    # R1915 room.board protocol-face persist across full server
    # process restarts (adjudication: the store-level read-face
    # persist is already in-book via R1891 AC-S32..S38; the genuine
    # zero-in-book surface is the PROTOCOL face with its
    # payload.rooms subscription filter across a ServerProc stop ->
    # same-config same-db same-port restart): pre-restart five-face
    # protocol snapshot (full / filter / empty / None-default, manual
    # SQL cross, month window SQL-derived), restarted process
    # reproduces every protocol read byte-for-byte at the payload
    # level (frame ts_utc/room stripped as envelope noise), new data
    # through the live protocol recomputes (zero cache, existing
    # config-room gate honored), a stopped-window explicit-ts
    # November row (R1876 product path) is born in the new month
    # window while the old month window stays frozen across restart
    # x new data, and a second restart keeps sequential-instance
    # byte identity; pure-read battery + sha256 double-proof hygiene
    # - AC-S49..S54 (51 -> 57).
    ("lobby", os.path.join("lobby", "test_client.py"), 57),
    ("ledger", os.path.join("ledger", "test_ledger.py"), 11),
    ("ledger-props", os.path.join("ledger", "test_props.py"), 7),
    # props persist window: cross-restart byte-identical replay of
    # the inventory/balance read battery, restart-surviving gate
    # probes, post-restart continuation (new spend-bound grant,
    # credit consume + stack re-purchase), frozen provenance faces
    # + dup gate, pure-read law, third instance stability (AC-PSP1..
    # PSP7 pre-registered in state/queue/tech.md).
    ("ledger-props-persist", os.path.join(
        "ledger", "test_props_persist.py"), 7),
    # identity persist window: cross-restart byte-identical replay of
    # the wrapped identity face over venue+props engines (registry
    # immutability, 15 fail-closed probes, zero-cache recompute;
    # AC-IDP1..IDP7 pre-registered in state/queue/tech.md).
    ("ledger-identity-persist", os.path.join(
        "ledger", "test_identity_persist.py"), 7),
    ("ledger-incentive",
     os.path.join("ledger", "test_incentive.py"), 7),
    ("ledger-settlement",
     os.path.join("ledger", "test_settlement.py"), 7),
    # settlement persist window: optional sqlite mirror + read
    # family (manifest_view/claims_view/last_window_id), cross-
    # restart byte-identical replay, chain-anchor survival,
    # five fail-closed probes, default-path zero drift
    # (AC-SEP1..SEP7 pre-registered in state/queue/tech.md).
    ("ledger-settlement-persist", os.path.join(
        "ledger", "test_settlement_persist.py"), 7),
    ("ledger-venue", os.path.join("ledger", "test_venue.py"), 7),
    # venue persist window: cross-restart byte-identical replay of
    # the is_rented/tenant_of/occupancy_ledger read battery,
    # restart-surviving gate probes, post-restart continuation on a
    # freed slot and a termination-freed storefront window, frozen
    # faces + dup/full gates, pure-read law, third instance
    # stability (AC-VNP1..VNP7 pre-registered in state/queue/
    # tech.md).
    ("ledger-venue-persist", os.path.join(
        "ledger", "test_venue_persist.py"), 7),
    ("ledger-collectibles",
     os.path.join("ledger", "test_collectibles.py"), 7),
    ("ledger-expedite",
     os.path.join("ledger", "test_expedite.py"), 7),
    # expedite persist window: cross-restart byte-identical
    # replay of the queue/credit read battery, restart-surviving
    # gate probes, post-restart continuation recompute, frozen
    # faces + idempotent replay, pure-read law, third instance
    # stability (AC-EPP1..EPP7 pre-registered in state/queue/
    # tech.md).
    ("ledger-expedite-persist", os.path.join(
        "ledger", "test_expedite_persist.py"), 7),
    ("ledger-ads",
     os.path.join("ledger", "test_ads.py"), 7),
    # ads persist window: cross-restart byte-identical replay of
    # the lineup/holder/board read battery, restart-surviving
    # gate probes, post-restart continuation on a freed carousel
    # window and a freed naming window, frozen faces + dup/full
    # gates, pure-read law, third instance stability (AC-ASP1..
    # ASP7 pre-registered in state/queue/tech.md).
    ("ledger-ads-persist", os.path.join(
        "ledger", "test_ads_persist.py"), 7),
    ("ledger-observation",
     os.path.join("ledger", "test_observation.py"), 7),
    # observation persist window: cross-restart byte-identical
    # replay of the read-face battery, restart-surviving gate
    # probes, post-restart continuation recompute, frozen faces
    # + window isolation, pure-read law, third instance stability
    # (AC-OBP1..OBP7 pre-registered in state/queue/tech.md).
    ("ledger-observation-persist", os.path.join(
        "ledger", "test_observation_persist.py"), 7),
    ("ledger-identity",
     os.path.join("ledger", "test_identity.py"), 7),
    ("ledger-studio",
     os.path.join("ledger", "test_studio.py"), 7),
    ("ledger-metered",
     os.path.join("ledger", "test_metered.py"), 7),
    # R1954 metered cross-restart persist window: two-piece close->
    # reopen battery, restart-surviving gates, continuation
    # recompute, frozen anchors, pure-read law, third instance
    # (AC-MTP1..MTP7 pre-registered in state/queue/tech.md).
    ("ledger-metered-persist",
     os.path.join("ledger", "test_metered_persist.py"), 7),
    ("ledger-reports",
     os.path.join("ledger", "test_reports.py"), 7),
    # R1955 reports cross-restart persist window: two-piece close->
    # reopen battery, restart-surviving gates, continuation
    # recompute, frozen anchors, pure-read law, third instance
    # (AC-RPP1..RPP7 pre-registered in state/queue/tech.md).
    ("ledger-reports-persist",
     os.path.join("ledger", "test_reports_persist.py"), 7),
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
    # companion persist window: cross-restart byte-identical replay
    # of the can_/transcript/memory/subs read battery, restart-
    # surviving gate probes (dup-pass/denied/content/gate-fault/
    # bad-month), post-restart continuation (missing month pass +
    # new dialogue rounds + memory appends), frozen faces +
    # dup/denied/content gates, pure-read law, third instance
    # stability (AC-CMP1..CMP7 pre-registered in state/queue/
    # tech.md).
    ("ledger-companion-persist",
     os.path.join("ledger", "test_companion_persist.py"), 7),
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
    # keys stay readable (AC-UW1..UW8 pre-registered in
    # state/queue/tech.md).
    ("ledger-apidev-usagewin",
     os.path.join("ledger", "test_apidev_usagewin.py"), 8),
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
    # (AC-UK1..UK7 pre-registered in state/queue/tech.md;
    # AC-UK8 month-rollover truth-preservation R1738).
    ("ledger-apidev-usagekind",
     os.path.join("ledger", "test_apidev_usagekind.py"), 8),
    # R1824 apidev lifecycle audit trace: the lifecycle store's
    # read-time audit face -- one key's own key_events timeline
    # (revoke/rotate_out/rotate_in with pair links) in
    # (event_utc, event_id) order, status and both pair links
    # derived from the same rows key_view reads (zero drift),
    # rotation chain walkable in both directions, dead keys
    # fully readable, embedded faces untouched (AC-RJW4 law)
    # (AC-TR1..TR7 R1824 + AC-TR8..TR14 R1875 explicit month-
    # window parameterization, pre-registered in tech.md).
    ("ledger-apidev-lifecycletrace",
     os.path.join("ledger", "test_apidev_lifecycle_trace.py"), 14),
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
    # degraded banner queue (own sqlite file, R1254 precedent);
    # R1850 banner_queue read-cap (AC-SB8..SB12) 7 -> 12;
    # R1855 banner_queue window filter (AC-SB13..SB17) 12 -> 17;
    # R1860 rows_by_status/queue_counts window filter
    # (AC-SB18..SB22 pre-registered in state/queue/tech.md) 17 -> 22
    ("ugc-sec-batch", os.path.join("ugc", "test_sec_batch.py"), 22),
    # R1859 sec_batch banner_queue monthly-roll preservation example
    # (AC-SBR1..AC-SBR7 pre-registered in state/queue/tech.md)
    ("ugc-sec-batch-roll", os.path.join("ugc", "test_sec_batch_roll.py"), 7),
    # R1901 sec_batch banner_queue cap-window read cross-restart
    # persistence example (AC-SB23..AC-SB29 pre-registered in
    # state/queue/tech.md)
    ("ugc-sec-batch-bannerpersist",
     os.path.join("ugc", "test_sec_batch_bannerpersist.py"), 7),
    # R1906 sec_batch rows_by_status/queue_counts windowed read
    # cross-restart persistence example (AC-SB30..AC-SB36
    # pre-registered in state/queue/tech.md)
    ("ugc-sec-batch-rowpersist",
     os.path.join("ugc", "test_sec_batch_rowpersist.py"), 7),
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
    # R1871 banner_queue read-cap (R1706 successor): limit tail param,
    # raw-list default byte-preserved, five-key capped envelope, rowid
    # tiebreak, E_PN_BAD_LIMIT fail-closed gate (AC-PN8..PN15
    # pre-registered in state/queue/tech.md).
    ("pay-notify-bannerlimit",
     os.path.join("pay", "test_pay_notify_bannerlimit.py"), 8),
    # R1878 banner_queue month-window filter (R1871 successor):
    # window=None tail param, record-time substr(1,7) row filter,
    # window-before-COUNT/LIMIT (windowed total), additive envelope
    # window echo key, E_PN_BAD_WINDOW fail-closed gate
    # (AC-PN16..PN22 pre-registered in state/queue/tech.md).
    ("pay-notify-bannerwin",
     os.path.join("pay", "test_pay_notify_bannerwin.py"), 7),
    # R1883 banner_queue monthly-roll fidelity example (R1878
    # successor): pre-roll snapshot -> post-roll explicit old-month
    # read byte-identity, rowid tail-window frozen across the roll,
    # default-face drift to the new month, windowed total semantics
    # across the roll (AC-PN23..PN29 pre-registered in tech.md).
    ("pay-notify-bannerroll",
     os.path.join("pay", "test_pay_notify_bannerroll.py"), 7),
    # R1884 banner_queue capped-window read cross-restart
    # persistence example (R1883 reseed): close -> new instance ->
    # same-db reopen reproduces all five derived read faces
    # byte-identically (zero in-memory drift), default faces drift
    # to post-restart data while explicit-window October reads stay
    # frozen, double-restart stability, pure-read law
    # (AC-PN30..PN36 pre-registered in tech.md).
    ("pay-notify-bannerpersist",
     os.path.join("pay", "test_pay_notify_bannerpersist.py"), 7),
    # R1885 authorize budget_face/authorization_state read
    # cross-restart persistence example (R1884 reseed): close ->
    # new instance -> same-db reopen reproduces the eight derived
    # read faces byte-identically (zero in-memory drift), the R1740
    # revocation cutoff keeps excluding pre-cutoff grants/sends
    # after the restart (nothing_to_revoke no-op, post-cutoff
    # re-arm, revoke_ts provenance), exhausted-once stays honestly
    # not-revoked, double-restart stability, pure-read law
    # (AC-PN37..PN43 pre-registered in state/queue/tech.md).
    ("pay-authorize-persist",
     os.path.join("pay", "test_authorize_persist.py"), 7),
    # R1886 authorize idempotency-cache restart semantics example
    # (R1885 reseed): the authorize.py header boundary note
    # ("restart survival is out of sandbox scope - a post-restart
    # replay re-grants one fresh once unit at most, longterm stays
    # gate-idempotent") pinned live: in-TTL replay absorption with
    # the original grant_id preserved, cache keyed on request_id
    # only, honest FIFO cap eviction, TTL-expired replay re-grants
    # one fresh unit (re-accept is legitimate W15 semantics),
    # cross-restart once replay grants exactly one unit,
    # cross-restart longterm replay stays gate-idempotent
    # (already_longterm, zero new rows), second-restart boundary
    # stability + per-avatar grant-row closure
    # (AC-PN44..PN50 pre-registered in state/queue/tech.md).
    ("pay-authorize-idem",
     os.path.join("pay", "test_authorize_idem.py"), 7),
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
    # R1740 W15 revocation face (R1719 successor): the user-side
    # settings unsubscribe is an append-only cutoff event - live-only
    # budget semantics (whole (avatar,template) subscription dies:
    # longterm + remaining once units), re-subscribe cycle re-arms via
    # post-cutoff grants, nothing_to_revoke honest zero-row no-op,
    # additive authorization_state read face, authorize.revoke report
    # face with approved-not-gated stop semantics
    # (AC-VR1..VR7 pre-registered in state/queue/tech.md).
    ("pay-notify-revoke", os.path.join("pay", "test_notify_revoke.py"), 7),
    # R1746 pay reconcile control-plane revokes coverage (R1740
    # successor): revoke_ref dangling-reference check + revoke_dead
    # dead-account discipline in the pay reconcile, notify-db
    # three-state resolution (explicit > sibling auto > six-check
    # mode), fail-closed on an explicitly named missing db
    # (AC-RVC1..RVC7 pre-registered in state/queue/tech.md).
    ("pay-revoke-reconcile", os.path.join("pay", "test_pay_revoke_recon.py"), 7),
    # R1776 pay channel-status coverage matrix (read-face family; the
    # reconcile control plane stays the independent enforcement face):
    # dense per-channel x per-status cell counts, zero cells explicit,
    # deterministic order, out-of-domain observed pairs appended not
    # hidden (AC-CHM1..CHM7 pre-registered in state/queue/tech.md).
    ("pay-channel-matrix", os.path.join("pay", "test_channel_matrix.py"), 7),
    # R1784 pay channel-status matrix monthly window (R1776 successor;
    # window-parameterized read-face family, R1730/R1732 same law):
    # default None keeps the full-window dense matrix with zero drift,
    # an explicit strict-anchor 'YYYY-MM' restricts counts to the
    # creation month (ts_utc record-time stamp), out-of-domain pairs
    # stay appended-and-counted inside the window, zero caching
    # (AC-CW1..CW7 pre-registered in state/queue/tech.md).
    ("pay-channel-window", os.path.join("pay", "test_channel_window.py"), 7),
    # R1904 pay channel-status matrix cross-restart persistence example
    # window (R1889..R1903 persist family, same law): face close -> new
    # instance same db same config -> window/default reads byte-identical
    # to pre-close snapshots, new November orders re-derive the default
    # read (zero caching) while the old window stays frozen, third
    # instance reads pairwise identical; suite-only round, zero product
    # changes (AC-CW8..CW14 pre-registered in state/queue/tech.md).
    ("pay-channel-persist", os.path.join("pay", "test_channel_persist.py"), 7),
    # R1921 pay channel_status_matrix windowed-read cross-restart DELTA
    # faces (dedup ruling in state/queue/tech.md, claim line R1921):
    # post-restart refund migration per-cell follow (granted->closed),
    # out-of-domain observation row x window x dense orthogonality
    # across restart, historical-month fixture window across restart;
    # the R1904 carrier faces (pre-close==reopen identity, new-order
    # recompute, two-instance sequential reads) ride as control
    # anchors. Suite-only round, zero product changes
    # (AC-CHM8..CHM12 pre-registered in state/queue/tech.md).
    ("pay-channel-migrate-persist", os.path.join(
        "pay", "test_channel_migrate_persist.py"), 5),
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
    # R1957 clawback wiring read-face family cross-restart persistence
    # (R1952 reseed FIFO head): close->same-db reopen keeps every
    # read face byte-identical (balances, claw envelopes, replays,
    # gate codes, wired close_refund), append-only frozen anchors,
    # pure-read battery, third instance stable (AC-CKP1..CKP7
    # pre-registered in state/queue/tech.md).
    ("ledger-clawback-persist", os.path.join("pay", "test_clawback_persist.py"), 7),
    ("member", os.path.join("member", "test_member.py"), 16),
    ("member-entry", os.path.join("member", "test_entry_tier.py"), 7),
    # R1932 member entry-tier activation-receipt read-face family
    # cross-restart persistence (patron C-20260927-01 true path via a
    # suite-owned dock row, idempotent replay byte law with the honest
    # vouchers_opened absence, refund dead-source gate across
    # instances, double-restart identity; AC-ETP1..ETP7 pre-registered
    # in state/queue/tech.md).
    ("member-entrytier-persist",
     os.path.join("member", "test_entry_tier_persist.py"), 7),
    # R1721 close_refund entitlement-recovery linkage (R1718 successor):
    # pay read-face refunded annotation (status-derived, zero schema
    # touch), member activation gate, revoke_refunded face (existing
    # active->expired legal edge + refund-recovery audit provenance),
    # birth-cert re-judge on non-refunded grants, caller-built recovery
    # wiring with never-break degradation + crash-window heal
    # (AC-RR1..RR7 pre-registered in state/queue/tech.md).
    ("member-refund-recovery",
     os.path.join("member", "test_refund_recovery.py"), 7),
    # R1774 member expiring-soon board: pre-expiry prediction pure-read
    # derived face (window-parameterized inclusive both edges, days_left
    # floor, reminder due-window alignment = honest superset; reminder
    # scan consumption candidate; AC-ES1..ES7 pre-registered in
    # state/queue/tech.md).
    ("member-expiring",
     os.path.join("member", "test_expiring_soon.py"), 7),
    # R1779 reminder due-scan read-face wiring (R1774 successor): the
    # renewal-due scan consumes the member pre-expiry board through
    # an injected callable (single window-derivation source; due =
    # the board's still-running subset, boundary row honest-superset)
    # - the reminder module's own SQL + window arithmetic (second
    # derivation) is cleared and its direct member read dock is
    # gone (AC-RW1..RW7 pre-registered in state/queue/tech.md).
    ("member-reminder-scanwire",
     os.path.join("member", "test_reminder_scan_wire.py"), 7),
    # R1782 reminder banner board (R1779 successor): pure-read derived
    # aggregation over the persistent degraded in-app fallback queue -
    # one board row per avatar holding skipped_* rows, dense status/
    # reason zero grids, deterministic census-key ascending order,
    # member-family compliance envelope, live derivation
    # (AC-BQ1..BQ17 pre-registered in state/queue/tech.md; the R1851
    # read-cap extension adds AC-BQ8..BQ12 - limit tail param with the
    # four-key additive overflow block; the R1856 month-window filter
    # adds AC-BQ13..BQ17 - window tail param, full-scope month cut,
    # E_REM_BAD_WINDOW fail-closed gate, window-x-cap orthogonality).
    ("member-banner-board",
     os.path.join("member", "test_banner_board.py"), 17),
    # R1861 member banner_board month-roll fidelity example: frozen
    # explicit-ts true product path across the Oct->Nov boundary -
    # new-month landing, old-month byte preservation, immutable-row
    # no-loss + telescoping totals, window-x-cap-x-roll orthogonality
    # (AC-MB1..MB7 pre-registered in state/queue/tech.md).
    ("member-banner-roll",
     os.path.join("member", "test_banner_board_roll.py"), 7),
    # R1866 member banner_queue window param (AC-MB8..MB14
    # pre-registered in state/queue/tech.md): raw row face month
    # filter - default byte-preservation + mirror-SQL equality,
    # 14 bad-window fail-closed, honest empty window, cross-month
    # byte preservation + zero mutual leakage, telescoping partition
    # + board-total interlock, pure-read + hygiene.
    ("member-banner-queue-window",
     os.path.join("member", "test_banner_queue_window.py"), 7),
    # R1872 member banner_queue read-cap (AC-MB15..MB22
    # pre-registered before code; tail limit param, additive
    # five-key envelope + window echo key, E_REM_BAD_LIMIT reused).
    ("member-banner-queue-limit",
     os.path.join("member", "test_banner_queue_limit.py"), 8),
    # R1879 member banner_queue capped+windowed monthly-roll
    # fidelity example (AC-MB23..MB29 pre-registered before code;
    # pre-roll snapshot -> post-roll explicit old-month cap-window
    # read byte-identity, default-cap drift to the new window,
    # window-total immutability across the roll).
    ("member-banner-queue-caproll",
     os.path.join("member", "test_banner_queue_caproll.py"), 7),
    # R1889 member banner_queue cap-window read cross-restart
    # persistence example (AC-MB30..MB36 pre-registered before
    # code; close -> same cfg same db reopen: October cap-window
    # envelope byte-identity, default-cap restoration, one new
    # November row = window-isolation across restart, dual live
    # instances sequential read identity, pure-read law across
    # the restart boundary).
    ("member-banner-queue-persist",
     os.path.join("member", "test_banner_queue_persist.py"), 7),
    # R1894 member banner_board capped+windowed read cross-restart
    # persistence example (R1889 reseed): face close -> same cfg
    # same db reopen; oct capped-window envelope (window echo +
    # cap block) == pre-close snapshot byte-identical; default
    # capped/bare reads recover; one new november row recomputes
    # the default face while the old window stays frozen (window
    # aggregates follow the window); dual live instances read
    # identical. (AC-BQ18..AC-BQ24 pre-registered in the R1894
    # tech.md claim row; suite-only round, product untouched.)
    ("member-banner-board-persist",
     os.path.join("member", "test_banner_board_persist.py"), 7),
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
    # R1747 search-refinement experiment on the R1725 IMPROVED 0.7x
    # case: search_num expansion {500,1000} + two-round window
    # narrowing; negative verdict (refinement cannot reach the 0.10
    # band; residual = interpolation information loss) lawful per
    # pre-registration (AC-UKR1..UKR6 in state/queue/tech.md).
    ("watermark-scale-refine",
     os.path.join("watermark", "test_scale_refine.py"), 6),
    ("dual-track", os.path.join("watermark", "test_dual_track.py"), 7),
    # R1778 binding-bit independence probe: 1-bit preimage perturbations
    # avalanche the SHA-256-bound payload (registered band [0.35, 0.65])
    # with pairwise independence across the bit-position sweep, and the
    # R593 forgery floor (0.40) holds at single-bit granularity while
    # perturbed seals still roundtrip exactly (AC-BI1..BI7
    # pre-registered in state/queue/tech.md).
    ("watermark-bindbit",
     os.path.join("watermark", "test_bind_bit.py"), 7),
    # R1783 two-bit crosstalk probe (successor of the R1778 single-bit
    # basis): C(8,2) simultaneous two-bit preimage flips stay inside the
    # avalanche band and within crosstalk slack of their component
    # single-bit readings (AC-BD1..BD7 pre-registered in
    # state/queue/tech.md).
    ("watermark-dualbit",
     os.path.join("watermark", "test_dual_bit.py"), 7),
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
    # minors persist window: cross-restart byte-identical replay of
    # the day_readout/residents_readout battery, restart-surviving
    # gate probes, post-restart continuation recompute + new-minor
    # registration on the reopened instance, frozen history face +
    # cross-restart idempotent replay + per-(resident,date) ref
    # domain law, pure-read law, third instance stability
    # (AC-MGP1..MGP7 pre-registered in state/queue/tech.md).
    ("minors-persist", os.path.join(
        "minors", "test_minors_persist.py"), 7),
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
    # R1749 AC-EF1..EF6: stale --check evidence-face comparison +
    # face-mismatch hint (+1 case; seed = R1739 same-run stale x2).
    ("suite-matrix-discovery", "test_suite_matrix.py", 16),
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
    # R1848 reconcile-daily census step: qa_writer_census --check
    # appended to the dated evidence log after the profile step;
    # baseline-present drift FLAG gates the day (exit 2/3 FAIL),
    # missing baseline is an honest INFO face (recorded, never
    # gating); daily exit aggregates runner -> sentinel -> census
    # (AC-WCD1..WCD7 pre-registered in state/queue/tech.md).
    ("reconcile-daily-census", "test_reconcile_daily_census.py", 8),
    # R1750 collectibles public-showcase face: append-only place/retract
    # event ledger (zero UPDATE, derived display state, one item one
    # window), dock-verified ownership over the collectibles rows,
    # zero token movement, caption msgSecCheck pre-gate, permanent
    # chronicle + derived tour (AC-SH1..SH7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase",
     os.path.join("ledger", "test_showcase.py"), 7),
    # R1751 showcase curation theme face: multi-showcase grouping
    # register (append-only, immutable, position 1..N), themed tour
    # with global stop numbering across member showcases, showcase
    # facts read exclusively through the ShowcaseFace public API
    # (reference, not copy), member existence fail-closed, zero
    # token movement, zero UPDATE (AC-CU1..CU7 pre-registered in
    # state/queue/explore.md). R1753 adds the theme heat board
    # hot_board pure-read derived ranking (heat = member on-display
    # sums, deterministic (-displayed_total, curation_id) sort,
    # zero RNG, zero writes) - AC-HB1..HB5 same row, criteria
    # 7 -> 12. R1770 adds the board rank-change diff hot_board_delta
    # movement face over two caller-held snapshots (four states
    # rise/fall/entered/dropped, steady rows omitted, zero storage,
    # single hot_board() derivation source) - AC-HD1..HD7 same row,
    # criteria 12 -> 19. R1970 adds the zero-heat cold board
    # cold_board honest inverse filter of the heat board (single
    # live hot_board() derivation source, zero second aggregation
    # engine, curation_id ASC rank 1..N, honest empty board over
    # zero-curation and all-hot worlds) - AC-CB1..CB5 same row,
    # criteria 19 -> 24.
    ("ledger-curation",
     os.path.join("ledger", "test_curation.py"), 24),
    # R1923 curation hot_board cross-restart persistence example
    # window: the theme heat board is pure-derived over THREE
    # databases (curation registry + live showcase display state
    # + ledger ownership), so the suite pins derived purity across
    # full-stack instance restarts - pre-close envelope byte-
    # identical to the reopened read, zero-cache recompute with
    # rank flips and curation_id tie-break following after a
    # post-restart placement/retract, third-instance sequential
    # reads byte-identical, pure-read law across restarts,
    # manual-SQL second-derivation cross, product-file sha256
    # double-proof (suite-only round, zero product changes)
    # (AC-HBP1..HBP6 pre-registered in state/queue/tech.md).
    ("ledger-curation-hotpersist",
     os.path.join("ledger", "test_curation_hotpersist.py"), 6),
    # R1972 curation cold_board cross-restart persistence example
    # window (R1970-reseeded explore-queue row claimed by R1972):
    # the zero-heat cold shelf is the honest inverse filter of the
    # heat board, pure-derived over THREE databases (curation
    # registry + live showcase display state + ledger ownership),
    # so the suite pins derived purity across full-stack instance
    # restarts PLUS cold<->hot migration continuation - pre-close
    # envelope byte-identical to the reopened read, cold->hot
    # (placement into a cold theme's member showcase) and
    # hot->cold (retracting a hot theme to zero) both recomputed
    # zero-cache with the cold/hot complementarity law held after
    # every migration step, third-instance sequential reads
    # byte-identical, pure-read law across restarts, manual-SQL
    # second-derivation cross, product-file sha256 double-proof
    # (suite-only round, zero product changes)
    # (AC-CZP1..CZP6 pre-registered in state/queue/explore.md).
    ("ledger-curation-coldpersist",
     os.path.join("ledger", "test_curation_coldpersist.py"), 6),
    # R1974 curation combined hot+cold dual board read face
    # (R1972-reseeded explore-queue row claimed by R1974): one
    # envelope presenting the heat board and the cold shelf side
    # by side - the hot/cold complementary law made visible in a
    # single read. Single derivation source = ONE live
    # hot_board() call (reference face, not a copy): hot zone =
    # heat>0 rows re-ranked 1..M with the parent
    # (-displayed_total, curation_id) order preserved by the
    # filter, cold zone = zero-heat rows re-ranked 1..K in
    # curation_id ASC (the cold_board law); zones disjoint by
    # construction, union == full snapshot row set (M+K==N),
    # envelope keys/totals/disclaimer contract, zero-curation
    # honest empty double board, all-hot and zero-heat boundary
    # worlds, double-read byte identity, curation+showcase
    # face close -> reopen over same dbs with the derived read
    # byte-identical to the pre-close snapshot, ledger_tx and
    # registry row-count invariance across every read, combined
    # face source pure ASCII + zero UPDATE + zero network
    # imports
    # (AC-CJ1..CJ7 pre-registered in state/queue/explore.md).
    ("ledger-curation-combined",
     os.path.join("ledger", "test_curation_combined.py"), 7),
    # R1975 curation combined hot+cold dual board cross-restart
    # persistence example window (R1974-reseeded explore-queue
    # row claimed by R1975): the joint read is pure-derived over
    # THREE databases (curation registry + live showcase display
    # state + ledger ownership) from ONE live hot_board() call,
    # so the suite pins the joint-read derived purity across
    # full-stack instance restarts PLUS cold<->hot migration
    # continuation on both zones at once - pre-close envelope
    # byte-identical to the reopened read (single derivation
    # source, zero in-memory drift), cold->hot (placement into a
    # cold theme's member showcase) and hot->cold (retracting a
    # hot theme to zero) both recomputed zero-cache with the
    # disjoint-union partition law and the live-hot_board
    # single-source cross held after every migration step,
    # third-instance sequential reads byte-identical, pure-read
    # law across restarts, manual-SQL second-derivation cross,
    # product-file sha256 double-proof (suite-only round, zero
    # product changes)
    # (AC-CDP1..CDP6 pre-registered in state/queue/explore.md).
    ("ledger-curation-combinedpersist",
     os.path.join("ledger", "test_curation_combinedpersist.py"), 6),
    # R1976 curation combined hot+cold dual board boundary-world
    # cross-restart persistence example window (R1975-reseeded
    # explore-queue row claimed by R1976): the persist-family
    # laws pinned across the THREE boundary worlds of the joint
    # read (AC-CJ4 boundary confluence) - zero-curation world
    # (honest empty both zones), all-hot world (cold zone empty)
    # and zero-hot world (hot zone empty). Each boundary world
    # is closed full-stack and reopened on the same three db
    # paths with the joint read byte-identical to the pre-close
    # snapshot (single derivation source, zero in-memory drift);
    # the world-to-world transitions (all-hot -> zero-hot by
    # retraction, zero-hot -> mixed by re-placement) recompute
    # zero-cache ON the reopened instances with the
    # disjoint-union partition law and the live hot_board
    # single-source cross held after every step; a fifth-instance
    # sequential read pair is byte-identical (re-read purity);
    # pure-read law across every read batch; product-file
    # sha256 double-proof (suite-only round, zero product
    # changes)
    # (AC-CBW1..CBW6 pre-registered in state/queue/explore.md).
    ("ledger-curation-combinedboundary",
     os.path.join("ledger", "test_curation_combinedboundary.py"), 6),
    # R1926 curation registry / tour read-face family
    # cross-restart persistence example window (R1923-reseeded
    # tech-queue row claimed by R1926): active_curations
    # registry board + curation_view facts/members read +
    # curation_tour global stop-numbered tour - CurationFace
    # close -> new instance over the SAME ShowcaseFace and the
    # same curation db: pre-close three-form snapshots ==
    # reopened reads byte-identical, zero-cache recompute after
    # a post-restart placement and a post-restart new
    # registration, third-instance sequential reads
    # byte-identical, pure-read law, manual-SQL cross,
    # product-file sha256 double-proof (suite-only round)
    # (AC-CRP1..CRP7 pre-registered in state/queue/tech.md).
    ("ledger-curation-regpersist",
     os.path.join("ledger", "test_curation_regpersist.py"), 7),
    # R1752 citizen civic-behavior points face: earned-only points
    # inside the counts-vs-tokens isolation law (constructor takes
    # NO ledger reference - token domain structurally out of reach),
    # idempotent earn rows with per-day anti-farming cap, fail-closed
    # redemption (derived balance gate, cosmetic one-grant-per-account),
    # own civic_grants table on the props-domain adjacency verdict
    # (props grant path is token-spend-bound, never copied), zero
    # UPDATE, zero back-flow/transfer verbs (AC-CV1..CV7
    # pre-registered in state/queue/explore.md). R1754 honor roll
    # extension: annual honor_board(year) pure-read derivation with
    # deterministic (-points, account_id) ordering, cross-year
    # isolation and the platform-side honor-certificate linkage
    # candidate judgment (AC-HN1..HN6 pre-registered in the R1754
    # explore-queue row), plus the 1224 competition-rank
    # presentation face with the row-count-based grant-slice
    # judgment (AC-HR1..HR7 pre-registered in the R1769 row).
    ("ledger-civicpoints",
     os.path.join("ledger", "test_civicpoints.py"), 20),
    # R1755 annual civic honor certificate grant face: pure
    # orchestration over two public faces (civic honor_board read +
    # collectibles issue_certificate/collection) - zero own storage,
    # zero SQL in the module, top-N slice derived from the board's
    # deterministic order, one-per-account-per-year idempotency
    # internalized by the collectibles duplicate law (E_CL_DUP
    # converges to an already-skip), permanent certificates that
    # survive board moves, platform-side posture with zero resident
    # text, zero token movement (AC-HC1..HC7 pre-registered in the
    # R1755 explore-queue row).
    ("ledger-honorcert",
     os.path.join("ledger", "test_honorcert.py"), 7),
    # R1979 honor yearbook certified-only roster read face:
    # single-source derivation from the honor_certs read face
    # (zero own board walks, zero own collection reads), keeps
    # certified members in board order with the certificate
    # provenance echo (item_id) and live board rank; board-scoped
    # honest derivation limit (off-board certificate holders
    # stay outside the view, the certificate itself is permanent
    # in the collectibles domain); zero-certified year returns an
    # honest empty roster; pure read (zero writes, zero storage,
    # zero token movement, zero RNG) (AC-HY1..HY7 pre-registered
    # in the R1979 explore-queue claim row).
    ("ledger-honorcert-yearbook",
     os.path.join("ledger", "test_honorcert_yearbook.py"), 7),
    # R1927 civic honor-board cross-restart persistence example
    # window (R1926-reseeded tech-queue row; the R1925 law): the
    # honor_board / honor_board_competition read faces derive
    # purely from the append-only civic_earns rows, so a face
    # close -> new instance over the same civic.db must reproduce
    # the six pre-close forms byte-identically (2025 dense + comp
    # with a 1224 tie, 2026 dense + comp, empty-year honest []),
    # recompute zero-cache after post-restart earns (order flip +
    # same-account cross-year coexistence with the old-year board
    # frozen), and hold through a second restart third instance;
    # pure-read law + manual-SQL cross + civicpoints.py sha256
    # double-proof (AC-CVP1..CVP7 pre-registered in the R1927
    # tech.md claim row; suite-only round, zero product changes).
    ("ledger-civicpersist",
     os.path.join("ledger", "test_civic_persist.py"), 7),
    # R1759 developer revenue-share gradient face: settlement chain
    # composed onto the IncentiveFace proper (band walk / collar /
    # budget pro-rata / window idempotence - structure reuse, zero
    # reimplementation) with the developer-ecosystem layers on top:
    # registry gate through the DevKeyFace.dev_board public read
    # face, usage-attribution intake from quota_used, devshare-
    # prefix window namespace (cross-face idempotence through the
    # shared incentive_windows table), read-only dock history face
    # (AC-DS1..DS7 pre-registered in state/queue/explore.md).
    ("ledger-devshare",
     os.path.join("ledger", "test_devshare.py"), 7),
    # R1763 explore-queue row: developer API marketplace face -
    # listing idempotence + registry gate (DevKeyFace.dev_board
    # public read face, before the content gate so off-register
    # publishers burn zero msgSecCheck calls), purchase with the
    # integer split law (incentive per-entry one-share structure
    # reuse), purchaser-only rating; SecGate pre-gate on
    # title/description (AC-AM1..AM7 pre-registered in
    # state/queue/explore.md).
    ("ledger-apimarket",
     os.path.join("ledger", "test_apimarket.py"), 7),
    # R1764 explore-queue row: city public dataset subscription
    # face - window law (monthly YYYY-MM / quarterly YYYY-QN, \Z
    # hard anchor per the R1748 lesson) + one-spend-per-
    # (account,dataset,window) subscription idempotency (the
    # observation R623 monthly-window judgement reused) +
    # permission-gate delivery with re-download voucher rows and
    # structural de-identification (the reports R627 law: the
    # delivered bundle carries exactly the descriptor key set,
    # zero foreign SELECT); platform-side registration posture
    # (AC-DSB1..DSB7 pre-registered in state/queue/explore.md).
    ("ledger-datasub",
     os.path.join("ledger", "test_datasub.py"), 7),
    # R1766 resident proposal co-signature face: proposal registry
    # with msgSecCheck pre-gate on resident free text (injected
    # SecGate, reference not copy) + one-sign-per-resident window
    # gate (inclusive both edges, ads/venue convention, self-sign
    # and re-sign rejected before any row) + read-time derived
    # qualification with the threshold-crossing sign awarding the
    # proposer one memorial certificate through the collectibles
    # public API (E_CL_DUP internalized, platform pre-award does
    # not double-issue) - zero token movement by structure (no
    # ledger reference exists in the module at all)
    # (AC-PP1..PP7 pre-registered in state/queue/explore.md).
    ("ledger-proposal",
    os.path.join("ledger", "test_proposal.py"), 12),
    # R1956 proposal cross-restart persist window: two-piece close->
    # reopen battery (byte-identical views/board/two-table SQL),
    # restart-surviving gates same-code, continuation recompute
    # (crossing award post-restart, new registration, board rowid
    # append), frozen anchors + replay gate, pre-award idempotence
    # across restart, pure-read law, third instance
    # (AC-PLP1..PLP7 pre-registered in state/queue/tech.md).
    ("ledger-proposal-persist",
     os.path.join("ledger", "test_proposal_persist.py"), 7),
    # R1958 tech-queue FIFO head claim (R1953 reseed row): UGC
    # creator incentive gradient allocator - cross-restart
    # persistence of the settlement read family: anchor world
    # (budget-binding window with exact pro-rata integer landing,
    # collar-binding window), two-piece close -> reopen byte-
    # identical battery (window projection + balances + incentive
    # tx join; settled_utc frozen stamps compared in-run),
    # restart-surviving seven-gate reject batch (same codes same
    # order, all before any write), continuation recompute
    # (W3 rides alongside frozen windows, zero-cache), frozen
    # anchors + replay gates, pure-read law, third instance
    # (AC-ICP1..ICP7 pre-registered in state/queue/tech.md).
    ("ledger-incentive-persist",
     os.path.join("ledger", "test_incentive_persist.py"), 7),
    # R1767 explore-queue row: virtual event ticket face - the
    # liveroom paid-admission variant over the festival schedule-
    # window convention: session registry (UNIQUE key, declared
    # AIGC label), in-window ticket purchase with replay /
    # per-account-limit / capacity gates all before the one spend,
    # and the admission check-in gate (no ticket = no entry, the
    # liveroom unattended-admission law; check-in appends one row
    # per (session, account) and moves zero tokens)
    # (AC-ET1..ET7 pre-registered in state/queue/explore.md).
    ("ledger-eventtickets",
     os.path.join("ledger", "test_eventtickets.py"), 14),
    # R1826 audit-board month-window parameterization: the
    # event_audit_board read gains the R1730/R1793 window family
    # law - default None keeps the full-window envelope
    # byte-identical; an explicit YYYY-MM window filters
    # sold/revenue by purchased_utc and admitted by checked_utc
    # (record-time provenance stamps); no_show in a windowed
    # read is the end-of-window snapshot (structurally
    # non-negative under the per-pair purchase-precedes-check-in
    # flow law; the in-window net flow is never surfaced under
    # the registered field name); admission_rate stays the
    # window-filtered ratio under the zero-sold guard; malformed
    # windows fail closed E_ET_BAD_ARGS before any read
    # (AC-EAW1..EAW7 pre-registered in state/queue/tech.md).
    ("ledger-eventtickets-boardwin",
     os.path.join("ledger", "test_eventtickets_boardwin.py"), 7),
    # R1840 event-ticket audit-board read-cap parameterization:
    # default limit=0 keeps the full board byte-identical; a
    # positive limit keeps the last N sessions in session_key
    # ascending order (the tail window = the mirror clause
    # DESC LIMIT reversed back), window filtering runs before
    # the cap (orthogonal), the overflow block reports the
    # in-window full count under "total" (four keys
    # {limit,total,returned,truncated}, the R1729 usage_log
    # same-type shape - the default envelope carries no total
    # key); a malformed limit fails closed E_ET_BAD_LIMIT
    # before the window gate (the double-bad gate-order law)
    # (AC-ETL1..ETL7 pre-registered in state/queue/tech.md).
    ("ledger-eventtickets-boardlimit",
     os.path.join("ledger", "test_eventtickets_boardlimit.py"), 7),
    # R1862 event-ticket audit-board cross-month month-roll
    # fidelity example: frozen explicit-stamp true product path
    # across the Oct->Nov boundary - new-month record-time
    # landing (each row family on its own provenance stamp),
    # old-month byte preservation, immutable-row no-loss with
    # ID-set superset, default all-window read including the
    # cross-month rows (the all-window default - honest note:
    # unlike the current-month-default family), windowed
    # no_show end-of-window snapshot vs the non-surfaced
    # in-window net flow, window-x-cap-x-roll orthogonality
    # (AC-ETR1..ETR7 pre-registered in state/queue/tech.md).
    ("ledger-eventtickets-roll",
     os.path.join("ledger", "test_eventtickets_roll.py"), 7),
    # R1867 month-axis telescoping example: sold/admitted/
    # revenue are additive flow faces (october + november ==
    # full-window, the row-set partition law via the SQL
    # mirror); no_show is the end-of-window snapshot and never
    # telescopes (the R1862 world anchor - cross-month pairing);
    # admission_rate is a window-local ratio (0.5 + 1.0 !=
    # 0.75); zero-activity month windows keep the registry-
    # driven dense rows with honest zeros
    # (AC-ETT1..ETT6 pre-registered in state/queue/tech.md).
    ("ledger-eventtickets-telescope",
     os.path.join("ledger", "test_eventtickets_telescope.py"), 6),
    # R1768 developer free-trial tier face: the zero-fee trial
    # window (lifetime cap, the apidev quota-ring variant -
    # immutable call rows, COUNT face, zero mutation) + the
    # upgrade-conversion gate (cap exhaustion refuses with the
    # upgrade hint; a converted developer loses the free tier
    # fail-closed; one terminal conversion row per (dev, plan),
    # the member tier-grant structure reference) over the
    # DevKeyFace registry gate (referenced, never copied); the
    # face holds no ledger reference at all - the free tier is
    # structurally free
    # (AC-FT1..FT7 pre-registered in state/queue/explore.md).
    ("ledger-freetrial",
     os.path.join("ledger", "test_freetrial.py"), 7),
    # R1788 free-trial conversion-funnel board: plan-level
    # grant/conversion counts + derived active-trials and
    # conversion-rate, pure read-time aggregation over
    # immutable rows (zero cached counters; the conversion gate
    # is itself a conversion-row count)
    # (AC-CF1..CF7 pre-registered in state/queue/explore.md)
    ("ledger-freetrial-funnel",
     os.path.join("ledger", "test_freetrial_funnel.py"), 7),
    # R1793 free-trial funnel window parameterization: default
    # None full-window zero drift + explicit YYYY-MM month
    # window filtering granted by granted_utc and converted by
    # converted_utc (record-time columns); windowed
    # active_trials = end-of-window snapshot (grants month<=W
    # minus conversions month<=W, structurally non-negative);
    # malformed windows fail closed E_FT_BAD_ARGS
    # (AC-CFW1..CFW7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-funnelwin",
     os.path.join("ledger", "test_freetrial_funnelwin.py"), 7),
    # R1828 free-trial calls-by-month pure read face: global
    # month-profile aggregation over immutable trial_calls rows
    # (record-time single column), window=None full-window
    # default; explicit YYYY-MM keeps that month's cell only;
    # malformed windows fail closed E_FT_BAD_ARGS
    # (AC-CBM1..CBM7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-callmonth",
     os.path.join("ledger", "test_freetrial_callmonth.py"), 7),
    # R1829 free-trial calls-by-kind pure read face: global
    # kind-profile aggregation over immutable trial_calls rows
    # (free TEXT domain, no CHECK constraint); window=None
    # full-window default; explicit YYYY-MM filters rows by
    # record-time stamp first, then aggregates kinds over the
    # surviving rows; malformed windows fail closed
    # E_FT_BAD_ARGS; observed kinds outside the registered
    # tally domain surface and count toward total (the face
    # never hides data)
    # (AC-CBK1..CBK8 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-callkind",
     os.path.join("ledger", "test_freetrial_callkind.py"), 8),
    # R1830 free-trial calls-by-plan pure read face: global
    # plan-profile aggregation over immutable trial_calls rows
    # (structured INTEGER domain, no CHECK, no FK); window=None
    # full-window default; explicit YYYY-MM filters rows by
    # record-time stamp first, then aggregates plans over the
    # surviving rows; malformed windows fail closed
    # E_FT_BAD_ARGS; orphan plan_id rows (no trial_plans row,
    # only direct injection can produce one) surface and
    # count toward total (the face never hides data)
    # (AC-CBP1..CBP8 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-callplan",
     os.path.join("ledger", "test_freetrial_callplan.py"), 8),
    # R1831 free-trial calls-by-engine pure read face: global
    # engine-profile aggregation over immutable trial_calls rows
    # (engine_ref free TEXT domain, the engine attribution
    # stamp; a live call always carries a non-empty stamp);
    # window=None full-window default; explicit YYYY-MM filters
    # rows by record-time stamp first, then aggregates engine
    # stamps over the surviving rows; malformed windows fail
    # closed E_FT_BAD_ARGS; out-of-domain stamps (only direct
    # injection can produce one) surface and count toward
    # total (the face never hides data)
    # (AC-CBE1..CBE8 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-callengine",
     os.path.join("ledger", "test_freetrial_callengine.py"), 8),
    # R1837 free-trial calls-by-account pure read face: global
    # developer-account profile aggregation over immutable
    # trial_calls rows (dev_account observed TEXT domain, the
    # developer account stamp; the live call gate always
    # stamps an in-register usr:-shaped account - grant first,
    # then call); window=None full-window default; explicit
    # YYYY-MM filters rows by record-time stamp first, then
    # aggregates accounts over the surviving rows; malformed
    # windows fail closed E_FT_BAD_ARGS; out-of-domain account
    # stamps (history fixture accounts or non-usr:-shaped
    # stamps, only direct injection can produce them) surface
    # and count toward total (the face never hides data)
    # (AC-CBA1..CBA8 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-callaccount",
     os.path.join("ledger", "test_freetrial_callaccount.py"), 8),
    # R1842 per-grant cap-distance profile board: pure-read
    # grant x plan-cap x call-count three-face derivation over
    # trial_grants/trial_plans/trial_calls (window filters the
    # grant row set only; counts stay lifetime - the
    # count-domain-not-sliced verdict)
    ("ledger-freetrial-capusage",
     os.path.join("ledger", "test_freetrial_capusage.py"), 8),
    # R1849 cap_usage_board read cap: limit=0 sole sentinel keeps
    # the full board; positive int caps to the (dev,plan) ascending
    # tail window; overflow block reuses total as the full
    # grant-row-set count and adds {limit, returned, truncated};
    # malformed limit fails closed E_FT_BAD_LIMIT before the
    # window gate; window filter runs before the cap
    # (AC-CUL1..CUL7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-caplimit",
     os.path.join("ledger", "test_freetrial_caplimit.py"), 7),
    # R1854 cap_usage_board month-roll fidelity example: frozen
    # clock +23d across the month boundary - new-month grants
    # land in the new window, the old-month windowed read keeps
    # its original row set (two windows never leak), the
    # surviving grant keeps LIFETIME calls_used/remaining
    # (count domain never sliced), the read cap rides along
    # (window x cap orthogonal, total = the windowed grant
    # count); zero product bytes - pin-only suite
    # (AC-CRU1..CRU7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-caproll",
     os.path.join("ledger", "test_freetrial_caproll.py"), 7),
    # R1858 free-trial calls_by_* five-profile month-roll
    # fidelity pin: frozen-clock isolated world, every window
    # slices CALL rows by their own record-time stamp (never
    # by grant birth month), old-month window reads preserved
    # byte-identical across the roll, calls_by_month month
    # axis telescopes (sum of observed month-window totals ==
    # all-window total); zero product bytes - pin-only suite
    # (AC-CFR1..CFR7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-callroll",
     os.path.join("ledger", "test_freetrial_callroll.py"), 7),
    # R1874 free-trial conversion_funnel_board month-roll
    # fidelity pin: frozen-clock isolated world, the cross-
    # month conversion (grant 2026-10 + conversion 2026-11)
    # reads two states in two windows (end-of-window snapshot
    # walks with the window), old-month window reads preserved
    # byte-identical across the roll, windowed rate keeps the
    # zero-grant guard; zero product bytes - pin-only suite
    # (AC-CVR1..CVR7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-funnelroll",
     os.path.join("ledger", "test_freetrial_funnelroll.py"), 7),
    # R1880 free-trial conversion_funnel_board read cap: limit=0
    # sole default sentinel keeps the full behavior byte-identical,
    # positive int caps to the tail window (mirror SQL plan_key
    # DESC LIMIT N reversed), overflow block adds exactly four keys
    # {limit, total, returned, truncated} with total = the registry
    # row count (dense axis, window-independent), malformed limit
    # fails closed E_FT_BAD_LIMIT before the window gate
    # (AC-CVR8..CVR14 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-funnelcap",
     os.path.join("ledger", "test_freetrial_funnelcap.py"), 7),
    # R1890 free-trial conversion_funnel_board capped-window
    # read cross-restart persistence: the full four-piece
    # dependency stack (Ledger -> MeteredFace -> DevKeyFace ->
    # FreeTrialFace) closes and reopens on the same db, capped
    # windowed/default reads return byte-identical to the
    # pre-close snapshots (zero in-memory drift), new November
    # rows recompute the default capped read (zero cache)
    # while the old-month windowed capped read stays
    # byte-identical (window isolation across restart and
    # across new data), second reopen reads sequentially
    # identical; zero product bytes - pin-only suite
    # (AC-CVR15..CVR21 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-funnelpersist",
     os.path.join("ledger", "test_freetrial_funnelpersist.py"), 7),
    # R1895 freetrial cap_usage_board capped-window read
    # cross-restart persistence: four-piece stack close/reopen,
    # windowed capped reads byte-identical to pre-close
    # snapshots, November grant recomputes the default capped
    # read (zero cache) while the October windowed capped read
    # stays byte-identical, second reopen reads sequentially
    # identical; zero product bytes - pin-only suite
    # (AC-CRU8..CRU15 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-cappersist",
     os.path.join("ledger", "test_freetrial_cappersist.py"), 8),
    # R1914 freetrial five count faces (calls_by_month/by_kind/
    # by_plan/by_engine/by_account) windowed-read cross-restart
    # persistence: four-piece stack close/reopen, windowed reads
    # byte-identical to pre-close snapshots, November calls on
    # the reopened face recompute defaults while October windows
    # freeze, third instance reads sequentially identical;
    # zero product bytes - pin-only suite
    # (AC-CFP1..CFP7 pre-registered in state/queue/tech.md)
    ("ledger-freetrial-fivepersist",
     os.path.join("ledger", "test_freetrial_fivepersist.py"), 7),
    # R1777 UGC noise/review pool water-level read face: pure-read
    # derivation over payload noise flags + review-desk verdicts
    # (zero stored counters, live per call; store envelope carries
    # the standing non-advisory disclaimer)
    # (AC-NP1..NP7 pre-registered in state/queue/tech.md)
    ("ugc-pool-water", os.path.join("ugc", "test_pool_water.py"), 7),
    # R1785 UGC pool water two-snapshot delta probe: caller-held
    # snapshot vs single live levels call (change-only cells,
    # prev-only keys show as negatives)
    # (AC-DW1..DW7 pre-registered in state/queue/tech.md)
    ("ugc-pool-delta", os.path.join("ugc", "test_pool_delta.py"), 7),
    # R1794 UGC ingest window water-delta wiring: dual live snapshots
    # around ingest_lobby + last_water_delta read face
    # (AC-IW1..IW6 pre-registered in state/queue/tech.md)
    ("ugc-ingest-waterwire", os.path.join("ugc", "test_ingest_waterwire.py"), 6),
    # R1796 UGC submit_batch batch water-delta wiring: dual live
    # snapshots around the batch window + single-slot co-residency
    # with the ingest window (last completed window wins)
    # (AC-BW1..BW6 pre-registered in state/queue/tech.md)
    ("ugc-batch-water", os.path.join("ugc", "test_batch_waterwire.py"), 6),
    # R1797 UGC drain_recover recovery water-delta wiring: dual live
    # snapshots around the recovery window; three-window co-residency
    # (ingest R1794 + batch R1796 + recovery R1797), last completed
    # window wins, an empty recovery window included
    # (AC-DR1..DR6 pre-registered in state/queue/tech.md)
    ("ugc-drain-water", os.path.join("ugc", "test_drain_waterwire.py"), 6),
    # R1798 UGC submit single-text water-delta wiring: dual live
    # snapshots around the submit window; four-window co-residency
    # (ingest R1794 + batch R1796 + recovery R1797 + submit R1798),
    # last completed window wins, refused paths keep the slot
    # (AC-SU1..SU7 pre-registered in state/queue/tech.md)
    ("ugc-submit-water", os.path.join("ugc", "test_submit_waterwire.py"), 7),
    # R1799 UGC review_verdict verdict water-delta wiring: dual live
    # snapshots around the verdict window; five-window co-residency
    # (ingest R1794 + batch R1796 + recovery R1797 + submit R1798 +
    # verdict R1799), last completed window wins; the risky verdict
    # records its trace before the raise, so it completes the window
    # (pre-mutation refusals keep the slot)
    # (AC-VW1..VW7 pre-registered in state/queue/tech.md)
    ("ugc-verdict-water", os.path.join("ugc", "test_verdict_waterwire.py"), 7),
    # R1800 UGC completed-window water journal: append-only observability
    # ledger next to ugc.db (one row per completed window: kind + delta
    # envelope + ts; single writer, zero ugc.db schema touch) with the
    # journal_board pure read face - window history persists across
    # restarts where the single _last_water slot cannot
    # (AC-WJ1..WJ7 pre-registered in state/queue/tech.md)
    ("ugc-water-journal", os.path.join("ugc", "test_water_journal.py"), 7),
    # R1801 water journal kind_tally: dense per-kind completed-window
    # count aggregation (window=None full-history default; explicit
    # YYYY-MM filters on the record-time ts_utc month; R1748 \Z-anchored
    # family law, 14 bad shapes fail closed; out-of-domain observed
    # kinds stay visible - the face never hides data)
    # (AC-KT1..KT7 pre-registered in state/queue/tech.md)
    ("ugc-water-kindtally", os.path.join("ugc",
                                         "test_water_kind_tally.py"), 7),
    # R1802 water journal monthly_flow: by-month net-flow aggregation
    # (window=None whole-board default; explicit YYYY-MM single-month
    # read; month keys ascending; row keys exactly {month, windows,
    # total_delta} with signed sums; total==sum windows and
    # net_delta==sum total_delta invariants)
    # (AC-MF1..MF7 pre-registered in state/queue/tech.md)
    ("ugc-water-monthlyflow", os.path.join("ugc",
                                          "test_water_monthly_flow.py"), 7),
    # R1803 water journal journal_board month-window filter: the full
    # time-ordered row list gains an optional YYYY-M read (ts_utc
    # record-time filter, one ORDER BY clause - the in-window order is
    # the full-board order restricted to the window, zero re-sorting;
    # explicit window adds the window key, default face unchanged)
    # (AC-JB1..JB7 pre-registered in state/queue/tech.md)
    ("ugc-water-journalwin", os.path.join("ugc",
                                          "test_water_journal_window.py"), 7),
    # R1804 water journal journal_board read-cap: limit=0 keeps the
    # full-list behavior; limit>0 returns the ascending tail window of
    # N rows (mirror-SQL law: DESC/DESC LIMIT N reversed back to board
    # order, R1729 AC-UL4 family) and adds exactly {limit, returned,
    # truncated} - total reports the full filtered count so a
    # truncated board never lies; window filter composes ahead of the
    # cap; both-bad args hit the limit gate first (E_WJ_BAD_LIMIT)
    # (AC-JL1..JL7 pre-registered in state/queue/tech.md)
    ("ugc-water-journalcap", os.path.join("ugc",
                                         "test_water_journal_limit.py"), 7),
    # R1805 water journal cell_totals: cumulative per-cell net-flow
    # aggregation over the archived delta rows (window=None
    # whole-board default; explicit YYYY-MM month filter; sparse
    # union of cell keys, ascending; envelope total == SUM of the
    # total_delta column == monthly_flow net_delta; the verdicted
    # cells keep their own keys and stay out of the envelope total -
    # the R1785 composition law, AC-VW1 verdict windows land -1)
    # (AC-CT1..CT7 pre-registered in state/queue/tech.md)
    ("ugc-water-celltotals", os.path.join("ugc",
                                          "test_water_cell_totals.py"), 7),
    # R1786 member expiring-board tier/line fold: aggregation-only
    # face over the expiring_soon board (single window-derivation
    # source, R1779 law; sparse ascending keys)
    # (AC-ESD1..ESD7 pre-registered in state/queue/tech.md)
    ("member-expiring-dist", os.path.join("member",
                                         "test_expiring_dist.py"), 7),
    # R1825 apidev rotation lineage one-shot read face: the
    # R1824 lifecycle_trace successor -- rotate_in walked upward
    # plus rotate_out walked downward in one ordered chain
    # (oldest ancestor first, queried key in the middle, newest
    # descendant last), every member block locked field-equal to
    # lifecycle_trace on that member (zero drift between the two
    # faces), member blocks exposing zero foreign raw api_keys,
    # dead keys fully readable, embedded faces untouched
    # (AC-LG1..LG7 R1825 + AC-LG8..LG15 R1887 window lens +
    # AC-LG16..LG22 R1888 read cap, pre-registered in
    # state/queue/tech.md)
    ("ledger-apidev-lineage", os.path.join("ledger",
                                           "test_apidev_lineage.py"), 22),
    # R1833 apidev lineage chain-usage one-shot read face: the
    # R1825 audit_lineage successor -- per-chain-member call
    # counts for one window in a single read (chain walked the
    # audit_lineage way, cross-face zero drift pinned by the
    # suite), the prefix sum over ancestors+queried pinned equal
    # to the quota ring's ancestry-only anti-evasion effective
    # count and to key_view quota_used for the current window,
    # chain_total split into that prefix plus the descendants'
    # own rows (audit view vs enforcement face), 14 bad-window
    # forms fail-closed, historical/future month semantics on the
    # record-time window column, dead keys fully readable,
    # embedded faces untouched, month-rollover truth preservation
    # (AC-LU1..LU7 R1833 + AC-LU8 R1839 + AC-LU9..LU14 R1893
    # read-cap pre-registered in state/queue/tech.md)
    ("ledger-apidev-chainusage", os.path.join("ledger",
                                             "test_apidev_chainusage.py"),
     14),
    # R1845 apidev dev_board month-rollover re-domain fidelity:
    # the account-level no-window-param panel re-domains honestly
    # when the frozen clock crosses the month boundary (window
    # key rolls, per-key faces + both total keys honest all-zero
    # before any new call, October quota reject row
    # record-time-stamped in reject_events never penetrates the
    # new-month panel tally, old month preserved as explicit
    # window reads, November call re-computes the panel, immutable
    # rows never lost) -- the panel symmetric case closing the
    # month-roll family (AC-DBR1..DBR7 pre-registered in
    # state/queue/tech.md; zero product bytes, pin-only suite)
    ("ledger-apidev-devboard-roll", os.path.join("ledger",
                                                "test_apidev_devboard_roll.py"),
     7),
    # R1852 apidev dev_board read-cap parameter window: the
    # account-level key board gains an optional limit tail
    # parameter (limit=0 default keeps the full-board envelope
    # byte-stable for every existing consumer; limit>0 bounds the
    # keys list to the most recent limit rows -- highest key_ids,
    # tail-window slice of the ascending key_id order -- and
    # adds an overflow block limit/total/returned/truncated with
    # total = the full key-row count; the world aggregates stay
    # full-world, truncation only cuts the keys list; five bad
    # limit forms reject the dedicated E_AD_BAD_LIMIT code
    # fail-closed before any read; the capped read stays honest
    # across the month rollover, orthogonal to the R1845 roll
    # panel) -- the apidev read-cap family row after the R1729
    # usage_log precedent (AC-DBL1..DBL8 pre-registered in
    # state/queue/tech.md)
    ("ledger-apidev-devboard-limit", os.path.join("ledger",
                                                 "test_apidev_devboard_limit.py"),
     14),
    # R1863 apidev dev_board ancestry-in-explicit-window
    # anti-evasion example: the per-key quota_used carries the
    # quota ring's ancestry semantics inside EXPLICIT history
    # window reads too (the R1857 AC-DBL12 mirror used fresh
    # zero-ancestry keys, leaving this face uncovered) -- the
    # rotate successor's explicit-window quota_used includes the
    # ancestor's window rows (board == chain_usage
    # effective_upto_queried == key_view current-window three
    # faces align), the own-only SQL mirror discriminates 1 != 3,
    # ancestors never inherit descendants, the old-month explicit
    # window projection is byte-preserved across the month roll
    # (minute fields + lifetime billing stripped per the
    # clock-orthogonal / lifetime-face rulings, two first-run
    # reds on record; zero product bytes, pin-only suite)
    # (AC-ANW1..ANW7 pre-registered in state/queue/tech.md)
    ("ledger-apidev-devboard-ancestry", os.path.join(
        "ledger", "test_apidev_devboard_ancestry.py"), 7),
    # R1868 apidev key_view explicit historical window read:
    # the single-key panel gains the optional window=None tail
    # parameter -- default keeps the current-UTC-month behavior
    # byte-stable (no-arg == window=None, the 18-key envelope
    # unchanged); an explicit "YYYY-MM" month re-domains the
    # quota panel (quota_used / quota_remaining / reject_tally /
    # usage_kind_tally window-scoped, the quota counter keeping
    # the rotation-chain ancestry semantics so a rotate never
    # resets an explicit month either); the minute ring stays
    # clock-orthogonal; a historical month stays readable forever
    # and a future month is an honest all-zero panel; 14 bad
    # window forms reject the dedicated E_AD_BAD_WINDOW fail-closed
    # (panel-class code per the dev_board precedent, claim-round
    # judgment recorded) after the key gate; the R1863 AC-ANW
    # three-face interlock carries to the single-key face:
    # key_view(key, window=W) quota_used == dev_board(window=W)
    # board row == chain_usage(key, window=W) effective_upto_queried
    # in the anchor month and across the roll; the old-month
    # window projection is byte-preserved across the month roll
    # (minute fields clock-orthogonal, the AC-ANW5 premise)
    # (AC-KVW1..KVW7 pre-registered in state/queue/tech.md)
    ("ledger-apidev-keyviewwin", os.path.join(
        "ledger", "test_apidev_keyviewwin.py"), 7),
    # R1864 water journal month-roll fidelity: frozen-clock +23d
    # cross-month pin over the four window-parameter read faces
    # (journal_board/kind_tally/monthly_flow/cell_totals) - new-
    # month windows land in new-month cells on record-time stamps,
    # old-month window reads preserved byte-identical across the
    # roll, default all-window reads carry the cross-month rows,
    # month-axis telescoping per face (sum of observed month-window
    # totals == all-window total; cell_totals total ==
    # monthly_flow net_delta cross-face law), read-cap x window
    # orthogonality, immutable rows never lost
    # (AC-WMR1..WMR7 pre-registered in state/queue/tech.md)
    ("ugc-water-journalroll", os.path.join(
        "ugc", "test_water_journal_roll.py"), 7),
    # R1865 sec_batch rows_by_status/queue_counts monthly-roll
    # preservation example (AC-RQR1..AC-RQR7 pre-registered in
    # state/queue/tech.md): new-month degraded rows land in the
    # new-month window via the real product path, old-month window
    # reads preserved byte-identical, immutable rows never lost, and
    # the cross-month drain keeps window attribution on the LANDING
    # month (drain writes status + ts_drained only; ts_drained is the
    # drain month while the row still reads under its landing-month
    # window - R1860 AC-SB21 law enforced as the roll example)
    ("ugc-sec-batch-rowsroll", os.path.join(
        "ugc", "test_sec_batch_rowsroll.py"), 7),
    # R1896 apidev audit_lineage capped-windowed read
    # restart-persistence example window (the R1891 seed): the
    # three-piece stack (Ledger -> MeteredFace -> DevKeyFace)
    # closes fully and reopens on the same db path and config --
    # the October capped-windowed lineage envelope (window echo +
    # overflow block) replays byte-identical from the fresh
    # instance (zero in-memory drift in the derived face), a
    # November revoke on an isolated lone key recalculates the
    # default capped read (zero cache) while the October windowed
    # chain reads stay byte-frozen (key_events rows are
    # record-time immutable; the injected key lives outside the
    # October chain's key domain per the claim ruling), and a
    # third instance replays the post-injection state
    # byte-identically (two-instance sequential reads)
    # (AC-LG23..AC-LG29 pre-registered in state/queue/tech.md)
    ("ledger-apidev-lineagepersist", os.path.join(
        "ledger", "test_apidev_lineagepersist.py"), 7),
    # R1897 apidev chain_usage capped-windowed read
    # restart-persistence example window (the R1893 seed): the
    # three-piece stack (Ledger -> MeteredFace -> DevKeyFace)
    # closes fully and reopens on the same db path and config --
    # the October capped-windowed usage envelope (window echo +
    # overflow block) replays byte-identical from the fresh
    # instance (zero in-memory drift in the derived face), two
    # November calls on the live chain-tail key C via the real
    # product path recalculate the default capped read (zero
    # cache) while the October windowed reads stay byte-frozen
    # (api_calls rows are record-time immutable; the injection
    # lands on the very key whose October capped read is pinned
    # -- a stronger hijack face than the R1896 isolated-key
    # injection per the claim ruling), and a third instance
    # replays the post-injection state byte-identically
    # (two-instance sequential reads)
    # (AC-LU15..AC-LU21 pre-registered in state/queue/tech.md)
    ("ledger-apidev-chainusagepersist", os.path.join(
        "ledger", "test_apidev_chainusagepersist.py"), 7),
    # R1902 apidev dev_board capped-windowed read
    # restart-persistence example window (the R1896 seed): the
    # three-piece stack (Ledger -> MeteredFace -> DevKeyFace)
    # closes fully in reverse dependency order and reopens on
    # the same db path and config bytes -- the October
    # windowed capped envelope (window re-domained panel x cap
    # tail-slice, window echo + overflow block, world
    # aggregates staying full-world under truncation) replays
    # byte-identical from the fresh instance (zero in-memory
    # drift in the derived face), two November calls on
    # chain-c -- the very key the October capped read pins in
    # its tail slice -- recalculate the default capped read via
    # the real product path (zero cache) while the October
    # windowed reads stay window-frozen under the window-scoped
    # projection (api_calls rows are record-time immutable; the
    # clock-following minute fields and the lifetime billing
    # block are stripped per the R1863 AC-DBL13 rulings for the
    # cross-clock face; the pure-restart face compares the FULL
    # envelope), and a third instance replays the
    # post-injection state byte-identically (two-instance
    # sequential reads)
    # (AC-DBL15..AC-DBL21 pre-registered in
    # state/queue/tech.md)
    ("ledger-apidev-devboardpersist", os.path.join(
        "ledger", "test_apidev_devboardpersist.py"), 7),
    # R1898 eventtickets event_audit_board capped-windowed read
    # restart-persistence example window (the R1894 seed): the
    # two-piece stack (Ledger -> EventTicketFace) closes fully
    # in reverse dependency order and reopens on the same db
    # path and config bytes -- the October capped-windowed
    # board envelope (window echo + overflow block) replays
    # byte-identical from the fresh instance (zero in-memory
    # drift in the derived face), a November purchase plus a
    # November check-in on the live tail-slice session delta
    # via the real product path recalculate the default board
    # and the default capped read (zero cache) while the
    # October windowed reads stay byte-frozen (purchase and
    # check-in rows are record-time immutable; the injection
    # lands inside the very tail slice the October capped read
    # pins -- a stronger double-hijack face than the R1896
    # isolated-key injection per the claim ruling), and a third
    # instance replays the post-injection state
    # byte-identically (two-instance sequential reads)
    # (AC-EAW8..AC-EAW14 pre-registered in
    # state/queue/tech.md)
    ("ledger-eventtickets-boardpersist", os.path.join(
        "ledger", "test_eventtickets_boardpersist.py"), 7),
    # R1930: eventtickets session_board/attendees/active_sessions
    # three read-face family derivation purity across an instance
    # restart (seed = the R1771/R1926 tech-queue claim row; the
    # R1898 boardpersist seat covers event_audit_board only -
    # the three session/check-in boards were zero-registered for
    # the restart face). Two-piece stack close -> reopen same
    # db/config replays the ten pre-close board reads
    # byte-identical; a November purchase + check-in on the live
    # gala session plus a fresh newmo registration recompute the
    # touched boards (zero cache) while untouched boards and
    # non-covering schedule windows stay byte-frozen; a third
    # instance replays the post-injection state byte-identically
    # (AC-SBP1..AC-SBP7 pre-registered in
    # state/queue/tech.md)
    ("ledger-eventtickets-sessionpersist", os.path.join(
        "ledger", "test_eventtickets_sessionpersist.py"), 7),
    # R1900: member expiring_soon board + distribution fold
    # read-face derivation purity across an instance restart
    # (seed = the R1899 tech-queue claim row; AC-ES1..ES7 R1774
    # window semantics + AC-ESD1..ESD7 R1786 fold semantics in
    # ce, the cross-instance restart example was zero-registered;
    # MemberStore close-reopen on the same db/cfg/pay replays the
    # frozen-as_of snapshot quartet byte-identically, the
    # same-grant re-activation stays idempotent (source_grant_id
    # db-backed dedup), a new true-path activation recomputes the
    # board (zero cache) and out-of-window rows never echo)
    # (AC-ES8..AC-ES14 pre-registered in
    # state/queue/tech.md)
    ("member-expiring-soon-persist", os.path.join(
        "member", "test_expiring_soon_persist.py"), 7),
    # R1903 apidev usage_log capped-windowed read
    # restart-persistence example window (the R1897 seed): the
    # three-piece stack (Ledger -> MeteredFace -> DevKeyFace)
    # closes fully in reverse dependency order and reopens on
    # the same db path and config bytes -- the October windowed
    # capped envelope (window echo + overflow block over the
    # immutable five-key call rows) replays byte-identical
    # from the fresh instance (zero in-memory drift), two
    # November calls on chain-b -- the very key whose October
    # capped-windowed read is pinned in its tail slice --
    # recalculate the default capped and default bare reads
    # via the real product path (zero cache) while the October
    # windowed reads stay FULL-envelope byte-frozen (api_calls
    # rows are record-time immutable and the envelope carries
    # zero clock-following fields, so the claim ruling-3
    # full-envelope face needs no projection), and a third
    # instance replays the post-injection state
    # byte-identically (two-instance sequential reads)
    # (AC-UW9..AC-UW15 pre-registered in
    # state/queue/tech.md)
    ("ledger-apidev-usagelogpersist", os.path.join(
        "ledger", "test_apidev_usagelogpersist.py"), 7),
    # R1905 water journal journal_board cap-window combined read
    # restart-persistence example window (the R1900 seed): the
    # single-writer face closes and a fresh instance reopens on
    # the same db path and disclaimer -- the October capped-
    # combined read (window echo + overflow block + ascending
    # tail slice == mirror-SQL rows) replays byte-identical
    # from the fresh instance (zero in-memory drift in the
    # derived face), frozen-clock November windows land via the
    # real record() path and recompute the default and
    # default-cap reads zero-cache while the October window
    # reads stay byte-frozen (record-time rows immutable), and
    # a third instance replays the post-injection state
    # byte-identically (two-instance sequential reads)
    # (AC-JL8..AC-JL14 pre-registered in
    # state/queue/tech.md)
    ("ugc-water-journalboardpersist", os.path.join(
        "ugc", "test_water_journal_boardpersist.py"), 7),
    # R1910 water journal three-sister read faces (kind_tally /
    # monthly_flow / cell_totals) windowed-read restart-persistence
    # example window (the R1905 seed): the three aggregation
    # faces close and a fresh instance reopens on the same db --
    # each sister's three read shapes (default / October explicit
    # window / empty-month honest-empty) replay byte-identical to
    # the pre-close snapshots (zero in-memory drift), frozen-clock
    # November windows land via the real record() path on the
    # fresh instance and recompute the default reads zero-cache
    # (cross-face laws re-verified on the new set) while the
    # October window reads stay byte-frozen (record-time rows
    # immutable), and a third instance replays the post-injection
    # state byte-identically (two-instance sequential reads)
    # (AC-KT8..KT10 / AC-MF8..MF10 / AC-CT8..CT10 /
    # AC-MW6..MW8 pre-registered in state/queue/tech.md)
    ("ugc-water-sisterpersist", os.path.join(
        "ugc", "test_water_journal_sisterpersist.py"), 12),
    # R1907 apidev key_view windowed panel read restart-persistence
    # example window (the R1902 seed): the three-piece stack
    # (Ledger -> MeteredFace -> DevKeyFace) closes fully in
    # reverse dependency order and reopens on the same db path
    # and config bytes -- the October explicit-window 18-key
    # panel (window echo + ancestry quota counter + exact-key
    # reject/usage tallies + lifecycle status) replays
    # byte-identical from the fresh instance while the clock
    # stands still (zero in-memory drift, full-envelope
    # comparable because the two minute-ring fields are frozen
    # too), two November calls on roll-b -- the very key whose
    # October panel is pinned -- recalculate the default read via
    # the real product path (zero cache) while the October
    # windowed read stays byte-frozen under the banded projection
    # (the two clock-following minute fields stripped; api_calls
    # rows are record-time immutable so the old window never
    # permeates), and a third instance replays the
    # post-injection state byte-identically (two-instance
    # sequential reads)
    # (AC-KVW8..AC-KVW14 pre-registered in
    # state/queue/tech.md)
    ("ledger-apidev-keyviewpersist", os.path.join(
        "ledger", "test_apidev_keyviewpersist.py"), 7),
    # R1908 apidev reject_tally windowed read cross-restart
    # persistence: three-piece close/reopen replays the October
    # windowed diagnostic aggregate (window echo + by_reason
    # GROUP BY + total over immutable key-attributed reject
    # rows) byte-for-byte; one November disabled-kind reject on
    # the pinned key (ancestry-inclusive cap-3 dual-reject world)
    # recalculates the clock-following default read (zero cache)
    # while the October windowed read stays byte-frozen; third-
    # instance identity; pure-read law + hygiene
    # (AC-RJW8..AC-RJW14 pre-registered in state/queue/tech.md)
    ("ledger-apidev-rejecttallpersist", os.path.join(
        "ledger", "test_apidev_rejecttallpersist.py"), 7),    # R1909 apidev lifecycle_trace windowed read cross-restart
    # persistence suite: the pinned active middle key (one real
    # October rotate_in row) plus a lone terminal-revoked key;
    # full-envelope byte-replay across the three-piece close/reopen,
    # one November rotation on the pinned key recalculates the
    # default full-trail read zero-cache while the October windowed
    # read freezes at the trail block (full-derived key facts
    # re-derive, the R1875 window-lens law), lone-e keeps the
    # full-envelope freeze, third-instance identity; pure-read
    # law + hygiene (AC-TRW8..AC-TRW14 pre-registered in
    # state/queue/tech.md)
    ("ledger-apidev-lifecycletracepersist", os.path.join(
        "ledger", "test_apidev_lifecycletracepersist.py"), 7),
    # R1911 apidev usage_kind_tally windowed read cross-restart
    # persistence suite: October mixed-kind six-call anchor on
    # the rotated chain-b (exact-key attribution; the rotated_out
    # chain-a read face stays open), full-envelope byte-replay
    # across the three-piece close/reopen, two November calls on
    # the pinned key recalculate the clock-following default read
    # zero-cache while the October explicit-window read stays
    # byte-frozen; future-window honest empty; third-instance
    # identity; pure-read law + hygiene (AC-UKP1..AC-UKP7
    # pre-registered in state/queue/tech.md)
    ("ledger-apidev-usagekindpersist", os.path.join(
        "ledger", "test_apidev_usagekindpersist.py"), 7),
    # R1912 member balance_face entitlement-balance panel read-face
    # restart-persistence suite (the R1907 seed): MemberStore
    # close-reopen on the same db/cfg/pay replays the five-avatar
    # panel snapshots byte-identically (full envelope: zero
    # clock-following fields, zero window params, no projection
    # band), the same-grant re-activation stays idempotent
    # (source_grant_id db-backed dedup), one new true-path
    # activation (EP-D) plus one new consumption (EP-A) recompute
    # their panels zero-cache while sibling avatars stay
    # byte-frozen, and a third instance replays the post-new-data
    # state byte-identically (two-instance sequential reads);
    # honest product-path note: the EP-B renewal stacking world
    # rides the granted->closed refund edge because
    # compute_order_id buckets on the closed order count
    # (AC-BFP1..AC-BFP7 pre-registered in
    # state/queue/tech.md)
    ("member-balanceface-persist", os.path.join(
        "member", "test_balance_face_persist.py"), 7),
    # R1916 privileges_for/has_privilege privilege read faces
    # cross-restart persistence suite (the R1912 seed): a fresh
    # MemberStore on the same db/cfg/pay dock re-derives the same
    # privilege envelopes byte-identically, the rejection family
    # fires identically, a new true-path activation recomputes
    # zero-cache while siblings stay byte-frozen, and a new
    # consumption moves zero privilege bytes (the
    # balance-invariance pin)
    # (AC-PRP1..AC-PRP7 pre-registered in
    # state/queue/tech.md)
    ("member-privileges-persist", os.path.join(
        "member", "test_privileges_persist.py"), 7),
    # R1913 drain_recover recovery-window water read faces
    # cross-restart persistence suite (the R1908 seed): the full
    # pipeline stack (store + batch + journal) closes and a fresh
    # UGCPipeline reopens on the same config bytes and db path --
    # the October explicit-window board read and the default
    # whole-board read replay byte-identically to the pre-close
    # snapshots, the store levels envelope replays byte-identically
    # while the fresh instance's single-slot last_water_delta()
    # reads an honest None (the journal is the history carrier),
    # NEW degraded rows queued on the restarted instance land one
    # November drain window through the REAL drain_recover()
    # product path which recomputes the default read zero-cache
    # while the October window read stays byte-frozen (record-
    # time rows immutable, zero penetration), and a third
    # instance replays the post-injection state byte-identically
    # (double-restart x new-data no drift)
    # (AC-DR7..AC-DR13 pre-registered in state/queue/tech.md)
    ("ugc-drain-waterpersist", os.path.join(
        "ugc", "test_drain_waterpersist.py"), 7),
    # R1929 pool-water read-face family cross-restart persistence
    # suite (the R1926 reseed claimed after the former queue head
    # was duplicate-closed): the seed's named carrier is the
    # STORE-level restart - UGCStore close -> new UGCStore over
    # the same ugc.db (R1913 AC-DR9 pinned only the levels
    # envelope across a full pipeline-stack restart in the drain
    # world). Both faces pin: the reopened levels read and the
    # delta(caller-held pre-close snapshot) re-derive
    # byte-identically (steady {} / total_delta 0), NEW noise +
    # gray + verdict flows through the real same-db pipeline
    # recompute both faces zero-cache with the change-only delta
    # semantics enforced across the restart (net-zero suspended
    # cell omitted), and a second restart's third instance
    # replays the post-flow state byte-identically on sequential
    # double reads; pure-read law + manual-SQL cross +
    # store.py sha256 double-proof (suite-only round)
    # (AC-PWP1..AC-PWP7 pre-registered in state/queue/tech.md)
    ("ugc-pool-waterpersist", os.path.join(
        "ugc", "test_pool_waterpersist.py"), 7),
    # R1917 review-desk read faces (pool_query + chronicle_query)
    # cross-restart persistence suite (the R1913 seed): a fresh
    # UGCPipeline on the same config bytes and db path re-derives
    # the pool envelope (pooled + drafted bodies with the rule-
    # template draft json), the line-filtered pool reads and the
    # city-chronicle envelope byte-identically to the pre-close
    # snapshots; NEW submissions on the restarted instance (one
    # standing draft + one small-idea adopt through the real
    # submit->draft->final_review->final_decide path) recompute the
    # whole pool and chronicle zero-cache while untouched lines and
    # pre-existing rows stay byte-frozen; the honest empty line
    # filter and the states= parameter face are pinned; a third
    # instance replays the post-injection state byte-identically
    # (double-restart x new-data no drift)
    # (AC-RDP1..AC-RDP7 pre-registered in state/queue/tech.md)
    ("ugc-reviewdesk-persist", os.path.join(
        "ugc", "test_reviewdesk_persist.py"), 7),
    # R1918 member birth_cert_face read-face derivation
    # purity across an instance restart (the R1915 seed):
    # the permanent entrance qualification face (the
    # pay.grants_for live-grant judgement + the
    # member_audit birth marker) replays byte-identically
    # from a fresh MemberStore on the same db/cfg/pay dock
    # (six faces: five avatar shapes + the blank probe),
    # a new true-path grant recomputes zero-cache while
    # MIN(granted_utc) keeps the historical anchor, a
    # refund flips the live judgement but preserves
    # history and the activation marker (R1721 semantics
    # across the restart boundary), and the first-paid-
    # activation marker stamps across the restart boundary
    # with idempotent re-activation stability
    # (AC-BCP1..AC-BCP7 pre-registered in
    # state/queue/tech.md)
    ("member-birthcert-persist", os.path.join(
        "member", "test_birthcert_persist.py"), 7),
    # R1919: member expiring_distribution fold read-face
    # derivation purity across an instance restart - default-
    # read restoration, second-order window membership, numeric
    # key-order evidence (AC-ESD8..AC-ESD14 pre-registered in
    # state/queue/tech.md; suite-only round, zero product
    # change)
    ("member-expiring-dist-persist", os.path.join(
        "member", "test_expiring_dist_persist.py"), 7),
    # R1920 UGC export three-outflow faces: same-instance re-export
    # determinism + chronicle-step migration idempotency (rejected->
    # chronicled exactly once) + file-byte persistence across the
    # full pipeline-stack restart (feed per-line / chronicle /
    # hot_index; the tie law = the stable sort keeps the
    # items_in_states ts-ascending order inside equal-score
    # segments; November new data recomputes hot zero-cache while
    # the untouched line feeds and the record-time rows stay
    # byte-frozen; a third instance replays byte-identically)
    # (AC-EXP1..AC-EXP7 pre-registered in state/queue/tech.md;
    # suite-only round, zero product change)
    ("ugc-export-persist", os.path.join(
        "ugc", "test_export_persist.py"), 7),
    # R1925 ledger showcase read faces (showcase_view /
    # chronicle / chronicle_tour) cross-restart persistence
    # example (the R1921 reseeded queue head, claimed after the
    # R1920 lobby room_message_board row closed as an in-book
    # duplicate): pre-close eight-shape snapshot == post-reopen
    # read byte-identical across the full-stack close/rebuild;
    # post-restart place/retract recomputes zero-cache with
    # event_id continuity and tour stop renumbering; retract-
    # then-re-place chain + unknown-showcase fail-closed gates
    # survive the restart; a third instance replays the final
    # state byte-identically while october anchor events stay
    # frozen (AC-SHVP1..AC-SHVP7 pre-registered in
    # state/queue/tech.md; suite-only round, zero product change)
    ("ledger-showcaseview-persist", os.path.join(
        "ledger", "test_showcase_persist.py"), 7),
    # R1931 collectibles cross-restart persistence window: the
    # collectibles seat of the R1742 family (curation regpersist
    # R1926 + civic persist R1927 in-book, this seat was absent);
    # close -> reopen byte-identical read replay, post-restart
    # continuation (numbering counter, sold-out cap, spend tx
    # binding), UNIQUE gate survival, cap-lock authority over a
    # divergent cap argument, third instance stability
    # (AC-CLP1..AC-CLP7 pre-registered in state/queue/tech.md;
    # suite-only round, zero product change)
    ("ledger-collectibles-persist", os.path.join(
        "ledger", "test_collectibles_persist.py"), 7),
    # R1933 liveroom risk-control read-face family cross-restart
    # persistence window (persist-family seat, R1886 lineage):
    # two-piece stack close -> same-db reopen replays the nine read
    # faces (funnel/transcript/conversion_ledger x closed/open/empty
    # sessions) byte-for-byte, the risk-control law survives the
    # restart (closed-session writers, dup window, anonymous and
    # unknown refusals, zero side effects), post-restart real-path
    # injection recomputes the open-session faces while the closed
    # and empty sessions stay byte-frozen, third instance keeps the
    # guarantee (AC-LRP1..LRP7 pre-registered in state/queue/tech.md;
    # suite-only round, zero product change).
    ("liveroom-persist", os.path.join(
        "liveroom", "test_liveroom_persist.py"), 7),
    # R1934 tourstate cross-process re-derivation window (persist-
    # family seat, R1886 lineage; suite-only round - zero product
    # change). tourstate is a pure stateless prep face (zero sqlite,
    # zero file substrate), so the restart carrier is a fresh
    # interpreter subprocess: both legs re-derive byte-identical
    # across sequential cold processes, tamper and bad-input law
    # survive the process boundary, module state zero-drift
    # (AC-TSP1..TSP7 pre-registered in state/queue/tech.md).
    ("tourstate-persist", os.path.join(
        "tourstate", "test_tourstate_persist.py"), 7),
    # R1935 datasub cross-restart persistence window (persist-family
    # seat, R1886 lineage; suite-only round - zero product change):
    # two-piece close -> same-db reopen replays the nine read faces
    # (bundle/view x2/subscription_view x4/reconcile x2) plus four
    # balances byte-for-byte, the pre-spend gate family survives the
    # restart (dup window, dup ref, dup delivery ref, not-subscribed,
    # bad window, register conflict + idempotence) with zero row/
    # balance drift, post-restart real-path continuation recomputes
    # the derived counts while the descriptor bundle and untouched
    # account faces stay byte-frozen, zero cross-dataset permeation,
    # third instance stability (AC-DSP1..DSP7 pre-registered in
    # state/queue/tech.md).
    ("ledger-datasub-persist", os.path.join(
        "ledger", "test_datasub_persist.py"), 7),
    # R1982 dataset subscription coverage board: registry-keyed
    # pure-read derived board (distinct-household subscribers,
    # subscription rows, delivery counts; three-key deterministic
    # order; AC-CVB1..CVB7 pre-registered in state/queue/
    # explore.md).
    ("ledger-datasub-coverage", os.path.join(
        "ledger", "test_datasub_coverage.py"), 7),
    ("ledger-devshare-persist", os.path.join(
        "ledger", "test_devshare_persist.py"), 7),
    # R1946 apimarket persist seat of the R1886 family: four-piece
    # full-chain restart (am/dk/metered/led), byte-identical read
    # replay across board/view/ratings/sales + balances, ten
    # restart-surviving gate probes, post-restart continuation with
    # a fresh bound spend/share pair, frozen immutable rows + dup
    # gates, pure-read law, third instance stability (AC-AMP1..AMP7
    # pre-registered in state/queue/tech.md).
    ("ledger-apimarket-persist", os.path.join(
        "ledger", "test_apimarket_persist.py"), 7),
    # R1978 developer sales board: developer-level sales/revenue
    # aggregation read face dev_sales_board() - row-set authority
    # = distinct listing dev_account (listed-but-unsold developer
    # stays visible with an honest zero row; zero-listing accounts
    # never appear), six-key row set with per-row gross == dev +
    # platform conservation (integer split law), deterministic
    # order dev_revenue DESC / purchase_count DESC / dev_account
    # ASC, api_sales cross-derivation, pure-read law, empty-market
    # honest [] (AC-AMB1..AMB7 pre-registered in the R1978
    # explore-queue claim row).
    ("ledger-apimarket-devboard", os.path.join(
        "ledger", "test_apimarket_devboard.py"), 7),
    # R1947 effects persist seat of the R1886 family: two-piece
    # restart (the face rides the same ledger.db with its own
    # connection), byte-identical read replay across credits and
    # effects views for three accounts + four balances, nine
    # restart-surviving gate probes, post-restart continuation
    # where pre-restart credits keep serving new uses and a fresh
    # purchase->use chain lands on a new account, three-lane
    # frozen faces (R1947 first-run erratum: continuation-consumed
    # credits freeze identity columns with asserted transition) +
    # idempotent replay gates, pure-read law, third instance
    # stability (AC-EFP1..EFP7 pre-registered in
    # state/queue/tech.md).
    ("ledger-effects-persist", os.path.join(
        "ledger", "test_effects_persist.py"), 7),
    # honorcert cross-restart persist window (R1948): three-piece
    # restart world, incremental heal + permanent-certificate law,
    # replay gates, pure-read law, third instance stability
    # (AC-HCP1..HCP7 pre-registered in state/queue/tech.md).
    ("ledger-honorcert-persist", os.path.join(
        "ledger", "test_honorcert_persist.py"), 7),
    # honor yearbook cross-restart persist window (R1981): the
    # yearbook seat of the R1948 honorcert persist family -
    # pinned anchor + byte-identical restart replay on both
    # years + live continuation (board move heal + off-slice
    # permanence + cross-year isolation) + gate survival +
    # pure-read law + third instance stability (AC-HYP1..HYP6
    # pre-registered in state/queue/explore.md).
    ("ledger-honorcert-yearbookpersist", os.path.join(
        "ledger", "test_honorcert_yearbook_persist.py"), 6),
    # studio cross-restart persist window (R1949): three-piece
    # restart world (registry + venue occupancy + ledger), twelve
    # restart-surviving gates, renewal advance booking, frozen
    # prefix rows, pure-read law, third instance stability
    # (AC-STP1..STP7 pre-registered in state/queue/tech.md).
    ("ledger-studio-persist", os.path.join(
        "ledger", "test_studio_persist.py"), 7),
    # R1950 showroom persist seat of the R1886 family: four-piece
    # restart world (ledger + venue + ads + showroom face, the
    # bundle granted only through the two referenced products'
    # public APIs), byte-identical read replay across all six
    # showroom read faces + carousel/occupancy faces, twelve
    # restart-surviving gate probes, post-restart continuation
    # (fresh-enterprise first contract + same-package third-window
    # renewal), frozen prefix rows + dup-pkg replay gate, pure-read
    # law, third instance stability (AC-SHWP1..SHWP7
    # pre-registered in state/queue/tech.md).
    ("ledger-showroom-persist", os.path.join(
        "ledger", "test_showroom_persist.py"), 7),
    # R1951 tmarket persist seat of the R1886 family: three-piece
    # restart world (ledger + gate + tmarket face; the content
    # gate is the lobby SecGate product re-wired on every
    # reopen), the full read battery (four template views +
    # market/rating/sales faces + six balances) replays
    # byte-identical, eleven restart-surviving gate probes
    # (fail-closed, zero rows, zero charge), post-restart
    # continuation (fresh creator publish + two purchases + a new
    # rating), frozen immutable anchor rows + replay gates,
    # pure-read law, third instance stability (AC-TMP1..TMP7
    # pre-registered in state/queue/tech.md).
    ("ledger-tmarket-persist", os.path.join(
        "ledger", "test_tmarket_persist.py"), 7),
    # R1952 festival persist seat (R1886 family, R1947 seed):
    # cross-restart window for the solar-term / festival
    # limited-event face - three-instance world on the real
    # product path (Ledger + CollectiblesFace + FestivalFace),
    # full read battery (event views / schedule-window listings /
    # per-event purchase boards / five collection faces / six
    # balances) replays byte-identical, eleven restart-surviving
    # gate probes (fail-closed, zero rows, zero charge, incl the
    # collectibles UNIQUE backstop E_CL_DUP re-probe),
    # post-restart continuation (fresh event registration + two
    # new first-purchases granting new commemorative certificates),
    # frozen immutable anchor rows + replay gates, pure-read law,
    # third instance stability (AC-FCP1..FCP7 pre-registered in
    # state/queue/tech.md).
    ("ledger-festival-persist", os.path.join(
        "ledger", "test_festival_persist.py"), 7),
    # R1953 sistercity persist seat (R1886 family, R1948 seed):
    # cross-restart window for the sister-city cross-city visit
    # face - two-piece restart world on the real product path
    # (Ledger + SisterCityFace; the four twin tables carry all
    # persistence, the embedded settlement chain is in-memory by
    # design and manifests persist as twin_settlements rows),
    # full read battery (three twin views + four schedule-window
    # listings + two audit boards + six balances) replays
    # byte-identical, thirteen restart-surviving gate probes
    # (fail-closed, zero rows, zero charge, incl the persisted
    # settlement replay gate E_SC_SETTLED and the no-disclaimer
    # constructor gate), post-restart continuation (fresh twin
    # registration + new visit pass + new exposure booking +
    # fresh-chain window settle), frozen immutable anchor rows +
    # replay gates, pure-read law, third instance stability
    # (AC-SCP1..SCP7 pre-registered in state/queue/tech.md).
    ("ledger-sistercity-persist", os.path.join(
        "ledger", "test_sistercity_persist.py"), 7),
    # R1959 growth-archive persist seat (R1886 family, R1954
    # seed): cross-restart window for the resident growth-archive
    # subscription face - two-piece restart world on the real
    # product path (Ledger + GrowthArchiveFace; two-month
    # two-buyer subscriptions each binding exactly one real
    # spend tx, append-only supply events), full four-element
    # read battery (two month pages + per-account subscription
    # views + residents census + compliance, stdout-safe
    # projections keeping subscribed_utc and spend tx ids
    # in-db-only) replays byte-identical, seven restart-surviving
    # gate probes (fail-closed, zero rows, zero charge),
    # post-restart continuation (new 2099-03 city_story event +
    # third-month subscription + new-resident subscription with
    # the 2099-01 page frozen byte-identical = in-month window
    # isolation), frozen anchor rows + dup-before-spend replay
    # gate, pure-read law, third instance stability
    # (AC-GAP1..GAP7 pre-registered in state/queue/tech.md).
    ("ledger-growth-archive-persist", os.path.join(
        "ledger", "test_growth_archive_persist.py"), 7),
    # R1960 refund-recovery persist seat (R1886 family, R1955
    # reseed claim): wired instant-converged world across three
    # restarts - five-face snapshot byte-identity, deterministic
    # audit-key re-entry convergence (zero duplicates), fresh
    # wired refund on the restarted instance with named-face
    # zero-drift, pure-read law, second-restart stability.
    ("member-refund-recovery-persist", os.path.join(
        "member", "test_refund_recovery_persist.py"), 7),
    # R1962 reminder authorization + read-face family persist seat
    # (R1886 family, R1959 reseed claim): grant journal / budget
    # arithmetic / idempotency keys / W10 dual-timepoint faces /
    # due-scan re-entry across two full close-reopen restarts -
    # six-face snapshot byte-identity both faces, budget arithmetic
    # continues post-restart (once exhaustion + fresh grant
    # activation), daily-cap counting crosses restart then clears on
    # day roll, untouched-avatar zero-drift, pure-read law (reminder
    # module performs zero member.db writes), second-restart terminal
    # state byte-identical (AC-RMP1..RMP7 pre-registered in
    # state/queue/tech.md).
    ("member-reminder-persist", os.path.join(
        "member", "test_reminder_persist.py"), 7),
    # pay-reconcile-persist (R1963 claim, R1964 takeover closeout):
    # the CLI reconcile scanner re-derives its whole verdict from the
    # three on-disk databases, so closing every writer face and
    # reopening fresh instances on the same databases must reproduce
    # the CLI scan byte-for-byte; tamper probes (dangling revoke /
    # dead-account sent) fail with the same naming before and after
    # the restart; a post-restart grant recomputes the scan (zero
    # cache) while pre-restart rows stay frozen (notify tables
    # untouched); the scanner is pure-read (AC-PRC1..PRC7
    # pre-registered in state/queue/tech.md).
    ("pay-reconcile-persist", os.path.join(
        "pay", "test_pay_reconcile_persist.py"), 7),
    # pay-sweep-persist (R1965 claim): the timeout-close sweep is a
    # durability seam - closed-by-timeout orders, drained-window
    # idempotency, the closed-rebuy bucket law and the grant read
    # faces survive a close -> reopen on the same databases
    # byte-identically; a live sweep after the restart closes only
    # in-window rows while every pre-restart row stays frozen
    # (append-only prefix law); the read battery is pure and
    # double-run stable across two restarts (AC-SWP1..SWP7
    # pre-registered in state/queue/tech.md).
    ("pay-sweep-persist", os.path.join(
        "pay", "test_pay_sweep_persist.py"), 7),
    # lobby-persist (R1966 claim): the two lobby board read faces
    # already carry their close -> reopen persist example in-book
    # (R1891 at the store level, R1915 at the protocol level); this
    # suite pins the residual EventStore read faces - count(where),
    # census_lookup, export_day - plus the import_census whole-table
    # refresh semantics and the content-addressed append dedup gate,
    # byte-identical across a close -> reopen on the same database;
    # post-restart real-path appends re-derive the counts (zero
    # cache) while pre-restart rows and old-day exports stay frozen
    # (AC-LBP1..AC-LBP7 pre-registered in state/queue/tech.md).
    ("lobby-persist", os.path.join(
        "lobby", "test_lobby_persist.py"), 7),
    # R1977 civic behavior distribution read face: registry-driven
    # per-behavior aggregation over the earn ledger - every
    # registered behavior appears exactly once, zero-earn
    # behaviors keep honest zero rows (the registry is the
    # row-set authority; dormant behaviors stay visible); per-row
    # events / total_points / participants / last_day with the
    # registry echo (title, points_per_event, ai_label); pure
    # read (zero writes), deterministic order total_points DESC,
    # events DESC, behavior_id ASC; cross-source recount from
    # points_view streams; counts-vs-tokens isolation inherited
    # structurally (constructor takes no ledger reference)
    # (AC-CVD1..CVD6 pre-registered in state/queue/explore.md).
    ("civic-behavior-distribution",
     os.path.join("ledger", "test_civic_distribution.py"), 6),
    # R1983 showcase stats board: registry-keyed pure-read
    # per-showcase place/retract event count aggregation with the
    # derived displayed-now column; dense over the showcase
    # registry (zero-event window shows honest zeros, zero
    # registration shows an honest empty board); net-flow identity
    # displayed_now == places - retracts per row; decisive order
    # places DESC, retracts DESC, showcase_id ASC; pure read with
    # cross-face reconciliation against showcase_view
    # (AC-SSB1..AC-SSB7 pre-registered in state/queue/explore.md).
    ("ledger-showcase-stats",
     os.path.join("ledger", "test_showcase_stats.py"), 7),
    # R1984 explore-queue FIFO-head claim (R1982 reseed row): the
    # dataset-subscription coverage board across a two-piece restart
    # (face close + ledger close -> new stack over the same db
    # paths): anchor world with the same-account multi-window
    # household-dedup law and an honest zero-subscription row,
    # board byte identity across restart, post-restart live
    # continuation (new subscription/registration/delivery on the
    # board face), stable gate codes, append-only frozen row
    # prefixes with the bound spend-tx SQL cross, pure-read law,
    # third-instance sequential identity
    # (AC-COVP1..AC-COVP7 pre-registered in state/queue/explore.md).
    ("ledger-coverageboard-persist",
     os.path.join("ledger", "test_coverage_board_persist.py"), 7),
    # R1985 explore-queue FIFO-head claim (R1984 reseed row): the
    # dataset-subscription coverage board month-window read face
    # (R1826/R1888 window-parameterization family law): default
    # window=None full-window byte-identical zero drift, explicit
    # YYYY-MM window slices each row family by its own record-time
    # provenance stamp (subscriptions by subscribed_utc, deliveries
    # by delivered_utc - the period window never decides the board
    # month), honest dense zero rows inside a window, all-zero
    # honest-empty month, additive window envelope key, malformed
    # window fail-closed, cross-restart battery byte identity,
    # pure-read law, frozen-schema anchor
    # (AC-CVW1..AC-CVW7 pre-registered in state/queue/explore.md).
    ("ledger-coverageboard-window",
     os.path.join("ledger", "test_coverage_board_window.py"), 7),
    # R1987 explore-queue claim (stats_board R1983 seed sibling
    # gap): the per-showcase statistics board across a full-stack
    # restart (face close -> ledger close -> fresh ledger +
    # stateless gate + fresh face on the same db paths): pre-close
    # board bytes re-derived identically by the reopened face;
    # post-restart place/retract recompute zero-cache with
    # untouched rows frozen; cross-window re-place continuation
    # reconciles with showcase_view; third-instance dual-live
    # sequential identity; pure-read law; the board rows carry no
    # time-derived fields so no clock patch is needed
    # (AC-SSBP1..AC-SSBP7 pre-registered in state/queue/explore.md).
    ("ledger-statsboard-persist",
     os.path.join("ledger", "test_stats_board_persist.py"), 7),
    # R1988 explore-queue claim (stats_board cap-window tail read):
    # limit=0 default keeps the two-key envelope byte-identical;
    # a positive limit is a decisive-order tail slice with an
    # honest overflow block (total carries the full registry
    # count, never the truncated one); the limit gate fires
    # before any read
    # (AC-SST1..AC-SST7 pre-registered in state/queue/explore.md).
    ("ledger-showcase-statslimit",
     os.path.join("ledger", "test_showcase_statslimit.py"), 7),
    # R1989 stats_board dual-window combined board: default
    # full-window + explicit capped-window side by side in one
    # envelope (single derivation source; R1974 single-envelope
    # law applied to the R1988 cap-window family)
    # (AC-SSD1..AC-SSD7 pre-registered in state/queue/explore.md).
    ("ledger-showcase-statsdual",
     os.path.join("ledger", "test_showcase_statsdual.py"), 7),
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
    # single-dialect child pipes: every child is forced to EMIT utf-8
    # (PYTHONIOENCODING injected over a copy of the ambient env, so
    # whatever the calling shell set is overridden) and the runner
    # DECODES the pipe as utf-8 explicitly - the machine locale never
    # participates. Locale-dependent decode is how mixed-dialect
    # evidence bytes were born (R1791/R1792 raw cp936 in the files,
    # R1824/R1825 child-utf-8-bytes-decoded-as-cp936 mojibake).
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True,
                           encoding="utf-8", errors="replace", cwd=cwd,
                           timeout=300, env=env)
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
    # R1746 notify leg (public API only): one grant-then-revoke pair -
    # shipped config stays byte-identical (default template registry
    # approved=0 = honest pending state: grants/revoke faces exercise,
    # the send face stays zero-row); the same-second grant lands dead
    # per R1740 ruling 2, so the demo pair is a dead account the
    # revoke checks verify against.
    import notify as N                                  # pay product
    nface = N.PayNotifyFace(cfg, os.path.join(tmp, "pay_notify.db"),
                            pay_db=os.path.join(tmp, "pay.db"))
    nface.grant_authorization("AV-PAY-DEMO-1",
                              "tpl_pay_success_pending_ceo", "once")
    nface.revoke_authorization("AV-PAY-DEMO-1",
                               "tpl_pay_success_pending_ceo")
    nface.close()
    return {"pay_db": os.path.join(tmp, "pay.db"),
            "ledger_db": os.path.join(tmp, "pay-ledger.db"),
            "notify_db": os.path.join(tmp, "pay_notify.db"),
            "config": os.path.join(PAY, "config.json"),
            "tamper_order": oid_pack}


def phase_pay_reconcile(tmp):
    world = build_pay_demo_state(tmp)
    code, out = run_cmd([sys.executable, os.path.join(PAY, "reconcile.py"),
                         world["pay_db"], world["config"], world["ledger_db"],
                         world["notify_db"]], cwd=PAY)
    echo(out)
    note(code == 0 and "reconcile: PASS checks=8/8" in out,
         "reconcile pay-demo exit=%d (expect 0, clean eight checks)" % code)
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
                           tampered, world["config"], world["ledger_db"],
                           world["notify_db"]], cwd=PAY)
    echo(out2)
    note(code2 == 2 and "reconcile: FAIL" in out2,
         "reconcile pay-tamper exit=%d (expect 2, FAIL detected)" % code2)
    # R1746 revokes tamper leg: clean pay db + tampered notify copy with
    # both postures injected - a dangling revoke (pair with zero grant
    # history) and a dead-account sent row (post-cutoff 'sent' on the
    # demo's dead pair) - both revoke checks must FAIL and be named.
    tampered_notify = os.path.join(tmp, "pay-notify-tampered.db")
    shutil.copyfile(world["notify_db"], tampered_notify)
    nconn = sqlite3.connect(tampered_notify)
    nconn.execute(
        "INSERT INTO pay_notify_revokes (revoke_id, census_avatar_id,"
        " template_id, ts_utc) VALUES ('rv-dangling-demo',"
        " 'AV-NO-GRANT-DEMO', 'tpl_pay_success_pending_ceo',"
        " '2026-10-10T00:00:00Z')")
    nconn.execute(
        "INSERT INTO pay_notify_log (send_id, census_avatar_id, order_id,"
        " template_id, reason, status, ts_utc) VALUES ('sn-dead-demo',"
        " 'AV-PAY-DEMO-1', 'ORD-DEMO', 'tpl_pay_success_pending_ceo',"
        " 'payment_success', 'sent', '2999-01-01T00:00:00Z')")
    nconn.commit()
    nconn.close()
    code3, out3 = run_cmd([sys.executable, os.path.join(PAY, "reconcile.py"),
                           world["pay_db"], world["config"],
                           world["ledger_db"], tampered_notify], cwd=PAY)
    echo(out3)
    note(code3 == 2 and "revoke_ref" in out3 and "revoke_dead" in out3
         and "[FAIL] revoke_ref" in out3 and "[FAIL] revoke_dead" in out3,
         "reconcile pay-tamper-revokes exit=%d (expect 2, revoke FAILs"
         " detected and named)" % code3)


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


SHELL_CAPTURE_LABEL = ("no evidence path: shell-capture mode, "
                       "evidence dialect follows the caller")


def main(argv):
    # pin the runner's own console/redirect stream to utf-8 as well,
    # so a no-argv shell-captured run (the R1791/R1792/R1824/R1825
    # evidence writer mode) lands single-dialect too; the Tee mirror
    # holds this reconfigured stream. Cosmetic-only on a real console.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    if len(argv) < 2:
        # R1836 AC-SL1 (pre-registered in state/queue/tech.md before
        # this code): with no evidence path the output goes to whoever
        # captures us - say so as the very first line so a captured
        # evidence file is mechanically identifiable as shell-capture
        # mode (writer-census / R1827 archaeology faces). Printed
        # before phase_suites, so the label is structurally first.
        print(SHELL_CAPTURE_LABEL, flush=True)
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
        print("RUNNER PASS (%d/%d suites green, reconcile controls 7/7, %.1fs)"
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
