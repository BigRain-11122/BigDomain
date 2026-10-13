"""Cross-restart persistence window for the city digital
collectibles face (BigDomain R1931; the collectibles seat of the
R1742 family - curation regpersist R1926 and civic persist R1927 are
in-book while this seat was absent). Asserts the pre-registered
criteria AC-CLP1..AC-CLP7 from the R1931 tech.md claim row (criteria
were registered before this code existed; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay -> post-restart real-path continuation -> UNIQUE gate
survival -> cap-lock authority -> third instance stability. Read
faces carry no timestamp echo so byte-identity is deterministic
without clock freezing.

Usage: python test_collectibles_persist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import collectibles as C    # noqa: E402  (R619 extension face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


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


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    out = {}
    for tbl in ("collectibles", "cl_editions", "ledger_tx", "ledger_entries"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    conn.close()
    return out


def read_faces(cf, led):
    return {
        "col_alice": dump(cf.collection("usr:alice")),
        "col_bob": dump(cf.collection("usr:bob")),
        "col_carol": dump(cf.collection("usr:carol")),
        "ed_2026": dump(cf.edition_status("card_2026")),
        "ed_2027": dump(cf.edition_status("card_2027")),
        "ed_2028": dump(cf.edition_status("card_2028")),
        "ed_unknown": dump(cf.edition_status("card_never")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def main():
    tmp = tempfile.mkdtemp(prefix="collectibles-persist-")
    cfg_text = io_open_config_raw()
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    coll_sha_before = sha16(io_open_module("collectibles.py"))
    led_sha_before = sha16(io_open_module("ledger.py"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    led.mint_to_pool("pool:reserve", 1000, "SETTLE-CLP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.ensure_account("usr:dave", census_avatar_id="dave")
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:clp-fund-a", "persist window funding alice")
    led.adjust([("pool:reserve", "debit", 120), ("usr:bob", "credit", 120)],
               "manual:clp-fund-b", "persist window funding bob")

    # ---- AC-CLP1: anchor world, real paths, pre-close snapshot -----
    cf.issue_certificate("usr:alice", "bld:harbor-gate:complete",
                         "cert_harbor_gate")
    cf.buy_replay_right("usr:alice", "chrono:2026-q1-parade", 25,
                        "order:clp-a")
    c1 = cf.claim_card("usr:alice", "card_2026", "resident_card", 3,
                       "per-clp-1")
    c2 = cf.claim_card("usr:bob", "card_2026", "resident_card", 3,
                       "per-clp-2")
    b1 = cf.claim_card("usr:bob", "card_2027", "resident_card", 2,
                       "per-clp-3")
    cc1 = cf.claim_card("usr:carol", "card_2027", "resident_card", 2,
                        "per-clp-4")
    e1 = cf.claim_card("usr:alice", "card_2028", "resident_card", 5,
                       "per-clp-5")
    ok_sold_pre, code_sold_pre = expect_cl_error(
        lambda: cf.claim_card("usr:dave", "card_2027", "resident_card", 2,
                               "per-clp-6"), C.E_CL_SOLD_OUT)
    ok_dupc_pre, code_dupc_pre = expect_cl_error(
        lambda: cf.issue_certificate(
            "usr:alice", "bld:harbor-gate:complete", "cert_harbor_gate"),
        C.E_CL_DUP)
    ok_dupk_pre, code_dupk_pre = expect_cl_error(
        lambda: cf.claim_card("usr:alice", "card_2026", "resident_card", 3,
                              "per-clp-7"), C.E_CL_DUP)
    snap = read_faces(cf, led)
    cnt1 = table_counts(db_path)
    col_a = json.loads(snap["col_alice"])
    col_b = json.loads(snap["col_bob"])
    col_c = json.loads(snap["col_carol"])
    ok1 = (c1["card_no"] == 1 and c2["card_no"] == 2
           and b1["card_no"] == 1 and cc1["card_no"] == 2
           and e1["card_no"] == 1 and e1["cap"] == 5
           and len(col_a["certificates"]) == 1
           and len(col_a["replays"]) == 1 and len(col_a["cards"]) == 2
           and len(col_b["cards"]) == 2 and len(col_b["replays"]) == 0
           and len(col_c["cards"]) == 1
           and json.loads(snap["ed_2026"]) == {"edition": "card_2026",
                                              "cap": 3, "issued": 2}
           and json.loads(snap["ed_2027"]) == {"edition": "card_2027",
                                              "cap": 2, "issued": 2}
           and json.loads(snap["ed_2028"]) == {"edition": "card_2028",
                                              "cap": 5, "issued": 1}
           and json.loads(snap["ed_unknown"]) == {"edition": "card_never",
                                                  "cap": None, "issued": 0}
           and snap["bal_alice"] == 275 and snap["bal_bob"] == 120
           and snap["bal_carol"] == 0
           and ok_sold_pre and ok_dupc_pre and ok_dupk_pre
           and cnt1["collectibles"] == 7 and cnt1["cl_editions"] == 3)
    record("AC-CLP1", ok1,
           "anchor world 7 rows/3 editions; numbering 2026=#1/#2, "
           "2027=#1/#2 (full), 2028=#1 cap locked 5; balances "
           "alice=%d bob=%d carol=%d; pre-close gates sold_out=%s "
           "dup_cert=%s dup_card=%s; snapshot sha16 %s"
           % (snap["bal_alice"], snap["bal_bob"], snap["bal_carol"],
              code_sold_pre, code_dupc_pre, code_dupk_pre,
              sha16(dump(snap))))

    # ---- AC-CLP2: close -> reopen -> byte-identical replay --------
    cf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    cf2 = C.CollectiblesFace(led2)
    snap2_open = read_faces(cf2, led2)
    diffs = [k for k in snap if snap[k] != snap2_open[k]]
    ok2 = not diffs
    record("AC-CLP2", ok2,
           "instance2 same db/config replays all 11 snapshot values "
           "byte-identical (diff keys=%s, snapshot sha16 %s)"
           % (diffs if diffs else "none", sha16(dump(snap2_open))))

    # ---- AC-CLP3: post-restart real-path continuation -------------
    r3 = cf2.claim_card("usr:carol", "card_2026", "resident_card", 3,
                        "per-clp-8")
    ok_sold3, code_sold3 = expect_cl_error(
        lambda: cf2.claim_card("usr:dave", "card_2026", "resident_card", 3,
                                "per-clp-9"), C.E_CL_SOLD_OUT)
    buy3 = cf2.buy_replay_right("usr:bob", "chrono:2026-q2-festival", 20,
                                "order:clp-b")
    cf2.issue_certificate("usr:bob", "bld:observatory:complete",
                          "cert_observatory")
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                       (buy3["spend_tx_id"],)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ? AND"
        " account_id = 'usr:bob'", (buy3["spend_tx_id"],)).fetchone()
    conn.close()
    col_b_after = cf2.collection("usr:bob")
    ed_2026_after = cf2.edition_status("card_2026")
    ok3 = (r3["card_no"] == 3 and ok_sold3
           and ed_2026_after["issued"] == 3 and ed_2026_after["cap"] == 3
           and len(col_b_after["replays"]) == 1
           and col_b_after["replays"][0]["event_ref"] ==
           "chrono:2026-q2-festival"
           and len(col_b_after["certificates"]) == 1
           and led2.balance("usr:bob")["balance"] == 100
           and head is not None and head[0] == "spend"
           and leg is not None and leg[0] == "debit")
    record("AC-CLP3", ok3,
           "post-restart continuation: carol claim continues numbering "
           "#3 (issued 2->3 durable), dave 4th claim sold out %s (3/3 "
           "cap survives), bob replay 20 charges 120->100 bound to real "
           "spend tx (%s/%s), bob new cert appends; touched faces "
           "re-read changed zero-cache" % (code_sold3,
                                           head[0] if head else "MISSING",
                                           leg[0] if leg else "MISSING"))

    # ---- AC-CLP4: UNIQUE gate survival across restart --------------
    cnt4_before = table_counts(db_path)
    bal4_before = led2.balance("usr:alice")["balance"]
    ok_dup4a, code_dup4a = expect_cl_error(
        lambda: cf2.issue_certificate(
            "usr:alice", "bld:harbor-gate:complete", "cert_harbor_gate"),
        C.E_CL_DUP)
    ok_dup4b, code_dup4b = expect_cl_error(
        lambda: cf2.claim_card("usr:alice", "card_2026", "resident_card",
                               3, "per-clp-10"), C.E_CL_DUP)
    ok_dup4c, code_dup4c = expect_cl_error(
        lambda: cf2.buy_replay_right("usr:alice", "chrono:2026-q1-parade",
                                     25, "order:clp-c"), C.E_CL_DUP)
    ok_dup4d, code_dup4d = expect_cl_error(
        lambda: cf2.claim_card("usr:carol", "card_2027", "resident_card",
                               2, "per-clp-11"), C.E_CL_DUP)
    cnt4_after = table_counts(db_path)
    bal4_after = led2.balance("usr:alice")["balance"]
    ok4 = (ok_dup4a and ok_dup4b and ok_dup4c and ok_dup4d
           and cnt4_before == cnt4_after and bal4_before == bal4_after)
    record("AC-CLP4", ok4,
           "post-restart dup gates all reject: cert=%s card=%s "
           "replay(same event, fresh ref)=%s card2027=%s; 4-table "
           "counts constant %s; balance zero-moved (%d==%d)"
           % (code_dup4a, code_dup4b, code_dup4c, code_dup4d,
              cnt4_after, bal4_before, bal4_after))

    # ---- AC-CLP5: cap-lock authority survives restart ---------------
    r5 = cf2.claim_card("usr:bob", "card_2028", "resident_card", 99,
                        "per-clp-12")
    st5 = cf2.edition_status("card_2028")
    ok5 = (r5["card_no"] == 2 and r5["cap"] == 5
           and st5 == {"edition": "card_2028", "cap": 5, "issued": 2})
    record("AC-CLP5", ok5,
           "post-restart claim with divergent cap=99 succeeds under the "
           "locked row: card_no=%d echo cap=%d (divergent arg ignored); "
           "edition status cap=%d issued=%d" % (r5["card_no"], r5["cap"],
                                                st5["cap"], st5["issued"]))

    # ---- AC-CLP6: pure-read law + double-restart stability ----------
    snap_post = read_faces(cf2, led2)
    cnt6_before = table_counts(db_path)
    for _ in range(2):
        read_faces(cf2, led2)
    cnt6_after = table_counts(db_path)
    cf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    cf3 = C.CollectiblesFace(led3)
    snap3 = read_faces(cf3, led3)
    diffs6 = [k for k in snap_post if snap_post[k] != snap3[k]]
    ok6 = (cnt6_before == cnt6_after and not diffs6)
    record("AC-CLP6", ok6,
           "read battery leaves all 4 table counts constant %s; third "
           "instance replays the post-continuation state byte-identical "
           "(diff keys=%s, sha16 %s)" % (cnt6_after,
                                         diffs6 if diffs6 else "none",
                                         sha16(dump(snap3))))

    # ---- AC-CLP7: hygiene -------------------------------------------
    cfg_sha_after = sha16(io_open_config_raw())
    coll_sha_after = sha16(io_open_module("collectibles.py"))
    led_sha_after = sha16(io_open_module("ledger.py"))
    with open(os.path.join(os.path.dirname(BASE), "reconcile_all.py"),
              encoding="utf-8") as h:
        reg_src = h.read()
    reg_ok = ('"ledger-collectibles-persist"' in reg_src
              and '"test_collectibles_persist.py"), 7)' in reg_src)
    with open(os.path.abspath(__file__), encoding="utf-8") as h:
        own_src = h.read()
    non_ascii = sum(1 for ch in own_src if ord(ch) > 127)
    import_lines = [ln for ln in own_src.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    network = [ln for ln in import_lines
               if any(w in ln for w in ("urllib", "requests", "socket",
                                        "http"))]
    ok7 = (cfg_sha_before == cfg_sha_after
           and coll_sha_before == coll_sha_after
           and led_sha_before == led_sha_after
           and reg_ok and non_ascii == 0 and not network
           and tmp.startswith(tempfile.gettempdir()))
    record("AC-CLP7", ok7,
           "shipped config sha16 stable %s; collectibles.py/ledger.py "
           "sha16 stable (%s/%s vs %s/%s); SUITES registration row "
           "present=%s; own source pure-ascii=%d network-imports=%d; "
           "world tmp outside repo=%s"
           % (cfg_sha_after, coll_sha_before, coll_sha_after,
              led_sha_before, led_sha_after, reg_ok, non_ascii,
              len(network), tmp.startswith(tempfile.gettempdir())))

    cf3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


def io_open_config():
    return open(os.path.join(BASE, "config.json"), encoding="utf-8")


def io_open_config_raw():
    with io_open_config() as h:
        return h.read()


def io_open_module(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as h:
        return h.read()


if __name__ == "__main__":
    main()
