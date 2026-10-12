"""Acceptance suite for the member banner_queue cap-window read
cross-restart persistence example (BigDomain R1889 tech-queue
claim row; seed = the R1879 caproll suite AC-MB23..29 - that
suite proved the capped+windowed face survives the MONTH ROLL
inside one live instance; this closes the sibling gap the seed
row names: the read face's derivation purity across an
INSTANCE RESTART, pay-side R1884 bannerpersist / R1885
authorize-persist family law).

Asserts the pre-registered criteria AC-MB30..AC-MB36 from the
R1889 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (family law): a fresh isolated face instance
in its own temp world drives the TRUE product write path end
to end - every journal row lands via attempt()/on_accept()
with an explicit ts (no frozen clock, R1869 explicit-ts
precedent), zero fixture injection.

World (cap=2 in-memory cfg variant, shipped config.json
untouched) = the R1879 caproll twin: October day - AV-A
renewal_due skip_budget, AV-B first_service skip_budget,
AV-C/AV-D sent (grants), AV-E/AV-F skip_daily_cap = 4 October
skipped; November day - AV-G/AV-A skip_budget, AV-I/AV-K sent,
AV-J skip_daily_cap = 3 November skipped. 7 skipped, 11 journal
rows, 5 grant rows.

Restart genealogy: face1 loads the world + takes the pre-close
snapshot quartet -> close -> face2 reopens (same cfg object,
same db file) + injects ONE new November skipped row (fresh
avatar AV-L @ a second November day, true attempt path) ->
face3 reopens again (two live instances) for the sequential
read identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_banner_queue_persist.py
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

CAP_SIX = {"rows", "limit", "total", "returned", "truncated",
           "window"}
CAP_FIVE = {"rows", "limit", "total", "returned", "truncated"}


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
    return (face.banner_queue(window=OCT_W),
            face.banner_queue(window=OCT_W, limit=2),
            face.banner_queue(limit=2),
            face.banner_queue())


def main():
    tmp = tempfile.mkdtemp(prefix="banner-persist-")
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
    (pre_oct_bare, pre_oct_cap2, pre_def_cap2, pre_def_bare) = pre
    s_pre = tuple(dumps(x) for x in pre)
    skipped_total = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'")[0][0])
    rows_total = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log")[0][0])
    grants_total = int(q(
        db, "SELECT COUNT(*) FROM"
        " member_subscribe_grants")[0][0])

    ok30 = (r_a["status"] == RM.ST_SKIP_BUDGET
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
            and len(pre_oct_bare) == 4
            and [r[1] for r in pre_oct_bare]
            == ["AV-A", "AV-B", "AV-E", "AV-F"]
            and set(pre_oct_cap2.keys()) == CAP_SIX
            and pre_oct_cap2["limit"] == 2
            and pre_oct_cap2["total"] == 4
            and pre_oct_cap2["returned"] == 2
            and pre_oct_cap2["truncated"] is True
            and pre_oct_cap2["window"] == OCT_W
            and [r[1] for r in pre_oct_cap2["rows"]]
            == ["AV-E", "AV-F"]
            and set(pre_def_cap2.keys()) == CAP_FIVE
            and pre_def_cap2["total"] == 7
            and [r[1] for r in pre_def_cap2["rows"]]
            == ["AV-A", "AV-J"]
            and len(pre_def_bare) == 7)
    record("AC-MB30", ok30,
           "statuses oct=%s,%s,%s,%s,%s,%s nov=%s,%s,%s,%s,%s "
           "skipped=%d rows=%d grants=%d oct_bare=%s "
           "oct_cap2_keys=%s tail=%s def_cap2_keys=%s total=%d "
           "def_bare_rows=%d"
           % (r_a["status"], r_b["status"], r_c["status"],
              r_d["status"], r_e["status"], r_f["status"],
              n_g["status"], n_a["status"], n_i["status"],
              n_k["status"], n_j["status"], skipped_total,
              rows_total, grants_total,
              [r[1] for r in pre_oct_bare],
              sorted(pre_oct_cap2.keys()),
              [r[1] for r in pre_oct_cap2["rows"]],
              sorted(pre_def_cap2.keys()), pre_def_cap2["total"],
              len(pre_def_bare)))

    # ---- restart: face2 reopens on the same cfg + same db -----
    face1.close()
    face2 = RM.ReminderFace(cfg, db)
    oct_cap2_b = face2.banner_queue(window=OCT_W, limit=2)
    oct_bare_b = face2.banner_queue(window=OCT_W)
    oct_cap2_b2 = face2.banner_queue(window=OCT_W, limit=2)
    ok31 = (dumps(oct_cap2_b) == s_pre[1]
            and dumps(oct_bare_b) == s_pre[0]
            and dumps(oct_cap2_b) == dumps(oct_cap2_b2)
            and set(oct_cap2_b.keys()) == CAP_SIX
            and oct_cap2_b["window"] == OCT_W)
    record("AC-MB31", ok31,
           "oct_cap2==pre=%s oct_bare==pre=%s repeat_identical=%s "
           "tiebreak_tail=%s"
           % (dumps(oct_cap2_b) == s_pre[1],
              dumps(oct_bare_b) == s_pre[0],
              dumps(oct_cap2_b) == dumps(oct_cap2_b2),
              [r[1] for r in oct_cap2_b["rows"]]))

    def_cap2_b = face2.banner_queue(limit=2)
    def_bare_b = face2.banner_queue()
    ok32 = (dumps(def_cap2_b) == s_pre[2]
            and def_cap2_b["total"] == 7
            and set(def_cap2_b.keys()) == CAP_FIVE
            and dumps(def_cap2_b["rows"])
            == dumps(def_bare_b[-2:])
            and dumps(def_bare_b) == s_pre[3]
            and [r[1] for r in def_cap2_b["rows"]]
            == ["AV-A", "AV-J"])
    record("AC-MB32", ok32,
           "def_cap2==pre=%s total=%d rows==def_bare_tail=%s "
           "def_bare==pre=%s tail=%s"
           % (dumps(def_cap2_b) == s_pre[2], def_cap2_b["total"],
              dumps(def_cap2_b["rows"]) == dumps(def_bare_b[-2:]),
              dumps(def_bare_b) == s_pre[3],
              [r[1] for r in def_cap2_b["rows"]]))

    # ---- one new November skipped row through the true path ---
    l_r = face2.attempt("AV-L", "renewal_notice", "renewal_due",
                        now=NOV_TS2, period_key="PK-L")
    def_cap2_c = face2.banner_queue(limit=2)
    nov_cap2_c = face2.banner_queue(window=NOV_W, limit=2)
    nov_bare_c = face2.banner_queue(window=NOV_W)
    oct_cap2_c = face2.banner_queue(window=OCT_W, limit=2)
    ok33 = (l_r["status"] == RM.ST_SKIP_BUDGET
            and def_cap2_c["total"] == 8
            and nov_cap2_c["total"] == 4
            and nov_cap2_c["returned"] == 2
            and nov_cap2_c["truncated"] is True
            and len(nov_bare_c) == 4
            and [r[1] for r in nov_bare_c]
            == ["AV-G", "AV-A", "AV-J", "AV-L"]
            and oct_cap2_c["total"] == 4
            and dumps(oct_cap2_c) == s_pre[1])
    record("AC-MB33", ok33,
           "av_l=%s def_total=%d nov_total=%d nov_bare=%s "
           "oct_total=%d oct_envelope==pre=%s"
           % (l_r["status"], def_cap2_c["total"],
              nov_cap2_c["total"],
              [r[1] for r in nov_bare_c], oct_cap2_c["total"],
              dumps(oct_cap2_c) == s_pre[1]))

    # ---- dual live instances: sequential read identity -------
    face3 = RM.ReminderFace(cfg, db)
    f2_reads = (face2.banner_queue(window=OCT_W, limit=2),
                face2.banner_queue(limit=2),
                face2.banner_queue(window=NOV_W, limit=2),
                face2.banner_queue())
    f3_reads = (face3.banner_queue(window=OCT_W, limit=2),
                face3.banner_queue(limit=2),
                face3.banner_queue(window=NOV_W, limit=2),
                face3.banner_queue())
    f2_again = (face2.banner_queue(window=OCT_W, limit=2),
                face2.banner_queue(limit=2),
                face2.banner_queue(window=NOV_W, limit=2),
                face2.banner_queue())
    pair_identical = all(dumps(a) == dumps(b)
                         for a, b in zip(f2_reads, f3_reads))
    reread_identical = all(dumps(a) == dumps(b)
                           for a, b in zip(f2_reads, f2_again))
    ok34 = (pair_identical and reread_identical
            and dumps(f3_reads[0]) == s_pre[1]
            and f3_reads[1]["total"] == 8)
    record("AC-MB34", ok34,
           "face2==face3_all_four=%s face2_reread_identical=%s "
           "oct_envelope==pre=%s def_total=%d"
           % (pair_identical, reread_identical,
              dumps(f3_reads[0]) == s_pre[1],
              f3_reads[1]["total"]))

    # ---- pure-read law across the restart boundary ----------
    src = inspect.getsource(RM.ReminderFace.banner_queue)
    writes = [kw for kw in WRITE_KW if kw in src]
    before35 = (q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db, "SELECT COUNT(*) FROM"
                  " member_subscribe_grants")[0][0])
    face2.banner_queue()
    face2.banner_queue(limit=3)
    face2.banner_queue(window=OCT_W, limit=3)
    face3.banner_queue(window=NOV_W, limit=1)
    face3.banner_queue(window="2026-09", limit=2)
    after35 = (q(db, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db, "SELECT COUNT(*) FROM"
                " member_subscribe_grants")[0][0])
    ok35 = (not writes and before35 == after35
            and before35[0] == 12 and before35[1] == 5)
    record("AC-MB35", ok35,
           "write_keywords=%s counts_stable=%s (log %d==%d "
           "grants %d==%d)"
           % (writes, before35 == after35, before35[0],
              after35[0], before35[1], after35[1]))

    # ---- hygiene ----------------------------------------------
    face2.close()
    face3.close()
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
    ok36 = (ascii_ok and not net_hits
            and cfg_sha_in == cfg_sha_out
            and rm_sha_in == rm_sha_out and world_outside_repo)
    record("AC-MB36", ok36,
           "ascii=%s net_imports=%s cfg_unchanged=%s "
           "reminder_unchanged=%s world_outside_repo=%s"
           % (ascii_ok, net_hits, cfg_sha_in == cfg_sha_out,
              rm_sha_in == rm_sha_out, world_outside_repo))

    shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE PASS %d/%d" % (passed, EXPECTED), flush=True)
    if passed != EXPECTED or len(RESULTS) != EXPECTED:
        sys.exit(1)


if __name__ == "__main__":
    main()
