"""Acceptance suite for the market-wide monthly provider-identity
redeclaration timeline (BigDomain R2207; canon = the R2202 seed row in
state/queue/explore.md, criteria AC-PIM1..AC-PIM8 registered in that row
BEFORE this suite existed; the AC-PIM prefix,
test_apimarket_marketprovidermonths, ledger-apimarket-marketprovidermonths
and redeclared_seller_count were git grep -F zero-occupancy against HEAD
on 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_provider_months. The real-name
layer answered one developer (api_provider_identity, api_provider_history)
but carried no time axis at all, so "how often is provider identity
redeclared, and is the shop front changing faster this quarter" had no
reading. This slot pins:

  - the fourteen-key envelope, the eight-key row, month_count ==
    len(months) and the honest empty world with a None average;
  - the booking law: a base registration books in the month of its own
    registered_utc, a revision books in the month of its own
    revised_utc, and a later revision never re-dates the registration
    month nor the base pair the history face publishes;
  - the contiguous grid with an honest zero row (a month carrying no
    identity event reports zeros and a None rate, not a fabricated 0.0);
  - the partition law event_count == registration_count +
    revision_count per row and in the envelope;
  - the distinct-account law: one developer registering once and
    revising twice inside a month is ONE seller and THREE events, with
    redeclared_seller_count <= seller_count everywhere;
  - the monotone running_revision whose last row equals the envelope
    total, the peak month with its earlier-month tie break, and the
    pooled average over redeclaring sellers only;
  - pure read (frozen table digests, constant ledger tx set), three
    identical reads and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_marketprovidermonths.py
"""

import ast
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
import apimarket_report as RPT        # noqa: E402 (config loader)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

ENVELOPE_KEYS = {"month_count", "registration_count", "revision_count",
                 "event_count", "seller_count",
                 "redeclared_seller_count",
                 "avg_revisions_per_redeclared_seller",
                 "peak_revision_month", "peak_revision_count",
                 "first_month", "last_month", "latest_event_utc",
                 "disclaimer", "months"}

ROW_KEYS = {"month", "registration_count", "revision_count",
            "event_count", "seller_count", "redeclared_seller_count",
            "redeclaration_rate", "running_revision"}

TABLES = ("apimarket_answers", "apimarket_answer_revisions",
          "apimarket_category_revisions", "apimarket_claim_notes",
          "apimarket_claim_responses", "apimarket_claim_withdrawals",
          "apimarket_claims", "apimarket_delistings",
          "apimarket_listing_revisions", "apimarket_listings",
          "apimarket_price_revisions", "apimarket_provider_revisions",
          "apimarket_providers", "apimarket_purchases",
          "apimarket_questions", "apimarket_rating_replies",
          "apimarket_rating_revisions", "apimarket_ratings",
          "apimarket_refunds", "apimarket_relistings",
          "apimarket_reply_revisions", "apimarket_review_resubmits",
          "apimarket_reviews", "apimarket_supply_revisions",
          "apimarket_unwatchings", "apimarket_watchlist")


class Clock(object):
    """Deterministic stamp holder; the module clock is patched in
    main() and restored in the finally block."""

    def __init__(self):
        self.value = "2026-09-01T00:00:00Z"

    def now_utc(self):
        return self.value


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


def frozen_digests(am):
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


def seed_world(led, dk, am, clock):
    """Two registrations and two revisions land in September; October
    carries no identity event at all; two revisions land in November.
    Dana is therefore one seller with four events across two months."""

    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-09-03T00:00:00Z"
    am.register_provider("usr:dana", "Dana Labs", "91310000AAAA")
    clock.value = "2026-09-04T00:00:00Z"
    am.register_provider("usr:frank", "Frank Sync", "91310000FFFF")
    clock.value = "2026-09-20T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="Dana Labs Inc")
    clock.value = "2026-09-25T00:00:00Z"
    am.revise_provider("usr:dana", credit_code="91310000BBBB")

    clock.value = "2026-11-05T00:00:00Z"
    am.revise_provider("usr:dana", provider_name="Dana Group")
    clock.value = "2026-11-06T00:00:00Z"
    am.revise_provider("usr:dana", credit_code="91310000CCCC")


def main():
    tmpdir = tempfile.mkdtemp(prefix="ampm-")
    db_path = os.path.join(tmpdir, "am.db")
    cfg = RPT.load_configs()[0]
    lobby_cfg = RPT.load_configs()[1]
    led = None
    am = None
    clock = Clock()
    real_now = A._now_utc
    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    try:
        A._now_utc = clock.now_utc
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

        # -- AC-PIM1 contract and the honest empty world ---------------
        empty = am.api_market_provider_months()
        ok1a = (set(empty) == ENVELOPE_KEYS
                and empty["month_count"] == 0
                and empty["months"] == []
                and empty["registration_count"] == 0
                and empty["revision_count"] == 0
                and empty["event_count"] == 0
                and empty["seller_count"] == 0
                and empty["redeclared_seller_count"] == 0
                and empty["avg_revisions_per_redeclared_seller"] is None
                and empty["peak_revision_month"] is None
                and empty["peak_revision_count"] is None
                and empty["first_month"] is None
                and empty["last_month"] is None
                and empty["latest_event_utc"] is None
                and empty["disclaimer"] == DISCLAIMER)
        seed_world(led, dk, am, clock)
        env = am.api_market_provider_months()
        ok1b = (set(env) == ENVELOPE_KEYS
                and env["month_count"] == len(env["months"]) == 3
                and all(set(row) == ROW_KEYS for row in env["months"]))
        record("AC-PIM1", ok1a and ok1b,
               "empty_ok=%r env_ok=%r months=%r"
               % (ok1a, ok1b, [r["month"] for r in env["months"]]))

        # -- AC-PIM2 booking law, no re-dating -------------------------
        months = {r["month"]: r for r in env["months"]}
        sept = months["2026-09"]
        octo = months["2026-10"]
        nov = months["2026-11"]
        hist = am.api_provider_history("usr:dana")
        ident = am.api_provider_identity("usr:dana")
        ok2 = (sept["registration_count"] == 2
               and sept["revision_count"] == 2
               and nov["registration_count"] == 0
               and nov["revision_count"] == 2
               and hist["registered_utc"] == "2026-09-03T00:00:00Z"
               and hist["base_provider_name"] == "Dana Labs"
               and hist["base_credit_code"] == "91310000AAAA"
               and hist["revision_count"] == 4
               and hist["provider_name"] == "Dana Group"
               and hist["credit_code"] == "91310000CCCC"
               and ident["registered_utc"] == "2026-09-03T00:00:00Z"
               and env["latest_event_utc"] == "2026-11-06T00:00:00Z")
        record("AC-PIM2", ok2,
               "sept=%r/%r nov=%r/%r base=%r effective=%r"
               % (sept["registration_count"], sept["revision_count"],
                  nov["registration_count"], nov["revision_count"],
                  (hist["base_provider_name"], hist["base_credit_code"]),
                  (hist["provider_name"], hist["credit_code"])))

        # -- AC-PIM3 contiguous grid with an honest zero month ---------
        ok3 = (sorted(months) == ["2026-09", "2026-10", "2026-11"]
               and octo["registration_count"] == 0
               and octo["revision_count"] == 0
               and octo["event_count"] == 0
               and octo["seller_count"] == 0
               and octo["redeclared_seller_count"] == 0
               and octo["redeclaration_rate"] is None
               and octo["running_revision"] == 2)
        record("AC-PIM3", ok3,
               "months=%r oct=%r"
               % (sorted(months),
                  (octo["event_count"], octo["redeclaration_rate"],
                   octo["running_revision"])))

        # -- AC-PIM4 partition law -------------------------------------
        part_ok = True
        for row in env["months"]:
            part_ok = part_ok and (
                row["event_count"] == row["registration_count"]
                + row["revision_count"])
        ok4 = (part_ok
               and env["event_count"] == env["registration_count"]
               + env["revision_count"] == 6
               and env["event_count"] == sum(
                   r["event_count"] for r in env["months"]))
        record("AC-PIM4", ok4,
               "partition=%r totals=%r"
               % (part_ok,
                  (env["registration_count"], env["revision_count"],
                   env["event_count"])))

        # -- AC-PIM5 distinct-account law ------------------------------
        subset_ok = all(
            r["redeclared_seller_count"] <= r["seller_count"]
            for r in env["months"])
        ok5 = (subset_ok
               and sept["event_count"] == 4
               and sept["seller_count"] == 2
               and sept["redeclared_seller_count"] == 1
               and sept["redeclaration_rate"] == 0.5
               and nov["event_count"] == 2
               and nov["seller_count"] == 1
               and nov["redeclared_seller_count"] == 1
               and nov["redeclaration_rate"] == 1.0
               and env["seller_count"] == 2
               and env["redeclared_seller_count"] == 1)
        record("AC-PIM5", ok5,
               "subset=%r sept=%r nov=%r env=%r"
               % (subset_ok,
                  (sept["event_count"], sept["seller_count"],
                   sept["redeclared_seller_count"]),
                  (nov["event_count"], nov["seller_count"],
                   nov["redeclared_seller_count"]),
                  (env["seller_count"], env["redeclared_seller_count"])))

        # -- AC-PIM6 accumulator, peak tie break and the pooled average -
        running = [r["running_revision"] for r in env["months"]]
        ok6 = (running == [2, 2, 4]
               and running == sorted(running)
               and months["2026-11"]["running_revision"]
               == env["revision_count"] == 4
               and env["peak_revision_month"] == "2026-09"
               and env["peak_revision_count"] == 2
               and env["avg_revisions_per_redeclared_seller"] == 4.0
               and env["first_month"] == "2026-09"
               and env["last_month"] == "2026-11")
        record("AC-PIM6", ok6,
               "running=%r peak=%r/%r avg=%r"
               % (running, env["peak_revision_month"],
                  env["peak_revision_count"],
                  env["avg_revisions_per_redeclared_seller"]))

        # -- AC-PIM7 pure read and cross-restart identity --------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_market_provider_months()),
                dumps(am.api_market_provider_months()),
                dumps(am.api_market_provider_months())]
        digests_after = frozen_digests(am)
        pure_ok = (runs[0] == runs[1] == runs[2]
                   and digests_before == digests_after
                   and tx_before == ledger_tx_ids(led))
        baseline = dumps(am.api_market_provider_months())
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_market_provider_months()))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (pure_ok
               and replays[0] == baseline == replays[1]
               and set(empty) == ENVELOPE_KEYS
               and empty["avg_revisions_per_redeclared_seller"] is None)
        record("AC-PIM7", ok7,
               "pure=%r restart_a=%r restart_b=%r empty_avg_none=%r"
               % (pure_ok, replays[0] == baseline,
                  replays[1] == baseline,
                  empty["avg_revisions_per_redeclared_seller"] is None))

        # -- AC-PIM8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-marketprovidermonths"'
                     in handle.read())
        with open(os.path.abspath(__file__), "rb") as handle:
            own = handle.read()
        ascii_ok = True
        try:
            own.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
        net_marks = {"requests", "urllib", "socket", "http", "ftplib",
                     "smtplib", "telnetlib"}
        mods = set()
        for node in ast.walk(ast.parse(own)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        net_ok = not (mods & net_marks)
        outside_ok = not os.path.abspath(db_path).startswith(
            os.path.join(os.path.dirname(BASE), ""))
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = (wired and ascii_ok and net_ok and shipped_ok and outside_ok)
        record("AC-PIM8", ok8,
               "wired=%r ascii=%r no_net=%r shipped=%r outside=%r"
               % (wired, ascii_ok, net_ok, shipped_ok, outside_ok))

        passed = sum(1 for _ac, ok in RESULTS if ok)
        print("\nSUITE %s %d/%d"
              % ("PASS" if passed == len(RESULTS) else "FAIL", passed,
                 len(RESULTS)), flush=True)
        return 0 if passed == len(RESULTS) else 1
    finally:
        A._now_utc = real_now
        if am is not None:
            try:
                am.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())