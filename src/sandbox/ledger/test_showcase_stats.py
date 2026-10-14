"""Acceptance suite for the per-showcase exhibit statistics
board (BigDomain R1983; canon = explore-queue showcase stats
line: registry-keyed pure-read place/retract event count
aggregation over the R1750 showcase face). Asserts the
pre-registered criteria AC-SSB1..AC-SSB7 from the R1983
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

World: five showcases registered in mixed order (registration
order deliberately differs from every board order), six
collectibles, cross-window place/retract sequences that exercise
the net-flow identity displayed_now == places - retracts.

The content gate is the lobby SecGate product injected by
reference (no copy); this test source stays pure ASCII per the
encoding discipline.

Usage: python test_showcase_stats.py
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
              " board is a display feature, not investment advice")

ROW_KEYS = {"showcase_id", "title", "ai_label", "places", "retracts",
            "displayed_now"}
ENV_KEYS = {"showcase_stats_board", "disclaimer"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _rowmap(board):
    return {r["showcase_id"]: r for r in board["showcase_stats_board"]}


def _sql_counts(conn):
    counts = {}
    for sid, action, n in conn.execute(
            "SELECT showcase_id, action, COUNT(*) FROM exhibit_events"
            " GROUP BY showcase_id, action").fetchall():
        slot = counts.setdefault(str(sid), {"place": 0, "retract": 0})
        slot[str(action)] = int(n)
    return counts


def _sql_dnow(conn):
    dnow = {}
    for sid, n in conn.execute(
            "SELECT showcase_id, COUNT(*) FROM exhibit_events"
            " WHERE event_id IN (SELECT MAX(event_id) FROM"
            " exhibit_events GROUP BY cl_id)"
            " AND action = 'place' GROUP BY showcase_id").fetchall():
        dnow[str(sid)] = int(n)
    return dnow


def main():
    tmp = tempfile.mkdtemp(prefix="showcase-stats-")
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
    cl_f = cl_ids["gate-cert"]

    # registration order deliberately mixed (omega, delta, gamma,
    # beta, alpha) - zero insertion-order keys must survive
    sh.register_showcase("omega-win", "Omega Window", 3, False)
    sh.register_showcase("delta-win", "Delta Window", 3, True)
    sh.register_showcase("gamma-win", "Gamma Window", 3, False)
    sh.register_showcase("beta-win", "Beta Window", 3, True)
    sh.register_showcase("alpha-win", "Alpha Window", 3, False)

    # event world: cross-window re-place + per-window pair churn
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

    conn = sqlite3.connect(db_path)
    shconn = sqlite3.connect(sh_path)

    # -- AC-SSB1 registry-keyed dense board + honest empty --------------
    empty = fresh.stats_board()
    board = sh.stats_board()
    reg_n = _count(shconn, "showcases")
    ok_env = (set(empty.keys()) == ENV_KEYS
              and empty["showcase_stats_board"] == []
              and empty["disclaimer"] == DISCLAIMER)
    ok_rows = (len(board["showcase_stats_board"]) == reg_n == 5
               and all(set(r.keys()) == ROW_KEYS
                       for r in board["showcase_stats_board"])
               and set(board.keys()) == ENV_KEYS
               and board["disclaimer"] == DISCLAIMER)
    rows_by_id = _rowmap(board)
    zero = rows_by_id["delta-win"]
    ok_zero = (zero["places"] == 0 and zero["retracts"] == 0
               and zero["displayed_now"] == 0)
    record("AC-SSB1", ok_env and ok_rows and ok_zero,
          "zero-registration face returns an honest empty board"
          " (envelope keys %s, disclaimer resident); mixed world"
          " board has %d rows == %d registered showcases, every"
          " row exactly six keys %s, envelope keys %s; the"
          " zero-event showcase shows honest zeros (%d/%d/%d)"
          % (sorted(empty.keys()), len(board["showcase_stats_board"]),
             reg_n, sorted(ROW_KEYS), sorted(ENV_KEYS),
             zero["places"], zero["retracts"],
             zero["displayed_now"]))

    # -- AC-SSB2 aggregation cross-check + net-flow identity -----------
    sql_counts = _sql_counts(shconn)
    sql_dnow = _sql_dnow(shconn)
    cross = []
    net = []
    for sid, row in rows_by_id.items():
        slot = sql_counts.get(sid, {"place": 0, "retract": 0})
        want_p, want_r = slot["place"], slot["retract"]
        want_d = sql_dnow.get(sid, 0)
        cross.append((row["places"] == want_p
                      and row["retracts"] == want_r
                      and row["displayed_now"] == want_d))
        net.append(row["displayed_now"]
                   == row["places"] - row["retracts"])
    ok2 = all(cross) and all(net) and len(cross) == 5
    record("AC-SSB2", ok2,
          "every row counts match the independent SQL"
          " re-derivation (places/retracts by action, displayed_now"
          " by latest-event-per-item) across all %d rows; net-flow"
          " identity displayed_now == places - retracts holds on"
          " every row (cross-window re-place included)"
          % len(cross))

    # -- AC-SSB3 deterministic decisive order ---------------------------
    order = [r["showcase_id"]
             for r in board["showcase_stats_board"]]
    want_order = ["beta-win", "gamma-win", "alpha-win",
                  "omega-win", "delta-win"]
    dumps_a = json.dumps(board, sort_keys=True)
    dumps_b = json.dumps(sh.stats_board(), sort_keys=True)
    ok3 = (order == want_order
           and dumps_a == dumps_b
           and rows_by_id["beta-win"]["retracts"]
           == rows_by_id["gamma-win"]["retracts"] == 2
           and rows_by_id["alpha-win"]["retracts"] == 1)
    record("AC-SSB3", ok3,
          "board order %s == expected (places DESC, retracts DESC,"
          " id ASC; equal-places tie broken by higher retracts,"
          " double tie broken by id ASC); registration order was"
          " mixed and does not leak; double-call dumps"
          " byte-identical" % order)

    # -- AC-SSB4 live derivation, zero cached counters ------------------
    b0 = _rowmap(sh.stats_board())
    sh.place_exhibit("usr:alice", "delta-win", cl_f, "", False)
    b1 = _rowmap(sh.stats_board())
    sh.retract_exhibit("usr:alice", "delta-win", cl_f)
    b2 = _rowmap(sh.stats_board())
    order2 = [r["showcase_id"]
              for r in sh.stats_board()["showcase_stats_board"]]
    ok4 = (b0["delta-win"]["places"] == 0
           and b1["delta-win"]["places"] == 1
           and b1["delta-win"]["displayed_now"] == 1
           and b1["delta-win"]["retracts"] == 0
           and b2["delta-win"]["retracts"] == 1
           and b2["delta-win"]["displayed_now"] == 0
           and b2["delta-win"]["places"] == 1
           and order2.index("delta-win")
           < order2.index("omega-win")
           and order2[:3] == ["beta-win", "gamma-win",
                              "alpha-win"])
    record("AC-SSB4", ok4,
          "live place moves the zero-event row to places 0->1 and"
          " displayed_now 0->1 on the immediate re-read; live"
          " retract moves retracts 0->1 and displayed_now 1->0"
          " (zero cached counters, board re-derived per call);"
          " the reordered board keeps the decisive key order"
          " (delta-win now precedes omega-win)")

    # -- AC-SSB6 ai_label persistence + cross-face reconciliation ------
    rows_now = _rowmap(sh.stats_board())
    want_ai = {"alpha-win": 0, "beta-win": 1, "gamma-win": 0,
               "delta-win": 1, "omega-win": 0}
    face_ok = []
    for sid, row in rows_now.items():
        view = sh.showcase_view(sid)
        face_ok.append(row["ai_label"] == want_ai[sid]
                        and row["displayed_now"]
                        == len(view["displayed"]))
    ok6 = all(face_ok) and len(face_ok) == 5
    record("AC-SSB6", ok6,
          "every row carries the registry-declared ai_label"
          " persistent (%s, both states present); displayed_now =="
          " len(showcase_view().displayed) on every row (board and"
          " view faces reconcile over the same store)"
          % {k: v for k, v in sorted(want_ai.items())})

    # -- AC-SSB5 pure-read law ------------------------------------------
    counts0 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"),
               _count(conn, "ledger_tx"))
    batch = []
    for _ in range(2):
        batch.append(json.dumps(sh.stats_board(), sort_keys=True))
        for sid in ("alpha-win", "beta-win", "gamma-win",
                    "delta-win", "omega-win"):
            sh.showcase_view(sid)
            sh.chronicle_tour(sid)
    counts1 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"),
               _count(conn, "ledger_tx"))
    method_src = inspect.getsource(S.ShowcaseFace.stats_board)
    write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                              "CREATE ", "ALTER ")
                  if w in method_src]
    ok5 = (counts0 == counts1 and batch[0] == batch[1]
           and not write_hits)
    record("AC-SSB5", ok5,
          "read batch (board x2 + view + tour per showcase) leaves"
          " every row count unchanged %s == %s and ledger_tx"
          " constant (display stays free); stats_board method"
          " source has zero write statements (%s); repeated board"
          " reads stay byte-identical"
          % (counts0, counts1, write_hits))

    # -- AC-SSB7 hygiene -------------------------------------------------
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
           and "random" not in method_src
           and os.path.isabs(tmp) and tmp not in os.path.abspath(
               os.path.join(BASE, "..", "..", "..")))
    record("AC-SSB7", ok7,
          "suite source pure ASCII (%d non-ascii), showcase.py"
          " stays pure ASCII (%d non-ascii); zero network imports"
          " (%d); shipped config.json sha256 stable (%s == %s);"
          " zero RNG in the method; world db under system temp"
          " outside the repo (%s)"
          % (own_non_ascii, mod_non_ascii, len(net_imports),
             sha_before[:16], sha_after[:16],
             ok7))

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
