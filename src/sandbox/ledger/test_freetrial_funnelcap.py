"""Acceptance suite for the free-trial conversion-funnel
board read cap (BigDomain R1880 tech-queue row; seed =
freetrial.py conversion_funnel_board window R1793 / R1874).
Asserts the pre-registered criteria AC-CVR8..AC-CVR14 from
the R1880 tech.md claim line (criteria were registered
before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL.

Family law = the R1729/R1840/R1849 read-hat line: limit=0 -
the sole default sentinel - keeps the full current behavior
byte-identical; a positive int caps the board to the tail
window (mirror clause ORDER BY plan_key DESC LIMIT N
reversed back to ascending); the overflow block adds exactly
four keys {limit, total, returned, truncated} with total =
the full registry row count (this axis is registry-dense, a
window never removes rows, total stays window-independent -
never the post-truncation count); a malformed limit fails
closed E_FT_BAD_LIMIT before the window gate; the sole
sentinel is 0 (a non-zero positive int caps, anything else
refuses).

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_freetrial_funnelcap.py
"""

import datetime
import inspect
import json
import os
import sqlite3
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

ROW_KEYS = {"plan_id", "plan_key", "title", "ai_label",
            "granted", "converted", "active_trials",
            "conversion_rate"}

BAD_LIMITS = [-1, True, "2", 2.5, None]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _month_now():
    return datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m")


def _next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return "%04d-%02d" % (y, m)


def main():
    cur_m = _month_now()
    fut = _next_month(cur_m)

    tmp = tempfile.mkdtemp(prefix="freetrial-funnelcap-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ft = T.FreeTrialFace(dk, DISCLAIMER)
    ftconn = sqlite3.connect(ft.db_path)

    def _counts():
        return tuple(
            ftconn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("trial_plans", "trial_grants",
                      "trial_calls", "trial_conversions"))

    # -- real-API world: four registered plans, ascending keys --
    dk.issue_key("usr:alice", "alice-key", 100,
                 ("backtest", "visualize"), False)
    pa = ft.register_trial_plan("alpha-starter",
                                "Alpha Starter Tier", 3, False)
    pm = ft.register_trial_plan("mid-lab",
                                "Mid Lab Tier", 4, False)
    pt = ft.register_trial_plan("tango-tier",
                                "Tango Tier", 5, False)
    pz = ft.register_trial_plan("zulu-zero",
                                "Zulu Zero Tier", 5, True)
    ft.grant_trial("usr:alice", pa["plan_id"])
    ft.trial_call("usr:alice", pa["plan_id"], "backtest",
                  "a1", "eng-a1")
    keys_asc = ["alpha-starter", "mid-lab", "tango-tier",
                "zulu-zero"]

    # -- AC-CVR8 default zero drift, additive window ----
    d1 = ft.conversion_funnel_board()
    d2 = ft.conversion_funnel_board(None, 0)
    ok8_same = (json.dumps(d1, sort_keys=True)
                == json.dumps(d2, sort_keys=True))
    ok8_keys = set(d1.keys()) == {"conversion_funnel_board",
                                  "disclaimer"}
    w0 = ft.conversion_funnel_board(cur_m, 0)
    ok8_win0 = (set(w0.keys())
                == {"conversion_funnel_board", "window",
                    "disclaimer"})
    ok8_rows = ([r["plan_key"] for r in
                 d1["conversion_funnel_board"]] == keys_asc
                and all(set(r.keys()) == ROW_KEYS
                        for r in
                        d1["conversion_funnel_board"]))
    record("AC-CVR8", ok8_same and ok8_keys and ok8_win0
           and ok8_rows,
           "default call == explicit (None, 0) byte-identical"
           "=%s; default envelope keys exact=%s; windowed"
           " limit=0 read adds window key only (zero overflow"
           " keys)=%s; four-plan ascending axis with 8-key rows"
           "=%s" % (ok8_same, ok8_keys, ok8_win0, ok8_rows))

    # -- AC-CVR9 malformed limit fail-closed + gate order ----
    before9 = _counts()
    rejects = 0
    for bad in BAD_LIMITS:
        try:
            ft.conversion_funnel_board(None, bad)
        except T.TrialError as exc:
            if exc.code == T.E_FT_BAD_LIMIT:
                rejects += 1
    after9 = _counts()
    ok9_rejects = (rejects == len(BAD_LIMITS)
                   and before9 == after9)
    gate_code = None
    try:
        ft.conversion_funnel_board("2026-99", -1)
    except T.TrialError as exc:
        gate_code = exc.code
    win_code = None
    try:
        ft.conversion_funnel_board("2026-99", 0)
    except T.TrialError as exc:
        win_code = exc.code
    ok9 = (ok9_rejects and gate_code == T.E_FT_BAD_LIMIT
           and win_code == T.E_FT_BAD_ARGS)
    record("AC-CVR9", ok9,
           "%d/%d bad forms rejected E_FT_BAD_LIMIT (None is"
           " not the sentinel - 0 is); four-table counts flat"
           " %s -> %s; double-bad call yields limit gate code"
           " %s; bad-window-only still yields %s"
           % (rejects, len(BAD_LIMITS), before9, after9,
              gate_code, win_code))

    # -- AC-CVR10 cap above total: full board --------------
    r10 = ft.conversion_funnel_board(None, 50)
    rows10 = r10["conversion_funnel_board"]
    ok10_keys = (set(r10.keys())
                 == {"conversion_funnel_board", "disclaimer",
                     "limit", "total", "returned", "truncated"})
    ok10_vals = (r10["limit"] == 50 and r10["total"] == 4
                 and r10["returned"] == 4
                 and r10["truncated"] is False)
    ok10_rows = ([r["plan_key"] for r in rows10] == keys_asc
                 and json.dumps(rows10, sort_keys=True)
                 == json.dumps(
                     d1["conversion_funnel_board"],
                     sort_keys=True))
    record("AC-CVR10", ok10_keys and ok10_vals and ok10_rows,
           "limit=50 over 4 plans: envelope = base + exactly"
           " four overflow keys=%s; limit=50 total=4"
           " returned=4 truncated=False=%s; rows == default"
           " ascending board byte-identical=%s"
           % (ok10_keys, ok10_vals, ok10_rows))

    # -- AC-CVR11 truncated tail window + mirror SQL ------
    r11 = ft.conversion_funnel_board(None, 2)
    rows11 = r11["conversion_funnel_board"]
    ro = sqlite3.connect(
        "file:%s?mode=ro" % ft.db_path.replace("\\", "/"),
        uri=True)
    mirror = [r[0] for r in ro.execute(
        "SELECT plan_key FROM trial_plans"
        " ORDER BY plan_key DESC LIMIT 2").fetchall()]
    mirror.reverse()
    ro.close()
    ok11_vals = (r11["limit"] == 2 and r11["total"] == 4
                 and r11["returned"] == 2
                 and r11["truncated"] is True)
    ok11_rows = ([r["plan_key"] for r in rows11]
                 == keys_asc[-2:]
                 and json.dumps(rows11, sort_keys=True)
                 == json.dumps(
                     d1["conversion_funnel_board"][-2:],
                     sort_keys=True)
                 and all(set(r.keys()) == ROW_KEYS
                         for r in rows11))
    ok11_mirror = mirror == keys_asc[-2:]
    record("AC-CVR11", ok11_vals and ok11_rows and ok11_mirror,
           "limit=2: returned=2 total=4 truncated=True=%s;"
           " rows == default tail-2 slice byte-identical"
           " (8-key rows unchanged)=%s; mirror SQL (ro"
           " connection ORDER BY plan_key DESC LIMIT 2"
           " reversed) == %s =%s"
           % (ok11_vals, ok11_rows, mirror, ok11_mirror))

    # -- AC-CVR12 boundary states --------------------------
    r12_eq = ft.conversion_funnel_board(None, 4)
    ok12_eq = (r12_eq["total"] == 4 and r12_eq["returned"] == 4
               and r12_eq["truncated"] is False)
    r12_one = ft.conversion_funnel_board(None, 1)
    ok12_one = (r12_one["returned"] == 1
                and [r["plan_key"]
                     for r in r12_one["conversion_funnel_board"]]
                == ["zulu-zero"])
    tmp2 = tempfile.mkdtemp(prefix="freetrial-funnelcap2-")
    db2 = os.path.join(tmp2, "ledger2.db")
    led2 = L.Ledger(db2, cfg)
    metered2 = M.MeteredFace(led2)
    dk2 = D.DevKeyFace(metered2, DISCLAIMER)
    ft2 = T.FreeTrialFace(dk2, DISCLAIMER)
    r12_empty = ft2.conversion_funnel_board(None, 3)
    ok12_empty = (r12_empty["conversion_funnel_board"] == []
                  and r12_empty["total"] == 0
                  and r12_empty["returned"] == 0
                  and r12_empty["truncated"] is False
                  and set(r12_empty.keys())
                  == {"conversion_funnel_board", "disclaimer",
                      "limit", "total", "returned",
                      "truncated"})
    ft2.close()
    dk2.close()
    metered2.close()
    led2.close()
    record("AC-CVR12", ok12_eq and ok12_one and ok12_empty,
           "limit==total (4/4): full board truncated=False=%s;"
           " limit=1 single tail row zulu-zero=%s; zero-plan"
           " world limit=3: empty board with all four overflow"
           " keys carried (honest empty capped read)=%s"
           % (ok12_eq, ok12_one, ok12_empty))

    # -- AC-CVR13 window x cap orthogonal -------------------
    r13 = ft.conversion_funnel_board(cur_m, 2)
    ok13_keys = (set(r13.keys())
                 == {"conversion_funnel_board", "window",
                     "disclaimer", "limit", "total",
                     "returned", "truncated"})
    wb = ft.conversion_funnel_board(cur_m, 0)
    ok13_rows = (json.dumps(r13["conversion_funnel_board"],
                            sort_keys=True)
                 == json.dumps(
                     wb["conversion_funnel_board"][-2:],
                     sort_keys=True))
    r13f = ft.conversion_funnel_board(fut, 2)
    ok13_fut = (r13f["total"] == 4
                and r13f["returned"] == 2
                and all(r["granted"] == 0 and r["converted"] == 0
                        for r in
                        r13f["conversion_funnel_board"]))
    ok13_tot = (r13["total"] == 4 and r13["window"] == cur_m
                and r13["truncated"] is True)
    record("AC-CVR13", ok13_keys and ok13_rows
           and ok13_tot and ok13_fut,
           "(window, limit) union envelope = 7 keys=%s; capped"
           " windowed rows == windowed board tail-2 slice=%s;"
           " total stays the registry count 4 across windows"
           " (dense axis verdict)=%s; future-window capped read"
           " returns honest zero rows under the cap=%s"
           % (ok13_keys, ok13_rows, ok13_tot, ok13_fut))

    # -- AC-CVR14 pure-read + determinism + hygiene ---------
    before14 = _counts()
    for args in ((None, 0), (None, 2), (None, 50),
                 (cur_m, 2), (fut, 3)):
        ft.conversion_funnel_board(*args)
    after14 = _counts()
    method_src = inspect.getsource(
        T.FreeTrialFace.conversion_funnel_board)
    ok14_pure = (before14 == after14
                 and "INSERT" not in method_src
                 and "UPDATE" not in method_src
                 and "DELETE" not in method_src)
    j1 = json.dumps(ft.conversion_funnel_board(cur_m, 2),
                    sort_keys=True)
    j2 = json.dumps(ft.conversion_funnel_board(cur_m, 2),
                    sort_keys=True)
    ok14_det = j1 == j2
    with open(os.path.join(BASE, "freetrial.py"),
              encoding="utf-8") as handle:
        src = handle.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [ln for ln in src.splitlines()
                    if (ln.startswith("import ")
                        or ln.startswith("from "))]
    net_imports = [ln for ln in import_lines
                   if any(w in ln for w in
                          ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(
            os.path.dirname(BASE), "reconcile_all.py"),
            encoding="utf-8") as handle:
        runner_src = handle.read()
    ok14 = (ok14_pure and ok14_det
            and non_ascii == 0 and not net_imports
            and "random" not in src
            and cfg_after == cfg_bytes
            and "ledger-freetrial-funnelcap" in runner_src
            and len(RESULTS) + 1 == EXPECTED)
    record("AC-CVR14", ok14,
           "four-table counts flat %s; method source carries"
           " zero data-changing statements (inspect)=%s;"
           " capped windowed double-call byte-identical=%s;"
           " module pure ASCII (%d non-ascii); true import"
           " lines carry zero network libs (%d); zero dice;"
           " config.json byte-stable; SUITES row"
           " 'ledger-freetrial-funnelcap' registered; criteria"
           " drift self-check %d/%d"
           % (before14 == after14, ok14_pure, ok14_det,
              non_ascii, len(net_imports), len(RESULTS),
              EXPECTED))

    ftconn.close()
    ft.close()
    dk.close()
    metered.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
