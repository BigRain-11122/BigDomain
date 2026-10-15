"""Acceptance suite: stats_board_dual cross-restart persistence
example window (BigDomain R1990; canon = explore-queue
stats_board-dual persist line, the R1989-reseed consume-1/reseed-1
head). The dual board (R1989) is a pure-derived read face over
showcase.db (single derivation source: exactly one stats_board()
call; capped zone = tail-window slice of the same decisive
order). Its derived purity across a full-stack instance restart
had no pinned example (persist family judgment reference
R1889/R1900/R1902; test_showcase_persist.py pins the three read
faces, the R1987 sibling pinned stats_board alone).

Asserts the pre-registered criteria AC-SSDP1..AC-SSDP7 from the
R1990 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(three, registered at claim time):
1. restart carrier = the full stack: ShowcaseFace close ->
   Ledger close, then a fresh Ledger (same db_path, same cfg
   bytes) + stateless SecGate + ShowcaseFace (same sh_path)
   reopen - the ledger dock reconnect is proven too.
2. world = the R1989 sibling shape (five showcases registered in
   mixed order, six collectibles, cross-window place/retract
   chain; decisive board order beta/gamma/alpha/omega/delta);
   no frozen clock is needed because the board rows carry no
   timestamps (the world writes do, the board output does not).
3. comparison face = dumps(sort_keys=True) byte equality on the
   dual read family at caps {1, 2, 50} plus the default full
   board; continuation faces prove the zones recompute from the
   disk state alone after the restart (zero cache).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_showcase_statsdualpersist.py
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

import ledger as L                     # noqa: E402 (P-47-2b core)
import collectibles as C               # noqa: E402 (owner face)
import showcase as S                   # noqa: E402 (face under test)
from sec_gate import SecGate           # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase dual"
              " board is a display feature, not investment"
              " advice")

DUAL_KEYS = {"full_board", "capped_board", "window", "disclaimer"}
WINDOW_KEYS = {"limit", "total", "returned", "truncated"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places", "retracts",
            "displayed_now"}

WANT_ORDER = ["beta-win", "gamma-win", "alpha-win",
              "omega-win", "delta-win"]

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


def dual_family(sh):
    """The enumerated dual read family: caps 1/2/50 serialized."""
    return {"d1": dumps(sh.stats_board_dual(1)),
            "d2": dumps(sh.stats_board_dual(2)),
            "d50": dumps(sh.stats_board_dual(50))}


def full_ids(sh):
    return [r["showcase_id"]
            for r in sh.stats_board_dual(2)["full_board"]]


def capped_ids(sh, cap):
    return [r["showcase_id"]
            for r in sh.stats_board_dual(cap)["capped_board"]]


def mirror_tail(sh_path, limit):
    """Mirror-SQL third path (R1729/R1988/R1989 mirror law): the
    ascending decisive key is (-places, -retracts,
    showcase_id), so the tail-N rows are fetched by the fully
    reversed key, taking N, then reversed back."""
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


def netflow_ok(board):
    return all(r["displayed_now"] == r["places"] - r["retracts"]
               for r in board["full_board"])


def table_counts(shconn, ledconn):
    return {"showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
            "collectibles": int(ledconn.execute(
                "SELECT COUNT(*) FROM collectibles").fetchone()[0])}


def build_world(led, cf, sh):
    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    cl = {}
    for who, ev, item in (
            ("alice", "evt-tower", "tower-cert"),
            ("bob", "evt-bridge", "bridge-cert"),
            ("carol", "evt-harbor", "harbor-cert"),
            ("dave", "evt-lamp", "lamp-cert"),
            ("alice", "evt-bell", "bell-cert"),
            ("alice", "evt-gate", "gate-cert")):
        cl[item] = cf.issue_certificate(
            "usr:" + who, ev, item)["cl_id"]
    sh.register_showcase("omega-win", "Omega Window", 3, False)
    sh.register_showcase("delta-win", "Delta Window", 3, True)
    sh.register_showcase("gamma-win", "Gamma Window", 3, False)
    sh.register_showcase("beta-win", "Beta Window", 3, True)
    sh.register_showcase("alpha-win", "Alpha Window", 3, False)
    sh.place_exhibit("usr:alice", "alpha-win", cl["tower-cert"],
                     "", False)
    sh.retract_exhibit("usr:alice", "alpha-win", cl["tower-cert"])
    sh.place_exhibit("usr:alice", "omega-win", cl["tower-cert"],
                     "", False)
    for _ in range(2):
        sh.place_exhibit("usr:bob", "beta-win", cl["bridge-cert"],
                         "", False)
        sh.retract_exhibit("usr:bob", "beta-win", cl["bridge-cert"])
    sh.place_exhibit("usr:bob", "beta-win", cl["bridge-cert"],
                     "", False)
    for _ in range(2):
        sh.place_exhibit("usr:carol", "gamma-win",
                         cl["harbor-cert"], "", False)
        sh.retract_exhibit("usr:carol", "gamma-win",
                           cl["harbor-cert"])
    sh.place_exhibit("usr:carol", "gamma-win", cl["harbor-cert"],
                     "", False)
    sh.place_exhibit("usr:dave", "alpha-win", cl["lamp-cert"],
                     "", False)
    sh.place_exhibit("usr:alice", "alpha-win", cl["bell-cert"],
                     "", False)
    return cl


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="showcase-statsdualpersist-")
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
        cl = build_world(led, cf, sh)
        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-SSDP1 world + pre-close dual family --------------
        fam = dual_family(sh)
        d2 = json.loads(fam["d2"])
        d50 = json.loads(fam["d50"])
        d1 = json.loads(fam["d1"])
        full_direct = sh.stats_board()["showcase_stats_board"]
        ok_env = (set(d2.keys()) == DUAL_KEYS
                  and set(d2["window"].keys()) == WINDOW_KEYS)
        ok_rows = all(set(r.keys()) == ROW_KEYS
                      for r in d2["full_board"])
        ok_full = (d2["full_board"] == full_direct
                   and [r["showcase_id"]
                        for r in d2["full_board"]] == WANT_ORDER)
        ok_cap = all(
            json.loads(fam["d%d" % c])["capped_board"]
            == json.loads(fam["d%d" % c])["full_board"][-c:]
            for c in (1, 2, 50))
        mirror = mirror_tail(sh_path, 2)
        ok_mirror = ([r["showcase_id"]
                      for r in d2["capped_board"]] == mirror)
        ok_total = (d2["window"]["total"] == 5
                    and d50["window"]["truncated"] is False
                    and d50["window"]["returned"] == 5
                    and d1["window"]["truncated"] is True
                    and [r["showcase_id"]
                         for r in d1["capped_board"]]
                    == [WANT_ORDER[-1]])
        record("AC-SSDP1",
               ok_env and ok_rows and ok_full and ok_cap
               and ok_mirror and ok_total,
               "dual family {1,2,50}: envelope keys=%s row keys=%s"
               " full==direct byte-identical=%s order=%s capped=="
               "tail slices=%s mirror==capped(2)=%s window honest"
               " (total 5, d50 full, d1 truncated tail delta)=%s"
               % (ok_env, ok_rows,
                  json.dumps(d2["full_board"], sort_keys=True)
                  == json.dumps(full_direct, sort_keys=True),
                  [r["showcase_id"] for r in d2["full_board"]],
                  ok_cap, mirror == [r["showcase_id"]
                                     for r in d2["capped_board"]],
                  ok_total))

        # -- AC-SSDP2 cross-restart byte identity -----------------
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam2 = dual_family(sh2)
        double2 = (dumps(sh2.stats_board_dual(2)) == fam2["d2"]
                   and dumps(sh2.stats_board_dual(1)) == fam2["d1"])
        record("AC-SSDP2", fam2 == fam and double2,
               "full-stack close (sh -> led) then rebuild on same"
               " paths + same cfg bytes: dual family {1,2,50}"
               " byte-identical=%s double-read self-stable=%s"
               % (fam2 == fam, double2))

        # -- AC-SSDP3 post-restart new registration --------------
        old_rows = {r["showcase_id"]: dumps(r)
                    for r in json.loads(fam2["d2"])["full_board"]}
        sh2.register_showcase("zeta-win", "Zeta Window", 3, False)
        ids3 = full_ids(sh2)
        d2_3 = sh2.stats_board_dual(2)
        frozen3 = all(
            dumps(next(r for r in d2_3["full_board"]
                       if r["showcase_id"] == sid))
            == old_rows[sid]
            for sid in WANT_ORDER)
        zeta_row = next(r for r in d2_3["full_board"]
                       if r["showcase_id"] == "zeta-win")
        record("AC-SSDP3",
               ids3 == WANT_ORDER + ["zeta-win"]
               and d2_3["window"]["total"] == 6
               and [r["showcase_id"]
                    for r in d2_3["capped_board"]]
               == ["delta-win", "zeta-win"]
               and zeta_row["places"] == 0
               and zeta_row["retracts"] == 0
               and zeta_row["displayed_now"] == 0
               and frozen3,
               "post-restart registration: full zone 5->6 %s,"
               " zero-event zeta row honest zeros=%s, window"
               " total 5->6=%s, capped(2) tail slid"
               " [omega,delta]->[delta,zeta]=%s, five old rows"
               " byte-frozen=%s"
               % (ids3 == WANT_ORDER + ["zeta-win"],
                  zeta_row["places"] == 0
                  and zeta_row["displayed_now"] == 0,
                  d2_3["window"]["total"] == 6,
                  [r["showcase_id"]
                   for r in d2_3["capped_board"]]
                  == ["delta-win", "zeta-win"], frozen3))

        # -- AC-SSDP4 post-restart new place/retract --------------
        pre4 = {r["showcase_id"]: dumps(r)
                for r in sh2.stats_board_dual(2)["full_board"]}
        sh2.retract_exhibit("usr:dave", "alpha-win",
                            cl["lamp-cert"])
        sh2.place_exhibit("usr:dave", "delta-win",
                          cl["lamp-cert"], "lamp glow two")
        d2_4 = sh2.stats_board_dual(2)
        ids4 = [r["showcase_id"] for r in d2_4["full_board"]]
        alpha4 = next(r for r in d2_4["full_board"]
                      if r["showcase_id"] == "alpha-win")
        frozen4 = all(
            dumps(next(r for r in d2_4["full_board"]
                       if r["showcase_id"] == sid)) == pre4[sid]
            for sid in ("beta-win", "gamma-win", "omega-win"))
        record("AC-SSDP4",
               ids4 == ["alpha-win", "beta-win", "gamma-win",
                        "delta-win", "omega-win", "zeta-win"]
               and alpha4["places"] == 3
               and alpha4["retracts"] == 2
               and alpha4["displayed_now"] == 1
               and netflow_ok(d2_4)
               and frozen4
               and d2_4["window"]["total"] == 6
               and [r["showcase_id"]
                    for r in d2_4["capped_board"]]
               == ["omega-win", "zeta-win"],
               "post-restart activity: zero-cache recompute"
               " order moved alpha first=%s alpha {p3,r2,dn1}=%s"
               " netflow identity all rows=%s untouched rows"
               " frozen=%s capped(2) tail [omega,zeta]=%s"
               % (ids4[:3] == ["alpha-win", "beta-win",
                               "gamma-win"],
                  alpha4["places"] == 3
                  and alpha4["retracts"] == 2
                  and alpha4["displayed_now"] == 1,
                  netflow_ok(d2_4), frozen4,
                  [r["showcase_id"]
                   for r in d2_4["capped_board"]]
                  == ["omega-win", "zeta-win"]))

        # -- AC-SSDP5 third instance stability --------------------
        fam_final = dual_family(sh2)
        counts5 = table_counts(shconn, ledconn)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam3 = dual_family(sh3)
        seq3 = (dumps(sh3.stats_board_dual(2)) == fam3["d2"]
                and dumps(sh3.stats_board_dual(1)) == fam3["d1"])
        counts5b = table_counts(shconn, ledconn)
        record("AC-SSDP5",
               fam3 == fam_final and seq3
               and counts5 == counts5b,
               "third instance == second-instance final state"
               " byte-identical=%s sequential double-read=%s"
               " counts flat=%s"
               % (fam3 == fam_final, seq3, counts5 == counts5b))

        # -- AC-SSDP6 pure-read law + single source ---------------
        counts6a = table_counts(shconn, ledconn)
        battery_a = [dumps(sh3.stats_board_dual(1)),
                     dumps(sh3.stats_board_dual(2)),
                     dumps(sh3.stats_board_dual(50)),
                     dumps(sh3.stats_board())]
        battery_b = [dumps(sh3.stats_board_dual(1)),
                     dumps(sh3.stats_board_dual(2)),
                     dumps(sh3.stats_board_dual(50)),
                     dumps(sh3.stats_board())]
        counts6b = table_counts(shconn, ledconn)
        method_src = inspect.getsource(
            S.ShowcaseFace.stats_board_dual)
        write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                                  "CREATE ", "ALTER ", "SELECT")
                      if w in method_src]
        source_calls = method_src.count("self.stats_board()")
        ok6 = (counts6a == counts6b and battery_a == battery_b
               and not write_hits and source_calls == 1
               and "random" not in method_src)
        record("AC-SSDP6", ok6,
               "read battery (dual 1/2/50 + default, twice)"
               " leaves counts unchanged %s == %s, repeat pairs"
               " byte-identical, dual method source zero SQL"
               " zero writes (%s) zero RNG, exactly ONE"
               " stats_board() call (%d)"
               % (counts6a, counts6b, write_hits, source_calls))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # -- AC-SSDP7 hygiene -------------------------------------
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith(
                    "from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-showcase-statsdual-persist" in reg_src
                  and "test_showcase_statsdualpersist.py"
                  in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        outside = tmp not in os.path.abspath(BASE)
        hyg = {"ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok,
               "outside": outside}
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
    record("AC-SSDP7",
           hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and hyg.get("outside") and sha_ok,
           "suite pure ASCII=%s net-clean=%s registry-wired=%s"
           " world outside repo=%s product-sha stable=%s"
           % (hyg.get("ascii_ok"), hyg.get("net_ok"),
              hyg.get("reg_ok"), hyg.get("outside"), sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
