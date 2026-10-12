"""Acceptance suite for the member banner_board capped-window
read cross-restart persistence example (BigDomain R1894
tech-queue claim on the R1889 reseed row; registered criteria
AC-BQ18..AC-BQ24 were written into tech.md BEFORE this code
existed; honesty law).

Sibling closure: the R1889 banner_queue persist suite proved the
raw-row face survives an instance restart; this closes the
board-face gap the seed row names. Read-cap (R1851), month-window
(R1856) and month-roll (R1861) are all in-suite for banner_board
already; the missing law is the board read's derivation purity
across an INSTANCE RESTART (face close -> same cfg same db
reopen), pay-side R1884 bannerpersist family law.

Carrier verdict (family law): a fresh isolated face instance in
its own temp world drives the TRUE product write path end to end -
every journal row lands via attempt()/on_accept() with an
explicit ts (no frozen clock, R1869 explicit-ts precedent), zero
fixture injection.

World (cap=2 in-memory cfg variant, shipped config.json
untouched) = the R1879 caproll / R1889 persist twin: October day
- AV-A renewal_due skip_budget, AV-B first_service skip_budget,
AV-C/AV-D sent (grants), AV-E/AV-F skip_daily_cap = 4 October
skipped; November day - AV-G/AV-A skip_budget, AV-I/AV-K sent,
AV-J skip_daily_cap = 3 November skipped. 7 skipped, 11 journal
rows, 5 grant rows. Default board = 6 avatar rows (AV-A holds a
cross-month cell with by_reason renewal_due: 2).

Restart genealogy: face1 loads the world + takes the pre-close
snapshot quartet (oct capped-window, default capped, default
bare, november capped-window) plus the oct bare read -> close ->
face2 reopens (same cfg object, same db file) + injects ONE new
november skipped row (fresh avatar AV-L @ a second november day,
true attempt path) -> face3 reopens again (two live instances)
for the sequential read identity law.

Seed correction (R1704 precedent, honest note): the seed line
said the default board read recovers with "nine keys" - the
product truth is the R1782 seven-key pin (bare default),
eleven with the cap block (R1851), twelve with an explicit
window (R1856). Criteria below enforce the product truth.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_banner_board_persist.py
"""

import hashlib
import inspect
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import reminder as RM                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

OCT_TS = "2026-10-15T10:00:00Z"         # October anchor day
NOV_TS = "2026-11-02T09:30:00Z"         # November roll day
NOV_TS2 = "2026-11-20T12:00:00Z"        # 2nd November day: fresh cap window
OCT_W = OCT_TS[:7]                      # "2026-10"
NOV_W = NOV_TS[:7]                      # "2026-11"
CFG_PATH = os.path.join(BASE, "config.json")

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

BOARD_SEVEN = {"banner_board", "total", "by_status", "by_reason",
               "ai_generated", "disclaimer", "persistent"}
BOARD_EIGHT = BOARD_SEVEN | {"window"}
BOARD_ELEVEN = BOARD_SEVEN | {"limit", "banner_board_total",
                              "returned", "truncated"}
BOARD_TWELVE = BOARD_ELEVEN | {"window"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def q(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def load_cfg(cap):
    with open(CFG_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg = json.loads(json.dumps(cfg))
    cfg["reminder"]["daily_send_cap_default"] = cap
    return cfg


def quartet(face):
    return (face.banner_board(limit=2, window=OCT_W),
            face.banner_board(limit=2),
            face.banner_board(),
            face.banner_board(limit=2, window=NOV_W))


def avatars(env_or_rows):
    rows = env_or_rows["banner_board"] if isinstance(
        env_or_rows, dict) else env_or_rows
    return [r["census_avatar_id"] for r in rows]


def main():
    tmp = tempfile.mkdtemp(prefix="bannerboard-persist-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()

    cfg = load_cfg(2)
    db = os.path.join(tmp, "persist.db")

    # ---- face1: world load (R1879 caproll twin, true path) ---
    face1 = RM.ReminderFace(cfg, db)
    for avatar in ("AV-C", "AV-D", "AV-E"):
        face1.grant_authorization(avatar, "renewal_notice", "longterm")
    r_a = face1.attempt("AV-A", "renewal_notice", "renewal_due",
                        now=OCT_TS, period_key="PK-A")
    r_b = face1.on_accept("AV-B", now=OCT_TS, auto_renewal=True)
    r_c = face1.attempt("AV-C", "renewal_notice", "renewal_due",
                        now=OCT_TS, period_key="PK-C")
    r_d = face1.attempt("AV-D", "renewal_notice", "renewal_due",
                        now=OCT_TS, period_key="PK-D")
    r_e = face1.attempt("AV-E", "renewal_notice", "renewal_due",
                        now=OCT_TS, period_key="PK-E")
    r_f = face1.on_accept("AV-F", now=OCT_TS, auto_renewal=True)
    for avatar in ("AV-I", "AV-K"):
        face1.grant_authorization(avatar, "renewal_notice", "longterm")
    n_g = face1.attempt("AV-G", "renewal_notice", "renewal_due",
                        now=NOV_TS, period_key="PK-G")
    n_a = face1.attempt("AV-A", "renewal_notice", "renewal_due",
                        now=NOV_TS, period_key="PK-A")
    n_i = face1.attempt("AV-I", "renewal_notice", "renewal_due",
                        now=NOV_TS, period_key="PK-I")
    n_k = face1.attempt("AV-K", "renewal_notice", "renewal_due",
                        now=NOV_TS, period_key="PK-K")
    n_j = face1.on_accept("AV-J", now=NOV_TS, auto_renewal=True)

    pre = quartet(face1)
    (pre_oct_cap, pre_def_cap, pre_def_bare, pre_nov_cap) = pre
    s_pre = tuple(dumps(x) for x in pre)
    pre_oct_bare = face1.banner_board(window=OCT_W)
    s_pre_oct_bare = dumps(pre_oct_bare)
    skipped_total = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'")[0][0])
    rows_total = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log")[0][0])
    grants_total = int(q(
        db, "SELECT COUNT(*) FROM"
        " member_subscribe_grants")[0][0])

    ava_row = None
    for row in pre_def_bare["banner_board"]:
        if row["census_avatar_id"] == "AV-A":
            ava_row = row
    ok18 = (r_a["status"] == RM.ST_SKIP_BUDGET
            and r_b["status"] == RM.ST_SKIP_BUDGET
            and r_c["status"] == "sent" and r_d["status"] == "sent"
            and r_e["status"] == RM.ST_SKIP_CAP
            and r_f["status"] == RM.ST_SKIP_CAP
            and n_g["status"] == RM.ST_SKIP_BUDGET
            and n_a["status"] == RM.ST_SKIP_BUDGET
            and n_i["status"] == "sent" and n_k["status"] == "sent"
            and n_j["status"] == RM.ST_SKIP_CAP
            and skipped_total == 7 and rows_total == 11
            and grants_total == 5
            and set(pre_oct_cap.keys()) == BOARD_TWELVE
            and pre_oct_cap["window"] == OCT_W
            and pre_oct_cap["limit"] == 2
            and pre_oct_cap["banner_board_total"] == 4
            and pre_oct_cap["returned"] == 2
            and pre_oct_cap["truncated"] is True
            and pre_oct_cap["total"] == 4
            and avatars(pre_oct_cap) == ["AV-E", "AV-F"]
            and pre_oct_cap["by_status"]
            == {RM.ST_SKIP_BUDGET: 2, RM.ST_SKIP_CAP: 2}
            and pre_oct_cap["by_reason"]
            == {"first_service": 2, "renewal_due": 2}
            and set(pre_def_cap.keys()) == BOARD_ELEVEN
            and pre_def_cap["banner_board_total"] == 6
            and pre_def_cap["total"] == 7
            and pre_def_cap["truncated"] is True
            and avatars(pre_def_cap) == ["AV-G", "AV-J"]
            and pre_def_cap["by_status"]
            == {RM.ST_SKIP_BUDGET: 4, RM.ST_SKIP_CAP: 3}
            and set(pre_def_bare.keys()) == BOARD_SEVEN
            and pre_def_bare["total"] == 7
            and avatars(pre_def_bare)
            == ["AV-A", "AV-B", "AV-E", "AV-F", "AV-G", "AV-J"]
            and ava_row is not None
            and ava_row["skipped"] == 2
            and ava_row["by_reason"]
            == {"first_service": 0, "renewal_due": 2}
            and pre_def_bare["ai_generated"] == 0
            and pre_def_bare["persistent"] is True
            and set(pre_nov_cap.keys()) == BOARD_TWELVE
            and pre_nov_cap["window"] == NOV_W
            and pre_nov_cap["total"] == 3
            and pre_nov_cap["banner_board_total"] == 3
            and avatars(pre_nov_cap) == ["AV-G", "AV-J"]
            and set(pre_oct_bare.keys()) == BOARD_EIGHT
            and pre_oct_bare["total"] == 4
            and avatars(pre_oct_bare)
            == ["AV-A", "AV-B", "AV-E", "AV-F"])
    record("AC-BQ18", ok18,
           "statuses ok skipped=%d rows=%d grants=%d oct_cap 12keys "
           "tail=%s total=%d def_cap 11keys bb_total=%d tail=%s "
           "total=%d def_bare 7keys rows=%s nov_cap total=%d "
           "oct_bare 8keys rows=%d"
           % (skipped_total, rows_total, grants_total,
              avatars(pre_oct_cap), pre_oct_cap["total"],
              pre_def_cap["banner_board_total"],
              avatars(pre_def_cap), pre_def_cap["total"],
              avatars(pre_def_bare), pre_nov_cap["total"],
              len(pre_oct_bare["banner_board"])))

    # ---- restart: face2 reopens on the same cfg + same db -----
    face1.close()
    face2 = RM.ReminderFace(cfg, db)
    oct_cap_b = face2.banner_board(limit=2, window=OCT_W)
    oct_cap_b2 = face2.banner_board(limit=2, window=OCT_W)
    oct_bare_b = face2.banner_board(window=OCT_W)
    ok19 = (dumps(oct_cap_b) == s_pre[0]
            and dumps(oct_cap_b) == dumps(oct_cap_b2)
            and set(oct_cap_b.keys()) == BOARD_TWELVE
            and oct_cap_b["window"] == OCT_W
            and dumps(oct_bare_b) == s_pre_oct_bare
            and set(oct_bare_b.keys()) == BOARD_EIGHT
            and avatars(oct_bare_b)
            == ["AV-A", "AV-B", "AV-E", "AV-F"])
    record("AC-BQ19", ok19,
           "oct_cap==pre=%s repeat_identical=%s keys=12 tail=%s "
           "oct_bare==pre=%s keys=8"
           % (dumps(oct_cap_b) == s_pre[0],
              dumps(oct_cap_b) == dumps(oct_cap_b2),
              avatars(oct_cap_b),
              dumps(oct_bare_b) == s_pre_oct_bare))

    def_cap_b = face2.banner_board(limit=2)
    def_bare_b = face2.banner_board()
    ok20 = (dumps(def_cap_b) == s_pre[1]
            and set(def_cap_b.keys()) == BOARD_ELEVEN
            and def_cap_b["banner_board_total"] == 6
            and def_cap_b["total"] == 7
            and dumps(def_cap_b["banner_board"])
            == dumps(def_bare_b["banner_board"][-2:])
            and dumps(def_bare_b) == s_pre[2]
            and set(def_bare_b.keys()) == BOARD_SEVEN
            and avatars(def_cap_b) == ["AV-G", "AV-J"])
    record("AC-BQ20", ok20,
           "def_cap==pre=%s 11keys bb_total=%d total=%d "
           "cap_board==bare_tail=%s def_bare==pre=%s tail=%s"
           % (dumps(def_cap_b) == s_pre[1],
              def_cap_b["banner_board_total"], def_cap_b["total"],
              dumps(def_cap_b["banner_board"])
              == dumps(def_bare_b["banner_board"][-2:]),
              dumps(def_bare_b) == s_pre[2],
              avatars(def_cap_b)))

    # ---- one new November skipped row through the true path ---
    l_r = face2.attempt("AV-L", "renewal_notice", "renewal_due",
                        now=NOV_TS2, period_key="PK-L")
    def_cap_c = face2.banner_board(limit=2)
    def_bare_c = face2.banner_board()
    ok21 = (l_r["status"] == RM.ST_SKIP_BUDGET
            and def_cap_c["banner_board_total"] == 7
            and def_cap_c["total"] == 8
            and dumps(def_cap_c) != s_pre[1]
            and avatars(def_cap_c) == ["AV-J", "AV-L"]
            and avatars(def_bare_c)
            == ["AV-A", "AV-B", "AV-E", "AV-F", "AV-G", "AV-J",
                "AV-L"]
            and def_bare_c["total"] == 8)
    record("AC-BQ21", ok21,
           "av_l=%s def_cap bb_total=%d total=%d differs_from_pre=%s"
           " tail=%s bare_rows=%d"
           % (l_r["status"], def_cap_c["banner_board_total"],
              def_cap_c["total"], dumps(def_cap_c) != s_pre[1],
              avatars(def_cap_c), len(def_bare_c["banner_board"])))

    # ---- old window frozen; new row lands in the new window ---
    oct_cap_c = face2.banner_board(limit=2, window=OCT_W)
    oct_bare_c = face2.banner_board(window=OCT_W)
    nov_cap_c = face2.banner_board(limit=2, window=NOV_W)
    nov_bare_c = face2.banner_board(window=NOV_W)
    ok22 = (dumps(oct_cap_c) == s_pre[0]
            and oct_cap_c["total"] == 4
            and oct_cap_c["banner_board_total"] == 4
            and dumps(oct_bare_c) == s_pre_oct_bare
            and nov_cap_c["total"] == 4
            and nov_cap_c["banner_board_total"] == 4
            and nov_cap_c["returned"] == 2
            and nov_cap_c["truncated"] is True
            and "AV-L" in avatars(nov_bare_c)
            and avatars(nov_bare_c)
            == ["AV-A", "AV-G", "AV-J", "AV-L"]
            and len(nov_bare_c["banner_board"]) == 4)
    record("AC-BQ22", ok22,
           "oct_cap==pre=%s oct_total=%d oct_bare==pre=%s "
           "nov_total=%d nov_bb_total=%d nov_bare=%s"
           % (dumps(oct_cap_c) == s_pre[0], oct_cap_c["total"],
              dumps(oct_bare_c) == s_pre_oct_bare,
              nov_cap_c["total"], nov_cap_c["banner_board_total"],
              avatars(nov_bare_c)))

    # ---- dual live instances: sequential read identity -------
    face3 = RM.ReminderFace(cfg, db)
    f2_reads = (face2.banner_board(limit=2, window=OCT_W),
                face2.banner_board(limit=2),
                face2.banner_board(limit=2, window=NOV_W),
                face2.banner_board())
    f3_reads = (face3.banner_board(limit=2, window=OCT_W),
                face3.banner_board(limit=2),
                face3.banner_board(limit=2, window=NOV_W),
                face3.banner_board())
    f2_again = (face2.banner_board(limit=2, window=OCT_W),
                face2.banner_board(limit=2),
                face2.banner_board(limit=2, window=NOV_W),
                face2.banner_board())
    pair_identical = all(dumps(a) == dumps(b)
                         for a, b in zip(f2_reads, f3_reads))
    reread_identical = all(dumps(a) == dumps(b)
                           for a, b in zip(f2_reads, f2_again))
    ok23 = (pair_identical and reread_identical
            and dumps(f3_reads[0]) == s_pre[0]
            and f3_reads[1]["total"] == 8
            and f3_reads[1]["banner_board_total"] == 7
            and f3_reads[2]["total"] == 4)
    record("AC-BQ23", ok23,
           "face2==face3_all_four=%s face2_reread_identical=%s "
           "oct_cap==pre=%s def_total=%d def_bb_total=%d "
           "nov_total=%d"
           % (pair_identical, reread_identical,
              dumps(f3_reads[0]) == s_pre[0],
              f3_reads[1]["total"],
              f3_reads[1]["banner_board_total"],
              f3_reads[2]["total"]))

    # ---- pure-read law + hygiene ------------------------------
    src = inspect.getsource(RM.ReminderFace.banner_board)
    writes = [kw for kw in WRITE_KW if kw in src]
    before24 = (q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db, "SELECT COUNT(*) FROM"
                 " member_subscribe_grants")[0][0])
    face2.banner_board()
    face2.banner_board(limit=3)
    face2.banner_board(limit=3, window=OCT_W)
    face3.banner_board(limit=1, window=NOV_W)
    face3.banner_board(limit=2, window="2026-09")
    after24 = (q(db, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db, "SELECT COUNT(*) FROM"
                " member_subscribe_grants")[0][0])
    with open(os.path.abspath(__file__), "rb") as fh:
        own = fh.read()
    ascii_ok = True
    try:
        own.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    import_lines = [ln.strip() for ln in own.decode("utf-8")
                    .splitlines() if ln.strip().startswith("import ")]
    net_hits = [ln for ln in import_lines
                for lib in NET_LIBS if lib in ln]
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_out = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()
    world_outside_repo = not os.path.abspath(db).startswith(
        os.path.abspath(BASE) + os.sep)
    ok24 = (not writes and before24 == after24
            and before24[0] == 12 and before24[1] == 5
            and ascii_ok and not net_hits
            and cfg_sha_in == cfg_sha_out
            and rm_sha_in == rm_sha_out and world_outside_repo)
    record("AC-BQ24", ok24,
           "write_keywords=%s counts_stable=%s (log %d==%d grants "
           "%d==%d) ascii=%s net_imports=%s cfg_unchanged=%s "
           "reminder_unchanged=%s world_outside_repo=%s"
           % (writes, before24 == after24, before24[0],
              after24[0], before24[1], after24[1], ascii_ok,
              net_hits, cfg_sha_in == cfg_sha_out,
              rm_sha_in == rm_sha_out, world_outside_repo))

    face2.close()
    face3.close()
    shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE PASS %d/%d" % (passed, EXPECTED), flush=True)
    if passed != EXPECTED or len(RESULTS) != EXPECTED:
        sys.exit(1)


if __name__ == "__main__":
    main()
