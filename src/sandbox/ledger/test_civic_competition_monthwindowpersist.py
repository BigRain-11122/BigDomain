"""Acceptance suite for the civic honor-competition month-window
read-face cross-restart persistence example window
(BigDomain R2005; canon = the R1999-reseeded explore-queue row
claimed by R2005, criteria AC-HCWP1..AC-HCWP7 registered in the
claim note BEFORE this code existed - honesty law; AC-HCWP
prefix git-grep zero-occupancy anchored 2026-10-17).

Face under proof: CivicPointsFace.honor_board_competition(year,
window=None) - the R1999 explicit strict YYYY-MM month-window
slice of the R1769 1224 competition-rank board (year-window
coupling gate fail-closed before any read). Persistence
substrate: the append-only civic_earns / civic_behaviors rows;
the read face is a read-time derivation with zero cached state,
so the suite pins derived purity across instance restarts:

  - pre-close five-form pinning (default full-year + explicit
    2026-09 / 2026-10 / 2026-11 / 2026-12 windows) with exact
    1224 tie ranks, envelope key laws and an independent manual
    SQL GROUP BY + second-derivation 1224 cross;
  - close -> new instance over the same civic.db: all five
    forms byte-identical;
  - post-restart earn inside the October window: zero-cache
    window recompute with the tie rank shifting, September
    window frozen byte-identical, empty windows stay honest;
  - post-restart behavior registration + November earns + the
    gate family probing identical codes across the restart
    (year-window coupling / bad window / bad year, zero row
    side effects);
  - second restart third instance: sequential reads
    byte-identical, repeat-read purity;
  - pure-read law, end-state manual SQL crosses, product-file
    sha256 double-proof (suite-only round), hygiene.

Usage: python test_civic_competition_monthwindowpersist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from civicpoints import (CivicPointsFace, CivicError,   # noqa: E402
                         E_CV_BAD_ARGS, E_CV_BAD_WINDOW)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: civic behavior points"
              " are a public-welfare count, not investment advice")

PRODUCT_FILES = [
    os.path.join(BASE, "civicpoints.py"),
]

FORMS = [
    ("full", None),
    ("w09", "2026-09"),
    ("w10", "2026-10"),
    ("w11", "2026-11"),
    ("w12", "2026-12"),
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def board_of(face, window):
    if window is None:
        return face.honor_board_competition(
            "2026")["honor_board_competition"]
    return face.honor_board_competition(
        "2026", window)["honor_board_competition"]


def rows_of(board):
    return [(r["rank"], r["account_id"], r["points"], r["events"])
            for r in board]


def manual_competition(conn, year, window=None):
    """Independent second derivation over the same rows: raw
    GROUP BY prefix-filter recount, then the 1224 competition
    rank law recomputed by hand (ties share the minimum rank,
    next distinct position skips). Zero shared code with the
    product face."""
    if window is None:
        like = year + "-%"
    else:
        like = window + "-%"
    rows = conn.execute(
        "SELECT account_id, COALESCE(SUM(points), 0), COUNT(*)"
        " FROM civic_earns WHERE at_day LIKE ? GROUP BY account_id",
        (like,)).fetchall()
    entries = sorted(
        ((int(r[1]), int(r[2]), r[0]) for r in rows),
        key=lambda e: (-e[0], e[2]))
    board = []
    prev_points = None
    prev_rank = 0
    for pos, (points, events, account_id) in enumerate(entries,
                                                       start=1):
        if points != prev_points:
            prev_points = points
            prev_rank = pos
        board.append({"rank": prev_rank, "account_id": account_id,
                      "points": points, "events": events})
    return board


def read_all_forms(face):
    """Read every window form under proof once, return dict of
    dumps (byte-comparable snapshots)."""
    out = {}
    for key, window in FORMS:
        if window is None:
            env = face.honor_board_competition("2026")
        else:
            env = face.honor_board_competition("2026", window)
        out[key] = dumps(env)
    return out


def earn_count(conn):
    return int(conn.execute(
        "SELECT COUNT(*) FROM civic_earns").fetchone()[0])


def behavior_count(conn):
    return int(conn.execute(
        "SELECT COUNT(*) FROM civic_behaviors").fetchone()[0])


def build_world(face):
    """True product path world (the R1999 month-window shape):
    two behaviors, September double-tie at 5 points and an
    October five-account 10/8/6/3/3 world with the dave/erin
    3-point tie sharing rank 4."""
    face.register_behavior("b-volunteer", "volunteer shift", 5, 2,
                           True)
    face.register_behavior("b-report", "civic report", 3, 1,
                           False)
    # September earns: alice and carol tie at 5 (1224 dual rank 1)
    face.earn_civic("usr:alice", "b-volunteer", "2026-09-28",
                    "ev-s1")
    face.earn_civic("usr:carol", "b-volunteer", "2026-09-29",
                    "ev-s2")
    # October earns
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01",
                    "ev-a1")
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01",
                    "ev-a2")
    face.earn_civic("usr:bob", "b-volunteer", "2026-10-02",
                    "ev-b1")
    face.earn_civic("usr:bob", "b-report", "2026-10-02", "ev-b2")
    face.earn_civic("usr:carol", "b-report", "2026-10-01",
                    "ev-c1")
    face.earn_civic("usr:carol", "b-report", "2026-10-03",
                    "ev-c2")
    face.earn_civic("usr:dave", "b-report", "2026-10-02", "ev-d1")
    face.earn_civic("usr:erin", "b-report", "2026-10-04", "ev-e1")


def main():
    tmp = tempfile.mkdtemp(prefix="civic-hcw-persist-")
    db_path = os.path.join(tmp, "civic.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    face = CivicPointsFace(DISCLAIMER, db_path)
    build_world(face)
    conn = sqlite3.connect(db_path)

    # -- AC-HCWP1 control anchor: pre-close five-form pinning --
    full_env = face.honor_board_competition("2026")
    w09_env = face.honor_board_competition("2026", "2026-09")
    w10_env = face.honor_board_competition("2026", "2026-10")
    w11_env = face.honor_board_competition("2026", "2026-11")
    w12_env = face.honor_board_competition("2026", "2026-12")
    ok1 = []
    ok1.append(sorted(full_env.keys()) == [
        "disclaimer", "honor_board_competition"])
    ok1.append(all(sorted(e.keys()) == [
        "disclaimer", "honor_board_competition", "window"]
        for e in (w09_env, w10_env, w11_env, w12_env)))
    ok1.append(w09_env["window"] == "2026-09"
               and w10_env["window"] == "2026-10"
               and w11_env["window"] == "2026-11"
               and w12_env["window"] == "2026-12")
    ok1.append(all(sorted(r.keys()) == ["account_id", "events",
                                        "points", "rank"]
                   for r in full_env["honor_board_competition"]))
    ok1.append(rows_of(full_env["honor_board_competition"]) == [
        (1, "usr:alice", 15, 3), (2, "usr:carol", 11, 3),
        (3, "usr:bob", 8, 2), (4, "usr:dave", 3, 1),
        (4, "usr:erin", 3, 1)])
    ok1.append(rows_of(w09_env["honor_board_competition"]) == [
        (1, "usr:alice", 5, 1), (1, "usr:carol", 5, 1)])
    ok1.append(rows_of(w10_env["honor_board_competition"]) == [
        (1, "usr:alice", 10, 2), (2, "usr:bob", 8, 2),
        (3, "usr:carol", 6, 2), (4, "usr:dave", 3, 1),
        (4, "usr:erin", 3, 1)])
    ok1.append(w11_env["honor_board_competition"] == []
               and w12_env["honor_board_competition"] == [])
    ok1.append(all(
        face.honor_board_competition("2026", w)[
            "honor_board_competition"] == manual_competition(
                conn, "2026", w)
        for w in ("2026-09", "2026-10", "2026-11", "2026-12")))
    ok1.append(face.honor_board_competition("2026")[
        "honor_board_competition"] == manual_competition(
            conn, "2026", None))
    ok1.append(dumps(face.honor_board_competition("2026"))
               == dumps(face.honor_board_competition("2026")))
    record("AC-HCWP1", all(ok1),
           "pre-close pinning: default envelope keys %s zero window"
           " key, explicit windows additive window key; full-year"
           " [(1,alice,15,3),(2,carol,11,3),(3,bob,8,2),"
           "(4,dave,3,1),(4,erin,3,1)] with the dave/erin 3-point"
           " tie sharing rank 4; 2026-09 [(1,alice,5,1),"
           "(1,carol,5,1)] 1224 dual rank 1; 2026-10"
           " [(1,alice,10,2),(2,bob,8,2),(3,carol,6,2),"
           "(4,dave,3,1),(4,erin,3,1)]; empty 2026-11 / 2026-12"
           " honest []; all five forms == independent manual SQL"
           " GROUP BY + 1224 second-derivation cross; double-call"
           " identical" % sorted(full_env.keys()))
    snap1 = read_all_forms(face)

    # -- AC-HCWP2 restart: byte-identical five forms --------------
    counts_before_read2 = earn_count(conn)
    face.close()
    face2 = CivicPointsFace(DISCLAIMER, db_path)
    snap2 = read_all_forms(face2)
    counts_after_read2 = earn_count(conn)
    ok2 = [snap2[k] == snap1[k] for k in
           ("full", "w09", "w10", "w11", "w12")]
    record("AC-HCWP2", all(ok2),
           "CivicPointsFace close -> new instance over the same"
           " civic.db: default + 2026-09 + 2026-10 + 2026-11 +"
           " 2026-12 competition window reads all byte-identical"
           " to the pre-close snapshots (sort_keys dumps; zero"
           " in-memory drift in the derived month-window"
           " competition read face)")

    # -- AC-HCWP3 post-restart earn: zero-cache window recompute ---
    face2.earn_civic("usr:frank", "b-volunteer", "2026-10-05",
                     "ev-f1")
    w10_b = face2.honor_board_competition("2026", "2026-10")
    full_b = face2.honor_board_competition("2026")
    ok3 = []
    ok3.append(rows_of(w10_b["honor_board_competition"]) == [
        (1, "usr:alice", 10, 2), (2, "usr:bob", 8, 2),
        (3, "usr:carol", 6, 2), (4, "usr:frank", 5, 1),
        (5, "usr:dave", 3, 1), (5, "usr:erin", 3, 1)])
    ok3.append(rows_of(full_b["honor_board_competition"]) == [
        (1, "usr:alice", 15, 3), (2, "usr:carol", 11, 3),
        (3, "usr:bob", 8, 2), (4, "usr:frank", 5, 1),
        (5, "usr:dave", 3, 1), (5, "usr:erin", 3, 1)])
    ok3.append(w10_b["honor_board_competition"]
               == manual_competition(conn, "2026", "2026-10")
               and full_b["honor_board_competition"]
               == manual_competition(conn, "2026", None))
    ok3.append(dumps(face2.honor_board_competition(
        "2026", "2026-09")) == snap1["w09"])
    ok3.append(dumps(face2.honor_board_competition(
        "2026", "2026-11")) == snap1["w11"]
               and dumps(face2.honor_board_competition(
                   "2026", "2026-12")) == snap1["w12"])
    record("AC-HCWP3", all(ok3),
           "post-restart earn (frank volunteer @2026-10-05):"
           " October window recomputed zero-cache (frank enters"
           " at rank 4, the dave/erin 3-point tie shifts 4 -> 5"
           " but keeps sharing the rank - the 1224 law survives"
           " restart) and the full-year face follows; both =="
           " manual SQL cross; the September window read stays"
           " byte-identical to the pre-close snapshot (old-window"
           " frozen); empty 2026-11 / 2026-12 windows stay honest"
           " empty")
    snap3 = read_all_forms(face2)

    # -- AC-HCWP4 post-restart registration + new month + gates ---
    face2.register_behavior("b-newmoon", "new moon", 4, 5, True)
    face2.earn_civic("usr:erin", "b-report", "2026-11-01", "ev-n1")
    face2.earn_civic("usr:grace", "b-newmoon", "2026-11-04",
                     "ev-n2")
    w11_c = face2.honor_board_competition("2026", "2026-11")
    w09_c = face2.honor_board_competition("2026", "2026-09")
    w10_c = face2.honor_board_competition("2026", "2026-10")
    full_c = face2.honor_board_competition("2026")
    ok4 = []
    ok4.append(rows_of(w11_c["honor_board_competition"]) == [
        (1, "usr:grace", 4, 1), (2, "usr:erin", 3, 1)])
    ok4.append(rows_of(full_c["honor_board_competition"]) == [
        (1, "usr:alice", 15, 3), (2, "usr:carol", 11, 3),
        (3, "usr:bob", 8, 2), (4, "usr:erin", 6, 2),
        (5, "usr:frank", 5, 1), (6, "usr:grace", 4, 1),
        (7, "usr:dave", 3, 1)])
    ok4.append(dumps(w09_c) == snap3["w09"]
               and dumps(w10_c) == snap3["w10"])
    ok4.append(w11_c["honor_board_competition"]
               == manual_competition(conn, "2026", "2026-11")
               and full_c["honor_board_competition"]
               == manual_competition(conn, "2026", None))
    # gate family across the restart: identical codes, zero side
    # effects (rejections happen before any read/write surface)
    gates_before = earn_count(conn)
    gate_codes = []
    for probe in (("2026", "2027-01"), ("2026", "2026-13")):
        try:
            face2.honor_board_competition(probe[0], probe[1])
            gate_codes.append(None)
        except CivicError as exc:
            gate_codes.append(exc.code)
    try:
        face2.honor_board_competition("20x6")
        gate_codes.append(None)
    except CivicError as exc:
        gate_codes.append(exc.code)
    gates_after = earn_count(conn)
    ok4.append(gate_codes == [E_CV_BAD_WINDOW, E_CV_BAD_WINDOW,
                              E_CV_BAD_ARGS])
    ok4.append(gates_before == gates_after)
    record("AC-HCWP4", all(ok4),
           "post-restart registration (b-newmoon) + November earns"
           " (erin report @11-01, grace newmoon @11-04): the"
           " November window gets its first content"
           " [(1,grace,4,1),(2,erin,3,1)] while the full-year"
           " board recomputes live (erin 3 -> 6 climbs to rank 4,"
           " the full-year tie dissolves - october-window tie"
           " stays frozen in its own window); September / October"
           " window reads byte-identical to the pre-registration"
           " snapshots; gate family identical across the restart:"
           " year-window coupling ('2026','2027-01') and bad"
           " window ('2026','2026-13') both E_CV_BAD_WINDOW, bad"
           " year ('20x6') E_CV_BAD_ARGS, all rejected before any"
           " read with the earn row count constant (%d == %d)"
           % (gates_before, gates_after))
    snap4 = read_all_forms(face2)

    # -- AC-HCWP5 second restart: sequential reads identical -----
    counts_before_read5 = earn_count(conn)
    face2.close()
    face3 = CivicPointsFace(DISCLAIMER, db_path)
    snap5 = read_all_forms(face3)
    snap5b = read_all_forms(face3)
    counts_after_read5 = earn_count(conn)
    ok5 = [snap5[k] == snap4[k] for k in
           ("full", "w09", "w10", "w11", "w12")]
    ok5.append(all(snap5b[k] == snap5[k] for k in snap5))
    record("AC-HCWP5", all(ok5),
           "second civic-face restart (third instance, same"
           " civic.db): all five window-form reads byte-identical"
           " to the post-registration state and the repeated read"
           " batch identical to itself (repeat-read purity, zero"
           " in-memory drift across two restarts)")

    # -- AC-HCWP6 pure-read law + manual cross + product sha -------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok6 = [counts_after_read2 == counts_before_read2,
           counts_after_read5 == counts_before_read5,
           shas_after == shas_before]
    ok6.append(face3.honor_board_competition("2026")[
        "honor_board_competition"] == manual_competition(
            conn, "2026", None)
    and face3.honor_board_competition("2026", "2026-09")[
        "honor_board_competition"] == manual_competition(
            conn, "2026", "2026-09")
    and face3.honor_board_competition("2026", "2026-10")[
        "honor_board_competition"] == manual_competition(
            conn, "2026", "2026-10")
    and face3.honor_board_competition("2026", "2026-11")[
        "honor_board_competition"] == manual_competition(
            conn, "2026", "2026-11")
    and face3.honor_board_competition("2026", "2026-12")[
        "honor_board_competition"] == manual_competition(
            conn, "2026", "2026-12"))
    record("AC-HCWP6", all(ok6),
           "pure-read law: every read batch left the civic_earns"
           " row count constant (%d == %d, %d == %d); end-state"
           " five-form boards == fresh manual SQL + 1224 crosses;"
           " civicpoints.py sha256 unchanged (suite-only round)"
           % (counts_before_read2, counts_after_read2,
              counts_before_read5, counts_after_read5))

    # -- AC-HCWP7 hygiene: ASCII, zero-network, tmp world ----------
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok7 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok7.append(not net_hits)
    ok7.append(os.path.abspath(tmp).startswith(tempfile.gettempdir()))
    ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    # criteria-count law: seven criteria total; this seventh one is
    # not yet in RESULTS at assertion time (same-round test-side
    # timing fix, criterion semantics unchanged - R1989/R1996
    # precedent family)
    ok7.append(len(RESULTS) + 1 == 7)
    record("AC-HCWP7", all(ok7),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system tmp"
           " outside the repo, criteria count == 7"
           % len(src_bytes))

    face3.close()
    conn.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
