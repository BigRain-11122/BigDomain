"""Acceptance suite for the member expiring-board tier/line fold
(tech.md claim line R1786).

Asserts the pre-registered criteria AC-ESD1..AC-ESD7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: MemberStore.expiring_distribution(days, now=None) -
aggregation-only pure-read face: folds the expiring_soon board by
tier and period line with ascending deterministic keys. The window
derivation lives solely in expiring_soon (single derivation source,
R1779 wiring law); this method holds no SQL at all.

Usage: python test_expiring_dist.py
"""

import inspect
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_member as TM               # noqa: E402 (build/tear/happy reuse)
import member as M                     # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
AS_OF = "2030-06-01T00:00:00Z"          # injected clock (frozen window)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_code(fn, *codes):
    try:
        fn()
    except M.MemberError as exc:
        return exc.code in codes, "%s (detail=%s)" % (exc.code,
                                                     exc.detail or "-")
    return False, "no-error-raised"


def set_end_pid(world, pid, end_utc):
    TM.db_exec(world["member_db"],
               "UPDATE member_periods SET end_utc = ?"
               " WHERE period_id = ?", (end_utc, pid))


def table_counts(world):
    out = {}
    for table in ("member_periods", "member_credit_events",
                  "member_vouchers", "member_audit"):
        out[table] = TM.db_query(world["member_db"],
                                 "SELECT COUNT(*) FROM %s" % table)[0][0]
    return out


def main():
    # ---- AC-ESD1: contract, single source, deterministic order ------
    w = TM.build()
    plan = [("ESD-A", "tier_experience"), ("ESD-B", "tier_mayor"),
            ("ESD-C", "tier_cocreator"), ("ESD-D", "tier_experience")]
    first_oid = None
    for avatar, prod in plan:
        oid, gid = TM.happy(w, prod, avatar, "esd1-" + avatar.lower())
        if avatar == "ESD-A":
            first_oid = oid
        w["store"].activate(gid, avatar)
    # same-line renewal for ESD-A -> period_no 2 (stacking law; the
    # second order line only opens after the first order reached its
    # terminal closed state - the AC-M2 machine-edge walk, no policy
    # invented here)
    TM.db_exec(w["pay_db"],
               "UPDATE pay_orders SET status = 'closed'"
               " WHERE order_id = ?", (first_oid,))
    _oid, gid = TM.happy(w, "tier_experience", "ESD-A", "esd1-a2")
    w["store"].activate(gid, "ESD-A")
    ends = {("ESD-A", 1): M.add_days(AS_OF, 2),
            ("ESD-A", 2): M.add_days(AS_OF, 4),
            ("ESD-B", 1): M.add_days(AS_OF, 5),
            ("ESD-C", 1): M.add_days(AS_OF, 8),
            ("ESD-D", 1): M.add_days(AS_OF, 9)}
    for (avatar, no), end in ends.items():
        set_end_pid(w, TM.period_of(w, avatar, no), end)
    env = w["store"].expiring_distribution(10, now=AS_OF)
    env_keys = set(env) == {"expiring_distribution", "days", "as_of",
                            "count", "ai_generated", "disclaimer",
                            "persistent"}
    fold = env["expiring_distribution"]
    fold_keys = set(fold) == {"by_tier", "by_period_no"}
    by_tier, by_line = fold["by_tier"], fold["by_period_no"]
    values_ok = (by_tier == {"cocreator": 1, "experience": 3, "mayor": 1}
                 and by_line == {"1": 4, "2": 1} and env["count"] == 5
                 and env["days"] == 10 and env["as_of"] == AS_OF)
    sums_ok = (env["count"] == sum(by_tier.values())
               == sum(by_line.values()))
    tier_order = list(by_tier.keys()) == sorted(by_tier.keys())
    line_order = list(by_line.keys()) == sorted(by_line.keys(), key=int)
    trio = (env["ai_generated"] == 0 and env["persistent"] is True
            and env["disclaimer"])
    src = inspect.getsource(M.MemberStore.expiring_distribution)
    single_source = ("expiring_soon(days, now)" in src
                    and all(word not in src for word in
                            ("SELECT", "INSERT", "UPDATE", "DELETE")))
    ok1 = (env_keys and fold_keys and values_ok and sums_ok
           and tier_order and line_order and trio and single_source)
    record("AC-ESD1", ok1,
           "env=%s fold=%s values=%s sums=%s tier-order=%s"
           " line-order=%s trio=%s single-source=%s"
           % (env_keys, fold_keys, values_ok, sums_ok, tier_order,
              line_order, trio, single_source))

    # ---- AC-ESD2: bad args fail-closed through the single gate -------
    before = table_counts(w)
    days_bad = []
    for bad in (True, 0, -1, "3", 2.5, None):
        refused, ev = expect_code(
            lambda b=bad: w["store"].expiring_distribution(b, now=AS_OF),
            M.E_BAD_STATE)
        days_bad.append(refused)
    ts_bad = []
    for bad_ts in ("2030-13-01T00:00:00Z", "not-a-ts", "2030-06-01"):
        refused, ev = expect_code(
            lambda t=bad_ts: w["store"].expiring_distribution(3, now=t),
            M.E_BAD_STATE)
        ts_bad.append(refused)
    after = table_counts(w)
    ok2 = all(days_bad) and all(ts_bad) and before == after
    record("AC-ESD2", ok2,
           "days-refused=%d/6 ts-refused=%d/3 counts-stable=%s"
           % (sum(1 for r in days_bad if r),
              sum(1 for r in ts_bad if r), before == after))

    # ---- AC-ESD3: three-way cross validation -------------------------
    board_env = w["store"].expiring_soon(10, now=AS_OF)
    board = board_env["expiring_soon"]
    cnt_tier, cnt_line = {}, {}
    for row in board:
        cnt_tier[row["tier"]] = cnt_tier.get(row["tier"], 0) + 1
        key = str(row["period_no"])
        cnt_line[key] = cnt_line.get(key, 0) + 1
    horizon = M.add_days(AS_OF, 10)
    sql_tier = dict(TM.db_query(
        w["member_db"],
        "SELECT tier, COUNT(*) FROM member_periods"
        " WHERE status = 'active' AND end_utc >= ? AND end_utc <= ?"
        " GROUP BY tier", (AS_OF, horizon)))
    sql_line = {str(no): c for no, c in TM.db_query(
        w["member_db"],
        "SELECT period_no, COUNT(*) FROM member_periods"
        " WHERE status = 'active' AND end_utc >= ? AND end_utc <= ?"
        " GROUP BY period_no", (AS_OF, horizon))}
    dist = w["store"].expiring_distribution(10, now=AS_OF)
    fold3 = dist["expiring_distribution"]
    ok3 = (fold3["by_tier"] == cnt_tier == sql_tier
           and fold3["by_period_no"] == cnt_line == sql_line)
    record("AC-ESD3", ok3,
           "tier three-way=%s line three-way=%s (tier=%s line=%s)"
           % (fold3["by_tier"] == cnt_tier == sql_tier,
              fold3["by_period_no"] == cnt_line == sql_line,
              fold3["by_tier"], fold3["by_period_no"]))

    # ---- AC-ESD4: scope isolation inherited from the board -----------
    # E: in-window but expired; F: active but beyond horizon;
    # G: active but end_utc before as_of (unswept lapsed line).
    _oid, gid = TM.happy(w, "tier_mayor", "ESD-E", "esd4-e")
    w["store"].activate(gid, "ESD-E")
    set_end_pid(w, TM.period_of(w, "ESD-E", 1), M.add_days(AS_OF, 2))
    TM.db_exec(w["member_db"],
               "UPDATE member_periods SET status = 'expired'"
               " WHERE census_avatar_id = 'ESD-E'")
    _oid, gid = TM.happy(w, "tier_cocreator", "ESD-F", "esd4-f")
    w["store"].activate(gid, "ESD-F")
    set_end_pid(w, TM.period_of(w, "ESD-F", 1), M.add_days(AS_OF, 30))
    _oid, gid = TM.happy(w, "tier_experience", "ESD-G", "esd4-g")
    w["store"].activate(gid, "ESD-G")
    set_end_pid(w, TM.period_of(w, "ESD-G", 1), "2030-05-31T00:00:00Z")
    after4 = w["store"].expiring_distribution(10, now=AS_OF)
    fold4 = after4["expiring_distribution"]
    ok4 = (fold4["by_tier"] == {"cocreator": 1, "experience": 3,
                                "mayor": 1}
           and fold4["by_period_no"] == {"1": 4, "2": 1}
           and after4["count"] == 5)
    record("AC-ESD4", ok4,
           "expired/beyond-horizon/pre-window all excluded: %s"
           % (fold4,))

    # ---- AC-ESD5: empty board + numeric key order ---------------------
    w0 = TM.build()
    empty = w0["store"].expiring_distribution(10, now=AS_OF)
    ok_empty = (empty["expiring_distribution"]["by_tier"] == {}
                and empty["expiring_distribution"]["by_period_no"] == {}
                and empty["count"] == 0)
    # direct fixture rows (test-side direct rows, noted per R1730
    # family precedent) with line numbers 2 and 10: key order must be
    # numeric ("2" before "10"), not lexicographic.
    for no in (2, 10):
        TM.db_exec(
            w0["member_db"],
            "INSERT INTO member_periods (period_id, census_avatar_id,"
            " product_id, tier, period_no, start_utc, end_utc, status,"
            " source_grant_id) VALUES (?,?,?,?,?,?,?,?,?)",
            ("fx-pid-%d" % no, "ESD-FX", "tier:experience",
             "experience", no, AS_OF, M.add_days(AS_OF, 1),
             "active", "fx-grant-%d" % no))
    numeric = w0["store"].expiring_distribution(10, now=AS_OF)
    nb = numeric["expiring_distribution"]["by_period_no"]
    ok_numeric = (list(nb.keys()) == ["2", "10"]
                  and nb == {"2": 1, "10": 1} and numeric["count"] == 2)
    record("AC-ESD5", ok_empty and ok_numeric,
           "empty-ok=%s numeric-key-order=%s keys=%s"
           % (ok_empty, ok_numeric, list(nb.keys())))
    TM.tear(w0)

    # ---- AC-ESD6: pure-read law + liveness ---------------------------
    before6 = table_counts(w)
    d1 = w["store"].expiring_distribution(10, now=AS_OF)
    d2 = w["store"].expiring_distribution(10, now=AS_OF)
    after6 = table_counts(w)
    pure = (before6 == after6
            and json.dumps(d1, sort_keys=True)
            == json.dumps(d2, sort_keys=True)
            and json.dumps(d1) == json.dumps(d2))
    _oid, gid = TM.happy(w, "tier_mayor", "ESD-H", "esd6-h")
    w["store"].activate(gid, "ESD-H")
    set_end_pid(w, TM.period_of(w, "ESD-H", 1), M.add_days(AS_OF, 3))
    d3 = w["store"].expiring_distribution(10, now=AS_OF)
    fold6 = d3["expiring_distribution"]
    live = (fold6["by_tier"]["mayor"] == 2
            and fold6["by_period_no"]["1"] == 5 and d3["count"] == 6)
    ok6 = pure and live
    record("AC-ESD6", ok6,
           "counts-stable=%s double-call-identical=%s liveness=%s"
           " (mayor 1->2, line1 4->5, count 5->6)"
           % (before6 == after6,
              json.dumps(d1) == json.dumps(d2), live))

    # ---- AC-ESD7: hygiene ----------------------------------------------
    subjects = [os.path.join(BASE, "member.py"), os.path.abspath(__file__)]
    ascii_ok = True
    net_hits = []
    for path in subjects:
        with open(path, "rb") as fh:
            data = fh.read()
        if any(b > 127 for b in data):
            ascii_ok = False
        text = data.decode("ascii", "replace")
        for line in text.splitlines():
            stripped = line.strip()
            if (stripped.startswith("import ")
                    or stripped.startswith("from ")) and (
                    re.search(r"\b(urllib|requests|socket|http)\b",
                              stripped)):
                net_hits.append(stripped)
    runner_src = ""
    with open(os.path.join(os.path.dirname(BASE), "reconcile_all.py"),
              encoding="utf-8") as fh:
        runner_src = fh.read()
    registered = '"member-expiring-dist"' in runner_src
    additive = (hasattr(M.MemberStore, "expiring_distribution")
                and hasattr(M.MemberStore, "expiring_soon")
                and hasattr(M.MemberStore, "activate")
                and hasattr(M.MemberStore, "balance_face")
                and hasattr(M.MemberStore, "consume_credits")
                and hasattr(M.MemberStore, "sweep_expired")
                and "by_period_no" in inspect.getsource(
                    M.MemberStore.expiring_distribution))
    ok7 = ascii_ok and not net_hits and registered and additive
    record("AC-ESD7", ok7,
           "ascii=%s subjects=%d network-imports=%d"
           " suites-registered=%s additive-face=%s"
           % (ascii_ok, len(subjects), len(net_hits), registered,
              additive))
    TM.tear(w)

    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
