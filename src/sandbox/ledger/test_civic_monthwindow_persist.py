"""Acceptance suite for the civic behavior-distribution
month-window read-face cross-restart persistence example window
(BigDomain R1998; canon = the R1997-reseeded explore-queue row
claimed by R1998, criteria AC-CVMP1..CVMP7 registered in the
claim note BEFORE this code existed - honesty law; AC-CVMP
prefix git-grep zero-occupancy anchored 2026-10-15).

Face under proof: CivicPointsFace.behavior_distribution(window)
- the R1977 registry-driven per-behavior aggregation with the
R1997 explicit strict YYYY-MM month-window slice. Persistence
substrate: the append-only civic_earns / civic_behaviors rows;
the read face is a read-time derivation with zero cached state,
so the suite pins derived purity across instance restarts:

  - pre-close five-form pinning (default full-window + explicit
    2026-09 / 2026-10 / 2026-11 / 2026-12 windows) with exact
    aggregates, envelope key laws and an independent manual SQL
    GROUP BY cross;
  - close -> new instance over the same civic.db: all five
    forms byte-identical;
  - post-restart earn inside the October window: zero-cache
    window recompute, old September window frozen
    byte-identical, empty windows stay honest zero;
  - post-restart behavior registration + November earns:
    registry continuation across restart (the new behavior
    appears on every window board - zero rows on old windows,
    first content on the November window), original-behavior
    earn-side aggregates frozen on old windows;
  - second restart third instance: sequential reads
    byte-identical, repeat-read purity;
  - pure-read law, manual SQL crosses at the end state,
    product-file sha256 double-proof (suite-only round, zero
    product-code changes), hygiene.

Usage: python test_civic_monthwindow_persist.py
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
        return face.behavior_distribution()["behavior_distribution"]
    return face.behavior_distribution(window)["behavior_distribution"]


def agg_of(board, behavior_id):
    for row in board:
        if row["behavior_id"] == behavior_id:
            return (row["events"], row["total_points"],
                    row["participants"], row["last_day"])
    return None


def manual_distribution(conn, window):
    """Independent second derivation over the same rows: registry
    row-set authority + GROUP BY aggregates with the window LIKE
    filter, zero-filled for dormant behaviors, sorted by
    (-total_points, -events, behavior_id ASC)."""
    regs = conn.execute(
        "SELECT behavior_id, title, points_per_event, ai_label"
        " FROM civic_behaviors").fetchall()
    if window is None:
        agg = conn.execute(
            "SELECT behavior_id, COUNT(*), COALESCE(SUM(points),0),"
            " COUNT(DISTINCT account_id), MAX(at_day)"
            " FROM civic_earns GROUP BY behavior_id").fetchall()
    else:
        agg = conn.execute(
            "SELECT behavior_id, COUNT(*), COALESCE(SUM(points),0),"
            " COUNT(DISTINCT account_id), MAX(at_day)"
            " FROM civic_earns WHERE at_day LIKE ?"
            " GROUP BY behavior_id", (window + "-%",)).fetchall()
    counts = {r[0]: (int(r[1]), int(r[2]), int(r[3]), r[4])
              for r in agg}
    board = []
    for behavior_id, title, points_per_event, ai_label in regs:
        events, total_points, participants, last_day = counts.get(
            behavior_id, (0, 0, 0, None))
        board.append({"behavior_id": behavior_id, "title": title,
                      "points_per_event": int(points_per_event),
                      "ai_label": int(ai_label),
                      "events": events,
                      "total_points": total_points,
                      "participants": participants,
                      "last_day": last_day})
    board.sort(key=lambda r: (-r["total_points"], -r["events"],
                              r["behavior_id"]))
    return board


def read_all_forms(face):
    """Read every window form under proof once, return dict of
    dumps (byte-comparable snapshots)."""
    out = {}
    for key, window in FORMS:
        if window is None:
            env = face.behavior_distribution()
        else:
            env = face.behavior_distribution(window)
        out[key] = dumps(env)
    return out


def earn_count(conn):
    return int(conn.execute(
        "SELECT COUNT(*) FROM civic_earns").fetchone()[0])


def build_world(face):
    """True product path world (the R1997 month-window shape):
    4 behaviors incl. a dormant one, earns across September and
    October."""
    face.register_behavior("b-volunteer", "volunteer shift", 5, 2,
                           True)
    face.register_behavior("b-report", "civic report", 3, 1, False)
    face.register_behavior("b-recycle", "recycle drop", 2, 10,
                           False)
    face.register_behavior("b-dormant", "dormant behavior", 9, 3,
                           True)
    # September earns
    face.earn_civic("usr:alice", "b-volunteer", "2026-09-28",
                    "ev-s1")
    face.earn_civic("usr:carol", "b-recycle", "2026-09-30", "ev-s2")
    # October earns
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01",
                    "ev-a1")
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01",
                    "ev-a2")
    face.earn_civic("usr:bob", "b-volunteer", "2026-10-02", "ev-b1")
    face.earn_civic("usr:alice", "b-report", "2026-10-01", "ev-r1")
    face.earn_civic("usr:carol", "b-report", "2026-10-03", "ev-r2")
    face.earn_civic("usr:bob", "b-recycle", "2026-10-02", "ev-c1")
    face.earn_civic("usr:bob", "b-recycle", "2026-10-02", "ev-c2")
    face.earn_civic("usr:carol", "b-recycle", "2026-10-03", "ev-c3")


def main():
    tmp = tempfile.mkdtemp(prefix="civic-mw-persist-")
    db_path = os.path.join(tmp, "civic.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    face = CivicPointsFace(DISCLAIMER, db_path)
    build_world(face)
    conn = sqlite3.connect(db_path)

    # -- AC-CVMP1 control anchor: pre-close five-form pinning -----
    full_env = face.behavior_distribution()
    w09_env = face.behavior_distribution("2026-09")
    w10_env = face.behavior_distribution("2026-10")
    w11_env = face.behavior_distribution("2026-11")
    w12_env = face.behavior_distribution("2026-12")
    ok1 = []
    ok1.append(sorted(full_env.keys()) == [
        "behavior_distribution", "disclaimer"])
    ok1.append(all(sorted(e.keys()) == [
        "behavior_distribution", "disclaimer", "window"]
        for e in (w09_env, w10_env, w11_env, w12_env)))
    ok1.append(w09_env["window"] == "2026-09"
               and w10_env["window"] == "2026-10"
               and w11_env["window"] == "2026-11"
               and w12_env["window"] == "2026-12")
    ok1.append(agg_of(full_env["behavior_distribution"],
                      "b-volunteer") == (4, 20, 2, "2026-10-02")
               and agg_of(full_env["behavior_distribution"],
                          "b-report") == (2, 6, 2, "2026-10-03")
               and agg_of(full_env["behavior_distribution"],
                          "b-recycle") == (4, 8, 2, "2026-10-03")
               and agg_of(full_env["behavior_distribution"],
                          "b-dormant") == (0, 0, 0, None))
    ok1.append(agg_of(w09_env["behavior_distribution"],
                      "b-volunteer") == (1, 5, 1, "2026-09-28")
               and agg_of(w09_env["behavior_distribution"],
                          "b-recycle") == (1, 2, 1, "2026-09-30")
               and agg_of(w09_env["behavior_distribution"],
                          "b-report") == (0, 0, 0, None)
               and agg_of(w09_env["behavior_distribution"],
                          "b-dormant") == (0, 0, 0, None))
    ok1.append(agg_of(w10_env["behavior_distribution"],
                      "b-volunteer") == (3, 15, 2, "2026-10-02")
               and agg_of(w10_env["behavior_distribution"],
                          "b-report") == (2, 6, 2, "2026-10-03")
               and agg_of(w10_env["behavior_distribution"],
                          "b-recycle") == (3, 6, 2, "2026-10-03")
               and agg_of(w10_env["behavior_distribution"],
                          "b-dormant") == (0, 0, 0, None))
    ok1.append(all(agg_of(e["behavior_distribution"], b) == (0, 0, 0,
                   None) for e in (w11_env, w12_env)
                   for b in ("b-volunteer", "b-report", "b-recycle",
                             "b-dormant")))
    ok1.append([r["behavior_id"] for r
                in full_env["behavior_distribution"]] == [
        "b-volunteer", "b-recycle", "b-report", "b-dormant"])
    ok1.append([r["behavior_id"] for r
                in w09_env["behavior_distribution"]] == [
        "b-volunteer", "b-recycle", "b-dormant", "b-report"])
    ok1.append([r["behavior_id"] for r
                in w10_env["behavior_distribution"]] == [
        "b-volunteer", "b-recycle", "b-report", "b-dormant"])
    ok1.append([r["behavior_id"] for r
                in w11_env["behavior_distribution"]] == [
        "b-dormant", "b-recycle", "b-report", "b-volunteer"]
        and [r["behavior_id"] for r
             in w12_env["behavior_distribution"]] == [
        "b-dormant", "b-recycle", "b-report", "b-volunteer"])
    ok1.append(face.behavior_distribution()["behavior_distribution"]
               == manual_distribution(conn, None)
               and face.behavior_distribution(
                   "2026-09")["behavior_distribution"]
               == manual_distribution(conn, "2026-09")
               and face.behavior_distribution(
                   "2026-10")["behavior_distribution"]
               == manual_distribution(conn, "2026-10")
               and face.behavior_distribution(
                   "2026-11")["behavior_distribution"]
               == manual_distribution(conn, "2026-11")
               and face.behavior_distribution(
                   "2026-12")["behavior_distribution"]
               == manual_distribution(conn, "2026-12"))
    ok1.append(dumps(face.behavior_distribution()) == dumps(
        face.behavior_distribution()))
    record("AC-CVMP1", all(ok1),
           "pre-close pinning: default envelope keys %s, window"
           " envelopes additive window key; full aggregates"
           " volunteer 4/20/2/2026-10-02, report 2/6/2/2026-10-03,"
           " recycle 4/8/2/2026-10-03, dormant 0/0/0/None; 2026-09"
           " volunteer 1/5/1 + recycle 1/2/1; 2026-10 volunteer"
           " 3/15/2 + report 2/6/2 + recycle 3/6/2; empty 2026-11"
           " / 2026-12 registry-complete zero boards; deterministic"
           " order law all forms; all five forms == independent"
           " manual SQL GROUP BY cross; double-call identical"
           % sorted(full_env.keys()))
    snap1 = read_all_forms(face)

    # -- AC-CVMP2 restart: byte-identical five forms ---------------
    counts_before_read2 = earn_count(conn)
    face.close()
    face2 = CivicPointsFace(DISCLAIMER, db_path)
    snap2 = read_all_forms(face2)
    counts_after_read2 = earn_count(conn)
    ok2 = [snap2[k] == snap1[k] for k in
           ("full", "w09", "w10", "w11", "w12")]
    record("AC-CVMP2", all(ok2),
           "CivicPointsFace close -> new instance over the same"
           " civic.db: default + 2026-09 + 2026-10 + 2026-11 +"
           " 2026-12 window reads all byte-identical to the"
           " pre-close snapshots (sort_keys dumps; zero"
           " in-memory drift in the derived month-window read"
           " face)")

    # -- AC-CVMP3 post-restart earn: zero-cache window recompute ----
    face2.earn_civic("usr:dave", "b-volunteer", "2026-10-05",
                     "ev-d1")
    w10_b = face2.behavior_distribution("2026-10")
    full_b = face2.behavior_distribution()
    ok3 = []
    ok3.append(agg_of(w10_b["behavior_distribution"],
                      "b-volunteer") == (4, 20, 3, "2026-10-05"))
    ok3.append(agg_of(full_b["behavior_distribution"],
                      "b-volunteer") == (5, 25, 3, "2026-10-05"))
    ok3.append(w10_b["behavior_distribution"]
               == manual_distribution(conn, "2026-10")
               and full_b["behavior_distribution"]
               == manual_distribution(conn, None))
    ok3.append(dumps(face2.behavior_distribution("2026-09"))
               == snap1["w09"])
    ok3.append(dumps(face2.behavior_distribution("2026-11"))
               == snap1["w11"]
               and dumps(face2.behavior_distribution("2026-12"))
               == snap1["w12"])
    record("AC-CVMP3", all(ok3),
           "post-restart earn (dave volunteer @2026-10-05):"
           " October window recomputed zero-cache (volunteer"
           " 4/20/3/2026-10-05, participants 2 -> 3) and the"
           " full-window face follows (5/25/3/2026-10-05), both"
           " == manual SQL cross; the September window read stays"
           " byte-identical to the pre-close snapshot (old-window"
           " frozen); empty 2026-11 / 2026-12 windows stay honest"
           " zero")
    snap3 = read_all_forms(face2)

    # -- AC-CVMP4 post-restart registration + new-month earn --------
    face2.register_behavior("b-newmoon", "new moon", 4, 5, True)
    face2.earn_civic("usr:alice", "b-report", "2026-11-01", "ev-n1")
    face2.earn_civic("usr:alice", "b-newmoon", "2026-11-02", "ev-n2")
    w11_c = face2.behavior_distribution("2026-11")
    w09_c = face2.behavior_distribution("2026-09")
    w10_c = face2.behavior_distribution("2026-10")
    full_c = face2.behavior_distribution()
    ok4 = []
    ok4.append(agg_of(w11_c["behavior_distribution"],
                      "b-newmoon") == (1, 4, 1, "2026-11-02")
               and agg_of(w11_c["behavior_distribution"],
                          "b-report") == (1, 3, 1, "2026-11-01"))
    ok4.append([r["behavior_id"] for r
                in w11_c["behavior_distribution"]] == [
        "b-newmoon", "b-report", "b-dormant", "b-recycle",
        "b-volunteer"])
    ok4.append(agg_of(w09_c["behavior_distribution"],
                      "b-volunteer") == (1, 5, 1, "2026-09-28")
               and agg_of(w09_c["behavior_distribution"],
                          "b-recycle") == (1, 2, 1, "2026-09-30")
               and agg_of(w09_c["behavior_distribution"],
                          "b-newmoon") == (0, 0, 0, None))
    ok4.append(agg_of(w10_c["behavior_distribution"],
                      "b-volunteer") == (4, 20, 3, "2026-10-05")
               and agg_of(w10_c["behavior_distribution"],
                          "b-recycle") == (3, 6, 2, "2026-10-03")
               and agg_of(w10_c["behavior_distribution"],
                          "b-report") == (2, 6, 2, "2026-10-03")
               and agg_of(w10_c["behavior_distribution"],
                          "b-newmoon") == (0, 0, 0, None))
    ok4.append(agg_of(full_c["behavior_distribution"],
                      "b-volunteer") == (5, 25, 3, "2026-10-05")
               and agg_of(full_c["behavior_distribution"],
                          "b-report") == (3, 9, 2, "2026-11-01")
               and agg_of(full_c["behavior_distribution"],
                          "b-recycle") == (4, 8, 2, "2026-10-03")
               and agg_of(full_c["behavior_distribution"],
                          "b-newmoon") == (1, 4, 1, "2026-11-02")
               and agg_of(full_c["behavior_distribution"],
                          "b-dormant") == (0, 0, 0, None))
    ok4.append([r["behavior_id"] for r
                in full_c["behavior_distribution"]] == [
        "b-volunteer", "b-report", "b-recycle", "b-newmoon",
        "b-dormant"])
    ok4.append(w09_c["behavior_distribution"]
               == manual_distribution(conn, "2026-09")
               and w10_c["behavior_distribution"]
               == manual_distribution(conn, "2026-10")
               and w11_c["behavior_distribution"]
               == manual_distribution(conn, "2026-11")
               and face2.behavior_distribution(
                   "2026-12")["behavior_distribution"]
               == manual_distribution(conn, "2026-12")
               and full_c["behavior_distribution"]
               == manual_distribution(conn, None))
    newmoon_row = [r for r
                   in face2.behavior_distribution("2026-12")[
                       "behavior_distribution"]
                   if r["behavior_id"] == "b-newmoon"][0]
    ok4.append(newmoon_row["events"] == 0
               and newmoon_row["total_points"] == 0
               and newmoon_row["last_day"] is None
               and newmoon_row["ai_label"] == 1)
    record("AC-CVMP4", all(ok4),
           "post-restart registration (b-newmoon ai_label=1) +"
           " November earns (alice report @11-01, alice newmoon"
           " @11-02): registry continuation across restart - the"
           " new behavior appears on every window board (honest"
           " zero rows on 2026-09 / 2026-10 / 2026-12, first"
           " content 1/4/1/2026-11-02 on the 2026-11 window with"
           " report 1/3/1/2026-11-01); original-behavior"
           " earn-side aggregates frozen on the September and"
           " October windows; full-window end state volunteer"
           " 5/25/3 + report 3/9/2 + recycle 4/8/2 + newmoon"
           " 1/4/1 + dormant 0 in deterministic order; all five"
           " forms == independent manual SQL cross")
    snap4 = read_all_forms(face2)

    # -- AC-CVMP5 second restart: sequential reads identical -------
    counts_before_read5 = earn_count(conn)
    face2.close()
    face3 = CivicPointsFace(DISCLAIMER, db_path)
    snap5 = read_all_forms(face3)
    snap5b = read_all_forms(face3)
    counts_after_read5 = earn_count(conn)
    ok5 = [snap5[k] == snap4[k] for k in
           ("full", "w09", "w10", "w11", "w12")]
    ok5.append(all(snap5b[k] == snap5[k] for k in snap5))
    record("AC-CVMP5", all(ok5),
           "second civic-face restart (third instance, same"
           " civic.db): all five window-form reads byte-identical"
           " to the post-registration state and the repeated read"
           " batch identical to itself (repeat-read purity, zero"
           " in-memory drift across two restarts)")

    # -- AC-CVMP6 pure-read law + manual cross + product sha --------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok6 = [counts_after_read2 == counts_before_read2,
           counts_after_read5 == counts_before_read5,
           shas_after == shas_before]
    ok6.append(face3.behavior_distribution()["behavior_distribution"]
               == manual_distribution(conn, None)
               and face3.behavior_distribution(
                   "2026-09")["behavior_distribution"]
               == manual_distribution(conn, "2026-09")
               and face3.behavior_distribution(
                   "2026-10")["behavior_distribution"]
               == manual_distribution(conn, "2026-10")
               and face3.behavior_distribution(
                   "2026-11")["behavior_distribution"]
               == manual_distribution(conn, "2026-11")
               and face3.behavior_distribution(
                   "2026-12")["behavior_distribution"]
               == manual_distribution(conn, "2026-12"))
    record("AC-CVMP6", all(ok6),
           "pure-read law: every read batch left the civic_earns"
           " row count constant (%d == %d, %d == %d); end-state"
           " five-form boards == fresh manual SQL crosses;"
           " civicpoints.py sha256 unchanged (suite-only round)"
           % (counts_before_read2, counts_after_read2,
              counts_before_read5, counts_after_read5))

    # -- AC-CVMP7 hygiene: ASCII, zero-network, tmp world -----------
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
    record("AC-CVMP7", all(ok7),
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
