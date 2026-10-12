"""Acceptance suite for the member banner_queue read-cap
(BigDomain R1872 tech-queue claim row; seed = the R1850/R1855
sec_batch banner_queue direct-line precedent + the R1871 pay
banner_queue mirror; the window param is the R1866 in-register
sibling).

Asserts the pre-registered criteria AC-MB15..AC-MB22 from the
R1872 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (the R1866 window-suite sister): a fresh
isolated face instance in its own temp world drives the TRUE
product write path end to end - every journal row lands via
attempt()/on_accept() with an explicit ts, so record-time
(ts_utc) is exactly the passed stamp and the tie worlds come
free (four October rows share one stamp, three November rows
share another) - zero fixture injection.

World (cap=2 in-memory cfg variant, shipped config.json
untouched): October day - AV-A attempts renewal_due with no
budget (skip_budget), AV-B accepts first_service with no budget
(skip_budget), AV-C/AV-D hold grants and send (cap exhausted at
2), AV-E attempts with a grant (skip_daily_cap), AV-F accepts
first_service once the cap is hit (skip_daily_cap) = 4 skipped
rows. November day - AV-G attempts with no budget
(skip_budget), AV-A retries the same reason on the new day
(skip_budget - one avatar living in both windows), AV-I/AV-K
send on the fresh day, AV-J accepts first_service (skip_daily_cap)
= 3 skipped rows. 7 skipped total, 11 journal rows.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_banner_queue_limit.py
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
EXPECTED = 8

OCT_TS = "2026-10-15T10:00:00Z"         # October anchor day
NOV_TS = "2026-11-02T09:30:00Z"         # November roll day
OCT_W = OCT_TS[:7]                      # "2026-10"
NOV_W = NOV_TS[:7]                      # "2026-11"
CFG_PATH = os.path.join(BASE, "config.json")

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
WRITE_KW = ("INSERT", "UPDATE ", "DELETE", "REPLACE", "CREATE",
            "DROP ")

# five bad limit forms (family law: sentinel is ONLY the int 0)
BADS5 = (-1, True, 2.5, None, "2")


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


def main():
    tmp = tempfile.mkdtemp(prefix="banner-qlimit-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    rm_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "reminder.py"), "rb").read()
    ).hexdigest()

    cfg = load_cfg(2)
    db = os.path.join(tmp, "qlimit.db")
    face = RM.ReminderFace(cfg, db)

    # ---- October anchor: 6 true-path calls, explicit ts -------
    for avatar in ("AV-C", "AV-D", "AV-E"):
        face.grant_authorization(avatar, "renewal_notice", "longterm")
    face.attempt("AV-A", "renewal_notice", "renewal_due",
                 now=OCT_TS, period_key="PK-A")
    face.on_accept("AV-B", now=OCT_TS, auto_renewal=True)
    face.attempt("AV-C", "renewal_notice", "renewal_due",
                 now=OCT_TS, period_key="PK-C")
    face.attempt("AV-D", "renewal_notice", "renewal_due",
                 now=OCT_TS, period_key="PK-D")
    face.attempt("AV-E", "renewal_notice", "renewal_due",
                 now=OCT_TS, period_key="PK-E")
    face.on_accept("AV-F", now=OCT_TS, auto_renewal=True)
    # ---- November roll: 5 true-path calls on the new day -------
    for avatar in ("AV-I", "AV-K"):
        face.grant_authorization(avatar, "renewal_notice", "longterm")
    face.attempt("AV-G", "renewal_notice", "renewal_due",
                 now=NOV_TS, period_key="PK-G")
    face.attempt("AV-A", "renewal_notice", "renewal_due",
                 now=NOV_TS, period_key="PK-A")
    face.attempt("AV-I", "renewal_notice", "renewal_due",
                 now=NOV_TS, period_key="PK-I")
    face.attempt("AV-K", "renewal_notice", "renewal_due",
                 now=NOV_TS, period_key="PK-K")
    face.on_accept("AV-J", now=NOV_TS, auto_renewal=True)
    total_skipped = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'")[0][0])
    total_rows = int(q(
        db, "SELECT COUNT(*) FROM member_reminder_log")[0][0])

    # ---- AC-MB15: default fidelity (limit=0 raw LIST) ---------
    default_read = face.banner_queue()
    explicit0 = face.banner_queue(limit=0)
    oct_bare = face.banner_queue(window=OCT_W)
    oct_explicit0 = face.banner_queue(window=OCT_W, limit=0)
    positional_win = face.banner_queue(OCT_W)
    mirror_full = q(
        db, "SELECT send_id, census_avatar_id, reason, status,"
        " ts_utc FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' ORDER BY ts_utc")
    ok15 = (total_skipped == 7 and total_rows == 11
            and isinstance(default_read, list)
            and isinstance(oct_bare, list)
            and len(default_read) == 7 and len(oct_bare) == 4
            and dumps(default_read) == dumps(explicit0)
            and dumps(default_read) == dumps(mirror_full)
            and dumps(oct_explicit0) == dumps(oct_bare)
            and dumps(positional_win) == dumps(oct_bare)
            and all(len(r) == 5 for r in default_read))
    record("AC-MB15", ok15,
           "skipped=%d rows=%d default==explicit0=%s default=="
           "mirror=%s window+limit0==window=%s positional==window"
           "=%s list_face=%s row_arity=%s"
           % (total_skipped, total_rows,
              dumps(default_read) == dumps(explicit0),
              dumps(default_read) == dumps(mirror_full),
              dumps(oct_explicit0) == dumps(oct_bare),
              dumps(positional_win) == dumps(oct_bare),
              isinstance(default_read, list),
              all(len(r) == 5 for r in default_read)))

    # ---- AC-MB16: bad-limit fail-closed (5 forms) -------------
    before16 = (q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db, "SELECT COUNT(*) FROM"
                  " member_subscribe_grants")[0][0])
    rejects = []
    for bad in BADS5:
        try:
            face.banner_queue(limit=bad)
            rejects.append(False)
        except ValueError as exc:
            rejects.append(RM.E_REM_BAD_LIMIT in str(exc))
    gate_order_ok = True
    try:
        face.banner_queue(window="2026-99", limit=-1)
        gate_order_ok = False
    except ValueError as exc:
        gate_order_ok = RM.E_REM_BAD_LIMIT in str(exc)
    win_gate_ok = True
    try:
        face.banner_queue("2026-99", 3)
        win_gate_ok = False
    except ValueError as exc:
        win_gate_ok = RM.E_REM_BAD_WINDOW in str(exc)
    after16 = (q(db, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db, "SELECT COUNT(*) FROM"
                 " member_subscribe_grants")[0][0])
    ok16 = (all(rejects) and gate_order_ok and win_gate_ok
            and before16 == after16)
    record("AC-MB16", ok16,
           "rejects=%d/%d limit_gate_first=%s window_gate_still="
           "%s counts_stable=%s (%s==%s)"
           % (sum(1 for r in rejects if r), len(rejects),
              gate_order_ok, win_gate_ok, before16 == after16,
              before16, after16))

    # ---- AC-MB17: cap above total = full read -----------------
    env50 = face.banner_queue(limit=50)
    keys50 = set(env50.keys())
    ok17 = (keys50 == {"rows", "limit", "total", "returned",
                       "truncated"}
            and env50["limit"] == 50 and env50["total"] == 7
            and env50["returned"] == 7 and env50["truncated"] is False
            and dumps(env50["rows"]) == dumps(default_read))
    record("AC-MB17", ok17,
           "keys=%s limit=%d total=%d returned=%d truncated=%s "
           "rows==bare=%s"
           % (sorted(keys50), env50["limit"], env50["total"],
              env50["returned"], env50["truncated"],
              dumps(env50["rows"]) == dumps(default_read)))

    # ---- AC-MB18: truncated tail window -----------------------
    env3 = face.banner_queue(limit=3)
    tail3 = default_read[-3:]
    mirror_sql3 = q(
        db, "SELECT send_id, census_avatar_id, reason, status,"
        " ts_utc FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%'"
        " ORDER BY ts_utc DESC, rowid DESC LIMIT 3")
    mirror_sql3.reverse()
    ok18 = (env3["total"] == 7 and env3["returned"] == 3
            and env3["truncated"] is True and env3["limit"] == 3
            and dumps(env3["rows"]) == dumps(tail3)
            and dumps(env3["rows"]) == dumps(mirror_sql3)
            and all(len(r) == 5 for r in env3["rows"])
            and [r[1] for r in env3["rows"]]
            == ["AV-G", "AV-A", "AV-J"])
    record("AC-MB18", ok18,
           "total=%d returned=%d truncated=%s rows==full_tail=%s "
           "rows==mirror_sql=%s tie_order=%s arity=%s"
           % (env3["total"], env3["returned"], env3["truncated"],
              dumps(env3["rows"]) == dumps(tail3),
              dumps(env3["rows"]) == dumps(mirror_sql3),
              [r[1] for r in env3["rows"]],
              all(len(r) == 5 for r in env3["rows"])))

    # ---- AC-MB19: boundary states -----------------------------
    env7 = face.banner_queue(limit=7)
    env1 = face.banner_queue(limit=1)
    empty_db = os.path.join(tmp, "empty.db")
    face2 = RM.ReminderFace(load_cfg(2), empty_db)
    env_empty = face2.banner_queue(limit=5)
    face2.close()
    ok19 = (env7["truncated"] is False and env7["returned"] == 7
            and env7["total"] == 7
            and env1["returned"] == 1 and env1["truncated"] is True
            and dumps(env1["rows"]) == dumps(default_read[-1:])
            and env_empty["rows"] == [] and env_empty["total"] == 0
            and env_empty["returned"] == 0
            and env_empty["truncated"] is False
            and set(env_empty.keys()) == {"rows", "limit", "total",
                                          "returned", "truncated"})
    record("AC-MB19", ok19,
           "limit==total: truncated=%s returned=%d | limit=1: "
           "returned=%d rows==last1=%s | empty_world: rows=%d "
           "total=%d truncated=%s five_keys=%s"
           % (env7["truncated"], env7["returned"],
              env1["returned"],
              dumps(env1["rows"]) == dumps(default_read[-1:]),
              len(env_empty["rows"]), env_empty["total"],
              env_empty["truncated"],
              set(env_empty.keys()) == {"rows", "limit", "total",
                                       "returned", "truncated"}))

    # ---- AC-MB20: same-timestamp tie determinism --------------
    # 4 October rows share OCT_TS; 3 November rows share NOV_TS
    # (frozen-stamp product-path tie world, zero injection).
    cap2 = face.banner_queue(limit=2)
    cap2_again = face.banner_queue(limit=2)
    tie_nov = [r[1] for r in cap2["rows"]]
    # October-windowed capped tail: AV-E/AV-F are the last two
    # October skipped rows by insertion order (rowid anchor).
    oct_cap2 = face.banner_queue(window=OCT_W, limit=2)
    ok20 = (dumps(cap2["rows"]) == dumps(default_read[-2:])
            and tie_nov == ["AV-A", "AV-J"]
            and dumps(cap2) == dumps(cap2_again)
            and dumps(oct_cap2["rows"]) == dumps(oct_bare[-2:])
            and [r[1] for r in oct_cap2["rows"]]
            == ["AV-E", "AV-F"])
    record("AC-MB20", ok20,
           "nov_tie_tail=%s oct_tie_tail=%s capped==full_tail=%s "
           "oct_capped==oct_bare_tail=%s double_call_identical=%s"
           % (tie_nov, [r[1] for r in oct_cap2["rows"]],
              dumps(cap2["rows"]) == dumps(default_read[-2:]),
              dumps(oct_cap2["rows"]) == dumps(oct_bare[-2:]),
              dumps(cap2) == dumps(cap2_again)))

    # ---- AC-MB21: window x cap orthogonality ------------------
    nov_bare = face.banner_queue(window=NOV_W)
    six_keys = {"rows", "limit", "total", "returned", "truncated",
                "window"}
    nov50 = face.banner_queue(window=NOV_W, limit=50)
    nov2 = face.banner_queue(window=NOV_W, limit=2)
    empty_combo = face.banner_queue(window="2026-09", limit=3)
    no_leak = all(r[4][:7] == OCT_W for r in oct_cap2["rows"]) \
        and all(r[4][:7] == NOV_W for r in nov2["rows"])
    ok21 = (oct_cap2["total"] == 4 and nov2["total"] == 3
            and set(oct_cap2.keys()) == six_keys
            and set(nov2.keys()) == six_keys
            and oct_cap2["window"] == OCT_W
            and nov2["window"] == NOV_W
            and oct_cap2["returned"] == 2
            and oct_cap2["truncated"] is True
            and nov2["returned"] == 2 and nov2["truncated"] is True
            and dumps(nov2["rows"]) == dumps(nov_bare[-2:])
            and nov50["total"] == 3 and nov50["truncated"] is False
            and dumps(nov50["rows"]) == dumps(nov_bare)
            and empty_combo["rows"] == []
            and empty_combo["total"] == 0
            and empty_combo["window"] == "2026-09"
            and empty_combo["truncated"] is False
            and no_leak)
    record("AC-MB21", ok21,
           "oct_total=%d(window-scoped) nov_total=%d "
           "oct_keys_six=%s nov_keys_six=%s "
           "nov_capped==nov_tail=%s nov50==nov_bare=%s "
           "empty_combo_honest=%s no_leak=%s "
           "default_cap_keys_five=%s"
           % (oct_cap2["total"], nov2["total"],
              set(oct_cap2.keys()) == six_keys,
              set(nov2.keys()) == six_keys,
              dumps(nov2["rows"]) == dumps(nov_bare[-2:]),
              dumps(nov50["rows"]) == dumps(nov_bare),
              empty_combo["rows"] == [] and
              empty_combo["total"] == 0, no_leak,
              keys50 == {"rows", "limit", "total", "returned",
                         "truncated"}))

    # ---- AC-MB22: pure-read law + hygiene ---------------------
    src = inspect.getsource(RM.ReminderFace.banner_queue)
    writes = [kw for kw in WRITE_KW if kw in src]
    before22 = (q(db, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db, "SELECT COUNT(*) FROM"
                  " member_subscribe_grants")[0][0])
    face.banner_queue()
    face.banner_queue(limit=3)
    face.banner_queue(window=OCT_W)
    face.banner_queue(window=NOV_W, limit=2)
    face.banner_queue(window="2026-09", limit=3)
    after22 = (q(db, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db, "SELECT COUNT(*) FROM"
                 " member_subscribe_grants")[0][0])
    face.close()
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
    ok22 = (not writes and before22 == after22
            and before22[0] == 11
            and ascii_ok and not net_hits
            and cfg_sha_in == cfg_sha_out
            and rm_sha_in == rm_sha_out and world_outside_repo)
    record("AC-MB22", ok22,
           "write_keywords=%s counts_stable=%s (log %d==%d) "
           "ascii=%s net_imports=%s cfg_unchanged=%s "
           "reminder_unchanged=%s world_outside_repo=%s"
           % (writes, before22 == after22, before22[0],
              after22[0], ascii_ok, net_hits,
              cfg_sha_in == cfg_sha_out,
              rm_sha_in == rm_sha_out, world_outside_repo))

    shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE PASS %d/%d" % (passed, EXPECTED), flush=True)
    if passed != EXPECTED or len(RESULTS) != EXPECTED:
        sys.exit(1)


if __name__ == "__main__":
    main()
