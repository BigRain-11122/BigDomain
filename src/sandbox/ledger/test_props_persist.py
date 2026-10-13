"""Cross-restart persistence window for the city prop/cosmetic
inventory face (BigDomain R1942; the props seat of the R1886
persist family - the R1937-seeded row, criteria AC-PSP1..PSP7
pre-registered in the R1942 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay (derived faces have zero in-memory drift) ->
restart-surviving gate probes (fail-closed, zero rows) ->
post-restart real-path continuation (new spend-bound grant,
credit consume + stack re-purchase on two riders) -> frozen
provenance faces + dup gate across restart -> pure-read law ->
third instance stability.

The inventory face replays stored values only (bound_spend_tx
and count_credits are stored columns, never clock echoes), so
full-dump byte identity holds without clock freezing. tx ids
are content-addressed and embed a timestamp, so evidence
digests mask 16-hex ids and ISO timestamps (deterministic
double-run stdout; R1941 mask law).

Provenance freeze law (design ruling 3): the stack re-purchase
path only UPDATEs count_credits; bound_spend_tx and granted_utc
stay bound to the first purchase across restarts and
continuation writes.

Stdlib only; this source stays pure ASCII (encoding
discipline). Usage: python test_props_persist.py
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
import props as P                # noqa: E402 (R599 extension face)

RESULTS = []

_MASKS = (
    (re.compile(r'"[0-9a-f]{16}"'), '"<tx>"'),
    (re.compile(r'"20\d\d-\d\d-\d\dT[^"]*"'), '"<ts>"'),
)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_prop_error(fn, *codes):
    try:
        fn()
    except P.PropError as exc:
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


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    out["props_inventory"] = int(conn.execute(
        "SELECT COUNT(*) FROM props_inventory").fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    out["ledger_entries"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_entries").fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def inventory_rows_snapshot(db_path):
    """Full-row SQL snapshot of the props table (freeze-law
    carrier: inv_id, account_id, item_id, kind, count_credits,
    bound_spend_tx, granted_utc)."""
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


def read_battery(pf, led):
    return {
        "inv_a": dump(pf.inventory("usr:alice")),
        "inv_b": dump(pf.inventory("usr:bob")),
        "inv_c": dump(pf.inventory("usr:carol")),
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
    pf = P.PropsFace(led)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-PSP-1", "settlement")
    for acct in ("usr:alice", "usr:bob", "usr:carol"):
        led.ensure_account(acct, census_avatar_id=acct[4:])
    led.adjust([("pool:reserve", "debit", 300), ("usr:alice", "credit", 300)],
               "manual:fund-a", "suite funding alice")
    led.adjust([("pool:reserve", "debit", 500), ("usr:bob", "credit", 500)],
               "manual:fund-b", "suite funding bob")
    led.adjust([("pool:reserve", "debit", 400), ("usr:carol", "credit", 400)],
               "manual:fund-c", "suite funding carol")
    return led, pf, db_path


def main():
    tmp = tempfile.mkdtemp(prefix="props-persist-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg_bytes = open(os.path.join(BASE, "config.json"), "rb").read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    cfg_sha_before = hashlib.sha256(cfg_bytes).hexdigest()

    led, pf, db_path = build_world(tmp, cfg)

    # -- anchor world ---------------------------------------------------
    pf.buy_prop("usr:alice", "hat_gold", "cosmetic", 15, "order:psp1-hat")
    pf.buy_prop("usr:alice", "jetpack", "prop", 20, "order:psp1-jet",
                count=3)
    pf.buy_prop("usr:bob", "flare", "prop", 10, "order:psp1-flare",
                count=2)
    pf.consume_prop("usr:bob", "flare", 1)          # 2 -> 1
    pf.buy_prop("usr:carol", "scarf_silk", "cosmetic", 12, "order:psp1-scarf")

    snap1 = read_battery(pf, led)
    counts1 = table_counts(db_path)
    rows_anchor = inventory_rows_snapshot(db_path)

    # AC-PSP1: anchor world + read battery + spend-bound provenance
    ok1 = (counts1["props_inventory"] == 4 and counts1["spend_tx"] == 4
           and snap1["bal_alice"] == 265 and snap1["bal_bob"] == 490
           and snap1["bal_carol"] == 388 and snap1["bal_pool"] == 18857)
    cross = []
    for acct, item in (("usr:alice", "hat_gold"), ("usr:alice", "jetpack"),
                       ("usr:bob", "flare"), ("usr:carol", "scarf_silk")):
        inv = pf.inventory(acct)
        tx = inv["bound_spend_tx"][item]
        head, leg = spend_cross(db_path, tx, acct)
        cross.append((head == "spend" and leg == "debit"))
    ok1 = ok1 and all(cross) and len(cross) == 4
    jet = [p for p in json.loads(snap1["inv_b"])]
    del jet  # placeholder guard: inv_b parsed only for shape sanity
    flare_credits = json.loads(snap1["inv_b"])["props"][0]["count_credits"]
    ok1 = ok1 and flare_credits == 1
    record("AC-PSP1", ok1, "anchor world 4 grants all spend-bound "
          "(spend+debit 4/4); counts inv=%d spend_tx=%d; balances "
          "a/b/c/pool=%d/%d/%d/%d; flare credits=%d; digest=%s"
          % (counts1["props_inventory"], counts1["spend_tx"],
             snap1["bal_alice"], snap1["bal_bob"], snap1["bal_carol"],
             snap1["bal_pool"], flare_credits,
             evidence_digest(snap1)))

    # AC-PSP2: close -> reopen -> byte-identical replay
    pf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    pf2 = P.PropsFace(led2)
    snap2 = read_battery(pf2, led2)
    diffs2 = battery_diffs(snap1, snap2)
    record("AC-PSP2", not diffs2, "instance 2 replay on same db/config: "
          "battery diffs=%s (derived faces zero in-memory drift)"
          % (diffs2 or "none"))

    # AC-PSP3: restart-surviving gate probes (fail-closed, zero rows)
    probes = []
    probes.append(expect_prop_error(
        lambda: pf2.consume_prop("usr:alice", "hat_gold", 1),
        P.E_PROP_BAD_KIND))                          # cosmetic permanent
    probes.append(expect_prop_error(
        lambda: pf2.consume_prop("usr:alice", "jetpack", 5),
        P.E_PROP_INSUFFICIENT))                      # 3 held < 5 asked
    probes.append(expect_prop_error(
        lambda: pf2.consume_prop("usr:alice", "ghost_lamp", 1),
        P.E_PROP_UNKNOWN))
    probes.append(expect_prop_error(
        lambda: pf2.buy_prop("usr:alice", "jetpack", "cosmetic", 5,
                             "order:psp3-drift"),
        P.E_PROP_BAD_KIND))                          # kind drift
    probes.append(expect_prop_error(
        lambda: pf2.buy_prop("usr:bob", "boat", "vehicle", 10,
                             "order:psp3-kind"),
        P.E_PROP_BAD_KIND))                          # unknown kind
    probes.append(expect_prop_error(
        lambda: pf2.buy_prop("usr:bob", "boat", "prop", 5, "   ",
                             count=1),
        P.E_PROP_BAD_REF))
    probes.append(expect_prop_error(
        lambda: pf2.buy_prop("usr:bob", "boat", "prop", 5,
                             "order:psp3-amt", count=0),
        P.E_PROP_BAD_AMOUNT))
    bal_c0 = led2.balance("usr:carol")["balance"]
    ok_neg, code_neg = expect_ledger_error(
        lambda: pf2.buy_prop("usr:carol", "yacht", "cosmetic", 99999,
                             "order:psp3-neg"),
        L.E_NEGATIVE_BALANCE)
    bal_c1 = led2.balance("usr:carol")["balance"]
    yacht = [c for c in pf2.inventory("usr:carol")["cosmetics"]
             if c == "yacht"]
    counts_after_probes = table_counts(db_path)
    ok3 = (all(p[0] for p in probes) and ok_neg
           and bal_c1 == bal_c0 and not yacht
           and counts_after_probes == counts1)
    record("AC-PSP3", ok3, "8 restart-surviving probes all-reject "
          "[cosmetic-consume/over-consume/unknown-item/kind-drift/"
          "unknown-kind/bad-ref/bad-amount=%s,%s,%s,%s,%s,%s,%s; "
          "insufficient=%s] with zero charge (%d==%d) zero grant; "
          "counts frozen %s"
          % tuple([p[1] for p in probes] + [code_neg, bal_c0, bal_c1,
              "inv=%d spend_tx=%d" % (counts_after_probes["props_inventory"],
                                      counts_after_probes["spend_tx"])]))

    # AC-PSP4: post-restart real-path continuation (zero cache)
    pf2.buy_prop("usr:carol", "lantern", "prop", 25, "order:psp4-lantern",
                 count=4)
    inv_c = pf2.inventory("usr:carol")
    lantern_tx = inv_c["bound_spend_tx"]["lantern"]
    l_head, l_leg = spend_cross(db_path, lantern_tx, "usr:carol")
    pf2.consume_prop("usr:alice", "jetpack", 2)      # 3 -> 1
    pf2.buy_prop("usr:alice", "jetpack", "prop", 20, "order:psp4-jet2",
                 count=1)                            # stack 1 -> 2
    pf2.consume_prop("usr:bob", "flare", 1)          # 1 -> 0
    pf2.buy_prop("usr:bob", "flare", "prop", 10, "order:psp4-flare3",
                 count=3)                            # stack 0 -> 3
    snap3 = read_battery(pf2, led2)
    counts3 = table_counts(db_path)
    inv_a3 = json.loads(snap3["inv_a"])
    inv_b3 = json.loads(snap3["inv_b"])
    jet_credits = [p for p in inv_a3["props"]
                   if p["item_id"] == "jetpack"][0]["count_credits"]
    flare_credits3 = [p for p in inv_b3["props"]
                      if p["item_id"] == "flare"][0]["count_credits"]
    changed3 = battery_diffs(snap2, snap3)
    ok4 = (l_head == "spend" and l_leg == "debit"
           and jet_credits == 2 and flare_credits3 == 3
           and counts3["props_inventory"] == 5 and counts3["spend_tx"] == 7
           and snap3["bal_alice"] == 245 and snap3["bal_bob"] == 480
           and snap3["bal_carol"] == 363 and snap3["bal_pool"] == 18912
           and len(changed3) >= 7)
    record("AC-PSP4", ok4, "continuation on instance 2: lantern spend "
          "SQL-cross (%s+%s); jetpack 3->1->2, flare 1->0->3; counts "
          "inv=%d spend_tx=%d; balances a/b/c/pool=%d/%d/%d/%d; "
          "battery cells moved=%d; digest=%s"
          % (l_head, l_leg, counts3["props_inventory"], counts3["spend_tx"],
             snap3["bal_alice"], snap3["bal_bob"], snap3["bal_carol"],
             snap3["bal_pool"], len(changed3), evidence_digest(snap3)))

    # AC-PSP5: frozen provenance faces + dup gate across restart
    rows_now = inventory_rows_snapshot(db_path)
    by_key_anchor = {(r[1], r[2]): r for r in rows_anchor}

    def prov_of(row):
        # provenance key set: everything but count_credits (index 4)
        # - stack rows move credits via product verbs, provenance
        # (inv_id/account/item/kind/bound_spend_tx/granted_utc)
        # must stay byte-frozen (design ruling 3).
        return (row[0], row[1], row[2], row[3], row[5], row[6])

    frozen_full = []
    frozen_prov = []
    for row in rows_now:
        key = (row[1], row[2])
        if key not in by_key_anchor:
            continue                                 # lantern = new row
        old = by_key_anchor[key]
        if prov_of(row) != prov_of(old):
            frozen_prov.append(key)
        if row != old and key in (("usr:alice", "hat_gold"),
                                  ("usr:carol", "scarf_silk")):
            frozen_full.append(key)
    bal_a_pre = led2.balance("usr:alice")["balance"]
    ok_dup, code_dup = expect_prop_error(
        lambda: pf2.buy_prop("usr:alice", "hat_gold", "cosmetic", 15,
                             "order:psp5-dup"),
        P.E_PROP_DUP)
    bal_a_post = led2.balance("usr:alice")["balance"]
    counts5 = table_counts(db_path)
    ok5 = (not frozen_prov and not frozen_full and ok_dup
           and bal_a_post == bal_a_pre and counts5 == counts3)
    record("AC-PSP5", ok5, "anchor rows provenance-frozen across restart"
          " x continuation (inv_id/account/kind/bound_spend_tx/"
          "granted_utc drift=%s; untouched-row drift=%s; stack rows "
          "moved only via product verbs jetpack 3->2 flare 1->3); dup "
          "re-buy rejected %s with zero charge (%d==%d) zero rows"
          % (frozen_prov or "none", frozen_full or "none", code_dup,
             bal_a_pre, bal_a_post))

    # AC-PSP6: pure-read law
    snap3b = read_battery(pf2, led2)
    counts6 = table_counts(db_path)
    ok6 = (snap3b == snap3 and counts6 == counts3)
    record("AC-PSP6", ok6, "pure-read law: double battery byte-identical "
          "(diffs=%s) and counts constant %s"
          % (battery_diffs(snap3, snap3b) or "none",
             "inv=%d spend_tx=%d" % (counts6["props_inventory"],
                                      counts6["spend_tx"])))

    # AC-PSP7: third instance stability + hygiene
    pf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    pf3 = P.PropsFace(led3)
    snap4 = read_battery(pf3, led3)
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
    record("AC-PSP7", ok7, "instance 3 on same db: battery diffs=%s; "
          "counts stable inv=%d spend_tx=%d; config sha unchanged=%s; "
          "non-ascii=%d; network-imports=%s; world outside repo=%s"
          % (diffs7 or "none", counts7["props_inventory"],
             counts7["spend_tx"],
             str(cfg_sha_after == cfg_sha_before).lower(),
             non_ascii, net_hits or "none", str(not in_repo).lower()))

    pf3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
