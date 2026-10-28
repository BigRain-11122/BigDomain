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
    # R2012 idem_seen TTL/FIFO boundary window: the TTL window is
    # fixed at first processing (an absorbed replay never slides
    # it), a post-expiry resend re-arms the cache with the NEW
    # evt_id, windows stagger per-key independently, len==cap is
    # the no-eviction boundary and the cap+1-th distinct key evicts
    # the FIFO oldest (evicted-while-live re-entry) - AC-IDT1..IDT8
    # (57 -> 65).
    # R2014 (criteria pre-registered R2013) idem gate-order budget
    # window: the idempotency gate sits BEFORE the rate limit
    # (server.py "replay costs no budget"), so replays of processed
    # sends absorb as duplicates without burning, freeing or
    # extending rate budget while the 5/10s window stays saturated
    # - fresh-storm + 10-replay storm + 6th-fresh rejection + no-id
    # control anchor, all on shipped config values - AC-IDB1..IDB7
    # (65 -> 72).
    # R2042 idem_seen expired-resend billing window: a TTL-expired
    # resend of the same (id,text) is billed as a fresh unit - at
    # saturation it answers E_RATE_LIMIT instead of absorbing as a
    # duplicate, a rejected expired resend does not re-arm the
    # cache, and on a clean window it really consumes a budget slot
    # (5th-fresh exhaustion proof + re-armed free replay after the
    # billed resend; behavioral-proof method, violations below the
    # mute trigger) - AC-IDR1..IDR7 (72 -> 79).
    ("lobby", os.path.join("lobby", "test_client.py"), 79),
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
    # R1996 curation combined hot+cold dual board MONTH-WINDOW
    # scoped read face (R1976-reseeded explore-queue row claimed
    # by R1996): an optional explicit strict YYYY-MM window
    # re-scopes the single hot_board(window) call through the
    # NEW ShowcaseFace public read face showcase_view_window
    # (reference, not copy, zero second aggregation engine);
    # window heat counts only items whose latest window-recorded
    # event is a place (the record-time law - a september
    # placement with zero october records stays off the october
    # window while remaining on the live board; an october
    # placement retracted in november is displayed in october
    # and not in november); registry stays the dense axis (every
    # registered curation boards; out-of-range month = honest
    # empty hot zone + all-cold shelf); registration month never
    # decides the board month (november-registered theme boards
    # in the october window); window gate fires before any read
    # with the dedicated E_CU_BAD_WINDOW / E_SH_BAD_WINDOW
    # family codes over 13 malformed forms; default None form
    # byte-for-byte the R1974/R1753 contracts (only an explicit
    # window adds the envelope window key); double-read
    # determinism + full-stack close/reopen byte identity;
    # pure-read law + hygiene machine-checked
    # (AC-CJM1..CJM7 pre-registered in state/queue/explore.md).
    ("ledger-curation-combinedmonth",
     os.path.join("ledger", "test_curation_combinedmonth.py"), 7),
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
    # R2006 developer sales board persist seat of the R1886
    # family: full-stack am->dk->metered->led close + same
    # db/cfg rebuild, board byte-identical across two
    # restarts, post-restart purchase / new-listing zero-cache
    # continuation, gate family identical codes with zero
    # side effects, pure-read law + product sha double-proof
    # (AC-AMBP1..AMBP7 pre-registered in the R2006
    # explore-queue claim row).
    ("ledger-apimarket-devsalespersist", os.path.join(
        "ledger", "test_apimarket_devsalespersist.py"), 7),
    # R2022 developer sales board month-window read seat of the
    # windowed-read family: additive window param with default
    # zero drift, strict YYYY-MM gate before any read (dedicated
    # E_AM_BAD_WINDOW), record-time dual-family slicing
    # (listing_count by listed_utc prefix, purchase aggregates
    # by purchased_utc prefix), dense ever-listed zero rows in
    # out months, honest [] on a zero-listing market, pure
    # additivity full == SEP + OCT, pure-read law
    # (AC-AMW1..AMW7 pre-registered in the R2022
    # explore-queue claim row).
    ("ledger-apimarket-devboardwindow", os.path.join(
        "ledger", "test_apimarket_devboardwindow.py"), 7),
    # apimarket dev_sales_board month-window cross-restart
    # persist window (R2023): pre-close pinning of the default /
    # SEP / OCT window boards + record-time separation probe,
    # full-stack restart byte-identical reads, post-restart NOV
    # continuation with frozen SEP / OCT boards and zero-cache
    # NOV / default recompute, bad-window gate family identical
    # codes on all three instances, append-only frozen row
    # prefixes + per-purchase ledger tx provenance, third
    # instance stability (AC-AMWP1..AMWP7 pre-registered in
    # the R2023 explore-queue claim row).
    ("ledger-apimarket-devboardmonthpersist", os.path.join(
        "ledger", "test_apimarket_devboardmonthpersist.py"), 7),
    # apimarket dev_sales_board zero-listing boundary world
    # cross-restart persist window (R2024): boundary isolates
    # the listing axis only (ledger + devkeys populated,
    # apimarket three tables zero rows), honest empty envelope
    # pinned, write-side gate family (off-register publish,
    # content gate hit, zero price, unknown listing purchase)
    # rejects before any read with zero side effects on the
    # empty data face, full-stack restart byte-identical empty
    # board, post-restart first listing honest-zero dense join
    # with zero phantoms, first purchase zero-cache recompute
    # with per-purchase spend/share tx provenance into the
    # ledger_tx id set, third instance stability
    # (AC-AMZB1..AMZB7 pre-registered in the R2024
    # explore-queue claim row).
    ("ledger-apimarket-devboardboundary", os.path.join(
        "ledger", "test_apimarket_devboardboundarypersist.py"), 7),
    # apimarket dev_sales_board zero-listing boundary GATE family
    # across restart instances (R2065 explore-queue claim row).
    ("ledger-apimarket-devboardgatepersist", os.path.join(
        "ledger", "test_apimarket_devboardgatepersist.py"), 8),
    # apimarket dev_sales_board month-window zero-listing
    # boundary cross-restart persist window (R2045): the
    # zero-listing boundary world (R2024 posture - listing
    # axis empty, ledger + devkeys populated) pinned on the
    # month-window read family (default + SEP / OCT / NOV /
    # 2099-01 honest empty envelopes with echo keys), the
    # fourteen bad-window gate family rejecting before any
    # read on the empty data face, full-stack restart
    # byte-identical, post-restart first listing dense
    # window-face join (record month carries listing_count,
    # every other month keeps the honest dense zero row),
    # first purchase NOV-window zero-cache recompute with the
    # OCT listing family byte-frozen (record-time dual-family
    # law) and spend/share tx provenance, third instance
    # stability with identical gate codes
    # (AC-AMWZB1..AMWZB7 pre-registered in the R2045
    # explore-queue claim row).
    ("ledger-apimarket-devboardmonthboundary", os.path.join(
        "ledger", "test_apimarket_devboardmonthboundarypersist.py"), 7),
    # apimarket dev_sales_board three-month purchase straddle
    # cross-restart persist window (R2073): the loaded world
    # (OCT listing + NOV first purchase grown by a DEC third
    # month on both an OCT listing and a NOV listing) pinned on
    # the exact boundary-second law (month-end 23:59:59Z and
    # next-month 00:00:00Z land on opposite sides, each counted
    # exactly once), three-window zero-permeation (earlier
    # window snapshots stay byte-frozen while later months
    # accumulate), the DEC window showing purchase aggregates on
    # zero listing_count rows, three-month conservation
    # (OCT + NOV + DEC == lifetime, per developer and total,
    # purchase ids partitioned), the dense ever-listed row set
    # on every window, three-instance restart stability and the
    # fourteen-form bad-window gate family on the loaded world
    # (AC-AMSTR1..AMSTR7 pre-registered in the R2073
    # explore-queue claim row).
    ("ledger-apimarket-devboardmonthstraddle", os.path.join(
        "ledger", "test_apimarket_devboardmonth_straddlepersist.py"), 7),
    # apimarket rating aggregate precision and gate-order window
    # (R2077): the AC-AM5 single-rating seat grown into the
    # aggregate surface - count/float-average/rater-order pinned
    # across api_view, api_board and api_ratings; purchaser-only
    # plus append-only immutability (repeat rejected, first value
    # preserved); the bad-args gate family and its order (account
    # gate before star gate, star gate before the listing lookup
    # so an unknown listing with bad stars answers BAD_STARS);
    # aggregate arithmetic exactness (4 raters 3.75, 7 raters
    # 30/7 by float repr, single rater float(stars), zero-rater
    # listing 0.0/0); cross-listing zero permeation; cross-restart
    # byte identity of the five read faces; the pure-read law and
    # zero token movement (the rating face never touches the
    # ledger) (AC-AMRT1..AC-AMRT8 pre-registered in the R2077
    # explore-queue claim row).
    ("ledger-apimarket-ratingagg", os.path.join(
        "ledger", "test_apimarket_ratingagg.py"), 8),
    # R2078 explore-queue self-seeded and self-claimed row: the
    # apimarket listing retirement (delist) door the face never had
    # - one append-only delisting row per listing with a seven-key
    # envelope; the ownership gate; the repeat-delist refusal that
    # never rewrites the first stamp; the bad-args gate family and
    # its order (account shape, then listing shape/existence, then
    # ownership - an unknown listing probed by a non-owner answers
    # UNKNOWN_LISTING); purchase fail-closed on a retired listing
    # with the delist gate preceding the self-buy gate while a live
    # listing stays purchasable; the read-face semantics (additive
    # delisted pair with every historical aggregate unchanged, the
    # board excluding retired rows, ratings/sales history still
    # answering, developer board keeping listing-side row
    # authority); two full-stack restarts; zero token movement from
    # the retirement batch (only the live purchase's spend+share
    # pair lands); hygiene, criteria count
    # (AC-AMD1..AC-AMD8 pre-registered in the R2078 explore-queue
    # claim row).
    ("ledger-apimarket-delist", os.path.join(
        "ledger", "test_apimarket_delist.py"), 8),
    # R2079 explore-queue self-seeded and self-claimed row: the
    # apimarket listing price-revision (repricing) door - one
    # append-only revision row per call with a nine-key envelope,
    # the base price preserved and the newest revision live; the
    # pinned gate order (account shape, listing shape/existence,
    # ownership, retired state, price shape, unchanged state); the
    # same-price refusal with zero rows while a revise-back is
    # legal; purchase charged at the current price with the integer
    # split law intact and older purchase rows keeping their
    # price_paid; retirement interaction (repricing refused,
    # history readable, board exclusion unchanged); the
    # api_price_history read face, the api_view additive pair and
    # per-listing isolation; cross-restart byte identity and zero
    # token movement across the revision batch; hygiene, criteria
    # count (AC-AMPR1..AC-AMPR8 pre-registered in the R2079
    # explore-queue claim row).
    ("ledger-apimarket-pricerev", os.path.join(
        "ledger", "test_apimarket_pricerev.py"), 8),
    # R2081 explore-queue self-seeded and self-claimed row: the
    # buyer-side purchase library face (api_library) the market
    # never had - one five-key envelope with fourteen-key rows,
    # purchase_count/total_spent derived from the rows, strict
    # buyer isolation (developer account carries no self-purchase
    # rows, prefix-valid account with no purchases gets an honest
    # empty library), retired listings staying readable with their
    # delist stamp, price_paid vs current_price separation, the
    # buyer's own my_rating only, the account gate fail-closed
    # before any read, the pure-read law (zero row mutations, zero
    # token movement) and cross-restart byte identity; criteria
    # count (AC-AML1..AC-AML8 pre-registered in the R2081
    # explore-queue claim row).
    ("ledger-apimarket-buyerlibrary", os.path.join(
        "ledger", "test_apimarket_library.py"), 8),
    # R2082 market discovery seat: the keyword axis (title OR
    # listing_key only, case-insensitive), the seller axis, the
    # price band applied to the current asking price, the
    # retirement switch, the pinned gate family and gate order,
    # the ordering law (price ASC then listing_id), the pure-read
    # law and cross-restart byte identity (AC-AMSQ1..AMSQ8
    # pre-registered in the R2082 explore-queue claim row).
    ("ledger-apimarket-search", os.path.join(
        "ledger", "test_apimarket_search.py"), 8),
    # R2084 discovery paging seat: the optional limit/offset axis on
    # api_search with the backward-compatibility law (no paging
    # parameters => the R2082 envelope byte-identical), page
    # stitching conservation, the boundary tie-break, bound
    # clamping (limit == total, limit > total, offset at/past the
    # end, tail crossing), the fail-closed limit/offset gate family
    # and its order after the account and price-band gates, totals
    # derived from the filtered set, the pure-read law and
    # cross-restart byte identity (AC-AMPG1..AC-AMPG8
    # pre-registered in the R2084 explore-queue claim row).
    ("ledger-apimarket-searchpaging", os.path.join(
        "ledger", "test_apimarket_searchpage.py"), 8),
    # R2098 discovery sort seat: api_search gained the five-token
    # order axis (price_desc / rating / sales / newest plus the
    # price_asc alias) on top of the R2082 discovery door and the
    # R2084 paging axis, with the legacy contract byte-identical
    # (AC-AMSR1..AC-AMSR8 pre-registered in the R2098 claim row).
    ("ledger-apimarket-searchsort", os.path.join(
        "ledger", "test_apimarket_searchsort.py"), 8),
    # R2142 discovery availability seat: api_search gained the
    # bool-only in_stock axis (buyable rows / sold-out rows) read
    # through the one scarcity seam, with the legacy contract
    # byte-identical when unfiltered, the pinned gate order and
    # partition law against api_supply (AC-AMAV1..AC-AMAV8
    # pre-registered in the R2142 explore-queue claim row).
    ("ledger-apimarket-searchstock", os.path.join(
        "ledger", "test_apimarket_searchstock.py"), 8),
    # R2143 seller reply-revision seat: revise_reply +
    # api_reply_history + apimarket_reply_revisions, the last
    # write-once axis on the trust face to gain a remedy door
    # (AC-AMRY1..AC-AMRY8 pre-registered in the R2143
    # explore-queue claim row BEFORE this suite existed).
    ("ledger-apimarket-replyrev", os.path.join(
        "ledger", "test_apimarket_replyrev.py"), 8),
    # R2144 competitive-position seat: api_listing_position, the
    # seller's standing inside its own category bucket on the three
    # buyer axes (asking price, net sales, effective rating), with
    # the bucket slice returned so the rank is auditable
    # (AC-AMPOS1..AC-AMPOS8 pre-registered in the R2144
    # explore-queue claim row BEFORE this suite existed).
    ("ledger-apimarket-listingposition", os.path.join(
        "ledger", "test_apimarket_listingposition.py"), 8),
    # R2148 nearest-neighbour seat: api_similar_listings, the
    # discovery door that answers "what else is like this one"
    # without making the caller restate its category and price band,
    # ordered by a pinned total order on price distance so the
    # neighbour set is auditable (AC-AMSI1..AC-AMSI8 pre-registered
    # in the R2148 explore-queue claim row BEFORE this suite existed).
    ("ledger-apimarket-similar", os.path.join(
        "ledger", "test_apimarket_similar.py"), 8),
    # R2085 seller-profile seat: the public dev_profile read face
    # with the thirteen-key envelope and nine-key rows, the
    # partition law (listing_count == live + retired, sales and
    # gross derived from rows, integer split closing exactly), the
    # retired-listing-stays rule with unrewritten history, the
    # cross-listing rating aggregate pinned at 3.75 and 30/7 with
    # per-listing agreement against api_ratings, seller isolation
    # plus the honest empty profile, the fail-closed account gate
    # family, the pure-read law with cross-face agreement against
    # dev_sales_board and api_view, and cross-restart byte identity
    # (AC-AMDP1..AC-AMDP8 pre-registered in the R2085
    # explore-queue claim row).
    ("ledger-apimarket-devprofile", os.path.join(
        "ledger", "test_apimarket_devprofile.py"), 8),
    # R2083 listing metadata revision seat: the append-only
    # apimarket_listing_revisions row with the listing row's base
    # metadata never rewritten, partial-edit semantics, the pinned
    # gate order (account, listing, ownership, retired, field
    # shape, content pre-gate, no-change), ownership/existence
    # refusals, retired-listing refusal with readable history, the
    # no-change refusal with the legal revise-back, effective
    # metadata on api_view/api_board/api_search plus the new
    # api_metadata_history read face, zero token movement and
    # cross-restart byte identity (AC-AMME1..AC-AMME8
    # pre-registered in the R2083 explore-queue claim row).
    ("ledger-apimarket-metadata", os.path.join(
        "ledger", "test_apimarket_metadata.py"), 8),
    # R2086 buyer-side watchlist seat: the pre-purchase intent face
    # (watch_api / unwatch_api / api_watchlist) with two append-only
    # tables, the pinned gate order (account, listing, retired,
    # duplicate), retired-new refusal while watched-before-retire
    # stays visible, unwatch-then-rewatch keeping both historical
    # rows while the live set holds exactly one, the first unwatch
    # stamp never rewritten, buyer isolation and honest empty
    # envelopes, zero token movement with frozen digests, and
    # cross-restart byte identity (AC-AMWL1..AC-AMWL8
    # pre-registered in the R2086 explore-queue claim row).
    ("ledger-apimarket-watchlist", os.path.join(
        "ledger", "test_apimarket_watchlist.py"), 8),
    # R2087 supply axis: the scarcity face nobody had (publish
    # gains an optional supply, purchase gains the exhaustion gate
    # after the buyer-specific gates and before any ledger
    # movement, api_supply reads supply/sold/remaining/sold_out
    # derived from the immutable purchase rows), plus the
    # idempotent pre-supply-database migration (AC-AMSP1..AMSP8
    # pre-registered in the R2087 explore-queue claim row).
    ("ledger-apimarket-supply", os.path.join(
        "ledger", "test_apimarket_supply.py"), 8),
    # R2088 refund / return axis: the buyer-side remedy door that
    # the irreversible purchase face never had (append-only refund
    # rows keyed on the purchase id, the four-entry ledger reversal
    # restoring buyer/seller/both pools exactly, the pinned gate
    # order, the no-overdraft funding gate, the refunded unit
    # returning to the shelf, additive refund columns on
    # api_view/api_library/api_sales and the api_refund provenance
    # face) - AC-AMRF1..AMRF8 pre-registered in the R2088
    # explore-queue claim row.
    ("ledger-apimarket-refund", os.path.join(
        "ledger", "test_apimarket_refund.py"), 8),
    # apimarket listing re-listing (relist) door - the missing
    # return leg of the delist face, plus the api_listing_lifecycle
    # read face - AC-AMRL1..AMRL8 pre-registered in the R2089
    # explore-queue claim row.
    ("ledger-apimarket-relist", os.path.join(
        "ledger", "test_apimarket_relist.py"), 8),
    ("ledger-apimarket-marketstats", os.path.join(
        "ledger", "test_apimarket_marketstats.py"), 8),
    # apimarket per-category demand - the demand counterpart of the
    # api_categories supply directory, with the same partition and
    # trade conservation laws as api_market_stats - criteria
    # AC-AMCD1..AC-AMCD8 pre-registered in the R2141 explore-queue
    # claim row BEFORE this suite existed.
    ("ledger-apimarket-categorydemand", os.path.join(
        "ledger", "test_apimarket_categorydemand.py"), 8),
    # apimarket buyer-side spend broken down by category - the
    # resident mirror of api_category_demand, purchase-side row
    # authority, effective-category seam and cash totals identical to
    # api_buyer_months - criteria AC-BCS1..AC-BCS8 pre-registered in
    # the R2149 explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-buyercategoryspend", os.path.join(
        "ledger", "test_apimarket_buyercategoryspend.py"), 8),
    # apimarket buyer-side spend broken down by seller - the seller
    # composition axis of the resident spend picture, purchase-side row
    # authority with a total order whose rank is a position, and cash
    # totals identical to api_buyer_category_spend - criteria
    # AC-BSS1..AC-BSS8 pre-registered in the R2158 explore-queue claim
    # row BEFORE this suite existed.
    ("ledger-apimarket-buyersellerspend", os.path.join(
        "ledger", "test_apimarket_buyersellerspend.py"), 8),
    # apimarket repeat-purchase structure - the retention axis the row
    # faces, the buyer profile, the seller profile and the category
    # demand face all stopped short of; net-purchase counting authority
    # so a refunded purchase never fakes a one-time buyer, seller and
    # market scopes with the honest difference between them, and
    # purchase-side category rows on the effective-bucket seam -
    # criteria AC-RPT1..AC-RPT8 pre-registered in the R2161
    # explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-repeatpurchase", os.path.join(
        "ledger", "test_apimarket_repeatpurchase.py"), 8),
    # apimarket watch-to-purchase conversion funnel - the conversion
    # rate, the conversion latency and the DIRECTIONAL law (a purchase
    # stamped before the watch can never convert) that the listing
    # demand counters never answered, watch-side category rows with the
    # pooled (non-additive) rate and average - criteria AC-WCV1..AC-WCV8
    # pre-registered in the R2162 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-watchconversion", os.path.join(
        "ledger", "test_apimarket_watchconversion.py"), 8),
    # apimarket category refund months - the per-category per-month
    # buyer star-giving tendency - the five-bucket distribution, the
    # harsh/neutral/generous split, the effective-stars seam with its
    # revision counters and the market-relative tendency_delta that the
    # buyer profile count and average never answered - criteria
    # AC-BRP1..AC-BRP8 pre-registered in the R2164 explore-queue claim
    # row BEFORE this suite existed.
    ("ledger-apimarket-buyerratingpattern", os.path.join(
        "ledger", "test_apimarket_buyerratingpattern.py"), 8),
    # apimarket market activity heatmap - the always-complete 24-hour /
    # 7-weekday / 168-cell grid over the cash-basis trade pair, with
    # participant authority per bucket, the peak law (count, then gross,
    # then the lower index) and refund-only buckets that never become a
    # peak - criteria AC-MHH1..AC-MHH8 pre-registered in the R2165
    # explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-hourheatmap", os.path.join(
        "ledger", "test_apimarket_hourheatmap.py"), 8),
    # the buyer refund-propensity face - the refund count and amount
    # normalised by the resident own purchase base (every purchase
    # counts, refunds are one per purchase), the market count-rate
    # benchmark with its honest None edges, and the low-sample
    # shrinkage whose deviation is scaled by exactly n/(n+K) so a
    # one-purchase history cannot read as more dangerous than a long
    # one - criteria AC-RFP1..AC-RFP8 pre-registered in the R2166
    # explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-refundpropensity", os.path.join(
        "ledger", "test_apimarket_buyerrefundpropensity.py"), 8),
    # apimarket shelf-to-sale velocity - the time from the cycle
    # opening (the latest re-listing at or before the sale, else the
    # published stamp) to the first NET sale, with an honestly unsold
    # shelf that never drags the mean to zero, the pooled average and
    # median, the fastest / slowest extremes and the MARKET-scoped
    # category benchmark that stays comparable under a seller scope -
    # criteria AC-LV1..AC-LV8 pre-registered in the R2169 explore-queue
    # claim row BEFORE this suite existed.
    ("ledger-apimarket-listingvelocity", os.path.join(
        "ledger", "test_apimarket_listingvelocity.py"), 8),
    # apimarket monthly seller cohort - one listing event per
    # listing row and one re-listing event per re-listing row, the
    # cohort law (new exactly once, earliest month across the whole
    # history), the repeat-seller law and the honest empty -
    # criteria AC-MSC1..AC-MSC8 pre-registered in the R2181
    # explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-sellercohort", os.path.join(
        "ledger", "test_apimarket_sellercohort.py"), 8),
    # apimarket retirement to re-listing gap - each closed retirement
    # cycle paired with the return that opens the next one, a running
    # gap reported without a duration, and the pooled durations - 
    # criteria AC-ARG1..AC-ARG8 pre-registered in the R2180
    # explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-relistgap", os.path.join(
        "ledger", "test_apimarket_relistgap.py"), 8),
    # apimarket seller-side buyer concentration - the purchase-side
    # roll with the refund law (a fully refunded buyer stays at zero
    # weight), the share / herfindahl / pareto laws on integers, the
    # market-wide benchmark carried under a seller scope and strict
    # seller isolation - criteria AC-SBC1..AC-SBC8 pre-registered in
    # the R2170 explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-concentration", os.path.join(
        "ledger", "test_apimarket_concentration.py"), 8),
    # buyer-side spend concentration (two independent axes - one bucket
    # per seller and one per effective category - with the shared
    # total-order / share / herfindahl / pareto law, purchase-side row
    # authority, net spend authority keeping a fully refunded seller at
    # zero weight, cross-face identity with api_buyer_seller_spend and
    # strict buyer isolation) - criteria AC-BC1..AC-BC8 pre-registered
    # in the R2178 explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-buyerconcentration", os.path.join(
        "ledger", "test_apimarket_buyerconcentration.py"), 8),
    # seller repricing discipline (step percentages derived only from
    # two stored prices, repricing-side row authority, pooled mean /
    # median / absolute peak / signed sum, market benchmark under a
    # seller scope) - criteria AC-PVC1..AC-PVC8 pre-registered in the
    # R2171 explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-pricevolatility", os.path.join(
        "ledger", "test_apimarket_pricevolatility.py"), 8),
    ("ledger-apimarket-buyercohort", os.path.join(
        "ledger", "test_apimarket_buyercohort.py"), 8),
    # monthly buyer retention matrix (net-purchase cohort origin, a
    # contiguous cell grid from the cohort month to the last active
    # month, exact and cumulative retention, refund recomputation) -
    # criteria AC-BRT1..AC-BRT8 pre-registered in the R2175
    # explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-buyerretention", os.path.join(
        "ledger", "test_apimarket_buyerretention.py"), 8),
    # per-category monthly asking-price trend (point-in-time rebuild at
    # every UTC month end from the append-only price, category, delist
    # and relist history, contiguous window with honest zero months,
    # median change series) - criteria AC-CPM1..AC-CPM8 pre-registered
    # in the R2176 explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-categorypricemonths", os.path.join(
        "ledger", "test_apimarket_categorypricemonths.py"), 8),
    # per-category monthly SUPPLY trend (point-in-time rebuild at every
    # UTC month end from publish stamps, restocks, purchases, refunds,
    # delistings, re-listings and category revisions: in-stock /
    # sold-out / unlimited split, units still buyable, contiguous
    # window with honest zero months) - criteria AC-CSM1..AC-CSM8
    # pre-registered in the R2182 explore-queue claim row BEFORE this
    # suite existed.
    # apimarket per-category monthly sell-through velocity - each NET
    # sale bucketed by its own purchased_utc month, a contiguous window
    # over SALE months (zero months are honest rows), the cycle-opening
    # duration law and the sale-instant category seam - criteria
    # AC-CVMT1..AC-CVMT8 pre-registered in the R2186 explore-queue row
    # BEFORE this suite existed.
    ("ledger-apimarket-categoryvelocitymonths", os.path.join(
        "ledger", "test_apimarket_categoryvelocitymonths.py"), 8),
    # seller-side supply rollup - every listing the seller owns
    # rolled into live/retired partitions, tracked vs unlimited
    # shelves, sold-out and low-stock counts and four derived
    # totals, all riding the single _supply_full seam - criteria
    # AC-SSUP1..AC-SSUP8 pre-registered in the R2178 10/10
    # explore-queue row BEFORE this suite existed.
    ("ledger-apimarket-sellersupply", os.path.join(
        "ledger", "test_apimarket_sellersupply.py"), 8),
    ("ledger-apimarket-categorysupplymonths", os.path.join(
        "ledger", "test_apimarket_categorysupplymonths.py"), 8),
    # calendar-day trade timeline (cash-basis day bucketing, a
    # contiguous grid with honest zero days, inclusive start_day /
    # end_day clipping, an honest empty window, extremes over active
    # days only) that the month face, the hour-of-day heatmap and the
    # event feed never answered - criteria AC-MDL1..AC-MDL8
    # pre-registered in the R2178 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-marketdaily", os.path.join(
        "ledger", "test_apimarket_marketdaily.py"), 8),
    # refund latency distribution (stamp-only durations from the sale
    # to the money coming back, a left-closed right-open six-band
    # partition, five aggregates over refunded rows only, same-date and
    # one-week crossings, a contiguous monthly leg with honest zero
    # months) that the refund propensity, register, exposure and
    # category-month faces never answered - criteria AC-RFLT1..AC-RFLT8
    # pre-registered in the R2179 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-refundlatency", os.path.join(
        "ledger", "test_apimarket_refundlatency.py"), 8),
    # refund reason distribution (a strip+lower bucket key that folds
    # case and whitespace yet never merges different spellings, an
    # honest unlabeled bucket ordered last and excluded from the leading
    # cause, row/envelope/split conservation, a total order and
    # one-step freshness) that the refund register, refund door and
    # market stats faces never answered - criteria AC-RFR1..AC-RFR8
    # pre-registered in the R2187 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-refundreasons", os.path.join(
        "ledger", "test_apimarket_refundreasons.py"), 8),
    # refund load (cash-basis bucketing, a refund-only month carrying
    # zero trade, honest None rates wherever nothing settled, the two
    # dissociated extremes) that the category demand, market months and
    # refund register faces never answered - criteria AC-CRM1..AC-CRM8
    # pre-registered in the R2163 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-categoryrefundmonths", os.path.join(
        "ledger", "test_apimarket_categoryrefundmonths.py"), 8),
    # apimarket asking-price distribution - the quartiles, median,
    # ninetieth percentile and spread that the catalog band, the
    # single listing position and the market average never answered;
    # live scope by default, one row per effective category bucket,
    # the linear-interpolation quantile law and an asking-price (not
    # turnover) face - criteria AC-MPP1..AC-MPP8 pre-registered in
    # the R2160 explore-queue claim row BEFORE this suite existed.
    ("ledger-apimarket-pricepercentiles", os.path.join(
        "ledger", "test_apimarket_pricepercentiles.py"), 8),
    # apimarket achieved ticket-size distribution - what a sale actually
    # costs, net-refund authority by default, cross-face identity with
    # the market stats on both axes - criteria AC-MTS1..AC-MTS8
    # pre-registered in the R2184 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-ticketsize", os.path.join(
        "ledger", "test_apimarket_ticketsize.py"), 8),
    # apimarket claim response latency scorecard - every claim leg as a
    # duration measured from the claim's own opened stamp, never a wall
    # clock, with the seller aggregates - criteria AC-CLT1..AC-CLT8
    # pre-registered in the R2159 explore-queue claim row BEFORE this
    # suite existed.
    ("ledger-apimarket-claimlatency", os.path.join(
        "ledger", "test_apimarket_claimlatency.py"), 8),
    # apimarket buyer account profile - the aggregate counterpart of
    # dev_profile (sellers) and api_market_stats (whole market), with
    # aggregates only so the row face stays api_library - criteria
    # AC-AMBY1..AC-AMBY8 pre-registered in the R2091 explore-queue
    # claim row BEFORE this suite existed.
    ("ledger-apimarket-buyerprofile", os.path.join(
        "ledger", "test_apimarket_buyerprofile.py"), 8),
    # apimarket seller rating-reply door - the missing response leg
    # of the two-arrow trust surface (one immutable reply per rating,
    # ownership gate, retired listing stays answerable) - criteria
    # AC-AMRP1..AC-AMRP8 pre-registered in the R2093 explore-queue
    # claim row BEFORE this suite existed.
    ("ledger-apimarket-ratreply", os.path.join(
        "ledger", "test_apimarket_ratingreply.py"), 8),
    # AC-AMRV1..AC-AMRV8 pre-registered in the R2094 explore-queue
    # claim row BEFORE this suite existed: buyer rating revision
    # door + rating history face + one effective-value seam.
    ("ledger-apimarket-ratingrev", os.path.join(
        "ledger", "test_apimarket_ratingrev.py"), 8),
    # AC-AMRS1..AC-AMRS8 pre-registered in the R2095 explore-queue
    # claim row BEFORE this suite existed: seller supply-replenishment
    # door (append-only restock rows, effective supply = base + sum),
    # replenishment history face and one scarcity seam behind both the
    # purchase gate and api_supply.
    ("ledger-apimarket-restock", os.path.join(
        "ledger", "test_apimarket_restock.py"), 8),
    # AC-AMI1..AC-AMI8 pre-registered in the R2096 explore-queue
    # claim row BEFORE this suite existed: the seller-side
    # unanswered-rating inbox read face (all ratings of the seller
    # merged across listings, only the unanswered ones, oldest debt
    # first, conversation arithmetic, effective stars, retired
    # listings keep their debt, seller isolation, pure read).
    ("ledger-apimarket-sellerinbox", os.path.join(
        "ledger", "test_apimarket_sellerinbox.py"), 8),
    # AC-AMDM1..AC-AMDM8 pre-registered in the R2112 explore-queue
    # claim row BEFORE this suite existed: the seller-side demand read
    # face (every listing of the seller as a row, live watches only,
    # net conversion through unrefunded purchases, retired listings
    # keep demand, effective-metadata and current-price seams, seller
    # isolation, pure read) plus the report attention consumer.
    ("ledger-apimarket-listingdemand", os.path.join(
        "ledger", "test_apimarket_listingdemand.py"), 8),
    # AC-RPX1..AC-RPX8 registered in the R2115 explore-queue claim row
    # before this suite existed (honesty note: the product code landed
    # earlier in the same window, disclosed in that row): the seller
    # refund exposure face - unrefunded purchases' stored dev_share
    # against the live ledger balance, dense listing-owned row set,
    # liability never recomputed from a price, refunds moving both
    # sides by the same amount, the funding/covered law, retirement
    # keeping the obligation, the account gate before any read, pure
    # read, cross-restart identity and the report attention consumer
    # (refund_risk family, REPORT_SCHEMA 8).
    ("ledger-apimarket-refundexposure", os.path.join(
        "ledger", "test_apimarket_refundexposure.py"), 8),
    # AC-AMLG1..AC-AMLG8 pre-registered in the R2126 explore-queue
    # claim row BEFORE this suite existed: the seller settlement
    # statement face - the live ledger balance joined to that
    # account's own entries newest first, derived credit/debit
    # totals, oldest-tail truncation, the purchase-credit and
    # refund-debit semantics, zero movement from publish/repricing/
    # metadata/restock/lifecycle, the gate family and its order,
    # honest absence, pure read and cross-restart identity.
    ("ledger-apimarket-sellerledger", os.path.join(
        "ledger", "test_apimarket_sellerledger.py"), 8),
    # AC-AMLGB1..AC-AMLGB8 pre-registered in the R2128 explore-queue
    # claim row BEFORE this suite existed: the buyer settlement
    # statement (the mirror of the seller statement) - live balance
    # through the same seam plus the buyer's own entries newest first,
    # derived credit/debit totals, oldest-tail truncation, the
    # purchase-debit and refund-credit semantics, zero movement from
    # publish/repricing/metadata/restock/lifecycle/rating/reply/
    # watch/question doors, the gate family and its order, honest
    # absence, pure read and cross-restart identity.
    ("ledger-apimarket-buyerledger", os.path.join(
        "ledger", "test_apimarket_buyerledger.py"), 8),
    # AC-AMCL1..AC-AMCL8 pre-registered in the R2129 explore-queue
    # claim row BEFORE this suite existed: the post-sale claim
    # registry - one append-only claim per purchase (disputed price
    # stored with it), status derived from the refunds table only,
    # the pinned gate order, buyer/seller/market views through one
    # filter pair, oldest-first queue, pure read and cross-restart
    # identity.
    ("ledger-apimarket-claims", os.path.join(
        "ledger", "test_apimarket_claims.py"), 8),
    # AC-AMCR1..AC-AMCR8 pre-registered in the R2130 explore-queue
    # claim row BEFORE this suite existed: the seller answer door for a
    # claim - one append-only response per claim, the pinned gate order,
    # a one-seam status derivation with refunded beating answered, the
    # answer keys on all three queue views, pure read and restart
    # identity.
    ("ledger-apimarket-claims-respond", os.path.join(
        "ledger", "test_apimarket_claims_respond.py"), 8),
    # AC-AMCW1..AC-AMCW8 pre-registered in the R2131 explore-queue
    # claim row BEFORE this suite existed: the buyer withdrawal door
    # that closes a claim - one append-only withdrawal per claim, the
    # pinned gate order, a one-seam status derivation
    # (refunded > withdrawn > answered > open), the withdrawal key on
    # all three queue views, pure read, restart identity.
    ("ledger-apimarket-claims-withdraw", os.path.join(
        "ledger", "test_apimarket_claims_withdraw.py"), 8),
    # AC-AMCN1..AC-AMCN8 pre-registered in the R2137 explore-queue row
    # BEFORE this suite existed: the buyer follow-up note that makes the
    # claim thread two-way - one append-only note per claim, the pinned
    # gate order, the claim thread read face with its enumerated event
    # stream and same-second rank, the disputed flag, party gating,
    # pure read and restart identity.
    ("ledger-apimarket-claimnote", os.path.join(
        "ledger", "test_apimarket_claimnote.py"), 8),
    # AC-AMCT1..AC-AMCT8 pre-registered in the R2132 explore-queue row
    # BEFORE this suite existed: the category directory axis - the
    # publish-time category declaration and its pre-gate, the exact
    # api_search filter, and the api_categories directory with its
    # conservation law, partition/live-price law, pure read, the
    # idempotent pre-category migration and restart identity.
    ("ledger-apimarket-category", os.path.join(
        "ledger", "test_apimarket_category.py"), 8),
    # AC-AMRC1..AC-AMRC8 pre-registered in the R2133 explore-queue row
    # BEFORE this suite existed: the review cycle law - a refusal is no
    # longer terminal, the seller resubmission door, the queue and
    # public faces reading the current cycle verdict through one seam,
    # the seller-side review status face, the write-once-per-cycle
    # history, zero token movement, the idempotent pre-cycle migration
    # and restart identity.
    ("ledger-apimarket-reviewcycle", os.path.join(
        "ledger", "test_apimarket_reviewcycle.py"), 8),
    # AC-REVM1..AC-REVM8 pre-registered in the R2097 explore-queue
    # claim row BEFORE this suite existed: the seller-side monthly
    # revenue timeline read face (cash basis - a sale books in the
    # UTC month of its purchase, a refund books in the UTC month it
    # was refunded and never rewrites the sale month, so a later
    # month refund shows an honestly negative net there; lifetime
    # conservation against raw rows, seller isolation, honest empty
    # envelope, account gate before any read, pure read).
    ("ledger-apimarket-revenuemonths", os.path.join(
        "ledger", "test_apimarket_revenuemonths.py"), 8),
    # AC-AMMM1..AC-AMMM8 pre-registered in the R2099 explore-queue
    # claim row BEFORE this suite existed: the market-wide monthly
    # trade timeline (cash basis - a sale books in the UTC month of
    # its purchase, a refund books in the UTC month it was refunded
    # and never rewrites the sale month; participant counts from
    # purchases only so a refund-only month honestly reports zero;
    # lifetime conservation against api_market_stats, the raw rows and
    # the union of every seller's revenue months; no-arg pure read).
    ("ledger-apimarket-marketmonths", os.path.join(
        "ledger", "test_apimarket_marketmonths.py"), 8),
    # R2100 buyer-side monthly spend mirror: eleven-key envelope with
    # eleven-key month rows on the same cash-basis law (purchase books
    # in the purchased_utc month, refund in the refunded_utc month and
    # never rewriting the purchase month), buyer isolation, lifetime
    # conservation against api_buyer_profile and the raw rows, pure
    # read with zero token movement.
    ("ledger-apimarket-buyermonths", os.path.join(
        "ledger", "test_apimarket_buyermonths.py"), 8),
    # R2101 first CONSUMER of the market read faces: the settlement
    # report generator renders market totals, the market month table,
    # seller month tables with their sales rows and buyer profiles with
    # their month tables into one self-contained offline HTML page
    # (deterministic, fully escaped, standing AIGC/disclaimer markers,
    # pure read, no external reference).
    ("ledger-apimarket-report", os.path.join(
        "ledger", "test_apimarket_report.py"), 9),
    # R2102 attention digest on the same report generator: the
    # statement-shaped R2101 page now opens with an ordered operator
    # to-do list derived from the faces (seller inbox debt, sold-out
    # shelves, negative settlement months) plus a machine-readable
    # ASCII JSON sidecar, both pure read.
    ("ledger-apimarket-attention", os.path.join(
        "ledger", "test_apimarket_report_attention.py"), 9),
    # R2103 machine-readable contract on the same report generator: the
    # versioned ASCII envelope (schema_version/report/attention) wraps
    # the same collect() dict the page consumes and lands atomically, so
    # automation gets a stable shape instead of scraping HTML.
    ("ledger-apimarket-reportjson", os.path.join(
        "ledger", "test_apimarket_report_json.py"), 8),
    # R2106 resident workbench on the same report generator: every buyer
    # block now reads the two newest resident faces (rating-debt queue
    # and watch alert feed) on every collect, with the additive schema
    # bump 1 -> 2 and a legacy-dict degrade path.
    ("ledger-apimarket-reportworkbench", os.path.join(
        "ledger", "test_apimarket_report_workbench.py"), 8),
    # apimarket buyer watch alert feed - the resident-side events of
    # the R2086 watchlist (price move / sold out / retired), derived
    # from the price-at-watch seam.
    ("ledger-apimarket-watchalerts", os.path.join(
        "ledger", "test_apimarket_watchalerts.py"), 8),
    # R2183 buyer watchlist budget: live watches rolled into a spend
    # reading with one bucket per row (purchased > delisted > sold_out
    # > buyable) and savings that never net a rise against a drop.
    ("ledger-apimarket-watchbudget", os.path.join(
        "ledger", "test_apimarket_watchbudget.py"), 8),
    # R2107 public activity feed: eleven append-only event families
    # merged into one ordered, windowable, kind-filterable stream.
    ("ledger-apimarket-marketfeed", os.path.join(
        "ledger", "test_apimarket_marketfeed.py"), 8),
    # R2113 per-listing filter on that feed: listing_id narrows the same
    # stream to one shelf, and every dossier block now carries the
    # listing's own activity tail (schema 6 -> 7 additive).
    ("ledger-apimarket-feedlisting", os.path.join(
        "ledger", "test_apimarket_marketfeed_listing.py"), 8),
    # R2139 seller dimension on that feed: dev_account narrows the same
    # stream to the shelves ONE seller owns, so a seller reads a single
    # timeline of their own events instead of merging N per-listing
    # answers by hand; the envelope echoes the filter only when given.
    ("ledger-apimarket-feeddev", os.path.join(
        "ledger", "test_apimarket_feeddev.py"), 8),
    # R2108 activity section on the report generator: the R2107 feed now
    # has a consumer - every collect reads the newest FEED_LIMIT events
    # into an activity block, the page renders them, and the JSON
    # contract moves 2 -> 3 additively.
    ("ledger-apimarket-activity", os.path.join(
        "ledger", "test_apimarket_report_activity.py"), 8),
    # R2109 listing dossiers on the report generator: the seven
    # per-listing history faces (view / lifecycle / price / metadata /
    # supply / ratings / replies) now have a consumer - every collect
    # reads them for every listing the market holds, live or retired,
    # and the JSON contract moves 3 -> 4 additively.
    ("ledger-apimarket-reportdossier", os.path.join(
        "ledger", "test_apimarket_report_dossier.py"), 8),
    # R2110 buyer history on the report generator: library, watchlist,
    # refund provenance and rating history finally have a consumer, and
    # the rating rows expose rating_id so the history face is reachable;
    # the JSON contract moves 4 -> 5 additively.
    ("ledger-apimarket-buyerhistory", os.path.join(
        "ledger", "test_apimarket_report_buyerhistory.py"), 8),
    # R2111 market-wide refund register: one row set answers the
    # operator refund question (window + seller + listing filters,
    # month/developer/row groupings, exact money conservation) and the
    # settlement report renders it; the JSON contract moves 5 -> 6
    # additively.
    ("ledger-apimarket-refundregister", os.path.join(
        "ledger", "test_apimarket_report_refundregister.py"), 8),
    # R2105 buyer-side rating-debt queue: the mirror of the R2096
    # seller inbox - only the purchases still awaiting a rating,
    # oldest debt first, with the refund precedence pinned.
    ("ledger-apimarket-buyertodo", os.path.join(
        "ledger", "test_apimarket_buyertodo.py"), 8),
    # R2116 seller demand block on the settlement report: the last read
    # face without a block consumer now renders one table per seller
    # (live watchers, net conversions, retired shelves kept) and the
    # JSON schema moves 8 -> 9 additively.
    ("ledger-apimarket-reportdemand", os.path.join(
        "ledger", "test_apimarket_report_demand.py"), 8),
    # R2125 distribution-duty block on the settlement report: the R2124
    # review queue and public-display envelopes plus the derived
    # undisclosed-seller gaps, so the JSON schema moves 14 -> 15
    # additively.
    ("ledger-apimarket-reportduty", os.path.join(
        "ledger", "test_apimarket_report_duty.py"), 8),
    # R2134 post-sale claim block on the settlement report: api_claims
    # had no consumer at all, so the operator page now carries the
    # market-wide claim envelope plus a claim_debt attention family and
    # the JSON schema moves 16 -> 17 additively.
    ("ledger-apimarket-reportclaims", os.path.join(
        "ledger", "test_apimarket_report_claims.py"), 8),
    # R2135 single-purchase dossier (api_purchase_dossier): one trade's
    # whole story behind one party-gated read face, because a support
    # ticket or a settlement dispute had to be assembled by hand from
    # api_library + api_refund + api_claims + the ledger statements.
    ("ledger-apimarket-purchasedossier", os.path.join(
        "ledger", "test_apimarket_purchasedossier.py"), 8),
    # R2138 seller unified duty queue (api_seller_todo): the four
    # seller obligations each lived on their own face (unanswered
    # ratings, unanswered questions, the claim queue and the R2137
    # disputed state), so a seller with N listings had to open four
    # faces and merge them by hand. This is the buyer-side
    # api_buyer_todo mirror.
    ("ledger-apimarket-sellertodo", os.path.join(
        "ledger", "test_apimarket_sellertodo.py"), 8),
    # R2140 buyer post-sale decision queue (api_buyer_claim_todo): the
    # claim thread became two-way across R2129..R2137, but the ball
    # only changed hands silently - R2138 had to state that an
    # answered claim with no note stays out of the SELLER queue
    # "because the ball is with the buyer", and nothing told the
    # buyer. Five disjoint states with pinned precedence, only the
    # needs_decision rows queued, pushed from the append-only tables.
    ("ledger-apimarket-buyerclaimtodo", os.path.join(
        "ledger", "test_apimarket_buyerclaimtodo.py"), 8),
    # R2136 provider identity revision leg (revise_provider /
    # api_provider_history): register_provider was write-once per
    # developer while the unified social credit code is the published
    # disclosure field, so one wrong character was a permanent
    # mis-disclosure. Append-only revisions behind one effective-value
    # seam keep the identity and public display faces byte-identical
    # until a revision exists.
    ("ledger-apimarket-providerrev", os.path.join(
        "ledger", "test_apimarket_providerrev.py"), 8),
    # R2117 seller-side rating quality scorecard (api_seller_quality):
    # star distribution, reply coverage and one quality row per shelf,
    # wired into every seller block plus a quality_risk attention
    # family, so the JSON schema moves 9 -> 10 additively.
    ("ledger-apimarket-sellerquality", os.path.join(
        "ledger", "test_apimarket_sellerquality.py"), 8),
    # R2118 pre-purchase Q&A (ask_question / answer_question /
    # api_listing_qna / api_seller_questions): the ask and answer
    # doors, the public listing thread and the seller open-question
    # queue, wired into every seller block plus a question_debt
    # attention family, so the JSON schema moves 10 -> 11 additively.
    ("ledger-apimarket-qna", os.path.join(
        "ledger", "test_apimarket_qna.py"), 8),
    # R2119 buyer-side question history (api_buyer_questions): the
    # asking side gets the merged view the seller side already had,
    # wired into every buyer block plus a my-questions table, so the
    # JSON schema moves 11 -> 12 additively.
    ("ledger-apimarket-buyerquestions", os.path.join(
        "ledger", "test_apimarket_buyerquestions.py"), 8),
    # R2120 seller-side answered-question ledger (api_seller_answers):
    # the proving side of the Q&A service - what was answered, what was
    # said, and how long each buyer waited - wired into every seller
    # block plus an answered-questions table, so the JSON schema moves
    # 12 -> 13 additively.
    ("ledger-apimarket-selleranswers", os.path.join(
        "ledger", "test_apimarket_selleranswers.py"), 8),
    # R2145 answer-revision leg: answer_question was write-once while
    # every other commodity axis grew a remedy door; one append-only
    # revision table plus a single effective-text seam shared by the
    # three public Q&A read faces.
    ("ledger-apimarket-answerrev", os.path.join(
        "ledger", "test_apimarket_answerrev.py"), 8),
    # R2147 category-revision leg: the last write-once declaration on
    # the listing row gets an append-only remedy door plus one
    # effective-bucket seam shared by the catalog, demand, discovery
    # filter and competitive bucket, and a history face.
    ("ledger-apimarket-categoryrev", os.path.join(
        "ledger", "test_apimarket_categoryrev.py"), 8),
    # R2124 distribution-duty faces: provider real-name registration
    # (append-only, one row per developer), the public display layer
    # (registered name plus unified social credit code shown per live
    # listing, unregistered shown honestly) and the review refusal
    # gate with its pending queue.
    ("ledger-apimarket-provideridentity", os.path.join(
        "ledger", "test_apimarket_provideridentity.py"), 8),
    # R2121 slow-answer attention family: the seller-side answered
    # ledger already measured the wait, so the digest surfaces a reply
    # older than one day as a sortable operator to-do item; the JSON
    # schema moves 13 -> 14 additively.
    ("ledger-apimarket-reportslowanswer", os.path.join(
        "ledger", "test_apimarket_report_slowanswer.py"), 8),
    # R2122 settlement CSV bundle: the market / seller / buyer month
    # tables projected from the same collect() dict as three pinned
    # RFC4180 files (LF, atomic write), with the HTML and JSON artifacts
    # unchanged (CSV_SCHEMA=1, REPORT_SCHEMA stays 14).
    ("ledger-apimarket-settlementcsv", os.path.join(
        "ledger", "test_apimarket_settlement_csv.py"), 8),
    # R2114 source-anchored decisions watermark v2 (D-20261025-08): the
    # four-tuple {repo, commit_sha, blob_bytes, sha256} plus a
    # reproducible fetch command, with the pinned comparison order and
    # a stale source that never advances the watermark.
    ("os-decwatermark", os.path.join(
        "..", "os", "test_dec_watermark.py"), 8),
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
    # multi-year combined yearbook read window (R2007): the
    # honorcert yearbooks_combined face - ascending year-axis
    # canonicalization, duplicate/shape front door before any
    # read, single-source derivation from honor_yearbook with
    # one outer-riding disclaimer, cross-year distinct-account
    # totals, honest empty envelope, live recompute isolation,
    # pure-read law (AC-HYM1..HYM7 pre-registered in
    # state/queue/explore.md).
    ("ledger-honorcert-multiyear", os.path.join(
        "ledger", "test_honorcert_multiyear.py"), 7),
    # multi-year combined yearbook cross-restart persist window
    # (R2025): the yearbooks_combined seat of the persist family
    # - three-piece close/rebuild on the same two dbs replays
    # the scrambled-request combined envelope byte-identical,
    # post-restart 2026/2027 block live continuation with the
    # permanent-certificate and cross-read isolation laws, the
    # front-door gate surviving the restart with zero
    # referenced-face calls, zero-token pure-read law (AC-HYCP1..
    # HYCP7 pre-registered in state/queue/explore.md).
    ("ledger-honorcert-yearbookspersist", os.path.join(
        "ledger", "test_honorcert_yearbooks_persist.py"), 7),
    # multi-year combined yearbook subset-axis semantics window
    # (R2026): the yearbooks_combined request-family hardening -
    # strictly descending full-set canonicalization, single-year /
    # two-year / all-empty-years request families, same-year-set
    # multi-form folding (list/tuple/scrambled/set/frozenset/
    # generator all byte-identical), single-source cross over the
    # whole family, zero-token pure-read law (AC-HYS1..HYS7
    # pre-registered in state/queue/explore.md).
    ("ledger-honorcert-yearbooksubsetaxis", os.path.join(
        "ledger", "test_honorcert_yearbook_subsetaxis.py"), 7),
    # honorcert yearbook zero-earn boundary cross-restart window
    # (R2027): a real product-path world where the ledger and
    # collectibles domains hold data (four ensured accounts, two
    # registered behaviors, one festival-namespace certificate)
    # while the earn axis is empty returns an honest empty
    # combined envelope across the request family, survives the
    # three-piece stack restart byte-identical, keeps every
    # front-door gate enforcing before any referenced read, and
    # continues with zero phantom after the restart's first earn
    # and first grant (festival certificate never leaks into a
    # block; re-grant idempotent) (AC-HYZB1..HYZB7
    # pre-registered in state/queue/explore.md).
    ("ledger-honorcert-yearbook-zeroboundary", os.path.join(
        "ledger", "test_honorcert_yearbook_zeroboundarypersist.py"),
     7),
    # honorcert yearbook zero-earn boundary gate-family
    # cross-restart same-code window (R2028): the 14-probe
    # front-door rejection battery (the R2027 AC-HYZB2 probe
    # face) rejects with the identical code vector on the
    # pre-close instance and on both full-stack restart
    # instances, the counting wrapper keeps its per-instance
    # 0/1 call semantics, the empty-board grant probe returns
    # the same granted=0 receipt on every instance with zero
    # phantom awards, the honest empty envelope stays
    # byte-identical across the whole window, and the window is
    # zero-token end to end (AC-HYZG1..HYZG7 pre-registered in
    # state/queue/explore.md).
    ("ledger-honorcert-yearbook-zeroboundarygate", os.path.join(
        "ledger",
        "test_honorcert_yearbook_zeroboundarygatepersist.py"), 7),
    # honorcert grant idempotency axis + top_n gate-family
    # cross-restart same-code window (R2029): on a positive-earn
    # world the already-granted idempotency gate converges every
    # replayed honoree to "already" with zero new rows and that
    # convergence survives both full-stack restarts (the
    # duplicate law lives in the collectibles domain), the
    # post-restart incremental heal re-grants exactly the new
    # board head while a demoted member keeps the yearbook row
    # (certificate permanence x on-board derivation), and the
    # 8-probe top_n cap-boundary battery (bad year, six bad
    # top_n forms, blank item_id) rejects with the identical
    # code vector on all three instances before any referenced
    # honor_board call lands (AC-HYGG1..HYGG7 pre-registered in
    # state/queue/explore.md).
    # grant slice-width axis on the already-granted honor world
    # (R2074): a narrower re-run (top_n=1) leaves the row set and
    # the certify flags untouched while alice keeps her permanent
    # certificate, a wider re-run (top_n=4) grants exactly the two
    # untouched members, an out-of-range top_n=9 CLAMPS to board
    # length instead of rejecting, a replay with a different
    # item_id keeps the first-grant award, the eight-form front-door
    # battery stays orthogonal to the idempotency axis (row set
    # constant around the batch), and both width forms replay
    # byte-identical across two full-stack restarts
    # (AC-HYGW1..HYGW8 pre-registered in state/queue/explore.md).
    ("ledger-honorcert-grantwidthworld", os.path.join(
        "ledger", "test_honorcert_grantwidthworld.py"), 8),
    # R2075 liveroom open-session minor-guard front-door law: the cheap
    # doors reject before the guard while the three guard-bearing forms
    # reach check_live once each, a refused session id stays unused, the
    # minor live ban survives two full-stack restarts and a guard-free
    # face keeps the old behaviour (AC-LGM1..AC-LGM8 pre-registered).
    ("liveroom-minorguard-persist", os.path.join(
        "liveroom", "test_liveroom_minorguard_persist.py"), 8),
    ("ledger-honorcert-grantgate-persist", os.path.join(
        "ledger", "test_honorcert_grantgatepersist.py"), 7),
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
    # R2008 explore-queue claim (coverage_board R1982/R1985
    # window reseed): dual-window combined board - the default
    # full-window board and the explicit month-window board in
    # one envelope (single derivation source via live
    # coverage_board delegations, window gate fail-closed
    # before any read, E_DSB_BAD_WINDOW family, provenance
    # separation probe, dense zero rows inside a window,
    # pure-read law, zero-cache liveness)
    # (AC-CVDB1..AC-CVDB7 pre-registered in
    # state/queue/explore.md).
    ("ledger-datasub-coveragedual", os.path.join(
        "ledger", "test_datasub_coveragedual.py"), 7),
    # R2009 explore-queue claim (coverage_board_dual R2008 seed
    # persist sibling): the dual-window combined coverage board
    # across a full-stack restart - byte-identical dual battery
    # replay, gate zero-drift, post-restart dual-zone continuation
    # (AC-CVDBP1..AC-CVDBP7 pre-registered in
    # state/queue/explore.md).
    ("ledger-datasub-coveragedualpersist", os.path.join(
        "ledger", "test_datasub_coveragedualpersist.py"), 7),
    # R2030 explore-queue claim (the R2009 reseed month-roll
    # seat): cross-month recorded world, the roll-moment
    # freeze law, month-diff telescoping, two restarts
    # (AC-CVMR1..AC-CVMR7 pre-registered in
    # state/queue/explore.md).
    ("ledger-datasub-coveragemonthroll", os.path.join(
        "ledger", "test_datasub_coveragemonthroll.py"), 7),
    # R2066 explore-queue claim (the R2030 month-roll seat
    # successor): the coverage bad-window gate family across
    # three instances - the ordered ten-form probe vector
    # (seven dual + three board) answers the single family code,
    # the dual-face reject performs zero coverage_board
    # delegations while each board probe lands exactly one,
    # probe batches leave world digests constant, interleaved
    # sequencing proves no latching gate and the post-battery
    # write path stays alive (AC-CVGG1..AC-CVGG8 pre-registered
    # in state/queue/explore.md).
    ("ledger-datasub-coveragegatepersist", os.path.join(
        "ledger", "test_datasub_coveragegatepersist.py"), 8),
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
    # R1990 stats_board dual-window cross-restart persistence
    # example: full-stack close -> rebuild on the same paths,
    # dual family byte-identical, post-restart registration and
    # place/retract activity recompute from disk state alone
    # (persist family R1889/R1900/R1902; third-instance
    # stability; pure-read law under restart)
    # (AC-SSDP1..AC-SSDP7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsdual-persist",
     os.path.join("ledger", "test_showcase_statsdualpersist.py"), 7),
    # R1992 showcase stats cap-window cross-restart persistence:
    # the R1988 cap face (tail-window slice + honest overflow
    # block) across a full-stack instance restart - byte identity
    # of the cap family {1,2,50} + default full read, post-restart
    # registration total continuation with tail slide and old-row
    # freeze, post-restart activity zero-cache recompute, third
    # instance stability, pure-read law, hygiene (suite-only).
    # (AC-SSTP1..AC-SSTP7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statscap-persist",
     os.path.join("ledger", "test_showcase_statscappersist.py"), 7),
    # R2010 explore-queue FIFO head claim (R1992 reseed row):
    # showcase stats_board zero-registry boundary world
    # cross-restart example - the three faces (default board,
    # cap-window tail read, dual combined board) keep honest
    # empty envelopes byte-identical across a full-stack
    # restart, bad-limit gates fire before any read, the
    # post-restart first registration + first place continue
    # all three faces with zero phantom rows, third instance
    # stability, pure-read law, hygiene (suite-only).
    # (AC-SSZB1..AC-SSZB7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsboundary-persist",
     os.path.join("ledger",
                   "test_showcase_statsboundarypersist.py"), 7),
    # R2035 explore-queue FIFO head claim (R2010 reseed row):
    # showcase stats_board bad-argument gate family
    # cross-restart same-code example - the 21-probe battery
    # (5 default limit forms + 6 dual limit forms + 9 window
    # forms + the dual-bad order probe) rejects with an
    # identical ordered code vector on instances one/two/three
    # across two full-stack restarts, zero side effects per
    # probe batch on the populated face, post-restart liveness,
    # pure-read law, hygiene (suite-only).
    # (AC-SGB1..AC-SGB7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsgatepersist",
     os.path.join("ledger",
                   "test_showcase_statsgatepersist.py"), 7),
    # R2036 explore-queue FIFO head claim (R2035 reseed row):
    # showcase_view_window bad-window gate family cross-restart
    # same-code - 15 bad window forms (non-str types incl. the
    # windowed-face None law, non-strict YYYY-MM shapes) plus
    # the window-before-showcase order probe and the
    # good-window unknown-showcase probe reject with an
    # identical ordered code vector (16x E_SH_BAD_WINDOW + 1x
    # E_SH_UNKNOWN_SHOWCASE) on instances one/two/three across
    # two full-stack restarts, zero side effects per probe batch
    # on the populated face, post-restart liveness (real write
    # on a new showcase, cross-showcase read isolation),
    # pure-read law, hygiene (suite-only).
    # (AC-SVW1..AC-SVW7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-viewwindow-gatepersist",
     os.path.join("ledger",
                   "test_showcase_viewwindow_gatepersist.py"), 7),
    # R2038 explore-queue FIFO head claim (R2036 reseed row):
    # showcase_view_window month-window slice cross-restart
    # persistence example window - full-stack close -> reopen
    # window-scoped read family byte-identical, post-restart
    # new place / new retract window liveness (the record-time
    # month law, months derived from stored events - zero wall
    # clock), cross-showcase write isolation, pure-read law,
    # third instance, hygiene (suite-only).
    # (AC-SVWP1..AC-SVWP7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-viewwindow-persist",
     os.path.join("ledger",
                   "test_showcase_viewwindow_persist.py"), 7),
    # R2067 explore-queue FIFO head claim (R2038 reseed row):
    # showcase window-view re-place bounce across restart - the
    # retracted world (empty window reads, full append-only
    # chronicle) persists byte-identically, post-restart re-place
    # bounce returns the item to the all-time view, its
    # record-month window view and the tour, a second
    # retract -> re-place cycle repeats the bounce, the
    # untouched showcase stays byte-frozen, the bounce final
    # state crosses a second restart onto a third instance,
    # gate codes stay stable across restarts, pure-read law,
    # hygiene (suite-only).
    # (AC-SVRP1..AC-SVRP7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-viewwindow-replacepersist",
     os.path.join("ledger",
                   "test_showcase_viewwindow_replacepersist.py"), 7),
    # R1995 explore-queue FIFO head claim (R1968 reseed row):
    # proposal progress_board cross-restart persistence example
    # window - full-stack close -> reopen byte-identical board
    # (dense registry axis, rounded-progress sort, mirror-SQL
    # third path), restart-surviving gates same-code, new
    # signature liveness (zero-cache recompute), threshold
    # crossing + overshoot saturation post-restart (memorial
    # first-award and honest overshoot count), new registration
    # dense row, third instance, pure-read law
    # (AC-PBP1..AC-PBP7 pre-registered in
    # state/queue/explore.md).
        ("ledger-proposal-progresspersist",
         os.path.join("ledger",
                       "test_proposal_progresspersist.py"), 7),
        # R1997 explore-queue FIFO head claim (R1977 reseed row): civic
        # behavior distribution month-window read face - strict YYYY-MM
        # window slice (write-time strict day check makes the prefix
        # match exact), total cross-window separation both directions,
        # empty windows keep the registry-complete all-zero board,
        # default full-window call byte-identical with the pre-window
        # era (zero window key), explicit-window envelope carries the
        # window additively, default == sept+oct cross per behavior,
        # pure-read law + ast zero-write scan, schema/config pins
        # (AC-CVM1..CVM7 pre-registered in state/queue/explore.md).
        ("civic-behavior-monthwindow",
         os.path.join("ledger", "test_civic_monthwindow.py"), 7),
        # R1998 (takeover closeout): civic behavior month-window read
        # face cross-restart persistence example window - close -> same
        # db reopen five-form byte-identity, post-restart earn and
        # registry continuation, two-restart stability, pure-read law
        # plus hygiene (AC-CVMP1..CVMP7 pre-registered in the
        # state/queue/explore.md claim row before this code existed).
        ("civic-behavior-monthwindow-persist",
         os.path.join("ledger", "test_civic_monthwindow_persist.py"), 7),
        # R1999 explore-queue FIFO head claim (R1998 reseed row): civic
        # honor_board_competition month-window read face - strict
        # YYYY-MM window slice inside the year scope (year-window
        # coupling gate, fail-closed before any read), 1224
        # competition ranks inside the window (ties share the
        # minimum rank, next distinct skips, account_id ASC
        # tie-break with zero insertion-order keys), total
        # cross-window separation both directions, in-year empty
        # windows and far-year windows honest empty boards,
        # default full-year call byte-identical with the
        # pre-window era (zero window key, single-source
        # derivation over honor_board preserved), explicit-window
        # envelope carries the window additively, pure-read law +
        # ast zero-write scan, schema/config pins
        # (AC-HCW1..HCW7 pre-registered in state/queue/explore.md).
        ("civic-competition-monthwindow",
         os.path.join("ledger",
                      "test_civic_competition_monthwindow.py"), 7),
        # R2005 explore-queue FIFO head claim (R1999 reseed row):
        # civic honor_board_competition month-window read face
        # cross-restart persistence example window - close ->
        # new CivicPointsFace over the same civic.db: default
        # full-year + 2026-09/10/11/12 competition boards all
        # byte-identical (zero in-memory drift in the derived
        # 1224 face); post-restart earn recomputes the October
        # window zero-cache with the tie rank shifting 4 -> 5
        # while old windows stay byte-frozen; post-restart
        # behavior registration + November earns land the first
        # November content and dissolve the full-year tie
        # live; the gate family (year-window coupling, bad
        # window, bad year) rejects with identical codes across
        # the restart before any read, zero row side effects;
        # third-instance sequential reads byte-identical;
        # pure-read law + manual SQL + 1224 second-derivation
        # crosses; product sha256 pinned (suite-only round)
        # (AC-HCWP1..HCWP7 pre-registered in
        # state/queue/explore.md).
        ("civic-competition-monthwindow-persist",
         os.path.join("ledger",
                      "test_civic_competition_monthwindowpersist.py"), 7),
        # R2011 explore-queue FIFO head claim (R1995 reseed row):
        # proposal progress_board zero-registration boundary world
        # cross-restart example - both zero-param read faces
        # (progress_board + proposal_board) keep honest empty
        # envelopes byte-identical across a full-stack restart in
        # a boundary world (ledger domain populated, registry axis
        # empty), the write-side gate family fires before any
        # read, the post-restart first registration + first sign
        # chain continue the boards with zero phantom rows ending
        # on the threshold crossing where the memorial linkage
        # re-proves the collectibles dock reconnection; third
        # instance stability, pure-read law, hygiene (suite-only)
        # (AC-PBZB1..AC-PBZB7 pre-registered in
        # state/queue/explore.md).
        ("ledger-proposal-progressboundary-persist",
         os.path.join("ledger",
                      "test_proposal_progressboundarypersist.py"), 7),
    # R2015 explore-queue FIFO head claim (R1996 reseed row): the
    # per-showcase statistics board month-window read face
    # (R1888/R1998 window-parameterization family law): default
    # window=None full-window byte-identical zero drift, explicit
    # strict YYYY-MM window slices places/retracts by the
    # record-time law (substr(acted_utc, 1, 7)) and displayed_now
    # by the latest window-recorded event (_displayed_rows_window
    # law), earlier-month display stays off the later window,
    # straddle pair reads an honest in-window retract, eventless
    # month shows dense honest zeros, additive window envelope
    # key, window x cap orthogonality with the honest overflow
    # block, malformed window fail-closed after the limit gate,
    # pure-read law, hygiene
    # (AC-SSM1..AC-SSM7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsmonth",
     os.path.join("ledger", "test_showcase_statsmonth.py"), 7),
    # showcase stats month-window cross-restart persistence
    # (R2016): seven-form window read family byte-identical
    # across a full-stack close/reopen, post-restart current-month
    # real-path recompute and new-month direct-INSERT recompute,
    # gate family same-code on the restarted instance, third
    # instance stability, pure-read law, hygiene
    # (AC-SSMP1..AC-SSMP7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsmonth-persist",
     os.path.join("ledger",
                  "test_showcase_statsmonthpersist.py"), 7),
    # R2017 statsmonth zero-registry boundary world persist:
    # seven-form month-window family on an empty registry stays
    # honest-empty across a full-stack restart; gates fire
    # before any read on the empty world; first registration +
    # first current-month place continue every window form with
    # honest window splits, zero phantom rows
    # (AC-SSMZ1..AC-SSMZ7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsmonthboundary-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonthboundarypersist.py"), 7),
    # R2018 showcase statsmonth post-retraction current-month
    # live-state cross-restart persistence example window: the
    # retract-state successor of the statsmonth family (R2016
    # place-state / R2017 zero-registration boundary already
    # in register): a current-month retraction through the
    # real path leaves the current-month window net-flow
    # identity displayed_now == places - retracts intact on
    # the place-first world shape, the earlier-month window
    # stays byte-frozen across the retraction, and the whole
    # eleven-form read family persists byte-identically
    # across two full-stack restarts (AC-SSMR1..AC-SSMR7
    # pre-registered in state/queue/explore.md).
    ("ledger-showcase-statsmonthretract-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonthretractpersist.py"), 7),
    # R2019 showcase statsmonth post-retraction re-place
    # bounce-state cross-restart persistence example window:
    # the re-place successor of the statsmonth family (R2016
    # place-state / R2017 zero-registration boundary / R2018
    # retract-state already in register): after a current-month
    # retraction, re-placing the freed item through the real
    # path keeps the current-month window net-flow identity
    # displayed_now == places - retracts intact on the bounced
    # shape ({3,1,2}: 2 == 3 - 1), the new place event joins
    # the current-month window and continues the view/chronicle/
    # tour faces, the old-month window stays byte-frozen, and
    # the bounced live state persists byte-identically across
    # a second full-stack restart (AC-SSMRP1..AC-SSMRP7
    # pre-registered in state/queue/explore.md).
    ("ledger-showcase-statsmonthreplace-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonthreplacepersist.py"), 7),
    # R2021 showcase statsmonth post-re-place re-retraction
    # live-state cross-restart persistence example window:
    # the re-retract successor of the statsmonth family
    # (R2016 place-state / R2017 zero-registration boundary /
    # R2018 retract-state / R2019 re-place bounce already in
    # register): after the re-place bounce, retracting the
    # re-placed item again through the real path keeps the
    # current-month window net-flow identity
    # displayed_now == places - retracts intact on the
    # re-retracted shape ({3,2,1}: 1 == 3 - 2), the
    # re-retract event joins the current-month window and
    # continues the view/chronicle/tour faces, the old-month
    # window stays byte-frozen, the not-displayed gate refuses
    # a further retraction, and the re-retracted live state
    # persists byte-identically across a second full-stack
    # restart (AC-SSMRR1..AC-SSMRR7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsmonth-rere-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonthrerepersist.py"), 7),
    # R2043 explore-queue FIFO head claim (R2021 reseed row):
    # statsmonth family cross-month STRADDLE-pair net-flow
    # identity exception cross-restart persistence example -
    # the positive closure of the R2018/R2019 claim rulings
    # that kept straddle pairs out of those worlds: an item
    # placed in a previous month (R1730 fixture law) and
    # retracted through the real path in the current month
    # reads {0,1,0} in the current-month window where the
    # month-window identity displayed_now == places - retracts
    # honestly BREAKS (0 != 0 - 1) while the full board keeps
    # the per-row identity ({3,1,2}: 2 == 3 - 1); the
    # post-restart re-place closes the straddle into the
    # leading-retract variant {1,1,1} (1 != 1 - 1) with the
    # full board still holding per row ({4,1,3}: 3 == 4 - 1);
    # the old-month window stays byte-frozen, the
    # view/chronicle/tour faces continue, and both live states
    # persist byte-identically across two full-stack restarts.
    # (AC-SMST1..AC-SMST7 pre-registered in
    # state/queue/explore.md).
    ("ledger-showcase-statsmonth-straddle-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonthstraddlepersist.py"), 7),
    # R2044 explore-queue FIFO head claim (R2043 reseed row):
    # statsmonth double-straddle pair exception-deepening
    # example - TWO previous-month fixture places retracted
    # through the real path in the current month read {0,2,0}
    # in the current-month window (0 != 0-2, the deepened
    # honest exception); after the restart the two freed
    # slots re-place one at a time: {1,2,1} (1 != 1-2, the
    # leading-retract multi-pair variant) then {2,2,2}
    # (2 != 2-2) - the closed-yet-still-broken terminal
    # shape: the window identity stays broken for straddle
    # rows even after full closure because the window can
    # never see the previous-month original places, while
    # the full board keeps the per-row identity at every
    # step ({3,2,1}, {4,2,2}, {5,2,3}).
    # (AC-SMDS1..AC-SMDS7 pre-registered in
    # state/queue/explore.md.)
    ("ledger-showcase-statsmonth-straddle2-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonth_straddle2persist.py"), 7),
    # R2071 (criteria pre-registered in the explore-queue claim row
    # BEFORE this suite existed - honesty law; AC-SMTR1..AC-SMTR7):
    # the post-closure retract THIRD shape of the statsmonth
    # straddle family ({2,3,1} with the negative-rhs break, plus the
    # {3,3,2} bounce pinned in passing) enters the battery. Pure
    # wiring - the suite file itself is unchanged; its own main()
    # prints seven AC PASS-lines plus the SUITE summary line.
    ("ledger-showcase-statsmonth-straddle3-persist",
     os.path.join(
         "ledger",
         "test_showcase_statsmonth_straddle3persist.py"), 7),
    # R2033 (criteria pre-registered in the backlog R2033 claim row
    # BEFORE this wiring existed - honesty law; AC-FN8): the
    # FUNNEL-LOOP v0.1 four-ring suite (docs/ops/
    # FUNNEL-AUTOMATION-PLAN-v1.md; AC-FN1..FN7 delivered R2032)
    # enters the daily battery. Pure wiring - the suite file itself
    # is unchanged. The suite's own main() prints exactly eight
    # case PASS-lines plus the SUITE summary line (8 criteria).
    ("funnel", os.path.join("funnel", "test_funnel_daily.py"), 8),
    # R2048 tech-queue FIFO head claim (R2047 reseed row): funnel
    # CLI bad-args gate family - the wiring layer absorbs every
    # reject into ONE clean E_FN_BAD_ARGS line + exit 2 (the
    # reconcile_daily family contract), the day is validated before
    # any disk artifact exists, the gate-FAIL exit law and the
    # library raise law stay intact (probe draft one had a
    # substring false positive on datetime.timedelta, fixed with
    # call-paren pinning before delivery; criteria unchanged).
    # (AC-FCG1..FCG7 pre-registered in state/queue/tech.md.)
    ("funnel-cli-gates",
     os.path.join("funnel", "test_funnel_cli_gates.py"), 7),
    # R2049 tech-queue FIFO head claim (R2047 reseed row, second
    # seed): funnel four-ring counter cross-restart persistence -
    # source rows, the stored rollup envelope bytes, same-day replay
    # idempotency, the disk-read previous-day delta (with a
    # fresh-db null control), a double restart cycle, the stored
    # gate/hits column coherence, and hygiene. The delta criterion
    # was amended during delivery: the first draft said "six keys
    # all zero", which is not what a day-over-day delta means -
    # honestly re-registered as each day-scoped key equal to minus
    # the day-one value with the lifetime outstanding delta at zero
    # (the zero-delta face is the AC-FPR5 fresh-db control).
    # (AC-FPR1..AC-FPR8 pre-registered in state/queue/tech.md.)
    ("funnel-persist",
     os.path.join("funnel", "test_funnel_persist.py"), 8),
    # R2050 tech-queue FIFO head claim (R2047 reseed row): funnel
    # inbox cross-day re-scan idempotency + first-write-wins
    # attribution - the three keyed source tables keep the first
    # day's row when the same id reappears on a later day with a
    # different payload, day ring counters book only new ids, the
    # day-window counts stay separate from the lifetime outstanding
    # face, the dispatches full-table re-scan books only new leads,
    # the earlier day's stored envelope stays byte-frozen, and the
    # prev-day delta closes over the previous day. One criterion was
    # amended during delivery: "old-day envelope re-derive is byte
    # identical" is not the product semantics - the lifetime
    # outstanding key follows the whole ledger, so the dual face is
    # registered instead (day-scoped keys frozen, lifetime key live).
    # (AC-FRS1..AC-FRS8 pre-registered in state/queue/tech.md.)
    ("funnel-rescan",
     os.path.join("funnel", "test_funnel_rescan.py"), 8),
    # R2051 tech FIFO head claim (R2047 reseed row): late-arrival
    # re-rollup on an already-booked day - a late inbox row for day D
    # books on the re-run, the day-D counts re-derive and the rollups
    # face still holds exactly one row, a second re-run is
    # byte-identical, the earlier day's stored envelope is frozen
    # while D's delta stays anchored to it, the conservation identity
    # survives a late spend, a late duplicate id is a no-op, the
    # correction propagates into the next day's delta, and the
    # hygiene face is read off the parsed AST.
    # (AC-FRL1..AC-FRL8 pre-registered in state/queue/tech.md.)
    ("funnel-rerollup",
     os.path.join("funnel", "test_funnel_rerollup.py"), 8),
    # R2052 tech-queue FIFO head claim (R2047 reseed row, fourth
    # seed): the funnel conservation identity over a multi-day chain
    # - the lifetime outstanding == granted - spent on every day of a
    # four-day world, the day-window / lifetime separation, key-by-key
    # delta closure, the pre-registered arithmetic chain, an empty
    # day with zero penetration, three-account coherence (stored
    # envelope vs booking-time SQL vs gate), whole-chain replay
    # idempotence (amended during delivery: the lifetime face
    # re-derives on rewrite, so byte identity is asserted on a
    # newest-day replay while day windows stay frozen), and hygiene.
    # (AC-FCV1..AC-FCV8 pre-registered in state/queue/tech.md.)
    ("funnel-conservation",
     os.path.join("funnel", "test_funnel_conservation.py"), 8),
    # R2053 tech-queue FIFO head claim (R2052 reseed row, fifth
    # seed): the per-account token ledger read face - flows grouped
    # by account into granted/spent/outstanding three keys in
    # sorted-account order, the sum of per-account outstanding
    # closing the lifetime rollup total, the day-window vs lifetime
    # vs honest-empty-day law, the blank account as its own bucket,
    # an honest negative overdraft (no clamp), cross-restart
    # byte-identical reads with zero writes, pure-read plus
    # bad-day fail-closed, and hygiene (ASCII, zero network, zero
    # wall clock). (AC-FAR1..AC-FAR8 pre-registered in
    # state/queue/tech.md before the suite existed.)
    ("funnel-account",
     os.path.join("funnel", "test_funnel_account.py"), 8),
    # R2054 tech-queue FIFO head claim (R2052 reseed row): the
    # funnel per-sku order totals read face - the rollup counts
    # orders per day and the ledger face reads flows, but the
    # orders table had no sku-grouped unit/amount aggregation at
    # all. A pure read: one bucket per sku, sorted sku order, the
    # blank sku as its own bucket (never merged into a named one),
    # lifetime vs explicit-day window with an honest empty day,
    # re-booking the same inbox leaves the totals unchanged,
    # bad-day fail-closed with zero row touch, zero writes plus
    # cross-restart byte-identical reads, and hygiene (ASCII, zero
    # network, zero wall clock, deterministic). (AC-FST1..AC-FST8
    # pre-registered in state/queue/tech.md before the suite
    # existed.)
    ("funnel-sku",
     os.path.join("funnel", "test_funnel_sku.py"), 8),
    # R2055 tech-queue FIFO head claim (R2052 reseed row): the
    # funnel dispatch route distribution read face - ring 2 reports
    # the routes of one run only and the rollup counts dispatches
    # per day, so the cross-round dispatches-by-route face did not
    # exist. A pure read: one bucket per route, sorted route order,
    # the honest unrouted archive as its own bucket (never merged
    # into a named route), an unknown route kept instead of dropped,
    # lifetime vs explicit-day window with an honest empty day,
    # idempotent re-dispatch, bad-day fail-closed with zero row
    # touch, zero writes plus cross-restart byte-identical reads,
    # and hygiene (ASCII, zero network, zero wall clock,
    # deterministic). (AC-FRT1..AC-FRT8 pre-registered in
    # state/queue/tech.md before the suite existed.)
    ("funnel-route",
     os.path.join("funnel", "test_funnel_route.py"), 8),
    # R2056 tech-queue FIFO head claim (R2052 reseed row): the funnel
    # daily CLI multi-day evidence determinism - the CLI accepted
    # --evidence (R2033) and the rejected-argument family was pinned
    # (AC-FCG, R2048), but no example covered a D1/D2/D3 chain. This
    # suite drives the real subprocess: one evidence file per day with
    # strict LF/utf-8 and byte equality to the stdout block, day
    # isolation, chain-rerun determinism (day-window keys frozen, the
    # lifetime key recomputing by product design - amended at delivery
    # time), printed envelope equals the stored rollup, the gate/exit
    # contract pair, evidence purity (ASCII, no repo path, no
    # un-injected date), source-table idempotency and hygiene.
    # (AC-FCC1..AC-FCC8 pre-registered in state/queue/tech.md before
    # the suite existed.)
    ("funnel-cli-chain",
     os.path.join("funnel", "test_funnel_cli_chain.py"), 8),
    # R2057 tech-queue FIFO head claim (R2052 reseed row): the funnel
    # inbox classification law - an inbox entry is a regular file with
    # the exact lower-case .json suffix, everything else (other
    # suffixes, directories including one named "fake.json") is junk
    # skipped unopened and never recursed into; a bad in-contract file
    # (bad JSON text, non-object value, empty file, undecodable bytes)
    # rejects the whole ring with FunnArgError before any row is
    # written, and no decoder error escapes the library boundary.
    # (AC-FIN1..AC-FIN8 pre-registered in state/queue/tech.md before
    # the suite or the product change existed.)
    ("funnel-inbox",
     os.path.join("funnel", "test_funnel_inbox.py"), 8),
    # R2058 tech-queue FIFO head claim (R2054 reseed row): the funnel
    # per-sku order totals read face across restarts - the gap AC-FST7
    # left behind (it proves only a single close/reopen of the same
    # face). Three-instance cascade on a three-day order world: the
    # first instance anchors lifetime plus three day windows plus a
    # no-row day; the reopened instance reproduces all five
    # byte-for-byte; a late day-three batch then grows the lifetime
    # face (the blank sku stays its own bucket, the new sku takes its
    # byte-order position) while day one and two stay frozen;
    # re-booking the original inbox is idempotent across the restart;
    # no-row days stay honest empty; the read path is pure and the
    # restart writes nothing; a second restart keeps the injected
    # state stable at a pinned row count; hygiene is AST-checked.
    # (AC-FSP1..AC-FSP8 pre-registered in state/queue/tech.md before
    # the suite existed.)
    ("funnel-sku-persist",
     os.path.join("funnel", "test_funnel_sku_persist.py"), 8),
    # R2059 tech-queue FIFO head claim (R2054 reseed row): the funnel
    # ranked per-sku order totals read face - sku_totals answers "what
    # is in the book?" but nothing ranked the buckets by money, so the
    # amount leaderboard face was missing. sku_top cuts the same buckets
    # by summed amount descending, ties broken by ascending sku byte
    # order, with a dense rank column and a prefix-only cap (no padding,
    # no phantom rows); the blank sku competes as its own bucket, a
    # non-positive or non-integer cap fails closed, day windows match
    # sku_totals, and the read is pure across restarts. (AC-FTP1..AC-FTP8
    # pre-registered in state/queue/tech.md before the suite existed;
    # AC-FTP8 amended in-window from "no clock library" to "no wall
    # clock calls" because datetime is the day-validation import.)
    ("funnel-sku-top",
     os.path.join("funnel", "test_funnel_sku_top.py"), 8),
    # R2060 tech-queue FIFO head claim (R2057 reseed row): the funnel
    # dispatch route distribution read face across restarts - three-day
    # anchor world, byte-identical reopen, post-restart injection with
    # the already-read day windows frozen, idempotent inbox re-drop,
    # honest empty day, pure read (restart writes no rows), a third
    # instance that does not drift again, and the hygiene face.
    # (AC-FRTP1..AC-FRTP8 pre-registered in state/queue/tech.md before
    # the suite existed.)
    ("funnel-route-persist",
     os.path.join("funnel", "test_funnel_route_persist.py"), 8),
    # R2061 tech-queue FIFO head claim (R2058 discovery row): the
    # funnel ring-3 order sku type gate - absent sku stays the blank
    # bucket, JSON scalars take one declared canonical text form,
    # containers reject the whole ring (E_FN_BAD_ARGS, zero rows), the
    # idempotency key law is untouched, and the read faces bucket on
    # the canonical form. (AC-FSK1..AC-FSK8 pre-registered in
    # state/queue/tech.md before the suite existed.)
    ("funnel-sku-gate",
     os.path.join("funnel", "test_funnel_sku_gate.py"), 8),
    # R2062 tech-queue FIFO head claim (R2056 reseed row): the funnel
    # evidence overwrite/rotation law - a brace-free --evidence path
    # keeps the historical single-file overwrite face, the literal
    # {day} token selects one file per day, any other brace form
    # rejects before the wiring layer creates directories, and the
    # write is always zero-append single-dialect. (AC-FCR1..AC-FCR8
    # pre-registered in state/queue/tech.md before the suite existed.)
    ("funnel-evidence-rotate",
     os.path.join("funnel", "test_funnel_evidence_rotate.py"), 8),
    # R2064 tech-queue FIFO head claim (R2056 reseed row): the funnel
    # CLI external-environment independence window - default_paths()
    # is the single module-anchored source for the carrier defaults
    # (so any cwd lands on the same repo-root state/funnel face and
    # produces byte-identical stdout/evidence), an ambient
    # PYTHONIOENCODING=cp936 shell changes no byte of the ASCII face,
    # explicitly passed relative paths stay cwd-relative (the second
    # law), and the gate verdict stays environment-independent.
    # (AC-FCW1..AC-FCW8 pre-registered in state/queue/tech.md before
    # the suite or the product face existed.)
    ("funnel-cli-env",
     os.path.join("funnel", "test_funnel_cli_env.py"), 8),
    # R2069 tech-queue claim (rebuilt R2059 seed window): the sku_top
    # ranking semantics battery - zero-amount buckets keep their rank,
    # negative-amount buckets rank last without clamping or dropping,
    # the cap is a strict prefix of the full board even with three tied
    # amounts (cutting never re-sorts), a late day re-ranks the lifetime
    # face while earlier day windows stay byte-frozen, and the money
    # conservation bound holds. (AC-FTS1..AC-FTS8 pre-registered in
    # state/queue/tech.md before the suite existed.)
    ("funnel-sku-top-rank",
     os.path.join("funnel", "test_funnel_sku_top_rank.py"), 8),
    # R2155 tech-queue FIFO head claim (R2149 reseed row): funnel
    # first-write-wins made auditable - a later submission of an
    # already-booked natural key carrying DIFFERENT money data used to
    # vanish in silence (INSERT OR IGNORE kept the first row). The two
    # money rings now register that divergence once per distinct claim
    # in an append-only table read by book_conflicts(); rings 1/2 keep
    # first-write-wins without registration (lead-text divergence is a
    # UGC content-safety matter, not a bookkeeping ruling). Ring return
    # dictionaries and every read face are unchanged (pure addition).
    # (AC-FSW1..AC-FSW8 pre-registered in state/queue/tech.md before
    # the suite or the product face existed.)
    ("funnel-firstwrite",
     os.path.join("funnel", "test_funnel_firstwrite.py"), 8),
    # R2039 explore-queue FIFO head claim (R2011 reseed row):
    # proposal register/sign write-side gate family
    # cross-restart same-code example - the 17-probe battery
    # (11 register-side: dup id, seven bad-args forms, the
    # args-before-content-gate order probe, the content-gate
    # hit; 6 sign/read-side: unknown proposal, outside-window,
    # window-before-dup order probe, duplicate sign, self
    # sign, unknown read) rejects with an identical ordered
    # code vector on instances one/two/three across two
    # full-stack restarts on a POPULATED registry world, zero
    # side effects per probe batch, post-restart liveness with
    # the world-growth battery invariance, zero-token law,
    # hygiene (suite-only).
    # (AC-PPG1..AC-PPG7 pre-registered in
    # state/queue/explore.md).
    ("ledger-proposal-gatepersist",
     os.path.join("ledger",
                   "test_proposal_gatepersist.py"), 7),
    # R2040 explore-queue FIFO head claim (R2039 reseed row):
    # proposal gate family ZERO-REGISTRATION boundary world
    # cross-restart same-code example - the boundary-state gap
    # fill beside the R2039 populated-world face: the identical
    # ordered R2011 AC-PBZB2 8-probe battery (sign-side unknown
    # proposal, six register bad-args, content-gate hit)
    # rejects with an identical ordered code vector on
    # instances one/two/three across two full-stack restarts
    # on a zero-registration boundary world, zero side
    # effects per probe batch, honest empty envelopes
    # byte-identical around every batch and across all
    # instances, zero-token law with zero phantom memorial
    # awards, hygiene (suite-only).
    # (AC-PBZG1..AC-PBZG7 pre-registered in
    # state/queue/explore.md).
    ("ledger-proposal-gateboundary-persist",
     os.path.join("ledger",
                   "test_proposal_gateboundarypersist.py"), 7),
    # R2041 explore-queue FIFO head claim (R2040 reseed row):
    # proposal sign-side bad-args gate family cross-restart
    # same-code example - the three-shape gap fill beside the
    # R2039/R2040 batteries (neither carried the sign-side
    # account/id/tick argument gates): an ordered 12-probe
    # battery (1 well-formed control reaching the unknown
    # branch, 11 bad-args probes: 4 account shape, 2 proposal
    # id shape, 5 tick shape) rejects with the identical pinned
    # code vector on instances one/two/three across two
    # full-stack restarts on a zero-registration boundary
    # world; the control probe versus the bad-args probes is
    # the mechanical proof of the bad-args-before-unknown
    # ordering law, zero side effects per probe batch, honest
    # empty envelopes byte-identical around every batch,
    # zero-token law with zero phantom memorial awards,
    # hygiene (suite-only).
    # (AC-PSG1..AC-PSG7 pre-registered in
    # state/queue/explore.md).
    ("ledger-proposal-signbadargs-persist",
     os.path.join("ledger",
                   "test_proposal_signbadargspersist.py"), 7),
    # R2068 explore-queue FIFO head claim (R2041 reseed successor):
    # proposal sign-side bad-args gate family LOADED-WORLD
    # cross-restart same-code example - R2041 pinned the three
    # shape gates on a zero-registration boundary world, this
    # window pins them on a loaded world (two proposals, three
    # signs) where the shape gates have live business gates
    # behind them: an ordered 15-probe battery (1 control on a
    # ghost id, 11 shape probes on the KNOWN id, 3 orthogonal
    # business-gate probes) rejects with the identical pinned
    # vector on instances one/two/three across two full-stack
    # restarts, proving both the bad-args-before-{window,self,
    # dup} ordering law and that the three business gates stay
    # reachable; loaded read faces byte-identical around every
    # batch and across restarts, qualified state never flips,
    # zero-token with zero phantom memorial, hygiene
    # (suite-only).
    # (AC-PSL1..AC-PSL7 pre-registered in
    # state/queue/explore.md).
    ("ledger-proposal-signbadargs-loadedpersist",
     os.path.join("ledger",
                   "test_proposal_signbadargspersist_loaded.py"), 7),
    # R2070 explore-queue FIFO head claim (R2042 seed row): the lobby
    # chat mute / idempotency boundary family - the idem gate sits
    # after the content gates and before the rate/mute gate, so an
    # in-TTL (client_msg_id, text) replay still answers
    # chat.duplicate inside a mute window (no budget, no violation,
    # no store row) while an expired replay falls through into the
    # mute refusal; the idem cache is lobby-scoped, so a second
    # connection can seed a key a muted connection replays to a
    # duplicate; mute accounting belongs to the rate gate alone (the
    # five orthogonal refusals keep the counters at zero); a
    # deterministic fake clock replaces server.time so windows move
    # without sleeps, and the shipped config is only TTL-compressed
    # in memory. (AC-CMI1..AC-CMI8 pre-registered in
    # state/queue/explore.md before the suite existed.)
    ("lobby-chat-mute-idem",
     os.path.join("lobby", "test_chatmute_idem.py"), 8),
    # R2072 evidence single-writer helper: one LF/utf-8 writer for
    # evidence logs (normalise before write, atomic replace, post-write
    # dialect assertion) plus a read-only census wiring check - the
    # recurring CRLF/LF mixture that failed reconcile-daily-census cd7
    # in R2068/R2069/R2070 gets a mechanical birth-place guard.
    # (AC-EVD1..AC-EVD8 pre-registered in state/queue/tech.md R2072.)
    ("os-evidence-writer",
     os.path.join("..", "os", "test_evidence_writer.py"), 8),
    # R2172 directory batch face for the same writer: census a whole
    # directory, repair only the flagged .log files, report before and
    # after bytes/lines, and roll the batch back on any failure.
    # (AC-EVDB1..AC-EVDB8 pre-registered in state/queue/tech.md R2172.)
    ("os-evidence-writer-dir",
     os.path.join("..", "os", "test_evidence_writer_dir.py"), 8),
    # R2126 birth-place cleanup for the sandbox worlds themselves: the
    # battery reclaims only what it just created, behind the same name /
    # signature anchors and the same rename probe the standalone sweep
    # uses (D-20261025-15 TEMP governance, owner-side fix).
    # (AC-TMP1..AC-TMP8 pre-registered in state/queue/tech.md R2126.)
    ("ledger-tmp-sweep",
     os.path.join("..", "os", "test_tmp_sweep.py"), 18),
    # R2151: the writer-census drift detector itself gets negative
    # coverage (three shell-capture dialects must be caught by name)
    # and a per-file disposition face so a rebuilt file can return to
    # DRIFT-CLEAN without a whole-baseline re-freeze.
    # (AC-CDN1..AC-CDN8 pre-registered in state/queue/tech.md R2151.)
    ("ledger-census-negative",
     os.path.join("..", "os", "test_census_negative.py"), 12),
    # R2152: the round ledger line that the F3 law and the
    # status-export self_drive face derive from gets a machine check -
    # pinned parse, bad-shape family with its gate order, the
    # narrative/ledger coverage law, the tail window and a live gate
    # over state.json.
    # (AC-LGR1..AC-LGR8 pre-registered in state/queue/tech.md R2152.)
    ("os-ledger-lines",
     os.path.join("..", "os", "test_ledger_lines.py"), 8),
    # R2157: the baseline is the gate's only exemption channel, so its
    # semantics are pinned - one entry exempts one round only, a stale
    # entry is reported instead of rotting quietly, a broken baseline
    # fails closed under its own code with zero writes, and an absent
    # baseline equals --no-baseline.
    # (AC-LGB1..AC-LGB8 pre-registered in state/queue/tech.md R2157.)
    ("os-ledger-baseline",
     os.path.join("..", "os", "test_ledger_baseline.py"), 8),
    # R2153: the double-run identity dialect gets one dialect instead of
    # two - explicit bytes/conclusions modes, claim verification against
    # the files (a byte claim that does not hold is a false claim) and a
    # read-only audit of the whole qa/ evidence directory with a shipped
    # known-defect baseline.
    # (AC-RID1..AC-RID8 pre-registered in state/queue/tech.md R2153.)
    ("os-run-identity",
     os.path.join("..", "os", "test_run_identity.py"), 8),
    # R2154: the round's closing station - the ledger line this window
    # just wrote is checked where it is written (parseable, settleable
    # reason, newer than everything already settled) instead of being
    # discovered by a later window, with one LEDGER OK <round> echo.
    # (AC-LGN1..AC-LGN8 pre-registered in state/queue/tech.md R2154.)
    ("os-ledger-closeout",
     os.path.join("..", "os", "test_ledger_closeout.py"), 8),
    # R2156: the logs/ inventory learns to read the qa/ evidence tree -
    # default byte identity, growth adaptivity, inode de-duplication across
    # overlapping roots and hard links, fail-closed root gates and retention
    # protection, so a "whole disk" census can no longer be green while
    # blind to the proof files the rounds produce.
    # (AC-LTI1..AC-LTI8 pre-registered in state/queue/tech.md R2156.)
    ("os-logs-inventory",
     os.path.join("..", "os", "test_logs_inventory.py"), 8),
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


TMP_TOOL = os.path.join(BASE, os.pardir, "os", "sweep_suite_tmp.py")


def sweep_run_worlds(started_at):
    """AC-TMP1..AC-TMP6: reclaim only the sandbox worlds this very run
    created, through the one ownership/probe implementation that lives
    in src/os/sweep_suite_tmp.py (reuse, never a second copy).

    Fail-open by contract: a missing or broken tool leaves the battery
    verdict untouched. Returns a report dict or None.
    """
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(
            "sweep_suite_tmp", TMP_TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.sweep_run_temps(
            tempfile.gettempdir(), started_at, execute=True)
    except Exception as exc:  # noqa: BLE001 - fail-open is the contract
        print("TMP RECLAIM skipped: %s" % exc.__class__.__name__, flush=True)
        return None


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
    reclaim = sweep_run_worlds(t0)
    if reclaim is not None:
        print("TMP RECLAIM candidates=%d removed=%d busy=%d failed=%d "
              "reclaimed=%.2f MiB"
              % (reclaim["candidates"], reclaim["removed"],
                 reclaim["busy_skipped"], reclaim["failed"],
                 reclaim["mib"]), flush=True)
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
