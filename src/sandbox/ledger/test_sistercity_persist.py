"""Cross-restart persistence window for the sister-city cross-city
visit face (BigDomain R1953; the sistercity seat of the R1886
persist family - the R1948-seeded row, criteria AC-SCP1..AC-SCP7
pre-registered in the R1953 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Two-piece restart world on the real product path: anchor world ->
close the SisterCityFace and the Ledger -> reopen the same
db/config with a fresh SisterCityFace -> byte-identical read
replay (the four twin tables carry all persistence; the embedded
settlement engine is an in-memory hash chain by design - manifests
persist as twin_settlements rows and the UNIQUE (pair, period)
row is the restart-surviving settle gate) -> thirteen
restart-surviving gate probes (fail-closed, zero rows, zero
charge, incl the persisted-settlement replay and the
no-disclaimer constructor gate) -> post-restart real-path
continuation (fresh pairing registration + new visit pass + new
exposure booking + fresh-chain window settle) -> frozen immutable
rows + replay gates across restart -> pure-read law -> third
instance stability.

Every read face replays stored values only (registered_utc /
purchased_utc / booked_utc / settled_utc are stored columns,
never clock echoes), so full-dump byte identity holds without
clock freezing. Tx ids are content-addressed 16-hex and manifest
ids are 64-hex, so evidence digests mask both plus ISO timestamps
(deterministic double-run stdout; R1941 mask law, 64-hex widened).
This test source stays pure ASCII (encoding discipline).
Stdlib only. Usage: python test_sistercity_persist.py
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
import sistercity as S                # noqa: E402 (R1696 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: cross-city visit passes"
              " and district exposures are city conveniences, not"
              " investment advice")

_MASKS = (
    (re.compile(r'"[0-9a-f]{64}"'), '"<mid>"'),
    (re.compile(r'"[0-9a-f]{16}"'), '"<tx>"'),
    (re.compile(r'"20\d\d-\d\d-\d\dT[^"]*"'), '"<ts>"'),
)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_sc_error(fn, *codes):
    try:
        fn()
    except S.SisterCityError as exc:
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
    out["registry"] = int(conn.execute(
        "SELECT COUNT(*) FROM twin_registry").fetchone()[0])
    out["passes"] = int(conn.execute(
        "SELECT COUNT(*) FROM twin_passes").fetchone()[0])
    out["exposures"] = int(conn.execute(
        "SELECT COUNT(*) FROM twin_exposures").fetchone()[0])
    out["settlements"] = int(conn.execute(
        "SELECT COUNT(*) FROM twin_settlements").fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def raw_rows(db_path):
    """Full-row SQL snapshot of the four twin tables (freeze
    carrier: registry incl registered_utc, passes incl bound
    spend_tx + purchased_utc, exposures likewise, settlements incl
    manifest_json + settled_utc)."""
    conn = sqlite3.connect(db_path)
    rows = {}
    rows["registry"] = conn.execute(
        "SELECT pair_id, pair_key, home_city, sister_city,"
        " start_window, end_window, pass_price, exposure_price,"
        " exposure_slots, ai_label, registered_utc"
        " FROM twin_registry ORDER BY pair_id").fetchall()
    rows["passes"] = conn.execute(
        "SELECT pass_id, pair_id, buyer_id, purchase_ref,"
        " price_paid, spend_tx, pass_window, purchased_utc"
        " FROM twin_passes ORDER BY pass_id").fetchall()
    rows["exposures"] = conn.execute(
        "SELECT exposure_id, pair_id, merchant_id, booking_ref,"
        " price_paid, spend_tx, exposure_window, booked_utc"
        " FROM twin_exposures ORDER BY exposure_id").fetchall()
    rows["settlements"] = conn.execute(
        "SELECT settle_id, pair_id, period, manifest_id,"
        " total_cent, manifest_json, settled_utc"
        " FROM twin_settlements ORDER BY settle_id").fetchall()
    conn.close()
    return rows


def settle_row(db_path, pair_id, period):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT manifest_id, total_cent FROM twin_settlements"
        " WHERE pair_id = ? AND period = ?",
        (pair_id, period)).fetchone()
    conn.close()
    return row


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


def read_battery(sc, led, ids):
    snap = {
        "view1": dump(sc.twin_view(ids["t1"])),
        "view2": dump(sc.twin_view(ids["t2"])),
        "view3": dump(sc.twin_view(ids["t3"])),
        "act6": dump(sc.active_twins(6)),
        "act12": dump(sc.active_twins(12)),
        "act15": dump(sc.active_twins(15)),
        "act40": dump(sc.active_twins(40)),
        "board1": dump(sc.twin_board(ids["t1"])),
        "board2": dump(sc.twin_board(ids["t2"])),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_dave": led.balance("usr:dave")["balance"],
        "bal_erin": led.balance("usr:erin")["balance"],
        "bal_reserve": led.balance("pool:reserve")["balance"],
    }
    if "t4" in ids:
        snap["view4"] = dump(sc.twin_view(ids["t4"]))
        snap["act16"] = dump(sc.active_twins(16))
        snap["board4"] = dump(sc.twin_board(ids["t4"]))
    return snap


def build_world(tmp, cfg):
    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    sc = S.SisterCityFace(led, DISCLAIMER)
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-SCP-A", "settlement")
    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:" + who, "credit", 100)],
                   "manual:fund-" + who, "suite funding " + who)
    led.ensure_account("usr:erin", census_avatar_id="erin")
    led.adjust([("pool:reserve", "debit", 50),
                ("usr:erin", "credit", 50)],
               "manual:fund-erin", "suite funding erin")
    return led, sc, db_path


def main():
    tmp = tempfile.mkdtemp(prefix="sistercity-persist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    led, sc, db_path = build_world(tmp, cfg)

    # -- anchor world ---------------------------------------------------
    t1 = sc.register_twin("harbor-twins", "New Harbor", "Old Harbor",
                          10, 20, 5, 3, 2, False)
    t2 = sc.register_twin("market-twins", "East Market", "West Market",
                          5, 9, 3, 4, 1, True)
    t3 = sc.register_twin("festival-twins", "North Fest", "South Fest",
                          30, 40, 4, 2, 3, True)
    ids = {"t1": t1["pair_id"], "t2": t2["pair_id"], "t3": t3["pair_id"]}
    passes = [
        sc.buy_visit_pass("usr:bob", ids["t1"], 10, "scp-p-bob"),
        sc.buy_visit_pass("usr:carol", ids["t1"], 20, "scp-p-carol"),
        sc.buy_visit_pass("usr:alice", ids["t1"], 12, "scp-p-alice"),
        sc.buy_visit_pass("usr:erin", ids["t1"], 15, "scp-p-erin"),
        sc.buy_visit_pass("usr:dave", ids["t2"], 6, "scp-p-dave"),
    ]
    exposures = [
        sc.book_exposure("usr:bob", ids["t1"], 11, "scp-e-bob"),
        sc.book_exposure("usr:carol", ids["t1"], 18, "scp-e-carol"),
        sc.book_exposure("usr:alice", ids["t2"], 8, "scp-e-alice"),
    ]
    manifest = sc.settle_twin_window(
        ids["t1"], "2026-10",
        ["home-admin", "sister-admin"],
        {"home-admin": 50, "sister-admin": 50})

    snap1 = read_battery(sc, led, ids)
    counts1 = table_counts(db_path)
    rows1 = raw_rows(db_path)

    # AC-SCP1: anchor world + provenance SQL cross + settle landed
    spend_rows = [(p["spend_tx"], p["buyer_id"]) for p in passes] \
        + [(e["spend_tx"], e["merchant_id"]) for e in exposures]
    cross = [tx_cross(db_path, tx, who) for tx, who in spend_rows]
    srow = settle_row(db_path, ids["t1"], "2026-10")
    view1 = json.loads(snap1["view1"])
    view2 = json.loads(snap1["view2"])
    act6 = json.loads(snap1["act6"])
    act40 = json.loads(snap1["act40"])
    ok1 = (counts1["registry"] == 3 and counts1["passes"] == 5
           and counts1["exposures"] == 3 and counts1["settlements"] == 1
           and counts1["spend_tx"] == 8
           and all(cross) and len(cross) == 8
           and passes[0]["pass_window"] == 10
           and passes[1]["pass_window"] == 20
           and passes[0]["price_paid"] == 5
           and exposures[0]["price_paid"] == 3
           and srow is not None and srow[0] == manifest["id"]
           and srow[1] == 26
           and manifest["sales_total_cent"] == 26
           and manifest["window_period"] == "2026-10"
           and manifest["sales_rows"] == 6
           and manifest["apportioned_cent"]
           == {"home-admin": 13, "sister-admin": 13}
           and view1["pass_count"] == 4
           and view1["pass_holder_count"] == 4
           and view1["exposure_count"] == 2
           and view1["merchant_count"] == 2
           and view1["ai_label"] == 0 and view2["ai_label"] == 1
           and [r["pair_key"] for r in act6["twins"]]
           == ["market-twins"]
           and [r["pair_key"] for r in act40["twins"]]
           == ["festival-twins"]
           and snap1["bal_alice"] == 91 and snap1["bal_bob"] == 92
           and snap1["bal_carol"] == 92 and snap1["bal_dave"] == 97
           and snap1["bal_erin"] == 45
           and snap1["bal_reserve"] == 1583)
    record("AC-SCP1", ok1, "anchor world 3 twins/5 passes/3"
          " exposures/1 settlement; every purchase binds a real"
          " spend (spend+debit on buyer) %d/%d; window edges legal"
          " (bob @10, carol @20); settle 2026-10 landed as a"
          " twin_settlements row (manifest id SQL-matched,"
          " total=%d, split=%s); view counts t1=%d/%d/%d/%d;"
          " act6=%s act40=%s; balances a/b/c/d/e/reserve ="
          " %d/%d/%d/%d/%d/%d; digest=%s"
          % (sum(cross), len(cross), srow[1],
             json.dumps(manifest["apportioned_cent"],
                        sort_keys=True),
             view1["pass_count"], view1["pass_holder_count"],
             view1["exposure_count"], view1["merchant_count"],
             [r["pair_key"] for r in act6["twins"]],
             [r["pair_key"] for r in act40["twins"]],
             snap1["bal_alice"], snap1["bal_bob"],
             snap1["bal_carol"], snap1["bal_dave"],
             snap1["bal_erin"], snap1["bal_reserve"],
             evidence_digest(snap1)))

    # AC-SCP2: close -> reopen -> byte-identical replay
    sc.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    sc2 = S.SisterCityFace(led2, DISCLAIMER)
    snap2 = read_battery(sc2, led2, ids)
    diffs2 = battery_diffs(snap1, snap2)
    rows2 = raw_rows(db_path)
    rows_frozen2 = rows2 == rows1
    record("AC-SCP2", not diffs2 and rows_frozen2,
          "instance 2 replay on same db/config with a fresh"
          " SisterCityFace: battery diffs=%s; raw registry/pass/"
          " exposure/settlement rows byte-identical=%s (four twin"
          " tables carry all persistence - the embedded settlement"
          " chain is in-memory by design, manifests persist as"
          " rows; stored utc, never clock echoes)"
          % (diffs2 or "none", str(rows_frozen2).lower()))

    # AC-SCP3: thirteen restart-surviving gate probes (fail-closed)
    probes = [
        expect_sc_error(
            lambda: sc2.register_twin("harbor-twins", "New Harbor",
                                      "Old Harbor", 10, 20, 5, 3, 2,
                                      False),
            S.E_SC_DUP_TWIN),
        expect_sc_error(
            lambda: sc2.buy_visit_pass("usr:dave", ids["t1"], 21,
                                       "scp-p-dave-w"),
            S.E_SC_WINDOW),
        expect_sc_error(
            lambda: sc2.buy_visit_pass("usr:bob", ids["t1"], 15,
                                       "scp-p-bob-x"),
            S.E_SC_PASS_EXISTS),
        expect_sc_error(
            lambda: sc2.buy_visit_pass("usr:carol", ids["t1"], 12,
                                       "scp-p-carol"),
            S.E_SC_DUP_PASS),
        expect_sc_error(
            lambda: sc2.book_exposure("usr:alice", ids["t1"], 15,
                                      "scp-e-alice-x"),
            S.E_SC_EXPOSURE_FULL),
        expect_sc_error(
            lambda: sc2.book_exposure("usr:bob", ids["t1"], 16,
                                      "scp-e-bob"),
            S.E_SC_DUP_EXPOSURE),
        expect_sc_error(
            lambda: sc2.buy_visit_pass("usr:dave", 999, 15,
                                       "scp-p-unk"),
            S.E_SC_UNKNOWN_TWIN),
        expect_sc_error(lambda: sc2.twin_view(999),
                        S.E_SC_UNKNOWN_TWIN),
        expect_sc_error(lambda: sc2.twin_board(999),
                        S.E_SC_UNKNOWN_TWIN),
        expect_sc_error(
            lambda: sc2.buy_visit_pass("svc:x", ids["t1"], 15,
                                       "scp-p-badacct"),
            S.E_SC_BAD_ACCOUNT),
        expect_sc_error(lambda: sc2.active_twins("x"),
                        S.E_SC_BAD_ARGS),
        expect_sc_error(
            lambda: sc2.settle_twin_window(
                ids["t1"], "2026-10",
                ["home-admin", "sister-admin"],
                {"home-admin": 50, "sister-admin": 50}),
            S.E_SC_SETTLED),
        expect_sc_error(
            lambda: S.SisterCityFace(led2, ""),
            S.E_SC_NO_DISCLAIMER),
    ]
    snap3probe = read_battery(sc2, led2, ids)
    counts3p = table_counts(db_path)
    ok3 = (all(p[0] for p in probes)
           and battery_diffs(snap2, snap3probe) == []
           and counts3p == counts1)
    record("AC-SCP3", ok3, "13 restart-surviving probes all-reject"
          " [dup-twin=%s; window=%s; pass-exists=%s; ref-replay=%s;"
          " exposure-full=%s; exposure-replay=%s; unknown-buy=%s;"
          " unknown-view=%s; unknown-board=%s; bad-account=%s;"
          " bad-tick=%s; settled-replay=%s (persisted settlement"
          " row gate); no-disclaimer-ctor=%s (refused before any"
          " connect)] with zero charge, zero rows; battery and"
          " counts frozen across the probe batch"
          " (registry=%d passes=%d exposures=%d settlements=%d"
          " spend=%d)"
          % tuple([p[1] for p in probes]
                  + [counts3p["registry"], counts3p["passes"],
                     counts3p["exposures"],
                     counts3p["settlements"],
                     counts3p["spend_tx"]]))

    # AC-SCP4: post-restart real-path continuation (zero cache)
    t4 = sc2.register_twin("lantern-twins", "Lantern North",
                           "Lantern South", 15, 25, 2, 2, 1, False)
    ids["t4"] = t4["pair_id"]
    p4 = sc2.buy_visit_pass("usr:erin", ids["t4"], 16, "scp-p-erin-l2")
    e4 = sc2.book_exposure("usr:dave", ids["t4"], 20, "scp-e-dave-l2")
    m4 = sc2.settle_twin_window(
        ids["t4"], "2026-11",
        ["home-admin", "sister-admin"],
        {"home-admin": 50, "sister-admin": 50})
    snap3 = read_battery(sc2, led2, ids)
    counts3 = table_counts(db_path)
    cross4 = (tx_cross(db_path, p4["spend_tx"], "usr:erin")
              and tx_cross(db_path, e4["spend_tx"], "usr:dave"))
    act16 = json.loads(snap3["act16"])
    act16_keys = [r["pair_key"] for r in act16["twins"]]
    view4 = json.loads(snap3["view4"])
    board4 = json.loads(snap3["board4"])
    srow4 = settle_row(db_path, ids["t4"], "2026-11")
    ok4 = (cross4
           and counts3["registry"] == 4 and counts3["passes"] == 6
           and counts3["exposures"] == 4
           and counts3["settlements"] == 2
           and counts3["spend_tx"] == 10
           and act16_keys == ["harbor-twins", "lantern-twins"]
           and view4["pass_count"] == 1
           and view4["exposure_count"] == 1
           and view4["ai_label"] == 0
           and board4["passes"][0]["buyer_id"] == "usr:erin"
           and board4["exposures"][0]["merchant_id"] == "usr:dave"
           and m4["sales_total_cent"] == 4 and m4["sales_rows"] == 2
           and m4["window_period"] == "2026-11"
           and srow4 is not None and srow4[0] == m4["id"]
           and srow4[1] == 4
           and snap3["bal_erin"] == 43 and snap3["bal_dave"] == 95
           and snap3["bal_alice"] == 91 and snap3["bal_bob"] == 92
           and snap3["bal_carol"] == 92
           and snap3["bal_reserve"] == 1587)
    record("AC-SCP4", ok4, "continuation on instance 2: fresh twin"
          " lantern-twins registered (4th registry row, ai=%d)"
          " + erin pass @16 (45->%d) + dave exposure @20 (97->%d)"
          " + fresh-chain settle 2026-11 landed (total=%d,"
          " sales_rows=%d, manifest SQL-matched); zero-cache"
          " recompute: act16 twins=%s, view4 counts=%d/%d,"
          " board4 rows erin+dave; balances e=%d d=%d others"
          " frozen; counts registry/passes/exposures/settlements/"
          " spend=%d/%d/%d/%d/%d; digest=%s"
          % (t4["ai_label"], snap3["bal_erin"], snap3["bal_dave"],
             srow4[1], m4["sales_rows"], act16_keys,
             view4["pass_count"], view4["exposure_count"],
             snap3["bal_erin"], snap3["bal_dave"],
             counts3["registry"], counts3["passes"],
             counts3["exposures"], counts3["settlements"],
             counts3["spend_tx"], evidence_digest(snap3)))

    # AC-SCP5: frozen anchor rows + replay gates across restart
    rows_now = raw_rows(db_path)
    ok5a = (rows_now["registry"][:3] == rows1["registry"]
            and rows_now["passes"][:5] == rows1["passes"]
            and rows_now["exposures"][:3] == rows1["exposures"]
            and rows_now["settlements"][:1] == rows1["settlements"])
    bal_b_pre = led2.balance("usr:bob")["balance"]
    ok_reg, code_reg = expect_sc_error(
        lambda: sc2.register_twin("harbor-twins", "New Harbor",
                                  "Old Harbor", 10, 20, 5, 3, 2,
                                  False),
        S.E_SC_DUP_TWIN)
    ok_settle, code_settle = expect_sc_error(
        lambda: sc2.settle_twin_window(
            ids["t1"], "2026-10",
            ["home-admin", "sister-admin"],
            {"home-admin": 50, "sister-admin": 50}),
        S.E_SC_SETTLED)
    bal_b_post = led2.balance("usr:bob")["balance"]
    counts5 = table_counts(db_path)
    ok5 = (ok5a and ok_reg and ok_settle
           and bal_b_post == bal_b_pre and counts5 == counts3)
    record("AC-SCP5", ok5, "anchor rows frozen across restart x"
          " continuation (3 registry rows incl registered_utc, 5"
          " pass rows incl bound spend_tx + purchased_utc, 3"
          " exposure rows, 1 settlement row incl manifest_json +"
          " settled_utc - byte-identical prefixes of the"
          " post-continuation tables, zero UPDATE surface); replay"
          " gates: re-register=%s, re-settle=%s fires from the"
          " persisted settlement row (zero charge %d==%d, zero"
          " rows); counts frozen"
          % (code_reg, code_settle, bal_b_pre, bal_b_post))

    # AC-SCP6: pure-read law
    snap3b = read_battery(sc2, led2, ids)
    counts6 = table_counts(db_path)
    ok6 = (snap3b == snap3 and counts6 == counts3)
    record("AC-SCP6", ok6, "pure-read law: double battery"
          " byte-identical (diffs=%s) and counts constant"
          " (registry=%d passes=%d exposures=%d settlements=%d)"
          % (battery_diffs(snap3, snap3b) or "none",
             counts6["registry"], counts6["passes"],
             counts6["exposures"], counts6["settlements"]))

    # AC-SCP7: third instance stability + hygiene
    sc2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    sc3 = S.SisterCityFace(led3, DISCLAIMER)
    snap4 = read_battery(sc3, led3, ids)
    diffs7 = battery_diffs(snap3, snap4)
    counts7 = table_counts(db_path)
    sha_files = {}
    for name in ("sistercity.py", "settlement.py", "ledger.py",
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
    update_hits = "UPDATE twin_" in open(
        os.path.join(BASE, "sistercity.py"), encoding="utf-8").read()
    ok7 = (not diffs7 and counts7 == counts3
           and sha_files["config.json"]
           == hashlib.sha256(cfg_bytes).hexdigest()
           and non_ascii == 0 and not net_hits and not in_repo
           and not update_hits)
    record("AC-SCP7", ok7, "instance 3 on same db: battery diffs=%s;"
          " counts stable registry=%d passes=%d exposures=%d"
          " settlements=%d; shipped files untouched"
          " (sistercity/settlement/ledger/config sha256 stable);"
          " non-ascii=%d; network-imports=%s; world outside"
          " repo=%s; sistercity module zero UPDATE surface=%s"
          % (diffs7 or "none", counts7["registry"],
             counts7["passes"], counts7["exposures"],
             counts7["settlements"], non_ascii,
             net_hits or "none", str(not in_repo).lower(),
             str(not update_hits).lower()))

    sc3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
