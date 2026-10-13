"""Acceptance suite for the member privileges_for / has_privilege
read-face derivation purity across an INSTANCE RESTART
(BigDomain R1916 tech-queue claim row; seed = the R1912 reseed:
the privilege read faces (member.py privileges_for AC-M5 /
has_privilege AC-M6, the R1721 consume-face freeze in the books)
had zero cross-instance restart example while the R1889
banner_queue / R1900 expiring_soon / R1912 balance_face
member-domain persist siblings already closed theirs. Family
law: a fresh MemberStore instance on the same db / cfg / live
pay dock must re-derive the same privilege envelopes, the
rejection family must fire identically, a new true-path
activation must recompute the new avatar's panel (zero cache)
while untouched siblings stay byte-frozen, and a new consumption
must move ZERO privilege-face bytes (the face derives from
active periods x catalog tiers only -- the balance-invariance
pin, contrasted with the R1912 balance_face recompute face).

Asserts the pre-registered criteria AC-PRP1..AC-PRP7 from the
R1916 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (family law): one world drives the TRUE product
path end to end - every period opens via pay order -> place ->
callback -> grant -> store.activate, the refund-recovery avatar
rides the R1721 granted->closed + active->expired edge, zero
fixture injection, zero raw SQL writes. Both faces carry zero
clock-following fields and zero window parameters, so every
comparison is FULL-envelope dumps byte identity (no projection
band needed).

Restart genealogy: face1 loads the world (EP-A experience
consumed-by-1, EP-B mayor double-grant stacked renewal consumed
by 4, EP-C experience untouched, EP-RVK refund-revoked empty
face, EP-D pre-restart empty, EP-EMPTY never touched) + takes
the pre-close snapshot set -> close -> face2 reopens (same cfg
object, same db file, same live pay dock) -> byte replay -> new
true-path activation (EP-D) recomputes zero-cache + a new
consumption on EP-A leaves its privilege envelope byte-stable ->
face3 reopens again (two live instances) for the sequential
read identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_privileges_persist.py
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
SUITE_LABEL = "member-privileges-persist"

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

PRIV_ENV_KEYS = {"census_avatar_id", "active", "tiers",
                 "privileges", "periods", "ai_generated",
                 "disclaimer", "persistent"}
GRANTED_ENV_KEYS = {"census_avatar_id", "granted", "privilege",
                    "tier", "period_id", "ai_generated",
                    "disclaimer", "persistent"}
PERIOD_ROW_KEYS = {"period_id", "tier", "period_no", "start_utc",
                   "end_utc"}

AVATARS = ("EP-A", "EP-B", "EP-C", "EP-RVK", "EP-D", "EP-EMPTY")

# experience-only privilege + mayor-only privilege for the
# E_TIER_REQUIRED probe (catalog pinned 2026-10-13)
EXP_PRIV = "basic_badge"
MAYOR_PRIV = "chat_highlight"


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


def priv_battery(face, avatars=AVATARS):
    return {a: dumps(face.privileges_for(a)) for a in avatars}


def manual_active_rows(world, avatar):
    return TM.db_query(
        world["member_db"],
        "SELECT period_id, tier, period_no, start_utc, end_utc"
        " FROM member_periods WHERE census_avatar_id = ?"
        " AND status = 'active' ORDER BY end_utc ASC",
        (avatar,))


def expected_face(world, avatar):
    """Catalog-derived expectation, exactly the face's own
    derivation (server-authority cross face): active rows in
    end_utc order -> tier keys deduped first-seen, tier
    privileges deduped first-seen."""
    rows = manual_active_rows(world, avatar)
    tiers = []
    privileges = []
    for r in rows:
        tier = world["store"].catalog.tiers[r[1]]
        if tier.key not in tiers:
            tiers.append(tier.key)
        for priv in tier.privileges:
            if priv not in privileges:
                privileges.append(priv)
    return tiers, privileges


def main():
    member_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "member.py"), "rb").read()).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    w = TM.build()
    try:
        # ---- world: five true-path avatars + one never touched --
        grants = {}
        # EP-A: experience, consumed by 1
        _oid_a, gid_a = TM.happy(w, "tier_experience", "EP-A",
                                 "prp-a")
        grants["EP-A"] = gid_a
        resp_a = w["store"].activate(gid_a, "EP-A")
        w["store"].consume_credits("EP-A", 1, ref="prp-a-svc",
                                   ref_type="service")
        # EP-B: mayor, renewal stacking through the only true-path
        # shape (compute_order_id buckets on CLOSED orders, so the
        # second same-(avatar, product) order opens after the
        # first rides the granted->closed refund edge; the R1912
        # product-path discovery note, reused).
        oid_b1, gid_b1 = TM.happy(w, "tier_mayor", "EP-B", "prp-b1")
        grants["EP-B1"] = gid_b1
        resp_b1 = w["store"].activate(gid_b1, "EP-B")
        w["pay"].close_refund(oid_b1)     # granted -> closed edge
        _oid_b2, gid_b2 = TM.happy(w, "tier_mayor", "EP-B",
                                   "prp-b2")
        grants["EP-B2"] = gid_b2
        resp_b2 = w["store"].activate(gid_b2, "EP-B")
        w["store"].consume_credits("EP-B", 4, ref="prp-b-svc",
                                   ref_type="service")
        # EP-C: experience, untouched
        _oid_c, gid_c = TM.happy(w, "tier_experience", "EP-C",
                                 "prp-c")
        grants["EP-C"] = gid_c
        resp_c = w["store"].activate(gid_c, "EP-C")
        # EP-RVK: refund-revoked recovery face (R1721) - the
        # active->expired edge empties the privilege face
        oid_r, gid_r = TM.happy(w, "tier_experience", "EP-RVK",
                                "prp-rvk")
        grants["EP-RVK"] = gid_r
        resp_r = w["store"].activate(gid_r, "EP-RVK")
        w["pay"].close_refund(oid_r)
        resp_rvk = w["store"].revoke_refunded(gid_r)
        # EP-D: pre-restart empty; EP-EMPTY: never touched

        fresh_ok = (resp_a["idempotent"] is False
                    and resp_b1["idempotent"] is False
                    and resp_b2["idempotent"] is False
                    and resp_c["idempotent"] is False
                    and resp_r["idempotent"] is False
                    and resp_rvk["revoked"] == 1)

        pre = priv_battery(w["store"])
        granted_a = w["store"].has_privilege("EP-A", EXP_PRIV)
        s_granted_a = dumps(granted_a)
        # client-hints zero-authority probes (both faces)
        hint_priv = dumps(w["store"].privileges_for(
            "EP-A", client_hints={"tiers": ["mayor"],
                                  "privileges": [MAYOR_PRIV]}))
        hint_granted = dumps(w["store"].has_privilege(
            "EP-A", EXP_PRIV,
            client_hints={"tier": "mayor", "granted": False}))

        pa = json.loads(pre["EP-A"])
        pb = json.loads(pre["EP-B"])
        pc = json.loads(pre["EP-C"])
        pr = json.loads(pre["EP-RVK"])
        pd = json.loads(pre["EP-D"])
        pe = json.loads(pre["EP-EMPTY"])

        # ---- AC-PRP1: world load + pre-close snapshot set -------
        ok_env = all(set(json.loads(pre[a])) == PRIV_ENV_KEYS
                     for a in AVATARS)
        ok_rows = all(set(x) == PERIOD_ROW_KEYS
                      for env in (pa, pb, pc)
                      for x in env["periods"])
        ok_granted = set(granted_a) == GRANTED_ENV_KEYS
        exp_a = expected_face(w, "EP-A")
        exp_b = expected_face(w, "EP-B")
        exp_c = expected_face(w, "EP-C")
        cross_a = (manual_active_rows(w, "EP-A") == [
            (x["period_id"], x["tier"], x["period_no"],
             x["start_utc"], x["end_utc"])
            for x in pa["periods"]])
        cross_c = (manual_active_rows(w, "EP-C") == [
            (x["period_id"], x["tier"], x["period_no"],
             x["start_utc"], x["end_utc"])
            for x in pc["periods"]])
        dedup_ok = (len(pb["periods"]) == 2
                    and pb["periods"][1]["start_utc"]
                    == pb["periods"][0]["end_utc"]
                    and pb["tiers"] == exp_b[0] == ["mayor"]
                    and pb["privileges"] == exp_b[1]
                    and len(pb["privileges"]) == 3)
        rvk_ok = (pr["active"] is False
                  and pr["tiers"] == [] and pr["privileges"] == []
                  and pr["periods"] == [])
        empty_ok = (pe["active"] is False and pe["tiers"] == []
                    and pe["privileges"] == []
                    and pe["periods"] == []
                    and pd["active"] is False
                    and pd["tiers"] == []
                    and pd["privileges"] == []
                    and pd["periods"] == [])
        compliance_ok = (pa["ai_generated"] == 0
                         and pa["persistent"] is True
                         and isinstance(pa["disclaimer"], str)
                         and granted_a["ai_generated"] == 0
                         and granted_a["persistent"] is True)
        granted_ok = (granted_a["census_avatar_id"] == "EP-A"
                      and granted_a["granted"] is True
                      and granted_a["privilege"] == EXP_PRIV
                      and granted_a["tier"] == "experience"
                      and granted_a["period_id"]
                      == pa["periods"][0]["period_id"])
        ok1 = (fresh_ok and ok_env and ok_rows and ok_granted
               and cross_a and cross_c
               and pa["tiers"] == exp_a[0] == ["experience"]
               and pa["privileges"] == exp_a[1]
               and pa["privileges"] == ["basic_badge",
                                        "emoji_pack_standard"]
               and pc["tiers"] == exp_c[0]
               and pc["privileges"] == exp_c[1]
               and len(pa["periods"]) == 1
               and len(pc["periods"]) == 1
               and all(x["tier"] == "experience"
                       for x in pa["periods"] + pc["periods"])
               and dedup_ok and rvk_ok and empty_ok
               and compliance_ok and granted_ok
               and hint_priv == pre["EP-A"]
               and hint_granted == s_granted_a)
        record("AC-PRP1", ok1,
               "fresh=%s env_keys=%s row_keys=%s granted_keys=%s"
               " cross=%s%s dedup_stack=%s rvk_empty=%s"
               " empty_faces=%s compliance=%s granted_face=%s"
               " hints_zero_authority=%s"
               % (fresh_ok, ok_env, ok_rows, ok_granted,
                  cross_a, cross_c, dedup_ok, rvk_ok, empty_ok,
                  compliance_ok, granted_ok,
                  hint_priv == pre["EP-A"]
                  and hint_granted == s_granted_a))

        # ---- AC-PRP2: cross-restart byte identity (core) --------
        w["store"].close()
        face2 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        post = priv_battery(face2)
        reread = {a: dumps(face2.privileges_for(a))
                  for a in AVATARS}
        granted2 = dumps(face2.has_privilege("EP-A", EXP_PRIV))
        ok2 = (post == pre and reread == post
               and granted2 == s_granted_a)
        record("AC-PRP2", ok2,
               "six_faces==pre=%s self_identical=%s granted==pre"
               "=%s (full envelopes: zero clock-following fields,"
               " zero window params, zero in-memory drift)"
               % (post == pre, reread == post,
                  granted2 == s_granted_a))

        # ---- AC-PRP3: rejection family across restart ----------
        before3 = counts(w)
        r1, d1 = TM.expect_code(
            lambda: face2.has_privilege("EP-EMPTY", EXP_PRIV),
            M.E_NO_ACTIVE_PERIOD)
        r2, d2 = TM.expect_code(
            lambda: face2.has_privilege("EP-RVK", EXP_PRIV),
            M.E_NO_ACTIVE_PERIOD)
        r3, d3 = TM.expect_code(
            lambda: face2.has_privilege("EP-A", MAYOR_PRIV),
            M.E_TIER_REQUIRED)
        r4, d4 = TM.expect_code(
            lambda: face2.has_privilege("EP-A", "bogus_privilege"),
            M.E_BAD_STATE)
        after3 = counts(w)
        ok3 = (r1 and r2 and r3 and r4
               and before3 == after3
               and after3["member_periods"] == 5)
        record("AC-PRP3", ok3,
               "no_active(empty)=%s no_active(revoked)=%s"
               " tier_required(mayor priv on experience)=%s"
               " bad_state(unknown key)=%s codes=%s|%s|%s|%s"
               " counts_stable=%s (periods %d, events %d,"
               " vouchers %d, audit %d)"
               % (r1, r2, r3, r4,
                  d1.split(" ")[0], d2.split(" ")[0],
                  d3.split(" ")[0], d4.split(" ")[0],
                  before3 == after3, after3["member_periods"],
                  after3["member_credit_events"],
                  after3["member_vouchers"],
                  after3["member_audit"]))

        # ---- AC-PRP4: new activation -> zero-cache recompute ---
        # + consumption balance-invariance pin -------------------
        _oid_d, gid_d = TM.happy(w, "tier_experience", "EP-D",
                                "prp-d")
        grants["EP-D"] = gid_d
        resp_d = face2.activate(gid_d, "EP-D")
        pd_new = face2.privileges_for("EP-D")
        exp_d = expected_face(w, "EP-D")
        ident_a_pre = dumps(face2.privileges_for("EP-A"))
        consume_resp = face2.consume_credits(
            "EP-A", 1, ref="prp-a-post", ref_type="service")
        pa_post_consume = dumps(face2.privileges_for("EP-A"))
        siblings_ok = (dumps(face2.privileges_for("EP-B"))
                       == post["EP-B"]
                       and dumps(face2.privileges_for("EP-C"))
                       == post["EP-C"]
                       and dumps(face2.privileges_for("EP-RVK"))
                       == post["EP-RVK"]
                       and dumps(face2.privileges_for("EP-EMPTY"))
                       == post["EP-EMPTY"])
        ok4 = (resp_d["idempotent"] is False
               and resp_d["status"] == "active"
               and dumps(pd_new) != pre["EP-D"]
               and pd_new["active"] is True
               and pd_new["tiers"] == exp_d[0]
               and pd_new["privileges"] == exp_d[1]
               and len(pd_new["periods"]) == 1
               and consume_resp["consumed"] == 1
               and pa_post_consume == ident_a_pre
               and siblings_ok)
        record("AC-PRP4", ok4,
               "ep_d_fresh=%s ep_d_changed=%s ep_d_tiers=%s"
               " ep_a_consume=%d ep_a_privilege_face_stable=%s"
               " (balance-invariance pin: consumption moves zero"
               " privilege bytes, contrasted with the R1912"
               " balance_face recompute face) siblings_frozen=%s"
               % (resp_d["idempotent"] is False,
                  dumps(pd_new) != pre["EP-D"],
                  pd_new["tiers"] == exp_d[0],
                  consume_resp["consumed"],
                  pa_post_consume == ident_a_pre, siblings_ok))

        # ---- AC-PRP5: third instance sequential identity ------
        face3 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        b2 = priv_battery(face2)
        b3 = priv_battery(face3)
        b2b = priv_battery(face2)
        g2 = dumps(face2.has_privilege("EP-A", EXP_PRIV))
        g3 = dumps(face3.has_privilege("EP-A", EXP_PRIV))
        # EP-A's privilege face is consume-invariant, so it must
        # still equal its ORIGINAL pre-close snapshot; the same
        # holds for EP-B / EP-C (untouched by the injection)
        ok5 = (b2 == b3 and b2b == b2 and g2 == g3
               and b3["EP-A"] == pre["EP-A"]
               and b3["EP-B"] == pre["EP-B"]
               and b3["EP-C"] == pre["EP-C"]
               and b3["EP-RVK"] == pre["EP-RVK"])
        record("AC-PRP5", ok5,
               "face2==face3=%s face2_reread=%s granted==%s"
               " stable_avatars_still==pre=%s%s%s%s (restart x"
               " new-data double hijack, stable avatars never"
               " drift; EP-D carries the only recompute)"
               % (b2 == b3, b2b == b2, g2 == g3,
                  b3["EP-A"] == pre["EP-A"],
                  b3["EP-B"] == pre["EP-B"],
                  b3["EP-C"] == pre["EP-C"],
                  b3["EP-RVK"] == pre["EP-RVK"]))

        # ---- AC-PRP6: pure-read law ------------------------------
        before6 = counts(w)
        for face in (face2, face3):
            for a in AVATARS:
                face.privileges_for(a)
                face.privileges_for(a, client_hints={"x": 1})
            face.has_privilege("EP-A", EXP_PRIV)
            face.has_privilege("EP-B", MAYOR_PRIV)
        r5, _d5 = TM.expect_code(
            lambda: face3.has_privilege("EP-D",
                                        MAYOR_PRIV),
            M.E_TIER_REQUIRED)
        r6, _d6 = TM.expect_code(
            lambda: face3.has_privilege("EP-EMPTY", EXP_PRIV),
            M.E_NO_ACTIVE_PERIOD)
        after6 = counts(w)
        rvk_still_empty = (json.loads(
            priv_battery(face3)["EP-RVK"])["active"] is False)
        ok6 = (r5 and r6 and before6 == after6
               and after6["member_periods"] == 6
               and rvk_still_empty)
        record("AC-PRP6", ok6,
               "read_battery_moved_zero_rows=%s (periods %d,"
               " events %d, vouchers %d, audit %d) refusals=%s%s"
               " rvk_face_still_empty=%s"
               % (before6 == after6, after6["member_periods"],
                  after6["member_credit_events"],
                  after6["member_vouchers"],
                  after6["member_audit"], r5, r6,
                  rvk_still_empty))

        # ---- AC-PRP7: hygiene ------------------------------------
        src_priv = inspect.getsource(M.MemberStore.privileges_for)
        src_has = inspect.getsource(M.MemberStore.has_privilege)
        writes = [kw for kw in WRITE_KW
                  if kw in src_priv or kw in src_has]
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
               and before6 == after6)
        record("AC-PRP7", ok7,
               "write_keywords=%s ascii=%s net_imports=%d"
               " member_sha=%s cfg_sha=%s world_outside=%s"
               " runner_row=%s drift=%d/%d counts_stable=%s"
               % (writes, ascii_ok, len(net_hits),
                  member_sha_in == member_sha_out,
                  cfg_sha_in == cfg_sha_out, world_outside,
                  registered, len(RESULTS), EXPECTED,
                  before6 == after6))

        face2.close()
        face3.close()
    finally:
        # world store was already closed at the AC-PRP2 boundary;
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
