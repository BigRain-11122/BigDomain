"""Acceptance suite for the combined hot+cold dual board read
face (BigDomain R1974; canon = explore-queue cold/hot dual-board
combined read seed row: one envelope presenting the heat board
and the cold shelf side by side - the hot/cold complementary law
made visible in a single read). Asserts the pre-registered
criteria AC-CJ1..CJ7 from the R1974 explore-queue claim note
(criteria were registered before this code existed; honesty
law). Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Usage: python test_curation_combined.py
"""

import inspect
import io
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import collectibles as C              # noqa: E402 (R619 owner face)
import showcase as S                  # noqa: E402 (R1750 parent face)
import curation as CU                 # noqa: E402 (R1751 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the combined board is a"
              " display feature, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def main():
    tmp = tempfile.mkdtemp(prefix="curation-cj-")
    with io.open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with io.open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    cu_path = os.path.join(tmp, "curation.db")

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)

    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    cl_a = cf.issue_certificate("usr:alice", "evt-tower",
                                "tower-cert")["cl_id"]
    cl_b = cf.issue_certificate("usr:bob", "evt-bridge",
                                "bridge-cert")["cl_id"]
    cl_c = cf.issue_certificate("usr:carol", "evt-harbor",
                                "harbor-cert")["cl_id"]
    sh.register_showcase("city-hall", "City Hall Window", 3, False)
    sh.register_showcase("east-wing", "East Wing Window", 3, True)
    sh.register_showcase("west-vault", "West Vault Window", 2, False)
    sh.place_exhibit("usr:alice", "city-hall", cl_a, "tower lamp")
    sh.place_exhibit("usr:bob", "city-hall", cl_b, "bridge arch")
    sh.place_exhibit("usr:carol", "east-wing", cl_c, "harbor light")

    # mixed world: two hot curations (heat 3 / heat 2) + one cold
    cu.register_curation("heritage-route", "Heritage Route",
                         ["city-hall", "east-wing"], False)
    cu.register_curation("night-market", "Night Market",
                         ["city-hall"], True)
    cu.register_curation("quiet-shelf", "Quiet Shelf",
                         ["west-vault"], False)

    import sqlite3
    conn = sqlite3.connect(db_path)
    cuconn = sqlite3.connect(cu_path)
    ledger_tx_before = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    cur_rows_before = cuconn.execute(
        "SELECT COUNT(*) FROM curations").fetchone()[0]
    mem_rows_before = cuconn.execute(
        "SELECT COUNT(*) FROM curation_members").fetchone()[0]

    # -- AC-CJ1 single-envelope contract ------------------------------
    env = cu.boards_combined()
    ok_keys = set(env.keys()) == {"hot_board", "cold_board",
                                  "totals", "disclaimer"}
    ok_tot = (set(env["totals"].keys())
              == {"hot_count", "cold_count", "total"})
    ok_vals = (env["totals"]["hot_count"] == 2
               and env["totals"]["cold_count"] == 1
               and env["totals"]["total"] == 3)
    ok_disc = env["disclaimer"] == DISCLAIMER
    ok_ai = all(row["ai_label"] in (0, 1)
                for row in env["hot_board"] + env["cold_board"])
    cu_empty = CU.CurationFace(sh, DISCLAIMER,
                               os.path.join(tmp, "curation-empty.db"))
    env_empty = cu_empty.boards_combined()
    ok_empty = (env_empty["hot_board"] == []
                and env_empty["cold_board"] == []
                and env_empty["totals"] == {"hot_count": 0,
                                            "cold_count": 0,
                                            "total": 0}
                and env_empty["disclaimer"] == DISCLAIMER)
    cu_empty.close()
    record("AC-CJ1", ok_keys and ok_tot and ok_vals and ok_disc
           and ok_ai and ok_empty,
           "envelope keys/totals/disclaimer exact, ai_label kept,"
           " mixed world 2/1/3, zero-curation world honest empty")

    # -- AC-CJ2 hot/cold complementary partition law ------------------
    full = cu.hot_board()
    full_ids = [r["curation_id"] for r in full["hot_board"]]
    hot_ids = [r["curation_id"] for r in env["hot_board"]]
    cold_ids = [r["curation_id"] for r in env["cold_board"]]
    ok_disjoint = not (set(hot_ids) & set(cold_ids))
    ok_union = set(hot_ids) | set(cold_ids) == set(full_ids)
    ok_count = (len(hot_ids) + len(cold_ids) == len(full_ids)
                == env["totals"]["total"])
    ok_heat = (all(r["displayed_total"] > 0 for r in env["hot_board"])
               and all(r["displayed_total"] == 0
                       for r in env["cold_board"]))
    ok_hot_order = hot_ids == ["heritage-route", "night-market"]
    ok_hot_rank = [r["rank"] for r in env["hot_board"]] == [1, 2]
    ok_cold_rank = ([r["rank"] for r in env["cold_board"]] == [1]
                    and cold_ids == ["quiet-shelf"])
    record("AC-CJ2", ok_disjoint and ok_union and ok_count
           and ok_heat and ok_hot_order and ok_hot_rank
           and ok_cold_rank,
           "zones disjoint, union==full board, M+K==N==3, hot"
           " order heat-DESC/id-ASC ranks 1..2, cold id-ASC rank 1")

    # -- AC-CJ3 single derivation source delegation -------------------
    hot_full_by = {r["curation_id"]: r for r in full["hot_board"]}
    ok_hot_src = all(
        all(env["hot_board"][i][k] == hot_full_by[
            env["hot_board"][i]["curation_id"]][k]
            for k in ("title", "ai_label", "member_count",
                      "displayed_total"))
        for i in range(len(env["hot_board"])))
    cold_ref = cu.cold_board()["cold_board"]
    ok_cold_src = canon(env["cold_board"]) == canon(cold_ref)
    src = inspect.getsource(CU.CurationFace.boards_combined)
    ok_no_showcase_read = "showcase_view" not in src
    record("AC-CJ3", ok_hot_src and ok_cold_src and ok_no_showcase_read,
           "hot rows key-equal to hot_board rows, cold rows"
           " byte-equal to cold_board rows, zero direct showcase"
           " reads in the combined face source")

    # -- AC-CJ4 boundary worlds --------------------------------------
    cu_all_hot = CU.CurationFace(sh, DISCLAIMER,
                                 os.path.join(tmp, "curation-allhot.db"))
    cu_all_hot.register_curation("day-tour", "Day Tour",
                                 ["city-hall"], False)
    env_all_hot = cu_all_hot.boards_combined()
    ok_all_hot = (env_all_hot["cold_board"] == []
                  and env_all_hot["totals"]["hot_count"] == 1
                  and env_all_hot["totals"]["total"] == 1
                  and [r["rank"] for r in env_all_hot["hot_board"]]
                  == [1])
    cu_all_hot.close()
    cu_all_cold = CU.CurationFace(sh, DISCLAIMER,
                                  os.path.join(tmp,
                                               "curation-allcold.db"))
    cu_all_cold.register_curation("vault-shelf", "Vault Shelf",
                                  ["west-vault"], False)
    env_all_cold = cu_all_cold.boards_combined()
    ok_all_cold = (env_all_cold["hot_board"] == []
                   and env_all_cold["totals"]["cold_count"] == 1
                   and env_all_cold["totals"]["total"] == 1
                   and [r["curation_id"]
                        for r in env_all_cold["cold_board"]]
                   == ["vault-shelf"])
    cu_all_cold.close()
    record("AC-CJ4", ok_all_hot and ok_all_cold,
           "all-hot world cold empty hot==N, zero-heat world hot"
           " empty cold==N (AC-CB mirror law)")

    # -- AC-CJ5 determinism + cross-restart derived read --------------
    snap1 = canon(cu.boards_combined())
    snap2 = canon(cu.boards_combined())
    ok_double = snap1 == snap2
    cu.close()
    sh.close()
    sh2 = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu2 = CU.CurationFace(sh2, DISCLAIMER, cu_path)
    snap3 = canon(cu2.boards_combined())
    ok_restart = snap3 == snap1
    record("AC-CJ5", ok_double and ok_restart,
           "double read byte-identical; curation+showcase faces"
           " closed and reopened over same dbs, combined read"
           " byte-identical to pre-close snapshot")

    # -- AC-CJ6 pure-read ledger/storage invariance -------------------
    ledger_tx_after = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    cur_rows_after = cuconn.execute(
        "SELECT COUNT(*) FROM curations").fetchone()[0]
    mem_rows_after = cuconn.execute(
        "SELECT COUNT(*) FROM curation_members").fetchone()[0]
    record("AC-CJ6", (ledger_tx_before == ledger_tx_after
                      and cur_rows_before == cur_rows_after
                      and mem_rows_before == mem_rows_after),
           "ledger_tx %d==%d, curations %d==%d, members %d==%d"
           " across every combined read" % (
               ledger_tx_before, ledger_tx_after,
               cur_rows_before, cur_rows_after,
               mem_rows_before, mem_rows_after))

    # -- AC-CJ7 hygiene + delivery verdict face -----------------------
    src_cj = inspect.getsource(CU.CurationFace.boards_combined)
    ok_ascii = all(ord(ch) < 128 for ch in src_cj)
    ok_no_update = "UPDATE" not in src_cj
    mod_path = CU.__file__
    mod_src = io.open(mod_path, encoding="utf-8").read()
    import_lines = [ln for ln in mod_src.splitlines()
                    if re.match(r"^(import|from)\s", ln)]
    banned = ("urllib", "requests", "socket", "http")
    ok_no_net = not any(b in ln for ln in import_lines
                        for b in banned)
    ok_prior = len(RESULTS) == 6 and all(ok for _, ok in RESULTS)
    record("AC-CJ7", ok_ascii and ok_no_update and ok_no_net
           and ok_prior,
           "combined face source pure ASCII, zero UPDATE, zero"
           " network imports (%d import lines), prior 6/6 green"
           % len(import_lines))

    conn.close()
    cuconn.close()
    cu2.close()
    sh2.close()
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d checks (%s)"
              % (len(failed), ",".join(failed)), flush=True)
        return 2
    print("SUITE PASS %d checks" % len(RESULTS), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
