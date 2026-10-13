"""Acceptance suite for the member expiring_distribution fold
read-face derivation purity across an INSTANCE RESTART
(BigDomain R1919 tech-queue claim row; seed = the R1786
AC-ESD1..ESD7 fold semantics + the R1900 AC-ES8..ES14 board
persist sibling - the fold face's own cross-instance restart
example, the default-read restoration, the second-order window
membership and the numeric key-order evidence were
zero-registered; this closes that gap per the R1889..R1918
persist family law).

Asserts the pre-registered criteria AC-ESD8..AC-ESD14 from the
R1919 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (family law): one world drives the TRUE product
path end to end - every period opens via pay order -> place ->
callback -> grant -> store.activate (zero fixture injection,
zero set_end SQL). EP-A experience x1, EP-B mayor x2 (stacking
period_no 2 via the R1912 product-path discovery), EP-C
experience x10 (ten-deep stack: period_no 1..10, ends at
t0 + 30k days - the numeric-order true-path carrier and the
natural out-of-window row family), then EP-D joins AFTER the
first restart for the zero-cache recompute law.

Frozen-anchor ruling (honest note): as_of is pinned to today's
23:59:59Z (end-of-day) rather than the R1900 midnight anchor.
The true-path stacking end carries the grant time-of-day
(t0 + 30k days), so a midnight-anchored 60d horizon excludes
the second-order row by the intraday remainder; the end-of-day
anchor keeps every registered window (d45 / d60 / d29 / d400)
reachable with no boundary tie in any window (minimum margin
~6h), robust at any run time of day.

Registered d60 shape correction (honest note, suite-side
criteria-fix precedent): the pre-registered d60 expectation
{"1": 3, "2": 1} count 4 is arithmetically unreachable in the
claim's own registered world - the EP-C ten-deep stack puts a
SECOND +60d row (EP-C no2) inside any window that holds EP-B
no2, per the claim's own end schedule (period ends at
t0 + 30k days); the world-consistent d60 shape is
{"1": 3, "2": 2} count 5, by_tier {experience: 3, mayor: 2}.
Corrected here with zero product involvement; every other
window keeps its registered shape verbatim.
The numeric key-order evidence is read from the live dict
(list(by_period_no)) because sort_keys dumps destroys key
order - pre-registered claim ruling.

Restart genealogy: face1 loads the world + takes the pre-close
quartet (d45 / d60 / d29 / d400 frozen-param fold reads) + the
default-read band -> close -> face2 reopens (same cfg object,
same db file, same live pay dock) -> default-read band restores
-> one new true-path activation recomputes the fold (zero
cache) -> face3 reopens (two live instances) for the sequential
read identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_expiring_dist_persist.py
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
SUITE_LABEL = "member-expiring-dist-persist"

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
SQL_KW = ("SELECT", "INSERT", "UPDATE ", "DELETE", "REPLACE",
          "CREATE", "DROP ")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

ENV_FOLD = {"expiring_distribution", "days", "as_of", "count",
            "ai_generated", "disclaimer", "persistent"}
WINDOWS = (45, 60, 29, 400)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def band(env):
    """Projection band: strip the clock echo key only."""
    return {k: v for k, v in env.items() if k != "as_of"}


def fold(face, days, as_of):
    return face.expiring_distribution(days, now=as_of)


def battery(face, as_of):
    """Frozen-as_of fold snapshot quartet (d45 / d60 / d29 /
    d400) plus the same-window board counts."""
    envs = [face.expiring_distribution(d, now=as_of)
            for d in WINDOWS]
    boards = {d: face.expiring_soon(d, now=as_of)["count"]
              for d in WINDOWS}
    return envs, boards


def key_order(env):
    return list(env["expiring_distribution"]["by_period_no"])


def sql_group_cross(db, as_of, days):
    """Manual SQL GROUP BY with the window predicate: returns
    ({tier: n}, {period_no: n}) straight from member_periods."""
    horizon = M.add_days(as_of, days)
    tiers = {}
    for tier, n in TM.db_query(
            db, "SELECT tier, COUNT(*) FROM member_periods"
            " WHERE status = 'active' AND end_utc >= ?"
            " AND end_utc <= ? GROUP BY tier", (as_of, horizon)):
        tiers[tier] = int(n)
    lines = {}
    for no, n in TM.db_query(
            db, "SELECT period_no, COUNT(*) FROM member_periods"
            " WHERE status = 'active' AND end_utc >= ?"
            " AND end_utc <= ? GROUP BY period_no",
            (as_of, horizon)):
        lines[str(int(no))] = int(n)
    return tiers, lines


def counts(world):
    out = {}
    for table in ("member_periods", "member_credit_events",
                  "member_vouchers", "member_audit"):
        out[table] = TM.db_query(
            world["member_db"],
            "SELECT COUNT(*) FROM %s" % table)[0][0]
    for table in ("pay_orders", "pay_grants"):
        out[table] = TM.db_query(
            world["pay_db"], "SELECT COUNT(*) FROM %s" % table)[0][0]
    return out


def invariant(env):
    f = env["expiring_distribution"]
    return (sum(f["by_tier"].values())
            == sum(f["by_period_no"].values()) == env["count"])


def main():
    suite_start = M.now_utc()
    as_of = suite_start[:11] + "23:59:59Z"   # today end-of-day

    member_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "member.py"), "rb").read()).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    w = TM.build()
    try:
        # ---- world: true-path stacked grants + activations ------
        # Honest product-path note (R1912 discovery, reused): the
        # pay order id buckets on the CLOSED same-(avatar, product)
        # order count, so a stacked renewal only opens after the
        # prior order rides the granted->closed refund edge; the
        # opened period itself is history and stays active. Each
        # stacked line thus walks: order -> grant -> activate ->
        # (refund edge when another line follows).
        plan = (("EP-A", "tier_experience", 1),
                ("EP-B", "tier_mayor", 2),
                ("EP-C", "tier_experience", 10))
        fresh_ok = True
        for avatar, product, n in plan:
            for k in range(1, n + 1):
                oid, gid = TM.happy(w, product, avatar,
                                    "esd-%s-%02d"
                                    % (avatar.lower(), k))
                resp = w["store"].activate(gid, avatar)
                fresh_ok = (fresh_ok
                            and resp["idempotent"] is False
                            and resp["status"] == "active")
                if k < n:
                    w["pay"].close_refund(oid)
        active_total = TM.db_query(
            w["member_db"], "SELECT COUNT(*) FROM member_periods"
            " WHERE status = 'active'")[0][0]

        pre_envs, pre_boards = battery(w["store"], as_of)
        d45, d60, d29, d400 = pre_envs
        s = tuple(dumps(x) for x in pre_envs)
        def1 = w["store"].expiring_distribution(45)
        band1 = band(def1)

        # ---- AC-ESD8: world load + pre-close fold snapshot set ---
        keys_ok = all(set(e) == ENV_FOLD for e in pre_envs)
        echo_ok = (d45["days"] == 45 and d60["days"] == 60
                   and d29["days"] == 29 and d400["days"] == 400
                   and all(e["as_of"] == as_of
                           for e in pre_envs))
        shape_ok = (d45["expiring_distribution"]
                    == {"by_tier": {"experience": 2, "mayor": 1},
                        "by_period_no": {"1": 3}}
                    and d45["count"] == 3
                    and d60["expiring_distribution"]
                    == {"by_tier": {"experience": 3, "mayor": 2},
                        "by_period_no": {"1": 3, "2": 2}}
                    and d60["count"] == 5
                    and d29["expiring_distribution"]
                    == {"by_tier": {}, "by_period_no": {}}
                    and d29["count"] == 0
                    and d400["count"] == 13
                    and d400["expiring_distribution"]["by_tier"]
                    == {"experience": 11, "mayor": 2})
        kset = set(d400["expiring_distribution"]["by_period_no"])
        order400 = key_order(d400)
        numeric_ok = (kset == {str(i) for i in range(1, 11)}
                      and order400 == [str(i) for i in range(1, 11)])
        inv_ok = all(invariant(e) for e in pre_envs)
        single_ok = all(
            e["count"] == pre_boards[e["days"]]
            for e in pre_envs)
        cross_ok = True
        for e in pre_envs:
            t, l = sql_group_cross(w["member_db"], as_of, e["days"])
            if (t != e["expiring_distribution"]["by_tier"]
                    or l != e["expiring_distribution"]["by_period_no"]):
                cross_ok = False
        excl_ok = (active_total == 13 and d45["count"] == 3
                   and active_total - d45["count"] == 10
                   and d60["count"] == 5)
        default_ok = (band1 == band(d45)
                     and def1["as_of"] != as_of)
        ok8 = (fresh_ok and keys_ok and echo_ok and shape_ok
               and numeric_ok and inv_ok and single_ok
               and cross_ok and excl_ok and default_ok)
        record("AC-ESD8", ok8,
               "fresh=%s active=%d shapes_ok=%s keys7=%s"
               " numeric_order=%s inv=%s single_source=%s"
               " sql_cross=%s excluded_from_d45=%d"
               " default_band==frozen=%s (as_of end-of-day"
               " anchor; d60 shape corrected to the claim's own"
               " world arithmetic: EP-C no2 also lands at +60d)"
               % (fresh_ok, active_total, shape_ok, keys_ok,
                  numeric_ok, inv_ok, single_ok, cross_ok,
                  active_total - d45["count"],
                  band1 == band(d45)))

        # ---- AC-ESD9: cross-restart byte identity (core) --------
        w["store"].close()
        face2 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        envs2, boards2 = battery(face2, as_of)
        s2 = tuple(dumps(x) for x in envs2)
        again = fold(face2, 45, as_of)
        order2 = [key_order(e) for e in envs2]
        order_pre = [key_order(e) for e in pre_envs]
        ok9 = (s2 == s and order2 == order_pre
               and dumps(again) == s[0]
               and all(e["count"] == boards2[e["days"]]
                       for e in envs2))
        record("AC-ESD9", ok9,
               "quartet==pre=%s key_orders==pre=%s"
               " reread_self_identical=%s single_source=%s"
               " (fresh instance re-derives identical bytes:"
               " zero in-memory state drift)"
               % (s2 == s, order2 == order_pre,
                  dumps(again) == s[0],
                  all(e["count"] == boards2[e["days"]]
                      for e in envs2)))

        # ---- AC-ESD10: default read restores across restart ------
        def2 = face2.expiring_distribution(45)
        band2 = band(def2)
        cells_stable = (band2 == band1
                        and band2 == band(fold(face2, 45, as_of)))
        ok10 = (cells_stable and def2["as_of"] != as_of)
        record("AC-ESD10", ok10,
               "band(face2_default)==band(face1_default)=%s"
               " cells==frozen_d45=%s as_off_clock=%s (default"
               " as_of rides the real clock minute-drift: band"
               " projection strips the echo, per R1902 law)"
               % (band2 == band1,
                  band2 == band(fold(face2, 45, as_of)),
                  def2["as_of"] != as_of))

        # ---- AC-ESD11: new activation recomputes (zero cache) ----
        _oid_d, gid_d = TM.happy(w, "tier_experience", "EP-D",
                                "esd-ep-d")
        resp_d = face2.activate(gid_d, "EP-D")
        n45 = fold(face2, 45, as_of)
        n60 = fold(face2, 60, as_of)
        n400 = fold(face2, 400, as_of)
        t45, l45 = sql_group_cross(w["member_db"], as_of, 45)
        old_prefix_ok = True
        for old, new in ((d45, n45), (d60, n60), (d400, n400)):
            of, nf = (old["expiring_distribution"],
                      new["expiring_distribution"])
            grew = {"1": of["by_period_no"]["1"] + 1}
            for key, val in of["by_period_no"].items():
                if key != "1":
                    grew[key] = val
            old_prefix_ok = (old_prefix_ok
                             and nf["by_period_no"] == grew
                             and nf["by_tier"]
                             == dict(of["by_tier"],
                                     experience=(of["by_tier"]
                                                 ["experience"] + 1)))
        ok11 = (resp_d["idempotent"] is False
                and resp_d["status"] == "active"
                and dumps(n45) != s[0]
                and n45["count"] == 4
                and n45["expiring_distribution"]
                == {"by_tier": {"experience": 3, "mayor": 1},
                    "by_period_no": {"1": 4}}
                and n60["count"] == 6
                and n60["expiring_distribution"]
                == {"by_tier": {"experience": 4, "mayor": 2},
                    "by_period_no": {"1": 4, "2": 2}}
                and n400["count"] == 14
                and key_order(n400) == order_pre[3]
                and old_prefix_ok
                and t45 == n45["expiring_distribution"]["by_tier"]
                and l45 == n45["expiring_distribution"]
                ["by_period_no"])
        record("AC-ESD11", ok11,
               "ep_d_fresh=%s d45_3to4=%s d60_5to6=%s"
               " d400_13to14=%s board_changed=%s"
               " old_cells_prefix_stable=%s sql_cross=%s"
               " key_order_stable=%s (recomputed from db,"
               " zero cache)"
               % (resp_d["idempotent"] is False,
                  n45["count"] == 4, n60["count"] == 6,
                  n400["count"] == 14, dumps(n45) != s[0],
                  old_prefix_ok,
                  t45 == n45["expiring_distribution"]["by_tier"],
                  key_order(n400) == order_pre[3]))

        # ---- AC-ESD12: window exclusion + covering window --------
        active14 = TM.db_query(
            w["member_db"], "SELECT COUNT(*) FROM member_periods"
            " WHERE status = 'active'")[0][0]
        n29 = fold(face2, 29, as_of)
        board400 = face2.expiring_soon(400, now=as_of)["count"]
        ok12 = (dumps(n29) == s[2]
                and n29["count"] == 0
                and active14 == 14
                and n45["count"] == 4
                and active14 - n45["count"] == 10
                and n400["count"] == active14
                and board400 == active14)
        record("AC-ESD12", ok12,
               "d29_still_byte_empty=%s active=%d d45_count=%d"
               " excluded=%d covering_three_way=%s (out-of-window"
               " rows never backfill; d400 fold==board==active"
               " = single derivation source)"
               % (dumps(n29) == s[2], active14, n45["count"],
                  active14 - n45["count"],
                  n400["count"] == active14 == board400))

        # ---- AC-ESD13: dual-instance sequential identity ---------
        face3 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        envs3, _ = battery(face3, as_of)
        f2_again, _ = battery(face2, as_of)
        s3 = tuple(dumps(x) for x in envs3)
        sf2 = tuple(dumps(x) for x in f2_again)
        pair_ok = (sf2 == s3
                   and [key_order(e) for e in envs3]
                   == order_pre
                   and tuple(dumps(x) for x in f2_again) == sf2)
        d_f2 = face2.expiring_distribution(45)
        d_f3 = face3.expiring_distribution(45)
        band_ok = band(d_f2) == band(d_f3)
        ok13 = (pair_ok and band_ok
                and d_f2["count"] == 4 and d_f3["count"] == 4)
        record("AC-ESD13", ok13,
               "frozen_quartet_face2==face3=%s key_orders=%s"
               " face2_reread_self=%s default_band_pair=%s"
               " count=%d"
               % (sf2 == s3,
                  [key_order(e) for e in envs3] == order_pre,
                  tuple(dumps(x) for x in f2_again) == sf2,
                  band_ok, d_f2["count"]))

        # ---- AC-ESD14: pure-read law + hygiene --------------------
        src_fold = inspect.getsource(
            M.MemberStore.expiring_distribution)
        sql_hits = [kw for kw in SQL_KW if kw in src_fold]
        write_hits = [kw for kw in WRITE_KW if kw in src_fold]
        before14 = counts(w)
        for face in (face2, face3):
            for d in WINDOWS:
                face.expiring_distribution(d, now=as_of)
            face.expiring_distribution(45)
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
            clock_live = (M.parse_iso(M.now_utc())
                          >= M.parse_iso(suite_start))
        except ValueError:
            clock_live = False
        ok14 = (not sql_hits and not write_hits
                and before14 == after14
                and before14["member_periods"] == 14
                and before14["pay_orders"] == 14
                and before14["pay_grants"] == 14
                and ascii_ok and not net_hits
                and member_sha_in == member_sha_out
                and cfg_sha_in == cfg_sha_out
                and world_outside and registered and drift
                and clock_live)
        record("AC-ESD14", ok14,
               "sql_in_fold=%s write_kw=%s counts_stable=%s"
               " (periods %d, events %d, vouchers %d, audit %d,"
               " pay_orders %d, pay_grants %d), member_sha=%s,"
               " cfg_sha=%s, ascii=%s, net_imports=%d,"
               " world_outside=%s, runner_row=%s, drift=%d/%d,"
               " clock_live=%s (suite-only round: zero product"
               " change; fold holds no SQL per R1779 law)"
               % (sql_hits, write_hits, before14 == after14,
                  before14["member_periods"],
                  before14["member_credit_events"],
                  before14["member_vouchers"],
                  before14["member_audit"],
                  before14["pay_orders"],
                  before14["pay_grants"],
                  member_sha_in == member_sha_out,
                  cfg_sha_in == cfg_sha_out, ascii_ok,
                  len(net_hits), world_outside, registered,
                  len(RESULTS), EXPECTED, clock_live))

        face2.close()
        face3.close()
    finally:
        # world store was already closed at the AC-ESD9 boundary;
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
