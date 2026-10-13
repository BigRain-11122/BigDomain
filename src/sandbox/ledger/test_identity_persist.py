"""Cross-restart persistence window for the city identity paid
face (BigDomain R1943; the identity seat of the R1886 persist
family - the R1938-seeded row, criteria AC-IDP1..AC-IDP7
pre-registered in the R1943 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world
(four-product identity registry + one private-room rental + three
permanent claims, every spend SQL-crossed) -> reverse-order close
of all four faces -> reopen the same db/config -> byte-identical
read replay (derived profile/holder faces have zero in-memory
drift) -> fifteen restart-surviving gate probes (fail-closed,
zero charge, zero rows; insufficient-balance rides the wrap-default
E_ID_BAD_ARGS surface per the identity-domain wrap law) ->
post-restart real-path continuation (bob's advance room renewal
month 11 + carol's gold-crown claim, both bound to real new spend
txs, zero-cache recompute) -> frozen registry/occupancy/inventory
faces + idempotent re-register + taken-gate across restart ->
pure-read law -> third instance stability.

Read faces replay stored values only (month windows and stored
spend tx ids, never clock echoes), so full-dump byte identity
holds without clock freezing; tx ids are content-addressed and
embed a timestamp, so evidence digests mask 16-hex ids and ISO
timestamps (deterministic double-run stdout; R1941 mask law).

Registry immutability law (design ruling 2): identity_products
rows are write-once (no UPDATE surface in the module); the
idempotent re-register returns without touching a single byte.

Stdlib only; this source stays pure ASCII (encoding
discipline). Usage: python test_identity_persist.py
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

import ledger as L               # noqa: E402 (P-47-2b core)
import venue as V                # noqa: E402 (R605 engine)
import props as P                # noqa: E402 (R599 engine)
import identity as ID            # noqa: E402 (R624 wrapped API)

RESULTS = []

_MASKS = (
    (re.compile(r'"[0-9a-f]{16}"'), '"<tx>"'),
    (re.compile(r'"20\d\d-\d\d-\d\dT[^"]*"'), '"<ts>"'),
)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_id_error(fn, *codes):
    try:
        fn()
    except ID.IdentityError as exc:
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


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    out["identity_products"] = int(conn.execute(
        "SELECT COUNT(*) FROM identity_products").fetchone()[0])
    out["venue_registry"] = int(conn.execute(
        "SELECT COUNT(*) FROM venue_registry").fetchone()[0])
    out["occ_storefront"] = int(conn.execute(
        "SELECT COUNT(*) FROM venue_occupancy"
        " WHERE kind = 'storefront'").fetchone()[0])
    out["props_inventory"] = int(conn.execute(
        "SELECT COUNT(*) FROM props_inventory").fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def registry_rows_snapshot(db_path):
    """Full-row SQL snapshot of the identity registry (freeze-law
    carrier: product_id, id_kind, registered_utc; write-once, no
    UPDATE surface in the module)."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT product_id, id_kind, registered_utc"
        " FROM identity_products ORDER BY product_id").fetchall()
    conn.close()
    return rows


def occ_rows_snapshot(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT occ_id, kind, unit_id, account_id, start_tick,"
        " end_tick, bound_spend_tx, terminated_tick, created_utc"
        " FROM venue_occupancy ORDER BY occ_id").fetchall()
    conn.close()
    return rows


def inv_rows_snapshot(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT inv_id, account_id, item_id, kind, count_credits,"
        " bound_spend_tx, granted_utc FROM props_inventory"
        " ORDER BY inv_id").fetchall()
    conn.close()
    return rows


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the purchasing account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(idf, led):
    return {
        "prof_a10": dump(idf.identity_profile("usr:alice", 10)),
        "prof_b10": dump(idf.identity_profile("usr:bob", 10)),
        "prof_b11": dump(idf.identity_profile("usr:bob", 11)),
        "prof_c10": dump(idf.identity_profile("usr:carol", 10)),
        "holder_10": idf.room_holder("room:sky-loft", 10),
        "holder_11": idf.room_holder("room:sky-loft", 11),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def build_world(tmp, cfg):
    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    prp = P.PropsFace(led)
    idf = ID.IdentityFace(led, ven, prp)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-IDP-1", "settlement")
    for acct in ("usr:alice", "usr:bob", "usr:carol"):
        led.ensure_account(acct, census_avatar_id=acct[4:])
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 500), ("usr:bob", "credit", 500)],
               "manual:fund-b", "suite funding bob")
    led.adjust([("pool:reserve", "debit", 400), ("usr:carol", "credit", 400)],
               "manual:fund-c", "suite funding carol")
    return led, ven, prp, idf, db_path


def close_all(idf, ven, prp, led):
    idf.close()
    ven.close()
    prp.close()
    led.close()


def main():
    tmp = tempfile.mkdtemp(prefix="identity-persist-")
    cfg_bytes = open(os.path.join(BASE, "config.json"), "rb").read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    cfg_sha_before = hashlib.sha256(cfg_bytes).hexdigest()

    led, ven, prp, idf, db_path = build_world(tmp, cfg)

    # -- anchor world ---------------------------------------------------
    idf.register_identity_product("room:sky-loft", "private_room")
    idf.register_identity_product("skin:neon-dragon", "avatar_skin")
    idf.register_identity_product("plaque:creator-01", "creator_plaque")
    idf.register_identity_product("plaque:floor-premium", "floor_plaque")
    idf.register_identity_product("skin:gold-crown", "avatar_skin")
    rent_a = idf.rent_private_room("usr:alice", "room:sky-loft", 10, 80,
                                   "order:idp1-rent-a")
    claim_a = idf.claim_permanent("usr:alice", "skin:neon-dragon", 30,
                                  "order:idp1-skin-a")
    claim_b = idf.claim_permanent("usr:bob", "plaque:creator-01", 50,
                                  "order:idp1-plaque-b")
    claim_c = idf.claim_permanent("usr:carol", "plaque:floor-premium", 199,
                                  "order:idp1-floor-c")

    snap1 = read_battery(idf, led)
    counts1 = table_counts(db_path)
    registry_anchor = registry_rows_snapshot(db_path)
    occ_anchor = occ_rows_snapshot(db_path)
    inv_anchor = inv_rows_snapshot(db_path)

    # AC-IDP1: anchor world + read battery + spend-bound provenance
    ok1 = (rent_a["fee"] == 80 and rent_a["month"] == 10
           and rent_a["window"] == [10, 10]
           and claim_a["id_kind"] == "avatar_skin"
           and claim_b["id_kind"] == "creator_plaque"
           and claim_c["id_kind"] == "floor_plaque"
           and counts1["identity_products"] == 5
           and counts1["venue_registry"] == 1
           and counts1["occ_storefront"] == 1
           and counts1["props_inventory"] == 3
           and counts1["spend_tx"] == 4
           and snap1["bal_alice"] == 190 and snap1["bal_bob"] == 450
           and snap1["bal_carol"] == 201 and snap1["bal_pool"] == 19159
           and snap1["holder_10"] == "usr:alice"
           and snap1["holder_11"] is None)
    cross = []
    for tx, acct in ((rent_a["spend_tx"], "usr:alice"),
                     (claim_a["spend_tx"], "usr:alice"),
                     (claim_b["spend_tx"], "usr:bob"),
                     (claim_c["spend_tx"], "usr:carol")):
        head, leg = spend_cross(db_path, tx, acct)
        cross.append((head == "spend" and leg == "debit"))
    prof_a10 = json.loads(snap1["prof_a10"])
    prof_b10 = json.loads(snap1["prof_b10"])
    prof_c10 = json.loads(snap1["prof_c10"])
    ok1 = (ok1 and all(cross) and len(cross) == 4
           and len(prof_a10["rooms"]) == 1
           and prof_a10["rooms"][0]["room_id"] == "room:sky-loft"
           and prof_a10["rooms"][0]["month"] == 10
           and [p["product_id"] for p in prof_a10["permanents"]]
           == ["skin:neon-dragon"]
           and [p["product_id"] for p in prof_b10["permanents"]]
           == ["plaque:creator-01"]
           and not prof_b10["rooms"]
           and [p["product_id"] for p in prof_c10["permanents"]]
           == ["plaque:floor-premium"]
           and len(registry_anchor) == 5)
    record("AC-IDP1", ok1, "anchor world: registry=%d venue_reg=%d "
          "occ=%d inv=%d spend_tx=%d; balances a/b/c/pool=%d/%d/%d/%d; "
          "4 spends SQL-crossed spend+debit %d/4; holder m10=%s m11=%s; "
          "profiles rooms a=1 b=0 perms a/b/c=%d/%d/%d; digest=%s"
          % (counts1["identity_products"], counts1["venue_registry"],
             counts1["occ_storefront"], counts1["props_inventory"],
             counts1["spend_tx"], snap1["bal_alice"], snap1["bal_bob"],
             snap1["bal_carol"], snap1["bal_pool"], sum(cross),
             snap1["holder_10"], snap1["holder_11"],
             len(prof_a10["permanents"]), len(prof_b10["permanents"]),
             len(prof_c10["permanents"]), evidence_digest(snap1)))

    # AC-IDP2: reverse-order close -> reopen -> byte-identical replay
    close_all(idf, ven, prp, led)
    led2 = L.Ledger(db_path, cfg)
    ven2 = V.VenueFace(led2)
    prp2 = P.PropsFace(led2)
    idf2 = ID.IdentityFace(led2, ven2, prp2)
    snap2 = read_battery(idf2, led2)
    diffs2 = battery_diffs(snap1, snap2)
    record("AC-IDP2", not diffs2, "instance 2 replay on same db/config: "
          "battery diffs=%s (derived profile/holder faces zero "
          "in-memory drift)" % (diffs2 or "none"))

    # AC-IDP3: fifteen restart-surviving gate probes (fail-closed)
    probes = []
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:alice", "room:ghost", 20,
                                        50, "order:idp3-unknown-room"),
        ID.E_ID_UNKNOWN))
    probes.append(expect_id_error(
        lambda: idf2.claim_permanent("usr:alice", "skin:ghost", 20,
                                     "order:idp3-unknown-skin"),
        ID.E_ID_UNKNOWN))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:alice", "skin:neon-dragon",
                                        20, 50, "order:idp3-kind-rent"),
        ID.E_ID_KIND_MISMATCH))
    probes.append(expect_id_error(
        lambda: idf2.claim_permanent("usr:alice", "room:sky-loft", 50,
                                     "order:idp3-kind-claim"),
        ID.E_ID_KIND_MISMATCH))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:alice", "room:sky-loft",
                                        -1, 80, "order:idp3-neg-month"),
        ID.E_ID_BAD_ARGS))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("corp:acme", "room:sky-loft", 20,
                                        80, "order:idp3-corp"),
        ID.E_ID_BAD_ARGS))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:alice", "room:sky-loft", 20,
                                        0, "order:idp3-zero-price"),
        ID.E_ID_BAD_ARGS))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:alice", "room:sky-loft", 20,
                                        80, "   "),
        ID.E_ID_BAD_ARGS))
    probes.append(expect_id_error(
        lambda: idf2.register_identity_product("ship:star", "spaceship"),
        ID.E_ID_BAD_ARGS))
    probes.append(expect_id_error(
        lambda: idf2.register_identity_product("", "avatar_skin"),
        ID.E_ID_BAD_ARGS))
    probes.append(expect_id_error(
        lambda: idf2.register_identity_product("room:sky-loft",
                                               "avatar_skin"),
        ID.E_ID_KIND_MISMATCH))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:bob", "room:sky-loft", 10,
                                        90, "order:idp3-taken"),
        ID.E_ID_TAKEN))
    probes.append(expect_id_error(
        lambda: idf2.rent_private_room("usr:alice", "room:sky-loft", 10,
                                       80, "order:idp3-dup-window"),
        ID.E_ID_DUP))
    probes.append(expect_id_error(
        lambda: idf2.claim_permanent("usr:carol", "plaque:floor-premium",
                                     199, "order:idp3-dup-plaque"),
        ID.E_ID_DUP))
    probes.append(expect_id_error(
        lambda: idf2.claim_permanent("usr:bob", "skin:gold-crown", 99999,
                                     "order:idp3-insufficient"),
        ID.E_ID_BAD_ARGS))               # wrap-default surface law
    counts_after_probes = table_counts(db_path)
    snap_after_probes = read_battery(idf2, led2)
    ok3 = (all(p[0] for p in probes)
           and counts_after_probes == counts1
           and not battery_diffs(snap1, snap_after_probes))
    record("AC-IDP3", ok3, "15 restart-surviving probes all-reject "
          "[%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s] "
          "fail-closed: counts frozen %s and battery frozen (zero "
          "charge zero rows zero drift)"
          % tuple([p[1] for p in probes]
                  + ["reg=%d occ=%d inv=%d spend=%d"
                     % (counts_after_probes["identity_products"],
                        counts_after_probes["occ_storefront"],
                        counts_after_probes["props_inventory"],
                        counts_after_probes["spend_tx"])]))

    # AC-IDP4: post-restart real-path continuation (zero cache)
    renew_b = idf2.rent_private_room("usr:bob", "room:sky-loft", 11, 80,
                                     "order:idp4-renew-b")
    crown_c = idf2.claim_permanent("usr:carol", "skin:gold-crown", 30,
                                   "order:idp4-crown-c")
    rb_head, rb_leg = spend_cross(db_path, renew_b["spend_tx"], "usr:bob")
    cc_head, cc_leg = spend_cross(db_path, crown_c["spend_tx"],
                                  "usr:carol")
    snap3 = read_battery(idf2, led2)
    counts3 = table_counts(db_path)
    prof_b11 = json.loads(snap3["prof_b11"])
    prof_c10_3 = json.loads(snap3["prof_c10"])
    moved3 = battery_diffs(snap2, snap3)
    ok4 = (rb_head == "spend" and rb_leg == "debit"
           and cc_head == "spend" and cc_leg == "debit"
           and renew_b["window"] == [11, 11]
           and snap3["holder_11"] == "usr:bob"
           and snap3["holder_10"] == "usr:alice"
           and len(prof_b11["rooms"]) == 1
           and prof_b11["rooms"][0]["month"] == 11
           and [p["product_id"] for p in prof_c10_3["permanents"]]
           == ["plaque:floor-premium", "skin:gold-crown"]
           and counts3["occ_storefront"] == 2
           and counts3["props_inventory"] == 4
           and counts3["spend_tx"] == 6
           and counts3["identity_products"] == 5
           and snap3["bal_alice"] == 190 and snap3["bal_bob"] == 370
           and snap3["bal_carol"] == 171 and snap3["bal_pool"] == 19269
           and len(moved3) >= 5)
    record("AC-IDP4", ok4, "continuation on instance 2: bob renewal "
          "m11 + carol gold-crown both real spend tx SQL-crossed "
          "(%s+%s, %s+%s); zero-cache recompute holder m10=%s m11=%s "
          "bob profile m11 rooms=1@11; carol perms=%d; counts "
          "occ=%d inv=%d spend=%d reg=%d; balances a/b/c/pool=%d/%d/%d/%d; "
          "battery cells moved=%d; digest=%s"
          % (rb_head, rb_leg, cc_head, cc_leg, snap3["holder_10"],
             snap3["holder_11"], len(prof_c10_3["permanents"]),
             counts3["occ_storefront"], counts3["props_inventory"],
             counts3["spend_tx"], counts3["identity_products"],
             snap3["bal_alice"], snap3["bal_bob"], snap3["bal_carol"],
             snap3["bal_pool"], len(moved3), evidence_digest(snap3)))

    # AC-IDP5: frozen registry/occupancy/inventory + idempotent
    # re-register + taken gate across restart x continuation
    registry_now = registry_rows_snapshot(db_path)
    occ_now = occ_rows_snapshot(db_path)
    inv_now = inv_rows_snapshot(db_path)
    frozen_reg = (registry_now == registry_anchor)
    occ_anchor_ids = {r[0] for r in occ_anchor}
    frozen_occ = all(occ_now[i] == occ_anchor[i]
                     for i in range(len(occ_anchor)))
    new_occ = [r for r in occ_now if r[0] not in occ_anchor_ids]
    inv_anchor_keys = {(r[1], r[2]) for r in inv_anchor}
    frozen_inv = all(row == inv_anchor[i]
                     for i, row in enumerate(inv_now)
                     if (row[1], row[2]) in inv_anchor_keys)
    idem = idf2.register_identity_product("room:sky-loft",
                                          "private_room")
    registry_after_idem = registry_rows_snapshot(db_path)
    bal_pre = led2.balance("usr:carol")["balance"]
    ok_taken, code_taken = expect_id_error(
        lambda: idf2.rent_private_room("usr:carol", "room:sky-loft", 10,
                                       95, "order:idp5-taken"),
        ID.E_ID_TAKEN)
    bal_post = led2.balance("usr:carol")["balance"]
    counts5 = table_counts(db_path)
    ok5 = (frozen_reg and frozen_occ and len(new_occ) == 1
           and frozen_inv and idem == {"product_id": "room:sky-loft",
                                       "id_kind": "private_room",
                                       "idempotent": True}
           and registry_after_idem == registry_anchor
           and ok_taken and bal_post == bal_pre
           and counts5 == counts3)
    record("AC-IDP5", ok5, "frozen faces across restart x "
          "continuation: registry 5 rows byte-frozen=%s; occupancy "
          "anchor row byte-frozen=%s (+%d new row only); inventory "
          "anchor rows frozen=%s; idempotent re-register "
          "idempotent=True zero row change; taken re-rent m10 "
          "rejected %s zero charge (%d==%d); counts stable %s"
          % (str(frozen_reg).lower(), str(frozen_occ).lower(),
             len(new_occ), str(frozen_inv).lower(), code_taken,
             bal_pre, bal_post,
             "occ=%d inv=%d spend=%d"
             % (counts5["occ_storefront"], counts5["props_inventory"],
                counts5["spend_tx"])))

    # AC-IDP6: pure-read law
    snap3b = read_battery(idf2, led2)
    counts6 = table_counts(db_path)
    ok6 = (snap3b == snap3 and counts6 == counts3)
    record("AC-IDP6", ok6, "pure-read law: double battery "
          "byte-identical (diffs=%s) and counts constant %s"
          % (battery_diffs(snap3, snap3b) or "none",
             "occ=%d inv=%d spend=%d"
             % (counts6["occ_storefront"], counts6["props_inventory"],
                counts6["spend_tx"])))

    # AC-IDP7: third instance stability + hygiene
    close_all(idf2, ven2, prp2, led2)
    led3 = L.Ledger(db_path, cfg)
    ven3 = V.VenueFace(led3)
    prp3 = P.PropsFace(led3)
    idf3 = ID.IdentityFace(led3, ven3, prp3)
    snap4 = read_battery(idf3, led3)
    diffs7 = battery_diffs(snap3, snap4)
    counts7 = table_counts(db_path)
    cfg_sha_after = hashlib.sha256(
        open(os.path.join(BASE, "config.json"), "rb").read()).hexdigest()
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
           and cfg_sha_after == cfg_sha_before
           and non_ascii == 0 and not net_hits and not in_repo)
    record("AC-IDP7", ok7, "instance 3 on same db: battery diffs=%s; "
          "counts stable reg=%d occ=%d inv=%d spend=%d; config sha "
          "unchanged=%s; non-ascii=%d; network-imports=%s; world "
          "outside repo=%s"
          % (diffs7 or "none", counts7["identity_products"],
             counts7["occ_storefront"], counts7["props_inventory"],
             counts7["spend_tx"],
             str(cfg_sha_after == cfg_sha_before).lower(),
             non_ascii, net_hits or "none", str(not in_repo).lower()))

    idf3.close()
    ven3.close()
    prp3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
