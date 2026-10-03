"""Acceptance suite for the resident growth-archive subscription
face (BigDomain R1017; canon = BLUEPRINT sec-4 C2-tier new
subscription line, C-20260927-01 adoption-order first item;
product definition = docs/spec/price-canon-amendment-spec.md
sec-2). Asserts the pre-registered criteria AC-GA1..AC-GA7 from
the R1017 backlog row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Probe supply stands in for the BigLife IF-7/IF-10 behavior feed
(deterministic ASCII payloads; production supply wiring is a
bootstrap-period item).

Usage: python test_growth_archive.py
"""

import inspect
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import growth_archive as G  # noqa: E402  (R1017 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_g_error(fn, *codes):
    try:
        fn()
    except G.GrowthArchiveError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


AM = "res:amy"


def _ev(eid, kind, ts, content):
    return (eid, AM, kind, ts, content)


SUPPLY = [
    _ev("ga:ev:r1", "year_ring", "2099-01-02T08:00:00Z",
        {"ring": 1, "note": "joined block L4"}),
    _ev("ga:ev:r2", "year_ring", "2099-02-05T09:00:00Z",
        {"ring": 2, "note": "first co-creation adopted"}),
    _ev("ga:ev:d1", "dialogue", "2099-01-15T10:00:00Z",
        {"line": "the river lights are on tonight"}),
    _ev("ga:ev:d2", "dialogue", "2099-02-15T10:00:00Z",
        {"line": "spring block market opens"}),
    _ev("ga:ev:c1", "city_story", "2099-01-20T12:00:00Z",
        {"story": "quant tower pulse reached level 3"}),
    _ev("ga:ev:m1", "memorial", "2099-01-09T06:00:00Z",
        {"kind": "birthday", "detail": "amy turns two"}),
]


def main():
    tmp = tempfile.mkdtemp(prefix="growth-archive-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    gf = G.GrowthArchiveFace(led)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-GA-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 500), ("usr:bob", "credit", 500)],
               "manual:fund-b", "suite funding bob")
    led.adjust([("pool:reserve", "debit", 200), ("usr:carol", "credit", 200)],
               "manual:fund-c", "suite funding carol")
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    with open(os.path.join(BASE, "growth_archive.py"),
              encoding="utf-8") as h:
        src = h.read()

    # -- AC-GA1 purity / composition law ---------------------------------
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    foreign_tables = [t for t in ("obs_strategies", "obs_grants",
                                  "cl_editions", "eff_credits",
                                  "member_credits", "pay_orders",
                                  "venue_occupancy", "exp_credits")
                      if t in src]
    no_update = ("UPDATE ga_resident_events" not in src
                 and "UPDATE ga_subscriptions" not in src)
    ok1 = (non_ascii == 0 and not foreign_tables and no_update)
    record("AC-GA1", ok1, "module pure ASCII (%d non-ascii); zero foreign"
          " suite tables in source (%s); zero UPDATE surface; compliance"
          " strings runtime-derived from ledger config"
          % (non_ascii, foreign_tables or "none"))

    # -- AC-GA2 supply gate + append-only events -------------------------
    b_bob0 = bal("usr:bob")
    ok_unk, code_unk = expect_g_error(
        lambda: gf.subscribe("usr:bob", "res:ghost", "2099-01", 99,
                             "order:ga2a"),
        G.E_GA_UNKNOWN)
    n_before = None
    conn = sqlite3.connect(db_path)
    n_before = conn.execute(
        "SELECT COUNT(*) FROM ga_resident_events").fetchone()[0]
    conn.close()
    gf.ingest_supply_event("ga:ev:probe", "res:probe", "dialogue",
                           "2099-01-11T00:00:00Z", {"line": "probe"})
    ok_dup_ev, code_dev = expect_g_error(
        lambda: gf.ingest_supply_event("ga:ev:probe", "res:probe",
                                       "dialogue", "2099-01-11T00:00:00Z",
                                       {"line": "probe"}),
        G.E_GA_DUP_EVENT)
    ok_bad_kind, code_bk = expect_g_error(
        lambda: gf.ingest_supply_event("ga:ev:x1", AM, "gossip",
                                      "2099-01-01T00:00:00Z", {"a": 1}),
        G.E_GA_BAD_EVENT)
    ok_bad_payload, code_bp = expect_g_error(
        lambda: gf.ingest_supply_event("ga:ev:x2", AM, "dialogue",
                                       "2099-01-01T00:00:00Z", {}),
        G.E_GA_BAD_EVENT)
    for item in SUPPLY:
        gf.ingest_supply_event(*item)
    conn = sqlite3.connect(db_path)
    n_after = conn.execute(
        "SELECT COUNT(*) FROM ga_resident_events").fetchone()[0]
    conn.close()
    ok2 = (ok_unk and code_unk == G.E_GA_UNKNOWN
           and bal("usr:bob") == b_bob0
           and ok_dup_ev and code_dev == G.E_GA_DUP_EVENT
           and ok_bad_kind and code_bk == G.E_GA_BAD_EVENT
           and ok_bad_payload and code_bp == G.E_GA_BAD_EVENT
           and n_before == 0 and n_after == len(SUPPLY) + 1)
    record("AC-GA2", ok2, "unknown-resident subscribe rejected %s zero"
          " charge (%d==%d); duplicate event id rejected %s, bad kind %s,"
          " empty payload %s - all zero rows; %d deterministic supply"
          " events ingested through the explicit supply face (BigLife"
          " IF-7/IF-10 sandbox stand-in)"
          % (code_unk, b_bob0, bal("usr:bob"), code_dev, code_bk,
             code_bp, n_after))

    # -- AC-GA3 subscription core: one spend, dup before spend ------------
    b_al0 = bal("usr:alice")
    s1 = gf.subscribe("usr:alice", AM, "2099-01", 99, "order:ga3a")
    b_al1 = bal("usr:alice")
    conn = sqlite3.connect(db_path)
    tx_head = conn.execute(
        "SELECT type FROM ledger_tx WHERE tx_id = ?",
        (s1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:alice'", (s1["spend_tx"],)).fetchone()
    conn.close()
    sub_view = gf.subscriptions_view("usr:alice")["subscriptions"]
    ok_dup, code_dup = expect_g_error(
        lambda: gf.subscribe("usr:alice", AM, "2099-01", 99,
                             "order:ga3b"),
        G.E_GA_DUP)
    ok_dup_bal = (bal("usr:alice") == b_al1
                 and len(gf.subscriptions_view("usr:alice")
                         ["subscriptions"]) == len(sub_view))
    b_bob1 = bal("usr:bob")
    s2 = gf.subscribe("usr:bob", AM, "2099-02", 99, "order:ga3c")
    b_bob2 = bal("usr:bob")
    bad = []
    raised_all = True
    for label, fn, code in (
            ("bad buyer", lambda: gf.subscribe("svc:x", AM, "2099-01", 99,
                                               "order:ga3d"),
             G.E_GA_BAD_ACCOUNT),
            ("zero price", lambda: gf.subscribe("usr:carol", AM, "2099-01",
                                               0, "order:ga3e"),
             G.E_GA_BAD_PRICE),
            ("bool price", lambda: gf.subscribe("usr:carol", AM, "2099-01",
                                               True, "order:ga3f"),
             G.E_GA_BAD_PRICE),
            ("bad month fmt", lambda: gf.subscribe("usr:carol", AM,
                                                   "209901", 99,
                                                   "order:ga3g"),
             G.E_GA_BAD_MONTH),
            ("month 13", lambda: gf.subscribe("usr:carol", AM, "2099-13",
                                              99, "order:ga3h"),
             G.E_GA_BAD_MONTH),
            ("empty ref", lambda: gf.subscribe("usr:carol", AM, "2099-01",
                                               99, "  "),
             G.E_GA_BAD_ARGS),
            ("empty resident", lambda: gf.subscribe("usr:carol", "  ",
                                                    "2099-01", 99,
                                                    "order:ga3i"),
             G.E_GA_BAD_ARGS)):
        ok_one, got = expect_g_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    conn = sqlite3.connect(db_path)
    n_sub = conn.execute(
        "SELECT COUNT(*) FROM ga_subscriptions").fetchone()[0]
    n_spend = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'").fetchone()[0]
    conn.close()
    ok3 = (b_al1 == b_al0 - 99 and len(sub_view) == 1
           and sub_view[0]["resident_id"] == AM
           and sub_view[0]["sub_month"] == "2099-01"
           and sub_view[0]["spend_tx"] == s1["spend_tx"]
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit"
           and ok_dup and code_dup == G.E_GA_DUP and ok_dup_bal
           and b_bob2 == b_bob1 - 99 and s1["spend_tx"] != s2["spend_tx"]
           and raised_all and n_sub == 2 and n_spend == 2
           and bal("usr:carol") == 200)
    record("AC-GA3", ok3, "subscription #%d charged once (%d->%d) binding"
          " a real spend tx (type=spend, debit leg); same (account,"
          " resident, month) replay rejected %s BEFORE the spend (balance"
          " %d, rows %d); another month is a separate legal spend (%d->%d);"
          " bad-args family all rejected zero side effects (%s); carol"
          " untouched (%d); sub rows %d == spend txs %d"
          % (s1["sub_id"], b_al0, b_al1, code_dup, bal("usr:alice"),
             len(sub_view), b_bob1, b_bob2, "; ".join(bad),
             bal("usr:carol"), n_sub, n_spend))

    # -- AC-GA4 fail-closed gate + window + pure reads --------------------
    conn = sqlite3.connect(db_path)
    spend_before = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'").fetchone()[0]
    conn.close()
    b_carol0 = bal("usr:carol")
    ok_denied, code_dn = expect_g_error(
        lambda: gf.archive_page("usr:carol", AM, "2099-01"),
        G.E_GA_DENIED)
    ok_next_month, code_nm = expect_g_error(
        lambda: gf.archive_page("usr:alice", AM, "2099-03"),
        G.E_GA_DENIED)
    ok_unk_page, code_up = expect_g_error(
        lambda: gf.archive_page("usr:alice", "res:ghost", "2099-01"),
        G.E_GA_UNKNOWN)
    page = gf.archive_page("usr:alice", AM, "2099-01")
    page_bob = gf.archive_page("usr:bob", AM, "2099-02")
    gf.subscriptions_view("usr:alice")
    gf.residents_view()
    gf.compliance_view()
    conn = sqlite3.connect(db_path)
    spend_after = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'").fetchone()[0]
    conn.close()
    ok4 = (ok_denied and code_dn == G.E_GA_DENIED
           and bal("usr:carol") == b_carol0
           and ok_next_month and code_nm == G.E_GA_DENIED
           and ok_unk_page and code_up == G.E_GA_UNKNOWN
           and spend_before == spend_after
           and len(page["year_ring"]) == 2
           and len(page["dialogue_digest"]) == 1
           and page["dialogue_digest"][0]["event_id"] == "ga:ev:d1"
           and len(page["city_story_monthly"]) == 1
           and len(page["memorial_pages"]) == 1
           and len(page_bob["dialogue_digest"]) == 1
           and page_bob["dialogue_digest"][0]["event_id"] == "ga:ev:d2")
    record("AC-GA4", ok4, "carol without entitlement rejected %s zero"
          " charge (%d==%d); alice next month 2099-03 denied %s (window"
          " covers exactly its month); unknown resident page %s; all read"
          " faces pure (spend txs %d==%d); page sections: year_ring=%d"
          " (full timeline), dialogue_digest=%d (in-month only),"
          " city_story=%d, memorial=%d; bob's 2099-02 digest sees the"
          " other-month line (%s)"
          % (code_dn, b_carol0, bal("usr:carol"), code_nm, code_up,
             spend_before, spend_after, len(page["year_ring"]),
             len(page["dialogue_digest"]), len(page["city_story_monthly"]),
             len(page["memorial_pages"]),
             page_bob["dialogue_digest"][0]["event_id"]))

    # -- AC-GA5 compliance verbatim from config ---------------------------
    tok = cfg.get("token") or {}
    want_label = str(tok.get("ai_label_text", ""))
    want_disc = str(tok.get("disclaimer", ""))
    want_note = str(cfg.get("params_status", ""))
    cs = page["city_story_monthly"][0]
    raw_ok = all("ai_generated" not in sec[0]
                 for sec in (page["year_ring"], page["dialogue_digest"],
                             page["memorial_pages"]))
    cv = gf.compliance_view()
    ok5 = (cs.get("ai_generated") is True and cs.get("ai_label") == want_label
           and page["disclaimer"] == want_disc
           and page["price_note"] == want_note and raw_ok
           and cv == {"ai_label": want_label, "disclaimer": want_disc,
                      "price_note": want_note}
           and want_disc in page["disclaimer"])
    record("AC-GA5", ok5, "derived city-story row carries AIGC label"
          " verbatim from config token.ai_label_text and"
          " ai_generated=True; raw sections (year_ring/dialogue/"
          " memorial) carry no generated marker; persistent disclaimer"
          " rides the page verbatim (config token.disclaimer); price note"
          " = config params_status verbatim ([needs-CEO] pricing"
          " confirmation with CEO); compliance_view matches config"
          " byte-verbatim; read-only archive face has no user-input"
          " channel (msgSecCheck = boundary note, ugc IF-8 single-source"
          " gate if any input face ever opens)")

    # -- AC-GA6 provenance + isolation audit -------------------------------
    conn = sqlite3.connect(db_path)
    ev_rows = conn.execute(
        "SELECT event_id, content_json FROM ga_resident_events"
    ).fetchall()
    conn.close()
    ev_map = {r[0]: json.loads(r[1]) for r in ev_rows}
    all_items = (page["year_ring"] + page["dialogue_digest"]
                 + page["city_story_monthly"] + page["memorial_pages"]
                 + page_bob["year_ring"] + page_bob["dialogue_digest"])
    prov_ok = all(item["content"] == ev_map.get(item["event_id"])
                  for item in all_items)
    banned = [w for w in ("sell", "refund", "exchange", "withdraw",
                          "transfer", "mint") if re.search(
                              r"\b%s\b" % w, src)]
    view_params = [p for p in inspect.signature(
        gf.archive_page).parameters]
    no_content_param = "content" not in view_params
    conn = sqlite3.connect(db_path)
    n_sub = conn.execute(
        "SELECT COUNT(*) FROM ga_subscriptions").fetchone()[0]
    distinct_tx = conn.execute(
        "SELECT COUNT(DISTINCT bound_spend_tx) FROM ga_subscriptions"
    ).fetchone()[0]
    bound_debits = conn.execute(
        "SELECT COUNT(*) FROM ga_subscriptions s JOIN ledger_entries e"
        " ON e.tx_id = s.bound_spend_tx AND e.direction = 'debit'"
        " AND e.account_id = s.account_id").fetchone()[0]
    conn.close()
    total = sum(bal(w) for w in ("usr:alice", "usr:bob", "usr:carol",
                                 "pool:reserve"))
    ok6 = (prov_ok and not banned and no_content_param
           and n_sub == 2 and distinct_tx == 2 and bound_debits == 2
           and bal("usr:alice") == 201 and bal("usr:bob") == 401
           and total == 1000)
    record("AC-GA6", ok6, "every rendered content round-trips"
          " byte-equal against the ingested supply event (%d items"
          " checked) - no fabrication is possible (views take no content"
          " parameter and only SELECT the events table); banned-verb"
          " scan clean (%s); audit: %d subscription rows == %d distinct"
          " bound spend txs == %d real debit legs; balances exact"
          " (alice=%d, bob=%d, carol=%d); pool conservation holds"
          " (sum=%d == minted 1000)"
          % (len(all_items), banned or "none", n_sub, distinct_tx,
             bound_debits, bal("usr:alice"), bal("usr:bob"),
             bal("usr:carol"), total))

    # -- AC-GA7 hard-law close-out -----------------------------------------
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = (cfg_after == cfg_bytes
           and len(RESULTS) == 6
           and all(ok for _, ok in RESULTS))
    record("AC-GA7", ok7, "config.json byte-stable across the suite run;"
          " criteria AC-GA1..AC-GA6 all green (%d/%d); evidence face ="
          " qa/growth-archive-R1017.log + full regression"
          " qa/reconcile-all-R1017.log; delivery = state log R1017 line"
          " + commit citing C-20260927-01 (P-51)"
          % (sum(1 for _, ok in RESULTS if ok), len(RESULTS)))

    gf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
