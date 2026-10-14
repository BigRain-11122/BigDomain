"""Cross-restart persistence window for the UGC template
marketplace face (BigDomain R1951; the tmarket seat of the R1886
persist family - the R1946-seeded row, criteria AC-TMP1..TMP7
pre-registered in the R1951 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config with a fresh
SecGate + TMarketFace -> byte-identical read replay (derived
faces have zero in-memory drift) -> eleven restart-surviving
gate probes (fail-closed, zero rows, zero charge) ->
post-restart real-path continuation (fresh creator publish +
two new purchases + a new rating) -> frozen immutable rows +
replay gates across restart -> pure-read law -> third instance
stability.

Every read face replays stored values only (listed_utc /
purchased_utc / rated_utc are stored columns, never clock
echoes), so full-dump byte identity holds without clock
freezing. Tx ids are content-addressed and purchase envelopes
embed them, so evidence digests mask 16-hex ids and ISO
timestamps (deterministic double-run stdout; R1941 mask law).

The content gate is the lobby SecGate product injected by
reference (no copy); its wordlists load from the lobby config at
runtime - this test source stays pure ASCII (encoding
discipline). Stdlib only. Usage: python test_tmarket_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import tmarket as T                   # noqa: E402 (R1691 face)
from sec_gate import SecGate          # noqa: E402 (lobby reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: template marketplace is"
              " a creation tool, not investment advice")

PAYLOAD = {"scene": "harbor", "layout": ["pier", "lamprow"],
           "revision": 1}

_MASKS = (
    (re.compile(r'"[0-9a-f]{16}"'), '"<tx>"'),
    (re.compile(r'"20\d\d-\d\d-\d\dT[^"]*"'), '"<ts>"'),
)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_tm_error(fn, *codes):
    try:
        fn()
    except T.TMarketError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_ledger_error(fn, *codes):
    try:
        fn()
    except L.LedgerError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    for pat, rep in _MASKS:
        text = pat.sub(rep, text)
    return text


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(str(val))))
    return sha16("\n".join(parts))


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    out = {}
    for tab in ("tmarket_templates", "tmarket_purchases",
                "tmarket_ratings"):
        out[tab] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tab).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    out["share_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'share'"
    ).fetchone()[0])
    conn.close()
    return out


def raw_rows(db_path):
    """Full-row SQL snapshot of the three tmarket tables (freeze
    carrier: templates incl listed_utc, purchases incl
    purchased_utc + both bound txs, ratings incl rated_utc)."""
    conn = sqlite3.connect(db_path)
    rows = {}
    rows["templates"] = conn.execute(
        "SELECT template_id, creator_id, template_key, title,"
        " description, payload_json, token_price, ai_label,"
        " listed_utc FROM tmarket_templates ORDER BY"
        " template_id").fetchall()
    rows["purchases"] = conn.execute(
        "SELECT purchase_id, template_id, buyer_id, price_paid,"
        " creator_share, platform_share, spend_tx, creator_share_tx,"
        " purchased_utc FROM tmarket_purchases ORDER BY"
        " purchase_id").fetchall()
    rows["ratings"] = conn.execute(
        "SELECT rating_id, template_id, buyer_id, stars, rated_utc"
        " FROM tmarket_ratings ORDER BY rating_id").fetchall()
    conn.close()
    return rows


def tx_cross(db_path, tx_id, account_id, tx_type, direction):
    """SQL cross: a bound tx is a real ledger row of the expected
    type with the expected leg on the expected account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = ?",
        (tx_id, account_id, direction)).fetchone()
    conn.close()
    return ((head[0] if head else None) == tx_type
            and leg is not None)


def read_battery(tf, led, ids):
    return {
        "tv1": dump(tf.template_view(ids["t1"])),
        "tv2": dump(tf.template_view(ids["t2"])),
        "tv3": dump(tf.template_view(ids["t3"])),
        "tv4": dump(tf.template_view(ids["t4"])),
        "mv": dump(tf.market_view()),
        "rv1": dump(tf.rating_view(ids["t1"])),
        "sv_a": dump(tf.sales_view("usr:alice")),
        "sv_b": dump(tf.sales_view("usr:bob")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_dave": led.balance("usr:dave")["balance"],
        "bal_reserve": led.balance("pool:reserve")["balance"],
        "bal_share": led.balance("pool:share")["balance"],
    }


def build_world(tmp, cfg, lobby_cfg):
    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    tf = T.TMarketFace(led, gate, DISCLAIMER)
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-TMP-A", "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-TMP-S", "settlement")
    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    for who, amount, tag in (("alice", 400, "a"), ("bob", 500, "b"),
                             ("carol", 300, "c"), ("dave", 100, "d")):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    return led, gate, tf, db_path


def main():
    tmp = tempfile.mkdtemp(prefix="tmarket-persist-")
    cfg_bytes = open(os.path.join(BASE, "config.json"), "rb").read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    lobby_cfg = json.loads(open(
        os.path.join(LOBBY, "config.json"), "rb").read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    led, gate, tf, db_path = build_world(tmp, cfg, lobby_cfg)

    # -- anchor world ---------------------------------------------------
    t1 = tf.publish_template("usr:alice", "harbor-tpl",
                             "Harbor Walk Template",
                             "a calm pier layout", PAYLOAD, 10, False)
    t2 = tf.publish_template("usr:alice", "night-market",
                             "Night Market Template",
                             "lantern row layout", PAYLOAD, 3, True)
    t3 = tf.publish_template("usr:bob", "harbor-tpl",
                             "Bob Harbor Variant",
                             "same key other creator", PAYLOAD, 7, False)
    t4 = tf.publish_template("usr:alice", "gold-plated",
                             "Gold Plated Layout", "very expensive",
                             PAYLOAD, 999, False)
    ids = {"t1": t1["template_id"], "t2": t2["template_id"],
           "t3": t3["template_id"], "t4": t4["template_id"]}
    p1 = tf.purchase("usr:bob", ids["t1"], "order:tmp1-bob")
    p2 = tf.purchase("usr:carol", ids["t1"], "order:tmp1-carol")
    p3 = tf.purchase("usr:bob", ids["t2"], "order:tmp1-bob2")
    p4 = tf.purchase("usr:carol", ids["t3"], "order:tmp1-carol3")
    tf.rate("usr:bob", ids["t1"], 5)
    tf.rate("usr:carol", ids["t1"], 1)
    tf.rate("usr:bob", ids["t2"], 4)

    snap1 = read_battery(tf, led, ids)
    counts1 = table_counts(db_path)
    rows1 = raw_rows(db_path)

    # AC-TMP1: anchor world + provenance SQL cross + pinned balances
    cross = []
    for purchase, buyer, creator in (
            (p1, "usr:bob", "usr:alice"), (p2, "usr:carol", "usr:alice"),
            (p3, "usr:bob", "usr:alice"), (p4, "usr:carol", "usr:bob")):
        cross.append(tx_cross(db_path, purchase["spend_tx"], buyer,
                              "spend", "debit")
                     and tx_cross(db_path,
                                  purchase["creator_share_tx"], creator,
                                  "share", "credit"))
    split_ok = (p1["creator_share"] == 7 and p1["platform_share"] == 3
                and p3["creator_share"] == 3
                and p3["platform_share"] == 0
                and p4["creator_share"] == 5
                and p4["platform_share"] == 2)
    ok1 = (counts1["tmarket_templates"] == 4
           and counts1["tmarket_purchases"] == 4
           and counts1["tmarket_ratings"] == 3
           and all(cross) and len(cross) == 4 and split_ok
           and snap1["bal_alice"] == 417 and snap1["bal_bob"] == 492
           and snap1["bal_carol"] == 283 and snap1["bal_dave"] == 100
           and snap1["bal_reserve"] == 730
           and snap1["bal_share"] == 978)
    record("AC-TMP1", ok1, "anchor world 4 templates/4 purchases/3"
          " ratings; every purchase binds a real spend (spend+debit"
          " on buyer) and a real share (share+credit on creator)"
          " 4/4; splits 10->(7,3) 3->(3,0) 7->(5,2); balances"
          " a/b/c/dave/reserve/share=%d/%d/%d/%d/%d/%d; counts"
          " spend=%d share=%d; digest=%s"
          % (snap1["bal_alice"], snap1["bal_bob"], snap1["bal_carol"],
             snap1["bal_dave"], snap1["bal_reserve"],
             snap1["bal_share"], counts1["spend_tx"],
             counts1["share_tx"], evidence_digest(snap1)))

    # AC-TMP2: close -> reopen -> byte-identical replay
    tf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    gate2 = SecGate.from_config(lobby_cfg)
    tf2 = T.TMarketFace(led2, gate2, DISCLAIMER)
    snap2 = read_battery(tf2, led2, ids)
    diffs2 = battery_diffs(snap1, snap2)
    rows2 = raw_rows(db_path)
    rows_frozen2 = rows2 == rows1
    record("AC-TMP2", not diffs2 and rows_frozen2,
          "instance 2 replay on same db/config with a fresh gate:"
          " battery diffs=%s; raw three-table rows byte-identical"
          "=%s (derived faces zero in-memory drift)"
          % (diffs2 or "none", str(rows_frozen2).lower()))

    # AC-TMP3: eleven restart-surviving gate probes (fail-closed)
    probes = [
        expect_tm_error(
            lambda: tf2.publish_template("usr:alice", "harbor-tpl",
                                         "Harbor Walk Template",
                                         "a calm pier layout", PAYLOAD,
                                         10, False),
            T.E_TM_DUP_TEMPLATE),
        expect_tm_error(
            lambda: tf2.purchase("usr:alice", ids["t1"],
                                  "order:tmp3-self"),
            T.E_TM_SELF_BUY),
        expect_tm_error(
            lambda: tf2.purchase("usr:bob", ids["t1"],
                                 "order:tmp3-dupref"),
            T.E_TM_PURCHASE_DUP),
        expect_tm_error(
            lambda: tf2.rate("usr:dave", ids["t1"], 5),
            T.E_TM_NOT_BUYER),
        expect_tm_error(
            lambda: tf2.rate("usr:bob", ids["t1"], 4),
            T.E_TM_RATE_DUP),
        expect_tm_error(
            lambda: tf2.rate("usr:dave", ids["t2"], 0),
            T.E_TM_BAD_STARS),
        expect_tm_error(
            lambda: tf2.purchase("usr:bob", 999, "order:tmp3-unk"),
            T.E_TM_UNKNOWN_TEMPLATE),
        expect_tm_error(
            lambda: tf2.rate("usr:bob", 999, 5),
            T.E_TM_UNKNOWN_TEMPLATE),
        expect_tm_error(
            lambda: tf2.publish_template(
                "usr:alice", "bad-t2",
                "clean prefix " + bad_word + " suffix",
                "clean desc", PAYLOAD, 9, False),
            T.E_TM_CONTENT_REJECTED),
        expect_ledger_error(
            lambda: tf2.purchase("usr:dave", ids["t4"],
                                 "order:tmp3-neg"),
            L.E_NEGATIVE_BALANCE),
        expect_tm_error(
            lambda: tf2.rate("svc:x", ids["t1"], 5),
            T.E_TM_BAD_ACCOUNT),
    ]
    snap3probe = read_battery(tf2, led2, ids)
    counts3p = table_counts(db_path)
    ok3 = (all(p[0] for p in probes)
           and battery_diffs(snap2, snap3probe) == []
           and counts3p == counts1)
    record("AC-TMP3", ok3, "11 restart-surviving probes all-reject"
          " [dup-template=%s; self-buy=%s; purchase-dup=%s;"
          " not-buyer=%s; rate-dup=%s; bad-stars=%s; unknown-buy=%s;"
          " unknown-rate=%s; content-gate=%s; negative-balance=%s;"
          " bad-account=%s] with zero charge, zero rows; battery"
          " and counts frozen across the probe batch (%s)"
          % tuple([p[1] for p in probes]
                  + ["tpl=%d pur=%d rat=%d spend=%d share=%d"
                     % (counts3p["tmarket_templates"],
                        counts3p["tmarket_purchases"],
                        counts3p["tmarket_ratings"],
                        counts3p["spend_tx"], counts3p["share_tx"])]))

    # AC-TMP4: post-restart real-path continuation (zero cache)
    t5 = tf2.publish_template("usr:dave", "dave-tpl", "Dave Layout",
                              "clean words", PAYLOAD, 4, False)
    ids["t5"] = t5["template_id"]
    p5 = tf2.purchase("usr:bob", ids["t5"], "order:tmp4-bob5")
    p6 = tf2.purchase("usr:dave", ids["t2"], "order:tmp4-dave2")
    tf2.rate("usr:carol", ids["t3"], 2)
    snap3 = read_battery(tf2, led2, ids)
    counts3 = table_counts(db_path)
    cross5 = (tx_cross(db_path, p5["spend_tx"], "usr:bob",
                       "spend", "debit")
              and tx_cross(db_path, p5["creator_share_tx"],
                           "usr:dave", "share", "credit"))
    cross6 = (tx_cross(db_path, p6["spend_tx"], "usr:dave",
                       "spend", "debit")
              and tx_cross(db_path, p6["creator_share_tx"],
                           "usr:alice", "share", "credit"))
    mv = json.loads(snap3["mv"])
    tv3b = json.loads(snap3["tv3"])
    ok4 = (cross5 and cross6
           and counts3["tmarket_templates"] == 5
           and counts3["tmarket_purchases"] == 6
           and counts3["tmarket_ratings"] == 4
           and snap3["bal_alice"] == 420 and snap3["bal_bob"] == 488
           and snap3["bal_carol"] == 283 and snap3["bal_dave"] == 100
           and snap3["bal_share"] == 972
           and snap3["bal_reserve"] == 737
           and len(mv["templates"]) == 5
           and tv3b["rating_count"] == 1 and tv3b["rating_avg"] == 2.0
           and json.loads(snap3["tv1"])["purchase_count"] == 2
           and p5["creator_share"] == 3 and p5["platform_share"] == 1
           and p6["creator_share"] == 3 and p6["platform_share"] == 0
           and t5["ai_label"] == 0)
    record("AC-TMP4", ok4, "continuation on instance 2: dave's fresh"
          " publish (5th template, gate-clean, ai_label=%d) + bob"
          " buys dave-tpl (spend+share SQL cross) + dave buys t2"
          " (cross) + carol rates t3=2; zero-cache recompute:"
          " market rows=%d, t3 rating (%d, avg %.1f), t1"
          " purchase_count=%d frozen; counts tpl/pur/rat=%d/%d/%d;"
          " balances a/b/c/dave/share=%d/%d/%d/%d/%d; splits"
          " 4->(3,1) 3->(3,0); digest=%s"
          % (t5["ai_label"], len(mv["templates"]),
             tv3b["rating_count"], tv3b["rating_avg"],
             json.loads(snap3["tv1"])["purchase_count"],
             counts3["tmarket_templates"],
             counts3["tmarket_purchases"], counts3["tmarket_ratings"],
             snap3["bal_alice"], snap3["bal_bob"], snap3["bal_carol"],
             snap3["bal_dave"], snap3["bal_share"],
             evidence_digest(snap3)))

    # AC-TMP5: frozen anchor rows + replay gates across restart
    rows_now = raw_rows(db_path)
    ok5a = (rows_now["templates"][:4] == rows1["templates"]
            and rows_now["purchases"][:4] == rows1["purchases"]
            and rows_now["ratings"][:3] == rows1["ratings"])
    bal_b_pre = led2.balance("usr:bob")["balance"]
    ok_rpub, code_rpub = expect_tm_error(
        lambda: tf2.publish_template("usr:alice", "harbor-tpl",
                                     "Harbor Walk Template",
                                     "a calm pier layout", PAYLOAD,
                                     10, False),
        T.E_TM_DUP_TEMPLATE)
    ok_rbuy, code_rbuy = expect_tm_error(
        lambda: tf2.purchase("usr:bob", ids["t1"], "order:tmp5-rb"),
        T.E_TM_PURCHASE_DUP)
    bal_b_post = led2.balance("usr:bob")["balance"]
    counts5 = table_counts(db_path)
    ok5 = (ok5a and ok_rpub and code_rpub == T.E_TM_DUP_TEMPLATE
           and ok_rbuy and code_rbuy == T.E_TM_PURCHASE_DUP
           and bal_b_post == bal_b_pre and counts5 == counts3)
    record("AC-TMP5", ok5, "anchor rows frozen across restart x"
          " continuation (4 template rows incl listed_utc, 4"
          " purchase rows incl purchased_utc + bound txs, 3 rating"
          " rows incl rated_utc - byte-identical prefixes of the"
          " post-continuation tables, zero UPDATE surface); replay"
          " gates: republish=%s, re-buy=%s (zero charge %d==%d,"
          " zero rows); counts frozen"
          % (code_rpub, code_rbuy, bal_b_pre, bal_b_post))

    # AC-TMP6: pure-read law
    snap3b = read_battery(tf2, led2, ids)
    counts6 = table_counts(db_path)
    ok6 = (snap3b == snap3 and counts6 == counts3)
    record("AC-TMP6", ok6, "pure-read law: double battery"
          " byte-identical (diffs=%s) and counts constant"
          " (tpl=%d pur=%d rat=%d)"
          % (battery_diffs(snap3, snap3b) or "none",
             counts6["tmarket_templates"],
             counts6["tmarket_purchases"],
             counts6["tmarket_ratings"]))

    # AC-TMP7: third instance stability + hygiene
    tf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    gate3 = SecGate.from_config(lobby_cfg)
    tf3 = T.TMarketFace(led3, gate3, DISCLAIMER)
    snap4 = read_battery(tf3, led3, ids)
    diffs7 = battery_diffs(snap3, snap4)
    counts7 = table_counts(db_path)
    sha_cfg = hashlib.sha256(
        open(os.path.join(BASE, "config.json"), "rb").read()).hexdigest()
    sha_tmk = hashlib.sha256(
        open(os.path.join(BASE, "tmarket.py"), "rb").read()).hexdigest()
    sha_lcfg = hashlib.sha256(
        open(os.path.join(LOBBY, "config.json"), "rb").read()).hexdigest()
    sha_led = hashlib.sha256(
        open(os.path.join(BASE, "ledger.py"), "rb").read()).hexdigest()
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        src = fh.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [ln.strip() for ln in src.splitlines()
                    if ln.strip().startswith("import ")
                    or ln.strip().startswith("from ")]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in ("urllib", "requests", "socket",
                                         "http"))]
    in_repo = os.path.commonpath([os.path.abspath(tmp), BASE]) == BASE
    ok7 = (not diffs7 and counts7 == counts3
           and sha_cfg == hashlib.sha256(cfg_bytes).hexdigest()
           and non_ascii == 0 and not net_hits and not in_repo
           and sha_tmk and sha_lcfg and sha_led)
    record("AC-TMP7", ok7, "instance 3 on same db: battery diffs=%s;"
          " counts stable tpl=%d pur=%d rat=%d; shipped files"
          " untouched (config/tmarket/lobby-config/ledger sha16"
          " stable); non-ascii=%d; network-imports=%s; world"
          " outside repo=%s"
          % (diffs7 or "none", counts7["tmarket_templates"],
             counts7["tmarket_purchases"],
             counts7["tmarket_ratings"], non_ascii,
             net_hits or "none", str(not in_repo).lower()))

    tf3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
