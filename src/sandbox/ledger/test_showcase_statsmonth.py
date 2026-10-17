"""Acceptance suite for the per-showcase statistics board
month-window read face (BigDomain R2015; canon = explore-queue
showcase stats month-window line, AC-SSM1..AC-SSM7 pre-
registered in state/queue/explore.md before this code existed;
honesty law). Asserts each criterion with PASS/FAIL evidence
and exits non-zero on any FAIL.

World: three showcases registered in mixed order, five
collectibles, current-month real-path place/retract churn plus
historical-month fixture rows (direct INSERT - the R1730
historical fixture law, noted per row) that exercise the
record-time law: an earlier-month display that stays off the
current-month window, and a straddle pair (earlier-month place +
current-month true-path retract).

The content gate is the lobby SecGate product injected by
reference (no copy); this test source stays pure ASCII per the
encoding discipline (the unicode look-alike probe is written as
escape sequences).

Usage: python test_showcase_statsmonth.py
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

import ledger as L                    # noqa: E402 (P-47-2b core)
import collectibles as C              # noqa: E402 (R619 owner face)
import showcase as S                  # noqa: E402 (R1750 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase stats"
              " month-window board is a display feature, not"
              " investment advice")

ROW_KEYS = {"showcase_id", "title", "ai_label", "places", "retracts",
            "displayed_now"}
FULL_KEYS = {"showcase_stats_board", "disclaimer"}
WIN_KEYS = {"showcase_stats_board", "disclaimer", "window"}
CAP_KEYS = {"showcase_stats_board", "disclaimer", "limit", "total",
            "returned", "truncated"}
WINCAP_KEYS = CAP_KEYS | {"window"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _rowmap(board):
    return {r["showcase_id"]: r for r in board["showcase_stats_board"]}


def _order(board):
    return [r["showcase_id"] for r in board["showcase_stats_board"]]


def _sql_counts_window(conn, window):
    counts = {}
    for sid, action, n in conn.execute(
            "SELECT showcase_id, action, COUNT(*) FROM exhibit_events"
            " WHERE substr(acted_utc, 1, 7) = ?"
            " GROUP BY showcase_id, action",
            (window,)).fetchall():
        slot = counts.setdefault(str(sid), {"place": 0, "retract": 0})
        slot[str(action)] = int(n)
    return counts


def _insert_hist(conn, sid, cl, owner, ts):
    """R1730 historical-month fixture law: direct INSERT of a
    fully valid event row with an explicit acted_utc stamp (the
    read face under test derives from record time, so the
    fixture carries only well-formed rows)."""
    conn.execute(
        "INSERT INTO exhibit_events (showcase_id, cl_id, owner_id,"
        " caption, ai_label, action, acted_utc) VALUES"
        " (?, ?, ?, '', 0, 'place', ?)",
        (sid, cl, "usr:" + owner, ts))
    conn.commit()


def _raise_code(fn):
    try:
        fn()
    except S.ShowcaseError as exc:
        return exc.code
    except Exception:                                  # noqa: BLE001
        return "WRONG-EXC"
    return "NO-RAISE"


def main():
    tmp = tempfile.mkdtemp(prefix="showcase-statsmonth-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    fresh_path = os.path.join(tmp, "showcase-fresh.db")

    now = datetime.datetime.now(datetime.timezone.utc)
    cur = now.strftime("%Y-%m")
    prev_dt = now - datetime.timedelta(days=45)
    prev = prev_dt.strftime("%Y-%m")
    prev_ts = prev_dt.strftime("%Y-%m-%dT10:00:00Z")

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    fresh = S.ShowcaseFace(led, gate, DISCLAIMER, fresh_path)

    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    cl_ids = {}
    for who, ev, item in (
            ("alice", "evt-tower", "tower-cert"),
            ("bob", "evt-bridge", "bridge-cert"),
            ("carol", "evt-harbor", "harbor-cert"),
            ("alice", "evt-bell", "bell-cert"),
            ("dave", "evt-gate", "gate-cert")):
        cl_ids[item] = cf.issue_certificate(
            "usr:" + who, ev, item)["cl_id"]
    cl_a = cl_ids["tower-cert"]
    cl_b = cl_ids["bridge-cert"]
    cl_c = cl_ids["harbor-cert"]
    cl_e = cl_ids["bell-cert"]
    cl_f = cl_ids["gate-cert"]

    # registration order deliberately mixed (zeta, mu, alpha) -
    # zero insertion-order keys must survive every windowed order
    sh.register_showcase("zeta-gal", "Zeta Gallery", 3, False)
    sh.register_showcase("mu-gal", "Mu Gallery", 3, True)
    sh.register_showcase("alpha-gal", "Alpha Gallery", 3, False)

    # current-month real-path world: cross-window re-place and
    # per-window pair churn (all rows stamped with acted_utc=now)
    sh.place_exhibit("usr:alice", "alpha-gal", cl_a, "", False)
    sh.retract_exhibit("usr:alice", "alpha-gal", cl_a)
    sh.place_exhibit("usr:alice", "mu-gal", cl_a, "", False)
    sh.place_exhibit("usr:bob", "mu-gal", cl_b, "", False)
    sh.retract_exhibit("usr:bob", "mu-gal", cl_b)
    sh.place_exhibit("usr:bob", "mu-gal", cl_b, "", False)
    sh.place_exhibit("usr:carol", "alpha-gal", cl_c, "", False)

    # historical-month fixture rows (direct INSERT, R1730 law):
    # cl_e displays in alpha-gal entirely inside the previous
    # month (stays off the current-month window); cl_f pairs with
    # the true-path retract below into the straddle case
    shconn = sqlite3.connect(sh_path)
    _insert_hist(shconn, "alpha-gal", cl_e, "alice", prev_ts)
    _insert_hist(shconn, "mu-gal", cl_f, "dave", prev_ts)

    # straddle: earlier-month place + current-month true-path
    # retract (the full-state display gate passes because the
    # latest event overall is still the earlier-month place)
    sh.retract_exhibit("usr:dave", "mu-gal", cl_f)

    conn = sqlite3.connect(db_path)

    # -- AC-SSM1 default zero-drift --------------------------------------
    full = sh.stats_board()
    capped = sh.stats_board(limit=2)
    ok1 = (set(full.keys()) == FULL_KEYS
           and set(capped.keys()) == CAP_KEYS
           and "window" not in capped
           and json.dumps(full, sort_keys=True)
           == json.dumps(sh.stats_board(), sort_keys=True)
           and capped["showcase_stats_board"]
           == full["showcase_stats_board"][-2:]
           and capped["total"] == 3 and capped["returned"] == 2
           and capped["truncated"] is True
           and len(full["showcase_stats_board"]) == 3)
    record("AC-SSM1", ok1,
          "default full envelope keys %s (no window key), capped"
          " envelope keys %s (no window key); double-call dumps"
          " byte-identical; capped rows == full decisive-order"
          " tail slice with total=3 returned=2 truncated=True"
          % (sorted(full.keys()), sorted(capped.keys())))

    # -- AC-SSM2 window gate fail-closed ---------------------------------
    bad_forms = [
        ("int", 202610), ("bool", True), ("month-1-digit", "2026-1"),
        ("month-13", "2026-13"), ("month-00", "2026-00"),
        ("slash-sep", "2026/10"), ("no-sep", "202610"),
        ("trailing-space", "2026-10 "),
        ("unicode-digits",
         "\uff12\uff10\uff12\uff16" + "-" + "\uff11\uff10")]
    counts_pre = (_count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))
    codes = []
    for label, form in bad_forms:
        code = _raise_code(
            lambda f=form: sh.stats_board(window=f))
        codes.append((label, code))
    order_code = _raise_code(
        lambda: sh.stats_board(limit=-1, window=123))
    order_code2 = _raise_code(
        lambda: sh.stats_board(limit=-1, window=cur))
    counts_post = (_count(shconn, "showcases"),
                   _count(shconn, "exhibit_events"))
    ok2 = (all(code == "E_SH_BAD_WINDOW"
               for _, code in codes)
           and len(codes) == 9
           and order_code == "E_SH_BAD_LIMIT"
           and order_code2 == "E_SH_BAD_LIMIT"
           and counts_pre == counts_post)
    record("AC-SSM2", ok2,
          "all %d malformed windows refuse E_SH_BAD_WINDOW"
          " (%s); gate order: bad limit + bad/good window ->"
          " E_SH_BAD_LIMIT fires first (x2 probes); showcase and"
          " event row counts unchanged %s == %s (fail-closed"
          " before any read)"
          % (len(codes), [c for c, _ in codes], counts_pre,
             counts_post))

    # -- AC-SSM3 windowed aggregation record-time law --------------------
    wboard = sh.stats_board(window=cur)
    wrows = _rowmap(wboard)
    sql_counts = _sql_counts_window(shconn, cur)
    cross = []
    for sid, row in wrows.items():
        slot = sql_counts.get(sid, {"place": 0, "retract": 0})
        cross.append(row["places"] == slot["place"]
                     and row["retracts"] == slot["retract"]
                     and row["displayed_now"]
                     == len(sh._displayed_rows_window(sid, cur)))
    ok3 = all(cross) and len(cross) == 3
    record("AC-SSM3", ok3,
          "windowed places/retracts match the independent SQL"
          " re-derivation (substr(acted_utc, 1, 7) filter) on"
          " all %d rows and displayed_now == len of the"
          " _displayed_rows_window view face per showcase"
          " (board x window-view two code paths)"
          % len(cross))

    # -- AC-SSM4 earlier-month display, straddle, honest zeros -----------
    disp_cur_alpha = {r[0] for r in
                      sh._displayed_rows_window("alpha-gal", cur)}
    disp_prev_alpha = {r[0] for r in
                       sh._displayed_rows_window("alpha-gal", prev)}
    disp_cur_mu = {r[0] for r in
                   sh._displayed_rows_window("mu-gal", cur)}
    pboard = sh.stats_board(window=prev)
    prows = _rowmap(pboard)
    zboard = sh.stats_board(window="2099-01")
    zrows = _rowmap(zboard)
    empty_win = fresh.stats_board(window=cur)
    mu_cur = wrows["mu-gal"]
    straddle_honest = (mu_cur["places"] == 3
                       and mu_cur["retracts"] == 2
                       and mu_cur["displayed_now"] == 2
                       and mu_cur["places"] - mu_cur["retracts"]
                       != mu_cur["displayed_now"])
    ok4 = (cl_e not in disp_cur_alpha
           and disp_cur_alpha == {cl_c}
           and disp_prev_alpha == {cl_e}
           and cl_f not in disp_cur_mu
           and disp_cur_mu == {cl_a, cl_b}
           and prows["mu-gal"]["places"] == 1
           and prows["mu-gal"]["retracts"] == 0
           and prows["mu-gal"]["displayed_now"] == 1
           and straddle_honest
           and all(zrows[s]["places"] == 0
                   and zrows[s]["retracts"] == 0
                   and zrows[s]["displayed_now"] == 0
                   for s in ("alpha-gal", "mu-gal", "zeta-gal"))
           and len(zboard["showcase_stats_board"]) == 3
           and empty_win["showcase_stats_board"] == []
           and set(empty_win.keys()) == WIN_KEYS)
    record("AC-SSM4", ok4,
          "earlier-month display (cl_e) stays off the current"
          " window but heads the previous-window board (record-"
          "time law); straddle pair (cl_f place@prev + true-path"
          " retract@cur) reads honestly as mu cur (places=3,"
          " retracts=2, displayed_now=2, net-flow identity NOT"
          " asserted in-window - full-board law only); eventless"
          " month 2099-01 shows dense honest zeros on all 3"
          " registry rows; zero-registration face returns an"
          " honest empty windowed board")

    # -- AC-SSM5 envelope + decisive order -------------------------------
    dumps_w1 = json.dumps(wboard, sort_keys=True)
    dumps_w2 = json.dumps(sh.stats_board(window=cur), sort_keys=True)
    ok5 = (set(wboard.keys()) == WIN_KEYS
           and wboard["window"] == cur
           and all(set(r.keys()) == ROW_KEYS
                   for r in wboard["showcase_stats_board"])
           and _order(wboard) == ["mu-gal", "alpha-gal", "zeta-gal"]
           and _order(pboard) == ["alpha-gal", "mu-gal", "zeta-gal"]
           and dumps_w1 == dumps_w2)
    record("AC-SSM5", ok5,
          "windowed envelope keys %s with window echo, row keys"
          " unchanged (%d keys); cur-window decisive order %s"
          " (places DESC, retracts DESC, id ASC), prev-window"
          " tie order resolved by id ASC %s; double-call dumps"
          " byte-identical"
          % (sorted(wboard.keys()), len(ROW_KEYS),
             _order(wboard), _order(pboard)))

    # -- AC-SSM6 window x cap orthogonality -------------------------------
    wcap = sh.stats_board(limit=2, window=cur)
    ok6 = (set(wcap.keys()) == WINCAP_KEYS
           and wcap["window"] == cur
           and wcap["showcase_stats_board"]
           == wboard["showcase_stats_board"][-2:]
           and wcap["total"] == 3 and wcap["returned"] == 2
           and wcap["truncated"] is True
           and _order(wcap) == ["alpha-gal", "zeta-gal"]
           and "window" not in sh.stats_board(limit=2))
    record("AC-SSM6", ok6,
          "windowed cap reads the tail of the WINDOWED decisive"
          " order %s with the honest overflow block (total=3 full"
          " registry count, returned=2, truncated=True, envelope"
          " keys %s); the default capped path still carries no"
          " window key"
          % (_order(wcap), sorted(wcap.keys())))

    # -- AC-SSM7 pure-read law + hygiene ---------------------------------
    counts0 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"),
               _count(conn, "ledger_tx"))
    dumps_r1 = json.dumps(sh.stats_board(window=cur), sort_keys=True)
    dumps_r2 = json.dumps(sh.stats_board(window=cur), sort_keys=True)
    for sid in ("alpha-gal", "mu-gal", "zeta-gal"):
        sh.showcase_view(sid)
        sh.showcase_view_window(sid, cur)
        sh.chronicle_tour(sid)
    counts1 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"),
               _count(conn, "ledger_tx"))
    method_src = inspect.getsource(S.ShowcaseFace.stats_board)
    write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                              "CREATE ", "ALTER ")
                  if w in method_src]
    with open(os.path.join(BASE, "showcase.py"),
              encoding="utf-8") as handle:
        sh_src = handle.read()
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_src = handle.read()
    own_non_ascii = sum(1 for ch in own_src if ord(ch) > 127)
    mod_non_ascii = sum(1 for ch in sh_src if ord(ch) > 127)
    net_imports = [ln for ln in own_src.splitlines()
                   if (ln.startswith("import ")
                       or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    sha_before = hashlib.sha256(cfg_bytes).hexdigest()
    sha_after = hashlib.sha256(cfg_after).hexdigest()
    ok7 = (counts0 == counts1 and dumps_r1 == dumps_r2
           and not write_hits and own_non_ascii == 0
           and mod_non_ascii == 0 and not net_imports
           and sha_before == sha_after
           and "random" not in method_src
           and os.path.isabs(tmp)
           and tmp not in os.path.abspath(
               os.path.join(BASE, "..", "..", "..")))
    record("AC-SSM7", ok7,
          "windowed read batch leaves every row count unchanged"
          " %s == %s, repeated windowed reads byte-identical;"
          " stats_board method source has zero write statements"
          " (%s); suite source pure ASCII (%d non-ascii),"
          " showcase.py stays pure ASCII (%d non-ascii); zero"
          " network imports (%d); shipped config.json sha256"
          " stable (%s == %s); zero RNG; world db under system"
          " temp outside the repo"
          % (counts0, counts1, write_hits, own_non_ascii,
             mod_non_ascii, len(net_imports), sha_before[:16],
             sha_after[:16]))

    conn.close()
    shconn.close()
    fresh.close()
    sh.close()
    cf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
