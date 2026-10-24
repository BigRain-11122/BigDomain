"""Acceptance suite for the apimarket buyer rating-debt queue
(BigDomain R2105; canon = the explore-queue row seeded and claimed in
R2105, criteria AC-AMBT1..AC-AMBT8 registered there BEFORE this suite
existed - honesty law; the AC-AMBT prefix, api_buyer_todo, the
buyer_todo token, this suite name and the ledger-apimarket-buyertodo
runner label were all git-grep -F zero-occupancy anchored 2026-10-25,
rc=1).

Face under proof: APIMarketFace.api_buyer_todo(buyer_id). R2096 gave
the seller side its unanswered-rating queue (api_seller_inbox) but the
buyer side had nothing: api_library lists every purchase with its own
stars and api_buyer_profile only counts them, so a resident has to
scan the library by eye to find the None rows. This suite pins the
mirror queue:

  - a seven-key envelope and nine-key rows, honest empty envelope for
    a prefix-valid account with no purchases;
  - oldest debt first, byte-identical double runs;
  - duplicate-free by construction: the purchase gate forbids a second
    purchase of the same listing, so a rejected repeat purchase leaves
    the queue byte-identical, and one rating drains its listing;
  - the refund law with pinned precedence rated > refunded > pending,
    so a rating-then-refund row counts as rated;
  - retirement keeps the debt and the live asking price reads through
    the one current-price seam while price_paid stays historical;
  - row conservation (rated + refunded + pending == purchases) and
    strict buyer isolation;
  - cross-restart byte identity on three instances;
  - the account shape gate before any read, frozen table digests and a
    constant ledger tx set (pure read, zero token movement);
  - runner wiring plus suite hygiene (ASCII, no network imports, world
    outside the repo, stable product file shas).

Usage: python test_apimarket_buyertodo.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import metered as M                   # noqa: E402 (R626 product)
import apidev as D                    # noqa: E402 (R1700 registry)
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

ENVELOPE_KEYS = {"buyer_id", "purchase_count", "rated_count",
                 "refunded_count", "pending_count", "disclaimer",
                 "pending"}

ROW_KEYS = {"purchase_id", "listing_id", "listing_key", "title",
            "dev_account", "price_paid", "purchased_utc", "delisted",
            "current_price"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds", "apimarket_supply_revisions")


class Clock(object):
    """Single mutable stamp behind A._now_utc (the R2104 precedent), so
    purchase stamps are pinned and the oldest-debt order is testable
    without sleeping."""

    def __init__(self, stamp):
        self.stamp = stamp

    def now_utc(self):
        return self.stamp

    def set(self, stamp):
        self.stamp = stamp


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dumps(env):
    return json.dumps(env, sort_keys=True)


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in TABLES}
    conn.close()
    return out


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def build_stack(db_path, cfg, lobby_cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    return led, metered, dk, gate, am


def close_stack(am, dk, metered, led):
    am.close()
    dk.close()
    metered.close()
    led.close()


def code_of(exc):
    return getattr(exc, "code", None)


def pending_keys(am, buyer_id):
    return [row["listing_key"]
            for row in am.api_buyer_todo(buyer_id)["pending"]]


def seed_world(led, dk, am, clock):
    """Owner dana publishes seven listings; the world then walks every
    queue state: one plain debt, one rated, one refunded, one more
    plain debt, one retired debt, one rated-then-refunded row, plus a
    second buyer for the isolation check."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BT-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.set("2026-10-25T08:00:00Z")
    ids = {}
    specs = [
        ("alpha", "Service Alpha", 10, None),
        ("beta", "Service Beta", 8, None),
        ("gamma", "Service Gamma", 6, None),
        ("delta", "Service Delta", 5, 1),
        ("epsilon", "Service Epsilon", 7, None),
        ("zeta", "Service Zeta", 4, None),
        ("eta", "Service Eta", 9, None),
    ]
    for key, title, price, supply in specs:
        ids[key] = am.publish_api("usr:dana", key, title,
                                  "service payload " + key, PAYLOAD,
                                  price, False, supply)["listing_id"]
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="ambuyertodo-")
    db_path = os.path.join(tmp, "bt.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock("2026-10-25T08:30:00Z")
    A._now_utc = clock.now_utc
    try:
        ids = seed_world(led, dk, am, clock)

        # purchases land in a scrambled order on purpose: the oldest
        # debt (epsilon) is neither the first nor the last row id.
        clock.set("2026-10-25T09:00:00Z")
        am.purchase_api("usr:bob", ids["epsilon"], "ref-bob-epsilon")
        clock.set("2026-10-25T09:10:00Z")
        am.purchase_api("usr:bob", ids["beta"], "ref-bob-beta")
        am.rate_api("usr:bob", ids["beta"], 5)
        clock.set("2026-10-25T09:20:00Z")
        gamma = am.purchase_api("usr:bob", ids["gamma"],
                                "ref-bob-gamma")["purchase_id"]
        am.refund_api("usr:bob", gamma, "not what I needed")
        clock.set("2026-10-25T09:30:00Z")
        am.purchase_api("usr:bob", ids["delta"], "ref-bob-delta")
        clock.set("2026-10-25T09:50:00Z")
        am.purchase_api("usr:bob", ids["alpha"], "ref-bob-alpha")
        clock.set("2026-10-25T10:00:00Z")
        eta = am.purchase_api("usr:bob", ids["eta"],
                              "ref-bob-eta")["purchase_id"]
        am.rate_api("usr:bob", ids["eta"], 4)
        am.refund_api("usr:bob", eta, "rated then refunded")
        clock.set("2026-10-25T10:10:00Z")
        am.purchase_api("usr:carol", ids["zeta"], "ref-carol-zeta")
        clock.set("2026-10-25T10:20:00Z")
        # the price moves while the listing is still live (a revision
        # on a retired listing is refused by the door), then the
        # listing retires: the queue must keep the debt and keep
        # reading the last live asking price.
        am.revise_price("usr:dana", ids["epsilon"], 11)
        clock.set("2026-10-25T10:30:00Z")
        am.delist_api("usr:dana", ids["epsilon"])

        # -- AC-AMBT1 envelope + shape gate before any read ------------
        pre_gate_digests = market_digests(am)
        pre_gate_tx = ledger_tx_ids(led)
        env = am.api_buyer_todo("usr:bob")
        rows = env["pending"]
        newbie = am.api_buyer_todo("usr:newbie")
        bad_codes = []
        for bad in BAD_ACCOUNTS:
            try:
                am.api_buyer_todo(bad)
                bad_codes.append(None)
            except A.ApiMarketError as exc:
                bad_codes.append(code_of(exc))
        gate_clean = (market_digests(am) == pre_gate_digests
                      and ledger_tx_ids(led) == pre_gate_tx)
        ok1 = (set(env.keys()) == ENVELOPE_KEYS
               and set(newbie.keys()) == ENVELOPE_KEYS
               and all(set(r.keys()) == ROW_KEYS for r in rows)
               and env["disclaimer"] == DISCLAIMER
               and env["buyer_id"] == "usr:bob"
               and newbie["purchase_count"] == 0
               and newbie["pending"] == []
               and newbie["pending_count"] == 0
               and all(code == A.E_AM_BAD_ACCOUNT
                       for code in bad_codes)
               and gate_clean)
        record("AC-AMBT1", ok1,
               "envelope keys=%d row keys=%r bad codes=%r"
               " empty purchases=%d gate wrote nothing=%r"
               % (len(env), sorted(set(len(r) for r in rows)),
                  bad_codes, newbie["purchase_count"], gate_clean))

        # -- AC-AMBT2 row shape + oldest-debt order + double run -------
        first = dumps(am.api_buyer_todo("usr:bob"))
        second = dumps(am.api_buyer_todo("usr:bob"))
        keys = [row["listing_key"] for row in rows]
        ok2 = (keys == ["epsilon", "delta", "alpha"]
               and first == second
               and [row["purchase_id"] for row in rows]
               == sorted(row["purchase_id"] for row in rows)
               and env["pending_count"] == 3)
        record("AC-AMBT2", ok2,
               "order=%r double-run identical=%r row keys=%d"
               % (keys, first == second, len(ROW_KEYS)))

        # -- AC-AMBT3 duplicate-free by construction + rating drains ----
        before = dumps(am.api_buyer_todo("usr:bob"))
        dup_code = None
        try:
            am.purchase_api("usr:bob", ids["delta"], "ref-bob-delta-2")
        except A.ApiMarketError as exc:
            dup_code = code_of(exc)
        after_dup = dumps(am.api_buyer_todo("usr:bob"))
        pre_rate = am.api_buyer_todo("usr:bob")
        am.rate_api("usr:bob", ids["delta"], 3)
        post_rate = am.api_buyer_todo("usr:bob")
        ok3 = (dup_code == A.E_AM_PURCHASE_DUP
               and before == after_dup
               and "delta" not in pending_keys(am, "usr:bob")
               and post_rate["pending_count"] == pre_rate["pending_count"]
               - 1
               and post_rate["rated_count"] == pre_rate["rated_count"]
               + 1
               and post_rate["purchase_count"]
               == pre_rate["purchase_count"])
        record("AC-AMBT3", ok3,
               "repeat purchase code=%r queue unchanged=%r"
               " pending %d->%d rated %d->%d"
               % (dup_code, before == after_dup,
                  pre_rate["pending_count"], post_rate["pending_count"],
                  pre_rate["rated_count"], post_rate["rated_count"]))

        # -- AC-AMBT4 refund law + pinned precedence -------------------
        env = am.api_buyer_todo("usr:bob")
        ok4 = (env["refunded_count"] == 1
               and "gamma" not in pending_keys(am, "usr:bob")
               and "eta" not in pending_keys(am, "usr:bob"))
        record("AC-AMBT4", ok4,
               "refunded=%d gamma pending=%r eta pending=%r"
               % (env["refunded_count"],
                  "gamma" in pending_keys(am, "usr:bob"),
                  "eta" in pending_keys(am, "usr:bob")))

        # -- AC-AMBT5 retirement keeps the debt, live price seam -------
        eps = [row for row in env["pending"]
               if row["listing_key"] == "epsilon"][0]
        ok5 = (eps["delisted"] is True and eps["current_price"] == 11
               and eps["price_paid"] == 7)
        record("AC-AMBT5", ok5,
               "delisted=%r current=%r price_paid=%r"
               % (eps["delisted"], eps["current_price"],
                  eps["price_paid"]))

        # -- AC-AMBT6 conservation + buyer isolation -------------------
        carol = am.api_buyer_todo("usr:carol")
        ok6 = (env["rated_count"] + env["refunded_count"]
               + env["pending_count"] == env["purchase_count"]
               and env["purchase_count"] == 6
               and env["rated_count"] == 3
               and env["pending_count"] == 2
               and carol["purchase_count"] == 1
               and pending_keys(am, "usr:carol") == ["zeta"]
               and "zeta" not in pending_keys(am, "usr:bob")
               and all(row["dev_account"] == "usr:dana"
                       for row in env["pending"]))
        record("AC-AMBT6", ok6,
               "rated=%d refunded=%d pending=%d purchases=%d"
               " carol pending=%r"
               % (env["rated_count"], env["refunded_count"],
                  env["pending_count"], env["purchase_count"],
                  pending_keys(am, "usr:carol")))

        # -- AC-AMBT7 pure read + cross-restart identity ---------------
        mid_digests = market_digests(am)
        mid_tx = ledger_tx_ids(led)
        family_one = {who: dumps(am.api_buyer_todo("usr:" + who))
                      for who in ("bob", "carol", "newbie")}
        after_digests = market_digests(am)
        after_tx = ledger_tx_ids(led)
        family_two = {}
        family_three = {}
        for index in (2, 3):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            try:
                fam = {who: dumps(am2.api_buyer_todo("usr:" + who))
                       for who in ("bob", "carol", "newbie")}
            finally:
                close_stack(am2, dk2, metered2, led2)
            if index == 2:
                family_two = fam
            else:
                family_three = fam
        ok7 = (mid_digests == after_digests and mid_tx == after_tx
               and family_one == family_two == family_three)
        record("AC-AMBT7", ok7,
               "digests stable=%r tx stable=%r instance"
               " 1==2==3=%r"
               % (mid_digests == after_digests, mid_tx == after_tx,
                  family_one == family_two == family_three))

        # -- AC-AMBT8 wiring + hygiene ---------------------------------
        with open(RECONCILE, "rb") as handle:
            wired = b"ledger-apimarket-buyertodo" in handle.read()
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        with open(os.path.abspath(__file__), "rb") as handle:
            blob = handle.read()
        ascii_ok = True
        try:
            blob.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
        src = blob.decode("utf-8", "replace")
        net_imports = [line for line in src.splitlines()
                       if line.strip().startswith(("import requests",
                                                   "import urllib",
                                                   "import http"))]
        outside = not os.path.abspath(tmp).startswith(
            os.path.abspath(os.path.join(BASE, "..", "..", "..")))
        ok8 = (wired and ascii_ok and not net_imports and outside
               and len(shas_after) == len(PRODUCT_FILES))
        record("AC-AMBT8", ok8,
               "runner wiring=%r ascii=%r network imports=%d world"
               " outside repo=%r product shas=%d"
               % (wired, ascii_ok, len(net_imports), outside,
                  len(shas_after)))
    finally:
        A._now_utc = original_now
        close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())