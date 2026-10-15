"""Acceptance suite for the civic behavior distribution
month-window read face (BigDomain R1997; canon = explore-queue
civicpoints successor row, criteria AC-CVM1..CVM7 registered in
the R1997 claim note BEFORE this code existed - honesty law).
The face under test is CivicPointsFace.behavior_distribution(
window=None): the R1977 registry-driven per-behavior aggregation
extended with an explicit strict YYYY-MM month-window slice
(cross-window separation, honest zero aggregates for empty
windows, byte-identical default full-window mode). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_civic_monthwindow.py
"""

import ast
import hashlib
import inspect
import json
import os
import sqlite3
import sys
import tempfile
import textwrap

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

TABLES = [("civic_behaviors", "behavior_id"),
          ("civic_earns", "earn_id"),
          ("civic_rewards", "reward_id"),
          ("civic_redeems", "redeem_id"),
          ("civic_grants", "grant_id")]


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


def agg_of(board_env, behavior_id):
    for row in board_env["behavior_distribution"]:
        if row["behavior_id"] == behavior_id:
            return (row["events"], row["total_points"],
                    row["participants"], row["last_day"])
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="civic-cvm-")
    face = CP.CivicPointsFace(DISCLAIMER,
                              os.path.join(tmp, "civic.db"))

    # ---- world build: 4 behaviors, earns across two months
    face.register_behavior("b-volunteer", "volunteer shift", 5, 2, True)
    face.register_behavior("b-report", "civic report", 3, 1, False)
    face.register_behavior("b-recycle", "recycle drop", 2, 10, False)
    face.register_behavior("b-dormant", "dormant behavior", 9, 3, True)

    # September earns
    face.earn_civic("usr:alice", "b-volunteer", "2026-09-28", "ev-s1")
    face.earn_civic("usr:carol", "b-recycle", "2026-09-30", "ev-s2")
    # October earns (the R1977 world shape inside the month)
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01", "ev-a1")
    face.earn_civic("usr:alice", "b-volunteer", "2026-10-01", "ev-a2")
    face.earn_civic("usr:bob", "b-volunteer", "2026-10-02", "ev-b1")
    face.earn_civic("usr:alice", "b-report", "2026-10-01", "ev-r1")
    face.earn_civic("usr:carol", "b-report", "2026-10-03", "ev-r2")
    face.earn_civic("usr:bob", "b-recycle", "2026-10-02", "ev-c1")
    face.earn_civic("usr:bob", "b-recycle", "2026-10-02", "ev-c2")
    face.earn_civic("usr:carol", "b-recycle", "2026-10-03", "ev-c3")

    # ---- AC-CVM1: default full-window zero drift
    default_env = face.behavior_distribution()
    cvm1 = sorted(default_env.keys()) == [
        "behavior_distribution", "disclaimer"]
    board = default_env["behavior_distribution"]
    cvm1 = cvm1 and sorted(r["behavior_id"] for r in board) == [
        "b-dormant", "b-recycle", "b-report", "b-volunteer"]
    full_expected = {
        "b-volunteer": (4, 20, 2, "2026-10-02"),
        "b-report": (2, 6, 2, "2026-10-03"),
        "b-recycle": (4, 8, 2, "2026-10-03"),
        "b-dormant": (0, 0, 0, None)}
    for bid, want in full_expected.items():
        cvm1 = cvm1 and agg_of(default_env, bid) == want
    first = canon(face.behavior_distribution())
    second = canon(face.behavior_distribution())
    cvm1 = cvm1 and first == second and default_env[
        "disclaimer"] == DISCLAIMER
    record("AC-CVM1", cvm1,
           "default envelope keys sorted=%s; full aggregates=%s; "
           "double-call byte-identical=%s"
           % (sorted(default_env.keys()), full_expected,
              first == second))

    # ---- AC-CVM2: strict window validation, zero side effects
    bad_windows = ["2026-13", "2026-00", "2026/10", "2026-1",
                   "2026-010", " 2026-10", "2026-10 ", "2026-10\n",
                   "2026-10-05", "abc", "", "2026-1004", 2026, True,
                   "202610", "2026-10-05x"]
    chk = sqlite3.connect(os.path.join(tmp, "civic.db"))
    before_counts = {t: chk.execute(
        "SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t, _ in TABLES}
    all_rejected = True
    for bad in bad_windows:
        rejected = False
        try:
            face.behavior_distribution(window=bad)
        except CP.CivicError as exc:
            rejected = (exc.code == CP.E_CV_BAD_WINDOW)
        all_rejected = all_rejected and rejected
    after_counts = {t: chk.execute(
        "SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t, _ in TABLES}
    none_ok = canon(face.behavior_distribution(window=None)) == first
    cvm2 = all_rejected and before_counts == after_counts and none_ok
    record("AC-CVM2", cvm2,
           "%d bad window forms all E_CV_BAD_WINDOW; five-table "
           "counts constant; window=None == default face"
           % len(bad_windows))

    # ---- AC-CVM3: month slicing + cross-window separation
    oct_env = face.behavior_distribution(window="2026-10")
    sep_env = face.behavior_distribution(window="2026-09")
    oct_expected = {
        "b-volunteer": (3, 15, 2, "2026-10-02"),
        "b-report": (2, 6, 2, "2026-10-03"),
        "b-recycle": (3, 6, 2, "2026-10-03"),
        "b-dormant": (0, 0, 0, None)}
    sep_expected = {
        "b-volunteer": (1, 5, 1, "2026-09-28"),
        "b-report": (0, 0, 0, None),
        "b-recycle": (1, 2, 1, "2026-09-30"),
        "b-dormant": (0, 0, 0, None)}
    cvm3 = True
    for bid, want in oct_expected.items():
        cvm3 = cvm3 and agg_of(oct_env, bid) == want
    for bid, want in sep_expected.items():
        cvm3 = cvm3 and agg_of(sep_env, bid) == want
    # independent prefix-filter recount straight through a second
    # sqlite connection (checker-side, not product-side)
    for win, env in (("2026-10", oct_env), ("2026-09", sep_env)):
        recount = {}
        for row in chk.execute(
                "SELECT behavior_id, COUNT(*),"
                " COALESCE(SUM(points),0),"
                " COUNT(DISTINCT account_id), MAX(at_day)"
                " FROM civic_earns WHERE at_day LIKE ?"
                " GROUP BY behavior_id", (win + "-%",)):
            recount[row[0]] = (int(row[1]), int(row[2]), int(row[3]),
                               row[4])
        for row in env["behavior_distribution"]:
            cvm3 = cvm3 and (recount.get(row["behavior_id"],
                                          (0, 0, 0, None))
                             == (row["events"], row["total_points"],
                                 row["participants"], row["last_day"]))
    record("AC-CVM3", cvm3,
           "oct=%s sep=%s; both == independent prefix-filter "
           "recount; zero cross-month leakage either direction"
           % (oct_expected, sep_expected))

    # ---- AC-CVM4: out-of-window honest zero + additive key
    dec_env = face.behavior_distribution(window="2026-12")
    far_env = face.behavior_distribution(window="2099-01")
    cvm4 = (sorted(dec_env.keys()) == ["behavior_distribution",
                                       "disclaimer", "window"]
            and dec_env["window"] == "2026-12"
            and far_env["window"] == "2099-01")
    zero_agg = (0, 0, 0, None)
    for env in (dec_env, far_env):
        cvm4 = cvm4 and sorted(r["behavior_id"] for r in env[
            "behavior_distribution"]) == ["b-dormant", "b-recycle",
                                          "b-report", "b-volunteer"]
        for bid in ("b-dormant", "b-recycle", "b-report",
                    "b-volunteer"):
            cvm4 = cvm4 and agg_of(env, bid) == zero_agg
    record("AC-CVM4", cvm4,
           "empty windows 2026-12/2099-01 keep registry-complete "
           "all-zero board; explicit envelope window key additive")

    # ---- AC-CVM5: default-vs-explicit cross + determinism
    # additive aggregates (events, total_points) obey the sum law
    # over the month partition; participants is a COUNT(DISTINCT)
    # and obeys the set-union law instead (an account active in
    # both months counts once in the full window) - the suite
    # first drafted a plain sum for all four columns, the red run
    # exposed the union dimension, the assertion was corrected to
    # the partition-correct math same round (product behavior was
    # already right; honest erratum, R1996 AC-CJM6 precedent).
    cvm5 = True
    for bid in ("b-volunteer", "b-report", "b-recycle", "b-dormant"):
        full = agg_of(default_env, bid)
        oct_row = agg_of(oct_env, bid)
        sep_row = agg_of(sep_env, bid)
        cvm5 = cvm5 and full[0] == oct_row[0] + sep_row[0]
        cvm5 = cvm5 and full[1] == oct_row[1] + sep_row[1]
        union_size = chk.execute(
            "SELECT COUNT(DISTINCT account_id) FROM civic_earns"
            " WHERE behavior_id = ? AND (at_day LIKE '2026-10-%'"
            " OR at_day LIKE '2026-09-%')", (bid,)).fetchone()[0]
        cvm5 = cvm5 and full[2] == int(union_size)
    win_first = canon(face.behavior_distribution(window="2026-10"))
    win_second = canon(face.behavior_distribution(window="2026-10"))
    cvm5 = cvm5 and win_first == win_second
    oct_order = [r["behavior_id"] for r in oct_env[
        "behavior_distribution"]]
    cvm5 = cvm5 and oct_order == ["b-volunteer", "b-recycle",
                                  "b-report", "b-dormant"]
    # tie world registered in reverse-id order: windowed order still
    # resolves on behavior_id ASC (zero insertion-order key)
    face2 = CP.CivicPointsFace(
        DISCLAIMER, os.path.join(tmp, "civic-tie.db"))
    face2.register_behavior("b-zeta", "zeta tie", 2, 5, False)
    face2.register_behavior("b-alpha", "alpha tie", 2, 5, False)
    face2.earn_civic("usr:alice", "b-zeta", "2026-10-01", "ev-z1")
    face2.earn_civic("usr:alice", "b-alpha", "2026-09-05", "ev-y1")
    tie_full = [r["behavior_id"] for r in face2.behavior_distribution()[
        "behavior_distribution"]]
    tie_oct = [r["behavior_id"] for r in face2.behavior_distribution(
        window="2026-10")["behavior_distribution"]]
    tie_sep = [r["behavior_id"] for r in face2.behavior_distribution(
        window="2026-09")["behavior_distribution"]]
    cvm5 = cvm5 and tie_full == ["b-alpha", "b-zeta"] and tie_oct == [
        "b-zeta", "b-alpha"] and tie_sep == ["b-alpha", "b-zeta"]
    face2.close()
    record("AC-CVM5", cvm5,
           "additive sum law events/total_points + participants "
           "set-union law per behavior; windowed double-call "
           "byte-identical; oct order %s; tie world full=%s oct=%s "
           "sep=%s (id ASC, zero insertion-order key)"
           % (oct_order, tie_full, tie_oct, tie_sep))

    # ---- AC-CVM6: pure-read law across a mixed windowed batch
    before = {t: table_snapshot(chk, t, oc) for t, oc in TABLES}
    face.behavior_distribution()
    face.behavior_distribution(window="2026-09")
    face.behavior_distribution(window="2026-10")
    face.behavior_distribution(window="2026-11")
    face.behavior_distribution(window="2099-01")
    face.behavior_distribution()
    chk2 = sqlite3.connect(os.path.join(tmp, "civic.db"))
    after = {t: table_snapshot(chk2, t, oc) for t, oc in TABLES}
    src = inspect.getsource(CP.CivicPointsFace.behavior_distribution)
    tree = ast.parse(textwrap.dedent(src))
    fn = tree.body[0]
    write_hits = []
    for node in ast.walk(fn):
        if (isinstance(node, ast.Constant)
                and isinstance(node.value, str)):
            head = node.value.strip().upper()
            if head.startswith(("INSERT", "REPLACE INTO", "DELETE")):
                write_hits.append(node.value.strip())
    stmts = [n.value.strip().upper() for n in ast.walk(fn)
             if isinstance(n, ast.Constant)
             and isinstance(n.value, str)
             and n.value.strip().upper().startswith("UPDATE")]
    write_hits.extend(stmts)
    cvm6 = (before == after) and not write_hits
    record("AC-CVM6", cvm6,
           "five-table row sets constant across the windowed read "
           "batch; ast scan zero write statements (%d hits)"
           % len(write_hits))

    # ---- AC-CVM7: hygiene
    schema_sha = hashlib.sha256(
        CP._SCHEMA.encode("utf-8")).hexdigest()
    cfg_path = os.path.join(BASE, "config.json")
    cfg_sha = hashlib.sha256(
        open(cfg_path, "rb").read()).hexdigest() if os.path.exists(
        cfg_path) else None
    prod_src = open(os.path.abspath(os.path.join(
        BASE, "civicpoints.py")), "rb").read()
    ascii_prod = all(b < 128 for b in prod_src)
    import_lines = [ln.strip() for ln in prod_src.decode(
        "ascii").split("\n") if ln.strip().startswith(
        "import ") or ln.strip().startswith("from ")]
    net_ok = not any(
        any(w in ln for w in ("urllib", "requests", "socket", "http"))
        for ln in import_lines)
    db_tables = sorted(r[0] for r in chk.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND"
        " name NOT LIKE 'sqlite_%'").fetchall())
    cvm7 = (schema_sha == PIN_SCHEMA_SHA and cfg_sha == PIN_CFG_SHA
            and ascii_prod and net_ok
            and db_tables == ["civic_behaviors", "civic_earns",
                              "civic_grants", "civic_redeems",
                              "civic_rewards"])
    record("AC-CVM7", cvm7,
           "schema sha pinned; config sha pinned; product ascii=%s; "
           "no-network-imports=%s; civic.db table set=%s"
           % (ascii_prod, net_ok, db_tables))

    chk.close()
    chk2.close()
    face.close()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d criteria, %d pass, %d fail" % (
        "PASS" if not failed else "FAIL", len(RESULTS),
        len(RESULTS) - len(failed), len(failed)), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
