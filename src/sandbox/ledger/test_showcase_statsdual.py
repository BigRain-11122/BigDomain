"""Acceptance suite for the stats_board dual-window combined
board (BigDomain R1989; canon = explore-queue stats-board
dual-window line: default full-window + explicit capped-window
side by side in one envelope, boards_combined single-envelope
law R1974 applied to the cap-window family R1988). Asserts the
pre-registered criteria AC-SSD1..AC-SSD7 from the R1989
explore-queue claim (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

World: the R1983/R1988 sibling shape - five showcases
registered in mixed order, six collectibles, cross-window
place/retract sequences; decisive board order
beta/gamma/alpha/omega/delta.

The content gate is the lobby SecGate product injected by
reference (no copy); this test source stays pure ASCII per the
encoding discipline.

Usage: python test_showcase_statsdual.py
"""

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
              " dual board is a display feature, not"
              " investment advice")

DUAL_KEYS = {"full_board", "capped_board", "window", "disclaimer"}
WINDOW_KEYS = {"limit", "total", "returned", "truncated"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places", "retracts",
            "displayed_now"}

WANT_ORDER = ["beta-win", "gamma-win", "alpha-win",
              "omega-win", "delta-win"]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _ids(board):
    return [r["showcase_id"] for r in board["showcase_stats_board"]]


def _mirror_tail(sh_path, limit):
    """Mirror-SQL third path (R1729/R1988 mirror law): the
    ascending decisive key is (-places, -retracts,
    showcase_id), so the tail-N rows are fetched by the fully
    reversed key (places ASC, retracts ASC, id DESC), taking
    N, then reversed back into ascending decisive order.
    Independent read-only connection."""
    uri = "file:" + sh_path.replace("\\", "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    rows = conn.execute(
        "SELECT s.showcase_id FROM showcases s LEFT JOIN"
        " (SELECT showcase_id,"
        "  SUM(CASE WHEN action = 'place' THEN 1 ELSE 0 END) AS p,"
        "  SUM(CASE WHEN action = 'retract' THEN 1 ELSE 0 END) AS r"
        "  FROM exhibit_events GROUP BY showcase_id) c"
        " ON c.showcase_id = s.showcase_id"
        " ORDER BY COALESCE(c.p, 0) ASC, COALESCE(c.r, 0) ASC,"
        " s.showcase_id DESC LIMIT ?",
        (limit,)).fetchall()
    conn.close()
    return [r[0] for r in reversed(rows)]


def main():
    tmp = tempfile.mkdtemp(prefix="showcase-statsdual-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    fresh_path = os.path.join(tmp, "showcase-fresh.db")

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
            ("dave", "evt-lamp", "lamp-cert"),
            ("alice", "evt-bell", "bell-cert"),
            ("alice", "evt-gate", "gate-cert")):
        cl_ids[item] = cf.issue_certificate(
            "usr:" + who, ev, item)["cl_id"]
    cl_a = cl_ids["tower-cert"]
    cl_b = cl_ids["bridge-cert"]
    cl_c = cl_ids["harbor-cert"]
    cl_d = cl_ids["lamp-cert"]
    cl_e = cl_ids["bell-cert"]

    # mixed registration order (same shape as the R1983 sibling)
    sh.register_showcase("omega-win", "Omega Window", 3, False)
    sh.register_showcase("delta-win", "Delta Window", 3, True)
    sh.register_showcase("gamma-win", "Gamma Window", 3, False)
    sh.register_showcase("beta-win", "Beta Window", 3, True)
    sh.register_showcase("alpha-win", "Alpha Window", 3, False)

    sh.place_exhibit("usr:alice", "alpha-win", cl_a, "", False)
    sh.retract_exhibit("usr:alice", "alpha-win", cl_a)
    sh.place_exhibit("usr:alice", "omega-win", cl_a, "", False)
    for _ in range(2):
        sh.place_exhibit("usr:bob", "beta-win", cl_b, "", False)
        sh.retract_exhibit("usr:bob", "beta-win", cl_b)
    sh.place_exhibit("usr:bob", "beta-win", cl_b, "", False)
    for _ in range(2):
        sh.place_exhibit("usr:carol", "gamma-win", cl_c, "", False)
        sh.retract_exhibit("usr:carol", "gamma-win", cl_c)
    sh.place_exhibit("usr:carol", "gamma-win", cl_c, "", False)
    sh.place_exhibit("usr:dave", "alpha-win", cl_d, "", False)
    sh.place_exhibit("usr:alice", "alpha-win", cl_e, "", False)

    shconn = sqlite3.connect(sh_path)

    # -- AC-SSD1 contract + default-zone fidelity -------------------
    dual2 = sh.stats_board_dual(2)
    full_direct = sh.stats_board()
    ok_env = set(dual2.keys()) == DUAL_KEYS
    ok_win = set(dual2["window"].keys()) == WINDOW_KEYS
    ok_full = (dual2["full_board"]
               == full_direct["showcase_stats_board"]
               and [r["showcase_id"] for r in dual2["full_board"]]
               == WANT_ORDER)
    ok_rows = all(set(r.keys()) == ROW_KEYS
                  for r in dual2["full_board"])
    record("AC-SSD1", ok_env and ok_win and ok_full and ok_rows,
          "dual envelope keys exactly %s; window block keys"
          " exactly %s; full zone == default full read"
          " byte-identical (dumps equal %s) in the decisive"
          " order %s; row field sets unchanged (six keys %s)"
          % (sorted(DUAL_KEYS), sorted(WINDOW_KEYS),
             json.dumps(dual2["full_board"], sort_keys=True)
             == json.dumps(
                 full_direct["showcase_stats_board"],
                 sort_keys=True),
             WANT_ORDER, ok_rows))

    # -- AC-SSD2 bad params fail-closed before any read --------------
    probes = (0, -1, True, "2", 2.5, None)
    c0 = (_count(shconn, "showcases"), _count(shconn, "exhibit_events"))
    codes = []
    for bad in probes:
        try:
            sh.stats_board_dual(bad)
            codes.append("no-raise")
        except S.ShowcaseError as exc:
            codes.append(exc.code)
    c1 = (_count(shconn, "showcases"), _count(shconn, "exhibit_events"))
    ok2 = (codes == [S.E_SH_BAD_LIMIT] * len(probes) and c0 == c1)
    record("AC-SSD2", ok2,
          "six bad forms %s (0 included: the dual face demands an"
          " actual cap) all rejected with E_SH_BAD_LIMIT (%s);"
          " probe batch leaves row counts unchanged %s == %s"
          " (gate fires before any read)"
          % (list(probes), codes, c0, c1))

    # -- AC-SSD3 single-source cross-check vs direct cap face --------
    ok3 = True
    evid = []
    for cap in (1, 2, 50):
        d = sh.stats_board_dual(cap)
        direct = sh.stats_board(cap)
        same_rows = (d["capped_board"]
                     == direct["showcase_stats_board"])
        same_win = (d["window"]["limit"] == direct["limit"]
                    and d["window"]["total"] == direct["total"]
                    and d["window"]["returned"]
                    == direct["returned"]
                    and d["window"]["truncated"]
                    is direct["truncated"])
        evid.append("cap=%d rows_eq=%s win_eq=%s"
                    % (cap, same_rows, same_win))
        ok3 = ok3 and same_rows and same_win
    record("AC-SSD3", ok3,
          "capped zone == direct stats_board(limit) rows and"
          " window block field-by-field for every cap (%s) - the"
          " two faces agree because they derive from the same"
          " decisive order, single-source law holds"
          % ("; ".join(evid)))

    # -- AC-SSD4 mirror-SQL third path + containment ------------------
    mirror = _mirror_tail(sh_path, 2)
    dual_ids = [r["showcase_id"] for r in dual2["capped_board"]]
    full_ids = [r["showcase_id"] for r in dual2["full_board"]]
    ok4 = (dual_ids == mirror
           and dual_ids == full_ids[-2:]
           and set(dual_ids).issubset(set(full_ids))
           and len(dual_ids) == 2)
    record("AC-SSD4", ok4,
          "limit=2 capped ids %s == mirror-SQL reversed-key"
          " third path %s == full-board tail slice %s;"
          " containment law holds (capped subset of full)"
          % (dual_ids, mirror, full_ids[-2:]))

    # -- AC-SSD5 boundary states + honest empty dual board ------------
    dual5 = sh.stats_board_dual(5)
    dual1 = sh.stats_board_dual(1)
    empty = fresh.stats_board_dual(3)
    ok5 = (dual5["capped_board"] == dual5["full_board"]
           and dual5["window"]["truncated"] is False
           and dual5["window"]["returned"] == 5
           and dual5["window"]["total"] == 5
           and [r["showcase_id"] for r in dual1["capped_board"]]
           == [WANT_ORDER[-1]]
           and dual1["window"]["truncated"] is True
           and empty["full_board"] == []
           and empty["capped_board"] == []
           and empty["window"] == {"limit": 3, "total": 0,
                                   "returned": 0,
                                   "truncated": False}
           and set(empty.keys()) == DUAL_KEYS)
    record("AC-SSD5", ok5,
          "limit==total (5/5) capped zone == full zone"
          " truncated=False; limit=1 returns the single tail"
          " row %s; a zero-registration world returns an honest"
          " empty dual board (both zones [], window"
          " {limit:3,total:0,returned:0,truncated:False},"
          " envelope keys still present)"
          % ([r["showcase_id"] for r in dual1["capped_board"]],))

    # -- AC-SSD6 pure-read law + determinism + single-source ----------
    counts0 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"))
    battery_a = [json.dumps(sh.stats_board_dual(2), sort_keys=True),
                json.dumps(sh.stats_board_dual(1), sort_keys=True),
                json.dumps(sh.stats_board_dual(50), sort_keys=True)]
    battery_b = [json.dumps(sh.stats_board_dual(2), sort_keys=True),
                json.dumps(sh.stats_board_dual(1), sort_keys=True),
                json.dumps(sh.stats_board_dual(50), sort_keys=True)]
    counts1 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"))
    method_src = inspect.getsource(S.ShowcaseFace.stats_board_dual)
    write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                              "CREATE ", "ALTER ", "SELECT")
                  if w in method_src]
    source_calls = method_src.count("self.stats_board()")
    ok6 = (counts0 == counts1 and battery_a == battery_b
           and not write_hits and source_calls == 1
           and "random" not in method_src)
    record("AC-SSD6", ok6,
          "read battery (dual 1/2/50, twice) leaves row counts"
          " unchanged %s == %s and every double-call dumps pair"
          " byte-identical; dual method source has zero SQL and"
          " zero write statements (%s), zero RNG, exactly ONE"
          " stats_board() call (%d) - single derivation source"
          % (counts0, counts1, write_hits, source_calls))

    # -- AC-SSD7 hygiene -----------------------------------------------
    with open(os.path.join(BASE, "showcase.py"),
              encoding="utf-8") as handle:
        sh_src = handle.read()
    with open(os.path.abspath(__file__),
              encoding="utf-8") as handle:
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
    ok7 = (own_non_ascii == 0 and mod_non_ascii == 0
           and not net_imports and sha_before == sha_after
           and "stats_board_dual(self, limit)" in sh_src
           and os.path.isabs(tmp) and tmp not in os.path.abspath(
               os.path.join(BASE, "..", "..", "..")))
    record("AC-SSD7", ok7,
          "suite source pure ASCII (%d non-ascii), showcase.py"
          " stays pure ASCII (%d non-ascii) and carries the dual"
          " signature; zero network imports (%d); shipped"
          " config.json sha256 stable (%s == %s); world db under"
          " system temp outside the repo (%s)"
          % (own_non_ascii, mod_non_ascii, len(net_imports),
             sha_before[:16], sha_after[:16], ok7))

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
