"""Acceptance suite for the apimarket listing metadata revision
face (BigDomain R2083; canon = the explore-queue row seeded and
claimed in R2083, criteria AC-AMME1..AC-AMME8 registered in that
claim note BEFORE this code existed - honesty law; the AC-AMME
prefix, the edit_listing and api_metadata_history names, this suite
name, the ledger-apimarket-metadata runner label, the
apimarket_listing_revisions table and the E_AM_METADATA_UNCHANGED
code were all git-grep -F zero-occupancy anchored 2026-10-24,
rc=1).

Face under proof: APIMarketFace.edit_listing and
APIMarketFace.api_metadata_history. publish_api writes title and
description exactly once: after a listing exists there was no
legal way to fix a typo or improve the copy - republishing
collides with UNIQUE(dev_account, listing_key) and delisting is
terminal. Price had revise_price, lifecycle had delist_api,
metadata had nothing. This window pins:

  - the envelope contract and the append-only revision row, with
    the listing row's original metadata never rewritten;
  - partial-edit semantics (an omitted field carries into the new
    revision, every revision stores the full effective pair);
  - the pinned gate order (account, listing, ownership, retired,
    field shape, content gate, no-change) with zero side effects;
  - ownership and existence refusals, plus the documented
    prefix-only account-gate behaviour of this face;
  - the retired-listing refusal while its history stays readable;
  - the no-change refusal with an honest provision for revising
    back to an older value (the comparison is against CURRENT);
  - the effective-metadata law on api_view / api_board /
    api_search (a renamed listing matches only its current title)
    and the new history read face with per-listing isolation;
  - purity (zero token movement), read purity, repeat-call and
    cross-restart byte identity across three instances, plus the
    runner wiring.

Usage: python test_apimarket_metadata.py
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

ENVELOPE_KEYS = {"listing_id", "dev_account", "listing_key",
                 "revision_id", "previous_title",
                 "previous_description", "title", "description",
                 "metadata_revision_count", "revised_utc",
                 "disclaimer"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions")

BASE_TITLE_1 = "Risk Scan API"
BASE_DESC_1 = "portfolio risk scan endpoint"
BASE_TITLE_2 = "Macro Feed API"
BASE_DESC_2 = "daily macro data feed"
BASE_TITLE_3 = "Scan Probe API"
BASE_DESC_3 = "probe endpoint for the scan pipeline"

BANNED_TITLE = "guaranteed returns \u8bc8\u9a97"
BANNED_DESC = "risk free \u8bc8\u9a97 pitch"

BAD_ACCOUNTS = ["bob", "", "usr", None]
BAD_LISTINGS = [0, -1, "1", True, None]


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


def revision_rows(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT revision_id, title, description FROM"
        " apimarket_listing_revisions WHERE listing_id = ?"
        " ORDER BY revision_id", (listing_id,)).fetchall()
    conn.close()
    return rows


def listing_row(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    row = conn.execute(
        "SELECT title, description FROM apimarket_listings"
        " WHERE listing_id = ?", (listing_id,)).fetchone()
    conn.close()
    return row


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def read_family(am, l1, l3):
    return {"view1": dumps(am.api_view(l1)),
            "hist1": dumps(am.api_metadata_history(l1)),
            "hist3": dumps(am.api_metadata_history(l3)),
            "search": dumps(am.api_search()),
            "board": dumps(am.api_board())}


def ids(env):
    return [r["listing_id"] for r in env["listings"]]


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


def seed_world(led, dk, am):
    """Two sellers, three listings. dana: risk-scan (10) and
    macro-feed (3, AIGC); erin: scan-probe (6). bob buys risk-scan
    so the listing carries a purchase aggregate."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMM-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)
    l1 = am.publish_api("usr:dana", "risk-scan", BASE_TITLE_1,
                        BASE_DESC_1, PAYLOAD, 10, False)["listing_id"]
    l2 = am.publish_api("usr:dana", "macro-feed", BASE_TITLE_2,
                        BASE_DESC_2, PAYLOAD, 3, True)["listing_id"]
    l3 = am.publish_api("usr:erin", "scan-probe", BASE_TITLE_3,
                        BASE_DESC_3, PAYLOAD, 6, False)["listing_id"]
    am.purchase_api("usr:bob", l1, "ref-bob-amm")
    return l1, l2, l3


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-metadata-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    l1, l2, l3 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)

    # -- AC-AMME1 envelope + append-only row, base never rewritten --------
    env = am.edit_listing("usr:dana", l1, title="Risk Scan API v2")
    row1 = listing_row(am, l1)
    revs1 = revision_rows(am, l1)
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["listing_id"] == l1
           and env["dev_account"] == "usr:dana"
           and env["listing_key"] == "risk-scan"
           and env["revision_id"] > 0
           and env["previous_title"] == BASE_TITLE_1
           and env["previous_description"] == BASE_DESC_1
           and env["title"] == "Risk Scan API v2"
           and env["description"] == BASE_DESC_1
           and env["metadata_revision_count"] == 1
           and env["revised_utc"] == env["revised_utc"].strip()
           and env["disclaimer"] == DISCLAIMER
           and row1 == (BASE_TITLE_1, BASE_DESC_1)
           and len(revs1) == 1
           and revs1[0][1] == "Risk Scan API v2"
           and revs1[0][2] == BASE_DESC_1)
    record("AC-AMME1", ok1,
           "keys=%r prev=%r new=%r base untouched=%r rows=%d"
           % (set(env.keys()) == ENVELOPE_KEYS,
              (env["previous_title"], env["previous_description"]),
              (env["title"], env["description"]),
              row1 == (BASE_TITLE_1, BASE_DESC_1), len(revs1)))

    # -- AC-AMME2 partial-edit semantics ---------------------------------
    e2 = am.edit_listing("usr:dana", l1,
                         description="risk scan endpoint v2")
    e3 = am.edit_listing("usr:erin", l3, title="Scan Probe API v2")
    revs1b = revision_rows(am, l1)
    revs3 = revision_rows(am, l3)
    ok2 = (e2["title"] == "Risk Scan API v2"
           and e2["description"] == "risk scan endpoint v2"
           and e2["previous_title"] == "Risk Scan API v2"
           and e2["previous_description"] == BASE_DESC_1
           and e2["metadata_revision_count"] == 2
           and revs1b[-1][1:] == ("Risk Scan API v2",
                                  "risk scan endpoint v2")
           and e3["title"] == "Scan Probe API v2"
           and e3["description"] == BASE_DESC_3
           and e3["previous_title"] == BASE_TITLE_3
           and e3["metadata_revision_count"] == 1
           and revs3[-1][1:] == ("Scan Probe API v2", BASE_DESC_3)
           and len(revs1b) == 2 and len(revs3) == 1)
    record("AC-AMME2", ok2,
           "desc-only carries title=%r title-only carries desc=%r"
           " counts=(%d,%d)"
           % (e2["title"], e3["description"], len(revs1b), len(revs3)))

    # -- AC-AMME3 gate order + content pre-gate, zero side effects --------
    dig = market_digests(am)
    view_before = dumps(am.api_view(l1))
    content_codes = []
    for form in ({"title": BANNED_TITLE}, {"description": BANNED_DESC}):
        try:
            am.edit_listing("usr:dana", l1, **form)
            content_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            content_codes.append(code_of(exc))
    probes = [
        (("bob", l1, {}), "E_AM_BAD_ACCOUNT"),
        (("usr:dana", 0, {}), "E_AM_BAD_ARGS"),
        (("usr:dana", 9999, {}), "E_AM_UNKNOWN_LISTING"),
        (("usr:carol", l1, {}), "E_AM_NOT_OWNER"),
        (("usr:dana", l2, {}), "E_AM_BAD_ARGS"),
        (("usr:erin", l3, {"title": 123}), "E_AM_BAD_ARGS"),
        (("usr:erin", l3, {"description": "   "}), "E_AM_BAD_ARGS"),
        (("usr:erin", l3, {"title": BANNED_TITLE}),
         "E_AM_CONTENT_REJECTED"),
        (("usr:erin", l3, {"title": "Scan Probe API v2"}),
         "E_AM_METADATA_UNCHANGED"),
    ]
    order = []
    for args, _expected in probes:
        account, listing, kwargs = args
        try:
            am.edit_listing(account, listing, **kwargs)
            order.append("NO-RAISE")
        except A.ApiMarketError as exc:
            order.append(code_of(exc))
    dig_after = market_digests(am)
    ok3 = (content_codes == ["E_AM_CONTENT_REJECTED"] * 2
           and order == [p[1] for p in probes]
           and dig_after == dig
           and dumps(am.api_view(l1)) == view_before
           and len(revision_rows(am, l1)) == 2
           and len(revision_rows(am, l3)) == 1)
    record("AC-AMME3", ok3,
           "content=%r order=%r digests frozen=%r view frozen=%r"
           % (content_codes, order, dig_after == dig,
              dumps(am.api_view(l1)) == view_before))

    # -- AC-AMME4 ownership / existence / shape forms --------------------
    dig = market_digests(am)
    acct_codes = []
    for form in BAD_ACCOUNTS:
        try:
            am.edit_listing(form, l1, title="x")
            acct_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            acct_codes.append(code_of(exc))
    try:
        am.edit_listing("usr:", l1, title="x")
        prefix_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        prefix_code = code_of(exc)
    list_codes = []
    for form in BAD_LISTINGS:
        try:
            am.edit_listing("usr:dana", form, title="x")
            list_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            list_codes.append(code_of(exc))
    try:
        am.edit_listing("usr:dana", 9999, title="x")
        unknown_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        unknown_code = code_of(exc)
    non_owner_codes = []
    for owner in ("usr:carol", "usr:erin"):
        try:
            am.edit_listing(owner, l1, title="hijack attempt")
            non_owner_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            non_owner_codes.append(code_of(exc))
    ok4 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and prefix_code == "E_AM_NOT_OWNER"
           and list_codes == ["E_AM_BAD_ARGS"] * len(BAD_LISTINGS)
           and unknown_code == "E_AM_UNKNOWN_LISTING"
           and non_owner_codes == ["E_AM_NOT_OWNER"] * 2
           and market_digests(am) == dig
           and listing_row(am, l1) == (BASE_TITLE_1, BASE_DESC_1))
    record("AC-AMME4", ok4,
           "accounts=%r prefix=%r listings=%r unknown=%r owners=%r"
           " frozen=%r"
           % (acct_codes, prefix_code, list_codes, unknown_code,
              non_owner_codes, market_digests(am) == dig))

    # -- AC-AMME5 retired refusal + readable history ---------------------
    stamp2 = am.delist_api("usr:dana", l2)["delisted_utc"]
    try:
        am.edit_listing("usr:dana", l2, title="Macro Feed API v2")
        retired_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        retired_code = code_of(exc)
    hist2 = am.api_metadata_history(l2)
    stamp1 = am.delist_api("usr:dana", l1)["delisted_utc"]
    hist1 = am.api_metadata_history(l1)
    ok5 = (retired_code == "E_AM_DELISTED"
           and hist2["base_title"] == BASE_TITLE_2
           and hist2["base_description"] == BASE_DESC_2
           and hist2["title"] == BASE_TITLE_2
           and hist2["revision_count"] == 0
           and hist2["revisions"] == []
           and hist2["delisted"] is True
           and hist2["delisted_utc"] == stamp2
           and hist1["revision_count"] == 2
           and hist1["title"] == "Risk Scan API v2"
           and hist1["delisted"] is True
           and hist1["delisted_utc"] == stamp1
           and len(hist1["revisions"]) == 2)
    record("AC-AMME5", ok5,
           "retired edit=%r zero-rev history=(%r,%d,%r)"
           " revised-then-retired history=(%r,%d,%r)"
           % (retired_code, hist2["title"], hist2["revision_count"],
              hist2["delisted"], hist1["title"],
              hist1["revision_count"], hist1["delisted"]))

    # -- AC-AMME6 no-change refusal + legal revise-back ------------------
    l1, l2, l3 = l1, l2, l3
    # l1 is retired at this point; re-open the no-change probes on the
    # live listing l3 so the family is testable, and keep l1's history
    # as the revise-back anchor via its recorded effective pair.
    try:
        am.edit_listing("usr:erin", l3, title="Scan Probe API v2",
                        description=BASE_DESC_3)
        same_code = "NO-RAISE"
    except A.ApiMarketError as exc:
        same_code = code_of(exc)
    count_before = len(revision_rows(am, l3))
    back = am.edit_listing("usr:erin", l3, title=BASE_TITLE_3)
    count_after = len(revision_rows(am, l3))
    try:
        am.edit_listing("usr:erin", l3, description=BASE_DESC_3)
        desc_same = "NO-RAISE"
    except A.ApiMarketError as exc:
        desc_same = code_of(exc)
    ok6 = (same_code == "E_AM_METADATA_UNCHANGED"
           and count_before == 1
           and back["title"] == BASE_TITLE_3
           and back["previous_title"] == "Scan Probe API v2"
           and back["metadata_revision_count"] == 2
           and count_after == 2
           and desc_same == "E_AM_METADATA_UNCHANGED"
           and len(revision_rows(am, l3)) == 2)
    record("AC-AMME6", ok6,
           "same=%r desc-same=%r revise-back new=%r prev=%r"
           " rows=%d->%d"
           % (same_code, desc_same, back["title"],
              back["previous_title"], count_before, count_after))

    # -- AC-AMME7 effective metadata on three read faces + history -------
    # l3 currently reads BASE_TITLE_3 again; rename it to a fully
    # distinct title so "old title no longer matches" is unambiguous.
    ren = am.edit_listing("usr:erin", l3, title="Orbit Probe API v2")
    view3 = am.api_view(l3)
    board = am.api_board()
    old_hit = am.api_search(keyword="scan probe")
    new_hit = am.api_search(keyword="orbit")
    hist3 = am.api_metadata_history(l3)
    hist1 = am.api_metadata_history(l1)
    board3 = [r for r in board["listings"]
              if r["listing_id"] == l3][0]
    ok7 = (ren["metadata_revision_count"] == 3
           and view3["title"] == "Orbit Probe API v2"
           and view3["description"] == BASE_DESC_3
           and view3["base_title"] == BASE_TITLE_3
           and view3["base_description"] == BASE_DESC_3
           and view3["metadata_revision_count"] == 3
           and view3["latest_metadata_revision_utc"] == ren["revised_utc"]
           and view3["revision_count"] == 0
           and board3["title"] == "Orbit Probe API v2"
           and old_hit["count"] == 0
           and new_hit["count"] == 1
           and ids(new_hit) == [l3]
           and hist3["base_title"] == BASE_TITLE_3
           and hist3["title"] == "Orbit Probe API v2"
           and hist3["revision_count"] == 3
           and [r["title"] for r in hist3["revisions"]]
           == ["Scan Probe API v2", BASE_TITLE_3,
               "Orbit Probe API v2"]
           and [r["title"] for r in hist1["revisions"]]
           == ["Risk Scan API v2", "Risk Scan API v2"]
           and hist1["revision_count"] == 2)
    record("AC-AMME7", ok7,
           "view=%r/%r base=%r count=%d board=%r old-hit=%d"
           " new-hit=%r hist3=%r hist1 rows=%d"
           % (view3["title"], view3["description"],
              (view3["base_title"], view3["base_description"]),
              view3["metadata_revision_count"], board3["title"],
              old_hit["count"], ids(new_hit),
              [r["title"] for r in hist3["revisions"]],
              len(hist1["revisions"])))

    # -- AC-AMME8 purity, determinism, cross-restart, wiring -------------
    dig_reads = market_digests(am)
    fam_a = read_family(am, l1, l3)
    fam_b = read_family(am, l1, l3)
    dig_after_reads = market_digests(am)
    tx_after = ledger_tx_ids(led)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    fam_c = read_family(am2, l1, l3)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    fam_d = read_family(am3, l1, l3)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-metadata" in handle.read()
    ok8 = (tx_after == tx_before
           and dig_reads == dig_after_reads
           and fam_a == fam_b == fam_c == fam_d
           and wired)
    record("AC-AMME8", ok8,
           "zero tokens=%r reads frozen=%r instance1==2==3==4=%r"
           " wiring=%r"
           % (tx_after == tx_before, dig_reads == dig_after_reads,
              fam_a == fam_b == fam_c == fam_d, wired))

    # -- hygiene ----------------------------------------------------------
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
    hygiene = (shas_before == shas_after
               and ascii_ok
               and not net_imports
               and not os.path.abspath(tmp).startswith(
                   os.path.abspath(os.path.join(BASE, "..", "..",
                                                ".."))))
    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("HYGIENE: consumer shas stable=%r suite ascii=%r"
          " network imports=%d world outside repo=%r"
          % (shas_before == shas_after, ascii_ok, len(net_imports),
             not os.path.abspath(tmp).startswith(
                 os.path.abspath(os.path.join(BASE, "..", "..",
                                              "..")))))
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8 and hygiene) else 1


if __name__ == "__main__":
    sys.exit(main())