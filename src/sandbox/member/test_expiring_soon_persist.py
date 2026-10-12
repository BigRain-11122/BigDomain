"""Acceptance suite for the member expiring_soon board + distribution
fold read-face derivation purity across an INSTANCE RESTART
(BigDomain R1900 tech-queue claim row; seed = the R1774 AC-ES1..ES7
window board + the R1786 AC-ESD1..ESD7 fold semantics - both
in-ce, while the cross-instance restart example was zero-registered;
this closes that sibling gap per the R1889..R1899 persist family
law: a fresh face instance on the same db must re-derive the same
board bytes, the dedup map must be db state, a new true-path
activation must recompute the board, and out-of-window rows must
never echo).

Asserts the pre-registered criteria AC-ES8..AC-ES14 from the R1900
tech.md claim line (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (family law): one world drives the TRUE product
path end to end - every period opens via pay order -> place ->
callback -> grant -> store.activate (zero fixture injection, zero
set_end SQL). Period ends are the real clock + 30 tier days, so the
frozen as_of read parameter (today's UTC midnight, computed once at
suite start) carries the window determinism: every in-window row has
days_left == 30 structurally, regardless of the time of day.

Restart genealogy: face1 loads the world + takes the pre-close
snapshot quartet (board / fold / near-boundary empty / far-boundary
empty) -> close -> face2 reopens (same cfg object, same db file,
same live pay dock) -> same-grant re-activation stays idempotent
(db-backed dedup) -> one new true-path activation recomputes the
board (zero cache) -> face3 reopens again (two live instances) for
the sequential read identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_expiring_soon_persist.py
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

FAR_AS_OF = "2030-06-01T00:00:00Z"     # far-boundary read anchor
CFG_PATH = os.path.join(BASE, "config.json")
RUNNER_SRC = os.path.join(BASE, "..", "reconcile_all.py")
SUITE_LABEL = "member-expiring-soon-persist"

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

ENV_BOARD = {"expiring_soon", "days", "as_of", "count",
             "ai_generated", "disclaimer", "persistent"}
ENV_FOLD = {"expiring_distribution", "days", "as_of", "count",
            "ai_generated", "disclaimer", "persistent"}
ROW_KEYS = {"census_avatar_id", "period_id", "product_id", "tier",
            "period_no", "end_utc", "days_left"}


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


def battery(face, as_of):
    """Frozen-as_of snapshot quartet: main board / fold / near
    boundary (empty) / far boundary (empty)."""
    return (face.expiring_soon(45, now=as_of),
            face.expiring_distribution(45, now=as_of),
            face.expiring_soon(29, now=as_of),
            face.expiring_soon(45, now=FAR_AS_OF))


def board_rows(env):
    return env["expiring_soon"]


def main():
    suite_start = M.now_utc()
    as_of = suite_start[:11] + "00:00:00Z"   # today's UTC midnight

    member_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "member.py"), "rb").read()).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    w = TM.build()
    try:
        # ---- world: three true-path grants + activations ------
        plan = (("EP-A", "tier_experience"), ("EP-B", "tier_mayor"),
                ("EP-C", "tier_experience"))
        grants = {}
        periods = {}
        fresh_ok = True
        for avatar, product in plan:
            _oid, gid = TM.happy(w, product, avatar,
                                 "ep-" + avatar.lower().split("-")[1])
            resp = w["store"].activate(gid, avatar)
            grants[avatar] = gid
            periods[avatar] = resp["period_id"]
            fresh_ok = (fresh_ok and resp["idempotent"] is False
                        and resp["status"] == "active")
        pre = battery(w["store"], as_of)
        (b45, d45, b29, bfut) = pre
        s = tuple(dumps(x) for x in pre)

        # ---- AC-ES8: world load + pre-close snapshot set --------
        rows = board_rows(b45)
        horizon = M.add_days(as_of, 45)
        manual = TM.db_query(
            w["member_db"],
            "SELECT census_avatar_id, period_id, product_id, tier,"
            " period_no, end_utc FROM member_periods"
            " WHERE status = 'active' AND end_utc >= ?"
            " AND end_utc <= ?"
            " ORDER BY end_utc, census_avatar_id, period_id",
            (as_of, horizon))
        cross = ([(r[0], r[1], r[2], r[3], int(r[4]), r[5])
                  for r in manual]
                 == [(x["census_avatar_id"], x["period_id"],
                      x["product_id"], x["tier"], x["period_no"],
                      x["end_utc"]) for x in rows])
        left_cross = all(
            x["days_left"] == (M.parse_iso(x["end_utc"])
                               - M.parse_iso(as_of)).days
            for x in rows)
        prod_map = {x["census_avatar_id"]: x["product_id"]
                    for x in rows}
        tier_map = {x["census_avatar_id"]: x["tier"] for x in rows}
        default_pre = w["store"].expiring_soon(45)
        default_left = sorted(x["days_left"] for x
                              in board_rows(default_pre))
        ok8 = (fresh_ok
               and set(b45) == ENV_BOARD and b45["days"] == 45
               and b45["as_of"] == as_of and b45["count"] == 3
               and b45["ai_generated"] == 0
               and b45["persistent"] is True
               and isinstance(b45["disclaimer"], str)
               and len(rows) == 3
               and all(set(x) == ROW_KEYS for x in rows)
               and all(x["days_left"] == 30 for x in rows)
               and all(x["period_no"] == 1 for x in rows)
               and {x["census_avatar_id"] for x in rows}
               == {"EP-A", "EP-B", "EP-C"}
               and prod_map == {"EP-A": "tier:experience",
                                "EP-B": "tier:mayor",
                                "EP-C": "tier:experience"}
               and tier_map == {"EP-A": "experience",
                                "EP-B": "mayor",
                                "EP-C": "experience"}
               and all(x["end_utc"] > as_of for x in rows)
               and cross and left_cross
               and b29["count"] == 0 and board_rows(b29) == []
               and set(b29) == ENV_BOARD
               and bfut["count"] == 0 and board_rows(bfut) == []
               and bfut["as_of"] == FAR_AS_OF
               and set(d45) == ENV_FOLD and d45["count"] == 3
               and d45["as_of"] == as_of and d45["days"] == 45
               and d45["expiring_distribution"]
               == {"by_tier": {"experience": 2, "mayor": 1},
                   "by_period_no": {"1": 3}}
               and d45["count"] == b45["count"]
               and default_pre["count"] == 3
               and default_pre["as_of"] != as_of
               and default_left in ([29, 29, 29], [29, 29, 30],
                                    [29, 30, 30], [30, 30, 30]))
        record("AC-ES8", ok8,
               "fresh_activations=%s count=%d days_left30=%s"
               " cross=%s left_floor=%s empty_near=%s empty_far=%s"
               " fold=%s default_count=%d default_left_in_range=%s"
               % (fresh_ok, b45["count"],
                  all(x["days_left"] == 30 for x in rows), cross,
                  left_cross, b29["count"] == 0, bfut["count"] == 0,
                  d45["expiring_distribution"], default_pre["count"],
                  default_left in ([29, 29, 29], [29, 29, 30],
                                   [29, 30, 30], [30, 30, 30])))

        # ---- AC-ES9: cross-restart byte identity (core) ---------
        w["store"].close()
        face2 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        pre2 = battery(face2, as_of)
        ident = tuple(dumps(x) for x in pre2)
        again = face2.expiring_soon(45, now=as_of)
        default2 = face2.expiring_soon(45)
        ok9 = (ident == s
               and dumps(again) == ident[0]
               and again["count"] == 3
               and default2["count"] == 3
               and default2["as_of"] != as_of)
        record("AC-ES9", ok9,
               "quartet==pre=%s self_identical=%s count=%d"
               " default_shape_count=%d (default as_of rides the"
               " real clock: minute-drift, shape-only per seed note)"
               % (ident == s, dumps(again) == ident[0],
                  again["count"], default2["count"]))

        # ---- AC-ES10: same-grant re-activation idempotency -----
        c_before = counts(w)
        resp_a = face2.activate(grants["EP-A"], "EP-A")
        c_after = counts(w)
        b45_re = face2.expiring_soon(45, now=as_of)
        ok10 = (resp_a["idempotent"] is True
                and resp_a["period_id"] == periods["EP-A"]
                and resp_a["status"] == "active"
                and dumps(b45_re) == s[0]
                and c_before == c_after
                and c_after["member_periods"] == 3)
        record("AC-ES10", ok10,
               "idempotent=%s same_period=%s board_unchanged=%s"
               " periods=%d counts_stable=%s (dedup map = db state"
               " across the restart boundary)"
               % (resp_a["idempotent"],
                  resp_a["period_id"] == periods["EP-A"],
                  dumps(b45_re) == s[0],
                  c_after["member_periods"], c_before == c_after))

        # ---- AC-ES11: new activation recomputes (zero cache) ----
        _oid_d, gid_d = TM.happy(w, "tier_experience", "EP-D",
                                 "ep-d")
        resp_d = face2.activate(gid_d, "EP-D")
        pre_rows = board_rows(json.loads(s[0]))
        b45_c = face2.expiring_soon(45, now=as_of)
        rows_c = board_rows(b45_c)
        d45_c = face2.expiring_distribution(45, now=as_of)
        manual_c = TM.db_query(
            w["member_db"],
            "SELECT census_avatar_id, period_id, product_id, tier,"
            " period_no, end_utc FROM member_periods"
            " WHERE status = 'active' AND end_utc >= ?"
            " AND end_utc <= ?"
            " ORDER BY end_utc, census_avatar_id, period_id",
            (as_of, horizon))
        cross_c = ([(r[0], r[1], r[2], r[3], int(r[4]), r[5])
                    for r in manual_c]
                   == [(x["census_avatar_id"], x["period_id"],
                        x["product_id"], x["tier"], x["period_no"],
                        x["end_utc"]) for x in rows_c])
        ok11 = (resp_d["idempotent"] is False
                and resp_d["status"] == "active"
                and b45_c["count"] == 4
                and rows_c[3]["census_avatar_id"] == "EP-D"
                and rows_c[3]["days_left"] == 30
                and dumps(rows_c[0:3]) == dumps(pre_rows)
                and dumps(b45_c) != s[0]
                and d45_c["expiring_distribution"]
                == {"by_tier": {"experience": 3, "mayor": 1},
                    "by_period_no": {"1": 4}}
                and cross_c)
        record("AC-ES11", ok11,
               "ep_d_fresh=%s count=%d new_row_last=%s"
               " old_prefix_stable=%s board_changed=%s fold=%s"
               " cross=%s (recomputed from db, zero cache)"
               % (resp_d["idempotent"] is False, b45_c["count"],
                  rows_c[3]["census_avatar_id"] == "EP-D",
                  dumps(rows_c[0:3]) == dumps(pre_rows),
                  dumps(b45_c) != s[0],
                  d45_c["expiring_distribution"], cross_c))

        # ---- AC-ES12: window-boundary zero penetration ----------
        active_total = TM.db_query(
            w["member_db"],
            "SELECT COUNT(*) FROM member_periods"
            " WHERE status = 'active'")[0][0]
        b29_c = face2.expiring_soon(29, now=as_of)
        bfut_c = face2.expiring_soon(45, now=FAR_AS_OF)
        b60_c = face2.expiring_soon(60, now=as_of)
        ok12 = (active_total == 4
                and b29_c["count"] == 0 and board_rows(b29_c) == []
                and bfut_c["count"] == 0 and board_rows(bfut_c) == []
                and b60_c["count"] == 4)
        record("AC-ES12", ok12,
               "active_rows_in_db=%d near_boundary_echo=%d"
               " far_boundary_echo=%d covering_window_echo=%d"
               " (rows live in the db; only the derived window"
               " decides the echo)"
               % (active_total, b29_c["count"], bfut_c["count"],
                  b60_c["count"]))

        # ---- AC-ES13: dual-instance sequential identity ---------
        face3 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        f2 = battery(face2, as_of)
        f3 = battery(face3, as_of)
        f2b = battery(face2, as_of)
        s2 = tuple(dumps(x) for x in f2)
        s3 = tuple(dumps(x) for x in f3)
        pair_ok = s2 == s3
        d_f2 = face2.expiring_soon(45)
        d_f3 = face3.expiring_soon(45)

        def core_rows(env):
            return [(x["census_avatar_id"], x["period_id"],
                     x["end_utc"], x["days_left"])
                    for x in board_rows(env)]

        ok13 = (pair_ok
                and tuple(dumps(x) for x in f2b) == s2
                and dumps(f3[0]) == s2[0]
                and core_rows(d_f2) == core_rows(d_f3)
                and d_f2["count"] == 4 and d_f3["count"] == 4
                and d_f2["as_of"] != as_of)
        record("AC-ES13", ok13,
               "frozen_quartet_face2==face3=%s face2_reread=%s"
               " face3==snapshot=%s default_rows_core_equal=%s"
               " default_count=%d (default as_of drifts per"
               " instance: core row elements compared, per seed"
               " minute-exemption note)"
               % (pair_ok,
                  tuple(dumps(x) for x in f2b) == s2,
                  dumps(f3[0]) == s2[0],
                  core_rows(d_f2) == core_rows(d_f3),
                  d_f2["count"]))

        # ---- AC-ES14: pure-read law + hygiene --------------------
        src_board = inspect.getsource(M.MemberStore.expiring_soon)
        src_fold = inspect.getsource(
            M.MemberStore.expiring_distribution)
        writes = [kw for kw in WRITE_KW
                  if kw in src_board or kw in src_fold]
        before14 = counts(w)
        face3.expiring_soon(45, now=as_of)
        face3.expiring_soon(29, now=as_of)
        face3.expiring_soon(60, now=as_of)
        face3.expiring_soon(45, now=FAR_AS_OF)
        face3.expiring_soon(45)
        face3.expiring_soon(29)
        face3.expiring_distribution(45, now=as_of)
        face3.expiring_distribution(29, now=as_of)
        after14 = counts(w)
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
        clock_live = True
        try:
            now_probe = M.parse_iso(M.now_utc())
            clock_live = now_probe >= M.parse_iso(suite_start)
        except ValueError:
            clock_live = False
        ok14 = (not writes and before14 == after14
                and before14["member_periods"] == 4
                and ascii_ok and not net_hits
                and member_sha_in == member_sha_out
                and cfg_sha_in == cfg_sha_out
                and world_outside and registered and drift
                and clock_live)
        record("AC-ES14", ok14,
               "write_keywords=%s counts_stable=%s (periods %d,"
               " events %d, vouchers %d, audit %d), member_sha=%s,"
               " cfg_sha=%s, ascii=%s, net_imports=%d,"
               " world_outside=%s, runner_row=%s, drift=%d/%d,"
               " clock_live=%s (as_of is param-injected: no"
               " global clock state to restore)"
               % (writes, before14 == after14,
                  before14["member_periods"],
                  before14["member_credit_events"],
                  before14["member_vouchers"],
                  before14["member_audit"],
                  member_sha_in == member_sha_out,
                  cfg_sha_in == cfg_sha_out, ascii_ok,
                  len(net_hits), world_outside, registered,
                  len(RESULTS), EXPECTED, clock_live))

        face2.close()
        face3.close()
    finally:
        # world store was already closed at the AC-ES9 boundary;
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
