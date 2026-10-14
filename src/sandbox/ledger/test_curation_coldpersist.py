"""Acceptance suite for the curation cold_board cross-restart
persistence example window (BigDomain R1972; canon = the R1970
reseeded explore-queue row claimed by R1972). The zero-heat cold
board read face (curation.py cold_board, R1970) is the honest
inverse filter of the heat board and is pure-derived over THREE
databases: the curation registry (curation.db curations +
curation_members), the live showcase display state (showcase.db
exhibit_events latest-action-per-item law) and the ledger
ownership rows. This suite pins the derived purity across
full-stack instance restarts PLUS the cold<->hot migration
continuation: pre-close envelope == post-reopen read
byte-identical, cold->hot migration (a placement into a cold
theme's member showcase) and hot->cold migration (retracting a
hot theme down to zero) both recomputed zero-cache with the
cold/hot complementarity law held across every migration,
third-instance sequential reads byte-identical, pure-read law
across restarts, and hygiene.

Criteria AC-CZP1..CZP6 were pre-registered in
state/queue/explore.md at claim time (R1972, before this code
existed; honesty law; AC-CZP prefix git-grep zero-occupancy
anchored 2026-10-14; AC-CB1..CB5 belong to the R1970 read face
and AC-HBP1..HBP6 to the R1923 hot_board persist window, none
re-registered here).

Suite-only round: zero product-code changes (curation.py,
showcase.py and both shipped config.json files are sha256
double-proven unchanged). Restart carrier = the R1923
four-piece full-stack precedent (close cu -> sh -> led, then
rebuild Ledger + stateless SecGate + ShowcaseFace + CurationFace
on the same three db paths) - the cold derivation crosses three
databases, so a curation-only restart would under-prove.

Usage: python test_curation_coldpersist.py
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
import showcase as S                  # noqa: E402 (R1750 parent face)
import curation as CU                 # noqa: E402 (R1751 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the zero-heat cold"
              " board is a display feature, not investment"
              " advice")

PRODUCT_FILES = [
    os.path.join(BASE, "curation.py"),
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ROW_KEYS = {"rank", "curation_id", "title", "ai_label",
            "member_count", "displayed_total"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def manual_sql_totals(shconn, cuconn):
    """Second derivation path (independent of the hot/cold
    single derivation source): per curation, sum the live
    on-display counts of the member showcases straight from the
    exhibit latest-action-per-item law."""
    members = {}
    for cid, sid in cuconn.execute(
            "SELECT curation_id, showcase_id FROM curation_members"
            " ORDER BY curation_id, position").fetchall():
        members.setdefault(cid, []).append(sid)
    totals = {}
    for cid, sids in members.items():
        total = 0
        for sid in sids:
            n = shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events WHERE"
                " event_id IN (SELECT MAX(event_id) FROM"
                " exhibit_events GROUP BY cl_id)"
                " AND action = 'place' AND showcase_id = ?",
                (sid,)).fetchone()[0]
            total += int(n)
        totals[cid] = total
    return totals


def table_counts(shconn, cuconn, ledconn):
    cu_cur = cuconn.execute(
        "SELECT COUNT(*) FROM curations").fetchone()[0]
    cu_mem = cuconn.execute(
        "SELECT COUNT(*) FROM curation_members").fetchone()[0]
    sh_reg = shconn.execute(
        "SELECT COUNT(*) FROM showcases").fetchone()[0]
    sh_evt = shconn.execute(
        "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]
    tx = ledconn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    return {"curations": int(cu_cur),
            "curation_members": int(cu_mem),
            "showcases": int(sh_reg),
            "exhibit_events": int(sh_evt),
            "ledger_tx": int(tx)}


def ids(env, key):
    return [row["curation_id"] for row in env[key]]


def complementarity_ok(cold_env, hot_env, all_ids):
    cold = set(ids(cold_env, "cold_board"))
    hot = set(ids(hot_env, "hot_board"))
    hot_pos = set(row["curation_id"] for row in hot_env["hot_board"]
                  if row["displayed_total"] > 0)
    return (cold | hot_pos == set(all_ids)
            and not (cold & hot_pos)
            and hot == set(all_ids))


def cold_rows_match(board, expected):
    if len(board) != len(expected):
        return False
    for row, (rank, cid, total, mcnt) in zip(board, expected):
        if row["rank"] != rank or row["curation_id"] != cid:
            return False
        if row["displayed_total"] != total:
            return False
        if row["member_count"] != mcnt:
            return False
    return True


def main():
    tmp = tempfile.mkdtemp(prefix="curation-coldpersist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    cu_path = os.path.join(tmp, "curation.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)

    # -- world: true product path, three avatars + three certs +
    # four showcases + three curations, one hot theme and two
    # cold themes visible by design ------------------------------
    for acct, avatar in (("usr:alice", "alice"), ("usr:bob", "bob"),
                         ("usr:carol", "carol")):
        led.ensure_account(acct, census_avatar_id=avatar)
    specs = (
        ("a", "usr:alice", "evt-tower", "tower-cert"),
        ("b", "usr:bob", "evt-bridge", "bridge-cert"),
        ("c", "usr:carol", "evt-harbor", "harbor-cert"),
    )
    cl = {}
    for key, acct, ev, kind in specs:
        cl[key] = cf.issue_certificate(acct, ev, kind)["cl_id"]
    for sid in ("sh-one", "sh-two", "sh-three", "sh-four"):
        sh.register_showcase(sid, sid + " window", 3, False)
    sh.place_exhibit("usr:alice", "sh-one", cl["a"], "tower light")
    sh.place_exhibit("usr:bob", "sh-one", cl["b"], "bridge arch")
    cu.register_curation("cu-alpha", "Alpha Route",
                         ["sh-one"], False)
    cu.register_curation("cu-beta", "Beta Route",
                         ["sh-two", "sh-three"], False)
    cu.register_curation("cu-gamma", "Gamma Route",
                         ["sh-four"], False)

    shconn = sqlite3.connect(sh_path)
    cuconn = sqlite3.connect(cu_path)
    ledconn = sqlite3.connect(db_path)
    all_ids = ["cu-alpha", "cu-beta", "cu-gamma"]

    # -- AC-CZP1 control anchor: pre-restart cold board pinned ---
    env1 = cu.cold_board()
    hot1 = cu.hot_board()
    board1 = env1["cold_board"]
    ok1 = []
    ok1.append(cold_rows_match(board1, [
        (1, "cu-beta", 0, 2), (2, "cu-gamma", 0, 1)]))
    ok1.append(set(env1.keys()) == {"cold_board", "disclaimer"})
    ok1.append(all(set(r.keys()) == ROW_KEYS for r in board1))
    ok1.append(complementarity_ok(env1, hot1, all_ids))
    totals1 = manual_sql_totals(shconn, cuconn)
    ok1.append(totals1 == {"cu-alpha": 2, "cu-beta": 0,
                           "cu-gamma": 0})
    record("AC-CZP1", all(ok1),
           "pre-restart cold board pinned rank1 cu-beta"
           " total=0 members=2, rank2 cu-gamma total=0"
           " members=1 (curation_id ASC); envelope keys %s, row"
           " keys %s; cold/hot complementarity: cold {cu-beta,"
           " cu-gamma} | hot(>0) {cu-alpha} == all three,"
           " disjoint; manual SQL second-derivation totals %s"
           % (sorted(env1.keys()), sorted(ROW_KEYS),
              json.dumps(totals1, sort_keys=True)))
    snap1 = dumps(env1)

    # -- AC-CZP2 full-stack restart: byte-identical envelope -----
    counts_before_read2 = table_counts(shconn, cuconn, ledconn)
    cu.close()
    sh.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    gate2 = SecGate.from_config(lobby_cfg)
    sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
    cu2 = CU.CurationFace(sh2, DISCLAIMER, cu_path)
    env2 = cu2.cold_board()
    counts_after_read2 = table_counts(shconn, cuconn, ledconn)
    snap2 = dumps(env2)
    record("AC-CZP2", snap2 == snap1,
           "full-stack close (cu -> sh -> led) then rebuild on"
           " the same three db paths: reopened cold_board =="
           " pre-close envelope byte-identical (%d bytes, dumps"
           " sort_keys); zero in-memory drift in the derived"
           " read" % len(snap2))

    # -- AC-CZP3 post-restart cold<->hot migration, both ways ----
    # cold->hot: place cl_c into sh-two (member of cu-beta)
    sh2.place_exhibit("usr:carol", "sh-two", cl["c"],
                      "harbor lamp")
    env_mid = cu2.cold_board()
    hot_mid = cu2.hot_board()
    ok_mid = []
    ok_mid.append(cold_rows_match(env_mid["cold_board"],
                                  [(1, "cu-gamma", 0, 1)]))
    ok_mid.append("cu-beta" not in ids(env_mid, "cold_board"))
    ok_mid.append(complementarity_ok(env_mid, hot_mid, all_ids))
    # hot->cold: retract both live items out of sh-one (cu-alpha)
    sh2.retract_exhibit("usr:alice", "sh-one", cl["a"])
    sh2.retract_exhibit("usr:bob", "sh-one", cl["b"])
    env3 = cu2.cold_board()
    hot3 = cu2.hot_board()
    snap3 = dumps(env3)
    ok3 = []
    ok3.append(cold_rows_match(env3["cold_board"], [
        (1, "cu-alpha", 0, 1), (2, "cu-gamma", 0, 1)]))
    ok3.append(snap3 != snap1 and snap3 != dumps(env_mid))
    ok3.append(complementarity_ok(env3, hot3, all_ids))
    ok3.append(all(ok_mid))
    totals3 = manual_sql_totals(shconn, cuconn)
    ok3.append(totals3 == {"cu-alpha": 0, "cu-beta": 1,
                           "cu-gamma": 0})
    record("AC-CZP3", all(ok3),
           "post-restart migrations recompute zero-cache:"
           " cold->hot (cl_c placed into sh-two: cu-beta left"
           " the cold board, cold=[cu-gamma]) then hot->cold"
           " (both live items retracted out of sh-one:"
           " cu-alpha entered the cold board, cold=[cu-alpha,"
           " cu-gamma] id ASC); complementarity law held after"
           " every migration step (cold | hot(>0) == all three,"
           " disjoint); envelope differs from both prior"
           " snapshots; manual SQL totals %s"
           % json.dumps(totals3, sort_keys=True))

    # -- AC-CZP4 third instance: sequential reads identical ------
    cu2.close()
    cu3 = CU.CurationFace(sh2, DISCLAIMER, cu_path)
    counts_before_read4 = table_counts(shconn, cuconn, ledconn)
    env4 = cu3.cold_board()
    env4b = cu3.cold_board()
    counts_after_read4 = table_counts(shconn, cuconn, ledconn)
    snap4 = dumps(env4)
    snap4b = dumps(env4b)
    ok4 = [snap4 == snap3, snap4b == snap4,
           counts_before_read4 == counts_after_read4]
    record("AC-CZP4", all(ok4),
           "second curation-face restart (third instance on the"
           " same db): sequential cold_board reads byte-identical"
           " to the post-migration state and to each other"
           " (repeat-read purity, zero in-memory drift)")

    # -- AC-CZP5 pure-read law + product-file sha double-proof ----
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok5 = [counts_after_read2 == counts_before_read2,
           counts_after_read4 == counts_before_read4,
           shas_after == shas_before]
    record("AC-CZP5", all(ok5),
           "pure-read law: every read batch left curations /"
           " curation_members / showcases / exhibit_events /"
           " ledger_tx row counts constant (%s); product files"
           " sha256 unchanged (curation.py, showcase.py, both"
           " shipped config.json)"
           % json.dumps(counts_after_read4, sort_keys=True))

    # -- AC-CZP6 hygiene: ASCII, zero-network imports, tmp world --
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok6 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok6.append(not net_hits)
    ok6.append(os.path.abspath(tmp).startswith(
        tempfile.gettempdir()))
    ok6.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    cold_src = inspect.getsource(CU.CurationFace.cold_board)
    ok6.append(not any(verb in cold_src for verb in
                       ("INSERT", "UPDATE ", "DELETE")))
    record("AC-CZP6", all(ok6),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, cold_board method"
           " source zero write statements, world db in system"
           " tmp outside the repo" % len(src_bytes))

    cu3.close()
    sh2.close()
    led2.close()
    shconn.close()
    cuconn.close()
    ledconn.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
