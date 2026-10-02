"""Wiring acceptance suite for the MinorGuardFace three call-site
integration (BigDomain R939, first cut of the R937 scope-amendment
follow-up row cc76e8c; criteria AC-W1..AC-W4 were pre-registered in
the R939 backlog row before this code existed - honesty law. AC-W5
regression = the four in-register suites re-run from the R939 qa
evidence log, not from here).

WIRING_POINTS registry (minors.py):
  [0] member activate   -> check_time  (read-only window gate; the
       money gate stays single-source at the pay entry, no re-record)
  [1] pay create_order  -> check_spend (server-table amount, before
       any billing row exists)
  [2] liveroom open     -> check_live  (sec.31 minors hard ban)

Resident-id namespace: guard residents ARE census avatar ids; every
resident must be registered (adult or minor) so the guard can make
a scope call - an unknown resident refuses (fail-closed). Wired
faces with missing caller-supplied gate inputs refuse likewise.

Usage: python test_wiring.py
"""

import datetime
import html
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_PAY = os.path.normpath(os.path.join(BASE, "..", "pay"))
_MEMBER = os.path.normpath(os.path.join(BASE, "..", "member"))
_LIVEROOM = os.path.normpath(os.path.join(BASE, "..", "liveroom"))
for _p in (_MEMBER, _PAY, _LEDGER, _LOBBY, _LIVEROOM, BASE):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import minors as MG                                # noqa: E402 (this package)
import ledger as L                                 # noqa: E402 (ledger product)
import sec_gate as SG                              # noqa: E402 (lobby product)
import store as lobby_store                        # noqa: E402 (lobby product)
import orders as pay_orders                        # noqa: E402 (pay product)
import adapters as A                               # noqa: E402 (pay product)
import member as M                                 # noqa: E402 (member product)
import liveroom as LR                              # noqa: E402 (R608 face)

RESULTS = []

_ERRS = (MG.GuardError, LR.LiveRoomError, pay_orders.PayError, M.MemberError)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_codes(fn, *codes):
    try:
        fn()
    except _ERRS as exc:
        code = getattr(exc, "code", None)
        return code in codes, "%s (detail=%s)" % (code, exc)
    return False, "no-error-raised"


def count_rows(db_path, table, where="1=1", args=()):
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute(
            "SELECT COUNT(*) FROM %s WHERE %s" % (table, where),
            args).fetchone()[0])
    finally:
        conn.close()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_guard(kid_window=(600, 900), kid_single=100000, kid_daily=100000):
    """One guard: adult amy, windowed minor kid, limitless minor nolimit.
    Limit VALUES are test-supplied (the [needs-CEO] face never gets a
    platform-invented default - minors.py law)."""
    g = MG.MinorGuardFace()
    g.register_resident("amy", False)
    g.register_resident("kid", True, "g1")
    g.register_resident("nolimit", True, "g1")
    g.set_guardian_limits("g1", "kid", allowed_windows=[kid_window],
                          single_cent=kid_single, daily_cent=kid_daily)
    return g


# -- liveroom world ---------------------------------------------------------


def build_liveroom(guard):
    tmp = tempfile.mkdtemp(prefix="wire-liveroom-")
    cfg = load_json(os.path.join(_LEDGER, "config.json"))
    led = L.Ledger(os.path.join(tmp, "ledger.db"), cfg)
    gate = SG.SecGate(cfg["gate"]["forbidden_words"],
                      cfg["gate"]["advisory_ban_words"])
    face = LR.LiveRoomFace(led, gate, cfg["token"]["disclaimer"],
                           cfg["token"]["ai_label_text"],
                           minor_guard=guard)
    legacy = LR.LiveRoomFace(L.Ledger(os.path.join(tmp, "legacy.db"), cfg),
                             gate, cfg["token"]["disclaimer"],
                             cfg["token"]["ai_label_text"])
    return {"tmp": tmp, "led": led, "face": face, "legacy": legacy,
            "db": os.path.join(tmp, "ledger.db"),
            "legacy_db": os.path.join(tmp, "legacy.db")}


def ac_w1_w2_liveroom():
    w = build_liveroom(build_guard())
    face, db = w["face"], w["db"]
    try:
        ok, ev = expect_codes(
            lambda: face.open_session("s1", "r1", True, "rc-1"),
            LR.E_LIVE_BAD_ARGS)
        record("AC-W2", ok,
               "liveroom guard wired, opener id missing -> %s" % ev)

        ok, ev = expect_codes(
            lambda: face.open_session("s1", "r1", True, "rc-1",
                                      opener_resident_id="kid"),
            "E_MG_LIVE_BAN")
        zero = count_rows(db, "live_sessions") == 0
        record("AC-W1", ok and zero,
               "minor opener refused (%s); live_sessions rows=%d"
               % (ev, count_rows(db, "live_sessions")))

        res = face.open_session("s1", "r1", True, "rc-1",
                                opener_resident_id="amy")
        record("AC-W1", res.get("attended") is True
               and count_rows(db, "live_sessions") == 1,
               "adult opener opens; rows=%d"
               % count_rows(db, "live_sessions"))

        res = w["legacy"].open_session("s9", "r1", True, "rc-1")
        record("AC-W1", res.get("session_id") == "s9"
               and count_rows(w["legacy_db"], "live_sessions") == 1,
               "legacy face (no guard) opens without opener id (unchanged)")
    finally:
        w["face"].close()
        w["legacy"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


# -- pay world --------------------------------------------------------------


def build_pay(guard):
    tmp = tempfile.mkdtemp(prefix="wire-pay-")
    cfg = load_json(os.path.join(_PAY, "config.json"))
    led_cfg = load_json(os.path.join(_LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = L.Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-WIRE-1", "settlement")
    pay = pay_orders.PayOrders(cfg, os.path.join(tmp, "pay.db"), events,
                               led, minor_guard=guard)
    legacy = pay_orders.PayOrders(cfg, os.path.join(tmp, "legacy-pay.db"),
                                  lobby_store.EventStore(
                                      os.path.join(tmp, "legacy-events.db")),
                                  L.Ledger(os.path.join(tmp, "legacy-ledger.db"),
                                           led_cfg))
    product = sorted(cfg["products"])[0]
    price = int(cfg["products"][product]["price_cent"])
    return {"tmp": tmp, "cfg": cfg, "led": led, "pay": pay, "legacy": legacy,
            "product": product, "price": price,
            "db": os.path.join(tmp, "pay.db"),
            "legacy_db": os.path.join(tmp, "legacy-pay.db")}


def ac_w2_w3_pay():
    g = build_guard()
    w = build_pay(g)
    pay, db, product, price = w["pay"], w["db"], w["product"], w["price"]
    try:
        ok, ev = expect_codes(
            lambda: pay.create_order(product, "kid"),
            pay_orders.E_BAD_STATE)
        record("AC-W2", ok,
               "pay guard wired, minor_date missing -> %s" % ev)

        ok, ev = expect_codes(
            lambda: pay.create_order(product, "nolimit", minor_date="2026-10-02"),
            "E_MG_NO_LIMIT")
        record("AC-W3", ok and count_rows(db, "pay_orders") == 0,
               "minor without limits refused (%s); zero orders" % ev)

        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=price - 1, daily_cent=price)
        ok, ev = expect_codes(
            lambda: pay.create_order(product, "kid", minor_date="2026-10-02"),
            "E_MG_SPEND_SINGLE")
        record("AC-W3", ok and count_rows(db, "pay_orders") == 0,
               "minor over single limit refused (%s); zero orders" % ev)

        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=price, daily_cent=price)
        res = pay.create_order(product, "kid", minor_date="2026-10-02")
        again = pay.create_order(product, "kid", minor_date="2026-10-02")
        record("AC-W3", res.get("status") == "created"
               and again.get("idempotent") is True
               and count_rows(db, "pay_orders") == 1,
               "minor within limits creates 1 order (replay idempotent)")

        res = pay.create_order(product, "amy", minor_date="2026-10-02")
        record("AC-W3", res.get("status") == "created"
               and count_rows(db, "pay_orders") == 2,
               "adult pass-through creates; orders=%d"
               % count_rows(db, "pay_orders"))

        ok, ev = expect_codes(
            lambda: pay.create_order(product, "stranger",
                                     minor_date="2026-10-02"),
            "E_MG_UNKNOWN")
        record("AC-W3", ok and count_rows(db, "pay_orders") == 2,
               "unregistered resident refused (%s); orders stay 2" % ev)

        res = w["legacy"].create_order(product, "amy")
        record("AC-W3", res.get("status") == "created",
               "legacy pay (no guard) creates without minor_date (unchanged)")
    finally:
        pay.close()
        w["legacy"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


# -- member world -----------------------------------------------------------


def build_member(guard):
    tmp = tempfile.mkdtemp(prefix="wire-member-")
    mcfg = load_json(os.path.join(_MEMBER, "config.json"))
    pcfg = load_json(os.path.join(_PAY, "config.json"))
    led_cfg = load_json(os.path.join(_LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = L.Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-WIRE-2", "settlement")
    pay = pay_orders.PayOrders(pcfg, os.path.join(tmp, "pay.db"), events, led)
    store = M.MemberStore(mcfg, os.path.join(tmp, "member.db"), pay,
                          minor_guard=guard)
    legacy = M.MemberStore(mcfg, os.path.join(tmp, "legacy-member.db"), pay)
    product = sorted(pcfg["products"])[0]
    return {"tmp": tmp, "led": led, "pay": pay, "store": store,
            "legacy": legacy, "chans": A.from_config(pcfg),
            "product": product,
            "db": os.path.join(tmp, "member.db"),
            "legacy_db": os.path.join(tmp, "legacy-member.db")}


def grant_for(w, avatar, nonce):
    resp = w["pay"].create_order(w["product"], avatar)
    oid = resp["order_id"]
    w["pay"].place_order(oid)
    amount = w["pay"].order_detail(oid)["amount_cent"]
    cb = w["chans"][resp["channel"]].make_callback(oid, amount, nonce)
    w["pay"].handle_callback(cb)
    items = w["pay"].grants_for(avatar)["items"]
    return items[-1]["grant_id"]


def ac_w2_w4_member():
    w = build_member(build_guard())
    store, db = w["store"], w["db"]
    try:
        g_kid = grant_for(w, "kid", "NONCE-KID-1")
        g_amy = grant_for(w, "amy", "NONCE-AMY-1")

        ok, ev = expect_codes(
            lambda: store.activate(g_kid, "kid"),
            M.E_BAD_STATE)
        record("AC-W2", ok, "member guard wired, minor_now_min missing -> %s"
               % ev)

        ok, ev = expect_codes(
            lambda: store.activate(g_kid, "kid", minor_now_min=100),
            M.E_BAD_STATE)
        record("AC-W2", ok, "member guard wired, minor_date missing -> %s"
               % ev)

        ok, ev = expect_codes(
            lambda: store.activate(g_kid, "kid", minor_now_min=100,
                                   minor_date="2026-10-02"),
            "E_MG_TIME")
        record("AC-W4", ok and count_rows(db, "member_periods",
                                         "census_avatar_id = ?",
                                         ("kid",)) == 0,
               "minor outside window refused (%s); zero periods" % ev)

        res = store.activate(g_kid, "kid", minor_now_min=700,
                             minor_date="2026-10-02")
        record("AC-W4", res.get("census_avatar_id") == "kid",
               "minor inside window activates a real grant")

        res = store.activate(g_amy, "amy", minor_now_min=100,
                             minor_date="2026-10-02")
        record("AC-W4", res.get("census_avatar_id") == "amy",
               "adult pass-through activates (guard wired)")

        res = w["legacy"].activate(g_amy, "amy")
        record("AC-W4", res.get("census_avatar_id") == "amy",
               "legacy store (no guard) activates without gate inputs"
               " (unchanged)")
    finally:
        store.close()
        w["legacy"].close()
        w["pay"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


def ac_w7_pay_grant_commit():
    """AC-W7 (pre-registered R939b, executed R940): the pay grant
    commit face books the minors day ledger exactly once per order,
    idempotent on ref, zero-record on refusal, adults untouched.

    Order ids are content-addressed by (avatar, product, bucket), so
    the two concurrent kid orders use two distinct products."""
    g = build_guard()
    w = build_pay(g)
    pay, db = w["pay"], w["db"]
    chans = A.from_config(w["cfg"])
    prods = sorted(w["cfg"]["products"])
    p1 = w["cfg"]["products"][prods[0]]["price_cent"]
    p2 = w["cfg"]["products"][prods[1]]["price_cent"]
    grant_day = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d")
    try:
        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=max(p1, p2),
                              daily_cent=p1 + p2)

        # (a) granted order books exactly one day-ledger entry (ref=oid)
        res = pay.create_order(prods[0], "kid", minor_date=grant_day)
        oid = res["order_id"]
        pay.place_order(oid)
        cb = chans[res["channel"]].make_callback(
            oid, p1, "NONCE-W7-A")
        out = pay.handle_callback(cb)
        day = g.day_readout("kid", grant_day)
        grant_rows = count_rows(db, "pay_grants", "order_id = ?", (oid,))
        record("AC-W7", out.get("status") == "granted"
               and day["spent_cent"] == p1
               and day["events"] == [oid] and grant_rows == 1,
               "granted minor order books day ledger once: spent=%d "
               "events=%s grant_rows=%d"
               % (day["spent_cent"], day["events"], grant_rows))

        # (b) ref replay (crash-window retry entry) double-records zero
        again = g.record_spend("kid", p1, grant_day, oid)
        day = g.day_readout("kid", grant_day)
        record("AC-W7", again.get("idempotent") is True
               and day["spent_cent"] == p1 and day["events"] == [oid],
               "same-ref record_spend replay is a no-op (zero double-"
               "record): spent=%d events=%s" % (day["spent_cent"],
                                                day["events"]))

        # (c) refusal at grant time records zero and rolls the grant
        res2 = pay.create_order(prods[1], "kid", minor_date=grant_day)
        oid2 = res2["order_id"]
        pay.place_order(oid2)
        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=max(p1, p2), daily_cent=p1)
        cb2 = chans[res2["channel"]].make_callback(
            oid2, p2, "NONCE-W7-C")
        ok, ev = expect_codes(lambda: pay.handle_callback(cb2), "E_MG_SPEND_DAILY")
        day = g.day_readout("kid", grant_day)
        st2 = pay.order_detail(oid2)["status"]
        record("AC-W7", ok and oid2 not in day["events"]
               and day["spent_cent"] == p1
               and count_rows(db, "pay_grants", "order_id = ?", (oid2,)) == 0
               and st2 == "paid",
               "grant-time limit refusal (%s) records zero, rolls back: "
               "spent=%d events=%s status=%s grant_rows2=%d"
               % (ev, day["spent_cent"], day["events"], st2,
                  count_rows(db, "pay_grants", "order_id = ?", (oid2,))))

        # guardian restores budget -> identical callback retries, grant
        # heals and books the one entry (paid->granted heal path)
        g.set_guardian_limits("g1", "kid", allowed_windows=[(600, 900)],
                              single_cent=max(p1, p2),
                              daily_cent=p1 + p2)
        out2 = pay.handle_callback(cb2)
        day = g.day_readout("kid", grant_day)
        record("AC-W7", out2.get("status") == "granted" and out2.get("idempotent") is True
               and day["events"] == [oid, oid2]
               and day["spent_cent"] == p1 + p2,
               "retry heals the refused grant and books its one entry: "
               "spent=%d events=%s" % (day["spent_cent"], day["events"]))

        # (d) adult grant books nothing on the minors day ledger
        res3 = pay.create_order(prods[0], "amy", minor_date=grant_day)
        oid3 = res3["order_id"]
        pay.place_order(oid3)
        cb3 = chans[res3["channel"]].make_callback(
            oid3, p1, "NONCE-W7-D")
        out3 = pay.handle_callback(cb3)
        amy_day = g.day_readout("amy", grant_day)
        record("AC-W7", out3.get("status") == "granted"
               and amy_day["spent_cent"] == 0 and amy_day["events"] == [],
               "adult grant pass-through books no day-ledger entry "
               "(minors-only face)")
    finally:
        pay.close()
        w["legacy"].close()
        w["led"].close()
        shutil.rmtree(w["tmp"], ignore_errors=True)


def ac_w8_frontdoor_card():
    """R940b remainder of the declared row (AC-W8, pre-registered in
    the R939b/R940b backlog rows before this code existed): the
    frontdoor live page mounts the minors compliance face -- real
    guard readings computed at render time (not canned), AIGC label
    + non-investment-advisory + [needs-CEO] + msgSecCheck gate note
    all persistent on the card."""
    _sandbox = os.path.normpath(os.path.join(BASE, ".."))
    if _sandbox not in sys.path:
        sys.path.insert(0, _sandbox)
    import frontdoor  # noqa: E402 (sandbox root, journey runs at import)
    page = frontdoor.render().decode("utf-8")

    # compliance four-piece, all imported from the guard module
    for needle in ("AI-GENERATED LABEL", "NON-INVESTMENT-ADVISORY",
                   "[needs-CEO]", "msgSecCheck"):
        record("AC-W8", needle in page,
               "frontdoor card carries %r" % needle)
    record("AC-W8", "Decree No.766" in page and "sec.31" in page
           and "sec.43" in page,
           "law citation rendered (Decree No.766 sec.31/43-44/24(3))")

    # real readings at render time, matching a fresh probe
    probe = frontdoor.minor_guard_probe()
    expect = ("probe summary: registered=%d calls=%d refusals=%d "
              "allowed=%d spent_cent=%d events=%d replays=%d"
              % (probe["registered"], probe["calls"], probe["refusals"],
                 probe["allowed"], probe["spent_cent"], probe["events"],
                 probe["replays"]))
    record("AC-W8", expect in page and probe["spent_cent"] > 0,
           "rendered readings equal a fresh in-process probe run: %s"
           % expect)

    # live-computation control: shrink the daily limit below the buy
    # amount -> the same render flips to refusal readings (proves the
    # numbers are computed by the guard, never canned strings)
    old_daily = frontdoor.PROBE["daily_cent"]
    try:
        frontdoor.PROBE["daily_cent"] = 990
        page2 = frontdoor.render().decode("utf-8")
        p2 = frontdoor.minor_guard_probe()
        record("AC-W8",
               "spent_cent=0" in page2
               and "spent_cent=%d" % probe["spent_cent"] not in page2
               and p2["spent_cent"] == 0
               and p2["refusals"] == probe["refusals"] + 3,
               "shrinking daily_cent flips the rendered readings "
               "(live compute, no canned numbers): spent 0, refusals "
               "%d" % p2["refusals"])
    finally:
        frontdoor.PROBE["daily_cent"] = old_daily

    # wiring points mounted from the guard module (single source)
    record("AC-W8",
           all(wp.split("->")[0].strip() in page for wp in MG.WIRING_POINTS),
           "WIRING_POINTS mounted from minors module: %d points"
           % len(MG.WIRING_POINTS))


def ac_fd6_m1_walk_card():
    """R942 frontdoor v0.6 M1 walk mount (criteria AC-FD6a..e were
    pre-registered in the R942 backlog row before this code existed;
    AC-FD6f receipt = state log line + backlog done mark + commit).
    The five-station commerce-mount data lives in a single JSON data
    file extracted verbatim from the preview page; the live card is
    pure composition and frontdoor.py must stay pure ASCII so no
    business copy can hide in code."""
    _sandbox = os.path.normpath(os.path.join(BASE, ".."))
    if _sandbox not in sys.path:
        sys.path.insert(0, _sandbox)
    import frontdoor  # noqa: E402 (sandbox root, journey runs at import)
    data = load_json(frontdoor.M1_JSON)
    stations, hooks = data["stations"], data["hooks"]
    record("AC-FD6a", len(stations) == 5 and len(hooks) == 3,
           "data file carries 5 walk stations + 3 first-launch hooks")
    with open(os.path.join(frontdoor.ROOT, "preview", "index.html"),
              encoding="utf-8") as fh:
        prev_html = fh.read()
    synced = all(str(st[k]) in prev_html for st in stations
                 for k in ("name", "role", "mount", "crit", "gate"))
    synced = synced and all(h["copy"] in prev_html for h in hooks)
    record("AC-FD6a", synced,
           "every station row + hook copy verbatim-synced with "
           "preview/index.html (mechanical drift gate)")

    page = frontdoor.render().decode("utf-8")
    record("AC-FD6b",
           data["card_title"] in page
           and all(str(st[k]) in page for st in stations
                   for k in ("name", "role", "mount", "crit", "gate"))
           and all(h["copy"] in page for h in hooks),
           "card title + 5 stations (name/role/mount/crit/gate) + "
           "3 hook copies rendered from the data file")
    with open(frontdoor.__file__, "rb") as fh:
        src = fh.read()
    record("AC-FD6b", max(src) < 0x80,
           "frontdoor.py stays pure ASCII: zero hardcoded business "
           "copy, all Chinese lives in data files (%d bytes checked)"
           % len(src))
    record("AC-FD6c",
           data["service_gate"]["code"] in page
           and data["service_gate"]["note"] in page
           and "class=fail" in page,
           "service-desk gate honest-red row rendered: %s (blocked "
           "on CEO physical items, no fake online)"
           % data["service_gate"]["code"])
    record("AC-FD6d",
           data["hooks_note"] in page and "[needs-CEO]" in page
           and "AI 生成" in page and "≤10-09" in page,
           "card compliance notes rendered from data: [needs-CEO] "
           "pricing + AI-generated copy + M1 milestone window")
    record("AC-FD6e",
           all(marker in page for marker in (
               "Minor Guardian Face", "Quality Face", "Membership Face",
               "Business-day Journey", "Lobby Face", "Pay Face")),
           "prior v0.1..v0.5 faces all still mounted (live page "
           "zero-regression check)")


def ac_fd7_city_commerce_card():
    """R943 frontdoor v0.7 city-commerce-plan card mount (criteria
    AC-FD7a..e were pre-registered in the R943 backlog row before
    this code existed; AC-FD7f receipt = state log line + backlog
    done mark + commit). The canon is docs/spec/city-commerce-plan
    v0.md (R849 skeleton answering audit P-2026-10-02-02 L76); the
    card data file is extracted verbatim from it and this suite
    gates the sync string-by-string. frontdoor.py must stay pure
    ASCII so no business copy can hide in code."""
    _sandbox = os.path.normpath(os.path.join(BASE, ".."))
    if _sandbox not in sys.path:
        sys.path.insert(0, _sandbox)
    import frontdoor  # noqa: E402 (sandbox root, journey runs at import)
    data = load_json(frontdoor.CC_JSON)
    layers, gaps = data["layers"], data["gaps"]
    pricing, miles = data["pricing"], data["milestones"]
    compl = data["compliance"]
    record("AC-FD7a",
           len(layers) == 4 and len(gaps) == 5 and len(pricing) == 3
           and len(miles) == 4 and len(compl) == 4,
           "data file carries 4 business layers + 5 audit-gap rows + "
           "3 pricing references + 4 milestones + 4 compliance items")
    spec_path = os.path.join(frontdoor.ROOT, "docs", "spec",
                             "city-commerce-plan-v0.md")
    with open(spec_path, encoding="utf-8") as fh:
        spec = fh.read()
    # markdown bold markers are presentation-only; the sync gate
    # compares content strings against the marker-stripped canon
    spec_norm = spec.replace("**", "")
    extracted = [data["card_title"], data["layer_title"],
                 data["gap_title"], data["pricing_title"],
                 data["demo_title"], data["workshop_title"],
                 data["milestone_title"], data["compliance_title"],
                 data["pricing_verdict"], data["blocked_note"],
                 data["blocked_note_2"]]
    extracted += [s for l in layers for s in (l["name"], l["desc"])]
    extracted += [s for g in gaps
                  for s in (g["gap"], g["answer"], g["status"])]
    extracted += [s for p in pricing for s in (p["ref"], p["note"])]
    extracted += [s for m in miles for s in (m["m"], m["pre"], m["win"])]
    extracted += [s for c in compl for s in (c["name"], c["text"])]
    extracted += data["demo_bullets"] + data["workshop_bullets"]
    missing = [s for s in extracted if s not in spec_norm]
    record("AC-FD7a", not missing,
           "every extracted string verbatim-synced with the canon "
           "spec (bold-marker-normalized, mechanical drift gate, "
           "%d strings, missing=%d)" % (len(extracted), len(missing)))

    page = frontdoor.render().decode("utf-8")

    def on_page(s):
        # the card escapes for HTML context (e.g. "AtS/W&R" -> amp),
        # so compare the escaped form - what the browser displays
        # back as the literal string
        return html.escape(s, quote=True) in page

    rendered = [data["card_title"], data["source_note"],
                data["pricing_verdict"], data["blocked_note"],
                data["blocked_note_2"]]
    rendered += [s for l in layers for s in (l["name"], l["desc"])]
    rendered += [s for g in gaps
                 for s in (g["gap"], g["answer"], g["status"])]
    rendered += [s for p in pricing for s in (p["ref"], p["note"])]
    rendered += [s for m in miles for s in (m["m"], m["pre"], m["win"])]
    rendered += [c["text"] for c in compl]
    rendered += data["demo_bullets"] + data["workshop_bullets"]
    record("AC-FD7b",
           all(on_page(s) for s in rendered),
           "card title + 4 layers + 5 gap rows + 3 pricing refs + "
           "verdict + 4 milestones + compliance texts + blocked "
           "notes all rendered from the data file (%d strings, "
           "HTML-escape-aware compare)" % len(rendered))
    with open(frontdoor.__file__, "rb") as fh:
        src = fh.read()
    record("AC-FD7b", max(src) < 0x80,
           "frontdoor.py stays pure ASCII: zero hardcoded business "
           "copy, all Chinese lives in data files (%d bytes checked)"
           % len(src))
    record("AC-FD7c",
           data["pricing_verdict"] in page
           and "[needs-CEO]" in page
           and data["gaps"][1]["answer"] in page,
           "P1 pricing/gate decision faces stay [needs-CEO] "
           "approval-only (verdict line + gap-2 answer rendered "
           "from data, zero execution)")
    record("AC-FD7d",
           data["blocked_note_2"] in page
           and page.count('class="card"') >= 8,
           "CEO-physicals blocked note rendered honest (merchant "
           "IDs / server family / platform accounts = blocked, no "
           "fake-online, no nagging)")
    record("AC-FD7e",
           all(marker in page for marker in (
               "City Live", "Business-day Journey", "Lobby Face",
               "Pay Face", "Membership Face", "Minor Guardian Face",
               "Quality Face", data["milestones"][0]["m"])),
           "prior v0.1..v0.6 faces all still mounted + M1 milestone "
           "bite-row visible (live page zero-regression check)")


def ac_fd8_citymodel_card():
    """R945 frontdoor v0.8 citymodel scenario card mount (criteria
    AC-FD8a..e were pre-registered in the R945 backlog row before
    this code existed; AC-FD8f receipt = state log line + backlog
    done mark + commit). The model is src/sandbox/citymodel/
    scenario.py (R850 dual-track scenario, audit P-2026-10-02-02
    L76 "pricing model = zero on file" answered by a runnable
    face); the card runs the REAL module in-process at render time
    with the caller-supplied probe params from the data file --
    the model computes, never decides; pricing stays [needs-CEO]."""
    _sandbox = os.path.normpath(os.path.join(BASE, ".."))
    if _sandbox not in sys.path:
        sys.path.insert(0, _sandbox)
    _cm = os.path.normpath(os.path.join(BASE, "..", "citymodel"))
    if _cm not in sys.path:
        sys.path.insert(0, _cm)
    import frontdoor  # noqa: E402 (sandbox root, journey at import)
    import scenario as CM  # noqa: E402 (citymodel product)

    data = frontdoor.CM_PROBE
    params, months = data["params"], int(data["months"])
    record("AC-FD8a",
           tuple(params["track_b"]["tier_prices"]) == CM.TIER_PRICES
           and months == 12 and len(data["compliance"]) == 4
           and len(data["price_steps"]) >= 3
           and float(data["fixed_cost"]) > 0,
           "probe data integrity: track_b band == scenario.TIER_PRICES"
           " (in-canon 9.9/19.9/29.9, C-20260927-01 case A), months=%d,"
           " compliance 4-piece, %d price steps, fixed_cost>0"
           % (months, len(data["price_steps"])))

    fa = CM.project_track_a(params, months)
    fb = CM.project_track_b(params, months)
    grid = CM.sensitivity_grid(params, months, data["price_steps"])
    be = CM.breakeven_month(fa, data["fixed_cost"])
    report = CM.render_report(params, months)
    page = frontdoor.render().decode("utf-8")

    nums = (["%.2f" % fa["gross_total"], "%.2f" % fb["mrr_total"],
             "%.2f" % round(fa["gross_total"] + fb["mrr_total"], 2),
             ("month %d" % be) if be else "none"]
            + ["%.2f" % g["gross_total"] for g in grid])
    record("AC-FD8b", all(n in page for n in nums),
           "rendered KPIs + breakeven + %d sensitivity totals equal "
           "a fresh in-process model recompute (%d numbers, zero "
           "canned)" % (len(grid), len(nums)))

    rep_html = html.escape(report.rstrip("\n"), quote=True)
    record("AC-FD8c", rep_html in page,
           "deterministic render_report block mounted byte-identical "
           "under the HTML-escape lens (%d chars, same inputs -> "
           "same text)" % len(rep_html))

    old_units = params["track_a"]["units_per_month"]
    try:
        params["track_a"]["units_per_month"] = old_units + 7
        page2 = frontdoor.render().decode("utf-8")
        fa2 = CM.project_track_a(params, months)
        rep2_html = html.escape(
            CM.render_report(params, months).rstrip("\n"), quote=True)
        record("AC-FD8b",
               ("%.2f" % fa2["gross_total"]) in page2
               and ("%.2f" % fa["gross_total"]) not in page2
               and rep_html not in page2 and rep2_html in page2,
               "probe param flip re-render flips every rendered "
               "number + the report block (live-compute control, "
               "AC-W8 pattern): track A gross %.2f -> %.2f"
               % (fa["gross_total"], fa2["gross_total"]))
    finally:
        params["track_a"]["units_per_month"] = old_units

    for needle in ("AI-GENERATED LABEL", "NON-INVESTMENT-ADVISORY",
                   "[needs-CEO]", "msgSecCheck"):
        record("AC-FD8d", needle in page,
               "scenario card carries %r (compliance four-piece)"
               % needle)
    compl_rendered = [data["card_title"], data["probe_note"],
                      data["tail_note"]] \
        + [c["text"] for c in data["compliance"]]
    record("AC-FD8d",
           all(html.escape(s, quote=True) in page
               for s in compl_rendered),
           "Chinese compliance four-piece + probe-declaration + "
           "blocked note rendered from the data file (%d strings, "
           "escape-aware compare; P1 pricing approval-only, zero "
           "execution)" % len(compl_rendered))

    with open(frontdoor.__file__, "rb") as fh:
        src = fh.read()
    record("AC-FD8e", max(src) < 0x80,
           "frontdoor.py stays pure ASCII: zero hardcoded business "
           "copy, all Chinese lives in data files (%d bytes checked)"
           % len(src))
    record("AC-FD8e",
           page.count('class="card"') >= 9
           and all(marker in page for marker in (
               "City Live", "Business-day Journey", "Lobby Face",
               "Pay Face", "Membership Face", "Minor Guardian Face",
               "Quality Face")),
           "prior v0.1..v0.7 faces all still mounted + scenario card "
           "in place (%d cards, live page zero-regression check)"
           % page.count('class="card"'))


def ac_fd9_publishing_card():
    """R946 frontdoor v0.9 publishing-research card mount (criteria
    AC-FD9a..f were pre-registered in the R946 backlog row before
    this code existed; AC-FD9f receipt = state log line + backlog
    done mark + commit). The canon is the same-window research piece
    docs/research/R-20261002-publishing-face-research.md answering
    the audit P-2026-10-02-02 P2-9 residual three faces (Steam store
    page / demo strategy / workshop ecosystem); the card data file is
    extracted verbatim from it and this suite gates the sync
    string-by-string. frontdoor.py must stay pure ASCII so no
    business copy can hide in code."""
    _sandbox = os.path.normpath(os.path.join(BASE, ".."))
    if _sandbox not in sys.path:
        sys.path.insert(0, _sandbox)
    import frontdoor  # noqa: E402 (sandbox root, journey runs at import)
    data = load_json(frontdoor.PB_JSON)
    faces, decs = data["faces"], data["decisions"]
    compl = data["compliance"]
    record("AC-FD9a",
           len(faces) == 3 and len(decs) == 4 and len(compl) == 4
           and len(data["decision_headers"]) == 2,
           "data file carries 3 research faces + 4 decision rows + "
           "2 table headers + 4 compliance items")
    canon_path = os.path.join(frontdoor.ROOT, "docs", "research",
                              "R-20261002-publishing-face-research.md")
    with open(canon_path, encoding="utf-8") as fh:
        canon = fh.read()
    # presentation-only markers are stripped mechanically: bold
    # markers, inline code backticks and per-line md/quote prefixes
    canon_norm = canon.replace("**", "").replace("`", "")
    canon_norm = "\n".join(
        re.sub(r"^(?:> |#+ )+", "", ln) for ln in canon_norm.split("\n"))
    # canon self-gate: pre-registration + compliance four-piece in
    # the research canon itself (AC-FD9a research-side face)
    for needle in ("AC-FD9a..f", "AIGC", "msgSecCheck",
                   "[needs-CEO]"):
        record("AC-FD9a", needle in canon_norm,
               "research canon carries %r (pre-registration + "
               "compliance four-piece on file)" % needle)
    extracted = [data["card_title"], data["source_note"],
                 data["honest_note"], data["decision_title"],
                 data["compliance_title"], data["blocked_note"]]
    extracted += data["decision_headers"]
    extracted += [s for f in faces for s in [f["name"]] + f["blocks"]]
    extracted += [s for d in decs for s in (d["m"], d["status"])]
    extracted += [s for c in compl for s in (c["name"], c["text"])]
    missing = [s for s in extracted if s not in canon_norm]
    record("AC-FD9b", not missing,
           "every extracted string verbatim-synced with the research "
           "canon (bold/backtick/heading-quote-normalized, mechanical "
           "drift gate, %d strings, missing=%d)"
           % (len(extracted), len(missing)))

    page = frontdoor.render().decode("utf-8")

    def on_page(s):
        return html.escape(s, quote=True) in page

    rendered = [data["card_title"], data["source_note"],
                data["honest_note"], data["decision_title"],
                data["compliance_title"], data["blocked_note"]]
    rendered += [s for f in faces for s in [f["name"]] + f["blocks"]]
    rendered += [s for d in decs for s in (d["m"], d["status"])]
    rendered += [c["text"] for c in compl]
    record("AC-FD9c",
           all(on_page(s) for s in rendered),
           "card title + source/honest notes + 3 faces with all "
           "blocks + 4 decision rows + compliance texts + blocked "
           "note all rendered from the data file (%d strings, "
           "HTML-escape-aware compare)" % len(rendered))
    with open(frontdoor.__file__, "rb") as fh:
        src = fh.read()
    record("AC-FD9c", max(src) < 0x80,
           "frontdoor.py stays pure ASCII: zero hardcoded business "
           "copy, all Chinese lives in data files (%d bytes checked)"
           % len(src))
    record("AC-FD9d",
           page.count("[needs-CEO]") >= 2
           and sum(1 for d in decs if d["status"] == "[needs-CEO] 呈批") == 2
           and sum(1 for d in decs if "blocked" in d["status"]) == 2
           and on_page(data["blocked_note"]),
           "P1 publish/listing decisions stay [needs-CEO] "
           "approval-only (2 approval rows + 2 CEO-physical blocked "
           "rows rendered from data, zero execution, honest blocked "
           "face, no fake-online)")
    for needle in ("AI-GENERATED LABEL", "NON-INVESTMENT-ADVISORY",
                   "[needs-CEO]", "msgSecCheck"):
        record("AC-FD9e", needle in page,
               "publishing card page carries %r (compliance "
               "four-piece live on the page)" % needle)
    record("AC-FD9e",
           all(on_page(c["text"]) for c in compl),
           "Chinese compliance four-piece rendered from the data "
           "file (%d strings, escape-aware compare)"
           % len(compl))
    record("AC-FD9c",
           page.count('class="card"') >= 10
           and all(marker in page for marker in (
               "City Live", "Business-day Journey", "Lobby Face",
               "Pay Face", "Membership Face", "Minor Guardian Face",
               "Quality Face")),
           "prior v0.1..v0.8 faces all still mounted + publishing "
           "card in place (%d cards, live page zero-regression "
           "check)" % page.count('class="card"'))


def main():
    print("=== MinorGuard wiring suite (R939/R940/R940b/R942/R943/R945/R946) ===",
          flush=True)
    ac_w1_w2_liveroom()
    ac_w2_w3_pay()
    ac_w2_w4_member()
    ac_w7_pay_grant_commit()
    ac_w8_frontdoor_card()
    ac_fd6_m1_walk_card()
    ac_fd7_city_commerce_card()
    ac_fd8_citymodel_card()
    ac_fd9_publishing_card()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE PASS %d/%d" % (len(RESULTS) - len(failed), len(RESULTS)),
          flush=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
