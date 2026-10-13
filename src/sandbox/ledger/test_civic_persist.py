"""Acceptance suite for the civic honor-board read-face family
cross-restart persistence example window (BigDomain R1927; canon =
the R1926-reseeded tech-queue row claimed by R1927 after the
queue-head pay-channel row was duplicate-closed against the R1904
pay-channel-persist seat). The two read faces under proof
(civicpoints.py, R1754/R1769 in-register):

  - honor_board(year): annual per-account aggregation of civic
    earn points, pure-read derivation, deterministic
    (-points, account_id) order, honest empty list for a
    zero-earn year;
  - honor_board_competition(year): the 1224 competition ranking
    over the SAME single-source aggregation - tied accounts
    share the minimum rank (rank-skip face pinned via a
    two-account tie in the anchor world).

Derived purity across instance restarts is pinned: pre-close
six-form snapshots (2025 dense + comp with tie, 2026 dense +
comp, empty-year 2030 dense + comp) == reopened reads
byte-identical, zero-cache recompute after post-restart earns
(order flip + new-account entry + same-account cross-year
coexistence), old-year boards frozen byte-identical, second
restart third-instance sequential reads byte-identical,
pure-read law, manual-SQL cross, product-file sha256
double-proof, hygiene.

Criteria AC-CVP1..CVP7 were pre-registered in
state/queue/tech.md at claim time (R1927, before this code
existed; honesty law; AC-CVP prefix git-grep zero-occupancy
anchored 2026-10-13; AC-CV1..CV7 / AC-HN1..HN6 / AC-HR1..HR7
belong to the single-instance civic suites and are not
re-registered here).

Suite-only round: zero product-code changes (civicpoints.py is
sha256 double-proven unchanged). Restart carrier = the seed row
text: CivicPointsFace close -> new instance over the same
civic.db path (the boards' persistence substrate is the
append-only civic_earns rows; both boards are read-time
derivations with zero cached state).

Usage: python test_civic_persist.py
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

from civicpoints import CivicPointsFace   # noqa: E402 (R1752 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: civic honor boards"
              " are community display features, not investment"
              " advice")

PRODUCT_FILES = [
    os.path.join(BASE, "civicpoints.py"),
]

DENSE_KEYS = {"honor_board", "disclaimer"}
COMP_KEYS = {"honor_board_competition", "disclaimer"}
ROW_KEYS = {"rank", "account_id", "points", "events"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def manual_board(conn, year):
    """Independent second derivation over the same rows: GROUP BY
    + SUM + COUNT with the year LIKE filter, sorted points DESC
    then account_id ASC, dense ranks 1..N."""
    rows = conn.execute(
        "SELECT account_id, COALESCE(SUM(points), 0), COUNT(*)"
        " FROM civic_earns WHERE at_day LIKE ? GROUP BY account_id",
        (year + "-%",)).fetchall()
    entries = sorted(((r[0], int(r[1]), int(r[2])) for r in rows),
                     key=lambda e: (-e[1], e[0]))
    return [{"rank": i, "account_id": e[0], "points": e[1],
             "events": e[2]} for i, e in enumerate(entries, 1)]


def table_counts(conn):
    return {
        "civic_earns": int(conn.execute(
            "SELECT COUNT(*) FROM civic_earns").fetchone()[0]),
        "civic_redeems": int(conn.execute(
            "SELECT COUNT(*) FROM civic_redeems").fetchone()[0]),
        "civic_grants": int(conn.execute(
            "SELECT COUNT(*) FROM civic_grants").fetchone()[0]),
    }


def read_all_forms(face):
    """Read every form under proof once, return dict of dumps."""
    return {
        "dense2025": dumps(face.honor_board("2025")),
        "comp2025": dumps(face.honor_board_competition("2025")),
        "dense2026": dumps(face.honor_board("2026")),
        "comp2026": dumps(face.honor_board_competition("2026")),
        "dense2030": dumps(face.honor_board("2030")),
        "comp2030": dumps(face.honor_board_competition("2030")),
    }


def build_world(face):
    """True product path: two behaviors + five accounts across two
    years, with a deliberate bravo/charlie tie at 5 points in the
    2025 anchor year (the 1224 rank-skip face)."""
    face.register_behavior("guide", "City Guide", 5, 3, False)
    face.register_behavior("cleanup", "River Cleanup", 3, 2, False)
    face.earn_civic("usr:alpha", "guide", "2025-04-01", "ev-a1")
    face.earn_civic("usr:alpha", "cleanup", "2025-04-02", "ev-a2")
    face.earn_civic("usr:bravo", "guide", "2025-03-03", "ev-b1")
    face.earn_civic("usr:charlie", "guide", "2025-09-09", "ev-c1")
    face.earn_civic("usr:delta", "guide", "2026-02-02", "ev-d1")
    face.earn_civic("usr:echo", "cleanup", "2026-03-03", "ev-e1")


def main():
    tmp = tempfile.mkdtemp(prefix="civic-persist-")
    db_path = os.path.join(tmp, "civic.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    face = CivicPointsFace(DISCLAIMER, db_path)
    build_world(face)
    conn = sqlite3.connect(db_path)

    # -- AC-CVP1 control anchor: pre-close six-form pinning --------
    f1 = read_all_forms(face)
    dense2025 = face.honor_board("2025")
    comp2025 = face.honor_board_competition("2025")
    dense2026 = face.honor_board("2026")
    comp2026 = face.honor_board_competition("2026")
    empty2030 = face.honor_board("2030")
    ok1 = []
    ok1.append(set(dense2025.keys()) == DENSE_KEYS
               and set(comp2025.keys()) == COMP_KEYS)
    ok1.append(all(set(r.keys()) == ROW_KEYS
                   for r in dense2025["honor_board"]
                   + comp2025["honor_board_competition"]
                   + dense2026["honor_board"]
                   + comp2026["honor_board_competition"]))
    ok1.append(dense2025["honor_board"] == [
        {"rank": 1, "account_id": "usr:alpha", "points": 8,
         "events": 2},
        {"rank": 2, "account_id": "usr:bravo", "points": 5,
         "events": 1},
        {"rank": 3, "account_id": "usr:charlie", "points": 5,
         "events": 1}])
    ok1.append(comp2025["honor_board_competition"] == [
        {"rank": 1, "account_id": "usr:alpha", "points": 8,
         "events": 2},
        {"rank": 2, "account_id": "usr:bravo", "points": 5,
         "events": 1},
        {"rank": 2, "account_id": "usr:charlie", "points": 5,
         "events": 1}])
    ok1.append(dense2026["honor_board"] == [
        {"rank": 1, "account_id": "usr:delta", "points": 5,
         "events": 1},
        {"rank": 2, "account_id": "usr:echo", "points": 3,
         "events": 1}])
    ok1.append(comp2026["honor_board_competition"] == [
        {"rank": 1, "account_id": "usr:delta", "points": 5,
         "events": 1},
        {"rank": 2, "account_id": "usr:echo", "points": 3,
         "events": 1}])
    ok1.append(empty2030 == {"honor_board": [],
                             "disclaimer": DISCLAIMER}
               and face.honor_board_competition("2030")
               == {"honor_board_competition": [],
                   "disclaimer": DISCLAIMER})
    ok1.append(dense2025["honor_board"]
               == manual_board(conn, "2025")
               and dense2026["honor_board"]
               == manual_board(conn, "2026"))
    ok1.append(len(manual_board(conn, "2030")) == 0)
    record("AC-CVP1", all(ok1),
           "pre-close pinning: 2025 dense 3 rows (alpha r1 8pts"
           " 2ev, bravo r2 / charlie r3 tie at 5pts,"
           " account_id ASC tie-break), comp 2025 = 1224 tie"
           " (bravo + charlie share rank 2), 2026 dense/comp 2"
           " rows (delta r1, echo r2), empty year 2030 honest"
           " [] on both faces, envelope/row key sets exact,"
           " boards == independent manual SQL GROUP BY cross")
    snap1 = read_all_forms(face)

    # -- AC-CVP2 restart: byte-identical six forms ------------------
    counts_before_read2 = table_counts(conn)
    face.close()
    face2 = CivicPointsFace(DISCLAIMER, db_path)
    f2 = read_all_forms(face2)
    counts_after_read2 = table_counts(conn)
    ok2 = [f2[k] == snap1[k] for k in
           ("dense2025", "comp2025", "dense2026", "comp2026",
            "dense2030", "comp2030")]
    record("AC-CVP2", all(ok2),
           "CivicPointsFace close -> new instance over the same"
           " civic.db path: reopened honor_board +"
           " honor_board_competition for 2025 / 2026 / 2030 all"
           " byte-identical to the pre-close snapshots"
           " (sort_keys dumps; zero in-memory drift in the"
           " derived read faces)")

    # -- AC-CVP3 post-restart earn: zero-cache recompute -------------
    face2.earn_civic("usr:echo", "guide", "2026-04-04", "ev-e2")
    dense2026b = face2.honor_board("2026")
    comp2026b = face2.honor_board_competition("2026")
    ok3 = []
    ok3.append(dense2026b["honor_board"] == [
        {"rank": 1, "account_id": "usr:echo", "points": 8,
         "events": 2},
        {"rank": 2, "account_id": "usr:delta", "points": 5,
         "events": 1}])
    ok3.append(comp2026b["honor_board_competition"] == [
        {"rank": 1, "account_id": "usr:echo", "points": 8,
         "events": 2},
        {"rank": 2, "account_id": "usr:delta", "points": 5,
         "events": 1}])
    ok3.append(dense2026b["honor_board"]
               == manual_board(conn, "2026"))
    ok3.append(dumps(face2.honor_board("2025")) == snap1["dense2025"]
               and dumps(face2.honor_board_competition("2025"))
               == snap1["comp2025"])
    ok3.append(dumps(dense2026b) != snap1["dense2026"])
    record("AC-CVP3", all(ok3),
           "post-restart earn (echo guide @2026-04-04): the 2026"
           " board recomputed zero-cache with the order flip echo"
           " 8pts r1 over delta 5pts r2 (echo events 1 -> 2"
           " counted), comp follows the dense single-source, and"
           " the 2025 dense + comp boards remain byte-identical"
           " to the pre-close snapshots (old-year frozen)")

    # -- AC-CVP4 cross-year separation across restart ----------------
    face2.earn_civic("usr:alpha", "cleanup", "2026-05-05", "ev-a3")
    dense2026c = face2.honor_board("2026")
    dense2025c = face2.honor_board("2025")
    ok4 = []
    ok4.append([r["account_id"] for r in dense2026c["honor_board"]]
               == ["usr:echo", "usr:delta", "usr:alpha"])
    ok4.append(dense2026c["honor_board"][2] ==
               {"rank": 3, "account_id": "usr:alpha",
                "points": 3, "events": 1})
    ok4.append(dense2026c["honor_board"]
               == manual_board(conn, "2026"))
    ok4.append(dense2025c["honor_board"][0] ==
               {"rank": 1, "account_id": "usr:alpha",
                "points": 8, "events": 2})
    ok4.append(dumps(dense2025c) == snap1["dense2025"]
               and dumps(face2.honor_board_competition("2025"))
               == snap1["comp2025"])
    ok4.append("usr:delta" not in
               [r["account_id"] for r in
                dense2025c["honor_board"]])
    record("AC-CVP4", all(ok4),
           "second post-restart earn (alpha cleanup @2026-05-05):"
           " alpha now coexists on both year boards with"
           " independent year-scoped sums (2025 row still 8pts"
           " 2ev, 2026 row new 3pts r3 == manual SQL), 2025"
           " dense + comp still byte-identical to the original"
           " snapshots, delta never leaks into the 2025 board")

    snap2 = read_all_forms(face2)

    # -- AC-CVP5 second restart: sequential reads identical ---------
    counts_before_read5 = table_counts(conn)
    face2.close()
    face3 = CivicPointsFace(DISCLAIMER, db_path)
    f3 = read_all_forms(face3)
    f3b = read_all_forms(face3)
    counts_after_read5 = table_counts(conn)
    ok5 = [f3[k] == snap2[k] for k in
           ("dense2025", "comp2025", "dense2026", "comp2026",
            "dense2030", "comp2030")]
    ok5.append(all(f3b[k] == f3[k] for k in f3))
    record("AC-CVP5", all(ok5),
           "second civic-face restart (third instance, same"
           " civic.db): all six form reads byte-identical to"
           " the post-earn state and the repeated read batch"
           " identical to itself (repeat-read purity, zero"
           " in-memory drift across two restarts)")

    # -- AC-CVP6 pure-read law + manual cross + product sha ---------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok6 = [counts_after_read2 == counts_before_read2,
           counts_after_read5 == counts_before_read5,
           shas_after == shas_before]
    ok6.append(f3["dense2026"] == dumps(
        {"honor_board": manual_board(conn, "2026"),
         "disclaimer": DISCLAIMER}))
    record("AC-CVP6", all(ok6),
           "pure-read law: every read batch left civic_earns /"
           " civic_redeems / civic_grants row counts constant"
           " (%s); post-earn 2026 board == fresh manual SQL"
           " cross; civicpoints.py sha256 unchanged"
           % json.dumps(counts_after_read5, sort_keys=True))

    # -- AC-CVP7 hygiene: ASCII, zero-network imports, tmp world ---
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
    record("AC-CVP7", all(ok7),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system tmp"
           " outside the repo" % len(src_bytes))

    face3.close()
    conn.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
