"""Acceptance suite for the civic honor competition board
month-window read face (BigDomain R1999; canon = explore-queue
civicpoints successor row, criteria AC-HCW1..HCW7 registered in
the R1999 claim note BEFORE this code existed - honesty law).
The face under test is CivicPointsFace.honor_board_competition(
year, window=None): the R1769 1224-competition-rank annual face
extended with an explicit strict YYYY-MM month-window slice
(year-window coupling gate, cross-window separation, in-window
1224 tie semantics, honest empty boards, byte-identical default
full-year mode). Each criterion prints PASS/FAIL with evidence;
the process exits non-zero on any FAIL.

Usage: python test_civic_competition_monthwindow.py
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


def board_rows(env):
    return env["honor_board_competition"]


def main():
    tmp = tempfile.mkdtemp(prefix="civic-hcw-")
    face = CP.CivicPointsFace(DISCLAIMER,
                              os.path.join(tmp, "civic.db"))

    # ---- world build: 3 behaviors, earns across two months
    face.register_behavior("b-five", "five-point shift", 5, 2, True)
    face.register_behavior("b-three", "three-point report", 3, 1,
                           False)
    face.register_behavior("b-two", "two-point drop", 2, 10, False)

    # September earns
    face.earn_civic("usr:alice", "b-five", "2026-09-28", "ev-s1")
    face.earn_civic("usr:carol", "b-two", "2026-09-30", "ev-s2")
    # October earns
    face.earn_civic("usr:alice", "b-five", "2026-10-01", "ev-a1")
    face.earn_civic("usr:alice", "b-five", "2026-10-01", "ev-a2")
    face.earn_civic("usr:bob", "b-five", "2026-10-02", "ev-b1")
    face.earn_civic("usr:alice", "b-three", "2026-10-01", "ev-r1")
    face.earn_civic("usr:carol", "b-three", "2026-10-03", "ev-r2")
    face.earn_civic("usr:bob", "b-two", "2026-10-02", "ev-c1")
    face.earn_civic("usr:bob", "b-two", "2026-10-02", "ev-c2")
    face.earn_civic("usr:carol", "b-two", "2026-10-03", "ev-c3")

    # ---- AC-HCW1: default full-year zero drift
    default_env = face.honor_board_competition("2026")
    none_env = face.honor_board_competition("2026", None)
    hcw1 = canon(default_env) == canon(none_env)
    hcw1 = hcw1 and sorted(default_env.keys()) == [
        "disclaimer", "honor_board_competition"]
    annual_expected = [
        {"rank": 1, "account_id": "usr:alice", "points": 18,
         "events": 4},
        {"rank": 2, "account_id": "usr:bob", "points": 9,
         "events": 3},
        {"rank": 3, "account_id": "usr:carol", "points": 7,
         "events": 3}]
    hcw1 = hcw1 and board_rows(default_env) == annual_expected
    second = canon(face.honor_board_competition("2026"))
    hcw1 = hcw1 and canon(default_env) == second
    hcw1 = hcw1 and default_env["disclaimer"] == DISCLAIMER
    record("AC-HCW1", hcw1,
           "default == explicit-None byte-identical=%s; envelope "
           "keys=%s; annual board=%s (R1769 semantics anchor); "
           "double-call identical"
           % (canon(default_env) == canon(none_env),
              sorted(default_env.keys()), annual_expected))

    # ---- AC-HCW2: strict window validation + coupling gate
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
            face.honor_board_competition("2026", window=bad)
        except CP.CivicError as exc:
            rejected = (exc.code == CP.E_CV_BAD_WINDOW)
        all_rejected = all_rejected and rejected
    coupled_rejected = False
    try:
        face.honor_board_competition("2026", window="2027-01")
    except CP.CivicError as exc:
        coupled_rejected = (exc.code == CP.E_CV_BAD_WINDOW)
    bad_years = ["202", "abcd", 2026, True, "2026 "]
    years_ok = True
    for by in bad_years:
        rejected = False
        try:
            face.honor_board_competition(by)
        except CP.CivicError as exc:
            rejected = (exc.code == CP.E_CV_BAD_ARGS)
        years_ok = years_ok and rejected
    after_counts = {t: chk.execute(
        "SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t, _ in TABLES}
    hcw2 = (all_rejected and coupled_rejected and years_ok
            and before_counts == after_counts)
    record("AC-HCW2", hcw2,
           "%d bad window forms all E_CV_BAD_WINDOW; coupling gate "
           "(2026 + 2027-01) rejected=%s; %d bad year forms all "
           "E_CV_BAD_ARGS; five-table counts constant"
           % (len(bad_windows), coupled_rejected, len(bad_years)))

    # ---- AC-HCW3: month slicing + cross-window separation
    oct_env = face.honor_board_competition("2026", window="2026-10")
    sep_env = face.honor_board_competition("2026", window="2026-09")
    oct_expected = [
        {"rank": 1, "account_id": "usr:alice", "points": 13,
         "events": 3},
        {"rank": 2, "account_id": "usr:bob", "points": 9,
         "events": 3},
        {"rank": 3, "account_id": "usr:carol", "points": 5,
         "events": 2}]
    sep_expected = [
        {"rank": 1, "account_id": "usr:alice", "points": 5,
         "events": 1},
        {"rank": 2, "account_id": "usr:carol", "points": 2,
         "events": 1}]
    hcw3 = (board_rows(oct_env) == oct_expected
            and board_rows(sep_env) == sep_expected
            and oct_env["window"] == "2026-10"
            and sep_env["window"] == "2026-09")
    # independent prefix-filter recount straight through the
    # checker connection (checker-side, not product-side)
    for win, env in (("2026-10", oct_env), ("2026-09", sep_env)):
        recount = {}
        for row in chk.execute(
                "SELECT account_id, COALESCE(SUM(points), 0),"
                " COUNT(*) FROM civic_earns WHERE at_day LIKE ?"
                " GROUP BY account_id", (win + "-%",)):
            recount[row[0]] = (int(row[1]), int(row[2]))
        hcw3 = hcw3 and len(recount) == len(board_rows(env))
        for row in board_rows(env):
            want = recount.get(row["account_id"])
            hcw3 = hcw3 and want == (row["points"], row["events"])
    record("AC-HCW3", hcw3,
           "oct=%s sep=%s; both == independent prefix-filter "
           "recount; zero cross-month leakage either direction "
           "(bob absent from sep board = honest zero-earn absence)"
           % (oct_expected, sep_expected))

    # ---- AC-HCW4: in-window 1224 competition ranks (tie world)
    face2 = CP.CivicPointsFace(
        DISCLAIMER, os.path.join(tmp, "civic-tie.db"))
    face2.register_behavior("b-twelve", "twelve point", 12, 5, True)
    face2.register_behavior("b-six", "six point", 6, 5, False)
    face2.register_behavior("b-seven", "seven point", 7, 5, False)
    face2.register_behavior("b-two", "two point", 2, 20, False)
    # non-alphabetical earn order: bob's earn lands BEFORE aaron's
    # (insertion order must not leak into the tie-break)
    face2.earn_civic("usr:erin", "b-twelve", "2026-10-01", "ev-e1")
    face2.earn_civic("usr:erin", "b-six", "2026-10-02", "ev-e2")
    face2.earn_civic("usr:carol", "b-six", "2026-10-01", "ev-o1")
    face2.earn_civic("usr:carol", "b-six", "2026-10-02", "ev-o2")
    face2.earn_civic("usr:bob", "b-seven", "2026-10-02", "ev-o3")
    face2.earn_civic("usr:aaron", "b-seven", "2026-10-01", "ev-o4")
    face2.earn_civic("usr:dave", "b-two", "2026-10-03", "ev-o5")
    tie_oct = face2.honor_board_competition("2026",
                                            window="2026-10")
    tie_full = face2.honor_board_competition("2026")
    tie_expected = [
        {"rank": 1, "account_id": "usr:erin", "points": 18,
         "events": 2},
        {"rank": 2, "account_id": "usr:carol", "points": 12,
         "events": 2},
        {"rank": 3, "account_id": "usr:aaron", "points": 7,
         "events": 1},
        {"rank": 3, "account_id": "usr:bob", "points": 7,
         "events": 1},
        {"rank": 5, "account_id": "usr:dave", "points": 2,
         "events": 1}]
    hcw4 = (board_rows(tie_oct) == tie_expected
            and board_rows(tie_full) == tie_expected)
    row_keys_ok = all(sorted(r.keys()) == ["account_id", "events",
                                           "points", "rank"]
                      for r in board_rows(tie_oct))
    hcw4 = hcw4 and row_keys_ok
    chk2 = sqlite3.connect(os.path.join(tmp, "civic-tie.db"))
    for row in board_rows(tie_oct):
        greater = chk2.execute(
            "SELECT COUNT(*) FROM (SELECT account_id,"
            " SUM(points) AS p FROM civic_earns WHERE at_day LIKE"
            " '2026-10-%' GROUP BY account_id) WHERE p > ?",
            (row["points"],)).fetchone()[0]
        hcw4 = hcw4 and row["rank"] == 1 + int(greater)
    # tie world all-october: boards equal, envelopes differ by key
    hcw4 = hcw4 and sorted(tie_oct.keys()) == [
        "disclaimer", "honor_board_competition", "window"]
    hcw4 = hcw4 and sorted(tie_full.keys()) == [
        "disclaimer", "honor_board_competition"]
    face2.close()
    chk2.close()
    record("AC-HCW4", hcw4,
           "tie world oct comp ranks [1,2,3,3,5] exact; aaron "
           "before bob despite later earn_id (account_id ASC "
           "tie-break, zero insertion-order key); every rank == 1 "
           "+ strictly-greater manual count; full-year board == "
           "oct board rows (envelopes differ by window key)")

    # ---- AC-HCW5: honest empty windows + additive cross
    nov_env = face.honor_board_competition("2026", window="2026-11")
    dec_env = face.honor_board_competition("2026", window="2026-12")
    far_env = face.honor_board_competition("2099", window="2099-01")
    hcw5 = (board_rows(nov_env) == [] and board_rows(dec_env) == []
            and board_rows(far_env) == []
            and nov_env["window"] == "2026-11"
            and far_env["window"] == "2099-01")
    # additive law: annual per-account points/events == sep + oct
    default_by_account = {r["account_id"]: r for r in board_rows(
        default_env)}
    oct_by_account = {r["account_id"]: r for r in board_rows(
        oct_env)}
    sep_by_account = {r["account_id"]: r for r in board_rows(
        sep_env)}
    union = (set(default_by_account) | set(oct_by_account)
            | set(sep_by_account))
    hcw5 = hcw5 and union == set(default_by_account)
    for account in union:
        full = default_by_account[account]
        oct_row = oct_by_account.get(account,
                                      {"points": 0, "events": 0})
        sep_row = sep_by_account.get(account,
                                     {"points": 0, "events": 0})
        hcw5 = hcw5 and full["points"] == (oct_row["points"]
                                          + sep_row["points"])
        hcw5 = hcw5 and full["events"] == (oct_row["events"]
                                          + sep_row["events"])
    win_first = canon(face.honor_board_competition(
        "2026", window="2026-10"))
    win_second = canon(face.honor_board_competition(
        "2026", window="2026-10"))
    hcw5 = hcw5 and win_first == win_second
    record("AC-HCW5", hcw5,
           "empty windows 2026-11/2026-12 in-year and far-year "
           "2099-01 (coupling gate forward pass) all honest [] "
           "boards; additive law annual==sep+oct per account "
           "(points+events); window double-call byte-identical")

    # ---- AC-HCW6: pure-read law across a mixed windowed batch
    before = {t: table_snapshot(chk, t, oc) for t, oc in TABLES}
    face.honor_board_competition("2026")
    face.honor_board_competition("2026", window="2026-09")
    face.honor_board_competition("2026", window="2026-10")
    face.honor_board_competition("2026", window="2026-11")
    face.honor_board_competition("2099", window="2099-01")
    face.honor_board_competition("2026")
    chk3 = sqlite3.connect(os.path.join(tmp, "civic.db"))
    after = {t: table_snapshot(chk3, t, oc) for t, oc in TABLES}
    src = inspect.getsource(
        CP.CivicPointsFace.honor_board_competition)
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
    hcw6 = (before == after) and not write_hits
    record("AC-HCW6", hcw6,
           "five-table row sets constant across the windowed read "
           "batch; ast scan zero write statements (%d hits)"
           % len(write_hits))

    # ---- AC-HCW7: hygiene
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
    # existing faces untouched by the window feature: honor_board
    # source carries no window parameter and the default branch of
    # the competition face still derives from honor_board
    hb_src = inspect.getsource(CP.CivicPointsFace.honor_board)
    hb_untouched = "window" not in hb_src
    default_delegates = "self.honor_board(year)" in src
    hcw7 = (schema_sha == PIN_SCHEMA_SHA and cfg_sha == PIN_CFG_SHA
            and ascii_prod and net_ok and hb_untouched
            and default_delegates
            and db_tables == ["civic_behaviors", "civic_earns",
                              "civic_grants", "civic_redeems",
                              "civic_rewards"])
    record("AC-HCW7", hcw7,
           "schema sha pinned; config sha pinned; product "
           "ascii=%s; no-network-imports=%s; honor_board "
           "window-free=%s; default branch delegates to "
           "honor_board=%s; civic.db table set=%s"
           % (ascii_prod, net_ok, hb_untouched,
              default_delegates, db_tables))

    chk.close()
    chk3.close()
    face.close()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d criteria, %d pass, %d fail" % (
        "PASS" if not failed else "FAIL", len(RESULTS),
        len(RESULTS) - len(failed), len(failed)), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
