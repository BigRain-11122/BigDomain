"""Acceptance suite for the member birth_cert_face read-face
derivation purity across an INSTANCE RESTART
(BigDomain R1918 tech-queue claim row; seed = the R1915 seed -
member.py birth_cert_face L474 in-ce, the permanent entrance
qualification judgement source, while the cross-instance
restart example was zero-registered; this closes that sibling
gap per the R1889..R1917 persist family law: a fresh face
instance on the same db must re-derive the same face bytes, a
new true-path grant must recompute the face (zero cache), a
refund recomputes the live judgement while first_granted_utc
stays the historical anchor, and the activation marker stamp
must survive and re-stamp across the restart boundary).

Asserts the pre-registered criteria AC-BCP1..AC-BCP7 from the
R1918 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (family law): one world drives the TRUE product
path end to end - every grant rides pay order -> place ->
callback -> grant (TM.happy), activations go through
MemberStore.activate (the birth marker stamp), refunds ride
PayOrders.close_refund (zero fixture injection, zero raw SQL
world mutation). The face under test is a pure derivation over
pay.grants_for + the member_audit marker row: it carries no
now() parameter, so byte-identity needs no clock freezing.

Restart genealogy: face1 loads the world + takes the pre-close
six-face snapshot (five avatars + the blank probe) -> close ->
face2 reopens (same cfg object, same db file, same live pay
dock) -> the six faces replay byte-identically -> new grant /
refund / activation recomputes re-derive from db state (zero
cache) -> face3 reopens (two live instances) for the
sequential read identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_birthcert_persist.py
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

SUITE_LABEL = "member-birthcert-persist"
CFG_PATH = os.path.join(BASE, "config.json")
RUNNER_SRC = os.path.join(BASE, "..", "reconcile_all.py")

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

ENV_KEYS = {"census_avatar_id", "birth_cert", "permanent",
            "first_granted_utc", "member_domain_marker",
            "judgement_source", "ai_generated", "disclaimer",
            "persistent"}
JUDGEMENT_SRC = ("pay.grants_for (lobby E_ENTRANCE_REQUIRED"
                 " face)")
# five real avatars + the blank probe, fixed read order
AVATARS = ("BC-A", "BC-B", "BC-C", "BC-D", "BC-E", "")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def manual_live(world, avatar):
    return TM.db_query(
        world["pay_db"],
        "SELECT COUNT(*) FROM pay_grants g LEFT JOIN pay_orders"
        " o ON o.order_id = g.order_id"
        " WHERE g.census_avatar_id = ? AND o.status = 'granted'",
        (avatar,))[0][0]


def manual_first(world, avatar):
    return TM.db_query(
        world["pay_db"],
        "SELECT MIN(granted_utc) FROM pay_grants"
        " WHERE census_avatar_id = ?", (avatar,))[0][0]


def manual_marker(world, avatar):
    return TM.db_query(
        world["member_db"],
        "SELECT COUNT(*) FROM member_audit WHERE audit_id = ?",
        (M._h("audit", "birth", avatar),))[0][0]


def counts(world):
    out = {}
    for table in ("member_periods", "member_credit_events",
                  "member_vouchers", "member_audit"):
        out[table] = TM.db_query(
            world["member_db"],
            "SELECT COUNT(*) FROM %s" % table)[0][0]
    for table in ("pay_orders", "pay_grants"):
        out[table] = TM.db_query(
            world["pay_db"],
            "SELECT COUNT(*) FROM %s" % table)[0][0]
    return out


def battery(face):
    return [face.birth_cert_face(a) for a in AVATARS]


def battery_dumps(face):
    return [dumps(f) for f in battery(face)]


def main():
    member_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "member.py"), "rb").read()
    ).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    w = TM.build()
    try:
        # ---- world: five true-path avatar shapes --------------
        # BC-A: one grant + activation -> cert True, marker True
        oid_a, gid_a = TM.happy(w, "tier_experience", "BC-A",
                                "bc-a")
        resp_a = w["store"].activate(gid_a, "BC-A")
        # BC-B: two grants, only the first activated
        _oid_b1, gid_b1 = TM.happy(w, "tier_experience", "BC-B",
                                   "bc-b1")
        _oid_b2, _gid_b2 = TM.happy(w, "tier_mayor", "BC-B",
                                    "bc-b2")
        resp_b1 = w["store"].activate(gid_b1, "BC-B")
        # BC-C: one grant, never activated (judgement/domain
        # marker split face)
        oid_c, gid_c = TM.happy(w, "tier_experience", "BC-C",
                                "bc-c")
        # BC-D: one grant + activation, then refund-closed
        oid_d, _gid_d = TM.happy(w, "tier_mayor", "BC-D", "bc-d")
        resp_d = w["store"].activate(_gid_d, "BC-D")
        env_d = w["pay"].close_refund(oid_d)
        # BC-E: zero rows; blank probe: zero rows
        fresh = (resp_a["idempotent"] is False
                and resp_a["status"] == "active"
                and resp_b1["idempotent"] is False
                and resp_d["idempotent"] is False
                and env_d["status"] == "closed")

        pre = battery(w["store"])
        s_pre = [dumps(f) for f in pre]

        # ---- AC-BCP1: world load + pre-close face set ---------
        face_a, face_b, face_c, face_d, face_e, face_blank = pre
        cross_ok = True
        for f in pre:
            if set(f) != ENV_KEYS:
                cross_ok = False
        m_live = {a: manual_live(w, a) for a in AVATARS}
        m_first = {a: manual_first(w, a) for a in AVATARS}
        m_mark = {a: manual_marker(w, a) for a in AVATARS}
        # three-way manual-SQL cross per avatar
        cross_ok = (cross_ok
                    and all(face_a["birth_cert"] is True
                            for _ in [0])
                    and face_a["birth_cert"] == (m_live["BC-A"] > 0)
                    and face_b["birth_cert"] == (m_live["BC-B"] > 0)
                    and face_c["birth_cert"] == (m_live["BC-C"] > 0)
                    and face_d["birth_cert"] == (m_live["BC-D"] > 0)
                    and face_e["birth_cert"] is False
                    and face_blank["birth_cert"] is False
                    and face_a["first_granted_utc"] == m_first["BC-A"]
                    and face_b["first_granted_utc"] == m_first["BC-B"]
                    and face_c["first_granted_utc"] == m_first["BC-C"]
                    and face_d["first_granted_utc"] == m_first["BC-D"]
                    and face_a["member_domain_marker"]
                    == (m_mark["BC-A"] > 0)
                    and face_c["member_domain_marker"]
                    == (m_mark["BC-C"] > 0)
                    and face_e["member_domain_marker"] is False)
        b_grants = w["pay"].grants_for("BC-B")["items"]
        ok1 = (fresh
               and all(set(f) == ENV_KEYS for f in pre)
               and len(pre) == 6
               and face_a["census_avatar_id"] == "BC-A"
               and face_a["birth_cert"] is True
               and face_a["permanent"] is True
               and face_a["member_domain_marker"] is True
               and face_a["first_granted_utc"] == m_first["BC-A"]
               and face_a["judgement_source"] == JUDGEMENT_SRC
               and face_a["ai_generated"] == 0
               and face_a["persistent"] is True
               and isinstance(face_a["disclaimer"], str)
               and face_b["birth_cert"] is True
               and face_b["member_domain_marker"] is True
               and len(b_grants) == 2
               and face_b["first_granted_utc"] == m_first["BC-B"]
               and b_grants[0]["granted_utc"] <= b_grants[1][
                   "granted_utc"]
               and face_c["birth_cert"] is True
               and face_c["member_domain_marker"] is False
               and face_d["birth_cert"] is False
               and face_d["member_domain_marker"] is True
               and face_d["first_granted_utc"] == m_first["BC-D"]
               and face_e["birth_cert"] is False
               and face_e["first_granted_utc"] is None
               and face_e["member_domain_marker"] is False
               and face_blank["census_avatar_id"] == ""
               and face_blank["birth_cert"] is False
               and face_blank["first_granted_utc"] is None
               and face_blank["member_domain_marker"] is False
               and m_live == {"BC-A": 1, "BC-B": 2, "BC-C": 1,
                              "BC-D": 0, "BC-E": 0, "": 0}
               and cross_ok)
        record("AC-BCP1", ok1,
               "fresh_paths=%s envelope9=%s live=%s "
               "cross_3way=%s marker_split(BC-C True/False)=%s"
               " refund_honest(BC-D False)=%s blank_probe=%s"
               % (fresh, all(set(f) == ENV_KEYS for f in pre),
                  m_live, cross_ok,
                  face_c["birth_cert"] is True
                  and face_c["member_domain_marker"] is False,
                  face_d["birth_cert"] is False,
                  face_blank["census_avatar_id"] == ""))

        # ---- AC-BCP2: cross-restart byte identity (core) ------
        w["store"].close()
        face2 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        s_2 = battery_dumps(face2)
        again = battery_dumps(face2)
        ok2 = (s_2 == s_pre and again == s_pre)
        record("AC-BCP2", ok2,
               "six_faces==pre=%s reread==pre=%s (same cfg/db/"
               "pay dock, zero in-memory drift; face carries no"
               " clock field)"
               % (s_2 == s_pre, again == s_pre))

        # ---- AC-BCP3: zero-cache recompute post-restart -------
        f_before = face2.birth_cert_face("BC-F")
        oid_f, _gid_f = TM.happy(w, "tier_experience", "BC-F",
                                 "bc-f")
        f_after = face2.birth_cert_face("BC-F")
        first_b_pre = face2.birth_cert_face("BC-B")[
            "first_granted_utc"]
        # create_order is content-addressed per (avatar, product,
        # closed-bucket): a genuinely new grant for BC-B needs the
        # third tier product (tier_cocreator, the tier_products
        # sandbox dock trio)
        _oid_b3, _gid_b3 = TM.happy(w, "tier_cocreator", "BC-B",
                                    "bc-b3")
        f_b_post = face2.birth_cert_face("BC-B")
        ok3 = (f_before["birth_cert"] is False
               and f_before["first_granted_utc"] is None
               and f_after["birth_cert"] is True
               and f_after["first_granted_utc"] == manual_first(
                   w, "BC-F")
               and manual_live(w, "BC-F") == 1
               and f_b_post["birth_cert"] is True
               and f_b_post["first_granted_utc"] == first_b_pre
               and manual_live(w, "BC-B") == 3)
        record("AC-BCP3", ok3,
               "bc_f False->True=%s bc_b first_stable=%s "
               "live_b=3=%s (recomputed from db, zero cache;"
               " MIN law keeps the historical anchor)"
               % (f_before["birth_cert"] is False
                  and f_after["birth_cert"] is True,
                  f_b_post["first_granted_utc"] == first_b_pre,
                  manual_live(w, "BC-B") == 3))

        # ---- AC-BCP4: refund recompute post-restart -----------
        first_a_pre = face2.birth_cert_face("BC-A")[
            "first_granted_utc"]
        marker_a_pre = face2.birth_cert_face("BC-A")[
            "member_domain_marker"]
        env_a = w["pay"].close_refund(oid_a)
        f_a_post = face2.birth_cert_face("BC-A")
        # refund-state anchor: the post-refund face is the state
        # the dual-instance read (AC-BCP6) must replay, not the
        # pre-close snapshot (the refund intentionally moved it)
        s_a_refunded = dumps(f_a_post)
        ok4 = (env_a["status"] == "closed"
               and f_a_post["birth_cert"] is False
               and f_a_post["first_granted_utc"] == first_a_pre
               and f_a_post["member_domain_marker"] is True
               and marker_a_pre is True
               and manual_live(w, "BC-A") == 0
               and manual_first(w, "BC-A") == first_a_pre)
        record("AC-BCP4", ok4,
               "refund_live_flip=%s first_preserved=%s "
               "marker_preserved=%s (refund undoes the purchase,"
               " not history: R1721 semantics across the"
               " restart boundary)"
               % (f_a_post["birth_cert"] is False,
                  f_a_post["first_granted_utc"] == first_a_pre,
                  f_a_post["member_domain_marker"] is True))

        # ---- AC-BCP5: activation marker stamp post-restart ----
        c_before = face2.birth_cert_face("BC-C")
        resp_c2 = face2.activate(gid_c, "BC-C")
        c_after = face2.birth_cert_face("BC-C")
        periods_before = counts(w)["member_periods"]
        resp_b1_re = face2.activate(gid_b1, "BC-B")
        periods_after = counts(w)["member_periods"]
        b_face_re = face2.birth_cert_face("BC-B")
        ok5 = (c_before["member_domain_marker"] is False
               and resp_c2["idempotent"] is False
               and resp_c2["status"] == "active"
               and c_after["member_domain_marker"] is True
               and c_after["birth_cert"] is True
               and resp_b1_re["idempotent"] is True
               and resp_b1_re["period_id"] == resp_b1["period_id"]
               and periods_before == periods_after
               and b_face_re["member_domain_marker"] is True)
        record("AC-BCP5", ok5,
               "marker_flip(BC-C False->True)=%s idem_reactivate"
               "(BC-B)=%s periods_stable=%s (the birth stamp is"
               " first-paid-activation domain state, restart"
               " carried)"
               % (c_before["member_domain_marker"] is False
                  and c_after["member_domain_marker"] is True,
                  resp_b1_re["idempotent"] is True,
                  periods_before == periods_after))

        # ---- AC-BCP6: dual-instance sequential identity ------
        face3 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        s_f2 = battery_dumps(face2)
        s_f3 = battery_dumps(face3)
        s_f2b = battery_dumps(face2)
        ok6 = (s_f2 == s_f3 and s_f2b == s_f2
               and s_f2[0] == s_a_refunded
               )
        record("AC-BCP6", ok6,
               "face2==face3=%s face2_reread=%s "
               "bc_a_refund_state_anchor=%s"
               " (two live instances replay the same six-face"
               " bytes; BC-A anchors on its post-refund state)"
               % (s_f2 == s_f3, s_f2b == s_f2,
                  s_f2[0] == s_a_refunded))

        # ---- AC-BCP7: pure-read law + hygiene -----------------
        src_face = inspect.getsource(M.MemberStore.birth_cert_face)
        writes = [kw for kw in WRITE_KW if kw in src_face]
        before7 = counts(w)
        for _ in range(2):
            for f in battery(face3):
                dumps(f)
        d_first = battery_dumps(face3)
        d_second = battery_dumps(face3)
        after7 = counts(w)
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
        ok7 = (not writes and before7 == after7
               and before7["member_periods"] == 4
               and before7["pay_orders"] == 7
               and before7["pay_grants"] == 7
               and d_first == d_second
               and ascii_ok and not net_hits
               and member_sha_in == member_sha_out
               and cfg_sha_in == cfg_sha_out
               and world_outside and registered and drift)
        record("AC-BCP7", ok7,
               "write_keywords=%s counts_stable=%s (periods %d,"
               " orders %d, grants %d), double_read_identical=%s,"
               " member_sha=%s, cfg_sha=%s, ascii=%s,"
               " net_imports=%d, world_outside=%s, runner_row=%s,"
               " drift=%d/%d"
               % (writes, before7 == after7,
                  before7["member_periods"],
                  before7["pay_orders"],
                  before7["pay_grants"],
                  d_first == d_second,
                  member_sha_in == member_sha_out,
                  cfg_sha_in == cfg_sha_out, ascii_ok,
                  len(net_hits), world_outside, registered,
                  len(RESULTS), EXPECTED))

        face2.close()
        face3.close()
    finally:
        # world store was already closed at the AC-BCP2 boundary;
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
