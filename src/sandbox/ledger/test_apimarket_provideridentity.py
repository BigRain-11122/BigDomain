"""Acceptance suite for the apimarket distribution-duty faces
(BigDomain R2124; canon = the explore-queue row seeded and claimed in
R2124, criteria AC-AMPI1..AC-AMPI8 registered there BEFORE this suite
existed - honesty law; the ten anchors AC-AMPI, register_provider,
api_provider_identity, api_public_listings, review_listing,
api_review_queue, apimarket_providers, apimarket_reviews,
ledger-apimarket-provideridentity and test_apimarket_provideridentity
were all git-grep -F zero-occupancy anchored 2026-10-25, rc=1).

Faces under proof: register_provider + api_provider_identity (real-name
layer), api_public_listings (public display layer), review_listing +
api_review_queue (review refusal layer). R2123 research found that the
marketplace identifies a seller by a bare dev_account string and that
the distribution-platform duty face had no product surface at all.

This suite pins:
  - the registration contract (trimmed, one row per developer);
  - the gate order and fail-closed behaviour of every refusal;
  - the honest empty identity of an unregistered developer;
  - the public display layer (registered identity shown, unregistered
    shown honestly, review state, retired shelves excluded);
  - the review gate (approve/refuse, reason on refusal, single row);
  - the pending queue arithmetic and its agreement with the public face;
  - pure-read law (17 frozen tables, constant ledger tx set) and
    cross-restart byte identity;
  - runner wiring and suite hygiene.

Usage: python test_apimarket_provideridentity.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

PROVIDER_KEYS = {"dev_account", "provider_name", "credit_code",
                 "registered_utc"}

IDENTITY_KEYS = {"dev_account", "registered", "provider_name",
                 "credit_code", "registered_utc", "disclosure_ok",
                 "disclaimer"}

PUBLIC_KEYS = {"listing_id", "dev_account", "listing_key", "title",
               "token_price", "ai_label", "listed_utc",
               "provider_name", "credit_code", "disclosure_ok",
               "review_state", "review_reason", "reviewed_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers",
          "apimarket_reviews")


class Clock(object):
    """Single mutable stamp behind A._now_utc."""

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


def expect_error(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return None


def seed_world(led, dk, am, clock):
    """Two developers (dana registered later, erin deliberately left
    unregistered so the honest-disclosure branch is provable)."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-PI-A", "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-PI-S", "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)
    clock.set("2026-10-25T08:00:00Z")
    ids = {}
    ids["alpha"] = am.publish_api("usr:dana", "alpha", "Service Alpha",
                                  "service payload alpha", PAYLOAD,
                                  10, False)["listing_id"]
    clock.set("2026-10-25T08:05:00Z")
    ids["beta"] = am.publish_api("usr:dana", "beta", "Service Beta",
                                 "service payload beta", PAYLOAD,
                                 8, False)["listing_id"]
    clock.set("2026-10-25T08:10:00Z")
    ids["zeta"] = am.publish_api("usr:erin", "zeta", "Service Zeta",
                                 "service payload zeta", PAYLOAD,
                                 7, False)["listing_id"]
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="ampi-")
    db_path = os.path.join(tmp, "provider.db")
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

        # -- AC-AMPI1 registration contract -------------------------
        clock.set("2026-10-25T09:00:00Z")
        reg = am.register_provider("usr:dana", "  Dana Labs  ",
                                   " 91310000MA1K3XYZ12 ")
        conn = sqlite3.connect(am.db_path)
        rows = conn.execute(
            "SELECT dev_account, provider_name, credit_code,"
            " registered_utc FROM apimarket_providers").fetchall()
        conn.close()
        ok1 = (set(reg.keys()) == PROVIDER_KEYS
               and reg["provider_name"] == "Dana Labs"
               and reg["credit_code"] == "91310000MA1K3XYZ12"
               and reg["registered_utc"] == "2026-10-25T09:00:00Z"
               and len(rows) == 1 and rows[0][0] == "usr:dana")
        record("AC-AMPI1", ok1,
               "keys=%r name=%r code=%r rows=%d"
               % (sorted(reg.keys()), reg["provider_name"],
                  reg["credit_code"], len(rows)))

        # -- AC-AMPI2 gate order, fail-closed -----------------------
        before = market_digests(am)
        before_tx = ledger_tx_ids(led)
        codes = []
        for bad in BAD_ACCOUNTS:
            codes.append(expect_error(am.register_provider, bad,
                                      "Name", "CODE"))
        name_codes = []
        for bad_name in ("", "   ", None):
            name_codes.append(expect_error(am.register_provider,
                                           "usr:erin", bad_name, "CODE"))
        code_codes = []
        for bad_code in ("", "   ", None):
            code_codes.append(expect_error(am.register_provider,
                                           "usr:erin", "Erin Co",
                                           bad_code))
        # order proof: the shape gates must fire before the registry
        # gate, so an unregistered developer with a bad name is a
        # provider-shape refusal, not a not-a-developer refusal.
        order_code = expect_error(am.register_provider, "usr:nobody",
                                  "", "CODE")
        not_dev = expect_error(am.register_provider, "usr:nobody",
                               "Nobody Co", "CODE")
        dup = expect_error(am.register_provider, "usr:dana",
                           "Dana Labs", "91310000MA1K3XYZ12")
        after = market_digests(am)
        after_tx = ledger_tx_ids(led)
        ok2 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
               and name_codes == ["E_AM_BAD_PROVIDER"] * 3
               and code_codes == ["E_AM_BAD_PROVIDER"] * 3
               and order_code == "E_AM_BAD_PROVIDER"
               and not_dev == "E_AM_NOT_DEV"
               and dup == "E_AM_PROVIDER_DUP"
               and before == after and before_tx == after_tx)
        record("AC-AMPI2", ok2,
               "accounts=%r names=%r codes=%r order=%r notdev=%r"
               " dup=%r digests_same=%r tx_same=%r"
               % (set(codes), set(name_codes), set(code_codes),
                  order_code, not_dev, dup, before == after,
                  before_tx == after_tx))

        # -- AC-AMPI3 identity read face ----------------------------
        idv = am.api_provider_identity("usr:dana")
        empty = am.api_provider_identity("usr:erin")
        bad_codes = [expect_error(am.api_provider_identity, bad)
                     for bad in BAD_ACCOUNTS]
        ok3 = (set(idv.keys()) == IDENTITY_KEYS
               and idv["registered"] is True
               and idv["provider_name"] == "Dana Labs"
               and idv["credit_code"] == "91310000MA1K3XYZ12"
               and idv["disclosure_ok"] is True
               and set(empty.keys()) == IDENTITY_KEYS
               and empty["registered"] is False
               and empty["provider_name"] is None
               and empty["credit_code"] is None
               and empty["registered_utc"] is None
               and empty["disclosure_ok"] is False
               and set(bad_codes) == {"E_AM_BAD_ACCOUNT"})
        record("AC-AMPI3", ok3,
               "registered=%r name=%r empty=%r bad=%r"
               % (idv["registered"], idv["provider_name"],
                  empty["registered"], set(bad_codes)))

        # -- AC-AMPI4 public display layer --------------------------
        pub = am.api_public_listings()
        board = am.api_board()
        by_key = {row["listing_key"]: row for row in pub["listings"]}
        ok4a = (pub["listing_count"] == len(board["listings"]) == 3
                and pub["review_pending_count"] == 3
                and pub["disclosure_ok_count"] == 2
                and set(by_key["alpha"].keys()) == PUBLIC_KEYS
                and by_key["alpha"]["provider_name"] == "Dana Labs"
                and by_key["alpha"]["disclosure_ok"] is True
                and by_key["alpha"]["review_state"] == "pending"
                and by_key["zeta"]["provider_name"] is None
                and by_key["zeta"]["disclosure_ok"] is False
                and pub["listings"] == sorted(
                    pub["listings"], key=lambda r: r["listing_id"]))
        clock.set("2026-10-25T09:10:00Z")
        am.review_listing(ids["alpha"], "approve")
        clock.set("2026-10-25T09:20:00Z")
        am.review_listing(ids["beta"], "refuse",
                          "shelf description does not match payload")
        pub2 = am.api_public_listings()
        by_key2 = {row["listing_key"]: row for row in pub2["listings"]}
        clock.set("2026-10-25T09:30:00Z")
        am.delist_api("usr:erin", ids["zeta"])
        pub3 = am.api_public_listings()
        ok4 = (ok4a
               and by_key2["alpha"]["review_state"] == "approved"
               and by_key2["alpha"]["review_reason"] is None
               and by_key2["beta"]["review_state"] == "refused"
               and by_key2["beta"]["review_reason"]
               == "shelf description does not match payload"
               and by_key2["zeta"]["review_state"] == "pending"
               and pub2["review_pending_count"] == 1
               and pub3["listing_count"] == 2
               and all(row["listing_key"] != "zeta"
                       for row in pub3["listings"]))
        record("AC-AMPI4", ok4,
               "count=%d disclosure=%d pending=%r states=%r"
               " retired_excluded=%r"
               % (pub["listing_count"], pub["disclosure_ok_count"],
                  pub2["review_pending_count"],
                  {k: v["review_state"] for k, v in by_key2.items()},
                  pub3["listing_count"] == 2))

        # -- AC-AMPI5 review gate ----------------------------------
        before = market_digests(am)
        before_tx = ledger_tx_ids(led)
        d1 = expect_error(am.review_listing, ids["alpha"], "maybe")
        d2 = expect_error(am.review_listing, ids["alpha"], "refuse",
                          "   ")
        d3 = expect_error(am.review_listing, 999999, "approve")
        d4 = expect_error(am.review_listing, ids["alpha"], "approve")
        mid = market_digests(am)
        mid_tx = ledger_tx_ids(led)
        delta = am.publish_api("usr:dana", "delta", "Service Delta",
                              "service payload delta", PAYLOAD, 5,
                              False)["listing_id"]
        clock.set("2026-10-25T09:40:00Z")
        approved = am.review_listing(delta, "approve")
        after = market_digests(am)
        after_tx = ledger_tx_ids(led)
        ok5 = (d1 == "E_AM_BAD_DECISION"
               and d2 == "E_AM_BAD_REASON"
               and d3 == "E_AM_UNKNOWN_LISTING"
               and d4 == "E_AM_ALREADY_REVIEWED"
               and approved["decision"] == "approve"
               and approved["reason"] == ""
               and before["apimarket_reviews"]
               == mid["apimarket_reviews"]
               and before_tx == mid_tx == after_tx)
        record("AC-AMPI5", ok5,
               "decision=%r reason=%r unknown=%r dup=%r approved=%r"
               " refusals_zero_rows=%r tx_same=%r"
               % (d1, d2, d3, d4, approved["decision"],
                  before["apimarket_reviews"]
                  == mid["apimarket_reviews"], before_tx == after_tx))

        # -- AC-AMPI6 review queue arithmetic ----------------------
        clock.set("2026-10-25T09:50:00Z")
        epsilon = am.publish_api("usr:dana", "epsilon", "Service Eps",
                                 "service payload eps", PAYLOAD, 4,
                                 False)["listing_id"]
        clock.set("2026-10-25T10:00:00Z")
        theta = am.publish_api("usr:erin", "theta", "Service Theta",
                               "service payload theta", PAYLOAD, 3,
                               False)["listing_id"]
        queue = am.api_review_queue()
        pub4 = am.api_public_listings()
        pending_ids = [row["listing_id"] for row in pub4["listings"]
                       if row["review_state"] == "pending"]
        ok6 = (queue["pending_count"] == len(queue["rows"]) == 2
               and [row["listing_id"] for row in queue["rows"]]
               == [epsilon, theta]
               and queue["pending_count"] == pub4["review_pending_count"]
               and set(pending_ids) == {epsilon, theta}
               and all(row["listing_id"] != ids["zeta"]
                       for row in queue["rows"])
               and queue["rows"][0]["token_price"] == 4)
        record("AC-AMPI6", ok6,
               "queue=%r order=%r public_pending=%d"
               % ([row["listing_id"] for row in queue["rows"]],
                  [row["listing_id"] for row in queue["rows"]]
                  == [epsilon, theta], pub4["review_pending_count"]))

        # -- AC-AMPI7 pure read + cross-restart --------------------
        before = market_digests(am)
        before_tx = ledger_tx_ids(led)
        dana_dump = dumps(am.api_provider_identity("usr:dana"))
        erin_dump = dumps(am.api_provider_identity("usr:erin"))
        public_dump = dumps(am.api_public_listings())
        queue_dump = dumps(am.api_review_queue())
        after = market_digests(am)
        after_tx = ledger_tx_ids(led)
        close_stack(am, dk, metered, led)
        seen = []
        for _index in range(3):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            try:
                seen.append((dumps(am2.api_provider_identity("usr:dana")),
                             dumps(am2.api_provider_identity("usr:erin")),
                             dumps(am2.api_public_listings()),
                             dumps(am2.api_review_queue())))
            finally:
                close_stack(am2, dk2, metered2, led2)
        ok7 = (before == after and before_tx == after_tx
               and len(TABLES) == 17
               and seen[0] == seen[1] == seen[2]
               and seen[0] == (dana_dump, erin_dump, public_dump,
                              queue_dump))
        record("AC-AMPI7", ok7,
               "digests_same=%r tx_same=%r tables=%d instances=%r"
               % (before == after, before_tx == after_tx, len(TABLES),
                  seen[0] == seen[1] == seen[2]))

        # -- AC-AMPI8 wiring + hygiene + no publish enforcement ----
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        with open(RECONCILE, "rb") as handle:
            wired = b"ledger-apimarket-provideridentity" in handle.read()
        with open(os.path.abspath(__file__), "rb") as handle:
            blob = handle.read()
        try:
            blob.decode("ascii")
            ascii_ok = True
        except UnicodeDecodeError:
            ascii_ok = False
        src = blob.decode("utf-8", "replace")
        net_imports = [line for line in src.splitlines()
                       if line.strip().startswith(("import requests",
                                                   "import urllib",
                                                   "import http"))]
        # An unregistered seller can still publish: this slice adds the
        # faces but does NOT wire enforcement into publish_api (a
        # deliberate zero-regression choice, disclosed in the queue row).
        final_pub = am.api_public_listings()
        unregistered_publish_ok = any(
            row["listing_key"] == "theta" and not row["disclosure_ok"]
            for row in final_pub["listings"])
        ok8 = (wired and ascii_ok and not net_imports
               and unregistered_publish_ok
               and final_pub["listing_count"] == 5)
        record("AC-AMPI8", ok8,
               "wired=%r ascii=%r net=%d unregistered_publish=%r"
               % (wired, ascii_ok, len(net_imports),
                  unregistered_publish_ok))
    finally:
        A._now_utc = original_now
        try:
            close_stack(am, dk, metered, led)
        except Exception:
            pass

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())