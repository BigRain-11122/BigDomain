"""Acceptance suite for the stats_board cap-window tail read
(BigDomain R1988; canon = explore-queue stats-board truncation
line: limit tail slice over the R1983 decisive order with an
honest overflow block, registry-keyed dense axis). Asserts the
pre-registered criteria AC-SST1..AC-SST7 from the R1988
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

World: the R1983 sibling shape - five showcases registered in
mixed order, six collectibles, cross-window place/retract
sequences; decisive board order beta/gamma/alpha/omega/delta.

The content gate is the lobby SecGate product injected by
reference (no copy); this test source stays pure ASCII per the
encoding discipline.

Usage: python test_showcase_statslimit.py
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
import showcase as S                  # noqa: E402 (R1750/R1983 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase stats"
              " board cap read is a display feature, not"
              " investment advice")

ROW_KEYS = {"showcase_id", "title", "ai_label", "places", "retracts",
            "displayed_now"}
DEFAULT_KEYS = {"showcase_stats_board", "disclaimer"}
CAPPED_KEYS = {"showcase_stats_board", "disclaimer",
               "limit", "total", "returned", "truncated"}

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
    """Mirror-SQL third path (R1729 mirror law): the ascending
    decisive key is (-places, -retracts, showcase_id), so the
    tail-N rows are fetched by the fully reversed key (places
    ASC, retracts ASC, id DESC), taking N, then reversed back
    into ascending decisive order. Independent read-only
    connection. (Direction note: the R1988 claim line drafted
    the mirror as p DESC/r DESC/id DESC - that drops the id
    component's reversal and was corrected at first red per the
    R1704 honest-fix precedent; the registered criterion is the
    cross-check semantics, the product tail was never wrong.)"""
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
    tmp = tempfile.mkdtemp(prefix="showcase-statslimit-")
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

    # -- AC-SST1 default sentinel keeps the two-key envelope -------
    d_def = json.dumps(sh.stats_board(), sort_keys=True)
    d_zero = json.dumps(sh.stats_board(0), sort_keys=True)
    ok_env = set(sh.stats_board().keys()) == DEFAULT_KEYS
    ok_order = _ids(sh.stats_board()) == WANT_ORDER
    record("AC-SST1", d_def == d_zero and ok_env and ok_order,
          "no-arg call == explicit limit=0 byte-identical"
          " (dumps equal %s); default envelope keys exactly"
          " %s (zero drift); decisive order intact %s"
          % (d_def == d_zero, sorted(DEFAULT_KEYS), ok_order))

    # -- AC-SST2 bad params fail-closed before any read ------------
    probes = (-1, True, "2", 2.5, None)
    c0 = (_count(shconn, "showcases"), _count(shconn, "exhibit_events"))
    codes = []
    for bad in probes:
        try:
            sh.stats_board(bad)
            codes.append("no-raise")
        except S.ShowcaseError as exc:
            codes.append(exc.code)
    c1 = (_count(shconn, "showcases"), _count(shconn, "exhibit_events"))
    ok2 = (codes == [S.E_SH_BAD_LIMIT] * len(probes) and c0 == c1)
    record("AC-SST2", ok2,
          "five bad forms %s all rejected with E_SH_BAD_LIMIT"
          " (%s); probe batch leaves row counts unchanged"
          " %s == %s (gate fires before any read)"
          % (list(probes), codes, c0, c1))

    # -- AC-SST3 cap above total returns everything ----------------
    cap50 = sh.stats_board(50)
    full = sh.stats_board()
    ok3 = (set(cap50.keys()) == CAPPED_KEYS
           and cap50["limit"] == 50 and cap50["total"] == 5
           and cap50["returned"] == 5
           and cap50["truncated"] is False
           and cap50["showcase_stats_board"]
           == full["showcase_stats_board"])
    record("AC-SST3", ok3,
          "limit=50 over 5 returns the full board rows"
          " (truncated=False, total=%d == returned=%d =="
          " registry rows), capped envelope keys exactly %s"
          % (cap50["total"], cap50["returned"],
             sorted(CAPPED_KEYS)))

    # -- AC-SST4 tail truncation + mirror-SQL third path ------------
    cap2 = sh.stats_board(2)
    tail = full["showcase_stats_board"][-2:]
    mirror = _mirror_tail(sh_path, 2)
    ok4 = (cap2["limit"] == 2 and cap2["total"] == 5
           and cap2["returned"] == 2 and cap2["truncated"] is True
           and cap2["showcase_stats_board"] == tail
           and _ids(cap2) == mirror
           and all(set(r.keys()) == ROW_KEYS
                   for r in cap2["showcase_stats_board"]))
    record("AC-SST4", ok4,
          "limit=2 returns the tail 2 rows of the decisive order"
          " %s (== default full read rows[-2:], == mirror SQL"
          " reversed-key LIMIT 2 reversed %s); total stays the"
          " honest full count %d != truncated %d; row field sets"
          " unchanged (six keys)"
          % (_ids(cap2), mirror, cap2["total"], cap2["returned"]))

    # -- AC-SST5 boundary states + honest empty capped read ---------
    cap5 = sh.stats_board(5)
    cap1 = sh.stats_board(1)
    empty = fresh.stats_board(3)
    ok5 = (cap5["truncated"] is False and cap5["returned"] == 5
           and cap5["total"] == 5
           and cap1["returned"] == 1 and cap1["truncated"] is True
           and _ids(cap1) == [WANT_ORDER[-1]]
           and empty["showcase_stats_board"] == []
           and empty["limit"] == 3 and empty["total"] == 0
           and empty["returned"] == 0
           and empty["truncated"] is False
           and set(empty.keys()) == CAPPED_KEYS)
    record("AC-SST5", ok5,
          "limit==total (5/5) returns everything truncated=False;"
          " limit=1 returns the single tail row %s; a"
          " zero-registration world returns an honest empty"
          " capped read (rows=[], total=0, returned=0,"
          " truncated=False, block keys still present)"
          % (_ids(cap1),))

    # -- AC-SST6 pure-read law + determinism -------------------------
    counts0 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"))
    battery_a = [json.dumps(sh.stats_board(), sort_keys=True),
                 json.dumps(sh.stats_board(2), sort_keys=True),
                 json.dumps(sh.stats_board(1), sort_keys=True),
                 json.dumps(sh.stats_board(50), sort_keys=True)]
    battery_b = [json.dumps(sh.stats_board(), sort_keys=True),
                 json.dumps(sh.stats_board(2), sort_keys=True),
                 json.dumps(sh.stats_board(1), sort_keys=True),
                 json.dumps(sh.stats_board(50), sort_keys=True)]
    counts1 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"))
    method_src = inspect.getsource(S.ShowcaseFace.stats_board)
    write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                              "CREATE ", "ALTER ")
                  if w in method_src]
    ok6 = (counts0 == counts1 and battery_a == battery_b
           and not write_hits and "random" not in method_src)
    record("AC-SST6", ok6,
          "read battery (default + limit 1/2/50, twice) leaves row"
          " counts unchanged %s == %s and every double-call dumps"
          " pair byte-identical; stats_board method source has"
          " zero write statements (%s) and zero RNG"
          % (counts0, counts1, write_hits))

    # -- AC-SST7 hygiene ----------------------------------------------
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
           and S.E_SH_BAD_LIMIT in sh_src
           and "stats_board(self, limit=0)" in sh_src
           and os.path.isabs(tmp) and tmp not in os.path.abspath(
               os.path.join(BASE, "..", "..", "..")))
    record("AC-SST7", ok7,
          "suite source pure ASCII (%d non-ascii), showcase.py"
          " stays pure ASCII (%d non-ascii) and carries the new"
          " signature + E_SH_BAD_LIMIT constant; zero network"
          " imports (%d); shipped config.json sha256 stable"
          " (%s == %s); world db under system temp outside the"
          " repo (%s)"
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
