"""Acceptance suite for the apimarket review-cycle axis (BigDomain
R2133; canon = the explore-queue row seeded and claimed in R2133,
criteria AC-AMRC1..AC-AMRC8 registered in that claim note BEFORE this
code existed - honesty law; the AC-AMRC prefix, resubmit_listing,
api_seller_reviews, apimarket_review_resubmits, the three review error
codes, this suite name, the ledger-apimarket-reviewcycle runner label
and review_cycle were all git grep -F zero-occupancy anchored
2026-10-26, rc=1).

Face under proof: the review cycle law, the seller resubmission door
and the seller-side review status face.

Before this window a refusal was terminal. apimarket_reviews carried
UNIQUE(listing_id) and review_listing refused a repeat verdict, so a
seller who fixed a description or supplied the missing qualification
had to publish a brand new listing_key and lose that listing's
purchases, ratings, repricing history and metadata history - and the
public face kept showing the first refusal reason forever. This is the
same dead end the retirement door had before the re-list cycle law
(AC-AMRL1), so it is closed the same way:

  - publishing opens review cycle 1, a resubmission opens the next
    one, and the current verdict is the row of the current cycle;
  - resubmit_listing pins the gate order (account shape, listing
    shape/existence, ownership, retired state, current verdict,
    duplicate) and every refusal writes zero rows and moves zero
    tokens;
  - a verdict stays write-once per cycle: the old rows are never
    rewritten, and a cycle can be refused again and again;
  - api_review_queue and api_public_listings read through one seam, so
    a resubmitted listing re-enters the operator queue exactly once and
    the public face flips refused -> pending -> approved;
  - api_seller_reviews answers the question the seller could not ask:
    which of my listings wait, which were refused and why;
  - the idempotent pre-cycle migration, pure-read law, zero token
    movement, cross-restart byte identity and runner wiring.

Usage: python test_apimarket_reviewcycle.py
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

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

RESUBMIT_KEYS = {"listing_id", "dev_account", "cycle", "note", "state",
                 "resubmitted_utc", "disclaimer"}

STATUS_KEYS = {"dev_account", "listing_count", "pending_count",
               "approved_count", "refused_count", "resubmit_count",
               "disclaimer", "rows"}

STATUS_ROW_KEYS = {"listing_id", "listing_key", "title", "token_price",
                   "delisted", "review_cycle", "review_state",
                   "review_reason", "reviewed_utc", "resubmit_count"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_reviews", "apimarket_review_resubmits")


class Clock(object):
    def __init__(self, value="2026-10-26T00:00:00Z"):
        self.value = value

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


def build_stack(db_path, cfg, lobby_cfg, gate=None):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    if gate is None:
        gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    return led, metered, dk, gate, am


def close_stack(am, dk, metered, led):
    am.close()
    dk.close()
    metered.close()
    led.close()


def code_of(call, *args, **kwargs):
    try:
        call(*args, **kwargs)
    except A.ApiMarketError as exc:
        return getattr(exc, "code", None)
    return "NO-RAISE"


def review_rows(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT listing_id, decision, reason, reviewed_utc, cycle FROM"
        " apimarket_reviews WHERE listing_id = ? ORDER BY cycle",
        (listing_id,)).fetchall()
    conn.close()
    return rows


def resubmit_rows(am, listing_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT listing_id, dev_account, cycle, note, resubmitted_utc"
        " FROM apimarket_review_resubmits WHERE listing_id = ?"
        " ORDER BY cycle", (listing_id,)).fetchall()
    conn.close()
    return rows


def seed_world(led, dk, am, clock):
    """Two developers, four listings, three funded buyers and two
    first-cycle verdicts (one refusal, one approval); two listings are
    deliberately left pending."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMRC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMRC-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)
    clock.value = "2026-10-26T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-26T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-26T00:00:03Z"
    d3 = am.publish_api("usr:dana", "chart-render", "Chart Render API",
                        "server-side chart rendering", PAYLOAD, 5,
                        False)["listing_id"]
    clock.value = "2026-10-26T00:00:04Z"
    d4 = am.publish_api("usr:erin", "text-summarise",
                        "Text Summarise API", "short summarisation",
                        PAYLOAD, 4, True)["listing_id"]
    clock.value = "2026-10-26T00:00:10Z"
    am.purchase_api("usr:bob", d1, "BUY-AMRC-1")
    clock.value = "2026-10-26T00:00:11Z"
    am.purchase_api("usr:carol", d2, "BUY-AMRC-2")
    clock.value = "2026-10-26T00:00:12Z"
    am.purchase_api("usr:dave", d4, "BUY-AMRC-3")
    clock.value = "2026-10-26T00:00:20Z"
    am.review_listing(d1, "refuse", "missing qualification docs")
    clock.value = "2026-10-26T00:00:21Z"
    am.review_listing(d2, "approve")
    return {"d1": d1, "d2": d2, "d3": d3, "d4": d4}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamrc-")
    db_path = os.path.join(tmpdir, "am.db")
    cfg = RPT.load_configs()[0]
    lobby_cfg = RPT.load_configs()[1]
    am = None
    clock = Clock()
    real_now = A._now_utc
    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    try:
        A._now_utc = clock.now_utc
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        ids = seed_world(led, dk, am, clock)

        # -- AC-AMRC1 cycle contract --------------------------------
        clock.value = "2026-10-26T00:01:00Z"
        env = am.resubmit_listing("usr:dana", ids["d1"],
                                  "qualification docs attached")
        rows_db = resubmit_rows(am, ids["d1"])
        face_d1 = [r for r in am.api_seller_reviews(
            "usr:dana")["rows"] if r["listing_id"] == ids["d1"]][0]
        clock.value = "2026-10-26T00:01:10Z"
        verdict = am.review_listing(ids["d1"], "approve")
        after = review_rows(am, ids["d1"])
        public_d1 = [r for r in am.api_public_listings()["listings"]
                     if r["listing_id"] == ids["d1"]][0]
        face_d1b = [r for r in am.api_seller_reviews(
            "usr:dana")["rows"] if r["listing_id"] == ids["d1"]][0]
        ok1 = (set(env) == RESUBMIT_KEYS
               and env["cycle"] == 2
               and env["state"] == "pending"
               and env["listing_id"] == ids["d1"]
               and env["disclaimer"] == DISCLAIMER
               and len(rows_db) == 1
               and rows_db[0][2] == 2
               and rows_db[0][3] == "qualification docs attached"
               and face_d1["review_cycle"] == 2
               and face_d1["review_state"] == "pending"
               and face_d1["resubmit_count"] == 1
               and verdict["review_cycle"] == 2
               and [r[4] for r in after] == [1, 2]
               and after[0][1] == "refuse" and after[1][1] == "approve"
               and public_d1["review_state"] == "approved"
               and public_d1["review_reason"] is None
               and face_d1b["review_state"] == "approved"
               and face_d1b["review_cycle"] == 2)
        record("AC-AMRC1", ok1,
               "keys=%r cycle=%r rows=%r verdict_cycle=%r"
               " public=%r"
               % (sorted(env), env["cycle"], [r[4] for r in after],
                  verdict["review_cycle"], public_d1["review_state"]))

        # -- AC-AMRC2 gate family and order ------------------------
        clock.value = "2026-10-26T00:02:00Z"
        d5 = am.publish_api("usr:dana", "pending-svc",
                            "Pending Service", "awaiting first review",
                            PAYLOAD, 6, False)["listing_id"]
        am.delist_api("usr:dana", ids["d3"])
        snap = frozen_digests(am)
        tx = ledger_tx_ids(led)
        bad_acct = [None, "", "bob", "usr", 1, True, [], {}]
        acct_codes = [code_of(am.resubmit_listing, who, ids["d1"])
                      for who in bad_acct]
        bad_ids = [None, "", "abc", 0, -1, 1.5, [], True]
        id_codes = [code_of(am.resubmit_listing, "usr:dana", bad)
                    for bad in bad_ids]
        unknown = code_of(am.resubmit_listing, "usr:dana", 999999)
        non_owner = code_of(am.resubmit_listing, "usr:erin", ids["d1"])
        retired = code_of(am.resubmit_listing, "usr:dana", ids["d3"])
        pending = code_of(am.resubmit_listing, "usr:dana", d5)
        approved = code_of(am.resubmit_listing, "usr:dana", ids["d2"])
        order_a = code_of(am.resubmit_listing, "bob", "abc")
        order_b = code_of(am.resubmit_listing, "usr:erin", 999999)
        snap_after = frozen_digests(am)
        tx_after = ledger_tx_ids(led)
        ok2 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * len(bad_acct)
               and id_codes == ["E_AM_BAD_ARGS"] * len(bad_ids)
               and unknown == "E_AM_UNKNOWN_LISTING"
               and non_owner == "E_AM_NOT_OWNER"
               and retired == "E_AM_DELISTED"
               and pending == "E_AM_REVIEW_PENDING"
               and approved == "E_AM_REVIEW_APPROVED"
               and order_a == "E_AM_BAD_ACCOUNT"
               and order_b == "E_AM_UNKNOWN_LISTING"
               and snap == snap_after
               and tx == tx_after)
        record("AC-AMRC2", ok2,
               "acct=%r ids=%r unknown=%r owner=%r retired=%r"
               " pending=%r approved=%r order=%r/%r frozen=%r"
               % (acct_codes, id_codes, unknown, non_owner, retired,
                  pending, approved, order_a, order_b,
                  snap == snap_after))

        # -- AC-AMRC3 write-once per cycle, history preserved ------
        clock.value = "2026-10-26T00:03:00Z"
        twice = code_of(am.review_listing, ids["d1"], "refuse", "again")
        dup_row = "NO-RAISE"
        conn = sqlite3.connect(am.db_path)
        try:
            conn.execute(
                "INSERT INTO apimarket_reviews (listing_id, decision,"
                " reason, reviewed_utc, cycle)"
                " VALUES (?, 'approve', '', ?, 2)",
                (ids["d1"], "2026-10-26T00:03:01Z"))
            conn.commit()
        except sqlite3.IntegrityError:
            dup_row = "INTEGRITY"
        finally:
            conn.close()
        clock.value = "2026-10-26T00:04:00Z"
        am.review_listing(ids["d4"], "refuse", "policy: no live quotes")
        d4_first = review_rows(am, ids["d4"])
        clock.value = "2026-10-26T00:04:10Z"
        am.resubmit_listing("usr:erin", ids["d4"], "quotes removed")
        clock.value = "2026-10-26T00:04:20Z"
        am.review_listing(ids["d4"], "refuse", "still needs a sample")
        d4_second = review_rows(am, ids["d4"])
        clock.value = "2026-10-26T00:04:30Z"
        env3 = am.resubmit_listing("usr:erin", ids["d4"],
                                   "sample added")
        d4_third = review_rows(am, ids["d4"])
        face_erin = am.api_seller_reviews("usr:erin")["rows"][0]
        ok3 = (twice == "E_AM_ALREADY_REVIEWED"
               and dup_row == "INTEGRITY"
               and len(d4_first) == 1 and d4_first[0][1] == "refuse"
               and len(d4_second) == 2
               and d4_second[0] == d4_first[0]
               and [r[4] for r in d4_second] == [1, 2]
               and d4_second[1][2] == "still needs a sample"
               and d4_third == d4_second
               and env3["cycle"] == 3
               and face_erin["review_cycle"] == 3
               and face_erin["review_state"] == "pending"
               and face_erin["resubmit_count"] == 2)
        record("AC-AMRC3", ok3,
               "twice=%r unique=%r cycles=%r third_row=%r env3=%r"
               " resubmits=%r"
               % (twice, dup_row, [r[4] for r in d4_second],
                  d4_third == d4_second, env3["cycle"],
                  face_erin["resubmit_count"]))

        # -- AC-AMRC4 queue law ------------------------------------
        clock.value = "2026-10-26T00:05:00Z"
        queue = am.api_review_queue()
        public = am.api_public_listings()
        q_ids = [r["listing_id"] for r in queue["rows"]]
        ok4 = (q_ids == [ids["d4"], d5]
               and queue["pending_count"] == len(queue["rows"]) == 2
               and queue["pending_count"]
               == public["review_pending_count"]
               and ids["d3"] not in q_ids
               and ids["d1"] not in q_ids
               and ids["d2"] not in q_ids)
        record("AC-AMRC4", ok4,
               "queue=%r pending=%r public_pending=%r"
               % (q_ids, queue["pending_count"],
                  public["review_pending_count"]))

        # -- AC-AMRC5 public face transitions ----------------------
        clock.value = "2026-10-26T00:06:00Z"
        d6 = am.publish_api("usr:dana", "policy-bot",
                            "Policy Bot API", "policy answer service",
                            PAYLOAD, 9, False)["listing_id"]
        clock.value = "2026-10-26T00:06:10Z"
        am.review_listing(d6, "refuse", "missing docs v1")
        pub_refused = [r for r in am.api_public_listings()["listings"]
                       if r["listing_id"] == d6][0]
        clock.value = "2026-10-26T00:06:20Z"
        am.resubmit_listing("usr:dana", d6, "docs v2 attached")
        pub_pending = [r for r in am.api_public_listings()["listings"]
                       if r["listing_id"] == d6][0]
        clock.value = "2026-10-26T00:06:30Z"
        am.review_listing(d6, "approve")
        pub_approved = [r for r in am.api_public_listings()["listings"]
                        if r["listing_id"] == d6][0]
        ok5 = (pub_refused["review_state"] == "refused"
               and pub_refused["review_reason"] == "missing docs v1"
               and pub_refused["reviewed_utc"]
               == "2026-10-26T00:06:10Z"
               and pub_pending["review_state"] == "pending"
               and pub_pending["review_reason"] is None
               and pub_pending["reviewed_utc"] is None
               and pub_approved["review_state"] == "approved"
               and pub_approved["review_reason"] is None
               and pub_approved["reviewed_utc"]
               == "2026-10-26T00:06:30Z")
        record("AC-AMRC5", ok5,
               "refused=%r pending=%r approved=%r"
               % (pub_refused["review_state"],
                  pub_pending["review_state"],
                  pub_approved["review_state"]))

        # -- AC-AMRC6 seller status face ---------------------------
        clock.value = "2026-10-26T00:07:00Z"
        snap = frozen_digests(am)
        tx = ledger_tx_ids(led)
        dana = am.api_seller_reviews("usr:dana")
        erin = am.api_seller_reviews("usr:erin")
        empty = am.api_seller_reviews("usr:zoe")
        run2 = dumps(am.api_seller_reviews("usr:dana"))
        run3 = dumps(am.api_seller_reviews("usr:dana"))
        bad_face = [code_of(am.api_seller_reviews, who)
                    for who in [None, "", "dana", "usr", 1, True]]
        snap_after = frozen_digests(am)
        tx_after = ledger_tx_ids(led)
        dana_ids = [r["listing_id"] for r in dana["rows"]]
        dana_state = {r["listing_id"]: r for r in dana["rows"]}
        ok6 = (set(dana) == STATUS_KEYS
               and all(set(r) == STATUS_ROW_KEYS for r in dana["rows"])
               and dana_ids == sorted(dana_ids)
               and dana["listing_count"] == len(dana["rows"]) == 5
               and dana["approved_count"] == 3
               and dana["pending_count"] == 2
               and dana["refused_count"] == 0
               and dana["resubmit_count"] == 2
               and dana_state[ids["d3"]]["delisted"] is True
               and dana_state[ids["d3"]]["review_state"] == "pending"
               and ids["d4"] not in dana_ids
               and erin["listing_count"] == 1
               and erin["pending_count"] == 1
               and erin["resubmit_count"] == 2
               and empty["listing_count"] == 0
               and empty["rows"] == []
               and empty["pending_count"] == 0
               and bad_face == ["E_AM_BAD_ACCOUNT"] * 6
               and run2 == run3
               and snap == snap_after
               and tx == tx_after)
        record("AC-AMRC6", ok6,
               "dana=%r/%r/%r resub=%r erin=%r empty=%r bad=%r"
               " frozen=%r" % (dana["listing_count"],
                               dana["approved_count"],
                               dana["pending_count"],
                               dana["resubmit_count"],
                               erin["listing_count"],
                               empty["listing_count"], bad_face,
                               snap == snap_after))

        # -- AC-AMRC7 legacy migration -----------------------------
        legacy_dir = tempfile.mkdtemp(prefix="amamrc-legacy-")
        legacy_db = os.path.join(legacy_dir, "apimarket.db")
        conn = sqlite3.connect(legacy_db)
        conn.execute(
            "CREATE TABLE apimarket_reviews ("
            " review_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " listing_id INTEGER NOT NULL,"
            " decision TEXT NOT NULL CHECK"
            " (decision IN ('approve', 'refuse')),"
            " reason TEXT NOT NULL,"
            " reviewed_utc TEXT NOT NULL,"
            " UNIQUE (listing_id))")
        conn.execute(
            "INSERT INTO apimarket_reviews (listing_id, decision,"
            " reason, reviewed_utc) VALUES (1, 'refuse',"
            " 'legacy refusal', '2026-10-01T00:00:00Z')")
        conn.commit()
        conn.close()
        legacy_led, legacy_m, legacy_dk, _g, legacy_am = build_stack(
            os.path.join(legacy_dir, "led.db"), cfg, lobby_cfg)
        cols_a = [r[1] for r in sqlite3.connect(
            legacy_am.db_path).execute(
            "PRAGMA table_info(apimarket_reviews)").fetchall()]
        sql_a = sqlite3.connect(legacy_am.db_path).execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'apimarket_reviews'").fetchone()[0]
        row_a = review_rows(legacy_am, 1)
        legacy_dk.issue_key("usr:yuri", "yuri-key", 10,
                            ["backtest"], False)
        clock.value = "2026-10-26T00:08:00Z"
        legacy_am.publish_api("usr:yuri", "only-one", "Only One",
                              "single legacy listing", PAYLOAD, 5,
                              False)
        queue_legacy = legacy_am.api_review_queue()
        legacy_am.close()
        legacy_am = A.APIMarketFace(legacy_led, legacy_dk, gate,
                                    DISCLAIMER)
        cols_b = [r[1] for r in sqlite3.connect(
            legacy_am.db_path).execute(
            "PRAGMA table_info(apimarket_reviews)").fetchall()]
        sql_b = sqlite3.connect(legacy_am.db_path).execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'apimarket_reviews'").fetchone()[0]
        row_b = review_rows(legacy_am, 1)
        flat = sql_b.upper().replace(" ", "")
        ok7 = ("cycle" in cols_a
               and "UNIQUE(LISTING_ID)" not in flat
               and "UNIQUE(LISTING_ID,CYCLE)" in flat
               and row_a == row_b
               and row_a[0][4] == 1
               and row_a[0][2] == "legacy refusal"
               and row_a[0][3] == "2026-10-01T00:00:00Z"
               and queue_legacy["pending_count"] == 0
               and cols_a == cols_b and sql_a == sql_b)
        record("AC-AMRC7", ok7,
               "cols=%r legacy=%r queue=%r idem=%r"
               % (cols_a, row_a[0][2], queue_legacy["pending_count"],
                  cols_a == cols_b and sql_a == sql_b))
        try:
            legacy_am.close()
        except Exception:
            pass
        close_stack(legacy_am, legacy_dk, legacy_m, legacy_led)

        # -- AC-AMRC8 zero token, restart identity, hygiene --------
        tx = ledger_tx_ids(led)
        clock.value = "2026-10-26T00:09:00Z"
        face_before = dumps(am.api_seller_reviews("usr:dana"))
        pub_before = dumps(am.api_public_listings())
        queue_before = dumps(am.api_review_queue())
        bal_before = [am.led.balance("usr:bob") if hasattr(
            am.led, "balance") else None]
        snap = frozen_digests(am)
        close_stack(am, dk, metered, led)
        restarts = []
        for _i in range(2):
            led, metered, dk, gate, am = build_stack(
                db_path, cfg, lobby_cfg)
            restarts.append((dumps(am.api_seller_reviews("usr:dana")),
                             dumps(am.api_public_listings()),
                             dumps(am.api_review_queue())))
            close_stack(am, dk, metered, led)
        led, metered, dk, gate, am = build_stack(
            db_path, cfg, lobby_cfg)
        tx_after = ledger_tx_ids(led)
        snap_after = frozen_digests(am)
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = "ledger-apimarket-reviewcycle" in handle.read()
        with open(os.path.join(BASE, "apimarket.py"), "r",
                  encoding="utf-8") as handle:
            src = handle.read()
        try:
            src.encode("ascii")
            ascii_ok = True
        except UnicodeEncodeError:
            ascii_ok = False
        mods = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mods.add(node.module.split(".")[0])
        net_marks = {"socket", "http", "urllib", "requests", "ftplib"}
        net_ok = not (mods & net_marks)
        outside_ok = not os.path.abspath(db_path).startswith(
            os.path.join(os.path.dirname(BASE), ""))
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = (tx == tx_after and snap == snap_after
               and bal_before is not None
               and face_before == restarts[0][0] == restarts[1][0]
               and pub_before == restarts[0][1] == restarts[1][1]
               and queue_before == restarts[0][2] == restarts[1][2]
               and wired and ascii_ok and net_ok and shipped_ok
               and outside_ok)
        record("AC-AMRC8", ok8,
               "tx=%r frozen=%r restarts=%d wired=%r ascii=%r"
               " no_net=%r shipped=%r outside=%r"
               % (tx == tx_after, snap == snap_after, len(restarts),
                  wired, ascii_ok, net_ok, shipped_ok, outside_ok))

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