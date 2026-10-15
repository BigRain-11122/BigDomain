"""Acceptance suite: the per-showcase exhibit statistics board
(stats_board, AC-SSB1..AC-SSB7 R1983) across a full-stack instance
restart (BigDomain R1987 explore-queue claim; seed = the R1983
stats board + the R1983-closing reseed; family law = the
R1889..R1976 persist example windows - test_showcase.py is
single-instance, test_showcase_stats.py pins the board itself,
test_showcase_persist.py (R1925, AC-SHVP1..7) pins the
view/chronicle/tour faces only, so the board's derived purity
across a restart had no pinned example).

Asserts the pre-registered criteria AC-SSBP1..AC-SSBP7 from the
R1987 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Restart carrier (R1925 family ruling, reused): ShowcaseFace close
-> Ledger close, then a fresh Ledger (same db_path, same cfg
bytes) + a stateless SecGate + a fresh ShowcaseFace (same
sh_path) - the ledger dock reconnect is proven too.

No clock patch: the board rows carry no time-derived fields
(showcase_id / title / ai_label / places / retracts /
displayed_now), so the board bytes are naturally deterministic;
the suite asserts S._now_utc stays the pristine original function
object for the whole run (AC-SSBP7).

Suite-only round: zero product bytes change (product sha in/out
asserted in AC-SSBP7). This source stays pure ASCII per the
encoding discipline.

Usage: python test_stats_board_persist.py
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
import collectibles as C              # noqa: E402 (owner face)
import showcase as S                   # noqa: E402 (face under test)
from sec_gate import SecGate           # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []
SUITE_LABEL = "ledger-statsboard-persist"

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase stats"
              " board is a display feature, not investment advice")

PRODUCT_FILES = [
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ENV_KEYS = {"showcase_stats_board", "disclaimer"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places",
            "retracts", "displayed_now"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def rowmap(board):
    return {r["showcase_id"]: r
            for r in board["showcase_stats_board"]}


def order_of(board):
    return [r["showcase_id"]
            for r in board["showcase_stats_board"]]


def net_ok(board):
    return all(r["displayed_now"] == r["places"] - r["retracts"]
               for r in board["showcase_stats_board"])


def sql_counts(shconn):
    out = {}
    for sid, action, n in shconn.execute(
            "SELECT showcase_id, action, COUNT(*) FROM"
            " exhibit_events GROUP BY showcase_id,"
            " action").fetchall():
        slot = out.setdefault(str(sid), {"place": 0, "retract": 0})
        slot[str(action)] = int(n)
    return out


def sql_dnow(shconn):
    out = {}
    for sid, n in shconn.execute(
            "SELECT showcase_id, COUNT(*) FROM exhibit_events"
            " WHERE event_id IN (SELECT MAX(event_id) FROM"
            " exhibit_events GROUP BY cl_id)"
            " AND action = 'place' GROUP BY"
            " showcase_id").fetchall():
        out[str(sid)] = int(n)
    return out


def table_counts(shconn, ledconn):
    return {
        "showcases": int(shconn.execute(
            "SELECT COUNT(*) FROM showcases").fetchone()[0]),
        "exhibit_events": int(shconn.execute(
            "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
        "collectibles": int(ledconn.execute(
            "SELECT COUNT(*) FROM collectibles").fetchone()[0]),
    }


def main():
    orig_now = S._now_utc
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="statsboard-persist-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    fresh_path = os.path.join(tmp, "showcase-fresh.db")

    led = sh = led2 = sh2 = led3 = sh3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        fresh = S.ShowcaseFace(led, gate, DISCLAIMER, fresh_path)

        # world: four avatars + six certificates
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        specs = (
            ("a", "usr:alice", "evt-tower", "tower-cert"),
            ("b", "usr:bob", "evt-bridge", "bridge-cert"),
            ("c", "usr:carol", "evt-harbor", "harbor-cert"),
            ("d", "usr:dave", "evt-lamp", "lamp-cert"),
            ("e", "usr:alice", "evt-bell", "bell-cert"),
            ("f", "usr:alice", "evt-gate", "gate-cert"),
        )
        cl = {k: cf.issue_certificate(acct, ev, kind)["cl_id"]
              for k, acct, ev, kind in specs}

        # registration order deliberately mixed
        sh.register_showcase("omega-win", "Omega Window", 3, False)
        sh.register_showcase("delta-win", "Delta Window", 3, True)
        sh.register_showcase("gamma-win", "Gamma Window", 3, False)
        sh.register_showcase("beta-win", "Beta Window", 3, True)
        sh.register_showcase("alpha-win", "Alpha Window", 3, False)

        # events: cross-window re-place + pair churn + trailing
        # places; cl_f stays unplaced (post-restart carrier item)
        sh.place_exhibit("usr:alice", "alpha-win", cl["a"], "",
                        False)
        sh.retract_exhibit("usr:alice", "alpha-win", cl["a"])
        sh.place_exhibit("usr:alice", "omega-win", cl["a"], "",
                        False)
        for _ in range(2):
            sh.place_exhibit("usr:bob", "beta-win", cl["b"], "",
                             False)
            sh.retract_exhibit("usr:bob", "beta-win", cl["b"])
        sh.place_exhibit("usr:bob", "beta-win", cl["b"], "", False)
        for _ in range(2):
            sh.place_exhibit("usr:carol", "gamma-win", cl["c"], "",
                             False)
            sh.retract_exhibit("usr:carol", "gamma-win", cl["c"])
        sh.place_exhibit("usr:carol", "gamma-win", cl["c"], "",
                         False)
        sh.place_exhibit("usr:dave", "alpha-win", cl["d"], "",
                         False)
        sh.place_exhibit("usr:alice", "alpha-win", cl["e"], "",
                         False)

        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # ---- AC-SSBP1: world + pre-close snapshot --------------
        empty = fresh.stats_board()
        board = sh.stats_board()
        s0 = dumps(board)
        rows = rowmap(board)
        sc, sd = sql_counts(shconn), sql_dnow(shconn)
        cross = []
        for sid, r in rows.items():
            slot = sc.get(sid, {"place": 0, "retract": 0})
            cross.append(
                r["places"] == slot["place"]
                and r["retracts"] == slot["retract"]
                and r["displayed_now"] == sd.get(sid, 0))
        order = order_of(board)
        ok1 = (
            set(empty.keys()) == ENV_KEYS
            and empty["showcase_stats_board"] == []
            and empty["disclaimer"] == DISCLAIMER
            and set(board.keys()) == ENV_KEYS
            and board["disclaimer"] == DISCLAIMER
            and len(board["showcase_stats_board"]) == 5
            and all(set(r.keys()) == ROW_KEYS
                    for r in board["showcase_stats_board"])
            and all(cross) and len(cross) == 5
            and net_ok(board)
            and order == ["beta-win", "gamma-win", "alpha-win",
                          "omega-win", "delta-win"]
            and rows["delta-win"] == {
                "showcase_id": "delta-win", "title": "Delta Window",
                "ai_label": 1, "places": 0, "retracts": 0,
                "displayed_now": 0}
            and rows["alpha-win"]["places"] == 3
            and rows["alpha-win"]["retracts"] == 1
            and rows["alpha-win"]["displayed_now"] == 2
            and rows["beta-win"]["places"] == 3
            and rows["beta-win"]["retracts"] == 2
            and rows["beta-win"]["displayed_now"] == 1
            and dumps(sh.stats_board()) == s0)
        record("AC-SSBP1", ok1,
               "fresh zero-registration face returns the honest"
               " empty board; pre-close board %d rows == 5"
               " registered showcases, keys exact, manual-SQL"
               " cross=%d/5, net identity holds, order=%s, delta"
               " honest zeros, double-read byte-stable"
               % (len(board["showcase_stats_board"]),
                  sum(1 for c in cross if c), order))

        # ---- AC-SSBP2: cross-restart byte identity (core) -------
        fresh.close()
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        b2 = sh2.stats_board()
        again = dumps(sh2.stats_board())
        ok2 = (dumps(b2) == s0 and again == s0
               and dumps(b2) == again)
        record("AC-SSBP2", ok2,
               "full-stack close (sh -> led) then rebuild on the"
               " same paths: board byte-identical=%s re-read"
               " self=%s (registry rows + event counts re-derived"
               " from disk, zero in-memory cache)"
               % (dumps(b2) == s0, again == s0))

        # ---- AC-SSBP3: post-restart recompute, zero cache ------
        pre_rows = rowmap(json.loads(s0))
        sh2.place_exhibit("usr:alice", "delta-win", cl["f"], "",
                          False)
        b3a = rowmap(sh2.stats_board())
        sh2.retract_exhibit("usr:alice", "delta-win", cl["f"])
        b3b = sh2.stats_board()
        r3 = rowmap(b3b)
        frozen = all(
            dumps(r3[sid]) == dumps(pre_rows[sid])
            for sid in ("alpha-win", "beta-win", "gamma-win",
                        "omega-win"))
        ok3 = (
            b3a["delta-win"]["places"] == 1
            and b3a["delta-win"]["retracts"] == 0
            and b3a["delta-win"]["displayed_now"] == 1
            and r3["delta-win"]["places"] == 1
            and r3["delta-win"]["retracts"] == 1
            and r3["delta-win"]["displayed_now"] == 0
            and r3["delta-win"]["displayed_now"]
            == r3["delta-win"]["places"]
            - r3["delta-win"]["retracts"]
            and net_ok(b3b)
            and frozen)
        record("AC-SSBP3", ok3,
               "live place moves the zero-event row 0->1 (places"
               " and displayed_now), live retract moves retracts"
               " 0->1 and displayed_now back to 0; untouched rows"
               " byte-frozen=%s; net identity holds on every row"
               % frozen)

        # ---- AC-SSBP4: continuation + cross-face reconcile ------
        sh2.place_exhibit("usr:alice", "alpha-win", cl["f"], "",
                          False)
        b4 = sh2.stats_board()
        r4 = rowmap(b4)
        order4 = order_of(b4)
        face_ok = []
        for sid in ("alpha-win", "beta-win", "gamma-win",
                    "delta-win", "omega-win"):
            view = sh2.showcase_view(sid)
            face_ok.append(
                r4[sid]["displayed_now"] == len(view["displayed"])
                and all(x["cl_id"] != cl["f"]
                        for x in view["displayed"])
                == (sid != "alpha-win"))
        ok4 = (
            r4["alpha-win"]["places"] == 4
            and r4["alpha-win"]["retracts"] == 1
            and r4["alpha-win"]["displayed_now"] == 3
            and r4["delta-win"]["places"] == 1
            and r4["delta-win"]["retracts"] == 1
            and r4["delta-win"]["displayed_now"] == 0
            and order4 == ["alpha-win", "beta-win", "gamma-win",
                           "delta-win", "omega-win"]
            and net_ok(b4)
            and all(face_ok) and len(face_ok) == 5)
        record("AC-SSBP4", ok4,
               "cross-window re-place continues the board (alpha"
               " 4/1/3, delta stays 1/1/0); every row reconciles"
               " with showcase_view displayed lengths=%s;"
               " reordered board keeps the decisive order=%s"
               % (all(face_ok), order4))

        # ---- AC-SSBP5: third instance, dual live, sequential ---
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        s4 = dumps(b4)
        b5_3 = sh3.stats_board()
        b5_2r = sh2.stats_board()
        b5_3r = sh3.stats_board()
        counts_pre = table_counts(shconn, ledconn)
        for sid in ("alpha-win", "beta-win", "gamma-win",
                    "delta-win", "omega-win"):
            sh3.showcase_view(sid)
        counts_post = table_counts(shconn, ledconn)
        ok5 = (dumps(b5_3) == s4
               and dumps(b5_2r) == s4
               and dumps(b5_3r) == s4
               and counts_pre == counts_post)
        record("AC-SSBP5", ok5,
               "third instance (two live faces) board"
               " byte-identical=%s; sequential re-reads"
               " stable=%s; read battery left table counts"
               " constant=%s"
               % (dumps(b5_3) == s4,
                  dumps(b5_2r) == s4 and dumps(b5_3r) == s4,
                  counts_pre == counts_post))

        # ---- AC-SSBP6: pure-read law ----------------------------
        method_src = inspect.getsource(
            S.ShowcaseFace.stats_board)
        write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                                  "CREATE ", "ALTER ")
                      if w in method_src]
        counts_a = table_counts(shconn, ledconn)
        battery = [dumps(sh3.stats_board()),
                   dumps(sh2.stats_board())]
        battery += [dumps(sh3.showcase_view(s))
                    for s in ("alpha-win", "beta-win",
                              "gamma-win", "delta-win",
                              "omega-win")]
        battery += [dumps(sh3.stats_board())]
        counts_b = table_counts(shconn, ledconn)
        ok6 = (not write_hits
               and counts_a == counts_b
               and battery[0] == battery[-1]
               and battery[0] == s4)
        record("AC-SSBP6", ok6,
               "stats_board method source has zero write"
               " statements (%s); read battery left"
               " showcases/exhibit_events/collectibles counts"
               " constant %s == %s; repeat-read pair"
               " byte-identical=%s"
               % (write_hits, counts_a, counts_b,
                  battery[0] == battery[-1]))

        sh3.close()
        led3.close()
        sh3 = led3 = None

        # ---- AC-SSBP7: hygiene ----------------------------------
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_clean = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or \
                    stripped.startswith("from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_clean = False
        post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
        reg_ok = (SUITE_LABEL in reg_src
                  and "test_stats_board_persist.py" in reg_src)
        repo_root = os.path.abspath(
            os.path.join(BASE, "..", "..", ".."))
        outside = (os.path.isabs(tmp)
                   and not os.path.abspath(
                       tmp).startswith(repo_root + os.sep))
        clock_ok = (S._now_utc is orig_now)
        ok7 = (ascii_ok and net_clean and pre_sha == post_sha
               and reg_ok and outside and clock_ok
               and len(RESULTS) == EXPECTED - 1)
        record("AC-SSBP7", ok7,
               "suite ascii=%s net-clean=%s product-sha-stable=%s"
               " runner-registered=%s world-outside-repo=%s"
               " clock-pristine=%s (no clock patch: board rows"
               " carry no time-derived fields) expected=%d"
               % (ascii_ok, net_clean, pre_sha == post_sha, reg_ok,
                  outside, clock_ok, EXPECTED))

        sh2.close()
        led2.close()
        sh2 = led2 = None
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
        try:
            cf.close()
        except Exception:
            pass

    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total
                              == EXPECTED else "FAIL",
                              passed, EXPECTED), flush=True)
    return 0 if passed == total == EXPECTED else 2


if __name__ == "__main__":
    sys.exit(main())
