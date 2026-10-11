"""Acceptance suite for the free-trial cap_usage_board read
cap (BigDomain R1849 tech-queue claim row; seed = the
freetrial.py cap_usage_board R1842 face plus the R1840
eventtickets boardlimit same-type precedent). Asserts the
pre-registered criteria AC-CUL1..AC-CUL7 from the R1849
tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Family law (the R1729/R1804/R1840 read-hat line, verdicts
registered in the claim row): limit=0 - the sole default
sentinel - keeps the full current behavior byte-identical; a
positive int caps to the tail window of the (dev_account,
plan_id) ascending board; the overflow block reuses the
existing "total" key as the full grant-row-set count and
adds exactly three keys {limit, returned, truncated}; a
malformed limit fails closed with the dedicated
E_FT_BAD_LIMIT code BEFORE the window gate (double-bad
gate-order law); window filtering runs before the cap
(orthogonal combination).

Fixture world: five current-month grants (alice x2 plans,
bob, carol, dave) plus one older-month history grant row
for usr:hist-g injected straight into trial_grants (the
R1730 family direct-write convention) - six grant rows
total on the default board, five in the current-month
window, exactly one in the older-month window.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_caplimit.py
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
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: the developer free"
              " tier is a trial allowance, not investment advice")

BAD_LIMITS = [-1, True, "2", 2.5, None]

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
    m1 = _prev_month(cur_m)          # the history grant month
    fut = _next_month(cur_m)         # the future month

    tmp = tempfile.mkdtemp(prefix="freetrial-caplimit-")
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

    # -- zero-grant world first: honest empty capped read -------
    zero = ft.cap_usage_board(limit=3)
    ok_zero = (zero["cap_usage_board"] == []
               and zero["total"] == 0
               and zero["limit"] == 3
               and zero["returned"] == 0
               and zero["truncated"] is False
               and set(zero.keys()) ==
               {"cap_usage_board", "total", "disclaimer",
                "limit", "returned", "truncated"}
               and zero["disclaimer"] == DISCLAIMER)

    # -- build the six-grant world ------------------------------
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
    ft.trial_call("usr:bob", pb["plan_id"], "backtest",
                  "b1", "eng-y")

    # history fixture grant row (direct write, R1730 convention)
    ftconn.execute(
        "INSERT INTO trial_grants (plan_id, dev_account,"
        " granted_utc) VALUES (?,?,?)",
        (pa["plan_id"], "usr:hist-g", _stamp(m1, 2)))
    ftconn.commit()

    counts_before = _counts()

    ROW_KEYS = {"dev_account", "plan_id", "plan_key", "title",
                "trial_cap", "calls_used", "remaining",
                "granted_utc", "ai_label"}

    # -- AC-CUL1 default sentinel keeps current behavior -------
    full = ft.cap_usage_board()
    capped = ft.cap_usage_board(limit=2)
    ok1 = (ok_zero
           and set(full.keys()) ==
           {"cap_usage_board", "total", "disclaimer"}
           and full["total"] == len(full["cap_usage_board"]) == 6
           and set(capped.keys()) ==
           {"cap_usage_board", "total", "disclaimer",
            "limit", "returned", "truncated"}
           and capped["limit"] == 2
           and capped["returned"] == 2
           and capped["truncated"] is True
           and capped["total"] == 6)
    # key-set union law: window + cap both present
    wc = ft.cap_usage_board(cur_m, limit=1)
    ok1 = (ok1
           and set(wc.keys()) ==
           {"cap_usage_board", "total", "disclaimer",
            "window", "limit", "returned", "truncated"}
           and wc["window"] == cur_m)
    # explicit-window default-limit read keeps the R1842 shape
    wplain = ft.cap_usage_board(cur_m)
    ok1 = (ok1
           and set(wplain.keys()) ==
           {"cap_usage_board", "total", "disclaimer", "window"})
    # double-call determinism on the default face
    ok1 = ok1 and (
        json.dumps(ft.cap_usage_board(), sort_keys=True) ==
        json.dumps(ft.cap_usage_board(), sort_keys=True))
    with open(os.path.join(BASE, "config.json"), "rb") as h2:
        ok1 = ok1 and (h2.read() == cfg_bytes)
    record("AC-CUL1", ok1,
           "zero-grant capped read honest empty (keys exact,"
           " returned 0, truncated False); limit=0 default"
           " envelope byte-shape stable {cap_usage_board,"
           " total, disclaimer} with total==6; limit=2 envelope"
           " adds exactly {limit, returned, truncated} (three"
           " additive keys, total reused as full count 6);"
           " window+cap key union exact; shipped config bytes"
           " stable")

    # -- AC-CUL2 malformed limits fail closed E_FT_BAD_LIMIT ---
    ok2 = True
    trace2 = []
    for form in BAD_LIMITS:
        try:
            ft.cap_usage_board(limit=form)
            ok2 = False
            trace2.append("accepted:%r" % (form,))
        except T.TrialError as exc:
            if exc.code != T.E_FT_BAD_LIMIT:
                ok2 = False
                trace2.append("wrongcode:%r->%s"
                              % (form, exc.code))
    ok2 = ok2 and (_counts() == counts_before)
    # sole default sentinel: 0 accepted on the limit slot
    # (keyword form; a positional 0 binds the window slot and
    # correctly refuses E_FT_BAD_ARGS as a malformed window -
    # first-run call-binding bug fixed here per the R1776/R1845
    # suite-side convention, noted)
    try:
        ft.cap_usage_board(limit=0)
    except T.TrialError:
        ok2 = False
        trace2.append("zero-rejected")
    # double-bad gate order: bad limit fires before bad window
    dbl = None
    try:
        ft.cap_usage_board("2026-13", limit=-1)
        ok2 = False
        trace2.append("double-bad-accepted")
    except T.TrialError as exc:
        dbl = exc.code
    ok2 = ok2 and (dbl == T.E_FT_BAD_LIMIT)
    # bad-window-only world keeps the family code (zero drift)
    wonly = None
    try:
        ft.cap_usage_board("2026-13")
        ok2 = False
        trace2.append("bad-window-accepted")
    except T.TrialError as exc:
        wonly = exc.code
    ok2 = ok2 and (wonly == T.E_FT_BAD_ARGS)
    record("AC-CUL2", ok2,
           "%d bad limit forms rejected E_FT_BAD_LIMIT %s;"
           " four-table counts unchanged %s; sole sentinel 0"
           " accepted; double-bad (bad limit + bad window)"
           " fires E_FT_BAD_LIMIT first (%s); bad-window-only"
           " keeps E_FT_BAD_ARGS (%s)"
           % (len(BAD_LIMITS), trace2[:3], counts_before,
              dbl, wonly))

    # -- AC-CUL3 tail-window truncation semantics ---------------
    env3 = ft.cap_usage_board(limit=2)
    rows3 = env3["cap_usage_board"]
    full_rows = full["cap_usage_board"]
    ok3 = (env3["total"] == 6
           and env3["returned"] == len(rows3) == 2
           and env3["truncated"] is True
           and json.dumps(rows3, sort_keys=True) ==
           json.dumps(full_rows[-2:], sort_keys=True)
           and all(set(r.keys()) == ROW_KEYS for r in rows3))
    # mirror SQL third path: DESC/DESC LIMIT reversed
    mir = ftconn.execute(
        "SELECT g.dev_account, g.plan_id FROM trial_grants g"
        " JOIN trial_plans p ON p.plan_id = g.plan_id"
        " ORDER BY g.dev_account DESC, g.plan_id DESC"
        " LIMIT 2").fetchall()
    mirror_pairs = [(str(a), int(b)) for a, b in reversed(mir)]
    ok3 = (ok3
           and mirror_pairs ==
           [(r["dev_account"], r["plan_id"]) for r in rows3]
           and [(r["dev_account"], r["plan_id"])
                for r in rows3] ==
           [(r["dev_account"], r["plan_id"])
            for r in full_rows[-2:]])
    record("AC-CUL3", ok3,
           "limit=2 on 6 grants: returned 2, truncated True,"
           " total 6 (full count, never post-truncation);"
           " rows == default read tail-2 byte-identical"
           " (in-board relative order unchanged); mirror SQL"
           " ORDER BY dev DESC, plan DESC LIMIT 2 reversed =="
           " product rows %s; row field set exact 9 keys"
           % (mirror_pairs,))

    # -- AC-CUL4 boundary states ---------------------------------
    e_eq = ft.cap_usage_board(limit=6)
    e_over = ft.cap_usage_board(limit=50)
    e_one = ft.cap_usage_board(limit=1)
    ok4 = (e_eq["truncated"] is False
           and e_eq["returned"] == 6
           and len(e_eq["cap_usage_board"]) == 6
           and e_over["truncated"] is False
           and e_over["returned"] == 6
           and e_one["returned"] == 1
           and e_one["truncated"] is True
           and json.dumps(e_one["cap_usage_board"],
                          sort_keys=True) ==
           json.dumps(full_rows[-1:], sort_keys=True))
    record("AC-CUL4", ok4,
           "limit==total (6/6): full board truncated False;"
           " limit>total (50 over 6): full board truncated"
           " False; limit=1: single tail row; zero-grant"
           " world limit=3: rows==[] returned 0 total 0"
           " truncated False with all keys present (AC-CUL1"
           " anchor)")

    # -- AC-CUL5 window x cap orthogonal combination ------------
    c_cur = ft.cap_usage_board(cur_m, limit=2)
    c_m1 = ft.cap_usage_board(m1, limit=1)
    c_fut = ft.cap_usage_board(fut, limit=4)
    w_full = ft.cap_usage_board(cur_m)
    ok5 = (c_cur["window"] == cur_m
           and c_cur["total"] == 5
           and c_cur["returned"] == 2
           and c_cur["truncated"] is True
           and json.dumps(c_cur["cap_usage_board"],
                          sort_keys=True) ==
           json.dumps(w_full["cap_usage_board"][-2:],
                      sort_keys=True)
           and c_m1["total"] == 1
           and c_m1["returned"] == 1
           and c_m1["truncated"] is False
           and c_m1["cap_usage_board"][0]["dev_account"] ==
           "usr:hist-g"
           and c_fut["total"] == 0
           and c_fut["returned"] == 0
           and c_fut["truncated"] is False
           and c_fut["cap_usage_board"] == [])
    # windowed mirror SQL third path for the capped window read
    mir_w = ftconn.execute(
        "SELECT g.dev_account, g.plan_id FROM trial_grants g"
        " JOIN trial_plans p ON p.plan_id = g.plan_id"
        " WHERE substr(g.granted_utc, 1, 7) = ?"
        " ORDER BY g.dev_account DESC, g.plan_id DESC"
        " LIMIT 2", (cur_m,)).fetchall()
    ok5 = (ok5
           and [(str(a), int(b))
                for a, b in reversed(mir_w)] ==
           [(r["dev_account"], r["plan_id"])
            for r in c_cur["cap_usage_board"]])
    record("AC-CUL5", ok5,
           "(cur,2): total==5 current-month grants (hist-g"
           " m1 row excluded), rows == windowed full read"
           " tail-2, truncated True, mirror SQL windowed"
           " third path matches; (m1,1): total==1 single"
           " hist-g row truncated False; (fut,4): total==0"
           " rows==[] truncated False - window filter runs"
           " before the cap, overflow total is the"
           " window-filtered count; window key coexists in"
           " every capped read")

    # -- AC-CUL6 pure-read law -----------------------------------
    src = inspect.getsource(T.FreeTrialFace.cap_usage_board)
    banned = ("INSERT INTO", "REPLACE INTO",
              "UPDATE ", "DELETE FROM")
    ok6 = not any(b in src for b in banned)
    ok6 = ok6 and (_counts() == counts_before)
    ok6 = ok6 and (
        json.dumps(ft.cap_usage_board(), sort_keys=True) ==
        json.dumps(ft.cap_usage_board(), sort_keys=True))
    ok6 = ok6 and (
        json.dumps(ft.cap_usage_board()) ==
        json.dumps(ft.cap_usage_board()))
    ok6 = ok6 and (
        json.dumps(ft.cap_usage_board(limit=2),
                  sort_keys=True) ==
        json.dumps(ft.cap_usage_board(limit=2),
                   sort_keys=True))
    ok6 = ok6 and (
        json.dumps(ft.cap_usage_board(cur_m, limit=2),
                   sort_keys=True) ==
        json.dumps(ft.cap_usage_board(cur_m, limit=2),
                   sort_keys=True))
    record("AC-CUL6", ok6,
           "method source free of data-changing statements;"
           " four-table counts unchanged %s; double-call dumps"
           " byte-identical on default, capped and"
           " window-capped reads (sorted and insertion order)"
           % (counts_before,))

    # -- AC-CUL7 hygiene and registration -----------------------
    with open(os.path.join(BASE, "freetrial.py"), "rb") as h3:
        src_bytes = h3.read()
    ok7 = all(b < 128 for b in src_bytes)
    imports = [ln.strip() for ln in
               src_bytes.decode("ascii").splitlines()
               if ln.strip().startswith("import ")]
    ok7 = ok7 and not any(
        lib in ln for ln in imports for lib in NET_LIBS)
    with open(os.path.join(BASE, "config.json"), "rb") as h4:
        ok7 = ok7 and (hashlib.sha256(
            h4.read()).hexdigest() == cfg_sha)
    reg_path = os.path.join(os.path.dirname(BASE),
                            "reconcile_all.py")
    with open(reg_path, "r", encoding="utf-8") as h5:
        reg_text = h5.read()
    ok7 = (ok7
           and "ledger-freetrial-caplimit" in reg_text
           and "test_freetrial_caplimit.py" in reg_text)
    ok7 = ok7 and (len(RESULTS) + 1 == EXPECTED)
    record("AC-CUL7", ok7,
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
