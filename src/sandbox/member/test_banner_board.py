"""Acceptance suite for the reminder banner board (tech.md claim line
R1782).

Asserts the pre-registered criteria AC-BQ1..AC-BQ7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: ReminderFace.banner_board() - pure-read derived aggregation
over the persistent degraded in-app fallback journal: one board row per
avatar holding at least one skipped_* row, dense status/reason zero
grids, deterministic census-key ascending order, member-family
compliance envelope, zero writes, live derivation (no cache).

Usage: python test_banner_board.py
"""

import hashlib
import inspect
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import reminder as RM                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
TS = "2030-06-01T00:00:00Z"             # frozen clock for row stamps
CFG_PATH = os.path.join(BASE, "config.json")


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


def load_cfg(cap=None):
    with open(CFG_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if cap is not None:
        cfg = json.loads(json.dumps(cfg))
        cfg["reminder"]["daily_send_cap_default"] = cap
    return cfg


def fresh_face(tmp, name, cfg):
    db = os.path.join(tmp, name)
    return RM.ReminderFace(cfg, db), db


def main():
    tmp = tempfile.mkdtemp(prefix="banner-board-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    # ---- AC-BQ1: contract, dense honest empty, refusal family -------
    mcfg = load_cfg()
    face1, db1 = fresh_face(tmp, "bq1.db", mcfg)
    env = face1.banner_board()
    env_keys = set(env) == {"banner_board", "total", "by_status",
                            "by_reason", "ai_generated", "disclaimer",
                            "persistent"}
    dense = (env["by_status"] == {"skipped_no_budget": 0,
                                  "skipped_daily_cap": 0}
             and env["by_reason"] == {"first_service": 0,
                                      "renewal_due": 0})
    ok_empty = (env["banner_board"] == [] and env["total"] == 0
                and env["ai_generated"] == 0 and env["persistent"] is True
                and isinstance(env["disclaimer"], str)
                and env["disclaimer"].strip()
                and env["disclaimer"]
                == mcfg["compliance"]["disclaimer"])
    # refusal family: the probes are valid member configs (constructor
    # gates all pass) - only the resident compliance copy is tampered,
    # so the refusal is attributable to the face-call gate alone
    refusals = []
    probe_specs = [
        ("no-compliance",
         lambda c: c.pop("compliance", None)),
        ("empty", lambda c: c["compliance"].update(disclaimer="")),
        ("blank", lambda c: c["compliance"].update(disclaimer="   ")),
        ("non-str", lambda c: c["compliance"].update(disclaimer=123)),
        ("null", lambda c: c["compliance"].update(disclaimer=None)),
    ]
    for label, mutate in probe_specs:
        bad = json.loads(json.dumps(mcfg))
        mutate(bad)
        probe, _ = fresh_face(tmp, "bq1-probe-%s.db" % label, bad)
        try:
            probe.banner_board()
            refusals.append((label, "no-refusal"))
        except ValueError as exc:
            refusals.append((label,
                             RM.E_REM_NO_DISCLAIMER in str(exc)))
    face1.close()
    ok1 = (env_keys and dense and ok_empty
           and all(r[1] is True for r in refusals))
    record("AC-BQ1", ok1,
           "env-keys=%s dense=%s empty-board=%s refusals=%d/%d %s"
           % (env_keys, dense, ok_empty,
              sum(1 for r in refusals if r[1] is True), len(refusals),
              [r[0] for r in refusals if r[1] is True]))

    # ---- AC-BQ2: mixed world + manual SQL cross --------------------
    # cap=2: skipped_no_budget rows cost no cap (only sent rows do),
    # so budget-skips land first, then two sends exhaust the cap and
    # later attempts degrade as cap-skips - all four degraded combos
    # plus sent control rows in ONE world.
    capcfg = load_cfg(cap=2)
    face2, db2 = fresh_face(tmp, "bq2.db", capcfg)
    face2.grant_authorization("AV-A", "renewal_notice", "longterm")
    face2.grant_authorization("AV-D", "renewal_notice", "longterm")
    face2.grant_authorization("AV-E", "renewal_notice", "longterm")
    face2.grant_authorization("AV-F", "renewal_notice", "longterm")
    face2.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")          # no budget
    face2.on_accept("AV-C", now=TS, auto_renewal=True)  # no budget
    face2.attempt("AV-A", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-A")          # sent (cap 1)
    face2.attempt("AV-D", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-D")          # sent (cap 2)
    face2.attempt("AV-E", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-E")          # cap skip
    face2.on_accept("AV-F", now=TS, auto_renewal=True)  # cap skip
    env2 = face2.banner_board()
    man_status = dict((r[0], r[1]) for r in q(
        db2, "SELECT status, COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' GROUP BY status"))
    man_reason = dict((r[0], r[1]) for r in q(
        db2, "SELECT reason, COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' GROUP BY reason"))
    man_total = q(db2, "SELECT COUNT(*) FROM member_reminder_log"
                  " WHERE status LIKE 'skipped_%'")[0][0]
    man_rows = {}
    for avatar, reason, n in q(
            db2, "SELECT census_avatar_id, reason, COUNT(*)"
            " FROM member_reminder_log WHERE status LIKE 'skipped_%'"
            " GROUP BY census_avatar_id, reason"):
        cell = man_rows.setdefault(avatar, {})
        cell[reason] = n
    board_ok = True
    for row in env2["banner_board"]:
        cell = man_rows.get(row["census_avatar_id"], {})
        if row["skipped"] != sum(cell.values()):
            board_ok = False
        for reason, n in cell.items():
            if row["by_reason"].get(reason) != n:
                board_ok = False
    seq = [r["census_avatar_id"] for r in env2["banner_board"]]
    row_keys = all(set(r) == {"census_avatar_id", "skipped",
                              "by_reason"}
                   for r in env2["banner_board"])
    ok2 = (env2["by_status"] == man_status
           and env2["by_reason"] == man_reason
           and env2["total"] == man_total == 4
           and board_ok and row_keys
           and seq == sorted(seq) == ["AV-B", "AV-C", "AV-E", "AV-F"]
           and len(man_rows) == len(seq))
    record("AC-BQ2", ok2,
           "by_status=%s by_reason=%s total=%d manual=%s rows-cross=%s"
           " order=%s" % (env2["by_status"], env2["by_reason"],
                          env2["total"], man_status == env2["by_status"],
                          board_ok, seq))
    face2.close()

    # ---- AC-BQ3: scope isolation (sent rows never counted) ----------
    log_all = q(db2, "SELECT COUNT(*) FROM member_reminder_log")[0][0]
    board_avatars = set(seq)
    skipped_avatars = set(r[0] for r in q(
        db2, "SELECT DISTINCT census_avatar_id FROM"
        " member_reminder_log WHERE status LIKE 'skipped_%'"))
    ok3 = (set(env2["by_status"]) == {"skipped_no_budget",
                                      "skipped_daily_cap"}
           and "sent" not in env2["by_status"]
           and env2["total"] == 4 < log_all == 6
           and board_avatars == skipped_avatars
           and "AV-A" not in board_avatars
           and "AV-D" not in board_avatars)
    record("AC-BQ3", ok3,
           "status-keys=%d total=%d < log=%d board==skipped-avatars=%s"
           " sent-avatars-absent=%s"
           % (len(env2["by_status"]), env2["total"], log_all,
              board_avatars == skipped_avatars,
              "AV-A" not in board_avatars
              and "AV-D" not in board_avatars))

    # ---- AC-BQ4: pure-read law --------------------------------------
    src = inspect.getsource(RM.ReminderFace.banner_board)
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
    face4, db4 = fresh_face(tmp, "bq4.db", load_cfg(cap=1))
    face4.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")
    before = (q(db4, "SELECT COUNT(*) FROM member_reminder_log")[0][0],
              q(db4, "SELECT COUNT(*) FROM"
                " member_subscribe_grants")[0][0])
    first = face4.banner_board()
    second = face4.banner_board()
    after = (q(db4, "SELECT COUNT(*) FROM member_reminder_log")[0][0],
             q(db4, "SELECT COUNT(*) FROM"
               " member_subscribe_grants")[0][0])
    same = (json.dumps(first, sort_keys=True)
            == json.dumps(second, sort_keys=True))
    ok4 = (not dml) and before == after and same
    record("AC-BQ4", ok4,
           "dml-hits=%d counts-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))
    face4.close()

    # ---- AC-BQ5: live derivation (zero cache) -----------------------
    face5, db5 = fresh_face(tmp, "bq5.db", load_cfg())
    face5.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")
    env5a = face5.banner_board()
    face5.attempt("AV-G", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-G")
    env5b = face5.banner_board()
    g_row = [r for r in env5b["banner_board"]
             if r["census_avatar_id"] == "AV-G"]
    ok5 = (env5a["total"] == 1
           and env5b["total"] == 2
           and env5b["by_status"]["skipped_no_budget"] == 2
           and len(g_row) == 1 and g_row[0]["skipped"] == 1
           and [r["census_avatar_id"] for r in env5b["banner_board"]]
           == ["AV-B", "AV-G"])
    record("AC-BQ5", ok5,
           "before=%d after=%d cell=%d new-row=%s order-follows=%s"
           % (env5a["total"], env5b["total"],
              env5b["by_status"]["skipped_no_budget"],
              len(g_row) == 1 and g_row[0]["skipped"] == 1,
              [r["census_avatar_id"] for r in env5b["banner_board"]]
              == ["AV-B", "AV-G"]))
    face5.close()

    # ---- AC-BQ6: hygiene ---------------------------------------------
    subjects = [os.path.join(BASE, "reminder.py"),
                os.path.abspath(__file__)]
    ascii_ok = True
    net_hits = []
    for path in subjects:
        data = open(path, "rb").read()
        if any(b > 127 for b in data):
            ascii_ok = False
        text = data.decode("ascii", "replace")
        for line in text.splitlines():
            stripped = line.strip()
            if (stripped.startswith("import ")
                    or stripped.startswith("from ")) and (
                    re.search(r"\b(urllib|requests|socket|http)\b",
                              stripped)):
                net_hits.append(stripped)
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    mod_src = inspect.getsource(RM)
    additive = (hasattr(RM.ReminderFace, "banner_board")
                and hasattr(RM.ReminderFace, "attempt")
                and hasattr(RM.ReminderFace, "scan")
                and hasattr(RM.ReminderFace, "on_accept")
                and hasattr(RM.ReminderFace, "banner_queue")
                and hasattr(RM.ReminderFace, "grant_authorization")
                and hasattr(RM.ReminderFace, "daily_sent_count")
                and hasattr(RM.ReminderFace,
                            "dual_timepoint_coverage")
                and 'self.disclaimer = comp.get("disclaimer")'
                in mod_src
                and mod_src.count("CREATE TABLE") == 2)
    ok6 = (ascii_ok and not net_hits
           and cfg_sha_in == cfg_sha_out and additive)
    record("AC-BQ6", ok6,
           "ascii=%s subjects=%d network-imports=%d cfg-sha-stable=%s"
           " additive=%s schema-tables=%d"
           % (ascii_ok, len(subjects), len(net_hits),
              cfg_sha_in == cfg_sha_out,
              additive, mod_src.count("CREATE TABLE")))

    # ---- AC-BQ7: delivery (registration self-check) ------------------
    reg_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    reg_src = open(reg_path, encoding="utf-8").read()
    registered = ('"member-banner-board"' in reg_src
                  and 'os.path.join("member", "test_banner_board.py"), 7'
                  in reg_src)
    ok7 = registered
    record("AC-BQ7", ok7,
           "suites-registry-row=%s criteria=7" % registered)

    shutil.rmtree(tmp, ignore_errors=True)
    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
