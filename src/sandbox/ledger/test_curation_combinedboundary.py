"""Acceptance suite for the curation boards_combined
boundary-world cross-restart persistence example window
(BigDomain R1976; canon = the R1975-reseeded explore-queue
row claimed by R1976). The combined hot+cold dual board read
face (curation.py boards_combined, R1974) derives from ONE live
hot_board() call over THREE databases (curation registry +
live showcase display state + ledger ownership). This suite
pins the persist-family laws across the THREE boundary worlds
of the read face (AC-CJ4 boundary confluence): the
zero-curation world (honest empty both zones), the all-hot
world (cold zone empty) and the zero-hot world (hot zone
empty). Each boundary world is closed full-stack and reopened
on the same three db paths with the joint read byte-identical
to the pre-close snapshot (single derivation source, zero
in-memory drift across restarts), the world-to-world
transitions (all-hot -> zero-hot by retraction, zero-hot ->
mixed by re-placement) recompute zero-cache on the REOPENED
instances with the disjoint-union partition law and the live
hot_board() single-source cross held after every step, a
fifth-instance sequential read pair is byte-identical
(re-read purity), the pure-read law holds across every read
batch, and hygiene is machine-checked.

Criteria AC-CBW1..CBW6 were pre-registered in
state/queue/explore.md at claim time (R1976, before this code
existed; honesty law; AC-CBW prefix git-grep zero-occupancy
anchored 2026-10-15; AC-CJ1..CJ7 belong to the R1974 read
face, AC-CDP1..CDP6 to the R1975 persist window and
AC-CZP1..CZP6 to the R1972 cold_board persist window, none
re-registered here).

Suite-only round: zero product-code changes (curation.py,
showcase.py and both shipped config.json files are sha256
double-proven unchanged). Restart carrier = the R1923
four-piece full-stack precedent (close cu -> sh -> led, then
rebuild Ledger + stateless SecGate + ShowcaseFace +
CurationFace on the same three db paths) - the joint read
crosses three databases, so a curation-only restart would
under-prove.

Usage: python test_curation_combinedboundary.py
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

DISCLAIMER = ("sandbox stand-in disclaimer: the hot+cold dual"
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

ENV_KEYS = {"hot_board", "cold_board", "totals", "disclaimer"}


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
    """Second derivation path (independent of the joint read's
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


def rows_match(board, expected):
    if len(board) != len(expected):
        return False
    for row, (rank, cid, total, mcnt) in zip(board, expected):
        if row["rank"] != rank or row["curation_id"] != cid:
            return False
        if row["displayed_total"] != total:
            return False
        if row["member_count"] != mcnt:
            return False
    return False if any(set(r.keys()) != ROW_KEYS
                        for r in board) else True


def partition_law(env, all_ids):
    """Combined-zone law: the two zones are disjoint and their
    union is the full registered id set; the hot zone holds
    only heat>0 rows and the cold zone only zero-heat rows;
    the totals block agrees with the actual zone sizes."""
    hot = env["hot_board"]
    cold = env["cold_board"]
    hot_ids = set(ids(env, "hot_board"))
    cold_ids = set(ids(env, "cold_board"))
    totals = env["totals"]
    return (not (hot_ids & cold_ids)
            and hot_ids | cold_ids == set(all_ids)
            and all(r["displayed_total"] > 0 for r in hot)
            and all(r["displayed_total"] == 0 for r in cold)
            and totals["hot_count"] == len(hot)
            and totals["cold_count"] == len(cold)
            and totals["total"] == len(hot) + len(cold)
            and totals["total"] == len(all_ids))


def single_source_cross(env, live_hot_env):
    """Single-derivation-source cross: every live hot_board()
    row must sit in the matching combined zone with identical
    data fields (rank is renumbered per zone, so the comparison
    keys are the data fields, not rank), and the zone membership
    agrees with the live heat sign."""
    live_by = {r["curation_id"]: r
               for r in live_hot_env["hot_board"]}
    for row in env["hot_board"]:
        live = live_by.get(row["curation_id"])
        if live is None:
            return False
        if (live["title"] != row["title"]
                or live["ai_label"] != row["ai_label"]
                or live["member_count"] != row["member_count"]
                or live["displayed_total"]
                != row["displayed_total"]):
            return False
        if live["displayed_total"] <= 0:
            return False
    for row in env["cold_board"]:
        live = live_by.get(row["curation_id"])
        if live is None:
            return False
        if (live["title"] != row["title"]
                or live["ai_label"] != row["ai_label"]
                or live["member_count"] != row["member_count"]
                or live["displayed_total"]
                != row["displayed_total"]):
            return False
        if live["displayed_total"] != 0:
            return False
    return True


def envelope_law(env):
    return (set(env.keys()) == ENV_KEYS
            and env["disclaimer"] == DISCLAIMER
            and all(set(r.keys()) == ROW_KEYS
                    for r in env["hot_board"] + env["cold_board"]))


def reopen(db_path, sh_path, cu_path, cfg, lobby_cfg):
    """R1923 four-piece full-stack restart carrier: rebuild
    Ledger + stateless SecGate + ShowcaseFace + CurationFace on
    the same three db paths."""
    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)
    return led, sh, cu


def main():
    tmp = tempfile.mkdtemp(prefix="curation-combinedboundary-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    cu_path = os.path.join(tmp, "curation.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    # -- instance 1: build the substrate (accounts, certificates,
    # showcases, ledger rows) with ZERO curations registered =
    # the zero-curation boundary world -------------------------
    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)
    for acct, avatar in (("usr:alice", "alice"), ("usr:bob", "bob"),
                         ("usr:carol", "carol")):
        led.ensure_account(acct, census_avatar_id=avatar)
    specs = (
        ("a1", "usr:alice", "evt-tower", "tower-cert"),
        ("a2", "usr:alice", "evt-spire", "spire-cert"),
        ("b", "usr:bob", "evt-bridge", "bridge-cert"),
        ("c", "usr:carol", "evt-harbor", "harbor-cert"),
    )
    cl = {}
    for key, acct, ev, kind in specs:
        cl[key] = cf.issue_certificate(acct, ev, kind)["cl_id"]
    for sid in ("sh-one", "sh-two", "sh-three", "sh-four"):
        sh.register_showcase(sid, sid + " window", 3, False)

    shconn = sqlite3.connect(sh_path)
    cuconn = sqlite3.connect(cu_path)
    ledconn = sqlite3.connect(db_path)
    all_ids = ["cu-alpha", "cu-beta", "cu-gamma"]
    read_batches = []

    # -- AC-CBW1 zero-curation boundary world anchor + restart --
    env0 = cu.boards_combined()
    ok1 = []
    ok1.append(envelope_law(env0))
    ok1.append(env0["hot_board"] == [] and env0["cold_board"] == [])
    ok1.append(env0["totals"] == {"hot_count": 0, "cold_count": 0,
                                  "total": 0})
    ok1.append(manual_sql_totals(shconn, cuconn) == {})
    counts_before1 = table_counts(shconn, cuconn, ledconn)
    snap0 = dumps(env0)
    cu.close()
    sh.close()
    led.close()
    led, sh, cu = reopen(db_path, sh_path, cu_path, cfg, lobby_cfg)
    env0r = cu.boards_combined()
    counts_after1 = table_counts(shconn, cuconn, ledconn)
    read_batches.append((counts_before1, counts_after1))
    record("AC-CBW1", all(ok1) and dumps(env0r) == snap0,
           "zero-curation boundary world (substrate rows live:"
           " 3 accounts, 4 certificates, 4 showcases, zero"
           " curations registered): boards_combined honest-empty"
           " anchor green (hot=[], cold=[], totals {0,0,0},"
           " envelope+disclaimer law, manual SQL totals empty);"
           " full-stack close (cu -> sh -> led) then reopen on"
           " the same three db paths: joint read byte-identical"
           " to the pre-close snapshot (%d bytes, dumps"
           " sort_keys)" % len(snap0))

    # -- all-hot world build on the reopened instance 2 --------
    cu.register_curation("cu-alpha", "Alpha Route",
                         ["sh-one"], False)
    cu.register_curation("cu-beta", "Beta Route",
                         ["sh-two", "sh-three"], False)
    cu.register_curation("cu-gamma", "Gamma Route",
                         ["sh-four"], False)
    sh.place_exhibit("usr:alice", "sh-one", cl["a1"],
                     "tower light")
    sh.place_exhibit("usr:alice", "sh-one", cl["a2"],
                     "spire lens")
    sh.place_exhibit("usr:bob", "sh-two", cl["b"], "bridge arch")
    sh.place_exhibit("usr:carol", "sh-four", cl["c"],
                     "harbor lamp")

    # -- AC-CBW2 all-hot boundary world + restart ---------------
    envh = cu.boards_combined()
    ok2 = []
    ok2.append(envelope_law(envh))
    ok2.append(rows_match(envh["hot_board"], [
        (1, "cu-alpha", 2, 1), (2, "cu-beta", 1, 2),
        (3, "cu-gamma", 1, 1)]))
    ok2.append(envh["cold_board"] == [])
    ok2.append(partition_law(envh, all_ids))
    ok2.append(single_source_cross(envh, cu.hot_board()))
    ok2.append(manual_sql_totals(shconn, cuconn)
               == {"cu-alpha": 2, "cu-beta": 1, "cu-gamma": 1})
    counts_before2 = table_counts(shconn, cuconn, ledconn)
    snaph = dumps(envh)
    cu.close()
    sh.close()
    led.close()
    led, sh, cu = reopen(db_path, sh_path, cu_path, cfg, lobby_cfg)
    envhr = cu.boards_combined()
    counts_after2 = table_counts(shconn, cuconn, ledconn)
    read_batches.append((counts_before2, counts_after2))
    record("AC-CBW2", all(ok2) and dumps(envhr) == snaph,
           "all-hot boundary world (three themes registered, a"
           " live placement inside every theme's member"
           " showcases: totals {cu-alpha:2, cu-beta:1,"
           " cu-gamma:1}): hot=[cu-alpha(2) rank1, cu-beta(1)"
           " rank2, cu-gamma(1) rank3] (-total, id ASC),"
           " cold=[]; partition complement law + live"
           " hot_board single-source cross green; manual SQL"
           " second-derivation totals agree; full-stack close"
           " then reopen: joint read byte-identical (%d bytes)"
           % len(snaph))

    # -- AC-CBW3 zero-hot boundary world via post-restart flip --
    # the all-hot -> zero-hot transition runs ON the reopened
    # instance (zero-cache recompute after restart proof)
    sh.retract_exhibit("usr:alice", "sh-one", cl["a1"])
    sh.retract_exhibit("usr:alice", "sh-one", cl["a2"])
    sh.retract_exhibit("usr:bob", "sh-two", cl["b"])
    sh.retract_exhibit("usr:carol", "sh-four", cl["c"])
    envc = cu.boards_combined()
    ok3 = []
    ok3.append(envelope_law(envc))
    ok3.append(envc["hot_board"] == [])
    ok3.append(rows_match(envc["cold_board"], [
        (1, "cu-alpha", 0, 1), (2, "cu-beta", 0, 2),
        (3, "cu-gamma", 0, 1)]))
    ok3.append(partition_law(envc, all_ids))
    ok3.append(single_source_cross(envc, cu.hot_board()))
    ok3.append(manual_sql_totals(shconn, cuconn)
               == {"cu-alpha": 0, "cu-beta": 0, "cu-gamma": 0})
    counts_before3 = table_counts(shconn, cuconn, ledconn)
    snapc = dumps(envc)
    cu.close()
    sh.close()
    led.close()
    led, sh, cu = reopen(db_path, sh_path, cu_path, cfg, lobby_cfg)
    envcr = cu.boards_combined()
    counts_after3 = table_counts(shconn, cuconn, ledconn)
    read_batches.append((counts_before3, counts_after3))
    record("AC-CBW3", all(ok3) and dumps(envcr) == snapc,
           "zero-hot boundary world: the all-hot -> zero-hot"
           " flip ran ON the reopened instance (all four live"
           " placements retracted) and the joint read recomputed"
           " zero-cache into the zero-hot boundary shape: hot=[],"
           " cold=[cu-alpha, cu-beta, cu-gamma] (id ASC);"
           " partition + single-source laws held across the flip;"
           " manual SQL totals all zero; full-stack close then"
           " reopen: joint read byte-identical (%d bytes)"
           % len(snapc))

    # -- AC-CBW4 zero-hot -> mixed boundary escape + fifth
    # instance sequential read purity ---------------------------
    sh.place_exhibit("usr:bob", "sh-two", cl["b"],
                     "bridge arch back")
    envm = cu.boards_combined()
    ok4 = []
    ok4.append(envelope_law(envm))
    ok4.append(rows_match(envm["hot_board"],
                          [(1, "cu-beta", 1, 2)]))
    ok4.append(rows_match(envm["cold_board"], [
        (1, "cu-alpha", 0, 1), (2, "cu-gamma", 0, 1)]))
    ok4.append(partition_law(envm, all_ids))
    ok4.append(single_source_cross(envm, cu.hot_board()))
    counts_before4 = table_counts(shconn, cuconn, ledconn)
    snapm = dumps(envm)
    cu.close()
    sh.close()
    led.close()
    led, sh, cu = reopen(db_path, sh_path, cu_path, cfg, lobby_cfg)
    envmr = cu.boards_combined()
    envmr2 = cu.boards_combined()
    counts_after4 = table_counts(shconn, cuconn, ledconn)
    read_batches.append((counts_before4, counts_after4))
    ok4.append(dumps(envmr) == snapm)
    ok4.append(dumps(envmr2) == dumps(envmr))
    record("AC-CBW4", all(ok4),
           "zero-hot -> mixed boundary escape ON the reopened"
           " instance (cl_b re-placed into sh-two, a cu-beta"
           " member showcase): joint read recomputed zero-cache"
           " into the mixed shape hot=[cu-beta(1)],"
           " cold=[cu-alpha, cu-gamma] (id ASC) with partition +"
           " single-source laws held; full-stack close then"
           " FIFTH instance reopen on the same three db paths:"
           " sequential reads byte-identical to the post-escape"
           " snapshot and to each other (re-read purity, zero"
           " in-memory drift, %d bytes)" % len(snapm))

    # -- AC-CBW5 pure-read law + product-file sha double-proof --
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok5 = [before == after for before, after in read_batches]
    ok5.append(shas_after == shas_before)
    ok5.append(len(read_batches) == 4)
    record("AC-CBW5", all(ok5),
           "pure-read law: all %d reopen read batches left"
           " curations / curation_members / showcases /"
           " exhibit_events / ledger_tx row counts constant"
           " (final counts %s); product files sha256 unchanged"
           " (curation.py, showcase.py, both shipped"
           " config.json) - suite-only round, zero product"
           " changes"
           % (len(read_batches),
              json.dumps(counts_after4, sort_keys=True)))

    # -- AC-CBW6 hygiene: ASCII, zero-network imports, tmp world -
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
    comb_src = inspect.getsource(CU.CurationFace.boards_combined)
    ok6.append(not any(verb in comb_src for verb in
                       ("INSERT", "UPDATE ", "DELETE")))
    record("AC-CBW6", all(ok6),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, boards_combined"
           " method source zero write statements, world db in"
           " system tmp outside the repo" % len(src_bytes))

    cu.close()
    sh.close()
    led.close()
    shconn.close()
    cuconn.close()
    ledconn.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
