"""Acceptance suite for the member expiring-soon board (tech.md claim
line R1774).

Asserts the pre-registered criteria AC-ES1..AC-ES7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: MemberStore.expiring_soon(days, now=None) - pure-read derived
pre-expiry prediction board (reminder-face consumption candidate):
every ACTIVE period with as_of <= end_utc <= as_of + days is listed
with its whole remaining days (floor), deterministic order, _face
compliance envelope, zero writes.

Usage: python test_expiring_soon.py
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


def set_end(world, avatar, end_utc):
    TM.db_exec(world["member_db"],
               "UPDATE member_periods SET end_utc = ?"
               " WHERE census_avatar_id = ?", (end_utc, avatar))


def expire_row(world, avatar):
    TM.db_exec(world["member_db"],
               "UPDATE member_periods SET status = 'expired'"
               " WHERE census_avatar_id = ?", (avatar,))


def table_counts(world):
    out = {}
    for table in ("member_periods", "member_credit_events",
                  "member_vouchers", "member_audit"):
        out[table] = TM.db_query(world["member_db"],
                                 "SELECT COUNT(*) FROM %s" % table)[0][0]
    return out


def main():
    # ---- AC-ES1: contract, window semantics, manual-SQL cross --------
    w = TM.build()
    _oid, gid = TM.happy(w, "tier_experience", "ES-1", "es-1")
    w["store"].activate(gid, "ES-1")
    set_end(w, "ES-1", M.add_days(AS_OF, 5))
    env = w["store"].expiring_soon(10, now=AS_OF)
    row = env["expiring_soon"][0]
    env_keys = set(env) == {"expiring_soon", "days", "as_of", "count",
                            "ai_generated", "disclaimer", "persistent"}
    row_keys = set(row) == {"census_avatar_id", "period_id", "product_id",
                            "tier", "period_no", "end_utc", "days_left"}
    horizon = M.add_days(AS_OF, 10)
    manual = TM.db_query(
        w["member_db"],
        "SELECT census_avatar_id, period_id, product_id, tier, period_no,"
        " end_utc FROM member_periods WHERE status = 'active'"
        " AND end_utc >= ? AND end_utc <= ?"
        " ORDER BY end_utc, census_avatar_id, period_id",
        (AS_OF, horizon))
    cross = ([(r[0], r[1], r[2], r[3], r[4], r[5]) for r in manual]
             == [(x["census_avatar_id"], x["period_id"], x["product_id"],
                  x["tier"], x["period_no"], x["end_utc"])
                 for x in env["expiring_soon"]])
    left_cross = all(
        x["days_left"] == (M.parse_iso(x["end_utc"]) - M.parse_iso(AS_OF)
                           ).days for x in env["expiring_soon"])
    ok1 = (env_keys and row_keys and env["days"] == 10
           and env["as_of"] == AS_OF and env["count"] == 1
           and env["ai_generated"] == 0 and env["persistent"] is True
           and row["days_left"] == 5 and row["period_no"] == 1
           and row["product_id"] == "tier:experience"
           and row["census_avatar_id"] == "ES-1" and cross and left_cross)
    record("AC-ES1", ok1,
           "env-keys=%s row-keys=%s days_left=%d count=%d cross=%s"
           " left-floor=%s" % (env_keys, row_keys, row["days_left"],
                               env["count"], cross, left_cross))
    TM.tear(w)

    # ---- AC-ES2: bad args fail-closed --------------------------------
    w = TM.build()
    _oid, gid = TM.happy(w, "tier_experience", "ES-2", "es-2")
    w["store"].activate(gid, "ES-2")
    before = table_counts(w)
    days_bad = []
    for bad in (-1, 0, True, "3", 2.5, None):
        refused, ev = expect_code(
            lambda b=bad: w["store"].expiring_soon(b, now=AS_OF),
            M.E_BAD_STATE)
        days_bad.append(refused)
    ts_bad = []
    for bad_ts in ("2030-13-01T00:00:00Z", "not-a-ts", "2030-06-01"):
        refused, ev = expect_code(
            lambda t=bad_ts: w["store"].expiring_soon(3, now=t),
            M.E_BAD_STATE)
        ts_bad.append(refused)
    after = table_counts(w)
    ok2 = all(days_bad) and all(ts_bad) and before == after
    record("AC-ES2", ok2,
           "days-refused=%d/6 ts-refused=%d/3 counts-stable=%s"
           % (sum(1 for r in days_bad if r), sum(1 for r in ts_bad if r),
              before == after))
    TM.tear(w)

    # ---- AC-ES3: boundary semantics (frozen as_of) -------------------
    w = TM.build()
    # (avatar, end_utc, in-board, days_left) - horizon for days=3 is
    # 2030-06-04T00:00:00Z (add_days(AS_OF, 3))
    cases = [
        ("ES-A", AS_OF, True, 0),                  # exactly at as_of
        ("ES-B", "2030-06-04T00:00:00Z", True, 3),  # exactly horizon
        ("ES-C", "2030-06-04T00:00:01Z", False, None),  # one past horizon
        ("ES-D", "2030-05-31T23:59:59Z", False, None),  # past end, active
        ("ES-E", "2030-06-01T23:00:00Z", True, 0),  # 23h left -> floor 0
        ("ES-F", "2030-06-02T00:00:00Z", True, 1),
    ]
    for avatar, _, _, _ in cases:
        _oid, gid = TM.happy(w, "tier_experience", avatar,
                             "es3-" + avatar.lower())
        w["store"].activate(gid, avatar)
    for avatar, end, _, _ in cases:
        set_end(w, avatar, end)
    expire_row(w, "ES-F")
    env3 = w["store"].expiring_soon(3, now=AS_OF)
    got = [(x["census_avatar_id"], x["days_left"])
           for x in env3["expiring_soon"]]
    expected = [("ES-A", 0), ("ES-E", 0), ("ES-B", 3)]
    ok3 = got == expected and env3["count"] == 3
    record("AC-ES3", ok3,
           "board=%s expected=%s count=%d (expired ES-F and out-of-window"
           " ES-C/ES-D absent)" % (got, expected, env3["count"]))

    # ---- AC-ES4: pure-read law ----------------------------------------
    src = inspect.getsource(M.MemberStore.expiring_soon)
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
    before = table_counts(w)
    first = w["store"].expiring_soon(3, now=AS_OF)
    second = w["store"].expiring_soon(3, now=AS_OF)
    after = table_counts(w)
    same = (json.dumps(first, sort_keys=True)
            == json.dumps(second, sort_keys=True))
    ok4 = (not dml) and before == after and same
    record("AC-ES4", ok4,
           "dml-hits=%d counts-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))

    # ---- AC-ES5: reminder due-window alignment ------------------------
    remind_days = int(w["mcfg"]["reminder"]["remind_days_before"])
    due_manual = set(r[0] for r in TM.db_query(
        w["member_db"],
        "SELECT period_id FROM member_periods WHERE status = 'active'"
        " AND end_utc > ? AND end_utc <= ?",
        (AS_OF, M.add_days(AS_OF, remind_days))))
    env5 = w["store"].expiring_soon(remind_days, now=AS_OF)
    live_rows = [x for x in env5["expiring_soon"] if x["end_utc"] > AS_OF]
    board_set = set(x["period_id"] for x in live_rows)
    edge_row = [x for x in env5["expiring_soon"] if x["end_utc"] == AS_OF]
    ok5 = (due_manual == board_set and len(due_manual) == len(live_rows)
           and len(edge_row) == 1 and edge_row[0]["days_left"] == 0
           and edge_row[0]["period_id"] not in due_manual)
    record("AC-ES5", ok5,
           "remind_days=%d due=%d board-live=%d edge-at-as_of=%d"
           " (edge in board, not due: honest superset)"
           % (remind_days, len(due_manual), len(live_rows), len(edge_row)))
    TM.tear(w)

    # ---- AC-ES6: global board + insertion-order determinism -----------
    def build_board(order):
        world = TM.build()
        plan = {"ES-X1": "tier_experience", "ES-X2": "tier_mayor",
                "ES-X3": "tier_experience"}
        ends = {"ES-X1": M.add_days(AS_OF, 2),
                "ES-X2": M.add_days(AS_OF, 2),   # tie -> census break
                "ES-X3": M.add_days(AS_OF, 1)}
        for avatar in order:
            _oid, gid = TM.happy(world, plan[avatar], avatar,
                                 "es6-" + avatar.lower())
            world["store"].activate(gid, avatar)
        for avatar, end in ends.items():
            set_end(world, avatar, end)
        env6 = world["store"].expiring_soon(10, now=AS_OF)
        dump = json.dumps(env6, sort_keys=True)
        avatars = set(x["census_avatar_id"] for x in env6["expiring_soon"])
        seq = [x["census_avatar_id"] for x in env6["expiring_soon"]]
        TM.tear(world)
        return dump, avatars, seq

    dump_x, avatars_x, seq_x = build_board(["ES-X1", "ES-X2", "ES-X3"])
    dump_y, avatars_y, seq_y = build_board(["ES-X3", "ES-X2", "ES-X1"])
    ok6 = (dump_x == dump_y and len(avatars_x) == 3
           and seq_x == ["ES-X3", "ES-X1", "ES-X2"])
    record("AC-ES6", ok6,
           "boards-identical=%s avatars=%d order=%s (tie ES-X1/ES-X2"
           " resolved by census id)" % (dump_x == dump_y, len(avatars_x),
                                        seq_x))

    # ---- AC-ES7: hygiene ----------------------------------------------
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
    additive = (hasattr(M.MemberStore, "expiring_soon")
                and hasattr(M.MemberStore, "activate")
                and hasattr(M.MemberStore, "balance_face")
                and hasattr(M.MemberStore, "consume_credits")
                and hasattr(M.MemberStore, "sweep_expired")
                and "ORDER BY end_utc, census_avatar_id, period_id"
                in inspect.getsource(M.MemberStore.expiring_soon))
    ok7 = ascii_ok and not net_hits and additive
    record("AC-ES7", ok7,
           "ascii=%s subjects=%d network-imports=%d additive-face=%s"
           % (ascii_ok, len(subjects), len(net_hits), additive))

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
