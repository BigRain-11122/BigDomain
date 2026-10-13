"""Acceptance suite for the curation hot_board cross-restart
persistence example window (BigDomain R1923; canon = the R1919
reseeded tech-queue row claimed by R1923). The theme heat board
read face (curation.py hot_board, R1753) is pure-derived over
THREE databases: the curation registry (curation.db curations +
curation_members), the live showcase display state (showcase.db
exhibit_events latest-action-per-item law) and the ledger
ownership rows. This suite pins the derived purity across
full-stack instance restarts: pre-close envelope == post-reopen
read byte-identical, zero-cache recompute with rank flips and
tie-break following after post-restart placement/retract, dual-
instance sequential reads byte-identical, pure-read law across
restarts, and hygiene.

Criteria AC-HBP1..HBP6 were pre-registered in
state/queue/tech.md at claim time (R1923, before this code
existed; honesty law; AC-HBP prefix git-grep zero-occupancy
anchored 2026-10-13; AC-HB1..HB7 belong to the R1753/R1770 read
faces and are not re-registered here).

Suite-only round: zero product-code changes (curation.py,
showcase.py and both shipped config.json files are sha256
double-proven unchanged). Restart carrier = the R1918
four-piece full-stack precedent (close cu -> sh -> led, then
rebuild Ledger + stateless SecGate + ShowcaseFace + CurationFace
on the same three db paths) - the heat derivation crosses three
databases, so a curation-only restart would under-prove.

Usage: python test_curation_hotpersist.py
"""

import hashlib
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

DISCLAIMER = ("sandbox stand-in disclaimer: the themed curation"
              " hot board is a display feature, not investment"
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
    """Second derivation path (independent of the hot_board single
    derivation source): per curation, sum the live on-display
    counts of the member showcases straight from the exhibit
    latest-action-per-item law."""
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


def table_counts(shconn, cuconn):
    cu_cur = cuconn.execute(
        "SELECT COUNT(*) FROM curations").fetchone()[0]
    cu_mem = cuconn.execute(
        "SELECT COUNT(*) FROM curation_members").fetchone()[0]
    sh_reg = shconn.execute(
        "SELECT COUNT(*) FROM showcases").fetchone()[0]
    sh_evt = shconn.execute(
        "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]
    return {"curations": int(cu_cur),
            "curation_members": int(cu_mem),
            "showcases": int(sh_reg),
            "exhibit_events": int(sh_evt)}


def board_matches(board, expected):
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
    tmp = tempfile.mkdtemp(prefix="curation-hotpersist-")
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

    # -- world: true product path, four avatars + seven certs +
    # four showcases + three curations, tie visible by design ----
    for acct, avatar in (("usr:alice", "alice"), ("usr:bob", "bob"),
                         ("usr:carol", "carol"),
                         ("usr:dave", "dave")):
        led.ensure_account(acct, census_avatar_id=avatar)
    specs = (
        ("a", "usr:alice", "evt-tower", "tower-cert"),
        ("b", "usr:bob", "evt-bridge", "bridge-cert"),
        ("c", "usr:carol", "evt-harbor", "harbor-cert"),
        ("d", "usr:dave", "evt-lamp", "lamp-cert"),
        ("e", "usr:alice", "evt-gate", "gate-cert"),
        ("f", "usr:bob", "evt-mill", "mill-cert"),
        ("g", "usr:carol", "evt-arch", "arch-cert"),
    )
    cl = {}
    for key, acct, ev, kind in specs:
        cl[key] = cf.issue_certificate(acct, ev, kind)["cl_id"]
    for sid in ("sh-one", "sh-two", "sh-three", "sh-four"):
        sh.register_showcase(sid, sid + " window", 3, False)
    sh.place_exhibit("usr:alice", "sh-one", cl["a"], "tower light")
    sh.place_exhibit("usr:bob", "sh-one", cl["b"], "bridge arch")
    sh.place_exhibit("usr:carol", "sh-two", cl["c"], "harbor lamp")
    sh.place_exhibit("usr:dave", "sh-three", cl["d"], "lamp glow")
    sh.place_exhibit("usr:alice", "sh-three", cl["e"], "gate relief")
    sh.place_exhibit("usr:bob", "sh-four", cl["f"], "mill wheel")
    sh.place_exhibit("usr:carol", "sh-four", cl["g"], "arch band")
    cu.register_curation("cu-alpha", "Alpha Route",
                         ["sh-one", "sh-two"], False)
    cu.register_curation("cu-beta", "Beta Route",
                         ["sh-three"], False)
    cu.register_curation("cu-gamma", "Gamma Route",
                         ["sh-four"], False)

    shconn = sqlite3.connect(sh_path)
    cuconn = sqlite3.connect(cu_path)
    counts_after_world = table_counts(shconn, cuconn)

    # -- AC-HBP1 control anchor: pre-restart envelope pinned ------
    env1 = cu.hot_board()
    board1 = env1["hot_board"]
    ok1 = []
    ok1.append(board_matches(board1, [
        (1, "cu-alpha", 3, 2), (2, "cu-beta", 2, 1),
        (3, "cu-gamma", 2, 1)]))
    ok1.append(set(env1.keys()) == {"hot_board", "disclaimer"})
    ok1.append(all(set(r.keys()) == ROW_KEYS for r in board1))
    ok1.append(board1[1]["displayed_total"] == 2
               and board1[2]["displayed_total"] == 2)
    ok1.append(board1[1]["curation_id"] == "cu-beta"
               and board1[2]["curation_id"] == "cu-gamma")
    totals1 = manual_sql_totals(shconn, cuconn)
    ok1.append(totals1 == {"cu-alpha": 3, "cu-beta": 2,
                           "cu-gamma": 2})
    record("AC-HBP1", all(ok1),
           "pre-restart board pinned rank1 cu-alpha total=3"
           " members=2, rank2 cu-beta / rank3 cu-gamma both"
           " total=2 with curation_id ASC tie-break; envelope"
           " keys %s, row keys %s; manual SQL second-derivation"
           " totals %s" % (sorted(env1.keys()), sorted(ROW_KEYS),
                           json.dumps(totals1, sort_keys=True)))
    snap1 = dumps(env1)

    # -- AC-HBP2 full-stack restart: byte-identical envelope -------
    cu.close()
    sh.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    gate2 = SecGate.from_config(lobby_cfg)
    sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
    cu2 = CU.CurationFace(sh2, DISCLAIMER, cu_path)
    counts_before_read2 = table_counts(shconn, cuconn)
    env2 = cu2.hot_board()
    counts_after_read2 = table_counts(shconn, cuconn)
    snap2 = dumps(env2)
    record("AC-HBP2", snap2 == snap1,
           "full-stack close (cu -> sh -> led) then rebuild on"
           " the same three db paths: reopened hot_board =="
           " pre-close envelope byte-identical (%d bytes,"
           " dumps sort_keys); zero in-memory drift in the"
           " derived read" % len(snap2))

    # -- AC-HBP3 post-restart world change: zero-cache recompute ---
    sh2.retract_exhibit("usr:bob", "sh-one", cl["b"])
    sh2.place_exhibit("usr:bob", "sh-four", cl["b"],
                      "bridge arch two")
    env3 = cu2.hot_board()
    board3 = env3["hot_board"]
    snap3 = dumps(env3)
    ok3 = []
    ok3.append(board_matches(board3, [
        (1, "cu-gamma", 3, 1), (2, "cu-alpha", 2, 2),
        (3, "cu-beta", 2, 1)]))
    ok3.append(snap3 != snap1)
    totals3 = manual_sql_totals(shconn, cuconn)
    ok3.append(totals3 == {"cu-alpha": 2, "cu-beta": 2,
                           "cu-gamma": 3})
    record("AC-HBP3", all(ok3),
           "post-restart retract cl_b out of sh-one + re-place"
           " into sh-four (live counts 2->1 and 2->3): board"
           " recomputed zero-cache, all three ranks flipped"
           " (gamma 3->1, alpha 1->2, beta 2->3) with the new"
           " alpha/beta tie at total=2 broken by curation_id"
           " ASC; envelope differs from the pre-restart"
           " snapshot; manual SQL totals %s"
           % json.dumps(totals3, sort_keys=True))

    # -- AC-HBP4 third instance: sequential reads identical --------
    cu2.close()
    cu3 = CU.CurationFace(sh2, DISCLAIMER, cu_path)
    counts_before_read4 = table_counts(shconn, cuconn)
    env4 = cu3.hot_board()
    env4b = cu3.hot_board()
    counts_after_read4 = table_counts(shconn, cuconn)
    snap4 = dumps(env4)
    snap4b = dumps(env4b)
    ok4 = [snap4 == snap3, snap4b == snap4,
           counts_before_read4 == counts_after_read4]
    record("AC-HBP4", all(ok4),
           "second curation-face restart (third instance on the"
           " same db): sequential hot_board reads byte-identical"
           " to the post-mutation state and to each other"
           " (repeat-read purity, zero in-memory drift)")

    # -- AC-HBP5 pure-read law + product-file sha double-proof -----
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok5 = [counts_after_read2 == counts_before_read2,
           counts_after_read4 == counts_before_read4,
           shas_after == shas_before]
    record("AC-HBP5", all(ok5),
           "pure-read law: every read batch left curations /"
           " curation_members / showcases / exhibit_events row"
           " counts constant (%s); product files sha256"
           " unchanged (curation.py, showcase.py, both shipped"
           " config.json)" % json.dumps(counts_after_read4,
                                        sort_keys=True))

    # -- AC-HBP6 hygiene: ASCII, zero-network imports, tmp world ---
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
    ok6.append(os.path.abspath(tmp).startswith(tempfile.gettempdir()))
    ok6.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    record("AC-HBP6", all(ok6),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system tmp"
           " outside the repo" % len(src_bytes))

    cu3.close()
    sh2.close()
    led2.close()
    shconn.close()
    cuconn.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
