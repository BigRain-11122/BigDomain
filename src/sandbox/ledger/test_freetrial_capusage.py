"""Acceptance suite for the free-trial per-grant cap-distance
profile board (BigDomain R1842 tech-queue claim row; seed = the
freetrial.py calls_by_account R1837 face plus the cap_usage
seed text). Asserts the pre-registered criteria AC-CCU1..
AC-CCU8 from the R1842 tech.md claim line (criteria were
registered before this code existed; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Family law = the R1730/R1732/R1735/R1784/R1793 window line
with the count-domain verdict registered in the claim row:
window=None keeps every grant row on the board; an explicit
YYYY-MM month window filters GRANT rows by their granted_utc
record-time stamp, while calls_used and remaining stay
LIFETIME counts for the surviving rows (the count domain is
never sliced by the window - "who is close to the cap" is a
property of the grant's whole life).

Fixture worlds (test-side direct writes, the R1730 family
precedent, noted here): a history grant row for usr:hist-g is
injected straight into trial_grants with an older-month
granted_utc stamp, and its two call rows carry CURRENT-month
stamps - so the older-month windowed read still shows the
lifetime count (the count-domain-not-sliced evidence). The
negative-remaining world directly appends five extra call
rows past bob's cap (only direct injection can produce
used > cap: the live call gate refuses at the cap, asserted
live here) - the face must surface the negative remaining,
not hide it (AC-CCU5, the R1776 AC-CHM3 law). dave converts
on his plan before any read: his grant row must stay on the
board and the conversion register must never merge into it.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_capusage.py
"""

import datetime
import hashlib
import inspect
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700 registry)
import freetrial as T                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 8

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
             " tier is a trial allowance, not investment advice")

BAD_FORMS = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
             "202610", "abcd", "", 2026, True, 2.5,
             "2026-10\n", "2026-10 ", "2026-10\r"]

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _month_now():
    return datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m")


def _prev_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)


def _next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return "%04d-%02d" % (y, m)


def _stamp(ym, day):
    return "%s-%02dT12:00:00Z" % (ym, day)


def main():
    cur_m = _month_now()
    m2 = _prev_month(cur_m)          # the recent history month
    m1 = _prev_month(m2)             # the older history month
    fut = _next_month(cur_m)         # the future month

    tmp = tempfile.mkdtemp(prefix="freetrial-capusage-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)

    import sqlite3
    ftconn = sqlite3.connect(ft.db_path)

    def _counts():
        return tuple(
            ftconn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("trial_plans", "trial_grants",
                      "trial_calls", "trial_conversions"))

    # -- zero-grant world first (honest empty state) ---------------
    zero = ft.cap_usage_board()
    ok_zero = (zero["cap_usage_board"] == []
               and zero["total"] == 0
               and set(zero.keys()) ==
               {"cap_usage_board", "total", "disclaimer"}
               and zero["disclaimer"] == DISCLAIMER)

    # -- live flow: devs, plans, grants, calls, one conversion ----
    for dev, kinds in (("usr:alice", ("backtest", "visualize")),
                       ("usr:bob", ("backtest",)),
                       ("usr:carol", ("backtest",)),
                       ("usr:dave", ("backtest",))):
        dk.issue_key(dev, "%s-key" % dev.split(":")[1], 100,
                     kinds, False)
    pa = ft.register_trial_plan("alpha-starter",
                                "Alpha Starter Tier", 3, False)
    pb = ft.register_trial_plan("beta-pro", "Beta Pro Trial",
                                5, True)
    pc = ft.register_trial_plan("gamma-mini", "Gamma Mini Trial",
                                4, False)
    ft.grant_trial("usr:alice", pa["plan_id"])
    ft.grant_trial("usr:alice", pc["plan_id"])
    ft.grant_trial("usr:bob", pb["plan_id"])
    ft.grant_trial("usr:carol", pb["plan_id"])
    ft.grant_trial("usr:dave", pc["plan_id"])
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a1", "eng-x")
    ft.trial_call("usr:alice", pa["plan_id"], "visualize",
                  "a2", "eng-x")
    ft.trial_call("usr:bob", pb["plan_id"], "backtest",
                  "b1", "eng-y")
    ft.trial_call("usr:carol", pb["plan_id"], "backtest",
                  "c1", "eng-y")
    conv = ft.convert_upgrade("usr:dave", pc["plan_id"],
                              "standard-tier")

    # -- history fixture rows (direct writes, noted in header) ----
    # a history grant stamped in the older month m1, whose two
    # call rows carry CURRENT-month stamps: the m1 windowed read
    # must still show the lifetime count (count domain never
    # sliced by the window).
    ftconn.execute(
        "INSERT INTO trial_grants (plan_id, dev_account,"
        " granted_utc) VALUES (?,?,?)",
        (pa["plan_id"], "usr:hist-g", _stamp(m1, 2)))
    for ref, day in (("hg1", 4), ("hg2", 6)):
        ftconn.execute(
            "INSERT INTO trial_calls (plan_id, dev_account,"
            " kind, call_ref, engine_ref, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (pa["plan_id"], "usr:hist-g", "backtest", ref,
             "eng-x", _stamp(cur_m, day)))
    ftconn.commit()

    counts_before = _counts()

    # expected board (ascending dev_account, then plan_id):
    #   usr:alice/pa  cap 3 used 2 remaining 1  ai_label 0
    #   usr:alice/pc  cap 4 used 0 remaining 4  ai_label 0
    #   usr:bob/pb    cap 5 used 1 remaining 4  ai_label 1
    #   usr:carol/pb  cap 5 used 1 remaining 4  ai_label 1
    #   usr:dave/pc   cap 4 used 0 remaining 4  ai_label 0
    #   usr:hist-g/pa cap 3 used 2 remaining 1  ai_label 0
    want_pairs = [("usr:alice", pa["plan_id"]),
                  ("usr:alice", pc["plan_id"]),
                  ("usr:bob", pb["plan_id"]),
                  ("usr:carol", pb["plan_id"]),
                  ("usr:dave", pc["plan_id"]),
                  ("usr:hist-g", pa["plan_id"])]
    want_used = {("usr:alice", pa["plan_id"]): 2,
                 ("usr:alice", pc["plan_id"]): 0,
                 ("usr:bob", pb["plan_id"]): 1,
                 ("usr:carol", pb["plan_id"]): 1,
                 ("usr:dave", pc["plan_id"]): 0,
                 ("usr:hist-g", pa["plan_id"]): 2}
    want_caps = {pa["plan_id"]: 3, pb["plan_id"]: 5,
                 pc["plan_id"]: 4}
    ROW_KEYS = {"dev_account", "plan_id", "plan_key", "title",
                "trial_cap", "calls_used", "remaining",
                "granted_utc", "ai_label"}

    # -- AC-CCU1 contract, ordering, invariants -------------------
    env = ft.cap_usage_board()
    board = env["cap_usage_board"]
    got_pairs = [(r["dev_account"], r["plan_id"]) for r in board]
    ok1 = (ok_zero
           and set(env.keys()) ==
           {"cap_usage_board", "total", "disclaimer"}
           and env["total"] == len(board) == 6
           and got_pairs == want_pairs
           and all(set(r.keys()) == ROW_KEYS for r in board)
           and all(r["remaining"] ==
                   r["trial_cap"] - r["calls_used"]
                   for r in board)
           and all(r["calls_used"] == want_used[(r["dev_account"],
                                                 r["plan_id"])]
                   for r in board)
           and all(r["trial_cap"] ==
                   want_caps[r["plan_id"]] for r in board)
           and board[0]["ai_label"] == 0
           and board[2]["ai_label"] == 1
           and board[0]["plan_key"] == "alpha-starter"
           and board[5]["granted_utc"] == _stamp(m1, 2)
           and env["disclaimer"] == DISCLAIMER
           and conv["dev_account"] == "usr:dave")
    wenv = ft.cap_usage_board(cur_m)
    ok1 = (ok1
           and set(wenv.keys()) ==
           {"cap_usage_board", "total", "disclaimer", "window"}
           and wenv["window"] == cur_m)
    with open(os.path.join(BASE, "config.json"), "rb") as h2:
        ok1 = ok1 and (h2.read() == cfg_bytes)
    record("AC-CCU1", ok1,
           "zero-grant world honest empty (%s); envelope keys"
           " exact; 6 grant rows in (dev,plan) ascending order"
           " %s; row keys exact 9; remaining==cap-used and"
           " calls_used==expected per row; ai_label rides rows;"
           " converted dave row still on board while the"
           " conversion register never merges (total %s =="
           " grant count); window key additive; config bytes"
           " stable"
           % (ok_zero, got_pairs, env["total"]))

    # -- AC-CCU2 malformed windows fail closed -------------------
    ok2 = True
    trace2 = []
    for form in BAD_FORMS:
        try:
            ft.cap_usage_board(form)
            ok2 = False
            trace2.append("accepted:%r" % (form,))
        except T.TrialError as exc:
            if exc.code != T.E_FT_BAD_ARGS:
                ok2 = False
                trace2.append("wrongcode:%r" % (form,))
    ok2 = ok2 and (_counts() == counts_before)
    try:
        ft.cap_usage_board(None)     # sole default sentinel
    except T.TrialError:
        ok2 = False
        trace2.append("None-rejected")
    record("AC-CCU2", ok2,
           "%d bad forms rejected E_FT_BAD_ARGS; four-table"
           " counts unchanged %s; None default accepted %s"
           % (len(BAD_FORMS), counts_before, trace2))

    # -- AC-CCU3 window filters the GRANT row set only -----------
    e_m1 = ft.cap_usage_board(m1)
    e_m2 = ft.cap_usage_board(m2)
    e_fut = ft.cap_usage_board(fut)
    m1_rows = e_m1["cap_usage_board"]
    ok3 = (e_m1["window"] == m1
           and e_m1["total"] == 1
           and len(m1_rows) == 1
           and m1_rows[0]["dev_account"] == "usr:hist-g"
           and m1_rows[0]["plan_id"] == pa["plan_id"]
           # the count-domain-not-sliced verdict: the two
           # current-month fixture calls still count on the
           # older-month windowed read of this grant row
           and m1_rows[0]["calls_used"] == 2
           and m1_rows[0]["remaining"] == 1
           and e_m2["cap_usage_board"] == []
           and e_m2["total"] == 0
           and e_fut["cap_usage_board"] == []
           and e_fut["total"] == 0)
    default_read = ft.cap_usage_board()
    ok3 = (ok3
           and default_read["total"] == 6
           and {r["dev_account"]
               for r in default_read["cap_usage_board"]} ==
           {"usr:alice", "usr:bob", "usr:carol", "usr:dave",
            "usr:hist-g"})
    record("AC-CCU3", ok3,
           "m1 window keeps only the m1-stamped grant row and"
           " its calls_used==%s stays the LIFETIME count (two"
           " current-month calls - count domain never sliced);"
           " m2/future windows honest empty %s/%s; default read"
           " carries all 6 grants; zero cross-month grant"
           " leakage"
           % (m1_rows[0]["calls_used"] if m1_rows else "?",
              e_m2["total"], e_fut["total"]))

    # -- AC-CCU4 manual SQL cross-validation ---------------------
    ok4 = True
    for r in board:
        sql_used = ftconn.execute(
            "SELECT COUNT(*) FROM trial_calls WHERE"
            " dev_account = ? AND plan_id = ?",
            (r["dev_account"], r["plan_id"])).fetchone()[0]
        ok4 = ok4 and (sql_used == r["calls_used"])
        ok4 = ok4 and (r["remaining"] ==
                       r["trial_cap"] - sql_used)
    sql_pairs = ftconn.execute(
        "SELECT g.dev_account, g.plan_id FROM trial_grants g"
        " JOIN trial_plans p ON p.plan_id = g.plan_id"
        " ORDER BY g.dev_account, g.plan_id").fetchall()
    sql_total = ftconn.execute(
        "SELECT COUNT(*) FROM trial_grants").fetchone()[0]
    ok4 = (ok4
           and [(str(a), int(b)) for a, b in sql_pairs] ==
           got_pairs
           and sql_total == env["total"])
    wsql_pairs = ftconn.execute(
        "SELECT g.dev_account, g.plan_id FROM trial_grants g"
        " JOIN trial_plans p ON p.plan_id = g.plan_id"
        " WHERE substr(g.granted_utc, 1, 7) = ?"
        " ORDER BY g.dev_account, g.plan_id",
        (m1,)).fetchall()
    ok4 = (ok4
           and [(str(a), int(b)) for a, b in wsql_pairs] ==
           [(r["dev_account"], r["plan_id"])
            for r in m1_rows])
    record("AC-CCU4", ok4,
           "per-row calls_used == manual SQL COUNT per"
           " (dev,plan); remaining == cap-used arithmetic; row"
           " order == SQL ORDER BY dev_account,plan_id %s;"
           " total %s == COUNT(trial_grants); windowed pairs =="
           " windowed SQL" % (got_pairs, env["total"]))

    # -- AC-CCU5 negative remaining surfaces (never hidden) -------
    # structural law (seed canon: remaining is structurally
    # NON-NEGATIVE in live worlds - the live gate refuses once
    # used >= cap, so a successful call lands used <= cap and
    # remaining >= 0; remaining == 0 at a full cap is the legal
    # conversion-gate trigger state, not a negative value).
    # The CCU1 snapshot fact for this world: every row still
    # has headroom (remaining >= 1) - recorded as world fact,
    # not as the structural law (the claim-row correction).
    ok5 = all(r["remaining"] >= 0 for r in board)
    ok5 = ok5 and all(r["remaining"] >= 1 for r in board)
    # headroom anchor: alice cap 3 used 2 -> the third live
    # call SUCCEEDS and lands remaining == 0 (legal live state)
    alice_live_ok = False
    try:
        ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                      "a3-live", "eng-x")
        alice_live_ok = True
    except T.TrialError:
        alice_live_ok = False
    ok5 = ok5 and alice_live_ok
    cap_env = ft.cap_usage_board()
    alice_row = [r for r in cap_env["cap_usage_board"]
                 if r["dev_account"] == "usr:alice"
                 and r["plan_id"] == pa["plan_id"]][0]
    ok5 = ok5 and (alice_row["calls_used"] == 3
                   and alice_row["remaining"] == 0)
    # bob used 1 < cap 5: inject five extra call rows straight
    # past the gate -> used 6 > cap 5 -> remaining -1
    for i in range(5):
        ftconn.execute(
            "INSERT INTO trial_calls (plan_id, dev_account,"
            " kind, call_ref, engine_ref, called_utc)"
            " VALUES (?,?,?,?,?,?)",
            (pb["plan_id"], "usr:bob", "backtest",
             "bn%d" % i, "eng-x", _stamp(cur_m, 20 + i)))
    ftconn.commit()
    neg = ft.cap_usage_board()
    neg_rows = {(r["dev_account"], r["plan_id"]): r
                for r in neg["cap_usage_board"]}
    bob_row = neg_rows[("usr:bob", pb["plan_id"])]
    ok5 = (ok5
           and bob_row["calls_used"] == 6
           and bob_row["remaining"] == -1
           and neg["total"] == 6
           and [r["dev_account"] for r in neg["cap_usage_board"]]
           == ["usr:alice", "usr:alice", "usr:bob",
               "usr:carol", "usr:dave", "usr:hist-g"])
    # the live gate now refuses bob: past-cap is injection-only
    live_refused = False
    try:
        ft.trial_call("usr:bob", pb["plan_id"], "backtest",
                      "b-live", "eng-y")
    except T.TrialError as exc:
        live_refused = (exc.code == T.E_FT_QUOTA)
    ok5 = ok5 and live_refused
    record("AC-CCU5", ok5,
           "pre-call snapshot: all remaining >= 1 in this world"
           " (world fact; structural law is >= 0 - the seed's"
           " non-negative canon); headroom call succeeded and"
           " landed alice remaining == 0 at the full cap (legal"
           " conversion-gate trigger state); directly-injected"
           " past-cap world: bob row surfaces calls_used=6"
           " remaining=-1 in ascending slot 3 of 6, counted on"
           " the board (total %s == grant count); live call"
           " attempt on the past-cap grant now refuses"
           " E_FT_QUOTA (%s) - negative remaining is"
           " injection-only, never hidden"
           % (neg["total"], live_refused))

    counts_mid = _counts()

    # -- AC-CCU6 pure-read law ------------------------------------
    src = inspect.getsource(T.FreeTrialFace.cap_usage_board)
    banned = ("INSERT INTO", "REPLACE INTO",
              "UPDATE ", "DELETE FROM")
    ok6 = not any(b in src for b in banned)
    ok6 = ok6 and (_counts() == counts_mid)
    a1_ = json.dumps(ft.cap_usage_board(), sort_keys=True)
    a2_ = json.dumps(ft.cap_usage_board(), sort_keys=True)
    b1_ = json.dumps(ft.cap_usage_board())
    b2_ = json.dumps(ft.cap_usage_board())
    ok6 = ok6 and (a1_ == a2_) and (b1_ == b2_)
    wa = json.dumps(ft.cap_usage_board(m1), sort_keys=True)
    wb = json.dumps(ft.cap_usage_board(m1), sort_keys=True)
    ok6 = ok6 and (wa == wb)
    record("AC-CCU6", ok6,
           "method source free of data-changing statements;"
           " four-table counts unchanged %s; double-call dumps"
           " byte-identical (sorted and insertion order);"
           " windowed double-call identical" % (counts_mid,))

    # -- AC-CCU7 live zero-cache derivation -----------------------
    mid_counts = _counts()
    ft.trial_call("usr:carol", pb["plan_id"], "backtest",
                  "c2", "eng-y")
    after = ft.cap_usage_board()
    after_rows = {(r["dev_account"], r["plan_id"]): r
                  for r in after["cap_usage_board"]}
    ok7 = (after_rows[("usr:carol", pb["plan_id"])]
           ["calls_used"] == 2
           and after_rows[("usr:carol", pb["plan_id"])]
           ["remaining"] == 3
           and after_rows[("usr:alice", pa["plan_id"])]
           ["calls_used"] == 3
           and after_rows[("usr:alice", pa["plan_id"])]
           ["remaining"] == 0
           and after_rows[("usr:bob", pb["plan_id"])]
           ["calls_used"] == 6
           and after_rows[("usr:bob", pb["plan_id"])]
           ["remaining"] == -1
           and after_rows[("usr:hist-g", pa["plan_id"])]
           ["calls_used"] == 2
           and after["total"] == 6)
    w_after = ft.cap_usage_board(cur_m)
    w_carol = [r for r in w_after["cap_usage_board"]
               if r["dev_account"] == "usr:carol"]
    ok7 = (ok7
           and len(w_carol) == 1
           and w_carol[0]["calls_used"] == 2
           and w_carol[0]["remaining"] == 3)
    m1_after = ft.cap_usage_board(m1)
    ok7 = (ok7
           and m1_after["cap_usage_board"][0]["calls_used"] == 2
           and _counts() != mid_counts)
    record("AC-CCU7", ok7,
           "new live call under cap: carol row calls_used 1->2"
           " remaining 4->3; alice/pa row still carries the CCU5"
           " headroom call (used 3, remaining 0); bob past-cap"
           " row and hist-g row unchanged; total %s; windowed"
           " read follows; m1 windowed row unchanged (no"
           " cross-window contamination)"
           % (after["total"]))

    # -- AC-CCU8 hygiene and registration -------------------------
    with open(os.path.join(BASE, "freetrial.py"), "rb") as h3:
        src_bytes = h3.read()
    ok8 = all(b < 128 for b in src_bytes)
    imports = [ln.strip() for ln in
               src_bytes.decode("ascii").splitlines()
               if ln.strip().startswith("import ")]
    ok8 = ok8 and not any(
        lib in ln for ln in imports for lib in NET_LIBS)
    with open(os.path.join(BASE, "config.json"), "rb") as h4:
        ok8 = ok8 and (hashlib.sha256(
            h4.read()).hexdigest() == cfg_sha)
    reg_path = os.path.join(os.path.dirname(BASE),
                            "reconcile_all.py")
    with open(reg_path, "r", encoding="utf-8") as h5:
        reg_text = h5.read()
    ok8 = (ok8
           and "ledger-freetrial-capusage" in reg_text
           and "test_freetrial_capusage.py" in reg_text)
    ok8 = ok8 and (len(RESULTS) + 1 == EXPECTED)
    record("AC-CCU8", ok8,
           "freetrial.py pure ASCII; import lines network-free"
           " (%d imports); shipped config.json sha256 stable;"
           " SUITES registration row present; criteria drift"
           " self-check %d+1==%d"
           % (len(imports), len(RESULTS), EXPECTED))

    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d exit=%d"
          % ("PASS" if fail == 0 else "FAIL",
             len(RESULTS) - fail, len(RESULTS),
             0 if fail == 0 else 1), flush=True)
    ft.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
