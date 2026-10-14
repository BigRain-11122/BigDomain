"""Acceptance suite for the civic behavior distribution read face
(BigDomain R1977; canon = explore-queue civicpoints successor row,
criteria AC-CVD1..CVD6 registered in the R1977 claim note BEFORE
this code existed - honesty law). The face under test is
CivicPointsFace.behavior_distribution: a registry-driven
per-behavior aggregation over the earn ledger (every registered
behavior appears exactly once, zero-earn behaviors keep honest
zero rows). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Usage: python test_civic_distribution.py
"""

import hashlib
import inspect
import io
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import civicpoints as CP                # noqa: E402 (product face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: civic behavior points"
              " are a public-welfare count, not investment advice")

PIN_SCHEMA_SHA = ("ef1d826ed8f2462f2b05d9418d23425cb624c45562bff7"
                  "bec301a4da66405081")
PIN_CFG_SHA = ("32b018fad53fb8bcd8a69357a4c2544886ca750c49734c42bcc"
               "313c3f7160c75")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def table_snapshot(conn, table, order_col):
    rows = conn.execute(
        "SELECT * FROM %s ORDER BY %s" % (table, order_col)).fetchall()
    return canon(rows)


def main():
    tmp = tempfile.mkdtemp(prefix="civic-cvd-")
    face = CP.CivicPointsFace(DISCLAIMER,
                              os.path.join(tmp, "civic.db"))

    # ---- world build: 4 behaviors, mixed ai flags / values / limits
    face.register_behavior("b-volunteer", "volunteer shift", 5, 2, True)
    face.register_behavior("b-report", "civic report", 3, 1, False)
    face.register_behavior("b-recycle", "recycle drop", 2, 10, False)
    face.register_behavior("b-dormant", "dormant behavior", 9, 3, True)

    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01", "ev-a1")
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01", "ev-a2")
    face.earn_civic("usr:bob", "b-volunteer", "2026-10-02", "ev-b1")
    face.earn_civic("usr:alice", "b-report", "2026-10-01", "ev-r1")
    face.earn_civic("usr:carol", "b-report", "2026-10-03", "ev-r2")
    face.earn_civic("usr:bob", "b-recycle", "2026-10-02", "ev-c1")
    face.earn_civic("usr:bob", "b-recycle", "2026-10-02", "ev-c2")
    face.earn_civic("usr:carol", "b-recycle", "2026-10-03", "ev-c3")

    # day-limit gate: b-volunteer daily_limit=2 already consumed by
    # alice on 2026-10-01 -> a third same-day earn must reject
    day_limited = False
    try:
        face.earn_civic("usr:alice", "b-volunteer", "2026-10-01",
                        "ev-a3")
    except CP.CivicError as exc:
        day_limited = (exc.code == CP.E_CV_DAY_LIMIT)
    # idempotent replay gate: same (account, behavior, event_ref)
    # must reject with E_CV_DUP_EARN
    replay_rejected = False
    try:
        face.earn_civic("usr:alice", "b-volunteer", "2026-10-01",
                        "ev-a1")
    except CP.CivicError as exc:
        replay_rejected = (exc.code == CP.E_CV_DUP_EARN)

    board = face.behavior_distribution()["behavior_distribution"]

    # ---- AC-CVD1: registry-complete world face
    reg_ids = [r["behavior_id"] for r in board]
    cvd1 = (sorted(reg_ids) == ["b-dormant", "b-recycle", "b-report",
                                "b-volunteer"]
            and len(board) == 4
            and day_limited and replay_rejected)
    by_id = {r["behavior_id"]: r for r in board}
    dorm = by_id.get("b-dormant", {})
    cvd1 = cvd1 and dorm.get("events") == 0 and dorm.get(
        "total_points") == 0 and dorm.get("participants") == 0 and \
        dorm.get("last_day") is None
    # independent GROUP BY recount straight through a second
    # sqlite connection (checker-side, not product-side)
    chk = sqlite3.connect(os.path.join(tmp, "civic.db"))
    recount = {}
    for row in chk.execute(
            "SELECT behavior_id, COUNT(*), COALESCE(SUM(points),0),"
            " COUNT(DISTINCT account_id), MAX(at_day) FROM"
            " civic_earns GROUP BY behavior_id"):
        recount[row[0]] = (int(row[1]), int(row[2]), int(row[3]),
                           row[4])
    for bid, (events, points, parts, last_day) in recount.items():
        row = by_id.get(bid, {})
        cvd1 = cvd1 and row.get("events") == events and row.get(
            "total_points") == points and row.get(
            "participants") == parts and row.get("last_day") == last_day
    expected_top = {"b-volunteer": (3, 15, 2, "2026-10-02"),
                    "b-report": (2, 6, 2, "2026-10-03"),
                    "b-recycle": (3, 6, 2, "2026-10-03")}
    for bid, want in expected_top.items():
        row = by_id.get(bid, {})
        cvd1 = cvd1 and (row.get("events"), row.get("total_points"),
                         row.get("participants"),
                         row.get("last_day")) == want
    record("AC-CVD1", cvd1,
           "registry-complete 4 rows, dormant honest-zero row, "
           "aggregates == independent GROUP BY recount, "
           "day-limit=%s replay-reject=%s" % (day_limited,
                                               replay_rejected))
    chk.close()

    # ---- AC-CVD2: cross-source recount via points_view per account
    per_behavior = {}
    for account in ("usr:alice", "usr:bob", "usr:carol"):
        view = face.points_view(account)
        for event in view["earn_events"]:
            key = event["behavior_id"]
            agg = per_behavior.setdefault(key, [0, 0, set()])
            agg[0] += 1
            agg[1] += event["points"]
            agg[2].add(account)
    cvd2 = True
    for bid, (events, points, parts) in per_behavior.items():
        row = by_id.get(bid, {})
        cvd2 = cvd2 and row.get("events") == events and row.get(
            "total_points") == points and row.get(
            "participants") == len(parts)
    cvd2 = cvd2 and "b-dormant" not in per_behavior
    record("AC-CVD2", cvd2,
           "per-behavior recount from points_view streams matches "
           "board aggregates for %d behaviors" % len(per_behavior))

    # ---- AC-CVD3: deterministic order + double-call byte identity
    order = [r["behavior_id"] for r in board]
    cvd3 = order == ["b-volunteer", "b-recycle", "b-report",
                     "b-dormant"]
    first = canon(face.behavior_distribution())
    second = canon(face.behavior_distribution())
    cvd3 = cvd3 and first == second
    # behavior_id tie-break world: same total AND same events ->
    # behavior_id ASC decides (fresh face, fresh db)
    face2 = CP.CivicPointsFace(
        DISCLAIMER, os.path.join(tmp, "civic-tie.db"))
    face2.register_behavior("b-zeta", "zeta tie", 2, 5, False)
    face2.register_behavior("b-alpha", "alpha tie", 2, 5, False)
    face2.earn_civic("usr:alice", "b-zeta", "2026-10-01", "ev-z1")
    face2.earn_civic("usr:alice", "b-alpha", "2026-10-01", "ev-y1")
    tie_order = [r["behavior_id"] for r in
                 face2.behavior_distribution()["behavior_distribution"]]
    cvd3 = cvd3 and tie_order == ["b-alpha", "b-zeta"]
    face2.close()
    record("AC-CVD3", cvd3,
           "order %s; double-call byte-identical; tie world order %s"
           % (order, tie_order))

    # ---- AC-CVD4: pure-read law across a read batch
    chk = sqlite3.connect(os.path.join(tmp, "civic.db"))
    tables = [("civic_behaviors", "behavior_id"),
              ("civic_earns", "earn_id"),
              ("civic_rewards", "reward_id"),
              ("civic_redeems", "redeem_id"),
              ("civic_grants", "grant_id")]
    before = {t: table_snapshot(chk, t, oc) for t, oc in tables}
    face.behavior_distribution()
    face.behavior_board()
    face.reward_board()
    for account in ("usr:alice", "usr:bob", "usr:carol"):
        face.points_view(account)
    face.behavior_distribution()
    chk2 = sqlite3.connect(os.path.join(tmp, "civic.db"))
    after = {t: table_snapshot(chk2, t, oc) for t, oc in tables}
    cvd4 = before == after
    record("AC-CVD4", cvd4,
           "five-table row sets and counts constant across the "
           "read batch (zero write side effects)")
    chk.close()
    chk2.close()

    # ---- AC-CVD5: honest empty faces + envelope law
    face3 = CP.CivicPointsFace(
        DISCLAIMER, os.path.join(tmp, "civic-empty.db"))
    empty = face3.behavior_distribution()
    cvd5 = empty["behavior_distribution"] == [] and empty[
        "disclaimer"] == DISCLAIMER
    face3.close()
    for row in board:
        cvd5 = cvd5 and row.get("ai_label") in (0, 1) and isinstance(
            row.get("title"), str)
    env = face.behavior_distribution()
    cvd5 = cvd5 and env["disclaimer"] == DISCLAIMER and all(
        "ai_label" in r for r in env["behavior_distribution"])
    record("AC-CVD5", cvd5,
           "zero-registry face returns an honest empty board; "
           "ai_label on every row; disclaimer on every envelope")

    # ---- AC-CVD6: isolation + hygiene
    params = [p for p in inspect.signature(
        CP.CivicPointsFace.__init__).parameters]
    schema_sha = hashlib.sha256(
        CP._SCHEMA.encode("utf-8")).hexdigest()
    cfg_path = os.path.join(BASE, "config.json")
    cfg_sha = hashlib.sha256(
        open(cfg_path, "rb").read()).hexdigest() if os.path.exists(
        cfg_path) else None
    src_path = os.path.abspath(__file__)
    src = open(src_path, "rb").read()
    ascii_ok = all(b < 128 for b in src)
    import_lines = [ln.strip() for ln in src.decode("ascii").split(
        "\n") if ln.strip().startswith("import ") or ln.strip(
        ).startswith("from ")]
    net_ok = not any(
        any(w in ln for w in ("urllib", "requests", "socket", "http"))
        for ln in import_lines)
    cvd6 = (params == ["self", "disclaimer", "db_path"]
            and schema_sha == PIN_SCHEMA_SHA
            and cfg_sha == PIN_CFG_SHA
            and ascii_ok and net_ok)
    record("AC-CVD6", cvd6,
           "ctor params=%s; schema sha pinned; config sha pinned; "
           "ascii=%s; no-network-imports=%s" % (params, ascii_ok,
                                                net_ok))

    face.close()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d criteria, %d pass, %d fail" % (
        "PASS" if not failed else "FAIL", len(RESULTS),
        len(RESULTS) - len(failed), len(failed)), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
