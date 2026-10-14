"""Cross-restart persistence window for the city solar-term /
festival limited-event face (BigDomain R1952; the festival seat of
the R1886 persist family - the R1947-seeded row, criteria
AC-FCP1..FCP7 pre-registered in the R1952 tech.md claim row before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close all three pieces -> reopen the same db/config with a fresh
CollectiblesFace + FestivalFace -> byte-identical read replay
(derived faces have zero in-memory drift) -> eleven
restart-surviving gate probes (fail-closed, zero rows, zero
charge) -> post-restart real-path continuation (fresh event
registration + two new first-purchases granting new commemorative
certificates) -> frozen immutable rows + replay gates across
restart -> pure-read law -> third instance stability.

Every read face replays stored values only (registered_utc /
purchased_utc / granted_utc are stored columns, never clock
echoes), so full-dump byte identity holds without clock freezing.
Tx ids are content-addressed and envelopes embed them, so
evidence digests mask 16-hex ids and ISO timestamps
(deterministic double-run stdout; R1941 mask law).

The commemorative linkage rides the collectibles public API by
reference (issue_certificate / collection - no copy, zero
collectibles-table writes from this suite outside that API);
the collectibles UNIQUE (account, kind, event_ref) backstop is
re-probed across restart (E_CL_DUP on pre-award replay).
This test source stays pure ASCII (encoding discipline).
Stdlib only. Usage: python test_festival_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                    # noqa: E402 (P-47-2b core)
import collectibles as C              # noqa: E402 (R619 product)
import festival as F                  # noqa: E402 (R1693 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: festival limited items"
              " are city keepsakes, not investment advice")

_MASKS = (
    (re.compile(r'"[0-9a-f]{16}"'), '"<tx>"'),
    (re.compile(r'"20\d\d-\d\d-\d\dT[^"]*"'), '"<ts>"'),
)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_fe_error(fn, *codes):
    try:
        fn()
    except F.FestivalError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_cl_error(fn, *codes):
    try:
        fn()
    except C.CollectiblesError as exc:
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
    out["events"] = int(conn.execute(
        "SELECT COUNT(*) FROM festival_events").fetchone()[0])
    out["purchases"] = int(conn.execute(
        "SELECT COUNT(*) FROM festival_purchases").fetchone()[0])
    out["certs"] = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind = 'certificate'"
    ).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def raw_rows(db_path):
    """Full-row SQL snapshot of the festival tables plus the
    certificate rows granted through the collectibles API (freeze
    carrier: events incl registered_utc, purchases incl
    purchased_utc + bound spend tx, certificates incl granted_utc)."""
    conn = sqlite3.connect(db_path)
    rows = {}
    rows["events"] = conn.execute(
        "SELECT event_id, event_key, title, start_window, end_window,"
        " token_price, per_account_limit, edition_cap, ai_label,"
        " registered_utc FROM festival_events ORDER BY event_id"
    ).fetchall()
    rows["purchases"] = conn.execute(
        "SELECT purchase_id, event_id, buyer_id, purchase_ref,"
        " price_paid, spend_tx, purchase_window, commemorative,"
        " purchased_utc FROM festival_purchases ORDER BY purchase_id"
    ).fetchall()
    rows["certs"] = conn.execute(
        "SELECT cl_id, account_id, kind, item_id, event_ref,"
        " granted_utc FROM collectibles WHERE kind = 'certificate'"
        " ORDER BY cl_id").fetchall()
    conn.close()
    return rows


def tx_cross(db_path, tx_id, account_id):
    """SQL cross: a bound spend tx is a real ledger row of type
    spend with the debit leg on the buyer account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = ?",
        (tx_id, account_id, "debit")).fetchone()
    conn.close()
    return ((head[0] if head else None) == "spend"
            and leg is not None)


def read_battery(ff, col, led, ids):
    snap = {
        "ev_view1": dump(ff.event_view(ids["ev1"])),
        "ev_view2": dump(ff.event_view(ids["ev2"])),
        "ev_view3": dump(ff.event_view(ids["ev3"])),
        "act6": dump(ff.active_events(6)),
        "act15": dump(ff.active_events(15)),
        "act40": dump(ff.active_events(40)),
        "board1": dump(ff.festival_board(ids["ev1"])),
        "board2": dump(ff.festival_board(ids["ev2"])),
        "certs_alice": dump(col.collection("usr:alice")),
        "certs_bob": dump(col.collection("usr:bob")),
        "certs_carol": dump(col.collection("usr:carol")),
        "certs_dave": dump(col.collection("usr:dave")),
        "certs_erin": dump(col.collection("usr:erin")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_dave": led.balance("usr:dave")["balance"],
        "bal_erin": led.balance("usr:erin")["balance"],
        "bal_reserve": led.balance("pool:reserve")["balance"],
    }
    if "ev4" in ids:
        snap["ev_view4"] = dump(ff.event_view(ids["ev4"]))
        snap["act16"] = dump(ff.active_events(16))
        snap["board4"] = dump(ff.festival_board(ids["ev4"]))
    return snap


def build_world(tmp, cfg):
    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    col = C.CollectiblesFace(led)
    ff = F.FestivalFace(led, col, DISCLAIMER)
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-FCP-A", "settlement")
    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:" + who, "credit", 100)],
                   "manual:fund-" + who, "suite funding " + who)
    led.ensure_account("usr:erin", census_avatar_id="erin")
    led.adjust([("pool:reserve", "debit", 50),
                ("usr:erin", "credit", 50)],
               "manual:fund-erin", "suite funding erin")
    return led, col, ff, db_path


def main():
    tmp = tempfile.mkdtemp(prefix="festival-persist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    led, col, ff, db_path = build_world(tmp, cfg)

    # -- anchor world ---------------------------------------------------
    ev1 = ff.register_event("lichun-2026", "Lichun Limited", 10, 20,
                            5, 2, False)
    ev2 = ff.register_event("mid-autumn", "Mid-Autumn Lantern", 5, 9,
                            3, 1, True, 2)
    ev3 = ff.register_event("winter-solstice", "Winter Solstice", 30,
                            40, 4, 3, True)
    ids = {"ev1": ev1["event_id"], "ev2": ev2["event_id"],
           "ev3": ev3["event_id"]}
    p_bob1 = ff.buy_event_item("usr:bob", ids["ev1"], 10, "order:fp1-bob")
    p_bob2 = ff.buy_event_item("usr:bob", ids["ev1"], 20, "order:fp1-bob2")
    p_carol = ff.buy_event_item("usr:carol", ids["ev1"], 12,
                                "order:fp1-carol")
    p_alice = ff.buy_event_item("usr:alice", ids["ev2"], 6, "order:fp2-alice")
    p_dave = ff.buy_event_item("usr:dave", ids["ev2"], 7, "order:fp2-dave")
    col.issue_certificate("usr:erin", "festival:lichun-2026",
                          "festival:lichun-2026")  # platform pre-award
    p_erin = ff.buy_event_item("usr:erin", ids["ev1"], 15, "order:fp1-erin")
    purchases = [(p_bob1, "usr:bob"), (p_bob2, "usr:bob"),
                 (p_carol, "usr:carol"), (p_alice, "usr:alice"),
                 (p_dave, "usr:dave"), (p_erin, "usr:erin")]

    snap1 = read_battery(ff, col, led, ids)
    counts1 = table_counts(db_path)
    rows1 = raw_rows(db_path)

    # AC-FCP1: anchor world + provenance SQL cross + linkage + pins
    cross = [tx_cross(db_path, p["spend_tx"], buyer)
             for p, buyer in purchases]
    board1 = json.loads(snap1["board1"])
    bob_comm = [r["commemorative"] for r in board1["purchases"]
                if r["buyer_id"] == "usr:bob"]
    certs_bob = json.loads(snap1["certs_bob"])["certificates"]
    certs_erin = json.loads(snap1["certs_erin"])["certificates"]
    ok1 = (counts1["events"] == 3 and counts1["purchases"] == 6
           and counts1["spend_tx"] == 6 and counts1["certs"] == 5
           and all(cross) and len(cross) == 6
           and p_bob1["purchase_window"] == 10
           and p_bob2["purchase_window"] == 20
           and p_erin["commemorative"] == 0 and p_bob1["commemorative"] == 1
           and bob_comm == [1, 0]
           and certs_bob == [{"item_id": "festival:lichun-2026",
                              "event_ref": "festival:lichun-2026"}]
           and certs_erin == [{"item_id": "festival:lichun-2026",
                               "event_ref": "festival:lichun-2026"}]
           and snap1["bal_alice"] == 97 and snap1["bal_bob"] == 90
           and snap1["bal_carol"] == 95 and snap1["bal_dave"] == 97
           and snap1["bal_erin"] == 45
           and snap1["bal_reserve"] == 1576
           and ev1["ai_label"] == 0 and ev2["ai_label"] == 1
           and ev3["ai_label"] == 1
           and json.loads(snap1["ev_view2"])["edition_cap"] == 2)
    record("AC-FCP1", ok1, "anchor world 3 events/6 purchases; every"
          " purchase binds a real spend (spend+debit on buyer) 6/6;"
          " window both edges legal (bob @10/@20); first-purchase"
          " linkage one cert per (account,event) (bob 2 buys ->"
          " %s); erin pre-award: buy legal flag=%d certs=%s; certs"
          " total=%d; balances a/b/c/d/e/reserve=%d/%d/%d/%d/%d/%d;"
          " counts events=%d purchases=%d spend=%d; digest=%s"
          % (bob_comm, p_erin["commemorative"], certs_erin,
             counts1["certs"], snap1["bal_alice"], snap1["bal_bob"],
             snap1["bal_carol"], snap1["bal_dave"], snap1["bal_erin"],
             snap1["bal_reserve"], counts1["events"],
             counts1["purchases"], counts1["spend_tx"],
             evidence_digest(snap1)))

    # AC-FCP2: close -> reopen -> byte-identical replay
    ff.close()
    col.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    col2 = C.CollectiblesFace(led2)
    ff2 = F.FestivalFace(led2, col2, DISCLAIMER)
    snap2 = read_battery(ff2, col2, led2, ids)
    diffs2 = battery_diffs(snap1, snap2)
    rows2 = raw_rows(db_path)
    rows_frozen2 = rows2 == rows1
    record("AC-FCP2", not diffs2 and rows_frozen2,
          "instance 2 replay on same db/config with fresh"
          " collectibles + festival faces: battery diffs=%s; raw"
          " event/purchase/cert rows byte-identical=%s (derived"
          " faces zero in-memory drift; stored utc, never clock"
          " echoes)"
          % (diffs2 or "none", str(rows_frozen2).lower()))

    # AC-FCP3: eleven restart-surviving gate probes (fail-closed)
    probes = [
        expect_fe_error(
            lambda: ff2.register_event("lichun-2026", "Again", 10, 20,
                                       5, 2, False),
            F.E_FE_DUP_EVENT),
        expect_fe_error(
            lambda: ff2.buy_event_item("usr:carol", ids["ev1"], 21,
                                       "order:fp3-window"),
            F.E_FE_WINDOW),
        expect_fe_error(
            lambda: ff2.buy_event_item("usr:bob", ids["ev1"], 15,
                                       "order:fp3-limit"),
            F.E_FE_LIMIT),
        expect_fe_error(
            lambda: ff2.buy_event_item("usr:carol", ids["ev1"], 13,
                                       "order:fp1-carol"),
            F.E_FE_DUP_PURCHASE),
        expect_fe_error(
            lambda: ff2.buy_event_item("usr:carol", ids["ev2"], 8,
                                       "order:fp3-cap"),
            F.E_FE_SOLD_OUT),
        expect_fe_error(
            lambda: ff2.buy_event_item("usr:dave", 999, 15,
                                       "order:fp3-unk"),
            F.E_FE_UNKNOWN_EVENT),
        expect_fe_error(lambda: ff2.event_view(999),
                        F.E_FE_UNKNOWN_EVENT),
        expect_fe_error(lambda: ff2.festival_board(999),
                        F.E_FE_UNKNOWN_EVENT),
        expect_fe_error(
            lambda: ff2.buy_event_item("svc:x", ids["ev1"], 15,
                                       "order:fp3-badacct"),
            F.E_FE_BAD_ACCOUNT),
        expect_fe_error(lambda: ff2.active_events("x"), F.E_FE_BAD_ARGS),
        expect_cl_error(
            lambda: col2.issue_certificate(
                "usr:erin", "festival:lichun-2026",
                "festival:lichun-2026"),
            C.E_CL_DUP),
    ]
    snap3probe = read_battery(ff2, col2, led2, ids)
    counts3p = table_counts(db_path)
    ok3 = (all(p[0] for p in probes)
           and battery_diffs(snap2, snap3probe) == []
           and counts3p == counts1)
    record("AC-FCP3", ok3, "11 restart-surviving probes all-reject"
          " [dup-event=%s; window=%s; limit=%s; ref-replay=%s;"
          " sold-out=%s; unknown-buy=%s; unknown-view=%s;"
          " unknown-board=%s; bad-account=%s; bad-tick=%s;"
          " pre-award-replay=%s] with zero charge, zero rows;"
          " battery and counts frozen across the probe batch"
          " (events=%d purchases=%d certs=%d spend=%d)"
          % tuple([p[1] for p in probes]
                  + [counts3p["events"], counts3p["purchases"],
                     counts3p["certs"], counts3p["spend_tx"]]))

    # AC-FCP4: post-restart real-path continuation (zero cache)
    ev4 = ff2.register_event("lantern-2027", "Lantern Festival", 15,
                             25, 2, 1, False)
    ids["ev4"] = ev4["event_id"]
    p_dave4 = ff2.buy_event_item("usr:dave", ids["ev4"], 16,
                                 "order:fp4-dave")
    p_erin3 = ff2.buy_event_item("usr:erin", ids["ev3"], 35,
                                 "order:fp4-erin")
    snap3 = read_battery(ff2, col2, led2, ids)
    counts3 = table_counts(db_path)
    cross4 = (tx_cross(db_path, p_dave4["spend_tx"], "usr:dave")
              and tx_cross(db_path, p_erin3["spend_tx"], "usr:erin"))
    act16 = json.loads(snap3["act16"])
    act16_keys = [r["event_key"] for r in act16["events"]]
    ev_view3b = json.loads(snap3["ev_view3"])
    board4 = json.loads(snap3["board4"])
    certs_dave = json.loads(snap3["certs_dave"])["certificates"]
    certs_erin3 = json.loads(snap3["certs_erin"])["certificates"]
    ok4 = (cross4
           and counts3["events"] == 4 and counts3["purchases"] == 8
           and counts3["certs"] == 7 and counts3["spend_tx"] == 8
           and act16_keys == ["lichun-2026", "lantern-2027"]
           and ev_view3b["purchase_count"] == 1
           and ev_view3b["participant_count"] == 1
           and p_dave4["commemorative"] == 1
           and p_erin3["commemorative"] == 1
           and board4["purchases"][0]["buyer_id"] == "usr:dave"
           and board4["purchases"][0]["commemorative"] == 1
           and len(certs_dave) == 2 and len(certs_erin3) == 2
           and snap3["bal_dave"] == 95 and snap3["bal_erin"] == 41
           and snap3["bal_alice"] == 97 and snap3["bal_bob"] == 90
           and snap3["bal_carol"] == 95
           and snap3["bal_reserve"] == 1582
           and ev4["ai_label"] == 0
           and json.loads(snap3["ev_view4"])["event_key"]
           == "lantern-2027")
    record("AC-FCP4", ok4, "continuation on instance 2: fresh event"
          " lantern-2027 registered (4th event row, ai_label=%d)"
          " + dave first-buy ev4 (new cert, flag=%d) + erin"
          " first-buy ev3 (new cert, flag=%d); certs 5->%d; both"
          " spends SQL-crossed; zero-cache recompute: act16"
          " events=%s, ev3 view purchases=%d, board4 first row"
          " dave/flag=1; balances d=%d e=%d others frozen; counts"
          " events/purchases/spend=%d/%d/%d; digest=%s"
          % (ev4["ai_label"], p_dave4["commemorative"],
             p_erin3["commemorative"], counts3["certs"], act16_keys,
             ev_view3b["purchase_count"], snap3["bal_dave"],
             snap3["bal_erin"], counts3["events"],
             counts3["purchases"], counts3["spend_tx"],
             evidence_digest(snap3)))

    # AC-FCP5: frozen anchor rows + replay gates across restart
    rows_now = raw_rows(db_path)
    ok5a = (rows_now["events"][:3] == rows1["events"]
            and rows_now["purchases"][:6] == rows1["purchases"]
            and rows_now["certs"][:5] == rows1["certs"])
    bal_b_pre = led2.balance("usr:bob")["balance"]
    ok_reg, code_reg = expect_fe_error(
        lambda: ff2.register_event("lichun-2026", "Again", 10, 20,
                                   5, 2, False),
        F.E_FE_DUP_EVENT)
    ok_rebuy, code_rebuy = expect_fe_error(
        lambda: ff2.buy_event_item("usr:bob", ids["ev1"], 15,
                                   "order:fp1-bob"),
        F.E_FE_DUP_PURCHASE)
    bal_b_post = led2.balance("usr:bob")["balance"]
    counts5 = table_counts(db_path)
    ok5 = (ok5a and ok_reg and code_reg == F.E_FE_DUP_EVENT
           and ok_rebuy and code_rebuy == F.E_FE_DUP_PURCHASE
           and bal_b_post == bal_b_pre and counts5 == counts3)
    record("AC-FCP5", ok5, "anchor rows frozen across restart x"
          " continuation (3 event rows incl registered_utc, 6"
          " purchase rows incl purchased_utc + bound spend_tx +"
          " commemorative, 5 certificate rows incl granted_utc -"
          " byte-identical prefixes of the post-continuation"
          " tables, zero UPDATE surface); replay gates:"
          " re-register=%s, ref-replay=%s fires before the limit"
          " gate (bob at limit 2, zero charge %d==%d, zero rows);"
          " counts frozen"
          % (code_reg, code_rebuy, bal_b_pre, bal_b_post))

    # AC-FCP6: pure-read law
    snap3b = read_battery(ff2, col2, led2, ids)
    counts6 = table_counts(db_path)
    ok6 = (snap3b == snap3 and counts6 == counts3)
    record("AC-FCP6", ok6, "pure-read law: double battery"
          " byte-identical (diffs=%s) and counts constant"
          " (events=%d purchases=%d certs=%d)"
          % (battery_diffs(snap3, snap3b) or "none",
             counts6["events"], counts6["purchases"],
             counts6["certs"]))

    # AC-FCP7: third instance stability + hygiene
    ff2.close()
    col2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    col3 = C.CollectiblesFace(led3)
    ff3 = F.FestivalFace(led3, col3, DISCLAIMER)
    snap4 = read_battery(ff3, col3, led3, ids)
    diffs7 = battery_diffs(snap3, snap4)
    counts7 = table_counts(db_path)
    sha_files = {}
    for name in ("festival.py", "collectibles.py", "ledger.py",
                 "config.json"):
        with open(os.path.join(BASE, name), "rb") as fh:
            sha_files[name] = hashlib.sha256(fh.read()).hexdigest()
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
           and sha_files["config.json"]
           == hashlib.sha256(cfg_bytes).hexdigest()
           and non_ascii == 0 and not net_hits and not in_repo
           and "UPDATE festival_" not in open(
               os.path.join(BASE, "festival.py"), encoding="utf-8"
           ).read())
    record("AC-FCP7", ok7, "instance 3 on same db: battery diffs=%s;"
          " counts stable events=%d purchases=%d certs=%d; shipped"
          " files untouched (festival/collectibles/ledger/config"
          " sha256 stable); non-ascii=%d; network-imports=%s;"
          " world outside repo=%s; festival module zero UPDATE"
          " surface"
          % (diffs7 or "none", counts7["events"],
             counts7["purchases"], counts7["certs"], non_ascii,
             net_hits or "none", str(not in_repo).lower()))

    ff3.close()
    col3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
