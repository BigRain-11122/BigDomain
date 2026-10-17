"""Acceptance suite: stats_board month-window zero-registry
boundary world cross-restart persistence example window
(BigDomain R2017; canon = the R2016-reseed FIFO head, the
statsmonth family boundary persist successor). The
month-window face (R2015) slices the per-showcase counts by
the exhibit_events record time over a dense registry axis; the
zero-registry boundary world (R2010 AC-SSZB judgment) keeps the
ledger domain populated while the showcase registration axis
stays empty. This suite pins the seven-form month-window read
family on that boundary world across a full-stack instance
restart (persist family judgment R1889/R1900/R1902): the empty
envelopes stay byte-identical, the gates still fire before any
read on the empty world, and the post-restart first
registration plus first current-month place continue every
window form with zero phantom rows and honest window splits.

Asserts the pre-registered criteria AC-SSMZ1..AC-SSMZ7 from
the R2017 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim
rulings (registered at claim time):
1. world = the R2010 boundary shape: four accounts, four
   certificates, zero showcases, zero events - the boundary
   isolates the registry axis, not the whole stack; no frozen
   clock is needed because the board rows carry no timestamps.
2. comparison face = the R2016 seven-form window read family
   {full, cap2, wcur, wcap2, wprev, whist, wzero} with cur
   (now), prev (now-45d), hist (prev-35d) mutually distinct.
3. restart carrier = the full stack: ShowcaseFace close ->
   Ledger close, then a fresh Ledger (same db_path, same cfg
   bytes) + stateless SecGate + ShowcaseFace (same sh_path)
   reopen - the ledger dock reconnect is proven too (R1992).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline (the unicode look-alike
probe is written as escape sequences).

Usage: python test_showcase_statsmonthboundarypersist.py
"""

import datetime
import hashlib
import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                     # noqa: E402 (P-47-2b core)
import collectibles as C               # noqa: E402 (owner face)
import showcase as S                   # noqa: E402 (face under test)
from sec_gate import SecGate           # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase stats"
              " month-window board is a display feature, not"
              " investment advice")

FULL_KEYS = {"showcase_stats_board", "disclaimer"}
CAP_KEYS = {"showcase_stats_board", "disclaimer", "limit",
            "total", "returned", "truncated"}
WIN_KEYS = {"showcase_stats_board", "disclaimer", "window"}
WINCAP_KEYS = CAP_KEYS | {"window"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places",
            "retracts", "displayed_now"}

PRODUCT_FILES = [
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def win_family(sh, cur, prev, hist):
    """The seven-form window read family, all serialized."""
    return {
        "full": dumps(sh.stats_board()),
        "cap2": dumps(sh.stats_board(2)),
        "wcur": dumps(sh.stats_board(window=cur)),
        "wcap2": dumps(sh.stats_board(2, cur)),
        "wprev": dumps(sh.stats_board(window=prev)),
        "whist": dumps(sh.stats_board(window=hist)),
        "wzero": dumps(sh.stats_board(window="2099-01")),
    }


def rowmap(board):
    return {r["showcase_id"]: r
            for r in board["showcase_stats_board"]}


def sql_counts_window(sh_path, window):
    uri = "file:" + sh_path.replace("\\", "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    counts = {}
    for sid, action, n in conn.execute(
            "SELECT showcase_id, action, COUNT(*) FROM"
            " exhibit_events WHERE substr(acted_utc, 1, 7) = ?"
            " GROUP BY showcase_id, action",
            (window,)).fetchall():
        slot = counts.setdefault(str(sid),
                                 {"place": 0, "retract": 0})
        slot[str(action)] = int(n)
    conn.close()
    return counts


def raise_code(fn):
    try:
        fn()
    except S.ShowcaseError as exc:
        return exc.code
    except Exception:                                # noqa: BLE001
        return "WRONG-EXC"
    return "NO-RAISE"


def table_counts(shconn, ledconn):
    return {"showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events")
                .fetchone()[0]),
            "collectibles": int(ledconn.execute(
                "SELECT COUNT(*) FROM collectibles")
                .fetchone()[0]),
            "ledger_tx": int(ledconn.execute(
                "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])}


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    now = datetime.datetime.now(datetime.timezone.utc)
    cur = now.strftime("%Y-%m")
    prev_dt = now - datetime.timedelta(days=45)
    prev = prev_dt.strftime("%Y-%m")
    hist_dt = prev_dt - datetime.timedelta(days=35)
    hist = hist_dt.strftime("%Y-%m")

    tmp = tempfile.mkdtemp(prefix="showcase-statsmonthboundary-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    hyg = {}
    led = sh = led2 = sh2 = led3 = sh3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        # boundary world (R2010 shape): ledger domain populated,
        # showcase registration axis empty
        for who in ("ada", "bob", "carol", "dana"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cl = {}
        for who, ev, item in (
                ("ada", "evt-lamp", "lamp-cert"),
                ("bob", "evt-bell", "bell-cert"),
                ("carol", "evt-harp", "harp-cert"),
                ("dana", "evt-arch", "arch-cert")):
            cl[item] = cf.issue_certificate(
                "usr:" + who, ev, item)["cl_id"]
        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-SSMZ1 zero-registry control anchor --------------
        fam = win_family(sh, cur, prev, hist)
        full_env = json.loads(fam["full"])
        cap_env = json.loads(fam["cap2"])
        wcur = json.loads(fam["wcur"])
        wcap_env = json.loads(fam["wcap2"])
        wprev = json.loads(fam["wprev"])
        whist = json.loads(fam["whist"])
        wzero = json.loads(fam["wzero"])
        ok_env = (set(full_env.keys()) == FULL_KEYS
                  and full_env["showcase_stats_board"] == []
                  and set(cap_env.keys()) == CAP_KEYS
                  and cap_env["showcase_stats_board"] == []
                  and cap_env["limit"] == 2
                  and cap_env["total"] == 0
                  and cap_env["returned"] == 0
                  and cap_env["truncated"] is False
                  and set(wcur.keys()) == WIN_KEYS
                  and wcur["window"] == cur
                  and wcur["showcase_stats_board"] == []
                  and set(wcap_env.keys()) == WINCAP_KEYS
                  and wcap_env["window"] == cur
                  and wcap_env["total"] == 0
                  and wcap_env["showcase_stats_board"] == []
                  and set(wprev.keys()) == WIN_KEYS
                  and wprev["window"] == prev
                  and wprev["showcase_stats_board"] == []
                  and set(whist.keys()) == WIN_KEYS
                  and whist["window"] == hist
                  and whist["showcase_stats_board"] == []
                  and set(wzero.keys()) == WIN_KEYS
                  and wzero["window"] == "2099-01"
                  and wzero["showcase_stats_board"] == [])
        fam_b = win_family(sh, cur, prev, hist)
        record("AC-SSMZ1", ok_env and fam == fam_b,
               "zero-registry world: seven-form family all"
               " honest-empty - full keys=%s rows==[]; cap2"
               " keys=%s total=0 returned=0 truncated=False=%s;"
               " wcur/wprev/whist/wzero 3-key envelopes with"
               " window echoes {%s,%s,%s,2099-01} rows==[]=%s;"
               " wcap2 keys=%s window echo=%s honest-empty=%s;"
               " family double-read byte-identical=%s"
               % (sorted(full_env.keys()),
                  sorted(cap_env.keys()),
                  cap_env["truncated"] is False
                  and cap_env["total"] == 0,
                  wcur["window"], wprev["window"],
                  whist["window"],
                  wprev["showcase_stats_board"] == []
                  and whist["showcase_stats_board"] == [],
                  sorted(wcap_env.keys()),
                  wcap_env["window"] == cur,
                  wcap_env["showcase_stats_board"] == [],
                  fam == fam_b))

        # -- AC-SSMZ2 gates fire before any read on empty world -
        bad_windows = [
            ("int", 202610), ("bool", True),
            ("month-1-digit", "2026-1"),
            ("month-13", "2026-13"), ("month-00", "2026-00"),
            ("slash-sep", "2026/10"), ("no-sep", "202610"),
            ("trailing-space", "2026-10 "),
            ("unicode-digits",
             "\uff12\uff10\uff12\uff16" + "-" + "\uff11\uff10")]
        bad_limits = (-1, True, "2", 2.5, None)
        c0 = table_counts(shconn, ledconn)
        win_codes = [(lbl, raise_code(
            lambda f=form: sh.stats_board(window=f)))
            for lbl, form in bad_windows]
        lim_codes = [raise_code(
            lambda b=bad: sh.stats_board(b))
            for bad in bad_limits]
        order_code = raise_code(
            lambda: sh.stats_board(limit=-1, window=123))
        c1 = table_counts(shconn, ledconn)
        ok2 = (all(code == "E_SH_BAD_WINDOW"
                   for _lbl, code in win_codes)
               and len(win_codes) == 9
               and lim_codes == [S.E_SH_BAD_LIMIT] * 5
               and order_code == "E_SH_BAD_LIMIT"
               and c0 == c1)
        record("AC-SSMZ2", ok2,
               "empty world still gates first: %d malformed"
               " windows all E_SH_BAD_WINDOW (%s); %d bad limits"
               " all E_SH_BAD_LIMIT; gate order probe bad limit"
               " + bad window -> E_SH_BAD_LIMIT fires first=%s;"
               " probe batch leaves counts unchanged %s == %s"
               " (gates independent of the empty data face)"
               % (len(win_codes), [c for c, _ in win_codes],
                  len(lim_codes),
                  order_code == "E_SH_BAD_LIMIT", c0, c1))

        # -- AC-SSMZ3 cross-restart byte identity ---------------
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam2 = win_family(sh2, cur, prev, hist)
        double2 = win_family(sh2, cur, prev, hist) == fam2
        record("AC-SSMZ3", fam2 == fam and double2,
               "full-stack close (sh -> led) then rebuild on same"
               " paths + same cfg bytes: seven-form window family"
               " byte-identical=%s same-param double-read"
               " self-stable=%s (derived face zero in-memory"
               " drift across restart, boundary state included)"
               % (fam2 == fam, double2))

        # -- AC-SSMZ4 post-restart first registration -----------
        sh2.register_showcase("sh-first", "First Window", 3, True)
        full4 = sh2.stats_board()
        rows4 = full4["showcase_stats_board"]
        cap4 = sh2.stats_board(2)
        wcur4 = sh2.stats_board(window=cur)
        wprev4 = sh2.stats_board(window=prev)
        whist4 = sh2.stats_board(window=hist)
        wzero4 = sh2.stats_board(window="2099-01")
        wcap4 = sh2.stats_board(2, cur)
        row4 = rows4[0] if rows4 else {}
        zero_row = {"places": 0, "retracts": 0,
                    "displayed_now": 0}
        win_rows_frozen = all(
            len(b["showcase_stats_board"]) == 1
            and {k: b["showcase_stats_board"][0][k]
                 for k in zero_row} == zero_row
            for b in (wcur4, wprev4, whist4, wzero4))
        ok4 = (len(rows4) == 1
               and set(row4.keys()) == ROW_KEYS
               and row4.get("showcase_id") == "sh-first"
               and row4.get("ai_label") == 1
               and {k: row4.get(k) for k in zero_row}
               == zero_row
               and cap4["total"] == 1 and cap4["returned"] == 1
               and cap4["truncated"] is False
               and cap4["showcase_stats_board"] == rows4
               and win_rows_frozen
               and wcur4["window"] == cur
               and wprev4["window"] == prev
               and whist4["window"] == hist
               and wzero4["window"] == "2099-01"
               and wcap4["window"] == cur
               and wcap4["total"] == 1
               and wcap4["showcase_stats_board"]
               == wcur4["showcase_stats_board"]
               and dumps(full4) != fam2["full"]
               and dumps(wcur4) != fam2["wcur"]
               and dumps(wzero4) != fam2["wzero"])
        record("AC-SSMZ4", ok4,
               "post-restart first registration: full face one"
               " honest-zero row {%s} ai_label=1=%s; cap(2) total"
               " 0->1 returned=1 truncated=False rows==full=%s;"
               " wcur/wprev/whist/wzero all carry the same dense"
               " zero-count row (registry axis survives every"
               " window; record-time law: zero events -> zero"
               " counts)=%s with window echoes intact=%s;"
               " wcap(2,cur) window=%s total=1 rows==wcur=%s;"
               " liveness vs pre-restart empty snapshots=%s;"
               " zero phantom (board rows == registry rows =="
               " 1)=%s"
               % ({k: row4.get(k) for k in zero_row},
                  row4.get("ai_label") == 1,
                  cap4["showcase_stats_board"] == rows4,
                  win_rows_frozen,
                  wcur4["window"] == cur
                  and wprev4["window"] == prev,
                  wcap4["window"], wcap4["showcase_stats_board"]
                  == wcur4["showcase_stats_board"],
                  dumps(full4) != fam2["full"]
                  and dumps(wcur4) != fam2["wcur"],
                  len(rows4) == 1))

        # -- AC-SSMZ5 post-restart first place, window split -----
        frozen_prev = dumps(wprev4)
        frozen_hist = dumps(whist4)
        frozen_zero = dumps(wzero4)
        sh2.place_exhibit("usr:ada", "sh-first",
                         cl["lamp-cert"], "", False)
        full5 = sh2.stats_board()
        row5 = full5["showcase_stats_board"][0]
        wcur5 = sh2.stats_board(window=cur)
        cur_row5 = wcur5["showcase_stats_board"][0]
        sql_cur5 = sql_counts_window(sh_path, cur).get(
            "sh-first", {"place": 0, "retract": 0})
        view5 = sh2.showcase_view("sh-first")
        ok5 = (row5["places"] == 1 and row5["retracts"] == 0
               and row5["displayed_now"] == 1
               and row5["displayed_now"] == row5["places"]
               - row5["retracts"]
               and cur_row5["places"] == 1
               and cur_row5["retracts"] == 0
               and cur_row5["displayed_now"] == 1
               and sql_cur5["place"] == 1
               and dumps(wcur5) != dumps(wcur4)
               and dumps(sh2.stats_board(window=prev))
               == frozen_prev
               and dumps(sh2.stats_board(window=hist))
               == frozen_hist
               and dumps(sh2.stats_board(window="2099-01"))
               == frozen_zero
               and len(view5["displayed"]) == 1
               and view5["displayed"][0]["cl_id"]
               == cl["lamp-cert"])
        record("AC-SSMZ5", ok5,
               "post-restart first current-month place (real"
               " path: collectibles dock reconnect + SecGate"
               " pass): full row {p=%s r=%s dn=%s} netflow"
               " identity=%s; wcur row recomputes {p=%s dn=%s}"
               " with SQL substr(acted_utc,1,7) cross place=%s"
               " and liveness vs SSMZ4 wcur=%s; wprev/whist/"
               " wzero boards byte-frozen (row stays zero-count"
               " outside the event month)=%s; cross-face"
               " displayed_now == len(showcase_view displayed)"
               "==1=%s"
               % (row5["places"], row5["retracts"],
                  row5["displayed_now"],
                  row5["displayed_now"] == row5["places"]
                  - row5["retracts"],
                  cur_row5["places"], cur_row5["displayed_now"],
                  sql_cur5["place"],
                  dumps(wcur5) != dumps(wcur4),
                  dumps(sh2.stats_board(window=prev))
                  == frozen_prev
                  and dumps(sh2.stats_board(window=hist))
                  == frozen_hist
                  and dumps(sh2.stats_board(window="2099-01"))
                  == frozen_zero,
                  len(view5["displayed"]) == 1))

        # -- AC-SSMZ6 third instance stability ------------------
        fam_final = win_family(sh2, cur, prev, hist)
        counts6 = table_counts(shconn, ledconn)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam3rd = win_family(sh3, cur, prev, hist)
        seq3rd = win_family(sh3, cur, prev, hist) == fam3rd
        counts6b = table_counts(shconn, ledconn)
        record("AC-SSMZ6",
               fam3rd == fam_final and seq3rd
               and counts6 == counts6b,
               "third instance == second-instance final state"
               " byte-identical on all seven forms=%s sequential"
               " double-read self-stable=%s counts flat=%s"
               % (fam3rd == fam_final, seq3rd,
                  counts6 == counts6b))

        # -- AC-SSMZ7 pure-read law + hygiene --------------------
        counts7a = table_counts(shconn, ledconn)
        battery_a = [dumps(x) for x in (
            sh3.stats_board(), sh3.stats_board(2),
            sh3.stats_board(window=cur),
            sh3.stats_board(2, cur),
            sh3.stats_board(window=prev),
            sh3.stats_board(window=hist),
            sh3.stats_board(window="2099-01"))]
        battery_b = [dumps(x) for x in (
            sh3.stats_board(), sh3.stats_board(2),
            sh3.stats_board(window=cur),
            sh3.stats_board(2, cur),
            sh3.stats_board(window=prev),
            sh3.stats_board(window=hist),
            sh3.stats_board(window="2099-01"))]
        counts7b = table_counts(shconn, ledconn)
        method_src = inspect.getsource(S.ShowcaseFace.stats_board)
        write_hits = [w for w in ("INSERT", "DELETE",
                                  "UPDATE ", "CREATE ", "ALTER ")
                      if w in method_src]
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or \
                    stripped.startswith("from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-showcase-statsmonthboundary-persist"
                  in reg_src
                  and "test_showcase_statsmonthboundarypersist.py"
                  in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        outside = tmp not in os.path.abspath(BASE)
        hyg = {"ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok,
               "outside": outside}
        hyg["pure_ok"] = (counts7a == counts7b
                          and battery_a == battery_b
                          and not write_hits
                          and "random" not in method_src)
        sh3.close()
        led3.close()
        sh3 = led3 = None

    finally:
        for obj in (sh, led, sh2, led2, sh3, led3):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
        if shconn is not None:
            shconn.close()
        if ledconn is not None:
            ledconn.close()

    post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-SSMZ7",
           hyg.get("pure_ok") and hyg.get("ascii_ok")
           and hyg.get("net_ok") and hyg.get("reg_ok")
           and hyg.get("expected_ok") and hyg.get("outside")
           and sha_ok,
           "seven-form read battery twice leaves counts"
           " unchanged with repeat pairs byte-identical,"
           " stats_board method source zero write statements"
           " zero RNG=%s; suite pure ASCII=%s net-clean=%s"
           " registry-wired=%s criteria-count=%s world outside"
           " repo=%s product-sha stable=%s (showcase.py +"
           " ledger config.json + lobby config.json)"
           % (hyg.get("pure_ok"), hyg.get("ascii_ok"),
              hyg.get("net_ok"), hyg.get("reg_ok"),
              hyg.get("expected_ok"), hyg.get("outside"),
              sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
