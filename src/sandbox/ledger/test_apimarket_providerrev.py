"""Acceptance suite for the provider identity revision leg (BigDomain
R2136; canon = the R2136 explore-queue row, criteria AC-AMPV1..AC-AMPV8
registered there BEFORE this code existed - honesty law; the AC-AMPV
prefix, revise_provider, apimarket_provider_revisions,
api_provider_history, E_AM_PROVIDER_UNCHANGED,
E_AM_PROVIDER_UNREGISTERED, this suite name and the
ledger-apimarket-providerrev runner label were all git grep -F
zero-occupancy anchored 2026-10-26, rc=1).

Product under proof: register_provider is write-once per developer (one
row behind UNIQUE(dev_account), no update and no delete surface) while
the unified social credit code is the disclosure field the public layer
publishes verbatim - so one wrong character at registration was a
permanent mis-disclosure with no remedy. Price (R2079), metadata
(R2083), supply (R2095) and rating (R2094) each had the same dead end
and each got a revision leg; this is the provider identity leg.

Criteria:
  AC-AMPV1 Append-only and partial edit: exactly one revision row per
    call carrying the previous and the new pair, omitted fields carry
    the current effective value, and the base provider row (name, code,
    registered_utc) is never rewritten.
  AC-AMPV2 Pinned gate order, fail-closed: account shape, then
    registration existence, then field shape, then no-change; the whole
    family writes zero rows and moves zero tokens.
  AC-AMPV3 No-change judged against the effective value: A -> B -> A is
    legal (the third call differs from the effective value) while an
    identical consecutive call is refused with E_AM_PROVIDER_UNCHANGED
    and the first stamp is never rewritten.
  AC-AMPV4 One seam, unchanged shape: api_provider_identity and
    api_public_listings both read provider_name/credit_code through
    _provider_state, their key sets are exactly what they were before
    this axis, and a provider with zero revisions reports its base pair.
  AC-AMPV5 History face: eleven keys, revisions ordered by revision_id,
    base pair versus effective pair separated, honest empty envelope for
    an in-shape unregistered account.
  AC-AMPV6 Pure read and reconciliation: repeat calls byte-identical,
    the provider faces move zero tokens, and every table digest is
    frozen around them.
  AC-AMPV7 Public display linkage: after a revision the seller's live
    listing rows show the new name and code immediately, disclosure_ok
    unchanged, review state and every other row key unchanged.
  AC-AMPV8 Cross-restart identity + wiring: three instances byte
    identical for identity, history and public snapshots, and the
    runner label is registered in reconcile_all.

Usage: python test_apimarket_providerrev.py
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

REVISION_KEYS = {"revision_id", "dev_account", "previous_provider_name",
                 "previous_credit_code", "provider_name",
                 "credit_code", "revised_utc"}

HISTORY_KEYS = {"dev_account", "registered", "provider_name",
                "credit_code", "base_provider_name",
                "base_credit_code", "registered_utc", "revision_count",
                "latest_revised_utc", "disclaimer", "revisions"}

IDENTITY_KEYS = {"dev_account", "registered", "provider_name",
                 "credit_code", "registered_utc", "disclosure_ok",
                 "disclaimer"}

PUBLIC_ROW_KEYS = {"listing_id", "dev_account", "listing_key", "title",
                   "token_price", "ai_label", "listed_utc",
                   "provider_name", "credit_code", "disclosure_ok",
                   "review_state", "review_reason", "reviewed_utc"}

BAD_ACCOUNTS = ["", None, "   ", 123, "dana"]

BAD_NAMES = [5, "", "   ", "x" * 121]

BAD_CODES = [7, "", "   ", "9" * 65]

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers",
          "apimarket_provider_revisions", "apimarket_reviews",
          "apimarket_review_resubmits", "apimarket_claims",
          "apimarket_claim_responses", "apimarket_claim_withdrawals")


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
    return len(rows), hashlib.sha256(
        repr(rows).encode("utf-8")).hexdigest()


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


def code_of(exc):
    return getattr(exc, "code", None)


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


def public_snapshot(am):
    """Byte-stable snapshot of the public display layer."""
    return dumps(am.api_public_listings())


def face_snapshot(am, accounts):
    """Byte-stable snapshot of the identity and history faces."""
    out = {}
    for account in accounts:
        out["identity|" + account] = dumps(
            am.api_provider_identity(account))
        out["history|" + account] = dumps(
            am.api_provider_history(account))
    return out


def seed_world(led, dk, am):
    """dana and fred are registered providers with one live listing
    each; gina is an in-shape developer who never registered."""
    led.mint_to_pool("pool:reserve", 4000, "SETTLE-AMPV-A",
                     "settlement")
    led.mint_to_pool("pool:share", 4000, "SETTLE-AMPV-S",
                     "settlement")
    for who in ("dana", "fred", "gina"):
        dk.issue_key("usr:" + who, who + "-key", 10, ["backtest"],
                     False)
    dana = am.register_provider("usr:dana", "Dana Data Lab",
                                "91310000MA1K000001")
    fred = am.register_provider("usr:fred", "Fred Feed Works",
                                "91310000MA1K000002")
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="backtest")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 4,
                        True)["listing_id"]
    f1 = am.publish_api("usr:fred", "fred-feed", "Fred Feed API",
                        "fred data feed", PAYLOAD, 6,
                        False)["listing_id"]
    return {"dana": dana, "fred": fred,
            "listings": {"d1": d1, "d2": d2, "f1": f1}}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-providerrev-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    world = seed_world(led, dk, am)
    lids = world["listings"]

    tx_before = ledger_tx_ids(led)

    # -- AC-AMPV1 append-only and partial edit --------------------------
    reg_before = am.api_provider_identity("usr:dana")
    r1 = am.revise_provider("usr:dana",
                            provider_name="Dana Data Lab II")
    r2 = am.revise_provider("usr:dana", credit_code="91310000MA1K000009")
    idv = am.api_provider_identity("usr:dana")
    hist = am.api_provider_history("usr:dana")
    ok1 = (set(r1.keys()) == REVISION_KEYS
           and r1["previous_provider_name"] == "Dana Data Lab"
           and r1["previous_credit_code"] == "91310000MA1K000001"
           and r1["provider_name"] == "Dana Data Lab II"
           and r1["credit_code"] == "91310000MA1K000001"
           and r2["previous_provider_name"] == "Dana Data Lab II"
           and r2["previous_credit_code"] == "91310000MA1K000001"
           and r2["provider_name"] == "Dana Data Lab II"
           and r2["credit_code"] == "91310000MA1K000009"
           and r2["revision_id"] == r1["revision_id"] + 1
           and idv["provider_name"] == "Dana Data Lab II"
           and idv["credit_code"] == "91310000MA1K000009"
           and idv["registered_utc"] == reg_before["registered_utc"]
           and hist["base_provider_name"] == "Dana Data Lab"
           and hist["base_credit_code"] == "91310000MA1K000001"
           and hist["registered_utc"] == reg_before["registered_utc"]
           and hist["revision_count"] == 2
           and len(hist["revisions"]) == 2)
    record("AC-AMPV1", ok1,
           "rev1=%r rev2=%r effective=%r/%r base=%r revision_count=%r"
           % ((r1["provider_name"], r1["credit_code"]),
              (r2["provider_name"], r2["credit_code"]),
              idv["provider_name"], idv["credit_code"],
              hist["base_provider_name"], hist["revision_count"]))

    # -- AC-AMPV2 pinned gate order, fail-closed -----------------------
    dig2 = market_digests(am)
    bad_acct = []
    for form in BAD_ACCOUNTS:
        try:
            am.revise_provider(form, provider_name="X")
            bad_acct.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_acct.append(code_of(exc))
    bad_name = []
    for form in BAD_NAMES:
        try:
            am.revise_provider("usr:fred", provider_name=form)
            bad_name.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_name.append(code_of(exc))
    bad_code = []
    for form in BAD_CODES:
        try:
            am.revise_provider("usr:fred", credit_code=form)
            bad_code.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_code.append(code_of(exc))
    empty_call = []
    try:
        am.revise_provider("usr:fred")
        empty_call.append("NO-RAISE")
    except A.ApiMarketError as exc:
        empty_call.append(code_of(exc))
    ordered = []
    for account, name in (("usr:gina", ""),
                          ("usr:gina", "Gina Labs")):
        try:
            am.revise_provider(account, provider_name=name)
            ordered.append("NO-RAISE")
        except A.ApiMarketError as exc:
            ordered.append(code_of(exc))
    try:
        am.revise_provider("gina", provider_name="")
        ordered.append("NO-RAISE")
    except A.ApiMarketError as exc:
        ordered.append(code_of(exc))
    dig2_after = market_digests(am)
    ok2 = (bad_acct == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and bad_name == ["E_AM_BAD_PROVIDER"] * len(BAD_NAMES)
           and bad_code == ["E_AM_BAD_PROVIDER"] * len(BAD_CODES)
           and empty_call == ["E_AM_BAD_PROVIDER"]
           and ordered == ["E_AM_PROVIDER_UNREGISTERED",
                           "E_AM_PROVIDER_UNREGISTERED",
                           "E_AM_BAD_ACCOUNT"]
           and dig2_after == dig2)
    record("AC-AMPV2", ok2,
           "accounts=%r names=%r codes=%r empty=%r order=%r frozen=%r"
           % (bad_acct, bad_name, bad_code, empty_call, ordered,
              dig2_after == dig2))

    # -- AC-AMPV3 no-change against the effective value -----------------
    dig3 = market_digests(am)
    unchanged = []
    for kwargs in ({"provider_name": "Dana Data Lab II"},
                   {"credit_code": "91310000MA1K000009"},
                   {"provider_name": "Dana Data Lab II",
                    "credit_code": "91310000MA1K000009"}):
        try:
            am.revise_provider("usr:dana", **kwargs)
            unchanged.append("NO-RAISE")
        except A.ApiMarketError as exc:
            unchanged.append(code_of(exc))
    hist3a = am.api_provider_history("usr:dana")
    back = am.revise_provider("usr:dana", provider_name="Dana Data Lab")
    hist3b = am.api_provider_history("usr:dana")
    again = []
    try:
        am.revise_provider("usr:dana", provider_name="Dana Data Lab")
        again.append("NO-RAISE")
    except A.ApiMarketError as exc:
        again.append(code_of(exc))
    dig3_after = market_digests(am)
    ok3 = (unchanged == ["E_AM_PROVIDER_UNCHANGED"] * 3
           and hist3a["revision_count"] == 2
           and hist3a["revisions"][0]["provider_name"] == "Dana Data Lab II"
           and back["previous_provider_name"] == "Dana Data Lab II"
           and back["provider_name"] == "Dana Data Lab"
           and hist3b["revision_count"] == 3
           and hist3b["provider_name"] == "Dana Data Lab"
           and hist3b["base_provider_name"] == "Dana Data Lab"
           and again == ["E_AM_PROVIDER_UNCHANGED"]
           and dig3_after != dig3)
    record("AC-AMPV3", ok3,
           "unchanged=%r count before=%r after=%r revise-back=%r"
           " again=%r"
           % (unchanged, hist3a["revision_count"],
              hist3b["revision_count"],
              (back["previous_provider_name"], back["provider_name"]),
              again))

    # -- AC-AMPV4 one seam, unchanged shape -----------------------------
    fred = am.api_provider_identity("usr:fred")
    gina = am.api_provider_identity("usr:gina")
    gina_hist = am.api_provider_history("usr:gina")
    pub = am.api_public_listings()
    rows = {r["listing_id"]: r for r in pub["listings"]}
    ok4 = (set(am.api_provider_identity("usr:dana").keys())
           == IDENTITY_KEYS
           and set(fred.keys()) == IDENTITY_KEYS
           and set(gina.keys()) == IDENTITY_KEYS
           and fred["provider_name"] == "Fred Feed Works"
           and fred["credit_code"] == "91310000MA1K000002"
           and fred["disclosure_ok"] is True
           and gina["registered"] is False
           and gina["provider_name"] is None
           and gina["disclosure_ok"] is False
           and gina_hist["registered"] is False
           and gina_hist["revisions"] == []
           and all(set(r.keys()) == PUBLIC_ROW_KEYS
                   for r in pub["listings"])
           and rows[lids["f1"]]["provider_name"] == "Fred Feed Works")
    record("AC-AMPV4", ok4,
           "identity keys=%r fred=%r gina=%r public row keys=%r"
           % (set(fred.keys()) == IDENTITY_KEYS,
              (fred["provider_name"], fred["credit_code"]),
              (gina["registered"], gina["provider_name"]),
              all(set(r.keys()) == PUBLIC_ROW_KEYS
                  for r in pub["listings"])))

    # -- AC-AMPV5 history face ------------------------------------------
    hist5 = am.api_provider_history("usr:dana")
    chain = [(r["previous_provider_name"], r["provider_name"],
              r["previous_credit_code"], r["credit_code"])
             for r in hist5["revisions"]]
    ids = [r["revision_id"] for r in hist5["revisions"]]
    ok5 = (set(hist5.keys()) == HISTORY_KEYS
           and hist5["disclaimer"] == DISCLAIMER
           and hist5["registered"] is True
           and hist5["revision_count"] == len(hist5["revisions"]) == 3
           and ids == sorted(ids)
           and chain[0][:2] == ("Dana Data Lab", "Dana Data Lab II")
           and chain[1][2:] == ("91310000MA1K000001",
                                "91310000MA1K000009")
           and chain[2][:2] == ("Dana Data Lab II", "Dana Data Lab")
           and hist5["latest_revised_utc"]
           == hist5["revisions"][-1]["revised_utc"]
           and hist5["provider_name"] == "Dana Data Lab"
           and hist5["base_provider_name"] == "Dana Data Lab")
    record("AC-AMPV5", ok5,
           "keys=%r counted=%r ids=%r chain=%r latest=%r"
           % (set(hist5.keys()) == HISTORY_KEYS,
              (hist5["revision_count"], len(hist5["revisions"])),
              ids, chain,
              hist5["latest_revised_utc"]
              == hist5["revisions"][-1]["revised_utc"]))

    # -- AC-AMPV6 pure read and reconciliation --------------------------
    dig6 = market_digests(am)
    tx6 = ledger_tx_ids(led)
    accounts = ["usr:dana", "usr:fred", "usr:gina"]
    snap_a = face_snapshot(am, accounts)
    snap_b = face_snapshot(am, accounts)
    pub_a = public_snapshot(am)
    pub_b = public_snapshot(am)
    dig6_after = market_digests(am)
    tx6_after = ledger_tx_ids(led)
    ok6 = (snap_a == snap_b and pub_a == pub_b
           and dig6_after == dig6 and tx6_after == tx6)
    record("AC-AMPV6", ok6,
           "faces repeat identical=%r public repeat identical=%r"
           " digests frozen=%r tx frozen=%r"
           % (snap_a == snap_b, pub_a == pub_b,
              dig6_after == dig6, tx6_after == tx6))

    # -- AC-AMPV7 public display linkage -------------------------------
    before = {r["listing_id"]: dict(r)
              for r in am.api_public_listings()["listings"]}
    am.revise_provider("usr:dana", provider_name="Dana Data Lab Final",
                       credit_code="91310000MA1K000077")
    after_env = am.api_public_listings()
    after = {r["listing_id"]: dict(r) for r in after_env["listings"]}
    dana_ids = [lids["d1"], lids["d2"]]
    unchanged_other = True
    for lid in dana_ids:
        strip_b = dict(before[lid])
        strip_a = dict(after[lid])
        strip_b.pop("provider_name")
        strip_b.pop("credit_code")
        strip_a.pop("provider_name")
        strip_a.pop("credit_code")
        if dumps(strip_b) != dumps(strip_a):
            unchanged_other = False
    fred_untouched = (dumps(before[lids["f1"]])
                      == dumps(after[lids["f1"]]))
    ok7 = (all(after[lid]["provider_name"] == "Dana Data Lab Final"
               and after[lid]["credit_code"] == "91310000MA1K000077"
               and after[lid]["disclosure_ok"] is True
               for lid in dana_ids)
           and all(r["listing_id"] not in dana_ids
                   or r["provider_name"] == "Dana Data Lab Final"
                   for r in after_env["listings"])
           and unchanged_other and fred_untouched
           and before[lids["d1"]]["provider_name"]
           != after[lids["d1"]]["provider_name"])
    record("AC-AMPV7", ok7,
           "dana rows=%r other keys stable=%r fred untouched=%r"
           % ([(after[lid]["provider_name"],
                after[lid]["credit_code"]) for lid in dana_ids],
              unchanged_other, fred_untouched))

    # -- AC-AMPV8 cross-restart identity + wiring -----------------------
    accounts8 = ["usr:dana", "usr:fred", "usr:gina"]
    one = (face_snapshot(am, accounts8), public_snapshot(am))
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = (face_snapshot(am2, accounts8), public_snapshot(am2))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = (face_snapshot(am3, accounts8), public_snapshot(am3))
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-providerrev" in handle.read()
    ok8 = (one == two == three and wired)
    record("AC-AMPV8", ok8,
           "instance1==2==3=%r runner wiring=%r"
           % (one == two == three, wired))

    # -- hygiene --------------------------------------------------------
    shas_after = {q: sha_file(q) for q in PRODUCT_FILES}
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
    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("HYGIENE: consumer shas stable=%r suite ascii=%r"
          " network imports=%d"
          % (shas_before == shas_after, ascii_ok, len(net_imports)))
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8
                 and shas_before == shas_after and ascii_ok
                 and not net_imports) else 1


if __name__ == "__main__":
    sys.exit(main())