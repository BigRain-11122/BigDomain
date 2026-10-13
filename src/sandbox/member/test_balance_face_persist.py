"""Acceptance suite for the member balance_face entitlement-balance
panel read-face derivation purity across an INSTANCE RESTART
(BigDomain R1912 tech-queue claim row; seed = the R1907 reseed:
balance_face (R1721 AC-RR4 history-readable, on the books) had zero
cross-instance restart example while the R1889 banner_queue /
R1900 expiring_soon member-domain persist siblings already closed
theirs. Family law: a fresh MemberStore instance on the same db /
cfg / live pay dock must re-derive the same panel bytes, the
same-grant dedup map must be db state, a new true-path activation
plus a new consumption must recompute the panel (zero cache), and
untouched sibling avatars must never drift.

Asserts the pre-registered criteria AC-BFP1..AC-BFP7 from the
R1912 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (family law): one world drives the TRUE product
path end to end - every period opens via pay order -> place ->
callback -> grant -> store.activate, every balance shift lands via
store.consume_credits (zero fixture injection, zero raw SQL
writes). balance_face carries zero clock-following fields and
zero window parameters, so every comparison is FULL-envelope
dumps byte identity (no projection band needed).

Restart genealogy: face1 loads the world (EP-A experience
consumed-by-1, EP-B mayor double-grant stacked renewal consumed
by 4, EP-C experience untouched, EP-D pre-restart empty,
EP-EMPTY never touched) + takes the pre-close five-face snapshot
-> close -> face2 reopens (same cfg object, same db file, same
live pay dock) -> byte replay -> same-grant re-activation stays
idempotent (source_grant_id db-backed dedup) -> one new true-path
activation (EP-D) + one new consumption (EP-A) recompute their
panels zero-cache while siblings stay byte-frozen -> face3
reopens again (two live instances) for the sequential read
identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_balance_face_persist.py
"""

import hashlib
import inspect
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import test_member as TM               # noqa: E402 (world build reuse)
import member as M                     # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

CFG_PATH = os.path.join(BASE, "config.json")
RUNNER_SRC = os.path.join(BASE, "..", "reconcile_all.py")
SUITE_LABEL = "member-balanceface-persist"

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

ENV_KEYS = {"census_avatar_id", "periods", "carryover",
            "carryover_note", "ai_generated", "disclaimer",
            "persistent"}
ROW_KEYS = {"period_id", "tier", "status", "start_utc", "end_utc",
            "balance"}

AVATARS = ("EP-A", "EP-B", "EP-C", "EP-D", "EP-EMPTY")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def counts(world):
    out = {}
    for table in ("member_periods", "member_credit_events",
                  "member_vouchers", "member_audit"):
        out[table] = TM.db_query(
            world["member_db"], "SELECT COUNT(*) FROM %s" % table
        )[0][0]
    return out


def panel(face, avatar):
    return face.balance_face(avatar)


def panel_battery(face):
    return {a: dumps(panel(face, a)) for a in AVATARS}


def manual_balances(world, avatar):
    """Per-period balance straight from the journal, period_no
    order (the face's documented ORDER BY)."""
    rows = TM.db_query(
        world["member_db"],
        "SELECT p.period_id, p.tier, p.status, p.start_utc,"
        " p.end_utc, p.period_no FROM member_periods p"
        " WHERE p.census_avatar_id = ? ORDER BY p.period_no",
        (avatar,))
    out = []
    for pid, tier, status, start, end, no in rows:
        bal = TM.db_query(
            world["member_db"],
            "SELECT COALESCE(SUM(delta), 0) FROM"
            " member_credit_events WHERE period_id = ?",
            (pid,))[0][0]
        out.append({"period_id": pid, "tier": tier, "status": status,
                   "start_utc": start, "end_utc": end,
                   "balance": int(bal)})
    return out


def main():
    member_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "member.py"), "rb").read()).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    w = TM.build()
    try:
        # ---- world: four true-path avatars + one never touched --
        grants = {}
        # EP-A: experience, consumed by 1 -> balance 2
        _oid, gid = TM.happy(w, "tier_experience", "EP-A", "bfp-a")
        grants["EP-A"] = gid
        resp_a = w["store"].activate(gid, "EP-A")
        w["store"].consume_credits("EP-A", 1, ref="bfp-a-svc",
                                   ref_type="service")
        # EP-B: mayor, renewal stacking. Honest product-path note:
        # compute_order_id buckets on the CLOSED order count, so the
        # second same-(avatar, product) order only opens after the
        # first rides the granted->closed refund edge - the stacking
        # law in activate() (renewal never starts in the past) is
        # reached here through that edge, the only true-path shape.
        oid_b1, gid1 = TM.happy(w, "tier_mayor", "EP-B", "bfp-b1")
        grants["EP-B1"] = gid1
        resp_b1 = w["store"].activate(gid1, "EP-B")
        w["pay"].close_refund(oid_b1)     # granted -> closed edge
        _oid_b2, gid2 = TM.happy(w, "tier_mayor", "EP-B", "bfp-b2")
        grants["EP-B2"] = gid2
        resp_b2 = w["store"].activate(gid2, "EP-B")
        w["store"].consume_credits("EP-B", 4, ref="bfp-b-svc",
                                   ref_type="service")
        # EP-C: experience, untouched -> balance 3
        _oid, gid = TM.happy(w, "tier_experience", "EP-C", "bfp-c")
        grants["EP-C"] = gid
        resp_c = w["store"].activate(gid, "EP-C")
        # EP-D: pre-restart empty; EP-EMPTY: never touched

        fresh_ok = (resp_a["idempotent"] is False
                    and resp_b1["idempotent"] is False
                    and resp_b2["idempotent"] is False
                    and resp_c["idempotent"] is False)
        pre = panel_battery(w["store"])
        pa = json.loads(pre["EP-A"])
        pb = json.loads(pre["EP-B"])
        pc = json.loads(pre["EP-C"])
        pd = json.loads(pre["EP-D"])
        pe = json.loads(pre["EP-EMPTY"])

        # ---- AC-BFP1: world load + pre-close snapshot set -------
        ok_env = all(set(json.loads(pre[a])) == ENV_KEYS
                     for a in AVATARS)
        ok_rows = (all(set(x) == ROW_KEYS for x in pa["periods"])
                   and all(set(x) == ROW_KEYS for x in pb["periods"])
                   and all(set(x) == ROW_KEYS for x in pc["periods"]))
        cross_a = (manual_balances(w, "EP-A") == pa["periods"])
        cross_b = (manual_balances(w, "EP-B") == pb["periods"])
        cross_c = (manual_balances(w, "EP-C") == pc["periods"])
        # stacking law read: period 2 starts exactly where
        # period 1 ends (renewal never starts in the past)
        stack_ok = (len(pb["periods"]) == 2
                    and pb["periods"][1]["start_utc"]
                    == pb["periods"][0]["end_utc"])
        bal_map = [pa["periods"][0]["balance"],
                   pb["periods"][0]["balance"],
                   pb["periods"][1]["balance"],
                   pc["periods"][0]["balance"]]
        ok1 = (fresh_ok
               and ok_env and ok_rows
               and cross_a and cross_b and cross_c
               and stack_ok
               and bal_map == [2, 6, 10, 3]
               and pa["census_avatar_id"] == "EP-A"
               and pb["census_avatar_id"] == "EP-B"
               and pc["census_avatar_id"] == "EP-C"
               and len(pa["periods"]) == 1
               and len(pb["periods"]) == 2
               and len(pc["periods"]) == 1
               and all(x["status"] == "active"
                       for x in pa["periods"] + pb["periods"]
                       + pc["periods"])
               and pa["periods"][0]["tier"] == "experience"
               and pb["periods"][0]["tier"] == "mayor"
               and pb["periods"][1]["tier"] == "mayor"
               and pd["periods"] == [] and pd["census_avatar_id"]
               == "EP-D"
               and pe["periods"] == []
               and pa["carryover"] is False
               and isinstance(pa["carryover_note"], str)
               and pa["ai_generated"] == 0
               and pa["persistent"] is True
               and isinstance(pa["disclaimer"], str))
        record("AC-BFP1", ok1,
               "fresh=%s env_keys=%s row_keys=%s cross_abc=%s%s%s"
               " stack=%s balances=%s counts(a/b/c)=%d/%d/%d"
               " empty_faces=%s%s carryover=%s"
               % (fresh_ok, ok_env, ok_rows, cross_a, cross_b,
                  cross_c, stack_ok, bal_map,
                  len(pa["periods"]), len(pb["periods"]),
                  len(pc["periods"]), pd["periods"] == [],
                  pe["periods"] == [], pa["carryover"] is False))

        # ---- AC-BFP2: cross-restart byte identity (core) --------
        w["store"].close()
        face2 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        post = panel_battery(face2)
        reread = {a: dumps(panel(face2, a)) for a in AVATARS}
        ok2 = (post == pre and reread == post)
        record("AC-BFP2", ok2,
               "five_faces==pre=%s self_identical=%s (full envelope:"
               " zero clock-following fields, zero window params)"
               % (post == pre, reread == post))

        # ---- AC-BFP3: same-grant re-activation idempotency ------
        c_before = counts(w)
        resp_a2 = face2.activate(grants["EP-A"], "EP-A")
        c_after = counts(w)
        pa_re = dumps(panel(face2, "EP-A"))
        ok3 = (resp_a2["idempotent"] is True
               and resp_a2["period_id"] == resp_a["period_id"]
               and resp_a2["status"] == "active"
               and pa_re == pre["EP-A"]
               and c_before == c_after
               and c_after["member_periods"] == 4)
        record("AC-BFP3", ok3,
               "idempotent=%s same_period=%s panel_unchanged=%s"
               " periods=%d counts_stable=%s (dedup map = db state"
               " across the restart boundary, source_grant_id)"
               % (resp_a2["idempotent"],
                  resp_a2["period_id"] == resp_a["period_id"],
                  pa_re == pre["EP-A"],
                  c_after["member_periods"], c_before == c_after))

        # ---- AC-BFP4: new activation + new consumption -> zero
        # cache recompute ------------------------------------------
        ident_a = dumps(panel(face2, "EP-A"))
        _oid_d, gid_d = TM.happy(w, "tier_experience", "EP-D",
                                 "bfp-d")
        resp_d = face2.activate(gid_d, "EP-D")
        pd_new = panel(face2, "EP-D")
        consume_resp = face2.consume_credits(
            "EP-A", 1, ref="bfp-a-post", ref_type="service")
        pa_new = panel(face2, "EP-A")
        cross_a2 = (manual_balances(w, "EP-A") == pa_new["periods"])
        siblings_ok = (dumps(panel(face2, "EP-B")) == post["EP-B"]
                       and dumps(panel(face2, "EP-C"))
                       == post["EP-C"]
                       and dumps(panel(face2, "EP-EMPTY"))
                       == post["EP-EMPTY"])
        ok4 = (resp_d["idempotent"] is False
               and resp_d["status"] == "active"
               and len(pd_new["periods"]) == 1
               and pd_new["periods"][0]["balance"] == 3
               and pd_new["periods"][0]["tier"] == "experience"
               and dumps(pd_new) != pre["EP-D"]
               and consume_resp["consumed"] == 1
               and pa_new["periods"][0]["balance"] == 1
               and dumps(pa_new) != ident_a
               and dumps(pa_new) != pre["EP-A"]
               and cross_a2 and siblings_ok)
        record("AC-BFP4", ok4,
               "ep_d_fresh=%s ep_d_balance=%d panel_changed=%s"
               " ep_a_balance=%d ep_a_changed=%s ep_a_cross=%s"
               " siblings_frozen=%s (recomputed from db, zero"
               " cache; new data never permeates untouched"
               " avatars)"
               % (resp_d["idempotent"] is False,
                  pd_new["periods"][0]["balance"],
                  dumps(pd_new) != pre["EP-D"],
                  pa_new["periods"][0]["balance"],
                  dumps(pa_new) != ident_a, cross_a2, siblings_ok))

        # ---- AC-BFP5: dual-instance sequential identity ---------
        face3 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        b2 = panel_battery(face2)
        b3 = panel_battery(face3)
        b2b = panel_battery(face2)
        ok5 = (b2 == b3 and b2b == b2
               and b3["EP-C"] == pre["EP-C"]
               and b3["EP-EMPTY"] == pre["EP-EMPTY"]
               and b3["EP-B"] == pre["EP-B"])
        record("AC-BFP5", ok5,
               "face2==face3=%s face2_reread=%s ep_c_still==pre=%s"
               " ep_b_still==pre=%s (restart x new-data double"
               " hijack, stable avatars never drift)"
               % (b2 == b3, b2b == b2,
                  b3["EP-C"] == pre["EP-C"],
                  b3["EP-B"] == pre["EP-B"]))

        # ---- AC-BFP6: pure-read law + honest refusal family -----
        before6 = counts(w)
        for face in (face2, face3):
            for a in AVATARS:
                panel(face, a)
                panel(face, a)
        r1, d1 = TM.expect_code(
            lambda: face2.consume_credits("EP-EMPTY", 1),
            M.E_PERIOD_EXPIRED)
        r2, d2 = TM.expect_code(
            lambda: face3.consume_credits("EP-C", 99),
            M.E_NO_CREDITS)
        after6 = counts(w)
        ep_c_stable = (dumps(panel(face3, "EP-C")) == pre["EP-C"])
        ok6 = (r1 and r2 and before6 == after6
               and after6["member_periods"] == 5
               and ep_c_stable)
        record("AC-BFP6", ok6,
               "empty_refusal=%s(%s) overdraw_refusal=%s(%s)"
               " counts_stable=%s (periods %d, events %d,"
               " vouchers %d, audit %d), ep_c_untouched=%s"
               % (r1, d1.split(" ")[0], r2, d2.split(" ")[0],
                  before6 == after6, after6["member_periods"],
                  after6["member_credit_events"],
                  after6["member_vouchers"],
                  after6["member_audit"], ep_c_stable))

        # ---- AC-BFP7: hygiene ------------------------------------
        src_panel = inspect.getsource(M.MemberStore.balance_face)
        writes = [kw for kw in WRITE_KW if kw in src_panel]
        before7 = counts(w)
        with open(os.path.abspath(__file__), "rb") as fh:
            own = fh.read()
        ascii_ok = True
        try:
            own.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
        import_lines = [ln.strip() for ln
                        in own.decode("utf-8").splitlines()
                        if ln.strip().startswith("import ")]
        net_hits = [ln for ln in import_lines
                    for lib in NET_LIBS if lib in ln]
        member_sha_out = hashlib.sha256(
            open(os.path.join(BASE, "member.py"), "rb")
            .read()).hexdigest()
        cfg_sha_out = hashlib.sha256(
            open(CFG_PATH, "rb").read()).hexdigest()
        world_outside = not os.path.abspath(
            w["member_db"]).startswith(
            os.path.abspath(BASE) + os.sep)
        runner_text = open(RUNNER_SRC, encoding="utf-8").read()
        registered = SUITE_LABEL in runner_text
        drift = len(RESULTS) + 1 == EXPECTED
        ok7 = (not writes and ascii_ok and not net_hits
               and member_sha_in == member_sha_out
               and cfg_sha_in == cfg_sha_out
               and world_outside and registered and drift
               and before7 == after6)
        record("AC-BFP7", ok7,
               "write_keywords=%s ascii=%s net_imports=%d"
               " member_sha=%s cfg_sha=%s world_outside=%s"
               " runner_row=%s drift=%d/%d counts_stable=%s"
               % (writes, ascii_ok, len(net_hits),
                  member_sha_in == member_sha_out,
                  cfg_sha_in == cfg_sha_out, world_outside,
                  registered, len(RESULTS), EXPECTED,
                  before7 == after6))

        face2.close()
        face3.close()
    finally:
        # world store was already closed at the AC-BFP2 boundary;
        # tear closes pay + ledger and removes the tmp world.
        try:
            w["store"].close()
        except Exception:
            pass
        TM.tear(w)

    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s: %d/%d criteria pass" % (SUITE_LABEL,
                                             passed, total),
          flush=True)
    if passed != total or total != EXPECTED:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
